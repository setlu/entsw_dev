""" Rommon/Bootloader Class Driver Module
========================================================================================================================

This module provides a set of classes for operating a specific bootloader/rommon types.
The bootloader/rommon driver type is identified by class name.
All classes are REQUIRED to use the RommonBootloader abstract base class for interface definition.

Product families supported:
    1. Cisco Catalyst 2900 series (WS-C2900 & C9200)
    2. Cisco Catalyst 3800/3600 series (WS-C3850/C3650 & C9300, C9300L)
    3. Cisco Catalyst 4000 series (WS-C4000 & C9400)

========================================================================================================================
"""
# ------
import sys
import re
import logging
import time
import parse
import os
from collections import OrderedDict, namedtuple
import inspect

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
from ..bases.rommon_base import RommonBase
from ..utils.common_utils import func_details
from ..utils.common_utils import func_retry
from ..utils.common_utils import get_mac
from ..utils.common_utils import validate_ip_addr
from ..utils.common_utils import validate_mac_addr
from ..utils.common_utils import convert_mac


# BU Product Specific
# -------------------
# none

__title__ = "Catalyst Rommon/Bootloader Module"
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
# External User functions
#
def universal_uut_detect(uut_conn, uut_prompt=None, uut_detect_params=None, universal_tlv_map_list=None):
    """ Universal UUT Detect
    This routine can be used on generic test stations that share many product lines in EntSw BU.
    Typically this could be FST or at the DF site where the station can easily connect to many different units
    and a traditional Apollo "Production Line" is not desired which could confuse the operator.
    The methodology here is to NOT write any detection routines but to use the existing methods in ALL the classes
    available to make the detection.  Detection is accomplished by reading rommon/bootloader parameters.
    :param (obj) uut_conn:
    :param (str) uut_prompt: RegEx universal rommon/bootloader prompt
    :param (str) uut_detect_params:
    :param (str) universal_tlv_map_list:
    :return (dict) params:  Ex. = {'TAN_NUM': '68-5991-01', 'MODEL_NUM': 'C9300-24U', 'MOTHERBOARD_ASSEMBLY_NUM': '73-17954-05'}
                            Only available values from the uut_detect_params list is returned.
    """
    uut_prompt = '(?:switch:)|(?:rommon:)|(?:sboot64>)|(?:rommon [0-9]+ >)' if not uut_prompt else uut_prompt
    uut_detect_params = ['MODEL_NUM', 'TAN_NUM', 'MOTHERBOARD_ASSEMBLY_NUM'] if not uut_detect_params else uut_detect_params
    universal_tlv_map_list = [
        ('Part Number - PCA',         ('0x00', 'MOTHERBOARD_ASSEMBLY_NUM')),
        ('Part Number - TAN(6-byte)', ('0x00', 'TAN_NUM')),
        ('Part Number -TAN',          ('0x00', 'TAN_NUM')),
        ('UDI name/Base PID',         ('0x00', 'MODEL_NUM')),
        ('Product number/identifier', ('0x00', 'MODEL_NUM')),
    ] if not universal_tlv_map_list else universal_tlv_map_list
    universal_tlv_map = OrderedDict(universal_tlv_map_list)

    log.debug("Checking UUT response...")
    try:
        uut_conn.send('\r', expectphrase=uut_prompt, regex=True, timeout=10)
    except aplib.apexceptions.TimeoutException:
        log.error("Cannot find a known rommon/bootloader prompt.")
        log.error("Check the UUT mode and connection for proper operation.")
        return None

    the_classes = []
    log.debug("Scanning rommon classes...")
    for name, obj in inspect.getmembers(thismodule):
        if inspect.isclass(obj) and hasattr(obj, 'get_params') and 'Base' not in name:
            the_classes.append((name, obj))
    log.debug("All possible rommon operation classes: {0}".format(the_classes))

    log.debug("Performing systematic attempts with each method...")
    for name, class_obj in the_classes:
        log.debug("Attempting: {0}.get_params() ...".format(name))
        class_instance = class_obj(uut_conn, uut_prompt)
        class_instance.tlv_map = universal_tlv_map
        params = class_instance.get_params()
        if params:
            log.debug("Some params were found!")
            if any([True if params[pname] else False for pname in list(set.intersection(set(params.keys()), set(uut_detect_params)))]):
                log.debug("Detection params are available!")
                break
    else:
        log.error("Cannot find any bootloader/rommon params with the currently known methods.")
        log.error("Check the rommon_driver classes for proper compatibilty with the UUT.")
        log.error("Check that the UUT has been programmed.  'Blank' UUTs cannot be universally detected!")
        return None

    for pname in params.keys():
        params.pop(pname) if pname not in uut_detect_params else None
    log.debug("Params: {0}".format(params))
    return params


# ======================================================================================================================
# Exceptions
class RommonException(Exception):
    """Raise for specific Rommon exceptions."""
    pass


