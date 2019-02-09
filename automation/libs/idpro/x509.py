""" X.509 General Module
========================================================================================================================

Intended for general X.509 SUDI programming as product and product family agnostic
within the Enterprise Switching BU spaces.

The X.509 AP SUDI Key and Cert are stored to the unit.  This SUDI is used exclusively by IOS for Access Point (AP)
authentication.  It is different from the ACT2 SUDI and it is stored differently.

You must supply an  ACT2/Quack2 device instance number and the request type when calling the function.
PID, System S/N, and MAC addr are required but can be obtained automatically from the UUT assuming the params
are already programmed.

Sample sequences given below on a GEN2 product that requires two SUDI certs (SHA1 & SHA256)
on the motherboard:
  1) SHA1 for QUACK2 or ACT2
  --------------------------
    sequence|req_type|method|cert_type|key_size = STANDARD|PROD|KEY|SHA1|1024

  2.a) SHA256 for QUACK2
  ----------------------
    A separate operation in the Linux kernel is required to support SHA256
    Mode = "LINUX"
    Mount = "/dev/sda5" to "/tmp"
    Create the following files:  sudi_key_hdr_v3, sudi_key_data_v3, sudi_cert_hdr_v3, sudi_cert_data_v3
    Mode = "STARDUST"
    sequence|req_type|method|cert_type|key_size = STANDARD|PROD|KEY|SHA256|2048

  2.b) SHA256 for ACT2
  --------------------
    A separate operation in the kernel is required to support SHA256
    Mode = "LINUX"
    Mount = "/dev/sda5" to "/tmp"
    Create the following files:  sudi_cert_hdr_v3, sudi_cert_data_v3
    Mode = "STARDUST"
    sequence|req_type|method|cert_type|key_size = STANDARD|PROD|KEY|SHA256|2048

  3.) SHA256-2099 for ACT2
  ------------------------
    A separate operation in the kernel is required to support SHA256
    Mode = "LINUX"
    Mount = "/dev/sda5" to "/tmp"
    Create the following files:  sudi_cert_hdr_v3, sudi_cert_data_v3
    Mode = "STARDUST"
    sequence|req_type|method|cert_type|key_size = STANDARD|PROD|KEY|CMCA3|2048

Notes:
    The new SUDI-2099 Initiative changes the cert expire date and requires a new call to a specific URL from CMCA;
    specifically cmca3.  This only supports sha256.

Recommendations:
    For speed of operation, it is highly recommended the target unit have a maximum console speed setting
    BAUD = 115200 (approx 4 minute completion time)
    BAUD = 9600   (approx 18 minute completion time)

WARNINGS:
    1. If legacy(sha1) SUDI is to be programmed alongside ACT2 on the same device, then perform Legacy SUDI first
       to preclude reboot requirement.
    2. If an ACT2 chip is used and the last operation was for sha256 SUDI or ACT2 programming, then sha1 SUDI cannot
       be programmed without a chip reset! (Some chip resets require a power cycle.)

========================================================================================================================
"""

# Python
# ------
import os
import re
import logging
import time
import sys
from collections import OrderedDict
from collections import namedtuple

# BU Lib
# ------
from ..utils.common_utils import validate_mac_addr
from ..utils.common_utils import validate_sernum
from ..utils.common_utils import validate_pid
from ..utils.common_utils import func_details
from ..utils.common_utils import print_large_dict
from ..utils.common_utils import cesium_srvc_retry
from ..utils.common_utils import apollo_step


# Apollo
# ------
from apollo.libs import lib as aplib
from apollo.libs import cesiumlib
from apollo.engine import apexceptions


__title__ = "X.509 SUDI General Module"
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


