"""
Catalyst

[Catalyst]---->[CatalystX]---->[<ProductLine class>]
    ^
    |
    +--- Parent class object.

NOTE: This class object provides the basis for ALL other Catalyst derived product classes.
      Basic product functions should be contained here.
      The class instance available here is primarily for PRE-SEQ to provide a starting point and
      some basic "kernel" functions. (Do not change the init order!)

"""

# Python
# ------
import sys
import logging
import time
import os
import inspect

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Libs
# ------
from apollo.scripts.entsw.libs.cat.uut_descriptor import UutDescriptor as _UutDescriptor
from apollo.scripts.entsw.libs.mode.modemanager import ModeManager as _ModeManager
from apollo.scripts.entsw.libs.mfg.process import Process as _Process
from apollo.scripts.entsw.libs.product_drivers.power import Power as _Power
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonGen3 as _RommonGen3
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapGen3 as _PcamapGen3
from apollo.scripts.entsw.libs.product_drivers.peripheral import Peripheral as _Peripheral
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.utils import common_utils
from apollo.scripts.entsw.libs.diags.stardust import Stardust as _Stardust
from apollo.scripts.entsw.libs.mode import modes

__title__ = "Catalyst Product General Module"
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

if not hasattr(aplib.conn, 'uutTN'):
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1, 'power_on': 1}))


