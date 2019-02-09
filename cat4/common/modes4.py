"""
----------------------------------------------------
Transition Functions for the C3K product family
----------------------------------------------------
"""
# Python
# ------
import time
import logging
import re
import sys

# Apollo
# ------
from apollo.engine import apexceptions

# Cisco Library
# -------------
# import here

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils.common_utils import func_details

# Product Specific
# ----------------
import _ios_manifest4 as ios_manifest

__title__ = "C4K Mode Module"
__version__ = '0.2.1'
__author__ = ['bborel', 'gchew', 'krauss', 'jabai']

log = logging.getLogger(__name__)
thismodule = sys.modules[__name__]

MAX_IOS_RETRY = 3


def show_version():
    log.info("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# Product specific transition functions given below.
# DO NOT call these directly; use the ProductMode class instance and the goto_mode() method.
# (See machinemanager.py for more details.)
# ------------------------------------------------------------------------------------------

@func_details
def btldr_to_linux(pp, **kwargs):
    """ Btldr->Linux
    Bootloader to Linux mode.
    1. From Local Device (flash:)
    2. From Network Device (tftp:)
    The method depends on finding an appropriate image.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    flash_device = kwargs.get('flash_device', uut_config.get('flash_device', {'name': 'flash'}))
    linux_image = kwargs.get('linux_image', uut_config.get('linux', {}).get('image', ''))
    device_name = kwargs.get('device_name', flash_device['name'])
    linux_dir = kwargs.get('linux_dir', '')

    log.debug("Linux boot...")
    uut_conn.send('boot {0}:{1}{2}\r'.format(device_name, linux_dir, linux_image), expectphrase=uut_prompts['LINUX'],
                  timeout=120, regex=True)

    return True


@func_details
def linux_to_btldr(pp, **kwargs):
    """ Linux->Btldr
    To exit Linux, we must unmount critical filesystems properly.
    Since we could be exiting from a stale or cold state (i.e. did not get into Linux programmatically via debug),
    need to gather enumeration data, prompt, and mode at root.
    :param pp:
    :param kwargs:
    :return:
    """
    # TODO: Power-cycle vs. reboot?  What is appropriate for Macallan?  (Mike & Janet)
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    # Ensure at root level; since prompt is dynamic based on dir use the prompt pattern and not the actual prompt
    uut_conn.send('cd /\r', expectphrase=uut_prompts['LINUX'], timeout=60, regex=True)
    # Unount ALL devices
    pp.inux.umount_devices(uut_conn, uut_prompts['LINUX'])
    uut_conn.send('reboot\r', expectphrase="SIGKILL", timeout=30)

    # Since MANUAL_BOOT cannot be set from Linux; multiple boot scenarios are possible.
    boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode=['BTLDR', 'IOS', 'IOSE'], boot_msg='(?:Booting)|(?:Initializing)')

    if boot_result:
        mode = pp.mode_mgr.get_current_mode()
        if mode == 'BTLDR':
            uut_conn.send('\r', expectphrase=uut_prompts['BTLDR'], timeout=30, regex=True)
            ret = True
        else:
            # Arrived at some other mode (not bootloader) after reboot; therefore need to change modes.
            # This is a short-cut so that the statemachine doesn't have to recalculate a new path.
            pp.mode_mgr.goto('BTLDR', srcmode=mode)
            # Confirm
            ret = True if pp.mode_mgr.is_mode('BTLDR', refresh=True) else False
    else:
        log.error("Reboot could not find a known mode.")
        ret = False

    return ret


@func_details
def linux_to_stardust(pp, **kwargs):
    """ Linux->Stardust
    Load stardust diags from linux mode.
    Stardust load can only occur locally in two ways:
        1. From a flash file,
        2. From the internal image that is part of Linux kernel but this is always older and has less features
        (used only as last effort).
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    diag_image = uut_config.get('diag', {}).get('image', 'sdX86')

    uut_conn.send('cd /mnt/flash3/user\r', expectphrase=uut_prompts['LINUX'], timeout=30, regex=True)
    uut_conn.send('./{0}\r'.format(diag_image), expectphrase=uut_prompts['STARDUST'], timeout=120, regex=True)

    # TODO: Add capability to filter error messages by way of 1) ignore or 2) fail
    # TODO: Add 'transistion_ignore': {'linux_to_stardust': [(<regex pattern>, <count>), ...]} in product definition
    if 'ERR' in uut_conn.recbuf:
        log.warning("Something bad happened trying to get to Stardust...")
        log.warning("Ignore this for now.")
        # return False   # bypass for now

    return True


@func_details
def stardust_to_linux(pp, **kwargs):
    """ Stardust->Linux
    Exit stardust diags and go back to Linux.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r', expectphrase='.*', timeout=30, regex=True)
    if 'Proceed? [Yes]' in uut_conn.recbuf:
        uut_conn.send('y\r', expectphrase=uut_prompts['LINUX'], timeout=60, regex=True)
    else:
        log.warning("The expected phrase was not seen.")
        log.warning("Proceeding anyway...")

    # Confirm
    ret = True if pp.mode_mgr.is_mode('LINUX', refresh=True) else False
    return ret


@func_details
def stardust_to_diag(pp, **kwargs):
    """ Stardust->Diag
    Enter diag mode from stardust.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('diag\r', expectphrase=uut_prompts['DIAG'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('DIAG', refresh=True) else False
    return ret


@func_details
def diag_to_stardust(pp, **kwargs):
    """ Diag->Stardust
    Exit diags back to stardust.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r', expectphrase=uut_prompts['STARDUST'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('STARDUST', refresh=True) else False

    return ret


@func_details
def stardust_to_btldr(pp, **kwargs):
    """ Stardust->Btldr
    Enter btldr mode from stardust.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('ForcePowerCycle\r', expectphrase='[y/n]', timeout=60)
    uut_conn.send('y\r', expectphrase=uut_prompts['BTLDR'], timeout=120, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('BTLDR', refresh=True) else False
    return ret


@func_details
def stardust_to_traf(pp, **kwargs):
    """ Stardust->Traf
    Enter traffic mode from stardust.
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('traf\r', expectphrase=uut_prompts['TRAF'], timeout=240, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('TRAF', refresh=True) else False
    return ret


@func_details
def traf_to_stardust(pp, **kwargs):
    """ Traf->Stardust
    Exit traffic mode back to stardust
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r', expectphrase=uut_prompts['STARDUST'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('STARDUST', refresh=True) else False
    return ret


@func_details
def stardust_to_symsh(pp, **kwargs):
    """ Stardust->Symsh
    :param pp:
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def diag_to_symsh(pp, **kwargs):
    """ Diag->Symsh
    :param pp:
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def traf_to_symsh(pp, **kwargs):
    """Traf->Symsh
    :param pp:
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def symsh_to_stardust(pp, **kwargs):
    """Symsh->Stardust
    :param pp:
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='STARDUST', **kwargs)


@func_details
def symsh_to_diag(pp, **kwargs):
    """Symsh->Diag
    :param pp:
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='DIAG', **kwargs)


@func_details
def symsh_to_traf(pp, **kwargs):
    """Symsh->Traf
    :param pp:
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='TRAF', **kwargs)


@func_details
def btldr_to_ios(pp, **kwargs):
    """ Btldr->IOS
    Put example of boot up here:
    <paste>
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    # Get params and set defaults where appropriate (source is from mm.uut_config).
    ios_test_pid = kwargs.get('ios_test_pid', uut_config.get('ios_test_pid', 'SGENERIC-0SE'))
    ios_customer_pid = kwargs.get('ios_customer_pid', uut_config.get('ios_customer_pid', None))
    flash_device = kwargs.get('flash_device', uut_config.get('flash_device', {'name': 'flash', 'relative_dir': 'user', 'device_num': 3}))

    # Function specific vars
    device_name = kwargs.get('device_name', flash_device['name'])
    ios_dirs = kwargs.get('ios_dirs', {'local': '', 'remote': ''})

    # Get IOS details
    _, sw_ios = pp.ios.get_ios_image_config(ios_customer_pid=ios_customer_pid, ios_test_pid=ios_test_pid,
                                               ios_manifest_module=ios_manifest)
    ios_image = sw_ios.get('image_name', None)
    if not ios_image:
        log.error("Cannot transistion to IOS since no image is available.")
        return False

    # TODO: tftp AND flash boot capability NEED WORK! (see c3k_mode.py for current solution)

    uut_conn.send('boot {0}:{1}{2}\r'.format(device_name, ios_dirs.get('local', ''), ios_image), expectphrase='.*',
                  timeout=60, regex=True)
    log.debug("Wait for Rommon to start IOS boot...")

    uut_conn.waitfor(['Reading', '[Bb]oot', '[Aa]ttempting'], timeout=140, idle_timeout=120, regex=True)
    log.debug("Reading/Booting/Attempting image...")

    # uut_conn.waitfor(['done', 'Waiting', 'Loading', 'IOSXEBOOT', '[Vv]alidate packages', '[Pp]rogram device'], timeout=300, regex=True, idle_timeout=120)
    # log.debug("Wait for IOS boot...")

    boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode='IOS',
                                               boot_msg='(?:Loading)|(?:Bootable image)|(?:Booting)|(?:Initializing)|(?:cisco Systems)|(?:[Vv]alidate)')
    log.debug("IOS Boot result = {0}".format(boot_result))
    return boot_result


@func_details
def iose_to_btldr(pp, **kwargs):
    """IOS-Enable->Btldr
    To go back to bootlader from IOS, two conditions must be met:
     1. Must be in IOS Enanble mode (state machine will ensure this, has to be properly set up),
     2. Have to ensure auto boot is off (which requires IOS Config mode).
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('config t\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('boot manual\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('exit\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)

    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    uut_conn.send('\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('reload\r', expectphrase='?', timeout=30)
    time.sleep(1)
    # If this changes the config, DO NOT save; just use this as a "one-shot" everytime so as to
    # preserve the config in its current state for any point in the automation process.
    # Any other config changes should be done and saved outside of the transistion mode functions!
    # Note: It seems the MANUAL_BOOT setting remains persistent even when NOT saving from IOS CLI.
    if 'Save? [yes/no]' in uut_conn.recbuf:
        uut_conn.send('n\r', expectphrase='reload?', timeout=30)
        time.sleep(1)
    if 'reload? [confirm]' in uut_conn.recbuf:
        uut_conn.send('y\r', expectphrase='(?i)RELOAD', timeout=30, regex=True)

    # Based on the above config, only bootloader is expected on reboot; no need to look for multiple reboot scenarios.
    result, _ = pp.mode_mgr.wait_for_boot(boot_mode='BTLDR', boot_msg='(?:Booting)|(?:Initializing)')

    # Confirm
    if result:
        ret = True if pp.mode_mgr.is_mode('BTLDR', refresh=True) else False
    else:
        log.debug("BTLDR boot result failed.")
        ret = False
    return ret


@func_details
def ios_to_iose(pp, **kwargs):
    """IOS->IOS-Enable
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOS'], timeout=30, regex=True)
    uut_conn.send('en\r', expectphrase='.*', timeout=30, regex=True)
    time.sleep(2)
    if re.search(uut_prompts['IOSE'], uut_conn.recbuf):
        log.debug("IOS Enable mode successful.")
    elif "Password:" in uut_conn.recbuf:
        log.warning("IOS Enable mode requires a passowrd.")
        log.warning("IOS Enable password should NOT be present in production units!.")
        log.warning("Please check the source of this unit and the production process!.")
        log.warning("Attempting known defaults...")
        loop_count = -1
        found_prompt = False
        patterns = "(?:{0})|(?:Password:)".format(uut_prompts['IOSE'])
        default_passwords = ['c', 'cisco', 'cisco123', 'Cisco']
        while not found_prompt and loop_count < len(default_passwords):
            time.sleep(1)
            uut_conn.send('{0}\r'.format(default_passwords[loop_count]), expectphrase=patterns, timeout=30, regex=True)
            time.sleep(1)
            found_prompt = True if re.search(uut_prompts['IOSE'], uut_conn.recbuf) else False
            loop_count += 1

        if not found_prompt:
            log.error("All IOS Enable default password attempts FAILED.")
            log.error("The password will need to be manually cleared to run this automation.")
            log.error("IOS Enable mode NOT possible.")
            return False
        else:
            log.warning("An IOS Enable default password was successful ({0}).".
                        format(default_passwords[loop_count - 1]))
            log.warning("This password needs to be cleared.")
    else:
        log.error("Unknown response to IOS Enable command.")
        return False

    # Ensure ALL commands complete to the prompt; no "---More---" paging
    # and remove any logging that could interfere with send.
    uut_conn.send('terminal length 0\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('terminal no monitor\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    time.sleep(2)

    return pp.mode_mgr.is_mode('IOSE', refresh=True)


@func_details
def iose_to_ios(pp, **kwargs):
    """IOS-Enable->IOS
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('exit\r', expectphrase='.?', timeout=30, regex=True)
    # Some IOS images will force the "Press RETURN" to start console; some will not.
    # Therefore, just allow time for recbuf update and then send another carriage return by default.
    time.sleep(2)
    uut_conn.send('\r', expectphrase=uut_prompts['IOS'], timeout=30, regex=True)
    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOS', refresh=True) else False
    return ret


@func_details
def iose_to_iosecfg(pp, **kwargs):
    """IOS-Enable->IOS-EnabledConfig
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('config terminal\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOSECFG', refresh=True) else False
    return ret


@func_details
def iosecfg_to_iose(pp, **kwargs):
    """IOS-EnabledConfig->IOS-Enable
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('exit\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOSE', refresh=True) else False
    return ret


@func_details
def iose_to_sysshell(pp, **kwargs):
    """ IOSE->SystemShell

    NOTE: This mode requires a config setting prior to entry.

    Example:
    Switch#config t
    Switch(config)#no loggin console
    Switch(config)#platform shell
    Switch(config)#end
    Switch#request platform software system shell
    Activity within this shell can jeopardize the functioning of the system.
    Are you sure you want to continue? [y/n] y

    2018/05/17 12:16:45 : Shell access was granted to user <anon>; Trace file: ,
    /crashinfo/tracelogs/system_shell_R0-0.23841_0.20180517121645.bin
    **********************************************************************
    Activity within this shell can jeopardize the functioning
    of the system.
    Use this functionality only under supervision of Cisco Support.

    Session will be logged to:
      crashinfo:tracelogs/system_shell_R0-0.23841_0.20180517121645.bin
    **********************************************************************
    Terminal type network' unknown.  Assuming vt100

    [Switch_RP_0:/]$

    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('config terminal\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('no loggin console\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('platform shell\r', expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('end\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('request platform software system shell\r', expectphrase='continue', timeout=30, regex=True)
    uut_conn.send('y\r', expectphrase=uut_prompts['SYSSHELL'], timeout=30, regex=True)
    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('SYSSHELL', refresh=True) else False

    return ret


@func_details
def sysshell_to_iose(pp, **kwargs):
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r', expectphrase=uut_prompts['SYSSHELL'], timeout=30, regex=True)
    uut_conn.send('exit\r', expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    ret = True if pp.mode_mgr.is_mode('IOSE', refresh=True) else False
    return ret


#
# ----------------------------------------------------------------------------------------------------------------------
# Helper functions (INTERNAL ONLY)
#  DO NOT USE these directly!

def __multi_to_symsh(pp, **kwargs):
    """ Multiple possible modes->Symsh
    :param pp:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('symsh\r', expectphrase=uut_prompts['SYMSH'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('SYMSH', refresh=True) else False
    return ret


def __symsh_to_multi(pp, tmode, **kwargs):
    """ Symsh->Multiple possible modes
    Note: The statemachine definition should define which mode to return to based on previous.
    :param pp:
    :param tmode:
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.mode_mgr.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r', expectphrase=uut_prompts[tmode], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode(tmode, refresh=True) else False
    return ret
