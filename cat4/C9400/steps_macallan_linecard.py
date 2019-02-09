"""
-----------------------
Macallan Linecard Steps
-----------------------
"""
import sys

import apollo.libs.lib as aplib

import c9400
import apollo.scripts.entsw.libs.utils.eng_debug_menu as eng_debug_menu

__title__ = "Macallan Linecard Steps Module"
__version__ = '2.0.0'
__author__ = ['bborel']

global m, edm

thismodule = sys.modules[__name__]


global m, edm

# ----------------------------------------------------------------------------------------------------------------------
# INIT + FINAL
# ----------------------------------------------------------------------------------------------------------------------
def init():
    global m
    m = c9400.MacallanLinecard()
    return aplib.PASS

def final():
    global m
    m = None
    return aplib.PASS

# ----------------------------------------------------------------------------------------------------------------------
# GENERAL MANAGEMENT (UUT Descriptor and Mode Mgr)
# ----------------------------------------------------------------------------------------------------------------------
def ud_print_uut_descriptor():
    return m.ud.print_uut_descriptor()

def ud_print_product_manifest():
    return m.ud.print_product_manifest()

def ud_print_uut_config():
    return m.ud.print_uut_config()

def ud_retrieve():
    return m.ud.retrieve()

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
    return aplib.PASS if m.mode_mgr.goto_mode(mode, **kwargs) else (aplib.FAIL, 'Cannot go to mode: {0}'.format(mode))

# ----------------------------------------------------------------------------------------------------------------------
# Debug
# ----------------------------------------------------------------------------------------------------------------------
def debug_menu():
    global edm
    edm = eng_debug_menu.EngineeringDebugMenu(product_step_module=thismodule, ud=m.ud)
    return edm.run()

def process_manual_select_product():
    """
    :menu: (enable=True, name=LOAD PRODUCT, section=UUT, num=1.1, args={})
    """
    return m.process.manual_select_product()

def process_auto_select_product():
    """
    :menu: (enable=True, name=AUTO-LOAD PRODUCT, section=UUT, num=1.2, args={})
    """
    return m.process.auto_select_product()

def ud_set_puid_keys():
    """
    :menu: (enable=True, name=SET PUID KEYS, section=UUT, num=1.3, args={})
    """
    return m.ud.select_puid_keys()

# ----------------------------------------------------------------------------------------------------------------------
# POWER
# ----------------------------------------------------------------------------------------------------------------------
def power_cycle_on():
    return m.power.cycle_on()

def power_on():
    return m.power.on()

def power_off():
    return m.power.off()

# ----------------------------------------------------------------------------------------------------------------------
# PROCESS
# ----------------------------------------------------------------------------------------------------------------------
def process_add_tst():
    """
    :menu: (enable=False, name=ADD TST, section=Config, num=1.1,  args={'menu_entry': True}) 
    """
    return m.process.add_tst()

def process_area_check(**kwargs):
    """
    :menu: (enable=False, name=AREA CHECK, section=Config, num=1.2,  args={'menu_entry': True})
    """
    return m.process.area_check(**kwargs)

def process_register_genealogy(**kwargs):
    """
    :menu: (enable=True, name=REG GENEALOGY, section=Config, num=2.1,  args={'menu_entry': True})
    """
    return m.process.register_genealogy(**kwargs)

def process_get_genealogy(**kwargs):
    """
    :menu: (enable=True, name=GET GENEALOGY, section=Config, num=2.2,  args={'menu_entry': True})
    """
    return m.process.get_genealogy(**kwargs)

def process_delete_genealogy(**kwargs):
    """
    :menu: (enable=True, name=DEL GENEALOGY, section=Config, num=2.3,  args={'menu_entry': True})
    """
    return m.process.delete_genealogy(**kwargs)

def process_assign_verify_mac(**kwargs):
    """
    :menu: (enable=True, name=MAC VERIFY, section=Config, num=3.1,  args={'include_debug': True})
    :menu: (enable=True, name=MAC FETCH, section=Config, num=3.2,  args={'include_debug': True, 'assign': True})
    """
    return m.process.assign_verify_mac(**kwargs)

def process_verify_quack_label(**kwargs):
    """
    :menu: (enable=False, name=VERIFY QUACK LBL, section=Config, num=4,  args={'menu': True})
    """
    return m.process.verify_quack_label(**kwargs)

def process_load_cmpd_to_uut(**kwargs):
    """
    :menu: (enable=True, name=LOAD CMPD, section=Config, num=5.1,  args={'menu': True})
    """
    return m.process.load_cmpd_to_uut(**kwargs)

def process_fetch_cmpd_fr_db(**kwargs):
    """
    :menu: (enable=True, name=FETCH CMPD, section=Config, num=5.2,  args={'menu': True})
    """
    return m.process.fetch_cmpd_fr_db(**kwargs)

