""" ACT2 General Module
========================================================================================================================

Intended for general ACT2 programming/verification as product and product family agnostic
within the Enterprise Switching and IoT BU spaces.
The ACT2 signing process is highly integrated with the product diags so general applicability with this module
may be limited.  All products implementing ACT2 will have to use the TAM Lib for manipulating the secure objects
embedded within the ACT2 device.

An instantiation of this class applys to a single ACT2 device instance.

Prior setup of the Apollo server is necessary.
For Cesium 2.0 infrastructure:
    1. The ATOM utilities must be installed to the server (via rpm's),
    2. USB eToken installed on the physical server (VM solution TBD),
    3. USB eToken must be activated via "atom activate",
    4. The local client service "atomdaemon" must be running in background,
    5. Standard PID mappings must be set for the eToken Cert S/N (both Init & Re-SUDI)
       in the IAS db https://act2-mtv-2.cisco.com
For Cesium 3.0 infrastructure:
    1. Must have Apollo v98-1 or higher installed and running (for local ACT2 client),
    2. USB eToken installed on the physical server (VM solution TBD),
    3. USB eToken must be activated via "python apollocli.py --activateact2",
    4. Standard PID mappings must be set for the eToken Cert S/N (both Init & Re-SUDI)
       in the IAS db https://act2-mtv-2.cisco.com

    Service Call Path:  Apollo_server--> LocalCSA--> RegionalCSA--> PCM.cisco.com--> CBE
                                                                    (IT router)
                        The Apollo machine must be authorized at both the Local & Regional CSA's.

The ACT2 Signing process has the following steps:
    (see "sign_chip(...)" method for more details)
    1. Construct Authentication Data
       a. Cert Chain
       b. NONCE
       c. Signature
    2. Process the CLIIP
       a. Put it to the UUT
       b. Record the put status to CBE database
    3. Process the SUDI Certs
       a. Product-Cert, CA-Cert, Root-Cert
       b. Put it to the UUT
       c. Record the put status to CBE database


NOTE: For unittesting, the code is meant to run standalone (i.e. no Apollo container).
      Any Apollo functions must be by-passed (e.g. apollo.libs.locking).


Cesium 3.0 + Apollo CLI method:
    How to run get_cliip from the cmd line:

    python apollocli.py -a POST --url https://localhost/apollo/cesiumsvcs/act2/act2/get_cliip -i /tmp/get_cliip.json -c JSON

    The json file needs to contain this:
    {"root":{
        "chip_serial_number": "51824D34414B0305A44D6F6E204F63742031332030383A31363A323320035F19",
        "spaced_hex_out": false,
        "serial_number": "DUMMYSN1",
        "product_id": "DUMMYDUT",
        "apollo_version": "98-2",
        "client_ip": "10.89.133.27",
        "token_serial": "00b600ca"
        }
    }

========================================================================================================================
"""

# Python
# ------
import logging
import os
import parse
import time
import re
import sys
from collections import OrderedDict

# Apollo
# ------
from apollo.libs import lib as aplib
from apollo.libs import cesiumlib
from apollo.engine import apexceptions
from apollo.libs.dfal.dfal import DFaL
from apollo.libs import locking

# BU Lib
# ------
from ..utils.common_utils import func_details
from ..utils.common_utils import cesium_srvc_retry
from ..utils.common_utils import apollo_step
from ..utils.common_utils import readfiledata
from ..utils.common_utils import writefiledata
from ..utils.common_utils import shellcmd
from ..utils.common_utils import print_large_dict
from ..utils.common_utils import read_apollo_registry


__title__ = "ACT2 General Module"
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