# ======================================================================================================================
# Drivers
#
# ----------------------------------------------------------------------------------------------------------------------
# Generic
class Rommon(RommonBase):
    """ Rommon Driver (generic)
    Use this for ALL Enterprise Switching products.

    The focus of this class is on the older "Generation 2" (WS-C3x00, WS-C2x00) product families.
    However, some properties and methods can also be used for "Generation 3" (C9x000) products.

    """

    RECBUF_TIME = 3.0
    RECBUF_CLEAR_TIME = 1.0
    USE_CLEAR_RECBUF = False
    NETWORK_PARAM_SETS = {
        'Gen2': ['MAC_ADDR', 'IP_ADDR', None, 'DEFAULT_ROUTER', None],
        'Gen3': ['MAC_ADDR', 'IP_ADDRESS', 'IP_SUBNET_MASK', 'DEFAULT_GATEWAY', 'TFTP_SERVER'],
        'Gen3b': ['MAC_ADDR', 'IP_ADDR', 'IP_MASK', 'DEFAULT_GATEWAY', 'TFTP_SERVER'],
    }
    NetworkParamNames = namedtuple('NetworkParamNames', ['mac', 'ip', 'mask', 'gw', 'tftp_srvr'])

    def __init__(self, mode_mgr, ud, **kwargs):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._check_dependencies()
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt_map = self._mode_mgr.uut_prompt_map
        self._uut_prompt = self._uut_prompt_map.get('BTLDR', ': ')
        self._version = dict(primary=dict(ver=None, date=None, status=None),
                             golden=dict(ver=None, date=None, status=None))
        self._fresh_read = False
        self._params = {}

        # Determine btldr/rommon types
        if 'BTLDRG' in self._uut_prompt_map:
            self.btldr_types = [('golden', 'BTLDRG'), ('primary', 'BTLDR')]
        else:
            self.btldr_types = [('primary', 'BTLDR')]
        log.debug("  Rommon types: {0}".format(self.btldr_types))
        self._callback = None

        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ------------------------------------------------------------------------------------------------------------------
    # User Properties
    #
    @property
    def version(self):
        return self._version

    @property
    def params(self):
        return self._params

    # ------------------------------------------------------------------------------------------------------------------
    # User Methods
    #
    @func_details
    def get_devices(self):
        """ Get Devices
        List of available devices to access from bootloader/rommon

        :return m: (list) All available devices seen by bootloader
        """
        m = list()
        try:

            @func_retry(max_attempts=1)
            def __dirdev():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('dir -a\r', expectphrase=self._uut_prompt, timeout=20, regex=True)
                time.sleep(self.RECBUF_TIME)
                p = re.compile(r"[ \t]*([\S]+)\[.*")
                return p.findall(self._uut_conn.recbuf)

            m = __dirdev()
        except Exception as e:
            log.error(e)
        finally:
            return m

    @func_details
    def get_device_files(self, device_name='flash', sub_dir='', file_filter='.*?', attrib_flags='-ld'):
        """ Get Device Files (via rommon/bootloader)
        Get device files (or dirs) only from the sub directory path given.
        Apply file attribs and regex patterns as filters.

        Sample output to process is given below:
        switch: dir flash:

            Directory of flash:/

             81921  drwx  4096       .
                 2  drwx  4096       ..
             81922  -rwx  22337271   vmlinux2013Sep23.mzip.SSA
             81924  -rwx  9979       17-G24CSR-16.SBC_cfg
             98305  drwx  4096       kirch
             81931  -rwx  23726120   stardust_021115
             81932  -rwx  524288     morseG_01_00_A0.hex
             81933  -rwx  1623       17-FibSchrod-03.SBC_cfg

            1967345664 bytes available (180137984 bytes used)

        :param device_name: (str) Device to operate on.
        :param sub_dir: (str) Sub directory path to look in.
        :param file_filter: (str) Look only for files matching the regex filter.
        :param attrib_flags:  (str) Use "d", "l', and "-" for dir, link, and file. (Default is get everything.)
        :return m: (list) All available devices seen by bootloader
        """
        m = list()
        try:

            @func_retry(max_attempts=1)
            def __dir():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('dir {0}:{1}\r'.format(device_name, sub_dir), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                attrib_filter = '[{0}][-rwx]'.format(attrib_flags) + '{3}'
                p = re.compile(r"[ \t]*[0-9]+[ \t]+{1}[ \t]+[0-9]+[ \t]+({0})[\r\n]+".format(file_filter, attrib_filter))
                return p.findall(self._uut_conn.recbuf)

            m = __dir()
            if not m:
                log.debug("No files found that match the criteria.")
                return m
            # Remove relative dir names (if in the list)
            i = 0
            while i < len(m):
                if m[i] == '.' or m[i] == '..':
                    m.pop(i)
                else:
                    i += 1
            # Do a reverse sort to put "newer" files first based on lexigraphical sort of datestamp in the filename.
            m.sort(reverse=True)
        except apexceptions.TimeoutException as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return m

    @func_details
    def get_params(self):
        """ Get Parameters
        Generic routine for obtaining the motherboard flash parameters

        :return params: (dict) All flash params
        """
        if self._fresh_read and self._params:
            log.debug("Params are fresh.")
            return self._params

        params = {}
        try:
            params = self._getflash()
        except apexceptions.TimeoutException:
            log.error("UUT timed out for bootloader response.")
        except RommonException as e:
            log.warning(e)
        except Exception as e:
            log.error(e)
        finally:
            self._params = params
            self._fresh_read = True
            return params

    @func_details
    def set_params(self, setparams, **kwargs):
        """ Set Params
        Set flash parameters for ALL blocks (parameter and variable).
        A verification step is done afterwards.
        By default the "pb:" block is made writeable and burned.

        :param setparams: (dict) Params and values to set.
        :return ret: (bool) True if all values to set were successfully set.
        """
        restore_ro = kwargs.get('restore_ro', False)
        ret = True
        try:
            # Get initial settings
            fullparams = self.get_params()

            time.sleep(1.0)
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=20, regex=True)

            # Set or update the params
            log.debug("SETTING Rommon Params...")
            for key in setparams:
                if key in fullparams:
                    if setparams[key]:
                        if setparams[key] != fullparams[key]:
                            # Change the parameter
                            self._mac_special(key, setparams, fullparams)
                            self._uut_conn.send('set {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                               expectphrase=self._uut_prompt, timeout=20, regex=True)
                            log.info("{0} = {1}  (set changed)".format(key, setparams[key]))
                        else:
                            # No change necessary
                            log.info("{0} = {1}".format(key, setparams[key]))
                    else:
                        # Empty or null value will be ignored.
                        log.info("{0} is empty; not allowed when setting. Use 'unset' instead.".format(key))
                else:
                    # Create a new parameter if it has a value
                    if setparams[key]:
                        self._uut_conn.send('set {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                           expectphrase=self._uut_prompt, timeout=10, regex=True)
                        log.info("{0} = {1}  (set new)".format(key, setparams[key]))
                    else:
                        log.debug("{0} is empty & new, ignore it.".format(key))
            self._fresh_read = False

            # Burn the parameter block
            # The "pb:" area is a strictly defined set of params used by IOS (and diags) that MUST be populated!
            # Note: "pb:" is typically protected by a read-only setting.
            #       The ro setting should be restored during customer configuration time.
            time.sleep(1.0)
            self._uut_conn.send('set_bs pb: rw\r', expectphrase=self._uut_prompt, timeout=10, regex=True)
            self._uut_conn.send('set_param -all\r', expectphrase=self._uut_prompt, timeout=10, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'Parameters burned' in self._uut_conn.recbuf:
                log.debug("Parameters burned into pb:")
            else:
                log.error("Parameters NOT burned into pb: !")
                ret = False
                raise aplib.apexceptions.ResultFailure("Param burn in pb: NOT confirmed.")
            if restore_ro:
                log.debug('Restore pb: to read-only.')
                self._uut_conn.send('set_bs pb: ro\r', expectphrase=self._uut_prompt, timeout=10, regex=True)

            # Now verify that the params were actually set
            fullparams = self.get_params()
            for key in setparams:
                if key in fullparams:
                    if setparams[key] and setparams[key] != fullparams[key]:
                        # Invalid; something went wrong during the set process.
                        log.warning("{0} set = '{1}'  found = '{2}'".format(key, setparams[key], fullparams[key]))
                        ret = False
                else:
                    if setparams[key]:
                        # Invalid, the item is missing and is not ignored.
                        log.warning("{0} was NOT found.".format(key))
                        ret = False

        except aplib.apexceptions.ResultFailure as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def ping(self, ip):
        """ Ping from Bootloader

        Sample1:
        switch: ping 10.1.1.1
        ping 10.1.1.1 with 32 bytes of data ...
        Host 10.1.1.1 is alive.

        Sample2:
        switch: ping 10.1.1.1
        ping 10.1.1.1 with 32 bytes of data ...
        Up 1000 Mbps Full duplex (port  0) (SGMII)
        Host 10.1.1.1 is alive.

        :param ip: (str) IP Addr
        :return ret: (bool) True if ping was good.
        """

        @func_retry
        def __ping():
            ret = False
            self._clear_recbuf(self._uut_conn, force=True)
            self._uut_conn.send('ping {0}\r'.format(ip), expectphrase=self._uut_prompt, timeout=120, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'is alive' in self._uut_conn.recbuf:
                log.debug("'Ping: {0}' is alive!".format(ip))
                ret = True
            else:
                log.debug("Ping: Network connection or setup problem with {0}".format(ip))
            return ret

        ret = False
        try:
            if ip:
                ret = __ping()
            else:
                log.warning("IP Addr is required to ping!")
        except apexceptions.TimeoutException as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def check_version(self, version=None):
        """ Check Version of Bootloader/Rommon
        Example:
        switch: version
        CAT3K_CAA Boot Loader (CAT3K_CAA-HBOOT-M) Version 1.3, engineering software (D)
        Compiled Mon Mar 24 08:15:52 PDT 2014 by johwang

        Note: Expects to be in bootloader mode already!

        :param (dict) version: Target version & date to check, e.g. {'ver': '1.3', 'date': 'Mar 24 2014'}
                               (Note: the time is removed.)
        :return: True if match or target version is null
        """

        if version and not isinstance(version, dict):
            log.error("Target version for checking must be in dict form.")
            return False

        m = self._get_version()
        if m:
            self._version['primary']['ver'] = m.get('ver', '')
            if not m.get('date'):
                self._version['primary']['date'] = '{0} {1} {2}'.format(m.get('month', ''), m.get('day', ''), m.get('yr', ''))
            else:
                self._version['primary']['date'] = m['date']
        else:
            log.warning("Version data not retrieved!")

        log.info("Bootloader Current Ver: {0}".format(self._version['primary']))
        log.info("Bootloader Target  Ver: {0}".format(version))

        # Sanity check
        if not version:
            log.debug("Target version is null; skip the check.")
            return True
        if not self._version['primary']['ver']:
            log.error("Unable to get current version of bootloader/rommon.")
            log.error("Check the UUT.  Check the parse.")
            return False

        # Now check for a match
        ret = True
        if self._version['primary']['ver'] == version['ver'] and self._version['primary']['date'] == version['date']:
            log.info("Revision match.")
            self._version['primary']['status'] = True
        elif not version:
            log.warning("No version data to check against.")
            log.warning("Image revision check will be ignored.")
        elif self._version['primary']['ver'] > version['ver']:
            log.warning("Current version {0} is NEWER than expected version {1}.".format(self._version['primary']['ver'], version['ver']))
            self._version['primary']['status'] = True
        else:
            log.warning("Revision MISMATCH!")
            self._version['primary']['status'] = False
            ret = False

        # Display
        log.info("-" * 50)
        log.info("Bootloader Current Primary Ver: {0}".format(self._version['primary']))
        log.info("Bootloader Target Ver         : {0}".format(version))

        return ret

    @func_details
    def upgrade(self, image, **kwargs):
        """ Upgrade the BIOS
        For Gen2 the bootloader/rommon is upgraded from the bootloader itself via a 'copy' command.
        :param (str) image: File name
        :param : kwargs
                 (str) image_type: None for GEN2
                 (str) device_name: device designation
                 (str) device_src_dir: Location of file on device (e.g. '/')
                 (str) network_src_url: URL of file on the network (e.g. 'tftp://10.1.1.1/biosimages')
        :return:
        """
        # Get to BTLDR
        original_mode = self._mode_mgr.current_mode
        if original_mode != 'BTLDR':
            log.debug("Not in Rommon/Btldr mode; changing to the target mode...")
            if not self._mode_mgr.goto_mode('BTLDR'):
                log.error("Problem trying to change mode.")
                log.error("Cannot perform upgrade.")
                return False

        # Input
        if not isinstance(image, str):
            log.error("The image parameter must be a str type.")
            return False
        image_type = kwargs.get('image_type', None)
        device_name = kwargs.get('device_name', 'flash')
        device_src_dir = kwargs.get('device_src_dir', '/')
        network_src_url = kwargs.get('network_src_url', None)

        log.debug("Image type = {0}".format(image_type)) if image_type else None

        # Check for image presence (load from network if required and available)
        full_path_image = "{0}:{1}".format(device_name, os.path.join(device_src_dir, image))
        log.info("Device image = {0}".format(full_path_image))
        if not self.get_device_files(device_name=device_name, file_filter=image):
            log.warning("The upgrade file ({0}) was not found on the device.".format(full_path_image))
            network_url = self._get_network_url(network_src_url)
            if not network_url:
                return False
            full_path_image = '{0}{1}'.format(network_url, os.path.join(device_src_dir, image).lstrip('/'))
            log.debug("Full network path = {0}".format(full_path_image))

        log.debug("Image is ready.")

        # Perform the upgrade
        self._clear_recbuf(self._uut_conn)
        time.sleep(self.RECBUF_CLEAR_TIME)
        self._uut_conn.send('set_bs bs: rw\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        self._uut_conn.send('copy {0} bs:\r'.format(full_path_image), expectphrase='.*', timeout=30, regex=True)

        # Loop to deal with the console output status updates
        loop_count = 0
        ret = False
        active_pattern = '{0}|(?:[\.]+)|(?:Are you sure)'.format(self._uut_prompt)
        old_status = ''
        while not ret and loop_count < 1000:
            self._uut_conn.waitfor(active_pattern, timeout=30, regex=True)
            new_status = self._uut_conn.recbuf.splitlines()[-1:][0]
            if new_status != old_status:
                # A change in the output status occurred; do something.
                loop_count += 1
                if re.search('(?:[\.]+)', self._uut_conn.recbuf):
                    log.debug("BTLDR Programming ({0})  {1} ...".format(loop_count, new_status))
                    old_status = new_status
                if re.search('successfully copied', self._uut_conn.recbuf):
                    log.debug('Done programming!')
                    ret = True
                if re.search('Are you sure', self._uut_conn.recbuf):
                    self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                if re.search('ERR', self._uut_conn.recbuf):
                    log.debug('Programming ERROR ocurred.')
                    break
                if re.search('(?i)no such file', self._uut_conn.recbuf):
                    log.debug('File does NOT exist.')
                    break
            time.sleep(1.0)

        if not ret:
            log.error("BTLDR Programming did not get a completion signal.")

        # Restore
        if original_mode != 'BTLDR':
            log.debug("Returning to the original mode...")
            self._mode_mgr.goto_mode(original_mode)

        return ret

    @func_details
    def set_uut_network_params(self, mac=None, ip=None, netmask=None, server_ip=None, sernum=None, tftp_ip=None):
        """ Set Network Params (WRAPPER)
        :param mac:
        :param ip:
        :param netmask:
        :param server_ip:
        :param sernum:
        :param tftp_ip:
        :return:
        """
        return self._select_set_uut_network_params(mac=mac,
                                                   ip=ip,
                                                   netmask=netmask,
                                                   server_ip=server_ip,
                                                   sernum=sernum,
                                                   tftp_ip=tftp_ip,
                                                   net_param_names='Gen2')

    @func_details
    def check_network_params(self, ip, netmask, server_ip, tftp_ip=None):
        """ Check Network Params (WRAPPER)
        :param ip:
        :param netmask:
        :param server_ip:
        :param tftp_ip:
        :return:
        """
        return self._select_check_network_params(ip, netmask, server_ip, tftp_ip=None, net_param_names='Gen2')

    @func_details
    def get_boot_param_image_details(self, fparams=None, default_device_name='flash', pattern=r'[\S]+'):
        """ Get Image Details from the BOOT Param
        :param fparams: Flash parameters used to extract BOOT param.
        :param default_device_name: Used if no device name was set in the parameter (e.g. 'tftp', 'flash', etc.)
        :param pattern: Regex pattern to use for searching filenames to find a suitable image.
        :return: tuple of image name, subdir(if any), device(typically 'flash' or 'tftp')
        """
        image = ''
        sub_dir = ''
        dev_name = ''
        fparams = self.get_params() if not fparams else fparams
        if 'BOOT' in fparams:
            bp_components = fparams['BOOT'].split(':')
            bp_dev_name, bp_full_filename = bp_components if len(bp_components) == 2 else \
                [default_device_name, bp_components]
            bp_sub_dir = os.path.dirname(bp_full_filename)
            bp_file = os.path.basename(bp_full_filename)
            if re.search(pattern, bp_file):
                image = bp_file
                sub_dir = bp_sub_dir
                dev_name = bp_dev_name
                log.info("Target image will be specified by BOOT param: {0}".format(image))
        else:
            log.warning("No BOOT param detected.")
        return image, sub_dir, dev_name

    @func_details
    def emergency_install(self, image, **kwargs):
        """ Perform emergency install with IOS main image

        Perform emergency-install from bootloader. If installation success, there will be expected phrase and switch will
        reboot to bootloader. If switch drop back to bootloader during installation w/o seeting expected phrase, installation
        fails.

        :param (str) image: File name
        :param kwargs:

        :return (bool): True for successful, False for unsuccessful
        """

        # Get to BTLDR
        original_mode = self._mode_mgr.current_mode
        if original_mode != 'BTLDR':
            log.debug("Not in Rommon/Btldr mode; changing to the target mode...")
            if not self._mode_mgr.goto_mode('BTLDR'):
                log.error("Problem trying to change mode.")
                log.error("Cannot perform installation.")
                return False

        # Input
        if not isinstance(image, str):
            log.error('Input image is {}'.format(image))
            log.error("The image parameter must be a str type.")
            return False
        tftp_ip = kwargs.get('tftp_ip', '10.1.1.1')
        ios_path = '{}/'.format(kwargs.get('ios_path')) if kwargs.get('ios_path') else ''

        # Perform the installation
        self._clear_recbuf(self._uut_conn)
        time.sleep(self.RECBUF_CLEAR_TIME)
        # Loop to deal with the console output status updates
        loop_count = 0
        ret = False
        self._uut_conn.send('emergency-install tftp://{0}/{1}{2}\r'.format(tftp_ip, ios_path, image),
                           expectphrase=['continue (y/n)', 'you sure you want to proceed?'])
        self._uut_conn.send('y\r')
        msg_list = ['Starting emergency recovery', 'Booting Recovery Image', 'Preparing flash',
                    'Emergency Install successful', 'Will reboot now', self._uut_prompt]
        while loop_count < 1000:
            self._uut_conn.waitfor(timeout=600, expectphrase=msg_list)
            # A change in the output status occurred; do something.
            loop_count += 1
            if re.search('Starting emergency recovery', self._uut_conn.recbuf):
                log.debug('Loading bundle image.')
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search('Booting Recovery Image', self._uut_conn.recbuf):
                log.debug('Loading recovery image.')
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search('Initiating Emergency Installation', self._uut_conn.recbuf):
                log.debug('Emergency installation initialized.')
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search('Preparing flash', self._uut_conn.recbuf):
                log.debug('Bundle images are downloaded and verified.')
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search('Emergency Install successful', self._uut_conn.recbuf):
                log.debug('Emergency Install successful.')
                ret = True
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search('Will reboot now', self._uut_conn.recbuf):
                log.debug('Emergency Install appears successful.')
                ret = True
                self._clear_recbuf(self._uut_conn, force=True)
            if re.search(self._uut_prompt, self._uut_conn.recbuf):
                log.debug('IOS main image installation complete.')
                break

        if not ret:
            log.error("Emergency Install does not get successful signal.")

        # Restore
        if original_mode != 'BTLDR':
            log.debug("Returning to the original mode...")
            self._mode_mgr.goto_mode(original_mode)

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNAL Functions
    #
    def _getflash(self):
        log.debug("Get flash...")
        cmd = 'set'
        pattern = r"[ \t]*([\S]+?)[ \t]*=[ \t]*(.*?)[\r\n]+"

        @func_retry(max_attempts=2)
        def __getflash():
            log.debug("Prompt={0}".format(self._uut_prompt))
            self._clear_recbuf(self._uut_conn)
            self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=40, regex=True)
            time.sleep(self.RECBUF_TIME)
            p = re.compile(pattern)
            m = p.findall(self._uut_conn.recbuf)
            if re.search('command .*? not found', self._uut_conn.recbuf):
                raise RommonException('Command not found.')
            return m

        params = dict(__getflash())
        return params

    def _get_network_param_names(self, net_param_names):
        if not net_param_names:
            npn = self.NetworkParamNames(*self.NETWORK_PARAM_SETS['Gen2'])
            log.debug("Using default Gen2 network param names.")
        elif isinstance(net_param_names, str):
            nps_list = self.NETWORK_PARAM_SETS.get(net_param_names, None)
            if not nps_list:
                log.error("Cannot find a known network parameter names list from the established set of lists.")
                return False
            npn = self.NetworkParamNames(*nps_list)
            log.debug("Using standard {0} network param names.".format(net_param_names))
        elif isinstance(net_param_names, list):
            if len(net_param_names) != 5:
                log.error("Network parameter name list must have only 5 elements.")
                return False
            log.debug("Using custom network param names: {0}".format(net_param_names))
            npn = net_param_names
        else:
            log.error("Unrecognized net_param_names: {0}".format(net_param_names))
            return False
        return npn

    def _select_set_uut_network_params(self, mac=None, ip=None, netmask=None, server_ip=None, sernum=None, tftp_ip=None, net_param_names=None):
        """ (INTERNAL) Select & Set Network Params
        Select the network param names and set them while in bootloader to facilitate a network boot of a bootable image.
        A valid MAC and IP must be provided; if not, the system is checked to determine if those are already set.
        If a MAC is not found but a sernum is provided then an attempt to lookup the MAC will be made.
        The netmask can be in 1 of 2 configs in rommon params:
            1. part of IP_ADDR = ip/mask
            2. separate IP_MASK

        :param (str) mac:
        :param (str) ip:
        :param (str) netmask:
        :param (str) server_ip: Gateway or default router IP
        :param (str) sernum: Serial Number associated with the MAC Addr
        :param (str) tftp_ip: Server to use for tftp download/upload (typically same as gateway)
        :param (list|str|None) net_param_names: identifies the flash param names used for setting vb: in bootloader.
        :return (bool) ret: True if param setting was good.
        """
        log.debug("Pre-check: IP='{0}', NM='{1}', GW='{2}', TFTP='{3}', MAC='{4}'".format(ip, netmask, server_ip, tftp_ip, mac))
        fparams = self.get_params() if not mac or not ip else None
        log.debug(fparams)

        npn = self._get_network_param_names(net_param_names)
        if not npn:
            return False

        # Get any pre-programmed flash params
        log.debug("Using network param names: {0}".format(npn))
        programmed_mac = fparams.get(npn.mac, '')
        programmed_ip = fparams.get(npn.ip, '')
        __ip = programmed_ip.split('/')
        programmed_ip = __ip[0]
        programmed_server_ip = fparams.get(npn.gw, '')
        programmed_tftp_ip = fparams.get(npn.tftp_srvr, '')
        if not npn.mask:
            programmed_mask = __ip[1] if len(__ip) > 1 else ''
        else:
            programmed_mask = fparams.get(npn.mask, '')

        # Set param defaults or overrides
        mac = programmed_mac if not mac else mac
        ip = programmed_ip if not ip else ip
        netmask = programmed_mask if not netmask else netmask
        server_ip = programmed_server_ip if not server_ip else server_ip
        tftp_ip = programmed_tftp_ip if not tftp_ip else tftp_ip

        # Sanity Check
        if not mac and sernum:
            log.info("No MAC input; attempting to retrieve assigned MAC if one exists for S/N={0}.".format(sernum))
            mac, _ = get_mac(sernum)
            if not mac:
                log.error("No MAC available; need to generate one.")
                return False
        elif not mac and not sernum:
            log.error("Need to generate/retrieve a MAC!")
            log.error("Cannot setup the network!")
            return False

        log.debug("Post-check: IP='{0}', NM='{1}', GW='{2}', TFTP='{3}', MAC='{4}'".format(ip, netmask, server_ip, tftp_ip, mac))

        # Validate the IP, Netmask, and MAC; if all are good then set the params if they need it.
        if validate_ip_addr(ip, 'IPv4') and \
                validate_ip_addr(netmask, 'IPv4') and \
                validate_mac_addr(mac):
            newparams = dict()
            if not npn.mask:
                newparams[npn.ip] = "{0}/{1}".format(ip, netmask)
            else:
                newparams[npn.ip] = "{0}".format(ip)
                newparams[npn.mask] = "{0}".format(netmask)
            newparams[npn.mac] = mac
            if server_ip:
                newparams[npn.gw] = server_ip
            if tftp_ip:
                newparams[npn.tftp_srvr] = tftp_ip
            ret = self.set_params(newparams)
        else:
            log.warning("UUT network is incomplete due to invalid param values! Cannot set up the network connection.")
            ret = False
        return ret

    def _select_check_network_params(self, ip, netmask, server_ip, tftp_ip=None, net_param_names=None):
        """ Check Bootloader Network Params
        Compare the UUT Bootloader network params to system assigned values (via input provided).
        :param (str) ip:
        :param (str) netmask:
        :param (str) server_ip:
        :param (str) tftp_ip:
        :return (bool) ret: True if comparison matches.
        """
        fparams = self.get_params()
        log.debug(fparams)

        npn = self._get_network_param_names(net_param_names)
        if not npn:
            return False

        # Get any pre-programmed flash params
        programmed_ip = fparams.get(npn.ip, '')
        __ip = programmed_ip.split('/')
        programmed_ip = __ip[0]
        programmed_server_ip = fparams.get(npn.gw, '')
        programmed_tftp_ip = fparams.get(npn.tftp_srvr, '')
        programmed_mask = fparams.get(npn.mask, '')
        # programmed_masks = [__ip[1] if len(__ip) > 1 else '', fparams.get('IP_MASK', ''), fparams.get('IP_SUBNET_MASK', '')]
        # for nm in programmed_masks:
        #     if nm:
        #         programmed_mask = nm
        #         break
        # else:
        #     programmed_mask = ''

        results = list()
        results.append(True if ip == programmed_ip else False)
        results.append(True if netmask == programmed_mask else False)
        results.append(True if server_ip == programmed_server_ip else False)
        results.append(True if tftp_ip == programmed_tftp_ip else False) if tftp_ip else None
        ret = all(results)

        log.debug("Network check-up")
        log.debug("----------------")
        log.debug("Desc       {0:<20} {1:<20}".format('ref', 'flash'))
        log.debug("IP      :  {0:<20} {1:<20}".format(ip, programmed_ip))
        log.debug("Netmask :  {0:<20} {1:<20}".format(netmask, programmed_mask))
        log.debug("Server  :  {0:<20} {1:<20}".format(server_ip, programmed_server_ip))
        log.debug("TFTP    :  {0:<20} {1:<20}".format(tftp_ip, programmed_tftp_ip)) if tftp_ip else None

        if ret:
            log.debug("UUT network params match system.")
        else:
            log.debug("UUT network params do NOT match system.")
        return ret

    def _get_network_url(self, network_src_url=None):
        """ Get Network URL
        For remote downloads, ensure the network URL is working.
        Currently supports only TFTP
        :param network_src_url:
        :return:
        """
        if not network_src_url:
            log.warning("Assume the default Network URL.")
            network_src_url = 'tftp://{0}/{1}'.format(self._ud.uut_config['server_ip'], '')
        log.debug("Network URL for downloads = {0}".format(network_src_url))
        m = re.search('(?P<protocol>[a-zA-Z0-9]+)://(?P<server_ip>[0-9\.]+)[/]?(?P<sudir>.*)', network_src_url)
        protocol, server_ip, subdir = (m.groups()[0], m.groups()[1], m.groups()[2]) if m else ('', '', '')
        if protocol == 'tftp':
            log.debug("Checking server connection for tftp protocol...")
            server_ip = self._ud.uut_config['server_ip'] if not server_ip else server_ip
            if not self.ping(server_ip):
                if not self.set_uut_network_params(ip=self._ud.uut_config['uut_ip'],
                                                   netmask=self._ud.uut_config['netmask'],
                                                   server_ip=server_ip):
                    log.error("Cannot upgrade bootloader from the network.")
                    return False
                # Check ping again
                if not self.ping(server_ip):
                    log.error("Network setup issue; cannot ping. Bootloader upgrade not possible.")
                    return False
        elif protocol == 'ftp':
            log.error("The ftp network protocol is NOT supported.")
            return False
        else:
            log.error("No recognized network protocol.")
            return False

        return network_src_url

    def _clear_recbuf(self, uut_conn, force=False):
        if self.USE_CLEAR_RECBUF or force:
            uut_conn.clear_recbuf()
            time.sleep(self.RECBUF_CLEAR_TIME)
        return

    def _get_version(self):
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('version\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        log.debug("Checking rommon version...")
        m = parse.search('Version {ver:0},{x1:1}Compiled {dow:2} {month:3} {day:4} {time:5} {tz:6} {yr:7} by', self._uut_conn.recbuf)
        if m:
            return m.named
        else:
            return None

    @staticmethod
    def _mac_special(key, setparams, fullparams):
        if key == 'MAC_ADDR' and validate_mac_addr(fullparams[key]):
            if convert_mac(setparams[key]) != convert_mac(fullparams[key]):
                log.critical("The MAC_ADDR is attempting to be changed where a valid addr already exists!")
                log.critical("Something went terribly wrong with the parameter data!")
                log.critical("Review UUT config data and the testing process.")
                log.critical("Current MAC_ADDR = {0}".format(fullparams[key]))
                log.critical("New MAC_ADDR     = {0}".format(setparams[key]))
                raise aplib.apexceptions.ResultFailure("MAC_ADDR param data conflict.")
            else:
                log.warning("Current MAC and set MAC are equivalent but in different forms; be careful!")
        return

    def _check_dependencies(self):
        if not self._mode_mgr:
            log.warning("*" * 50)
            log.warning("The BTLDR/ROMMON mode must be present when apttempting to use this driver.")
            log.warning("Since a Mode Manager was NOT provided, the mode and dependencies cannot be guaranteed!")
            log.warning("*" * 50)
            raise RommonException("The rommon driver MUST have a Mode Manager.")
        if not self._ud or not getattr(self._ud, 'uut_config'):
            log.warning("*" * 50)
            log.warning("The BTLDR/ROMMON mode must have a description of the UUT when apttempting to use this driver.")
            log.warning("Since a UUT Descriptor was NOT provided, this driver will generate an exception!")
            log.warning("*" * 50)
            raise RommonException("The rommon driver MUST have a UUT Descriptor.")
        return True


class RommonGen3(Rommon):
    """ Generic C9x00 Rommon Driver
    Use this for all "Generation 3" (Gen3) products - aka C9200/C9300/C9400/C9500
    This class inherits from the general (Rommon) class and provides for additional support methods
    (e.g. TLV)
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonGen3, self).__init__(mode_mgr, ud, **kwargs)
        self._verbose = True
        self._linux = kwargs.get('linux', None)
        return

    @func_details
    def get_params(self):
        """ Get Parameters
        Generic routine for obtaining the motherboard flash parameters from vb: space.
        The pb: space params are now in TLV for in ACT2 and can only be read via bootloader/rommon.

        Example:
        switch: set
        ABNORMAL_RESET_COUNT=0
        BOARDID=20563
        BOOT_PARAM=console=ttyS0,115200 root=/dev/ram0 BOARDID=20563 SWITCH_NUMBER=1
        BSI=0
        DEFAULT_GATEWAY=172.20.128.1
        D_STACK_DOMAIN_NUM=1
        IP_ADDRESS=172.20.128.231
        IP_SUBNET_MASK=255.255.255.0
        LICENSE_BOOT_LEVEL=lanbasek9,all:ngwc;
        MAC_ADDR=00:11:22:33:44:55
        PS1=switch:
        RANDOM_NUM=387482152
        REAL_MGMTE_DEV=
        RET_2_RCALTS=1481529069
        RET_2_RTS=
        SR_MGMT_VRF=0
        SWITCH_NUMBER=1
        TEMPLATE=advanced
        TFTP_BLKSIZE=8192
        TFTP_FILE=/tftp-sjc-users2/jahuang/cat3k.bin
        TFTP_SERVER=172.20.128.17
        switch:


        Shannon48P>

        Shannon48P> gettlv
        Part Number - PCA               : 73-17956-03
        Revision number - PCA           : P3
        Deviation Number                : 0x00000000
        Serial Number - PCA             : FHH20390015
        RMA test history                : 0x00
        RMA Number                      : 0-0-0-0
        RMA history                     : 0x00
        Part Number - TAN               : 68-5994-01
        Revision number - TAN           : A0
        CLEI codes                      : 0123456789
        ECI number                      : 0
        Product number/identifier       : WS-C3850X-48P
        Version identifier              : V01
        Serial number                   : FHH2040P001
        MAC address - Base              : 0C75.BD0F.0580
        MAC address - block size        : 128
        RFID - chassis                  : E000000000000000
        Manufacturing test data         : 0000000000000000
        DB info
          USB DB
            Part number - USB           : 73-16167-02
            Rev number - USB            : A0
            Serial number - USB         : SNxxxxxxxxx
          StackPower DB
            Part number - StackPower    : 73-11956-08
            Rev number - StackPower     : B0
            Serial number - StackPower  : SNxxxxxxxxx
        DB info
          POE DB 1
            Part number - POE1          : 73-16439-02
            Rev number - POE1           : A0
            Serial number - POE1        : SNxxxxxxxxx
          POE DB 2
            Part number - POE2          : 73-16439-02
            Rev number - POE2           : A0
            Serial number - POE2        : SNxxxxxxxxx

        Shannon48P>

        :return params: (dict) All UUT params from vb: & tlv: (in traditional form)
        """
        params = {}
        log.debug("GenericGen3 get_params...")
        if self._fresh_read and self._params:
            log.debug("Params are fresh.")
            return self._params

        try:
            # Get flash params from two locations
            tlv_params = self._gettlv(device_instance=0)
            vb_params = self._getflash()

            # Combine
            # Note1: 'tlv:' can be duplicated in 'vb:' however 'tlv:' is the gold source.
            # Note2: 'vb:' will be set FIRST for MAC and network connectivity.
            # Note3: Because 'vb:' is set first on new units, it has PRECEDENCE when combining with 'tlv:'.
            #        ENSURE 'vb:' is correct since 'tlv:' gets overwritten with 'vb:' data!
            # Note4: Some bootloaders will update vb: automatically AFTER tlv: is programmed for the first time.
            log.debug("tlv_params = {0}".format(tlv_params))
            log.debug("vb_params = {0}".format(vb_params))
            params = tlv_params.copy()
            # params.update(vb_params)
            for k, v in vb_params.items():
                if v:
                    if k in params:
                        log.debug("Override TLV with vb: {0}".format(k))
                    else:
                        log.debug("Extra item vb: not in TLV: {0}".format(k))
                    params[k] = v
                else:
                    # vb_params item is empty so allow tlv item data to be used if available
                    if params.get(k, None):
                        log.debug("Keep TLV item since vb item is empty: {0}".format(k))

        except apexceptions.TimeoutException:
            log.error("UUT timed out for bootloader response.")
        except RommonException as e:
            log.warning(e)
        except Exception as e:
            log.error(e)
        finally:
            self._params = params
            self._fresh_read = True
            return params

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNAL Functions
    #
    def _gettlv(self, device_instance=None, physical_slot=None, tlv_type=None):
        log.debug("Get TLV...")
        # tlv Params (from either bootloader or diags)
        if device_instance and physical_slot:
            log.warning("Only specify one: EITHER device_instance OR physical_slot.")
            log.warning("Defaulting to use device_instance.  The physical_slot will be ignored.")
            physical_slot = None
        options = []
        if device_instance is not None:
            options.append('-i:{0}'.format(device_instance))
        elif physical_slot is not None:
            options.append('-s:{0}'.format(physical_slot))
        else:
            if tlv_type is not None:
                log.debug("An attempt to use only TLV type ({0}) will be made.".format(tlv_type))
            else:
                log.warning("No device_instance and no physical_slot specified.")
                log.warning("No tlv_type specified; cannot get TLV data!")
                return {}

        if tlv_type:
            options.append('-t:{0}'.format(tlv_type))

        @func_retry(max_attempts=1)
        def __gettlv():
            self._clear_recbuf(self._uut_conn)
            current_prompt = self._mode_mgr.current_prompt_pattern
            self._uut_conn.send('gettlv {0}\r'.format(' '.join(options)), expectphrase=current_prompt, timeout=20, regex=True)
            time.sleep(self.RECBUF_TIME)
            # Note: The regex pattern should discard any items not having a value.
            pattern = r"[ \t]*([A-Za-z].*?)[ \t]+:[ \t]+([\S]*)"
            p = re.compile(pattern)
            if "'gettlv' not found" in self._uut_conn.recbuf:
                log.debug("The 'gettlv' command is NOT available in this rommon.")
                return None
            return p.findall(self._uut_conn.recbuf)

        m = __gettlv()
        tlv_params = {}
        if m:
            d = dict(m)
            tlv_params = {self._ud.tlv_map[k][1]: v for k, v in d.items() if k in self._ud.tlv_map}
            if self._verbose:
                log.debug("tlv_params-----")
                log.debug(tlv_params)
                log.debug("self._ud.tlv_map-----")
                log.debug(self._ud.tlv_map)
            hdr = "{0:<2}. {1:<30}   {2:<30}     {3}             ".format('No', 'TLV', 'Param', 'Value')
            log.debug(hdr)
            log.debug("-" * len(hdr))
            for i, kv in enumerate(d.items(), 1):
                k, v = kv[0], kv[1]
                log.debug("{0:>02d}. {1:<30}   {2:<30}  =  {3}".format(i, k, self._ud.tlv_map.get(k, ('00', '** unknown **'))[1], v))
            log.debug("-" * len(hdr))
        else:
            log.warning("No TLV params to return.")
        return tlv_params


# ----------------------------------------------------------------------------------------------------------------------
# C2K & C9200 Family
class RommonC2000(Rommon):
    """ WS-C3x00 Rommon Driver
    This class is product family specific.
    Families included: Edison, Gladiator, Planck, Orsted, Euclid, Theon, Archimedes
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC2000, self).__init__(mode_mgr, ud, **kwargs)
        return


class RommonC9200(RommonGen3):
    """ C9200 Rommon Driver
    This class is product family specific.
    Families included: Quake
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC9200, self).__init__(mode_mgr, ud, **kwargs)
        return

    @func_details
    def get_devices(self):
        """ Get Devices
        List of available devices to access from bootloader/rommon

        sboot64> dir

        List of filesystems currently registered:

            flash:      3.10227GB   Main flash disk filesystem (eMMC)
              sb1:     64.0KB   Sboot1 secure binary on main flash disk
             sb1g:     64.0KB   Sboot1 golden secure binary on main flash disk
              env:     16.0KB   Environment variable storage on main flash disk
             envg:     16.0KB   Environment variable golden storage on main flash disk
              mfg:     16.0KB   Manufacturing data storage on main flash disk
              sb2:    512.0KB   Sboot2 secure binary on main flash disk
             sb2g:    512.0KB   Sboot2 golden secure binary on main flash disk
               sd:     62.7MB   SD card filesystem
              spi:      2.7MB   SPI flash disk filesystem
             usb0:      0.0KB   USB0 flash disk filesystem
             usb1:      0.0KB   USB1 flash disk filesystem
           mmcraw:      1.0GB   Raw byte access to main flash disk (eMMC)
            sdraw:      1.0GB   Raw byte access to SD card
           spiraw:      4.0MB   Raw byte access to SPI flash disk
           xmodem:      0.0KB   Xmodem filesystem

        :return m: (list) All available devices seen by bootloader
        """
        m = list()
        try:

            @func_retry(max_attempts=1)
            def __dirdev():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('dir\r', expectphrase=self._uut_prompt, timeout=20, regex=True)
                time.sleep(self.RECBUF_TIME)
                p = re.compile(r"[ \t]*([\S]+)\:[ \t]+.*?[\r\n]+")
                return p.findall(self._uut_conn.recbuf)

            m = __dirdev()
        except Exception as e:
            log.error(e)
        finally:
            return m

    @func_details
    def get_device_files(self, device_name='flash', sub_dir='', file_filter='.*?', attrib_flags='-ld', attrib_filter=None):
        """ Get Device Files (via rommon/bootloader)
        Get device files (or dirs) only from the sub directory path given.
        Apply file attribs and regex patterns as filters.

        Sample output to process is given below:

        BTLDR #1 (proto)
         sboot64> dir flash:

         Date       Time    Attribute   Size         Name
         ========== =====   ==========  ==========   ================
         2017/06/14 23:12   drwxr-xr-x        4096   .install
         2017/06/14 23:12   drwxrwxrwx        4096   user
         1970/01/01 00:15   -rwxrwxrwx    24659752   uImage64.171114
         1970/01/01 00:16   -rwxrwxrwx        4370   dtb_4cores.170810

           Total space = 1941504 KB
           Available   = 1884008 KB


       BTLDR #2 (release)
        switch: dir flash:
        Attributes        Size         Name
         - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        -rwxrwxrwx    43492452   quake.itb.ssa.180727
        -rwxrwxrwx      423388   sboot2v64s_mac_addr_fix.bin
        -rwxrwxrwx    43492452   quake.itb.ssa.180720
        -rwxrwxrwx    43492452   quake.itb.ssa.180815B
        -rwxrwxrwx    28733313   cat9k_lite_autoupgrade_v10.3.bin
        -rwxrwxrwx    43508836   quake.itb.ssa.180906
         - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        :param (str) device_name: Device to operate on.
        :param (str) sub_dir: Sub directory path to look in.
        :param (str) file_filter: Look only for files matching the regex filter.
        :param (str) attrib_flags: Use "d", "l', and "-" for dir, link, and file. (Default is get everything.)
        :param (str) attrib_filter: regex for file attributes (overrides attrib_flag)
        :return (list) m: All available devices seen by bootloader
        """
        m = list()
        try:

            @func_retry(max_attempts=1)
            def __dir():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('dir {0}:{1}\r'.format(device_name, sub_dir), expectphrase=self._uut_prompt, timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                a_filter = '[{0}][-rwx]'.format(attrib_flags) + '{9}' if not attrib_filter else attrib_filter
                pattern_proto = r"[ \t]*[0-9/: ]+[ \t]+{1}[ \t]+[0-9]+[ \t]+({0})[\r\n]+".format(file_filter, a_filter)
                pattern_release = r"[ \t]*{0}[ \t]+[0-9]+[ \t]+({1})[\r\n]+".format(a_filter, file_filter)
                p1 = re.compile(pattern_proto)
                p2 = re.compile(pattern_release)
                m1 = p1.findall(self._uut_conn.recbuf)
                m2 = p2.findall(self._uut_conn.recbuf)
                return list(set(m1) | set(m2))

            m = __dir()
            if not m:
                log.debug("No files found that match the criteria.")
                return m
            # Remove relative dir names (if in the list)
            i = 0
            while i < len(m):
                if m[i] == '.' or m[i] == '..':
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
    def set_params(self, setparams, **kwargs):
        """ Set Params
        Set flash parameters for ALL blocks (parameter and variable).
        A verification step is done afterwards.
        By default the "pb:" block is made writeable and burned.

        :param (dict) setparams: Params and values to set.
        :param kwargs:
                 reset_required:    (bool) whether to reset bootloader after operation, default False.
                 restore_ro:        (bool) read only protect set on vb:
        :return ret: (bool) True if all values to set were successfully set.
        """
        log.debug("Setting w/ {0}".format(RommonC9200))
        reset_required = kwargs.get('reset_required', True)
        restore_ro = kwargs.get('restore_ro', False)
        ret = True
        try:
            # Get initial settings
            fullparams = self.get_params()

            # Set or update the params
            log.debug("SETTING C2K/C9200 Gen3 Rommon Params...")
            for key in setparams:
                if key in fullparams:
                    if setparams[key]:
                        if setparams[key] != fullparams[key]:
                            # Change the parameter
                            self._mac_special(key, setparams, fullparams)
                            self._uut_conn.send('setenv {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                               expectphrase=self._uut_prompt, timeout=20, regex=True)
                            log.info("{0} = {1}  (set changed)".format(key, setparams[key]))
                        else:
                            # No change necessary
                            log.info("{0} = {1}".format(key, setparams[key]))
                    else:
                        # Empty or null value will be ignored.
                        log.info("{0} is empty; not allowed when setting. Use 'unset' instead.".format(key))
                else:
                    # Create a new parameter if it has a value
                    if setparams[key]:
                        self._uut_conn.send('setenv {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                           expectphrase=self._uut_prompt, timeout=10, regex=True)
                        log.info("{0} = {1}  (set new)".format(key, setparams[key]))
                    else:
                        log.debug("{0} is empty & new, ignore it.".format(key))
            self._fresh_read = False

            # Now verify that the params were actually set
            if reset_required:
                log.debug("Reset is required...")
                self._uut_conn.send('reset\r', expectphrase='reset', timeout=20, regex=True)  # 'reset the system (y/n)?'
                self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                log.debug("Waiting for boot...")
                self._mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')

            fullparams = self.get_params()
            for key in setparams:
                if key in fullparams:
                    if setparams[key] and setparams[key] != fullparams[key]:
                        # Invalid; something went wrong during the set process.
                        log.warning("{0} setenv = '{1}'  found = '{2}'".format(key, setparams[key], fullparams[key]))
                        ret = False
                else:
                    if setparams[key]:
                        # Invalid, the item is missing and is not ignored.
                        log.warning("{0} was NOT found.".format(key))
                        ret = False

        except aplib.apexceptions.ResultFailure as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def get_boot_param_image_details(self, fparams=None, default_device_name='flash', pattern=r'[\S]+'):
        """ Get Image Details from the BOOT Param
        :param fparams: Flash parameters used to extract BOOT param.
        :param default_device_name: Used if no device name was set in the parameter (e.g. 'tftp', 'flash', etc.)
        :param pattern: Regex pattern to use for searching filenames to find a suitable image.
        :return: tuple of image name, subdir(if any), device(typically 'flash' or 'tftp')
        """
        image = ''
        sub_dir = ''
        dev_name = ''
        fparams = self.get_params() if not fparams else fparams
        if 'BOOT64' in fparams:
            bp_components = fparams['BOOT64'].split(':')
            bp_dev_name, bp_full_filename = bp_components if len(bp_components) == 2 else \
                [default_device_name, bp_components]
            bp_sub_dir = os.path.dirname(bp_full_filename)
            bp_file = os.path.basename(bp_full_filename)
            if re.search(pattern, bp_file):
                image = bp_file
                sub_dir = bp_sub_dir
                dev_name = bp_dev_name
                log.info("Target image will be specified by BOOT64 param: {0}".format(image))
        else:
            log.warning("No BOOT64 param detected.")
            log.debug("Params = {0}".format(fparams))
        return image, sub_dir, dev_name

    @func_details
    def set_uut_network_params(self, mac=None, ip=None, netmask=None, server_ip=None, sernum=None, tftp_ip=None):
        """ Set Network Params (WRAPPER)
        :param mac:
        :param ip:
        :param netmask:
        :param server_ip:
        :param sernum:
        :param tftp_ip:
        :return:
        """
        if not tftp_ip:
            tftp_ip = server_ip
            log.debug("Defaulting the TFT Server = {0}".format(tftp_ip))
        return self._select_set_uut_network_params(mac=mac,
                                                   ip=ip,
                                                   netmask=netmask,
                                                   server_ip=server_ip,
                                                   sernum=sernum,
                                                   tftp_ip=tftp_ip,
                                                   net_param_names='Gen3b')

    @func_details
    def check_network_params(self, ip, netmask, server_ip, tftp_ip=None):
        """ Check Network Params (WRAPPER)
        :param ip:
        :param netmask:
        :param server_ip:
        :param tftp_ip:
        :return:
        """
        if not tftp_ip:
            tftp_ip = server_ip
            log.debug("Defaulting the TFT Server = {0}".format(tftp_ip))
        return self._select_check_network_params(ip, netmask, server_ip, tftp_ip=tftp_ip, net_param_names='Gen3b')

    @func_details
    def upgrade(self, images, **kwargs):
        """ Upgrade

        Example:
            boot64> spi program spi:sboot1s_1221.bin brom:
            SPI Program from spi:sboot1s_1221.bin to brom:(0x00010000), 0x10000 bytes
            spi:sboot1s_1221.bin opened; file size: 65536 Bytes
            SecureBoot: authentication keys @ 0xFF543558...
            SecureBoot: signing key parsed successfully!
            SecureBoot: signing key verified successfully!
            SecureBoot: image verified successfully!
            SPI Sector erase: from 0x00010000, 0x10000 bytes(1 sectors)
            .
            SPI Write from spi:sboot1s_1221.bin to brom:(0x00010000), 0x10000 bytes
            blk_num - 0x80, blk_count - 0x80(btr-0x10000).
            SPI Read: From spi:sboot1s_1221.bin to 0x80000000, 0x10000 bytes
            SPI Read: From brom:(0x00010000) to 0x80400000, 0x10000 bytes
            blk_num - 0x80, blk_count - 0x80(btr-0x10000).

            Program Success !!!

        :param (str|list) images: Filename (or list of names) with which to upgrade
        :param: kwargs
                 (str) image_type: SB (only option)
                 (str) device_name: device designation
                 (str) params: Params used in the upgrade command
                 (str) device_src_dir: Location of file on device (e.g. '/')
                 (str) network_src_url: URL of file on the network (e.g. 'tftp://10.1.1.1/biosimages')
                 (bool) reset_required: reboot after upgrade
        :return:
        """
        # Input
        if not isinstance(images, str) and not isinstance(images, list):
            log.error("The image parameter must be a str or list type.")
            return False
        images = [images] if not isinstance(images, list) else images
        # image_type = kwargs.get('image_type', 'SB')
        device_name = kwargs.get('device_name', 'flash')
        dst_device_name = kwargs.get('dst_device_name', 'spi')
        device_src_dir = kwargs.get('device_src_dir', '/')
        network_src_url = kwargs.get('network_src_url', None)
        reset_required = kwargs.get('reset_required', True)

        # Show initial env
        self._uut_conn.send('setenv\r', expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Get initial files in flash
        ffiles = self.get_device_files(device_name=device_name, sub_dir=device_src_dir, attrib_flags='-')
        log.debug("ffiles = {0}".format(ffiles))

        # Process each image; move to "spi:"
        for image in images:
            src_full_path_image = "{0}:{1}".format(device_name, image)
            dst_full_path_image = "{0}:{1}".format(dst_device_name, image)
            log.info("Src device image = {0}".format(src_full_path_image))

            # Check if a copy is available in flash; if not pull it from the network and put directly to "spi:"
            if image not in ffiles:
                log.warning("The file ({0}) was not found on the device.".format(src_full_path_image))
                network_url = self._get_network_url(network_src_url)
                if not network_url:
                    return False
                src_full_path_image = '{0}{1}'.format(network_url, os.path.join(device_src_dir, image).lstrip('/'))
                log.debug("Full network path = {0}".format(src_full_path_image))

            # Perform the upgrade
            self._clear_recbuf(self._uut_conn)
            time.sleep(self.RECBUF_CLEAR_TIME)
            self._uut_conn.send('copy {0} {1}\r'.format(src_full_path_image, dst_full_path_image), expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Check the target files
        sfiles = self.get_device_files(device_name=dst_device_name, attrib_filter=r'[-A]{5}')
        log.debug("ffiles = {0}".format(sfiles))
        for image in images:
            if image not in sfiles:
                log.error("{0} file not in '{1}:'.".format(image, dst_device_name))
                return False

        # Do the actual programming
        for image in images:
            if 'sboot1' in image:
                btldr_device = 'brom'
            elif 'sboot2' in image:
                btldr_device = 'bs'
            else:
                btldr_device = None
            if btldr_device:
                log.debug("Programming bootloader image {0}:{1} to device '{2}'".format(dst_device_name, image, btldr_device))
                self._uut_conn.send('spi program {0}:{1} {2}:\r'.format(dst_device_name, image, btldr_device),
                                   expectphrase='Program Success', timeout=60, regex=True)

        if reset_required:
            log.info("NOTICE: Reset is required to complete the update.")
            self._reset()

        log.info("ALL bootloader files: SUCCESSFUL update.")
        return True

    # -----------------------------------------------------------------------
    # INTERNAL Functions
    def _getflash(self):
        """
        sboot64> setenv
        BAUD=9600
        BOOT=flash:uImages
        BOOT64=flash:uImage64.171114
        BOOT64_DTB=flash:dtb_4cores.170810
        BOOT_DTB=flash:craw.dtb
        MANUAL_BOOT=yes
        BOOT_PARAMS=failure_shell emergency
        COPY_SBOOT2=copy 0x80000000 sb2: 0x80000
        DEFAULT_ROUTER=10.1.1.1
        IP_ADDR=10.1.0.36
        IP_MASK=255.255.0.0
        LINUX_DEBUG=no
        MAC_ADDR=70:6B:B9:B0:5D:00
        MEM_SIZE=2048
        MEM_TEST=yes
        MMC_FLASH=copy 0x80000000 mmcraw: 0x1000000
        MODEL_NUM=C9200-24P-4X
        MODEL_REVISION_NUM=P1B
        MOTHERBOARD_ASSEMBLY_NUM=73-18699-01
        MOTHERBOARD_REVISION_NUM=10
        SD_FLASH=copy 0x80000000 sdraw: 0x1000000
        SOC_WDOG=on
        SYSTEM_SERIAL_NUM=JPG213100DD
        TAN_NUM=68-101386-01
        TFTP_SERVER=10.1.1.1
        :return:
        """
        cmd = 'setenv'
        pattern = r"[ \t]*([\S]+)[ \t]*=[ \t]*(.*?)[\r\n]+"

        @func_retry(max_attempts=1)
        def __getflash():
            self._clear_recbuf(self._uut_conn)
            self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=20, regex=True)
            time.sleep(self.RECBUF_TIME)
            p = re.compile(pattern)
            m = p.findall(self._uut_conn.recbuf)
            if re.search('command .*? not found', self._uut_conn.recbuf):
                raise RommonException('Command not found.')
            return m

        params = dict(__getflash())
        return params

    def _get_version(self):
        """
        Example:
        [SBOOT2 v6.1 crayprod_20170515-42-gb8438dd mmohisin-20170919-1530]
        :return:
        """
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('version\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        log.debug("Checking rommon C2KGen3 version...")
        m = parse.search('[SBOOT2 v{ver:0} {x1:1} {n:2}-{date:3}-{time:4}]', self._uut_conn.recbuf)
        if m:
            return m.named
        else:
            return None

    def _reset(self):
        self._uut_conn.send('reset\r', expectphrase='reset', timeout=20, regex=True)  # 'reset the system (y/n)?'
        self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
        log.debug("Waiting for boot...")
        boot_result, _ = self._mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')
        if not boot_result:
            log.error("The RESET did NOT complete properly; FATAL ERROR.")
            raise StandardError("Reset + boot has fatal error.")

        return


# ----------------------------------------------------------------------------------------------------------------------
# C3K & C9300 Family
class RommonC3000(Rommon):
    """ WS-C3x00 Rommon Driver
    This class is product family specific.
    Families included: Edison, Gladiator, Planck, Orsted, Euclid, Theon, Archimedes
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC3000, self).__init__(mode_mgr, ud, **kwargs)
        return

    @func_details
    def unset_params(self, unset_params, **kwargs):
        """ Unset Params
        Unset flash parameters for ALL blocks (parameter and variable).
        A verification step is done afterwards.
        By default the "pb:" block is made writeable and burned.

        :param unset_params:        (list) Params to unset.
        :param kwargs:
                 reset_required:    (bool) whether to reset bootloader after operation, default False.
                 restore_ro:        (bool) read only protect set on vb:
        :return ret:                (bool) True if all values to set were successfully set.
        """
        reset_required = kwargs.get('reset_required', False)
        restore_ro = kwargs.get('restore_ro', False)
        ret = True
        try:
            # Get initial settings
            fullparams = self.get_params()

            time.sleep(1.0)
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=20, regex=True)

            # Set or update the params
            log.debug("UNSETTING Rommon Params...")
            for key in unset_params:
                if key in fullparams:
                    self._uut_conn.send('unset {0}\r'.format(key), expectphrase=self._uut_prompt, timeout=20, regex=True)
                    log.info("Unset param {0}".format(key))

            # Burn the parameter block
            # The "pb:" area is a strictly defined set of params used by IOS (and diags) that MUST be populated!
            # Note: "pb:" is typically protected by a read-only setting.
            #       The ro setting should be restored during customer configuration time.
            time.sleep(1.0)
            self._uut_conn.send('set_bs pb: rw\r', expectphrase=self._uut_prompt, timeout=10, regex=True)
            self._uut_conn.send('set_param -all\r', expectphrase=self._uut_prompt, timeout=10, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'Parameters burned' in self._uut_conn.recbuf:
                log.debug("Parameters burned into pb:")
            else:
                log.error("Parameters NOT burned into pb: !")
                ret = False
                raise aplib.apexceptions.ResultFailure("Param burn in pb: NOT confirmed.")
            if restore_ro:
                log.debug('Restore pb: to read-only.')
                self._uut_conn.send('set_bs pb: ro\r', expectphrase=self._uut_prompt, timeout=10, regex=True)
            self._fresh_read = False

            # Now verify that the params were actually removed
            fullparams = self.get_params()
            for key in unset_params:
                if key in fullparams:
                    # Invalid, the item shouldn't exist once unset.
                    log.warning("{0} was found, which shouldn't exist.".format(key))
                    ret = False
            # reset rommon if it is required
            if reset_required:
                log.debug("Reset is required...")
                self._uut_conn.send('reset\r', expectphrase='reset', timeout=20, regex=True)  # 'reset the system (y/n)?'
                self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                log.debug("Waiting for boot...")
                self._mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')

        except aplib.apexceptions.ResultFailure as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def set_params(self, setparams, **kwargs):
        # add reset_required for compatibility
        return super(RommonC3000, self).set_params(setparams, **kwargs)


class RommonC9300(RommonGen3):
    """C9300 Rommon Driver
    This class is product family specific.
    Families included: Nyquist
    """

    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC9300, self).__init__(mode_mgr, ud, **kwargs)
        return

    @func_details
    def get_devices(self):
        """ Get Devices
        List of available devices to access from bootloader/rommon

        Sample output:
        Usage: dir { [ flash: ] | [ usbflash0: ] | [ usbflash1: ] }

        :return m: (list) All available devices seen by bootloader
        """
        m = list()
        try:

            @func_retry(max_attempts=1)
            def __dirdev():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('dir\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
                p = re.compile(r"[ \t]+([a-z0-9_]+):[ \t]*")
                time.sleep(self.RECBUF_TIME)
                return p.findall(self._uut_conn.recbuf)

            m = __dirdev()
        except Exception as e:
            log.error(e)
        finally:
            return m

    @func_details
    def get_device_files(self, device_name='flash', sub_dir='', file_filter='.*?', attrib_flags='-ld', mode='BTLDR'):
        """ Get Device Files (via rommon/bootloader)
        Get device files (or dirs) only from the sub directory path given.
        Apply file attribs and regex patterns as filters.

        Sample output to process is given below:
            switch: dir flash:

            Sample #1 BTLDR
            ---------
            0   9932      -rw-     17-S48P3-02.txt
            0   1605693   -rw-     strutt_00_22.hex
            0   25166     -rw-     app_data.srec
            0   381758    -rw-     app_flash.bin
            0   44713896  -rw-     bzImage.110116.SSA
            0   9932      -rw-     17-S24P3-02.txt
            0   84781540  -rw-     stardust2016Nov15
            0   16777216  -rw-     20161116_cat3k4k_x86_RM.bin
            0   45164424  -rw-     bzImage.111616.SSA
            0   16777216  -rw-     btldr.bin
            0   16777216  -rw-     20161207_cat3k4k_x86_RM.bin

            Sample #2 BTLDR
            ---------
            Size       Attributes Name
             - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            9932         -rw-     17-S48P3-02.txt
            85221540     -rw-     stardust2017Feb21
            46271080     -rw-     bzImage.030217.SSA
            16777216     -rw-     20170308_cat3k4k_x86_RM_SB_REL.bin.SPA
            2097152      -rw-     strutt_01_09a_02212017_SB_prodkey_hmac.hex
            381758       -rw-     app_flash.bin
            25166        -rw-     app_data.srec
            85295780     -rw-     stardust2017Mar29
            86019140     -rw-     stardust2017Jul31
             - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

            Sample #3 STARDUST
            ---------
             131075 -rwx   85221540  stardust2017Feb21
            131074 -rwx       9932  17-S48P3-02.txt
            131078 -rwx    2097152  strutt_01_09a_02212017_SB_prodkey_hmac.hex
            131081 -rwx   85295780  stardust2017Mar29
            131080 -rwx      25166  app_data.srec
            131073 drwx        0  .
            131082 -rwx   86019140  stardust2017Jul31
            131076 -rwx   46271080  bzImage.030217.SSA
            131079 -rwx     381758  app_flash.bin
                 2 drwx        0  ..
            131077 -rwx   16777216  20170308_cat3k4k_x86_RM_SB_REL.bin.SPA

        :param device_name: (str) Device to operate on.
        :param sub_dir: (str) Sub directory path to look in.
        :param file_filter: (str) Look only for files matching the regex filter.
        :param attrib_flags: (str)  Use "d", "l', and "-" for dir, link, and file. (Default is get everything.)
        :param mode: BTLDR or STARDUST (because NSB & SB have different requirements)
        :return m: (list) File (and/or) subdir names per the location and filter
        """
        m = list()

        # Set pattern and command based on mode
        attrib_filter = '[{0}][-rwx]'.format(attrib_flags) + '{3}'
        if mode == 'BTLDR':
            pattern = r".*?[ \t]+{0}[ \t]+({1})[\r\n]+".format(attrib_filter, file_filter)
            # default pattern is '.*?[ \\t]+[-ld][-rwx]{3}[ \\t]+(.*?)[\\r\\n]+'
            cmd = 'dir {0}:{1}\r'.format(device_name, sub_dir)
        elif mode == 'STARDUST':
            pattern = r"[ \t]*[0-9]+[ \t]+{1}[ \t]+[0-9]+[ \t]+({0})[\r\n]+".format(file_filter, attrib_filter)
            cmd = 'dir {0}\r'.format(sub_dir)
        else:
            log.error("Unknown mode; cannot get device files.")
            return m

        # Perform action
        try:

            @func_retry(max_attempts=1)
            def __dir():
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send(cmd, expectphrase=self._uut_prompt_map[mode], timeout=30, regex=True)
                time.sleep(self.RECBUF_TIME)
                p = re.compile(pattern)
                return p.findall(self._uut_conn.recbuf)

            log.debug("Cmd={0}".format(cmd))
            m = __dir()
            if not m:
                log.debug("No files found that match the criteria.")
                return m
            # Remove relative dir names (if in the list)
            i = 0
            while i < len(m):
                if m[i] == '.' or m[i] == '..':
                    m.pop(i)
                else:
                    i += 1
            # Do a reverse sort to put "newer" files first based on lexigraphical sort of datestamp in the filename.
            m.sort(reverse=True)
            log.debug("Filtered and sorted files = {0}".format(m))
        except apexceptions.TimeoutException as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return m

    @func_details
    def set_params(self, setparams, **kwargs):
        """ Set Params
        Set flash parameters for vb: block ONLY.
        A verification step is done afterwards.
        The "pb:" block is located in the TLV space within the ACT2 chip.
        The TLV space can be read from rommon but it is NOT writable via rommon due to security.
        An additional copy of the tlv: space will be put in vb: for convenience.

        :param setparams: Params and values to set (traditional form)
        :param kwargs:
                 reset_required:    (bool) whether to reset bootloader after operation, default False.
                 restore_ro:        (bool) read only protect set on vb:
        :return ret: (bool) True if all values to set were successfully set.
        """
        reset_required = kwargs.get('reset_required', True)
        restore_ro = kwargs.get('restore_ro', False)
        force = kwargs.get('force')

        ret = True
        try:
            # Get initial settings (this will include any TLV data!)
            fullparams = self.get_params()

            time.sleep(1.0)
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=20, regex=True)
            time.sleep(1.0)

            # Set or update the params
            log.debug("SETTING Gen3 Rommon Params...")
            for key in setparams:
                if key in fullparams:
                    if setparams[key]:
                        if setparams[key] != fullparams[key] or force:
                            # Change the parameter
                            self._mac_special(key, setparams, fullparams)
                            self._uut_conn.send('set {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                               expectphrase=self._uut_prompt, timeout=30, regex=True)
                            log.info("{0} = {1}  (set changed)".format(key, setparams[key]))
                        else:
                            # No change necessary
                            log.info("{0} = {1}".format(key, setparams[key]))
                    else:
                        # Empty or null value will be ignored.
                        log.info("{0} is empty; not allowed when setting. Use 'unset' instead.".format(key))
                else:
                    if setparams[key]:
                        # Create a new parameter
                        self._uut_conn.send('set {0} {1}\r'.format(key, setparams[key] if ' ' not in setparams[key] else '"{0}"'.format(setparams[key])),
                                           expectphrase=self._uut_prompt, timeout=30, regex=True)
                        log.info("{0} = {1}  (set new)".format(key, setparams[key]))
                    else:
                        log.debug("{0} is empty & new, ignore it.".format(key))
            self._fresh_read = False

            # Now verify that the params were actually set
            time.sleep(1.0)
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=20, regex=True)
            time.sleep(1.0)
            if reset_required:
                log.debug("Reset is required...")
                self._uut_conn.send('reset\r', expectphrase='reset', timeout=20, regex=True)  # 'reset? [y]'
                self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                log.debug("Waiting for boot...")
                self._mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')

            fullparams = self.get_params()
            for key in setparams:
                if key in fullparams:
                    if setparams[key] and setparams[key] != fullparams[key]:
                        # Invalid; something went wrong during the set process.
                        log.warning("{0} set = '{1}'  found = '{2}'".format(key, setparams[key], fullparams[key]))
                        ret = False
                else:
                    if setparams[key]:
                        # Invalid, the item is missing and is not ignored.
                        log.warning("{0} was NOT found.".format(key))
                        ret = False

        except aplib.apexceptions.ResultFailure as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def unset_params(self, unset_params, **kwargs):
        """ Unset Params
        Unset flash parameters for ALL blocks (parameter and variable).
        This method only operates with vb:, not tlv:, so do not verify after unset, because tlv: keys stay after unset.

        :param unset_params:        (list) Params to unset.
        :param kwargs:
                 reset_required:    (bool) whether to reset bootloader after operation, default False.
                 restore_ro:        (bool) whether to restore read-only, default False, not used for GEN3, only for compatibility.
        :return ret:                (bool) True if all values to set were successfully set.
        """
        reset_required = kwargs.get('reset_required', False)
        restore_ro = kwargs.get('restore_ro', False)
        all_params = kwargs.get('all_params')

        ret = True
        try:
            # Get initial settings
            fullparams = self.get_params()

            time.sleep(1.0)
            self._uut_conn.send('\r', expectphrase=self._uut_prompt, timeout=20, regex=True)

            # Unset the params
            if all_params:
                self._uut_conn.send('unset --all\r', expectphrase='will be cleared', timeout=20, regex=True)
                self._uut_conn.send('y\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
                log.info("Unset ALL params.")
            else:
                log.debug("UNSETTING Rommon Params...")
                for key in unset_params:
                    if key in fullparams:
                        self._uut_conn.send('unset {0}\r'.format(key), expectphrase=self._uut_prompt, timeout=20, regex=True)
                        log.info("Unset param {0}".format(key))
            self._fresh_read = False

            # reset rommon if it is required
            if reset_required:
                log.debug("Reset is required...")
                self._uut_conn.send('reset\r', expectphrase='reset', timeout=20, regex=True)
                self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                log.debug("Waiting for boot...")
                self._mode_mgr.wait_for_boot(boot_mode=['BTLDR'], boot_msg='(?:Booting)|(?:Initializing)')

        except aplib.apexceptions.ResultFailure as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def ping(self, ip):
        """ Ping from Bootloader

        Partial output:

        Packet(s): Sent       Received   Loss       | RTT: Minimum    Maximum    Average
                   4          4          0        % |      <0         ~4         ~1

        :param ip: (str) IP Addr
        :return (bool): True if ping was good.
        """

        @func_retry
        def __ping():
            ret = False
            self._clear_recbuf(self._uut_conn)
            self._uut_conn.send('ping {0}\r'.format(ip), expectphrase=self._uut_prompt, timeout=120, regex=True)
            time.sleep(self.RECBUF_TIME)
            m = parse.search(' {sent:0d} {recv:1d} {loss:2d} ', self._uut_conn.recbuf)
            if m:
                log.debug("Ping packets: sent={0}, recv={1}".format(m['sent'], m['recv']))
                if m['sent'] == m['recv']:
                    log.debug("'Ping: {0}' is alive!".format(ip))
                    ret = True
                else:
                    log.debug("Ping: Network connection or setup problem with {0}".format(ip))
            else:
                log.debug("Ping: Problem with response. Check UUT. Check output and parse.")
            return ret

        ret = False
        try:
            if ip:
                ret = __ping()
            else:
                log.warning("IP Addr is required to ping!")
        except apexceptions.TimeoutException as e:
            log.error(e)
        except Exception as e:
            log.error(e)
        finally:
            return ret

    @func_details
    def check_version(self, version=None):
        """ Check Version of Bootloader/Rommon

        Example:
        switch: version

        System Bootstrap, Version 1.17, DEVELOPMENT SOFTWARE
        Copyright (c) 1994-2016  by cisco Systems, Inc.
        Compiled Wed 12/07/2016 12:02:35.31 by sapitcha

        !!! NON-Secure Boot ROMMON Image. For INTERNAL USE ONLY !!!

        Current image running:
        Last reset cause: UNKNOWN
        Last RstCode: 0x00000000
         platform with 4194304 Kbytes of main memory

        Note: Expects to be in bootloader mode already!

        :param (dict) version: Target version & date to check, e.g. {'ver': '1.17', 'date': '12/07/2016 12:02:35.31'}
        :return: True if match or target version is null
        """
        if version and not isinstance(version, dict):
            log.error("Target version for checking must be in dict form.")
            return False

        # Determine if golden present
        golden_present = True if 'BTLDRG' in self._uut_prompt_map else False

        # Get version for all available types
        for name, mode in self.btldr_types:
            if not self._mode_mgr.goto_mode(mode):
                log.error("Cannot goto correct mode {0} for {1} version check.".format(name, mode))
                return False
            m = self._get_version()
            if m:
                self._version[name]['ver'] = m['ver']
                self._version[name]['date'] = m['date']
            else:
                log.warning("Version data ({0}) not retrieved!".format(name))

        if golden_present:
            if not self._mode_mgr.goto_mode('BTLDR'):
                log.error("Could not return to BTLDR mode.")
                return False

        # Sanity check
        if not version:
            log.debug("Target version is null; skip the check.")
            return True
        if not self._version['primary']['ver']:
            log.error("Unable to get current version of bootloader/rommon.")
            log.error("Check the UUT.  Check the parse.")
            return False
        if not self._version['golden']['ver'] and golden_present:
            log.error("Unable to get current golden version of bootloader/rommon.")
            log.error("Check the UUT.  Check the parse.")
            return False

        # Now check for a match
        ret = True
        for name, _ in self.btldr_types:
            if self._version[name]['ver'] == version['ver'] and self._version[name]['date'] == version['date']:
                log.info("Revision {0} match.".format(name))
                self._version[name]['status'] = True
            elif not version:
                log.warning("No version data to check against.")
                log.warning("Image {0} revision check will be ignored.".format(name))
            elif self._version[name]['ver'] > version['ver']:
                log.warning("Current {0} version {1} is NEWER than expected version {2}.".format(name, self._version[name]['ver'], version['ver']))
                self._version[name]['status'] = True
            else:
                log.warning("Revision {0} MISMATCH!".format(name))
                self._version[name]['status'] = False
                ret = False

        # Display
        log.info("-" * 50)
        log.info("Bootloader Current Primary Ver: {0}".format(self._version['primary']))
        log.info("Bootloader Current Golden Ver : {0}".format(self._version['golden'])) if golden_present else None
        log.info("Bootloader Target Ver         : {0}".format(version))

        return ret

    @func_details
    def upgrade(self, image, **kwargs):
        """ Upgrade
        Two types of upgrade methods exist for some GEN3 products: Non-secure boot (NSB) and secure boot (SB).
        WARNING: NSB was used mainly for the HW development phase and should NOT be used for production!

        SB Upgrade: First command attempt MUST unlock SPI; It remains unlocked until power-cycle.
        ****************************************************************
        * !!! CPU Reset is required to unlock the SPI flash region !!! *
        *        Please re-run the command after the reset             *
        ****************************************************************
        Are you sure to continue to reset CPU now? [y/n]

        SB Upgrade: Actual prompt (after SPI unlock & reboot):
        *************************************************************
        * !!! WARNING: Incorrect operation could corrupt system !!! *
        *************************************************************
        Are you sure to continue? [y/n]y

        :param image: Filename with which to upgrade
        :param: kwargs
                 (str) image_type: NSB or SB (default)
                 (str) device_name: device designation
                 (str) params: Params used in the upgrade command
                 (str) device_src_dir: Location of file on device (e.g. '/')
                 (str) network_src_url: URL of file on the network (e.g. 'tftp://10.1.1.1/biosimages')
        :return:
        """

        def __upgrade_sb(image, params='', device_src_dir=None):
            """ SB Upgrade the BIOS (INTERNAL ONLY)
            For GEN3 the bootloader/rommon is SB upgraded from diags ONLY!
            Notes:
            Initially before SB is introduced, you can either use stardust CLI or biosupg util to program the BIOS flash.
            But after SB is introduced, the platform specific FPGA operation is added regarding upgrading the BIOS SPI
            flashes. There are multiple platforms sharing the same kernel base and that kernel util doesn't have platform
            dependent operations. It is highly recommend users use one place which is stardust to do all the flash upgrading.
            Unless the user knows what they are doing using the kernel util, that util can only program the current
            booting flash non-ME regions.
            :param image:
            :param params:
            :param device_name:
            :param device_src_dir:
            :param network_src_url:
            """
            log.info("*** Perform SB Upgrade! ***")

            log.debug("Params = {0}".format(params))
            if not device_src_dir:
                device_src_dir = ''

            # Check for image presence.
            if image not in self.get_device_files(sub_dir=device_src_dir, file_filter='.*?'):
                log.error("The upgrade file ({0}) was not found on the device.".format(image))
                log.error("Be sure to load the appropriate image before running this upgrade.")
                return False

            # Execute the upgrade
            log.info("Preparing the upgrade.")
            log.warning("DO NOT power off!")
            log.info("Bootloader types for upgrade: {0}".format(self.btldr_types))
            log.info("Version data = {0}".format(self._version))
            original_mode = self._mode_mgr.current_mode

            def __upgrade_sb_worker():
                log.info("Bootloader/rommon upgrade: {0}...".format(name))
                # Get to STARDUST
                if not self._mode_mgr.goto_mode('STARDUST'):
                    log.error("Problem trying to change mode.")
                    log.error("Cannot perform upgrade.")
                    return False
                # First command
                self._uut_conn.send('SPIBootFlashProg {0} {1} -f:{2}\r'.format(image, params, name), expectphrase='[y/n]', timeout=30)
                if "CPU Reset is required to unlock" in self._uut_conn.recbuf:
                    log.info("Phase 1: Bootloader/rommon SPI unlock.")
                    self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                    self._mode_mgr.wait_for_boot('BTLDR')
                    log.info("Phase 1b: Go back to STARDUST.")
                    if not self._mode_mgr.goto_mode('STARDUST'):
                        log.error("Problem trying to change mode.")
                        log.error("Cannot perform upgrade.")
                        return False
                    # Second command
                    self._uut_conn.send('SPIBootFlashProg {0} {1} -f:{2}\r'.format(image, params, name), expectphrase='[y/n]', timeout=30)
                else:
                    log.debug("CPU reset for SPI unlock already done.")
                log.info("Phase 2: Bootloader/rommon image program.")
                self._uut_conn.send('y\r', expectphrase='.*', timeout=60, regex=True)
                log.debug("Bootloader/rommon {0} waiting for done...".format(name))
                self._uut_conn.waitfor('Done', timeout=400, idle_timeout=120, regex=True)
                self._uut_conn.send('\r', expectphrase=self._uut_prompt_map['STARDUST'], timeout=60, regex=True)
                log.debug("Bootloader/rommon {0} DONE!".format(name))
                return

            for name, _ in self.btldr_types:
                if aplib.need_to_abort():
                    log.warning("ABORTING...")
                    return False
                if self._version.get(name, {}).get('status', None) is False or force:
                    __upgrade_sb_worker()
                elif self._version.get(name, {}).get('status', None) is True:
                    log.info("Bootloader/rommon upgrade NOT needed: {0}.".format(name))
                else:
                    log.warning("Bootloader/rommon {0} version status is unknown.".format(name))
                    ans = aplib.ask_question("Bootloader/rommon {0} version status is unknown.  Upgrade anyway?".format(name), answers=['YES', 'NO'])
                    if ans == 'YES':
                        __upgrade_sb_worker()

            # Restore
            log.debug("All bootloader/rommon types have been processed.")
            if original_mode != 'STARDUST' and return_orig_mode:
                log.info("Returning to the original mode (this was explicitly requested)...")
                self._mode_mgr.goto_mode(original_mode)

            return True

        def __upgrade_nsb(image, params=None, device_src_dir=None, network_src_url=None):
            """ NSB Upgrade the BIOS (INTERNAL ONLY)
            For GEN3 the bootloader/rommon is NSB upgraded from Linux via a utility.
            ***WARNING*** This was used for early development & should NOT be used in production!
            :param (str) image: File name
            :param (str) params: Biosupg params
            :param (str) device_src_dir: Location of file on device (e.g. '/mnt/flash3/user'
            :param (str) network_src_url: URL of file on the network (e.g. 'tftp://10.1.1.1/biosimages')
            :return:
            """

            log.info("*** Perform NSB Upgrade! ***")

            bios_utility = '/proj/util/biosupg'

            if not params:
                log.warning("Setting default upgrade params.")
                # old : params = '0x800000 0x800000'  # Partial flash space upgrade
                params = '-s:0x000000 -b:0x1000000'  # Full flash space upgrade

            # Get to LINUX
            original_mode = self._mode_mgr.current_mode
            if original_mode != 'LINUX':
                if not self._mode_mgr.goto_mode('LINUX'):
                    log.error("Problem trying to change mode.")
                    log.error("Cannot perform upgrade.")
                    return False

            # Check for the utility
            cmd = 'ls --color=never {0}\r'.format(bios_utility)
            self._uut_conn.send(cmd, expectphrase=self._uut_prompt_map['LINUX'], timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'No such file' in self._uut_conn.recbuf:
                log.error("The upgrade utility is missing.")
                log.error("Please check the linux installation.")
                return False
            else:
                log.debug("Upgrade utility available: '{0}".format(bios_utility))

            # Get prime flash dir
            if not device_src_dir:
                log.warning("Device image location was NOT explicitly provided; using default.")
                device_src_dir = self._ud.get_flash_mapped_dir()

            # Check for image presence (load from network if required and available)
            full_path_image = os.path.join(device_src_dir, image)
            log.info("Device image = {0}".format(full_path_image))
            cmd = 'ls --color=never {0}\r'.format(full_path_image, )
            self._uut_conn.send(cmd, expectphrase=self._uut_prompt_map['LINUX'], timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            if 'No such file' in self._uut_conn.recbuf:
                log.warning("The upgrade file ({0}) was not found on the device.".format(full_path_image))
                if not network_src_url:
                    log.warning("A network alternative was NOT given for the image.")
                    log.warning("Assume the default URL.")
                    network_src_url = 'tftp://{0}/{1}'.format(self._ud.uut_config['server_ip'], '')
                log.debug("Network alternative = {0}".format(network_src_url))
                m = re.search('(?P<protocol>[a-zA-Z0-9]+)://(?P<server_ip>[0-9\.]+)[/]?(?P<sudir>.*)', network_src_url)
                protocol, server_ip, subdir = (m.groups()[0], m.groups()[1], m.groups()[2]) if m else ('', '', '')
                if protocol == 'tftp':
                    log.debug("Attempting tftp upload...")
                    server_ip = self._ud.uut_config['server_ip'] if not server_ip else server_ip
                    # Attempt to retrieve an image
                    if not self._linux.transfer_tftp_files(src_files=os.path.join(subdir, image),
                                                           dst_files=full_path_image,
                                                           direction='get',
                                                           server_ip=server_ip,
                                                           netmask=self._ud.uut_config['netmask'],
                                                           ip=self._ud.uut_config['uut_ip'],
                                                           force=True):
                        log.error("The upgrade file was NOT on the network")
                        return False
                    else:
                        log.debug("Transfer GOOD; image file ready.")
                else:
                    log.error("No recognized network protocol.")
                    return False

            # Execute the upgrade
            log.info("Performing the upgrade.")
            log.warning("DO NOT power off!")
            cmd = '{0} {1} {2}\r'.format(bios_utility, full_path_image, params)
            self._clear_recbuf(self._uut_conn)
            self._uut_conn.send(cmd, expectphrase='[y/n]', timeout=30)
            self._uut_conn.send('y\r', expectphrase='%', timeout=30)

            # Loop to deal with the console output status updates
            loop_count = 0
            ret = False
            active_pattern = '(?:[0-9]+%)|(?:Done)'
            old_status = ''
            while not ret and loop_count < 1000:
                self._uut_conn.waitfor(active_pattern, timeout=30, regex=True)
                new_status = self._uut_conn.recbuf.splitlines()[-1:][0]
                if new_status != old_status:
                    # A change in the output status occurred; do something.
                    loop_count += 1
                    if re.search('(?:[0-9]+%)', self._uut_conn.recbuf):
                        log.debug("BTLDR Programming ({0})  {1} ...".format(loop_count, new_status))
                        old_status = new_status
                    if re.search('Done', self._uut_conn.recbuf):
                        log.debug('Done programming!')
                        ret = True
                time.sleep(1.0)

            if not ret:
                log.error("BTLDR/ROMMON Programming did not get a completion signal.")

            # Restore
            if original_mode != 'LINUX':
                self._mode_mgr.goto_mode(original_mode)

            return ret

        # Input
        if not isinstance(image, str):
            log.error("The image parameter must be a str type.")
            return False
        image_type = kwargs.get('image_type', None)
        params = kwargs.get('params', None)
        device_src_dir = kwargs.get('device_src_dir', '')
        network_src_url = kwargs.get('network_src_url', None)
        force = kwargs.get('force', False)
        return_orig_mode = kwargs.get('return_orig_mode', False)

        if not image_type:
            image_type = 'SB'
            log.debug("Defaulting image type upgrade to '{0}'.".format(image_type))

        if image_type == 'SB':
            ret = __upgrade_sb(image=image,
                               params=params,
                               device_src_dir=device_src_dir)
        elif image_type == 'NSB':
            ret = __upgrade_nsb(image=image,
                                params=params,
                                device_src_dir=device_src_dir,
                                network_src_url=network_src_url)
        else:
            log.error("Bootloader/rommon type='{0}' is unknown.".format(image_type))
            ret = False

        return ret

    @func_details
    def set_uut_network_params(self, mac=None, ip=None, netmask=None, server_ip=None, sernum=None, tftp_ip=None):
        """ Set Network Params (WRAPPER)
        :param mac:
        :param ip:
        :param netmask:
        :param server_ip:
        :param sernum:
        :param tftp_ip:
        :return:
        """
        if not tftp_ip:
            tftp_ip = server_ip
            log.debug("Defaulting the TFT Server = {0}".format(tftp_ip))
        return self._select_set_uut_network_params(mac=mac,
                                                   ip=ip,
                                                   netmask=netmask,
                                                   server_ip=server_ip,
                                                   sernum=sernum,
                                                   tftp_ip=tftp_ip,
                                                   net_param_names='Gen3')

    @func_details
    def check_network_params(self, ip, netmask, server_ip, tftp_ip=None):
        """ Check Network Params (WRAPPER)
        :param ip:
        :param netmask:
        :param server_ip:
        :param tftp_ip:
        :return:
        """
        if not tftp_ip:
            tftp_ip = server_ip
            log.debug("Defaulting the TFT Server = {0}".format(tftp_ip))
        return self._select_check_network_params(ip, netmask, server_ip, tftp_ip=tftp_ip, net_param_names='Gen3')

    # -----------------------------------------------------------------------
    # INTERNAL Functions
    def _get_version(self):
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('version\r', expectphrase=self._uut_prompt, timeout=30, regex=True)
        time.sleep(self.RECBUF_TIME)
        log.debug("Checking rommon version...")
        m = parse.search('System Bootstrap, Version {ver:0},{x1:1}Compiled {dow:2} {date:3} {time:4} by', self._uut_conn.recbuf)
        if m:
            return m.named
        else:
            return None


class RommonC9300L(RommonC9300):
    """C9300L Rommon Driver
    This class is product family specific.
    Families included: Franklin
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC9300L, self).__init__(mode_mgr, ud, **kwargs)
        return


# ----------------------------------------------------------------------------------------------------------------------
# C4K & C9400 Family
class RommonC4000(Rommon):
    """C4000 Rommon Driver
    This class is product family specific.
    Families included: K10, K5, Galaxy
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC4000, self).__init__(mode_mgr, ud, **kwargs)
        return


class RommonC9400(RommonGen3):
    """C9400 Rommon Driver
    This class is product family specific.
    Families included: Macallen
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC9400, self).__init__(mode_mgr, ud, **kwargs)
        return

    def upgrade(self, image, **kwargs):

        if image == 'LINUX_BATCH':
            log.info("Running Linux batch upgrade for Rommon & FPGA...")
            rev = self._ud.uut_config.get('MOTHERBOARD_REVISION_NUM', None)
            if rev is None:
                # Should always have a rev
                log.error("Could not get the Sup motherboard revision.")
                log.error("Cannot determine which linux batch to run; failing this unit.")
                return False
            elif rev < 'A0':
                # Do PROTO
                script = self._ud.uut_config.get('btldr', {}).get('proto_image', None)
                pass
            else:
                # Do PRODUCTION
                script = self._ud.uut_config.get('btldr', {}).get('production_image', None)
                pass
        else:
            log.info("Performing Rommon upgrade...")
            pass


# ----------------------------------------------------------------------------------------------------------------------
# C9500 Family
class RommonC9500(RommonC9300):
    """C9500 Rommon Driver
    This class is product family specific.
    Families included: Adelphi
    """

    def __init__(self, mode_mgr, ud, **kwargs):
        super(RommonC9500, self).__init__(mode_mgr, ud, **kwargs)
        return
