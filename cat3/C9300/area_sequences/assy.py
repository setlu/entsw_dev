"""
----------
C9300 ASSY
----------
"""

# Python
# ------
import logging
import sys

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Specific
# -----------
import apollo.scripts.entsw.libs.seq.dynamic_sequence_builder as dynamic_sequence_builder
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_nyquist


__product_line__ = 'C9300'
__area__ = 'ASSY'
__title__ = "{0} {1} Sequence Module".format(__product_line__, __area__)
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

PUID_KEYS = ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SYSTEM_SERIAL_NUM', 'MODEL_NUM']

def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __area__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.ud_set_puid_keys, name='SET PUID', kwargs={'keys': PUID_KEYS})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER',
                 kwargs={'method': 'scan',
                         'required_items': ['TAN_NUM',
                                            'SYSTEM_SERIAL_NUM'
                                            ],
                         'prepopulated_items': ['DEVIATION_NUM'],
                         'optional_items': ['USB_ASSEMBLY_NUM',
                                            'USB_SERIAL_NUM',
                                            'STKPWR_ASSEMBLY_NUM',
                                            'STKPWR_SERIAL_NUM']}
                 )

    seq.add_step(steps_catalyst.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    seq.add_step(steps_catalyst.process_add_tst, name='ADD TST')
    seq.add_step(steps_catalyst.ud_save, name='SAVE UUT DESCRIPTOR')
    seq.add_step(steps_catalyst.ud_cache_ud_data, name='CACHE UUT DATA')
    seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def standard_switch_sequence_definition():
    try:
        container = aplib.get_my_container_key()
    except Exception:
        raise Exception("Cannot use this Apollo version!")
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(container))
    pf = udd.get('product_family').upper()
    pc = udd.get('product_codename').upper()
    psd = udd.get('uut_config', {}).get('prod_seq_def', {})
    area = __area__  # udd.get('test_area', None)
    seq = aplib.get_sequence_definition('{0} {1} {2} {3} SEQ'.format(__product_line__, pf, pc, area), jump_on_error='FINAL')

    # ------------------------------------------------------------------------------------------------------------------
    # Init
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_nyquist.init, name='INIT', kwargs={})
    init_seq.add_step(steps_nyquist.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_nyquist.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_nyquist.ud_print_uut_config, name='PRINT UUT CONFIG')

    # Area Check
    seq.add_step(steps_nyquist.process_area_check, name='AREACHECK', kwargs={}, enabled=True)

    # Power ON & Boot
    # Unit should already be powered up from pre-sequence auto-discovery.
    # seq.add_step(steps_nyquist.power_cycle_on, name='POWER ON BOOT', group_level=5, enabled=False)

    # Basic Mode
    seq.add_step(steps_nyquist.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})

    # ------------------------------------------------------------------------------------------------------------------
    # PCAMAP
    pcamap_seq = seq.add_sequence('PCAMAP PROGRAMMING', enabled=True)
    # Verify CMPD
    # TODO: waiting Trac #5852
    pcamap_seq.add_step(steps_nyquist.process_verify_cmpd, name='VERIFY CMPD SPROM', enabled=False,
                        kwargs={'force': False,
                                'cmpd_description': 'SPROM',
                                'uut_type_key': 'MODEL_NUM',
                                'part_number_key': 'TAN_NUM',
                                'part_revision_key': 'TAN_REVISION_NUMBER',
                                'eco_type': 'VERIFICATION'})

    # PCAMAP Program
    pcamap_seq.add_step(steps_nyquist.pcamap_write_uut, name='PCAMAP PROGRAM', kwargs={'device_instance': 0, 'memory_type': 'vb'})

    # PIDVID Verify
    seq.add_step(steps_nyquist.process_verify_pidvid, name='PIDVID VERIFY', jump_on_error='CLEAN UP')

    # ------------------------------------------------------------------------------------------------------------------
    # Diag Testing
    diag_seq = seq.add_sequence('DIAGNOSTIC TESTS', enabled=True)
    diag_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    diag_seq.add_step(steps_nyquist.diags_sysinit, name='SYSINIT')
    diag_seq.add_step(steps_nyquist.diags_psu_check, name='PSU CHECK', kwargs={})

    # Diag Testlist build-out
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)

    # ------------------------------------------------------------------------------------------------------------------
    # Traffic Testing
    traf_seq = seq.add_sequence('TRAFFIC TESTS', enabled=True)
    traf_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST PRETRAF', kwargs={'mode': 'STARDUST'})
    traf_seq.add_step(steps_nyquist.diags_sysinit, name='DIAG SYSINIT PRETRAF')
    dynamic_sequence_builder.build_traffic_cases_subseq(traffic_seq=traf_seq, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)

    # ------------------------------------------------------------------------------------------------------------------
    # Power OFF
    seq.add_step(steps_nyquist.power_off, name='POWER OFF', group_level=1000)

    # Clean up
    final_seq = seq.add_sequence('FINAL', finalization=True)
    final_seq.add_step(steps_nyquist.power_off, name='POWER OFF', kwargs={}, group_level=1000)
    final_seq.add_step(steps_nyquist.clean_up, name='CLEAN UP')
    final_seq.add_step(steps_nyquist.final, name='END')

    return seq