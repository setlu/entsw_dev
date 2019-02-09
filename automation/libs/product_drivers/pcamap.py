""" PCAMAP Class Driver Module
========================================================================================================================

This module provides a set of classes for manipulating the PCAMAP.
The driver type is identified by class name.
All classes are REQUIRED to use the PCAMap abstract base class for interface definition.

Product families supported:
    1. Cisco Catalyst 2900 series (WS-C2900 & C9200)
    2. Cisco Catalyst 3800/3600 series (WS-C3850/C3650 & C9300, C9300L)
    3. Cisco Catalyst 4000 series (WS-C4000 & C9400)

"""
# ------
import sys
import re
import logging
import time
from collections import OrderedDict

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Lib
# ------
from ..bases.pcamap_base import PCAMapBase
from ..utils.common_utils import func_details
from ..utils.common_utils import convert_mac
from ..utils.common_utils import convert_eco_deviation
from ..utils.common_utils import apollo_step
from ..utils.common_utils import ask_dict_question
from ..utils.common_utils import print_large_dict
from ..utils.common_utils import diff_dict


__title__ = "Catalyst PCAMAP Driver Module"
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
class PcamapException(Exception):
    """Raise for specific Pcamap exceptions."""
    pass


# ======================================================================================================================
# CLASS DRIVERS
#
# ----------------------------------------------------------------------------------------------------------------------
# Generic
class Pcamap(PCAMapBase):
    """ Pcamap Gen3
    Manages all PCAMAP activity for the Generation 2 product families.
    """

    RECBUF_TIME = 3.0
    RECBUF_CLEAR_TIME = 1.0
    USE_CLEAR_RECBUF = False
    MEMORY_TYPES = ['tlv', 'vb']

    def __init__(self, mode_mgr, ud, **kwargs):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._check_dependencies()
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt_map = self._mode_mgr.uut_prompt_map
        self._uut_prompt = self._mode_mgr.current_prompt_pattern if self._mode_mgr.current_prompt_pattern else '> '
        self._rommon = kwargs.get('rommon', None)
        self._peripheral = kwargs.get('peripheral', None)
        sysinit_default = self._peripheral._sysinit if hasattr(self._peripheral, '_sysinit') else None
        self._sysinit = kwargs.get('sysinit', sysinit_default)
        self._callback = None
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    @property
    def version(self):
        return self.version

    # ------------------------------------------------------------------------------------------------------------------
    # USER STEPS
    #
    @apollo_step
    def read_uut(self, **kwargs):
        """ Read to uut_config
        [flash:] --> [uut_config]
        :param (**dict) **kwargs:
               (bool) smart_update: True = Ignore invalid values and null values that were read from the UUT.
               (bool) allow_empty: True = Do not fail if the params are empty (fresh UUT).
        :return:
        """
        device_instance = kwargs.get('device_instance', self._ud.device_instance)
        smart_update = kwargs.get('smart_update', True)
        allow_empty = kwargs.get('allow_empty', True)
        menu = kwargs.get('menu', False)

        log.debug("Read ---> Update in uut_config")

        if device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            device_instance = None
            while device_instance is None or not str(device_instance).isdigit():
                device_instance = aplib.ask_question("Device instance [int]:")
        device_instance = int(device_instance)

        params = self.read(device_instance=device_instance)

        if not params:
            if allow_empty:
                log.warning("No params read.")
                log.warning("The flash may be empty. (Allow this condition.)")
                return aplib.PASS
            else:
                log.error("No params read.")
                errmsg = "The flash may be empty or has a read problem."
                log.error(errmsg)
                return aplib.FAIL, errmsg

        # Update
        if 0 < device_instance < 1000:
            log.debug("Peripheral data update...")
            if 'pcamaps' not in self._ud.uut_config:
                self._ud.uut_config['pcamaps'] = {}
            pcamaps = self._ud.uut_config.get('pcamaps')
            pcamaps.update({str(device_instance): params})
            # Params for peripherals are stored in uut_config['pcamaps']
            self._ud.uut_config['pcamaps'].update(pcamaps)
            result = True if self._ud.uut_config['pcamaps'].get(str(device_instance)) == params else False
            smart_update = None
        else:
            log.debug("Standard data update...")
            result = self._ud.uut_config.smart_update(params) if smart_update else self._ud.uut_config.update(params)

        # Check the update result
        if not result:
            errmsg = "The uut_config update (smart={0}) failed.".format(smart_update)
            log.error(errmsg)
            return aplib.FAIL, errmsg

        return aplib.PASS

    @apollo_step
    def write_uut(self, **kwargs):
        """ Write from uut_config
        [uut_config or params] --> [flash:]
        :param (**dict) kwargs:
               (dict) params: Key/value pairs to write in lieu of uut_config (the uut_config will also be updated)
               (list) keys: Keys to filter uut_config ("selective write")
               (str) memory_type: 'vb', 'tlv', 'both'
               (bool) tlv_reset: True = Resets ALL tvl values to the default setting.
                                 False = Just updates changes in values.
        :return:
        """

        # Input
        device_instance = kwargs.get('device_instance', self._ud.device_instance)
        params = kwargs.get('params', None)
        keys = kwargs.get('keys', None)
        memory_type = kwargs.get('memory_type', None)
        tlv_reset = kwargs.get('tlv_reset', True)
        menu = kwargs.get('menu', False)

        # Sanity check
        if keys and params:
            log.warning("Please use only one at a time when writing to the UUT: 'params' or 'keys'.")
            return aplib.SKIPPED
        if memory_type.lower() not in self.MEMORY_TYPES:
            log.warning("Please use one of these memory types for writing: {0}".format(self.MEMORY_TYPES))
            return aplib.SKIPPED

        label = 'uut_config' if not params else 'params'
        label = 'uut_config filtered' if keys else label
        log.debug("Read [{0}] --> Write [flash:]".format(label))

        if device_instance is None or menu:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while device_instance is None or not str(device_instance).isdigit():
                device_instance = aplib.ask_question("Device instance [int]:")
        device_instance = int(device_instance)

        if menu:
            source = aplib.ask_question("Data source:", answers=['uut_config', 'uut_config filtered', 'params'])
            if source == 'params':
                params = ask_dict_question("Enter params to write:")
                tlv_reset = False
            elif source == 'uut_config filtered':
                ans = aplib.ask_question("Enter keys to filter uut_config (csv):")
                keys = [k.strip(' ') for k in ans.split(',')]
                tlv_reset = False
            else:
                params = self._ud.get_flash_params()

        if params:
            log.debug("Target data source = params.")
            target_data = params
        elif keys:
            log.debug("Target data source = keys filter of uut_config.")
            target_data = self._ud.get_filtered_params(keys)
        else:
            log.debug("Target data source = uut_config.")
            target_data = self._ud.get_flash_params()

        log.debug("Prelim data = {0}".format(target_data))

        if memory_type == 'vb':
            log.debug("Memory Type = vb")
            tlv_only, vb_only = False, True
            vb_filter = self._ud.uut_config.get('flash_vb_params', [])
            log.debug("Filter flash_vb_params = {0}".format(vb_filter))
            if vb_filter:
                filtered_data = {k: target_data[k] for k in vb_filter if target_data.get(k, None)}
                target_data = filtered_data
        else:
            log.debug("Memory Type = tlv")
            tlv_only, vb_only = True, False

        # Show params to write
        td_len = len(target_data.keys())
        print_large_dict(target_data, title="PCAMAP to Write (instance={0}  len={1})".format(device_instance, td_len),
                         max_display_length=160, sort=True)

        if td_len == 0:
            log.warning("Nothing to write!")
            return aplib.PASS

        # Perform the action
        result = self.write(device_instance, target_data, tlv_only=tlv_only, vb_only=vb_only, tlv_reset=tlv_reset)

        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def write_uut_peripheral(self, **kwargs):
        """ Write PCAMAP data from uut_config to peripherals (Uplink, Data stack cable and cable module, etc)
        [uut_config or params] --> SCCWriteQuackFruEeprom

        :param (**dict) kwargs:
               (dict) params: Key/value pairs to write in lieu of uut_config (the uut_config will also be updated)
               (list) keys: Keys to filter uut_config ("selective write")
        :return:                aplib.PASS/FAIL
        """

        # Input
        device_instance = kwargs.get('device_instance', self._ud.device_instance)
        params = kwargs.get('params')
        keys = kwargs.get('keys')

        # Sanity check
        if keys and params:
            log.warning("Please use only one at a time when writing to the UUT: 'params' or 'keys'.")
            return aplib.FAIL
        if device_instance is None:
            log.error("Must provide a device instance number.")
            return aplib.FAIL
        if int(device_instance) == 0 or int(device_instance) > 5:
            log.error('Only operates on device_instance [1-5]')
            return aplib.FAIL

        pcamaps = self._ud.uut_config.get('pcamaps', {})
        if params:
            log.debug("Target data source = params.")
            target_data = params
        elif keys:
            log.debug("Target data source = keys filter {0} of uut_config.".format(keys))
            target_data = pcamaps.get(str(device_instance))
            target_data = {k: v for k, v in target_data.items() if k in keys}
        else:
            log.debug("Target data source = uut_config.")
            target_data = pcamaps.get(str(device_instance), {})

        log.debug("Target data = {0}".format(target_data))

        # Show params to write
        td_len = len(target_data.keys())
        print_large_dict(target_data, title="PCAMAP to Write (instance={0}  len={1})".format(device_instance, td_len),
                         max_display_length=160, sort=True)

        if td_len == 0:
            log.warning("Nothing to write!")
            return aplib.PASS

        # Perform the action
        result = self.write(device_instance, target_data)

        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def diff_flash_vs_uut_config(self, **kwargs):
        """ Diff Flash (PCAMAP) vs. uut_config
        :param kwargs:
        :return:
        """
        device_instance = kwargs.get('device_instance', self._ud.device_instance)

        if device_instance is None:
            # Get the device ID to program.
            # Do this first to satisfy unittest blind prompting.
            while device_instance is None or not str(device_instance).isdigit():
                device_instance = aplib.ask_question("Device instance [int]:")
        device_instance = int(device_instance)

        flash_params = self.read(device_instance=device_instance)
        uut_config_params = self._ud.get_flash_params()

        # Display "before & after" results of the PCAMAP loading.
        kw = max([len(k) for k in flash_params.keys()] + [len(k) for k in uut_config_params.keys()])
        vw = max([len(v) for v in flash_params.values()] + [len(v) for v in uut_config_params.values()])

        if False:
            diff_params, keys = diff_dict(uut_config_params, flash_params)
            log.debug("Param changes:")
            fstr = "{0:<" + str(kw) + "}   {1:<" + str(vw) + "}   {2:<" + str(vw) + "}   {3:<10}"
            log.debug(fstr.format('Param', 'In flash', 'In uut_config', 'Status'))
            log.debug(fstr.format('-' * kw, '-' * vw, '-' * vw, '-' * 10))
            for k in sorted(diff_params.keys()):
                log.debug(fstr.format(k, "{}".format(diff_params[k]), "{}".format(uut_config_params.get(k, '')), '*'))
            for k in sorted(keys['match']):
                log.debug(fstr.format(k, "{}".format(flash_params[k]), "{}".format(uut_config_params[k]), '.'))

        diffdicts, keys = diff_dict(flash_params, uut_config_params, full_return=True)

        log.debug("Param changes:")
        fstr = "{0:<" + str(kw) + "}   {1:<" + str(vw) + "}   {2:<" + str(vw) + "}   {3:<10}"
        log.debug(fstr.format('Param', 'In flash', 'In uut_config', 'Status'))
        log.debug(fstr.format('-' * kw, '-' * vw, '-' * vw, '-' * 10))
        for k in sorted(diffdicts['left'].keys()):
            log.debug(fstr.format(k, "{}".format(diffdicts['left'][k]), '-', '<-'))
        for k in sorted(diffdicts['right'].keys()):
            log.debug(fstr.format(k, '-', "{}".format(diffdicts['right'][k]), '->'))
        for k in sorted(diffdicts['delta'].keys()):
            log.debug(fstr.format(k, "{}".format(diffdicts['delta'][k][0]), "{}".format(diffdicts['delta'][k][1]), '*'))
        for k in sorted(diffdicts['match'].keys()):
            log.debug(fstr.format(k, "{}".format(diffdicts['match'][k]), "{}".format(diffdicts['match'][k]), '.'))

        return aplib.PASS

    @apollo_step
    def program_toplevel_pid(self, **kwargs):
        """ Program Top Level PID

        Program uut_config['CFG_MODEL_NUM'] to tlv (default) or vb.
        Note: The "top-level" PID is consider the "CFG_MODEL_NUM" = Customer Configured Model Number.

        :param kwargs:
        :return:
        """
        aplib.set_container_text('PROGRAM TOP LEVEL PID')
        log.info('STEP: Program Top Level PID.')

        # Input processing
        top_level_pid = kwargs.get('top_level_pid', self._ud.uut_config.get('CFG_MODEL_NUM'))
        device_instance = kwargs.get('device_instance', self._ud.device_instance)
        memory_type = kwargs.get('memory_type', 'tlv')

        if not top_level_pid:
            log.warning('No Top level PID is provided')
            return aplib.SKIPPED
        params = {'CFG_MODEL_NUM': top_level_pid}

        ret = self.write_uut(device_instance=device_instance, params=params, memory_type=memory_type, tlv_reset=False)

        return ret

    @apollo_step
    def set_manual_boot(self, **kwargs):
        """ Set Manual Boot (Step)

        This step sets MANUAL_BOOT param in rommon based on kwargs input.
        It takes only 1 input 'manual_boot', if it is True, set MANUAL_BOOT to yes, if it is False, set MANUAL_BOOT to no.

        :param (dict) kwargs:
        :return:
        """
        aplib.set_container_text('SET MANUAL BOOT')
        log.debug("STEP: Set Manual Boot Param in Rommon.")

        # Process input
        manual_boot = kwargs.get('manual_boot', None)
        if manual_boot is not True and manual_boot is not False:
            log.error('Param manual_boot must be True or False, input is {0}'.format(manual_boot))

        set_params = {'MANUAL_BOOT': 'yes'} if manual_boot else {'MANUAL_BOOT': 'no'}

        ret = self._rommon.set_params(setparams=set_params, reset_required=False)

        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def cleanup_rommon_params(self, **kwargs):
        """ Cleanup Rommon/Bootloader Params
        Unset any extra params that should not go to the customer.
        Legacy products must be individually unset in vb.
        Newer products have an "unset --all" + reboot-sync, use the step in class PcamapGen3.

        :param kwargs:
        :return:
        """
        # Process Input.
        params_to_keep = kwargs.get('params_to_keep', self._ud.uut_config.get('rommon_params_to_keep', []))
        reset_required = kwargs.get('reset_required', False)

        # test_area
        test_info = aplib.apdicts.test_info
        area = test_info.test_area

        # 1. Get required items from CMPD
        cmpd_types_dict = self._callback.process.get_cmpd_types_dict_from_manifest()
        cmpd_types = self._callback.process.get_cmpd_types_by_area(cmpd_types_dict, area)

        # 2. Determine items to unset
        fullparams = self._rommon.get_params()
        unset_params = [item for item in fullparams if item not in cmpd_types and item not in params_to_keep]

        log.debug('CMPD Params: {0}'.format(cmpd_types))
        log.debug('Full Params: {0}'.format(fullparams.keys()))
        log.debug('Params to keep: {0}'.format(params_to_keep))
        log.debug('Unset Params: {0}'.format(unset_params))

        # 3. Perform the unset
        # ret = self.write_uut(device_instance=0, setparams=set_params, memory_type='vb')
        ret = self._rommon.unset_params(unset_params=unset_params, reset_required=reset_required)

        return aplib.PASS if ret else aplib.FAIL

    # ------------------------------------------------------------------------------------------------------------------
    # USER METHODS
    #
    @func_details
    def read(self, device_instance, **kwargs):
        params = {}
        original_mode = None
        mode = None

        # Sanity
        if not str(device_instance).isdigit():
            log.error("Device instance MUST be numeric only.  Unable to read params.")
            return params
        device_instance = int(device_instance)

        # Motherboard
        if device_instance == 0:
            mode, original_mode = self._mode(['BTLDR', 'STARDUST', 'IOSE'], do_sysinit=False)
            # Select the command based on mode.
            if mode == 'BTLDR':
                params = self._rommon.get_params()
            elif mode == 'STARDUST':
                cmd = 'flashr'
                pattern = r"[ \t]*([\S]+)[ \t]*=[ \t]*([\S]*)"
                self._clear_recbuf(self._uut_conn)
                self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=20, regex=True)
                time.sleep(self.RECBUF_TIME)  # Allow recbuf time to catchup after send completion: Apollo limitation!
                p = re.compile(pattern)
                m = p.findall(self._uut_conn.recbuf)
                params = dict(m) if m else {}
            elif mode == 'IOSE':
                params = self._ios_get_params()
            else:
                log.warning("Unable to get flash params; appropriate mode is not available.")

        # Peripherals
        elif device_instance > 0:
            mode, original_mode = self._mode('STARDUST')
            params = self._peripheral.read_quack_params(device_instance)

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        return params

    @func_details
    def write(self, device_instance, set_params, **kwargs):
        log.debug("Writing PCAMAP data: {0}".format(set_params))
        result = False
        original_mode = None
        mode = None

        # Sanity
        if not str(device_instance).isdigit():
            log.error("Device instance MUST be numeric only.  Unable to write params.")
            return result
        device_instance = int(device_instance)

        # Motherboard
        if device_instance == 0:
            # Can only write main board params from bootloader
            mode, original_mode = self._mode('BTLDR')
            result = self._rommon.set_params(set_params)

        # Peripherals
        elif 0 < device_instance < 1000:
            # Can only write peripheral params from diags
            mode, original_mode = self._mode('STARDUST')
            result = self._peripheral.write_quack_params(device_instance, set_params)

        elif device_instance >= 1000:
            log.error("There is no provision for this device_instance: {0}".format(device_instance))
            log.error("Please use a more product-specific class.")

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        log.info("WRITE Result = {0}".format(result))
        return result

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNAL Functions
    #
    def _mode(self, target_modes, **kwargs):
        """ Mode
        Go to a specific mode.  If a list of modes is provided then go to the most convenient mode.
        Return both the original mode and the new mode so that a return to the original mode can be done later.
        The prompt is maintained as a convenience.
        :param (list or str) target_modes:
        :return (tuple): new_mode, old_mode
        """
        do_sysinit = kwargs.get('do_sysinit', True)
        new_mode, old_mode = self._mode_mgr.goto_mode_of_least_cost(target_modes)
        if old_mode in ['LINUX'] and new_mode == 'STARDUST' and do_sysinit:
            if self._sysinit:
                log.debug("Ensuring peripherals can be accessed...")
                if not self._sysinit():
                    log.warning("The sysinit could not complete properly!")
                    log.warning("Board access cannot be guaranteed; however, operations will continue.")
            else:
                log.warning("Peripheral access NOT guaranteed since no sysinit function was available.")

        self._uut_prompt = self._mode_mgr.current_prompt_pattern

        return new_mode, old_mode

    def _ios_get_params(self):
        # Note: This is not a comprehensive list.
        params = {}
        cmd = 'show hardware | include Number'
        pattern = r"[ \t]*(.+?)[ \t]{1,}:[ \t]*([\S]*)"
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=20, regex=True)
        time.sleep(self.RECBUF_TIME)  # Allow recbuf time to catchup after send completion: Apollo limitation!
        p = re.compile(pattern)
        m = p.findall(self._uut_conn.recbuf)
        for k, v in m:
            if 'Number' in k:
                # Convert IOS nomenclature to Bootloader nomenclature.
                k = k.replace('Number', 'Num').upper().replace(' ', '_')
            params[k] = v
        # Get MAC
        # Switch#show hardware | include MAC
        # Base Ethernet MAC Address          : 04:6c:9d:1e:35:80
        cmd = 'show hardware | include MAC'
        self._clear_recbuf(self._uut_conn)
        self._uut_conn.send('{0}\r'.format(cmd), expectphrase=self._uut_prompt, timeout=20, regex=True)
        time.sleep(self.RECBUF_TIME)
        p = re.compile(pattern)
        m = p.findall(self._uut_conn.recbuf)
        params['MAC_ADDR'] = m[0][1] if m and len(m[0]) == 2 else None
        return params

    def _clear_recbuf(self, uut_conn, force=False):
        if self.USE_CLEAR_RECBUF or force:
            uut_conn.clear_recbuf()
            time.sleep(self.RECBUF_CLEAR_TIME)
        return

    def _check_mode_mgr(self):
        if not self._mode_mgr:
            log.warning("*" * 50)
            log.warning("Many modes must be supported when apttempting to use this driver.")
            log.warning("The PCAMAP can be derived from ROMMON/BTLDR, STARDUST, or IOSE (limited).")
            log.warning("Since a Mode Manager was NOT provided, all modes and dependencies have no mechanism!")
            log.warning("*" * 50)
            raise PcamapException("The pcamap driver MUST have a Mode Manager.")
        return True

    def _check_dependencies(self, names=None):
        if names:
            log.debug("  Checking class dependencies: {0}".format(names))
            for varname, classname in names.items():
                if not getattr(self, varname):
                    raise PcamapException("The property pattern {0} has no class instance.".format(varname))
                if classname != getattr(self, varname).__class__.__name__:
                    raise PcamapException("Wrong class instance: {0};  Expected pattern: {1}.".
                                          format(getattr(self, varname).__class__.__name__, classname))
        if not self._mode_mgr:
            log.warning("*" * 50)
            log.warning("Since a Mode Manager was NOT provided, the mode and dependencies cannot be guaranteed!")
            log.warning("*" * 50)
            raise PcamapException("The pcamap driver MUST have a Mode Manager.")
        if not self._ud or not getattr(self._ud, 'uut_config'):
            log.warning("*" * 50)
            log.warning("This class must have a description of the UUT when apttempting to use this driver.")
            log.warning("Since a UUT Descriptor was NOT provided, this driver will generate an exception!")
            log.warning("*" * 50)
            raise PcamapException("The pcamap driver MUST have a UUT Descriptor.")
        return True


