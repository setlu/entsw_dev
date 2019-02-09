"""
Stardust4
"""

# Python
# ------
import sys
import re
import logging
import time
from collections import namedtuple


# Apollo
# ------
from apollo.libs import lib as aplib
# from apollo.engine import apexceptions

# BU Lib
# ------
from apollo.scripts.entsw.libs.diags.stardust import Stardust as _Stardust
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Stardust Series4 Module"
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
func_retry = common_utils.func_retry


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# Stardust (shared)
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class _Stardust4(_Stardust):
    def __init__(self, **kwargs):
        super(_Stardust4, self).__init__(**kwargs)
        return


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# C4000 Diags (Stardust)
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class StardustC4000(_Stardust4):
    def __init__(self, **kwargs):
        super(StardustC4000, self).__init__(**kwargs)
        return


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# C9400 Stardust
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class StardustC9400(_Stardust4):
    def __init__(self, **kwargs):
        super(StardustC9400, self).__init__(**kwargs)
        return

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def serdeseye_supdp_test(self, **kwargs):
        """SerdesEye Test
        :menu: (enable=True, name=SERDESEYE SUPDP, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        area = aplib.apdicts.test_info.test_area

        interfaces = kwargs.get('serdeseye_interfaces', self._ud.uut_config.get('serdeseye', {}).get('interfaces', []))
        supdp_options = kwargs.get('serdeseye_supdp_options', self._ud.uut_config.get('serdeseye', {}).get(area, {}).get('supdp_options', ''))
        asic_core_count = kwargs.get('asic_core_count', self._ud.uut_config.get('asic', {}).get('core_count', 0))

        # Check mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.warning('Wrong mode ({0}) for this operation. Mode "STARDUST" is required.'.format(self._mode_mgr.current_mode))
            return aplib.FAIL, 'Wrong mode.'

        log.info('-' * 40)
        if 'SUPDP' in interfaces:
            log.debug("Running SUPDP SerDesEye...")
            current_supdp = self._get_supdp_serdeseye(asic_core_count, supdp_options=supdp_options)
            if not current_supdp:
                return aplib.FAIL, 'SUPDP SerDesEye TEST: FAILED (no results collected).'
            result = self._check_supdp_serdeseye(current_supdp) if current_supdp else None
            if not result:
                return aplib.FAIL, 'SUPDP SerdesEye TEST: FAILED.'
            log.info('SUPDP SerDesEye TEST: PASSED.')
        else:
            log.warning("SUPDP SerdesEye TEST: SKIPPED.")
            return aplib.SKIPPED

        log.info('-' * 40)
        log.info('SerDesEye Testing done.')
        return aplib.PASS

    @apollo_step
    def serdeseye_nru_test(self, **kwargs):
        """SerdesEye Test
        :menu: (enable=True, name=SERDESEYE NRU, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        area = aplib.apdicts.test_info.test_area

        interfaces = kwargs.get('serdeseye_interfaces', self._ud.uut_config.get('serdeseye', {}).get('interfaces', None))
        nru_options = kwargs.get('serdeseye_nru_options', self._ud.uut_config.get('serdeseye', {}).get(area, {}).get('nru_options', ''))

        # Check mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.warning('Wrong mode ({0}) for this operation. Mode "STARDUST" is required.'.format(self._mode_mgr.current_mode))
            return aplib.FAIL, 'Wrong mode.'

        log.info('-' * 40)
        if 'NRU' in interfaces:
            log.debug("Running NRU SerDesEye...")
            current_nru = self._get_nru_serdeseye(nru_options=nru_options)
            if not current_nru:
                return aplib.FAIL, 'NRU SerDesEye TEST: FAILED (no results collected).'
            result = self._check_nru_serdeseye(current_nru) if current_nru else None
            if not result:
                return aplib.FAIL, 'NRU SerdesEye TEST: FAILED.'
            log.info('NRU SerDesEye TEST: PASSED.')
        else:
            log.warning("NRU SerdesEye TEST: SKIPPED.")
            return aplib.SKIPPED

        log.info('-' * 40)
        log.info('SerDesEye Testing done.')
        return aplib.PASS

    @apollo_step
    def vbds(self, **kwargs):
        """ VBDS Load and install

        Example:
        ---------------------------------------------------------------------
        Chivas_1,3> WriteRawMMCFlash 1000 /proj/fw/vbds_v2.bin -o:0x40000
        Chivas_1,3> WriteRawMMCFlash 1000 /proj/fw/vbds_v2.bin -o:0xc0000
        Chivas_1,3> VerifyRawMMCFlash 1000 /proj/fw/vbds_v2.bin -o:0x40000
        PASS
        Chivas_1,3> VerifyRawMMCFlash 1000 /proj/fw/vbds_v2.bin -o:0xc0000
        PASS
        Note:
        expecting the vbds file bundled in the diags kernel
        :param kwargs:
        :return:
        """
        aplib.set_container_text('VBDS INSTALL')
        log.info('STEP: Install the VBDS bin file.')

        uut_prompt = self._mode_mgr.uut_prompt_map['STARDUST']
        log.debug("Prompt={0}".format(uut_prompt))

        linecard_device_instance = self._ud.uut_config['linecard']['device_instance']
        self._uut_conn.send('WriteRawMMCFlash {0} /proj/fw/vbds_v2.bin -o:0x40000\r'.format(linecard_device_instance),
                           expectphrase=uut_prompt, regex=True)
        self._uut_conn.send('WriteRawMMCFlash {0} /proj/fw/vbds_v2.bin -o:0xC0000\r'.format(linecard_device_instance),
                           expectphrase=uut_prompt, regex=True)
        self._uut_conn.send('VerifyRawMMCFlash {0} /proj/fw/vbds_v2.bin -o:0x40000\r'.format(linecard_device_instance),
                           expectphrase='PASS')
        self._uut_conn.send('VerifyRawMMCFlash {0} /proj/fw/vbds_v2.bin -o:0xC0000\r'.format(linecard_device_instance),
                           expectphrase='PASS')

        return aplib.PASS

    @apollo_step
    def emmc_erase(self, **kwargs):
        """ eMMC erase test

        Example:
        Chivas_1,3> GetRawMMCFlashInfo
        [Slot 00] Flash: dev:flash1, MMC: 3744MB (7733248 blocks)
        [Slot 01] Flash: dev:flash2, MMC: 3744MB (7733248 blocks)

        Chivas_1,3>


        Chivas_1,3> FlashShowInfo

        ===============================================

        Char. Device: dev:flash0
        Total Block Count: 119296
        Block Index Range: 0 - 119295
        Block Size in bytes: 131072

        Char. Device: dev:flash1
        Total Block Count: 7733248
        Block Index Range: 119296 - 7852543
        Block Size in bytes: 512

        Char. Device: dev:flash2
        Total Block Count: 7733248
        Block Index Range: 7852544 - 15585791
        Block Size in bytes: 512

        ===============================================


        Chivas_1,3>


        Chivas_1,3> flasherase 7852544 -u:512 -m:128

        Block 7852544-7852671 (2/000-127): 0.6 secs for 1 iteration.
        Block 7852672-7852799 (2/128-255): 0.6 secs for 1 iteration.
        Block 7852800-7852927 (2/256-383): 0.6 secs for 1 iteration.
        Block 7852928-7853055 (2/384-511): 0.6 secs for 1 iteration.


        :param kwargs:
        :return:
        """
        aplib.set_container_text('EMMC ERASE')
        log.info('STEP: EMMC ERASE.')

        uut_prompt = self._mode_mgr.uut_prompt_map['STARDUST']
        log.debug("Prompt={0}".format(uut_prompt))

        linecard_device_instance = self._ud.uut_config['linecard']['device_instance']
        slot_num = str(linecard_device_instance)[:1]
        log.info("slot_num : '{}'".format(slot_num))

        self._uut_conn.send('GetRawMMCFlashInfo\r', expectphrase=uut_prompt, regex=True)
        console_data = str(self._uut_conn.recbuf)
        dev_flash = console_data.split('[Slot 0{}]'.format(slot_num))[1].split(' ')[2][0:10]
        log.info("dev_flash : '{}'".format(dev_flash))

        self._uut_conn.send('FlashShowInfo\r', expectphrase=uut_prompt, regex=True)

        console_data = str(self._uut_conn.recbuf)
        flash_index_range = console_data.split('{}'.format(dev_flash))[1].split(' ')[8]
        log.info("flash_index_range : '{}'".format(flash_index_range))

        self._uut_conn.send('flasherase {} -u:512 -m:128\r'.format(flash_index_range), expectphrase=uut_prompt, regex=True)

        # TODO:  done in diags

        return aplib.PASS

    @apollo_step
    def emmc_partition_format(self, **kwargs):
        """ eMMC Partition and format
        The SUP must be in IOS mode to perform this task.
        This means ALL linecards MUST sync to the sub-sequence point BEFORE going to IOS!

        Example:
        ---------------------------------------------------------------------
        Switch#conf t

        Enter configuration commands, one per line.  End with CNTL/Z.
        Switch(config)#no logging console

        Switch(config)#end

        Switch#
        Switch#conf t

        Enter configuration commands, one per line.  End with CNTL/Z.
        Switch(config)#platform shell

        Switch(config)#end

        Switch#request platform software system shell

        Activity within this shell can jeopardize the functioning of the system.
        Are you sure you want to continue? [y/n] y

        2018/02/12 23:19:56 : Shell access was granted to user <anon>; Trace file: , /crashinfo/tracelogs/system_shell_R0-0.21000_0.20180212231956.bin
        **********************************************************************
        Activity within this shell can jeopardize the functioning
        of the system.
        Use this functionality only under supervision of Cisco Support.

        Session will be logged to:
          crashinfo:tracelogs/system_shell_R0-0.21000_0.20180212231956.bin
        **********************************************************************
        Terminal type 'network' unknown.  Assuming vt100

        [Switch_RP_0:/]$
        [Switch_RP_0:/]$

        [Switch_RP_0:/]$ cd bootflash

        [Switch_RP_0:/bootflash]$ ./vbd_partition.sh a

        dev=/dev/vbda, mountpoint=/vbda1
        There appears no partition table for device /dev/vbda
        umount: /vbda1: mountpoint not found

        Welcome to fdisk (util-linux 2.27.1).
        Changes will remain in memory only, until you decide to write them.
        Be careful before using the write command.

        Device does not contain a recognized partition table.
        Created a new DOS disklabel with disk identifier 0x95508a77.

        Command (m for help): Partition type
           p   primary (0 primary, 0 extended, 4 free)
           e   extended (container for logical partitions)
        Select (default p): Partition number (1-4, default 1): First sector (2048-7733247, default 2048): Last sector, +sectors or +size{K,M,G,T,P} (2048-7733247, default 7733247):
        Created a new partition 1 of type 'Linux' and of size 2 GiB.

        Command (m for help): Partition type
           p   primary (1 primary, 0 extended, 3 free)
           e   extended (container for logical partitions)
        Select (default p): Partition number (2-4, default 2): First sector (4196352-7733247, default 4196352): Last sector, +sectors or +size{K,M,G,T,P} (4196352-7733247, default 7733247):
        Created a new partition 2 of type 'Linux' and of size 128 MiB.

        Command (m for help): Partition type
           p   primary (2 primary, 0 extended, 2 free)
           e   extended (container for logical partitions)
        Select (default p): Partition number (3,4, default 3): First sector (4458496-7733247, default 4458496): Last sector, +sectors or +size{K,M,G,T,P} (4458496-7733247, default 7733247):
        Created a new partition 3 of type 'Linux' and of size 1.6 GiB.

        Command (m for help): Disk /dev/vbda: 3.7 GiB, 3959422976 bytes, 7733248 sectors
        Units: sectors of 1 * 512 = 512 bytes
        Sector size (logical/physical): 512 bytes / 512 bytes
        I/O size (minimum/optimal): 512 bytes / 512 bytes
        Disklabel type: dos
        Disk identifier: 0x95508a77

        Device     Boot   Start     End Sectors  Size Id Type
        /dev/vbda1         2048 4196351 4194304    2G 83 Linux
        /dev/vbda2      4196352 4458495  262144  128M 83 Linux
        /dev/vbda3      4458496 7733247 3274752  1.6G 83 Linux

        Command (m for help): The partition table has been altered.
        Calling ioctl() to re-read partition table.
        Syncing disks.

        + mkfs.ext2 -F /dev/vbda1
        % Generating 2048 bit RSA keys, keys will be non-exportable...
        [OK] (elapsed time was 0 seconds)
        + mkfs.ext2 -F /dev/vbda2
        + mkfs.ext2 -F /dev/vbda3
        + tune2fs -c 0 -i 0 /dev/vbda1
        + /bin/mkdir -p /vbda1
        + mount /dev/vbda1 /vbda1
        + rm -rf /vbda1/lost+found
        + umount /vbda1
        + set +x
        [Switch_RP_0:/bootflash]$

        [Switch_RP_0:/bootflash]$ fdisk /dev/vbda -l

        Disk /dev/vbda: 3.7 GiB, 3959422976 bytes, 7733248 sectors
        Units: sectors of 1 * 512 = 512 bytes
        Sector size (logical/physical): 512 bytes / 512 bytes
        I/O size (minimum/optimal): 512 bytes / 512 bytes
        Disklabel type: dos
        Disk identifier: 0x95508a77

        Device     Boot   Start     End Sectors  Size Id Type
        /dev/vbda1         2048 4196351 4194304    2G 83 Linux
        /dev/vbda2      4196352 4458495  262144  128M 83 Linux
        /dev/vbda3      4458496 7733247 3274752  1.6G 83 Linux
        [Switch_RP_0:/bootflash]$ exit

        exit
        Session log crashinfo:tracelogs/system_shell_R0-0.21000_0.20180212231956.bin closed.

        Switch#	?????

        :menu: (enable=True, name=EMMC PARTITION, section=Linux, num=10, args=None)

        :param kwargs:
        :return:
        """
        aplib.set_container_text('eMMC')
        log.info('STEP: Partition & format eMMC on the Linecard.')

        # Ensure IOSE mode first.
        if self._mode_mgr.current_mode not in ['IOSE', 'IOS', 'SYSSHELL']:
            log.error("The eMMC partitioning requires IOSE or SYSSHELL mode prior to running.")
            return aplib.FAIL

        # System Shell
        if not self._mode_mgr.goto_mode('SYSSHELL'):
            log.error("Cannot enter the System Shell.  Check IOS.")
            return aplib.FAIL

        # Linecard details
        linecard_device_instance = self._ud.uut_config['linecard']['device_instance']
        linecard_physical_slot = self._ud.uut_config['linecard']['physical_slot']
        linecard_slot_vdbs = self._ud.uut_config['linecard']['slot_map']
        log.debug("Linecard instance      = {0}".format(linecard_device_instance))
        log.debug("Linecard physical slot = {0}".format(linecard_physical_slot))
        log.debug("Linecard slot vdbs     = {0}".format(linecard_slot_vdbs))

        # Run macro
        self._uut_conn.send('cd bootflash\r', expectphrase='bootflash]$')
        self._uut_conn.send('./vbd_partition.sh {0}\r'.format(linecard_slot_vdbs), expectphrase='bootflash]$')
        self._uut_conn.send('\r', expectphrase='bootflash]$')
        self._uut_conn.send('fdisk /dev/vbd{0} -l\r'.format(linecard_slot_vdbs), expectphrase='bootflash]$')
        time.sleep(2.0)

        # Collect results
        pat = '(/dev/vbd[a-h][0-9]) [ \t]* [0-9]+ [ \t]*[0-9]+ [ \t]*[0-9]+ [ \t]*([\S]+) [ \t]*[0-9]+ '
        p = re.compile(pat)
        m = p.findall(mm.uut_conn.recbuf)
        lc_partition_sizes = dict(m)
        LC_PARTITION_SIZE_REF = {'/dev/vbd{0}1'.format(linecard_slot_vdbs): '2G',
                                 '/dev/vbd{0}2'.format(linecard_slot_vdbs): '128M',
                                 '/dev/vbd{0}3'.format(linecard_slot_vdbs): '[12][\.0-9]*G'}

        # Evaluate
        result = True
        for k in sorted(LC_PARTITION_SIZE_REF.keys()):
            actual_size = lc_partition_sizes.get(k, 'missing')
            expected_size = LC_PARTITION_SIZE_REF[k]
            if not re.match(expected_size, actual_size):
                log.error("Partition {0} : {1:<5} (Expected={2})".format(k, actual_size, expected_size))
                result = False
            else:
                log.info("Partition {0} : {1:<5} Good.".format(k, actual_size))

        # Return to IOSE
        if not self._mode_mgr.goto_mode('IOSE'):
            log.error("Cannot enter the System Shell.  Check IOS.")
            return aplib.FAIL

        return aplib.PASS if result else aplib.FAIL

    # ==================================================================================================================
    # USER/Internal Methods  (step support)
    # ==================================================================================================================
    @func_details
    def _get_supdp_serdeseye(self, asic_core_count, supdp_options=''):
        """ Get SUPDP SerdesEye
        :param asic_core_count:
        :param verbose:
        :param supdp_options:

        sample SUPDP serdes eye data:
        ???
        :return:
        """

        def __generate_supdp_serdeseye(asic_core_count, supdp_cmd_name, supdp_pattern, Eye, supdp_options=''):
            """ Generate SIF SerdesEye
            :param asic_core_count:
            :param supdp_cmd_name:
            :param supdp_pattern:
            :param Eye:
            :param supdp_options:
            :return:
            """
            verbose = True if self._ud.verbose_level > 1 else False
            log.info('SUPDP Serdes Eye GENERATE (generic)')

            supdp = {}
            failures = []

            # Regex for all entries: summary, min, and max
            p = re.compile(supdp_pattern)

            # Get and Check Serdes Eye
            # TODO: put code here!

            if failures or len(supdp) == 0:
                for failure in failures:
                    log.error(failure)
                log.error('get_supdp_serdeseye: FAIL. Failed to retreive valid SupDPSerdesEye.')
                return False

            common_utils.print_large_dict(supdp, title='supdp') if verbose else None
            return sif

        log.info('SUPDP Serdes Eye START (generic)')

        supdp_cmd_name = 'SupDPSerdesEye'
        Eye = namedtuple('Eye', 'Channel Amin AminP AminN Ap An EScan LScan EL SyncCnt ErrCnt Result')
        # Regex for all entries: summary, min, and max
        supdp_pattern = '(?m)([A-Z][0-9])[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d]+)' \
                        '[ \t]+([\d]+)[ \t]+([\d\S]+)[ \t]+([\d\S]+)[ \t]+([\d]?)[ \t]*([\S]+)[\r\n]+'

        supdp = __generate_supdp_serdeseye(asic_core_count,
                                           supdp_cmd_name=supdp_cmd_name,
                                           supdp_pattern=supdp_pattern,
                                           Eye=Eye,
                                           supdp_options=supdp_options)

        return supdp

    @func_details
    def _check_supdp_serdeseye(self, current_supdp):
        """ Check SUPDP SerdesEye

        :param current_supdp:
                ???
        :return:
        """
        ret = True if current_supdp else False
        for k, v in current_supdp.items():
            if v.Result.upper() == 'PASS':
                pass
            elif v.Result.upper() == 'IGNORE':
                ignored_channel = "SUPDP SerDesEye IGNORED: {0:<24} = {1}".format(k, v)
                log.warning(ignored_channel)
            else:
                failed_channel = "SUPDP SerDesEye FAILED: {0:<24} = {1}".format(k, v)
                log.error(failed_channel)
                ret = False
        if ret:
            log.info('SUPDP SerDesEye results are good.')
        else:
            log.error('SUPDP SerDesEye results indicate failure(s).')
        return ret

    @func_details
    def _get_nru_serdeseye(self, nru_options=''):
        """ Get NIF SerdesEye
        :param uplink_test_card: 'Hilbert', 'Makron', etc. or None
        :param eye_option:

        Sample Nif serdes Eye data:
        N48P_CSR> DopNifSerdesEyeMeasure 0 -i:10 -pd:0 -pu:4
        Phy Serdes Tx -> Doppler Nif Serdes Rx
        Note: Skip 40G or 10/100M speed or Fourier 1G ports.

        Port  Amin(mV) AminP  AminN  Ap(mV) An(mV) EScan LScan E+L PRBS PS   PE  P/F
        ----- -------- ------ ------ ------ ------ ----- ----- --- ---- --- --- ----
        1-4    170.0   170.0  195.0  212.5  235.0    10    11   22   7+  10   0  Pass
        1-4    172.5   172.5  195.0  212.5  235.0    11    12   23   (Max)       Pass
        1-4    170.0   170.0  195.0  212.5  235.0    10    11   21   (Min)       Pass
        5-8    177.5   180.0  177.5  220.0  217.5    10    10   20   7+  10   0  Pass
        5-8    180.0   182.5  180.0  222.5  217.5    10    11   21   (Max)       Pass
        5-8    177.5   180.0  177.5  220.0  217.5    10    10   20   (Min)       Pass
        9-12   182.5   187.5  182.5  227.5  220.0    12    12   24   7+  10   0  Pass
        9-12   185.0   187.5  185.0  230.0  220.0    12    12   24   (Max)       Pass
        9-12   182.5   187.5  182.5  227.5  220.0    12    12   24   (Min)       Pass
        13-16  177.5   177.5  210.0  212.5  240.0    10    11   21   7+  10   0  Pass
        13-16  177.5   177.5  210.0  212.5  240.0    10    11   21   (Max)       Pass
        13-16  177.5   177.5  210.0  212.5  240.0    10    11   21   (Min)       Pass
        17-20  187.5   187.5  200.0  225.0  235.0    9     11   20   7+  10   0  Pass
        17-20  190.0   190.0  202.5  227.5  237.5    10    11   21   (Max)       Pass
        17-20  187.5   187.5  200.0  225.0  235.0    9     11   20   (Min)       Pass
        21-24  162.5   162.5  187.5  210.0  232.5    11    13   24   7+  10   0  Pass
        21-24  165.0   165.0  190.0  212.5  235.0    11    13   24   (Max)       Pass
        21-24  162.5   162.5  187.5  210.0  232.5    11    13   24   (Min)       Pass
        25-28  157.5   157.5  175.0  202.5  222.5    10    13   23   7+  10   0  Pass
        25-28  157.5   157.5  177.5  202.5  222.5    11    13   24   (Max)       Pass
        25-28  157.5   157.5  175.0  202.5  222.5    10    13   23   (Min)       Pass
        29-32  177.5   210.0  177.5  247.5  212.5    11    11   22   7+  10   0  Pass
        29-32  180.0   212.5  180.0  250.0  215.0    11    12   23   (Max)       Pass
        29-32  177.5   210.0  177.5  247.5  212.5    11    11   22   (Min)       Pass
        33-36  205.0   205.0  207.5  237.5  237.5    11    12   23   7+  10   0  Pass
        33-36  207.5   207.5  207.5  237.5  240.0    12    12   24   (Max)       Pass
        33-36  205.0   205.0  207.5  237.5  237.5    11    12   23   (Min)       Pass
        37-40  177.5   187.5  177.5  222.5  220.0    11    12   23   7+  10   0  Pass
        37-40  180.0   190.0  180.0  225.0  222.5    11    13   24   (Max)       Pass
        37-40  177.5   187.5  177.5  222.5  220.0    11    12   23   (Min)       Pass
        41-44  167.5   175.0  167.5  217.5  207.5    11    12   23   7+  10   0  Pass
        41-44  170.0   177.5  170.0  220.0  207.5    11    13   24   (Max)       Pass
        41-44  167.5   175.0  167.5  217.5  207.5    11    12   23   (Min)       Pass
        45-48  197.5   197.5  200.0  230.0  232.5    12    13   25   7+  10   0  Pass
        45-48  200.0   200.0  202.5  232.5  235.0    12    13   25   (Max)       Pass
        45-48  197.5   197.5  200.0  230.0  232.5    12    13   25   (Min)       Pass


        Phy Serdes Tx -> Doppler Nif Serdes Rx
        Note: For uplink 1G ports, no eye measurement, checking only PRBS sync/error.
              Fourier 1G ports will be skipped.

        Port  Amin(mV) Ap(mV) An(mV) Az(mV) EScan LScan E+L Amin/Ap PRBS PS   PE  P/F
        ----- -------- ------ ------ ------ ----- ----- --- ------- ---- --- --- ----
        1-4    167.7   183.3  179.4   0.0    13    12   25   91.48%  7+  10   0  Pass
        1-4    167.7   183.3  179.4   0.0    13    13   26   91.48%  (Max)       Pass
        1-4    167.7   183.3  179.4   0.0    13    12   25   91.48%  (Min)       Pass
        5-8    187.2   202.8  202.8   0.0    12    12   25   93.45%  7+  10   0  Pass
        5-8    191.1   202.8  206.7   0.0    13    13   26   94.23%  (Max)       Pass
        5-8    187.2   202.8  202.8   0.0    12    12   25   92.30%  (Min)       Pass
        9-12   163.8   175.5  175.5   0.0    12    13   25   91.90%  7+  10   0  Pass
        9-12   163.8   179.4  175.5   0.0    13    13   26   93.33%  (Max)       Pass
        9-12   163.8   175.5  175.5   0.0    12    13   25   91.30%  (Min)       Pass

    N48U_CSR> dopnifserdeseye --help
    ERR: DopNifSerdesEyeMeasure: Unknown option flag: "--help"


    USAGE: DopNifSerdesEyeMeasure [<portNum>] [<-pd:<downlink PRBS>] [<-pu:<uplink P
    RBS>] [-o:<option>][-i:<iteration>] [-z] [-t:<PRBSTestTime>]
        <portNum> -- front-end port number (0 for all ports) (default 0)
        -pd:<downlink ports PRBS> --
           0: PRBS7+ (default)
           1: PRBS7-
           2: PRBS23+
           3: PRBS23-
           4: PRBS31+
           5: PRBS31-


        -pu:<Uplink ports PRBS> --
           0: PRBS7+
           1: PRBS7-
           2: PRBS23+
           3: PRBS23-
           4: PRBS31+ (default)
           5: PRBS31-


        -o:<option> --
           0: Nif Serdes Tx -> Nif Serdes Rx with Nif Serdes loopback
           1: Phy Serdes Tx -> Nif Serdes Rx (default)
           2: Nif Serdes Tx -> Nif Serdes Rx with Phy Serdes loopback
           3: Nif Serdes Tx -> Phy Serdes Rx
           4: real traffic with no PRBS setup
           5: Phy Serdes Tx -> Nif Serdes Rx for downlink ports
              Nif Serdes Tx -> Nif Serdes Rx with ext. LB for uplink ports


        -i:<iteration> -- number of iterations (default 1)
        -z -- zero Az (default non-zero)
        -t:<PRBSTestTime> -- time in msec for PRBS to run prior to checking
             sync and error. Default 10msec.

        :return:
        """

        def __generate_nru_serdeseye(nru_cmd, nru_pattern, Eye):
            """ Generate NRU SerdesEye
            :param (str) nru_cmd:
            :param (str) nru_pattern:
            :param (named tuple) eye:
            :return:
            """
            verbose = True if self._ud.verbose_level > 1 else False
            log.info('NRU Serdes Eye GENERATE (generic)')

            # Output
            nru = {}

            # Run command
            self._clear_recbuf(force=True)
            log.debug("prompt={0}".format(self._uut_prompt))
            self._uut_conn.send(nru_cmd, expectphrase='.*', timeout=60, regex=True)
            time.sleep(1.0)
            log.debug("Waiting for NIF completion...")
            self._uut_conn.waitfor(self._uut_prompt, timeout=500, regex=True)
            time.sleep(5.0)

            # Parse output
            p = re.compile(nru_pattern)
            m = p.findall(self._uut_conn.recbuf)
            for i in m:
                tag = 'Sum' if not re.match('([(]?Max[)])|([(]?Min[)])', i[-4]) else i[-4][1:4]
                nru[i[0], tag] = Eye._make(i)

            common_utils.print_large_dict(nru, title='nru') if verbose else None

            if not nru:
                log.error('FAILED. Failed to retrieve NRU result.')
                m = re.search('\*\*\*ERR: .*?[\n\r]', self._uut_conn.recbuf)
                log.debug(m.group(0)) if m else None
                return None
            return nru

        log.info('NRU Serdes Eye START (generic)')

        common_utils.uut_comment(self._uut_conn, 'NRU', 'SerDes Eye Metric ASIC')

        # Get NRUSerdesEye
        Eye = namedtuple('Eye', 'RxTx Amin AminP AminN Ap An EScan LScan EL PRBS PS PE Result')
        nru_cmd = 'NRUSerdesEyeMeasure {0} -i:3 -s:{1}\r'.format(nru_options, self._ud.physical_slot)
        # Regex for Summary, Min, Max
        nru_pattern = '(?m)([\d]+-*[\d]*)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+' \
                      '([\d.]+)[ \t]+([\d]+)[ \t]+([\d]+)[ \t]+([\d\S]+)[ \t]+([\S]+)[ \t]*([\d]*)[ \t]*([\d]*)' \
                      '[ \t]*([\S]+)[\r\n]*'

        nru = __generate_nru_serdeseye(nru_cmd, nru_pattern, Eye)

        return nru

    @func_details
    def _check_nru_serdeseye(self, current_nru):
        """ Check NRU SerdesEye
        :param current_nif:

        Current NRU Data sample:
        ???
        :return:
        """
        ret = True if current_nru else False
        for k, v in current_nru.items():
            if v.Result.upper() != 'PASS':
                failed_channel = "NRU SerDesEye FAILED: {0:<24} = {1}".format(k, v)
                log.error(failed_channel)
                ret = False
        if ret:
            log.info('NRU SerDesEye results are good.')
        else:
            log.error('NRU SerDesEye results indicate failure(s).')
        return ret
