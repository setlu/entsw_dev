""" Peripheral Class Driver Module
=========================================================================================================================

This module provides a set of classes for manipulating the peripherals of a product in the Catalyst families:
    1. Cisco Catalyst 2900 series (WS-C2900 & C9200)
    2. Cisco Catalyst 3800/3600 series (WS-C3850/C3650 & C9300, C9300L)
    3. Cisco Catalyst 4000 series (WS-C4000 & C9400)

The driver type is identified by class name.
"""

# ------
import sys
import re
import logging
import time

# Apollo
# ------
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils.common_utils import func_details
from apollo.scripts.entsw.libs.utils.common_utils import apollo_step
from apollo.scripts.entsw.libs.cat.uut_descriptor import UutDescriptor as _UutDescriptor


__title__ = "Catalyst Peripheral Module"
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

# ======================================================================================================================
# Exceptions
class PeripheralException(Exception):
    """Raise for specific Peripheral exceptions."""
    pass


# ======================================================================================================================
# CLASS DRIVERS
#
class Peripheral(object):
    def __init__(self, mode_mgr, ud, **kwargs):
        log.info(self.__repr__())
        self.pd = None
        self._ud = ud
        self._mode_mgr = mode_mgr
        self._check_mode_mgr()
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt_map = self._mode_mgr.uut_prompt_map
        self._uut_prompt = self._uut_prompt_map.get('STARDUST', '> ')
        self._uut_config = kwargs.get('uut_config', {})
        self._sysinit = kwargs.get('sysinit', None)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


    # Properties -------------------------------------------------------------------------------------------------------
    # none

    @apollo_step(s='Utility')
    def manual_select(self, **kwargs):
        if self.pd:
            self.pd.product_selection = aplib.ask_question("Select peripheral:", answers=self.pd.products_available)
            log.debug("Peripheral Selection = {0}".format(self.pd.get_flash_params()))
            if 'pcamaps' not in self._ud.uut_config:
                self._ud.uut_config['pcamaps'] = {}
            self._ud.uut_config['pcamaps'].update(self.pd.uut_config.get('pcamaps', {}))
        else:
            log.warning("There is no Peripheral UutDescriptor.")
            log.warning("Ensure a valid Peripheral class has been initialized.")
            log.warning("The selection will be null.")
        return aplib.PASS

    # User Methods -----------------------------------------------------------------------------------------------------
    @func_details
    def read_quack_params(self, device_instance):
        """ Read Quack/ACT2 Device Params (INTERNAL)
        If an error is encountered, attempt a single sysinit and try again.
        :param (int) device_instance:
        :return (dict): Device PCAMAP params.
        """
        params = {'bid': None}
        if device_instance < 1:
            log.warning("Device instance for peripherals MUST be greater than 1.")
            return params

        pattern = r"[ \t]*([\S]+)[ \t]*:[ \t]*([\S]*)"
        count = 0
        while count < 3:
            # self._uut_conn.clear_recbuf()
            count += 1
            self._uut_conn.send('SCCReadQuackFruEeprom -instance:{0} -f:all\r'.
                                format(device_instance), expectphrase=self._uut_prompt, timeout=120, regex=True)
            time.sleep(2.0)
            if "***ERR" in self._uut_conn.recbuf:
                if count == 1:
                    log.warning("Error encountered on first attempt of EEPROM read of peripheral.")
                    if self._sysinit:
                        log.warning("Performing sysinit to ensure clean setup...")
                        self._sysinit()
                    else:
                        log.warning("Sysinit is unavailable; cannot perform reset for EEPROM read.")
                elif count == 2 and 'failed at QuackReadEeprom' in self._uut_conn.recbuf:
                    log.warning("Error encountered on second attempt.")
                    log.warning("Failed at QuackReadEeprom; most likely no peripheral device installed.")
                    log.warning("EEPROM read will return empty.")
                    log.warning("Please ensure this warning is accurate!")
                    break
                else:
                    log.error("Multiple command attempts failed to complete.")
            else:
                log.debug("Successful command completion.")
                break
        else:
            msg = self._uut_conn.recbuf[self._uut_conn.recbuf.find('***ERR'):self._uut_conn.recbuf.find('USAGE')]
            log.error("Error attempting EEPROM read.")
            log.error("Check peripheral presence/function and check that 'sysinit' has completed successfully.")
            log.error(msg)
            return params

        p = re.compile(pattern)
        m = p.findall(self._uut_conn.recbuf)
        if m and len(m) > 0:
            for k, v in m:
                # Change unprogrammed values to char '0'.
                v = v.replace('\xff', '').replace('\x00', '')
                v = '0' if v == '' else v
                # The param MUST start with a letter! Otherwise it might be a cmd option (e.g. "-instance:1")
                # or something else that was picked up in the recbuf.
                if re.match('[A-Za-z].*', k):
                    params[k] = v
        return params

    @func_details
    def write_quack_params(self, device_instance, set_params):
        """ Write the Quack/ACT2 Device Params (INTERNAL)
        :param (int) device_instance:
        :param (dict) set_params:
        :return (bool): True if successful
        """
        if not set_params or len(set_params) < 1:
            log.error("Parameters to write is empty!")
            return False

        # First check if device is accessible
        if not self.read_quack_params(device_instance):
            log.error("Problem accessing the device device.")
            return False
        # Check that the input is correct form
        if not isinstance(set_params, dict):
            log.error("The params input MUST be in dict form.")
            return False

        # Perform the write programming
        err_msg = ''
        for k in set_params.keys():
            if set_params[k]:
                log.debug("Writing: '{0}' = '{1}' ...".format(k, set_params[k]))
                self._uut_conn.send('SCCWriteQuackFruEeprom -instance:{0} -f:{1} -v:{2}\r'.
                                    format(device_instance, k, set_params[k]),
                                    expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(2.0)
                if "***ERR" in self._uut_conn.recbuf:
                    # Collect errors for all params.
                    a = self._uut_conn.recbuf.find('***ERR')
                    b = self._uut_conn.recbuf.find('USAGE')
                    err_msg += self._uut_conn.recbuf[a:b]
            else:
                log.warning("NOT writing: '{0}' is null.".format(k))
        if err_msg:
            log.error("Error attempting EEPROM read.")
            log.error("Check peripheral presence/function and check that 'sysinit' has completed successfully.")
            log.error(err_msg)
            return False

        # Confirm programming w/ read-back
        if not self.read_quack_params(device_instance):
            log.error("Problem reading back the programmed device.")
            return False

        return True

    @func_details
    def get_uplink_card_type(self):

        uplink_card = None
        uplink_test_card = None
        uplink_params = self.read_quack_params(device_instance=1)
        if uplink_params.get('bid', None):
            if uplink_params['bid'].upper() == 'F001':
                uplink_test_card = 'Hilbert'
            elif uplink_params['bid'].upper() == 'F002':  # TODO: Confirm w/ HW Eng
                uplink_test_card = 'Makron'
            else:
                uplink_card = 'NM'

        return uplink_card, uplink_test_card

    @func_details
    def set_uplink_test_card(self, test_card, uplink_port_pairs_and_speed):
        speed_map = {'1G': 'G', '1000': 'G', 'GIG': 'G', 'G': 'G', '10000': 'XG', '10G': 'XG', 'XG': 'XG', None: 'G'}
        if test_card:
            log.info("{0}".format("Uplink Test Card detected: {0}".format(test_card)))
            # Process all uplink port pairs for speed
            # Format: [(a,b,speed), (c,d,speed), ...]
            tc_cfg_list = []
            for i, v in enumerate(sorted(uplink_port_pairs_and_speed), 1):
                if not v[2]:
                    log.warning("Uplink speed not specified; default of {0} will be used.".format(speed_map[None]))
                tc_cfg_list.append('{0}/{1}'.format(i, speed_map[v[2]]))
            test_card_cfg = ';'.join(tc_cfg_list)

            log.debug("{0} Port Setting = {1}".format(test_card, test_card_cfg))
            self._uut_conn.sende("{0}SetPort {1}\r".format(test_card, test_card_cfg), expectphrase=self._uut_prompt,
                                 timeout=30, regex=True)
            if re.search('(?m)(?:ERR)|(?:Error)', self._uut_conn.recbuf):
                msg = "Problem with {0}SetPort.".format(test_card)
                log.error(msg)
                raise aplib.apexceptions.ApolloException(msg)
        else:
            log.info("NO Uplink Test Card detected.")

    # Internal Methods -------------------------------------------------------------------------------------------------
    # none

    def _check_mode_mgr(self):
        if not self._mode_mgr:
            log.warning("*" * 50)
            log.warning("The BTLDR/ROMMON mode must be present when apttempting to use this driver.")
            log.warning("Since a Mode Manager was NOT provided, the mode and dependencies cannot be guaranteed!")
            log.warning("*" * 50)
            raise PeripheralException("The rommon driver MUST have a Mode Manager.")
        return True


# ----------------------------------------------------------------------------------------------------------------------
# C2K & C9200 Family
class PeripheralC2K(Peripheral):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PeripheralC2K, self).__init__(mode_mgr, ud, **kwargs)
        import apollo.scripts.entsw.cat2.C_PERIPH.product_definitions._product_line_def as _cperiph2_product_line_def
        log.debug(" UutDescriptor for {0}".format(self.__class__.__name__))
        self.pd = _UutDescriptor(common_def=None, product_line_def=_cperiph2_product_line_def, uut_conn=None,
                                 parent_module=thismodule, standalone=True)
    pass