class PcamapGen3(Pcamap):
    """ Pcamap Gen3
    Manages all PCAMAP activity for the Generation 3 product families.
    """

    # Note: This is a Read-Only TLV Map List (meant for generic Catalyst class uasge only for initial UUT discovery).
    #       Do not use this default map for writing to TLV since all offsets are 0x00.
    DEFAULT_RO_TLV_MAP_LIST = [
        ('Part Number - PCA', ('0x00', 'MOTHERBOARD_ASSEMBLY_NUM')),
        ('Revision number - PCA', ('0x00', 'MOTHERBOARD_REVISION_NUM')),
        ('Serial number', ('0x00', 'SYSTEM_SERIAL_NUM')),
        ('Part Number - TAN', ('0x00', 'TAN_NUM')),
        ('Revision number - TAN', ('0x00', 'TAN_REVISION_NUMBER')),
        ('Product number/identifier', ('0x00', 'CFG_MODEL_NUM')),
        ('UDI Product Name', ('0x00', 'MODEL_NUM')),
        ('Version identifier', ('0x00', 'VERSION_ID')),
        ('MAC address - Base', ('0x00', 'MAC_ADDR')),
        ('MAC address - block size', ('0x00', 'MAC_BLOCK_SIZE')),
    ]
    DEFAULT_RO_TLV_MAP = OrderedDict(DEFAULT_RO_TLV_MAP_LIST)

    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapGen3, self).__init__(mode_mgr, ud, **kwargs)
        self._tlv_map = None
        self._tlv_inverse_map = None
        self.tlv_map = self._ud.tlv_map if hasattr(self._ud, 'tlv_map') else self.DEFAULT_RO_TLV_MAP
        return

    @property
    def tlv_map(self):
        return self._tlv_map

    @tlv_map.setter
    def tlv_map(self, newvalue):
        self._tlv_map = newvalue
        self._tlv_inverse_map = OrderedDict([(v[1], (v[0], k, v[2] if len(v) == 3 else None)) for k, v in self._tlv_map.items()])
        setattr(self._ud, 'tlv_map', self._tlv_map)
        setattr(self._ud, 'tlv_inverse_map', self._tlv_inverse_map)
        # Example:
        # tlv_map         ->  ('Part number - PCA', ('0x82', 'MOTHERBOARD_ASSEMBLY_NUM')),
        # tlv_inverse_map ->  'MOTHERBOARD_ASSEMBLY_NUM': ('0x82', 'Part number - PCA', None)

    # ------------------------------------------------------------------------------------------------------------------
    # USER STEPS
    #
    @apollo_step
    def sync_up(self, **kwargs):
        """Sync Up Pcamap from TLV to flash for GEN3
        :menu: (enable=True, name=SYNC PCAMAP, section=PCAMAP, num=1, args=None)
        :param kwargs:
        :return:
        """

        def __unset_for_sync_up(unset_params):
            """unset default params in flash and re-set. Bootloader automatically sync up from TLV
            :param unset_params:
            :param mm:
            :return:
            """
            rommon_uut_prompt = self._uut_prompt_map['BTLDR']
            p = re.compile('([\S].+)=([\S]*)')
            self._uut_conn.clear_recbuf()
            self._uut_conn.send('set\r', expectphrase=rommon_uut_prompt, timeout=30, regex=True)
            time.sleep(1.0)
            m = p.findall(self._uut_conn.recbuf)
            log.debug(m)
            for i in m:
                if i[0] in unset_params and i[1] != self._ud.uut_config.get(i[0], None):
                    try:
                        self._uut_conn.send('unset {}\r'.format(i[0]), expectphrase=rommon_uut_prompt, timeout=30, regex=True)
                    except Exception:
                        log.error("Params 'unset' FAILED.")
                        log.error("Error info = {}".format(self._uut_conn.recbuf))
                        return False
            return True

        aplib.set_container_text('SYNC UP PCAMAP')
        log.info('STEP: SYNC UP PCAMAP...')

        golden_present = True if 'BTLDRG' in self._uut_prompt_map else False
        mode_list = ['BTLDR', 'BTLDRG'] if golden_present else ['BTLDR']

        # Process input
        unset_params = self._ud.uut_config.get('flash_vb_sync_params', None)
        if not unset_params:
            log.debug("The params for flash sync are not in the product definition (see flash_vb_sync_params).")
            log.warning("The SYNC PCAMAP will be skipped.")
            return aplib.SKIPPED

        # Perform all necessary "unset"
        results = []
        for i, mode in enumerate(mode_list):
            if not self._mode_mgr.goto_mode(mode):
                log.error("Could not goto to {0} mode.".format(mode))
                return aplib.FAIL
            result = __unset_for_sync_up(unset_params)
            results.append(result)
        if not all(results):
            log.error("Unset problem.")
            return aplib.FAIL

        # Reset the system
        log.debug("Reset for params sync up")
        self._uut_conn.send('reset\r', expectphrase='reset', timeout=30, regex=True)
        self._uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
        boot_result, _ = self._mode_mgr.wait_for_boot()
        if not boot_result:
            log.error("Wait for boot failed.")
            aplib.FAIL

        # Ensure BTLDR/Rommon standard mode.
        if not self._mode_mgr.goto_mode('BTLDR'):
            log.error("Could not goto to {0} mode.".format(mode))
            return aplib.FAIL

        log.info('STEP: SYNC UP PCAMAP PASSED.')

        return aplib.PASS if all(results) else aplib.FAIL

    @apollo_step
    def cleanup_rommon_params(self, **kwargs):
        """ Unset Extra Bootloader Parameters for Gen3 (Step)
        Unset any extra params that should not go to the customer.
        Remove parameters setting during manufacturing test, except those default values.
        This step uses 'unset --all' command

        :param (dict) kwargs:
        :return:
        """
        aplib.set_container_text('UNSET EXTRA PARAMS')
        log.debug("STEP: Unset extra params in bootloader.")

        # Process Input.
        params_to_keep = kwargs.get('params_to_keep', self._ud.uut_config.get('rommon_params_to_keep', []))
        set_params = {}
        result_list = []

        # Determine items to unset
        fullparams = self._rommon.get_params()
        for item in params_to_keep:
            set_params.update({item: fullparams.get(item, '')})
        set_params.update(MANUAL_BOOT='yes')

        log.debug('Full Params: {0}'.format(fullparams.keys()))
        log.debug('Params to keep: {0}'.format(params_to_keep))
        log.debug('Set Params: {0}'.format(set_params))

        ret = self._rommon.unset_params(unset_params=None, all_params=True, reset_required=True)
        result_list.append(ret)
        ret = self._rommon.unset_params(unset_params=['ROMMON_AUTOBOOT_ATTEMPT'], reset_required=False)
        result_list.append(ret)
        ret = self._rommon.set_params(setparams=set_params, reset_required=True, force=True)
        result_list.append(ret)

        return aplib.PASS if all(result_list) else aplib.FAIL

    # ------------------------------------------------------------------------------------------------------------------
    # USER METHODS
    #
    @func_details
    def read(self, device_instance, **kwargs):
        params = {}
        original_mode = None
        mode = None

        # Inputs
        tlv_type = kwargs.get('tlv_type', None)

        if not str(device_instance).isdigit():
            log.error("Device instance MUST be numeric only.  Unable to read params.")
            return params
        device_instance = int(device_instance)

        # Motherboard
        if device_instance == 0 or device_instance >= 1000:
            # Get into one of these modes closest to the current mode and save the original.
            mode, original_mode = self._mode(['BTLDR', 'STARDUST', 'IOSE'], do_sysinit=False)
            # Select the command based on mode.
            if mode == 'BTLDR':
                params = self._rommon.get_params()
            elif mode == 'STARDUST':
                # Get vb: space params (not currently supported)
                vb_params = {}

                # Get tlv space params
                log.debug("Prompt = '{0}'".format(self._uut_prompt))
                tlv_params = self._rommon._gettlv(device_instance, tlv_type=tlv_type)

                # Combine
                # Note: tlv: can be duplicated in vb: however tlv: is the gold source so use tlv: data for the update.
                params = vb_params.copy()
                params.update(tlv_params)

            elif mode == 'IOSE':
                params = self._ios_get_params()
            else:
                log.warning("Unable to get flash params; appropriate mode is not available.")

        # Peripherals
        elif 0 < device_instance < 1000:
            mode, original_mode = self._mode('STARDUST')
            params = self._peripheral.read_quack_params(device_instance)

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        return params

    @func_details
    def write(self, device_instance, set_params, **kwargs):
        """ Write

        Two write methods:
            1. Motherboard/Mainboard
            2. Perihperals

        Two write mode:
            1. Flash params in "vb:" (variable block) space
            2. TLV params (in flash or quack; hw dependent)

        The TLV fields for "Standard" and "Custom DB" (0xE6) are processed differently.
        The Custom DB can sometimes ask for data that does NOT apply to the product; a mechanism is in place to provide null data.
        TLV fields required by the product are referenced by the TLV map (reverse lookup).

        :param (int) device_instance:
        :param (dict) set_params: From mm.uut_config (typically)
        :param (dict) kwargs:
        :return:
        """
        log.debug("Writing Gen3 PCAMAP data: {0}".format(set_params))

        result = False
        original_mode = None
        mode = None

        # Inputs
        tlv_only = kwargs.get('tlv_only', False)
        tlv_type = kwargs.get('tlv_type', None)
        tlv_reset = kwargs.get('tlv_reset', True)
        ignore_empty = kwargs.get('ignore_empty', True)
        vb_only = kwargs.get('vb_only', False)
        verbose = kwargs.get('verbose', False)

        # Sanity
        if not str(device_instance).isdigit():
            log.error("Device instance MUST be numeric only.  Unable to write params.")
            return result
        device_instance = int(device_instance)
        if vb_only and tlv_only:
            log.error("Must choose only one or none: vb_only, tlv_only.")
            return False

        log.debug("Setting the following params: {0}".format(set_params.keys()))

        # Motherboard
        if device_instance == 0 or device_instance >= 1000:
            # Two spaces must be managed: TLV and flash vb:
            # Phase 1
            # Extract any vb: flash params first, then set them.
            log.debug("PCAMAP write Phase 1: vb.")
            flash_vb_params = self._ud.uut_config.get('flash_vb_params', None)
            if flash_vb_params and not tlv_only:
                self._vb_flash_write(set_params, flash_vb_params)
            else:
                log.debug("No 'vb:' write.  (tlv_only={0})".format(tlv_only))

            # Phase 2
            # Can only write TLV params from diags
            log.debug("PCAMAP write Phase 2: tlv.")
            if not vb_only:
                mode, original_mode = self._mode('STARDUST')
                self._tlv_write(set_params, tlv_type, tlv_reset, device_instance, None, ignore_empty, mode, verbose)
            else:
                log.debug("No 'tlv' write.  (vb_only={0})".format(vb_only))

            # Confirm write operation
            result = self._check_write(set_params, device_instance, ignore_empty)

        # Peripherals
        elif 0 < device_instance < 1000:
            # Can only write peripheral params from diags
            mode, original_mode = self._mode('STARDUST')
            result = self._peripheral.write_quack_params(device_instance, set_params)

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        log.info("WRITE Result = {0}".format(result))
        return result

    # ------------------------------------------------------------------------------------------------------------------
    # INTERNAL Functions
    #
    def _vb_flash_write(self, set_params, flash_vb_params):
        log.debug("Product Definition 'flash_vb_params': {0}".format(flash_vb_params))
        log.debug("Setting vb: params...")
        if flash_vb_params != 'ALL':
            log.debug('Find set params against flash_vb_params...')
            vb_set_param_list = list(set(flash_vb_params) & set(set_params))
        else:
            log.debug('Find set params against ALL...')
            vb_set_param_list = list(set(self._ud.get_flash_params()) & set(set_params))
        vb_set_params = self._ud.get_flash_params()
        log.debug("Flash params for vb: space = {0}".format(vb_set_params))
        if vb_set_params:
            mode, original_mode = self._mode('BTLDR')
            self._rommon.set_params(vb_set_params)
            if mode != original_mode:
                self._mode(original_mode)
        return

    def _tlv_write(self, set_params, tlv_type, tlv_reset, device_instance, physical_slot, ignore_empty, mode, verbose):
        # Phase 2
        # Can only write TLV params from diags
        log.debug("PCAMAP write Phase 2: tlv.")
        if not mode:
            log.error("Cannot set TLV due to incompatible mode.")
            return False

        tlv_type = self._ud.uut_config.get('tlv_type', '') if not tlv_type else tlv_type
        log.debug("TLV Type = {0}".format(tlv_type))
        if not tlv_type:
            log.error("A valid TLV type is needed with a device_instance.")
            return False

        if device_instance is not None:
            cmd_param = '-i:{0}'.format(device_instance)
            cmd_param2 = '-i:{0} -t:{1}'.format(device_instance, tlv_type)
        elif physical_slot is not None:
            cmd_param = '-s:{0}'.format(physical_slot)
            cmd_param2 = '-s:{0}'.format(physical_slot)
        else:
            log.error("Need a device_instance or physical_slot!")
            log.error("Cannot continue with TLV write since neither were specified.")
            return False

        # Init on full write
        self._clear_recbuf(self._uut_conn, force=True)
        current_params = dict()
        if tlv_reset:
            self._uut_conn.send('setdefaulttlv {0} {1}\r'.format(tlv_type, cmd_param),
                                expectphrase='[y/n]', regex=True, timeout=20)
            self._uut_conn.send('y\r', expectphrase=self._uut_prompt, regex=True, timeout=30)
        else:
            current_params = self.read(device_instance)

        # Print the TLV map that will be applied
        log.debug("TLV MAP for Standard-Named Params")
        log.debug("  Note: Since this is an inverse of the map list, ")
        log.debug("        any duplicate 'standard-named' params should be avoided.")
        log.debug("-" * 80)
        for param_item, tlv_composite in self._tlv_inverse_map.items():
            log.debug("{0:<30} : {1}".format(param_item, tlv_composite))

        # Step thru the TLV inverse map (i.e. keys are the traditional flash params) and select
        # only the params necessary.
        db_state = 0
        db_previous_header = None
        for param_item, tlv_composite in self._tlv_inverse_map.items():
            tlv_field, tlv_field_desc, db_header = tlv_composite

            # 1. Determine param item & value (set defaults)
            param_value = ' ' if not ignore_empty and not set_params.get(param_item, None) else set_params.get(
                param_item, None)
            db_empty_placeholder = False
            if param_item not in set_params:
                log.debug("{0} is NOT part of the params to set.".format(param_item))
                if not db_header:
                    param_item, param_value = None, None
                    tlv_field, tlv_field_desc, db_header = None, None, None
                else:
                    log.debug("  Process TLV item for possible empty placeholder.")
                    db_empty_placeholder = True

            # 2. Special processing
            if param_item == 'MAC_ADDR':
                param_value = convert_mac(param_value, '3.', case='upper')
            if param_item == 'DEVIATION_NUM':
                param_value = convert_eco_deviation(param_value)

            # 3. Zero TLV
            if tlv_field == '0x0' or tlv_field == '0x00':
                log.warning("TLV field is set to 0x00 and will be skipped ({0}).".format(tlv_field_desc))

            # 4. Standard TLV Param
            elif tlv_field != '0xE6':
                # This is standard TLV data.

                # 4. a. Skip if already programmed to same value and only updating TLV
                if not tlv_reset and current_params.get(param_item, None) == param_value:
                    log.debug("Skipping param   '{0}' ({1}, {2}) = '{3}'".format(tlv_field_desc, tlv_field, param_item, param_value))
                    continue

                # 4.b. Sanity
                if not tlv_field:
                    log.debug("No TLV Field.")
                    continue

                # Diags is sloppy with the '-' + suffix (ugh!)
                tlv_field_prompt = '{0}.*:'.format(tlv_field_desc.split('-')[0].strip())
                self._uut_conn.send('settlv {0} -f:{1}\r'.format(cmd_param2, tlv_field), expectphrase='.*:', regex=True, timeout=30)
                time.sleep(self.RECBUF_TIME)
                if 'ERR:' in self._uut_conn.recbuf:
                    log.error("Problem running the settlv command.")
                    log.error("Cannot continue!")
                    return False

                # deep debug log.debug("prompt = '{0}'".format(tlv_field_prompt))
                if re.search(tlv_field_prompt, self._uut_conn.recbuf):
                    # Supported field
                    log.debug("Writing standard '{0}' ({1}, {2}) = '{3}'".
                              format(tlv_field_desc, tlv_field, param_item, param_value))
                    self._uut_conn.send('{0}\r'.format(param_value), expectphrase='[Ww]rite.*\[y/n\]:', timeout=20,
                                        regex=True)
                    if re.search('(?i)ERR:', self._uut_conn.recbuf):
                        # ERR: Invalid input.
                        # Write the new TLV data to SEEPROM ?[y/n]:
                        # please input [y/n]:
                        log.warning("Problem with data entry for TLV '{0}'! This entry will be skipped; check the data & format.".format(tlv_field_desc))
                        self._uut_conn.send('n\r', expectphrase=self._uut_prompt, regex=True, timeout=30)
                    else:
                        self._uut_conn.send('y\r', expectphrase=self._uut_prompt, regex=True, timeout=30)
                else:
                    # Unsupported field for this product.
                    log.warning("Unsupported '{0}' ({1}, {2}) = '{3}'".format(tlv_field_desc, tlv_field, param_item, param_value))
                    if '[y/n]:' not in self._uut_conn.recbuf:
                        self._uut_conn.send('\r', expectphrase='.*', regex=True, timeout=30)
                    self._uut_conn.send('n\r', expectphrase=self._uut_prompt, regex=True, timeout=30)

            # 5. Custom TLV Param
            elif tlv_field == '0xE6':
                # This is DB info!
                # Setting this field is invoked only once!  Multiple sub-settings can occur.
                # IMPORTANT: The order in the tlv_map MUST match the programming sequence for custom DB.
                # This sequence is predetermined by diags and the board tlv type.
                # This is also why the tlv_inverse_map is an OrderedDict.
                tlv_field_prompt = '(?:.*:)|(?:.*\[y/n\]:)'
                log.debug("Writing custom   '{0}' ({1}, {2}) = '{3}'".
                          format(tlv_field_desc, tlv_field, param_item, param_value))
                if db_state == 0:
                    log.debug("DB state 0.") if verbose else None
                    self._uut_conn.send('settlv {0} -f:{1}\r'.format(cmd_param2, tlv_field),
                                        expectphrase=tlv_field_prompt, regex=True, timeout=30)
                    db_state = 1
                if db_state == 1:
                    log.debug("DB state 1.") if verbose else None
                    if db_empty_placeholder:
                        if db_header in self._uut_conn.recbuf:
                            log.warning("Unused DB entry!  Check the diags and the product definition params.")
                            log.warning("Possibilites: 1) diag needs to remove the field, or 2) prod def needs to add the field.")
                            log.warning("The entry will be given a dummy value for now.")
                            db_previous_header = db_header
                        if db_previous_header == db_header:
                            log.warning("Empty value.") if verbose else None
                            self._uut_conn.send('\r', expectphrase=tlv_field_prompt, timeout=20, regex=True)
                    else:
                        self._uut_conn.send('{0}\r'.format(param_value),
                                            expectphrase=tlv_field_prompt, timeout=20, regex=True)
                    time.sleep(self.RECBUF_TIME)
                    if re.search('[Ww]rite.*\[y/n\]:', self._uut_conn.recbuf):
                        log.debug("DB state 2.") if verbose else None
                        self._uut_conn.send('y\r', expectphrase=self._uut_prompt, regex=True, timeout=30)
                        db_state = 2

        log.debug("TLV map processing done.")

        # 6. Ensure graceful exit of previous TLV write command
        # Do this if the TLV map does not match with Custom DB entries expected by diags.
        done = False
        while not done:
            self._uut_conn.send('\r', expectphrase='.*', regex=True, timeout=30)
            time.sleep(self.RECBUF_TIME)
            if re.search('[Ww]rite.*\[y/n\]:', self._uut_conn.recbuf):
                self._uut_conn.send('y\r', expectphrase='.*', regex=True, timeout=30)
                log.warning("Graceful end, write remaining...")
                log.warning("Check synchronization of prompts and available data.")
            elif re.search('.*\[y/n\]:', self._uut_conn.recbuf):
                self._uut_conn.send('n\r', expectphrase='.*', regex=True, timeout=30)
                log.warning("Graceful end...")
                log.warning("Something went wrong with the synchronization of data entry!")
                log.warning("Check the TLV map, product definition params, and diags settlv function!")
                log.warning("This can also occur for incomplete TLV data during middle of E2E process whereby")
                log.warning(" a custom TLV setting is not part of params to set.")
                # result_list.append(False)
            elif re.search('.*:', self._uut_conn.recbuf):
                self._uut_conn.send('\r', expectphrase='.*', regex=True, timeout=30)
                log.warning("Graceful cleanup...")
            elif re.search(self._uut_prompt, self._uut_conn.recbuf):
                done = True
        return True

    def _check_write(self, set_params, device_instance, ignore_empty):
        log.debug("Checking the write operation...")
        result_list = []
        current_params = self.read(device_instance)
        params_to_check = list(set(set_params) & set(current_params))
        # Step thru each param but only look at what is common to the target params and current params.
        log.debug("Params to check: {0}".format(params_to_check))
        for item in params_to_check:
            # Normalize and handle any special items
            check_item = True
            if 'ATTEMPT' in item or 'COUNT' in item:
                check_item = False
            if item == 'MAC_ADDR':
                set_params[item] = convert_mac(set_params[item], conv_type='3.', case='upper')
                current_params[item] = convert_mac(current_params[item], conv_type='3.', case='upper')
            if item == 'DEVIATION_NUM':
                set_params[item] = convert_eco_deviation(set_params[item])
                current_params[item] = convert_eco_deviation(current_params[item])

            # Do the check
            if check_item:
                if set_params[item] == current_params[item]:
                    result_list.append(True)
                else:
                    log.warning("Item {0} NOT set: current='{1}'  target='{2}'".
                                format(item, current_params[item], set_params[item]))
                    if set_params[item]:
                        result_list.append(False)
                        log.error("Item {0} FAILED for programming!".format(item))
                    elif ignore_empty:
                        result_list.append(True)
                        log.warning("Item {0} is IGNORED for programming.".format(item))
        return all(result_list)


