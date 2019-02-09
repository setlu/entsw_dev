"""
-------------------------------------------------------------
Transition Functions for the Catalyst Series-2 product family
-------------------------------------------------------------
"""

# Python
# ------
import time
import logging
import re
import os
import sys

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# Cisco Library
# -------------
# import here

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils import common_utils


# Product Specific
# ----------------
import _ios_manifest2 as ios_manifest

__title__ = "Catalyst Series-2 Mode Module"
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
func_details = common_utils.func_details
thismodule = sys.modules[__name__]

MAX_IOS_RETRY = 2


def show_version():
    log.info("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# Product specific transition functions given below.
# DO NOT call these directly; use the ProductMode class instance and the goto_mode() method.
# (See modemanager.py for more details.)
# ------------------------------------------------------------------------------------------

@func_details
def smon1_to_btldr(mm, **kwargs):
    log.warning("Powering up to the SMON state usually means there is a memory problem!")
    mm.uut_conn.send('boot\r', expectphrase=mm.uut_prompt_map['BTLDR'], timeout=60, regex=True)
    mm.get_current_mode()
    return True


@func_details
def btldr_to_btldrg(pp, **kwargs):
    """ Btldr->Golden Btldr
    """
    # Set local copy of modemachine vars
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('nextbootselect golden\r',  expectphrase=uut_prompts['BTLDR'], timeout=30, regex=True)
    uut_conn.send('reset\r',  expectphrase='reset?', timeout=30)
    uut_conn.send('y\r',  expectphrase='.*', timeout=30, regex=True)
    boot_result, _ = pp._mode_mgr.wait_for_boot(boot_mode=['BTLDRG'], boot_msg='(?:Booting)|(?:Initializing)')
    if not boot_result:
        log.error("Reboot could not find a known mode.")
        ret = False

    # Confirm
    ret = True if pp.mode_mgr.is_mode('BTLDRG', refresh=True) else False
    return ret


@func_details
def btldrg_to_btldr(pp, **kwargs):
    """ Golden Btldr --> Btldr
    """
    # Set local copy of modemachine vars
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('nextbootselect upgrade\r',  expectphrase=uut_prompts['BTLDRG'], timeout=30, regex=True)
    uut_conn.send('reset\r',  expectphrase='reset?', timeout=30)
    uut_conn.send('y\r',  expectphrase='.*', timeout=30, regex=True)
    boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')
    if not boot_result:
        log.error("Reboot could not find a known mode.")
        ret = False

    # Confirm
    ret = True if pp.mode_mgr.is_mode('BTLDR', refresh=True) else False
    return ret


@func_details
def btldr_to_linux(pp, **kwargs):
    """ Btldr->Linux
    Bootloader to Linux mode.
    1. From Local Device (flash:)
    2. From Network Device (tftp:)
    The method depends on finding an appropriate image.  That image can be specified explicitly or specified via the
    boot param.  If the image cannot be found and it was not specified explicitly, a "best effort" file search is
    attempted for the given local device.
    If Local Device boot is not possible, a network boot is attempted.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    # Decide how some param defaults will be generated
    flash_device_default = {'name': 'flash', 'relative_dir': '', 'device_num': 3}
    device_mounts_default = {'primary': [(3, '/mnt/flash3')], 'secondary': None, 'tertiary': None}

    # Get params and set defaults where appropriate.
    linux_image = kwargs.get('linux', {}).get('image', uut_config.get('linux', {}).get('image', ''))
    flash_device = kwargs.get('flash_device', uut_config.get('flash_device', flash_device_default))
    disk_enums = kwargs.get('disk_enums', uut_config.get('disk_enums', None))
    device_mounts = kwargs.get('device_mounts', uut_config.get('device_mounts', device_mounts_default))
    uut_mac = None  # Let the UUT autodiscover instead  kwargs.get('MAC_ADDR', '')
    uut_sernum = kwargs.get('MOTHERBOARD_SERIAL_NUM', uut_config.get('MOTHERBOARD_SERIAL_NUM', ''))  # Must be s/n that is associated w/ the MAC
    uut_ip = kwargs.get('uut_ip', uut_config.get('uut_ip', ''))
    server_ip = kwargs.get('server_ip', uut_config.get('server_ip', ''))
    netmask = kwargs.get('netmask', uut_config.get('netmask', ''))

    # Function specific vars
    device_name = kwargs.get('device_name', flash_device['name'])
    linux_dirs = kwargs.get('linux_dirs', {'local': '', 'remote': ''})
    do_primary_mount = kwargs.get('do_primary_mount', True)
    log.debug("do_primary_mount={0}".format(do_primary_mount))

    ret = False
    do_load = True

    # Determine the most robust way to boot the target image IF expected conditions are NOT met.
    pattern = r'(?:vmlinu[xz][\S]*)|(?:bzImage[\S]*)|(?:uImage[\S]*)|(?:quake[\S]*)'
    set_net_load, linux_image, linux_dir = __get_robust_load_details('Linux',
                                                                     pp,
                                                                     uut_conn,
                                                                     uut_prompts['BTLDR'],
                                                                     linux_image,
                                                                     linux_dirs,
                                                                     device_name,
                                                                     pattern,
                                                                     guess_image='uImage64.bin')

    # Set up the network connection via management port for a remote load as the target.
    # Disallow the load if network setup was required and unsuccessful.
    if set_net_load:
        do_load, device_name, linux_dir = __set_uut_network('Linux',
                                                            pp,
                                                            uut_conn,
                                                            uut_prompts['BTLDR'],
                                                            linux_image,
                                                            uut_mac,
                                                            uut_ip,
                                                            netmask,
                                                            server_ip,
                                                            device_name,
                                                            linux_dir,
                                                            uut_sernum)

    # Now issue the commands for the Linux image and path that was determined as the target.
    if do_load:
        # Perform load
        try:
            log.debug("Linux boot...")
            uut_conn.send('boot {0}:{1}{2}\r'.format(device_name, linux_dir, linux_image),
                          expectphrase=".*", timeout=30, regex=True)

            # Quick assessment of boot process
            log.debug("Linux boot load started...")
            time.sleep(3)
            uut_conn.waitfor('(?:Reading)|(?:Loading)|(?:Attempting)|(?:{0})'.format(uut_prompts['BTLDR']), timeout=90, regex=True)
            if "Reading" in uut_conn.recbuf:
                log.debug("Reading image...")
            elif "Attempting" in uut_conn.recbuf:
                log.debug("Attempting image...")
            elif "Loading" in uut_conn.recbuf:
                log.debug("Loading image...")
            elif "Booting" in uut_conn.recbuf:
                log.debug("Booting image...")
            elif "Boot process failed" in uut_conn.recbuf:
                log.debug("Boot process failed...")
                raise Exception("FAILED Linux boot.")

            # Getting here means the image is trying to boot; wait on it.
            log.debug("Linux boot confirm load...")
            uut_conn.waitfor('(Loading)|(Initializing)|(done)', timeout=240, regex=True, idle_timeout=30)

            log.debug("Linux boot load done; wait for launch...")
            boot_interim_msgs = r'(?:Launching Linux Kernel)|' \
                                r'(?:BusyBox)|(?:booting anyway (y/n)?)'
            boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode='LINUX',
                                            boot_msg='(?:Bootable image)|(?:Booting)')

            if boot_result:
                if pp.mode_mgr.is_mode('LINUX', refresh=True):
                    ret = True
                    log.debug("Linux ready.")
            else:
                log.error("Waiting for boot result failed.")

        except apexceptions.TimeoutException, apexceptions.IdleTimeoutException:
            log.error("TIMEOUT waiting for Linux response!")
            ret = False

        if do_primary_mount:
            # Primary mount REQUIRED!
            log.debug("Primary mount is required.")
            if ret:
                # Linux boot up maybe good; however, if primary mounting is required and fails,
                #  the end result will be mode failure.
                #
                # Get disk enumerations
                if not disk_enums:
                    disk_enums = pp.linux.get_disk_enumeration(disk_enums)
                    uut_config['disk_enums'] = disk_enums

                # Mount the primary disk
                ret, _ = pp.linux.mount_disks(device_numbers=[3],
                                              disk_type='primary',
                                              device_mounts=device_mounts,
                                              disk_enums=disk_enums)

                if ret:
                    map_dir = pp.ud.get_flash_mapped_dir()
                    log.info("Flash map = '{0}'".format(map_dir))
                    if map_dir:
                        uut_conn.send('cd {0}\r'.format(map_dir), expectphrase=uut_prompts['LINUX'], timeout=30, regex=True)
                    else:
                        log.warning("Linux mount was good but no 'flash:' dir map was found; remaining in cwd.")
                else:
                    log.error("Linux mount was required but did not complete properly.")

            else:
                log.error("Primary mount will NOT be performed since the Linux kernel mode was not confirmed.")
        else:
            # Primary mount NOT required.
            if ret:
                # The mount is a "don't care" if the filesystem is not present.
                # This is to accomodate a net boot w/ blank flash in order to prepare the device.
                log.info("Primary mount NOT required during Linux load.")
            else:
                log.error("Linux kernel mode was not confirmed.")

    else:
        log.error("Unable to perform load.")

    return ret


@func_details
def linux_to_btldr(pp, **kwargs):
    """ Linux->Btldr
    To exit Linux, we must unmount critical filesystems properly.
    Since we could be exiting from a stale or cold state (i.e. did not get into Linux programmatically via debug),
    need to gather enumeration data, prompt, and mode at root.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    # Ensure at root level; since prompt is dynamic based on dir use the prompt pattern and not the actual prompt
    uut_conn.send('cd /\r',  expectphrase=uut_prompts['LINUX'], timeout=60, regex=True)
    # Update actual prompt
    log.debug(pp.mode_mgr.current_mode)
    # Unount ALL devices
    pp.linux.umount_devices()
    uut_conn.send('reboot\r',  expectphrase="SIGKILL", timeout=30)

    # Since MANUAL_BOOT cannot be set from Linux; multiple boot scenarios are possible.
    boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode=['BTLDR', 'IOS', 'IOSE'], boot_msg='(?:Booting)|(?:Initializing)')

    if boot_result:
        if pp.mode_mgr.current_mode == 'BTLDR':
            uut_conn.send('\r',  expectphrase=uut_prompts['BTLDR'], timeout=30, regex=True)
            ret = True
        else:
            # Arrived at some other mode (not bootloader) after reboot; therefore need to change modes.
            # This is a short-cut so that the statemachine doesn't have to recalculate a new path.
            pp.mode_mgr.goto_mode('BTLDR', srcmode=mode)
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
    If the requested diag image is not available, the most recent stardust image available on flash will be used or
    the internal mechanism will be invoked.  If strict_image = True then the load will fail if the explicit image is
    not found on flash; a best effort attempt will not be made.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    # Decide how some param defaults will be generated
    flash_device_default = {'name': 'flash', 'relative_dir': '', 'device_num': 3}
    device_mounts_default = {'primary': [(3, '/mnt/flash3')], 'secondary': None, 'tertiary': None}
    diag_default = uut_config.get('diag', {'image': 'stardust', 'rev': ''})

    # UUT config data
    flash_device = kwargs.get('flash_device', uut_config.get('flash_device', flash_device_default))
    device_mounts = kwargs.get('device_mounts', uut_config.get('device_mounts', device_mounts_default))
    diag = kwargs.get('diag', diag_default)
    diag_image = diag.get('image', diag.get('image', ''))
    disk_enums = kwargs.get('disk_enums', uut_config.get('disk_enums', None))
    diag_builtin = kwargs.get('diag_builtin', True)

    # Function specific vars
    strict_image = kwargs.get('strict_image', False)

    target_dir = os.path.join(device_mounts['primary'][0][1], flash_device['relative_dir'])
    if not pp.linux.cd(target_dir):
        log.warning("Cannot locate the diags directory.")
        log.warning("Checking primary mount...")
        # Confirm disk enumerations and set the config
        disk_enums = pp.linux.get_disk_enumeration(disk_enums)
        uut_config['disk_enums'] = disk_enums
        # Mount the primary disk
        ret, _ = pp.linux.mount_disks(device_numbers=[3],
                                      disk_type='primary',
                                      device_mounts=device_mounts,
                                      disk_enums=disk_enums)
        if ret:
            log.debug("Primary mount is good.")
            # Try again now that the mount appears good.
            if not pp.linux.cd(target_dir):
                log.error("Although the mount was good, the expected path was still not found.")
                log.error("Check the filesystem.")
                return False
        else:
            log.error("Unable to mount the Linux image.")
            log.error("Please confirm 1) flash was properly configured, "
                      "2) UUT defines are correctly loaded, and "
                      "3) UUT can be properly mounted.")
            return False
    else:
        log.debug("Already in correct dir location.")

    if diag_builtin:
        log.debug("The diag image is built-in...")
        ffiles = []
    else:
        log.debug("Get available diag images...")
        ffiles = pp.linux.get_device_files(sub_dir='',
                                           file_filter='stardust.*?',
                                           attrib_flags='-')
    if ffiles:
        if diag_image in ffiles:
            log.debug("Diag image (explicitly given) was found = {0}".format(diag_image))
            final_diag_image = './{0}'.format(diag_image)
        else:
            log.debug("Explicit diag image NOT found! ({0})".format(diag_image))
            if not strict_image:
                log.debug("Using the most recent image available: ({0})".format(ffiles[0]))
                final_diag_image = './{0}'.format(ffiles[0])
    else:
        log.warning("No diag files on device!")
        if not strict_image:
            log.warning("Using the built-in diags.")
            final_diag_image = 'stardust'

    # Perform load based on final image
    if final_diag_image:
        uut_conn.send('{0}\r'.format(final_diag_image),  expectphrase=uut_prompts['STARDUST'], timeout=120, regex=True)
        # Confirm
        ret = True if pp.mode_mgr.is_mode('STARDUST', refresh=True) else False
    else:
        log.error("Cannot complete diag load.")
        ret = False

    return ret


