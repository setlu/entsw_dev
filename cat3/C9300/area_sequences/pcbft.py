"""
-----------
C9300 PCBFT
-----------

NOTE: Some legacy systems use "SYSBI" for this test area.
      The configs.common.cat3.stations provide for an alias of SYSBI to be PCBFT for legacy via switch_sysbi().
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
__area__ = 'PCBFT'
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


def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __area__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER', kwargs={'method': 'boot'})
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

    # MAC Verify Only
    seq.add_step(steps_nyquist.process_assign_verify_mac, name='VERIFY MAC', kwargs={'assign': False})

    # Get RFID Data
    seq.add_step(steps_nyquist.process_get_rfid_db, name='GET RFID TID', enabled=True, kwargs={})

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
    # Load Images
    image_load_seq = seq.add_sequence('IMAGE LOADING', enabled=True)
    image_load_seq.add_step(steps_nyquist.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    image_load_seq.add_step(steps_nyquist.linux_set_network_interface, name='SET LINUX NET INTF')
    image_load_seq.add_step(steps_nyquist.load_hw_images, name='LOAD HW IMAGES',
                            kwargs={'master_list': ['btldr', 'linux', 'diag', 'fpga', 'mcu', 'nic', 'SBC_CFG'], 'force': False}, enabled=False)
    image_load_seq.add_step(steps_nyquist.ios_install_supplemental_images, name='LOAD IOS SUPPLEMENTAL IMAGES', enabled=True)

    # ------------------------------------------------------------------------------------------------------------------
    # Update any Images via stardust
    # SBC update will ALWAYS program; turn off for FST.
    image_seq = seq.add_sequence('DEVICE IMAGE PROGRAMMING', enabled=True)
    image_secboot_seq = image_seq.add_sequence('DEVICE IMAGE PROGRAMMING SECBOOT')
    image_secboot_seq.add_step(steps_nyquist.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    image_secboot_seq.add_step(steps_nyquist.upgrade_btldr, name='PROG BTLDR')
    image_secboot_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    image_secboot_seq.add_step(steps_nyquist.upgrade_fpga, name='PROG FPGA')
    image_secboot_seq.add_step(steps_nyquist.power_cycle_on, name='POWER ON REBOOT', kwargs={'contingent': True}, group_level=5)
    image_mcu_seq = image_seq.add_sequence('DEVICE IMAGE PROGRAMMING MCU')
    image_mcu_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    image_mcu_seq.add_step(steps_nyquist.diags_switch_mcu_mode, name='MCU MODE IOS', kwargs={'kkmode': 'IOS'})
    image_mcu_seq.add_step(steps_nyquist.upgrade_mcu, name='PROG MCU', enabled=False)
    image_nic_seq = image_seq.add_sequence('DEVICE IMAGE PROGRAMMING NIC')
    image_nic_seq.add_step(steps_nyquist.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    image_nic_seq.add_step(steps_nyquist.upgrade_nic, name='PROG NIC', enabled=True)
    image_sbc_seq = image_seq.add_sequence('DEVICE IMAGE PROGRAMMING SBC')
    image_sbc_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    image_sbc_seq.add_step(steps_nyquist.update_sbc, name='PROG SBC', enabled=False)

    # ------------------------------------------------------------------------------------------------------------------
    # Identity Protection Programming
    idpro_seq = seq.add_sequence('IDENTITY PROTECTION')
    idpro_main_subseq = idpro_seq.add_sequence('IDENTITY PROTECTION MAINBOARD', enabled=True)
    idpro_main_subseq.add_step(steps_nyquist.power_cycle_on, name='POWER ON REBOOT', group_level=5)
    idpro_main_subseq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    idpro_main_subseq.add_step(steps_nyquist.diags_sysinit, name='DIAG SYSINIT')
    idpro_main_subseq.add_step(steps_nyquist.x509sudi_sign_certificate, name='X509 SHA1', kwargs={'x509_sudi_hash': 'SHA1'}, enabled=False)
    idpro_main_subseq.add_step(steps_nyquist.act2_sign_chip, name='ACT2', kwargs={'device_instance': 0, 'keytype': 'ACT2-RSA'}, enabled=True)
    idpro_main_subseq.add_step(steps_nyquist.act2_sign_chip, name='ACT2 2099', kwargs={'device_instance': 0, 'keytype': 'ACT2-HARSA'}, enabled=True)
    idpro_main_subseq.add_step(steps_nyquist.x509sudi_sign_certificate, name='X509 SHA256', kwargs={'x509_sudi_hash': 'SHA256', 'keytype': 'ACT2-RSA'}, enabled=True)
    idpro_main_subseq.add_step(steps_nyquist.x509sudi_sign_certificate, name='X509 SHA256 2099', kwargs={'x509_sudi_hash': 'CMCA3', 'keytype': 'ACT2-HARSA'}, enabled=False)

    # Peripherals for special builds only (i.e. proto, etc.).
    if psd.get(area, {}).get('idpro_periphs', False):
        idpro_peripheral_subseq = idpro_seq.add_sequence('IDENTITY PROTECTION PERIPHERALS', enabled=True)
        idpro_peripheral_subseq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
        idpro_peripheral_subseq.add_step(steps_nyquist.diags_sysinit, name='DIAG SYSINIT')
        idpro_peripheral_subseq.add_step(steps_nyquist.quack2_sign_chip, name='QUACK2 2', kwargs={'device_instance': 2}, enabled=True)
        idpro_peripheral_subseq.add_step(steps_nyquist.quack2_sign_chip, name='QUACK2 3', kwargs={'device_instance': 3}, enabled=True)

    # IOS Boot Test and IdPro Check
    idpro_seq.add_step(steps_nyquist.goto_mode, name='MODE IOSE', kwargs={'mode': 'IOSE'})
    idpro_seq.add_step(steps_nyquist.ios_verify_idpro, name='ID PRO VERIFICATION', kwargs={})
    idpro_seq.add_step(steps_nyquist.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    idpro_seq.add_step(steps_nyquist.process_assign_verify_mac, name='VERIFY MAC', kwargs={'assign': False})

    # ------------------------------------------------------------------------------------------------------------------
    # Power Cycle Testing
    seq.add_step(steps_nyquist.power_power_cycle_testing, name='POWER CYCLE TEST')

    # ==================================================================================================================
    # Main Loop Tests
    # ------------------------------------------------------------------------------------------------------------------
    fst_loop_seq = seq.add_sequence('SYSTEM LOOP TESTS', iterations=(aplib.ITERATION_TIME, 30))
    fst_loop_seq.iterations.type = aplib.ITERATION_TIME
    fst_loop_seq.iterations.value = psd.get(area, {}).get('total_loop_time_secs', 1) if psd else 1
    fst_loop_seq.add_step(steps_nyquist.loop_marker, name='FST LOOP', kwargs={'title': 'FST'})

    # ------------------------------------------------------------------------------------------------------------------
    # Diag Testing
    diag_seq = fst_loop_seq.add_sequence('DIAGNOSTIC TESTS', enabled=True)
    diag_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    diag_seq.add_step(steps_nyquist.diags_sysinit, name='SYSINIT')
    diag_seq.add_step(steps_nyquist.diags_rtc_chkset_test, name='RTC CHK SET TEST', kwargs={})
    diag_seq.add_step(steps_nyquist.diags_psu_check, name='PSU CHECK', kwargs={})
    diag_seq.add_step(steps_nyquist.diags_update_mcu_settings, name='MCU SETTINGS', kwargs={})
    diag_seq.add_step(steps_nyquist.diags_temperature_test, name='TEMPERATURE TEST', kwargs={'operational_state': 'diag'})
    diag_seq.add_step(steps_nyquist.diags_vmargin_test, name='VMARGIN TEST', kwargs={'device_instance': 0, 'margin_level': 'NOMINAL'})
    diag_seq.add_step(steps_nyquist.diags_fan_test, name='FAN TEST', kwargs={})
    diag_seq.add_step(steps_nyquist.diags_stackrac_test, name='STACKRAC TEST', kwargs={})
    diag_seq.add_step(steps_nyquist.diags_serdeseye_sif_test, name='SERDES EYE SIF TEST', kwargs={}, enabled=True)
    diag_seq.add_step(steps_nyquist.diags_serdeseye_nif_test, name='SERDES EYE NIF TEST', kwargs={})
    # Diag Testlist build-out
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)

    # ------------------------------------------------------------------------------------------------------------------
    # Traffic Testing
    traf_seq = fst_loop_seq.add_sequence('TRAFFIC TESTS', enabled=True)
    traf_seq.add_step(steps_nyquist.goto_mode, name='MODE STARDUST PRETRAF', kwargs={'mode': 'STARDUST'})
    traf_seq.add_step(steps_nyquist.diags_sysinit, name='DIAG SYSINIT PRETRAF')
    dynamic_sequence_builder.build_traffic_cases_subseq(traffic_seq=traf_seq, container=container, udd=udd, step_module=steps_nyquist, category=None, enabled=True)

    seq.add_step(steps_nyquist.loop_marker, name='FST LOOPS DONE', kwargs={'title': 'FST (Loops completed)', 'close_loop': True})
    # ==================================================================================================================

    # ------------------------------------------------------------------------------------------------------------------
    # Power OFF
    seq.add_step(steps_nyquist.power_off, name='POWER OFF', group_level=1000)

    # Clean up
    final_seq = seq.add_sequence('FINAL', finalization=True)
    final_seq.add_step(steps_nyquist.power_off, name='POWER OFF', kwargs={}, group_level=1000)
    final_seq.add_step(steps_nyquist.clean_up, name='CLEAN UP')
    final_seq.add_step(steps_nyquist.final, name='END')

    return seq