# ----------------------------------------------------------------------------------------------------------------------
# C2K & C9200 Family
class PcamapC2000(PcamapGen3):
    """ Pcamap C9200
    Manages all PCAMAP activity for the C2900 product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Quake
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC2000, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC2000', '_peripheral': 'PeripheralC2K'})
        return


class PcamapC9200(PcamapGen3):
    """ Pcamap C9200
    Manages all PCAMAP activity for the C9200 product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Quake
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC9200, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC9200', '_peripheral': 'PeripheralC2K'})
        return


# ----------------------------------------------------------------------------------------------------------------------
# C3K & C9300 Family
class PcamapC3000(Pcamap):
    """ Pcamap C3000
    Manages all PCAMAP activity for the C3850/C3650 product families.
    Inherits from Gen2 and overrides where needed.
    Includes: Edison (Newton, Gladiator, Planck, Orsted)
              Archimedes, Euclid, Theon
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC3000, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC3000', '_peripheral': 'PeripheralC3K'})
        return


class PcamapC9300(PcamapGen3):
    """ Pcamap C9300
    Manages all PCAMAP activity for the C9300 product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Nyquist (Shannon, Hartely, Whittaker)
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC9300, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC9300', '_peripheral': 'PeripheralC3K'})
        return


class PcamapC9300L(PcamapGen3):
    """ Pcamap C9300L
    Manages all PCAMAP activity for the C9300L product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Franklin
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC9300L, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC9300L', '_peripheral': 'PeripheralC3K'})
        return


# ----------------------------------------------------------------------------------------------------------------------
# C4K & C9400 Family
class PcamapC4000(Pcamap):
    """ Pcamap C4000
    Manages all PCAMAP activity for the C4500 product families.
    Includes: K10, K5, Galaxy
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC4000, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC4000', '_peripheral': 'PeripheralC4K'})
        self.modular_type = kwargs.get('modular_type', 'supervisor')
        return


