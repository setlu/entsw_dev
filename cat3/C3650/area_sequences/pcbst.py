"""
-----------
C3650 PCBST
-----------
"""

# Python
# ------
import logging
import sys
from collections import namedtuple

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Specific
# -----------
import apollo.scripts.entsw.libs.seq.dynamic_sequence_builder as dynamic_sequence_builder
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_archimedes


__product_line__ = 'C3650'
__desc__ = 'PCBST'
__title__ = "{0} {1} Sequence Module".format(__product_line__, __desc__)
__version__ = '2.0.0'
__author__ = 'bborel'

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

SeqStep = namedtuple('SeqStep', ' step_module seq_function_name')
SEQ_STEP_MAP = {
    'ARCHIMEDES': SeqStep(steps_archimedes, 'archimedes_sequence'),
}
PUID_KEYS = ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
             'MOTHERBOARD_SERIAL_NUM', 'MOTHERBOARD_ASSEMBLY_NUM']

def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE-SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __desc__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.ud_set_puid_keys, name='SET PUID', kwargs={'keys': PUID_KEYS})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER',
                 kwargs={'method': 'scan',
                         'required_items': ['MOTHERBOARD_ASSEMBLY_NUM',
                                            'MOTHERBOARD_SERIAL_NUM',
                                            'QUACK_LABEL_SN'],
                         'prepopulated_items': ['DEVIATION_NUM'],
                         'optional_items': ['POE1_ASSEMBLY_NUM',
                                            'POE1_SERIAL_NUM',
                                            'POE2_ASSEMBLY_NUM',
                                            'POE2_SERIAL_NUM']}
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
    seq = aplib.get_sequence_definition('{0} {1} {2} {3} SEQ'.format(__product_line__, pf, pc, __desc__), jump_on_error='FINAL')
    if pf in SEQ_STEP_MAP:
        func = getattr(thismodule, SEQ_STEP_MAP[pf].seq_function_name)
        return func(seq, pf, udd, container)
    else:
        seq.add_step(step__unknown, kwargs={'pf': pf})
        seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


def step__unknown(pf):
    errmsg = "The product family {0} is NOT known.".format(pf)
    log.critical(errmsg)
    return aplib.FAIL, errmsg


#-----------------------------------------------------------------------------------------------------------------------
# ARCHIMEDES
#-----------------------------------------------------------------------------------------------------------------------
def archimedes_sequence(seq, pf, udd, container):
    """ Nyquist SEQ
    :param seq:
    :param pf:
    :param udd:
    :return:
    """
    uut_config = udd.get('uut_config', {})
    # ------------------------------------------------------------------------------------------------------------------
    # Set up
    subseq__init(seq, pf)

    # Area Check
    seq.add_step(steps_archimedes.process_area_check, name='AREACHECK',
                 kwargs={'previous_area': 'ICT'},
                 enabled=True)

    # Assemble Motherboard Geneaology
    seq.add_step(steps_archimedes.process_register_genealogy,
                 name='REGISTER MOTHERBOARD GENEALOGY',
                 kwargs={'parent_sernum_item': 'MOTHERBOARD_SERIAL_NUM',
                         'parent_pid_item': 'MOTHERBOARD_ASSEMBLY_NUM',
                         'optional_child_sernum_items': ['POE1_SERIAL_NUM', 'POE2_SERIAL_NUM'],
                         'optional_child_pid_items': ['POE1_ASSEMBLY_NUM', 'POE2_ASSEMBLY_NUM']},
                 )

    # ------------------------------------------------------------------------------------------------------------------
    # Power ON & Boot
    seq.add_step(steps_archimedes.power_cycle_on, name='POWER ON BOOT', kwargs={}, group_level=5)

    # SubSeq Blocks
    subseq__preprocess_pcamap(seq, pf)
    subseq__format_flash(seq, pf)
    subseq__load_images(seq, pf)
    subseq__write_pcamap(seq, pf)
    subseq__prog_hw(seq, pf, uut_config, 'STANDARD')
    subseq__diags(seq, pf, container, udd)
    subseq__traffic(seq, pf, container, udd)

    # ------------------------------------------------------------------------------------------------------------------
    # Power OFF
    # Clean up
    subseq__final(seq, pf)
    return seq


