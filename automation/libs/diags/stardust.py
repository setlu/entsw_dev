"""
Stardust
"""

# Python
# ------
import sys
import re
import logging
import time
import parse
import os
import random
from collections import namedtuple
from collections import OrderedDict

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils import common_utils
from apollo.scripts.entsw.libs.equip_drivers.poe_loadbox import handle_no_poe_equip


__title__ = "Stardust Generic Diagnostics Module"
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

func_details = common_utils.func_details
func_retry = common_utils.func_retry
apollo_step = common_utils.apollo_step


class Stardust(object):
    RECBUF_TIME = 5.0
    RECBUF_CLEAR_TIME = 2.0
    USE_CLEAR_RECBUF = False

    FPGA_NAMES = ['bell', 'morse', 'morseg', 'proximo', 'pseudaria', 'hypatia', 'strutt', 'bifocal']
    OSC_ACCURACY = 1.44  # 0.72
    ASIC_ECID_LOG_PATH = '/tftpboot/logs/ecid/'

    def __init__(self, mode_mgr, ud, **kwargs):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt = self._mode_mgr.uut_prompt_map['STARDUST']
        self._linux = kwargs.get('linux', None)
        self._equip = kwargs.get('equip', None)
        self._power = kwargs.get('power', None)
        self.__check_dependencies()
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def sysinit(self, **kwargs):
        """ SysInit
        :param kwargs:
        :return:
        """
        @func_retry
        def __sysinit(level='', pass_pattern_compsite_list=list((None, None)), ignore_pattern_list=list(), timeout=360):
            """ Sysinit
            Perform sysinit at a specific level (if given).
            Check the output for any errors or fails and (if specified) check for a passing pattern.
            Check for presence of unprogrammed peripherals (cables and/or adapters).

            Examples:
            G24> sysinit
            PCIe: Port 1 link active, 4 lanes, speed gen1
            Doppler 0 PCIe link lane width is 4.
            Doppler 1 PCIe link lane width is 4.
            Doppler 2 PCIe link lane width is 4.
            Doppler 3 PCIe link lane width is 4.
            Cable BID 0xffff detected on stack connector 1
            Cable BID 0xffff detected on stack connector 2

            Vore24P_10G> sysinit
            ***ERR: RxI2cQuackMessage failed at idx 0.
            ***ERR: cannot rx data from Quack for cmd type 0x23.
            ***ERR: ProcessQuackFruEepromAccess failed at QuackReadEeprom.
            WARNING: StackCableCtrl() failed in reading Quack BID for stack 1. Assign default bid: 0x8001.
            Cable BID 0x8001 detected on stack connector 1
            ***ERR: RxI2cQuackMessage failed at idx 0.
            ***ERR: cannot rx data from Quack for cmd type 0x23.
            ***ERR: ProcessQuackFruEepromAccess failed at QuackReadEeprom.
            WARNING: StackCableCtrl() failed in reading Quack BID for stack 2. Assign default bid: 0x8001.
            Cable BID 0x8001 detected on stack connector 2

            Note:
            Other "error" messages can exist in the form "*** Err:" and are secondary errors that do NOT fail sysinit.
            Example:  ***Err: DopDGetSifSerdesPDSISettings - unsupported cable ID

            :param (str) level: System initialization level per diags
            :param (tuple) pass_pattern_compsite_list: Required list of patterns for passing
                                                       [(<regex pattern>, <count of pattern to find>), ...]
                                                  ex.  [('Doppler [0-7] PCIe link lane width is 4', 8)]
            :param (list) ignore_pattern_list: Optional list of error patterns to ignore.
            :param (int) timeout:
            :return (bool): True if successful
            """
            ret = False
            try:
                def __chk_fail_pattern():
                    log.debug("Sysinit collecting valid fail patterns...")
                    result = True
                    p = re.compile('(ERR.*)')
                    m = p.findall(self._uut_conn.recbuf)
                    if m:
                        # Cycle thru any and all ignore patterns and remove the matching messages from any errors captured.
                        err_cnt = len(m)
                        for ignore_pattern in ignore_pattern_list:
                            for idx, err in reversed(list(enumerate(m, 0))):
                                if re.search(ignore_pattern, err):
                                    m.pop(idx)
                                    log.warning("ERR IGNORED = {0}".format(err))
                        # Check for any remaining non-matched patterns
                        if m:
                            result = False
                            for err in m:
                                log.error("{0}".format(err))
                        else:
                            log.warning("All errors ignored (Error count={0}).".format(err_cnt))
                    else:
                        log.debug("No Sysinit errors.")
                    return result

                def __chk_pass_pattern():
                    log.debug("Sysinit now checking for pass patterns...")
                    result = True
                    time.sleep(self.RECBUF_TIME)
                    for pass_pattern_composite in pass_pattern_compsite_list:
                        pass_pattern, pass_pattern_count = pass_pattern_composite if pass_pattern_composite and len(pass_pattern_composite) == 2 else (None, None)
                        if pass_pattern and pass_pattern_count:
                            p = re.compile(pass_pattern)
                            m2 = p.findall(self._uut_conn.recbuf)
                            if not m2 or len(m2) != pass_pattern_count:
                                result = False
                                log.error("Sysinit Output: \n{0}".format(self._uut_conn.recbuf))
                                log.error('Sysinit FAILED for expected output {0}'.format(pass_pattern_composite))
                                log.debug("Match count = {0}".format(len(m2) if m2 else 0))
                                log.debug("Match = {0}".format(m2))
                    return result

                def __chk_peripherals_presence():
                    self._ud.uut_config['idpro_peripherals_to_prog'] = list()  # Reset everytime.
                    if 'Cable BID 0xffff detected on stack connector 1' in self._uut_conn.recbuf:
                        self._ud.uut_config['idpro_peripherals_to_prog'].append('2')
                    if 'Cable BID 0xffff detected on stack connector 2' in self._uut_conn.recbuf:
                        self._ud.uut_config['idpro_peripherals_to_prog'].append('3')
                    if 'Adapter BID 0xffff detected on stack connector 1' in self._uut_conn.recbuf:
                        self._ud.uut_config['idpro_peripherals_to_prog'].append('4')
                    if 'Adapter BID 0xffff detected on stack connector 2' in self._uut_conn.recbuf:
                        self._ud.uut_config['idpro_peripherals_to_prog'].append('5')
                    return True

                # Perform the sysinit
                self._uut_conn.send('sysinit {0}\r'.format(level), expectphrase=self._uut_prompt, timeout=timeout, regex=True)
                time.sleep(self.RECBUF_TIME * 2)

                # Check for SYSINIT fail patterns
                if not __chk_fail_pattern():
                    raise apexceptions.ApolloException("SYSINIT Failure (fail patterns).")

                # Check for SYSINIT pass patterns
                if not __chk_pass_pattern():
                    raise apexceptions.ApolloException("SYSINIT Failure (pass patterns).")
                log.debug("Sysinit is good.")
                ret = True

                # Check for presence of unprogrammed peripherals (cables)
                __chk_peripherals_presence()

            except RuntimeError as e:
                log.error(e)
            except apexceptions.TimeoutException as e:
                log.error(e)

            return ret

        # Process input
        srtp_default = self._ud.uut_config.get('sysinit_required_to_pass', [(None, None)])
        sie_default = self._ud.uut_config.get('sysinit_ignore_errors', list())
        sysinit_required_to_pass = kwargs.get('sysinit_required_to_pass', srtp_default)
        sysinit_ignore_errors = kwargs.get('sysinit_ignore_errors', sie_default)
        timeout = kwargs.get('timeout', 360)

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL

        result = __sysinit(level='',
                           pass_pattern_compsite_list=sysinit_required_to_pass,
                           ignore_pattern_list=sysinit_ignore_errors,
                           timeout=timeout)

        return aplib.PASS if result else (aplib.FAIL, 'Sysinit could not complete.')

    @apollo_step
    def run_testlist_item(self, **kwargs):
        """ Run Testlist Item
        :param kwargs:
        :return:
        """
        max_attempts = kwargs.get('max_attempts', 3)

        @func_retry(max_attempts=max_attempts)
        def __run_testlist_item(test_name, params='', timeout=100):
            """ Run TestList Item from diags

            Example of vaild test command w/ PASS:
            --------------------------------------
            Diag> run PortIntrDiag
              PortIntrDiag (Ports Interrupt Diag Test): PCIe: Port 1 link active, 4 lanes, speed gen1
            Doppler 0 PCIe link lane width is 4.
            Cable BID 0x8001 detected on stack connector 1
            Cable BID 0x8001 detected on stack connector 2
            PASSED
                 Run-time: 61202 millisecs


            Example of wrong test command:
            ------------------------------
            Diag> run PortCable
            ***ERR: TEXEC: Invalid or ambiguous name
            USAGE: Run [<name>] [-n:<num_of_times>]
                <name> -- A string: name of the section or individual test.
                -n:<num_of_times> -- Number of times to run (default: 1) (range: 0 - 65535).

            :param test_name:
            :param params:
            :param timeout:
            :return:
            """
            if test_name == 'EXIT':
                return True
            self._clear_recbuf()
            self._uut_conn.send('run {0} {1}\r'.format(test_name, params), expectphrase=self._uut_prompt, timeout=timeout, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'PASSED' in self._uut_conn.recbuf:
                # TODO: Need mechanism to check certain failures even when a PASS!  Why? Diag bug? (4/23/2018)
                log.info("DIAG TEST: {0} = PASSED.".format(test_name))
                return True
            elif 'IGNORED' in self._uut_conn.recbuf:
                log.info("DIAG TEST: {0} = IGNORED/SKIPPED.".format(test_name))
                return True
            elif 'FAIL' in self._uut_conn.recbuf:
                log.error("DIAG TEST: {0} = FAILED.".format(test_name))
                return False
            elif '***ERR' in self._uut_conn.recbuf:
                if 'Invalid or ambiguous name' in self._uut_conn.recbuf:
                    log.error("The diag command was NOT recognized!")
                    log.error("Please check the product definition to ensure correct command set to be tested.")
                # TODO: Need mechanism to ignore certain failures. !!!!!!  (3/2/2018)
                log.error("DIAG TEST: {0} = ERROR.".format(test_name))
                return False
            else:
                log.warning("DIAG TEST: {0} result is UNKNOWN. Check for correct name & diags version.".format(test_name))
            return False

        diag_tests_list = self._ud.uut_config.get('diag_tests', None)
        if not diag_tests_list:
            log.warning("The 'diag_tests' data dict is unavailable; please check the product_definitions.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        if not isinstance(diag_tests_list, list) or len(diag_tests_list) == 0:
            log.error("The 'diag_tests' entry is NOT in the correct form or is empty.")
            return aplib.FAIL, "Bad form for 'diag_tests'."
        diag_tests = OrderedDict(diag_tests_list)

        # Process input
        verbose = kwargs.get('verbose', True if self._ud.verbose_level > 1 else False)
        menu = kwargs.get('menu', False)
        test_name = kwargs.get('test_name', None)
        timeout = kwargs.get('timeout', 200)
        args = kwargs.get('args', '')
        aplib.set_container_text('DIAG TEST {0}'.format(test_name))
        # Handle alternate names
        test_cmd = diag_tests.get(test_name, {}).get('cmd', test_name)
        # Print Info
        log.debug("category   = {0}".format(self._ud.category))
        log.debug("test_name  = {0}".format(test_name))
        log.debug("cmd        = {0}".format(test_cmd))
        log.debug("timeout    = {0}".format(timeout))
        log.debug("args       = {0}".format(args))

        # Check for modular
        if self._ud.category == 'MODULAR':
            if self._ud.modular_type == 'linecard':
                args = '-slot:{0} {1}'.format(self._ud.physical_slot, args) if self._ud.physical_slot else args
                log.debug("args (xfm) = {0}".format(args))
            elif self._ud.modular_type == 'supervisor':
                sup = str(self._ud.physical_slot) if self._ud.physical_slot else ''
                auxsup = str(self._ud.uut_config.get('supervisor', {}).get('physical_slot_auxsup', ''))
                if not sup or not auxsup:
                    log.error("The supervisor physical slots are NOT completely defined. Check _config.py file.")
                    return aplib.FAIL
                if args:
                    args = re.sub('auxsup', auxsup, args)
                    args = re.sub('sup', sup, args)
                    log.debug("args (xfm) = {0}".format(args))

        # Check Mode
        if self._mode_mgr.current_mode != 'DIAG':
            log.error("Wrong mode; need to be in DIAG.")
            return aplib.FAIL

        # Run from menu?
        if menu:
            enabled_diag_tests = [item for item in diag_tests.keys() if diag_tests[item].get('enabled', False)]
            enabled_diag_tests.append('EXIT')
            test_name = aplib.ask_question("Select a Diag Test:", answers=enabled_diag_tests)
            test_cmd = diag_tests.get(test_name, {}).get('cmd', test_name)

        # Check for test item
        if not test_cmd or test_name not in diag_tests:
            if test_name != 'EXIT':
                log.warning("The test_name ({0}) is not available.".format(test_name))
            else:
                log.debug("EXIT diag testlist.")
            return aplib.SKIPPED

        test_name_details = diag_tests[test_name]
        log.debug("DIAG TEST {0} : {1}".format(test_name, test_name_details)) if verbose else None
        if not test_name_details.get('enabled', False):
            log.info("The diag test is NOT enabled; no run will occur.")
            return aplib.SKIPPED

        result = __run_testlist_item(test_cmd, params=args, timeout=timeout)
        return aplib.PASS if result else (aplib.FAIL, "{0} : {1}".format(test_name, self._uut_conn.recbuf))

    @apollo_step
    def temperature_test(self, **kwargs):
        """ Diag Temperature Test
        :menu: (enable=True, name=TEMPERATURE, section=DiagTests, num=1, args=None)
        :return (str): aplib.PASS/FAIL
        """
        # Process Input
        temperature_table = kwargs.get('temperature_table', self._ud.uut_config.get('temperature_table', None))
        temperature_corner = kwargs.get('temperature_corner', 'AMBIENT')
        operational_state = kwargs.get('operational_state', 'idle')
        testarea = kwargs.get('testarea', aplib.apdicts.test_info.test_area)
        cpu_cmd = self._ud.uut_config.get('cpu', {}).get('cmd', None)

        # Pull Temperature Limit Data
        log.debug("Temperature Limit Data Params")
        log.debug("  Area  : {0}".format(testarea))
        log.debug("  Temp  : {0}".format(temperature_corner))
        log.debug("  UUT   : {0}".format(operational_state))

        aplib.set_container_text(
            'DIAG TEMPERATURE TEST for {0},{1},{2}'.format(testarea, temperature_corner, operational_state))

        # Check Mode
        mode = self._mode_mgr.current_mode
        if mode not in ['STARDUST', 'TRAF', 'DIAG']:
            errmsg = "Wrong mode for temperature test; need to be in one of STARDUST, TRAF, or DIAG."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Gather data
        sys_temps = self._get_system_temperature()
        sbc_temps = self._get_sbc_temperature()
        asic_temps = self._get_asic_temperature()
        cpu_temps = self._get_cpu_temperature(cpu_cmd) if cpu_cmd else None

        # Add to UUT status
        self._ud.uut_status['temperatures'] = {} if 'temperatures' not in self._ud.uut_status else self._ud.uut_status['temperatures']
        self._ud.uut_status['temperatures'].update({testarea: {temperature_corner: {operational_state: sys_temps}}})
        self._ud.uut_status['temperatures'].update({testarea: {temperature_corner: {operational_state: sbc_temps}}})
        self._ud.uut_status['temperatures'].update({testarea: {temperature_corner: {operational_state: asic_temps}}})
        self._ud.uut_status['temperatures'].update({testarea: {temperature_corner: {operational_state: cpu_temps}}}) if cpu_cmd else None
        self._ud.uut_status['active_temperature'] = temperature_corner
        common_utils.print_large_dict(self._ud.uut_status, exploded=False) # if self._ud.verbose_level > 2 else None

        # Check for chamber simulation
        # Note: Skip temperature check since readings will be wrong from a live UUT that simulates a chamber.
        chamber_conn_name, chamber_model = common_utils.get_chamber_conn()
        if chamber_model == 'simulator':
            log.warning("=" * 70)
            log.warning("The environment is being simulated via the connection name: {0}".format(chamber_conn_name))
            log.warning("Therefore, UUT temperature readings will not correspond to expected tables.")
            log.warning("All UUT temperature checks will be skipped.")
            log.warning("=" * 70)
            return aplib.SKIPPED

        # Check temp
        result = self._check_temperatures(temperatures=self._ud.uut_status['temperatures'],
                                          limit_table=temperature_table,
                                          area=testarea,
                                          temp_corner=temperature_corner,
                                          uut_state=operational_state)
        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def vmargin_test(self, **kwargs):
        """ Diag Voltage Margin Test
        :menu: (enable=True, name=VMARGIN,     section=DiagTests, num=1,   args={'margin_all': False})
        :menu: (enable=True, name=VMARGIN ALL, section=DiagTests, num=2, args={})
        :param (dict) kwargs:
                      device_instance (int): 0=motherboard, 1+ = peripherals
                      margin_level (str): 'NOMINAL', 'HIGH', or 'LOW'
                      margin_table (dict): Table describing voltage rails and their margin amounts for checking.
                                           Table is in product definition file.  If a table is not provided, all rails are
                                           margined at default levels based on SBC settings and no check can be done.
                      margin_all (bool): If True ignore table for margining specific rails. (Default is True)
                      check_only (bool): If True, only check the margin; do not perform margining.

        :return (str): aplib.PASS/FAIL
        """

        valid_margin_levels = ['NOMINAL', 'HIGH', 'LOW', 'DYNAMIC']

        # Process input
        device_instance = kwargs.get('device_instance', self._ud.device_instance)
        if device_instance is None:
            while device_instance is None or not str(device_instance).isdigit():
                device_instance = aplib.ask_question("Enter target device instance number:")
        device_instance = int(device_instance)

        margin_all = kwargs.get('margin_all', True)
        margin_level = kwargs.get('margin_level', None)
        if margin_level is None:
            margin_level = aplib.ask_question("Select Voltage Margin Level:", answers=valid_margin_levels)
        if margin_level not in valid_margin_levels:
            log.error("Voltage margin level description is unknown ({0}).".format(margin_level))
            raise apexceptions.AbortException
        if margin_level == 'DYNAMIC':
            margin_level = self._ud.uut_status.get('active_voltage_margin', 'NOMINAL')
        margin_table = kwargs.get('vmargin_table', self._ud.uut_config.get('vmargin_table', 'ALL'))
        check_only = kwargs.get('check_only', False)

        if check_only:
            aplib.set_container_text('DIAG VMARGIN CHK TEST: {0}'.format(margin_level))
        else:
            aplib.set_container_text('DIAG VMARGIN TEST: {0}'.format(margin_level))

        # Check Mode
        if self._mode_mgr.current_mode not in ['STARDUST', 'TRAF', 'DIAG']:
            log.error("Wrong mode; need to be in one of STARDUST, TRAF, or DIAG.")
            return aplib.FAIL, "Wrong mode."

        # Perform the voltage margin.
        # Note: The bin option is currently set to 0. This is for future feature. TBD.
        if not check_only:
            self._set_volt(device_instance=device_instance,
                          margin_level=margin_level,
                          vtable=margin_table if not margin_all else 'ALL',
                          asic_bin=0)

        @func_retry
        def __validate_voltages():
            # Get new voltages and save to status
            voltages = self._get_volt(device_instance=device_instance)
            self._ud.uut_status['voltages'] = {margin_level: voltages}
            self._ud.uut_status['active_voltage_margin'] = margin_level

            # Check against the margin limit table.
            return self._check_voltages(margin_level=margin_level, voltages=voltages, limit_table=margin_table, asic_bin=0)

        result = __validate_voltages()

        return aplib.PASS if result else (aplib.FAIL, "Voltage Margin problem (see log).")

    @apollo_step
    def fan_test(self, **kwargs):
        """ Fan Test (STEP)
        :menu: (enable=True, name=FAN, section=Diags, num=1, args={})
        :menu: (enable=False, name=FAN noretry, section=Diags, num=1, args={'max_attempts': 1})
        :param kwargs:
        :return:
        """
        max_attempts = kwargs.get('max_attempts', 1)
        if self._ud.automation:
            log.info("-" * 50)
            log.info("AUTOMATION")
            log.info("Robotic automation is enabled for this container!")
            log.info("No retries allowed.")
            log.info("-" * 50)
            max_attempts = 1

        @func_retry(max_attempts=max_attempts)
        def __fan_test():
            self.read_kirchhoff_regs(offsets=fan.get('regs', {}).values())
            results = []
            for test_speed_name in speed_sequence:
                fan_speed = fan.get('speed_settings', {}).get(test_speed_name, None)
                log.debug("Fan Speed = {0}".format(fan_speed))
                results.append(self._set_fan_speed(speed_name=test_speed_name,
                                                   fan_speed=fan_speed,
                                                   status_value_reference=fan.get('status_value')))
            return all(results)

        # Inputs
        speed_sequence = kwargs.get('speed_sequence', ['LOW', 'HIGH', 'NOMINAL'])
        fan = kwargs.get('fan', self._ud.uut_config.get('fan', {}))

        if not fan:
            log.warning("The 'fan' data dict is not defined per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        if not fan.get('enabled', True):
            log.warning("Fan Test has been disabled.")
            return aplib.DISABLED

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode."

        result = __fan_test()
        if result:
            log.info("FAN TEST: PASSED.")
            ret = aplib.PASS
        else:
            log.info("FAN TEST: FAILED.")
            ret = aplib.FAIL, "Fan Test set speed error."

        return ret

    @apollo_step
    def record_ecid(self, **kwargs):
        """Record Ecid (STEP)
        :menu: (enable=True, name=ECID, section=Diags, num=1, args={})

        Note: Uses 'asic' dict in product definition.
        Ex.  'asic': {'core_count': 1, 'locations': ['U98']},

        :param kwargs:
        :return:
        """
        # Input
        uut_asic_setup = kwargs.get('asic', self._ud.uut_config.get('asic', {}))
        if not uut_asic_setup:
            log.warning("The 'asic' data dict is not available or not defined per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode."

        # Get ASIC data (ALL instances)
        uut_asic_data = self._get_asic_ecid()

        # Integrity check
        if not uut_asic_data:
            log.error("FAILED - Unable to retrieve ASIC ECID data.")
            return aplib.FAIL
        if len(uut_asic_data) != uut_asic_setup.get('core_count', 0):
            log.error(
                "FAILED - The retreived ASIC data count ({0}) does NOT match the expected core count ({1})".format(
                    len(uut_asic_data), uut_asic_setup.get('core_count', 0)))
            return aplib.FAIL

        sernum = self._ud.puid.sernum
        if not sernum:
            log.warning("Serial Number for {0} is missing.".format(self._ud.puid_keys.sernum))
            if aplib.get_apollo_mode() == aplib.MODE_DEBUG:
                sernum = 'TST00000001'
                log.warning("Defaulting to bogus s/n for debug: {0}".format(sernum))
            else:
                log.error("Must have a valid s/n.")
                return aplib.FAIL

        # Setup for recording
        result = self._record_asic_ecid(uut_asic_data, uut_asic_setup, self._ud.asic_type_table, sernum)

        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def rtc_chkset_test(self, **kwargs):
        """ RTC Check/Set Test (STEP)
        Check the RTC and Set it (if conditions warrant the setting).

        This test uses an external reference file (saved to the UUT flash) which contains the server time
        when the RTC was originally set.  'No file' indicates the first attempt to check RTC and the datetime is assumed
        to be at the vendor default time greater than 1 yr in the past (typically epoch time).
        Additionally, on first attempt the external reference file will be generated and saved (in linux mode).
        On first creation of the reference file (server_mktime.txt) a sysinit must be done later.

        A "drift" is calculated based on the original set time to establish the pass/fail time window.
        Ultimately, this can determine if the RTC and battery have been working properly (assuming no unit tampering).

        *** IMPORTANT ***
        This test assumes ALL Apollo servers are synchronized!
        As of this writing the NTP mechanism is being used by the Apollo servers.
        "service ntpd status" will show if it is running.

        :menu: (enable=True, name=RTC CHK/SET, section=Diags, num=8, args={})
        :param kwargs:
        :return:
        """

        if 'rtc' not in self._ud.uut_config:
            log.warning("The 'rtc' data dict is not defined per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        # Inputs
        time_zone = kwargs.get('time_zone', self._ud.uut_config.get('rtc', {}).get('time_zone', 'GMT'))
        osc_accuracy = kwargs.get('osc_accuracy', self._ud.uut_config.get('rtc', {}).get('osc_accuracy', None))
        severity_allowed = kwargs.get('severity_allowed', self._ud.uut_config.get('rtc', {}).get('severity_allowed', 120))
        force_set = kwargs.get('force_set', False)

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode."

        # Check for NTP
        if not common_utils.getservicestatus('ntpd'):
            log.warning('*' * 81)
            log.warning("NTP is NOT running on this server; RTC check & set accuracy cannot be guaranteed!")
            log.warning("The RTC Test will be skipped which may result in an unset/incorrect RTC.")
            log.warning('*' * 81)
            return aplib.SKIPPED
        else:
            log.debug("NTP is running!")

        # Attempt retrieval of server time when the RTC was originally set.
        self._uut_conn.send('cat server_mktime.txt\r', expectphrase=self._mode_mgr.uut_prompt_map['STARDUST'], regex=True)
        time.sleep(1.0)
        m = parse.search("server_mktime='{server_mktime:0}'", self._uut_conn.recbuf)
        server_mktime = float(m['server_mktime']) if m else None

        # Get RTC
        log.info("-" * 40)
        log.info("RTC CHKSET TEST: CHECK")
        result = self._check_rtc(time_zone=time_zone,
                                 original_server_mktime=server_mktime,
                                 osc_accuracy=osc_accuracy,
                                 severity_allowed=severity_allowed)

        if result == 'PROG' or force_set:
            log.info("RTC CHKSET TEST: PROGRAM")
            retry_count = 1
            post_sysinit = False
            while result != 'PASS' and retry_count < 4:
                log.debug("RTC PROG: Attempt #{0}".format(retry_count))
                server_mktime = self._program_rtc(time_zone=time_zone)
                # Now save server time to file for later reference.
                if self._mode_mgr.goto_mode('LINUX'):
                    post_sysinit = True
                    self._uut_conn.send("""echo "server_mktime='{0}'" > server_mktime.txt\r""".format(server_mktime),
                                     expectphrase=self._mode_mgr.uut_prompt_map['LINUX'], regex=True)
                self._mode_mgr.goto_mode('STARDUST')
                # The check must NOT modify the default severity_allowed since RTC was just programmed.
                result = self._check_rtc(time_zone=time_zone, original_server_mktime=server_mktime)
                retry_count += 1

            if result != 'PASS':
                log.error("RTC PROG: Please check the RTC, battery, and server time.")
                log.error("RTC PROG: The UUT RTC could not be programmed in 3 attempts.")
            else:
                log.debug("RTC PROG: Successful.")
                if post_sysinit:
                    log.debug("Must have a clean sysinit after returning from Linux kernel.")
                    self.sysinit(**kwargs)

        log.info("RTC CHKSET TEST: {}.".format(result))
        log.info("-" * 40)

        return aplib.PASS if result == 'PASS' else aplib.FAIL

    @apollo_step
    def port_status_test(self, **kwargs):
        """ Port Status Test
        :menu: (enable=True, name=PORTSTAT, section=Diags, num=1, args={})
        :param kwargs:
        :return:
        """
        # Input
        retry_cnt = 0
        result = False
        max_attempts = kwargs.get('max_attempts', 3)
        if self._ud.automation:
            log.info("-" * 50)
            log.info("AUTOMATION")
            log.info("Robotic automation is enabled for this container!")
            log.info("No retries allowed.")
            log.info("-" * 50)
            max_attempts = 1

        # TODO: just target downlink ports or include uplink ports (if applicable)?
        downlink_ports = common_utils.expand_comma_dash_num_list(
            ','.join(self._ud.uut_config.get('traffic_cases', {}).get('TrafCase_NIF_1', {}).get('downlink_ports', {}).keys()))
        target_ports = self._ud.uut_config.get('target_ports', downlink_ports)
        loopbacks_required = kwargs.get('loopbacks_required', None)

        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode."

        # Loopback setting
        if aplib.get_apollo_mode() == aplib.MODE_DEBUG and loopbacks_required is None:
            log.debug("Loopback setting override was not indicated and UUT is in DEBUG_MODE; therefore, NO loopback required.")
            loopbacks_required = False
        elif loopbacks_required is None:
            log.debug("Setting loopback default.")
            loopbacks_required = True
        else:
            log.debug("Loopback setting override.")
        log.info("Port Loopbacks Requirement setting = {0}".format(loopbacks_required))

        poe_loadbox_present = False
        if hasattr(self._equip, 'poe_loadbox') and self._equip.poe_loadbox:
            log.debug("PoE Loadbox detected.  MUST configure external loopback for port status!")
            self._equip.poe_loadbox.connect(detect_signature='ok', external='on', auto='on')
            poe_loadbox_present = True

        log.debug("Downlink Ports      = {0}".format(downlink_ports))
        log.debug("Target Ports        = {0}".format(target_ports))
        log.debug("Loopbacks Required  = {0}".format(loopbacks_required))
        log.debug("PoE Loadbox Present = {0}".format(poe_loadbox_present))

        # Get and Check all ports' status
        log.info("-" * 40)
        while not result and retry_cnt < max_attempts:
            retry_cnt += 1
            log.info("Port Status TEST: Attempt #{0}".format(retry_cnt))
            current_portstatus = self._get_portstat(target_ports)
            if not current_portstatus:
                log.error("Critial error with port status; no data returned.")
                return aplib.FAIL
            result, ratio = self._check_portstat(current_portstatus, target_ports)
            if not result:
                if ratio == 1.0 and not loopbacks_required:
                    log.warning("-" * 50)
                    log.warning("Port status indicates ALL ports have no link up.")
                    log.warning("Loopbacks NOT installed is most likely condition.")
                    log.warning("Since 'loopbacks_required' flag is False, the Port Status will be SKIPPED.")
                    log.warning("External traffic test is also NOT possible!")
                    log.warning("-" * 50)
                    ret = aplib.SKIPPED
                    break
                else:
                    if max_attempts > 1:
                        if aplib.ask_question("Check all port cables and retry:", answers=['NO', 'YES'],
                                              timeout=60 * 60) == 'NO':
                            log.error("STEP: Port Status TEST FAILED. (Retry was refused.)")
                            ret = aplib.FAIL, "Port status error."
                            break
                    else:
                        log.error("STEP: Port Status TEST FAILED. (No retry.)")
                        ret = aplib.FAIL, "Port status error."
                        break
            else:
                log.info("Port Status TEST: PASSED.")
                ret = aplib.PASS
        log.info("-" * 40)

        self._ud.uut_status['portstat'] = ret
        self._ud.uut_status['loopbacks_required'] = loopbacks_required
        return ret

    @apollo_step
    def stackrac_test(self, **kwargs):
        """ StackRac Test (STEP)
        NOTE: No retries for robot automation OR chamber testing!

        :menu: (enable=True, name=STACKRAC, section=Diags, num=1, args={})
        :param kwargs:
        :return:
        """

        # Input
        retry_cnt = 0
        result = False
        max_attempts = kwargs.get('max_attempts', 3)
        enabled = kwargs.get('enabled', self._ud.uut_config.get('stackrac', {}).get('datastack', 0))

        if not enabled:
            log.warning("The 'stackrac' is not enabled per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        if self._ud.automation:
            log.info("-" * 50)
            log.info("AUTOMATION")
            log.info("Robotic automation is enabled for this container!")
            log.info("No retries allowed.")
            log.info("-" * 50)
            max_attempts = 1

        if aplib.apdicts.test_info.test_area in ['PCB2C', 'PCB4C']:
            log.info("-" * 50)
            log.info("CHAMBER {0}".format(aplib.apdicts.test_info.test_area))
            log.info("This container is running in a Chamber!")
            log.info("No retries allowed.")
            log.info("-" * 50)
            max_attempts = 1

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode."

        # Get and Check Stackdata
        log.info("-" * 40)
        while not result and retry_cnt < max_attempts:
            retry_cnt += 1
            log.info("StackRac TEST: Attempt #{0}".format(retry_cnt))
            current_stackdata = self._get_stackdata()
            result = self._check_stackdata(current_stackdata)
            if not result:
                if max_attempts > 1:
                    if aplib.ask_question("Check Data Stack Cable and retry:", answers=['YES', 'NO']) == 'NO':
                        log.error("STEP: StackRac TEST FAILED. (Retry was refused.)")
                        break
                    self.sysinit()
                else:
                    log.error("STEP: StackRac TEST FAILED. (No retry.)")
                    break
            else:
                log.info("StackRac TEST: PASSED.")
        log.info("-" * 40)

        self._ud.uut_status['stackrac'] = aplib.PASS if result else aplib.FAIL
        return self._ud.uut_status['stackrac']

    @apollo_step
    def i2c_test(self, **kwargs):
        """ I2C Tests
        Example:
        N24Pwr_CR> SCCTestNonDestructive -i:2
        Start testing read/write operations of Quack (non-destructive) ...
        PASSED.
        :menu: (enable=True, name=I2C TEST, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        area = aplib.apdicts.test_info.test_area

        # Input
        i2c = self._ud.uut_config.get('i2c', {})
        menu = kwargs.get('menu', False)
        if menu:
            ans = aplib.ask_question("Enter device instances to test:")
            target_device_instances = common_utils.expand_comma_dash_num_list(ans)
        else:
            target_device_instances = kwargs.get('target_device_instances',
                                                 i2c.get('target_device_instances', {}).get(area, None))

        log.info("Target Device Instances = {0}".format(target_device_instances))

        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL

        if not i2c:
            log.warning("No I2C test data available from product definition.")
            log.warning("This test will be skipped.")
            return aplib.SKIPPED

        result_list = []
        fail_list = []
        for test in i2c.get('tests', []):
            log.info("I2C {0}".format(test))
            for instance in target_device_instances:
                log.info(" Instance = {0}".format(instance))
                cmd = '{0} -i:{1}'.format(test, instance)
                self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=120, regex=True)
                time.sleep(1)
                if 'PASSED' not in self._uut_conn.recbuf:
                    result_list.append(False)
                    fail_list.append(cmd)
                else:
                    result_list.append(True)
        if all(result_list):
            log.info("STEP: I2C Tests = PASSED")
            ret = aplib.PASS
        else:
            log.info("STEP: I2C Tests = FAILED")
            log.info("Failing Tests: {0}".format(fail_list))
            ret = aplib.FAIL, "I2C error."

        return ret

    @apollo_step
    def led_test(self, **kwargs):
        """ LED Tests
        :menu: (enable=True, name=LED, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        def __check_led():
            """Check Led
            Random choice a Color in led sequences
            led_sequences  from products definitions, ['Green', 'Amber', 'Off']
            current_prog_dict {'cmd': 'SetLed all %op%', 'op': ['Green', 'Amber', 'Off']}
            :return:
            """
            result = False
            retry_cnt = 1
            while not result and retry_cnt < 3:
                current_led = random.choice(led_sequences)
                if current_led in results:
                    continue
                retry_cnt += 1
                current_prog_dict['op'] = current_led
                cmd = common_utils.rebuild_cmd(current_prog_dict, self._ud.uut_config)
                self._uut_conn.send("{0}\r".format(cmd), expectphrase=self._uut_prompt, regex=True, timeout=60)
                ans = aplib.ask_question("Choice UUT LED light color -> {0}".format(led_sequences),
                                         answers=led_sequences + ['None'])
                if ans == 'None':
                    log.error("Ops input None --> LED color:{0} Check Fail".format(current_led))
                    break
                elif ans != current_led:
                    log.warning("LED Color:{0}, Ops input:{1} Check fail".format(current_led, ans))
                else:
                    log.debug("LED Color:{0} Checked..".format(current_led))
                    result = True
                if result:
                    results.append(current_led)
                    log.debug("debug results --> {}".format(results))

            return result

        # Input
        led = self._ud.uut_config.get('led', {})

        if not led:
            log.warning("The 'led' is not enabled per the product_definition.")
            log.warning("This operation will be skipped.")
            return aplib.SKIPPED

        # Mode Check
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL

        # LED Check
        results = []
        for index in sorted(led):
            prog_dict = led[index]
            led_sequences = prog_dict['op']
            current_prog_dict = prog_dict.copy()
            for i in led_sequences:
                ret = __check_led()
                if not ret:
                    log.error("LED {0} Test = Fail.".format(i))
                    return aplib.FAIL

        log.info("STEP: LED Tests = PASS")

        return aplib.PASS

    @apollo_step
    def poe_power_test(self, **kwargs):
        """ PoE Power Test (STEP)
        :menu: (enable=True, name=POE POWER TEST, section=Diags, num=10.0, args={})
        :param kwargs:
        :return:
        """
        # If product definition does not specify PoE (irrespective of any PoE equipment connections),
        # then do not run this step.
        if 'poe' not in self._ud.uut_config:
            log.warning("The 'poe' data dict is not defined per the product_definition.")
            log.warning("This test will be disabled.")
            return aplib.DISABLED

        poe = self._ud.uut_config.get('poe', {})
        log.debug("PoE UUT Config: {0}".format(poe))
        if not poe:
            log.error("The 'poe' product definition entry is empty!")
            return aplib.FAIL
        poe_ports = poe.get('uut_ports', None)

        # Now check PoE Loadbox driver
        if not self._equip.poe_loadbox:
            return handle_no_poe_equip()

        # Inputs
        poe_type = kwargs.get('poe_type', poe.get('type', None))
        poe_volt_range = kwargs.get('poe_volt_range', poe.get('volt_range', (47.0, 57.0)))
        poe_current_range = kwargs.get('poe_current_range', poe.get('current_range', (200, 1200)))
        powerholdtime = kwargs.get('powerholdtime', poe.get('powerholdtime', 60000))
        disconnecttimeout = kwargs.get('disconnecttimeout', poe.get('disconnecttimeout', 60000))
        poweronsetuptimeout = kwargs.get('poweronsetuptimeout', poe.get('poweronsetuptimeout', 30000))
        disconnecttype = kwargs.get('disconnecttype', poe.get('disconnecttype', 1))
        icutcode = kwargs.get('icutcode', poe.get('icutcode', None))

        if poe_type not in self._equip.poe_loadbox.LOAD_CLASSES.keys():
            log.error("PoE Type for testing is not recognized.")
            return aplib.FAIL

        if not self._mode_mgr.is_mode('DIAG'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'DIAG' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['DIAG']

        # Phase 1: Cfg UUT and Get Power Budget
        # -------------------------------------
        aplib.set_container_text('PoE Power Test: UUT Cfg')
        log.info('STEP: PoE Power Test -- Phase1 UUT Cfg.')
        self._operate_poe_uut(action='CFG', poe_type=poe_type, poe_params=poe)
        if self._ud.uut_status.get('poe_pwr_budget_groups', 0) == 0:
            # Set power budget if not previously set.
            self._ud.uut_status['poe_pwr_budget_groups'] = self._operate_poe_uut(action='BUDGET', poe_type=poe_type, poe_ports=poe_ports)
        poe_pwr_budget_groups = self._ud.uut_status['poe_pwr_budget_groups']

        # Phase 2: Set PoE Equipment Cfg
        # ------------------------------
        aplib.set_container_text('PoE Power Test: Equip Cfg')
        log.info('STEP: PoE Power Test -- Phase2 Equip Cfg.')
        self._equip.poe_loadbox.uut_poe_type = poe_type
        self._equip.poe_loadbox.echo_msg("PoE Power Test (Volt Meas)")
        self._equip.poe_loadbox.show_equipment()
        self._equip.poe_loadbox.reset()
        self._equip.poe_loadbox.set_power_load(ieee=True)
        self._equip.poe_loadbox.set_class(load_class=self._equip.poe_loadbox.LOAD_CLASSES[poe_type])
        self._equip.poe_loadbox.set_load_on()

        # Phase 3: Turn on PoE Power and Measure Voltage
        # ----------------------------------------------
        aplib.set_container_text('PoE Power Test: ON')
        log.info('STEP: PoE Power Test -- Phase3 ON.')
        results = []
        for group in range(1, poe_pwr_budget_groups + 1):
            active_poe_ports = self._build_pwr_budget_port_list(ports=poe_ports, group_index=group,
                                                                poe_pwr_budget_groups=poe_pwr_budget_groups)
            title = "PoE Port SubGroup {0}/{1}".format(group, poe_pwr_budget_groups) if poe_pwr_budget_groups > 1 else "PoE Port Group {0}".format(group)
            log.info(" ")
            log.info(title)
            log.info("-" * len(title))
            log.debug("Active PoE Ports: {0}".format(active_poe_ports))
            log.debug("1. PoE ON")
            self._set_poe_on(poe_type=poe_type, active_poe_ports=active_poe_ports)
            log.debug("2. PoE Events")
            self._operate_poe_uut(action='EVENTS', poe_type=poe_type, poe_ports=active_poe_ports)
            log.debug("3. PoE Measure Voltage at LoadBox")
            results.append(self._measure_poe_volt_test(active_poe_ports=active_poe_ports, poe_volt_range=poe_volt_range))
            log.debug("4. PoE Measure UUT Power")
            results.append(self._measure_uut_poe_power(poe_type=poe_type, active_poe_ports=active_poe_ports, poe_current_range=poe_current_range))
            log.debug("5. PoE OFF")
            self._set_poe_off(poe_type=poe_type, active_poe_ports=active_poe_ports)

        if not all(results):
            log.warning("The PoePowerTest will NOT be run since the Power Measure Tests failed.")
            self._equip.poe_loadbox.set_load_off()
            self._equip.poe_loadbox.disconnect()
            return aplib.FAIL

        # Phase 4: Run the Diag PoePowerTest
        # ----------------------------------
        log.info('STEP: PoE Power Test -- Phase4 Diag.')
        self._equip.poe_loadbox.echo_msg("PoE Power Test (Diag)")
        testallports = 1 if poe_pwr_budget_groups == 1 else 0
        results = []
        for group in range(1, poe_pwr_budget_groups + 1):
            active_poe_ports = self._build_pwr_budget_port_list(ports=poe_ports, group_index=group,
                                                                poe_pwr_budget_groups=poe_pwr_budget_groups)
            title = "PoE Port SubGroup {0}/{1}".format(group, poe_pwr_budget_groups) if poe_pwr_budget_groups > 1 else "PoE Port Group {0}".format(group)
            log.info(" ")
            log.info(title)
            log.info("-" * len(title))
            log.debug("Active PoE Ports: {0}".format(active_poe_ports))
            active_poe_ports_list = active_poe_ports.split(',')
            port_count = len(active_poe_ports_list)
            poe_params = {'testallports': str(testallports), 'portgroupsize': port_count,
                          'portnum': active_poe_ports_list[0],
                          'disconnecttype': disconnecttype, 'disconnecttimeout': disconnecttimeout,
                          'poweronsetuptimeout': poweronsetuptimeout, 'powerholdtime': powerholdtime,
                          'icutcode': icutcode}
            if self._operate_poe_uut(action='CFG', poe_type=poe_type, poe_params=poe_params, poe_ports=active_poe_ports):
                ret = self._run_poe_diag_test(command='PoePowerTest')
            else:
                log.error("Cannot config UUT for PoE operation.")
                ret = False
            results.append(ret)

        ret = all(results)

        # Phase 5: Disconnect PoE Equipment
        # ----------------------------------
        log.info('STEP: PoE Power Test -- Phase5 OFF.')
        aplib.set_container_text('PoE Power Test: OFF')
        self._equip.poe_loadbox.set_load_off()
        self._equip.poe_loadbox.disconnect()

        aplib.set_container_text('PoE Power Test')
        log.info('STEP: PoE Power Test = {0}'.format('PASSED.' if ret else 'FAILED.'))

        return aplib.PASS if ret else (aplib.FAIL, "PoE Poer load is bad.")

    @apollo_step
    def poe_class_test(self, **kwargs):
        """ PoE Power Test (STEP)
        :menu: (enable=True, name=POE CLASS TEST, section=Diags, num=11.0, args={})
        :param kwargs:
        :return:
        """
        # If product definition does not specify PoE (irrespective of any PoE equipment connections),
        # then do not run this step.
        if 'poe' not in self._ud.uut_config:
            log.warning("The 'poe' data dict is not defined per the product_definition.")
            log.warning("This test will be disabled.")
            return aplib.DISABLED

        poe = self._ud.uut_config.get('poe', {})
        log.debug("PoE UUT Config: {0}".format(poe))
        if not poe:
            log.error("The 'poe' product definition entry is empty!")
            return aplib.FAIL

        # Now check PoE driver
        if not self._equip.poe_loadbox:
            return handle_no_poe_equip()

        # Inputs
        poe_type = poe.get('type', None)
        if poe_type not in self._equip.poe_loadbox.LOAD_CLASSES.keys():
            log.error("PoE Type for testing is not recognized.")
            return aplib.FAIL
        poe_classes = kwargs.get('poe_classes', [i for i in range(0, self._equip.poe_loadbox.LOAD_CLASSES[poe_type] + 1)])
        if isinstance(poe_classes, str):
            poe_classes = poe_classes.split(',')

        log.debug("PoE Classes: {0}".format(poe_classes))
        log.debug("PoE Type to test: {0}".format(poe_type))

        if not self._mode_mgr.is_mode('DIAG'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'DIAG' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['DIAG']

        # Phase 1: Set PoE Equipment Cfg
        # ------------------------------
        aplib.set_container_text('PoE Class Test: Equip Cfg')
        log.info('STEP: PoE Class Test -- Phase1 Equip Cfg.')
        self._equip.poe_loadbox.uut_poe_type = poe_type
        self._equip.poe_loadbox.echo_msg("PoE Class Test")
        self._equip.poe_loadbox.show_equipment()
        self._equip.poe_loadbox.reset()
        self._equip.poe_loadbox.set_power_load(ieee=True)

        # Phase 2: Iterate thru all selected classes
        # ------------------------------------------
        results = []
        for poe_class in poe_classes:
            aplib.set_container_text('PoE Class {0} Test'.format(poe_class))
            log.info('STEP: PoE Class {0} Test'.format(poe_class))
            self._equip.poe_loadbox.disconnect()
            self._equip.poe_loadbox.set_class(load_class=int(poe_class))
            self._equip.poe_loadbox.connect(detect_signature='ok', external='on', auto='on')
            ret = self._run_poe_diag_test(command='PoeClassTest')
            log.debug("PoE Class {0} Test: {1}.".format(poe_class, 'PASSED' if ret else 'FAILED'))
            results.append(ret)
        self._equip.poe_loadbox.disconnect()

        ret = all(results)
        log.info("STEP: PoE Class Test SUMMARY = {0}.".format('PASSED' if ret else 'FAILED'))

        return aplib.PASS if ret else (aplib.FAIL, "PoE Class power is bad.")

    @apollo_step
    def poe_detect_test(self, **kwargs):
        """ PoE Detect Test (STEP)

         detecttype = 1  : CSCO  --> mdimode = 0,1
         detecttype = 2  : IEEE  --> mdimode = X (don't care)

         UPoE units must perform detect tests in both POE and UPOE modes.
         (Do this as additional steps in the sequence with the 'type' param.)

        :menu: (enable=True, name=POE DETECT TEST, section=Diags, num=11.0, args={})
        :menu: (enable=True, name=POE DETECT TEST IEEE_p, section=Diags, num=11.0, args={'detecttype': [2], 'mdimode': [1], 'poe_type': 'POE+'})
        :menu: (enable=True, name=POE DETECT TEST IEEE_u, section=Diags, num=11.0, args={'detecttype': [2], 'mdimode': [1], 'poe_type': 'UPOE'})
        :param kwargs:
        :return:
        """
        # If product definition does not specify PoE (irrespective of any PoE equipment connections),
        # then do not run this step.
        if 'poe' not in self._ud.uut_config:
            log.warning("The 'poe' data dict is not defined for the UUT per the product_definition.")
            log.warning("This test will be disabled.")
            return aplib.DISABLED
        poe = self._ud.uut_config.get('poe', {})
        log.debug("PoE UUT Config: {0}".format(poe))
        if not poe:
            log.error("The 'poe' product definition entry is empty!")
            return aplib.FAIL

        # Now check PoE driver
        if not self._equip.poe_loadbox:
            return handle_no_poe_equip()

        # Inputs
        poe_type = kwargs.get('poe_type', poe.get('type', None))
        detecttypes = kwargs.get('detecttype', poe.get('detecttype', [1, 2]))
        mdimodes = kwargs.get('mdimode', poe.get('mdimode', [0, 1]))
        # Check input form
        detecttypes = [detecttypes] if not isinstance(detecttypes, list) else detecttypes
        mdimodes = [mdimodes] if not isinstance(mdimodes, list) else mdimodes

        log.debug("PoE Type to test: {0}".format(poe_type))
        if poe_type not in self._equip.poe_loadbox.LOAD_CLASSES.keys():
            log.error("PoE Type for testing is not recognized.")
            return aplib.FAIL

        if not self._mode_mgr.is_mode('DIAG'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'DIAG' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['DIAG']

        # Phase 1: Set PoE Equipment Cfg
        # ------------------------------
        aplib.set_container_text('PoE Detect Test: Equip Cfg')
        log.info("STEP: PoE Detect Test -- Phase1 Equip Cfg.")
        self._equip.poe_loadbox.uut_poe_type = poe_type
        self._equip.poe_loadbox.echo_msg("PoE Detect Test")
        self._equip.poe_loadbox.show_equipment()
        self._equip.poe_loadbox.reset()
        self._equip.poe_loadbox.set_power_load(ieee=True)
        self._equip.poe_loadbox.disconnect()
        self._equip.poe_loadbox.set_class(load_class=self._equip.poe_loadbox.LOAD_CLASSES[poe_type])

        # Phase 2: run det test
        # ---------------------
        aplib.set_container_text('PoE Detect Test: Run')
        log.info("STEP: PoE Detect Test -- Phase2 Run Tests.")
        results = []
        for detecttype in detecttypes:
            if detecttype == 2:
                if mdimodes != [1]:
                    log.warning("PoE DetectType is IEEE; the MDI Mode is a don't care (default=1).")
                    mdimodes = [1]
            for mdimode in mdimodes:
                poe_params = {'detecttype': detecttype, 'mdimode': str(mdimode)}
                log.info("STEP: PoE Detect Test = {0}".format(poe_params))
                ret = False
                if self._operate_poe_uut('CFG', poe_type=poe_type, poe_params=poe_params):
                    self._equip.poe_loadbox.connect(detect_signature='ok', external='on', auto='on', cisco=1 if detecttype == 1 else 0)
                    ret = self._run_poe_diag_test(command='PoeDetTest')
                log.debug("STEP: PoE Detect Test D{0}M{1} = {2}".format(detecttype, mdimode, 'PASSED' if ret else 'FAILED'))
                results.append(ret)
                self._equip.poe_loadbox.disconnect()
        self._equip.poe_loadbox.disconnect()
        log.debug("PoE Detect Individual Results = {0}".format(results))
        log.info("STEP: PoE Detect Test = {0}.".format('PASSED' if all(results) else 'FAILED'))

        return aplib.PASS if ret else (aplib.FAIL, "Bad PoE Detect")

    @apollo_step
    def poe_verify_empty_ports(self, **kwargs):
        """PoE Verify Empty Ports Test (STEP)

            NOTE1: This step requires UUT in 'DIAG' mode.
            NOTE2: This does NOT requires PoE Loadbox, it is testing empty POE ports (no device connected),
                   making sure ports show FAIL/TIMEOUT.

        :param kwargs: poe_ports:       POE ports (str), this is for manual override,
                                        usually this value should come from uut_config
                                    ex: '1-48', '1-24', MUST be in this format
        :return:
        """
        # If product definition does not specify PoE (irrespective of any PoE equipment connections),
        # then do not run this step.
        if 'poe' not in self._ud.uut_config:
            log.warning("The 'poe' data dict is not defined for the UUT per the product_definition.")
            log.warning("This test will be disabled.")
            return aplib.DISABLED

        poe = self._ud.uut_config.get('poe', {})
        log.debug("PoE UUT Config: {0}".format(poe))
        if not poe:
            log.error("The 'poe' product definition entry is empty!")
            return aplib.FAIL

        poe_ports = kwargs.get('poe_ports', poe.get('uut_ports'))

        if not self._mode_mgr.is_mode('DIAG'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'DIAG' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['DIAG']

        # perform test
        ret = self._run_poe_empty_ports_test(poe_ports=poe_ports)

        return aplib.PASS if ret else (aplib.FAIL, "PoE Empty Port status not correct.")

    @apollo_step
    def psu_check(self, **kwargs):
        """ PSU Check
        This routine has 2 levels of checking:
            1. PCBA site (just presence)
            2. DF site (PID check against customer ordered PID)
        :menu: (enable=True, name=PSU CHECK, section=Diags, num=12.0, args={})
        :param kwargs: expected_pids (list) of 0, 1, or 2 PIDs.
                       Note: 0=[], 1=[A], 2= [A,B]
        :return:
        """
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['STARDUST']

        # Inputs
        psu = kwargs.get('psu', self._ud.uut_config.get('psu', {}))
        expected_pids = kwargs.get('expected_pids', [None, None])
        expected_pids = [expected_pids] if not isinstance(expected_pids, list) else expected_pids
        for i in range(0, len(psu.keys())):
            if i > len(expected_pids) - 1:
                expected_pids.append(None)

        # Sanity
        if not psu or not psu.get('slots', None):
            log.warning("No PSU slot data in product definition.")
            return aplib.SKIPPED

        # Get PSU Data
        psu_info = self._get_psu()
        for slot in psu_info.keys():
            log.debug("PSU {0} eeprom: {1}".format(slot, psu_info[slot]))

        # PIDs: Discover which PID key to use.
        pid_key = 'unknown'
        for pk in ['PID', 'PS PID', 'PS Product Number', 'unknown']:
            for slot in psu_info.keys():
                if pk in psu_info[slot]:
                    pid_key = pk
                    break
        log.debug("PSU PID Key = '{0}'".format(pid_key))

        # If expected PIDs then check against installed PIDs.
        # TODO: Determine if we care about slot location; currenly expected list order and installed slot loc is required to align.
        result = True
        for i, slot in enumerate(psu_info.keys()):
            pid = psu_info[slot].get(pid_key, None)
            pstat = psu_info[slot].get('Hardware status', '')
            epid = expected_pids[i]
            log.info("-" * 40)
            log.info("PSU {0}:".format(slot))
            log.info("  Detected = {0}".format(pid))
            log.info("  Power    = {0}".format(pstat))
            log.info("  Expected = {0}".format(epid))
            if epid:
                if pid == epid:
                    log.info("PSU PID match!")
                    result = False if 'Good' not in pstat else result
                else:
                    log.error("PSU PID mismatch!")
                    result = False
            else:
                log.debug("Ignore PSU PID slot check.")

        self._ud.uut_config['psu_info'] = psu_info

        return aplib.PASS if result else aplib.FAIL

    # ==================================================================================================================
    # USER METHODS   (step support)
    # ==================================================================================================================
    # ------------------------------------------------------------------------------------------------------------------
    # Diag Utility Functions
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def get_cwd(self):
        """ Get CWD
        :return:
        """
        self._clear_recbuf()
        self._uut_conn.send('pwd\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        m = parse.search('{dev:0}:{cwd:1S}', self._uut_conn.recbuf)
        log.debug("CWD = {0}".format(m['cwd']))
        return m['cwd']

    @func_details
    def set_cwd(self, new_dir):
        """ Set CWD
        :param new_dir:
        :return:
        """
        if not new_dir:
            return None
        self._clear_recbuf()
        self._uut_conn.send('cd {0}\r'.format(new_dir), expectphrase=self._uut_prompt, timeout=30, regex=True)
        cwd = self.get_cwd()
        if new_dir in cwd:
            log.debug("CWD is set.")
            return cwd
        else:
            return None

    @func_details
    def get_device_files(self, sub_dir='', file_filter='.*?', attrib_flags='-ld'):
        """ Get Device/Flash Files

        Sample:
        PL24_CR> dir
         46465 drwx        0  .
             2 drwx        0  ..
         46466 -rw-  2097152  nvram_config
         46467 -rw- 79110340  cat3k_caa-base.SPA.03.03.04SE.pkg
         46468 -rw-  6521532  cat3k_caa-drivers.SPA.03.03.04SE.pkg
         46469 -rw- 34530288  cat3k_caa-infra.SPA.03.03.04SE.pkg
         46470 -rw- 34856268  cat3k_caa-iosd-universalk9.SPA.150-1.EZ4.pkg
         46471 -rw- 25172880  cat3k_caa-platform.SPA.03.03.04SE.pkg
         46472 -rw- 77445952  cat3k_caa-wcm.SPA.10.1.140.0.pkg
         46473 -rw-     1247  packages.conf
         46475 drwx        0  dc_profile_dir
         46477 -rwx 24072024  test_image.bin
         46478 -rwx  1048576  cat3k_caa_loader.img.14Jul10.SSA
         46479 -rwx   109405  bellCrFpga06_01.hex
         46480 -rwx 22337271  vmlinux2013Sep23.mzip.SSA
         46481 -rwx 14506680  stardustThrCR.2014May01
         46482 -rwx 23728592  stardustThrCSR.2015Sep11
         69697 drwx        0  kirch90
         46483 -r--  1048576  cat3k_caa_loader.img.14Nov26.SPA
         46484 -r--  1048576  cat3k_caa_loader_dev.img.14Mar24.SSA
         46485 -rwx  1605693  strutt_00_23.hex


         Shannon48U> dir
        147465 -rwx 16777216  20161116_cat3k4k_x86_RM.bin
        147472 drwx        0  kirch90
        147457 drwx        0  .
        147481 -rwx 85134532  stardust2017Jan06
        147467 -rw- 16777216  btldr.bin
        147462 -rwx 44713896  bzImage.110116.SSA
        147461 -rwx   381758  app_flash.bin
        147463 -rwx     9932  17-S24P3-02.txt
        147471 -rwx 16777216  20161207_cat3k4k_x86_RM2.bin
        147475 -rwx 85108292  stardust2016Dec13
        147479 -rwx  1605693  strutt_00_23.hex
        147459 -rwx  1605693  strutt_00_22.hex
        147466 -rwx 45164424  bzImage.111616.SSA
        147464 -rwx 84781540  stardust2016Nov15
        147458 -rwx     9932  17-S48P3-02.txt
        147460 -rwx    25166  app_data.srec
             2 drwx        0  ..
        147469 -rwx 45170216  bzImage.112216.SSA
        147470 -rw-     1250  nyquist_fdisk
        147468 -rw- 16777216  20161207_cat3k4k_x86_RM.bin

        Shannon48U> pwd
        simfs:/mnt/flash3/user

        :param sub_dir:
        :param file_filter:
        :param attrib_flags:
        :return:
        """
        m = list()
        try:

            @func_retry
            def __dir():
                self._clear_recbuf()
                self._uut_conn.send('dir {0}\r'.format(sub_dir), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                attrib_filter = '[{0}][-rwx]'.format(attrib_flags) + '{3}'
                p = re.compile(
                    r'[ \t]*[0-9]+[ \t]+{1}[ \t]+[0-9]+[ \t]+({0})[\r\n]+'.format(file_filter, attrib_filter))
                return p.findall(self._uut_conn.recbuf)

            m = __dir()
            if not m:
                log.debug("No files found that match the criteria.")
                return []
            i = 0
            while i < len(m):
                if m[i][1] == '.' or m[i][1] == '..':
                    m.pop(i)
                else:
                    i += 1
            # Do a reverse sort to put "newer" files first based on lexigraphical sort of datestamp in the filename.
            m.sort(reverse=True)
        except apexceptions.TimeoutException as e:
            log.error(e)
        finally:
            return m

    @func_details
    def run_batch_file(self, batch_image, begin_label=None, home_dir=None, timeout=500):
        """ Run Batch File
        Run any generic diags batch file.
        :param batch_image:
        :param begin_label:
        :param home_dir:
        :param timeout:
        :return:
        """
        # Set known Diags home dir
        home_dir = self.get_cwd() if not home_dir else home_dir

        batch_subdir = os.path.dirname(batch_image)
        batch_file = os.path.split(batch_image)[1]

        # Change to subdir (if any)
        self.set_cwd(batch_subdir)

        # Check that the batch file is available
        device_files = self.get_device_files(file_filter=batch_file, attrib_flags='-')
        if not device_files or batch_file != device_files[0]:
            log.error("Required Batch file '{0}' not found{1}.".format(batch_file, ' in {0}'.format(
                batch_subdir) if batch_subdir else ''))
            return False

        # Set params
        if begin_label:
            args = '-begin:{0}'.format(begin_label)
        else:
            args = ''
        log.debug("Args = {0}".format(args))

        # Run it!
        self._clear_recbuf()
        self._uut_conn.send('exec {0} {1}\r'.format(batch_file, args), expectphrase='.*', timeout=30, regex=True)

        # Loop on output status; print each command as it is executed.
        loop_count, cmd_count = 0, 0
        head_ptr, tail_ptr = 0, 0
        collective_errors = []
        fail_pattern = '(?:(?i)Error)|(?:(?i)Fail)|(?:USAGE)'
        ret = True
        while loop_count < int(timeout) * 2:
            # Snapshot recbuf and put in list (note: last line can be incomplete)
            recbuf_lines = self._uut_conn.recbuf.splitlines()
            buf_len = len(recbuf_lines)

            if buf_len != tail_ptr:
                # Process only if number of lines has changed since last capture.
                tail_ptr = buf_len
                for line in recbuf_lines[head_ptr:tail_ptr - 1]:
                    # Process most recently added lines.
                    if re.search(self._uut_prompt, line):
                        cmd_count += 1
                        log.debug("{0:04d}: {1}".format(cmd_count, line))

                recbuf_lines_partial = recbuf_lines[head_ptr:tail_ptr - 1]
                if re.search(fail_pattern, str(recbuf_lines_partial)):
                    # NOTE1: Batch will continue to run if an error or fail condition is found.
                    log.error("Problem with batch!")
                    for line in recbuf_lines_partial:
                        if re.search(fail_pattern, line):
                            collective_errors.append(line)
                    ret = False

                # Move pointer
                head_ptr = tail_ptr - 1

            if re.search('EXEC_STOP', self._uut_conn.recbuf):
                # Exec: my.SBC_cfg EXEC_STOP reached line 100
                log.debug("Batch is done.")
                break

            if re.search('Exec: .* Done.', self._uut_conn.recbuf):
                # NOTE2: Batch will finish if the begin_label is NOT found.
                # (Exec: "my.SBC_cfg": 100 lines: Done.)
                log.warning("Batch reach end; execution ignored.")
                break

            loop_count += 1
            time.sleep(0.5)

        else:
            log.error("Batch output status processing timed out; check the batch file.")
            ret = False

        # Restore
        self.set_cwd(home_dir)

        log.info("Batch run was {0}.".format('successful' if ret else 'unsuccessful'))
        if not ret:
            log.error("Batch ERRORS")
            for line in collective_errors:
                log.error(line)

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Voltage
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_volt(self, device_instance=0):
        """ Get Volt

        SAMPLE OUTPUT:
        N24Pwr_CR> getvolt
        *****************************************************************************
        |       SBC | VOUT_CMD |  Margin | Output (Volts) | Change (%) |  Board/FRU |
        *****************************************************************************
        |      3.3V |       NA |     OFF |         3.3007 |    +0.0000 |      BOARD |
        |      2.5V |       NA |     OFF |             NA |         NA |      BOARD |
        |      1.8V |       NA |     OFF |         1.7929 |     -0.444 |      BOARD |
        |      1.5V |       NA |     OFF |         1.4960 |     -0.266 |      BOARD |
        |      1.2V |       NA |     OFF |             NA |         NA |      BOARD |
        |      1.0V |       NA |     OFF |         0.9980 |     -0.200 |      BOARD |
        |      0.9V |       NA |     OFF |         0.8984 |     -0.222 |      BOARD |
        |  1.0V-DP0 |   1.0000 |     OFF |         0.9978 |     -0.300 |      BOARD |
        |   1.5V-DP |       NA |     OFF |         1.4941 |     -0.400 |      BOARD |

        WARN: No FRU detected or no FRU Voltage rails defined.

        :param device_instance:
        :return:
        """
        device_instance = int(device_instance)
        if device_instance == 0:
            volt_type = '(BOARD)|(Main Board)'
        elif device_instance > 0:
            volt_type = 'FRU'
        else:
            volt_type = '.*'

        @func_retry
        def __volt():
            self._clear_recbuf()
            self._uut_conn.send('GetVoltMarg\r', expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('\|(.*?)\|(.*?)\|(.*?)\|([ \-.0-9]+|[ NAna]+)\|(.*?)\|(.*?)\|')
            return p.findall(self._uut_conn.recbuf)

        m = __volt()
        voltages = {i[0].strip(): i[3].strip() for i in m if re.search(volt_type, i[5])} if m else {}
        for voltage in voltages:
            try:
                voltages[voltage] = float(voltages[voltage])
            except ValueError:
                pass
        log.debug("Voltages for {0}: {1}".format(volt_type, voltages))
        return voltages

    @func_details
    def _set_volt(self, device_instance=0, margin_level='NOMINAL', vtable=None, asic_bin=0):
        """ Set Voltage
        Provides a voltage margin setting per voltage rail (via SBC) based on HW design.
        Note: Some voltage rails may NOT be marginable.
        :param device_instance: Device
        :param margin_level: 'NOMINAL', 'HIGH', 'LOW'
        :param vtable: (see product_definitions)
        :param asic_bin: Binning
        :return:
        """
        verbose = True if self._ud.verbose_level > 1 else False
        device_instance = int(device_instance)
        if device_instance >= 0:
            device_param = ' -f:{0}'.format(device_instance)
        else:
            device_param = ''

        if not vtable:
            log.warning("NO Voltage Rail Table provided.  By default, ALL rails will be selected!")
            vtable = ['ALL']
        elif isinstance(vtable, str) and vtable.upper() == 'ALL':
            log.debug('ALL voltage rails selected.')
            vtable = ['ALL']
        else:
            log.debug("Using voltage rail table = {0}".format(vtable if verbose else 'vtable'))

        if margin_level != 'NOMINAL':
            # Note: To ensure a smooth voltage swing; always margin to nominal first!
            margin_level_seq = ['NOMINAL', margin_level]
        else:
            margin_level_seq = [margin_level]

        # Set the Voltages
        for vrail in vtable:
            for volt_level in margin_level_seq:
                self._uut_conn.send('SetVoltMarg {0} {1}{2}\r'.format(vrail, volt_level, device_param),
                              expectphrase=self._uut_prompt, regex=True, timeout=120)
                time.sleep(1.0)
        common_utils.uut_comment(self._uut_conn, 'Voltage', 'Wait for voltage margin to settle.')
        time.sleep(2.0)

        return True

    @func_details
    def _check_voltages(self, margin_level, voltages, limit_table, asic_bin=0):

        verbose = True if self._ud.verbose_level > 1 else False
        m_factor = {'NOMINAL': 0, 'HIGH': 1, 'LOW': -1}
        vresults = {}

        # Check
        for i, voltage in enumerate(voltages):
            vlimits = None
            if voltage in limit_table:
                if 'bins' in limit_table[voltage]:
                    vlimits = limit_table[voltage]['bins'][asic_bin] if asic_bin in limit_table[voltage]['bins'] else None
                else:
                    vlimits = limit_table[voltage]

            if verbose:
                log.debug("Rail #{0:02}  = {1}  {2})".format(i, voltage, voltages[voltage]))
                log.debug("Margin Limits = {0}".format(vlimits))

            if vlimits and isinstance(voltages[voltage], float):
                m_sign = m_factor[margin_level]
                v_marg_levels = {'NOMINAL': 0.0, 'HIGH': vlimits['mhi'], 'LOW': vlimits['mlo']}
                v_marg = v_marg_levels[margin_level]
                upper_limit = round(
                    ((vlimits['vnom'] + vlimits['trim']) * (1.0 + (m_sign * v_marg))) * (1.0 + vlimits['gb']), 3)
                lower_limit = round(
                    ((vlimits['vnom'] + vlimits['trim']) * (1.0 + (m_sign * v_marg))) * (1.0 - vlimits['gb']), 3)
                vresults[voltage] = {'upper': upper_limit, 'lower': lower_limit, 'actual': voltages[voltage]}
                vresults[voltage]['status'] = True if lower_limit <= voltages[voltage] <= upper_limit else False
            else:
                vresults[voltage] = {'upper': 'NA', 'lower': 'NA', 'actual': voltages[voltage], 'status': True}

        log.debug("Voltage Status for {0}:".format(margin_level))
        for v in vresults:
            log.debug("{0:<20}: AC={1:<10}  UL={2:<10}  LL={3:<10}  ST={4}".format(v,
                                                                                   vresults[v]['actual'],
                                                                                   vresults[v]['upper'],
                                                                                   vresults[v]['lower'],
                                                                                   vresults[v]['status'], ))

        ret = all([vresults[i]['status'] for i in vresults])
        if not ret:
            log.debug("Voltage margins FAILED.")
        else:
            log.debug("Voltage margins PASSED.")

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Temperature
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_system_temperature(self):
        """
        Examples:
        C3K
        ****************************
        Temperature and Fan Status
        ****************************
        Intake Temperature (0x0060): +24C
        Exhaust Temperature (0x0084): +33C
        Hot-spot Temperature (0x00a6): +41C
        Fan 0 status: OK
        Fan 1 status: OK
        Fan 2 status: OK
        PS-A  status: 0x03( Present - Power Good - )
        ****************************


        C9200
        *************************************
        Main Board: Temperature and Fan Status
        *************************************
        INLET LM75 Thermal (0x1d00): +29.0C
        OUTLET LM75 Thermal (0x1e80): +30.5C

        *************************************
        Main Board: Voltages and Currents
        *************************************
        DP-vdd_1.00V :   1000
                Iout :    990

        :return:
        """

        @func_retry
        def __systemp():
            self._clear_recbuf()
            self._uut_conn.send('GetSystemStatus\r', expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('[ \t]*([ \-_a-zA-Z0-9]+) (?:Thermal|Temperature).*?: ([\-+.0-9]+)C')
            return p.findall(self._uut_conn.recbuf)

        m = __systemp()
        temps = {i[0].strip(): i[1].strip() for i in m}
        for temp in temps:
            try:
                temps[temp] = float(temps[temp])
            except ValueError:
                pass
        log.debug("System Temps: {0}".format(temps))
        return temps

    @func_details
    def _get_asic_temperature(self, asic_name='Doppler'):
        """

        GEN2
          *** Doppler #0 chip info:
          Type = 0x0390
          Version = 0x2
          Die ID = 1200a980 18e020c1 21e3b0e0 ec000000
                  (01950048 83040718 070dc784 00000037) IBM format
                   FUSE0 = 0 (svb_psro is slower than svb_cut)
                   FUSE86:89 (svb_psro) = 7, FUSE82:85 (svb_cut) = 8
          Temp = 46 degree C
          Voltage = 1.005V
          Core frequency = 375 Mhz

        GEN3
          *** Main Board: Doppler #0 chip info:
            Type = 0x03e1
            Version = 0x1
            Die ID = 01303032 3034534d 54545413 0a021a00
              VID : 825 mV
              Die column X/Y : 2/10
              Wafer Id       : 19
              Wafer lot Id   : TTTMS40200
              Programmed at wafer sort : 1
              Programmed at final test : 0
            Local Temp    = 53 degree C
            Remote Temp 1 = 54 degree C
            Remote Temp 2 = 57 degree C

            Remote Temp 3 = 56 degree C
            Remote Temp 4 = 56 degree C
            Voltage = 0.839V
            Core frequency = 500 Mhz

        :param (str) asic_name:
        :return:
        """

        @func_retry
        def __doptemps():
            self._clear_recbuf()
            self._uut_conn.send('DopChipInfo\r', expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            pats = [re.compile('{0} #([0-9]+)'.format(asic_name)), re.compile('Temp[ \t]* = ([\-+.0-9]+)')]
            matches = []
            try:
                for p in pats:
                    matches.append(p.findall(self._uut_conn.recbuf))
                _temps = {'{0}_{1}'.format(asic_name, k): v for k, v in zip(matches[0], matches[1])}
            except (ValueError, KeyError):
                _temps = {}
            return _temps

        temps = __doptemps()
        for temp in temps:
            try:
                temps[temp] = float(temps[temp])
            except ValueError:
                pass
        log.debug("ASIC Temps: {0}".format(temps))
        return temps

    @func_details
    def _get_cpu_temperature(self, cmd):
        """
        :param cmd:
        :return:
        Example:
        C3k
            PL24_CR> cvmtempread
            Temperature read results for CPU device (in Deg C):  +45
            PL24_CR>

        C9K
            Shannon48P_CR> BroadWellTempRead
            DTS Temp on core 0: 70C
            Shannon48P_CR>
        """
        @func_retry
        def __cputemp():
            self._clear_recbuf()
            self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('[\S].*:[ \t]*([\-+0-9]*)')
            return p.findall(self._uut_conn.recbuf)

        m = __cputemp()
        temps = {'CPU': i.strip() for i in m}
        for temp in temps:
            try:
                temps[temp] = float(temps[temp])
            except ValueError:
                pass
        log.debug("Cpu Temps: {0}".format(temps))
        return temps

    @func_details
    def _get_sbc_temperature(self, device_instance=0):
        """ Get SBC Temperature

        SAMPLE OUTPUT:
        N24Pwr_CR> sbccmd all READ_TEMPERATURE_1

         SBC Command : READ_TEMPERATURE_1
        *******************************************************
        |         SBC     |              Celsius |  Board/FRU |
        *******************************************************
        |       3.3V      |              -0.5000 |      BOARD |
        |       2.5V      |                   NA |      BOARD |
        |       1.8V      |              -0.5000 |      BOARD |
        |       1.5V      |              -0.5000 |      BOARD |
        |       1.2V      |                   NA |      BOARD |
        |       1.0V      |              -0.5000 |      BOARD |
        |       0.9V      |              -0.5000 |      BOARD |
        |   1.0V-DP0      |              38.8750 |      BOARD |
        |    1.5V-DP      |              -0.5000 |      BOARD |

        :param device_instance:
        :return:
        """
        device_instance = int(device_instance)
        if device_instance == 0:
            sbc_type = '(BOARD)|(Main Board)'
        elif 0 < device_instance < 1000:
            sbc_type = 'FRU'
        else:
            sbc_type = '.*'

        @func_retry
        def __sbctemp():
            sbc = self._ud.uut_config.get('sbc', {})
            if not sbc.get('temperature_reg', None):
                sbc['temperature_reg'] = 'READ_TEMPERATURE_2'
            self._clear_recbuf()
            self._uut_conn.send('sbccmd all {0} -f:{1}\r'.format(sbc['temperature_reg'], device_instance), expectphrase=self._uut_prompt,
                          regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('\|(.*?)\|([ \-.0-9]+|[ NAna]+)\|(.*?)\|')
            return p.findall(self._uut_conn.recbuf)

        log.debug("SBC Type = {0}".format(sbc_type))
        m = __sbctemp()
        sbc_temps = {i[0].strip(): i[1].strip() for i in m if re.search(sbc_type, i[2])} if m else {}
        for temp in sbc_temps:
            try:
                sbc_temps[temp] = float(sbc_temps[temp])
            except ValueError:
                pass
        log.debug("SBC Temperatures for {0}: {1}".format(sbc_type, sbc_temps))
        return sbc_temps

    @func_details
    def _check_temperatures(self, temperatures, limit_table, area, temp_corner, uut_state):
        """

        Reading example:
        temperatures =  {'PCB2C': {'AMBIENT': {'idle': {'Exhaust': '37.0'}}}}

        Limit Table example:
        limit_table = {
        'Exhaust':   {'PCB2C': {'AMBIENT': {'idle': 30, 'traf': 40, 'diag': 35, 'gb': 0.05},
                                'HOT':     {'idle': 30, 'traf': 40, 'diag': 35, 'gb': 0.05},
                                'COLD':    {'idle': 30, 'traf': 40, 'diag': 35, 'gb': 0.05}},
                      'PCBST': {'AMBIENT': {'idle': 30, 'traf': 40, 'diag': 35, 'gb': 0.05}},
                      'PCBFT': {'AMBIENT': {'idle': 30, 'traf': 40, 'diag': 35, 'gb': 0.05}}},

        :param (dict) temperatures:
        :param (dict) limit_table:
        :param (str) area:
        :param (str) temp_corner:
        :param (str) uut_state:
        :return:
        """
        verbose = True if self._ud.verbose_level > 1 else False
        if not limit_table:
            log.warning("No limit table for temperature. No checking.")
            return True

        if area not in temperatures:
            log.warning("TestArea ({0}) data index not available.")
            return False
        if temp_corner not in temperatures[area]:
            log.warning("Temperature corner ({0}) data index not available.")
            return False
        if uut_state not in temperatures[area][temp_corner]:
            log.warning("UUT operational state ({0}) data index not available.")
            return False

        tresults = {}

        for t_index in limit_table:
            if t_index in temperatures[area][temp_corner][uut_state]:
                if area in limit_table[t_index] and temp_corner in limit_table[t_index][area] and uut_state in \
                        limit_table[t_index][area][temp_corner]:
                    gb = float(limit_table[t_index][area][temp_corner]['gb']) if 'gb' in limit_table[t_index][area][
                        temp_corner] else 0.10
                    delta = int(limit_table[t_index][area][temp_corner]['delta']) if 'delta' in limit_table[t_index][area][
                        temp_corner] else None
                    upper_limit = round(limit_table[t_index][area][temp_corner][uut_state] * (1.0 + gb), 2)
                    lower_limit = round(limit_table[t_index][area][temp_corner][uut_state] * (1.0 - gb), 2)
                    tresults[t_index] = {'upper': upper_limit, 'lower': lower_limit,
                                         'actual': temperatures[area][temp_corner][uut_state][t_index]}
                    tresults[t_index]['status'] = True if lower_limit <= temperatures[area][temp_corner][uut_state][
                        t_index] <= upper_limit else False
                    if delta:
                        log.debug("Doppler AC Temperature: {}, Exhaust AC Temperature: {}".format(
                            temperatures[area][temp_corner][uut_state][t_index],
                            temperatures[area][temp_corner][uut_state]['Exhaust'])
                        )
                        current_dopple_delta = abs(temperatures[area][temp_corner][uut_state][t_index] - temperatures[area][temp_corner][uut_state]['Exhaust'])
                        tresults[t_index]['status'] = True if current_dopple_delta < delta else False
                else:
                    tresults[t_index] = {'upper': 'NA', 'lower': 'NA',
                                         'actual': temperatures[area][temp_corner][uut_state][t_index], 'status': True}
            else:
                tresults[t_index] = {'upper': 'NA', 'lower': 'NA', 'actual': '{0}_NOT_IN_UUT'.format(t_index),
                                     'status': True}

        log.debug("Temperature Status:")
        log.debug(" Table index: {0}|{1}|{2}".format(area, temp_corner, uut_state))
        for t in tresults:
            log.debug("{0:<20}: AC={1:<20}  UL={2:<10}  LL={3:<10}  ST={4}".format(t,
                                                                                   tresults[t]['actual'],
                                                                                   tresults[t]['upper'],
                                                                                   tresults[t]['lower'],
                                                                                   tresults[t]['status'], ))

        ret = all([tresults[i]['status'] for i in tresults])
        if not ret:
            log.debug("Temperature margins FAILED.")
        else:
            log.debug("Temperature margins PASSED.")

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Data Interface Connections
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_portstat(self, target_ports):
        """ Get Port Status

        48P_CSR> portstat
        ERR: No port has been detected as well as supported.

        USAGE: PortStatus [<port_list>] [-l:<display_level>]
            <port_list> -- Front-end ports
               Format: <port>[,<port>]*, where <port> is an integer 1..96.
               Default: all ports.
            -l:<display_level> -- Display level: 1 Summary; 2 Detail (default)

        N48P_CSR> portstat

          Port  Speed  Dplx  Crossover  Loopback  Link
          ----  -----  ----  ---------  --------  ----
             1:  1000  FULL     N/A     DISABLED   UP
             2:  1000  FULL     N/A     DISABLED   UP
             3:  1000  FULL     N/A     DISABLED   UP
             4:  1000  FULL     N/A     DISABLED   UP
             5:  1000  FULL     N/A     DISABLED   UP
             6:  1000  FULL     N/A     DISABLED   UP
             7:  1000  FULL     N/A     DISABLED   UP
             8:  1000  FULL     N/A     DISABLED   UP
             ...
            44:  1000  FULL     N/A     DISABLED   UP
            45:  1000  FULL     N/A     DISABLED   UP
            46:  1000  FULL     N/A     DISABLED   UP
            47:  1000  FULL     N/A     DISABLED   UP
            48:  1000  FULL     N/A     DISABLED   UP
            49:  1000  FULL     N/A     DISABLED   UP
            50:  1000  FULL     N/A     DISABLED   UP
            51: 10GIG  FULL     N/A     DISABLED   UP
            52: 10GIG  FULL     N/A     DISABLED   UP
            53:  1000  FULL     N/A     DISABLED   UP
            54:  1000  FULL     N/A     DISABLED   UP
            55: 10GIG  FULL     N/A     DISABLED   UP
            56: 10GIG  FULL     N/A     DISABLED   UP

        Hartley48U> PortStat

          Port  Speed  Dplx  Crossover  Loopback  Link
          ----  -----  ----  ---------  --------  ----
             1:  2.5G  FULL     MDIX    DISABLED   UP
             2:  2.5G  FULL     MDI     DISABLED   UP
             3:  2.5G  FULL     MDIX    DISABLED   UP
             4:  2.5G  FULL     MDI     DISABLED   UP
             5:  2.5G  FULL     MDIX    DISABLED   UP
             6:  2.5G  FULL     MDI     DISABLED   UP
             7:  2.5G  FULL     MDIX    DISABLED   UP
             8:  2.5G  FULL     MDI     DISABLED   UP
             9:  2.5G  FULL     MDIX    DISABLED   UP
            10:  2.5G  FULL     MDI     DISABLED   UP
            11:  2.5G  FULL     MDIX    DISABLED   UP
            12:  2.5G  FULL     MDI     DISABLED   UP
            13:  2.5G  FULL     MDIX    DISABLED   UP
            14:  2.5G  FULL     MDI     DISABLED   UP
            15:  2.5G  FULL     MDIX    DISABLED   UP
            16:  2.5G  FULL     MDI     DISABLED   UP
            17:  2.5G  FULL     MDIX    DISABLED   UP
            18:  2.5G  FULL     MDI     DISABLED   UP
            19:  2.5G  FULL     MDI     DISABLED   UP
            20:  2.5G  FULL     MDIX    DISABLED   UP
            21:  2.5G  FULL     MDIX    DISABLED   UP
            22:  2.5G  FULL     MDI     DISABLED   UP
            23:  2.5G  FULL     MDIX    DISABLED   UP
            24:  2.5G  FULL     MDI     DISABLED   UP
            25:  2.5G  FULL     MDIX    DISABLED   UP
            26:  2.5G  FULL     MDI     DISABLED   UP
            27:  2.5G  FULL     MDIX    DISABLED   UP
            28:  2.5G  FULL     MDI     DISABLED   UP
            29:  2.5G  FULL     MDIX    DISABLED   UP
            30:  2.5G  FULL     MDI     DISABLED   UP
            31:  2.5G  FULL     MDIX    DISABLED   UP
            32:  2.5G  FULL     MDI     DISABLED   UP
            33:  2.5G  FULL     MDIX    DISABLED   UP
            34:  2.5G  FULL     MDIX    DISABLED   UP
            35:  2.5G  FULL     MDI     DISABLED   UP
            36:  2.5G  FULL     MDI     DISABLED   UP
            37: 10GIG  FULL     MDIX    DISABLED   UP
            38: 10GIG  FULL     MDI     DISABLED   UP
            39: 10GIG  FULL     MDIX    DISABLED   UP
            40: 10GIG  FULL     MDI     DISABLED   UP
            41: 10GIG  FULL     MDI     DISABLED   UP
            42: 10GIG  FULL     MDIX    DISABLED   UP
            43: 10GIG  FULL     MDIX    DISABLED   UP
            44: 10GIG  FULL     MDI     DISABLED   UP
            45: 10GIG  FULL     MDI     DISABLED   UP
            46: 10GIG  FULL     MDIX    DISABLED   UP
            47: 10GIG  FULL     MDI     DISABLED   UP
            48: 10GIG  FULL     MDIX    DISABLED   UP
            49: 10GIG  FULL     N/A     DISABLED   UP
            50: 10GIG  FULL     N/A     DISABLED   UP
            51: 10GIG  FULL     N/A     DISABLED   UP
            52: 10GIG  FULL     N/A     DISABLED   UP
            53: 10GIG  FULL     N/A     DISABLED   UP
            54: 10GIG  FULL     N/A     DISABLED   UP
            55: 10GIG  FULL     N/A     DISABLED   UP
            56: 10GIG  FULL     N/A     DISABLED   UP
            57:  1000  FULL     N/A     DISABLED   UP
            58: 10GIG  FULL     N/A     DISABLED   UP

        :return:
        """

        # @func_retry
        def __portstat():
            self._clear_recbuf()
            # p = re.compile(
            #     '(?m)^[ \t]*([\d]+):[ \t]*([0-9A-Za-z]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*')
            p = re.compile('(?m)^[ \t]*([\d]+):[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*([\S]+)[ \t]*')
            self._uut_conn.send('PortStat{0}\r'.format(args), expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            if 'ERR' in self._uut_conn.recbuf:
                err_target_ports = [True if e in self._uut_conn.recbuf else False for e in err_filter]
                if any(err_target_ports):
                    log.error(self._uut_conn.recbuf)
                    return None
                else:
                    log.warning("ERR found; however, NO Target Port Errors.")
                    log.warning("Portstatus ERR may be ignored; please confirm this is valid.")
            _m = p.findall(self._uut_conn.recbuf)
            return _m

        PortStat = namedtuple('PortStat', 'Speed Duplex Crossover Loopback Link')
        log.debug("Prompt={0}".format(self._uut_prompt))
        err_filter = ["Port/{0} ".format(p) for p in target_ports]
        args = ' {0}'.format(','.join([str(p) for p in target_ports])) if target_ports else ''
        args += ' -slot:{0}'.format(self._ud.physical_slot) if self._ud.physical_slot else ''

        m = __portstat()
        d = {int(m[i][0]): PortStat(m[i][1], m[i][2], m[i][3], m[i][4], m[i][5]) for i in xrange(len(m))} if m else {}

        return d

    @func_details
    def _check_portstat(self, current_portdata, target_ports=None):
        """ Check Port Status

        Data Sample format:
        1: PortStat(Speed='1000', Duplex='FULL', Crossover='N/A', Loopback='DISABLED', Link='UP'),
        2: PortStat(Speed='1000', Duplex='FULL', Crossover='N/A', Loopback='DISABLED', Link='UP'),
        3: PortStat(Speed='1000', Duplex='FULL', Crossover='N/A', Loopback='DISABLED', Link='UP'),
        ...

        :param (dict) current_portdata: see sample above; format = {<port>: <named tuple>, ...}
        :param (list) target_ports: format = [<port1>, <port2>, ...] where <portX> is an int
        :return: True if all ports are UP,  ratio of unlinked/total ports (0.0 = All UP, 1.0 = All DOWN)
        """
        if not current_portdata:
            log.warning("No port data to check.")
            return False
        current_ports = current_portdata.keys()
        log.debug("Current ports (detect) : {0}".format(current_ports))

        if not target_ports:
            target_ports = sorted(current_portdata.keys())
        log.debug("Target ports (input)   : {0}".format(target_ports))

        target_ports_final = sorted(list(set(current_ports) & set(target_ports)))
        excluded_current_ports = sorted(list(set(current_ports) - set(target_ports)))
        log.debug("Target ports (final)   : {0}".format(target_ports_final))
        log.debug("Excluded current ports : {0}".format(excluded_current_ports))
        error_list = []
        for port in target_ports_final:
            if current_portdata[port].Link != 'UP':
                error_list.append(port)
                log.error("Port {0} link is {1} !".format(port, current_portdata[port].Link))

        unlinked_ports = len(error_list)
        total_ports = len(target_ports_final)
        log.debug("Total Current Ports   = {0}".format(len(current_ports)))
        log.debug("Target Ports          = {0}".format(total_ports))
        log.debug("Target Ports Linked   = {0}".format(total_ports - unlinked_ports))
        log.debug("Target Ports Unlinked = {0}".format(unlinked_ports))

        ratio = round(float(unlinked_ports) / total_ports, 2) if total_ports > 0 else 0

        ret = True if unlinked_ports == 0 and total_ports != 0 else False
        if ret:
            log.debug("Port Status - All target ports have a link.")
        else:
            if total_ports == 0:
                log.error("Problem with target ports input or port status detection.")
                log.error("Check diags and product definition.")
            elif unlinked_ports == total_ports:
                log.warning("ALL target ports are not linked!")
                log.warning("The unit may not have loopbacks.")
            else:
                log.error("Some target ports are not linked.")
        return ret, ratio

    @func_details
    def _get_stackdata(self):
        """Get StackData

        NOTE: The GEN3 table has an extra column which will be ignored.

        Examples:
        GEN2
        N48U_CSR> stackrac
        asic#  ring#  active  avail  linkOk  syncOk  pcsAlignOk
        ========================================================
        0      0       1      1       1       1        1
        0      1       1      1       1       1        1
        0      2       1      1       1       1        1
        0      3       1      1       1       1        1
        0      4       1      1       1       1        1
        0      5       1      1       1       1        1
        1      0       1      1       1       1        1
        1      1       1      1       1       1        1
        1      2       1      1       1       1        1
        1      3       1      1       1       1        1
        1      4       1      1       1       1        1
        1      5       1      1       1       1        1

        GEN3
        Shannon24U> StackRAC
        asic/group  ring#  active  avail  linkOk  syncOk  pcsAlignOk  wrapped
        ======================================================================
            0/0      0       1      1       1       1        1           0
            0/0      1       1      1       1       1        1           0
            0/0      2       1      1       1       1        1           0
            0/0      3       1      1       1       1        1           0
            0/0      4       1      1       1       1        1           0
            0/0      5       1      1       1       1        1           0
            0/1      0       1      1       1       1        1           0
            0/1      1       1      1       1       1        1           0
            0/1      2       1      1       1       1        1           0
            0/1      3       1      1       1       1        1           0
            0/1      4       1      1       1       1        1           0
            0/1      5       1      1       1       1        1           0

        :return:
        """

        @func_retry
        def __stackrac():
            self._clear_recbuf()
            p = re.compile(
                '(?m)^[ \t]*([\S]+)[ \t]*([\d]+)[ \t]*([\d]+)[ \t]*([\d]+)'
                '[ \t]*([\d]+)[ \t]*([\d]+)[ \t]*([\d]+)[ \t]*')
            self._uut_conn.send('StackRAC\r', expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            return p.findall(self._uut_conn.recbuf)

        m = __stackrac()
        d = {(m[i][0], int(m[i][1])): (int(m[i][2]), int(m[i][3]), int(m[i][4]), int(m[i][5]), int(m[i][6])) for i in
             xrange(len(m))} if m else {}
        return d

    @func_details
    def _check_stackdata(self, current_stackdata):
        """Check StackData

        See the "self._get_stackdata(...)" function for examples.

        :param current_stackdata:
        :return:
        """

        # Check stackdata
        result_list = []
        for asic_ring in sorted(current_stackdata.keys()):
            result = all(current_stackdata[asic_ring])
            result_list.append(result)
            if not result:
                log.error("ASIC-Ring {0}: FAILED = {1}".format(asic_ring, current_stackdata[asic_ring]))
            else:
                log.debug("ASIC-Ring {0}: PASSED".format(asic_ring))

        return all(result_list)

    # ------------------------------------------------------------------------------------------------------------------
    # FPGA
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _upgrade_fpga(self, images, dual=False, timeout=200, **kwargs):
        """ Upgrade FPGA

        Example #1 single:
        -----------------

        PL24_CR> FpgaUpgradeImage morseG_01_00_A0.hex -p:0
        Writing new FPGA configuration.
        Erasing FPGA sector 0
        Finished erasing FPGA sector 0
        ...............................................................
        <blah, blah, blah>
        Finished erasing FPGA sector 3
        ...............................................................
        Total bytes written: 262144
        Verifying...
        ...............................................................
        FPGA Image upgrade successful.


        EXAMPLE #2 dual:
        ----------------
        Afterwit24QU> FpgaDualImageUpgrade bifocal_01_00_05162018_mb_gld.hex golden -p:0
        Writing new FPGA configuration.

        Erasing FPGA sector 0
        Finished erasing FPGA sector 0
        ..................
        Erasing FPGA sector 1
        Finished erasing FPGA sector 1
        ..................
        Erasing FPGA sector 2
        Finished erasing FPGA sector 2
        ..................
        Erasing FPGA sector 3
        Finished erasing FPGA sector 3
        Total bytes written: 1048576
        Verifying...
        ..................
        FPGA Image upgrade successful.


        Afterwit24QU> FpgaDualImageUpgrade bifocal_01_03_06282018_mb_upg.hex upgrade -p:1
        Writing new FPGA configuration.

        Erasing FPGA sector 16
        Finished erasing FPGA sector 16
        ..................
        Erasing FPGA sector 17
        Finished erasing FPGA sector 17
        ..................
        Erasing FPGA sector 18
        Total bytes written: 1048576
        Verifying...
        ..................
        FPGA Image upgrade successful.

        :param (str|list) images:
        :param (bool) dual:  True if there is a dual location for FPGA.
        :param (int) timeout:
        :return:
        """

        # Input
        images = [images] if not isinstance(images, list) else images
        enabled = kwargs.get('enabled', True)

        if not enabled:
            log.debug("FPGA upgrade disabled.")
            return aplib.DISABLED

        self._clear_recbuf()
        self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Check that files exists
        files = self.get_device_files(attrib_flags='-')
        if not files:
            log.warning("No files available in expected flash location.")
            return False

        # Check that the image(s) is/are available from flash files
        if not all([True if image in files else False for image in images]):
            log.warning("Required FPGA file(s) is/are not in expected flash location.")
            log.debug("Attempting image(s) loading: {0} ...".format(images))

            if not self._mode_mgr:
                log.warning("FPGA Upgrade not possible.  Must have methods for mode operation.")
                return False
            if not self._ud:
                log.warning("FPGA Upgrade not possible.  Must have a UUT descriptor.")
                return False

            server_ip = self._ud.uut_config.get('server_ip', None)
            netmask = self._ud.uut_config.get('netmask', None)
            uut_ip = self._ud.uut_config.get('uut_ip', None)
            uut_linux_prompt = self._ud.uut_config.get('uut_prompt_map', {}).get('LINUX', '# ')
            if not all([server_ip, uut_ip, netmask]):
                log.error("Image load not possible; network params are absent.")
                return False

            if not self._mode_mgr.goto_mode('LINUX'):
                log.error("Cannot get into LINUX mode for FPGA download.")
                return False

            result = self._linux.transfer_tftp_files(src_files=images,
                                                      dst_files=images,
                                                      direction='get',
                                                      server_ip=server_ip, ip=uut_ip, netmask=netmask, force=True)

            self._mode_mgr.goto_mode('STARDUST')

            if not result:
                log.debug("FPGA Image load: FAILED.")
                return result
            else:
                log.debug("FPGA Image load: PASSED.")

        # Determine generation command and FPGA type
        fpga_type = {1: ('', ''), 2: ('', '')}
        fpga_cmd = 'FpgaUpgradeImage'

        if dual:
            log.debug("Dual FPGA image upgrade indicated.")
            fpga_type = {1: ('golden', 'mb_gld'), 2: ('upgrade', 'mb_upg')}
            fpga_cmd = 'FpgaDualImageUpgrade'

        # Do the upgrade
        log.debug("FPGA upgrade image(s) available: {0}.".format(images))
        result_list = []
        fpga_sector = 0
        for i, image in enumerate(images, 1):

            # Match check for dual images
            if fpga_type[i][1] and fpga_type[i][1] not in image:
                    track = fpga_type[i][0]
                    log.error("FPGA image mismatch with FPGA type: {0} --> {1}".format(image, fpga_type[i][0]))
                    log.error("Please check the product definition for proper file names and order. Cannot upgrade.")
                    return False

            log.debug("{0}. Upgrading FPGA '{1}': '{2}' ...".format(i, fpga_type[i][0], image))
            self._uut_conn.send('{0} {1} {2} -p:0\r'.format(fpga_cmd, image, fpga_type[i][0]),
                          expectphrase='(?:Writing new)|(?:.*)',
                          timeout=30,
                          regex=True)

            # Loop to deal with the console status updates
            loop_count = 0
            ret = False
            end_pattern = '(?:upgrade successful)|{0}'.format(self._uut_prompt)
            while not ret and loop_count < 1000:
                active_pattern = '(?:FPGA sector {0})|{1}'.format(fpga_sector, end_pattern)
                self._uut_conn.waitfor(active_pattern, timeout=timeout, regex=True)
                # Pattern found in output; do something.
                if re.search('(?:FPGA)', self._uut_conn.recbuf):
                    log.debug("FPGA Programming (sector {0}) ...".format(fpga_sector))
                if re.search('upgrade successful', self._uut_conn.recbuf):
                    log.debug('Successful programming!')
                    ret = True
                if re.search('(?i)Err', self._uut_conn.recbuf):
                    log.debug('Error.')
                    break
                if re.search('Total bytes written:', self._uut_conn.recbuf):
                    m = re.search('Total bytes written: ([0-9]+)', self._uut_conn.recbuf)
                    bytes_written = m.group(0) if m and m.group(0) else 0
                    log.info("Bytes written = {0}".format(bytes_written))
                if re.search(self._uut_prompt, self._uut_conn.recbuf):
                    log.debug('Done.')
                    break
                loop_count += 1
                fpga_sector += 1
                time.sleep(1.0)
            result_list.append(ret)

        return all(result_list)

    @func_details
    def _check_fpga(self, name, revision, register='FpgaRevision'):
        """ Check FPGA Revision
        :param name: FPGA name
        :param revision: Revision number (hex) given by the FPGA register
        :param register: Name of register associated with the revision
        :return: tuple of (version_good/bad, operational_error)
        """
        fpga_data = self._read_fpga(name=name)
        if register not in fpga_data:
            log.error("Missing FPGA data.  Check the name.")
            return False, True

        if fpga_data[register].lower() == revision.lower():
            log.info("FPGA {0} Rev={1} is GOOD.".format(name, fpga_data[register]))
            return True, False
        elif fpga_data[register].lower() > revision.lower():
            log.warning("FPGA {0} Rev={1} is NEWER than expected Rev={2}.!".format(name, fpga_data[register], revision))
            log.warning("FPGA downgrade is not necessary.")
            return True, False
        else:
            log.warning(
                "FPGA {0} Rev={1} is OLDER/MISMATCHED to expected Rev={2}.".format(name, fpga_data[register], revision))
            return False, False

    @func_details
    def _read_fpga(self, name):
        """ Read FPGA
        Example:
        PL24_CR> rd morse
        SystemRegs.Morse/0 (base @ 0x00000000.10000000):
        Offset                                Value  RegisterName
        ------  -----------------------------------  ----------------------------------
        000000                                 4005  BoardId
        010000                                 010a  FpgaRevision
        020000                                 0060  ResetControl1
        030000                                 0000  ResetControl2
        040000                                 0307  SBCEnable

        :param name: FPGA name
        :return:
        """

        @func_retry
        def __fpgard():
            self._clear_recbuf()
            self._uut_conn.send('rd {0}\r'.format(name), expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('[\t ]*[0-9a-fA-F]{5,8}[\t ]*([0-9a-fA-F]{4,8})[\t ]+([\S]+)')
            return p.findall(self._uut_conn.recbuf)

        m = __fpgard()
        f_data = {i[1]: i[0] for i in m} if m else {}
        return f_data

    @func_details
    def _get_fpga_name(self):
        """ Get FPGA Name
        Either derive the name from the image name (checked against known names) OR
        use the name given (checked against known names also).
        fpga image and fpga name(optional) are contained in the product_definitions.
        :param uut_config:
        :return:
        """
        if 'fpga' not in self._ud.uut_config:
            log.error("No FPGA data dict in the uut_config! Check the product_definitions.")
            return None

        fpga_name = self._ud.uut_config.get('fpga', {}).get('name', None)
        fpga_image = self._ud.uut_config.get('fpga', {}).get('image', None)

        if not fpga_name:
            if not fpga_image:
                log.error("No identifying FPGA data to determine name. Check the product_definition.")
                return None
            else:
                log.debug("Checking FPGA name against image name ({0})...".format(fpga_image))
                for fpga_name in self.FPGA_NAMES:
                    if fpga_name in fpga_image.lower():
                        log.debug("FPGA name (inferred) = {0}".format(fpga_name))
                        break
                else:
                    log.error("FPGA image does not contain any known names. Check the product_definition.")
                    return None
        else:
            log.debug("FPGA name = {0}".format(fpga_name))
            if fpga_name.lower() not in self.FPGA_NAMES:
                log.error("FPGA name does not match any known names. Check the product_definition.")
                return None

        return fpga_name

    # ------------------------------------------------------------------------------------------------------------------
    # SBC
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _run_sbc_batch(self, sbc_image, begin_label, home_dir=None, timeout=400):
        """ Run SBC Batch
        :param sbc_image:
        :param begin_label:
        :param home_dir:
        :param timeout:
        :return:
        """

        if not self._ud.uut_config.get('sbc', {}).get('enable', False):
            log.debug("SBC feature not enabled for this product.")
            log.debug("No SBC batch run available.")
            return True

        if not sbc_image:
            log.error("No SBC image provided.")
            return False

        self._uut_conn.send('pwd\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        log.info("SBC: {0} START.".format(begin_label))

        # Execute
        if not self.run_batch_file(batch_image=sbc_image,
                                   begin_label=begin_label,
                                   home_dir=home_dir,
                                   timeout=timeout):
            log.error("SBC: {0} encountered a batch execution problem.".format(begin_label))
            return False

        log.info("SBC: {0} DONE.".format(begin_label))

        return True

    @func_details
    def _get_sbc_mfrid(self, device_instance=0):
        """ Get SBC Mfr ID's

        SAMPLE OUTPUT:
        N24Pwr_CR> sbccmd all MFR_ID -f:0

         SBC Command : MFR_ID
        *******************************************************
        |         SBC     |                ASCII |  Board/FRU |
        *******************************************************
        |       3.3V      |                   TI |      BOARD |
        |       2.5V      |                      |      BOARD |
        |       1.8V      |                   TI |      BOARD |
        |       1.5V      |                   TI |      BOARD |
        |       1.2V      |                      |      BOARD |
        |       1.0V      |                   TI |      BOARD |
        |       0.9V      |                   TI |      BOARD |
        |   1.0V-DP0      |            BEL-POWER |      BOARD |
        |    1.5V-DP      |                   TI |      BOARD |

        :param device_instance:
        :return:
        """
        if not self._ud.uut_config.get('sbc', {}).get('enable', False):
            log.debug("SBC feature not enabled for this product.")
            log.debug("No SBC MfgrIDs available.")
            return []

        device_instance = int(device_instance)
        if device_instance == 0:
            sbc_type = '(BOARD)|(Main Board)'
        elif device_instance > 0:
            sbc_type = 'FRU'
        else:
            sbc_type = '.*'

        @func_retry
        def __sbcid():
            self._clear_recbuf()
            self._uut_conn.send('sbccmd all MFR_ID -f:{0}\r'.format(device_instance), expectphrase=self._uut_prompt, regex=True,
                          timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('\|(.*?)\|(.*?)\|(.*?)\|')
            return p.findall(self._uut_conn.recbuf)

        m = __sbcid()
        sbc_list = [i[0].strip() for i in m if re.search(sbc_type, i[2])] if m else []
        log.debug("SBC {0} List: {1}".format(sbc_type, sbc_list))
        return sbc_list

    # ------------------------------------------------------------------------------------------------------------------
    # PoE
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _set_poe_on(self, poe_type, active_poe_ports):
        self._equip.poe_loadbox.connect(detect_signature='ok', external='on', auto='on')
        time.sleep(2.0)
        self._operate_poe_uut(action='ON', poe_type=poe_type, poe_ports=active_poe_ports)
        time.sleep(1.0)
        self._equip.poe_loadbox.set_power_load()
        time.sleep(5.0)
        return

    @func_details
    def _set_poe_off(self, poe_type, active_poe_ports):
        self._operate_poe_uut(action='OFF', poe_type=poe_type, poe_ports=active_poe_ports)
        self._equip.poe_loadbox.disconnect()
        return

    @func_details
    def _operate_poe_uut(self, action, poe_type=None, poe_params=None, poe_ports=None):
        """ Operate PoE functions on UUT

        A single function for operating on the UUT to perform PoE functions under various conditions or test scenarios.
        Includes a) 'CFG'        = configure PoE prior to load testing or traffic runs,
                 b) 'BUDGET'     = determine the power budget available for poe based on PSU(s) installed and PoE type,
                 c) 'GETPWR'     = read PoE power on ports from UUT
                 c) 'GETREG'     = read poe controller registers for poe specific data,
                 d) 'ON'         = turn on poe power,
                 e) 'OFF'        = turn off poe power

        SetParam command (DIAG mode only):
        USAGE: Setparam <name> <param_id> <param_value | -v:<param_value> | -u>
            <name> -- A string: name of the section or individual test.
            <param_id> -- A string: test parameter name.
            <param_value> -- A value to be set to the specified test parameter.
            -v:<param_value> -- A value to be set to the specified test parameter.
            -u -- Unsetting the param_id (revert back to default setting).

        Alchemy command:
        USAGE: Alchemy <command> [-a:<alchemy_list> | -c:<ctrlr_list> | -p:<port_list>]
          [-reg:<reg> | -regvalue:<reg_value>]
          [-action:<action> | -icutoff:<icutoff>]
          [-icutcode:<icutcode>] [-dutycycle:<dutycycle>]
          [-v1:data1] [-v2:data2]      [-upoe]
        <command> -- Specify Alchemy Command.
            <cmd>[|<cmd>]...,
            <cmd> are POESHUT | POEAUTO | POEAPPROVE | POEREJECT |
                      POEPOWER | POEEVENTS | POESETICUT |
                      POEBASICREGS | POEEXTREGS | POESETREG |
                      POESETPOWERPOLICE | POEGETPOWERSENSE | POEPRIORITY |
                      THERMSPEED | THERMEVENT | THERMREADADC |
                      GPIOPORTLED | GPIOOUT | GPIOIN | GPIOADC |
                      GPIOSETVOLTMARGIN |
                      SYSRESET | SYSSYNC | SYSEVENTS | SYSINTR |
                      SWBREAK | SWSEQ | SWBREAKSEQ | HWRESET | VERSION |
                      APPVERCHECK | BLVERCHECK | SN (serial#) | PN (part#) |
                      STATDUMP | STATCLEAR |
                      PDPSEGETPWRSRC | PDPSEREADPORT | PDPSEWRITEPORT |
                      PDPSESETPDTYPE | PDPSESETLOADSHED | PDPSESETILIM |
                      PDPSEGETILIM | PDPSESETDAC | PDPSEGETDAC |
                      PDPSEGETTEMP | PDPSESETILIMPERC | PDPSESETDACPERC

        -a:<alchemy_list> -- Format: <alchemy>[,<alchemy>]*, where <alchemy> is integer >= 0
        -c:<poectrlr_list> -- Format: <ctrlr>[,<ctrlr>]*, where <ctrlr> is integer >= 0
        -p:<port_list> -- Format: <port>[,<port>]*, where <port> is integer >= 0
        -reg:<poectrlr_set_register> -- An integer (0..255)
        -regvalue:<poectrlr_set_registervalue> -- An integer (0..255)
        -action:<poectrlr_set_action> -- An integer (0..3)
        -icutoff:<poectrlr_set_icutoff> -- Cutoff current in mA (0..65535)
        -icutcode:<poectrlr_set_icutcode> -- Cutoff current code (0..7)
        -dutycycle:<poectrlr_dutycycle> -- ILIM Duty Cycle (1..1023)
        -v1:<Parameter #1> -- Parameter 1 (valid for some commands)
        -v2:<Parameter #2> -- Parameter 2 (valid for some commands)
        -upoe -- Apply to spare pair for UPOE (valid for some POE commands)

        Samples:
        Diag> alchemy POEGET
             Alchemy 0:    V(left) = N/A,  V(right) = N/A
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
            -------------------------------------------------------------
               1       --           --
               ...
              12       --           --

             Alchemy 1:    V(left) = N/A,  V(right) = N/A
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
            -------------------------------------------------------------
              13       --           --
              ...
              24       --           --

        Diag> alchemy POEGET
             Alchemy 0:    V(left) = 55.945V,  V(right) = 55.816V
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
            -------------------------------------------------------------
               1      PWRG          --              96           5.3
               ...
              12      PWRG          --             104           5.8


             Alchemy 1:    V(left) = 55.945V,  V(right) = 56.009V
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
            -------------------------------------------------------------
              13      PWRG          --             103           5.7
              ...
              24      PWRG          --             100           5.5

        Diag> alchemy POEGET -upoe
             Alchemy 0:  (Primary/Spare)                (Primary/Spare)
                V(left) =   N/A  /  N/A,      V(right) =   N/A  /  N/A
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
                   (Pri/Spare)                 (Pri/Spare)    (Pri/Spare)
            -------------------------------------------------------------
               1      PWRG/PWRG          --     96/97           5.3/5.4
               ...
              12      PWRG/PWRG          --     104/105         5.8/5.6

             Alchemy 1:  (Primary/Spare)                (Primary/Spare)
                V(left) =   N/A  /  N/A,      V(right) =   N/A  /  N/A
             Port   PWR Sense    PWR Police    Current(mA)     Power(W)
                   (Pri/Spare)                 (Pri/Spare)    (Pri/Spare)
            -------------------------------------------------------------
              13      --/--           --
              ...
              24      --/--           --
        Diag>

        Diag> alchemy POEEVENTS
            #    Port Event            Device Event    VEE VDD TMP OSC
            00   PGood SparePair (06)
            01   PGood SparePair (06)
            02   PGood SparePair (06)
            03   PGood SparePair (06)
            04   PGood SparePair (06)
            05   PGood SparePair (06)
            06   PGood SparePair (06)
            07   PGood SparePair (06)
            08   PGood SparePair (06)
            09   PGood SparePair (06)
            10   PGood SparePair (06)
            11   PGood SparePair (06)


        Samples:
            Traf> Alchemy POEBASICREGS
            Reg: 0x00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B
            -------------------------------------------------------------------------------------------
            ctrl/00 00 f6 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0f 00 f0 c0 80 00 00 10 1b
            ctrl/01 00 f6 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04 00 0f 00 f0 c0 80 00 00 10 1b
            ...
            ctrl/22 00 f6 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 28 00 0f 00 f0 c0 80 00 00 10 1b
            ctrl/23 00 f6 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 2c 00 0f 00 f0 c0 80 00 00 10 1b


            Traf> Alchemy POEEXTREGS
             Reg: 0x1E 1F 23 24 25 2A 2B 2C 2D 2E 2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45 46 47 48 75
            ----------------------------------------------------------------------------------------------------------------------
            ctrl/00 aa aa 00 00 00 00 00 a8 00 69 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 f0 09 16 60 00 00 00 00 00 aa
            ctrl/01 aa aa 00 00 00 00 00 a8 00 69 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 f0 09 16 60 00 00 00 00 00 aa
            ...
            ctrl/22 aa aa 00 00 00 00 00 aa 00 65 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 f0 09 16 60 00 00 00 00 00 aa
            ctrl/23 aa aa 00 00 00 00 00 aa 00 65 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 f0 09 16 60 00 00 00 00 00 aa


        Traf command:
        USAGE: PwrConfPort [<port list>] [-power:<power>] [-disc:<disconnects>] [-upoe:<power>]
        <port_list> -- Format: <port>[,<port>]*, where <port> is integer > 0
        -power:<power> -- port power: ON|OFF
        -disc:<disconnects> -- Set port power disconnect type.
            <disconnect>[|<disconnect>]...,
            <disconnect> is AC|DC|LINK|ALL
        -upoe:<upoe> -- Spare Pair for UPOE: ON|OFF

        Parameters for PoePowerTest (POE Power-up Test):
           PowerHoldTime       : 120000  (1000 - 120000)  (default 120000)  (Time to exercise/hold power in mS)
           DisconnectType      : 1  (0 - 2)  (default 1)                    (0:Skip  1:DC  2:AC)
           DisconnectTimeout   : 60000  (1000 - 60000)  (default 60000)     (Time in mS)
           PowerOnSetupTimeout : 30000  (1000 - 30000)  (default 30000)     (Time to wait for power on confirmation - in mS)
           VEEVoltageSkipTest  : 1  (0 - 1)  (default 1)                    (1: skip this test, 0: run it)
           VEEVoltageThreshold : 20  (1 - 20)  (default 20)                 (Max VEE drift. 1=0.1,2=0.2, ... ,10=1.0, ... ,20=2.0)
           Verbosity           : 3  (0 - 5)  (default 3)
           MaxError            : 0  (0 - 2147483647)  (default 0)
           TestRunCnt          : 1  (0 - 65535)  (default 1)

        :param (str) action: Choice of 'CFG', 'BUDGET', 'GETPWR','ON', 'OFF'
        :param (str) poe_type: Choice of 'POE', 'POE+', 'UPOE'
        :param (dict) poe_params:  The uut_config['poe'] dict containing configuration data (source is product definition)
        :param (str) poe_ports: Ex.A. '1-12' or '1,2,3,4,5,6,7,8,9,10,11,12'
        :return:
        """
        # Put ports in a standard form
        poe_ports_list = common_utils.expand_comma_dash_num_list(poe_ports)
        poe_ports_list_z = [i - 1 for i in poe_ports_list]
        poe_ports = str(poe_ports_list).replace(' ', '')[1:-1]
        poe_ports_z = str(poe_ports_list_z).replace(' ', '')[1:-1]

        # Set params
        poe_params = {} if not poe_params else poe_params
        port_param_z = '-p:{0}'.format(poe_ports_z) if poe_ports_z else ''
        upoe_param = '-upoe' if poe_type == 'UPOE' else ''

        log.debug("PoE Params = {0}".format(poe_params))
        if action == 'CFG':
            # Must be in 'DIAG' mode only!
            # Optional
            #   Note: The param MUST be specified; otherwise diag default will be used (param default is for info only).

            # PoeDetTest
            # ----------
            if poe_params.get('detecttimeout', None):
                self._uut_conn.send("SetParam PoeDetTest DetectTimeout {0}\r".format(poe_params.get('detecttimeout', 10000)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('detecttype', None):
                self._uut_conn.send("SetParam PoeDetTest DetectType {0}\r".format(poe_params.get('detecttype', 1)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('mdimode', None):
                self._uut_conn.send("SetParam PoeDetTest MDIMode {0}\r".format(poe_params.get('mdimode', 0)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)

            # PoeClassTest
            # ------------
            if poe_params.get('classtimeout', None):
                self._uut_conn.send("SetParam PoeClassTest ClassTimeout {0}\r".format(poe_params.get('classtimeout', 20000)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('classtype', None):
                self._uut_conn.send("SetParam PoeClassTest ClassType {0}\r".format(poe_params.get('classtype', 0)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)

            # PoePowerTest
            # ------------
            if poe_params.get('powerholdtime', None):
                self._uut_conn.send(
                    "SetParam PoePowerTest PowerHoldTime {0}\r".format(poe_params.get('powerholdtime', 120000)),
                    expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('disconnecttimeout', None):
                self._uut_conn.send(
                    "SetParam PoePowerTest DisconnectTimeout {0}\r".format(poe_params.get('disconnecttimeout', 60000)),
                    expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('poweronsetuptimeout', None):
                self._uut_conn.send("SetParam PoePowerTest PowerOnSetupTimeout {0}\r".format(
                    poe_params.get('poweronsetuptimeout', 30000)), expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('disconnecttype', None):
                self._uut_conn.send("SetParam PoePowerTest DisconnectType {0}\r".format(poe_params.get('disconnecttype', 1)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)

            # PoE
            # ---
            if poe_params.get('testallports', None):
                self._uut_conn.send("SetParam POE TestAllPorts {0}\r".format(poe_params.get('testallports', 1)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('portgroupsize', None):
                self._uut_conn.send("SetParam POE PortGroupSize {0}\r".format(poe_params.get('portgroupsize', 24)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            if poe_params.get('portnum', None):
                self._uut_conn.send("SetParam POE PortNum {0}\r".format(poe_params.get('portnum', 1)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            # PoE Type
            # --------
            if poe_type == 'UPOE':
                self._uut_conn.send("SetParam POE upoe 1\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            else:
                self._uut_conn.send("SetParam POE upoe 0\r", expectphrase=self._uut_prompt, timeout=30, regex=True)

            # Forced
            self._uut_conn.send("SetParam POE PDPresent {0}\r".format(poe_params.get('pdpresent', 1)),
                          expectphrase=self._uut_prompt, timeout=30, regex=True)

        elif action == 'BUDGET':
            return self._calc_poe_power_budget(poe_type, poe_ports)

        elif action == 'GETPWR':
            if upoe_param:
                pattern = '(?m)^[ \t]*([\d]+)[ \t]+([A-Z]+)/([A-Z]+)[ \t]+.*?[ \t]+([\d.]+)/([\d.]+)[ \t]+([\d.]+)/([\d.]+)'
            else:
                pattern = '(?m)^[ \t]*([\d]+)[ \t]+([A-Z]+)[ \t]+.*?[ \t]+([\d.]+)[ \t]+([\d.]+)'
            p = re.compile(pattern)
            self._clear_recbuf()
            self._uut_conn.send("Alchemy POEGET {0}\r".format(upoe_param), expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m = p.findall(self._uut_conn.recbuf)
            if m:
                # Ex. [('1', 'PWRG', '96', '5.3'), ('12', 'PWRG', '104', '5.8'), ...]
                # Ex. [('1', 'PWRG', 'PWRG', '96', '97', '5.3', '5.4'), ... ('12', 'PWRG', 'PWRG', '104', '105', '5.8', '5.6')]
                d = {item[0]: item[1:] for item in m}
                # {'1': ('PWRG', 'PWRG', '96', '97', '5.3', '5.4'), ... '12': ('PWRG', 'PWRG', '104', '105', '5.8', '5.6')}
                log.debug("UUT POE Power data retrieved.")
                for i in d:
                    log.debug("{0} : {1}".format(i, d[i]))
                return d
            else:
                log.debug("No UUT POE Power data available.")
                return {}

        elif action == 'GETREG':
            p = re.compile('(?m)^[ \t]*([\S]+/[0-9]+) (.*)[ \t\r\n]+')
            self._clear_recbuf()
            self._uut_conn.send("Alchemy POEBASICREGS\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m1 = p.findall(self._uut_conn.recbuf)
            self._clear_recbuf()
            self._uut_conn.send("Alchemy POEEXTREGS\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m2 = p.findall(self._uut_conn.recbuf)
            return dict(POEBASICREGS=dict(m1), POEEXTREGS=dict(m2))

        elif action == 'EVENTS':
            p = re.compile('(?m)^[ \t]*([\S]+/[0-9]+) (.*)[ \t\r\n]+')
            self._clear_recbuf()
            self._uut_conn.send("Alchemy POEEVENTS\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m1 = p.findall(self._uut_conn.recbuf)
            return dict(POEEVENTS=dict(m1))

        elif action == 'ON':
            self._uut_conn.send("Alchemy POESHUT {0}\r".format(upoe_param), expectphrase=self._uut_prompt, timeout=30, regex=True)
            # Set the current limit
            if poe_params.get('icutcode', None):
                self._uut_conn.send("Alchemy POESETICUT -icutcode:{0}\r".format(poe_params.get('icutcode', 34)),
                              expectphrase=self._uut_prompt, timeout=30, regex=True)
            else:
                icutcode_default = 34
                log.info("ATTENTION: PoE icutcode default ({0}) will be set.".format(icutcode_default))
                self._uut_conn.send("Alchemy POESETICUT -icutcode:{0}\r".format(icutcode_default), expectphrase=self._uut_prompt,
                              timeout=30, regex=True)
            # Power up in small sets of 4 discontinuous ports to avoid large in-rush over-current.
            for i in range(0, 4):
                ps = [str(p) for p in poe_ports_list_z[i::4]]
                port_param_z = '-p:{0}'.format(','.join(ps))
                self._uut_conn.send("Alchemy POEPOWER {0} {1}\r".format(port_param_z, upoe_param), expectphrase=self._uut_prompt,
                              timeout=30, regex=True)

        elif action == 'OFF':
            self._uut_conn.send("Alchemy POESHUT {0}\r".format(upoe_param), expectphrase=self._uut_prompt, timeout=30, regex=True)

        else:
            log.error("Set PoE UUT action is unknown: {0}".format(action))
            return False

        if re.search('(?m)(?:ERR)|(?:Error)', self._uut_conn.recbuf):
            log.error("Problem with PoE set params.")
            log.error("Check UUT mode. Check commands. Check UUT.")
            return False

        return True

    @func_details
    def _calc_poe_power_budget(self, poe_type, uut_poe_ports):
        """ Calc PoE Power Budget

        Determines the number of groups the PoE Ports must be subdivided into so that the total available power
        is not exceeded.
        NOTE: Uses the PSU functions.

        :param (str) poe_type: Choice of 'POE', 'POE+', 'UPOE'
        :param (str) uut_poe_ports: Ex. '1-12' or '1,2,3,4,5,6,7,8,9,10,11,12'
        :return (int): The number of groups the poe ports need to be subdivided into.
        """
        poe_ports = common_utils.expand_comma_dash_num_list(uut_poe_ports)
        pwr_map = {'POE': 15, 'POE+': 30, 'UPOE': 60}
        port_group_list = [4, 3, 2, 1]
        pwr_available = self.get_power_available()
        if pwr_available == 0:
            log.warning("*" * 100)
            log.warning("Power Available from PSUs are indeterminant!")
            log.warning("This can be cause by non-working diags or bad I2C.")
            log.warning("A default budget of 2200W will be allowed.")
            log.warning("Ensure the unit actually has this amount of power for the PSU.")
            log.warning("*" * 100)
            pwr_available = 2200
        port_count = len(poe_ports)
        pwr_per_port = pwr_map.get(poe_type, 60)  # Assume worst case power requirement.
        while port_group_list:
            port_groups = port_group_list.pop()
            pwr_needed = port_count / port_groups * pwr_per_port
            log.debug("PoE Type         : {0}".format(poe_type))
            log.debug("PoE Port Count   : {0}".format(port_count))
            log.debug("PoE Port Groups  : {0}".format(port_groups))
            log.debug("Power Requirement: {0} W".format(pwr_needed))
            log.debug("Power Available  : {0} W".format(pwr_available))
            if pwr_needed > pwr_available:
                log.warning("Power needed exceeds power available by {0} W!".format(pwr_needed - pwr_available))
            else:
                log.info("Power available to meet PoE requirement.")
                break
        else:
            log.warning("Port group subdivision for power budget could NOT be determined.")
            log.warning("Please check the PSU(s) for proper configuration.")
            port_groups = 1
        return port_groups

    @func_details
    def _measure_poe_volt_test(self, active_poe_ports, poe_volt_range):
        """ Measure PoE Voltage
        NOTE: This requires Stardust and the PoE Loadbox working together.
        results samples:
        Sample1: {1: {'volt': (-1.6, 1.0), 'temp': 31.0, 'power': (0.0, 0.0)}, ...}
        Sample2: {1: {'volt': -1.6, 'temp': 31.0, 'power': 0.0}, ...}
        :param active_poe_ports:
        :param poe_volt_range:
        :return:
        """
        results = {}
        measurements = self._equip.poe_loadbox.get_instrument_data()
        log.debug("Checking Instrument data...")
        log.debug("Volt range (abs): {0} - {1}".format(poe_volt_range[0], poe_volt_range[1]))
        for p in active_poe_ports.split(','):
            results[int(p)] = measurements.get(int(p), {'volt': 0, 'temp': None, 'power': 0})
            if isinstance(results[int(p)]['volt'], tuple):
                results[int(p)]['pass'] = True if (poe_volt_range[0] <= abs(results[int(p)]['volt'][0]) <=
                                                   poe_volt_range[1]) and \
                                                  (poe_volt_range[0] <= abs(results[int(p)]['volt'][1]) <=
                                                   poe_volt_range[1]) else False
            else:
                results[int(p)]['pass'] = True if (poe_volt_range[0] <= abs(results[int(p)]['volt']) <= poe_volt_range[1]) else False
        time.sleep(1.0)
        ret = True
        for p in sorted(results.keys()):
            log.debug("P_{0:02d}: {1}".format(p, results[p]))
            if not results[p]['pass']:
                log.debug("Bad result: {0}".format(results[p]['pass']))
                ret = False
        log.debug("Measure PoE Volts from LoadBox for Ports {0}: Result={1}".format(active_poe_ports, ret))
        return ret

    @func_details
    def _measure_uut_poe_power(self, poe_type, active_poe_ports, poe_current_range):
        """ Measure UUT PoE Power
        Alchemy POEGET for the UUT power readings.
        Samples:
        pwr_data = {'1': ('PWRG', '97', '5.4'), ... '12': ('PWRG', '104', '5.6')}
        pwr_data = {'1': ('PWRG', 'PWRG', '96', '97', '5.3', '5.4'), ... '12': ('PWRG', 'PWRG', '104', '105', '5.8', '5.6')}

        :param poe_type:
        :param active_poe_ports:
        :param poe_current_range:
        :return results:  {1: {'status: ['PWRG', 'PWRG'], 'current': [96, 97], 'power_level': [5.3, 5.4]} ... }
                          {1: {'status: ['PWRG'], 'current': [97], 'power_level': [5.3]} ... }
        """
        pwr_data = self._operate_poe_uut(action='GETPWR', poe_type=poe_type, poe_ports=active_poe_ports)
        results = {}
        active_poe_ports_list = common_utils.expand_comma_dash_num_list(active_poe_ports)
        for p in active_poe_ports_list:
            k = int(p)
            v = pwr_data.get(str(p), None)
            if v:
                # log.debug("Checking {0}: {1} ...".format(p, v))
                if len(v) == 6:
                    status, current, power_level = [v[0], v[1]], [int(v[2]), int(v[3])], [float(v[4]), float(v[5])]
                else:
                    status, current, power_level = [v[0]], [int(v[1])], [float(v[2])]
                results[k] = {'status': status, 'current': current, 'power_level': power_level}
            else:
                log.error("Missing port {0} data.".format(p))
                results[k] = {'status': '', 'current': [0], 'power_level': [0]}
        ret = True
        for p in sorted(results.keys()):
            log.debug("P_{0:02d}: {1}".format(p, results[p]))
            if results[p]['status'] != ['PWRG'] and results[p]['status'] != ['PWRG', 'PWRG']:
                log.error("Bad status result: {0}".format(results[p]['status']))
                ret = False
            total_current = 0
            for c in results[p]['current']:
                total_current += c
            if not poe_current_range[0] <= total_current <= poe_current_range[1]:
                log.warning("Out of spec current result: {0}".format(total_current))
                log.debug("Current range: {0}".format(poe_current_range))
                ret = False
        log.debug("Measure UUT PoE Power for Ports {0}: Result={1}".format(active_poe_ports, ret))
        return ret

    @func_details
    def _run_poe_diag_test(self, command):
        """ Run PoE Diag Test

        NOTE1: This function assumes UUT is in 'DIAG' mode.
        NOTE2: This requires Stardust and the PoE Loadbox working together.

        POE: The POE Diagnostics Section
             PoeDetTest       POE Powered Device Detection Test  [+]
             PoeClassTest     POE Powered Device Classification Test  [+]
             PoePowerTest     POE Power-up Test  [+]

        Sample Outputs:
            Diag> run PoePowerTest
            PoePowerTest (POE Power-up Test):
            PCIE2: (RC) X4 GEN-2 link UP
            Cable BID 0x8001 detected on stack connector 1
            Cable BID 0x8001 detected on stack connector 2
            PCIE2: (RC) X4 GEN-2 link UP
            Cable BID 0x8001 detected on stack connector 1
            Cable BID 0x8001 detected on stack connector 2
            IGNORED
            WARNING: VEEThreshold Test skipped.
            READY for disconnect test.
              #   PGood Time  HoldTime    DiscTime    Result   Condition
              1   0.20s      123.18s      24.84s       PASS
              2   0.41s      123.18s      25.05s       PASS
             ...
             23   4.72s      123.18s      24.43s       PASS
             24   4.92s      123.18s      24.63s       PASS
            PASSED
                 Run-time: 217774 millisecs

        :param (str) command:
        :return:
        """
        if command == 'PoeDetTest':
            self._uut_conn.send("run {0}\r".format(command), expectphrase=self._uut_prompt, timeout=300, regex=True)
            time.sleep(self.RECBUF_TIME)
            ret = False if 'PASS' not in self._uut_conn.recbuf else True

        elif command == 'PoeClassTest':
            self._uut_conn.send("run {0}\r".format(command), expectphrase=self._uut_prompt, timeout=300, regex=True)
            time.sleep(self.RECBUF_TIME)
            ret = False if 'PASS' not in self._uut_conn.recbuf else True

        elif command == 'PoePowerTest':
            self._equip.poe_loadbox.connect(detect_signature='ok', external='on', auto='on', ieee='on')
            time.sleep(2.0)
            self._uut_conn.send("run {0}\r".format(command), expectphrase='PoePowerTest', timeout=30, regex=True)
            self._uut_conn.waitfor(['READY for disconnect test', self._uut_prompt], timeout=300, regex=True)
            if 'READY for disconnect test' in self._uut_conn.recbuf:
                self._equip.poe_loadbox.disconnect()
                time.sleep(2.0)
                self._uut_conn.waitfor(self._uut_prompt, timeout=300, regex=True)
            else:
                self._equip.poe_loadbox.disconnect()
            time.sleep(self.RECBUF_TIME)
            ret = False if 'PASS' not in self._uut_conn.recbuf else True

        else:
            log.error("Run PoE Diag command='{0}' is not recognized.".format(command))
            ret = False

        return ret

    @func_details
    def _run_poe_empty_ports_test(self, poe_ports):
        """Run POE empty ports test

        NOTE1: This function assumes UUT is in 'DIAG' mode.
        NOTE2: This does NOT requires PoE Loadbox, it is testing empty POE ports (no device connected),
               making sure ports show FAIL/TIMEOUT.

        Sample output:
            Diag> run poedet
              PoeDetTest (POE Powered Device Detection Test): PCIe: Port 1 link active, 4 lanes, speed gen1 Doppler 0 PCIe link lane width is 4.
            Doppler 1 PCIe link lane width is 4.
            No cable detected on stack connector 1.
            No cable detected on stack connector 2.
            ***Err : Detect Timeout after 27073 ms on ports : 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48

              #   Detect     Time     Conditions
              1   FAIL      27.07s     TIMEOUT
              2   FAIL      27.07s     TIMEOUT
              3   FAIL      27.07s     TIMEOUT
              4   FAIL      27.07s     TIMEOUT
              5   FAIL      27.07s     TIMEOUT
              6   FAIL      27.07s     TIMEOUT
              7   FAIL      27.07s     TIMEOUT
              8   FAIL      27.07s     TIMEOUT
              9   FAIL      27.07s     TIMEOUT
             10   FAIL      27.07s     TIMEOUT
             11   FAIL      27.07s     TIMEOUT
             12   FAIL      27.07s     TIMEOUT
             13   FAIL      27.07s     TIMEOUT
             14   FAIL      27.07s     TIMEOUT
             15   FAIL      27.07s     TIMEOUT
             16   FAIL      27.07s     TIMEOUT
             17   FAIL      27.07s     TIMEOUT
             18   FAIL      27.07s     TIMEOUT
             19   FAIL      27.07s     TIMEOUT
             20   FAIL      27.07s     TIMEOUT
             21   FAIL      27.07s     TIMEOUT
             22   FAIL      27.07s     TIMEOUT
             23   FAIL      27.07s     TIMEOUT
             24   FAIL      27.07s     TIMEOUT
             25   FAIL      27.07s     TIMEOUT
             26   FAIL      27.07s     TIMEOUT
             27   FAIL      27.07s     TIMEOUT
             28   FAIL      27.07s     TIMEOUT
             29   FAIL      27.07s     TIMEOUT
             30   FAIL      27.07s     TIMEOUT
             31   FAIL      27.07s     TIMEOUT
             32   FAIL      27.07s     TIMEOUT
             33   FAIL      27.07s     TIMEOUT
             34   FAIL      27.07s     TIMEOUT
             35   FAIL      27.07s     TIMEOUT
             36   FAIL      27.07s     TIMEOUT
             37   FAIL      27.07s     TIMEOUT
             38   FAIL      27.07s     TIMEOUT
             39   FAIL      27.07s     TIMEOUT
             40   FAIL      27.07s     TIMEOUT
             41   FAIL      27.07s     TIMEOUT
             42   FAIL      27.07s     TIMEOUT
             43   FAIL      27.07s     TIMEOUT
             44   FAIL      27.07s     TIMEOUT
             45   FAIL      27.07s     TIMEOUT
             46   FAIL      27.07s     TIMEOUT
             47   FAIL      27.07s     TIMEOUT
             48   FAIL      27.07s     TIMEOUT
            FAILED

        :param poe_ports:       POE ports (str)
                            ex: '1-24'

        :return:                True if test passes, otherwise False
        """
        # get POE port list from poe_ports(str)
        # ex: '1-8' translated to '1,2,3,4,5,6,7,8'
        port_list = map(int, poe_ports.split('-'))
        port_list = range(port_list[0], port_list[1] + 1)
        port_list = str(port_list).replace(' ', '').replace('[', '').replace(']', '')
        log.debug('POE port list is {0}'.format(port_list))

        # build lookup regex pattern with port_list
        err_p = r'Detect Timeout after \d+ ms on ports : %s\s*\r\n' % port_list

        # execute cmd to run test, look for err_p
        self._uut_conn.send('setp poe PDPresent 1\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        self._uut_conn.send('setp poedet DetectType 1\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        self._uut_conn.send('run poedet\r', expectphrase=self._uut_prompt, timeout=200, regex=True)
        ret = True if re.search(err_p, self._uut_conn.recbuf) else False

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # PSU
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_psu(self):
        """ Get Power SUpply Unit (PSU)

        Diag> psee A
        Scrubs Power Supply EEPROM:
          PS PID              : PWR-C1-1100WAC
          PS VID              : V01
          PS SN               : LIT204423NP
          PS Power Class      : 1100W
          PS Vendor Name      : LITE-ON
          PS TAN              : 341-0561-01
          PS TAN Rev          : A0
          PS CLEI             : IPUPAJ0AAA
         *PS Fan Curve Coef.  : 0x50 0x90 0x8A 0xCE
         *PS Check-code base  : 0x9D
         *: Not applicable for Jack-Jack power supplies
        EEPROM (77 bytes of raw hex data)
        =================================
        0x00 : 50 57 52 2D 43 31 2D 31 31 30 30 57 41 43 20 20
        0x10 : 20 20 56 30 31 4C 49 54 32 30 34 34 32 33 4E 50
        0x20 : B0 4C 49 54 45 2D 4F 4E 20 20 20 20 20 20 20 20
        0x30 : 33 34 31 2D 30 35 36 31 2D 30 31 20 41 30 49 50
        0x40 : 55 50 41 4A 30 41 41 41 50 90 8A CE 9D

        Diag> psee B
        Err: func_ScrubsPsEeprom fails - PS slot B not powered on


        Diag> psstat a

        Scrubs Power Supply Status:
          Hardware status     : 0x13( Present - Power Good - Alert - )
          Power Class         : 715W (0x80)
          Status Fan          : 0x00
          Status Temp         : 0x00
          Status Word         : 0x0002

          V_in                : 0xF360
          I_in                : 0xB8DA
          P_in                : 0xF0FC

          V_out               : 0x707A
          I_out               : 0xC875
          P_out               : 0xE99B

          T_in                : 0xF094
          T_out               : 0xF0D0
          T_spot              : 0xF0AC

          V_out Mode          : 0x17

        :return:
        """
        p1 = re.compile('(?m)^[ \t*]*(?:PS )*(.*?)[ \t]+: (.*?)[\r\n]+')
        p2 = re.compile('(?m)^[ \t*]*(.*?)[ \t]+: (.*?)[\r\n]+')

        # @func_retry
        def __psee(psid):
            self._clear_recbuf()
            self._uut_conn.send("PSEEprom {0}\r".format(psid), expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m = p1.findall(self._uut_conn.recbuf)
            return dict(m) if m else {}

        # @func_retry
        def __psstat(psid):
            self._clear_recbuf()
            self._uut_conn.send("PSStatus {0}\r".format(psid), expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            m = p2.findall(self._uut_conn.recbuf)
            return dict(m) if m else {}

        psu_info = {}
        psu = self._ud.uut_config.get('psu', {})
        if not psu or not psu.get('slots', None):
            log.warning("No 'psu' data available from product definition.")
            return {}
        log.debug("PSU Slots: {0}".format(psu['slots']))
        for p in psu['slots']:
            log.debug("Getting {0} ...".format(p))
            d = __psstat(p)
            d.update(__psee(p))
            for k, v in d.items():
                d[k] = v.rstrip(' ')
            psu_info[p] = d
        log.debug(psu_info)
        return psu_info

    @func_details
    def get_power_available(self):
        """ Get Power Available
        Calc total power available from all PSU's installed.
        :return:
        """
        psu = self._get_psu()
        pwr_total = 0
        for pwr_slot, pwr_details in psu.items():
            pwr_one = int(pwr_details.get('Power Class', '0W').rstrip(' \n\r')[:-1])
            pwr_total += pwr_one
            log.debug("PSU {0} = {1} W".format(pwr_slot, pwr_one))
        log.debug("Total = {0} W".format(pwr_total))
        log.warning("Total power available could NOT be determined.") if pwr_total == 0 else None
        return pwr_total

    @func_details
    def read_kirchhoff_regs(self, offsets):
        """ Read Kirchhoff Registers
        Output Example:
          FpgaRead: read offset=0x58, read value=0x00000015
        :param offsets: Kirchhoff register offset list or single reg
        :return (list):
        """

        # Make it a list
        offsets = [offsets] if not isinstance(offsets, list) else offsets
        self._clear_recbuf()
        for offset in offsets:
            self._uut_conn.send('kirch fpgaread -offset:{}\r'.format(offset), expectphrase=self._uut_prompt, regex=True,
                          timeout=120)
        time.sleep(self.RECBUF_TIME)
        p = re.compile('read value=([\S]+)')
        m = p.findall(self._uut_conn.recbuf)

        return m

    @func_details
    def _build_pwr_budget_port_list(self, ports, group_index, poe_pwr_budget_groups):
        """ Build Power Budget Port List (EXTERNAL)
        This function can be used externally for non-traffic operations.

        :param (str) ports: Complete list of PoE ports on the UUT.
        :param (int) group_index: Port group index to determine the specific PoE ports based on power budget.
        :param (int) poe_pwr_budget_groups: Total port groups for power budgeting.
        :return (str): Specific PoE ports based on power budget and group index.
        """
        ports_list = common_utils.expand_comma_dash_num_list(ports)
        if poe_pwr_budget_groups == 0:
            log.warning("A PoE Power Budget has NOT been established!")
            log.warning("Please check PSU(s) and ensure a power budget group count is established.")
            log.warning("Defaulting to a single group.")
            poe_pwr_budget_groups = 1
        ports_per_group = len(ports_list) / poe_pwr_budget_groups
        port_sets = list()
        for s in range(0, poe_pwr_budget_groups, 1):
            start = s * ports_per_group
            end = start + ports_per_group
            port_sets.append([i for i in ports_list[start:end]])
        if len(ports_list) % poe_pwr_budget_groups:
            log.warning("Port groups NOT evenly divided! Some ports will be excluded.")
        idx = group_index - 1
        return str(port_sets[idx]).replace(' ', '')[1:-1] if idx < len(port_sets) else None

    # ------------------------------------------------------------------------------------------------------------------
    # FANs
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _set_fan_speed(self, speed_name, fan_speed, status_value_reference, max_attempts=3):
        """ Set Fan Speed
        Speed Read Example
        FpgaRead: read offset=0x58, read value=0x0000002A
        :param speed_name: 'low' 'high' 'nominal'
        :param fan_speed: '0x0A', '0xFF', '0x7B'
        :param status_value_reference:
        :param max_attempts:
        :return:
        """
        common_utils.uut_comment(self._uut_conn, 'FanTest', 'Speed={}'.format(speed_name))
        self._uut_conn.send('sendredearthframe 0 0x11.{} -e -c\r'.format(fan_speed), expectphrase=self._uut_prompt, regex=True,
                      timeout=120)
        time.sleep(self.RECBUF_TIME)
        retry_cnt = 0
        result = False
        while not result and retry_cnt < max_attempts:
            retry_cnt += 1
            m = self.read_kirchhoff_regs('0x58')
            status_value_current = m[0] if m else '0x00'
            log.debug(
                'Fan Speed: {0} (status: {1}, read attempt: {2})'.format(speed_name, status_value_current, retry_cnt))
            result = self._check_fan_value(status_value_reference, status_value_current)
            time.sleep(1.0)

        return result

    @func_details
    def _check_fan_value(self, status_value_reference, status_value_current):
        """ Check Fan Value
        :param status_value_reference: 0x0000002A, from product definition
        :param status_value_current: read from uut
        :return:
        """
        if status_value_current is '0x00':
            ret = False
            log.warning('FAN: Could not detect; please check fan module connection.')
        elif status_value_current != status_value_reference:
            log.warning('FAN: Bad read/wrong value, expected = {0}'.format(status_value_reference))
            ret = False
        else:
            log.debug("FAN: Good.")
            ret = True

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # ASIC
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_asic_ecid(self, instance_number=None):
        """Get ASIC ECID

        Sample 1:
        ---------
            N48P_CSR> dopchipinfo 0
            *** Doppler #0 chip info:
            Type = 0x03ce
            Version = 0x3
            Die ID = 7473d9 4953b1c5 cc63618a
            AVS Info = Typ (AF[4:2] = 3'b010)
            Temp = 50 degree C
            Voltage = 1.081V
            Core frequency = 375 Mhz

        Sample 2:
        ---------
            Shannon24U> dopchipinfo
            *** Main Board: Doppler #0 chip info:
              Type = 0x03e1
              Version = 0x1
              Die ID = 01303032 3034534d 54545401 03051a00
                VID : 825 mV
                Die column X/Y : 5/3
                Wafer Id       : 1
                Wafer lot Id   : TTTMS40200
                Programmed at wafer sort : 1
                Programmed at final test : 0
              Local Temp    = 42 degree C
              Remote Temp 1 = 42 degree C
              Remote Temp 2 = 42 degree C
              Remote Temp 3 = 41 degree C
              Remote Temp 4 = 41 degree C
              Voltage = 0.837V
              Core frequency = 500 Mhz

        :param (int) instance_number: ASIC device instance num (default is to get all instances)
        :return (list) ecids: List of tuples of (type, ver, ecid, freq)
                sample for two cores present:
                [('0x03e1', '0x1', '01303032 3034534d 54545401 03051a00', '500'),
                 ('0x03e1', '0x1', '01303032 3034534d 54545401 03051a00', '500')]
        """
        common_utils.uut_comment(self._uut_conn, 'ECID', 'Get ASIC ID data.')

        # Input
        if instance_number:
            if not isinstance(instance_number, int):
                log.error("The 'instance_number' param MUST be an integer.")
                return None
            elif 0 <= instance_number <= 32:
                log.error("The 'instance_number' param is outside of normal range.")
                return None
            log.debug("Getting instance {0}...".format(instance_number))
        else:
            log.debug("Getting ALL instances...")
            instance_number = ''

        @func_retry
        def __dopchipinfo():
            self._clear_recbuf()
            self._uut_conn.send('dopchipinfo {}\r'.format(instance_number), expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile(
                r'(?ms)Type = ([0-9xa-fA-F]+).*?Version = ([0-9xa-fA-F]+).*?Die ID = ([0-9a-fA-F ]+).*?'
                r'(?:Core frequency = ([0-9]+))?')
            return p.findall(self._uut_conn.recbuf)

        ecids = __dopchipinfo()
        if ecids:
            log.info("Found {0} ECID(s).".format(len(ecids)))
        else:
            log.warning("No ECIDs found.")
        return ecids

    @func_details
    def _record_asic_ecid(self, uut_asic_data, uut_asic_setup, asic_type_table, host_sn):
        """ Record ASIC ECID

        :param (list) uut_asic_data: Info retrieved by diags.
         Ex. [('0x03e1', '0x1', '01303032 3034534d 54545401 03051a00', '500'),
              ('0x03e1', '0x1', '01303032 3034534d 54545401 03051a00', '500')]
        :param (dict) uut_asic_setup: PCBA specific data about the ASIC(s)
         Ex. {'core_count': 1, 'locations': ['U98']}
        :param (dict) asic_type_table: Table of info about ASIC vendor information (from common product module).
         Ex.  asic_type_table = {
         '0x0351': {'name': 'Doppler',    'ver': {'0x1': {'cpn': '08-0849-01', 'freq': '100 Mhz', 'vendor': 'IBM'},
                                                  '0x2': {'cpn': '08-0849-02', 'freq': '100 Mhz', 'vendor': 'IBM'}}},
         '0x0390': {'name': 'DopplerCR',  'ver': {'0x1': {'cpn': '08-0912-01', 'freq': '300 Mhz', 'vendor': 'IBM'},
                                                  '0x2': {'cpn': '08-0912-02', 'freq': '300 Mhz', 'vendor': 'IBM'}}},
         ...}  (see the product _x_common.py modules in product_definitions dir).
        :param (str) host_sn: PCBA S/N hosting the ASIC(s)
        :return:
        """
        AsicData = namedtuple('AsicData', 'type ver ecid freq')
        ref_des_list = uut_asic_setup.get('locations', ['U0'])
        device_count = len(ref_des_list)
        core_count = uut_asic_setup.get('core_count', 1)
        if core_count % device_count != 0:
            log.error(
                "The total core_count ({0}) and total ASIC devices ({1}) do NOT properly align.".format(core_count,
                                                                                                        device_count))
            log.error("Please correct the product definition file.")
            return False
        cores_per_device = core_count / device_count
        log.debug("CC={0}, DC={1}, RF={2}".format(core_count, device_count, ref_des_list))

        # Assemble the data.
        temp_data = []
        timestruct, _ = common_utils.getservertime()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', timestruct)
        for i, reading in enumerate(uut_asic_data):
            asic = AsicData(reading[0], reading[1], reading[2], reading[3])
            u = (i - i % cores_per_device) / cores_per_device
            ref_des = ref_des_list[u] if u < device_count else 'U?'
            asic_type_data = asic_type_table.get(asic.type, {'name': 'unknown', 'ver': {}})
            asic_name = asic_type_data.get('name', 'unknown')
            asic_cpn = asic_type_data.get('ver', {}).get(asic.ver, {}).get('cpn', '08-0000-01')
            asic_vendor = asic_type_data.get('ver', {}).get(asic.ver, {}).get('vendor', 'unknown')
            line = '|'.join(
                [host_sn, iso_timestamp, asic_cpn, asic.type, asic.ver, asic.ecid.replace(' ', ''), ref_des, asic_name,
                 asic.freq, asic_vendor])
            temp_data.append(line)

        # Remove duplicates for multi-core devices
        file_data = list(set(temp_data))
        if not file_data:
            log.error("Something went wrong with ecid data processing: no data found.")
            return False

        # Record the data
        log.debug("Recording the following ECID data:")
        for line in file_data:
            log.debug(line)

        # Add the subdir if nonexistant
        subdirs = self.ASIC_ECID_LOG_PATH.split('/')
        subdirs[0] = '/'
        epath = ''
        for subdir in subdirs:
            epath = os.path.join(epath, subdir)
            if not os.path.exists(epath):
                os.mkdir(epath)

        uut_file_name = os.path.join(self.ASIC_ECID_LOG_PATH, '{0}.txt'.format(host_sn))
        common_file_name = os.path.join(self.ASIC_ECID_LOG_PATH, 'ecids_collection.txt')
        ret = common_utils.writefiledata(common_file_name, file_data, mode='a+')
        ret2 = common_utils.writefiledata(uut_file_name, file_data)
        log.debug("UUT ECID File = {0}".format(uut_file_name))
        return all([ret, ret2])

    # ------------------------------------------------------------------------------------------------------------------
    # RTC
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _check_rtc(self, time_zone='GMT', time_secs_margin=4.0, original_server_mktime=None, osc_accuracy=None, severity_allowed=120):
        """ Check RTC

        Note: Use 4 x 2 seconds of margin between UUT RTC capture and server time capture. This is the default.

              A typical crystal has an error of 100ppm which translates as 100/1e6 or (1e-4).
              So the total error on a day is 86400 x 1e-4= 8.64 secs/day or 3600 x 1e-4 = 0.36 secs/hr.
              The oscillator used in C3K platforms has +/-20ppm and depending on aging and temperature it
              could be as high as +/-200ppm accuracy.
              Worst case, translates to 200/1e6 x 3600 = +/- 0.72 secs/hr.
                Note: Some empirical measurements have shown this accuracy to be as bad as >1.0 sec/hr.

        Sample uut capture
            N48P_CSR> getrtc

            Monday 05-22-17
            22:13:57

        server_time has the data type:
        time.struct_time(tm_year=2017, tm_mon=5, tm_mday=20,
                         tm_hour=17, tm_min=14, tm_sec=13,
                         tm_wday=5, tm_yday=140, tm_isdst=1)

        :param (str) time_zone: GMT(Greenwich Mean Time) or PTZ(Pacific Time Zone)
        :param (float) time_secs_margin: Difference +/- margin in seconds
        :param (float) original_server_mktime: If provided, use to dynamically adjust the delta measurement.
                                             This is the mktime when the RTC was originally set.
        :param (float) osc_accuracy: override standard osc ppm accuracy
        :param (int) severity_allowed: Amount of secs the time delta is allowed to have when the original_server_mktime is NOT available.
        :return (str): 'PASS', 'FAIL', 'PROG'
        """

        # UUT comment
        common_utils.uut_comment(self._uut_conn, 'CHECK RTC', 'Time Zone:{}'.format(time_zone))
        self._clear_recbuf()

        # Get Apollo server time then RTC time quickly in succession.
        # Perform this 3 times and use the lowest delta reading; this is to minimize server lag between
        # Apollo instructions since we cannot synchronize reading the time from both server and UUT.
        # It is not known what the worst case lag is so a built-in buffer will be added to the margin by default.
        # The same lag must be accounted for during the programming operation therefore total built-in
        # margin is 2x of the default margin.
        osc_accuracy = self.OSC_ACCURACY if not osc_accuracy else osc_accuracy
        time_results = []
        for count in range(1, 4):
            self._clear_recbuf()
            server_time, server_mktime = common_utils.getservertime(time_zone)
            self._uut_conn.send('getrtc\r', expectphrase=self._uut_prompt, regex=True, timeout=120)
            time.sleep(self.RECBUF_TIME)
            p = re.compile('([0-9]{2})-([0-9]{2})-([0-9]{2})[ \n\r]+([0-9]{2}):([0-9]{2}):([0-9]{2})')
            m = p.findall(self._uut_conn.recbuf)
            if m and m[0]:
                current_uut_time = (int(m[0][2]) + 2000, int(m[0][0]), int(m[0][1]),
                                    int(m[0][3]), int(m[0][4]), int(m[0][5]),
                                    0, 0, server_time.tm_isdst)
            else:
                log.error("UUT did not provide an RTC time or the format is not recognized.")
                log.critical("Check the diagnostics and alert Cisco TDE.")
                return False

            uut_mktime = time.mktime(current_uut_time)
            delta_mktime = server_mktime - uut_mktime
            time_results.append((server_mktime, uut_mktime, delta_mktime))

        # Get the best reading
        deltas = [abs(i[2]) for i in time_results]
        log.debug("Abs Deltas: {0}".format(deltas))
        lowest_delta_index = deltas.index(min(deltas))
        server_mktime, uut_mktime, delta_mktime = time_results[lowest_delta_index]

        # Calculate normalized margin window
        drift = 0
        if original_server_mktime:
            log.debug("Calculating OSC drift...")
            drift = (server_mktime - original_server_mktime) * \
                    (osc_accuracy / 3600.0) if server_mktime > original_server_mktime else 0
        else:
            log.warning("Original server time for RTC setting was NOT found!")
            log.warning(
                "This indicates 1) the unit did not get initially set by this function in the upstream process, or")
            log.warning(
                "               2) the unit's server_mktime.txt file is missing due to rework  (flash format, etc.).")
            log.warning(
                "This test may fail since drift cannot be calculated; please reset RTC and retest with this function.")
        builtin_margin = time_secs_margin * 2
        normalized_window = builtin_margin + drift

        # Print Time values
        log.debug("Server orig mktime     : {0} secs".format(original_server_mktime))
        log.debug("UUT mktime             : {0} secs".format(uut_mktime))
        log.debug("Server mktime          : {0} secs".format(server_mktime))
        log.debug("Raw Delta              : {0} secs".format(delta_mktime))
        log.debug("Built-in margin        : {0} secs".format(builtin_margin))
        log.debug("OSC Accuracy           : {0} secs/hr".format(osc_accuracy))
        log.debug("Set-to-Meas Time Span  : {0}".format(
            common_utils.ddhhmmss(server_mktime - original_server_mktime) if original_server_mktime else 'unknown'))
        log.debug("OSC Drift              : {0} secs".format(drift))
        log.debug("TOTAL Margin window    : {0} secs (+/-)".format(normalized_window))

        # Check RTC
        if abs(delta_mktime) <= normalized_window:
            log.debug("UUT current time is within margin window!")
            result = 'PASS'
            # Even though time delta is within the normalized window, need to check if raw delta exceeds the
            # standard margin.  This is done to bring RTC back to be as accurate as possible via reprogramming.
            if delta_mktime > builtin_margin:
                log.warning("The RTC needs adjustment due to substantial OSC drift!")
                log.warning("RTC reprogramming will occur to make it as accurate as possible.")
                result = 'PROG'
        elif abs(delta_mktime) > 31536000:
            if original_server_mktime:
                log.error("RTC was previously set.")
                log.error("UUT current time exceeds margin (>1 yr delta); catastrophic RTC and/or battery failure.")
                result = 'FAIL'
            else:
                log.warning(
                    "UUT current time exceeds margin (>1 yr delta); RTC possibly at default. Programming required.")
                result = 'PROG'
        elif abs(delta_mktime) > 3600:
            log.error(
                "UUT current time exceeds margin (>1 hr delta); "
                "possible Time Zone difference, possible RTC failure, possible battery failure.")
            result = 'FAIL'
        elif abs(delta_mktime) > 120:
            log.error(
                "UUT current time exceeds margin (>2 min delta); "
                "possible RTC failure, possible RTC inaccuracy, possible battery failure.")
            result = 'FAIL'
        else:
            log.error("UUT current time exceeds margin (<2 min delta); possible RTC inaccuracy, possible setting lag.")
            result = 'FAIL'

        # Process failure condition
        if 'FAIL' in result:
            if original_server_mktime:
                log.debug("Failure severity: {0}".format(abs(delta_mktime)))
            else:
                log.warning("Allowed failure severity: <= {0} secs.".format(severity_allowed))
                if abs(delta_mktime) <= severity_allowed:
                    # Accomodate legacy process
                    log.warning("The UUT RTC time failure was within severity limits without a server time reference.")
                    log.warning("This is usually an indication of legacy process at BST or at the DF sites; a reprogramming will be allowed.")
                    result = 'PROG'
                else:
                    log.error("The UUT RTC time failure had a severity greater than what is allowed when the server time reference is absent.")

        return result

    @func_details
    def _program_rtc(self, time_zone='GMT', time_secs_margin=4.0, dow=False):
        """Program RTC
        :param time_zone: 'GMT'(Greenwich Mean Time) or 'PTZ'(Pacific Time Zone)
        :param time_secs_margin: Margin also used as timeout
        :param dow: If True set the day-of-week (newer diags do this automatically)
        :Sample uut capture
            Shannon48P> setrtc -time:hh:mm:ss -date:MM:DD:YY

        ;struct time:
        ;time.struct_time(tm_year=2017, tm_mon=5, tm_mday=20, tm_hour=17,
                          tm_min=14, tm_sec=13, tm_wday=5, tm_yday=140, tm_isdst=1
                          )
        :return (int): mktime of server that was programmed.
        """

        week_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        self._clear_recbuf()

        # Get Server Time and immediately program the UUT's RTC time only!
        # Timeout must be within built-in margin for checking.
        server_time, server_mktime = common_utils.getservertime(time_zone)
        self._uut_conn.send('setrtc -time:{}:{}:{}\r'.
                      format(server_time.tm_hour, server_time.tm_min, server_time.tm_sec),
                      expectphrase=self._uut_prompt,
                      regex=True,
                      timeout=time_secs_margin
                      )
        # Perform other settings separate to improve internal diag speed for time above.
        self._uut_conn.send('setrtc -date:{}/{}/{}\r'.
                      format(server_time.tm_mon, server_time.tm_mday, server_time.tm_year % 2000),
                      expectphrase=self._uut_prompt,
                      regex=True,
                      timeout=30
                      )
        if dow:
            self._uut_conn.send('setrtc -day:{}\r'.format(week_map.get(server_time.tm_wday)), expectphrase=self._uut_prompt,
                          regex=True, timeout=30)

        log.debug('UUT programed RTC')

        # Save the original server mktime for normalization during check at a later time
        return server_mktime

    # ==================================================================================================================
    # Support Methods (Internal or External)
    # ==================================================================================================================
    def _clear_recbuf(self, force=False):
        if self.USE_CLEAR_RECBUF or force:
            self._uut_conn.clear_recbuf()
            time.sleep(self.RECBUF_CLEAR_TIME)
        return

    def __check_dependencies(self):
        if not self._linux:
            msg = "Missing the Linux driver."
            log.error(msg)
            raise Exception(msg)
        if not self._mode_mgr:
            msg = "Missing the Mode Manager driver."
            log.error(msg)
            raise Exception(msg)
        if not self._ud:
            msg = "Missing the UUT Descriptor driver."
            log.error(msg)
            raise Exception(msg)
        return


