""" Quack2 General Module
========================================================================================================================

Intended for general quack programming/verification as product and product family agnostic
within the Enterprise Switching and IoT BU spaces.

This module expects Stardust as the cli diags.

========================================================================================================================
"""

# Python
# ------
import sys
import os
import logging
import re
import binascii
from collections import OrderedDict
import time

# Apollo
# ------
from apollo.libs import lib as aplib
from apollo.libs import cesiumlib

# BU Lib
# ------
from ..utils.common_utils import apollo_step
from ..utils.common_utils import validate_sernum
from ..utils.common_utils import validate_pid
from ..utils.common_utils import func_details
from ..utils.common_utils import print_large_dict


__title__ = "Quack2 General Module"
__version__ = '2.0.0'
__author__ = 'bborel'

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


class Quack2(object):
    """ Quack2 Utility
    """
    QUACK2_LOG_PATH = "/tmp"
    QUACK2_CONSOLE_SEND_SIZE = 16
    QUACK2_MAX_SERVICE_RETRY = 10

    # These profiles are a means to validate the data content by way of string size representing the hex data.
    QUACK2_CERT_PROFILES = {
        'WS-C3850': [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'C3850-NM': [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'STACK-T1': [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'WS-C3750': [191, 95, 413, 5, 32, 53, 41, 143, 17, 1],
        'ME-3600':  [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'ME-3800':  [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'AIR-CT57': [191, 95, 419, 5, 32, 53, 47, 143, 17, 2],
        'DEFAULT':  [191, 95, 419, 5, 32, 53, 47, 143, 17, 2]
    }
    # Data field items returned by the UUT.
    # Each field corresponds to the size table entries above via list index.
    QUACK2_CERT_PROFILE_FIELDS = [
        'tlv_info',
        'quack_mfg_serial_number',
        'data_to_sign',
        'controller_type',
        'system_serial_number',
        'pid',
        'iudi',
        'quack_pub_key_signature',
        'digital_signature_list',
        'scc_version_num'
    ]

    def __init__(self, mode_mgr, ud, **kwargs):
        """ Instantiate the class

        :param mode_mgr:
        :param kwargs: Params needed specific to the UUT's diags CLI prompting for sending data to the console.
                       Typical input would look like the following below--

        :return:
        """
        log.info(self.__repr__())

        self._ud = ud
        self._mode_mgr = mode_mgr                                                  # UUT Mode Mgr instance
        self._uut_conn = self._mode_mgr.uut_conn                                   # Connection to UUT
        self._uut_prompt = self._mode_mgr.uut_prompt_map.get('STARDUST', '> ')     # UUT prompt

        self.quack2_data = OrderedDict()

        # UUT Params
        self.device_instance = None
        self.quack2_data['uut_sernum'] = kwargs.get('uut_sernum', '')               # UUT main s/n
        self.quack2_data['uut_pid'] = kwargs.get('uut_pid', '')                     # UUT Base PID ! (not Cfg PID)

        # Quack2 Parameters
        self.quack2_data['cert_params'] = \
            kwargs.get('cert_params', self.__lookup_cert_params_by_pid(self.quack2_data['uut_pid']))  # Allow custom

        return

    def __str__(self):
        doc = "{0},  ConSndSize:{1},  MaxServiceRetry:{2}".\
            format(self.__repr__(), Quack2.QUACK2_CONSOLE_SEND_SIZE, Quack2.QUACK2_MAX_SERVICE_RETRY)
        return doc

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    def show_version(self):
        log.info(self.__repr__())

    # Properties -------------------------------------------------------------------------------------------------------
    #
    @property
    def uut_pid(self):
        return self.quack2_data.get('uut_pid', None)

    @uut_pid.setter
    def uut_pid(self, newvalue):
        self.quack2_data['uut_pid'] = newvalue
        self.quack2_data['cert_params'] = self.__lookup_cert_params_by_pid(newvalue)

    @property
    def uut_sernum(self):
        return self.quack2_data.get('uut_sernum', None)

    @uut_sernum.setter
    def uut_sernum(self, newvalue):
        self.quack2_data['uut_sernum'] = newvalue

    # ------------------------------------------------------------------------------------------------------------------
    # USER STEPS
    #
    @apollo_step
    def sign_chip(self, **kwargs):
        """ QUACK2 Sign
        Note: The uut_config is also used as input.
        :menu: (enable=True, name=QUACK2, section=Diags, num=1, args={'menu': True})
        :param (dict) kwargs: 'device_instance'
        :return (str): aplib.PASS/FAIL
        """

        # Process input
        menu = kwargs.get('menu', False)
        self.device_instance = kwargs.get('device_instance', self._ud.device_instance)

        # TODO: check below condition, if safe then remove it
        # Sanity check.
        # identity_protection_type = self._ud.uut_config.get('identity_protection_type', None)
        # if not identity_protection_type:
        #     log.error("Unknown Identity Protection type.")
        #     log.error("Ensure the product definition is loaded and has an 'identity_protection_type' entry.")
        #     return aplib.FAIL, "IdPro undefined."
        # if 'QUACK2' not in identity_protection_type:
        #     log.warning("The UUT Identity Protection Type ='{0}'.".format(identity_protection_type))
        #     log.warning("Nothing to do here (not QUACK2).")
        #     # Note: Skip since QUACK2 does not apply and we don't want to penalize the menu selection (if called).
        #     return aplib.SKIPPED

        if self.device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while self.device_instance is None or not str(self.device_instance).isdigit():
                self.device_instance = aplib.ask_question("Device instance [int]:")
        self.device_instance = int(self.device_instance)
        if not 0 <= self.device_instance < 10:
            raise Exception("Device instance for Quack2 is invalid (must be 0 to 10).")

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode for QUACK2."

        # Arrange UUT required params
        # Ensure the PUID Keys are set appropriately:
        #   1. 'SYSTEM_SERIAL_NUM'/'SERIAL_NUM', 'MODEL_NUM'   for main units
        #   2. 'SN', 'VPN' for peripherals
        self.uut_pid = self._ud.puid.pid
        self.uut_sernum = self._ud.puid.sernum

        # Perform the action
        log.debug("Device Instance = {0}".format(self.device_instance))
        log.debug("PID             = {0}".format(self.uut_pid))
        log.debug("S/N             = {0}".format(self.uut_sernum))
        result = self.__sign_chip()
        return aplib.PASS if result else (aplib.FAIL, "Quack2 signing error.")

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNALS
    #
    @func_details
    def __sign_chip(self):
        """ Sign the QUACK Chip
        Perform the sequence of operations required to sign/program the Quack2 device.
        :return:
        """
        ret = False
        try:
            self.__validate_input_params()
            self.__get_hardware_data()
            self.__get_signature()
            self.__put_signature()
            ret = True

        except Exception as e:
            log.critical(e)
            log.error("Cannot complete QUACK2 Sign operation.")
            # Deep debug: log.debug("recbuf='{0}'".format(self._uut_conn.recbuf))
            self.__graceful_exit()
            ret = False

        finally:
            print_large_dict(self.quack2_data)
            return ret

    @func_details
    def __validate_input_params(self):
        """ Validate Input Parameters
        Only prompt the questions when the input is empty or not correct.
        This routine serves mainly use for bench/debug testing but is always called to validate input and offer
        corrective action.
        :return:
        """

        # UUT Params ---------------
        while not validate_sernum(self.quack2_data['uut_sernum']):
            log.warning("Could not validate Serial Number; prompting for input...")
            self.quack2_data['uut_sernum'] = aplib.ask_question("UUT\n\nEnter Cisco System "
                                                                "Serial Number (LLLYYWWSSSS): ")

        while not validate_pid(self.quack2_data['uut_pid']):
            log.warning("Could not validate Base PID; prompting for input...")
            self.quack2_data['uut_pid'] = aplib.ask_question("UUT\n\nEnter Base PID (18 max chars): ")

        # Quack Cert Params ---------------
        if not self.quack2_data['cert_params']:
            raise Exception("Could not validate Quack2 Cert parameters.")

        return True

    @func_details
    def __lookup_cert_params_by_pid(self, pid='DEFAULT'):
        """ Lookup Quack2 Cert Profile
        Create the dict based on the PID.
        :param pid:
        :return: (dict)
        """
        matching_pid_list = [key for key in Quack2.QUACK2_CERT_PROFILES if key in pid]
        matching_pid_list_len = len(matching_pid_list)
        if matching_pid_list_len == 0:
            log.warning("The PID '{0}' is not in the Quack Cert Profile list; PID = 'DEFAULT' will be used.".format(pid))
            pid = 'DEFAULT'
        elif matching_pid_list_len > 1:
            log.warning("The PID '{0}' matches more than one entry in the Quack Cert Profile list.".format(pid))
            log.warning("Please correct the list or check the pid.  PID = 'DEFAULT' will be used.")
            pid = 'DEFAULT'
        else:
            pid = matching_pid_list[0]
            log.debug("Quack2 Cert Profile: {0}".format(pid))

        if len(Quack2.QUACK2_CERT_PROFILE_FIELDS) != len(Quack2.QUACK2_CERT_PROFILES[pid]):
            log.error("Quack2 Cert Profile for '{0}' does not match field count.".format(pid))
            return {}

        return {Quack2.QUACK2_CERT_PROFILE_FIELDS[i]: Quack2.QUACK2_CERT_PROFILES[pid][i]
                for i in range(0, len(Quack2.QUACK2_CERT_PROFILE_FIELDS))}

    @func_details
    def __get_hardware_data(self):
        """ Get QuackChip HW Data
        Sample output from diags:
        TLV Info    : 00 01 01 02 10 14 b9 92 0a 29 b1 b5 1b 90 f4 df 48 be 55 0c 73 cb e5 ec 18 be e6 05 ...
        Data-To-Sign : 51 82 4d 34 41 4b 03 05 a4 4d 6f 6e 20 4f 63 74 20 31 33 20 30 38 3a 31 36 3a 32 33 ...
        Quack Mfg Serial Number: 51 82 4d 34 41 4b 03 05 a4 4d 6f 6e 20 4f 63 74 20 31 33 20 30 38 3a 31 ...
        Controller Type        : 40 05
        System Serial Number   : 46 4f 43 31 38 35 31 58 31 33 59
        IUDI                   : 00 00 0d dd 00 00 0d dd 00 00 1a d9 00 00 1a d9
        PID                    : 57 53 2d 43 33 38 35 30 2d 32 34 53 00 00 00 00 00 00
        Digital Signature List : d9 04 40 c2 dc cb
        Quack Pub Key Signature: 93 39 7f 35 17 0f e9 3e 77 2e 65 fc 8e 6c 8b 33 b0 9c 5a b6 61 53 b1 77 ...

        :return:
        """

        self._uut_conn.send('SCCWriteToLockDownArea -instance:{0} -version:{1}\r'.
                             format(self.device_instance, self.quack2_data['cert_params']['scc_version_num']),
                             expectphrase=self._uut_prompt, timeout=30, regex=True)
        if 'PASSED' not in self._uut_conn.recbuf:
            raise Exception("SCCWriteToLockDownArea was unsuccessful.")

        self._uut_conn.send('SCCGetDataToSign -instance:{0} -version:{1}\r'.
                             format(self.device_instance, self.quack2_data['cert_params']['scc_version_num']),
                             expectphrase=self._uut_prompt, timeout=30, regex=True)

        pattern = r'([A-Za-z0-9 \-]+?)[ \t]*: ([0-9a-fA-F ]+)'
        m = re.compile(pattern).findall(self._uut_conn.recbuf)
        if m:
            log.debug("Capturing HW data...")
            d = {k.lower().replace(' ', '_').replace('-', '_'): v.strip() for k, v in m}
            self.quack2_data.update(d)

        # Check for expected lengths on HW data capture.
        keys = self.quack2_data['cert_params'].keys()
        keys.pop(keys.index('scc_version_num'))
        for k in keys:
            size = self.quack2_data['cert_params'][k]
            if k in self.quack2_data:
                cparam_len = len(self.quack2_data[k])
                if size != cparam_len:
                    raise Exception("Wrong size of Quack2 HW data '{0}': expected={1}, read={2}".
                                    format(k, size, cparam_len))
            else:
                raise Exception("Missing Quack2 HW data '{0}'".format(k))

        return True

    @func_details
    def __get_signature(self):
        """ Get QUACK Signature
        Request the quack key & cert data from the cesium service.
        :return:
        """

        log.debug("Host = {0}".format(aplib.get_hostname()))
        log.debug("User = {0}".format(aplib.apdicts.test_info.user_name))

        s = binascii.hexlify(self.quack2_data['uut_sernum'])
        self.quack2_data['uut_sernum_hex'] = ' '.join(s[i:i + 2] for i in range(0, len(s), 2))

        p = binascii.hexlify(self.quack2_data['uut_pid'])
        self.quack2_data['uut_pid_hex'] = ' '.join(p[i:i + 2] for i in range(0, len(p), 2))

        log.debug("Cesium 'generate_quack' inputs:")
        log.debug("serial_number            = {0}".format(self.quack2_data['uut_sernum_hex']))
        log.debug("product_id               = {0}".format(self.quack2_data['uut_pid_hex']))
        log.debug("smart_chip_serial_number = {0}".format(self.quack2_data['quack_mfg_serial_number']))
        log.debug("data_to_sign             = {0}".format(self.quack2_data['data_to_sign']))
        log.debug("lot_tlv                  = {0}".format(self.quack2_data['tlv_info']))
        log.debug("controller_id            = {0}".format(self.quack2_data['controller_type']))
        quack2_signature = \
            cesiumlib.generate_quack(serial_number=self.quack2_data['uut_sernum_hex'],
                                     product_id=self.quack2_data['uut_pid_hex'],
                                     smart_chip_serial_number=self.quack2_data['quack_mfg_serial_number'],
                                     data_to_sign=self.quack2_data['data_to_sign'],
                                     lot_tlv=self.quack2_data['tlv_info'],
                                     controller_id=self.quack2_data['controller_type'])
        self.quack2_data.update(quack2_signature)
        return True

    @func_details
    def __put_signature(self):
        """ Put QUACK Signature
        Program the quack key & cert data to the UUT quack device.
        :return:
        """

        self._uut_conn.send('SCCProgramDigitalSignaturesFromServer -instance:{0} -version:{1}\r'.
                             format(self.device_instance, self.quack2_data['cert_params']['scc_version_num']),
                             expectphrase='Enter Cookie Digital Signature', timeout=60, regex=True)

        self._uut_conn.send('{0}\r'.format(self.quack2_data['signature']),
                             expectphrase='Enter CM Public Key', timeout=60, regex=True)
        self._uut_conn.send('{0}\r'.format(self.quack2_data['public_key']),
                             expectphrase='Enter CM Certificate', timeout=60, regex=True)
        self._uut_conn.send('{0}\r'.format(self.quack2_data['certificate']),
                             expectphrase='Enter Epsilon TLV', timeout=60, regex=True)
        self._uut_conn.send('{0}\r'.format(self.quack2_data['epsilon_tlv']),
                             expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(3.0)
        if 'PASSED' not in self._uut_conn.recbuf:
            raise Exception("SCCProgramDigitalSignaturesFromServer was unsuccessful.")

        return True

    def __graceful_exit(self):
        self._uut_conn.send('\r')
        return