# ----------------------------------------------------------------------------------------------------------------------
# C3K & C9300 Family
class PeripheralC3K(Peripheral):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PeripheralC3K, self).__init__(mode_mgr, ud, **kwargs)
        import apollo.scripts.entsw.cat3.C_PERIPH.product_definitions._product_line_def as _cperiph3_product_line_def
        log.debug(" UutDescriptor for {0}".format(self.__class__.__name__))
        self.pd = _UutDescriptor(common_def=None, product_line_def=_cperiph3_product_line_def, uut_conn=None,
                                 parent_module=thismodule, standalone=True)
    pass



# ----------------------------------------------------------------------------------------------------------------------
# C4K & C9400 Family
class PeripheralC4K(Peripheral):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PeripheralC4K, self).__init__(mode_mgr, ud, **kwargs)
    pass


# ----------------------------------------------------------------------------------------------------------------------
# C9500 Family
class PeripheralC5K(Peripheral):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PeripheralC5K, self).__init__(mode_mgr, ud, **kwargs)
        import apollo.scripts.entsw.cat3.C_PERIPH.product_definitions._product_line_def as _cperiph5_product_line_def
        log.debug(" UutDescriptor for {0}".format(self.__class__.__name__))
        self.pd = _UutDescriptor(common_def=None, product_line_def=_cperiph5_product_line_def, uut_conn=None,
                                 parent_module=thismodule, standalone=True)
    pass