@func_details
def stardust_to_linux(pp, **kwargs):
    """ Stardust->Linux
    Exit stardust diags and go back to Linux
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r',  expectphrase='Proceed? [Yes]', timeout=30)
    uut_conn.send('y\r',  expectphrase=uut_prompts['LINUX'], timeout=60, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('LINUX', refresh=True) else False
    return ret


@func_details
def stardust_to_diag(pp, **kwargs):
    """ Stardust->Diag
    Enter diag mode from stardust.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('diag\r',  expectphrase=uut_prompts['DIAG'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('DIAG', refresh=True) else False
    return ret


@func_details
def diag_to_stardust(pp, **kwargs):
    """ Diag->Stardust
    Exit diags back to stardust.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r',  expectphrase=uut_prompts['STARDUST'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('STARDUST', refresh=True) else False
    return ret


@func_details
def stardust_to_traf(pp, **kwargs):
    """ Stardust->Traf
    Enter traffic mode from stardust.
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('traf\r',  expectphrase=uut_prompts['TRAF'], timeout=240, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('TRAF', refresh=True) else False
    return ret


@func_details
def traf_to_stardust(pp, **kwargs):
    """ Traf->Stardust
    Exit traffic mode back to stardust
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r',  expectphrase=uut_prompts['STARDUST'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('STARDUST', refresh=True) else False
    return ret


@func_details
def stardust_to_symsh(pp, **kwargs):
    """ Stardust->Symsh
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def diag_to_symsh(pp, **kwargs):
    """ Diag->Symsh
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def traf_to_symsh(pp, **kwargs):
    """Traf->Symsh
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __multi_to_symsh(pp=pp, **kwargs)


@func_details
def symsh_to_stardust(pp, **kwargs):
    """Symsh->Stardust
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='STARDUST', **kwargs)


@func_details
def symsh_to_diag(pp, **kwargs):
    """Symsh->Diag
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='DIAG', **kwargs)


@func_details
def symsh_to_traf(pp, **kwargs):
    """Symsh->Traf
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    return __symsh_to_multi(pp=pp, tmode='TRAF', **kwargs)


@func_details
def btldr_to_ios(pp, **kwargs):
    """ Btldr->IOS

    GEN3 Example1
    -------------
    switch: boot tftp://10.1.1.1/IOS/cat9k_iosxe.16.05.01a.prd3.SPA.bin
    Attempting to boot from [tftp://10.1.1.1/IOS/cat9k_iosxe.16.05.01a.prd3.SPA.bin]

                MAC_ADDR: 04:6C:9D:1E:4D:80
              ETHER_PORT: 0
              IP_ADDRESS: 10.1.0.35
          IP_SUBNET_MASK: 255.255.0.0
         DEFAULT_GATEWAY: 10.1.1.1
             TFTP_SERVER: 10.1.1.1
               TFTP_FILE: IOS/cat9k_iosxe.16.05.01a.prd3.SPA.bin
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!...!!!!!!!!!!!!!!!!!!!!!!!!

    Loading image in Verbose mode: 1

    Image Base is: 0x6ACBE018
    Image Size is: 0x1E51022E
    Package header rev 3 structure detected
    Package type:30000, flags:0x0
    IsoSize = 484372480
    Parsing package TLV info:
    000: 000000090000001D4B45595F544C565F -         KEY_TLV_
    010: 5041434B4147455F434F4D5041544942 - PACKAGE_COMPATIB
    020: 494C495459000000000000090000000B - ILITY
    030: 4652555F52505F545950450000000009 - FRU_RP_TYPE
    040: 000000184B45595F544C565F5041434B -     KEY_TLV_PACK
    050: 4147455F424F4F544152434800000009 - AGE_BOOTARCH
    060: 0000000E415243485F693638365F5459 -     ARCH_i686_TY
    070: 5045000000000009000000144B45595F - PE          KEY_
    080: 544C565F424F4152445F434F4D504154 - TLV_BOARD_COMPAT
    090: 0000000900000010424F4152445F6361 -         BOARD_ca
    0A0: 74396B5F545950450000000900000018 - t9k_TYPE
    0B0: 4B45595F544C565F43525950544F5F4B - KEY_TLV_CRYPTO_K
    0C0: 4559535452494E47000000090000000A - EYSTRING

    TLV: T=9, L=29, V=KEY_TLV_PACKAGE_COMPATIBILITY
    TLV: T=9, L=11, V=FRU_RP_TYPE
    TLV: T=9, L=24, V=KEY_TLV_PACKAGE_BOOTARCH
    TLV: T=9, L=14, V=ARCH_i686_TYPE
    TLV: T=9, L=20, V=KEY_TLV_BOARD_COMPAT
    TLV: T=9, L=16, V=BOARD_cat9k_TYPE
    TLV: T=9, L=24, V=KEY_TLV_CRYPTO_KEYSTRING
    TLV: T=9, L=10, V=EnCrYpTiOn
    TLV: T=9, L=11, V=CW_BEGIN=$$
    TLV: T=9, L=17, V=CW_FAMILY=$cat9k$
    TLV: T=9, L=45, V=CW_IMAGE=$cat9k_iosxe.16.05.01a.prd3.SPA.bin$
    TLV: T=9, L=20, V=CW_VERSION=$16.5.1a$
    TLV: T=9, L=52, V=CW_DESCRIPTION=$Cisco IOS Software, IOS-XE Software$
    TLV: T=9, L=9, V=CW_END=$$
    Found DIGISIGN TLV type 12 length = 392
    RSA Self Test Passed

    Expected hash:
    DDAF35A193617ABACC417349AE204131
    12E6FA4E89A97EA20A9EEEE64B55D39A
    2192992A274FC1A836BA3C23A3FEEBBD
    454D4423643CE80E2A9AC94FA54CA49F

    Obtained hash:
    DDAF35A193617ABACC417349AE204131
    12E6FA4E89A97EA20A9EEEE64B55D39A
    2192992A274FC1A836BA3C23A3FEEBBD
    454D4423643CE80E2A9AC94FA54CA49F
    Sha512 Self Test Passed
    Found package arch type ARCH_i686_TYPE
    Found package FRU type FRU_RP_TYPE
    Calculating SHA-1 hash...Validate package: SHA-1 hash:
            calculated 6D0BC190:1972D322:52EF2E17:1375A59A:DC2E1B9F
            expected   6D0BC190:1972D322:52EF2E17:1375A59A:DC2E1B9F

    RSA Signed RELEASE Image Signature Verification Successful.
    Booting image with bootparam="root=/dev/ram rw console=tty0,9600n8 max_loop=64 pciehp.pciehp_force bdinfo_start=0xA7A60018
             bdinfo_size=0x35C34 rd_start=0x8A044000 rd_size=0x13B5126 pkg_start=0x4DECF000 pkg_size=0x1CDEF000
             SR_BOOT=tftp://10.1.1.1/IOS/cat9k_iosxe.16.05.01a.prd3.SPA.bin"
    %IOSXEBOOT-Thu-###: (rp/0): Sep 14 17:12:36 Universal 2017 PLEASE DO NOT POWER CYCLE ### BOOT LOADER UPGRADING 4

    Front-end Microcode IMG MGR: found 4 microcode images for 1 device.
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_0
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_1
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_2
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_3

    Front-end Microcode IMG MGR: Preparing to program device microcode...
    Front-end Microcode IMG MGR: Preparing to program device[0]...594412 bytes.
    Front-end Microcode IMG MGR: Programming device 0...rwRrrrrrrw..0%........................................................
    %IOSXEBOOT-loader-boot: (rp/0): upgrade successful 4
    .......................................................10%
    ..............................................................................................................20%
    ...........................................................................................................30%
    ..............................................................................................................40%
    ..............................................................................................................50%
    ...............................................................................................................60%
    ..............................................................................................................70%
    ..............................................................................................................80%
    ..............................................................................................................90%
    ..............................................................................................................100%
    Front-end Microcode IMG MGR: Preparing to program device[0]...393050 bytes.
    Front-end Microcode IMG MGR: Programming device 0...rrrrrrw..0%
    .........................................................................10%
    ........................................................................20%
    ..........................................................................30%
    ........................................................................40%
    ........................................................................50%
    ..........................................................................60%
    .........................................................................70%
    ..........................................................................80%
    ........................................................................90%
    ........................................................................100%
    Front-end Microcode IMG MGR: Preparing to program device[0]...25186 bytes.
    Front-end Microcode IMG MGR: Programming device 0...rrrrrrw..0%....10%....20%......30%...40%......50%....60%......70%...80%......90%....100%w

    Front-end Microc
    Initializing Hardware...

    Initializing Hardware...
    Disable Boot timer
    Disable flash-upgrade timer
    Getting the card type
    Board type is set to 10

    Checking for PCIe device presence...done

    Warning: monitor nvram area is corrupt ... using default values
    SpdSdram: memory=8589934592

    System Bootstrap, Version 1.26SB, RELEASE SOFTWARE (P)
    Compiled Wed 03/08/2017 14:30:36.28 by rel

    Current image running:
    Golden Rommon Image!
    RstCode: 0x00100244

    Last reset cause: SecureBootFail
    C9300-48U            platform with 8388608 Kbytes of main memory


    Example2
    --------
    switch: boot tftp://10.1.1.1/NG3K_IOS/cat9k_iosxe.16.06.01.SPA.bin
    Attempting to boot from [tftp://10.1.1.1/NG3K_IOS/cat9k_iosxe.16.06.01.SPA.bin]

                MAC_ADDR: 04:6C:9D:1E:4D:80
              ETHER_PORT: 0
              IP_ADDRESS: 10.1.0.35
          IP_SUBNET_MASK: 255.255.0.0
         DEFAULT_GATEWAY: 10.1.1.1
             TFTP_SERVER: 10.1.1.1
               TFTP_FILE: /NG3K_IOS/cat9k_iosxe.16.06.01.SPA.bin
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    %IOSXEBOOT-Thu-###: (rp/0): Sep 14 20:17:28 Universal 2017 PLEASE DO NOT POWER CYCLE ### BOOT LOADER UPGRADING 4
    MM [1] MCU version 105 sw ver 102
    MM [2] MCU version 105 sw ver 102

    Front-end Microcode IMG MGR: found 4 microcode images for 1 device.
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_0 mismatch: 0
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_1 mismatch: 1
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_2 mismatch: 1
    Image for front-end 0: /tmp/microcode_update/front_end/fe_type_6_3 mismatch: 0

    Front-end Microcode IMG MGR: Preparing to program device microcode...
    Front-end Microcode IMG MGR: Preparing to program device[0], index=0 ...594412 bytes.... Skipped[0].
    Front-end Microcode IMG MGR: Preparing to program device[0], index=1 ...395430 bytes.
    Front-end Microcode IMG MGR: Programming device 0...rwRrrrrrrw..0%........................................................
    %IOSXEBOOT-loader-boot: (rp/0): upgrade successful 4
    .................
    10%..........................................................................
    20%........................................................................
    30%..........................................................................
    40%..........................................................................
    50%........................................................................
    60%..........................................................................
    70%.........................................................................
    80%..........................................................................
    90%..........................................................................100%
    Front-end Microcode IMG MGR: Preparing to program device[0], index=2 ...25186 bytes.
    Front-end Microcode IMG MGR: Programming device 0...rrrrrrw..0%....10%....20%......30%...40%......50%....60%......70%...80%......90%....100%wRr!
    Front-end Microcode IMG MGR: Microcode programming complete for device 0.
    Front-end Microcode IMG MGR: Preparing to program device[0], index=3 ...86370 bytes.... Skipped[3].
    Front-end Microcode IMG MGR: Microcode programming complete in 291 seconds

    Waiting for 120 seconds for other switches to boot
    #######################################################################################################################
    Switch number is 1

                  Restricted Rights Legend

    Use, duplication, or disclosure by the Government is
    subject to restrictions as set forth in subparagraph
    (c) of the Commercial Computer Software - Restricted
    Rights clause at FAR sec. 52.227-19 and subparagraph
    (c) (1) (ii) of the Rights in Technical Data and Computer
    Software clause at DFARS sec. 252.227-7013.

               cisco Systems, Inc.
               170 West Tasman Drive
               San Jose, California 95134-1706

    Cisco IOS Software [Everest], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 16.6.1, RELEASE SOFTWARE (fc2)
    Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2017 by Cisco Systems, Inc.
    Compiled Sat 22-Jul-17 05:51 by mcpre

    Cisco IOS-XE software, Copyright (c) 2005-2017 by cisco Systems, Inc.
    All rights reserved.  Certain components of Cisco IOS-XE software are
    licensed under the GNU General Public License ("GPL") Version 2.0.  The
    software code licensed under GPL Version 2.0 is free software that comes
    with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
    GPL code under the terms of GPL Version 2.0.  For more details, see the
    documentation or "License Notice" file accompanying the IOS-XE software,
    or the applicable URL provided on the flyer accompanying the IOS-XE
    software.

    % failed to initialize nvram
    % attempting to recover from backup
    % failed to initialize backup nvram

    FIPS: Flash Key Check : Begin
    FIPS: Flash Key Check : End, Not Found, FIPS Mode Not Enabled

    This product contains cryptographic features and is subject to United
    States and local country laws governing import, export, transfer and
    use. Delivery of Cisco cryptographic products does not imply
    third-party authority to import, export, distribute or use encryption.
    Importers, exporters, distributors and users are responsible for
    compliance with U.S. and local country laws. By using this product you
    agree to comply with applicable laws and regulations. If you are unable
    to comply with U.S. and local laws, return this product immediately.

    A summary of U.S. laws governing Cisco cryptographic products may be found at:
    http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

    If you require further assistance please contact us by sending email to
    export@cisco.com.

    cisco C9300-48U (X86) processor with 868521K/6147K bytes of memory.
    Processor board ID FCW2112G008
    2048K bytes of non-volatile configuration memory.
    8388608K bytes of physical memory.
    1638400K bytes of Crash Files at crashinfo:.
    11264000K bytes of Flash at flash:.
    0K bytes of WebUI ODM Files at webui:.

    Base Ethernet MAC Address          : 04:6c:9d:1e:4d:80
    Motherboard Assembly Number        : 73-17957-06
    Motherboard Serial Number          : FOC21094MU1
    Model Revision Number              : PP
    Motherboard Revision Number        : 05
    Model Number                       : C9300-48U
    System Serial Number               : FCW2112G008

    %INIT: waited 0 seconds for NVRAM to be available

    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map
    uut_config = pp.ud.uut_config

    # Get params and set defaults where appropriate (source is from mm.uut_config).
    # If an IOS Customer PID is present in uut_config then add the packages.conf as a boot file.
    ios_test_pid = kwargs.get('ios_test_pid', uut_config.get('ios_test_pid', 'SGENERIC-0SE'))
    ios_customer_pid = kwargs.get('ios_customer_pid', uut_config.get('ios_customer_pid', None))
    _, sw_ios = pp.ios.get_ios_image_config(ios_customer_pid=ios_customer_pid, ios_test_pid=ios_test_pid, ios_manifest_module=ios_manifest)
    ios_image = sw_ios.get('image_name', 'ios.bin')
    ios_image = [ios_image, 'packages.conf'] if ios_customer_pid else [ios_image]

    default_flash_device = {'name': 'flash', 'relative_dir': 'user', 'device_num': 3}
    flash_device = kwargs.get('flash_device', uut_config.get('flash_device', default_flash_device))
    uut_mac = None  # Let the UUT autodiscover instead kwargs.get('MAC_ADDR', '')
    uut_ip = kwargs.get('uut_ip', uut_config.get('uut_ip', ''))
    server_ip  = kwargs.get('server_ip', uut_config.get('server_ip', ''))
    netmask = kwargs.get('netmask',  uut_config.get('netmask', ''))

    # Function specific vars
    device_name = kwargs.get('device_name', flash_device['name'])
    ios_dirs = kwargs.get('ios_dirs', {'local': '', 'remote': ''})

    ret = False
    do_load = True

    # Determine the most robust way to boot the target image IF expected conditions are NOT met.
    pattern = r'(?:cat[\S]*.bin)|(?:packages.conf)|(?:ios[\S]*.bin)'
    set_net_load, ios_image, ios_dir = __get_robust_load_details('IOS',
                                                                 pp,
                                                                 uut_conn,
                                                                 uut_prompts['BTLDR'],
                                                                 ios_image, ios_dirs,
                                                                 device_name,
                                                                 pattern,
                                                                 guess_image='cat3k_universalk9.bin')
    # Set up the network connection via management port for a remote load as the target.
    # Disallow the load if network setup was required and unsuccessful.
    if set_net_load:
        do_load, device_name, ios_dir = __set_uut_network('IOS',
                                                          pp,
                                                          uut_conn,
                                                          uut_prompts['BTLDR'],
                                                          ios_image,
                                                          uut_mac,
                                                          uut_ip,
                                                          netmask,
                                                          server_ip,
                                                          device_name,
                                                          ios_dir)
    # Now issue the commands for the IOS image and path that was determined as the target.
    if do_load:
        # Perform load
        try:

            boot_interim_msgs = r'(?:Launching Linux Kernel)|' \
                                r'(?:All packages are Digitally Signed)|' \
                                r'(?:Starting System Services)|' \
                                r'(?:Cisco IOS)'

            # Some units have an IOS anomaly whereby the console stops sending boot data and the unit appears locked up.
            # Char echo still occurs on the console line but no UUT response.  Failure rate = 1:300.
            # This retry loop is a temporary measure and should be set to MAX_IOS_RETRY = 0 once the IOS issue
            # is resolved.
            retry_count = 0
            boot_result = False
            while retry_count <= MAX_IOS_RETRY and not boot_result and not aplib.need_to_abort():

                uut_conn.clear_recbuf()
                if boot_result:
                    break
                elif retry_count > 0:
                    log.warning("POWER CYCLE for IOS boot retry!")
                    uut_conn.power_cycle(10)
                    log.debug("Power cycle complete.")
                    btldr_result, _ = pp.mode_mgr.wait_for_boot(boot_mode='BTLDR', boot_msg='(?:Booting)|(?:Initializing)')
                    if not btldr_result:
                        log.error("The POWER CYCLE did NOT complete properly; FATAL ERROR.")
                        raise StandardError("Power cycle + boot has fatal error.")
                #
                # IOS Boot
                retry_count += 1
                log.info("IOS Boot attempt = {0}".format(retry_count))
                uut_conn.send('\r', expectphrase=uut_prompts['BTLDR'], timeout=60, regex=True)
                time.sleep(2.0)

                common_utils.network_availability('acquire')
                uut_conn.send('boot {0}:{1}{2}\r'.format(device_name, ios_dir, ios_image), expectphrase='.*', timeout=60, regex=True)
                log.debug("Wait for Rommon to start IOS boot...")

                try:
                    uut_conn.waitfor(['Reading', '[Bb]oot', '[Aa]ttempting'], timeout=140, idle_timeout=120, regex=True)
                    log.debug("Reading/Booting/Attempting image...")

                    uut_conn.waitfor(['done', '[Ww]aiting', 'Loading', 'IOSXEBOOT', '[Vv]alidate packages', '[Pp]rogram device'], timeout=600, regex=True, idle_timeout=120)
                    log.debug("Wait for IOS boot...")
                    time.sleep(1.0)
                    common_utils.network_availability('release')

                except apexceptions.IdleTimeoutException as e:
                    log.error(e)
                    log.warning("IDLETIMEOUT waiting for IOS to load!")
                    log.warning("Possible causes: 1) network bandwidth exceeded, 2) file access issue, 3) faulty connection.")
                    log.warning("Retrying...")
                    continue

                boot_result, _ = pp.mode_mgr.wait_for_boot(boot_mode='IOS',
                                                  boot_msg='(?:Loading)|(?:Bootable image)|(?:Booting)|(?:Initializing)|(?:[Cc]isco Systems)|(?:[Vv]alidate)',
                                                  boot_interim_msgs=boot_interim_msgs)
                # endwhile loop ---

            if boot_result:
                log.debug("Confirming IOS...")
                if pp.mode_mgr.is_mode('IOS', refresh=True):
                    ret = True
                    log.info("IOS ready.")
            else:
                log.error("IOS is NOT ready.")

        except StandardError as e:
            log.error("STANDARDERROR Exception...")
            log.error(e.message)
            ret = False
        except apexceptions.IdleTimeoutException as e:
            log.error("IDLETIMEOUT waiting for IOS response!")
            log.error(e.message)
            ret = False
        except apexceptions.TimeoutException as e:
            log.error("TIMEOUT waiting for IOS response!")
            log.error(e.message)
            ret = False
        except (apexceptions.AbortException, apexceptions.ScriptAbortException) as e:
            log.exception("Aborting...")
        except Exception as e:
            log.error(e)
            raise Exception(e.message)
        finally:
            common_utils.network_availability('release')

    else:
        log.error("Unable to perform load.")

    return ret


@func_details
def iose_to_btldr(pp, **kwargs):
    """IOS-Enable->Btldr
    To go back to bootlader from IOS, two conditions must be met:
     1. Must be in IOS Enanble mode (state machine will ensure this, has to be properly set up),
     2. Have to ensure auto boot is off (which requires IOS Config mode).
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    # Config IOS
    uut_conn.send('\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('config t\r',  expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('boot manual\r',  expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('exit\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)

    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    uut_conn.send('\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('reload\r',  expectphrase='?', timeout=30)
    time.sleep(1)
    # If this changes the config, DO NOT save; just use this as a "one-shot" everytime so as to
    # preserve the config in its current state for any point in the automation process.
    # Any other config changes should be done and saved outside of the transistion mode functions!
    # Note: It seems the MANUAL_BOOT setting remains persistent even when NOT saving from IOS CLI.
    if 'Save? [yes/no]' in uut_conn.recbuf:
        uut_conn.send('n\r',  expectphrase='reload?', timeout=30)
        time.sleep(1)
    if 'reload? [confirm]' in uut_conn.recbuf:
        uut_conn.send('y\r',  expectphrase='(?i)RELOAD', timeout=30, regex=True)

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
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r',  expectphrase=uut_prompts['IOS'], timeout=30, regex=True)
    uut_conn.send('en\r',  expectphrase='.*', timeout=30, regex=True)
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
            uut_conn.send('{0}\r'.format(default_passwords[loop_count]),  expectphrase=patterns, timeout=30, regex=True)
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
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('exit\r',  expectphrase='.?', timeout=30, regex=True)
    # Some IOS images will force the "Press RETURN" to start console; some will not.
    # Therefore, just allow time for recbuf update and then send another carriage return by default.
    time.sleep(2)
    uut_conn.send('\r',  expectphrase=uut_prompts['IOS'], timeout=30, regex=True)
    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOS', refresh=True) else False
    return ret


@func_details
def iose_to_iosecfg(pp, **kwargs):
    """IOS-Enable->IOS-EnabledConfig
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    uut_conn.send('config terminal\r',  expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOSECFG', refresh=True) else False
    return ret


@func_details
def iosecfg_to_iose(pp, **kwargs):
    """IOS-EnabledConfig->IOS-Enable
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """

    # Set local copy of modemachine vars
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('\r',  expectphrase=uut_prompts['IOSECFG'], timeout=30, regex=True)
    uut_conn.send('exit\r',  expectphrase=uut_prompts['IOSE'], timeout=30, regex=True)
    # Allow time for console logging to print (if enabled).
    time.sleep(2)
    # Confirm
    ret = True if pp.mode_mgr.is_mode('IOSE', refresh=True) else False
    return ret


# ----------------------------------------------------------------------------------------------------------------------
# Helper functions (INTERNAL ONLY)
#  DO NOT USE these directly!
def __get_robust_load_details(name, pp, uut_conn, uut_prompt, image, image_dirs, device_name, pattern, guess_image=None):
    """ Get Robust Load Details
    Use this to determine what image to boot and what method to boot that image (i.e. via network or local device)
    when the unit is in bootloader mode only!
    :param name: Title of the image type.
    :param uut_conn:
    :param uut_prompt:
    :param image: Filename of image to boot.
    :param image_dirs: Subdir of image locations for both local and remote.
    :param device_name: Device to boot from (e.g. 'tftp', 'flash', etc.)
    :param pattern: Regex pattern to use for searching filenames to find a suitable image.
    :param guess_image: Best guess for the image if none cane be found.
    :return: tuple of (<booelan for setting network>, <image name>, <subdir if any>)
    """
    set_net_load = False
    selected_image = ''
    image_dir = ''
    if device_name == 'tftp':
        # Network Device
        # Only set a flag here since the Local Boot may also fall back to attempt a Network Boot hence perform the
        # network routine later.
        log.info("{0} NETWORK DEVICE boot attempt.".format(name))
        image_dir = image_dirs['remote']
        if not image:
            log.info("No explicit network {0} image specified.".format(name))
            fparams = pp.rommon.get_params(0)
            # When attempting a network boot, if the image was NOT specified then at least make an attempt to guess
            # the network image based on the boot param if it is present.
            selected_image, _, _ = pp.rommon.get_boot_param_image_details(fparams, device_name, pattern)
            if selected_image:
                log.info("Boot param image is available: {0}".format(selected_image))
            elif guess_image:
                selected_image = guess_image
                log.warning("No {0} file; using best guess: {1}".format(name, selected_image))
            else:
                log.error("No image name available for network boot!")
        else:
            selected_image = image[0] if isinstance(image, list) else image
            log.info("Network {0} image specified = {1}".format(name, selected_image))
        set_net_load = True
    else:
        # Local Device
        log.info("{0} LOCAL DEVICE boot attempt.".format(name))
        local_devices = pp.rommon.get_devices()
        if device_name not in local_devices:
            log.warning("Expected device '{0}' is not present in {1}!  Flash may need formatting.".format(device_name, local_devices))
            selected_image = image[0] if isinstance(image, list) else image
            image_dir = image_dirs['remote']
            set_net_load = True
            return set_net_load, selected_image, image_dir
        # Image
        if not image:
            # Image was NOT specified (this is NOT typical of production, common for NPI debug):
            #  a. check if flash boot param is set; if so, then check for that file,
            #  b. if no boot param, then check if flash has the image or similar image based on pattern and
            #     if so then boot it,
            #  c. if no boot param image file and no other image file whatsoever then try a default network
            #     file (last effort).
            log.info("No explicit local {0} image specified.".format(name))
            fparams = pp.rommon.get_params()
            bp_file, bp_sub_dir, bp_dev_name = pp.rommon.get_boot_param_image_details(fparams, device_name, pattern)

            if bp_file:
                log.info("BOOT64 param is present: '{0}'".format(fparams['BOOT64']))
                # Get all potential target IOS images that are on the flash (per boot param path).
                ffiles = pp.rommon.get_device_files(bp_dev_name, bp_sub_dir, file_filter=pattern, attrib_flags='-')
                if ffiles:
                    image_dir = bp_sub_dir
                    if bp_file in ffiles:
                        selected_image = bp_file
                        log.info("{0} image (from boot param) found = {1}".format(name, selected_image))
                    else:
                        # Look for some other target image.
                        # There is no standard naming convention so we just pick the first in the list that
                        # was sorted if any.
                        selected_image = ffiles[0]
                        log.warning("Image (from boot param) cannot be found or is not an IOS image.")
                        log.info("Alternate {0} image found on flash = {1}.".format(name, selected_image))
                else:
                    # Since the file (indicated by boot param) is NOT on flash and there are no similar target files;
                    # then use the boot param file name in a net boot attempt.
                    selected_image = bp_file
                    image_dir = image_dirs['remote']
                    set_net_load = True
                    log.warning("No {0} files per boot param ({1}) prefix or general search.".
                                format(name, selected_image))
            else:
                log.warning("No explicit {0} image, no matching boot param; searching for alternatives...".format(name))
                ffiles = pp.rommon.get_device_files(device_name, image_dirs['local'], file_filter=pattern, attrib_flags='-')
                if ffiles:
                    selected_image = ffiles[0]
                    image_dir = image_dirs['local']
                    log.info("Local alternate {0} image found = {1}.".format(name, selected_image))
                elif guess_image:
                    selected_image = guess_image  # typically --> 'cat3k_universalk9.bin' or 'vmlinux.mzip.SSA'
                    image_dir = image_dirs['remote']
                    set_net_load = True
                    log.warning("No {0} file determination; using best guess: {1}".format(name, selected_image))
                else:
                    log.error("No {0} file determination and no best guess.".format(name))
        else:
            # Image was specified.
            #  Possible conditions:
            #  a. It is present on flash at designated subdir,
            #  b. It is NOT present on flash BUT the pattern has a single hit.
            #  c. It is NOT present on flash so attempt a net boot for that image (requires setup).
            # Strip out any pathing; it is specified separately.
            log.debug("Image was specified.")
            bt_images = [os.path.basename(i) for i in image] if isinstance(image, list) else [os.path.basename(image)]
            ffiles = pp.rommon.get_device_files(device_name, image_dirs['local'], file_filter=pattern, attrib_flags='-')
            log.debug("Potential files for loading (unspecified): {0}".format(ffiles))
            log.debug("Target boot images: {0}".format(bt_images))
            match_index_list = [i in ffiles for i in bt_images]
            if any(match_index_list):
                # One or more specified files match the list of files gathered by the pattern filter.
                # Find the first specified file that matched the gathered files.
                match_index = next((i for i, v in enumerate(match_index_list) if v), -1)
                selected_image = bt_images[match_index]
                image_dir = image_dirs['local']
                log.info("{0} image explicitly given was found = {1}".format(name, selected_image))
            elif len(ffiles) == 1 and ffiles[0] == 'packages.conf':
                # TODO: Is this a good idea?
                selected_image = ffiles[0]
                image_dir = image_dirs['local']
                log.warning("Single file exception will be used: {0}".format(ffiles[0]))
                log.warning("{0} explicit file {1} was NOT found and will be ignored.".format(name, image))
            else:
                selected_image = bt_images[0]
                image_dir = image_dirs['remote']
                set_net_load = True
                log.warning("{0} image explicitly given was NOT found ({1}).".format(name, selected_image))

    return set_net_load, selected_image, image_dir


def __set_uut_network(name, pp, uut_conn, uut_prompt, image, uut_mac, uut_ip, netmask, server_ip, device_name, directory, sernum=None):
    """ Set UUT Network
    Configure new UUT for network access and ping server to validate.
    Perform an initial ping to see if the network is already set to avoid repeating the setup.
    :param name: Title for the type of image to network boot
    :param image: name of image to boot
    :param uut_conn:
    :param uut_prompt:
    :param uut_mac:
    :param uut_ip: Temporary UUT private test network IP.
    :param netmask: Private test network mask.
    :param server_ip: Apollo server private test network IP used for downloading.
    :param device_name: Bootloader device - 'flash', 'tftp', etc.
    :param directory: directory of image location; use this for subdir on tftpboot (if needed)
    :param sernum: Serial number of UUT which is associated with the MAC (optional for MAC pull when lost from UUT)
    :return: True if successful setting of bootloader params for network and can ping to server.
    """
    do_load = False
    new_device_name = device_name
    new_dir = directory
    if image:
        log.info("{0} NETWORK BOOT attempt with image = {1}".format(name, image))
        common_utils.uut_comment(uut_conn, name, 'Network boot setup.')

        # Check the UUT network setup
        if not pp.rommon.check_network_params(ip=uut_ip, netmask=netmask, server_ip=server_ip):
            log.debug('UUT Network Boot: setting network...')
            if pp.rommon.set_uut_network_params(mac=uut_mac, ip=uut_ip, netmask=netmask, server_ip=server_ip, sernum=sernum):
                log.debug("UUT Network Boot: setup was successful.")
            else:
                log.error("UUT Network Boot: problem with setup.")
        else:
            log.debug("UUT Network Boot: already set.")

        # Check for ping
        for i in range(1, 4):
            if pp.rommon.ping(server_ip):
                log.debug("UUT Network Boot Ping: server ping successful; network setup is working.")
                do_load = True
                break
            else:
                log.warning("Power Cycle for UUT Ping retry!")
                pp.power.cycle_on(channels='ALL')
                btldr_result, _ = pp.wait_for_boot(boot_mode='BTLDR', boot_msg='(?:Booting)|(?:Initializing)')
                if not btldr_result:
                    log.error("Power Cycle did NOT complete properly; FATAL ERROR.")
                    raise StandardError("Power Cycle + boot has fatal error.")
                if i >= 2 and not pp.automation.get('enabled', False):
                    if aplib.ask_question("IOS could not Boot up. Check Download Interface cables and retry:",
                                          answers=['YES', 'NO']) == 'NO':
                        log.error("STEP: Set network interface FAILED. (Retry was refused.)")
                        break
        else:
            log.error("UUT Network Boot Ping: problem pinging the server.")

        # Set new device and directory if a network boot setup is ready.
        if do_load:
            new_device_name = 'tftp'
            remote_prefix = '//{0}'.format(server_ip)
            new_dir = '/'.join([remote_prefix, directory])
            if new_dir[-1:] != '/':
                new_dir += '/'

    else:
        log.error("UUT Network Boot Setup: missing setup data (no image name); network load not possible.")

    return do_load, new_device_name, new_dir


def __multi_to_symsh(pp, **kwargs):
    """ Multiple possible modes->Symsh
    :param pp: Product Pointer (callback class object)
    :param kwargs:
    :return:
    """
    # Set local
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('symsh\r', expectphrase=uut_prompts['SYMSH'], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode('SYMSH', refresh=True) else False
    return ret


def __symsh_to_multi(pp, tmode, **kwargs):
    """ Symsh->Multiple possible modes
    Note: The statemachine definition should define which mode to return to based on previous.
    :param pp: Product Pointer (callback class object)
    :param mode:
    :param kwargs:
    :return:
    """
    # Set local
    uut_conn = pp.uut_conn
    uut_prompts = pp.mode_mgr.uut_prompt_map

    uut_conn.send('exit\r', expectphrase=uut_prompts[tmode], timeout=30, regex=True)

    # Confirm
    ret = True if pp.mode_mgr.is_mode(tmode, refresh=True) else False
    return ret
