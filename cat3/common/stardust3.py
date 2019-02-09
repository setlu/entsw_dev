"""
Stardust3
"""

# Python
# ------
import sys
import re
import logging
import time
import parse
import os
from collections import namedtuple


# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.diags.stardust import Stardust as _Stardust
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Stardust Series3 Module"
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

class _Stardust3(_Stardust):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(_Stardust3, self).__init__(mode_mgr, ud, **kwargs)
        return

    # ------------------------------------------------------------------------------------------------------------------
    # MCU
    # ------------------------------------------------------------------------------------------------------------------
    @apollo_step
    def switch_mcu_mode(self, **kwargs):
        """ Switch MCU Mode (kkmode)
        :menu: (enable=True, name=MCU IOS, section=Diags, num=1, args={'kkmode': 'IOS'})
        :menu: (enable=True, name=MCU CL, section=Diags, num=1, args={'kkmode': 'CL'})
        :param kwargs:
        :return (str): aplib.PASS/FAIL
        """
        def __switch_mcu_mode(mode):
            """ Get MCU Mode
            Sample output:
            Kirchhoff MCU is in IOS mode
            Kirchhoff MCU is in Coulomb (diag) mode
            :param (str) mode:
            :return: boolean tuple (switch_result, reboot)
            """
            mode = mode.lower()
            mode = 'cl' if mode == 'coulomb' else mode

            # Sanity
            if mode != 'ios' and mode != 'cl':
                log.error("Unknown kkmode requested ({0}).".format(mode))
                return False, False

            # Check current mode
            kkmode = self._get_mcu_mode()
            kkmode = 'cl' if kkmode == 'coulomb' else kkmode
            expectphrase = {
                'ios': 'request is successful',
                'cl': '.*',
                None: '.*',
            }

            # Check for supported command
            if not kkmode:
                log.error("The kkmode is undefined; check the product for command support.")
                return False, False
            elif kkmode == 'not_applicable':
                log.warning("The kkmode is not applicable; no MCU switch possible.")
                return True, False
            else:
                log.debug("A kkmode was retrieved.")

            # Perform switch
            if mode != kkmode:
                log.debug("MCU switching to mode '{0}'".format(mode))
                self._uut_conn.send('kkswitch {0}\r'.format(mode), expectphrase=expectphrase.get(kkmode, '.*'),
                                    timeout=30, regex=True)
                log.debug("Reboot will occur...")
                time.sleep(2.0)
                return True, True
            else:
                log.debug("Already in mode '{0}'".format(mode))
                return True, False

        if 'mcu' not in self._ud.uut_config:
            log.warning("The 'mcu' data dict is not defined per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        # Process input
        kkmode = kwargs.get('kkmode', None)
        if not kkmode:
            kkmode = aplib.ask_question("MCU Mode", answers=['IOS', 'CL'])

        # Check Mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.error("Wrong mode; need to be in STARDUST.")
            return aplib.FAIL, 'Wrong mode.'

        # Perform switch
        kkswitch, reboot = __switch_mcu_mode(kkmode)
        if kkswitch:
            if reboot:
                log.debug("MCU mode switch waiting for reboot...")
                result, _ = self._mode_mgr.wait_for_boot(boot_mode='BTLDR',
                                                         boot_msg='(?:Booting)|(?:Initializing)')
                if not result:
                    errmsg = "Boot problem after MCU mode switch."
                    log.error(errmsg)
                    return aplib.FAIL, errmsg
            else:
                log.debug("MCU mode switch done.")
        else:
            errmsg = "Problem with MCU mode switch."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Return to mode
        if not self._mode_mgr.goto_mode('STARDUST'):
            errmsg = "Problem loading diags after MCU mode switch."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        return aplib.PASS

    @apollo_step
    def set_mcu_id(self, **kwargs):
        """ Set MCU ID
        :menu: (enable=True, name=MCU SET ID, section=Diags, num=1, args=None)
        :param kwargs:
        :return (str): aplib.PASS/FAIL
        """
        def __set_mcu_id(mac_addr, mcu_instance=0, stack_num=1, poepresent=None, sku=None, timeout=200):
            """ Set MCU ID

            SAMPLE OUTPUT:
            PL24_CR> AlchemyProgram 0 -eeprom -mac:76:88:28:00:07:80 -stack:1
            Programming Alchemy 0 (Sub Addr 0) Alchemy Config registers.
            Wait for 5 seconds after writing Alchemy Config registers..
            Programming Alchemy 0 (Sub Addr 0) MAC address
            Wait for 5 seconds after writing MAC address..
            Programming Alchemy 0 (Sub Addr 0) stackable bit to: 1.
            Wait for 5 seconds after writing StackPower bit
            Sending RE_SYS_RESET command to Alchemy-0, wait for 12 seconds...
            PASSED

            AlchemyProgram [<inst>]
                 [-eeprom] [-mac:<MAC address>] [-stack:<data stack>]
                 [-sku:<sku_enum>]
                 [-poepresent:<poepresent>]
                 [-hw:<img>] [-bl:<img>] [-sw_bin:<img>] [-sw_srec:<img>] [-cl]


            <inst> -- Alchemy instance number (default is all instances).
            -eeprom -- Program EEPROM with defaults from Stardust config.
            -sku:<sku> -- Setting of SKU type.
                        (0 - Set Alchemy16, 1 - Set Alchemy12)
                        NOTE: A16 = for 48 port units
                              A12 = for 24 port units
            -poepresent:<poepresent> -- Setting of POE Present.
                        (0 - Set POE Not Present, 1 - Set POE Present)
            -mac:<MAC address> -- MAC address (xx:xx:xx:xx:xx:xx) saved in the MCU.
            -stack:<Data stack> -- Data stackable setting saved in the MCU (0 or 1).
            -hw:<img> -- MCU hardware image file.
            -bl:<img> -- MCU bootloader image file, not applicable for Coulomb.
            -sw_bin:<img> -- MCU software binary image file.
            -sw_srec:<img> -- MCU software SREC image file, not applicable for Coulomb.
            -cl -- MCU upgrade is targeted for Coulomb.

            :param mac_addr:
            :param mcu_instance:
            :param stack_num:
            :param poepresent: (auto handled by -eeprom)
            :param sku:        (auto handled by -eeprom)
            :param timeout:
            :return:
            """
            # Get the mode.
            kkmode = self._get_mcu_mode()
            if kkmode == 'ios':
                log.debug("MCU is in IOS mode; correct for ID programming.")
            elif kkmode == 'coulomb':
                log.warning("MCU is in Coulomb mode; unable to program ID. Must be in IOS mode.")
                return False
            elif kkmode == 'not_applicable':
                log.debug("MCU has no mode switch.")
            else:
                log.error("Unknown MCU mode ({0}).".format(kkmode))
                log.warning("Product may not support MCU. Check product_definition.")
                return False

            log.debug("MAC for MCU ID: {0}".format(mac_addr))

            # Sanity
            if not common_utils.validate_mac_addr(mac_addr):
                log.error("Problem with MAC Addr format: '{0}'".format(mac_addr))
                return False

            # Format MAC
            mac = common_utils.convert_mac(mac_addr, conv_type='6:')

            # Set the args
            args = '{0} -eeprom -mac:{1} -stack:{2}{3}{4}'.format(mcu_instance, mac, stack_num,
                                                                  ' -poepresent:{0}'.format(
                                                                      poepresent) if poepresent else '',
                                                                  ' -sku:{0}'.format(sku) if sku else '')

            # Do the signing
            log.debug("Performing MCU {0} id signing...".format(kkmode.upper()))
            log.debug("Args = {0}".format(args))
            self._uut_conn.send('AlchemyProgram {0}\r'.format(args), expectphrase=self._uut_prompt, timeout=timeout,
                                regex=True)
            time.sleep(self.RECBUF_TIME)

            if 'PASSED' in self._uut_conn.recbuf:
                log.debug("MCU ID programming PASSED.")
                return True
            else:
                log.error("MCU ID programming FAILED.")
                log.error(self._uut_conn.recbuf)
                return False
        # -----------------------------------------------

        if 'mcu' not in self._ud.uut_config:
            log.warning("The 'mcu' data dict is not defined per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        # Process input
        mcu_instance = kwargs.get('mcu_instance', 0)
        stack_num = kwargs.get('stack_num', 1)
        mcu_id = kwargs.get('mcu_id', self._ud.uut_config.get('MAC_ADDR', None))
        poepresent = kwargs.get('poepresent', 1 if self._ud.uut_config.get('poe', None) else 0)
        sku = kwargs.get('sku', None)

        # Check MCU ID
        if not mcu_id:
            errmsg = "No MAC available for MCU ID."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Check Mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.error("Wrong mode; need to be in STARDUST.")
            return aplib.FAIL, "Wrong mode."

        # Perform
        log.debug("MCU Instance   : {0}".format(mcu_instance))
        log.debug("MCU ID         : {0}".format(mcu_id))
        log.debug("MCU Stack Num  : {0}".format(stack_num))
        log.debug("MCU PoE Present: {0}".format(poepresent)) if poepresent else None
        log.debug("MCU Sku        : {0}".format(sku)) if sku else None
        if __set_mcu_id(mac_addr=mcu_id,
                        mcu_instance=mcu_instance,
                        stack_num=stack_num,
                        poepresent=poepresent,
                        sku=sku, ):
            log.debug("MCU ID done.")
            return aplib.PASS
        else:
            errmsg = "Problem with MCU ID programming."
            log.error(errmsg)
            return aplib.FAIL, errmsg

    @apollo_step
    def update_mcu_settings(self, **kwargs):
        """ Update MCU Settings

            Includes:
                1. Fan Curve
                2. UCSDS
                3 P-min

            This routine performs the commands in the order listed in the dict.
            NOTE: This will update the settings regardless of whether it is needed or not needed.

            'mcu_settings': {
                'cmd': 'sendredearthframe 0 %data% -e -p:5000',
                'update': {
                    1: {'data': 'f1.06', 'label': 'Fan curve coeff', 'op': 'READ'},
                    2: {'data': '71.60.59.14.09.22.26', 'label': 'Fan curve coeff', 'op': 'WRITE'},
                    3: {'data': 'f7.04', 'label': 'UCSDS coeff', 'op': 'READ'},
                    4: {'data': '77.5f.36.32.e9', 'label': 'UCSDS coeff', 'op': 'WRITE'},
                    5: {'data': 'ef.02', 'label': 'Read Pmin', 'op': 'READ'},
                    6: {'data': '6f.01.fe', 'label': 'Pmin 510W', 'op': 'WRITE'},
                },
            },

        Example output:
        Tx: Char0:_PE_,0(60) Char1:1,02(82) Data:f1.06. End:d9
        Rx: Char0:_PEI,0(70) Char1:1,06(86) Data:20.4c.0d.09.0f.2f. End:b6

        USAGE: SendRedEarthFrame
            <subaddr> [<data0>.<data1>...[<dataN>]
            [<-x>] [<-e>] [<-c>] [-p:<resp_time>]
            [-length:<length>] [-s:<seqbit>]
            <subaddr> -- subordinate address (0xf for broadcast).
            <payload_data> -- Format: [<data0>.<data1> ... <dataN>]
                        where <dataN> is a byte in hex.
            -x -- use extended 12-bit addressing.
            -e -- append end byte (check sum).
            -c -- set command bit.
            -p:<resp_time> -- response indicator and timeout in mS
                        (0..5000, default:no response).
            -l:<length> -- force frame length (0..64, default:auto).
            -s:<seqbit> -- force sequence bit (0/1 default:auto).

        :menu: (enable=True, name=UPDATE MCU SETTING, section=Upgrade, num=7, args={'force': False})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('UPDATE FANCURVE')
        log.info('STEP: Update Fancurve.')

        if 'mcu_settings' not in self._ud.uut_config:
            log.warning("The 'mcu_settings' data dict is not defined per the product_definition.")
            log.warning("This update will be skipped.")
            return aplib.SKIPPED

        # Process input
        mcu_settings = kwargs.get('mcu_settings', self._ud.uut_config.get('mcu_settings', {}))
        # force = kwargs.get('force', False)

        # Sanity check
        if not mcu_settings or len(mcu_settings.keys()) == 0:
            log.warning("This 'mcu_settings' data dict is empty.")
            return aplib.FAIL

        # Check mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.error("Wrong mode; need to be in STARDUST.")
            return aplib.FAIL

        generic_cmd = mcu_settings.get('cmd', None)
        # Process each index in the sequential order given.
        for index in sorted(mcu_settings.get('update', {}).keys()):
            prog_dict = mcu_settings['update'][index]
            cmd = common_utils.rebuild_cmd(prog_dict, self._ud.uut_config, command=generic_cmd)
            op = prog_dict.get('op', '')
            prog_data = prog_dict.get('data', '')
            label = prog_dict.get('label', '')
            log.debug("MCU Op     : {0}".format(op))
            log.debug("MCU Desc   : {0}".format(label))
            log.debug("MCU Command: {0}".format(cmd))
            self._uut_conn.send("{0}\r".format(cmd), expectphrase=self._mode_mgr.uut_prompt_map['STARDUST'],
                               timeout=60, regex=True)
            m = parse.parse("{x1:0}Rx:{x2:1} Data:{data:2}. {x3:3}", self._uut_conn.recbuf)
            rx_data = m.named.get('data', None) if hasattr(m, 'named') else None
            if op == 'WRITE':
                if prog_data[3:] != rx_data:
                    log.error("The RX Data did NOT match the programming data.")
                    return aplib.FAIL
                else:
                    log.debug("WRITE is good!  MCU setting is updated.")
            if op == 'READ':
                if prog_data[3:] != rx_data:
                    log.warning("The MCU setting will need updating.")

        return aplib.PASS

    # -----------
    @func_details
    def _upgrade_mcu(self, name, image_pkg, timeout=400, home_dir=None):
        """ Upgrade MCU

        COMMAND
        -------
        USAGE: AlchemyProgram [<inst>]
             [-eeprom] [-mac:<MAC address>] [-stack:<data stack>]
             [-sku:<sku_enum>]
             [-poepresent:<poepresent>]
             [-hw:<img>] [-bl:<img>] [-sw_bin:<img>] [-sw_srec:<img>] [-cl]
        <inst>                   -- Alchemy instance number (default is all instances).
        -eeprom                  -- Program EEPROM with defaults from Stardust config.
        -sku:<sku>               -- Setting of SKU type. (0 - Set Alchemy16, 1 - Set Alchemy12)
        -poepresent:<poepresent> -- Setting of POE Present. (0 - Set POE Not Present, 1 - Set POE Present)
        -mac:<MAC address>       -- MAC address (xx:xx:xx:xx:xx:xx) saved in the MCU.
        -stack:<Data stack>      -- Data stackable setting saved in the MCU (0 or 1).
        -hw:<img>                -- MCU hardware image file.
        -bl:<img>                -- MCU bootloader image file, not applicable for Coulomb.
        -sw_bin:<img>            -- MCU software binary image file.
        -sw_srec:<img>           -- MCU software SREC image file, not applicable for Coulomb.
        -cl                      -- MCU upgrade is targeted for Coulomb.

        SAMPLE FILES:
        'app_data.srec_V90', 'app_flash.bin_V90', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                           'c_kirchhoff_swap_33.bin', 'coulomb_kirchhoff_33.bin'

        SAMPLE OUTPUT
        -------------
        N24Pwr_CR> AlchemyProgram -hw:c_kirchhoff_swap_31.bin -sw_bin:app_flash.bin
                                  -sw_srec:app_data.srec -bl:Cisco_loader.srec
        Note: Programming Hw or Sw_Bootloader image will result in  system power cycle
        Start programming images process...
        Programming Sw_Binary file app_flash.bin (361802 bytes):
        .... 10% .... 20% .... 30% .... 40% .... 50% .... 60% .... 70% .... 80% .... 90% .... 100%
        Done. Total time 88 seconds.
        Programming Sw_Srec file app_data.srec (25166 bytes):
        .... 10% .... 20% .... 30% .... 40% .... 50% .... 60% .... 70% .... 80% .... 90% .... 100%
        Done. Total time 6 seconds.
        Programming Sw_Bootloader file Cisco_loader.srec (86370 bytes):
        .... 10% .... 20% .... 30% .... 40% .... 50% .... 60% .... 70% .... 80% .... 90% .... 100%
        Done. Total time 21 seconds.
        Programming Hw file c_kirchhoff_swap_31.bin (594412 bytes):
        .... 10% .... 20% .... 30% .... 40% .... 50% .... 60% .... 70% .... 80% .... 90% .... 100%
        Done. Total time 145 seconds.
        30 secs?
        N24Pwr_CR>

        :param (str) name:
        :param (dict) image_pkg: All files to upgrade.
        :param (int) timeout:
        :param (str) home_dir:
        :param kwargs: optional params for tftp transfers
        :return:
        """
        log.debug("MCU name: {0}".format(name))
        self._clear_recbuf()
        self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Set known Diags home dir, Get MCU Sub-dir,
        home_dir = self.get_cwd() if not home_dir else home_dir
        mcu_subdir = image_pkg.keys()[0]
        mcu_files = image_pkg[mcu_subdir]
        self.set_cwd(home_dir)

        # Check that the image package files are available
        device_dirs = self.get_device_files(attrib_flags='d')
        log.debug(device_dirs)
        if not device_dirs or mcu_subdir not in device_dirs:
            log.warning("Required MCU package subdir '{0}' is not in expected flash location.".format(mcu_subdir))
            log.debug("Attempting image load...")
            src_files = [os.path.join(mcu_subdir, i) for i in mcu_files]

            if not self._mode_mgr:
                log.error("MCU Upgrade not possible.  Must have methods for mode operation.")
                return False
            if not self._ud:
                log.error("MCU Upgrade not possible.  Must have a UUT descriptor.")
                return False

            server_ip = self._ud.uut_config.get('server_ip', None)
            netmask = self._ud.uut_config.get('netmask', None)
            uut_ip = self._ud.uut_config.get('uut_ip', None)
            uut_linux_prompt = self._ud.uut_config.get('uut_prompt_map', {}).get('LINUX', '# ')
            if all([server_ip, uut_ip, netmask]):
                self._mode_mgr.goto_mode('LINUX')
                result = self._linux.transfer_tftp_files(src_files=src_files,
                                                          dst_files=None,
                                                          direction='get',
                                                          server_ip=server_ip, ip=uut_ip, netmask=netmask, force=True)
                self._mode_mgr.goto_mode('STARDUST')
            else:
                log.error("Image load not possible; network params are absent.")
                result = False
            if not result:
                log.debug("MCU Image load: FAILED.")
                return result
            else:
                log.debug("MCU Image load: PASSED.")

        log.debug("MCU package files = {0}".format(mcu_files))
        device_files = self.get_device_files(sub_dir=mcu_subdir, file_filter='[a-zA-Z].*?', attrib_flags='-')
        device_files.sort()
        mcu_files.sort()
        if not device_files or device_files != mcu_files:
            log.error("Files in the MCU subdir package do NOT match the files loaded to flash.")
            log.error("Check the product_definition and the flash contents.")
            return False

        # Move to MCU Sub-dir
        mcu_full_dir = os.path.join(home_dir, mcu_subdir)
        log.debug("MCU image package location = '{0}'".format(mcu_full_dir))
        if not self.set_cwd(mcu_full_dir):
            log.error("Problem changing to MCU subdir location.")
            return False

        # Check the current MCU Mode
        kkmode = self._get_mcu_mode()
        if kkmode == 'ios':
            log.debug("MCU is in IOS mode.  Upgrade will proceed.")
        elif kkmode == 'coulomb':
            log.error("MCU is in Coulomb mode and should be switched to IOS mode prior to upgrade.")
            return False
        elif kkmode == 'not_applicable':
            log.debug("MCU has no mode switch.")
        else:
            log.error("Unknown MCU mode ({0}).".format(kkmode))
            log.warning("Product may not support MCU. Check product_definition.")
            self.set_cwd(home_dir)
            return False

        # Select the appropriate files.
        # (Note: file type is given by primary naming convention.)
        # IOS parameters
        log.debug("Getting ios mcu images...")
        sw_bin = next((s for s in mcu_files if 'app_flash' in s), None)
        sw_rec = next((s for s in mcu_files if 'app_data' in s), None)
        bl = next((s for s in mcu_files if 'isco_loader' in s), None)
        hw = next((s for s in mcu_files if 'kirchhoff_swap' in s and 'c_kirchhoff_swap' not in s), None)
        ios_param_map = [('-sw_bin:', sw_bin), ('-sw_srec:', sw_rec), ('-bl:', bl), ('-hw:', hw)]
        args_list = ['{0}{1}'.format(p, i) for p, i in ios_param_map if i]
        args = ' '.join(args_list)
        max_file_count = len(args_list)
        # Coulomb parameters
        log.debug("Getting coulomb mcu images...")
        cl_sw_bin = next((s for s in mcu_files if 'coulomb_kirchhoff' in s), None)
        cl_hw = next((s for s in mcu_files if 'c_kirchhoff_swap' in s), None)
        cl_param_map = [('-sw_bin:', cl_sw_bin), ('-hw:', cl_hw)]
        cl_args_list = ['{0}{1}'.format(p, i) for p, i in cl_param_map if i]
        cl_args = '-cl ' + ' '.join(cl_args_list)
        cl_max_file_count = len(cl_args_list)

        # Do the upgrade
        result_list = []
        log.debug("Performing MCU upgrade...")
        for arg in [(args, max_file_count), (cl_args, cl_max_file_count)]:
            log.debug("Args = {0}".format(arg))
            if arg[1] > 0:

                try:
                    self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=15, idle_timeout=10, regex=True)
                except (apexceptions.IdleTimeoutException, apexceptions.TimeoutException):
                    log.warning("MCU upgrade timeout response.")
                    log.warning("Mode is NOT available due to reboot or upgrade still processing; waiting for prompt...")
                    self._uut_conn.send('\r', expectphrase=None, regex=True)
                    self._uut_conn.waitfor([self._mode_mgr.uut_prompt_map['BTLDR'],
                                             self._mode_mgr.uut_prompt_map['STARDUST']],
                                            timeout=240, regex=True, idle_timeout=60)

                self._mode_mgr.goto_mode('STARDUST')
                if not self.set_cwd(mcu_full_dir):
                    log.error("Problem changing to MCU subdir location.")
                    return False
                self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=120, regex=True)
                self._uut_conn.send('AlchemyProgram {0}\r'.format(arg[0]), expectphrase='.*', timeout=60, regex=True)

                # Loop on output status
                loop_count = 0
                file_count, previous_file_count = 0, 0
                old_status = ''
                end_pattern = '{0}|(?:[Ss]witch:)'.format(self._uut_prompt)
                while file_count != arg[1] and loop_count < int(timeout) * 2:
                    # Check for file done
                    if re.search('Done\.', self._uut_conn.recbuf):
                        # Count the number of times the "Done." msg appears.
                        p = re.compile('(Done\. .*)+')
                        m = p.findall(self._uut_conn.recbuf)
                        if m:
                            file_count = len(m)
                        if file_count != previous_file_count:
                            log.debug("File done count = {0}.".format(file_count))
                            previous_file_count = file_count

                    # Grab last line of output
                    new_status = self._uut_conn.recbuf.splitlines()[-1:][0]
                    if old_status != new_status:
                        # A change in the last line of output (recbuf) occurred
                        if re.search('Programming .*? bytes', new_status):
                            log.debug("{0}".format(new_status))
                        if re.search('[0-9]+%', new_status):
                            log.debug("{0}".format(new_status))
                        old_status = new_status

                    # Look for abnormal patterns
                    if re.search('((?i)Err)|((?i)Fail)', self._uut_conn.recbuf):
                        log.debug("Error/Failure.")
                        break
                    if re.search(end_pattern, self._uut_conn.recbuf):
                        log.debug("Prompt found.")
                        break

                    loop_count += 1
                    time.sleep(0.5)

                # At this point upgrade file set is done.
                #
                # Power cycle will occur when done. It will take approx 2 mins for most platforms.
                # TODO: Check diags to see if power cycle is automatic or must manually do it.
                #
                # NOTE: The beginning of this loop branch will test for mode and wait if necessary.
                # btldr_result, _ = self._mode_mgr.wait_for_boot(boot_mode='BTLDR', boot_msg='(?:Booting)|(?:Initializing)')
                # if not btldr_result:
                #    log.error("The Reset did NOT complete properly; FATAL ERROR.")
                #    raise apexceptions.ScriptAbortException("Reset + boot has fatal error.")

                # Check for correct completion based on output status.
                log.debug("MCU File count = {0} of {1}".format(file_count, max_file_count))
                if file_count != arg[1]:
                    log.debug("MCU file programming INCOMPLETE!")
                    result_list.append(False)
                else:
                    log.debug("MCU file programming COMPLETE!")
                    result_list.append(True)

        return all(result_list)

    @func_details
    def _check_mcu(self, name, revision):
        """ Check MCU Version
        Sample output (IOS):
        Shannon48U_CR> alchemy ver
        A#    (SA)    SW Version          HW Version    Bootloader Version
        0    ( 0)    APPL 0.90 (0x5a)    41  (0x29)    16  (0x10)
        1    ( 7)    APPL 0.90 (0x5a)    41  (0x29)    16  (0x10)
        2    (14)    APPL 0.90 (0x5a)    41  (0x29)    16  (0x10)

        Sample output (Coulomb):
        Shannon48U_CR> alchemy version
        A#    (SA)    SW Version          HW Version    Bootloader Version
        0    ( 0)    APPL 0.33 (0x21)    41  (0x29)    0   (0x00)
        1    ( 7)    APPL 0.33 (0x21)    41  (0x29)    0   (0x00)
        2    (14)    APPL 0.33 (0x21)    41  (0x29)    0   (0x00)

        :param name:
        :param revision:
        :return:
        """
        # Get mode
        kkmode = self._get_mcu_mode()
        if not kkmode:
            log.error("MCU mode is unavailable.  Check UUT and diags.")
            log.error("Skipping MCU revision check.")
            return False
        elif kkmode == 'not_applicable':
            log.warning("MCU mode is not applicable. The psuedo-mode 'single' will be applied.")
            rev = revision
            revision = dict(single=rev)
            kkmode = 'single'

        # Input check
        if kkmode not in revision and kkmode != 'single':
            log.warning("No MCU {0} revision entry.".format(kkmode))
            log.warning("Skipping MCU revision check.")
            return True

        # Get revision
        # (not yet implemented in diags) self._uut_conn.send('{0} version\r'.format(name), expectphrase=self._uut_prompt, timeout=30, regex=True)
        # Note: The version retrieval for all platforms use the legacy command (as of 08/01/2018).
        self._clear_recbuf()
        self._uut_conn.send('alchemy version\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        rev_pattern = 'APPL {sw:0} ({swx:1}) {hw:2} ({hwx:3}) {bl:4} ({blx:5})'
        m1 = parse.search(rev_pattern, self._uut_conn.recbuf)
        m2 = parse.search(rev_pattern, revision[kkmode])
        # Fix-up dicts
        m_uut = {k: v.strip() for k, v in m1.__dict__['named'].items()} if m1 else None
        m_rev = {k: v.strip() for k, v in m2.__dict__['named'].items()} if m2 else None

        # Sanity checks
        if not m_uut:
            log.error("No available UUT data for MCU revision.")
            return False
        if not m_rev:
            log.warning("No available revision reference data. Check product_definition.")
            log.warning("Skipping MCU revision check.")
            return True
        if 'sw' not in m_uut or 'hw' not in m_uut or 'bl' not in m_uut:
            log.error("Incomplete revision data. Check UUT output and format.")
            log.debug(m_uut)
            return False

        # Print & Compare
        log.debug("MCU current : {0}".format(m_uut))
        log.debug("MCU expected: {0}".format(m_rev))
        if m_uut == m_rev:
            log.info("MCU Revision MATCH for mode={0}.".format(kkmode))
            return True
        elif m_uut['swx'] > m_rev['swx']:
            log.warning("MCU {0} Rev={1} is NEWER than expected Rev={2}.!".format(kkmode, m_uut['swx'], m_rev['swx']))
            log.warning("MCU downgrade is not necessary.")
            return True
        else:
            log.warning("MCU Revision MISMATCH for mode={0}!".format(kkmode))
            return False

    @func_details
    def _get_mcu_mode(self):
        """ Get MCU Mode

        Sample#1:
        ShannonCR24P> kkmode
        Kirchhoff MCU is in IOS mode
        --OR--
        Kirchhoff MCU is in Coulomb (diag) mode

        Sample#2:
        Dogood48P> kkmode
        ERR: Command not found: "kkmode"

        :return:
        """

        @func_retry
        def __kkmode():
            self._clear_recbuf()
            self._uut_conn.send('kkmode\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('MCU is in ([\S]+) [\S]')
            n = p.findall(self._uut_conn.recbuf)
            if not n and 'Command not found' in self._uut_conn.recbuf:
                return ['not_applicable']
            return n

        m = __kkmode()
        if m:
            log.debug("Detected MCU mode = {0}".format(m[0]))
            return m[0].lower()
        else:
            log.debug("MCU mode NOT detected!")
            return None

    # ------------------------------------------------------------------------------------------------------------------
    # SerDes
    # ------------------------------------------------------------------------------------------------------------------
    @apollo_step
    def serdeseye_sif_test(self, **kwargs):
        """SerdesEye Test
        :menu: (enable=True, name=SERDESEYE SIF, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        area = aplib.apdicts.test_info.test_area

        interfaces = kwargs.get('serdeseye_interfaces', self._ud.uut_config.get('serdeseye', {}).get('interfaces', []))
        sif_options = kwargs.get('serdeseye_sif_options', self._ud.uut_config.get('serdeseye', {}).get(area, {}).get('sif_options', ''))
        eye_version = kwargs.get('serdeseye_version', self._ud.uut_config.get('serdeseye', {}).get('version', '1'))
        asic_core_count = kwargs.get('asic_core_count', self._ud.uut_config.get('asic', {}).get('core_count', 0))

        # The stack cable must be installed and good for SIF.
        if self._ud.uut_status.get('stackrac', None) != aplib.PASS and 'SIF' in interfaces:
            log.warning("There is no StackRAC passing status therefore SIF SerDesEye cannot be tested.")
            log.warning("Please check the process and ensure StackRAC can pass.")
            log.warning("SIF SerDesEye will be FAILED.")
            return aplib.FAIL, 'Cannot test SIF due to bad StackRAC status.'

        # Must have the ASIC core count for SIF (TBD: get this automatically).
        if asic_core_count == 0 and 'SIF' in interfaces:
            log.warning('ASIC Core count is not set; SIF SerDesEye will be skipped.')
            log.warning('PLEASE CONFIRM PRODUCT DEFINITION FOR UUT.')
            return aplib.SKIPPED

        # Check mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.warning('Wrong mode ({0}) for this operation. Mode "STARDUST" is required.'.format(self._mode_mgr.current_mode))
            return aplib.FAIL, 'Wrong mode.'

        # SIF Serdes test
        log.info('-' * 40)
        if 'SIF' in interfaces:
            log.debug("Running SIF SerDesEye...")
            current_sif = self._get_sif_serdeseye(asic_core_count, sif_options=sif_options, eye_version=eye_version)
            if not current_sif:
                return aplib.FAIL, 'SIF SerDesEye TEST: FAILED (no results collected).'
            result = self._check_sif_serdeseye(current_sif) if current_sif else None
            if not result:
                return aplib.FAIL, 'SIF SerdesEye TEST: FAILED.'
            log.info('SIF SerDesEye TEST: PASSED.')
        else:
            log.warning("SIF SerdesEye TEST: SKIPPED.")
            return aplib.SKIPPED

        log.info('-' * 40)
        log.info('SerDesEye Testing done.')
        return aplib.PASS

    @apollo_step
    def serdeseye_nif_test(self, **kwargs):
        """SerdesEye Test
        :menu: (enable=True, name=SERDESEYE NIF, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        area = aplib.apdicts.test_info.test_area

        interfaces = kwargs.get('serdeseye_interfaces', self._ud.uut_config.get('serdeseye', {}).get('interfaces', []))
        nif_options = kwargs.get('serdeseye_nif_options', self._ud.uut_config.get('serdeseye', {}).get(area, {}).get('nif_options', ''))

        # Check mode
        if self._mode_mgr.current_mode != 'STARDUST':
            log.warning('Wrong mode ({0}) for this operation. Mode "STARDUST" is required.'.format(self._mode_mgr.current_mode))
            return aplib.FAIL, 'Wrong mode.'

        # NIF Serdes test
        log.info('-' * 40)
        if 'NIF' in interfaces:
            log.debug("Running NIF SerDesEye...")
            uplink_ports = self._ud.uut_config.get('traffic_cases', {}).get('TrafCase_NIF_1', {}).get('uplink_ports', {})
            log.debug('uplink ports= {}'.format(uplink_ports))
            _, uplink_test_card = self._callback.traffic.fmdiags.config_uplink_test_card(uplink_ports=uplink_ports)
            self.sysinit() if uplink_test_card else None

            current_nif = self._get_nif_serdeseye(uplink_test_card, eye_option=nif_options)
            if not current_nif:
                return aplib.FAIL, 'NIF SerDesEye TEST: FAILED (no results collected).'

            result = self._check_nif_serdeseye(current_nif)
            if not result:
                return aplib.FAIL, 'NIF SerDesEye TEST: FAILED.'
            log.info("NIF SerDesEye TEST: PASSED.")
        else:
            log.warning("NIF SerDesEye TEST: SKIPPED.")
            return aplib.SKIPPED

        log.info('-' * 40)
        log.info('SerDesEye Testing done.')
        return aplib.PASS

    # -----------
    @func_details
    def _generate_sif_serdeseye(self, asic_core_count, sif_cmd_name, sif_pattern, Eye, sif_options='', eye_version=1):
        """ Generate SIF SerdesEye
        :param asic_core_count:
        :param sif_cmd_name:
        :param sif_pattern:
        :param Eye:
        :param sif_options:
        :return:
        """
        verbose = True if self._ud.verbose_level > 1 else False
        log.info('SIF Serdes Eye GENERATE (version {0})'.format(eye_version))

        sif = {}
        failures = []

        # Regex for all entries: summary, min, and max
        p = re.compile(sif_pattern)

        # Get and Check Serdes Eye
        for core in xrange(asic_core_count):
            for side in ['e', 'w']:
                common_utils.uut_comment(self._uut_conn, 'SIF', 'SerDesEye Metric ASIC {0}'.format(core))
                self._clear_recbuf(force=True)
                self._uut_conn.send('{0} {1} {2} -i:3 {3}\r'.format(sif_cmd_name, core, side, sif_options),
                                    expectphrase=self._uut_prompt, regex=True, timeout=300)
                time.sleep(self.RECBUF_TIME)
                if 'ERR:' in self._uut_conn.recbuf:
                    log.error("SIF SerDesEye error found.")
                    failures.append(
                        'Core{0}:({1}) - {2}'.format(core, side, re.findall('ERR:.*', self._uut_conn.recbuf)[0]))
                if re.search('core-to-core so no SERDES.', self._uut_conn.recbuf):
                    log.debug(re.findall('.*core-to-core.*', self._uut_conn.recbuf)[0])
                elif re.search('[Nn]o support', self._uut_conn.recbuf):
                    log.debug("SIF SerDesEye not supported for the ASIC.")
                    sif[core, side, '0', 'Sum'] = Eye._make(
                        [None if i != 'Result' else 'IGNORE' for i in Eye._fields])
                else:
                    m = p.findall(self._uut_conn.recbuf)
                    log.debug("SIF SerDesEye {0} {1} {2}".format(core, side, 'ok' if m else '?'))
                    for i in m:
                        if eye_version == 1:
                            tag = 'Sum' if not re.match('([(]?Max[)])|([(]?Min[)])', i[-3]) else i[-3][1:4]
                        elif eye_version == 2:
                            tag = 'Sum' if not re.match('([(]?Max[)])|([(]?Min[)])', i[-4]) else i[-4][1:4]
                        sif[core, side, i[0], tag] = Eye._make(i)

        if failures or len(sif) == 0:
            for failure in failures:
                log.error(failure)
            log.error('get_sif_serdeseye: FAIL. Failed to retreive valid SifSerdesEye.')
            return False

        common_utils.print_large_dict(sif, title='sif') if verbose else None
        return sif

    @func_details
    def _get_sif_serdeseye(self, asic_core_count, sif_options='', **kwargs):
        """ Get SIF SerdesEye
        :param asic_core_count:
        :param sif_options:

        sample SIF serdes eye data:
        N48P_CSR> sifserdeseye 0 e -i:10

        Using PRBS pattern 31+:
        ====  PRBS test: Doppler #0 East side rx, #1 West side tx,  ====

        Eye measurement of Doppler #0 East side rx:
        Amin(mV) AminP  AminN  Ap(mV) An(mV) EScan  LScan   E+L SyncCnt ErrCnt P/F
        ================================================================================
        A0  172.5   172.5  182.5  220.0  237.5   12     6      18   10      0     Pass
        A0  177.5   177.5  187.5  222.5  240.0   13     7      20     (Max)       Pass
        A0  170.0   170.0  182.5  220.0  237.5   12     6      18     (Min)       Pass
        A1  177.5   177.5  197.5  215.0  232.5   12     7      19   10      0     Pass
        A1  185.0   185.0  200.0  220.0  235.0   13     7      20     (Max)       Pass
        A1  175.0   175.0  192.5  215.0  230.0   12     7      19     (Min)       Pass
        A2  195.0   212.5  195.0  237.5  220.0   12     7      19   10      0     Pass
        A2  197.5   215.0  197.5  240.0  222.5   13     8      21     (Max)       Pass
        A2  192.5   210.0  192.5  237.5  220.0   12     7      19     (Min)       Pass
        A3  195.0   212.5  195.0  237.5  220.0   12     7      20   10      0     Pass
        A3  197.5   215.0  197.5  242.5  222.5   13     8      21     (Max)       Pass
        A3  190.0   210.0  190.0  237.5  217.5   12     7      19     (Min)       Pass
        C0  187.5   212.5  187.5  240.0  212.5   11     7      18   10      0     Pass
        C0  190.0   215.0  190.0  242.5  215.0   11     8      19     (Max)       Pass
        C0  187.5   212.5  187.5  240.0  212.5   11     7      18     (Min)       Pass
        C1  200.0   205.0  200.0  232.5  227.5   12     8      20   10      0     Pass
        C1  205.0   207.5  205.0  235.0  230.0   12     8      20     (Max)       Pass
        C1  197.5   202.5  197.5  232.5  227.5   12     8      20     (Min)       Pass
        C2  195.0   195.0  197.5  230.0  230.0   12     7      19   10      0     Pass
        C2  197.5   197.5  202.5  232.5  232.5   13     8      21     (Max)       Pass
        C2  195.0   195.0  195.0  230.0  227.5   12     7      19     (Min)       Pass
        C3  172.5   195.0  172.5  240.0  227.5   12     5      17   10      0     Pass
        C3  177.5   197.5  177.5  240.0  230.0   12     5      17     (Max)       Pass
        C3  167.5   195.0  167.5  240.0  225.0   12     5      17     (Min)       Pass
        E0  185.0   207.5  185.0  235.0  215.0   12     7      19   10      0     Pass
        E0  190.0   212.5  190.0  237.5  220.0   13     7      20     (Max)       Pass
        E0  182.5   205.0  182.5  232.5  215.0   12     7      19     (Min)       Pass
        E1  185.0   185.0  197.5  222.5  235.0   11     6      17   10      0     Pass
        E1  190.0   190.0  202.5  225.0  237.5   12     7      18     (Max)       Pass
        E1  177.5   177.5  197.5  220.0  235.0   11     6      17     (Min)       Pass
        E2  175.0   210.0  175.0  245.0  200.0   11     7      18   10      0     Pass
        E2  180.0   212.5  180.0  247.5  202.5   11     7      18     (Max)       Pass
        E2  172.5   210.0  172.5  242.5  200.0   11     7      18     (Min)       Pass
        E3  192.5   220.0  192.5  252.5  230.0   12     7      19   10      0     Pass
        E3  197.5   222.5  197.5  255.0  232.5   12     8      20     (Max)       Pass
        E3  190.0   217.5  190.0  252.5  230.0   12     7      19     (Min)       Pass

        Shannon24U> SifSerdesEye 0 e -i:10

        Using PRBS pattern 31+:
        NOTE: can take up to 2 secs for one channel per iteration.
        ====  PRBS test: Doppler #0 East side rx, #0 West side tx,  ====
              Eye measurement of Doppler #0 East side rx:

        Criteria: height = 30.0, UI = 0.154

        RxChan Core   mV/step Top(mV) Bot(mV) Height(mV) Left(UI) Right(UI) Width(UI) PRBS PS  PE  P/F
        ------ ------ ------- ------- ------- ---------- -------- --------- --------- ---- --- --- ----
        0      0        10.03   65.20  -65.20     130.41   -0.209     0.367     0.577   31  10   0 Pass
        0      0         9.94   64.59  -65.81     129.19   -0.211     0.367     0.562 (Min)        Pass
        0      0        10.12   65.81  -64.59     131.62   -0.195     0.367     0.578 (Max)        Pass
        1      0        12.17   91.27  -87.61     178.88   -0.225     0.336     0.561   31  10   0 Pass
        1      0        12.00   90.00  -91.41     170.62   -0.227     0.336     0.547 (Min)        Pass
        1      0        12.19   91.41  -79.22     182.81   -0.211     0.336     0.562 (Max)        Pass
        2      0        11.21   84.09  -72.88     156.97   -0.242     0.375     0.617   31  10   0 Pass
        2      0        11.06   82.97  -73.12     154.88   -0.258     0.367     0.594 (Min)        Pass
        2      0        11.25   84.38  -71.91     157.50   -0.227     0.383     0.625 (Max)        Pass
        3      0        10.80   79.93  -59.40     139.33   -0.212     0.398     0.611   31  10   0 Pass
        3      0        10.69   69.47  -59.81     128.25   -0.227     0.398     0.609 (Min)        Pass
        3      0        10.88   81.56  -58.78     141.38   -0.211     0.398     0.625 (Max)        Pass
        8      0        10.76   69.96  -69.96     139.91   -0.242     0.323     0.566   31  10   0 Pass
        8      0        10.69   69.47  -70.69     138.94   -0.242     0.320     0.562 (Min)        Pass
        8      0        10.88   70.69  -69.47     141.38   -0.242     0.336     0.578 (Max)        Pass
        9      0         9.96   64.72  -64.72     129.43   -0.258     0.291     0.548   31  10   0 Pass
        9      0         9.94   64.59  -65.81     129.19   -0.258     0.289     0.547 (Min)        Pass
        9      0        10.12   65.81  -64.59     131.62   -0.258     0.305     0.562 (Max)        Pass
        10     0         9.39   61.06  -61.06     122.12   -0.173     0.394     0.567   31  10   0 Pass
        10     0         9.38   60.94  -62.16     121.88   -0.180     0.383     0.547 (Min)        Pass
        10     0         9.56   62.16  -60.94     124.31   -0.164     0.398     0.578 (Max)        Pass
        11     0         9.24   62.84  -59.17     122.01   -0.239     0.334     0.573   31  10   0 Pass
        11     0         9.19   59.72  -60.94     119.44   -0.242     0.320     0.562 (Min)        Pass
        11     0         9.38   68.91  -50.53     128.62   -0.227     0.336     0.578 (Max)        Pass
        16     0         9.54   62.03  -60.12     122.16   -0.227     0.434     0.661   31  10   0 Pass
        16     0         9.38   60.94  -62.16     114.75   -0.227     0.430     0.656 (Min)        Pass
        16     0         9.56   62.16  -52.59     124.31   -0.227     0.445     0.672 (Max)        Pass
        17     0        11.34   70.36  -62.39     132.75   -0.225     0.430     0.655   31  10   0 Pass
        17     0        11.25   61.88  -62.91     123.75   -0.227     0.430     0.641 (Min)        Pass
        17     0        11.44   74.34  -61.88     137.25   -0.211     0.430     0.656 (Max)        Pass
        18     0         9.69   63.01  -55.27     118.28   -0.217     0.395     0.613   31  10   0 Pass
        18     0         9.56   62.16  -63.38     114.75   -0.227     0.383     0.594 (Min)        Pass
        18     0         9.75   63.38  -52.59     126.75   -0.211     0.398     0.625 (Max)        Pass
        19     0        10.91   70.93  -70.93     141.86   -0.205     0.366     0.570   31  10   0 Pass
        19     0        10.69   69.47  -71.91     138.94   -0.211     0.352     0.547 (Min)        Pass
        19     0        11.06   71.91  -69.47     143.81   -0.195     0.367     0.578 (Max)        Pass

        USAGE: SifSerdesEye <asicRx> <sideRx> [<PRBSpattern>] [-t:<PRBSTestTime>]
                    [-i:<iteration>] [-z] [-d]
            <asicRx> -- Doppler asic # to rx and get eye measurement
            <sideRx> -- east or west
            <PRBSpattern> -- choose a PRBS pattern or don't run PRBS:
             NOTE: PRBS test only works with stack links tx/rx within one board.
                0: PRBS7+
                1: PRBS7-
                2: PRBS23+
                3: PRBS23-
                4: PRBS31+ (default)
                5: PRBS31-
                6: 10101010...
                7: Repeating pattern of 64 1's and 64 0's
                8: don't run PRBS, do eye measurement only
            -t:<PRBSTestTime> -- time in msec for PRBS to run prior to checking
                 sync and error. Default 10msec.
            -i:<iteration> -- number of iterations (default 1)
            -z -- zero Az (default non-zero)
            -d -- print detail if amin >= ap in each iteration

        :return:
        """

        log.info('SIF Serdes Eye START (Gen2)')

        sif_cmd_name = 'SifSerdesEye'
        Eye = namedtuple('Eye', 'Channel Amin AminP AminN Ap An EScan LScan EL SyncCnt ErrCnt Result')
        sif_pattern = '(?m)([A-Z][0-9])[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d]+)' \
                      '[ \t]+([\d]+)[ \t]+([\d\S]+)[ \t]+([\d\S]+)[ \t]+([\d]?)[ \t]*([\S]+)[\r\n]+'

        sif = self._generate_sif_serdeseye(asic_core_count,
                                           sif_cmd_name=sif_cmd_name,
                                           sif_pattern=sif_pattern,
                                           Eye=Eye,
                                           sif_options=sif_options,
                                           eye_version=1)

        return sif

    @func_details
    def _check_sif_serdeseye(self, current_sif):
        """ Check SIF SerdesEye

        :param current_sif:
        '(0, 'e', 'C0', '(Max)')' = 'Eye(Channel='C0', Amin='292.5', AminP='358.8', AminN='354.9', Ap='98.3', An='9', EScan='8', LScan='17', EL='89.15%', SyncCnt='(Max)', ErrCnt='', Result='Pass')',   # nopep8
        '(0, 'e', 'C3', '(Max)')' = 'Eye(Channel='C3', Amin='308.1', AminP='347.1', AminN='351.0', Ap='117.8', An='8', EScan='8', LScan='16', EL='92.59%', SyncCnt='(Max)', ErrCnt='', Result='Pass')',  # nopep8
        '(0, 'e', 'C1', '(Max)')' = 'Eye(Channel='C1', Amin='300.3', AminP='347.1', AminN='347.1', Ap='121.7', An='7', EScan='8', LScan='15', EL='92.59%', SyncCnt='(Max)', ErrCnt='', Result='Pass')',  # nopep8
        '(0, 'e', 'C3', '10')'    = 'Eye(Channel='C3', Amin='296.4', AminP='327.6', AminN='327.6', Ap='110.0', An='7', EScan='8', LScan='15', EL='90.56%', SyncCnt='10', ErrCnt='0', Result='Pass')',    # nopep8
        '(0, 'e', 'E3', '10')'    = 'Eye(Channel='E3', Amin='292.5', AminP='327.6', AminN='327.6', Ap='117.8', An='6', EScan='8', LScan='14', EL='89.38%', SyncCnt='10', ErrCnt='0', Result='Pass')',    # nopep8
        '(0, 'e', 'C0', '10')'    = 'Eye(Channel='C0', Amin='284.7', AminP='327.6', AminN='327.6', Ap='90.5', An='9', EScan='8', LScan='17', EL='87.21%', SyncCnt='10', ErrCnt='0', Result='Pass')',     # nopep8
        '(0, 'e', 'E3', '(Min)')' = 'Eye(Channel='E3', Amin='288.6', AminP='319.8', AminN='315.9', Ap='117.8', An='6', EScan='8', LScan='14', EL='85.05%', SyncCnt='(Min)', ErrCnt='', Result='Pass')',  # nopep8
        '(0, 'e', 'A2', '(Min)')' = 'Eye(Channel='A2', Amin='292.5', AminP='327.6', AminN='327.6', Ap='82.7', An='8', EScan='8', LScan='16', EL='82.41%', SyncCnt='(Min)', ErrCnt='', Result='Pass')',   # nopep8
        :return:
        """
        ret = True if current_sif else False
        for k, v in current_sif.items():
            if v.Result.upper() == 'PASS':
                pass
            elif v.Result.upper() == 'IGNORE':
                ignored_channel = "SIF SerDesEye IGNORED: {0:<24} = {1}".format(k, v)
                log.warning(ignored_channel)
            else:
                failed_channel = "SIF SerDesEye FAILED: {0:<24} = {1}".format(k, v)
                log.error(failed_channel)
                ret = False
        if ret:
            log.info('SIF SerDesEye results are good.')
        else:
            log.error('SIF SerDesEye results indicate failure(s).')
        return ret

    @func_details
    def _generate_nif_serdeseye(self, nif_cmd, nif_pattern, Eye):
        """ Generate NIF SerdesEye
        :param (str) nif_cmd_name:
        :param (str) nif_pattern:
        :param (named tuple) eye:
        :return:
        """
        verbose = True if self._ud.verbose_level > 1 else False
        log.info('NIF Serdes Eye GENERATE (generic)')

        # Output
        nif = {}

        # Run command
        self._clear_recbuf(force=True)
        log.debug("prompt={0}".format(self._uut_prompt))
        self._uut_conn.send(nif_cmd, expectphrase='.*', timeout=60, regex=True)
        time.sleep(1.0)
        log.debug("Waiting for NIF completion...")
        self._uut_conn.waitfor(self._uut_prompt, timeout=500, regex=True)
        time.sleep(5.0)

        # Parse output
        p = re.compile(nif_pattern)
        m = p.findall(self._uut_conn.recbuf)
        for i in m:
            tag = 'Sum' if not re.match('([(]?Max[)])|([(]?Min[)])', i[-4]) else i[-4][1:4]
            nif[i[0], tag] = Eye._make(i)

        common_utils.print_large_dict(nif, title='nif') if verbose else None

        if not nif:
            log.error('FAILED. Failed to retrieve NIF result.')
            m = re.search('\*\*\*ERR: .*?[\n\r]', self._uut_conn.recbuf)
            log.debug(m.group(0)) if m else None
            return None
        return nif

    @func_details
    def _get_nif_serdeseye(self, uplink_test_card=None, eye_option='', **kwargs):
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

        log.info('NIF Serdes Eye START (generic)')

        common_utils.uut_comment(self._uut_conn, 'NIF', 'SerDes Eye Metric ASIC')

        # Input
        if uplink_test_card:
            if not eye_option:
                eye_option = '-o:5 -z'
            else:
                olist = eye_option.split(' ')
                eye_option = ' '.join([i for i in olist if '-o:' not in i])
                eye_option = ' '.join([eye_option, '-o:5 -z'])

        # Get NifSerdesEye
        Eye = namedtuple('Eye', 'RxTx Amin AminP AminN Ap An EScan LScan EL PRBS PS PE Result')
        nif_cmd = 'DopNifSerdesEyeMeasure {0} -i:3\r'.format(eye_option)
        # Regex for Summary, Min, Max
        nif_pattern = '(?m)([\d]+-*[\d]*)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+' \
                      '([\d.]+)[ \t]+([\d]+)[ \t]+([\d]+)[ \t]+([\d\S]+)[ \t]+([\S]+)[ \t]*([\d]*)[ \t]*([\d]*)' \
                      '[ \t]*([\S]+)[\r\n]*'

        nif = self._generate_nif_serdeseye(nif_cmd, nif_pattern, Eye)

        return nif

    @func_details
    def _check_nif_serdeseye(self, current_nif):
        """ Check Nif SerdesEye
        :param current_nif:

        Current Nif Data sample:
        #Gen2
        {'17-20': Eye(Amin='187.5', AminP='187.5', AminN='200.0', Ap='225.0', An='235.0', EScan='9', LScan='11', EL='20', REBS='7+', PS='10', PE='0', Result='Pass'),   # nopep8
         '25-28': Eye(Amin='157.5', AminP='157.5', AminN='175.0', Ap='202.5', An='222.5', EScan='10', LScan='13', EL='23', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '33-36': Eye(Amin='205.0', AminP='205.0', AminN='207.5', Ap='237.5', An='237.5', EScan='11', LScan='12', EL='23', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '1-4': Eye(Amin='170.0', AminP='170.0', AminN='195.0', Ap='212.5', An='235.0', EScan='10', LScan='11', EL='22', REBS='7+', PS='10', PE='0', Result='Pass'),    # nopep8
         '29-32': Eye(Amin='177.5', AminP='210.0', AminN='177.5', Ap='247.5', An='212.5', EScan='11', LScan='11', EL='22', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '5-8': Eye(Amin='177.5', AminP='180.0', AminN='177.5', Ap='220.0', An='217.5', EScan='10', LScan='10', EL='20', REBS='7+', PS='10', PE='0', Result='Pass'),    # nopep8
         '13-16': Eye(Amin='177.5', AminP='177.5', AminN='210.0', Ap='212.5', An='240.0', EScan='10', LScan='11', EL='21', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '37-40': Eye(Amin='177.5', AminP='187.5', AminN='177.5', Ap='222.5', An='220.0', EScan='11', LScan='12', EL='23', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '41-44': Eye(Amin='167.5', AminP='175.0', AminN='167.5', Ap='217.5', An='207.5', EScan='11', LScan='12', EL='23', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '45-48': Eye(Amin='197.5', AminP='197.5', AminN='200.0', Ap='230.0', An='232.5', EScan='12', LScan='13', EL='25', REBS='7+', PS='10', PE='0', Result='Pass'),  # nopep8
         '9-12': Eye(Amin='182.5', AminP='187.5', AminN='182.5', Ap='227.5', An='220.0', EScan='12', LScan='12', EL='24', REBS='7+', PS='10', PE='0', Result='Pass'),   # nopep8
         '21-24': Eye(Amin='162.5', AminP='162.5', AminN='187.5', Ap='210.0', An='232.5', EScan='11', LScan='13', EL='24', REBS='7+', PS='10', PE='0', Result='Pass')   # nopep8
         }

         # Gen3
        {'25': Eye(Tx='n/a', StepmV='10.01', TopmV='75.09', BotmV='-75.09', HeightmV='150.19', LeftUI='-0.212', RightUI='0.316', WidthUI='0.528', PRBS='31', PS='10', PE='0', Result='Pass'),  # nopep8
        '26': Eye(Tx='n/a', StepmV='8.94', TopmV='58.13', BotmV='-58.13', HeightmV='116.27', LeftUI='-0.231', RightUI='0.298', WidthUI='0.530', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '27': Eye(Tx='n/a', StepmV='9.17', TopmV='67.85', BotmV='-67.85', HeightmV='135.69', LeftUI='-0.211', RightUI='0.414', WidthUI='0.625', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '17': Eye(Tx='n/a', StepmV='9.38', TopmV='79.69', BotmV='-79.69', HeightmV='159.38', LeftUI='-0.242', RightUI='0.361', WidthUI='0.603', PRBS='7', PS='10', PE='0', Result='Pass'),     # nopep8
        '32': Eye(Tx='n/a', StepmV='9.38', TopmV='60.94', BotmV='-60.00', HeightmV='120.94', LeftUI='-0.195', RightUI='0.389', WidthUI='0.584', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '31': Eye(Tx='n/a', StepmV='10.09', TopmV='75.66', BotmV='-75.66', HeightmV='151.31', LeftUI='-0.256', RightUI='0.334', WidthUI='0.591', PRBS='31', PS='10', PE='0', Result='Pass'),   # nopep8
        '30': Eye(Tx='n/a', StepmV='9.28', TopmV='69.61', BotmV='-69.61', HeightmV='139.22', LeftUI='-0.289', RightUI='0.320', WidthUI='0.609', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '28': Eye(Tx='n/a', StepmV='9.43', TopmV='58.49', BotmV='-62.24', HeightmV='120.73', LeftUI='-0.223', RightUI='0.414', WidthUI='0.637', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '29': Eye(Tx='n/a', StepmV='9.24', TopmV='60.08', BotmV='-68.39', HeightmV='128.47', LeftUI='-0.256', RightUI='0.389', WidthUI='0.645', PRBS='31', PS='10', PE='0', Result='Pass'),    # nopep8
        '1': Eye(Tx='n/a', StepmV='9.68', TopmV='89.98', BotmV='-82.24', HeightmV='172.22', LeftUI='-0.258', RightUI='0.367', WidthUI='0.625', PRBS='7', PS='10', PE='0', Result='Pass'),      # nopep8
        '9': Eye(Tx='n/a', StepmV='8.66', TopmV='73.63', BotmV='-71.08', HeightmV='144.71', LeftUI='-0.217', RightUI='0.398', WidthUI='0.616', PRBS='7', PS='10', PE='0', Result='Pass')       # nopep8
        }
        :return:
        """
        ret = True if current_nif else False
        for k, v in current_nif.items():
            if v.Result.upper() != 'PASS':
                failed_channel = "NIF SerDesEye FAILED: {0:<24} = {1}".format(k, v)
                log.error(failed_channel)
                ret = False
        if ret:
            log.info('NIF SerDesEye results are good.')
        else:
            log.error('NIF SerDesEye results indicate failure(s).')
        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------------------------------------------------------
    @apollo_step
    def dopsetvolt(self, **kwargs):
        """ Set Doppler Voltage
        This is a one shot function.
    
        Example:
        Shannon48U_CR> DopSetVoltage
        Set Doppler voltage rail using ECID bin value.
    
        Asic[0] voltage setting completed. Please power cycle system.
    
        :param kwargs:
        :return:
        """    
        # Check mode
        mode = self._mode_mgr.current_mode
        if mode != 'STARDUST':
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(mode))
            return aplib.FAIL, 'Wrong mode.'
    
        self._uut_conn.send('DopSetVoltage\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(1)
        if 'complete' in self._uut_conn.recbuf:
            log.debug("Set voltage complete. Must power cycle.")
            self._power.cycle_on(**kwargs)
            if not self._mode_mgr.goto_mode('STARDUST'):
                errmsg = "Could not return to STARDUST after Doppler set voltage."
                log.error(errmsg)
                return aplib.FAIL, errmsg
    
        log.info('STEP: Doppler Set Voltage: PASSED.')
        return aplib.PASS


class StardustC3000(_Stardust3):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(StardustC3000, self).__init__(mode_mgr, ud, **kwargs)
        return


class StardustC9300(_Stardust3):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(StardustC9300, self).__init__(mode_mgr, ud, **kwargs)
        return

    @apollo_step
    def dopsetvoltage(self, **kwargs):
        return aplib.PASS

    @func_details
    def _get_nif_serdeseye(self, uplink_test_card=None, eye_option='', **kwargs):
        """ Get NIF SerdesEye
        :param uplink_test_card: 'Hilbert', 'Makron', etc. or None
        :param eye_option:

        Sample Nif serdes Eye data:

        Shannon24P> nifserdeseyemeasure -o:5 -z -i:10

        Phy Serdes Tx -> Doppler Nif Serdes Rx for downlink
        Doppler Nif Serdes Tx -> Nif Serdes Rx with ext LB for Hilbert ports
        Note(s):
        . For uplink 1G ports, no eye measurement, checking only PRBS sync/error.
        . It takes 2 seconds to run one lane per iteration.
        Skip 40G or 10/100M speed or Fourier 1G ports.


        RxPort TxPort mV/step Top(mV) Bot(mV) Height(mV) Left(UI) Right(UI) Width(UI) PRBS PS  PE  P/F
        ------ ------ ------- ------- ------- ---------- -------- --------- --------- ---- --- --- ----
        1       n/a      9.68   89.98  -82.24     172.22   -0.258     0.367     0.625    7  10   0 Pass
        1       n/a      9.56   81.28  -82.88     162.56   -0.258     0.367     0.625 (Min)        Pass
        1       n/a      9.75   92.62  -81.28     175.50   -0.258     0.367     0.625 (Max)        Pass
        9       n/a      8.66   73.63  -71.08     144.71   -0.217     0.398     0.616    7  10   0 Pass
        9       n/a      8.44   71.72  -82.88     135.00   -0.227     0.398     0.609 (Min)        Pass
        9       n/a      9.75   82.88  -63.28     165.75   -0.211     0.398     0.625 (Max)        Pass
        17      n/a      9.38   79.69  -79.69     159.38   -0.242     0.361     0.603    7  10   0 Pass
        17      n/a      9.38   79.69  -79.69     159.38   -0.242     0.352     0.594 (Min)        Pass
        17      n/a      9.38   79.69  -79.69     159.38   -0.242     0.367     0.609 (Max)        Pass
        25      n/a     10.01   75.09  -75.09     150.19   -0.212     0.316     0.528   31  10   0 Pass
        25      n/a      9.94   74.53  -75.94     149.06   -0.227     0.305     0.500 (Min)        Pass
        25      n/a     10.12   75.94  -74.53     151.88   -0.195     0.320     0.547 (Max)        Pass
        26      n/a      8.94   58.13  -58.13     116.27   -0.231     0.298     0.530   31  10   0 Pass
        26      n/a      8.81   57.28  -58.50     114.56   -0.242     0.289     0.516 (Min)        Pass
        26      n/a      9.00   58.50  -57.28     117.00   -0.227     0.305     0.547 (Max)        Pass
        27      n/a      9.17   67.85  -67.85     135.69   -0.211     0.414     0.625   31  10   0 Pass
        27      n/a      9.00   59.72  -68.91     128.62   -0.211     0.398     0.609 (Min)        Pass
        27      n/a      9.19   68.91  -59.72     137.81   -0.211     0.430     0.641 (Max)        Pass
        28      n/a      9.43   58.49  -62.24     120.73   -0.223     0.414     0.637   31  10   0 Pass
        28      n/a      9.38   51.56  -70.31     112.50   -0.227     0.414     0.625 (Min)        Pass
        28      n/a      9.56   62.16  -60.94     131.25   -0.211     0.414     0.641 (Max)        Pass
        29      n/a      9.24   60.08  -68.39     128.47   -0.256     0.389     0.645   31  10   0 Pass
        29      n/a      9.19   59.72  -70.31     121.88   -0.258     0.383     0.641 (Min)        Pass
        29      n/a      9.38   60.94  -60.94     131.25   -0.242     0.398     0.656 (Max)        Pass
        30      n/a      9.28   69.61  -69.61     139.22   -0.289     0.320     0.609   31  10   0 Pass
        30      n/a      9.19   68.91  -70.31     137.81   -0.289     0.320     0.609 (Min)        Pass
        30      n/a      9.38   70.31  -68.91     140.62   -0.289     0.320     0.609 (Max)        Pass
        31      n/a     10.09   75.66  -75.66     151.31   -0.256     0.334     0.591   31  10   0 Pass
        31      n/a      9.94   74.53  -75.94     149.06   -0.258     0.320     0.578 (Min)        Pass
        31      n/a     10.12   75.94  -74.53     151.88   -0.242     0.336     0.594 (Max)        Pass
        32      n/a      9.38   60.94  -60.00     120.94   -0.195     0.389     0.584   31  10   0 Pass
        32      n/a      9.38   60.94  -60.94     112.50   -0.211     0.383     0.578 (Min)        Pass
        32      n/a      9.38   60.94  -51.56     121.88   -0.180     0.398     0.594 (Max)        Pass

        :return:
        """
        log.info('NIF Serdes Eye START (Gen3)')

        common_utils.uut_comment(self._uut_conn, 'NIF', 'SerDes Eye Metric ASIC')

        if uplink_test_card:
            if not eye_option:
                eye_option = '-o:5 -z'

        # Get NifSerdesEye
        Eye = namedtuple('Eye', 'Rx Tx StepmV TopmV BotmV HeightmV LeftUI RightUI WidthUI PRBS PS PE Result')
        nif_cmd = 'NifSerdesEyeMeasure {0}\r'.format(eye_option)
        nif_pattern = '(?m)([\d]+)[ \t]+([^.1-9 ]*)[ \t]*([\S]+)[ \t]+([\d\S]+)[ \t]+([\S]+)[ \t]+([\S]+)' \
                      '[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\d]*)[ \t]*([\d]*)' \
                      '[ \t]*([\S]+)[\r\n]+'

        nif = self._generate_nif_serdeseye(nif_cmd, nif_pattern, Eye)

        return nif

    @func_details
    def _get_sif_serdeseye(self, asic_core_count, sif_options='', **kwargs):
        """ Get SIF SerdesEye
        :param asic_core_count:
        :param sif_options:

        sample SIF serdes eye data:

        Shannon24U> SifSerdesEye 0 e -i:10

        Using PRBS pattern 31+:
        NOTE: can take up to 2 secs for one channel per iteration.
        ====  PRBS test: Doppler #0 East side rx, #0 West side tx,  ====
              Eye measurement of Doppler #0 East side rx:

        Criteria: height = 30.0, UI = 0.154

        RxChan Core   mV/step Top(mV) Bot(mV) Height(mV) Left(UI) Right(UI) Width(UI) PRBS PS  PE  P/F
        ------ ------ ------- ------- ------- ---------- -------- --------- --------- ---- --- --- ----
        0      0        10.03   65.20  -65.20     130.41   -0.209     0.367     0.577   31  10   0 Pass
        0      0         9.94   64.59  -65.81     129.19   -0.211     0.367     0.562 (Min)        Pass
        0      0        10.12   65.81  -64.59     131.62   -0.195     0.367     0.578 (Max)        Pass
        1      0        12.17   91.27  -87.61     178.88   -0.225     0.336     0.561   31  10   0 Pass
        1      0        12.00   90.00  -91.41     170.62   -0.227     0.336     0.547 (Min)        Pass
        1      0        12.19   91.41  -79.22     182.81   -0.211     0.336     0.562 (Max)        Pass
        2      0        11.21   84.09  -72.88     156.97   -0.242     0.375     0.617   31  10   0 Pass
        2      0        11.06   82.97  -73.12     154.88   -0.258     0.367     0.594 (Min)        Pass
        2      0        11.25   84.38  -71.91     157.50   -0.227     0.383     0.625 (Max)        Pass
        3      0        10.80   79.93  -59.40     139.33   -0.212     0.398     0.611   31  10   0 Pass
        3      0        10.69   69.47  -59.81     128.25   -0.227     0.398     0.609 (Min)        Pass
        3      0        10.88   81.56  -58.78     141.38   -0.211     0.398     0.625 (Max)        Pass
        8      0        10.76   69.96  -69.96     139.91   -0.242     0.323     0.566   31  10   0 Pass
        8      0        10.69   69.47  -70.69     138.94   -0.242     0.320     0.562 (Min)        Pass
        8      0        10.88   70.69  -69.47     141.38   -0.242     0.336     0.578 (Max)        Pass
        9      0         9.96   64.72  -64.72     129.43   -0.258     0.291     0.548   31  10   0 Pass
        9      0         9.94   64.59  -65.81     129.19   -0.258     0.289     0.547 (Min)        Pass
        9      0        10.12   65.81  -64.59     131.62   -0.258     0.305     0.562 (Max)        Pass
        10     0         9.39   61.06  -61.06     122.12   -0.173     0.394     0.567   31  10   0 Pass
        10     0         9.38   60.94  -62.16     121.88   -0.180     0.383     0.547 (Min)        Pass
        10     0         9.56   62.16  -60.94     124.31   -0.164     0.398     0.578 (Max)        Pass
        11     0         9.24   62.84  -59.17     122.01   -0.239     0.334     0.573   31  10   0 Pass
        11     0         9.19   59.72  -60.94     119.44   -0.242     0.320     0.562 (Min)        Pass
        11     0         9.38   68.91  -50.53     128.62   -0.227     0.336     0.578 (Max)        Pass
        16     0         9.54   62.03  -60.12     122.16   -0.227     0.434     0.661   31  10   0 Pass
        16     0         9.38   60.94  -62.16     114.75   -0.227     0.430     0.656 (Min)        Pass
        16     0         9.56   62.16  -52.59     124.31   -0.227     0.445     0.672 (Max)        Pass
        17     0        11.34   70.36  -62.39     132.75   -0.225     0.430     0.655   31  10   0 Pass
        17     0        11.25   61.88  -62.91     123.75   -0.227     0.430     0.641 (Min)        Pass
        17     0        11.44   74.34  -61.88     137.25   -0.211     0.430     0.656 (Max)        Pass
        18     0         9.69   63.01  -55.27     118.28   -0.217     0.395     0.613   31  10   0 Pass
        18     0         9.56   62.16  -63.38     114.75   -0.227     0.383     0.594 (Min)        Pass
        18     0         9.75   63.38  -52.59     126.75   -0.211     0.398     0.625 (Max)        Pass
        19     0        10.91   70.93  -70.93     141.86   -0.205     0.366     0.570   31  10   0 Pass
        19     0        10.69   69.47  -71.91     138.94   -0.211     0.352     0.547 (Min)        Pass
        19     0        11.06   71.91  -69.47     143.81   -0.195     0.367     0.578 (Max)        Pass

        USAGE: SifSerdesEye <asicRx> <sideRx> [<PRBSpattern>] [-t:<PRBSTestTime>]
                    [-i:<iteration>] [-z] [-d]
            <asicRx> -- Doppler asic # to rx and get eye measurement
            <sideRx> -- east or west
            <PRBSpattern> -- choose a PRBS pattern or don't run PRBS:
             NOTE: PRBS test only works with stack links tx/rx within one board.
                0: PRBS7+
                1: PRBS7-
                2: PRBS23+
                3: PRBS23-
                4: PRBS31+ (default)
                5: PRBS31-
                6: 10101010...
                7: Repeating pattern of 64 1's and 64 0's
                8: don't run PRBS, do eye measurement only
            -t:<PRBSTestTime> -- time in msec for PRBS to run prior to checking
                 sync and error. Default 10msec.
            -i:<iteration> -- number of iterations (default 1)
            -z -- zero Az (default non-zero)
            -d -- print detail if amin >= ap in each iteration

        :return:
        """
        log.info('SIF Serdes Eye START (Gen3)')

        sif_cmd_name = 'SifSerdesEye'
        Eye = namedtuple('Eye', 'Channel core StepmV TopmV BotmV HeightmV LeftUI RightUI WidthUI PRBS PS PE Result')
        # Regex for all entries: summary, min, and max
        sif_pattern = '(?m)([\d]+)[ \t]+([^.1-9 ]*)[ \t]*([\S]+)[ \t]+([\d\S]+)[ \t]+([\S]+)[ \t]+([\S]+)' \
                      '[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\S]+)[ \t]+([\d]*)[ \t]*([\d]*)' \
                      '[ \t]*([\S]+)[\r\n]+'

        sif = self._generate_sif_serdeseye(asic_core_count,
                                           sif_cmd_name=sif_cmd_name,
                                           sif_pattern=sif_pattern,
                                           Eye=Eye,
                                           sif_options=sif_options,
                                           eye_version=2)

        return sif


class StardustC9300L(StardustC9300):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(StardustC9300L, self).__init__(mode_mgr, ud, **kwargs)
        return

    # ------------------------------------------------------------------------------------------------------------------
    # MCU
    # ------------------------------------------------------------------------------------------------------------------
    @apollo_step
    def set_mcu_id(self, mac_addr=None, mcu_instance=None, stack_num=None, poepresent=None, sku=None, timeout=200):
        """ Set MCU ID
        Afterwit48QU> alchemyp -eeprom
        Programming Alchemy 0 (Sub Addr 0) Alchemy Config registers.
        Wait for 5 seconds after writing Alchemy Config registers..
        Sending RE_SYS_RESET command to Alchemy-0, wait for 16 seconds...
        Sending RE_SYS_RESET command to Alchemy-1, wait for 16 seconds...
        Sending RE_SYS_RESET command to Alchemy-2, wait for 16 seconds...
        PASSED

        :param mac_addr:
        :param mcu_instance:
        :param stack_num:
        :param poepresent:
        :param sku:
        :param timeout:
        :return:
        """
        # Do the signing
        log.debug("Performing MCU id signing...")
        self._uut_conn.send('AlchemyProgram -eeprom\r', expectphrase=self._uut_prompt, timeout=timeout, regex=True)
        time.sleep(self.RECBUF_TIME)

        if 'PASSED' in self._uut_conn.recbuf:
            log.debug("MCU ID programming PASSED.")
            return aplib.PASS
        elif 'Command not found' in self._uut_conn.recbuf:
            log.warning("Command not supported! Please check diags capability!")
            log.warning("This result will be ignored.")
            return aplib.UNKNOWN
        else:
            log.error("MCU ID programming FAILED.")
            log.error(self._uut_conn.recbuf)
            return aplib.FAIL

    @apollo_step
    def switch_mcu_mode(self, **kwargs):
        log.debug("Note: C9300L platforms do not support MCU mode switch.")
        return aplib.PASS

    # -----------
    @func_details
    def _upgrade_mcu(self, name, image_pkg, timeout=400, home_dir=None, **kwargs):
        """ Upgrade MCU

        EXAMPLE#1:
        ----------
        Afterwit48QU> AlmanacMcuUpgradeApplication app_062618.bin
        Programming with app_062618.bin
        Initial ping attempt failed, attempting to force bootloader
        Almanac forced to run Bootloader
        Resetting MCU to force back to bootloader
        Bootloader Ping Command passed
        Send Download command:
        Write data: ....................................................................
        Reset MCU

        Almanac MCU application image upgrade successful.

        Afterwit48QU> AlmanacMcuUpgradeBL bl_062618.bin
        Programming with bl_062618.bin
        Send RE_IMAGE_START_DOWNLOAD command
        Send RE_IMAGE_SEND_DATA command and data .................................................
        Reset MCU

        Almanac MCU bootloader image upgrade successful.

        Afterwit48QU> alchemy version
        A#    (SA)    SW Version          HW Version    Bootloader Version
         0    ( 0)    APPL 0.101 (0x65)    0   (0x00)    101 (0x65)
         1    ( 7)    APPL 0.101 (0x65)    0   (0x00)    101 (0x65)
         2    (14)    APPL 0.101 (0x65)    0   (0x00)    101 (0x65)


        EXAMPLE#2:
        ----------
        Afterwit24XU> AlmanacMcuUpgradeApplication app_062618.bin							// Step 1
        Afterwit24XU> AlmanacMcuUpgradeBL bl_062618.bin										// Step 2

        Afterwit24XU> rw alchemy/0 AlchemyConfig0 0xc1										// Step 3

        Alchemy.Alchemy/0 (base @ 0x00000000.00000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000050                                   c1  AlchemyConfig0

        Afterwit24XU> rw bi rst_1 0x0001										            // Step 4

        FPGA.Bifocal/0 (base @ 0x00000000.88000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000008                             00000001  rst_1

        Afterwit24XU> rw bi rst_1 0x0000										            // Step 5

        FPGA.Bifocal/0 (base @ 0x00000000.88000000):
        Offset                                  Value  RegisterName
        --------  -----------------------------------  --------------------------------
        00000008                             00000000  rst_1

        :param name:
        :param image_pkg:
        :param timeout:
        :param home_dir:
        :param kwargs:
        :return:
        """
        log.debug("MCU name: {0}".format(name))
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Set known Diags home dir, Get MCU Sub-dir,
        home_dir = self.get_cwd() if not home_dir else home_dir
        mcu_subdir = home_dir
        mcu_files = image_pkg

        if not self._mode_mgr:
            log.error("MCU Upgrade not possible.  Must have methods for mode operation.")
            return False

        # Check that the image package files are available
        device_files = self.get_device_files(file_filter='[a-zA-Z].*?', attrib_flags='-')
        log.debug(device_files)
        if not all([True if file in device_files else False for file in mcu_files]):
            log.warning("Required MCU files not in expected flash location.")
            log.debug("Attempting image load...")

            server_ip = self._ud.uut_config.get('server_ip', None)
            netmask = self._ud.uut_config.get('netmask', None)
            uut_ip = self._ud.uut_config.get('uut_ip', None)
            if all([server_ip, uut_ip, netmask]):
                self._mode_mgr.goto_mode('LINUX')
                result = self._linux.transfer_tftp_files(src_files=mcu_files, dst_files=None,
                                                         direction='get',
                                                         server_ip=server_ip, ip=uut_ip, netmask=netmask, force=True)
                self._mode_mgr.goto_mode('STARDUST')
            else:
                log.error("Image load not possible; network params are absent.")
                result = False
            if not result:
                log.debug("MCU Image load: FAILED.")
                return result
            else:
                log.debug("MCU Image load: PASSED.")

        log.debug("MCU files = {0}".format(mcu_files))
        device_files = self.get_device_files(sub_dir=mcu_subdir, file_filter='[a-zA-Z].*?', attrib_flags='-')
        if not all([True if file in device_files else False for file in mcu_files]):
            log.error("MCU files do NOT match the files loaded to flash.")
            log.error("Check the product_definition and the flash contents.")
            return False

        log.debug("Getting mcu images...")
        app_bin = next((s for s in mcu_files if 'app_' in s), None)
        bl_bin = next((s for s in mcu_files if 'bl_' in s), None)
        mcu_command_list = [i for i in [(app_bin, 'AlmanacMcuUpgradeApplication'), (bl_bin, 'AlmanacMcuUpgradeBL')] if i[0]]

        if not self._mode_mgr.goto_mode('STARDUST'):
            log.error("Not in correct mode; cannot continue")
            return False

        for mcu_image, mcu_cmd in mcu_command_list:
            log.info("Performing MCU {0} {1}...".format(mcu_cmd, mcu_image))
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=120, regex=True)
            self._uut_conn.send('{0} {1}\r'.format(mcu_cmd, mcu_image), expectphrase=self._uut_prompt, timeout=300, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'image upgrade successful' in self._uut_conn.recbuf:
                log.info("MCU upgrade: PASSED!")
                ret = True
            else:
                log.error("MCU upgrade: FAILED.")
                log.error(self._uut_conn.recbuf)
                ret = False

        return ret

    @func_details
    def _get_mcu_mode(self):
        log.debug("Note: C9300L platforms do not support MCU modes.")
        return 'not_applicable'