class Catalyst(object):
    def __init__(self):
        """ Init
        Method: Single layer of nested class instances for easy organization.
        Note: Order is important due to dependencies!  Any inheritance MUST follow suit.
        *** DO NOT CHANGE THIS INIT ***
        """
        self.show_version()
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=None, product_line_def=None, uut_conn=self.uut_conn,
                                 parent_module=thismodule)
        self.mode_mgr = _ModeManager(mode_module=modes, statemachine=modes.uut_state_machine,
                                     uut_prompt_map=modes.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonGen3(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[])
        self.diags = _Stardust(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip)
        self.peripheral = _Peripheral(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapGen3(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self._callback_()
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    def _callback_(self):
        """ Callback
        For each of the member classes that belong to the top-level Catalyst product class, add a callback
        property which is the product class itself.
        :return:
        """
        log.debug("Catalyst callbacks")
        for c in ['ud', 'mode_mgr', 'process', 'power', 'rommon', 'linux', 'equip', 'diags', 'peripheral',
                  'pcamap', 'ios', 'quack2', 'act2', 'x509sudi', 'traffic.fmdiags', 'traffic.fmgenerator']:
            p = self
            for m in c.split('.'):
                if hasattr(p, m):
                    p2 = getattr(p, m)
                    setattr(p2, '_callback', self) if p2 else None
                    p = p2
                    # log.debug("  Callback {0} = {1}".format(m, p2))

    def show_version(self):
        log.info("-" * len(self.__repr__()))
        log.info(self.__repr__())
        log.info("-" * len(self.__repr__()))
        return

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def clean_up(self, **kwargs):
        # All Equipment disconnect
        self.equip.disconnect()
        # Automation
        if self.ud.automation:
            # auto_control.auto_finish(self.ud.puid.sernum)
            pass
        return aplib.PASS

    @apollo_step
    def loop_marker(self, **kwargs):
        """ Loop Marker
        Keep track of an arbitrary loop counter called "loop_count" and print a banner.
        The loop counter can be used for anything; (for example FST loop on a subsequence).
        Usage would be at the the start of a sequence loop, then make final call with close_loop outside the
        sequence loop.
        :param kwargs:
               (int) loop_count: Value of current loop count. If provided, can be used as an offset (not typical).
               (bool) close_loop: Closes the counter and removes the dict.  Allows for final banner print.
        :return:
        """

        title = kwargs.get('title', 'LOOP')
        loop_count = kwargs.get('loop_count', self._ud.uut_config.get('loop', {}).get('count', 0))
        close_loop = kwargs.get('close_loop', False)

        loop_count += 1
        _, mktime = common_utils.getservertime()
        if 'loop' not in self._ud.uut_status:
            self._ud.uut_status['loop'] = {'count': loop_count, 'singlelooptimestamp': mktime, 'allloopstimestamp': mktime}
            elapsed_time = 0
            total_elapsed_time = 0
        else:
            elapsed_time = mktime - self._ud.uut_status['loop']['singlelooptimestamp']
            total_elapsed_time = mktime - self._ud.uut_status['loop']['allloopstimestamp']
            self._ud.uut_status['loop'] = {'count': loop_count, 'singlelooptimestamp': mktime}
            if close_loop:
                self._ud.uut_status.pop('loop')
                loop_count -= 1

        aplib.set_container_text('{0} {1}'.format(title, loop_count))

        log.debug("=" * 120)
        log.debug("{0}".format(title))
        log.debug("LOOP COUNT             = {0}".format(loop_count))
        log.debug("LOOP ELAPSED TIME      = {0}  ({1} secs)".
                  format(common_utils.ddhhmmss(elapsed_time), elapsed_time)) if elapsed_time else None
        log.debug("TOTAL TIME (all loops) = {0}  ({1} secs)".
                  format(common_utils.ddhhmmss(total_elapsed_time), total_elapsed_time)) if total_elapsed_time else None
        log.debug("=" * 120)

        return aplib.PASS

    @apollo_step
    def load_hw_images(self, **kwargs):
        """ Load Mfg Images
        :menu: (enable=True, name=LOAD IMAGES, section=Upgrade, num=1, args={'master_list': None})
        :menu: (enable=True, name=LOAD ALL IMAGES, section=Upgrade, num=1, args={})
        :param (dict) kwargs:
               (list) master_list: key names of file items to load from product_definition
                                   e.g. ['btldr', 'linux', 'diag', 'fpga', 'mcu', 'SBC_CFG']
                                   If a master_list is NOT provided the user will be asked to manually enter the files.
                                   'DEFAULT' file name entry will use the existing product_definition specified files.
               (bool) force: True means to overwrite any existing
        :return (str): aplib.PASS/FAIL
        """
        DEFAULT_IMAGE_TYPES = ['btldr', 'linux', 'diag', 'fpga', 'mcu', 'nic', 'SBC_CFG']

        # Process input
        master_list = kwargs.get('master_list', DEFAULT_IMAGE_TYPES)
        force = kwargs.get('force', True)
        ignore_result = kwargs.get('ignore_result', False)

        # Check mode
        if not self.mode_mgr.is_mode('LINUX'):
            errmsg = "Must be in LINUX mode to download files."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        src_files = []
        if not master_list:
            # Menu/Operator Option
            answer = aplib.ask_question("Enter the image names to download.\n"
                                        "Comma separated if more than one.\n"
                                        "(Note1: Syntax = file1, file2, subdir1/file3, ...)\n"
                                        "(Note2: 'MASTER=x,y,z,...' will use a new master list.)\n"
                                        "(Note3: 'DEFAULT' will automatically choose the standard "
                                        "images from the product_definitions' master list: [{0}].)\n".format(master_list))
            if 'MASTER=' in answer:
                tmp = answer.split('=')
                master_list = tmp[1].split(',')
            elif answer != 'DEFAULT':
                src_files = [i.strip() for i in answer.split(',')]
            else:
                # Override the master list if empty
                master_list = DEFAULT_IMAGE_TYPES if not master_list else master_list

        if not src_files:
            # Explicit param list option OR 'DEFAULT' user option.
            # Create source file list
            uut_target_list = list(set(master_list) & set(self.ud.uut_config))
            src_files = []
            log.debug("UUT Target key list for TFTP: {0}".format(uut_target_list))
            for item in uut_target_list:
                item_data = self.ud.uut_config.get(item, None)
                if not item_data:
                    log.warning("{0} has no data specified; confirm product_definition file data.".format(item))
                    continue
                source_items = []
                if isinstance(item_data, dict):
                    if 'image' in item_data:
                        source_items.append(item_data['image'])
                        source_items.append(item_data.get('cfg', None))
                        if 'image2' in item_data:
                            source_items.append(item_data['image2'])
                            source_items.append(item_data.get('cfg2', None))
                    elif 'images' in item_data:
                        source_items.append(item_data['images'])
                    elif len(item_data.keys()) > 0:
                        for k, v in item_data.items():
                            if not isinstance(v, bool) and not isinstance(v, int):
                                if 'image' in v:
                                    source_items.append(v['image'])
                else:
                    source_items.append(item_data)

                for source_item in source_items:
                    if source_item:
                        log.debug("{0:<10} = {1}".format(item, source_item))
                        if isinstance(source_item, str):
                            src_files.append(source_item) if source_item else None
                        elif isinstance(source_item, dict):
                            for sub_dir, image_list in source_item.items():
                                for item2 in image_list:
                                    src_files.append(os.path.join(sub_dir, item2)) if item2 else None
                        elif isinstance(source_item, list):
                            for item2 in source_item:
                                src_files.append(item2) if item2 else None
                        else:
                            log.warning(
                                "{0} type is unknown; check product_definition file for correct nomenclature.".format(
                                    source_item))
                            log.warning("It will be ignored.")

            # Remove duplicates
            src_files = list(set(src_files))

        tftpargs = {
            'src_files': src_files,
            'dst_files': 'SAME',
            'direction': 'get',
            'force': force
        }
        log.debug("src_files={0}".format(src_files))
        ret = self.linux.tftp(**tftpargs)
        if ret != aplib.PASS and ignore_result:
            log.warning("*** TFTP results will be IGNORED! ***")
            ret = aplib.PASS
        return ret

    @apollo_step
    def upgrade_btldr(self, **kwargs):
        """ Upgrade Bootloader/Rommon
        :menu: (enable=True, name=UPGRADE BTLDR, section=Upgrade, num=1, args={'force': False})
        :menu: (enable=True, name=UPGRADE BTLDR force, section=Upgrade, num=1, args={'force': True})
        :param kwargs:
        :return:
        """
        if 'btldr' not in self.ud.uut_config:
            log.warning("The 'btldr' data dict is not defined per the product_definition.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        # Process input
        btldr = kwargs.get('btldr', self.ud.uut_config.get('btldr', {}))
        btldr_image = btldr.get('image', '')
        btldr_image_type = btldr.get('image_type', None)
        btldr_image_upgrade_params = btldr.get('params', None)
        btldr_rev = btldr.get('rev', '')
        confirm = kwargs.get('confirm', False)
        force = kwargs.get('force', False)

        # Check mode
        if self.mode_mgr.current_mode not in ['BTLDR']:
            errmsg = "Wrong mode; need to be in BTLDR."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        if not self.rommon.check_version(btldr_rev) or force:
            # Perform the upgrade
            aplib.set_container_text('UPGRADE BTLDR: {0}'.format(btldr_image))
            result = self.rommon.upgrade(btldr_image, image_type=btldr_image_type, params=btldr_image_upgrade_params, force=force)
            self.ud.uut_config['POR_enabled'] = True
            if result and confirm:
                self.rommon.check_version(btldr_rev)
        else:
            log.info("Bootloader version {0} = GOOD.".format(btldr_rev))
            log.info("Bootloader upgrade not required.")
            result = True
            self.ud.uut_config['POR_enabled'] = False

        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def upgrade_fpga(self, **kwargs):
        """ Upgrade FPGA
        :menu: (enable=True, name=UPGRADE FPGA, section=Upgrade, num=1, args={'force': False, 'confirm': False})
        :menu: (enable=False, name=UPGRADE FPGA force, section=Upgrade, num=1, args={'force': True, 'confirm': False})
        :param kwargs:
        :return:
        """
        if 'fpga' not in self.ud.uut_config:
            log.warning("The 'fpga' data dict is not defined per the product_definition.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        # Process input
        fpga = kwargs.get('fpga', self.ud.uut_config.get('fpga', {}))
        force = kwargs.get('force', False)
        confirm = kwargs.get('confirm', False)

        # Set some defaults if needed
        fpga_image = fpga.get('image', fpga.get('images', None))
        fpga_rev = fpga.get('rev', '')
        fpga_reg = fpga.get('revreg', 'FpgaRevision')
        fpga_dual = fpga.get('dual', False)
        enabled = fpga.get('enabled', True)

        # Check Mode
        if self.mode_mgr.current_mode != 'STARDUST':
            errmsg = "Wrong mode; need to be in STARDUST."
            log.error(errmsg)
            return aplib.FAIL. errmsg

        # Get the FPGA Name
        fpga_name = self.diags._get_fpga_name()
        if not fpga_name:
            log.debug("No FPGA name. Upgrade will be ignored.")
            return aplib.SKIPPED

        # Check the version
        fpga_good, op_error = self.diags._check_fpga(name=fpga_name, revision=fpga_rev, register=fpga_reg)
        if op_error:
            errmsg = "Operational error; cannot check FPGA."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Check the upgrade if needed or if forced
        if fpga_good and not force:
            log.info("No FPGA upgrade required.")
            return aplib.PASS

        # Check that an image is available
        if not fpga_image:
            errmsg = "FPGA upgrade is required but no image(s) available!"
            log.error(errmsg)
            return aplib.FAIL, errmsg
        if len(fpga_image) == 2 and not fpga_dual:
            fpga_dual = True
            log.debug("Dual images detected. Adjusting fpga_dual=True.")

        # Perform the upgrade
        aplib.set_container_text('UPGRADE FPGA: {0}'.format(fpga_image))
        log.info("FPGA {0}upgrade started...".format('forced ' if force else ''))
        if not self.diags._upgrade_fpga(images=fpga_image, dual=fpga_dual, enabled=enabled):
            log.error("FPGA Programming incomplete.")
            return aplib.FAIL
        self.ud.uut_config['POR_enabled'] = True

        # Confirm version
        # Note: Careful using the confirm feature since secure boot upgrade might have other required
        #       tasks before a power-cycle.
        if confirm:
            log.debug("Upgrade confirmation requested; power-cycle will occur...")
            # Prepare
            powresult = self.power.cycle_on()
            self.ud.uut_config['POR_enabled'] = False
            if powresult != aplib.PASS:
                errmsg = "Cannot return from power-cycle after FPGA upgrade!"
                log.error(errmsg)
                return aplib.FAIL, errmsg
            if not self.mode_mgr.goto_mode('STARDUST'):
                errmsg = "Cannot return to diags after FPGA upgrade!"
                log.error(errmsg)
                return aplib.FAIL, errmsg
            if self.diags.sysinit() != aplib.PASS:
                errmsg = "Cannot sysinit after FPGA upgrade!"
                log.error(errmsg)
                return aplib.FAIL, errmsg
            # Check
            fpga_good, _ = self.diags._check_fpga(name=fpga_name, revision=fpga_rev, register=fpga_reg)
            if fpga_good:
                log.info("FPGA Programmed revision confirmed.")
            else:
                errmsg = "FPGA Programmed revision NOT confirmed."
                log.error(errmsg)
                return aplib.FAIL, errmsg
        else:
            log.warning("No upgrade confirmation requested; therefore the unit will need a power-cycle later.")
            log.warning("Ensure the power-cycle takes places for the upgrade to take effect!")

        return aplib.PASS

    @apollo_step
    def update_sbc(self, **kwargs):
        """ Update SBC

        SBC Programming and Power Cycle (garzaga 09/24/2018)
        You must absolutely power cycle after programming and before performing the check.
        The reason we do this is because we want the check to be done on the NVRAM contents.
        If you don't power cycle, you're just checking what's in SRAM.
        It's possible to have a successful write to SRAM but an unsuccessful write to NVRAM.
        It has happened before and it's why we have the check.
        Reasons are usually because of problems with the config file, but a bit flip could cause the same problem.
        The controllers will ignore invalid values and not tell you about it, but you will notice what you wrote is not valid.

        :menu: (enable=True, name=UPDATE SBC, section=Upgrade, num=1, args=None)
        :param kwargs:
        :return:
        """

        # Process input
        sbc_image = kwargs.get('SBC_CFG', self.ud.uut_config.get('SBC_CFG', None))
        device_instance = kwargs.get('device_instance', 0)
        sbc = kwargs.get('sbc', self.ud.uut_config.get('sbc', None))
        home_dir = kwargs.get('home_dir', self.ud.get_flash_mapped_dir())

        if not sbc_image:
            log.warning("The 'SBC_CFG' param is empty.")
            log.warning("This upgrade will be skipped.")
            return aplib.SKIPPED

        if not sbc:
            errmsg = "The product definition is missing the 'sbc' entry."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Set vars
        self.diags.sbc = sbc
        power_request = self.diags.sbc.get('op', True)
        program_begin_label = self.diags.sbc.get('label', {}).get('program_begin_label', None)
        sync_begin_label = self.diags.sbc.get('label', {}).get('sync_begin_label', None)
        verify_begin_label = self.diags.sbc.get('label', {}).get('verify_begin_label', None)

        # Check Mode
        if self.mode_mgr.current_mode != 'STARDUST':
            errmsg = "Wrong mode; need to be in STARDUST."
            log.error(errmsg)
            return aplib.FAIL. errmsg

        aplib.set_container_text('UPDATE SBC: {0}'.format(sbc_image))
        log.info("SBC Update: Process START.")
        time.sleep(2.0)

        # Step 1: Show SBC voltages
        aplib.set_container_text('UPDATE SBC Step 1: Show volt')
        log.debug("SBC Update: Step 1 - Show Voltages...")
        self.diags._get_volt(device_instance)

        # Step 2: Perform the programming update
        aplib.set_container_text('UPDATE SBC Step 2: Prog')
        log.debug("SBC Update: Step 2 - Prog...")
        if not self.diags._run_sbc_batch(sbc_image=sbc_image,
                                        begin_label=program_begin_label,
                                        home_dir=home_dir):
            log.error("SBC Update: Programming phase FAILED.")
            log.error("Suspending update process.")
            return aplib.FAIL, "Bad SBC programming."

        # Step 3: Power Cycle, Option: some products do not need power cycle
        aplib.set_container_text('UPDATE SBC Step 3: Power cycle')
        log.debug("SBC Update: Step 3 - Power-cycle...")
        if power_request:
            self.power.cycle_on()
            if not self.mode_mgr.goto_mode('STARDUST'):
                log.error("SBC Update: Problem with entering diags after SBC update and power-cycle.")
                return aplib.FAIL, "Mode failure after power cycle during SBC programming."
        else:
            log.debug("No Power-cycle Request, Skipped...")

        # Step 4: Sync
        aplib.set_container_text('UPDATE SBC Step 4: Sync')
        log.debug("SBC Update: Step 4 - Sync...")
        if sync_begin_label:
            if not self.diags._run_sbc_batch(sbc_image=sbc_image,
                                            begin_label=sync_begin_label,
                                            home_dir=home_dir):
                log.error("SBC Update: Sync phase FAILED.")
                log.error("Suspending update process.")
                return aplib.FAIL, "SBC Sync Phase."
        else:
            log.debug("No Sync request, Skipped...")

        # Step 5: Verify programming
        aplib.set_container_text('UPDATE SBC Step 5: Verify')
        log.debug("SBC Update: Step 5 - Verify Prog...")
        if not self.diags._run_sbc_batch(sbc_image=sbc_image,
                                        begin_label=verify_begin_label,
                                        home_dir=home_dir):
            log.error("SBC Update: Verification phase FAILED.")
            return aplib.FAIL, "SBC Verification."

        # Step 6: Show SBC voltages
        aplib.set_container_text('UPDATE SBC Step 6: Show volt')
        log.debug("SBC Update: Step 6 - Show Voltages...")
        self.diags._get_volt(device_instance)

        log.info("SBC Update: Process DONE.")
        time.sleep(2.0)
        return aplib.PASS

        # INTERNAL ---------------------------------------------------------------------------------------------------------
        #

    # ==================================================================================================================
    # USER Methods (support)
    # ==================================================================================================================
    def list_apollo_steps(self):
        """ List Apollo Steps
        Handy utility to list all class methods decorated with "@apollo_step".
        The methods are intended to be called by the step functions directly via the initialized class.
        :return:
        """
        verbose = False
        col1 = 40
        col2 = 100
        cdict = {}
        mdict = {}

        def __list_subclass_names(_class, _pfx=''):
            _class_instance_names = []
            for p in [i for i in dir(_class) if i[0] != '_']:
                ci = getattr(_class, p)
                if "<class 'apollo." in str(type(ci)):
                    _class_instance_names.append(p)
                    log.debug("{0:<{2}} = {1}".format(p, type(getattr(_class, p)), col1)) if verbose else None
                    idx = [_pfx, p] if _pfx else [p]
                    cdict['.'.join(idx)] = (_class.__repr__())
                elif "<type 'instancemethod" in str(type(getattr(_class, p))):
                    mdict[p] = (_class.__class__.__name__, _class.__class__.__module__)
            return _class_instance_names

        def __list_methods(_parent_class, _class_instance_names, _pfx=''):
            for cin in _class_instance_names:
                ci = getattr(_parent_class, cin)
                properties = []
                log.debug("CI={0}".format(ci)) if verbose else None
                plist = [i for i in dir(ci) if i[0] != '_']
                log.debug("plist={0}".format(plist)) if verbose else None
                for p in plist:
                    log.debug(p) if verbose else None
                    try:
                        pi = getattr(ci, p)
                        if "<type 'instancemethod" in str(type(pi)):
                            log.debug("{0:<{2}} = {1}".format(p, type(pi), col1)) if verbose else None
                            if hasattr(pi, 'decorator'):
                                properties.append(p)
                                idx = [_pfx, cin, p] if _pfx else [cin, p]
                                mdict['.'.join(idx)] = (ci.__class__.__name__, ci.__class__.__module__)
                    except RuntimeError:
                        log.debug("RTE: {0}".format(p)) if verbose else None
                        pass
                try:
                    if ci.__class__.__name__ in ['Equipment', 'Traffic']:
                        __list_methods(ci, __list_subclass_names(ci, cin), _pfx=cin)
                except RuntimeError:
                    log.debug("CI2={0}".format(ci)) if verbose else None
                    pass
            return

        # Gather class & method info
        sc = __list_subclass_names(self)
        __list_methods(self, sc)

        # Display
        log.debug("{0} = {1}".format('-' * col1, '-' * col2))
        log.debug("{0:<{2}} = {1}".format('Product Class Members', 'Class Info', col1))
        log.debug("{0} = {1}".format('-' * col1, '-' * col2))
        for k in sorted(cdict.keys()):
            log.debug("{0:<{2}} = {1}".format(k, cdict[k], col1))

        log.debug("{0} = {1}".format('-' * col1, '-' * col2))
        log.debug("{0:<{2}} = {1}".format('Apollo Step method', 'Class, Module', col1))
        log.debug("{0} = {1}".format('-' * col1, '-' * col2))
        for k in sorted(mdict.keys()):
            log.debug("{0:<{2}} = {1}".format(k, mdict[k], col1))
        return