class ACT2(object):
    """ ACT2
    """

    # Class settings: temporary until all servers are switched.
    APOLLO_VER_CESIUM3 = 98

    # These min-max versions are meant as a quality check for this module.
    # Any changes to the diags-TAM library or chip firmware should have already been qualified thru EDVT or CIT.
    # The version checks will alert the mfg process when this module has not been updated to reflect the
    # qualification process.
    # IMPORTANT: This is NOT necessarily meant to confirm the proper ACT2 device or proper diags version!
    LIB_VER_MIN = "0.1-36"
    LIB_VER_MAX = "3.3-9"
    CHIP_FW_MIN = "49.0.0"
    CHIP_FW_MAX = "81.0.0"
    CONSOLE_SEND_SIZE = 16
    BLOCK_SEND_SLEEP = 0.3
    MAX_SERVICE_ATTEMPTS = 5

    ATOM_PATH = "/usr/auto/ATOM"             # Path to atom utilities
    ATOM_LOG_PATH = "/tmp"                   # "/var/log/ATOMLogs"=offical path but need root permission
    ATOM_CONFIG = 'ATOMClientConfig.xml'

    STATUS_MAP = {
        '0x00': (6, 'Completed Install (0x00)', 'completed_install'),            # 6 success
        '0x01': (6, 'Install already completed (0x01).', 'completed_install'),   # 6 but may need resudi
        '0x26': (8, 'Error: Unknown (0x26)', 'failed_install'),                  # 8 but unknown ?
        '0x2e': (12, 'Error: HW (0x2e)', '2e_error'),                            # 11 (FW 1.2) or 12 (FW >=1.3)
        '0x2f': (12, 'Error: HW or FW? (0x2f)', '2f_error'),                     # 12 hard failure
        'Othr': (8, 'Failed Install (0x08 or other codes)', 'failed_install'),   # 8 or other; failed
    }
    __STAT_MAP_INDEX = {
        'Cesium 2.0': 2,
        'Cesium 3.0': 0
    }

    # Identity Protection map ONLY for ACT2 selection!
    # Defines both menu system and param system.
    IDPRO_MAP = {
        'ACT2': {'menu': '1', 'keytype': 0},
        'ACT2-RSA': {'menu': '1', 'keytype': 0},
        'ACT2-HARSA': {'menu': '3', 'keytype': 1},
        # 'ACT2-ECC': {'menu': '2', 'keytype': 2},
    }

    def __init__(self, mode_mgr, ud, **kwargs):
        """ Instantiate the class
        :param (obj) mode_mgr:
        :param (obj) ud:
        :param kwargs: Params needed specific to the UUT's diags CLI prompting for sending data to the console.
                       Typical input would look like the following below--
                       cert_chain_segments=2,
                       signature_segments=1,
                       cliip_segments=3,
        :return:
        """
        log.info(self.__repr__())

        # User properties
        self.device_instance = None                                                # ACT2 chip location.
        self.keytype = None                                                        # ACT2 keytype

        self._ud = ud
        self._mode_mgr = mode_mgr                                                  # UUT Mode Mgr instance
        self._uut_conn = self._mode_mgr.uut_conn                                   # Connection to UUT
        self._uut_prompt = self._mode_mgr.uut_prompt_map.get('STARDUST', '> ')     # UUT prompt

        self.cesium_key = kwargs.get('cesium_key', 'Cesium 3.0')                   # For Cesium 2.0/3.0 compatibility
        self.act2_data = OrderedDict()

        self.serial_number = kwargs.get('serial_number', None)
        self.product_id = kwargs.get('product_id', None)

        # Internal
        self.__unittest = kwargs.get('unittest', False)
        self.__verbose = kwargs.get('verbose', True)
        self.__stat_index = self.__STAT_MAP_INDEX.get(self.cesium_key, 0)

        # Initial Status
        self.act2_data['signing_status'] = None
        self.act2_data['cliip_status'] = None
        self.act2_data['sudi_status'] = None

        # Optional send data segment definitions
        # Use these to override the defaults (e.g. some IoT products only need 1 segment for all).
        self.act2_data['cert_chain_segments'] = kwargs.get('cert_chain_segments', 2)
        self.act2_data['signature_segments'] = kwargs.get('signature_segments', 1)
        self.act2_data['cliip_segments'] = kwargs.get('cliip_segments', 3)

        self.act2_mfg_session_file = os.path.join(ACT2.ATOM_LOG_PATH, "act2mfgsession_{uid}.id".format(uid=self._uut_conn.uid))

        m = parse.search('Apollo-{maj:0}-{min:1}', shellcmd("apollo version").strip('\n'))
        self.act2_data['apolloversion'] = int(m['maj']) if m else 0
        if not self.act2_data['apolloversion']:
            raise apexceptions.ApolloException("Problem obtaining Apollo version.")

        return

    def __str__(self):
        doc = "{0},  Lib Ver:{1}-{2},  Chip FW Ver:{3}-{4},  ConSndSize:{5}".\
            format(self.__repr__(),
                   ACT2.LIB_VER_MIN, ACT2.LIB_VER_MAX,
                   ACT2.CHIP_FW_MIN, ACT2.CHIP_FW_MAX,
                   ACT2.CONSOLE_SEND_SIZE)
        return doc

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ------------------------------------------------------------------------------------------------------------------
    # PROPERTIES
    #
    @property
    def cesium_key(self):
        return self.__cesium_key

    @cesium_key.setter
    def cesium_key(self, newvalue):
        self.__cesium_key = newvalue if newvalue in ACT2.__STAT_MAP_INDEX else 'Cesium 3.0'
        self.__cesium_index = ACT2.__STAT_MAP_INDEX.get(self.__cesium_key, 0)
        return

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def sign_chip(self, **kwargs):
        """ ACT2 Sign Chip
        Note: The uut_config is also used as input.
        :menu: (enable=True, name=ACT2, section=Diags, num=1, args={'menu': True})
        :param (dict) kwargs:
                      device_instance:
                      slot_number:
        :return (str): aplib.PASS/FAIL
        """
        # Process input
        self.device_instance = kwargs.get('device_instance', self._ud.device_instance)
        self.keytype = kwargs.get('keytype', 'ACT2')
        skip_chip_verify = kwargs.get('skip_chip_verify', False)
        skip_session_id = kwargs.get('skip_session_id', False)
        autoresudi = kwargs.get('autoresudi', False)
        menu = kwargs.get('menu', False)

        # TODO: check below condition, if safe then remove it
        # Sanity check.
        # self.__usage_sanity_check()

        if self.device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while not self.device_instance or not str(self.device_instance).isdigit():
                self.device_instance = aplib.ask_question("Device instance [int]:")
        self.device_instance = int(self.device_instance)
        if not 0 <= self.device_instance <= 10000:
            raise Exception("Device instance for ACT2 is invalid (must be 0 to 10000).")

        if not self.keytype or menu:
            self.keytype = aplib.ask_question("Select ACT2 Keytype:", answers=self.IDPRO_MAP.keys())

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode for QUACK2."

        # Arrange UUT required params
        # Ensure the PUID Keys are set appropriately:
        #   1. 'SYSTEM_SERIAL_NUM'/'SERIAL_NUM', 'MODEL_NUM'   for main units
        #   2. 'SN', 'VPN' for peripherals
        # Note: ACT2 in diags does not take params directly; it reads from flash internally.
        # To verify the UUT has sn, pid, mac since ACT2 extracts internally, just run the new Act2Auth diags cmd.
        self.uut_pid = self._ud.puid.pid
        self.uut_sernum = self._ud.puid.sernum

        # Perform the action
        log.debug("Device Instance = {0}".format(self.device_instance))
        log.debug("PID             = {0}".format(self.uut_pid))
        log.debug("S/N             = {0}".format(self.uut_sernum))

        result = self.__sign_chip(skip_chip_verify=skip_chip_verify,
                                  skip_session_id=skip_session_id,
                                  autoresudi=autoresudi)
        log.debug("ACT2 Sign Result = {0}".format(result))

        return aplib.PASS if result else (aplib.FAIL, "ACT2 signing error.")

    @apollo_step
    def authenticate(self, **kwargs):
        """ Confirm Auth
        :param kwargs:
        :return:
        """
        self.device_instance = kwargs.get('device_instance', self._ud.device_instance)
        self.keytype = kwargs.get('keytype', 'ACT2')
        menu = kwargs.get('menu', False)

        # Sanity check.
        self.__usage_sanity_check()

        if self.device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while not self.device_instance or not str(self.device_instance).isdigit():
                self.device_instance = aplib.ask_question("Device instance [int]:")
        self.device_instance = int(self.device_instance)
        if not 0 <= self.device_instance <= 10000:
            raise Exception("Device instance for ACT2 is invalid (must be 0 to 10000).")

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL, "Wrong mode for QUACK2."

        result = self.__confirm_authentication()

        return aplib.PASS if result else (aplib.FAIL, 'ACT2 did NOT authenticate!')

    # ==================================================================================================================
    # USER METHODS   (step support)
    # ==================================================================================================================
    @func_details
    def check_previous_session(self):
        """ Check Previous ACT2 Session
        If a previous ACT2 session was not properly closed, the stateful file will indicate
        this by presence and content.
        :return: tuple of (act2_mfg_session_id, act2_mfg_session_file)
        """
        act2_prev_mfg_session_id = ''

        log.debug("Looking for {0}".format(self.act2_mfg_session_file))
        if os.path.exists(self.act2_mfg_session_file):
            log.info("Previous ACT2 session found.")
            act2_prev_mfg_session_id = readfiledata(self.act2_mfg_session_file)[0]
            if not act2_prev_mfg_session_id:
                log.warning("A previous ACT2 session file was found but the data was unreadable/corrupted.")
                log.warning("This condition will be ignored and the file will be overwritten.")
        else:
            log.info("ACT2 session history is clean.")

        if act2_prev_mfg_session_id:
            log.debug("Previous ACT2 session ID = {0}".format(act2_prev_mfg_session_id))

        return act2_prev_mfg_session_id

    @func_details
    def close_session(self, act2_mfg_session_id=None):
        """ Close ACT2 Session
        Using the ACT2 session ID typically read from the stateful file, gracefully close the session.
        Remove any stateful file if present.
        :param act2_mfg_session_id:
        :return:
        """
        if not act2_mfg_session_id:
            if 'act2_mfg_session_id' in self.act2_data.keys():
                act2_mfg_session_id = self.act2_data['act2_mfg_session_id']
            else:
                log.info("No ACT2 session to close.")
                return True

        cmd = "ACT2CloseSession -instance:{inst} -session:{sid}\r".\
            format(inst=self.device_instance, sid=act2_mfg_session_id)
        self._uut_conn.send(cmd, expectphrase=self._uut_prompt, timeout=60, regex=True)
        if "ACT2 Session Ended" in self._uut_conn.recbuf or "status=0x0-ACT2_RC_OK" in self._uut_conn.recbuf:
            log.info("ACT2 Session has ended successfully.")
        elif "In Unknown mode" in self._uut_conn.recbuf:
            log.info("ACT2 in unknown mode; nothing to close.")
            log.warning("System may not be initialized.")
        elif "***ERR Session End FAILED" in self._uut_conn.recbuf:
            log.warning("ACT2 Session Close FAILED.")
            log.warning("UUT might need to be rebooted.")
            log.warning("Some close session failures can be ignored; attempt to continue...")
        else:
            log.error("ACT2 Session Close is indeterminant.")
            log.error("UUT must be rebooted!")
            raise Exception("ACT2 Close Session INDETERMINANT.")

        if os.path.exists(self.act2_mfg_session_file):
            shellcmd('rm -f {0}\r'.format(self.act2_mfg_session_file))

        self.act2_data['mfg_end_session_id'] = None

        return True

    @func_details
    def check_chip_info(self, skip=False):
        """ Check ACT2 Chip Info
        Use diags command to get chip version data and compare to what is currently allowed.
        Do this to ensure any ACT2 chip changes that were not tested are flagged by this check.
        Sample cli data given below:
        FW Version: 81.0.0
        Metal Rand: c6 12 cf 45 9f 09 71 c9 97 f5 b3 73 bf 42 00 34 93 6c 50 fe c7 5d f5
         7d ae 07 01 b1 8f 2a 47 69
        Last Reset Status: 00 00 00 00 00 00 00
        Reset Counts: 00 00 00 00 00 00
        Total RAM: 0
        Total ROM: 0
        :param skip:  Provided for debug only or workaround for some incomplete diags.
        :return:
        """
        if skip:
            log.warning("ACT2 Chip Version check was skipped.")
            log.warning("Ensure diags works to retrieve the proper ACT2 device information.")
            log.warning("Monitor the script process to ensure it completes.")
            log.warning("Skipping the FW check is for debug only and should be resolved prior to production release.")
            return True

        ret = False
        try:
            patterns = ['FW Version: {fw_version:0}\n',
                        'Metal Rand: {metal_rand_bytes:0}\n{mrb2:1}\n',
                        'Last Reset Status: {last_reset_stat:0}\n']
            cmd = "ACT2ChipInfo -instance:{0}\r".format(self.device_instance)
            self._uut_conn.send(cmd, expectphrase=self._uut_prompt, timeout=60, regex=True)
            time.sleep(1)
            self.__collect_data(patterns)

            if 'fw_version' in self.act2_data.keys():
                if ACT2.CHIP_FW_MIN <= self.act2_data['fw_version'] <= ACT2.CHIP_FW_MAX:
                    log.info("ACT2 Chip FW Version CONFIRMED.")
                    ret = True
                else:
                    log.error("Unknown ACT2 Chip FW version: '{0}'".format(self.act2_data['fw_version']))
                    log.error("This ACT2 chip FW version is outside the allowed versions: min='{0}'  max='{1}'".
                              format(ACT2.CHIP_FW_MIN, ACT2.CHIP_FW_MAX))
                    log.error("Ensure this new version is compatible with the existing process and product.")
                    log.error("Modification and review of this module is required.")
            else:
                log.error("Unable to obtain ACT2 Chip FW version.")
                log.error("Check the diag response.")

        except aplib.apexceptions.TimeoutException:
            log.error("Timeout on communication w/ ACT2 device.")
            log.error("Unable to retrieve ACT2 Chip info.")
            ret = False

        finally:
            return ret

    @func_details
    def get_act2_etoken(self, spaced_hex_out=False, lock=True):
        """ Get the S/N's for the eToken Dongle installed

        Apollo Sample:
        --------------
        [~]$ python /opt/cisco/constellation/apollocli.py act2 -tsn
        ACT2 HW token serial number: 00c42702
        ACT2 Certificate serial number: 396878037829816529
        [~]$

        Atomdaemon Sample:
        ------------------
        response={u'getTokenSNResponse': {u'@xmlns:ns1':
                                          u'http://atom.cisco.com/GetTokenSNs.xsd',
                                          u'AtomResponseHeader': {u'ResponseMessage': u'SUCCESS',
                                                                  u'ResponseCode': u'0'},
                                          u'@xmlns:ns2': u'http://atom.cisco.com/AtomHeaders.xsd',
                                          u'getTokenSNResponseBody': {u'TokenSN': u'00b600cf',
                                                                      u'TokenCertSN': u'0581fe7900000847'}}}

        :param boolean spaced_hex_out: default False, if True, hexadecimal strings in response will be spaced
        """

        def __run_cmd_for_etoken():
            if not self.__unittest and lock:
                with locking.named_priority_lock('atom_lock_{0}'.format('ACT2')):
                    log.debug("E-Token ATOM locked for request...")
                    out, err = shellcmd(cmd, combine=False)
            else:
                out, err = shellcmd(cmd, combine=False)
            return out, err

        token_sernum = None
        token_cert_sernum = None

        if self.act2_data['apolloversion'] >= self.APOLLO_VER_CESIUM3:
            log.debug("Apollo v{0} supports ACT2 built-in.".format(self.act2_data['apolloversion']))
            cmd = "python /opt/cisco/constellation/apollocli.py -tsn"
            out, err = __run_cmd_for_etoken()
            if err:
                log.error('stdout:{0}, stderr:{1}'.format(out, err))
                raise apexceptions.ApolloException('get_act2_etoken() failed: {0}, {1}'.format(cmd, err))
            m = re.search('(?s)ACT2 HW token serial number: ([\S]+).*?ACT2 Certificate serial number: ([0-9]+)', out)
            if m and len(m.groups()) == 2:
                token_sernum = m.groups()[0]
                token_cert_sernum = hex(int(m.groups()[1]))
            else:
                log.warning("Problem parsing eToken serial number data with Apollo cli.")
                log.warning("Check the output: {0}".format(out))

        else:
            log.debug("Apollo v{0} supports the external atomdaemon".format(self.act2_data['apolloversion']))
            cmd = "atom ACT2 ShowTokenSN --OutFormat XML"
            if spaced_hex_out is True:
                cmd += " --SpacedHexOut"
            log.debug("Getting E-Token data...")
            out, err = __run_cmd_for_etoken()
            if err:
                log.error('stdout:{0}, stderr:{1}'.format(out, err))
                raise apexceptions.ServiceFailure('get_act2_etoken() failed: {0}, {1}'.format(cmd, err))
            log.debug("Parsing E-Token data...")
            out = out.strip()
            try:
                responsedict = DFaL.xml2dict(out)
                if 'getTokenSNResponse' in responsedict.keys():
                    if 'AtomResponseHeader' not in responsedict['getTokenSNResponse'].keys():
                        msg = 'get_act2_etoken() failed: Bad Header - {0}'.format(responsedict)
                        raise apexceptions.ServiceFailure(msg)
                    elif 'ResponseMessage' not in responsedict['getTokenSNResponse']['AtomResponseHeader'].keys() or \
                            'ResponseCode' not in responsedict['getTokenSNResponse']['AtomResponseHeader'].keys():
                        msg = 'get_act2_etoken() failed: Bad Response - {0}'.format(responsedict)
                        raise apexceptions.ServiceFailure(msg)
                    else:
                        respcode = responsedict['getTokenSNResponse']['AtomResponseHeader']['ResponseCode']
                        respmesg = responsedict['getTokenSNResponse']['AtomResponseHeader']['ResponseMessage']
                        if respmesg != 'SUCCESS':
                            msg = 'get_act2_etoken() FAILED. Response Code:{0}, Msg:{1}'.format(respcode, respmesg)
                            log.error(msg)
                            raise apexceptions.ServiceFailure(msg)
                        else:
                            log.info("Response Code:{0}  Msg:{1}".format(respcode, respmesg))
                if 'getTokenSNResponseBody' not in responsedict['getTokenSNResponse'].keys():
                    msg = 'get_act2_etoken() failed: Bad Body - {0}'.format(responsedict)
                    raise apexceptions.ServiceFailure(msg)
                if 'TokenSN' in responsedict['getTokenSNResponse']['getTokenSNResponseBody'].keys():
                    token_sernum = responsedict['getTokenSNResponse']['getTokenSNResponseBody']['TokenSN']
                if 'TokenCertSN' in responsedict['getTokenSNResponse']['getTokenSNResponseBody'].keys():
                    token_cert_sernum = responsedict['getTokenSNResponse']['getTokenSNResponseBody']['TokenCertSN']
            except Exception as e:
                log.exception(e)
                log.error(out)
            finally:
                pass

        return token_sernum, token_cert_sernum

    # @func_details
    def get_cesium_server(self):
        self.act2_data['cesium_servers'] = None

        if self.act2_data['apolloversion'] >= self.APOLLO_VER_CESIUM3:
            log.debug("Apollo v{0} supports ACT2 built-in.".format(self.act2_data['apolloversion']))
            areg_data = read_apollo_registry()
            log.debug(areg_data.keys())
            cesium_servers = areg_data.get('Machine', {}).get('reportsTo', '').split(',')
            self.act2_data['cesium_servers'] = cesium_servers if len(cesium_servers) > 0 and cesium_servers[0] else None

        else:
            log.debug("Apollo v{0} supports the external atomdaemon".format(self.act2_data['apolloversion']))
            xml_data = readfiledata(os.path.join(ACT2.ATOM_PATH, ACT2.ATOM_CONFIG), raw=True)
            responsedict = DFaL.xml2dict(xml_data)
            if 'atom' in responsedict.keys() and 'CesiumServer' in responsedict['atom'].keys():
                self.act2_data['cesium_servers'] = responsedict['atom']['CesiumServer'].split(',')

        return self.act2_data['cesium_servers']

    # @func_details
    def ping_cesium_server(self):
        if not self.act2_data.get('cesium_servers', None):
            raise Exception("ERROR: Cesium Server is unknown; cannot ping connection.")

        results_list = []
        for cesium_server in self.act2_data['cesium_servers']:
            results = shellcmd("ping -c 5 {0}".format(cesium_server))
            if re.search("[1-5] received", results):
                results_list.append(True)
            else:
                results_list.append(False)
            log.debug("Cesium Server: {0} = {1}".format(cesium_server, results_list[-1:]))

        if not any(results_list):
            raise Exception("ERROR: Cesium Server connection is unreachable.\n{0}".format(results))

        log.info("Cesium Server minimum connection: GOOD.")
        return True

    @func_details
    def get_chip_serial_number(self):
        """ ACT2 Get Chip S/N
        :param (str) csn: ACT2 Chip S/N
        :return:
        """
        if self.__unittest:
            # Use a known good ACT2 chip s/n.
            # e.g. '5102125369700109E20000002DDA11672033302031353A30373A343120E86A41'
            csn = self.act2_data.get('chip_sernum', 'NONE')
            return csn

        ret = False
        try:
            patterns = ['CSN = {chip_sernum:0}\n']
            cmd = "ACT2GetCSN -instance:{0}\r".format(self.device_instance)
            self._uut_conn.send(cmd, expectphrase=self._uut_prompt, timeout=60, regex=True)
            time.sleep(1)
            self.__collect_data(patterns)

            if 'chip_sernum' in self.act2_data.keys():
                log.info("ACT2 Chip S/N: {0}".format(self.act2_data['chip_sernum']))
                ret = self.act2_data['chip_sernum']
            else:
                log.error("Unable to obtain ACT2 Chip S/N.")
                log.error("Check the diag response and HW.")

        except aplib.apexceptions.TimeoutException:
            log.error("Timeout on communication w/ ACT2 device.")
            log.error("Unable to retrieve ACT2 S/N.")
            ret = None

        finally:
            return ret

    @func_details
    def clear_act2_data(self):
        """ Clear ACT2 Data
        Only clear the run data.  Do not clear "setting" data.
        :return:
        """
        for key in ['chip_sernum', 'cert_chain', 'cert_chain_len', 'login_status', 'credential_status', 'nonce',
                    'challenge', 'challenge_len', 'signature', 'signature_len', 'signature_status',
                    'cliip', 'cliip_len', 'cliip_status', 'log_cliip_status',
                    'sudi_req_status', 'sudi_request_len', 'sudi_request', 'sudi', 'sudi_len',
                    'sudi_ca', 'sudi_ca_len', 'sudi_root', 'sudi_root_len', 'sudi_status', 'log_sudi_status',
                    'authenticated'
                    ]:
            if key in self.act2_data:
                self.act2_data[key] = None
        return

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNALS
    #
    def __sign_chip(self, skip_chip_verify=False, skip_session_id=False, autoresudi=False):
        """ ACT2 Sign Chip
        Main routine that governs the ACT2 device programming process.
        :param skip_chip_verify: (bool) flag to check the chip fw or skip the check
        :param skip_session_id: (bool) flag to not use ACT2 session ID feature; set True if feature not available
        :param autoresudi: (bool) Automatically resudi IFF CLIIP status indicates a previous CLIIP.
        :return:
        """
        ret = False
        max_display_length = 256
        try:
            # Get eToken data & Cesium Server
            self.act2_data['token_sn'], self.act2_data['token_cert_sn'] = self.get_act2_etoken()
            log.info("Token S/N           = {0}".format(self.act2_data['token_sn']))
            log.info("Token Cert S/N      = {0}".format(self.act2_data['token_cert_sn']))
            log.info("ACT2 Cesium Servers = {0}".format(self.get_cesium_server()))
            log.info("Product ID          = {0}".format(self.product_id)) if self.product_id else None
            log.info("Serial Number       = {0}".format(self.serial_number)) if self.serial_number else None

            # Provide prerequisit warning
            if not self.__unittest:
                log.info("UUT must have been properly system initialized (sysinit) to perform ACT2 signing!")
                log.debug("Checking UUT state...")
                self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

            # Check Cesium Server connection
            self.ping_cesium_server()

            # Check for a previous session
            if not skip_session_id:
                previous_session_id = self.check_previous_session()
                if previous_session_id:
                    self.close_session(previous_session_id)

            # START OF ACT2 SIGNING PROCESS
            # -----------------------------
            # 1. Get Preliminary ACT2 data
            if not self.check_chip_info(skip=skip_chip_verify):
                raise Exception("ACT2 Chip Info")
            self.get_chip_serial_number()
            self.__get_cert_chain()
            # 1.a. End here if this is called by unittesting.
            # Future unittesting needs to employ a diag simulator.
            if self.__unittest:
                log.warning("Unittest only operation for ACT2.")
                log.warning("Signing process will end.")
                max_display_length = 100
                log.warning("Unittest done; signing does NOT apply.")
                return self.act2_data
            # 1.b Finish prelim
            self.__get_cliip()

            # 2. Launch the UUT ACT2 diag interactive process
            if self.keytype not in ['ACT2', 'ACT']:
                # Not default so use explicit with keytype
                param = '-instance:{0} -keytype:{1}\r'.\
                    format(self.device_instance, ACT2.IDPRO_MAP.get(self.keytype, {}).get('keytype', 0))
            else:
                # Use default (no keytype param)
                param = '-instance:{0}\r'.format(self.device_instance)
            self._uut_conn.send("ACT2Sign {0}\r".format(param),
                               expectphrase="Enter cert chain length >", timeout=30, regex=True)
            if not self.__check_lib_version():
                # Close session and exit
                return self.__graceful_exit()

            # 3. Construct Authentication Data
            self.__put_cert_chain()
            self.__get_nonce()
            self.__construct_challenge_data()
            self.__get_signature()
            self.__put_signature()
            self.__save_session_id(skip_session_id=skip_session_id)

            # 4. Process CLIIP
            self.__put_cliip()
            self.__record_cliip_status()

            # 5. Process SUDI
            self.__set_sudi_type()
            if autoresudi:
                self.__get_autosudi()
            else:
                self.__get_sudi()
            self.__put_sudi()
            self.__record_sudi_status()
            self.__confirm_authentication()
            self.__finalize()

            ret = True
            self.act2_data['signing_status'] = True

        except Exception as e:
            log.critical(e)
            log.error("Cannot complete ACT2 Sign operation.")
            ret = False
            self.act2_data['signing_status'] = False
            # Deep debug: log.debug("recbuf='{0}'".format(self._uut_conn.recbuf))
            self.__graceful_exit(skip_session_id=skip_session_id)

        finally:
            print_large_dict(self.act2_data, max_display_length=max_display_length)
            return ret if not self.__unittest else self.act2_data

    def __check_lib_version(self):
        """ (INTERNAL) Check TAM Lib version used by Diags
        :return:
        """
        log.debug("Check Lib Ver...")
        ret = False
        patterns = ['Using ACT2 Library Version: {sw_lib_version:0}\n']
        self.__collect_data(patterns)

        if 'sw_lib_version' in self.act2_data.keys():
            log.info("ACT2 SW Lib Version: {0}".format(self.act2_data['sw_lib_version']))
            if ACT2.LIB_VER_MIN <= self.act2_data['sw_lib_version'] <= ACT2.LIB_VER_MAX:
                log.info("ACT2 SW Lib Version CONFIRMED.")
                ret = True
            else:
                log.error("Unknown ACT2 SW Lib version: '{0}'".format(self.act2_data['sw_lib_version']))
                log.error("This ACT2 SW Lib version is outside the allowed versions: min='{0}'  max='{1}'".
                          format(ACT2.LIB_VER_MIN, ACT2.LIB_VER_MAX))
                log.error("Ensure this new version is compatible with the existing process and product.")
                log.error("Modification and review of this module is required.")
        else:
            log.error("Unable to obtain ACT2 SW Lib Version.")
            log.error("Check the diag response and HW.")
        return ret

    def __get_cert_chain(self):
        """ (INTERNAL) Get Certificate Chain from Apollo Server
        :return:
        """

        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS, lock_enabled=True if not self.__unittest else False)
        def __get_act2_certificate_chain():
            return cesiumlib.get_act2_certificate_chain()

        log.debug("Get Cert Chain...")
        self.act2_data['cert_chain'], self.act2_data['cert_chain_len'] = __get_act2_certificate_chain()
        # deep debug: log.debug("Cert Chain='{0}'".format(self.act2_data['cert_chain']))
        log.debug("Cert Chain Length={0}".format(self.act2_data['cert_chain_len']))
        ret = True if len(self.act2_data['cert_chain']) >= 64 else False  # sanity check
        return ret

    def __put_cert_chain(self):
        """ (INTERNAL) Put Certificate Chain to Diags
        TAM Lib will process..
        :return:
        """
        log.debug("Put Cert Chain...")
        self.__data_sanity_check(['cert_chain', 'cert_chain_len'])

        # Step 1: Cert chain length w/ Login Status
        self._uut_conn.send("{0}\r".format(self.act2_data['cert_chain_len']),
                           expectphrase="Read (cert chain) >", timeout=30)
        patterns = ['A2L Mfg Login Init Status = {login_status:0}\n']
        self.__collect_data(patterns)

        # Step #2: Cert chain data send w/ Credential status
        self.__send_uut_data(self.act2_data['cert_chain'],
                             segments=self.act2_data['cert_chain_segments'],
                             interim_expectphrase=r"Read \(cert chain\) >",
                             final_expectphrase=r"Read signature >")
        patterns = ['A2L Credential Status = {credential_status:0}\n']
        self.__collect_data(patterns)

        log.debug("A2L Mfg Login Init Status = {0}".format(self.act2_data['login_status']))
        log.debug("A2L Credential Status = {0}".format(self.act2_data['credential_status']))
        return True

    def __get_nonce(self):
        """ (INTERNAL) Get UUT ACT2 Device NONCE
        :return:
        """
        log.debug("Get Nonce...")
        patterns = ['Nonce Number is: {nonce:0}\n']
        self.__collect_data(patterns)

        log.info("NONCE = '{0}'".format(self.act2_data['nonce']))
        ret = True if len(self.act2_data['nonce']) >= 64 else False  # sanity check
        return ret

    def __construct_challenge_data(self):
        """ (INTERNAL) Construct Challenge Data
        :return:
        """
        self.__data_sanity_check(['cert_chain', 'nonce'])

        self.act2_data['challenge'] = self.act2_data['nonce'] + self.act2_data['cert_chain']
        self.act2_data['challenge_len'] = len(self.act2_data['challenge']) / 2  # Byte length; not char length!
        log.debug("Challenge Data Length = {0}".format(self.act2_data['challenge_len']))
        return True

    def __get_signature(self):
        """ (INTERNAL) Get Signature
        :return:
        """
        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS)
        def __sign_act2_challenge_data(challenge_data, challenge_data_len):
            return cesiumlib.sign_act2_challenge_data(challenge_data, challenge_data_len)

        log.debug("Get Signature...")
        self.act2_data['signature'], self.act2_data['signature_len'] = \
            __sign_act2_challenge_data(challenge_data=self.act2_data['challenge'],
                                       challenge_data_len=self.act2_data['challenge_len'])
        log.debug("Signature Length = {0}".format(self.act2_data['signature_len']))
        # deep debug: log.debug("Signature = '{0}'".format(self.act2_data['signature']))
        ret = True if len(self.act2_data['signature']) >= 264 else False  # sanity check
        return ret

    def __put_signature(self):
        """ (INTERNAL) Put Signature to UUT
        :return:
        """
        log.debug("Put Signature...")
        self.__data_sanity_check(['signature'])
        self.__send_uut_data(self.act2_data['signature'],
                             segments=self.act2_data['signature_segments'],
                             final_expectphrase=r"CLIIP data length >")
        patterns = ['A2L Signature Status = {signature_status:0}\n',
                    'Manufacturing Session ID: {mfg_session_id:0}\n']
        self.__collect_data(patterns)

        log.debug("Signature Status = {0}".format(self.act2_data['signature_status']))
        log.info("Mfg Session ID = {0}".format(self.act2_data['mfg_session_id']))

        return True

    def __get_cliip(self):
        """ (INTERNAL) Get CLIIP of ACT2 Device S/N via Cesium service
        :return:
        """
        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS, lock_enabled=True if not self.__unittest else False)
        def __get_act2_cliip(chip_serial_no, serial_number, product_id):
            return cesiumlib.get_act2_cliip(chip_serial_no=chip_serial_no, serial_number=serial_number, product_id=product_id)

        log.debug("Get CLIIP...")
        self.__data_sanity_check(['chip_sernum'])

        try:
            log.debug("Get CLIIP attempt...")
            self.act2_data['cliip'], self.act2_data['cliip_len'] = \
                __get_act2_cliip(chip_serial_no=self.act2_data['chip_sernum'],
                                 serial_number=self.serial_number,
                                 product_id=self.product_id)
            if self.act2_data['cliip_len'] < 264:
                raise apexceptions.ServiceFailure("Bad CLIIP Length.")
            log.info("ACT2 CLIIP successful retrieval!")
            log.debug("ACT2 CLIIP Length = {0}".format(self.act2_data['cliip_len']))
        except apexceptions.ServiceFailure as ape:
            log.exception(ape.message)
            raise Exception("Cesium Service call: get_act2_cliip FAILED!")

        return True

    def __put_cliip(self):
        """ (INTERNAL) Put CLIIP to UUT
        This will cause TAM Lib to generate the SUDI Request data.
        Some ACT2 devices >= v1.5 can produce RSA or ECC SUDIs.
        If enabled, the diags will prompt for type BEFORE generating the SUDI Request data.
        **IMPORTANT**: If the CLIIP Status is NOT GOOD, the status MUST be recorded before the signing process
        is exceptioned
        :return:
        """
        log.debug("Put CLIIP...")
        self.act2_data['cliip_status'] = None
        self.__data_sanity_check(['cliip', 'cliip_len'])

        self._uut_conn.send("{0}\r".format(self.act2_data['cliip_len']),
                           expectphrase=r"Read CLIIP data >", timeout=30)

        self.__send_uut_data(self.act2_data['cliip'],
                             segments=self.act2_data['cliip_segments'],
                             interim_expectphrase=r'Read CLIIP data >',
                             final_expectphrase=[r"A2L CLIIP Status", r"CLIIP Install Succeeded"])
        log.debug("ACT2 CLIIP status found!")

        # Capture final output
        log.debug("Capturing cliip status...")
        patterns = ['A2L CLIIP Status = {cliip_status:0}\n']
        self.__collect_data(patterns)
        log.debug("A2L CLIIP Status = {0}".format(self.act2_data['cliip_status']))

        return True

    def __record_cliip_status(self):
        """ (INTERNAL) Record the CLIIP Status reported by the UUT
        Required by the IAS database.
        :return:
        """
        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS)
        def __record_act2_cliip_insertion_status(chip_serial_no, cliip_status, serial_number, product_id):
            return cesiumlib.record_act2_cliip_insertion_status(chip_serial_no=chip_serial_no,
                                                                cliip_status=cliip_status,
                                                                serial_number=serial_number,
                                                                product_id=product_id)

        log.debug("Record CLIIP status...")
        self.__data_sanity_check(['cliip_status'])

        if self.act2_data['cliip_status'] in ACT2.STATUS_MAP.keys():
            self.act2_data['log_cliip_status'] = ACT2.STATUS_MAP[self.act2_data['cliip_status']][self.__stat_index]
            msg = ACT2.STATUS_MAP[self.act2_data['cliip_status']][1]
        else:
            self.act2_data['log_cliip_status'] = ACT2.STATUS_MAP['Othr'][self.__stat_index]
            msg = ACT2.STATUS_MAP['Othr'][1]
        log.debug("Recording A2L Log Status (CLIIP) = {0} -> {1}".format(self.act2_data['log_cliip_status'], msg))

        record_success = False
        try:
            log.debug("ACT2 Rec CLIIP attempt...")
            result = __record_act2_cliip_insertion_status(chip_serial_no=self.act2_data['chip_sernum'],
                                                          cliip_status=self.act2_data['log_cliip_status'],
                                                          serial_number=self.serial_number,
                                                          product_id=self.product_id)
            log.debug("ACT2 Rec CLIIP result = {0}".format(result))
            record_success = True if result.response_mesg == 'SUCCESS' else False
        except apexceptions.ServiceFailure as ape:
            log.exception(ape.message)

        if not record_success:
            raise Exception("Cesium Service call: record_act2_cliip_insertion_status FAILED!")
        else:
            log.info("ACT2 CLIIP Record successful!")

        # Stop signing if the CLIIP status is not good; MUST do this AFTER recording the status!
        if self.act2_data['cliip_status'] not in ['0x00', '0x01']:
            raise Exception("ACT2 Signing halted due to CLIIP Status!")

        return True

    def __set_sudi_type(self):
        """ (INTERNAL) Optional SUDI Type to Set
        Supported on ACT2 device w/ FW ver >= 1.5
        This is an "in-process menu" during signing that was used on some older diag versions.
        Also see the "-keytype:0|1" param option.
        :return:
        """
        if "Enter sudi type option" in self._uut_conn.recbuf:
            log.debug("Selecting SUDI Type: {0} -> {1}".format(self.keytype,
                                                               ACT2.IDPRO_MAP[self.keytype]))
            self._uut_conn.send('{0}\r'.format(ACT2.IDPRO_MAP[self.keytype]['menu']), expectphrase='.*', timeout=30)
        return True

    def __get_autosudi(self):
        """ (INTERNAL) Automatically get SUDI or Re-SUDI
        Wrapper function.
        :return:
        """
        if self.act2_data['cliip_status'] == '0x01':
            return self.__get_sudi(resudi=True)
        else:
            return self.__get_sudi()

    def __get_sudi(self, resudi=None):
        """ (INTERNAL) Get SUDI Certs from the CBE via Cesium
        "SUDI Request:" must be captured from UUT.
        The diag output is still rolling from the put CLIIP operation, so recbuf continues to be filled.
        Check for the SUDI request status and operate accordingly.
        (Note: a 'SUDI type' option prompt can occur before this.)
        :param resudi: Set 'True' if a Re-SUDI is required,
                       Set 'False' for first SUDI.
                       set 'None' to prompt for Re-SUDI iff CLIIP status is non-zero.
        :return:
        """
        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS)
        def __get_act2_sudi_certificate(cms_data, serial_number, product_id):
            return cesiumlib.get_act2_sudi_certificate(cms_data=cms_data, serial_number=serial_number, product_id=product_id)

        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS)
        def __get_act2_resudi_certificate(cms_data, serial_number, product_id):
            return cesiumlib.get_act2_resudi_certificate(cms_data=cms_data, serial_number=serial_number, product_id=product_id)

        log.debug("Get SUDI...")
        sudi_request_is_good = False
        try:
            self._uut_conn.waitfor("SUDI Request Succeeded", timeout=60)
            sudi_request_is_good = True
        except apexceptions.TimeoutException as e:
            log.error("Did NOT get a 'SUDI Request Succeeded' message from diags.")
            log.error(e)
        except apexceptions.IdleTimeoutException as e:
            log.error("Did NOT get any SUDI response from diags; connection or unit appears hung.")
            log.error(e)
        except apexceptions.ConnectionFailure as e:
            log.error("Connection failure; cannot get status.")
            log.error(e)

        time.sleep(1)  # buffer settle time; needed?  Anomalous parse failures on recbuf.
        patterns = ['A2L SUDI Request Status = {sudi_req_status:0}\n',
                    'IDevID Req Length: {sudi_request_len:0}\n',
                    'SUDI Request: {sudi_request:0}\n']
        self.__collect_data(patterns)

        if not sudi_request_is_good:
            raise apexceptions.ApolloException("SUDI Request Failure.")

        self.__data_sanity_check(['sudi_req_status', 'sudi_request_len', 'sudi_request'])
        log.info("SUDI Request Succeeded!")
        log.debug("A2L SUDI Request Status = {0}".format(self.act2_data['sudi_req_status']))
        # deep debug: log.debug("A2L SUDI Request = '{0}'".format(self.act2_data['sudi_request']))
        log.debug("A2L SUDI Req Length: = {0}".format(self.act2_data['sudi_request_len']))

        if int(self.act2_data['sudi_request_len']) == len(self.act2_data['sudi_request']) / 2:
            log.debug("SUDI Request length confirmed.")
        else:
            log.debug("SUDI Request length NOT confirmed; there was a mismatch.")
            raise Exception("SUDI Request length mismatch.")

        if self.act2_data['cliip_status'] == '0x01' and resudi is None:
            log.warning("Previous CLIIP detected; may need a Re-SUDI.")
            if aplib.get_apollo_mode() == aplib.MODE_DEBUG:
                ans = aplib.ask_question(
                        'ACT2 Re-SUDI\n'
                        'A previous ACT2 CLIIP was detected. Choose carefully on which action to take.\n'
                        '1. ACT2 Re-SUDI is required if a previous SUDI was already programmed and the PID or S/N has been changed from the previous signing.\n'
                        '2. ACT2 SUDI is required if no previous SUDI was programmed but a previous CLIIP was detected.'
                        '   (This might occur if the process was interupted after the CLIIP was installed; very rare.)\n'
                        'Typically a Re-SUDI is not warranted.\n\n'
                        'Perform a "Re-SUDI" ([no]/yes)?', answers=['no', 'yes'], timeout=30)
            else:
                log.warning("Production default is NO Re-SUDI!")
                log.warning("If a Re-SUDI is needed; this must be done manually via DEBUG mode.")
                ans = 'no'
            resudi = True if ans == 'yes' else False
            if resudi:
                log.warning("Re-SUDI signing action was requested!")
            else:
                log.info("Standard SUDI signing action was requested.")

        try:
            if not resudi:
                log.info("Getting a SUDI cert...")
                self.act2_data['sudi'], self.act2_data['sudi_len'],\
                    self.act2_data['sudi_ca'], self.act2_data['sudi_ca_len'],\
                    self.act2_data['sudi_root'], self.act2_data['sudi_root_len'] \
                    = __get_act2_sudi_certificate(cms_data=self.act2_data['sudi_request'],
                                                  serial_number=self.serial_number,
                                                  product_id=self.product_id)
            else:
                log.info("Getting a Re-SUDI cert...")
                self.act2_data['sudi'], self.act2_data['sudi_len'],\
                    self.act2_data['sudi_ca'], self.act2_data['sudi_ca_len'],\
                    self.act2_data['sudi_root'], self.act2_data['sudi_root_len'] \
                    = __get_act2_resudi_certificate(cms_data=self.act2_data['sudi_request'],
                                                    serial_number=self.serial_number,
                                                    product_id=self.product_id)
            log.info("ACT2 Get SUDI Certs successful!")
            log.debug("A2L SUDI Lengths: Prod={0}, CA={1}, Root={2}".format(self.act2_data['sudi_len'],
                                                                            self.act2_data['sudi_ca_len'],
                                                                            self.act2_data['sudi_root_len'],))
        except apexceptions.ServiceFailure as ape:
            log.exception(ape.message)
            raise apexceptions.ApolloException("Cesium Service call: get_act2_sudi/resudi_certificate FAILED!")

        return True

    def __put_sudi(self):
        """ (INTERNAL) Put SUDI Certs to the UUT ACT2 Device
        SUDI chain consists of 3 certs w/ diag tool having 2 prompts:
         1. SUDI Cert data > = Product-Cert
         2. SUDI Cert Chain data > = CA-Cert + Root-Cert
        :return:
        """
        log.debug("Put SUDI...")
        self.act2_data['sudi_status'] = None
        self.__data_sanity_check(['sudi', 'sudi_len', 'sudi_ca', 'sudi_ca_len', 'sudi_root', 'sudi_root_len'])
        self._uut_conn.waitfor(r"Enter SUDI Cert length >", timeout=30)

        # Part 1
        self._uut_conn.send("{0}\r".format(self.act2_data['sudi_len']), expectphrase=r"Read SUDI Cert data >",
                           timeout=30)
        self.__send_uut_data(self.act2_data['sudi'], segments=1, final_expectphrase=r"Enter SUDI Cert Chain length >")

        # Part 2
        sudi_chain_len = self.act2_data['sudi_ca_len'] + self.act2_data['sudi_root_len']
        self._uut_conn.send("{0}\r".format(sudi_chain_len),
                           expectphrase=r"Read SUDI Cert Chain data >", timeout=30)
        self.__send_uut_data(self.act2_data['sudi_ca'], segments=1,
                             final_expectphrase='.*', join=True)
        self.__send_uut_data(self.act2_data['sudi_root'], segments=1,
                             final_expectphrase=[r"A2L SUDI Status", r"SUDI Install Succeeded"])
        log.debug("ACT2 SUDI status found!")

        # Capture final output
        log.debug("Capturing sudi status...")
        patterns = ['A2L SUDI Status = {sudi_status:0}\n',
                    'ACT2 Session Ended for ID {mfg_end_session_id:0}\n']
        self.__collect_data(patterns)

        try:
            log.debug("Checking for SUDI verification...")
            self._uut_conn.waitfor(r"SUDI Verified", timeout=120)
        except (apexceptions.TimeoutException, apexceptions.IdleTimeoutException) as e:
            log.error(e)
            log.error("The ACT2 SUDI Verification was NOT found.")
            if self.act2_data['sudi_status'] in ['0x00', '0x01']:
                log.warning("The SUDI status indicates GOOD; however, the verification was not confirmed.")
                log.warning("The SUDI status will be changed: Othr.")
                self.act2_data['sudi_status'] = 'Othr'
            return False

        return True

    def __record_sudi_status(self):
        """ (INTERNAL) Record SUDI Status
        Required by the IAS database.
        :return:
        """
        @cesium_srvc_retry(max_attempts=ACT2.MAX_SERVICE_ATTEMPTS)
        def __record_act2_sudi_cert_installation_status(chip_serial_no, sudi_status, serial_number, product_id):
            return cesiumlib.record_act2_sudi_cert_installation_status(chip_serial_no=chip_serial_no,
                                                                       sudi_status=sudi_status,
                                                                       serial_number=serial_number,
                                                                       product_id=product_id)

        log.debug("Record SUDI status...")
        self.__data_sanity_check(['sudi_status'])

        if self.act2_data['sudi_status'] in ACT2.STATUS_MAP.keys():
            self.act2_data['log_sudi_status'] = ACT2.STATUS_MAP[self.act2_data['sudi_status']][self.__stat_index]
            msg = ACT2.STATUS_MAP[self.act2_data['sudi_status']][1]
        else:
            self.act2_data['log_sudi_status'] = ACT2.STATUS_MAP['Othr'][self.__stat_index]
            msg = ACT2.STATUS_MAP['Othr'][1]

        log.debug("Recording A2L Log Status (SUDI) = {0} -> {1}".format(self.act2_data['log_sudi_status'], msg))

        record_success = False
        try:
            log.debug("ACT2 Rec SUDI attempt...")
            result = __record_act2_sudi_cert_installation_status(chip_serial_no=self.act2_data['chip_sernum'],
                                                                 sudi_status=self.act2_data['log_sudi_status'],
                                                                 serial_number=self.serial_number,
                                                                 product_id=self.product_id
                                                                 )
            log.debug("ACT2 Rec SUDI result = {0}".format(result))
            record_success = True if result.response_mesg == 'SUCCESS' else False

        except apexceptions.ServiceFailure as ape:
            log.exception(ape.message)

        if not record_success:
            raise Exception("Cesium Service call: record_act2_sudi_cert_installation_status FAILED!")
        else:
            log.info("ACT2 Record SUDI Status successful!")

        # Stop signing if the SUDI status is not good; MUST do this AFTER recording the status!
        if self.act2_data['sudi_status'] not in ['0x00', '0x01']:
            raise Exception("ACT2 Signing halted due to SUDI Status!")

        return True

    def __confirm_authentication(self):
        """
        Example if supported:
        ---------------------
        Hartley48U> Act2Authen
        <blah...blah...blah>
        Retrying last read that failed: 10
        Err: Strutt Register I2C Error detected in StruttSupOpStatus()
        ACT2 Authenticated!

        Example if NOT supported:
        -------------------------
        PL24_CR> Act2Authen
        ERR: Command not found: "Act2Authen"

        :return:
        """
        self.act2_data['authenticated'] = False
        if self.keytype != 'ACT2' and self.keytype != 'ACT':
            # Not default so use explicit
            param = '-instance:{0} -keytype:{1}\r'.format(self.device_instance,
                                                          ACT2.IDPRO_MAP.get(self.keytype, {}).get('keytype', 0))
        else:
            # Use default (no keytype param)
            param = '-instance:{0}\r'.format(self.device_instance)
        self._uut_conn.send("Act2Authen {0}\r".format(param),
                           expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(3)
        if 'ACT2 Authenticated' in self._uut_conn.recbuf:
            self.act2_data['authenticated'] = True
            log.info("ACT2 Authenticated!")
        elif 'Command not found' in self._uut_conn.recbuf:
            log.warning("The Act2Authen command is NOT available for this platform/diags version.")
        else:
            msg = "Act2 Authentication FAILED."
            log.error(msg)
            log.debug(self._uut_conn.recbuf)
            raise Exception(msg)

        return True

    def __finalize(self):
        """ (INTERNAL) Finalize the Signing process
        Ensure the SUDI Certs are verified by the diags tool.
        Remove session ID file.
        :return:
        """

        if self.act2_data['mfg_session_id'] == self.act2_data['mfg_end_session_id']:
            log.debug("ACT2 Mfg Session ENDED ({0})".format(self.act2_data['mfg_end_session_id']))
            if os.path.exists(self.act2_mfg_session_file):
                log.debug("Removing session file.")
                result = shellcmd('rm -f {0}\r'.format(self.act2_mfg_session_file))
                log.debug(result)
                self.act2_data['mfg_end_session_id'] = None
        else:
            log.debug("No mfg session id close confirmation; stateful session file will remain.")

        return True

    def __save_session_id(self, skip_session_id=False):
        """ (INTERNAL) Save ACT2 Session ID
        Use this as a backup in case the session is interrupted and the process is restarted.
        The old ID will be available to close versus having to reset the ACT2 chip.
        :param: skip_session_id (bool) skip this if True
        :return:
        """
        if skip_session_id:
            log.debug("Skip ACT2 session save.")
            return True

        if 'mfg_session_id' not in self.act2_data.keys():
            log.error("ACT2 Mfg Session ID is NOT present.")
            return False

        log.debug("Mfg Session File = {0}".format(self.act2_mfg_session_file))

        return writefiledata(self.act2_mfg_session_file, self.act2_data['mfg_session_id'])

    def __graceful_exit(self, skip_session_id=False):
        """ (INTERNAL) Graceful Exit of the ACT2 session in Diags.
        :return:
        """
        log.debug("Performing graceful exit...")
        done = False
        ret = False
        lp_cnt = 0
        try:
            while not done and lp_cnt < 10:
                try:
                    self._uut_conn.send("\r", expectphrase='.*', timeout=30, regex=True)
                except (apexceptions.TimeoutException, apexceptions.IdleTimeoutException) as e:
                    log.warning(e)
                    log.warning("The unit is unresponsive; trying one more time.")
                    self._uut_conn.send("\r", expectphrase='.*', timeout=30, regex=True)
                time.sleep(4)
                if re.search(self._uut_prompt, self._uut_conn.recbuf):
                    log.debug("ACT2 sign graceful exit complete.")
                    done = True
                    ret = True
                elif " # " in self._uut_conn.recbuf:
                    log.warning("Something unexpected happened; UUT appears to be in Linux mode.")
                    self._uut_conn.send("reset\r", expectphrase='.*', timeout=30, regex=True)
                    done = True
                elif "length >" in self._uut_conn.recbuf:
                    log.debug("ACT2 exiting...")
                    # Provide an invalid length to force exit.
                    self._uut_conn.send("1\r", expectphrase='.*', timeout=30, regex=True)
                    time.sleep(1)
                else:
                    log.debug("ACT2 exiting ...")
                    # Just hit return for typical data entry; usually has to occur twice.
                    self._uut_conn.send("\r", expectphrase='.*', timeout=30, regex=True)
                    time.sleep(1)
                lp_cnt += 1

            if not skip_session_id:
                log.debug("Graceful exit will attempt to close the session...")
                self._uut_conn.send("\r", expectphrase='.*', timeout=30, regex=True)
                time.sleep(1)
                if self._uut_prompt in self._uut_conn.recbuf:
                    log.debug("Diag ready; prompt was detected...")
                    self.close_session()

        except Exception as e:
            log.error(e)
            log.error("The graceful exit did NOT exit gracefully; something unexpected happened.")
            log.error("The UUT state cannot be guaranteed; please proceed with caution.")
        finally:
            return ret

    def __send_uut_data(self, data, segments=1,
                        interim_expectphrase='.*', final_expectphrase='.*', join=False, verbose=False):
        """
        Send ASCII Hex data to the UUT via the console when prompted by diag interface..
        Some diags breaks up the input into segments (typically 2 or 3); this funtion provides a means to
        divide the input accordingly.
        Some diags also can only handle small bursts of data so the console sendsize is set as a class parameter
        and used by this function.
        :param data: Data to send to the UUT.
        :param segments: Total number of divided segments in the data corresponding to prompting diag interface.
        :param interim_expectphrase: Response between segments.
                                     Must comply w/ regex expression rules
        :param final_expectphrase: Last response after all segments and residual data.
                                   Must comply w/ regex expression rules
        :param join: Flag to allow more data for append (no carriage return at end)
        :param verbose:
        :return:
        """
        def __send_block(s_data, s_blocks, s_size, s_offset, noexpectphrase=True):
            """
            Internal helper function for sending small blocks of data to the UUT.
            :param s_data: Data to send to the UUT.
            :param s_blocks: Total number of 'sendsize' blocks in the data segment.
            :param s_size: Amount of chars to send to UUT console.
            :param s_offset: Slice start point of ASCII hex char index in the data.
            :param noexpectphrase: Just what it means.
            :return:
            """
            j = s_offset
            for block in range(0, s_blocks):
                i = block * s_size + offset
                j = (block + 1) * s_size + s_offset
                if verbose:
                    log.debug("{0}:{1}".format(i, s_data[i:j]))
                if noexpectphrase:
                    self._uut_conn.send(s_data[i:j], expectphrase=None, timeout=120, idle_timeout=90, regex=True)
                else:
                    self._uut_conn.send(s_data[i:j], expectphrase='.*', timeout=90, regex=True)
                time.sleep(ACT2.BLOCK_SEND_SLEEP)
            return j

        log.debug("send_uut_data...")
        # Init operating varsACT2Sign
        sendsize = ACT2.CONSOLE_SEND_SIZE
        data_len = len(data)
        blocks = data_len / (sendsize * segments)
        current_index = 0
        remaining_data = data_len % (sendsize * segments)
        log.debug("Data Length={0}".format(data_len))
        log.debug("Blocks={0}".format(blocks))

        # Process data per the segments requested.
        # Deep debug: log.debug("interim = '{0}'".format(interim_expectphrase))
        # Deep debug: log.debug("final   = '{0}'".format(final_expectphrase))
        for segment in range(0, segments):
            offset = segment * blocks * sendsize
            log.debug("Segment = {0}   (offset:{1})".format(segment, offset))
            current_index = __send_block(data, blocks, sendsize, offset)
            if segment != segments - 1:
                # Send a carriage return if this is NOT the last segment.
                self._uut_conn.send("\r", expectphrase=interim_expectphrase, timeout=120, regex=True)

        if remaining_data > 0:
            remaining_blocks = (data_len - current_index) / sendsize
            offset = current_index
            log.debug("Remaining Blocks={0}".format(remaining_blocks))
            last = __send_block(data, remaining_blocks, sendsize, offset)
            if last < data_len:
                sendsize = data_len - last
                log.debug("Remaining Data Length={0}".format(sendsize))
                __send_block(data, 1, sendsize, last)

        if not join:
            # Send final carriage return if no other data will join the 'send session' to the UUT.
            self._uut_conn.send("\r", expectphrase=final_expectphrase, timeout=120, regex=True)

        return

    def __data_sanity_check(self, keylist):
        """ (INTERNAL) Data Sanity Check
        Use to verify existence and content of ACT2 data.
        :param keylist:
        :return:
        """
        if type(keylist) is not list:
            raise Exception("Coding error: 'keylist' param must be a list.")
        for item in keylist:
            if item not in self.act2_data.keys():
                raise Exception("ACT2 Sanity Check: item '{0}' is missing.".format(item))
            elif not self.act2_data[item]:
                raise Exception("ACT2 Sanity Check: data for '{0}' is null.".format(item))
        log.debug("Sanity check on {0}: GOOD.".format(keylist))
        return True

    # TODO: check below condition, if safe then remove it
    def __usage_sanity_check(self):
        # Sanity check.
        identity_protection_type = self._ud.uut_config.get('identity_protection_type', None)
        if not identity_protection_type:
            log.error("Unknown Identity Protection type.")
            log.error("Ensure the product definition is loaded and has an 'identity_protection_type' entry.")
            return aplib.FAIL, "IdPro undefined."
        if 'ACT2' not in identity_protection_type:
            log.warning("The UUT Identity Protection Type ='{0}'.".format(identity_protection_type))
            log.warning("Nothing to do here (not ACT2).")
            # Note: Skip since ACT2 does not apply and we don't want to penalize the menu selection (if called).
            return aplib.SKIPPED

    def __collect_data(self, patterns, verbose=False):
        """ (INTERNAL) Collect Data
        :param patterns: List of patterns to use for parsing and collecting.
        :return:
        """
        if type(patterns) is not list:
            log.error("Coding error: 'patterns' param must be a list")
            return False
        # Pause for recbuf and collect
        time.sleep(2.0)
        for pattern in patterns:
            found_items = parse.search(pattern, self._uut_conn.recbuf)
            if found_items:
                for key in found_items.named.keys():
                    if verbose:
                        log.debug('Found {0} = {1}'.format(key, found_items[key]))
                    self.act2_data[key] = self.__strip_eol(found_items[key])
        return True

    @staticmethod
    def __strip_eol(string):
        # Ensure removal of extraneous control characters on end of line (eol).
        return string.strip('\n').strip('\r').strip('\n')

# ----------------------------------------------------------------------------------------------------------------------
sample_act2_transaction = \
    """
Sample ACT2 Process console output (3K)
---------------------------------------


Arbelos24P>

Arbelos24P> ACT2ChipInfo -instance:0
FW Version: 49.0.0
Metal Rand: e7 1a ba 07 10 e7 1f 27 c0 16 73 98 69 c2 bb 0d b8 b7 1f 18 db 58 fe
 35 b1 64 2f 15 88 59 f0 81
Last Reset Status: 00 00 00 00 00 00 00 Reset Counts: 00 00 00 00 00 00 Total RAM: 0 Total ROM: 0

Arbelos24P>

Arbelos24P> ACT2GetCSN -instance:0

Already in simple mode.
CSN = 5102125369700109E20000002DDA11672033302031353A30373A343120E86A41


Arbelos24P> ACT2Sign -instance:0
Using ACT2 Library Version: 0.1-36
CSN = 5102125369700109E20000002DDA11672033302031353A30373A343120E86A41


 Enter cert chain length > [0]:  3072

cert chain length: 3072

A2L Mfg Login Init Status = 0x00

 Read (cert chain) > 308204573...[blah,blah,blah]...C0F35A9C478

..count 0; total bytes entered so far is 3104

 Read (cert chain) > E35076DB2...[blah,blah,blah]...C623828B45

..count 1; total bytes entered so far is 6144

A2L Credential Status = 0x00

Nonce Number is: 4da3883501e05600a24c193d29ca4dd1f40dc4c4ee7ed31d9d3701082861e157

 Read signature > 3DAF19C3F3...[blah,blah,blah]...1790D1DFAF417A

A2L Signature Status = 0x00

Manufacturing Session ID: 0xA9194C4E

 Enter CLIIP data length > [0]:  3968

cliip length: 3968

 Read CLIIP data > BFF2C974C092...[blah,blah,blah]...6518AA6FAF

..count 0; total bytes entered so far is 2656

 Read CLIIP data > 4F965E43FDA0...[blah,blah,blah]...B513507B95C

..count 1; total bytes entered so far is 5312

 Read CLIIP data > 3DFA7D2852FC...[blah,blah,blah]...258DB8ECA6C

..count 2; total bytes entered so far is 7936

A2L CLIIP Status = 0x01

CLIIP Install Succeeded!!

-------
{POSSIBLE ACT2 1.5 Option ECC or RSA would go here.   (bborel)}
Enter sudi type option (1-2): [1]:
-------

A2L SUDI Request Status = 0x00

SUDI Request: 30820d2706092a86...[blah,blah,blah]...600c778ef1d2

IDevID Req Length: 3371
SUDI Request Succeeded!!

 Enter SUDI Cert length > [0]:  907

SUDI Cert length: 907

 Read SUDI Cert data > 308203873082...[blah,blah,blah]...232444F1BF

..count 0; total bytes entered so far is 1814

 Enter SUDI Cert Chain length > [0]:  1927

SUDI Cert Chain length: 1927

 Read SUDI Cert Chain data > 3082043c308...[blah,blah,blah]...e8119e10b35

..count 0; total bytes entered so far is 3854

A2L SUDI Status = 0x00

> SUDI Install Succeeded

> ACT2 Session Ended for ID 0xA9194C4E

A2L SUDI Cert Chain Read Object Info Status = 0x00

A2L Object Read Status = 0x00

[0x00000000] 3082043c30820324a003020102020a61096e7d00000000000c300d06092a8648
[0x00000020] 86f70d0101050500303531163014060355040a130d436973636f205379737465
...[blah,blah,blah]...
[0x00000760] 91e0e0973c326805854bd1f757e2521d931a549f0570c04a71601e430b601efe
[0x00000780] a3ce8119e10b35

A2L SUDI Cert Object Read Info Status = 0x00

A2L Object Read Status = 0x00

[0x00000000] 308203873082026fa0030201020203019cf3300d06092a864886f70d01010b05
[0x00000020] 003027310e300c060355040a1305436973636f311530130603550403130c4143
...[blah,blah,blah]...
[0x00000360] d0c1e1728e0c6eef6c439b8e0db78338e8f2effad508f988d2ad494e8e3f0468
[0x00000380] dc17f64ae4553ee644f1bf

> SUDI Verified

Arbelos24P>
"""

sample_application_for_retry = """
attempts = 0
while attempts < 3:
    attempts += 1
    log.debug("ACT2 Sign Attempt #{0}".format(attempts))
    if act2.sign_chip(autoresudi=True):
        log.info("ACT2 Sign PASSED!.")
        break
    log.warning("ACT2 Sign attempt UNSUCCESSFUL.")
    log.debug("Login Status = {0}".format(act2.act2_data['login_status']))
    log.debug("Sig Status   = {0}".format(act2.act2_data['signature_status']))
    log.debug("Cred Status  = {0}".format(act2.act2_data['credential_status']))
    log.debug("CLIIP Status = {0}".format(act2.act2_data['cliip_status']))
    log.debug("SUDI Status  = {0}".format(act2.act2_data['sudi_status']))
    act2.clear_act2_data()
else:
    log.error("ACT2 Sign FAILED.")
    return lib.FAIL
"""
