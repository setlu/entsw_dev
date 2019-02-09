"""
------------
Arcade Steps
------------
"""

import apollo.libs.lib as aplib
import c9300

global a


def init():
    global a
    a = c9300.Arcade()
    return aplib.PASS

def final():
    global a
    a = None
    return aplib.PASS

def print_uut_descriptor():
    return a.ud.print_uut_descriptor()

def print_product_manifest():
    return a.ud.print_product_manifest()

def print_uut_config():
    return a.ud.print_uut_config()

def power_cycle_on():
    return a.power.cycle_on()

def add_tst():
    return a.process.add_tst()

def ud_retrieve():
    return a.ud.retrieve()

def mode(**kwargs):
    """
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
    :param kwargs: 
    :return: 
    """
    return aplib.PASS if a.mode_mgr.goto_mode(**kwargs) else aplib.FAIL

def act2_sign_chip(**kwargs):
    return a.act2.sign_chip(**kwargs)