#=======================================================================================================================
# Library of Common Main Sub-Sequences
#=======================================================================================================================
def subseq__init(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_pf.init, name='INIT', kwargs={})
    init_seq.add_step(steps_pf.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_pf.equip_setup, name='EQUIP SETUP', kwargs={})
    init_seq.add_step(steps_pf.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_pf.ud_print_uut_config, name='PRINT UUT CONFIG')
    return seq


def subseq__preprocess_pcamap(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    # Basic Mode
    seq.add_step(steps_pf.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    seq.add_step(steps_pf.pcamap_read_uut, name='IMPORT ROMMON PARAMS',
                 kwargs={'device_instance': 0, 'memory_type': 'vb'})
    # MAC Verify and Assign
    seq.add_step(steps_pf.process_assign_verify_mac, name='ASSIGN-VERIFY MAC', kwargs={'assign': True})
    # Write to rommon for MAC & network connectivity
    seq.add_step(steps_pf.pcamap_write_uut, name='WRITE UUT PCAMAP ROMMON',
                 kwargs={'device_instance': 0, 'memory_type': 'vb'})
    return seq


def subseq__write_pcamap(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    pcamap_seq = seq.add_sequence('PCAMAP PROGRAMMING')
    # Show any existing UUT params differences
    pcamap_seq.add_step(steps_pf.pcamap_diff_flash_vs_uut_config, name='DIFF UUT PCAMAP',
                        kwargs={'device_instance': '0'})
    # Load CMPD (Replaces loaded UUT params)
    pcamap_seq.add_step(steps_pf.process_load_cmpd_to_uut, name='LOAD CMPD SPROM',
                        kwargs={'force': False,
                                'cmpd_description': 'SPROM',
                                'uut_type_key': 'MODEL_NUM',
                                'part_number_key': 'MOTHERBOARD_ASSEMBLY_NUM',
                                'part_revision_key': 'MOTHERBOARD_REVISION_NUM',
                                'eco_deviation_key': 'DEVIATION_NUM',
                                'previous_area': 'PCBST'},
                        enabled=False)

    # Programming PCAMAP
    pcamap_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    pcamap_seq.add_step(steps_pf.pcamap_write_uut, name='WRITE UUT PCAMAP TLV',
                        kwargs={'device_instance': 0, 'memory_type': 'tlv', 'reset_tlv': True})

    # Sync PCAMAP for GEN3
    pcamap_seq.add_step(steps_pf.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})

    # Verify CMPD
    # TODO: waiting Trac #5852
    pcamap_seq.add_step(steps_pf.process_verify_cmpd, name='VERIFY CMPD SPROM',
                        kwargs={'force': False,
                                'cmpd_description': 'SPROM',
                                'uut_type_key': 'MODEL_NUM',
                                'part_number_key': 'MOTHERBOARD_ASSEMBLY_NUM',
                                'part_revision_key': 'MOTHERBOARD_REVISION_NUM',
                                'previous_area': 'PCBST',
                                'eco_type': 'VERIFICATION'},
                        enabled=False)

    return seq


def subseq__format_flash(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    format_seq = seq.add_sequence('FLASH FORMAT')
    format_seq.add_step(steps_pf.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX', 'do_primary_mount': False})
    format_seq.add_step(steps_pf.linux_format_flash, name='PARTITION FORMAT DEVICE',
                        kwargs={'disk_type': 'primary', 'force': False, 'ask': True})
    return seq


def subseq__load_images(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    image_load_seq = seq.add_sequence('IMAGE LOADING')
    image_load_seq.add_step(steps_pf.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    image_load_seq.add_step(steps_pf.linux_set_network_interface, name='SET LINUX NET INTF')
    image_load_seq.add_step(steps_pf.load_hw_images, name='LOAD HW IMAGES',
                            kwargs={'master_list': ['btldr', 'linux', 'diag', 'fpga', 'mcu', 'SBC_CFG', 'nic']})
    return seq


def subseq__prog_hw(seq, pf, uut_config, group='STANDARD'):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    log.debug(steps_pf)
    prog_hw_seq = seq.add_sequence('HARDWARE PROGRAMMING {0}'.format(group))
    if group == 'STANDARD':
        image_secboot_seq = prog_hw_seq.add_sequence('DEVICE IMAGE PROGRAMMING SECBOOT', enabled=True)
        image_secboot_seq.add_step(steps_pf.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
        image_secboot_seq.add_step(steps_pf.upgrade_btldr, name='PROG BTLDR')
        image_secboot_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
        image_secboot_seq.add_step(steps_pf.diags_sysinit, name='SYSINIT', kwargs={})
        if uut_config.get('fpga', None):
            image_secboot_seq.add_step(steps_pf.upgrade_fpga, name='PROG FPGA', enabled=True)
            image_secboot_seq.add_step(steps_pf.power_cycle_on, name='POWER ON REBOOT', kwargs={}, group_level=5)
        if uut_config.get('mcu', None):
            image_mcu_seq = prog_hw_seq.add_sequence('DEVICE IMAGE PROGRAMMING MCU', enabled=True)
            image_mcu_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
            image_mcu_seq.add_step(steps_pf.diags_switch_mcu_mode, name='MCU MODE IOS', kwargs={'kkmode': 'IOS'})
            image_mcu_seq.add_step(steps_pf.upgrade_mcu, name='PROG MCU')
            image_mcu_seq.add_step(steps_pf.diags_set_mcu_id, name='MCU ID', kwargs={})
            image_mcu_seq.add_step(steps_pf.diags_update_mcu_settings, name='MCU SETTINGS', kwargs={})
        if uut_config.get('SBC_CFG', None):
            image_sbc_seq = prog_hw_seq.add_sequence('DEVICE IMAGE PROGRAMMING SBC', enabled=True)
            image_sbc_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
            image_sbc_seq.add_step(steps_pf.update_sbc, name='PROG SBC')
        prog_hw_seq.add_step(steps_pf.power_cycle_on, name='POWER CYCLE REBOOT', kwargs={}, group_level=5)
    elif group == 'PREPROCESS':
        pass
    else:
        log.debug("Unrecognized group.")
    return seq


def subseq__diags(seq, pf, container, udd):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    diag_seq = seq.add_sequence('DIAGNOSTIC TESTS')
    diag_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    diag_seq.add_step(steps_pf.diags_sysinit, name='DIAG SYSINIT')
    # Diag Testlist build-out #1
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq, container=container, udd=udd, step_module=steps_pf, category=1, enabled=True)
    diag_seq.add_step(steps_pf.diags_rtc_chkset_test, name='RTC CHK SET TEST', kwargs={'force_set': True})
    diag_seq.add_step(steps_pf.diags_psu_check, name='PSU CHECK', kwargs={})
    diag_seq.add_step(steps_pf.diags_port_status_test, name='PORT STATUS CHECK', kwargs={})
    diag_seq.add_step(steps_pf.diags_stackrac_test, name='STACKRAC TEST', kwargs={})
    diag_seq.add_step(steps_pf.diags_temperature_test, name='DIAG TEMPERATURE TEST', kwargs={'temperature_corner': 'AMBIENT', 'operational_state': 'idle'})
    diag_seq.add_step(steps_pf.diags_vmargin_test, name='DIAG VMARGIN TEST', kwargs={'device_instance': 0, 'margin_level': 'NOMINAL'})
    diag_seq.add_step(steps_pf.diags_record_ecid, name='RECORD ECID', kwargs={})
    diag_seq.add_step(steps_pf.diags_fan_test, name='FAN TEST', kwargs={}, enabled=False)
    diag_seq.add_step(steps_pf.diags_serdeseye_sif_test, name='SERDES EYE SIF TEST', kwargs={})
    diag_seq.add_step(steps_pf.diags_serdeseye_nif_test, name='SERDES EYE NIF TEST', kwargs={})
    # Diag Testlist build-out #2
    diag_seq.add_step(steps_pf.goto_mode, name='MODE DIAG', kwargs={'mode': 'DIAG'})
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq, container=container, udd=udd, step_module=steps_pf, category=None, enabled=True)
    return seq


def subseq__traffic(seq, pf, container, udd):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    traf_seq = seq.add_sequence('TRAFFIC TESTS')
    traf_seq.add_step(steps_pf.goto_mode, name='MODE STARDUST PRETRAF', kwargs={'mode': 'STARDUST'})
    traf_seq.add_step(steps_pf.diags_sysinit, name='DIAG SYSINIT PRETRAF')
    dynamic_sequence_builder.build_traffic_cases_subseq(traffic_seq=traf_seq, container=container, udd=udd, step_module=steps_pf, category=None, enabled=True)
    return seq


def subseq__final(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    final_seq = seq.add_sequence('FINAL', finalization=True)
    seq.add_step(steps_pf.power_off, name='POWER OFF', kwargs={}, group_level=1000)
    final_seq.add_step(steps_pf.clean_up, name='CLEAN UP')
    final_seq.add_step(steps_pf.final, name='END')
