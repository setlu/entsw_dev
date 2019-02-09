"""
========================================================================================================================
Linux General Module
========================================================================================================================

This module contains various utilities and support functions to operate specifically on the diagnostic
Linux kernel for the product families:
    1. Cisco Catalyst 2 series (WS-C2900 & C9200)
    2. Cisco Catalyst 3 series (WS-C3850/C3650 & C9300)
    3. Cisco Catalyst 4 series (WS-C4000 & C9400)
    4. Cisco Catalyst 5 series (C9500)

IMPORTANT: All functions use only the UUT connection object and the UUT prompt pattern.
           All general Linux utilities should be machine agnostic!

========================================================================================================================
"""

# Python
# ------
import sys
import os
import time
import re
import logging
import collections
from ast import literal_eval

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Specific
# -----------
from ..utils.common_utils import func_details
from ..utils.common_utils import func_retry
from ..utils.common_utils import apollo_step
from ..utils.common_utils import shellcmd
from ..utils.common_utils import touch
from ..utils.common_utils import validate_ip_addr
from ..utils.common_utils import get_system_ip_and_mask

__title__ = "Linux (diag kernel) General Module"
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


class Linux(object):
    """ Linux
    """
    MountDescriptor = collections.namedtuple('MountDescriptor', 'device dir')
    Disk = collections.namedtuple('Disk', 'size gsize bytes devices')
    RECBUF_TIME = 5.0
    FDISK = {'checked': False, 'cmd': 'fdisk', 'param': ''}

    def __init__(self, mode_mgr, ud):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt = self._mode_mgr.uut_prompt_map['LINUX']
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def set_network_interface(self, **kwargs):
        """ Set Network Interface
        Set the UUT network interface via Linux kernel.
        :menu: (enable=True, name=SET NET INTF, section=Linux, num=1, args=None)
        :param (dict) kwargs:
        :return (str): aplib.PASS/FAIL
        """
        # Process input (use uut_config defaults)
        ip = kwargs.get('uut_ip', self._ud.uut_config.get('uut_ip', ''))
        server_ip = kwargs.get('server_ip', self._ud.uut_config.get('server_ip', ''))
        netmask = kwargs.get('netmask', self._ud.uut_config.get('netmask', ''))

        aplib.set_container_text('LINUX SET NET INTF {0}/{1}'.format(ip, netmask))

        # Check mode
        if not self._mode_mgr.is_mode('LINUX'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'LINUX' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong UUT mode for set_network_interface."

        # Embedded wrapper for retries (manual only; no retry for automation)
        @func_retry(max_attempts=self._ud.max_attempts, ask_yn='Check Download Interface cables and retry:')
        def __set_uut_network_params():
            if self.set_uut_network_params(ip=ip, netmask=netmask, server_ip=server_ip):
                result = self.ping(ip=server_ip, count=3)
                msg = '' if result else "Cannot ping the network after LINUX interface setup."
            else:
                result = False
                msg = "Network setup in Linux was unsuccessful."
                log.error(msg)
            return result, msg

        # Perform the action
        result, msg = __set_uut_network_params()
        return aplib.PASS if result else aplib.FAIL, msg

    @apollo_step
    def format_flash(self, **kwargs):
        """ Format Flash
        Process as follows:
            1. Ensure Linux mode
            2. Partition & Format
            3. Create flash map dir (also mounts primary device)
        :menu: (enable=True, name=FORMAT primary, section=Linux, num=1, args={'disk_type': 'primary', 'ask': True})
        :menu: (enable=True, name=FORMAT secondary, section=Linux, num=1, args={'disk_type': 'secondary', 'ask': True})
        :param (dict) kwargs:
        :return (str): aplib.PASS/FAIL
        """
        # Defaults
        disk_partition_tables_default = self._ud.disk_partition_tables if hasattr(self._ud, 'disk_partition_tables') else None

        # Process input
        force = kwargs.get('force', False)
        ask = kwargs.get('ask', False)
        disk_type = kwargs.get('disk_type', 'primary')
        disk_partition_tables = kwargs.get('disk_partition_tables', disk_partition_tables_default)
        pm_func_name = kwargs.get('partition_macro_func', self._ud.uut_config.get('partition_macro_func', None))
        partition_macro_func = getattr(self._callback, pm_func_name) if pm_func_name and hasattr(self._callback, pm_func_name) else None
        pim_func_name = kwargs.get('partition_init_macro_func', self._ud.uut_config.get('partition_init_macro_func', None))
        partition_init_macro_func = getattr(self._callback, pim_func_name) if pim_func_name and hasattr(self._callback, pim_func_name) else None

        # Check mode
        if not self._mode_mgr.is_mode('LINUX'):
            log.warning("Preparing Linux mode...")
            if not self._mode_mgr.goto_mode('LINUX', kwargs={'do_primary_mount': False}):
                log.warning("Linux mode from flash unsuccessful; attempting network load...")
                # Assume a blank flash therefore need to boot linux from network.
                if not self._mode_mgr.goto_mode('LINUX', kwargs={'device_name': 'tftp', 'do_primary_mount': False}):
                    log.error("Unable to make Linux ready.")
                    return aplib.FAIL, "PRE-REQUISITE- Cannot get to the Linux kernel."

        # Check disk enumeration since it will be needed for partitioning & formatting.
        if 'disk_enums' not in self._ud.uut_config:
            self._ud.uut_config['disk_enums'] = None
        else:
            log.debug("Using existing enumeration.")

        # Perform the action
        if not self._format_device(disk_type,
                                   partition_tables=disk_partition_tables,
                                   disk_enums=self._ud.uut_config['disk_enums'],
                                   force=force,
                                   ask=ask,
                                   partition_macro_func=partition_macro_func,
                                   partition_init_macro_func=partition_init_macro_func):
            errmsg = "Unable to format device."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # All newly formatted flash space needs the flash device mapping directory.
        # In order to create that directory the primary device needs to be mounted.
        if aplib.FAIL in self.create_flash_mapping():
            errmsg = "Unable to map flash device."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        return aplib.PASS

    @apollo_step
    def create_flash_mapping(self, **kwargs):
        """  Create Flash Mapping
        Make 'flash:' a mapped directory
        Note: The filesystem MUST be mounted first!!!
        :menu: (enable=True, name=MAP FLASH, section=Linux, num=1, args=None)
        :param (dict) kwargs:
        :return (str): aplib.PASS/FAIL
        """

        # Process input
        disk_type = kwargs.get('disk_type', 'primary')
        device_numbers = kwargs.get('device_numbers', self._ud.uut_config['flash_device']['device_num'])
        log.debug("Disk Type={0},  Device Numbers={1}".format(disk_type, device_numbers))

        # Check mode
        if not self._mode_mgr.is_mode('LINUX'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'LINUX' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong UUT mode for create_flash_mapping."

        # Ensure a mounted location first
        mresult, _ = self.mount_disks(device_numbers=device_numbers,
                                      disk_type=disk_type,
                                      device_mounts=self._ud.uut_config['device_mounts'],
                                      disk_enums=self._ud.uut_config['disk_enums'])
        if not mresult:
            errmsg = "Cannot create flash dir due to mount error."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Perform the action
        map_dir = self._ud.get_flash_mapped_dir()
        if not map_dir:
            return aplib.FAIL, "Cannot get a flash mapped directory from uut_config."
        log.info("Flash map = {0}".format(map_dir))
        result = self.make_flash_dir_map(map_dir)
        if result:
            self.cd(map_dir)
        return aplib.PASS if result else (aplib.FAIL, "Cannot make the dir for flash mapping.")

    @apollo_step
    def tftp(self, **kwargs):
        """ TFTP Transfers
        Covers both GET and PUT.
        :menu: (enable=True, name=TFTP get, section=Linux, num=1, args={'direction': 'get'})
        :menu: (enable=True, name=TFTP put, section=Linux, num=1, args={'direction': 'put'})
        :menu: (enable=True, name=TFTP DIR get, section=Linux, num=06c, args={'direction': 'get', 'dir_transfer': True})
        :param (dict) kwargs:
        :return (str): aplib.PASS/FAIL
        """

        # Process input
        force = kwargs.get('force', True)
        src_files = kwargs.get('src_files', None)
        dst_files = kwargs.get('dst_files', None)
        direction = kwargs.get('direction', '')
        dir_transfer = kwargs.get('dir_transfer', False)
        ip = kwargs.get('uut_ip', self._ud.uut_config.get('uut_ip', ''))
        server_ip = kwargs.get('server_ip', self._ud.uut_config.get('server_ip', ''))
        netmask = kwargs.get('netmask', self._ud.uut_config.get('netmask', ''))

        # Check mode
        if not self._mode_mgr.is_mode('LINUX'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'LINUX' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL

        # Source Files
        if not src_files:
            answer = aplib.ask_question("TFTP {0}: Enter source files (',' separated):".format(direction.upper()))
            if answer == '':
                log.error("TFTP operation must have a source file provided!")
                return aplib.FAIL
            answer2 = re.sub(r'[a-zA-Z0-9.\-_:/]+', lambda m: '"{0}"'.format(m.group(0)), answer)
            log.debug("Src Response = {0}".format(answer2))
            src_files = literal_eval(answer2)
            # Ensure a list of tuples and/or strings when they mix.
            if (isinstance(src_files, tuple) and not re.match("[0-9]{1,32}", "{0}".format(src_files[1]))) \
                    or any([isinstance(src_files[i], tuple) for i in range(0, len(src_files))]):
                src_files = [elem for elem in src_files]

        # Destination Files
        if not dst_files:
            answer = aplib.ask_question("TFTP {0}: Enter destination files (',' separated):".format(direction.upper()))
            if answer == 'SAME':
                dst_files = src_files
            elif answer != '':
                answer2 = re.sub(r'[a-zA-Z0-9.\-_:/]+', lambda m: '"{0}"'.format(m.group(0)), answer)
                log.debug("Dst Response = {0}".format(answer2))
                dst_files = literal_eval(answer2)
                # Ensure a list of tuples and/or strings when they mix.
                if (isinstance(dst_files, tuple) and not re.match("[0-9]{1,32}", "{0}".format(dst_files[1]))) \
                        or any([isinstance(dst_files[i], tuple) for i in range(0, len(dst_files))]):
                    dst_files = [elem for elem in dst_files]
        elif dst_files == 'SAME':
            dst_files = None

        # Perform the action
        if not dir_transfer:
            result = self.transfer_tftp_files(src_files=src_files,
                                              dst_files=dst_files,
                                              direction=direction,
                                              server_ip=server_ip,
                                              ip=ip,
                                              netmask=netmask,
                                              force=force)
        else:
            result = self.transfer_tftp_directory(src_dir=src_files,
                                                  dst_dir=dst_files,
                                                  direction=direction,
                                                  server_ip=server_ip,
                                                  ip=ip,
                                                  netmask=netmask,
                                                  force=force)

        log.debug("TFTP consolidated transfer result = {0}".format(result))

        return aplib.PASS if result else (aplib.FAIL, "Incomplete TFTP transfer.")

    @apollo_step
    def set_termial_width(self, **kwargs):
        """ Set Linux Terminal Width (step)

        For some reason Linux terminal width is limited when connetion was open, which causes problem when sending long
        commands. Commond gets truncated to multiple lines with returns in between.

        This step set the width to 200 via stty.

        :param kwargs:
        :return:
        """
        self._uut_conn.sende('stty rows 40 cols 200\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        return aplib.PASS

    # ==================================================================================================================
    # USER METHODS   (step support)
    # ==================================================================================================================
    @func_details
    def get_device_files(self, sub_dir='', file_filter='.*?', attrib_flags='-ld'):
        """ Get Device Files
        --------------------
        Get all files for the given subdir.
        Sort by time stamp; most recent first.
        Sample output given below:

        /mnt/user # ls -al --color=never
        drwxrwxrwx    3 root     root          4096 Mar 24  2015 .
        drwxr-xr-x    6 root     root          4096 Feb  8 17:16 ..
        -rwxr-xr-x    1 root     root          1623 Mar 16  2015 17-FibSchrod-03.SBC_cfg
        -rwxrwxrwx    1 root     root          9979 Mar 24  2015 17-G24CSR-16.SBC_cfg
        drwxrwxrwx    2 root     root          4096 Mar 16  2015 kirch
        -rwxr-xr-x    1 root     root        524288 Mar 24  2015 morseG_01_00_A0.hex
        -rwxrwxrwx    1 root     root      23978872 Feb  4  2015 stardust_012315
        -rwxrwxrwx    1 root     root      22337271 Mar 24  2015 vmlinux2013Sep23.mzip.SSA

        :param sub_dir: Target subdirectory to list.
        :param file_filter: Regex pattern filter for file names.
        :param attrib_flags:  Use "d", "l', and "-" for dir, link, and file. (Default is get everything.)
        :return:
        """
        files = []
        try:

            @func_retry
            def __ls():
                self._uut_conn.send('ls -alt --color=never {0}\r'.format(sub_dir), expectphrase=self._uut_prompt, timeout=30,
                              regex=True)
                time.sleep(self.RECBUF_TIME)
                attrib_filter = '(?:[{0}]'.format(attrib_flags) + '(?:[-rwx]{3}){3})'
                pat_prefix = r"[ \t]*{0}[ \t]+[0-9]+[ \t]+[\S]+[ \t]+[\S]+[ \t]+[0-9]+[ \t]+([\S]+[ \t]+[0-9]+[ \t]+[:0-9]+)".format(
                    attrib_filter)
                p = re.compile(r"{0}[ \t]+({1})(?=(?: -> .*[\n\r]+)|[\n\r]+)".format(pat_prefix, file_filter))
                return p.findall(self._uut_conn.recbuf)

            m = __ls()
            if m:
                i = 0
                while i < len(m):
                    if m[i][1] == '.' or m[i][1] == '..':
                        m.pop(i)
                    else:
                        i += 1
                # Just get filename; no need to use timestamp since already sorted.
                # (Keep the timestamp capture; future use?)
                files = [f for d, f in m] if m else []
            else:
                log.debug("No files found that match the criteria.")
        finally:
            return files

    @func_details
    def make_flash_dir_map(self, full_path_dir):
        """ Make Flash Dir Map
        ----------------------
        Make a directory in the mounted filesystem which will map to the "flash:" device designation.
        This is typically for linux kernel based systems.
        :param full_path_dir: Fully qualified path from root mount.
        :return:
        """
        ret = True
        self._uut_conn.send('ls -al --color=never {0}\r'.format(full_path_dir), expectphrase=self._uut_prompt, timeout=60,
                      regex=True)
        time.sleep(self.RECBUF_TIME)
        if 'No such file or directory' in self._uut_conn.recbuf:
            self._uut_conn.send('mkdir -p {0}\r'.format(full_path_dir), expectphrase=self._uut_prompt, timeout=60, regex=True)
            self._uut_conn.send('chmod 777 {0}\r'.format(full_path_dir), expectphrase=self._uut_prompt, timeout=60, regex=True)
            self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
            self._uut_conn.send('ls -al --color=never {0}\r'.format(full_path_dir), expectphrase=self._uut_prompt, timeout=60,
                          regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'No such file or directory' in self._uut_conn.recbuf:
                log.error("Cannot create the flash dir: {0}".format(full_path_dir))
                ret = False
            else:
                log.info("Flash mapped dir creation successful: {0}".format(full_path_dir))
        else:
            log.info("Flash mapped directory is already available.")
        return ret

    @func_details
    def set_uut_network_params(self, ip=None, netmask=None, server_ip=None, broadcast=None, mac=None):
        """ Set Network Ethernet Interface Params
        -----------------------------------------
        Set the network config under Linux
        :param mac: Only used to confirm the interface (optional).
        :param ip:
        :param netmask:
        :param server_ip:
        :param broadcast:
        :return:
        """

        # Check input params
        if not validate_ip_addr(ip):
            log.error("Need a valid IP Address.")
            return False
        if not validate_ip_addr(netmask):
            log.error("Need a valid Netmask.")
            return False
        if broadcast and not validate_ip_addr(broadcast):
            log.error("Need a valid Broadcast IP.")
            return False

        # Configure
        cmd = 'ifconfig eth0 {0} netmask {1}\r'.format(ip, netmask)
        if broadcast:
            cmd += " broadcast {0}".format(broadcast)
        self._uut_conn.send('ifconfig eth0 down\r', expectphrase=self._uut_prompt, regex=True)
        self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, regex=True)
        if server_ip:
            self._uut_conn.send('route add default gw {0} eth0\r'.format(server_ip), expectphrase=self._uut_prompt, regex=True)
        # Bring up
        self._uut_conn.send('ifconfig eth0 up\r', expectphrase=self._uut_prompt, regex=True)
        # Allow some time for the ethernet port to discover the network.
        time.sleep(2.0)
        self._uut_conn.send('ifconfig -a eth0\r', expectphrase=self._uut_prompt, regex=True)
        time.sleep(self.RECBUF_TIME)
        if mac and mac not in self._uut_conn.recbuf:
            log.error("Cannot find mac.")
            return False
        if ip and ip not in self._uut_conn.recbuf:
            log.error("Cannot find IP.")
            return False

        log.info("Linux Network Setup: successful.")
        return True

    @func_details
    def ping(self, ip, count=3, checking='relaxed', max_retry=3):
        """ Linux Ping
        --------------
        Ping a network device from Linux
        Need only one successful ping from the total count.
        :param ip: Target IP to ping.
        :param count: Number of times to ping.
        :param checking: 'relaxed' = at least one successful packet in the count; 'strict' = all packets in count must be successful
        :param max_retry: Number of retries to perform.
        :return (bool):
        """
        ret = False
        retry_cnt = 0
        try:
            while not ret and retry_cnt < max_retry:
                retry_cnt += 1
                self._uut_conn.send('ping -c {0} {1}\r'.format(count, ip), expectphrase=self._uut_prompt, timeout=120, regex=True)
                time.sleep(self.RECBUF_TIME)
                m = re.search('([0-9]+) packets transmitted, ([0-9]+) .*?received, ([0-9]+)% packet loss',
                              self._uut_conn.recbuf)
                if m:
                    if (checking == 'relaxed' and int(m.groups(0)[1]) > 0) or (
                            checking == 'strict' and m.groups(0)[0] == m.groups(0)[1]):
                        log.debug("Ping: {0} was successful!  (packets T={1} R={2})".format(ip, m.groups(0)[0],
                                                                                            m.groups(0)[1]))
                        ret = True
                    else:
                        log.warning("Ping: {0} unsuccessful.".format(ip))
                else:
                    log.debug("Ping: bad results with {0} : {1}".format(ip, self._uut_conn.recbuf))

                # Allow network time to discover
                if not ret:
                    log.debug("Ping: wait for network...")
                    time.sleep(5)

        except apexceptions.TimeoutException as e:
            log.error(e)

        finally:
            if ret:
                log.info("Ping PASSED.")
            else:
                log.error("Ping FAILED.")
            return ret

    @func_details
    def get_fdisk_tables(self, size_only=False):
        """ Get FDISK Tables
        --------------------
        Get the fdisk table(s) of a UUT and put them in a dict for later processing.

        Sample #1 : GEN2
        ~ # fdisk -l
        Disk /dev/sda: 2048 MB, 2048901120 bytes
        16 heads, 63 sectors/track, 3970 cylinders
        Units = cylinders of 1008 * 512 = 516096 bytes

           Device Boot      Start         End      Blocks  Id System
        /dev/sda1               1         497      250456+ 83 Linux
        /dev/sda2             498         777      141120   5 Extended
        /dev/sda3             778        3970     1609272  83 Linux
        /dev/sda5             498         502        2488+ 83 Linux
        /dev/sda6             503         507        2488+ 83 Linux
        /dev/sda7             508         586       39784+ 83 Linux
        /dev/sda8             587         665       39784+ 83 Linux
        /dev/sda9             666         777       56416+ 83 Linux

        Sample output dict
        disks['/dev/sda'].size = '2048 MB'
        disks['/dev/sda'].gsize = '2GB'
        disks['/dev/sda'].bytes = '2048901120'
        disks['/dev/sda'].devices = ['/dev/sda1', '/dev/sda2', '/dev/sda3', '/dev/sda5', '/dev/sda6', '/dev/sda7', '/dev/sda8', '/dev/sda9']


        Sample #2 GEN3
        # fdisk -l | grep Disk

        Disk /dev/ram0: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram1: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram2: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram3: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram4: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram5: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram6: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram7: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram8: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram9: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram10: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram11: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram12: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram13: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram14: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/ram15: 4 MiB, 4194304 bytes, 8192 sectors
        Disk /dev/sda: 13.8 GiB, 14763950080 bytes, 28835840 sectors

        Disklabel type: gpt
        Disk identifier: 40B47963-0875-4E68-9BD1-730FCD5204B1

        :param size_only:  Option to return only the device sizes.
        :return disks: The disk data. (Dict of named tuples).
        """

        def _adjust_size_calc(insize):
            """ Adjust size
            Some memory size descriptions from fdisk do not fall on a 2^x boundary due to overhead formatting.
            So use this to find the boundary.
            :param insize:
            :return:
            """
            if 4 < insize <= 8:
                outsize = 8
            elif 8 < insize <= 16:
                outsize = 16
            elif 16 < insize <= 32:
                outsize = 32
            elif 32 < insize <= 64:
                outsize = 64
            else:
                outsize = insize
            return outsize

        disks = dict()
        g_normal_lookup = {'K': 1000000.0, 'M': 1000.0, 'G': 1.0, 'T': 0.001}
        try:
            option, _ = self.__get_fdisk_option()
            if not size_only:
                self._uut_conn.send('fdisk -l{0}\r'.format(option), expectphrase=self._uut_prompt, timeout=30, regex=True)
            else:
                self._uut_conn.send('fdisk -l{0} | grep "Disk "\r'.format(option), expectphrase=self._uut_prompt, timeout=30,
                              regex=True)
            time.sleep(self.RECBUF_TIME)
            p1 = re.compile(r'Disk ([\S]+):[ \t]*([0-9\.]+) ([KMGT])[i]?B,[ \t]*([\S]*) bytes')
            p2 = re.compile(r'([\S]+)[ \t]+[0-9]+[ \t]+[0-9]+[ \t]+[0-9]+[+]*[ \t]+[0-9]+.*')
            disk_data = p1.findall(self._uut_conn.recbuf)
            devices = p2.findall(self._uut_conn.recbuf)

            if disk_data:
                log.debug("Got fdisk data.")
                for disk, size, denom, fbytes in disk_data:
                    # Partition Table is defined by 'GB' flash sizes so normalize the size to this unit.
                    gsize = _adjust_size_calc(int(round(float(size) / g_normal_lookup[denom], 0)))
                    dspl_size = '{0} {1}B'.format(size, denom)
                    if not size_only:
                        disks[disk] = self.Disk(dspl_size, gsize, fbytes,
                                                 [i for i in devices if disk in i]) if devices else self.Disk(size, gsize, fbytes, None)
                    else:
                        disks[disk] = self.Disk(dspl_size, gsize, fbytes, None)
            else:
                log.warning('No disk data!')

        finally:
            log.debug("Disks = {0}".format(disks))
            return disks

    @func_details
    def get_storage_device_size_index(self, disk):
        """ Device Size Index
        ---------------------
        Get device size index (i.e. the partition table dict key) based on actual byte size.
        This normalizes certain vendor devices with small variances.
        :param disk:
        :return:
        """
        log.debug("Looking for Disk = {0}".format(disk))
        disk_sizes = self.get_fdisk_tables(size_only=True)
        log.debug("Available sizes = {0}".format(disk_sizes))
        if disk in disk_sizes and disk_sizes[disk].gsize:
            size_index = '{0}GB'.format(disk_sizes[disk].gsize)
            log.debug("Target disk {0} has size = {1}".format(disk, size_index))
        else:
            log.error("Cannot obtain storage device size; check device.")
            size_index = None
        return size_index

    @func_details
    def determine_disk(self, disk_type, disk_enums=None):
        """ Determine Disk Enumeration
        ------------------------------
        Get disk enumeration if it was not supplied.
        :param disk_type:
        :param disk_enums:
        :return:
        """
        disk_enums = self.get_disk_enumeration() if not disk_enums else disk_enums
        # Check if known and provide correct nomenclature.
        if disk_type in disk_enums:
            disk = '/dev/{0}'.format(disk_enums[disk_type])
            disk_names = self.get_fdisk_tables(size_only=True).keys()
            if disk not in disk_names:
                log.debug("Adjusting disk name...")
                disk = disk[:-1]
                if disk not in disk_names:
                    log.error("Disk name has no match with kernel implementation; check the product definition.")
                    disk = None
            log.debug("Target disk for format = {0}".format(disk))
        else:
            log.error("Unknown disk type: {0}".format(disk_type))
            disk = None
        return disk

    @func_details
    def get_partition_table(self, size_index, partition_tables):
        """ Get Partition Size
        ----------------------
        Check that the partition size is recognized by the product defined partition tables.
        :param size_index:
        :param partition_tables:
        :return:
        """
        if size_index in partition_tables:
            partition_table = partition_tables[size_index]
        else:
            log.error("Storage device size {0} is unrecognized in the partition table.  Consult Cisco TDE.".format(
                size_index))
            partition_table = None
        return partition_table

    @func_details
    def get_disk_enumeration(self, required_disk_enums=None):
        """ Get Disk Enumeration
        ------------------------
        Determine the disk enumeration given by the OS.
        Depending on what storage devices are attached, the disk designation could change dynamically.
        Possible Linux boot messages indicating attached disks (but this is not always guaranteed):
        sd 0:0:0:0: [sda] Attached SCSI disk
        sd 1:0:0:0: [sdb] Attached SCSI removable disk

        Alternate method via command line yeilds:
        Disk /dev/sda: 2048 MB, 2048901120 bytes
        Disk /dev/sdb: 3925 MB, 3925868544 bytes

        This algorithm can only manage 3 attached disks which would be very unusual; most products have only 1 and sometimes 2.
        TBD: Need to research this algorithm for >3 attached devices. (bborel) (2 on-board flash + usb stick + sd card ???)

        :param required_disk_enums: The expected disk enumeration from the UUT config to validate against.
        :return:
        """
        enum_list = ['primary', 'secondary', 'tertiary']  # force a very specific key set!
        disk_enums = {k: None for k in enum_list}
        option, _ = self.__get_fdisk_option()
        self._uut_conn.send('fdisk -l{0} | grep "Disk "\r'.format(option), expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        p = re.compile(r'Disk /[\S]+/(sd[a-z]): .*')
        m = p.findall(self._uut_conn.recbuf)
        if m:
            for i, disk in enumerate(m):
                if i < len(enum_list):
                    disk_enums[enum_list[i]] = disk
                else:
                    log.warning("Maximum enumeration slots exceeded!")
                    log.warning("Disk attachement script handler will need investigation. Contact Cisco TDE.")
                    break
            log.debug("Detected Disk Enumeration = {0}".format(disk_enums))

            if required_disk_enums:
                if 'dynamic' not in required_disk_enums:
                    required_disk_enums['dynamic'] = False
                disk_enums['dynamic'] = required_disk_enums['dynamic']

                # If a required enumeration was provided, validate against what was detected.
                if disk_enums == required_disk_enums:
                    log.debug("Disks match required enumeration!")
                else:
                    if required_disk_enums['dynamic']:
                        log.warning("Disk enumeration will be dynamic via detected enumeration.")
                        log.warning("The required enumeration will be ignored.")
                    else:
                        if set(disk_enums.values()) == set(required_disk_enums.values()):
                            log.warning("Disks do NOT match required enumeration but all disks were detected.")
                            log.warning(
                                "The detected enumeration will be rearranged to match the required enumeration.")
                            # Just rearrange
                            disk_enums = required_disk_enums
                        else:
                            log.warning("Disks do NOT match required enumeration and detection count is wrong.")
                            log.warning(
                                "This could be a script oversight. Check the product definition file for 'disk_enums' setting.")
                            log.warning("This could be a hardware error. Confirm hw operation.")
                            log.warning("The detected enumeration will be used as a fallback.")
            else:
                # Required enumeration was not provided so use the detected arrangement by default.
                log.debug('Using detected enumeration.')
        else:
            log.error("No disks detected!")

        log.info("Finalized Disk Enumeration = {0}".format(disk_enums))
        return disk_enums

    @func_details
    def __get_storage_mounts(self, device_filter=None):
        """ Retrieve the Current Storage Mounts
        ---------------------------------------
        Get all storage devices that are currently mounted.  If a filter is applied then get only those matching the pattern.
        INTERNAL function; do not call directly.

        :param device_filter: Text pattern to capture only specific devices. Ex: 'sda'
        :return:
        """
        self._uut_conn.send('mount\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
        pattern = r'([\S]*{0}[\S]*) on ([\S]+) .*'.format(device_filter) if device_filter else r'([\S]+) on ([\S]+) .*'
        time.sleep(self.RECBUF_TIME)
        p = re.compile(pattern)
        all_mounts = p.findall(self._uut_conn.recbuf)
        mounts = [(a, b) for a, b in all_mounts if a != 'none' and a != 'rootfs' and a != 'none_debugs']
        log.debug("Mounts = {0}".format(mounts)) if mounts else None
        return mounts

    @func_details
    def __do_mounting_cmd(self, command, params):
        """ Run mount/unmount Command
        -----------------------------
        Perform either a mount or a umount to a storage device.
        INTERNAL function; do not call directly.
        Allow multiple attempts in case the resource is busy finishing a sync.
        :param command: The mount/umount command.
        :param params: Device and/or mount location per the command requirement (provided as a single string).
        :return:
        """
        ret = False
        retry = 0
        while retry <= 3:
            retry += 1
            self._uut_conn.send('{0} {1}\r'.format(command, params), expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME) if command != 'umount' else None
            if re.search('(?:[Ff]ail)|(?:FAIL)|(?:[Ee]rror)|(?:ERROR)|(?:busy)', self._uut_conn.recbuf):
                if 'busy' in self._uut_conn.recbuf:
                    log.warning("Resource was busy; {0} attempt #{1}".format(command, retry))
                    # Give the unit some time for the device to come ready and/or allow background sync to finish.
                    time.sleep(2)
                else:
                    log.error("FAILED {0}.".format(command))
            else:
                log.info("Successful {0}.".format(command))
                ret = True
                break
        else:
            # Retry loop hit maximum.
            log.error("Retry exceeded: {0} was NOT successful!".format(command))

        return ret

    @func_details
    def is_dir_assigned_mount(self, mount_dir):
        """ Is Dir Assigned A Mount (aka mount point)?
        example of mount output:
        /dev/sda5 on /mnt/flash5 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda6 on /mnt/flash6 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda3 on /mnt/flash3 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda2 on /mnt/flash2 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)

        example:
        is_dir_assigned_mount('/mnt/flash2') --> '/dev/sda2'

        :param (str) mount_dir:
        :return (str): device that is mounted
        """
        self._uut_conn.send('mount\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(self.RECBUF_TIME)
        p = re.compile('([\S]+) on ([\S]+) type ext2')
        m = p.findall(self._uut_conn.recbuf)
        ret = None
        if m:
            for dev, mnt in m:
                if mnt == mount_dir:
                    ret = dev
        return ret

    @func_details
    def is_dev_mounted(self, mount_device):
        """ Is Device Mounted?
        example of mount output:
        /dev/sda5 on /mnt/flash5 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda6 on /mnt/flash6 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda3 on /mnt/flash3 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)
        /dev/sda2 on /mnt/flash2 type ext2 (rw,relatime,block_validity,barrier,user_xattr,acl)

        example:
        is_dev_mounted('/dev/sda2') --> '/mnt/flash2'

        :param (str) mount_device:
        :return (str): The mounted directory (aka mount point)
        """
        self._uut_conn.send('mount\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(self.RECBUF_TIME)
        p = re.compile('([\S]+) on ([\S]+) type ext2')
        m = p.findall(self._uut_conn.recbuf)
        ret = None
        if m:
            for dev, mnt in m:
                if dev == mount_device:
                    ret = mnt
        return ret

    @func_details
    def mount_disks(self, device_numbers, disk_type, device_mounts, disk_enums=None):
        """ Mount Disks
        ---------------
        Mount one or more disks based on the disk type and the device numbers requested.
        The mount and enumeration definitions must be provided to determine the proper mounting targets.
        Note: This is a "super function" for mount_devices(...).

        :param (list) device_numbers:  Specific disk device mounts to target by number (int).
        :param (str) disk_type: 'primary', 'secondary', 'tertiary'
        :param (dict) device_mounts: Definition of all mounts for all disk types.
        :param (dict) disk_enums: Definition of disk enumeration for all disk types.
        :return (bool, list): True|False if successful, List of mounts
        """
        # Input param checking first
        if not isinstance(device_mounts, dict):
            log.error("device_mounts '{0}' not a dict; cannot continue.".format(device_mounts))
            return False, None
        disk_enums = self.get_disk_enumeration(disk_enums) if not disk_enums else disk_enums
        if disk_type not in disk_enums or not disk_enums[disk_type]:
            log.error("Disk enumeration ({0}) missing.".format(disk_type))
            return False, None
        if disk_type not in device_mounts or not device_mounts[disk_type]:
            log.error(
                "Disk device mount ({0}) is undefined for the product; cannot perform mounting.".format(disk_type))
            log.error("Check product definition.")
            return False, None
        if not device_numbers:
            log.error("Need to provide at least one device number when mounting a disk device.")
            return False, None

        # Mount the device if available.
        log.debug("Trying disk device mounting...")
        device_numbers = [device_numbers] if type(device_numbers) is not list else device_numbers
        log.debug("Device Numbers = {0}".format(device_numbers))
        log.debug("Disk Type      = {0}".format(disk_type))
        log.debug("Device Mounts  = {0}".format(device_mounts))
        log.debug("Disk Enums     = {0}".format(disk_enums))
        mounts = [self.MountDescriptor('/dev/{0}{1}'.format(disk_enums[disk_type], num), path) for num, path in
                  device_mounts[disk_type] if num in device_numbers]
        log.debug("TARGET Mounts  = {0}".format(mounts))
        # Now do the mount!
        ret, _ = self.mount_devices(mounts)
        time.sleep(3)
        self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
        return ret, mounts

    @func_details
    def mount_devices(self, mounts):
        """ Mount Device(s)
        -------------------
        Mount a device or list of devices.
        :param mounts:  List of target mounts of type MountDescriptor = collections.namedtuple('MountDescriptor', 'device dir')
        :return: boolean tuple of ("Mount result", "Already mounted flag")
                 Note: For a list of mounts to mount, the second element in tuple is not applicable.
        """
        if not mounts:
            log.debug("No mounts provided.")
            return [], False
        mounts = [mounts] if type(mounts) is not list else mounts
        all_mounts = self.__get_storage_mounts()
        mounted_devices = [a for a, b in all_mounts]
        ret_list = []  # Result of the mount
        ret2 = False  # Flag to indicate whether the device was already mounted. (Useful in downstream processes.)

        for mount in mounts:
            if mount.device not in mounted_devices:
                # self._uut_conn.send('e2fsck -vy {0}\r'.format(mount.device), expectphrase=self._uut_prompt, timeout=60, regex=True)
                self._uut_conn.send('ls -al --color=never {0}\r'.format(mount.dir), expectphrase=self._uut_prompt, timeout=60,
                              regex=True)
                time.sleep(self.RECBUF_TIME)
                if 'No such file or directory' in self._uut_conn.recbuf:
                    self._uut_conn.send('mkdir -p {0}\r'.format(mount.dir), expectphrase=self._uut_prompt, timeout=60, regex=True)
                    self._uut_conn.send('chmod 777 {0}\r'.format(mount.dir), expectphrase=self._uut_prompt, timeout=60, regex=True)
                    self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
                ret_list.append(
                    self.__do_mounting_cmd('mount', '{0} {1}'.format(mount.device, mount.dir)))
            else:
                if (mount.device, mount.dir) in all_mounts:
                    log.info("Device '{0}' is already mounted to '{1}'.".format(mount.device, mount.dir))
                    ret_list.append(True)
                    ret2 = True
                else:
                    log.error("Device '{0}' is already mounted to a different dir {1}.".format(mount.device, mount.dir))
                    ret_list.append(False)
                    ret2 = True
        return all(ret_list), ret2

    @func_details
    def umount_devices(self, mounts=None, device_filter=None):
        """ Unmount Device(s)
        ---------------------
        Unmount a mount or list of mounts.
        If mounts is None then unmount ALL storage devices (take care when calling).
        Also, the current working directory is restored if the umount occurred elsewhere.
        :param mounts: List of target mounts of type MountDescriptor = collections.namedtuple('MountDescriptor', 'device dir')
        :param device_filter: Text pattern to capture only specific devices for unmounting; ex: 'sda', 'sdb', etc.
        :return:
        """
        ret = False
        try:
            cwd = '.'
            restore_cwd = True
            mounts = [mounts, ] if mounts and type(mounts) is not list else mounts
            all_mounts = self.__get_storage_mounts(device_filter)
            # Get cwd and restore if not unmounting all or not unmounting the cwd path
            cwd = self.get_pwd()
            self._uut_conn.send('cd /\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
            self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
            ret = True
            if all_mounts:
                if mounts:
                    # Unmount specific mounts in the specific order given.
                    log.debug("Umount specific storage mounts: {0}".format(mounts))
                    for mount in mounts:
                        if (mount.device, mount.dir) in all_mounts:
                            log.info("Umount: {0} on {1}".format(mount.device, mount.dir))
                            ret &= self.__do_mounting_cmd('umount', '{0}'.format(mount.dir))
                            restore_cwd = False if mount.dir in cwd else restore_cwd
                else:
                    # No specific mounts given so unmount ALL storage mounts!
                    # Mount dependencies could exist; ensure proper sort order for unmounting.
                    log.debug("Umount ALL storage mounts.")
                    restore_cwd = False
                    all_mounts.sort(key=lambda x: x[1], reverse=True)
                    for device, mount in all_mounts:
                        if '/dev/' in device:
                            # Ensure only storage mounts are unmounted.
                            log.info("Unmount: {0} on {1}".format(device, mount))
                            ret &= self.__do_mounting_cmd('umount', '{0}'.format(mount))
                    if not ret:
                        leftover_mounts = set([a for a, b in self.__get_storage_mounts()])
                        log.warning("Cannot unmount all storage mounts: {0}".format(leftover_mounts))
                self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
            else:
                log.info("No storage mounts mounted.")

        except apexceptions.TimeoutException as e:
            log.debug("UUT unmount response error: {0}".format(e))
            ret = False

        finally:
            # Get back to the dir level if available.
            if restore_cwd:
                self._uut_conn.send('cd {0}\r'.format(cwd), expectphrase=self._uut_prompt, timeout=60, regex=True)
            return ret

    @func_details
    def _format_device(self, disk_type, partition_tables, disk_enums=None, force=False, ask=False, **kwargs):
        """ Format a Device (includes partitioning)
        -------------------------------------------
        Partition & Format the target storage device (typically a flash disk).
        A disk type is used rather than the direct disk name so that enumeration can be verified.
        Also note, all partition tables are provided since a device size must be determined.
        The specific table is selected once a size is obtained.

        Additional hooks are provided for running a 1) init macro and running a 2) replacement macro for fdisk/gdisk.
        Both macros MUST reside in the product-specific classes.

        :param disk_type: Target to format: 'primary', 'secondary', or 'tertiary'.
        :param partition_tables: A collection of partition tables to pass to the _partition_disk() function.
        :param disk_enums: Enumeration indicating the name for the 'disk_type'.
        :param force: Force the partitioning if a previous one already exists; ignore ask
        :param ask: Ask operator to confirm when previous partition is detected.
        :param kwargs:
               partition_macro_func: Pointer to product specific function to run a linux macro instead of commands to do fdisk/gdisk.
               partition_init_macro_func: Pointer to product specific function to as a pre-operation/init prior to fdisk/gdisk/macro.
               default_disk_size: Default size that must exist in the partition table.
        :return:
        """

        log.debug("-" * 50)
        log.debug("PARTITION & FORMAT")
        # Additional inputs
        partition_macro_func = kwargs.get('partition_macro_func', None)
        partition_init_macro_func = kwargs.get('partition_init_macro_func', None)
        default_disk_size = kwargs.get('default_disk_size', '16GB')

        # Process
        # -------
        # 1. Get disk enumeration if it was not supplied.
        disk_enums = self.get_disk_enumeration() if not disk_enums else disk_enums
        log.debug("Enum   = {0}".format(disk_enums))
        # 2. Determine the disk name based on disk enum and disk type.
        disk = self.determine_disk(disk_type=disk_type, disk_enums=disk_enums)
        if not disk:
            log.warning("Using primary as default.")
            disk = '/dev/{0}'.format(disk_enums.get('primary', 'sda'))
        kwargs['disk'] = disk
        log.debug("Disk   = {0}".format(disk))
        # 3. Obtain the disk size.
        size_index = self.get_storage_device_size_index(disk=disk) if disk else None
        if not size_index:
            log.warning("Using 16GB default size.")
            size_index = default_disk_size
        log.debug("Size   = {0}".format(size_index))
        # 4. Get the specific partition table based on all the data above.
        partition_table = self.get_partition_table(size_index, partition_tables=partition_tables) if size_index else None
        log.debug("PTable = {0}".format(partition_table))
        # 5. Prompt option: Check if partition exists ONLY when 'ask' is True
        if ask:
            current_disks = self.get_fdisk_tables()
            has_partition = True if disk in current_disks and current_disks[disk].devices else False
            if has_partition:
                if aplib.get_apollo_mode() == aplib.MODE_DEBUG:
                    yn = aplib.ask_question("Confirm partitioning:\n"
                                            "NO  = Leave as-is (no change).\n"
                                            "YES = Re-partition & format.\n",
                                            answers=['NO', 'YES'], timeout=30) if ask else 'YES'
                else:
                    yn = 'NO'
                if yn == 'NO':
                    log.debug('Re-partitioning has been bypassed by operator.')
                    return True
                else:
                    log.debug("Operator has chosen to overwrite the existing partition (i.e. re-partition).")
                    force = True
        # 6. Run any init routines
        if partition_init_macro_func:
            log.info("Partition initialization...")
            if not partition_init_macro_func(**kwargs):
                log.error("Partition init macro ({0}) did not properly complete.".format(partition_init_macro_func))
                return False
        # 7. Do the partition and format!
        if not partition_macro_func:
            log.info("Partition/Format Method: CMD + TABLE.")
            if not partition_table:
                log.error("No partition table; cannot complete format process.")
                return False
            log.info("Partition table acquired.")
            # Step 1
            # Umount all mounts of the disk type when formatting.
            self.umount_devices(device_filter=disk_enums[disk_type])
            # Step 2
            # Partition device
            if self._partition_disk(disk=disk, partition_table=partition_table, force=force):
                # Step 3
                # Format filesystem
                log.debug("Format filesystem.")
                if self._make_filesystem(disk=disk, partition_table=partition_table,
                                         device_num_filter_list=None):
                    log.debug("Performing partition sync....")
                    time.sleep(3)
                    self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
                    time.sleep(3)
                    self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
                    ret = True
                    log.info("Partition SUCCESSFUL!")
                else:
                    log.error("Filesystem creation FAILED.")
                    ret = False
            else:
                log.error("Partitioning FAILED.")
                ret = False
        else:
            log.info("Partition/Format Method: MACRO.")
            ret = partition_macro_func(**kwargs)

        return ret

    @func_details
    def _partition_disk(self, disk, partition_table, force=False):
        """ Partition a Disk
        --------------------
        Create the Linux (or DOS) partitions for a disk (typically a flash device).
        Previous partitions may need deleting if present; the default is to force deletion of any previous partitions.

        fdisk
        -----


        gdisk
        -----
        root@diags:/# gdisk /dev/mmcblk0
        GPT fdisk (gdisk) version 1.0.0

        Partition table scan:
          MBR: protective
          BSD: not present
          APM: not present
          GPT: present

        Found valid GPT with protective MBR; using GPT.

        Command (? for help): ?
        b	back up GPT data to a file
        c	change a partition's name
        d	delete a partition
        i	show detailed information on a partition
        l	list known partition types
        n	add a new partition
        o	create a new empty GUID partition table (GPT)
        p	print the partition table
        q	quit without saving changes
        r	recovery and transformation options (experts only)
        s	sort partitions
        t	change a partition's type code
        v	verify disk
        w	write table to disk and exit
        x	extra functionality (experts only)
        ?	print this menu

        Command (? for help): n
        Partition number (1-128, default 1):
        First sector (2048-28835806, default = 2048) or {+-}size{KMGTP}:
        Last sector (2048-28835806, default = 28835806) or {+-}size{KMGTP}:
        Current type is 'Linux filesystem'
        Hex code or GUID (L to show codes, Enter = 8300):
        Changed type of partition to 'Linux filesystem'

        :param disk: Specific disk to partition (e.g. '/dev/sda', '/dev/sdb', etc.)
        :param partition_table: Specific table used to partition the target disk.
               Example:
               1: {'device_num': 1,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '1',  'first_cylinder': '1', 'last_cylinder': '+256M'},
               2: {'device_num': None, 'sys_id': '',   'partition_type': 'e', 'partition_number': '2',  'first_cylinder': '',  'last_cylinder': '+144M'},
               etc...  (see your product line's _common.py in the product_definitions folder).
        :param force: If True then delete the existing partitions if one already exists and create a new one.
                      If False then keep the existing partitions if they exist and do nothing.
        :return: True = success
        """
        ret = False
        menu_prompt = ['Command (m for help):', 'Command (? for help):']
        try:
            log.debug("Target Disk to partition = {0}".format(disk))

            # Get the current disks (if any) to determine if deletion is required.
            current_disks = self.get_fdisk_tables()
            log.debug("Current disk for format = {0}".format(current_disks[disk]))
            has_partition = True if disk in current_disks and current_disks[disk].devices else False
            # Prepare logic based on forcing flag and current disk partition presence.
            if has_partition:
                log.debug('Device already has one or more partitions.')
                if force:
                    log.debug('Force re-partitioning.')
                    do_partition_delete = True
                    do_partition = True
                else:
                    # Do nothing since an existing partition was detected and 'force' was NOT designated.
                    log.debug('No forced partitioning; keep existing partitions.')
                    do_partition_delete = False
                    do_partition = False
            else:
                # Since no partitions the 'force' is a don't care and partitioning must occur.
                log.debug('Device has no previous partitions.')
                do_partition_delete = False
                do_partition = True

            # Start the fdisk process
            _, option = self.__get_fdisk_option()
            self._uut_conn.sende('{0} {1}{2}\r'.format(self.FDISK['cmd'], disk, option), expectphrase=menu_prompt, timeout=30)
            time.sleep(self.RECBUF_TIME)

            if do_partition_delete:
                log.debug('Partition deletion will occur.')
                done = False
                partition_number = 0
                while not done and partition_number < 10:
                    partition_number += 1
                    self._uut_conn.sende('d\r',
                                   expectphrase=['No partition is defined', 'Selected partition', 'Partition number',
                                                 'artition'] + menu_prompt, timeout=30)
                    time.sleep(self.RECBUF_TIME)
                    if 'Partition number' in self._uut_conn.recbuf:
                        log.debug('Partition {0} for deletion.'.format(partition_number))
                        self._uut_conn.sende('{0}\r'.format(partition_number), expectphrase=menu_prompt, timeout=30)
                    elif 'Selected partition' in self._uut_conn.recbuf:
                        log.debug('Final partition {0} (auto selected) for deletion.'.format(partition_number))
                        self._uut_conn.sende('\r', expectphrase=menu_prompt, timeout=30)
                        done = True
                    elif 'No partition is defined' in self._uut_conn.recbuf:
                        log.debug('No partition available to delete.')
                        done = True
                    elif any([(i in self._uut_conn.recbuf) for i in menu_prompt]):
                        log.debug('No further partition deletes allowed; back at menu prompt.')
                        done = True
                    else:
                        log.error(
                            'Unknown situation for partition deletion during prompting. Please consult Cisco TDE.')
                        log.error('Partitioning will be aborted.')
                        raise RuntimeError("Partition deletion problem.")
            else:
                log.debug('Partition deletion NOT required.')

            if do_partition:
                log.debug('New partitioning started.')

                if partition_table[1]['partition_type'] == 'g' and self.FDISK['cmd'] == 'fdisk':
                    # GPT disklabel (GUID: xxx-xxx...)
                    # Do this when NOT using 'gdisk' but instead using 'fdisk'.
                    log.warning(
                        "GPT partition requested but using fdisk; ensure this is correct. Check product definition!")
                    self._uut_conn.sende('g\r', expectphrase=menu_prompt, timeout=30)
                    time.sleep(self.RECBUF_TIME)
                    if 'Created a new GPT disklabel' not in self._uut_conn.recbuf:
                        log.error("Problem creating GPT disk label.")
                        return False

                # Process all partition definition indices:
                for partition_index in sorted(partition_table):
                    log.debug('Partition Index = {0} = {1}'.format(partition_index, partition_table[partition_index]))

                    # Create a new partition
                    self._uut_conn.sende('n\r', expectphrase='(?:Command action)|(?:Partition number)', timeout=10,
                                   regex=True)

                    # Partition type determines prompts
                    if partition_table[partition_index]['partition_type'] == 'g':
                        # GPT Partition types
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['partition_number']),
                                       expectphrase='First sector', timeout=10)
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['first_sector']),
                                       expectphrase='Last sector', timeout=10)
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['last_sector']),
                                       expectphrase=menu_prompt + ['Hex code'], timeout=10)
                        time.sleep(self.RECBUF_TIME)
                        self._uut_conn.sende('\r', expectphrase=menu_prompt,
                                       timeout=10) if 'Hex code' in self._uut_conn.recbuf else None
                    else:
                        # Non-GPT Partition types (i.e. Legacy MBR partitions)
                        if partition_table[partition_index]['partition_number']:
                            self._uut_conn.send('{0}\r'.format(partition_table[partition_index]['partition_type']),
                                          expectphrase='Partition number', timeout=10)
                            self._uut_conn.send('{0}\r'.format(partition_table[partition_index]['partition_number']),
                                          expectphrase='First cylinder', timeout=10)
                        else:
                            self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['partition_type']),
                                           expectphrase='First cylinder', timeout=10)
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['first_cylinder']),
                                       expectphrase='Last cylinder', timeout=10)
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['last_cylinder']),
                                       expectphrase=menu_prompt, timeout=10)

                    if partition_table[partition_index]['sys_id'] and (
                            partition_table[partition_index]['partition_type'] == 'p' or
                            partition_table[partition_index]['partition_type'] == 'g') and self.FDISK['cmd'] == 'fdisk':
                        # Only set the filesystem type if it is a primary partition.
                        self._uut_conn.sende('t\r', expectphrase='[Pp]artition', timeout=10, regex=True)
                        time.sleep(self.RECBUF_TIME)
                        if 'Partition number' in self._uut_conn.recbuf:
                            self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['partition_number']),
                                           expectphrase='Hex code', timeout=10)
                        elif 'Selected partition' in self._uut_conn.recbuf:
                            log.debug("Partition auto selected for type.")
                        else:
                            log.warning(
                                "Unrecognized behavior during fdisk partition typing. Please contact Cisco TDE.")
                        self._uut_conn.sende('{0}\r'.format(partition_table[partition_index]['sys_id']),
                                       expectphrase=menu_prompt, timeout=10)

                # Print the partition setup and check the table
                log.debug("Validating partition table...")
                log.debug("Expected table:")
                for k, v in partition_table.items():
                    log.debug("{0:>4} = {1}".format(k, v))
                self._uut_conn.sende('p\r', expectphrase=menu_prompt, timeout=30)
                valid_table = True
                for partition_index in sorted(partition_table):
                    p_num = partition_table[partition_index]['partition_number']
                    dev_num = partition_table[partition_index]['device_num']
                    device = '{0}{1}'.format(disk, dev_num)
                    device_alt = '{0}p{1}'.format(disk, dev_num)
                    if self.FDISK['cmd'] == 'fdisk':
                        log.debug("Check {0} or {1} : {2}".format(device, device_alt, valid_table))
                        valid_table = False if dev_num and device not in self._uut_conn.recbuf and device_alt not in self._uut_conn.recbuf else valid_table
                    elif self.FDISK['cmd'] == 'gdisk':
                        valid_table = False if p_num and not re.search('{0} .*? Linux filesystem'.format(p_num),
                                                                       self._uut_conn.recbuf) else valid_table
                        log.debug("Check {0} : {1}".format(p_num, valid_table))
                    else:
                        log.warning("Unknown format command ({0}).".format(self.FDISK['cmd']))

                # Write It!
                if valid_table:
                    log.debug('Partitioned table is valid based on requirement.')
                    if self.FDISK['cmd'] == 'fdisk':
                        self._uut_conn.sende('w\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
                    elif self.FDISK['cmd'] == 'gdisk':
                        self._uut_conn.sende('w\r', expectphrase='want to proceed', timeout=30, regex=True)
                        self._uut_conn.sende('y\r', expectphrase=self._uut_prompt, timeout=60, regex=True)

                    # Check for success first.
                    # Any mount failures can be ignored IFF partition was successful! (bborel 9/27/2018)
                    time.sleep(self.RECBUF_TIME)
                    if re.search('(?i)(?:partition table has been altered)|(?:completed successfully)',
                                 self._uut_conn.recbuf):
                        log.info("Partitioning is good!")
                        ret = True
                    elif re.search('(?i)(?:err)|(?i)(?:fail)|(?i)(?:unknown partition table)', self._uut_conn.recbuf):
                        log.error("Partitioning errror.")
                    else:
                        log.warning("Partitioning status is unknown.  Contact Cisco TDE.")

                else:
                    log.error('Partitioned table is NOT valid!')

            else:
                log.debug('Partitioning NOT required.')
                ret = True

        except RuntimeError as e:
            log.debug('Runtime error during partitioning: {0}'.format(e))
            ret = False
        except apexceptions.TimeoutException as e:
            log.debug('UUT partition disk response error: {0}'.format(e))
            ret = False
        except Exception as e:
            log.error(e)
            ret = False

        finally:
            log.debug("Partition finalization...")
            # Ensure fdisk process is done.
            self._uut_conn.send('\r', timeout=30)
            self._uut_conn.send('\r', expectphrase='.*', timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            try:
                # Failsafe exit
                if any([(i in self._uut_conn.recbuf) for i in menu_prompt]):
                    log.debug("Failsafe menu exit.")
                    self._uut_conn.sende('q\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
            except apexceptions.TimeoutException:
                pass
            log.debug("Partitioning done!")
            return ret

    @func_details
    def __get_fdisk_option(self):
        log.debug("Getting fdisk/gdisk options...")
        self.FDISK['cmd'] = self._ud.uut_config.get('fdisk_cmd', self.FDISK['cmd'])
        log.debug("Disk util = {0}".format(self.FDISK['cmd']))
        if not self.FDISK['checked']:
            self._uut_conn.send('fdisk --help\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            if '--color' in self._uut_conn.recbuf:
                self.FDISK['param'] = ' --color=never'
            self.FDISK['checked'] = True
            self.FDISK['param2'] = self.FDISK['param'] if self.FDISK['cmd'] == 'fdisk' else ''
        log.debug("FDISK = {0}".format(self.FDISK))
        return self.FDISK['param'], self.FDISK['param2']

    @func_details
    def _make_filesystem(self, disk, partition_table, device_num_filter_list=None):
        """ Make the Filesystem
        -----------------------
        Create the filesystem for a given partition table.
        Current support is for Linux EXT2 and DOS/Win95 FAT32.

        :param disk: Specific disk to make fs (e.g. '/dev/sda', '/dev/sdb', etc.)
        :param partition_table: Specific table used to partition the target disk. (See _partition_disk() function for more details.)
        :param device_num_filter_list: List of device numbers to filter on for creating the fs; exclude all others. If empty then do ALL devices.
        :return: True if successful
        """

        def _create_fs(partition, device):
            ret = False
            if partition['sys_id'] == '83' or partition['sys_id'] == '20' or partition['sys_id'] == '8300':
                log.debug("Device = {0} has Linux EXT2".format(device))
                self._uut_conn.send('umount {0}\r'.format(device), expectphrase=self._uut_prompt, timeout=30, regex=True)
                self._uut_conn.send('mke2fs {0}\r'.format(device), expectphrase=[self._uut_prompt, 'Proceed anyway?'], timeout=60,
                              regex=True)
                if 'Proceed anyway?' in self._uut_conn.recbuf:
                    self._uut_conn.send('y\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
                self._uut_conn.send('e2fsck {0}\r'.format(device), expectphrase=self._uut_prompt, timeout=60, regex=True)
                time.sleep(self.RECBUF_TIME)
                if re.search('(?i)(?:clean)', self._uut_conn.recbuf):
                    ret = True
                else:
                    log.error("Device = {0} EXT2 filesystem is not properly set.".format(device))
                    ret = False
            elif partition['sys_id'].upper() == '0B':
                log.debug("Device = {0} has DOS/Win95 FAT32".format(device))
                self._uut_conn.send('mkdosfs -F 32 {0}\r'.format(device), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                if not re.search('(?i)(?:error)|(?i)(?:fail)', self._uut_conn.recbuf):
                    ret = True
                else:
                    log.error("Device = {0} DOS/Win95 filesystem is not properly set.".format(device))
                    ret = False
            elif partition['sys_id'] is None or partition['sys_id'] == '':
                log.debug("Device = {0} FS creation not required.".format(device))
            else:
                log.error("Device = {0} has an unrecognized filesystem of {1}".format(device, partition['sys_id']))
                log.error("Check the disk_partition_tables in the common product definition area.")
                ret = False
            return ret

        # -------------
        ret = False
        ret_list = []
        try:
            # Get initial partition info
            option, _ = self.__get_fdisk_option()
            self._uut_conn.send('fdisk -l{0}\r'.format(option), expectphrase=self._uut_prompt, timeout=30, regex=True)
            device_alt = '{0}p{1}'.format(disk, partition_table[1]['device_num'])
            extra_id = 'p' if device_alt in self._uut_conn.recbuf else ''

            # Step thru each partition and format each one
            for partition_index in sorted(partition_table):
                dev_num = partition_table[partition_index]['device_num']
                if dev_num:
                    # Prepare logic based on filter
                    if device_num_filter_list:
                        process_dev_num = True if dev_num in device_num_filter_list else False
                    else:
                        process_dev_num = True
                    # Process
                    if process_dev_num:
                        device = '{0}{1}{2}'.format(disk, extra_id, dev_num)
                        # Create filesystem based on type.
                        ret_list.append(_create_fs(partition_table[partition_index], device))
            ret = all(ret_list)

            time.sleep(3)
            self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(3)
            self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        except apexceptions.TimeoutException as e:
            log.debug('UUT make filesystem response error: {0}'.format(e))

        finally:
            return ret

    def __is_local_server(self, target_ip):
        local_ip, _, _ = get_system_ip_and_mask('eth1')
        ret = True if target_ip == local_ip else False
        return ret

    def __get_tftp_secure_dir(self, is_local_server):
        if is_local_server:
            # Check Local TFTP Server secure dir location.
            # "server_args		= -c -s /tftpboot"   The '-c' is for auto-create on puts.
            # Since the lockdown, much of /etc is non-readable for user=apollo. sudo doesn't allow either! :-(
            o = shellcmd("cat /etc/xinetd.d/tftp | grep server_args")
            log.debug(o)
            m = re.search(r"server_args[ \t]+= .*?(-c)?.*-s ([\S]+)", o)
            if m:
                tftp_secure_dir = m.groups()[1].strip()
                auto_create = True if m.groups()[0] else False
                if tftp_secure_dir != '/tftpboot':
                    log.warning("The local tftpboot dir ({0}) is not in the standard path!".format(tftp_secure_dir))
                    log.warning("Forcing a change to standard path.")
                    tftp_secure_dir = '/tftpboot'
            else:
                log.warning("No server_args were detected (or readable) for the TFTP server!")
                tftp_secure_dir = '/tftpboot'
                auto_create = False
            server = "Local"
        else:
            # Make assumption about Remote TFTP Server secure dir location.
            # TODO: ssh to remote server and confirm.
            log.warning("TFTP Remote Server params are assumed! Check TFTP server config to confirm!")
            tftp_secure_dir = '/tftpboot'
            auto_create = True
            server = "Remote"

        return server, tftp_secure_dir, auto_create

    @func_details
    def transfer_tftp_files(self, src_files=None, dst_files=None, direction='get',
                            server_ip=None, netmask=None, ip=None, transfer_timeout=600, force=True):
        """ TFTP File Transfer (with checking and path creation)
        --------------------------------------------------------
        Transfer files between the UUT/target device (running Linux) and the LOCAL or REMOTE APOLLO SERVER.
        Typically, this is for downloading files to a UUT but this can also be used for uploading files from a UUT.
        The src_files/dst_files params have the following list formats:
            1. filename, filename2, ...
            2. (filename, cksum), (filename2, cksum_2), ...    note: cksum's = 1 to 10 hex chars
            3. (filename, md5), (filename2, md5_2), ...        note: md5's = 32 hex chars
            4. Any permutation of the above formats.
            'filename' may have absolute or relative paths included based on the direction.

        If BOTH src_files and dst_files are given, they must map one-to-one per the lists!
        If dst_files is NOT provided, the target location will be the current working dir and the names will be identical to src_files.

        ASSUMPTIONS:
          1) The target UUT or device is already in the Linux mode.
          2) Any destination target paths on the UUT requiring mounting should already be mounted to the appropriate devices
             for which the directory is intended. (This means all mounting should be done first.)
        NOTES:
          1) For destination files with paths prepended, the paths will be created on the UUT/device if they do not exist;
             both relative and absolute paths are allowed.
          2) Any crc on the src_files list will be used to check an existing file if force=False and it will be used to check
             the destination file.
          3) Some limitations will exist if a remote server is specified, particularly with the 'put' operation.
          4) If the UUT cannot ping the server, an attempt to setup the UUT on the test network will be done
             (if the server ip and netmask are provided).

        :param (list) src_files: List of source file items.
        :param (list) dst_files: List of destination file items.
        :param (str) direction: 'get' or 'put' (Always relative from the UUT or local device perspective!!!)
        :param (str) server_ip: TFTP Server IP for getting or putting (typically the private test network Apollo server eth1 port)
        :param (str) netmask: Private test network Apollo server netmask
        :param (str) ip: UUT assigned IP on the private test network
        :param (int) transfer_timeout: Timeout for file transfer; adjust appropriately for large files.
        :param (bool) force:  Ignore existing files and overwrite if True.
        :return: True if all files transferred successfully (i.e. via file presence or valid crc).
        """

        def __perform_tftp_cmd(src_file, dst_file, direction, server_ip, transfer_timeout,
                               crc, server_secure_dir='', is_local_server=True):
            """ Perform TFTP Command
            ------------------------
            Internal command runner.
            Same params as main function plus...
            :param crc: crc of file to check against (optional)
            :param server_secure_dir: Directory of the TFTP server for secure transfers.
            :param is_local_server: Boolean flag to indicate if server is local or remote.
            :return: True if successful.
            """

            map_locale = {'get': 'uut', 'put': 'server'}
            if direction == 'get':
                cmd = 'tftp  -{0} -r {1} -l {2}'.format(direction[0:1], src_file, dst_file)
            elif direction == 'put':
                cmd = 'tftp  -{0} -r {1} -l {2}'.format(direction[0:1], dst_file, src_file)
            else:
                log.error("Unknown 'direction param!")
                return False

            attempt_count = 0
            result = False
            while attempt_count < 3 and not result:
                attempt_count += 1
                self._uut_conn.send('{0} {1}\r'.format(cmd, server_ip), expectphrase=self._uut_prompt, timeout=transfer_timeout,
                              regex=True)
                time.sleep(self.RECBUF_TIME)
                if any([x in self._uut_conn.recbuf.lower() for x in ['error', 'fail', 'no such file', 'timeout']]):
                    log.error("TFTP {0}: FAILED = {1}".format(direction.upper(), self._uut_conn.recbuf))
                else:
                    result = True

            if result:
                log.debug("TFTP {0}: checking result...".format(direction.upper()))
                if map_locale[direction] == 'server' and not is_local_server:
                    log.warning("Cannot currently perform CRC on TFTP remotely uploaded files from the UUT.")
                    result = True
                else:
                    result = self.check_crc(dst_file, locale=map_locale[direction], crc=crc, server_dir=server_secure_dir)
                if result:
                    log.info("TFTP {0}: PASSED for '{1}'".format(direction.upper(), dst_file))
                else:
                    log.error("TFTP {0}: FAILED validation for '{1}'".format(direction.upper(), dst_file))
            return result

        result_list = []

        # Ensure the params are lists
        src_files = [src_files] if not isinstance(src_files, list) else src_files
        dst_files = [dst_files] if not isinstance(dst_files, list) else dst_files
        # Sanity check
        if (src_files and dst_files) and ((len(src_files) != len(dst_files)) and dst_files[0]):
            log.error("Source and destination file(s) do not have a one-to-one mapping.")
            log.error("Src = {0}".format(src_files))
            log.error("Dst = {0}".format(dst_files))
            return False
        elif not src_files:
            log.error("Source file(s) must be provided.")
            return False
        elif (not dst_files) or (len(dst_files) == 1 and not dst_files[0]):
            log.debug("Destination file names/paths will be identical to the source files.")
            dst_files = src_files

        log.info("TFTP {0}: All Source files      = {1}".format(direction.upper(), src_files))
        log.info("TFTP {0}: All Destination files = {1}".format(direction.upper(), dst_files))

        # Determine if Server IP is Local or Remote and get tftp secure dir
        is_local_server = self.__is_local_server(server_ip)
        server, tftp_secure_dir, auto_create = self.__get_tftp_secure_dir(is_local_server)

        log.info("TFTP {0}: {1} Server secure directory = '{2}'".format(direction.upper(), server, tftp_secure_dir))
        log.info("TFTP {0}: {1} Server auto create      = '{2}'".format(direction.upper(), server, auto_create))

        # Check that UUT/device can reach the TFTP server.
        if not self.ping(ip=server_ip, count=1):
            log.warning("TFTP {0}: Cannot ping the server/source IP ({1}).".format(direction.upper(), server_ip))
            if ip and netmask and server_ip:
                log.info("Checking network setup...")
                if self.set_uut_network_params(ip=ip, netmask=netmask, server_ip=server_ip):
                    if not self.ping(ip=server_ip, count=3):
                        log.warning("TFTP {0}: Still cannot ping the server/source IP ({1}).".format(direction.upper(),
                                                                                                     server_ip))
                        log.error("Check UUT network connections and setup.")
                        return False
                else:
                    log.error("Problem with netowrk setup.")
                    return False
            else:
                log.error("Check UUT network settings and connections.")
                return False

        # Process the file list
        for src_file_item, dst_file_item in zip(src_files, dst_files):
            src_file, crc = src_file_item if isinstance(src_file_item, tuple) else (src_file_item, None)
            dst_file, crc2 = dst_file_item if isinstance(dst_file_item, tuple) else (dst_file_item, None)
            crc = crc2 if not crc and crc2 else crc
            dst_file = src_file if not dst_file else dst_file
            src_file.strip()
            dst_file.strip()
            log.debug("TFTP {0}: ------".format(direction.upper()))
            log.debug("TFTP {0}: Source file      = '{1}'".format(direction.upper(), src_file))
            log.debug("TFTP {0}: Destination file = '{1}'".format(direction.upper(), dst_file))

            if not src_file:
                log.warning("TFTP {0}: source filename is empty. Ignore this transfer.".format(direction.upper()))
                continue

            # Make any new dirs that are specified by the destination files
            if direction == 'get':
                cwd = self.get_pwd()
                dst_filepath, dst_filename = os.path.split(dst_file)
                log.debug("Dst path = '{0}'".format(dst_filepath))
                if dst_filepath:
                    self._uut_conn.send('if test -d {0}; then echo "{0}=True"; fi\r'.format(dst_filepath),
                                  expectphrase=self._uut_prompt, timeout=30, regex=True)
                    time.sleep(2.0)
                    create_folders = True if not '{0}=True'.format(dst_filepath) in self._uut_conn.recbuf.splitlines()[
                        1] else False
                else:
                    create_folders = False

                if create_folders:
                    log.debug("Creating new folders for the TFTP files...")
                    dst_filepath_dirs = dst_filepath.split('/')
                    log.debug("TFTP GET: cwd={0},  file path dirs={1}".format(cwd, dst_filepath_dirs))
                    if len(dst_filepath_dirs) > 0 and dst_filepath_dirs[0] == "":
                        # If the dst filepath starts at root then change to there otherwise stay at relative dir level.
                        self._uut_conn.send('cd /\r', expectphrase=self._uut_prompt, timeout=30, regex=True) if len(
                            dst_filepath_dirs) > 1 else None
                        dst_filepath_dirs.pop(0)
                    for path in dst_filepath_dirs:
                        log.debug("TFTP GET: setting dir '{0}'".format(path))
                        # Check dir first
                        self._uut_conn.send('if test -d {0}; then echo "{0}=True"; fi\r'.format(path),
                                      expectphrase=self._uut_prompt, timeout=30, regex=True)
                        time.sleep(2)
                        if not '{0}=True'.format(path) in self._uut_conn.recbuf.splitlines()[1]:
                            # Make as needed; existing will not cause error.
                            self._uut_conn.send('mkdir -p {0}\r'.format(path), expectphrase=self._uut_prompt, timeout=30,
                                          regex=True)
                            # default permissions for dirs
                            self._uut_conn.send('chmod 777 {0}\r'.format(path), expectphrase=self._uut_prompt, timeout=30,
                                          regex=True)
                        self._uut_conn.send('cd {0}\r'.format(path), expectphrase=self._uut_prompt, timeout=30, regex=True)
                    # Get back
                    self._uut_conn.send('cd {0}\r'.format(cwd), expectphrase=self._uut_prompt, timeout=30, regex=True)

            # Choose DIRECTION
            # ----------------
            if direction == 'get':
                # Check source file path: for TFTP GET this MUST be a relative path to ensure server secure dir usage.
                if src_file[0:1] == '/':
                    log.error("TFTP GET: Cannot use absolute paths in the source files.")
                    log.error(
                        "TFTP GET: Ensure usage of the TFTP server directory with a relative path for source files.")
                    result_list.append(False)
                    continue
                #
                # Do GET
                # Allow skipping if correct file is already present at the destination and the call is
                # not forcing the transfer.
                skip = self.check_crc(dst_file, locale='uut', crc=crc) if not force else False
                if not skip:
                    src_file_full = os.path.join(tftp_secure_dir, src_file)
                    result = __perform_tftp_cmd(src_file, dst_file, direction, server_ip,
                                                transfer_timeout, crc, is_local_server=is_local_server)
                    if result:
                        # Now match up the permissions: the server file --> uut file
                        if is_local_server:
                            permissions = oct(os.stat(src_file_full).st_mode & 0777)
                        else:
                            permissions = oct(0755)
                        log.debug("TFTP GET: file permissions = {0}".format(permissions))
                        self._uut_conn.send('chmod {0} {1}\r'.format(permissions, dst_file), expectphrase=self._uut_prompt,
                                      timeout=30, regex=True)
                        self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=transfer_timeout, regex=True)
                else:
                    log.debug("TFTP GET: skip; file is present.")
                    result = True

            elif direction == 'put':
                # Check destination file path: for TFTP PUT this MUST be a relative path to ensure server
                # secure dir usage.
                if dst_file[0:1] == '/':
                    log.error("TFTP PUT: Cannot use absolute paths in the destination files.")
                    log.error(
                        "TFTP PUT: Ensure usage of the TFTP server directory with a relative path for destination files.")
                    result_list.append(False)
                    continue
                #
                # Do PUT
                dst_file_full = os.path.join(tftp_secure_dir, dst_file)
                if is_local_server:
                    if not auto_create:
                        log.warning("TFTP server may not be authorized to auto create ingress TFTP transfers.")
                        touch(dst_file_full) if not os.path.exists(dst_file_full) else None
                else:
                    log.warning("Since a remote TFTP server is being used, it is assumed auto create is on "
                                "for ingress TFTP transfers.")
                result = __perform_tftp_cmd(src_file, dst_file, direction, server_ip,
                                            transfer_timeout, crc, tftp_secure_dir, is_local_server=is_local_server)
                # Now match up the permissions: uut file --> server file
                self._uut_conn.send('stat -c "%a" {0}\r'.format(src_file), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                permissions = self._uut_conn.recbuf.splitlines()[1].strip()
                if is_local_server:
                    cmd = 'chmod {0} {1}'.format(permissions, dst_file_full)
                    log.debug(cmd)
                    shellcmd(cmd)

            else:
                log.error("TFTP: direction={0} is unknown.".format(direction))
                result = False

            # Record this loop
            result_list.append(result)
        # end_for

        log.debug("TFTP result list = {0}".format(result_list))
        ret = all(result_list)

        self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=transfer_timeout, regex=True)
        log.info("TFTP {0}: Successful!".format(direction.upper())) if ret else None
        return ret

    @func_details
    def transfer_tftp_directory(self, src_dir=None, dst_dir=None, direction='get',
                                server_ip=None, netmask=None, ip=None, transfer_timeout=600, force=True):

        if not src_dir:
            log.error("Must specify a source directory.")
            return False
        if not dst_dir:
            log.debug("Destination directory will be the same name as source directory.")
            dst_dir = src_dir

        # Determine if Server IP is Local or Remote and get tftp secure dir
        is_local_server = self.__is_local_server(server_ip)
        server, tftp_secure_dir, _ = self.__get_tftp_secure_dir(is_local_server)
        tftp_server_dir = os.path.join(tftp_secure_dir, src_dir)

        log.debug("Src Dir         = {0}".format(src_dir))
        log.debug("Dst Dir         = {0}".format(dst_dir))
        log.debug("Direction       = {0}".format(direction))
        log.debug("Server IP/NM    = {0}/{1}".format(server_ip, netmask))
        log.debug("Server          = {0}".format(server))
        log.debug("TFTP Server Dir = {0}".format(tftp_server_dir))

        result_list = []
        if direction == 'get':
            if server != 'Local':
                log.warning("TFTP DIR GET is only supported on local servers.")
                server_ip = self._ud.server_config['eth1_ip']
                log.warning("Trying on local server {0}...".format(server_ip))

            w = os.walk(tftp_server_dir)
            dir_content = 'seed'
            while dir_content:
                try:
                    dir_content = w.next()
                except StopIteration:
                    dir_content = None
                if dir_content:
                    path, _, files = dir_content
                    relative_path = path.strip(tftp_secure_dir)
                    relative_pathed_src_files = [os.path.join(relative_path, file) for file in files]
                    relative_pathed_dst_files = [os.path.join(dst_dir, file) for file in files]
                    result = self.transfer_tftp_files(src_files=relative_pathed_src_files,
                                                      dst_files=relative_pathed_dst_files,
                                                      direction='get',
                                                      server_ip=server_ip, netmask=netmask, ip=ip,
                                                      transfer_timeout=transfer_timeout, force=force)
                    result_list.append(result)

        elif direction == 'put':
            log.error("This operation is currently NOT supported.")
            return False
        else:
            log.error("TFTP: direction={0} is unknown.".format(direction))
            return False

        log.debug("TFTP DIR result list = {0}".format(result_list))
        if not result_list:
            log.warning("No files were transferred; check the server tftpboot location for expected files.")
            return False

        ret = all(result_list)
        log.info("TFTP DIR {0}: Successful!".format(direction.upper())) if ret else None

        return ret

    @func_details
    def delete_files(self, files=None, delete_timeout=60):
        """ Delete File/dir on Linux system
        --------------------------------------------------------
        Delete every file/dir in input list, the item in input should be complete file name with path.
        This func goes through the list, check file existence, if it exists, delete it, then check again.

        :param (list/str) files:        List of files/dirs to be deleted, if it is a str, then it is a single file to delete
        :param (int) delete_timeout:    Timeout for sync;
        :return: True if all files deleted successfully (i.e. file does not exist after deleting).
        """

        result_list = []

        # Ensure the params are lists
        files_to_delete = [files] if not isinstance(files, list) else files
        log.info("All files to delete   = {0}".format(files_to_delete))

        # Process the file list
        for file_del in files_to_delete:
            log.info('Checking file|dir {0} existence'.format(file_del))
            self._uut_conn.send('ls {0}\r'.format(file_del), expectphrase=self._uut_prompt, timeout=30, regex=True)
            if 'No such file' not in self._uut_conn.recbuf:
                log.info('File|dir {0} exists, now delete it'.format(file_del))
                self._uut_conn.send('rm -rf {}\r'.format(file_del), expectphrase=self._uut_prompt, timeout=300, regex=True)
                # check again after deleting
                self._uut_conn.send('ls {0}\r'.format(file_del), expectphrase=self._uut_prompt, timeout=30, regex=True)
                if 'No such file' not in self._uut_conn.recbuf:
                    log.warning('Failed to delete file|dir {0}'.format(file_del))
                    result_list.append(False)
                else:
                    log.info('File|dir {0} deleted'.format(file_del))
                    result_list.append(True)
            else:
                log.info('File|dir {0} does not exist'.format(file_del))
                result_list.append(True)

        log.debug('Delete result list = {0}'.format(result_list))
        ret = all(result_list)

        self._uut_conn.send('sync\r', expectphrase=self._uut_prompt, timeout=delete_timeout, regex=True)
        if ret:
            log.info('Delete file|dir: Successful!')
        return ret

    @func_details
    def touch_files(self, target_files, mount_device, mount_dir, clean=True, keep_mount=False):
        """ Create file(s) on a Linux mounted partition.
        Using the linux 'touch' command, files will be created with full permissions set.
        If the file already exists it will be replaced if clean is True.
        If a new mount has to be done to create the files, this routine will unmount when done.
        :param target_files: list of target file names
        :param mount_device: device to to mount
        :param mount_dir: directory of mounted device
        :param clean: boolean flag for removing existing files
        :param keep_mount: keep the mount intact after touching
        :return:
        """
        target_files = [target_files] if not isinstance(target_files, list) else target_files

        # Mount
        mounts = self.MountDescriptor(mount_device, mount_dir)
        mount_result, previous_mount = self.mount_devices(mounts)
        if not mount_result:
            log.error("Cannot create files due to mount failure.")
            return False
        self._uut_conn.send('cd {0}\r'.format(mount_dir), expectphrase=self._uut_prompt, timeout=30, regex=True)
        all_files = self.get_device_files(sub_dir='', file_filter='.*?', attrib_flags='-')
        log.debug("Files collected (current): {0}".format(all_files))

        for target_file in target_files:
            if target_file in all_files and clean:
                self._uut_conn.send('rm -f {0}\r'.format(target_file), timeout=60, expectphrase=self._uut_prompt, regex=True)
            self._uut_conn.send('sync\r', timeout=60, expectphrase=self._uut_prompt, regex=True)
            self._uut_conn.send('touch {0}\r'.format(target_file), timeout=60, expectphrase=self._uut_prompt, regex=True)
            self._uut_conn.send('chmod 777 {0}\r'.format(target_file), timeout=60, expectphrase=self._uut_prompt, regex=True)
        # Final sync
        self._uut_conn.send('sync\r', timeout=60, expectphrase=self._uut_prompt, regex=True)
        time.sleep(2.0)

        # Now check to make sure all the target files are present.
        ret = True
        all_files = self.get_device_files(sub_dir='', file_filter='.*?', attrib_flags='-')
        log.debug("Files collected (post op): {0}".format(all_files))
        if sorted(target_files) == sorted(list(set(target_files) & set(all_files))):
            log.info("All target files are present.")
        else:
            log.error("Not all files were present; check file names and mounting permission.")
            ret = False

        # Unmount only if the device was newly mounted in this function AND no keep mount.
        # This preserves the UUT in the same state before this function was called.
        if not previous_mount and not keep_mount:
            ret &= self.umount_devices(mounts=mounts, device_filter=None)

        return ret

    def check_crc(self, filename, locale, crc=None, server_dir=''):
        """ Check CRC
        -------------
        Check a file on the UUT/target device OR on the Apollo Server.
        Three methods:
        1. MD5
        2. CKSUM (CRC-32)
        3. File present (if no crc provided).
        :param filename: Filename (may include path) to check
        :param locale: Location to target = 'uut' or 'server'
        :param crc: md5 or cksum value
        :param server_dir:
        :return: True if CRC matches or file is present (based on input)
        """
        if crc:
            # Using a crc so determine which type
            if len(crc) == 32:
                cmd = 'md5'
                pattern = '([0-9]{32}) '
            elif len(crc) <= 10:
                cmd = 'cksum'
                pattern = '([0-9]{1,10}) '
            else:
                log.error("TFTP: file '{0}' expected crc={1} is of unknown size.".format(filename, crc))
                return False

            # Run the command
            if locale.lower() == 'uut':
                self._uut_conn.send('{0} {1}\r'.format(cmd, filename), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                m = re.search(pattern, self._uut_conn.recbuf)
            elif locale.lower() == 'server':
                m = re.search(pattern, shellcmd('{0} {1}'.format(cmd, os.path.join(server_dir, filename))))
            else:
                log.error("CRC: Unrecognized target location.")
                m = None
            file_crc = m.groups()[0] if m else "0"

            # Now compare
            if crc == file_crc:
                log.debug("File CRC confirmed: {0}".format(file_crc))
                ret = True
            else:
                log.error("File CRC {0} does not match expected CRC {1}.".format(file_crc, crc))
                ret = False
        else:
            # Not using a crc so just check file presence.
            if locale.lower() == 'uut':
                self._uut_conn.send('ls --color=never {0}\r'.format(filename), expectphrase=self._uut_prompt, timeout=30,
                              regex=True)
                time.sleep(self.RECBUF_TIME)
                if filename in self._uut_conn.recbuf and "No such file" not in self._uut_conn.recbuf:
                    log.debug("File is confirmed present: {0}".format(filename))
                    ret = True
                else:
                    log.error("File NOT present.")
                    ret = False
            elif locale.lower() == 'server':
                if os.path.exists(os.path.join(server_dir, filename)):
                    ret = True
                else:
                    log.error("Server file NOT present.")
                    ret = False
            else:
                log.error("CRC: Unrecognized target type.")
                ret = False

        return ret

    def get_pwd(self):
        self._uut_conn.send('pwd\r', expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(self.RECBUF_TIME)
        if len(self._uut_conn.recbuf.splitlines()) > 2:
            return self._uut_conn.recbuf.splitlines()[-2].strip()
        else:
            raise Exception('Cannot get current path with pwd.')

    def cd(self, target_dir):
        if target_dir[-1] == '/':
            target_dir = target_dir[:-1]

        if target_dir != self.get_pwd():
            self._uut_conn.send('cd {0}\r'.format(target_dir), expectphrase=self._uut_prompt, timeout=60, regex=True)
            if target_dir != self.get_pwd():
                log.debug("Problem with target dir; can't cd.")
                ret = False
            else:
                log.debug("'cd' to target good.")
                ret = True
        else:
            log.debug("Already at target dir.")
            ret = True
        return ret