class PcamapC9400(PcamapGen3):
    """ Pcamap C9400
    Manages all PCAMAP activity for the C9400 product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Macallen
    """

    MODULAR_SPECIFIER = {'linecard':   'physical_slot',
                         'supervisor': 'physical_slot',
                         'chassis':    'device_instance',
                         'fantray':    'device_instance'}

    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC9400, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC9400', '_peripheral': 'PeripheralC4K'})
        self.modular_type = kwargs.get('modular_type', 'supervisor')
        return

    @func_details
    def read(self, device_instance, **kwargs):
        params = {}
        original_mode = None
        mode = None

        # Sanity check and ensure int
        if device_instance and not str(device_instance).isdigit():
            log.error("Device instance or physical slot MUST be numeric only.  Unable to read params.")
            return params
        if self.modular_type not in self.MODULAR_SPECIFIER:
            log.error("The modular type is NOT properly set for the C4KPcamap class.")
            return params
        device_instance = int(device_instance) if device_instance else None

        # Sup
        if self.modular_type == 'supervisor':
            physical_slot = device_instance
            # Get into one of these modes closest to the current mode and save the original.
            mode, original_mode = self._mode(['BTLDR', 'STARDUST', 'IOSE'], do_sysinit=False)
            # Select the command based on mode.
            if mode == 'BTLDR':
                params = self._rommon.get_params()
            elif mode == 'STARDUST':
                # Get vb: space params (not currently supported)
                vb_params = {}
                # Get tlv space params
                log.debug("Prompt = '{0}'".format(self._uut_prompt))
                tlv_params = self._rommon._gettlv(physical_slot=physical_slot)
                # Combine
                # Note: tlv: can be duplicated in vb: however tlv: is the gold source so use tlv: data for the update.
                params = vb_params.copy()
                params.update(tlv_params)
            elif mode == 'IOSE':
                params = self._ios_get_params()
            else:
                log.warning("Unable to get flash params; appropriate mode is not available.")

        # Linecards
        elif self.modular_type == 'linecard':
            physical_slot = device_instance
            mode, original_mode = self._mode('STARDUST')
            # Get tlv space params
            log.debug("Prompt = '{0}'".format(self._uut_prompt))
            params = self._rommon._gettlv(physical_slot=physical_slot)

        # Chassis, Fantray
        elif self.modular_type in ['chassis', 'fantray']:
            mode, original_mode = self._mode('STARDUST')
            # Get tlv space params
            log.debug("Prompt = '{0}'".format(self._uut_prompt))
            params = self._rommon._gettlv(device_instance=device_instance)

        else:
            log.error("Modular type ({0}) is unknown.".format(self.modular_type))

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        return params

    @func_details
    def write(self, device_instance, set_params, **kwargs):
        """ Write

        Two write methods:
            1. Motherboard/Mainboard
            2. Perihperals

        Two write mode:
            1. Flash params in "vb:" (variable block) space
            2. TLV params (in flash or quack; hw dependent)
               USAGE: SetTlvIdprom [-t:<type>|-s:<slot>] [-i:<instance>] [-f:<tlv_field>]
                    -t:<type> -- Idprom type: fantray/chassis/chassis_alphaECI/
                                 (default to active sup)
                    -s:<slot> -- Slot number (default to local sup slot)
                    -i:<instance> -- Instance number of the idprom (default 0)
                          For idproms stored on act2, run ShowAllQuackInst
                          to see all quack instances.
                    -f:<tlv_field> -- Tlv type of the field
                          Default to all tlv fields supported in system,
                          run ShowIdpromTlvType to see all tlv types.

        The TLV fields for "Standard" and "Custom DB" (0xE6) are processed differently.
        The Custom DB can sometimes ask for data that does NOT apply to the product; a mechanism is in place to provide null data.
        TLV fields required by the product are referenced by the TLV map (reverse lookup).

        :param device_instance:
        :param (dict) set_params: From mm.uut_config (typically)
        :param kwargs:
        :return:
        """
        result = False
        original_mode = None
        mode = None
        log.debug("Writing Gen3 PCAMAP data: {0}".format(set_params))

        # Inputs
        tlv_only = kwargs.get('tlv_only', False)
        tlv_type = kwargs.get('tlv_type', None)
        tlv_reset = kwargs.get('tlv_reset', True)
        ignore_empty = kwargs.get('ignore_empty', True)
        vb_only = kwargs.get('vb_only', False)
        verbose = kwargs.get('verbose', False)

        # Sanity
        if not str(device_instance).isdigit():
            log.error("Device instance MUST be numeric only.  Unable to write params.")
            return result
        device_instance = int(device_instance)
        if vb_only and tlv_only:
            log.error("Must choose only one or none: vb_only, tlv_only.")
            return False

        log.debug("Setting the following params: {0}".format(set_params.keys()))

        # Sanity check and ensure int
        if device_instance and not str(device_instance).isdigit():
            log.error("Device instance or physical slot MUST be numeric only.  Unable to write params.")
            return False
        if self.modular_type not in self.MODULAR_SPECIFIER:
            log.error("The modular type is NOT properly set for the C4KPcamap class.")
            return False

        device_instance = int(device_instance) if device_instance else None
        physical_slot = device_instance

        # Sup -------------------------------------------------------------------------
        if self.modular_type == 'supervisor':
            # Two spaces must be managed: TLV and flash vb:
            # Phase 1
            # Extract any vb: flash params first, then set them.
            log.debug("PCAMAP write Phase 1: vb.")
            flash_vb_params = self._ud.uut_config.get('flash_vb_params', None)
            if flash_vb_params and not tlv_only:
                self._vb_flash_write(set_params, flash_vb_params)
            else:
                log.debug("No 'vb:' write.  (tlv_only={0})".format(tlv_only))

            # Phase 2
            # Can only write TLV params from diags
            log.debug("PCAMAP write Phase 2: tlv.")
            if not vb_only:
                mode, original_mode = self._mode('STARDUST')
                self._tlv_write(set_params, tlv_type, tlv_reset, None, physical_slot, ignore_empty, mode, verbose)
            else:
                log.debug("No 'tlv' write.  (vb_only={0})".format(vb_only))

        # Linecards --------------------------------------------------------------------
        elif self.modular_type == 'linecard':
            mode, original_mode = self._mode('STARDUST')
            self._tlv_write(set_params, tlv_type, tlv_reset, None, physical_slot, ignore_empty, mode, verbose)

        # Chassis, Fantray --------------------------------------------------------------------
        elif self.modular_type in ['chassis', 'fantray']:
            mode, original_mode = self._mode('STARDUST')
            self._tlv_write(set_params, tlv_type, tlv_reset, device_instance, None, ignore_empty, mode, verbose)

        else:
            log.error("Modular type ({0}) is unknown.".format(self.modular_type))

        # Confirm write operation
        result = self._check_write(set_params, physical_slot, ignore_empty)

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        log.info("WRITE Result = {0}".format(result))
        return result


