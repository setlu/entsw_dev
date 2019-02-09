"""
-----------
C9300 PCB2C
-----------
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
import apollo.scripts.entsw.libs.equip_drivers.steps_ess_chamber as steps_ess_chamber
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_nyquist


__product_line__ = 'C9300'
__area__ = 'PCB2C'
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

PUID_KEYS = ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
             'MOTHERBOARD_SERIAL_NUM', 'MOTHERBOARD_ASSEMBLY_NUM']

DEFAULT_MAX_CHAMBER_SLOTS = 16


def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    """ Supercontainer
    :return:
    """
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __area__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})

    steps_ess_chamber.set_chamber_slots(max_chamber_slots=DEFAULT_MAX_CHAMBER_SLOTS)
    seq.add_step(steps_ess_chamber.prestep__chamber_staging, name='CHAMBER STAGING', kwargs={'area': 'PCB2C'})

    # Chamber PRE-SEQ Readiness
    seq.add_step(steps_ess_chamber.step__chamber_init, name='CHAMBER INIT', kwargs={'first_init': True, 'profile_type': 'commercial', 'fi_action': 'nopause'})
    seq.add_step(steps_ess_chamber.step__chamber_start, name='CHAMBER START')

    # UUT PRE-SEQ Queue
    seq.add_step(step__queue_children, name='QUEUE UUT PRESEQ')

    # Chamber Post-Staging
    seq.add_step(steps_ess_chamber.prestep__chamber_post_staging, name='CHAMBER POST STAGING')

    seq.add_step(steps_catalyst.final, name='FINAL', finalization=True)

    return seq


def pre2_sequence_definition():
    """ UUT Container
    :return:
    """
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __area__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.ud_set_puid_keys, name='SET PUID', kwargs={'keys': PUID_KEYS})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER', kwargs={'method': 'boot'})
    seq.add_step(steps_ess_chamber.prestep__set_chamber_attributes, name='UUT CHAMBER ATTRIBUTES', kwargs={})
    seq.add_step(steps_catalyst.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    seq.add_step(steps_catalyst.process_add_tst, name='ADD TST')
    seq.add_step(steps_catalyst.ud_save, name='SAVE UUT DESCRIPTOR')
    seq.add_step(steps_catalyst.ud_cache_ud_data, name='CACHE UUT DATA')
    seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


def step__queue_children():
    ACTIVECS_KEY, MAXCS_KEY = steps_ess_chamber.get_chamber_slots_keys()
    uut_slots = aplib.get_cached_data(ACTIVECS_KEY)
    log.debug('Chamber slots staged: {0}'.format(uut_slots))
    supercontainer = aplib.get_container_name()
    for i, uut_slot in enumerate(uut_slots):
        container_name = '{0}:UUT{1:02}'.format(supercontainer, uut_slot)
        log.debug("Queued Conatiner = {0}".format(container_name))
        aplib.queue_child_container(container_name, test_area=__area__)
    return aplib.PASS


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def standard_switch_sequence_definition():
    return standard_switch_common(profile_type='productdef')


def standard_switch_unittest_sequence_definition():
    return standard_switch_common(profile_type='quicksim')


def standard_switch_common(profile_type):
    """ 2C/4C Run Sequence that includes:
        1) setup
        2) area check
        3) chamber startup
        4) corner buildup
        5) chamber wrapup
        5) power off
        6) cleanup

    :return: seq
    """
    try:
        container = aplib.get_my_container_key()
    except Exception:
        raise Exception("Cannot use this Apollo version!")
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(container))
    pf = udd.get('product_family').upper()
    pc = udd.get('product_codename').upper()
    seq = aplib.get_sequence_definition('{0} {1} {2} {3} SEQ'.format(__product_line__, pf, pc, __area__), jump_on_error='FINAL')

    # Enable CATS
    # seq.adt_enabled = ['cats']
    # ------------------------------------------------------------------------------------------------------------------
    # Init
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_nyquist.init, name='INIT', kwargs={})
    init_seq.add_step(steps_nyquist.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_nyquist.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_nyquist.ud_print_uut_config, name='PRINT UUT CONFIG')


    # Chamber Init
    # TODO: Trac#6087
    seq.add_step(steps_ess_chamber.step__chamber_init, name='CHAMBER INIT',
                 kwargs={'profile_type': profile_type, 'fi_action': 'nopause', 'first_init': False})
    # Area Check
    seq.add_step(steps_nyquist.process_area_check, name='AREACHECK',
                 kwargs={'previous_area': 'ICT'},
                 enabled=True)

    # MAC Verify Only
    seq.add_step(steps_nyquist.process_assign_verify_mac, name='VERIFY MAC', kwargs={'assign': False})

    # ------------------------------------------------------------------------------------------------------------------
    # PCAMAP
    pcamap_seq = seq.add_sequence('PCAMAP PROGRAMMING', enabled=True)
    # Verify CMPD
    # TODO: waiting Trac #5852
    pcamap_seq.add_step(steps_nyquist.process_verify_cmpd, name='VERIFY CMPD SPROM',
                        kwargs={'force': False,
                                'cmpd_description': 'SPROM',
                                'uut_type_key': 'MODEL_NUM',
                                'part_number_key': 'MOTHERBOARD_ASSEMBLY_NUM',
                                'part_revision_key': 'MOTHERBOARD_REVISION_NUM',
                                'previous_area': 'PCBST',
                                'eco_type': 'VERIFICATION'},
                        enabled=False)

    # Chamber Start
    seq.add_step(steps_ess_chamber.step__chamber_start, name='CHAMBER START', kwargs={})

    # --------------------------------------------------------------------------------------------------------------
    # Build All Corners
    # Example corners = OrderedDict([('NTNV', ('AMBIENT', 'NOMINAL', False)),
    #                                ('HTLV', ('HOT', 'LOW', True)),
    #                                ('LTLV', ('COLD', 'LOW', True))])
    if True:  # Logic branch for chamber debug (if needed)
        corners = steps_ess_chamber.get_global_corners()
        for i, corner in enumerate(corners):
            temperature = corners[corner][0]
            voltage = corners[corner][1]
            adt_flag = corners[corner][2]
            corner_seq = seq.add_sequence('{0} CORNER'.format(corner), adt_enabled=adt_flag)
            corner_seq.add_step(steps_ess_chamber.step__chamber_ramp, name='CHAMBER RAMP {0}'.format(temperature), kwargs={'action': temperature})
            corner_seq_sublevel1 = corner_seq.add_sequence('UUT-MONITOR GROUP', parallel_steps=True)
            corner_seq_sublevel1.add_step(steps_ess_chamber.step__chamber_start_monitor, name="CHAMBER MONITOR START {0}".format(i))
            corner_seq_sublevel2 = corner_seq_sublevel1.add_sequence('UUT AT {0} VOLT'.format(voltage))
            corner_seq_sublevel3 = corner_seq_sublevel2.add_sequence('UUT TESTS', adt_enabled=adt_flag, jump_on_error="CHAMBER MONITOR STOP {0}".format(i))
            corner_seq_sublevel3.add_step(steps_nyquist.power_cycle_on, name='POWER ON BOOT', group_level=5)
            if True:  # Logic branch for chamber debug (if needed)
                corner_seq_sublevel3.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_switch_mcu_mode, name='MCU MODE IOS', kwargs={'kkmode': 'IOS'})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_sysinit, name='DIAG SYSINIT')
                corner_seq_sublevel3.add_step(steps_nyquist.diags_vmargin_test, name='VOLTAGE MARGIN', kwargs={'device_instance': 0, 'margin_level': voltage})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_temperature_test, name='UUT TEMPERATURES', kwargs={'temperature_corner': temperature, 'operational_state': 'idle'})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_psu_check, name='PSU CHECK', kwargs={})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_stackrac_test, name='STACKRAC TEST', kwargs={})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_serdeseye_sif_test, name='SERDES EYE SIF TEST', kwargs={})
                corner_seq_sublevel3.add_step(steps_nyquist.diags_serdeseye_nif_test, name='SERDES EYE NIF TEST', kwargs={})
                # Diag Testlist build-out
                corner_seq_sublevel3_diag = corner_seq_sublevel3.add_sequence('DIAG TESTS')
                corner_seq_sublevel3_diag.add_step(steps_nyquist.goto_mode, name='MODE DIAG', kwargs={'mode': 'DIAG'})
                dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=corner_seq_sublevel3_diag, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)
                # Traffic Testlist build-out
                corner_seq_sublevel3_traf = corner_seq_sublevel3.add_sequence('TRAF TESTS')
                corner_seq_sublevel3_traf.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
                dynamic_sequence_builder.build_traffic_cases_subseq(traffic_seq=corner_seq_sublevel3_traf, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)
            # Corner wrap-up
            corner_seq_sublevel2.add_step(steps_ess_chamber.step__chamber_stop_monitor, name="CHAMBER MONITOR STOP {0}".format(i), kwargs={}, group_level=aplib.FINALIZATION - 2)
            corner_seq.add_step(steps_nyquist.power_off, name='POWER OFF', group_level=aplib.FINALIZATION - 1)

    # ------------------------------------------------------------------------------------------------------------------
    # Chamber Wrap-Up
    #   1. Chamber Stop will sync all containers AND return chamber to ambient.
    #   2. Power off each UUT.
    #   3. Clean Up (remove classes and clean userdict)
    final_seq = seq.add_sequence('FINAL', finalization=True)
    final_seq.add_step(steps_ess_chamber.step__chamber_final, name="CHAMBER STOP", kwargs={}, group_level=aplib.FINALIZATION - 3)
    final_seq.add_step(steps_nyquist.power_off, name='POWER OFF', group_level=aplib.FINALIZATION - 2)
    final_seq.add_step(steps_nyquist.clean_up, name='CLEAN UP', group_level=aplib.FINALIZATION - 1)

    return seq