def process_verify_cmpd(**kwargs):
    """
    :menu: (enable=True, name=VERIFY CMPD, section=Config, num=5.3,  args={'menu': True}) 
    """
    return m.process.verify_cmpd(**kwargs)

def process_verify_pidvid(**kwargs):
    """
    :menu: (enable=True, name=VERIFY PIDVID, section=Config, num=5.4,  args={'menu': True})
    """
    return m.process.verify_pidvid(**kwargs)

def process_get_vid(**kwargs):
    """
    :menu: (enable=True, name=GET VID, section=Config, num=5.5,  args={'menu': True})
    """
    return m.process.get_vid(**kwargs)

def process_get_clei_eci(**kwargs):
    """
    :menu: (enable=True, name=GET CLEI/ECI, section=Config, num=5.6,  args={'menu': True})
    """
    return m.process.get_clei_eci(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# HW Upgrades
# ----------------------------------------------------------------------------------------------------------------------
def load_hw_images(**kwargs):
    """
    :menu: (enable=True, name=LOAD HW IMAGES, section=Upgrade, num=1,  args={'menu': True})
    """
    return m.load_hw_images(**kwargs)

def upgrade_btldr(**kwargs):
    """
    :menu: (enable=True, name=UPGRADE BTLDR, section=Upgrade, num=2,  args={'menu': True})
    """
    return m.upgrade_btldr(**kwargs)

def upgrade_fpga(**kwargs):
    """
    :menu: (enable=True, name=UPGRADE FPGA, section=Upgrade, num=3,  args={'menu': True})
    """
    return m.upgrade_fpga(**kwargs)

def update_sbc(**kwargs):
    """
    :menu: (enable=True, name=UPDATE SBC, section=Upgrade, num=5,  args={'menu': True})
    """
    return m.update_sbc(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# LINUX
# ----------------------------------------------------------------------------------------------------------------------
def linux_set_network_interface(**kwargs):
    """
    :menu: (enable=True, name=SET NET INTF, section=Linux, num=1,  args={'menu': True})
    """
    return m.linux.set_network_interface(**kwargs)

def linux_format_flash(**kwargs):
    """
    :menu: (enable=True, name=FORMAT primary, section=Linux, num=2.1, args={'disk_type': 'primary', 'ask': True})
    :menu: (enable=True, name=FORMAT secondary, section=Linux, num=2.2, args={'disk_type': 'secondary', 'ask': True})
    """
    return m.linux.format_flash(**kwargs)

def linux_create_flash_mapping(**kwargs):
    """
    :menu: (enable=True, name=FLASH MAP DIR, section=Linux, num=3,  args={'menu': True})
    """
    return m.linux.create_flash_mapping(**kwargs)

def linux_tftp(**kwargs):
    """
    :menu: (enable=True, name=TFTP get, section=Linux, num=4.1, args={'direction': 'get'})
    :menu: (enable=True, name=TFTP put, section=Linux, num=4.2, args={'direction': 'put'})
    :menu: (enable=True, name=TFTP DIR get, section=Linux, num=4.3, args={'direction': 'get', 'dir_transfer': True})
    """
    return m.linux.tftp(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# PCAMAP
# ----------------------------------------------------------------------------------------------------------------------
def pcamap_read_uut(**kwargs):
    """
    :menu: (enable=True, name=READ PCAMAP, section=PCAMAP, num=1.1,  args={'menu': True, 'smart_update': True})
    """
    return m.pcamap.read_uut(**kwargs)

def pcamap_write_uut(**kwargs):
    """
    :menu: (enable=True, name=WRITE PCAMAP vb, section=PCAMAP, num=2.1,  args={'menu': True, 'memory_type': 'vb'})
    :menu: (enable=True, name=WRITE PCAMAP tlv, section=PCAMAP, num=2.2,  args={'menu': True, 'memory_type': 'tlv'})
    :menu: (enable=True, name=WRITE PCAMAP tlv update, section=PCAMAP, num=2.3,  args={'menu': True, 'memory_type': 'tlv', 'tlv_reset': False})
    """
    return m.pcamap.write_uut(**kwargs)

def pcamap_diff_flash_vs_uut_config(**kwargs):
    """
    :menu: (enable=True, name=DIFF PCAMAP, section=PCAMAP, num=3,  args={})
    """
    return m.pcamap.diff_flash_vs_uut_config(**kwargs)


# ----------------------------------------------------------------------------------------------------------------------
# IDENTITY PROTECTION
# ----------------------------------------------------------------------------------------------------------------------
def act2_sign_chip(**kwargs):
    """
    :menu: (enable=True, name=ACT2 HW, section=Diags, num=1, args={'menu': True})
    """
    return m.act2.sign_chip(**kwargs)

def act2_authenticate(**kwargs):
    """
    :menu: (enable=True, name=ACT2 AUTH, section=Diags, num=2, args={'menu': True})
    """
    return m.act2.authenticate(**kwargs)
