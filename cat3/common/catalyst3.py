"""
Catalyst Series 3

[Catalyst]---->[Catalyst3]---->[<ProductLine class>]
                   ^
                   |
                   +--- Mid-Tier class objects.

NOTE: These class objects should normally be used only for overriding the methods of the parent class.
      The class instances available here are for debug purposes only. (Do not change the init order!)
"""

# Python
# ------
import sys
import logging
import re
import time
import os

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Libs
# ------
from apollo.scripts.entsw.libs.cat.catalyst import Catalyst as _Catalyst
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

# Product Specific
# ----------------
#

__title__ = "Catalyst Series 3 Module"
__version__ = '2.0.0'
__author__ = ['bborel']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

apollo_step = common_utils.apollo_step
func_details = common_utils.func_details


if not hasattr(aplib.conn, 'uutTN'):
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1}))


# ______________________________________________________________________________________________________________________
#
# Catalyst3 (shared)
# ______________________________________________________________________________________________________________________
class _Catalyst3(_Catalyst):

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    @apollo_step
    def upgrade_mcu(self, **kwargs):
        """ Upgrade MCU
        Upgrade the images on the MCU (kirchhoff) device.
        :menu: (enable=True, name=UPGRADE MCU, section=Upgrade, num=1, args={'force': False})
        :menu: (enable=True, name=UPGRADE MCU force, section=Upgrade, num=1, args={'force': True})
        :param (dict) kwargs
               (bool) force:        force upgrade/flash even when rev meets requirement, default is False
               (bool) confirm:      confirm rev after upgrade/flash (require AC cycle), default is False
               (bool) verify_only:  do not upgrade/flash mcu if rev doesn't meeting requirement, return FAIL, this is for DF use, default is False
               (bool) skip:         use only for proto; MCU is checked but result is "don't care".

        :return:
        """
        if 'mcu' not in self.ud.uut_config:
            log.warning("The 'mcu' data dict is not defined per the product_definition.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        # Process input
        mcu = kwargs.get('mcu', self.ud.uut_config.get('mcu', None))
        force = kwargs.get('force', self.ud.uut_config.get('mcu', {}).get('force', False))
        skip = kwargs.get('skip', self.ud.uut_config.get('mcu', {}).get('skip', False))
        confirm = kwargs.get('confirm', self.ud.uut_config.get('mcu', {}).get('confirm', False))
        verify_only = kwargs.get('verify_only', False)
        force_power_cycle = kwargs.get('force_power_cycle', self.ud.uut_config.get('mcu', {}).get('force_power_cycle', True))

        # Set some defaults (if needed)
        mcu_images = mcu.get('images', {'kirch': ['app_data.srec', 'app_flash.bin',
                                                  'kirchoff_swap.bin', 'Cisco_loader.srec',
                                                  'c_kirchhoff_swap.bin', 'coulomb_kirchhoff.bin']})
        mcu_name = mcu.get('name', 'alchemy')
        mcu_rev = mcu.get('rev', {'ios': '', 'cl': ''})
        mcu_post_upgrade = mcu.get('post_upgrade', None)

        # Check Mode
        if self.mode_mgr.current_mode != 'STARDUST':
            errmsg = "Wrong mode; need to be in STARDUST."
            log.error(errmsg)
            return aplib.FAIL. errmsg

        # Check the version
        mcu_good = self.diags._check_mcu(name=mcu_name, revision=mcu_rev)

        # Logic Table
        # mcu_good  &  verify_only &  force  &  skip  =  RESULT
        # ----------|--------------|---------|--------|--------
        #     1     |       X      |   0     |    X   |  PASS
        #     1     |       X      |   1     |    0   |  upgrade
        #     0     |       0      |   0     |    0   |  upgrade
        #     0     |       1      |   X     |    0   |  FAIL
        #     0     |       0      |   X     |    0   |  upgrade
        #     X     |       X      |   X     |    1   |  SKIP

        # Check skip regardless of result
        if skip:
            if not mcu_good:
                log.warning("*" * 50)
                log.warning("The MCU needs upgrading but it has been requested to skip the upgrade.")
                log.warning("This is NOT for released products!  Use only for proto testing.")
                log.warning("*" * 50)
                return aplib.SKIPPED
            else:
                log.info("MCU is good, no upgrade required.  Skip not needed.")
                return aplib.PASS

        # Check the upgrade if needed or if forced
        if mcu_good and not force:
            log.info("MCU is good, no upgrade required.")
            return aplib.PASS

        # Fail step if it is verify only, do not upgrade
        if not mcu_good and verify_only:
            errmsg = 'MCU Rev ({0}) does not meet the requirement.'.format(mcu_rev)
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Perform the upgrade ----------------------------------------------------
        aplib.set_container_text('UPGRADE MCU: {0} {1}'.format(mcu_name, mcu_rev))
        log.info("MCU {0}upgrade started...".format('forced ' if force else ''))
        if not self.diags._upgrade_mcu(name=mcu_name,
                                       image_pkg=mcu_images,
                                       home_dir=self.ud.get_flash_mapped_dir()):
            errmsg = "MCU Programming incomplete."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Wait for automatic reboot, Some SKUs no automatic reboot
        # Some SKUs require reboot, others do not.
        if force_power_cycle:
            log.debug("Force power cycle reboot after MCU upgrade.")
            self.power.cycle_on()
            result, _ = self.mode_mgr.wait_for_boot(boot_mode=['BTLDR'],
                                                    boot_msg='(?:Booting)|(?:System Bootstrap)|(?:Initializing)')
            if not result:
                errmsg = "System did not properly reboot after MCU upgrade."
                log.error(errmsg)
                return aplib.FAIL, errmsg

        # Get back to diags
        if not self.mode_mgr.goto_mode('STARDUST'):
            errmsg = "Cannot return to diags after MCU upgrade!"
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Check System Init
        if self.diags.sysinit() != aplib.PASS:
            errmsg = "Cannot sysinit after MCU upgrade!"
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Confirm version
        if confirm:
            log.debug("Upgrade confirmation requested; power-cycle will occur...")
            if self.diags._check_mcu(name=mcu_name, revision=mcu_rev):
                log.info("MCU Programmed Revision confirmed.")
            else:
                errmsg = "MCU Programmed Revision ({0}) NOT confirmed.".format(mcu_rev)
                log.error(errmsg)
                return aplib.FAIL, errmsg
        else:
            log.warning("No MCU upgrade confirmation requested.")
            log.warning("Correct MCU versions will need manual check!")

        # Checkpoint: getting here means the upgarde appears to be good.
        result = True
        log.debug("MCU upgrade appears to be good.")

        # Run any routine for post-upgrade
        if mcu_post_upgrade:
            log.debug("Additional post-upgrade operation was specified: {0}.{1}".format(self.__name__,
                                                                                        mcu_post_upgrade))
            mcu_post_up_func = getattr(self, mcu_post_upgrade)
            if not mcu_post_up_func:
                log.error("The post-upgrade function is not available in the object: {0}".format(self.__name__))
                result = False
            else:
                log.debug("Running the post-upgrade function...")
                result = mcu_post_up_func()

        log.debug("MCU upgrade/operation end.")
        return aplib.PASS if result else (aplib.FAIL, "MCU Upgrade incomplete.")

    @apollo_step
    def upgrade_nic(self, **kwargs):
        """ Upgrade NIC

            This routine performs the commands in the order listed in the dict.

            'nic': {1: {'image': 'BDXDE_P0_1G_P1_XFI_PV_A0000636.bin',
                        'rev': '',
                        'cmd': 'eeupdate64e /NIC=1 /DATA /DEBUG %image%'},
                    2: {'image': 'I211_Invm_APM_v0.6.1.txt',
                        'rev': '',
                        'cmd': 'eeupdate64e /NIC=2 /INVMUPDATE /MAC=%MAC_ADDR% /FILE=%image%'},
                    3: {'image': 'eeupdate64e',
                        'cmd': 'eeupdate64e /ALL /MAC_DUMP'},
                    },

        :menu: (enable=True, name=UPGRADE NIC, section=Upgrade, num=1, args={'force': False})
        :menu: (enable=True, name=UPGRADE NIC force, section=Upgrade, num=1, args={'force': True})
        :param kwargs:
        :return:
        """

        def __check_nic():
            # Check NIC setup
            log.debug("Checking NIC...")
            self.uut_conn.send("ls --color=n /sys/class/net\r", expectphrase=self.mode_mgr.uut_prompt_map['LINUX'], timeout=60,
                             regex=True)
            time.sleep(3.0)
            if 'eth1' in self.uut_conn.recbuf or 'eth2' in self.uut_conn.recbuf:
                log.info("NIC setup is GOOD.")
                return True
            else:
                log.warning("NIC is not setup.")
                return False

        aplib.set_container_text('UPGRADE NIC')
        log.info('STEP: Upgrade NIC.')

        if 'nic' not in self.ud.uut_config:
            log.warning("The 'nic' data dict is not defined per the product_definition.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        # Process input
        nic = kwargs.get('nic', self.ud.uut_config.get('nic', {}))
        force = kwargs.get('force', nic.get('force', False))

        # Sanity check
        if not nic or len(nic.keys()) == 0:
            errmsg = "This 'nic' data dict is empty."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Check mode
        if self.mode_mgr.current_mode != 'LINUX':
            errmsg = "Wrong mode; need to be in LINUX."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Check if need to perform NIC setup
        if __check_nic() and not force:
            log.info("NIC already setup!")
            return aplib.PASS

        # Process each index in the sequential order given.
        for index in sorted(nic.keys()):
            if isinstance(index, int):
                cmd = common_utils.rebuild_cmd(nic[index], self.ud.uut_config, special_key='MAC_ADDR',
                                               special_func=common_utils.convert_mac_single_upper)
                log.debug("NIC Command: {0}".format(cmd))
                if re.search('%[\S]+%', cmd):
                    errmsg = "String substitution is missing in the command.  Cannot run."
                    log.error(errmsg)
                    return aplib.FAIL, errmsg
                elif 'POWERCYCLE' in cmd:
                    self.power.cycle_on()
                    if not self.mode_mgr.goto_mode('LINUX'):
                        errmsg = "Problem returning to LINUX; cannot continue."
                        log.error(errmsg)
                        return aplib.FAIL, errmsg
                else:
                    self.uut_conn.send("./{0}\r".format(cmd), expectphrase=self.mode_mgr.uut_prompt_map['LINUX'], timeout=180,
                                     regex=True)
                    time.sleep(1.0)
                    if 'not found' in self.uut_conn.recbuf:
                        log.error("Cannot continue since the command was not found.")
                        log.error("Please check all support files are loaded.")
                        return aplib.FAIL, 'NIC command not found.'

            else:
                log.debug("NIC other data ({0}); no cmd to process.".format(index))

        # Check again to confirm
        if not __check_nic():
            log.error("NIC setup FAILED!")
            return aplib.FAIL, "NIC setup error."
        else:
            log.info("NIC setup PASSED!")

        return aplib.PASS


# ______________________________________________________________________________________________________________________
#
# Catalyst3000
# ______________________________________________________________________________________________________________________
class Catalyst3000(_Catalyst3):
    pass


# ______________________________________________________________________________________________________________________
#
# Catalyst9300
# ______________________________________________________________________________________________________________________
class Catalyst9300(_Catalyst3):

    @func_details
    def _prepare_emmc_v2(self, **kwargs):
        """ Prepare eMMC (INTERNAL for Nyquist/NyquistCR)

        Use this routine prior to partition & format of the eMMC flash.

        ----------------------------------------------------------------------------
        root@diags:/# /proj/util/set_dfu_mode -vvv /dev/sda
        Diagnostic sgtool for set_dfu_mode, Version 1.0.0
        Compiled by ptong on Fri 09-Sep-16 14:47
        SCSI Inquiry:
          Vendor Id Generic Ultra HS-SD/MMC
          Product Id Ultra HS-SD/MMC
          Revision 2.09
          Device Type 0x0
          Version 0x0
        *** Setting mode to: DFU MODE ***


        ----------------------------------------------------------------------------
        RESULT 1
        root@diags:/# /proj/util/dfu-util -R -D /proj/fw/Cisco-emmc-v211.dfu
        dfu-util 0.7
        Copyright 2005-2008 Weston Schmidt, Harald Welte and OpenMoko Inc.
        Copyright 2010-2012 Tormod Volden and Stefan Schmidt
        This program is Free Software and has ABSOLUTELY NO WARRANTY
        Please report bugs to dfu-util@lists.gnumonks.org
        No DFU capable USB device found

        RESULT 2
        root@diags:/# /proj/util/dfu-util -R -D /proj/fw/Cisco-emmc-v211.dfu
        dfu-util 0.7
        Copyright 2005-2008 Weston Schmidt, Harald Welte and OpenMoko Inc.
        Copyright 2010-2012 Tormod Volden and Stefan Schmidt
        This program is Free Software and has ABSOLUTELY NO WARRANTY
        Please report bugs to dfu-util@lists.gnumonks.org
        Opening DFU capable USB device... ID 0424:2df0
        Deducing device DFU version from functional descriptor length
        Run-time device DFU version 0100
        Claiming USB DFU Runtime Interface...
        Determining device status: state = dfuIDLE, status = 0
        WARNING: Runtime device already in DFU state ?!?
        Found Runtime: [0424:2df0] devnum=0, cfg=1, intf=0, alt=0, name="UNDEFINED"
        Claiming USB DFU Interface...
        Setting Alternate Setting #0 ...
        Determining device status: state = dfuIDLE, status = 0
        dfuIDLE, continuing
        Deducing device DFU version from functional descriptor length
        DFU mode device DFU version 0100
        Device returned transfer size 65534
        Limited transfer size to 4096
        Dfu suffix version 100
        Warning: File product ID 4041 does not match device 2df0
        bytes_per_hash=1392
        Copying data from PC to DFU device
        Starting download: [##################################################] finished!
        state(2) = dfuIDLE, status(0) = No error condition is present
        Done!
        Resetting USB to switch back to runtime mode
        root@diags:/#


        ----------------------------------------------------------------------------
        RESULT 1
        root@diags:/# /proj/util/sd_partition /dev/sda
        Diagnostic sgtool for sd_partition, Version 1.0.0
        Compiled by ptong on Fri 09-Sep-16 14:47
        open device /dev/sda failed 2

        RESULT 2
        root@diags:/# /proj/util/sd_partition /dev/sda
        Diagnostic sgtool for sd_partition, Version 1.0.0
        Compiled by ptong on Fri 09-Sep-16 14:47
        open device /dev/sda failed 2
        root@diags:/# sd 7:0:0:0: [sda] No Caching mode page found
        sd 7:0:0:0: [sda] Assuming drive cache: write through
        /proj/util/sd_partition /dev/sda
        Diagnostic sgtool for sd_partition, Version 1.0.0
        Compiled by ptong on Fri 09-Sep-16 14:47
        +++ Doing standard SCSI Inquiry +++
        SCSI Inquiry:
          Vendor Id CISCO   eMMC  HS-SD/MMC
          Product Id eMMC  HS-SD/MMC
          Revision 2.11
        +++ Doing SD Inquiry +++
        SD Inquiry:
          Protocol Version 1
          Host Controller Version 2.0
          Slot 0
          Protocol Class 0xe
          Vendor Id 0x80
        SD Card Initialize
          SD memory function type 3
          SDIO 0, Card Locked 0/Error 0/Present 1/Power 1
          Bus Clock Speed 0x30
          Bus Width 0
          SDIO Functions 0
          RCA 01 02
          CID
             90 01 4a 48 42 47 34 65 05 81 4a fb 2d 63 44 00
          Memory OCR
             00 00 00 00
          SDIO OCR
             00 00 00
        +++ Partition check +++
        --- Doing CMD8 (Ext CSD)
        CMD8 response:
         08 00 00 09 00 0f 00 00 00 00 00 00 00 00 00 00 00
        CMD8 (Ext CSD) Data:
          0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
        ...
        496: 78 00 00 01 3f 3f 01 01 01 00 00 00 00 00 00 00
        --- Doing optimized CMD8 (Ext CSD)
        Optimized CMD8 response:
         ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
        Optimized CMD8 Data:
          0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
        ...
        496: 78 00 00 01 3f 3f 01 01 01 00 00 00 00 00 00 00
        -----
        Partitioning Support [160] 0x07
        Max Enhanced Area Size [157-159] 0x000748
        Partitioning initialization timeout [241] 1000 ms
        EXT_CSD registers to be set:
          Partitions Attribute [156] 0x01
          Partitioning Setting [155] 0x01
          Enhanced User Data Area Size [140-142] 0x000748
        Verifying...
        !!! Partition Setting already set?
        !!! Partitions Attribute already set for ENH_USR?
        !!! Enhanced user data area size already set?
        +++ Device cannot be paritioned?
        root@diags:/#

        :param uut_conn:
        :param uut_prompt:
        :param kwargs:
        :return:
        """
        log.debug("Prepare eMMC (v2)...")
        UTIL_PATH = '/proj/util'

        # Input
        disk = kwargs.get('disk', 'None')
        if not disk:
            log.error("Must have a disk to partition.")
            return False
        log.debug("Partition & Format Disk: {0}".format(disk))

        if not self.mode_mgr.is_mode('LINUX'):
            log.error("Wrong mode; MUST be in LINUX mode for eMMC v2 prep.")
            return False
        linux_uut_prompt = self.mode_mgr.uut_prompt_map['LINUX']

        if True:
            log.info("Set dfu mode...")
            for i in range(1, 4):
                log.debug("Set dfu mode...attempt={0}".format(i))
                self.uut_conn.send('{0}/set_dfu_mode -vvv {1}\r'.format(UTIL_PATH, disk), expectphrase=linux_uut_prompt, timeout=30, regex=True)
                time.sleep(1)
                if 'DFU MODE' in self.uut_conn.recbuf:
                    break
            else:
                log.error("DFU Mode NOT confirmed.")
                log.error(self.uut_conn.recbuf)
                return False

            log.info("eMMC firmware update...")
            for i in range(1, 4):
                log.debug("eMMC firmware update..attempt={0}".format(i))
                self.uut_conn.send('{0}/dfu-util -R -D /proj/fw/Cisco-emmc-v211.dfu\r'.format(UTIL_PATH),
                                   expectphrase=linux_uut_prompt, timeout=120, regex=True)
                time.sleep(1)
                if 'Done' in self.uut_conn.recbuf:
                    break
            else:
                log.error("eMMC firmware update fail")
                log.error(self.uut_conn.recbuf)
                return False

            log.debug("Perform partition init...")
            attempt = 1
            while attempt <= 3:
                log.info("Partition init attempt={0}".format(attempt))
                self.uut_conn.send('{0}/sd_partition {1}\r'.format(UTIL_PATH, disk), expectphrase=linux_uut_prompt, timeout=240, regex=True)
                time.sleep(1)
                if 'Partitioning complete' in self.uut_conn.recbuf:
                    log.debug("Partition init done.")
                    break
                elif 'Partition Setting already set' in self.uut_conn.recbuf:
                    if attempt > 1:
                        log.debug("Partition Setting already set after multiple attempts.")
                        break
                log.warning("Partition init will retry...")
                attempt += 1
                time.sleep(5)
            else:
                log.warning("Did not get a completion status (or prior set) after {0} attempts.".format(attempt))
                log.warning(self.uut_conn.recbuf)
                if 'open device {0} failed 2'.format(disk) in self.uut_conn.recbuf:
                    log.error("Device failure during partition init.")
                    return False
                else:
                    log.error("Prepare eMMC partition init: FAILED.")
                    return False

            self.uut_conn.send('sync\r', expectphrase=linux_uut_prompt, timeout=20, regex=True)
            log.debug("Power cycle...")
            self.power.cycle_on()
            self.mode_mgr.goto_mode('LINUX', kwargs={'do_primary_mount': False})

            log.debug("Prepare eMMC partition init: DONE.")
        return True


# ______________________________________________________________________________________________________________________
#
# Catalyst9300L
# ______________________________________________________________________________________________________________________
class Catalyst9300L(_Catalyst3):

    @apollo_step
    def upgrade_emmc_fw(self, **kwargs):
        """ Upgrade eMMC Flash Firmware

        emmcparm -V
        Device file = /dev/mmcblk0
        EXT_CSD revision [192] = 1.7 (for MMC v5.0x)
        Host = mmc0
        Name = HBG4e
        Manuf ID = 0x000090
        PRV = 0x81
        Manufacturing Date = 08/2016

        emmcparm -I
        ...
        FIRMWARE_VERSION up 32b[261-258]:   0x0 ()
        FIRMWARE_VERSION lo 32b[257-254]:   0x81 (?)

        :menu: (enable=True, name=UPGRADE EMMC FW, section=Upgrade, num=8, args={})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('UPGRADE eMMC FLASH FW')
        log.info('STEP: Upgrade eMMC Flash Firmware.')

        if 'emmc' not in self.ud.uut_config:
            log.warning("The 'emmc' data dict is not defined per the product_definition.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        # Process input
        emmc_dir = kwargs.get('emmc_dir', self.ud.uut_config.get('emmc', {}).get('dir', 'emmcparm_mfg'))
        emmc_image = kwargs.get('emmc_image', self.ud.uut_config.get('emmc', {}).get('image', None))
        emmc_version = kwargs.get('emmc_version', self.ud.uut_config.get('emmc', {}).get('version', None))
        uut_ip = kwargs.get('uut_ip', self.ud.uut_config.get('uut_ip', ''))
        server_ip = kwargs.get('server_ip', self.ud.uut_config.get('server_ip', ''))
        netmask = kwargs.get('netmask', self.ud.uut_config.get('netmask', ''))
        force = kwargs.get('force', False)

        # Check mode
        # Note: This MUST be done over the network!
        if not self.mode_mgr.goto_mode('LINUX', kwargs={'device_name': 'tftp', 'do_primary_mount': False}):
            errmsg = "Cannot get to LINUX for eMMC FW."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Set Net Intf
        result = None
        if self.linux.set_uut_network_params(ip=uut_ip, netmask=netmask, server_ip=server_ip):
            result = self.linux.ping(ip=server_ip, count=3)
        if not result:
            errmsg = "Unable to setup interface for eMMC dir upload."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Move files to RAM
        log.debug("Transferring emmc dir...")
        emmc_uut_path = os.path.join('/tmp', emmc_dir)
        result = self.linux.transfer_tftp_directory(src_dir=emmc_dir,
                                                    dst_dir=emmc_uut_path,
                                                    direction='get',
                                                    server_ip=server_ip,
                                                    netmask=netmask,
                                                    ip=uut_ip)
        if not result:
            errmsg = "TFTP transfer error. Check source dir and destination mounts."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        log.debug("Running eMMC detect...")
        linux_uut_prompt = self.mode_mgr.uut_prompt_map['LINUX']
        self.uut_conn.send('{0}/emmcparm -V\r'.format(emmc_uut_path), expectphrase=linux_uut_prompt, timeout=60, regex=True)
        time.sleep(3.0)
        if 'Manuf ID = 0x00013' in self.uut_conn.recbuf:
            log.debug("Micron Vendor for eMMC, therefore need to verify FW version.")
            log.debug("Getting eMMC version...")
            self.uut_conn.send('{0}/emmcparm -I\r'.format(emmc_uut_path), expectphrase=linux_uut_prompt, timeout=60, regex=True)
            time.sleep(3.0)
            m = re.search('FIRMWARE_VERSION lo .*?: [ \t]*([\S]+)', self.uut_conn.recbuf)
            emmc_current_version = m.groups()[0] if m else None
            if (emmc_current_version < emmc_version) or force:
                log.debug("Running eMMC firmware upgrade...")
                self.uut_conn.send('{0}/ffu.sh {0}\r'.format(emmc_uut_path, emmc_image), expectphrase=linux_uut_prompt, timeout=60, regex=True)
                time.sleep(3.0)
        else:
            log.debug("No eMMC FW upgrade required for this vendor.")

        return aplib.PASS

    @func_details
    def _mcu_post_upgrade(self, **kwargs):
        """MCU Post Upgrade

        Product specific operation (C9300L Franklin 24-port only).

        Dogood24P> rd alchemy/0 AlchemyConfig0
        Alchemy.Alchemy/0 (base @ 0x00000000.00000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000050                                   e0  AlchemyConfig0

        Dogood24P> rw alchemy/0 AlchemyConfig0 0xc1
        Alchemy.Alchemy/0 (base @ 0x00000000.00000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000050                                   c1  AlchemyConfig0

        Dogood24P> rw bi rst_1 0x0001
        FPGA.Bifocal/0 (base @ 0x00000000.88000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000008                             00010001  rst_1

        Dogood24P> rw bi rst_1 0x0000
        FPGA.Bifocal/0 (base @ 0x00000000.88000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000008                             00010000  rst_1

        :param kwargs:
        :return:
        """

        uut_prompt = self.mode_mgr.uut_prompt_map['STARDUST']
        self.uut_conn.send('rd alchemy/0 AlchemyConfig0\r', expectphrase=uut_prompt, timeout=30, regex=True)
        self.uut_conn.send('rw alchemy/0 AlchemyConfig0 0xc1\r', expectphrase=uut_prompt, timeout=30, regex=True)
        self.uut_conn.send('rw bi rst_1 0x0001\r', expectphrase=uut_prompt, timeout=30, regex=True)
        self.uut_conn.send('rw bi rst_1 0x0000\r', expectphrase=uut_prompt, timeout=30, regex=True)
        log.debug("Waiting for MCU to settle on register writes...")
        time.sleep(7)
        log.debug("MCU Post Upgrade DONE!")
        return True

    @func_details
    def _prepare_emmc_v1(self, **kwargs):
        """ Prepare eMMC (INTERNAL for Franklin)

        Use this routine prior to partition & format of the eMMC flash.
        Note: Must begin AND end in LINUX mode.
        :param kwargs:
        :return:
        """

        log.debug("Prepare eMMC (v1)...")

        # Inputs
        emmc_dir = kwargs.get('emmc_dir', self.ud.uut_config.get('emmc', {}).get('dir', 'emmcparm_mfg'))
        set_pSLC_mode_file = kwargs.get('set_pSLC_mode', self.ud.uut_config.get('emmc', {}).get('set_pSLC_mode_file', 'set_emmc_pslc.sh'))
        uut_ip = kwargs.get('uut_ip', self.ud.uut_config.get('uut_ip', ''))
        server_ip = kwargs.get('server_ip', self.ud.uut_config.get('server_ip', ''))
        netmask = kwargs.get('netmask', self.ud.uut_config.get('netmask', ''))

        if not self.mode_mgr.is_mode('LINUX'):
            log.error("Wrong mode; MUST be in LINUX mode for eMMC v1 prep.")
            return False

        emmc_uut_path = os.path.join('/tmp', emmc_dir)
        result = None
        if self.linux.set_uut_network_params(ip=uut_ip, netmask=netmask, server_ip=server_ip):
            result = self.linux.ping(ip=server_ip, count=3)
        if not result:
            log.error("Unable to setup interface for pSLC shell script upload.")
            return False

        linux_uut_prompt = self.mode_mgr.uut_prompt_map['LINUX']
        pwd = self.linux.get_pwd()
        self.uut_conn.send('cd /tmp\r', expectphrase=linux_uut_prompt, timeout=30, regex=True)
        result = self.linux.get_device_files(sub_dir=emmc_dir, file_filter=set_pSLC_mode_file)
        if not result:
            log.debug("File not found; transferring emmc dir...")
            result = self.linux.transfer_tftp_directory(src_dir=emmc_dir,
                                                        dst_dir=emmc_uut_path,
                                                        direction='get',
                                                        server_ip=server_ip,
                                                        netmask=netmask,
                                                        ip=uut_ip)
            if not result:
                log.error("TFTP transfer error. Check source dir and destination mounts.")
                return False

        log.debug("Running pSLC script...")
        self.uut_conn.send('{0}/{1}\r'.format(emmc_uut_path, set_pSLC_mode_file), expectphrase=linux_uut_prompt, timeout=30, regex=True)
        time.sleep(3.0)
        log.debug(self.uut_conn.recbuf)
        if 'Already in pSLC mode' in self.uut_conn.recbuf:
            ret = True
        elif "Rebooting" in self.uut_conn.recbuf:
            log.debug("Wait for reboot because of pSLC mode setting...")
            self.mode_mgr.wait_for_boot(boot_mode=['BTLDR', 'IOS', 'IOSE'])
            if self.mode_mgr.goto_mode('LINUX', kwargs={'device_name': 'tftp', 'do_primary_mount': False}):
                ret = True
            else:
                log.error("Cannot return to LINUX after pSLC mode setting.")
                ret = False
        else:
            log.debug("Set pSLC mode result undetermined.")
            ret = False

        # Return to linux dir
        log.debug("Returning to dir: {0}".format(pwd))
        self.uut_conn.send('cd {0}\r'.format(pwd), expectphrase=linux_uut_prompt, timeout=30, regex=True)

        log.debug("The pSLC mode set is done!")
        return ret