class X509Sudi(object):

    X509_LOG_PATH = "/tmp"
    X509_CONSOLE_SEND_SIZE = 64
    X509_MAX_SERVICE_ATTEMPTS = 5

    X509_REQUEST_TYPES = ['PROD', 'TEST']
    X509_CERT_METHODS = ['KEY', 'CERT_ONLY']
    X509_SUDI_HASH_TYPES = ['SHA1', 'SHA256', 'CMCA', 'CMCA2', 'CMCA3']

    # Selection list for an ask menu when the hash type is NOT provided.
    # The list includes both the hash name and the key size.
    HashDesc = namedtuple('HashDesc', 'hash size')
    shsl = [('SHA1', HashDesc('sha1', 1024)),
            ('SHA256', HashDesc('sha256', 2048)),
            ('CMCA', HashDesc('cmca', 1024)),
            ('CMCA2', HashDesc('cmca2', 2048)),
            ('CMCA3', HashDesc('cmca3', 2048))]
    SUDI_HASH_SELECT_LIST = OrderedDict(shsl)

    # Programming Sequence of X.509 certs based on PID.
    # The sequences are established by the IOS for a given PID family.
    # Some PIDs adhere to the Cisco standard (seq = 'STANDARD') and others do not!
    # See the method '__map_sequence_to_pid()' for more sequence details.
    # Although the PIDs below are hard-coded to this module, the class can override this table by providing both
    # sequence and prog_version explicitly.  The table is a convenience item and provides historical context.
    PidSeqMap = namedtuple('PidSeqMap', 'pid_pattern sequence prog_version')
    PID_SEQ_MAP = [
        PidSeqMap("WS-C3850.*", 'STANDARD', 'MULTICERT'),
        PidSeqMap("WS-C3650.*", 'STANDARD', 'MULTICERT'),
        PidSeqMap("WS-C3750.*", 'REVERSE', 'LEGACY'),
        PidSeqMap("ME-3600X.*", 'REVERSE', 'MULTICERT'),
        PidSeqMap("ME-3800X.*", 'REVERSE', 'MULTICERT'),
        PidSeqMap("WS-C3290.*", 'STANDARD', 'MULTICERT'),
        PidSeqMap("AIR-CT57.*", 'STANDARD', 'MULTICERT'),
        PidSeqMap("IE-2000U.*", 'REVERSE', 'MULTICERT'),
        PidSeqMap("IE-3010.*", 'REVERSE', 'MULTICERT'),
        PidSeqMap(".*", 'STANDARD', 'MULTICERT'),
    ]

    # File map for SHA256 hash based on IdPro Type.
    # These files are required since there is not enough eeprom space in the ACT2 or Quack2 chip in mode 1 to store
    # the larger certs and key for SUDI.
    SHA256_HIDDEN_FILE_MAP = {
        'QUACK2': ['sudi_key_hdr_v3', 'sudi_key_data_v3', 'sudi_cert_hdr_v3', 'sudi_cert_data_v3'],
        'ACT2': ['sudi_cert_hdr_v3', 'sudi_cert_data_v3'],
        'ACT2-RSA': ['sudi_cert_hdr_v3', 'sudi_cert_data_v3'],
        'ACT2-HARSA': ['sudi_cert_hdr_v4', 'sudi_cert_data_v4'],
        # 'ACT2-ECC': ['sudi_cert_hdr_v5', 'sudi_cert_data_v5']
    }

    # Cert programming sequence
    SUDI_SEQUENCE = {
        'STANDARD': ['x509_certificate', 'sub_ca_certificate', 'root_certificate'],
        'REVERSE': ['root_certificate', 'sub_ca_certificate', 'x509_certificate']
    }

    X509_DATA_KEYS = ['client_certificate_signing_request',
                      'x509_certificate',
                      'private_key',
                      'sub_ca_certificate',
                      'root_certificate',
                      'ra_encryption_certificate',
                      'ra_signing_certificate']

    def __init__(self, mode_mgr, ud, **kwargs):
        """ Instantiate the class
        :param (obj) mode_mgr:
        :param (obj) ud: 
        :param kwargs: UUT & SUDI params needed for the x509 cesiumlib call.
               Typical input would look like the following below--
               Required
               --------
               uut_mac='BA:DB:AD:BA:DB:AD',
               uut_sernum='TST12345678',
               uut_pid='WS-C0000-00',
               keytype='ACT2',                    (valid types = ACT2, ACT2-ECC QUACK2)
               x509_sudi_request_type='PROD',     (valid types = PROD, TEST)
               x509_sudi_cert_method='KEY',       (valid types = KEY, CERT_ONLY)
               x509_sudi_hash=['SHA1', 'SHA256']  (valid types = SHA1, SHA256, [SHA1, SHA256], CMCA, CMCA2,
                                                                 CMCA3, [SHA2, CMCA3], etc.) **order is important**
               Optional
               --------
               uut_cert_sequence='STANDARD'       (valid types = STANDARD, REVERSE)
               uut_prog_version='MULTICERT'       (valid types = MULTICERT, LEGACY)
               hidden_device='/dev/sda5'          (product dependent)
               hidden_mount_dir=/tmp              (MUST match diags internal function)

        :return:
        """
        log.info(self.__repr__())

        # Explicit class init params
        self.device_instance = None                                                # ACT2 chip location.
        self.keytype = None                                                        # X.509 SUDI keytype

        self._mode_mgr = mode_mgr                                                  # UUT Mode Manager instance
        self._uut_conn = self._mode_mgr.uut_conn                                   # Connection to UUT
        self._uut_prompt = self._mode_mgr.uut_prompt_map.get('STARDUST', '> ')     # UUT prompt
        self._ud = ud
        self._linux = kwargs.get('linux', None)
        self.__unittest = kwargs.get('unittest', False)
        self.__verbose = kwargs.get('verbose', True)

        # UUT related Parameters
        self.x509_data = OrderedDict()
        self.x509_data['uut_mac'] = self.__format_mac(kwargs.get('uut_mac', ''))       # UUT MAC
        self.x509_data['uut_sernum'] = kwargs.get('uut_sernum', '')                    # UUT main s/n
        self.x509_data['uut_pid'] = kwargs.get('uut_pid', '')                          # UUT Base PID ! (not Cfg PID)
        self.x509_data['hidden_mount'] = self._linux.MountDescriptor(
                kwargs.get('hidden_device', self._ud.uut_config.get('hidden_device', '/dev')),
                kwargs.get('hidden_mount_dir', self._ud.uut_config.get('hidden_mount_dir', '/tmp')))

        # X.509 Parameters
        self.x509_data['request_type'] = kwargs.get('x509_sudi_request_type', 'PROD')  # 'PROD' or 'TEST'
        self.x509_data['cert_method'] = kwargs.get('x509_sudi_cert_method', 'KEY')     # 'KEY' or 'CERT_ONLY'
        self.x509_data['sudi_hash'] = kwargs.get('x509_sudi_hash', [])                 # 'SHA1', 'SHA256', or a list
        self.x509_data['public_key'] = kwargs.get('x509_sudi_public_key', None)        # Used w/ 'CERT_ONLY' method

        # Internal params
        self.x509_data['key_size'] = []                                                # 1024, 2048, ...
        self.x509_data['common_name'] = ''                                             # Derived (typically PID-MAC)
        self.x509_data['hidden_files'] = None                                          # Set by map based on type
        self.x509_data['uut_cert_sequence'] = kwargs.get('uut_cert_sequence', None)    # Cert order (internal)
        self.x509_data['uut_prog_version'] = kwargs.get('uut_prog_version', None)      # Program version (internal)
        self.x509_data['current_mount'] = None

        self.x509_session_file = os.path.join(X509Sudi.X509_LOG_PATH, "x509mfgsession_{uid}.id".format(uid=self._uut_conn.uid))

        return

    def __str__(self):
        doc = "{0}".format(self.__repr__())
        return doc

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ------------------------------------------------------------------------------------------------------------------
    # USER STEPS
    #
    @apollo_step
    def sign_certificate(self, **kwargs):
        """ X509 SUDI Sign
        Note: The uut_config is also used as input.
        :menu: (enable=True, name=X509 SUDI, section=Diags, num=1, args={'menu': True})
        :param (dict) kwargs: 'device_instance'
        :return (str): aplib.PASS/FAIL
        """
        # Process input
        self.device_instance = kwargs.get('device_instance', self._ud.device_instance)
        self.keytype = kwargs.get('keytype', None)

        x509_sudi_hash = kwargs.get('x509_sudi_hash', [])
        menu = kwargs.get('menu', False)

        # Sanity checks
        identity_protection_type = self._ud.uut_config.get('identity_protection_type', None)
        if not identity_protection_type:
            log.error("Unknown Identity Protection type.")
            log.error("Ensure the product definition is loaded and has an 'identity_protection_type' entry.")
            return aplib.FAIL, "IdPro undefined."
        if 'ACT2' not in identity_protection_type and 'QUACK2' not in identity_protection_type:
            log.warning("The UUT Identity Protection Type ='{0}'.".format(identity_protection_type))
            log.warning("Nothing to do here.")
            # Note: Skip since this does not apply and we don't want to penalize the menu selection (if called).
            return aplib.SKIPPED

        if self.device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while not self.device_instance or not str(self.device_instance).isdigit():
                self.device_instance = aplib.ask_question("Device instance [int]:")
        self.device_instance = int(self.device_instance)
        if not 0 <= self.device_instance <= 10000:
            raise Exception("Device instance for X.509 SUDI (ACT2 chip) is invalid (must be 0 to 10000).")

        if self.device_instance != 0:
            # Check the device ID for motherboard/supervisor only.
            # This does NOT apply to peripherals.
            log.error("X509 SUDI certs typically apply to motherboards/supervisors ONLY.")
            log.error("A non-zero device instance was specified!")
            log.error("The device will need a MAC, S/N, & Base-PID to be properly signed.")
            log.error("If a non-motherboard needs an X.509 cert, please consult the Cisco Prod Ops TDE.")
            raise Exception("Non-zero device instance for X.509 certs.")

        if not x509_sudi_hash or menu:
            ans = aplib.ask_question('Choose an X.509 SUDI Hash:', answers=self.SUDI_HASH_SELECT_LIST.keys())
            x509_sudi_hash = [ans]
        if not isinstance(x509_sudi_hash, list):
            x509_sudi_hash = [x509_sudi_hash]
        if len(x509_sudi_hash) > 1:
            log.warning("Multiple SUDI hashes detected: {0}".format(x509_sudi_hash))
            log.warning("X.509 SUDI certs must be done in a specific order; successive programming is not allowed.")
            log.warning("For automation, please see 'Identification Protection' (IdPro).")
            log.warning("Please choose one hash only.")
            ans = aplib.ask_question('Choose an X.509 SUDI Hash:', answers=x509_sudi_hash)
            x509_sudi_hash = [ans]

        if not self.keytype or menu:
            if x509_sudi_hash in ['SHA256', 'CMCA2']:
                self.keytype = aplib.ask_question("Select SHA256 keytype:", answers=['QUACK2', 'ACT2-RSA'])
            elif x509_sudi_hash in ['CMCA3']:
                self.keytype = 'ACT2-HARSA'
            else:
                log.debug("Don't care about key_type.")

        # Verify and arrange UUT required params
        self.x509_data['uut_mac'] = self.__format_mac(self._ud.uut_config.get('MAC_ADDR'))
        self.x509_data['uut_sernum'] = self._ud.puid.sernum
        self.x509_data['uut_pid'] = self._ud.puid.pid           # UUT Base PID ! (not Cfg PID)
        self.x509_data['sudi_hash'] = x509_sudi_hash            # 'SHA1', 'SHA256', etc. or a list

        # Check mode
        if not self._mode_mgr.is_mode('STARDUST'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'STARDUST' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL

        # Perform the action
        result = self.__sign_certificate()

        return aplib.PASS if result else aplib.FAIL

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNALS
    #
    def __sign_certificate(self):
        """ Sign SUDI Cert (INTERNAL)
        :return: 
        """
        ret = False
        ret_list = []
        try:
            # Provide prerequisite warning
            log.warning("UUT must have been properly system initialized (sysinit) to perform ACT2 signing!")

            # Do pre-signing activities
            self.__process_input_params()
            self.__map_sequence_to_pid()

            self.__print_sudi_data(enable=self.__verbose)

            # Perform the signing for each hash type requested.
            # Order is important for multi hash esp if using the ACT2 device, (mode 1 must be programmed before mode 2).
            # WARNING: Although this function can successively process a list of X.509 SUDI hashes, the product
            # may not support programming in this type of sequence. Verify diags & IOS can support.
            # Typically, multiple certs are split up in a before & after sequence w/ ACT/QUACK programming.
            # (Consult specific product requirements. Also see 'Identification Protection' routines.)
            log.debug("Sign start.")
            cnt = 0
            for hash_type, key_size in zip(self.x509_data['sudi_hash'], self.x509_data['key_size']):
                cnt += 1
                msg = "Signing SUDI Hash/Key {0}/{1} ...          ".format(hash_type, key_size)
                log.info(msg)
                log.info("-" * len(msg))
                if not self.__unittest:
                    # Get
                    x509_data = self.__get_x509_sudi(hash_type.lower(), key_size)
                    if not x509_data:
                        raise Exception("Data content error.")
                    # Put
                    ret_list.append(self.__put_x509_sudi(x509_data, hash_type))
                else:
                    log.warning("Unittest only operation for X.509 SUDI.")
                    log.warning("Signing process will end.")
                    ret_list.append(False)

            ret = all(ret_list)
        except Exception as e:
            log.critical(e)
            log.error("Cannot complete X.509 SUDI Sign operation.")
            # Deep debug: log.debug("recbuf='{0}'".format(self._uut_conn.recbuf))
            # TODO: need a graceful exit?
            ret = False

        finally:
            self.__print_sudi_data(method='nested')
            return ret

    @func_details
    def __print_sudi_data(self, method='simple', enable=True):
        if enable:
            if method == 'simple':
                for key in sorted(self.x509_data):
                    log.info("{0:<25s} = {1}".format(key, self.x509_data[key]))
            elif method == 'nested':
                print_large_dict(self.x509_data, title="X.509 Data", print_ctrl=True)
        return

    @func_details
    def __process_input_params(self):
        """
        Only prompt the questions when the input is empty or not correct.
        This routine is mainly used for bench/debug testing.
        :return:
        """

        # UUT Params ---------------
        while not validate_sernum(self.x509_data['uut_sernum']):
            log.warning("Could not validate Serial Number; prompting for input...")
            self.x509_data['uut_sernum'] = aplib.ask_question("UUT\n\nEnter Cisco System Serial Number (LLLYYWWSSSS): ")

        while not validate_mac_addr(self.x509_data['uut_mac']):
            log.warning("Could not validate MAC; prompting for input...")
            self.x509_data['uut_mac'] = \
                self.__format_mac(aplib.ask_question("UUT\n\nEnter MAC Address (hex form): "))

        while not validate_pid(self.x509_data['uut_pid']):
            log.warning("Could not validate Base PID; prompting for input...")
            self.x509_data['uut_pid'] = aplib.ask_question("UUT\n\nEnter Base PID (18 max chars): ")

        # SUDI Params ---------------
        if not self.__validate_request_type():
            # Note: The cesiumlib forces the request type to only 'PROD'; need to determine if this remains.
            # This input has no effect as a param doesn't exist for the call.
            log.warning("Could not validate X.509 Request Type; prompting for input...")
            self.x509_data['request_type'] = \
                aplib.ask_question("X.509 SUDI\n\nSelect request type: ", answers=X509Sudi.X509_REQUEST_TYPES)

        if not self.__validate_cert_method():
            log.warning("Could not validate X.509 Cert Method; prompting for input...")
            self.x509_data['cert_method'] = \
                aplib.ask_question("X.509 SUDI\n\nSelect Cert Method: ", answers=X509Sudi.X509_CERT_METHODS)

        if self.x509_data['cert_method'] == 'CERT_ONLY' and not self.__validate_public_key_file():
            log.warning("Could not validate Public Key File when using CERT_ONLY method; prompting for input...")
            self.x509_data['public_key'] = aplib.ask_question("X.509 SUDI\n\nEnter Public Key File (incl path): ")

        if not self.__validate_sudi_hash():
            log.warning("Could not validate SUDI Hash Type(s); prompting for input...")
            ans = aplib.ask_question("X.509 SUDI\n\nSelect Hash Type: ",
                                     answers=X509Sudi.SUDI_HASH_SELECT_LIST.keys())
            self.x509_data['sudi_hash'] = [ans]
            self.x509_data['key_size'] = [X509Sudi.SUDI_HASH_SELECT_LIST[ans].size]

        # Other derived Params --------------
        self.x509_data['common_name'] = "{0}-{1}".format(self.x509_data['uut_pid'], self.x509_data['uut_mac'])

        return

    @func_details
    def __map_sequence_to_pid(self):
        """ Map the SUDI Storage Sequence and the Programming Version

        Sequence 'STANDARD' *** DEFAULT ***   (Ex. Edison)
            > Key header
            > Key contents
            > Certificate header
            > Certificate contents:
            > - Device certificate
            > - Sub-CA certificate
            > - Root certificate

        Sequence 'REVERSE'  Legacy  (Ex. Whales, Surge)
            > Key header
            > Key contents
            > Certificate header
            > Certificate contents:
            > - Root certificate
            > - Sub-CA certificate
            > - Device certificate


        :return:
        """
        if not self.x509_data['uut_cert_sequence'] and not self.x509_data['uut_prog_version']:
            log.debug("Mapping PID...")
            for ps_map in X509Sudi.PID_SEQ_MAP:
                if re.search(ps_map.pid_pattern, self.x509_data['uut_pid']):
                    self.x509_data['uut_cert_sequence'] = ps_map.sequence
                    self.x509_data['uut_prog_version'] = ps_map.prog_version
                    break
            else:
                log.debug("Unmapped PID; using default SUDI sequence arrangement.")
                self.x509_data['uut_cert_sequence'] = 'STANDARD'
                self.x509_data['uut_prog_version'] = 'MULTICERT'
        else:
            log.debug("No PID mapping necessary; Cert Sequence and Programming Version were explicitly specified.")

        log.info("X509 SUDI sequence arrangement = {0}".format(self.x509_data['uut_cert_sequence']))
        log.info("X509 SUDI programming version  = {0}".format(self.x509_data['uut_prog_version']))
        return

    @func_details
    def __get_x509_sudi(self, sudi_hash, key_size):
        """ Get the Certs from Cesium service
        The only items that change for different certs of the same UUT is the hash and key.
        :param sudi_hash:  This is either the sha1, sha256 OR the cmca,cmca2,cmca3 types.
        :param key_size: Typically from the lookup map.
        :return:
        """

        @cesium_srvc_retry(max_attempts=X509Sudi.X509_MAX_SERVICE_ATTEMPTS)
        def __generate_x509(uut_sernum, product_id, common_name, certificate_method, public_key, sudi_enabled, public_key_size, hash_type):
            """
            Have to make separate calls as of 1/19/2018 since the new function is not released.
            :return:
            """
            if 'CMCA' in hash_type.upper():
                log.debug("New call method: url_qualifier.")
                url_qualifier = hash_type
                hash_type = None
                return cesiumlib.generate_x509(uut_sernum,
                                               product_id=product_id,
                                               common_name=common_name,
                                               certificate_method=certificate_method,
                                               public_key=public_key,
                                               sudi_enabled=sudi_enabled,
                                               public_key_size=public_key_size,
                                               hash_type=hash_type,
                                               url_qualifier=url_qualifier)

            else:
                log.debug("Legacy call method: hash_type.")
                # url_qualifier = None
                return cesiumlib.generate_x509(uut_sernum,
                                               product_id=product_id,
                                               common_name=common_name,
                                               certificate_method=certificate_method,
                                               public_key=public_key,
                                               sudi_enabled=sudi_enabled,
                                               public_key_size=public_key_size,
                                               hash_type=hash_type)

        sudi_hash = sudi_hash[0].lower() if isinstance(sudi_hash, list) else sudi_hash.lower()
        key_size = int(key_size)
        sudi_enabled = True
        sudi_data = {}

        log.info("{0:<25s} = {1}".format('SerNum', self.x509_data['uut_sernum']))
        log.info("{0:<25s} = {1}".format('PID', self.x509_data['uut_pid']))
        log.info("{0:<25s} = {1}".format('Common Name', self.x509_data['common_name']))
        log.info("{0:<25s} = {1}".format('Cert Method', self.x509_data['cert_method']))
        log.info("{0:<25s} = {1}".format('Sudi Enabled', sudi_enabled))
        log.info("{0:<25s} = {1}".format('Public Key File', self.x509_data['public_key']))
        log.info("{0:<25s} = {1}".format('Hash Type', sudi_hash))
        log.info("{0:<25s} = {1}".format('Key Size', key_size))

        success = False
        try:
            sudi_data = __generate_x509(self.x509_data['uut_sernum'],
                                        product_id=self.x509_data['uut_pid'],
                                        common_name=self.x509_data['common_name'],
                                        certificate_method=self.x509_data['cert_method'],
                                        public_key=self.x509_data['public_key'],
                                        sudi_enabled=sudi_enabled,
                                        public_key_size=key_size,
                                        hash_type=sudi_hash)
            success = True
        except apexceptions.ServiceFailure as ape:
            log.exception(ape.message)

        if not success:
            raise apexceptions.ApolloException("Cesium Service call: generate_x509 FAILED!")
        else:
            log.info("X.509 Cert successful retrieval!")
            for key in X509Sudi.X509_DATA_KEYS:
                if key not in sudi_data:
                    log.error("X.509 data is missing '{0}' data.".format(key))
                    self.__print_sudi_data()
                    raise Exception("X.509 data is incomplete!")

        return sudi_data

    @func_details
    def __put_x509_sudi(self, sudi_data, sudi_hash):
        """ Program the Certs to the UUT
        :param sudi_data: Dictionary of cert data from the previous service call.
        :param sudi_hash:
        :return:
        """
        # Preliminary set up (cmd_params)
        if self.x509_data['uut_prog_version'] == 'LEGACY':
            log.debug("X.509 LEGACY")
            if sudi_hash == 'SHA1':
                log.warning("The older Quack2/ACT2 EEPROM programming map has been requested.")
                log.warning("WDC must NOT be loaded.")
                log.warning("Confirm IOS authentication for this mapping.")
                log.warning("This is not normal.")
                cmd_params = '-i:{0} -v:{1}'.format(self.device_instance, '1')
                self.x509_data['hidden_files'] = None
            else:
                log.error("Legacy programming map does NOT support this SUDI hash!")
                return False

        elif self.x509_data['uut_prog_version'] == 'MULTICERT':
            log.debug("X.509 MULTICERT")
            if sudi_hash == 'SHA1' or sudi_hash == 'CMCA1' or sudi_hash == 'CMCA':
                cmd_params = '-i:{0} -v:{1}'.format(self.device_instance, '2')
                self.x509_data['hidden_files'] = None
            elif sudi_hash == 'SHA256' or sudi_hash == 'CMCA2':
                cmd_params = '-i:{0} -v:{1}'.format(self.device_instance, '3')
                self.x509_data['hidden_files'] = X509Sudi.SHA256_HIDDEN_FILE_MAP[self.keytype]
            elif sudi_hash == 'CMCA3':
                cmd_params = '-i:{0} -v:{1}'.format(self.device_instance, '4')
                self.x509_data['hidden_files'] = X509Sudi.SHA256_HIDDEN_FILE_MAP[self.keytype]
            else:
                log.error("SUDI hash not supported!")
                return False

        else:
            log.error("Programming version unknown.")
            log.error("Check the PID_SEQ_MAP and this module {0}.".format(sys.modules[__name__]))
            return False

        log.info("{0:<25s} = {1}".format('Prog Version', self.x509_data['uut_prog_version']))
        log.info("{0:<25s} = {1}".format('Prog Sequence', self.x509_data['uut_cert_sequence']))

        self.__print_sudi_data(enable=self.__verbose)

        # 1. Create any hidden files if needed
        if self.x509_data['hidden_files']:
            # Note: A mounting to the 'hidden_mount_dir' will be done AND left in that state when creating the files.
            if not self.__make_hidden_files():
                log.debug("Hidden file setup did not succeed; cannot continue.")
                return False
            self._uut_conn.send("dir {0}\r".format(self.x509_data['hidden_mount'].dir),
                               expectphrase=self._uut_prompt, timeout=30, regex=True)

        # 2. Program the Key!
        self._uut_conn.send("SCCProgramSudiKey {0}\r".format(cmd_params), expectphrase='Enter SUDI', timeout=30)
        self.__send_uut_data(sudi_data['private_key'], join=True)
        result, error = self.__send_uut_data('ENDOFKEY', join=False, final_expectphrase=self._uut_prompt)
        if not result:
            log.error("Cannot continue.")
            return False
        self._uut_conn.waitfor('SUDI Key writing successful', timeout=60)

        # 3. Program the Certs!
        if self.x509_data['uut_cert_sequence'] not in X509Sudi.SUDI_SEQUENCE:
            log.error("SUDI programming sequence unknown!")
            return False
        self._uut_conn.send("SCCProgramSudiCert {0}\r".format(cmd_params), expectphrase='Enter SUDI', timeout=30)
        for cert_item in X509Sudi.SUDI_SEQUENCE[self.x509_data['uut_cert_sequence']]:
            self.__send_uut_data(sudi_data[cert_item], join=True)
        result, error = self.__send_uut_data('ENDOFCERT', join=False)
        if not result:
            log.error("Cannot continue.")
            return False
        self._uut_conn.waitfor('SUDI Certificate writing successful', timeout=240)

        # 4. Release the 'hidden_mount_dir' mounting and restore the original mount.
        if self.x509_data['hidden_files']:
            self._uut_conn.send("dir {0}\r".format(self.x509_data['hidden_mount'].dir),
                               expectphrase=self._uut_prompt, timeout=30, regex=True)
            if not self._mode_mgr.goto_mode('LINUX'):
                log.error("Cannot switch to Linux mode.")
                return False
            uut_prompt = self._mode_mgr.uut_prompt_map['LINUX']
            self._linux.umount_devices(mounts=self.x509_data['hidden_mount'])
            if self.x509_data['current_mount']:
                self._linux.mount_devices(mounts=self.x509_data['current_mount'])
            if not self._mode_mgr.goto_mode('STARDUST'):
                log.error("Cannot switch to diags mode.")
                return False

        return True

    @staticmethod
    def __format_mac(mac):
        nmac = re.sub(r"(0x)?[:\-\. ]", '', mac).upper() if mac else ''
        return nmac

    def __validate_request_type(self):
        ret = True if self.x509_data['request_type'] in X509Sudi.X509_REQUEST_TYPES else False
        return ret

    def __validate_cert_method(self):
        ret = True if self.x509_data['cert_method'] in X509Sudi.X509_CERT_METHODS else False
        return ret

    def __validate_public_key_file(self):
        if not self.x509_data['public_key']:
            return False
        if os.path.exists(self.x509_data['public_key']) and os.path.getsize(self.x509_data['public_key']) > 64:
            ret = True
        else:
            ret = False
        # TODO: Can content be confirmed?
        return ret

    def __validate_sudi_hash(self):
        """ Validate SUDI Hash
        This also sets the appropriate key_size list per the hash list.
        :return:
        """

        # Ensure the hash and size items are lists.
        # This is for compatibility to process a list of hashes (as a feature) and not just one hash.
        if not isinstance(self.x509_data['sudi_hash'], list):
            self.x509_data['sudi_hash'] = [self.x509_data['sudi_hash']]
        if not isinstance(self.x509_data['key_size'], list):
            self.x509_data['key_size'] = [self.x509_data['key_size']]

        # Now check for valid hash name and get the proper size for each hash from the map.
        ret_list = []
        for hash_type in self.x509_data['sudi_hash']:
            if hash_type not in X509Sudi.X509_SUDI_HASH_TYPES:
                ret_list.append(False)
                self.x509_data['key_size'].append(0)
            else:
                ret_list.append(True)
                self.x509_data['key_size'].append(X509Sudi.SUDI_HASH_SELECT_LIST[hash_type.upper()].size)

        log.debug(self.x509_data['sudi_hash'])
        log.debug(self.x509_data['key_size'])
        log.debug(ret_list)
        return all(ret_list)

    def __send_uut_data(self, data, segments=1, interim_expectphrase='.*', final_expectphrase='.*',
                        join=False, verbose=False):
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
                i = block * s_size + s_offset
                j = (block + 1) * s_size + s_offset
                if verbose:
                    log.debug("{0}:{1}".format(i, s_data[i:j]))
                if not noexpectphrase:
                    self._uut_conn.send(s_data[i:j], expectphrase='.*', timeout=90, regex=True)
                else:
                    self._uut_conn.send(s_data[i:j], expectphrase=None, timeout=120, idle_timeout=90, regex=True)
                time.sleep(0.10)
            return j

        # Init operating vars
        sendsize = X509Sudi.X509_CONSOLE_SEND_SIZE
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
            log.debug('Segment = {0}'.format(segment))
            offset = segment * blocks * sendsize
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

        log.debug("Send data done.")
        errors = re.findall('\*\*\*ERR:.*', self._uut_conn.recbuf)
        if errors:
            log.error("SEND DATA Failure: {0}".format(errors))

        return (True, None) if not errors else (False, errors)

    def __make_hidden_files(self):
        """ Create empty X.509 hidden files.
        Do this when diagnostics capability is limited and cannot perform file creation.
        A MachineManager instance MUST have been passed during instantiation if this function is to be used.
        NOTE: This function is enabled when the MachineManager param "mm" is present.
        NOTE2: This method is somewhat product-line specific but is included in this module for completeness.
               Ultimately, diags capability should preclude the use of this method; it is the TDE responsibility
               to verify each new product with the diags to determine if this is needed.
        :return:
        """

        # Enablement
        if not self._mode_mgr:
            log.warning("A product mode object was not provided; therefore no hidden file external creation to do.")
            log.warning("Ensure the diagnostics properly creates the required hidden files.")
            return True

        # Prerequisite check
        if not self.x509_data['hidden_files']:
            log.error("Hidden files have not been specified.")
            return False

        # Get to Linux
        if not self._mode_mgr.is_mode('LINUX'):
            log.debug("Need Linux mode...")
            if not self._mode_mgr.goto_mode('LINUX'):
                log.error("Cannot switch to Linux mode.")
                return False
        uut_prompt = self._mode_mgr.uut_prompt_map['LINUX']

        # Check current mounting
        current_mount_dir = self._linux.is_dev_mounted(self.x509_data['hidden_mount'].device)
        if current_mount_dir:
            log.debug("Current mounts detected.")
            # Must unmount any current mounting that conflicts with hidden mounting.
            current_mount = self._linux.MountDescriptor(self.x509_data['hidden_mount'].device, current_mount_dir)
            log.debug("Already mounted to the target: {0} on {1}".format(current_mount.device, current_mount.dir))
            if current_mount.dir != self.x509_data['hidden_mount'].dir:
                log.debug("Mount point is not correct; saving and changing mount...")
                self.x509_data['current_mount'] = current_mount
                self._linux.umount_devices(mounts=current_mount)

        # File creation.
        ret = True
        log.debug("Creating X.509 files: {0}".format(self.x509_data['hidden_files']))
        if not self._linux.touch_files(self.x509_data['hidden_files'],
                                       self.x509_data['hidden_mount'].device,
                                       self.x509_data['hidden_mount'].dir,
                                       clean=True,
                                       keep_mount=True):
            log.error("Unable to create the requested X.509 files.")
            ret = False

        # Get back to Stardust
        if not self._mode_mgr.goto_mode('STARDUST'):
            log.error("Unable to return to Stardust mode.")
            ret = False
        # TODO: Does the unit need another 'sysinit' after exit+enter Stardust?  Does not appear to need it.

        return ret
