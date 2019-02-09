"""
-------------
Nyquist Steps
-------------
"""
# Python
# ------
import sys

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.eng_debug_menu as eng_debug_menu
import c9300


__title__ = "Nyquist Steps Module"
__version__ = '2.0.0'
__author__ = ['bborel']

global n, edm

thismodule = sys.modules[__name__]


# ----------------------------------------------------------------------------------------------------------------------
# INIT + FINAL
# ----------------------------------------------------------------------------------------------------------------------
def init():
    global n
    n = c9300.Nyquist()
    return aplib.PASS

def final():
    global n
    n = None
    return aplib.PASS

# ----------------------------------------------------------------------------------------------------------------------
# GENERAL MANAGEMENT (UUT Descriptor and Mode Mgr)
# ----------------------------------------------------------------------------------------------------------------------
def ud_print_uut_descriptor():
    return n.ud.print_uut_descriptor()

def ud_print_product_manifest():
    return n.ud.print_product_manifest()

def ud_print_uut_config():
    return n.ud.print_uut_config()

def ud_retrieve():
    return n.ud.retrieve()

def get_mode():
    """:menu: (enable=True, name=GET MODE,   section=Mode, num=00, args={})"""
    return aplib.PASS if n.mode_mgr.current_mode else (aplib.FAIL, 'Cannot get mode.')

def goto_mode(mode, **kwargs):
    """
    This step has special meaning.
    :menu: (enable=True, name=BTLDR,         section=Mode, num=01, args={'mode': 'BTLDR'})
    :menu: (enable=True, name=LINUX,         section=Mode, num=02, args={'mode': 'LINUX'})
    :menu: (enable=True, name=LINUX-nomount, section=Mode, num=03, args={'mode': 'LINUX', 'do_primary_mount': False})
    :menu: (enable=True, name=LINUX-netboot, section=Mode, num=04, args={'mode': 'LINUX', 'device_name': 'tftp'})
    :menu: (enable=True, name=STARDUST,      section=Mode, num=05, args={'mode': 'STARDUST'})
    :menu: (enable=True, name=DIAG,          section=Mode, num=06, args={'mode': 'DIAG'})
    :menu: (enable=True, name=TRAF,          section=Mode, num=07, args={'mode': 'TRAF'})
    :menu: (enable=True, name=SYMSH,         section=Mode, num=08, args={'mode': 'SYMSH'})
    :menu: (enable=True, name=IOS,           section=Mode, num=09, args={'mode': 'IOS'})
    :menu: (enable=True, name=IOSE,          section=Mode, num=10, args={'mode': 'IOSE'})
    :menu: (enable=True, name=IOSECFG,       section=Mode, num=11, args={'mode': 'IOSECFG'})
    :menu: (enable=True, name=SYSSHELL,      section=Mode, num=12, args={'mode': 'SYSSHELL'})
    """
    return aplib.PASS if n.mode_mgr.goto_mode(mode, **kwargs) else (aplib.FAIL, 'Cannot go to mode: {0}'.format(mode))

def clean_up(**kwargs):
    """:menu: (enable=True, name=CLEAN UP,   section=UUT, num=00, args={})"""
    return n.clean_up()

# ----------------------------------------------------------------------------------------------------------------------
# Debug
# ----------------------------------------------------------------------------------------------------------------------
def debug_menu():
    global edm
    edm = eng_debug_menu.EngineeringDebugMenu(product_step_modules=[thismodule], ud=n.ud)
    return edm.run()

def process_manual_select_product():
    """:menu: (enable=True, name=LOAD PRODUCT, section=UUT, num=1.1, args={})"""
    return n.process.manual_select_product()

def process_auto_select_product():
    """:menu: (enable=True, name=AUTO-LOAD PRODUCT, section=UUT, num=1.2, args={})"""
    return n.process.auto_select_product()

