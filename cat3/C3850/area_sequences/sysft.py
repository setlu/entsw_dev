"""
-----------
C3850 SYSFT
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
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_edison

__product_line__ = 'C3850'
__desc__ = 'SYSFT'
__title__ = "{0} {1} Sequence Module".format(__product_line__, __desc__)
__version__ = '2.1.0'
__author__ = ['bborel', 'qingywu']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __desc__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER',
                 kwargs={'method': 'boot'})
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
    # -------
    subseq__init(seq)

    # Area Check
    seq.add_step(steps_edison.process_area_check, name='AREACHECK',
                 kwargs={'previous_area': 'SYSASSY'},
                 enabled=True,
                 jump_on_error='FINAL')

    seq.add_step(steps_edison.goto_mode, name='MODE BTLDR INIT', kwargs={'mode': 'BTLDR'})
    seq.add_step(steps_edison.pcamap_read_uut, name='READ UUT INFO')
    seq.add_step(steps_edison.process_verify_cmpd, name='VERIFY CMPD',
                 kwargs={'eco_type': 'VERIFICATION'})
    seq.add_step(steps_edison.process_get_swpid_from_lineid, name='GET IOS PID')
    seq.add_step(steps_edison.ios_get_software_licenses, name='GET SW LICENSES')
    # seq.add_step(steps_edison.process_assign_verify_mac, name='VERIFY MAC')
    seq.add_step(steps_edison.process_populate_dsc_pcamap, name='LOAD DSC PCAMAP',
                 kwargs={'source_testarea': ['SYSINT', 'SYSASSY']})
    seq.add_step(steps_edison.process_verify_clei_eci_label, name='VERIFY CLEI LABEL',
                 kwargs={'source_testarea': ['SYSINT', 'SYSASSY']})
    seq.add_step(steps_edison.ios_download_images, name='PREPARE IOS IMAGES')

    # Bootloader mode
    seq.add_step(steps_edison.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    seq.add_step(steps_edison.upgrade_btldr, name='UPGRADE BTLDR')
    # Program Top Level PID
    seq.add_step(steps_edison.pcamap_program_toplevel_pid, name='PROGRAM TOP LEVEL PID')

    # Linux Mode
    seq.add_step(steps_edison.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX', 'do_primary_mount': True})
    seq.add_step(steps_edison.linux_set_terminal_width, name='SET TERMINAL WIDTH')
    seq.add_step(steps_edison.ios_remove_default_licenses, name='DELETE DEFAULT LICENSES')
    seq.add_step(steps_edison.ios_install_supplemental_images, name='INSTALL SUPP IMAGES')
    seq.add_step(steps_edison.load_hw_images, name='DOWNLOAD DIAG IMAGE', kwargs={'master_list': ['diag']})

    # Verify MCU -----------------
    mcu_vrfy_subseq = seq.add_sequence('VERIFY MCU')
    mcu_vrfy_subseq.add_step(steps_edison.goto_mode, name='MODE STARDUST - VERIFY MCU', kwargs={'mode': 'STARDUST'})
    mcu_vrfy_subseq.add_step(steps_edison.upgrade_mcu, name='VERIFY MCU', kwargs={'verify_only': True})

    # Get PSU data----------------
    seq.add_step(steps_edison.diags_psu_check, name='GET PSU INFO')
    # ----------------------------

    # Quack DSC ------------------
    quack_dsc_subseq = seq.add_sequence('QUACK DATA STACK CABLE',
                                        precondition='userdict.get("dsc_installed")')
    quack_dsc_subseq.add_step(steps_edison.goto_mode, name='MODE STARDUST - QUACK DSC',
                              kwargs={'mode': 'STARDUST'})
    quack_dsc_subseq.add_step(steps_edison.pcamap_write_uut_peripheral, name='WRITE DSC PCAMAP DEV 2',
                              kwargs={'device_instance': '2'})
    quack_dsc_subseq.add_step(steps_edison.pcamap_write_uut_peripheral, name='WRITE DSC PCAMAP DEV 3',
                              kwargs={'device_instance': '3'})
    quack_dsc_subseq.add_step(steps_edison.quack2_sign_chip, name='QUACK DSC 2',
                              kwargs={'device_instance': '2'})
    quack_dsc_subseq.add_step(steps_edison.quack2_sign_chip, name='QUACK DSC 3',
                              kwargs={'device_instance': '3'})
    quack_dsc_subseq.add_step(steps_edison.diags_stackrac_test, name='STACK RAC TEST')
    # ----------------------------

    # Config check ---------------
    cnf_chk_subseq = seq.add_sequence('CONFIG CHECK')
    cnf_chk_subseq.add_step(steps_edison.pcamap_read_uut, name='READ DEV 1', kwargs={'device_instance': 1})
    cnf_chk_subseq.add_step(steps_edison.pcamap_read_uut, name='READ DEV 2', kwargs={'device_instance': 2})
    cnf_chk_subseq.add_step(steps_edison.pcamap_read_uut, name='READ DEV 3', kwargs={'device_instance': 3})
    cnf_chk_subseq.add_step(steps_edison.process_configuration_check, name='CNF CHECK')
    # ----------------------------

    # Add tst data ---------------
    seq.add_step(steps_edison.process_add_tst_data_for_children, name='ADD TST DATA FOR COMPONENTS')
    # ----------------------------

    # Stardust Diag Testing ------
    diag_subseq = seq.add_sequence('DIAGNOSTIC TESTS')
    diag_subseq.add_step(steps_edison.goto_mode, name='MODE STARDUST - DIAGNOSTIC', kwargs={'mode': 'STARDUST'})
    diag_subseq.add_step(steps_edison.diags_sysinit, name='SYSINIT')
    diag_subseq.add_step(steps_edison.diags_rtc_chkset_test, name='RTC CHK SET', kwargs=dict(severity_allowed=400))
    diag_subseq.add_step(steps_edison.diags_serdeseye_sif_test, name='SERDES EYE SIF TEST',
                         precondition='userdict.get("dsc_installed")')
    diag_subseq.add_step(steps_edison.diags_serdeseye_nif_test, name='SERDES EYE NIF TEST')
    diag_subseq.add_step(steps_edison.diags_vmargin_test, name='VOLTAGE TEST',
                         kwargs={'check_only': True, 'margin_level': 'NOMINAL', 'device_instance': 0})
    diag_subseq.add_step(steps_edison.upgrade_fpga, name='UPGRADE FPGA')
    # ----------------------------

    # IOS install ----------------
    ios_install_subseq = seq.add_sequence('IOS INSTALLATION')
    ios_install_subseq.add_step(steps_edison.goto_mode, name='MODE BTLDR - IOS INSTALL', kwargs={'mode': 'BTLDR'})
    ios_install_subseq.add_step(steps_edison.ios_install_main_image, name='INSTALL MAIN IOS IMAGE')
    # ----------------------------

    # License Install/Verify -----
    lic_subseq = seq.add_sequence('LIC INSTALL AND VERIFY')
    lic_subseq.add_step(steps_edison.goto_mode, name='MODE IOSE - LIC', kwargs={'mode': 'IOSE'})
    lic_subseq.add_step(steps_edison.ios_install_licenses, name='INSTALL LIC')
    lic_subseq.add_step(steps_edison.ios_verify_default_licenses, name='VERIFY LIC')
    lic_subseq.add_step(steps_edison.ios_verify_apcount_license, name='VERIFY APCOUNT LIC')
    # ----------------------------

    # Verify IOS status ----------
    ios_verify_subseq = seq.add_sequence('VERIFY IOS STATUS')
    ios_verify_subseq.add_step(steps_edison.goto_mode, name='MODE IOSE - IOS VERIFY STATUS', kwargs={'mode': 'IOSE'})
    ios_verify_subseq.add_step(steps_edison.process_get_hw_modules_from_lineid, name='GET HW MODULES')
    ios_verify_subseq.add_step(steps_edison.ios_verify_idpro, name='ID PRO VERIFY')
    ios_verify_subseq.add_step(steps_edison.ios_verify_log_for_empty_poe_ports, name='VERIFY POE LOGS')
    ios_verify_subseq.add_step(steps_edison.ios_verify_customer_version, name='VERIFY IOS VER')
    ios_verify_subseq.add_step(steps_edison.ios_check_environments, name='IOS ENV')
    # ----------------------------

    # IOS clean up
    seq.add_step(steps_edison.ios_clean_up, name='IOS CLEAN UP')
    # ------------------------------------------------------------------------------------------------------------------

    # Power Cycle and wait for UUT to boot up IOS
    seq.add_step(steps_edison.goto_mode, name='MODE BTLDR - FINAL', kwargs={'mode': 'BTLDR'})
    seq.add_step(steps_edison.pcamap_cleanup_rommon_params, name='UNSET PARAMS',)
    seq.add_step(steps_edison.pcamap_set_manual_boot, name='MANUAL BOOT NO', kwargs={'manual_boot': False})
    seq.add_step(steps_edison.power_cycle_on, name='POWER CYCLE', kwargs={'wait_for_boot': False})
    seq.add_step(steps_edison.ios_waitfor_cfg_dialog_boot, name='WAIT FOR IOS BOOT UP')
    seq.add_step(steps_edison.power_off, name='POWER OFF')

    subseq__final(seq)
    return seq


#=======================================================================================================================
# Library of Common Main Sub-Sequences
#=======================================================================================================================
def subseq__init(seq):
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_edison.init, name='INIT', kwargs={})
    init_seq.add_step(steps_edison.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_edison.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_edison.ud_print_uut_config, name='PRINT UUT CONFIG')
    return seq


def subseq__final(seq):
    final_seq = seq.add_sequence('FINAL', finalization=True)
    # seq.add_step(steps_edison.power_off, name='POWER OFF', kwargs={}, group_level=1000)
    final_seq.add_step(steps_edison.clean_up, name='CLEAN UP')
    final_seq.add_step(steps_edison.final, name='END')