# ----------------------------------------------------------------------------------------------------------------------
# C9500 Family
class PcamapC9500(PcamapGen3):
    """ Pcamap C9500
    Manages all PCAMAP activity for the C9500 product families.
    Inherits from Gen3 and overrides where needed.
    Includes: Adelphi
    """
    def __init__(self, mode_mgr, ud, **kwargs):
        super(PcamapC9500, self).__init__(mode_mgr, ud, **kwargs)
        self._check_dependencies({'_rommon': 'RommonC9500', '_peripheral': 'PeripheralC5K'})
        return

    @func_details
    def read(self, device_instance=None, **kwargs):
        """ Read PCAMAP from Stardust

        Only support reading PCAMAP by gettlv from Stardust

        :param device_instance:     not used for C5K, keep for compatibility with rommon._gettlv()
        :return params:             (dict) data from gettlv
        """
        valid_modes = ['BTLDR', 'STARDUST']
        params = {}

        # Inputs
        tlv_type = kwargs.get('tlv_type', None)

        # Get into one of these modes closest to the current mode and save the original.
        mode, original_mode = self._mode(valid_modes, do_sysinit=False)
        # Select the command based on mode.
        if mode == 'BTLDR':
            params = self._rommon.get_params()
        elif mode == 'STARDUST':
            # Get vb: space params (not currently supported)
            vb_params = {}

            # Get tlv space params
            log.debug("Prompt = '{0}'".format(self._uut_prompt))
            tlv_params = self._rommon._gettlv(device_instance=device_instance, tlv_type=tlv_type)

            # Combine
            # Note: tlv: can be duplicated in vb: however tlv: is the gold source so use tlv: data for the update.
            params = vb_params.copy()
            params.update(tlv_params)

        elif mode == 'IOSE':
            params = self._ios_get_params()
        else:
            log.warning("Unable to get flash params; appropriate mode {0} is not available.".format(valid_modes))

        # Restore mode
        if mode != original_mode:
            self._mode(original_mode)

        return params

    @func_details
    def write(self, device_instance=None, set_params=None, **kwargs):
        log.debug("C5k PCAMAP Wite: {0}".format(set_params))
        log.warning("THIS METHOD IS NOT YET SUPPORTED!")
        return False