def ud_select_puid_keys(**kwargs):
    """:menu: (enable=True, name=SELECT PUID KEYS, section=UUT, num=1.3, args={})"""
    return n.ud.select_puid_keys(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# POWER
# ----------------------------------------------------------------------------------------------------------------------
def power_cycle_on(**kwargs):
    return n.power.cycle_on(**kwargs)

def power_on(**kwargs):
    return n.power.on(**kwargs)

def power_off(**kwargs):
    return n.power.off(**kwargs)

def power_power_cycle_testing(**kwargs):
    """:menu: (enable=True, name=POWER CYCLE TEST, section=Power, num=1,  args={'menu_entry': True})"""
    return n.power.power_cycle_testing(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# PROCESS (Cesium related)
# ----------------------------------------------------------------------------------------------------------------------
def process_add_tst():
    """:menu: (enable=False, name=ADD TST, section=Config, num=1.1,  args={'menu_entry': True})"""
    return n.process.add_tst()

def process_area_check(**kwargs):
    """:menu: (enable=True, name=AREA CHECK, section=Config, num=1.2,  args={'menu_entry': True})"""
    return n.process.area_check(**kwargs)

def process_register_genealogy(**kwargs):
    """:menu: (enable=True, name=REG GENEALOGY, section=Config, num=2.1,  args={'menu_entry': True})"""
    return n.process.register_genealogy(**kwargs)

def process_get_genealogy(**kwargs):
    """:menu: (enable=True, name=GET GENEALOGY, section=Config, num=2.2,  args={'menu_entry': True})"""
    return n.process.get_genealogy(**kwargs)

def process_delete_genealogy(**kwargs):
    """:menu: (enable=True, name=DEL GENEALOGY, section=Config, num=2.3,  args={'menu_entry': True})"""
    return n.process.delete_genealogy(**kwargs)

def process_assign_verify_mac(**kwargs):
    """:menu: (enable=True, name=MAC VERIFY, section=Config, num=3.1,  args={'include_debug': True})
       :menu: (enable=True, name=MAC FETCH, section=Config, num=3.2,  args={'include_debug': True, 'assign': True})"""
    return n.process.assign_verify_mac(**kwargs)

def process_verify_quack_label(**kwargs):
    """:menu: (enable=True, name=VERIFY QUACK LBL, section=Config, num=4,  args={'menu': True})"""
    return n.process.verify_quack_label(**kwargs)

def process_load_cmpd_to_uut(**kwargs):
    """:menu: (enable=True, name=LOAD CMPD, section=Config, num=5.1,  args={'menu': True})"""
    return n.process.load_cmpd_to_uut(**kwargs)

def process_fetch_cmpd_fr_db(**kwargs):
    """:menu: (enable=True, name=FETCH CMPD, section=Config, num=5.2,  args={'menu': True})"""
    return n.process.fetch_cmpd_fr_db(**kwargs)

def process_verify_cmpd(**kwargs):
    """:menu: (enable=True, name=VERIFY CMPD, section=Config, num=5.3,  args={'menu': True})"""
    return n.process.verify_cmpd(**kwargs)

def process_verify_pidvid(**kwargs):
    """:menu: (enable=True, name=VERIFY PIDVID, section=Config, num=6.1,  args={'menu': True})"""
    return n.process.verify_pidvid(**kwargs)

def process_get_vid(**kwargs):
    """:menu: (enable=True, name=GET VID, section=Config, num=6.2,  args={'menu': True})"""
    return n.process.get_vid(**kwargs)

def process_get_clei_eci(**kwargs):
    """:menu: (enable=True, name=GET CLEI/ECI, section=Config, num=7.1,  args={'menu': True})"""
    return n.process.get_clei_eci(**kwargs)

def process_verify_clei_eci_label(**kwargs):
    """:menu: (enable=True, name=VERIFY CLEI/ECI LABEL, section=Config, num=7.2,  args={'menu': True})"""
    return n.process.verify_clei_eci_label(**kwargs)

def process_analyze_lineid(**kwargs):
    """:menu: (enable=True, name=LINEID ANALYZE, section=Config, num=8.1,  args={'menu': True})"""
    return n.process.analyze_lineid(**kwargs)

def process_get_hw_modules_from_lineid(**kwargs):
    """:menu: (enable=True, name=LINEID GET HW MODULES, section=Config, num=8.2,  args={'menu': True})"""
    return n.process.get_hw_modules_from_lineid(**kwargs)

def process_get_swpid_from_lineid(**kwargs):
    """:menu: (enable=True, name=LINEID GET SW PID, section=Config, num=8.3,  args={'menu': True})"""
    return n.process.get_swpid_from_lineid(**kwargs)

def process_update_cfg_model_num(**kwargs):
    """:menu: (enable=True, name=UPDATE CFG MODEL NUM, section=Config, num=9.1,  args={'menu': True})"""
    return n.process.update_cfg_model_num(**kwargs)

def process_populate_dsc_pcamap(**kwargs):
    """:menu: (enable=True, name=UPDATE DSC PCAMAP, section=Config, num=9.2,  args={'menu': True})"""
    return n.process.populate_dsc_pcamap(**kwargs)

def process_configuration_check(**kwargs):
    """:menu: (enable=True, name=CFG Check, section=Config, num=9.3,  args={'menu': True})"""
    return n.process.configuration_check(**kwargs)

def process_add_tst_data_for_children(**kwargs):
    return n.process.add_tst_data_for_children(**kwargs)

def process_get_rfid_db(**kwargs):
    """:menu: (enable=True, name=GET RFID DB, section=Config, num=10, args={'menu': True})"""
    return n.process.get_rfid_db(**kwargs)

def process_get_serial_num(**kwargs):
    """:menu: (enable=True, name=GET SYSTEM SERIAL NUM, section=Config, num=11, args={'menu': True})"""
    return n.process.get_serial_num(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# HW Upgrades
# ----------------------------------------------------------------------------------------------------------------------
def load_hw_images(**kwargs):
    """:menu: (enable=True, name=LOAD HW IMAGE, section=Upgrade, num=1.1, args={'master_list': None})
       :menu: (enable=True, name=LOAD ALL HW IMAGES, section=Upgrade, num=1.2, args={})"""
    return n.load_hw_images(**kwargs)

def upgrade_btldr(**kwargs):
    """:menu: (enable=True, name=UPGRADE BTLDR, section=Upgrade, num=2,  args={'menu': True})"""
    return n.upgrade_btldr(**kwargs)

def upgrade_fpga(**kwargs):
    """:menu: (enable=True, name=UPGRADE FPGA, section=Upgrade, num=3,  args={'menu': True})"""
    return n.upgrade_fpga(**kwargs)

def upgrade_mcu(**kwargs):
    """:menu: (enable=True, name=UPGRADE MCU, section=Upgrade, num=4,  args={'menu': True})"""
    return n.upgrade_mcu(**kwargs)

def upgrade_nic(**kwargs):
    """:menu: (enable=True, name=UPGRADE NIC, section=Upgrade, num=5,  args={'menu': True})"""
    return n.upgrade_nic(**kwargs)

def upgrade_emmc_fw(**kwargs):
    """:menu: (enable=True, name=UPGRADE EMMC FW, section=Upgrade, num=6,  args={'menu': True})"""
    return n.upgrade_emmc_fw(**kwargs)

def update_sbc(**kwargs):
    """:menu: (enable=True, name=UPDATE SBC, section=Upgrade, num=7,  args={'menu': True})"""
    return n.update_sbc(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# Peripherals
# ----------------------------------------------------------------------------------------------------------------------
def peripheral_manual_select(**kwargs):
    """:menu: (enable=True, name=SELECT PERIPH, section=Config, num=20,  args={'menu': True})"""
    return n.peripheral.manual_select(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# LINUX
# ----------------------------------------------------------------------------------------------------------------------
def linux_set_network_interface(**kwargs):
    """:menu: (enable=True, name=SET NET INTF, section=Linux, num=1,  args={'menu': True})"""
    return n.linux.set_network_interface(**kwargs)

def linux_format_flash(**kwargs):
    """:menu: (enable=True, name=FORMAT primary, section=Linux, num=2.1, args={'disk_type': 'primary', 'ask': True})
       :menu: (enable=True, name=FORMAT secondary, section=Linux, num=2.2, args={'disk_type': 'secondary', 'ask': True})"""
    return n.linux.format_flash(**kwargs)

def linux_create_flash_mapping(**kwargs):
    """:menu: (enable=True, name=FLASH MAP DIR, section=Linux, num=3,  args={'menu': True})"""
    return n.linux.create_flash_mapping(**kwargs)

def linux_tftp(**kwargs):
    """:menu: (enable=True, name=TFTP get, section=Linux, num=4.1, args={'direction': 'get'})
       :menu: (enable=True, name=TFTP put, section=Linux, num=4.2, args={'direction': 'put'})
       :menu: (enable=True, name=TFTP DIR get, section=Linux, num=4.3, args={'direction': 'get', 'dir_transfer': True})"""
    return n.linux.tftp(**kwargs)

def linux_set_terminal_width(**kwargs):
    return n.linux.set_termial_width(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# PCAMAP
# ----------------------------------------------------------------------------------------------------------------------
def pcamap_read_uut(**kwargs):
    """:menu: (enable=True, name=READ PCAMAP, section=PCAMAP, num=1.1,  args={'menu': True, 'smart_update': True})"""
    return n.pcamap.read_uut(**kwargs)

def pcamap_write_uut(**kwargs):
    """:menu: (enable=True, name=WRITE PCAMAP vb, section=PCAMAP, num=2.1,  args={'menu': True, 'memory_type': 'vb'})
       :menu: (enable=True, name=WRITE PCAMAP tlv, section=PCAMAP, num=2.2,  args={'menu': True, 'memory_type': 'tlv'})
       :menu: (enable=True, name=WRITE PCAMAP tlv update, section=PCAMAP, num=2.3,  args={'menu': True, 'memory_type': 'tlv', 'tlv_reset': False})"""
    return n.pcamap.write_uut(**kwargs)

def pcamap_write_uut_peripheral(**kwargs):
    """:menu: (enable=True, name=WRITE PCAMAP periph, section=PCAMAP, num=2.4,  args={'menu': True})"""
    return n.pcamap.write_uut_peripheral(**kwargs)

def pcamap_diff_flash_vs_uut_config(**kwargs):
    """:menu: (enable=True, name=DIFF PCAMAP, section=PCAMAP, num=3,  args={})"""
    return n.pcamap.diff_flash_vs_uut_config(**kwargs)

def pcamap_sync_up(**kwargs):
    """:menu: (enable=True, name=SYNC PCAMAP, section=PCAMAP, num=4,  args={})"""
    return n.pcamap.sync_up(**kwargs)

def pcamap_program_toplevel_pid(**kwargs):
    """:menu: (enable=True, name=PROG TOP PID PCAMAP, section=PCAMAP, num=5,  args={})"""
    return n.pcamap.program_toplevel_pid(**kwargs)

def pcamap_set_manual_boot(**kwargs):
    """:menu: (enable=True, name=SET MANUAL BOOT PCAMAP, section=PCAMAP, num=6,  args={})"""
    return n.pcamap.set_manual_boot(**kwargs)

def pcamap_cleanup_rommon_params(**kwargs):
    """:menu: (enable=True, name=CLEANUP ROMMON PARAMS, section=PCAMAP, num=7,  args={})"""
    return n.pcamap.cleanup_rommon_params(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# IDENTITY PROTECTION
# ----------------------------------------------------------------------------------------------------------------------
def act2_sign_chip(**kwargs):
    """:menu: (enable=True, name=ACT2 SIGN HW, section=IdPro, num=1, args={'menu': True})"""
    return n.act2.sign_chip(**kwargs)

def act2_authenticate(**kwargs):
    """:menu: (enable=True, name=ACT2 AUTH, section=IdPro, num=2, args={'menu': True})"""
    return n.act2.authenticate(**kwargs)

def x509sudi_sign_certificate(**kwargs):
    """:menu: (enable=True, name=X509 SUDI, section=IdPro, num=3, args={'menu': True})"""
    return n.x509sudi.sign_certificate(**kwargs)

def quack2_sign_chip(**kwargs):
    return n.quack2.sign_chip(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# DIAGS
# ----------------------------------------------------------------------------------------------------------------------
def diags_run_testlist_item(**kwargs):
    """:menu: (enable=True, name=RUN TESTLIST, section=DiagTests, num=01, args={'menu': True})"""
    return n.diags.run_testlist_item(**kwargs)

def diags_sysinit(**kwargs):
    """:menu: (enable=True, name=SYSINIT, section=Diags, num=01, args={'menu': True})"""
    return n.diags.sysinit(**kwargs)

def diags_temperature_test(**kwargs):
    """:menu: (enable=True, name=TEMPERATURE TEST, section=Diags, num=03, args={'menu': True})"""
    return n.diags.temperature_test(**kwargs)

def diags_vmargin_test(**kwargs):
    """:menu: (enable=True, name=VMARGIN TEST, section=Diags, num=04, args={'menu': True})"""
    return n.diags.vmargin_test(**kwargs)

def diags_fan_test(**kwargs):
    """:menu: (enable=True, name=FAN TEST, section=Diags, num=05, args={'menu': True})"""
    return n.diags.fan_test(**kwargs)

def diags_switch_mcu_mode(**kwargs):
    """:menu: (enable=True, name=MCU SWITCH MODE, section=Diags, num=06.1, args={'menu': True})"""
    return n.diags.switch_mcu_mode(**kwargs)

def diags_set_mcu_id(**kwargs):
    """:menu: (enable=True, name=MCU SET ID, section=Diags, num=06.2, args={'menu': True})"""
    return n.diags.set_mcu_id(**kwargs)

def diags_update_mcu_settings(**kwargs):
    """:menu: (enable=True, name=MCU UPDATE SETTINGS, section=Upgrade, num=06.3,  args={'menu': True})"""
    return n.diags.update_mcu_settings(**kwargs)

def diags_rtc_chkset_test(**kwargs):
    """:menu: (enable=True, name=RTC CHKSET, section=Diags, num=07, args={'menu': True})"""
    return n.diags.rtc_chkset_test(**kwargs)

def diags_record_ecid(**kwargs):
    """:menu: (enable=True, name=ECID RECORD, section=Diags, num=08, args={'menu': True})"""
    return n.diags.record_ecid(**kwargs)

def diags_port_status_test(**kwargs):
    """:menu: (enable=True, name=PORTSTATUS, section=Diags, num=09, args={'menu': True})"""
    return n.diags.port_status_test(**kwargs)

def diags_stackrac_test(**kwargs):
    """:menu: (enable=True, name=STACKRAC, section=Diags, num=10, args={'menu': True})"""
    return n.diags.stackrac_test(**kwargs)

def diags_serdeseye_sif_test(**kwargs):
    """:menu: (enable=True, name=SERDESEYE SIF, section=Diags, num=11.1, args={'menu': True})"""
    return n.diags.serdeseye_sif_test(**kwargs)

def diags_serdeseye_nif_test(**kwargs):
    """:menu: (enable=True, name=SERDESEYE NIF, section=Diags, num=11.2, args={'menu': True})"""
    return n.diags.serdeseye_nif_test(**kwargs)

def diags_i2c_test(**kwargs):
    """:menu: (enable=True, name=I2C TEST, section=Diags, num=12, args={'menu': True})"""
    return n.diags.i2c_test(**kwargs)

def diags_led_test(**kwargs):
    """:menu: (enable=True, name=LED TEST, section=Diags, num=13, args={'menu': True})"""
    return n.diags.led_test(**kwargs)

def diags_poe_detect_test(**kwargs):
    """:menu: (enable=True, name=POE DETECT TEST, section=Diags, num=14.1, args={'menu': True})"""
    return n.diags.poe_detect_test(**kwargs)

def diags_poe_class_test(**kwargs):
    """:menu: (enable=True, name=POE CLASS TEST, section=Diags, num=14.2, args={'menu': True})"""
    return n.diags.poe_class_test(**kwargs)

def diags_poe_power_test(**kwargs):
    """:menu: (enable=True, name=POE POWER TEST, section=Diags, num=14.3, args={'menu': True})"""
    return n.diags.poe_power_test(**kwargs)

def diags_poe_verify_empty_ports(**kwargs):
    """:menu: (enable=True, name=POE VERIFY EMPTY TEST, section=Diags, num=14.4, args={'menu': True})"""
    return n.diags.poe_verify_empty_ports(**kwargs)

def diags_psu_check(**kwargs):
    """:menu: (enable=True, name=PSU CHECK, section=Diags, num=15, args={'menu': True})"""
    return n.diags.psu_check(**kwargs)

def diags_dopsetvoltage(**kwargs):
    return n.diags.dopsetvoltage(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# TRAFFIC
# ----------------------------------------------------------------------------------------------------------------------
def traffic_fmdiags_traffic_test(**kwargs):
    """:menu: (enable=True, name=SHOW TRAF CFG, section=Traffic, num=1, args={'action': 'showcfg'})
       :menu: (enable=True, name=RUN TRAFFIC, section=Traffic, num=2, args={'action': 'run', 'traffic_cases': None})
       :menu: (enable=True, name=GET CONVERSATION, section=Traffic, num=3, args={'action': 'getc'})"""
    return n.traffic.fmdiags.traffic_test(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# IOS
# ----------------------------------------------------------------------------------------------------------------------
def ios_verify_idpro(**kwargs):
    """:menu: (enable=True, name=IOS VERIFY IDPRO, section=IOS, num=01, args={'menu': True})"""
    return n.ios.verify_idpro(**kwargs)

def ios_download_images(**kwargs):
    """:menu: (enable=True, name=IOS DWNLD IMAGES, section=IOS, num=02, args={'menu': True})"""
    return n.ios.download_images(**kwargs)

def ios_install_main_image(**kwargs):
    """:menu: (enable=True, name=IOS INSTALL MAIN, section=IOS, num=03, args={'menu': True})"""
    return n.ios.install_main_image(**kwargs)

def ios_install_supplemental_images(**kwargs):
    """:menu: (enable=True, name=IOS INSTALL SUPP, section=IOS, num=03.2, args={'menu': True})"""
    return n.ios.install_supplemental_images(**kwargs)

def ios_install_licenses(**kwargs):
    """:menu: (enable=True, name=IOS INSTALL LIC, section=IOS, num=04.1, args={'menu': True})"""
    return n.ios.install_licenses(**kwargs)

def ios_verify_default_licenses(**kwargs):
    """:menu: (enable=True, name=IOS VERIFY LIC, section=IOS, num=04.2, args={'menu': True})"""
    return n.ios.verify_default_licenses(**kwargs)

def ios_verify_apcount_license(**kwargs):
    """:menu: (enable=True, name=IOS VERIFY AP COUNT, section=IOS, num=04.3, args={'menu': True})"""
    return n.ios.verify_apcount_license(**kwargs)

def ios_get_software_licenses(**kwargs):
    """:menu: (enable=True, name=IOS GET SW LIC, section=IOS, num=04.4, args={'menu': True})"""
    return n.ios.get_software_licenses(**kwargs)

def ios_remove_default_licenses(**kwargs):
    """:menu: (enable=True, name=IOS REMOVE DEFAULT LIC, section=IOS, num=04.5, args={'menu': True})"""
    return n.ios.remove_default_licenses(**kwargs)

def ios_verify_log_for_empty_poe_ports(**kwargs):
    """:menu: (enable=True, name=IOS VERIFY POE, section=IOS, num=05, args={'menu': True})"""
    return n.ios.verify_log_for_empty_poe_ports(**kwargs)

def ios_check_environments(**kwargs):
    """:menu: (enable=True, name=IOS CHK ENV, section=IOS, num=06, args={'menu': True})"""
    return n.ios.check_environments(**kwargs)

def ios_verify_customer_version(**kwargs):
    """:menu: (enable=True, name=IOS VERIFY VER, section=IOS, num=07, args={'menu': True})"""
    return n.ios.verify_customer_version(**kwargs)

def ios_clean_up(**kwargs):
    """:menu: (enable=True, name=IOS CLEANUP, section=IOS, num=08, args={'menu': True})"""
    return n.ios.clean_up(**kwargs)

def ios_waitfor_cfg_dialog_boot(**kwargs):
    """:menu: (enable=False, name=IOS WAITFOR CFG-DIALOG, section=IOS, num=09, args={'menu': True})"""
    return n.ios.waitfor_cfg_dialog_boot(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# Catalyst Product level
# ----------------------------------------------------------------------------------------------------------------------
def loop_marker(**kwargs):
    """:menu: (enable=False, name=LOOP MARK, section=Catalyst, num=01, args={'menu': True})"""
    return n.loop_marker(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# Equipment
# ----------------------------------------------------------------------------------------------------------------------
def equip_setup(**kwargs):
    """:menu: (enable=True, name=EQUIP SETUP, section=Equipment, num=01, args={'menu': True})"""
    return n.equip.setup(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# Data Utility/Debug
# ----------------------------------------------------------------------------------------------------------------------
def process_read_sn_data(**kwargs):
    """:menu: (enable=True, name=RD TST SN DATA, section=Data, num=01, args={'menu': True})"""
    return n.process.read_sn_data(**kwargs)

def process_lookup_mac(**kwargs):
    """:menu: (enable=True, name=LOOKUP MAC, section=Data, num=02, args={'menu': True})"""
    return n.process.lookup_mac(**kwargs)

def process_get_sw_configs(**kwargs):
    """:menu: (enable=True, name=GET SW CONFIG, section=Data, num=03, args={'menu': True})"""
    return n.process.get_sw_configs(**kwargs)

def process_get_container_details(**kwargs):
    """:menu: (enable=True, name=GET CONTAINER, section=Data, num=04, args={'menu': True})"""
    return n.process.get_container_details(**kwargs)

def process_get_lineid_data(**kwargs):
    """:menu: (enable=True, name=GET LINEID, section=Data, num=05, args={'menu': True})"""
    return n.process.get_lineid_data(**kwargs)
