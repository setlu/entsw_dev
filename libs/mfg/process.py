"""
Process
"""

# Python
# ------
import sys
import logging
import os
import operator

# Apollo
# ------
import apollo.libs.lib as aplib
from apollo.libs import cesiumlib
from apollo.engine import apexceptions

# BU Libs
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils
import apollo.scripts.entsw.libs.utils.cnf_utils as cnf_utils

from ..utils.common_utils import func_details


__title__ = "Mfg Process General Module"
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
cesium_srvc_retry = common_utils.cesium_srvc_retry


class Process(object):
    SCAN, BOOT, DB = 'scan', 'boot', 'db'

    def __init__(self, mode_mgr, ud):
        log.info(self.__repr__())
        self._ud = ud
        if self._ud.__class__.__name__ != 'UutDescriptor':
            raise Exception("Class (UutDescriptor) dependency has not been properly initialized.")
        self._mode_mgr = mode_mgr
        if self._mode_mgr.__class__.__name__ != 'ModeManager':
            raise Exception("Class (ModeManager) dependency has not been properly initialized.")
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def uut_discover(self, method, **kwargs):
        if method.lower() == self.SCAN:
            required_items = kwargs.get('required_items')
            optional_items = kwargs.get('optional_items')
            prepopulated_items = kwargs.get('prepopulated_items')
            required_items = [required_items] if not isinstance(required_items, list) else required_items
            optional_items = [optional_items] if not isinstance(optional_items, list) else optional_items
            prepopulated_items = [prepopulated_items] if not isinstance(prepopulated_items, list) else prepopulated_items

            # Scan first item to get selection which loads the product definition
            first_item = required_items[0]
            sd1 = self.__uut_scan_info(first_item, None)
            self._ud.product_selection = sd1.get(first_item)

            # Scan remaining required + optional items based on product
            sd = self.__uut_scan_info(required_items[1:], optional_items)
            self._ud.uut_config.update(sd)

            # Get and/or Scan prepopulated items
            self.__uut_process_prepopulated_info(prepopulated_items)

        elif method.lower() == self.BOOT:
            return self.__uut_boot_retrieve_info(**kwargs)

        elif method.lower() == self.DB:
            return self.__uut_rd_database_info(**kwargs)

        else:
            raise Exception("Unknown UUT discovery method.")

        return aplib.PASS

    @apollo_step
    def uut_scan(self, **kwargs):
        required_items = kwargs.get('required_items')
        optional_items = kwargs.get('optional_items')
        required_items = [required_items] if not isinstance(required_items, list) else required_items
        optional_items = [optional_items] if not isinstance(optional_items, list) else optional_items
        sd = self.__uut_scan_info(required_items, optional_items)
        self._ud.uut_config.update(sd)
        return aplib.PASS

    @apollo_step
    def auto_select_product(self, **kwargs):
        return self.uut_discover(self.BOOT, **kwargs)

    @apollo_step
    def cache_ud_data(self):
        if not self._ud.apollo_go:
            return
        key = '{0}_uut_descriptor'.format(aplib.get_my_container_key())
        log.debug("UutDescriptor caching to key={0}".format(key))
        aplib.cache_data(key, self._ud.convert_to_dict())
        return aplib.PASS

    @apollo_step
    def add_tst(self):
        sernum = self._ud.puid.sernum
        uut_type = self._ud.puid.uut_type
        area = self._ud.test_area
        container = self._ud.container_name
        backflush_status = self._ud.uut_config.get('backflush_status', 'NO')
        tst_data = {'uut_type': uut_type, 'test_area': area, 'test_container': container, 'backflush_status': backflush_status}
        # For debug: log.debug("Preliminary TST Data: {0}".format(tst_data))

        # TST Additional Data - Mapping to uut_config
        # Other Items that can be present during any part of the EntSw end-to-end test process.
        # The tst_field_map is a list of 2-element tuples: (<uut_config item name>, <tst field name>)
        #  Note1: For nested items in uut_config, use a list as the <uut_config item name> to drill down to the value.
        #  Note2: The map list order is important since subsequent items can override previous items of the same TST
        #         field name (e.g. 'diagrev' --> if a diag image does not exist then linux image will be the last
        #         update as diag image will be skipped IF empty; if diag image is not empty then it will be the last
        #         update and used for TST).
        tst_field_map = {
            'SWITCH':
                [('MOTHERBOARD_ASSEMBLY_NUM', 'board_part_num'),
                 ('MOTHERBOARD_REVISION_NUM', 'board_hw_rev'),
                 # ('SYSTEM_SERIAL_NUM', 'parent_serial_number'),
                 ('MODEL_NUM', 'basepid'),
                 ('VERSION_ID', 'version_id'),
                 ('CFG_MODEL_NUM', 'vendpartnum'),
                 ('TAN_NUM', 'tan'),
                 ('TAN_REVISION_NUMBER', 'tan_hw_rev'),
                 (['linux', 'image'], 'diagrev'),
                 (['diag', 'image'], 'diagrev'),
                 ('ios_pid', 'swrev'),
                 ('CLEI_CODE_NUMBER', 'clei'),
                 ('ECI_CODE_NUMBER', 'eci', int),
                 ('coo', 'coo'),
                 ('QUACK_LABEL_SN', 'labelnum'),
                 ('RFID_TID', 'testr1'),
                 ('DEVIATION_NUM', 'deviation'),
                 ('lineid', 'lineid', int),
                 ],
            'MODULAR':
                [('MOTHERBOARD_ASSEMBLY_NUM', 'board_part_num'),
                 ('MOTHERBOARD_REVISION_NUM', 'board_hw_rev'),
                 # ('SYSTEM_SERIAL_NUM', 'parent_serial_number'),
                 ('MODEL_NUM', 'basepid'),
                 ('VERSION_ID', 'version_id'),
                 ('CFG_MODEL_NUM', 'vendpartnum'),
                 ('TAN_NUM', 'tan'),
                 ('TAN_REVISION_NUMBER', 'tan_hw_rev'),
                 (['diag', 'image'], 'diagrev'),
                 ('ios_pid', 'swrev'),
                 ('CLEI_CODE_NUMBER', 'clei'),
                 ('ECI_CODE_NUMBER', 'eci', int),
                 ('coo', 'coo'),
                 ('QUACK_LABEL_SN', 'labelnum'),
                 ('RFID_TID', 'testr1'),
                 ('DEVIATION_NUM', 'deviation'),
                 ('lineid', 'lineid', int),
                 ],
            'PERIPH':
                [('PCAPN', 'board_part_num'), ('PCAREV', 'board_hw_rev'),
                 ('VPN', 'tan'), ('VID', 'tan_hw_rev'),
                 ('CLEI', 'clei'), ('ECI', 'eci', int), ('coo', 'coo'),
                 (['diag', 'image'], 'diagrev'),
                 ('DEVIATION_NUM', 'deviation'), ('lineid', 'lineid', int),
                 ],
            'unknown': [],
        }

        # ---------------------
        # TST Data - Additional
        # ---------------------
        log.info("Mapping TST data types...")
        tst_field_inverse_map = dict()

        for item in tst_field_map.get(self._ud.category, []):

            # item[0] "script field name" (can be str, list) --> must be only str
            if isinstance(item[0], str):
                # ONLY add it to the TST data if it is NOT empty (i.e. in the uut_config).
                if self._ud.uut_config.get(item[0], None):
                    # Type cast if a type is provided.
                    if len(item) == 2:
                        tst_data[item[1]] = self._ud.uut_config[item[0]]
                        tst_field_inverse_map[item[1]] = item[0]
                    elif len(item) == 3:
                        try:
                            tst_data[item[1]] = item[2](self._ud.uut_config[item[0]])
                            tst_field_inverse_map[item[1]] = item[0]
                        except NameError:
                            log.warning("NameError with {0}".format(item[2]))
                            log.warning("The TST item '{0}' will NOT be added.".format(item[1]))

            elif isinstance(item[0], list):
                try:
                    uut_config_value = reduce(operator.getitem, item[0], self._ud.uut_config)
                    if uut_config_value:
                        tst_data[item[1]] = uut_config_value
                        tst_field_inverse_map[item[1]] = '_'.join(item[0]).upper()
                except KeyError:
                    log.warning("List key: {0} cannot reduce.".format(item[0]))
                    pass
            else:
                log.warning("Unknown map item type.")

            # Ensure tst_data[item[1]] is ONLY a str or int
            if tst_data.get(item[1], None) and (
                not isinstance(tst_data[item[1]], str) and not isinstance(tst_data[item[1]], int)):
                log.warning("TST data item '{0}' value needs default converting to str.".format(item[1]))
                try:
                    tmp_str = str(tst_data[item[1]])
                except ValueError as e:
                    log.error("Cannot process TST data value into default str.")
                    log.error(e)
                    tmp_str = 'FATAL:CANNOT CONVERT TST DATA TO STR.'
                finally:
                    tst_data[item[1]] = tmp_str

        # TST Data Check
        log.info("Cleaning up TST data...")
        log.debug("Note: Ensure any corrupted data from the TVL/diags is removed.")
        for param, value in tst_data.items():
            standard_param_name = tst_field_inverse_map.get(param, 'UNKNOWN')
            if standard_param_name != 'UNKNOWN':
                if not common_utils.validate_entry(standard_param_name, value, silent=True):
                    log.warning("{0:<30}  {1:<20} = '{2:<30}'  INVALID (will be removed from TST).".
                                format(standard_param_name, param, value))
                    tst_data.pop(param)
                else:
                    log.debug("{0:<30}  {1:<20} = '{2:<30}'  VALID.".format(standard_param_name, param, value))
            else:
                log.debug("{0:<30}  {1:<20} = '{2:<30}'  N/A.".format(standard_param_name, param, value))

        # Display Pre-Seq TST Record Info to be recorded
        fam = aplib.get_machine_config().get('machineFamily', 'apollostg')
        db = 'PROD' if 'apolloprod' in fam else 'STAGE'
        log.info("-" * 120)
        log.info("TST Data (DB={0} Mode={1}) for {2}".format(db, aplib.get_apollo_mode(), self._ud.container_key))
        log.info("-" * 120)
        log.info("{0:<30} {1:<20} : {2}".format('UUT S/N', '(sernum)', sernum))
        log.info("{0:<30} {1:<20} : {2}".format('PID', '(uut_type)', uut_type))
        log.info("{0:<30} {1:<20} : {2}".format('Area', '(test_area)', area))
        log.info("{0:<30} {1:<20} : {2}".format('Container', '(test_container)', container))
        for item in tst_field_map.get(self._ud.category, []):
            if item[1] in tst_data:
                log.debug("{0:<30} {1:<20} : {2:<50} ({3})".format(item[0], '(' + item[1] + ')', tst_data[item[1]],
                                                                   type(tst_data[item[1]])))

        # Sanity check
        if not sernum:
            err_msg = "*** Serial Number is missing! ***"
            log.error(err_msg)
            raise Exception(err_msg)

        # *******************
        # Add the TST Record!
        # *******************
        aplib.add_tst_data(sernum, **tst_data)

        self._ud.uut_config.update({'tst': {'serial_number': sernum, 'uut_type': uut_type, 'container': container, 'area': area}})
        return aplib.PASS

    @apollo_step
    def area_check(self, **kwargs):
        """ AreaCheck test for scanned serial number
        :param (dict) kwargs:
                (str) previous_area: Area to check for the PASS record in TST
                                     If not provided then look at the process_flow from uut_config to
                                     determine previous area.
                (tuple) previous_uuttype_and_sn_source: Form of (uuttype param name, sn param name)
                                     IF different from current area.
                                     Ex. ('MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_SERIAL_NUM')
                                     Use this when a sub-assembly is promoted to a higher level in the current
                                     test area; therefore, need to know what previous data to do areacheck against.
        :return (str): aplib.PASS/FAIL
        """
        @cesium_srvc_retry
        def verify_area(prev_sernum, prev_uuttype, prev_area, bellcore, timeframe):
            return cesiumlib.verify_area(serial_number=prev_sernum,
                                         uut_type=prev_uuttype,
                                         area=prev_area,
                                         bellcore=bellcore,
                                         timeframe=timeframe)

        # Inputs
        previous_area = kwargs.get('previous_area', None)
        previous_uuttype_and_sn_source = kwargs.get('previous_uuttype_and_sn_source', None)
        override = kwargs.get('override', False)
        process_flow = kwargs.get('process_flow', self._ud.uut_config.get('process_flow', None))
        process_flow_alt = kwargs.get('process_flow_alt', self._ud.uut_config.get('process_flow_alt', None))

        try:
            test_info = aplib.apdicts.test_info
            # log.debug("test_info: {0}".format(test_info))
            sernum = test_info.serial_number
            uuttype = test_info.test_data('uut_type', serial_number=sernum)
            area = test_info.test_area
            mode = aplib.get_apollo_mode()

            # Check against process flow
            if process_flow:
                if area in process_flow:
                    current_area_index = process_flow.index(area)
                    if current_area_index == 0:
                        log.info("No previous test area based on process flow (previous_area input is ignored).")
                        log.info("Areacheck is not possible.")
                        return aplib.PASS
                    if not previous_area:
                        previous_area = process_flow[current_area_index - 1]
                        log.debug("Got previous area from process_flow: {0}".format(previous_area))
                    else:
                        log.debug("Previous test area provided explicitly.")
                elif process_flow_alt and area in process_flow_alt:
                    current_area_index = process_flow_alt.index(area)
                    if current_area_index == 0:
                        log.info("No previous test area based on alternative process flow (previous_area input is ignored).")
                        log.info("Areacheck is not possible.")
                        return aplib.PASS
                    if not previous_area:
                        previous_area = process_flow_alt[current_area_index - 1]
                        log.debug("Got previous area from process_flow_alt: {0}".format(previous_area))
                    else:
                        log.debug("Previous test area provided explicitly.")
                else:
                    log.error("A process flow exists; however, the current area {0} is NOT in the list!".format(area))
                    log.error("Please correct the product definition.")
                    return aplib.FAIL, "Missing test area in process flow list."

            # Get Previous Area UUT data
            if previous_uuttype_and_sn_source:
                # Use this when needing uuttype & sn from a source other than the current test_info source.
                # Our source will always be the uut_config params.
                previous_uuttype = self._ud.uut_config[previous_uuttype_and_sn_source[0]]
                previous_sernum = self._ud.uut_config[previous_uuttype_and_sn_source[1]]
            else:
                # If previous area uuttype & sernum is NOT used then assume they are the same as the current new area.
                previous_uuttype = uuttype
                previous_sernum = sernum

            # Check that the areas are valid names
            if not aplib.valid_areaname(area):
                errmsg = "The area name '{0}' is invalid.".format(area)
                log.error(errmsg)
                return aplib.FAIL, errmsg
            if previous_area and not aplib.valid_areaname(previous_area):
                errmsg = "The previous area name '{0}' is invalid.".format(previous_area)
                log.error(errmsg)
                return aplib.FAIL, errmsg

            # Display
            log.info("AREACHECK")
            log.info("Current Area       = {0}".format(area))
            log.info("Current UUT Type   = {0}".format(uuttype))
            log.info("Current S/N        = {0}".format(sernum))
            log.info("Previous Area      = {0}".format(previous_area))
            log.info("Previous UUT Type  = {0}".format(previous_uuttype))
            log.info("Previous S/N       = {0}".format(previous_sernum))
            log.info("Mode               = {0}".format(mode))

            aplib.set_container_text('AREACHECK: Prev={0} Cur={1}'.format(previous_area, area))

            # Verify and Take Action
            if previous_area:
                verify_area(previous_sernum, previous_uuttype, previous_area, bellcore=False, timeframe='6m')
                log.info("AREACHECK GOOD!")
            else:
                # No previous area provided.
                if mode == aplib.MODE_PROD:
                    log.error("\r")
                    log.error("*" * 80)
                    log.error("AREACHECK BYPASS: NOT ALLOWED IN PRODUCTION!")
                    log.error("Previous area is unknown (i.e. 'None'), no area check to perform.")
                    log.error("Ensure a correct previous area is provided when performing an areacheck!")
                    log.error("*" * 80)
                    log.error("\r")
                    raise apexceptions.ApolloException('Areacheck missing previous area.')
                else:
                    log.warning("*" * 80)
                    log.warning("AREACHECK BYPASS: DEBUG MODE.")
                    log.warning("Previous area is unknown (i.e. 'None'), no area check to perform.")
                    log.warning("This is a provision for development/debug ONLY.")
                    log.warning("*" * 80)

        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.error('AREACHECK FAILED!')
            log.debug(e)
            if override:
                if aplib.ask_question("Areacheck Failure Override\n"
                                      "***WARNING: Not allowed for production!**\n"
                                      "Password:") == 'cisco':
                    return aplib.PASS
            elif mode == aplib.MODE_DEBUG:
                log.warning("*" * 80)
                log.warning("AREACHECK BYPASS: DEBUG MODE.")
                log.warning("Previous area is known, however areacheck has failed.")
                log.warning("The failure will be ignored while in DEBUG mode.")
                log.warning("This is a provision for development/debug ONLY.")
                log.warning("*" * 80)
                return aplib.PASS

            return aplib.FAIL, "Areacheck failure."

        return aplib.PASS

    @apollo_step
    def get_serial_num(self, **kwargs):
        """ Get a Serial NUmber
        Get the serial number for any assembly.
        If this is a parent assembly requesting the s/n, then a check must occur for its child serial numbers to ensure
        they have not already been assigned to a previous parent serial number.

        :param kwargs:
               sernum_item:        Parameter name of s/n to obtain (e.g. SYSTEM_SERIAL_NUM)
               child_sernum_item:  Parameter name of child s/n  (e.g. MOTHERBOARD_SERIAL_NUM)
               child_pid_item:     Parameter name of BasePID/PID/CPN associated with the child s/n
                                   (e.g. MOTHERBOARD_ASSEMBLY_NUM)
        :return:
        """
        aplib.set_container_text('RETRIEVE SERIAL NUMBER')

        # Inputs
        sernum_item = kwargs.get('sernum_item', None)
        child_sernum_item = kwargs.get('child_sernum_item', None)
        child_pid_item = kwargs.get('child_pid_item', None)

        # Check for previous sernum based on child_sernum
        sernum = None
        if child_sernum_item and child_pid_item:
            sernum = common_utils.get_parent_sernum(self._ud.uut_config.get(child_sernum_item, None),
                                                    self._ud.uut_config.get(child_pid_item, None))

        # If no previous sernum (or no parent based on child if exists) then generate a new one!
        if not sernum:
            sernum = common_utils.generate_cisco_sernum(sernum_item=sernum_item,
                                                        uut_category=self._ud.category)
        else:
            log.debug("A previous parent S/N from genealogy will be used.")

        self._ud.uut_config[sernum_item] = sernum

        return aplib.PASS


    # Geneaology --------------------------
    @apollo_step
    def register_genealogy(self, **kwargs):
        """ Register Geneaology
        Register a parent/child relationship.
        This function has the flexibility to register a list of both required and optional child items based on
        the loaded uut_config.
        :menu: (enable=True, name=REG GENEALOGY, section=Config, num=1,  args={'menu_entry': True})
        :param (dict) kwargs: parent_sernum_item (str): Index name of parent s/n.
                              parent_pid_item (str): Index name of parent PID/CPN.
                              child_sernum_items (str or list): Index name(s) of children s/n.
                              child_pid_items (str or list): Index name(s) of children PIDs/CPNs.
                              Additionally, an optional list can be supplied which is filtered against the
                              uut_config from the product_definition.
                              optional_child_sernum_items (str or list): Optional index name(s) of children s/n.
                              optional_child_pid_items (str or list): Optional index name(s) of children PIDs/CPNs.
        :return (str): aplib.PASS/FAIL
        """

        @cesium_srvc_retry
        def assemble_genealogy(parent_serial_number, parent_product_id, child_serial_number, child_product_id,
                               child_location=None):
            log.debug("Parent SN, PID       : {0}, {1}".format(parent_serial_number, parent_product_id))
            log.debug("Child  SN, PID (Loc) : {0}, {1} ({2})".format(child_serial_number, child_product_id,
                                                                     child_location))
            return cesiumlib.assemble_genealogy(parent_serial_number=parent_serial_number,
                                                parent_product_id=parent_product_id,
                                                child_serial_number=child_serial_number,
                                                child_product_id=child_product_id,
                                                child_location=child_location)

        # Process input params
        psn_key = kwargs.get('parent_sernum_item', None)
        ppid_key = kwargs.get('parent_pid_item', None)
        csns_keys = kwargs.get('child_sernum_items', [])
        cpids_keys = kwargs.get('child_pid_items', [])
        ocsns_keys = kwargs.get('optional_child_sernum_items', [])
        ocpids_keys = kwargs.get('optional_child_pid_items', [])
        menu_entry = kwargs.get('menu_entry', False)

        if not menu_entry:
            # Pull parent from uut_config
            psn = self._ud.uut_config.get(psn_key, None)
            ppid = self._ud.uut_config.get(ppid_key, None)

            # Ensure these are lists only!
            csns_keys = [csns_keys] if not isinstance(csns_keys, list) else csns_keys
            cpids_keys = [cpids_keys] if not isinstance(cpids_keys, list) else cpids_keys
            ocsns_keys = [ocsns_keys] if not isinstance(ocsns_keys, list) else ocsns_keys
            ocpids_keys = [ocpids_keys] if not isinstance(ocpids_keys, list) else ocpids_keys

            # Combine child lists with optional lists.
            if ocsns_keys and ocpids_keys:
                log.debug("Gathering optional items applicable to the UUT...")
                fcsns_keys = self._ud.get_filtered_keys(allowed_params=ocsns_keys)
                if fcsns_keys:
                    csns_keys += fcsns_keys
                fcpids_keys = self._ud.get_filtered_keys(allowed_params=ocpids_keys)
                if fcpids_keys:
                    cpids_keys += fcpids_keys

            # Display
            log.debug("Parent SN       : {}".format(psn))
            log.debug("Parent PID      : {}".format(ppid))
            log.debug("Child SN items  : {}".format(csns_keys))
            log.debug("Child PID items : {}".format(cpids_keys))

            # Sanity check
            if not psn or not ppid:
                errmsg = "Parent data incomplete; CANNOT register genealogy."
                log.error(errmsg)
                return aplib.FAIL, errmsg
            if not csns_keys or not cpids_keys:
                if not ocsns_keys and not ocpids_keys:
                    errmsg = "Child data items incomplete; CANNOT register genealogy."
                    log.error(errmsg)
                    return aplib.FAIL, errmsg
                else:
                    log.debug("All child data items (required & optional) are empty; nothing to do.")
                    return aplib.PASS
            if len(csns_keys) != len(cpids_keys):
                errmsg = "Child data S/N and PID items do not match up, check product_definition; CANNOT register genealogy."
                log.error(errmsg)
                return aplib.FAIL, errmsg
        else:
            csns_keys = ['CHILD_SN']
            cpids_keys = ['CHILD_PID']

        # Loop on child list.
        for count, csn_key, cpid_key in zip(range(1, len(csns_keys) + 1), csns_keys, cpids_keys):
            if not menu_entry:
                csn = self._ud.uut_config[csn_key]
                cpid = self._ud.uut_config[cpid_key]
                log.debug("Child S/N = {0}".format(csn))
                log.debug("Child PID = {0}".format(cpid))
                if not csn or not cpid:
                    errmsg = "Child #{0} data S/N and/or PID is incomplete; CANNOT register genealogy.".format(
                        count)
                    log.error(errmsg)
                    return aplib.FAIL, errmsg
            else:
                psn, ppid, csn, cpid = common_utils.enter_parent_child(desc='REG')

            try:
                assemble_genealogy(parent_serial_number=psn,
                                   parent_product_id=ppid,
                                   child_serial_number=csn,
                                   child_product_id=cpid)
                log.debug("Done for the child #{0}.".format(count))
            except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
                log.error(e)
                return aplib.FAIL, e.message

        log.debug("Genealogy registration done.")
        return aplib.PASS

    @apollo_step
    def get_genealogy(self, **kwargs):
        """ Get Geneaology
        Get a parent/child relationship(s).
        :menu: (enable=True, name=GET GENEALOGY, section=Config, num=1,  args={'menu_entry': True})
        :param (dict) kwargs: parent_sernum_item (str): Index name of parent s/n.
                              parent_pid_item (str): Index name of parent PID/CPN.
                              level (int): Optional level (up to 10).
        :return (str): aplib.PASS/FAIL
        """
        @cesium_srvc_retry
        def get_genealogy(parent_serial_number, parent_product_id, level=1):
            log.debug("Parent SN, PID       : {0}, {1}".format(parent_serial_number, parent_product_id))
            return cesiumlib.get_genealogy(serial_number=parent_serial_number,
                                           product_id=parent_product_id,
                                           level=level)

        # Process input params
        psn_key = kwargs.get('parent_sernum_item', None)
        ppid_key = kwargs.get('parent_pid_item', None)
        level = kwargs.get('level', 1)
        menu_entry = kwargs.get('menu_entry', False)

        if not menu_entry:
            # Pull parent from uut_config
            psn = self._ud.uut_config.get(psn_key, None)
            ppid = self._ud.uut_config.get(ppid_key, None)
        else:
            psn, ppid = common_utils.enter_parent_child(desc='GET', names=['Parent'])

        # Sanity check
        if not psn or not ppid:
            errmsg = "Parent data incomplete; CANNOT get genealogy."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Display
        log.debug("Parent SN       : {}".format(psn))
        log.debug("Parent PID      : {}".format(ppid))

        # Perform the service
        try:
            g_dict = get_genealogy(parent_serial_number=psn, parent_product_id=ppid, level=level)
        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.error(e)
            return aplib.FAIL, e.message

        log.debug(g_dict)
        log.debug("Genealogy retrieval done.")
        return aplib.PASS

    @apollo_step
    def delete_genealogy(self, **kwargs):
        """ Delete Geneaology
        Delete  parent/child relationship(s).
        :menu: (enable=True, name=DEL GENEALOGY, section=Config, num=1,  args={'menu_entry': True})
        :param (dict) kwargs: parent_sernum_item (str): Index name of parent s/n.
                              parent_pid_item (str): Index name of parent PID/CPN.
                              level (int): Optional level (up to 10).
        :return (str): aplib.PASS/FAIL
        """

        @cesium_srvc_retry
        def disassemble_genealogy(parent_serial_number, parent_product_id, child_serial_number, child_product_id,
                                  child_location=None):
            log.debug("Parent SN, PID       : {0}, {1}".format(parent_serial_number, parent_product_id))
            log.debug(
                "Child SN, PID        : {0}, {1} ({2})".format(child_serial_number, child_product_id, child_location))
            return cesiumlib.disassemble_genealogy(parent_serial_number=parent_serial_number,
                                                   parent_product_id=parent_product_id,
                                                   child_serial_number=child_serial_number,
                                                   child_product_id=child_product_id,
                                                   child_location=child_location)

        def disassemble_complete_genealogy(parent_serial_number, parent_product_id):
            log.debug("Parent SN, PID       : {0}, {1}".format(parent_serial_number, parent_product_id))
            return cesiumlib.disassemble_complete_genealogy(parent_serial_number=parent_serial_number,
                                                            parent_product_id=parent_product_id)


        # Process input params
        psn_key = kwargs.get('parent_sernum_item', None)
        ppid_key = kwargs.get('parent_pid_item', None)
        csn_key = kwargs.get('child_sernum_item', None)
        cpid_key = kwargs.get('child_pid_item', None)
        menu_entry = kwargs.get('menu_entry', False)

        if not menu_entry:
            # Pull parent from uut_config
            psn = self._ud.uut_config.get(psn_key, None)
            ppid = self._ud.uut_config.get(ppid_key, None)
            csn = self._ud.uut_config.get(csn_key, None)
            cpid = self._ud.uut_config.get(cpid_key, None)

            # Sanity check
            if not psn or not ppid:
                errmsg = "Parent data incomplete; CANNOT delete genealogy."
                log.error(errmsg)
                return aplib.FAIL, errmsg
        else:
            psn, ppid, csn, cpid = common_utils.enter_parent_child(desc='DEL')

        # Perform the service
        try:
            if csn and cpid:
                g_dict = disassemble_genealogy(parent_serial_number=psn, parent_product_id=ppid,
                                               child_serial_number=csn, child_product_id=cpid)
            else:
                g_dict = disassemble_complete_genealogy(parent_serial_number=psn, parent_product_id=ppid)
        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.error(e)
            return aplib.FAIL, e.message

        log.debug(g_dict)
        log.debug("Genealogy delete done.")
        return aplib.PASS

    # MAC ----------------------------------
    @apollo_step
    def assign_verify_mac(self, **kwargs):
        """ Assign and/or Verify MAC
        If the UUT does have a MAC then validate that it is good; if it is NOT good, then generate a new one.
        If the UUT does NOT have a MAC then generate one.
        If we are in DEBUG mode and the UUT does have a MAC then skip the verify (don't care).
        If we are in DEBUG mode and the UUT does NOT have a MAC then generate a BA:DB:AD:xx:xx:xx one.
        :menu: (enable=True, name=MAC VERIFY, section=Config, num=1,  args={'include_debug': True})
        :menu: (enable=True, name=MAC FETCH, section=Config, num=1,  args={'include_debug': True, 'assign': True})
        :param kwargs:
               (bool) include_debug: If True perform MAC verify for debug mode.
               (bool) assign: Set True only for the testarea where MAC assignment is allowed.
                              All other downstream verification should set this to False.
        :return:
        """
        @cesium_srvc_retry
        def verify_mac(serial_number, uut_type, mac_start_address, mac_block_size):
            return cesiumlib.verify_mac(serial_number=serial_number,
                                        uut_type=uut_type,
                                        mac_start_address=mac_start_address,
                                        block_size=mac_block_size)

        # Inputs
        include_debug = kwargs.get('include_debug', False)
        assign = kwargs.get('assign', False)

        # Get properly associated data.
        # This is typically motherboard sernum & motherboard uut_type.
        # Note: Setting the ud.puid_keys = [...] will automatically update the ud.puid from uut_config.
        # Note2: The uut_config must already have been loaded.
        sernum = self._ud.puid.sernum
        uuttype = self._ud.puid.uut_type

        log.debug('MAC - SERIAL NUMBER and UUTTYPE')
        log.debug('{0:<30}:{1} (sernum)'.format(self._ud.puid_keys.sernum, sernum))
        log.debug('{0:<30}:{1} (uuttype)'.format(self._ud.puid_keys.uut_type, uuttype))
        # Sanity
        if not sernum or not uuttype:
            errmsg = "No S/N and/or PID data for MAC association.  Cannot continue!"
            log.error(errmsg)
            return aplib.FAIL, errmsg

        mac_good = False
        mode = aplib.get_apollo_mode()
        if 'MAC_ADDR' in self._ud.uut_config and common_utils.validate_mac_addr(self._ud.uut_config['MAC_ADDR']):
            mac = common_utils.convert_mac(self._ud.uut_config['MAC_ADDR'], '0x')
            block_size = int(self._ud.uut_config['MAC_BLOCK_SIZE'])
            log.info("UUT MAC Verify")
            log.info("-" * 50)
            log.info("S/N       = {0}".format(sernum))
            log.info("MAC Addr  = {0}".format(mac))
            log.info("MAC Block = {0}".format(block_size))
            log.info("Mode      = {0}".format(mode))

            aplib.set_container_text('MAC VERIFY: {0}'.format(mac))

            try:
                if mode != aplib.MODE_DEBUG or include_debug:
                    verify_mac(serial_number=sernum,
                               uut_type=uuttype,
                               mac_start_address=mac,
                               mac_block_size=block_size)
                else:
                    log.warning("MAC will NOT be validated while in DEBUG mode!")
                    log.warning(
                        "Since MAC validation was not included while in DEBUG mode, no new MAC assignment can occur.")
                    log.warning("MAC will be assumed good.")

                # Getting here means the verify_mac() did not throw an exception and the MAC is good; or in DEBUG mode.
                mac_good = True
                log.info("MAC GOOD!")

            except apexceptions.ApolloException as e:
                log.debug(e)
                log.warning("*" * 31)
                log.warning("*** MAC ADDR DID NOT VERIFY ***")
                log.warning("*" * 31)
                log.info("Re-assign a new MAC Addr.")

            finally:
                pass
        else:
            if 'MAC_ADDR' in self._ud.uut_config:
                log.info("MAC Addr is incorrectly formed or has bad value; generate a new one.")
                log.debug("MAC_ADDR = '{0}'".format(self._ud.uut_config['MAC_ADDR']))
            else:
                log.info("MAC Addr is undefined; generate a new one.")

        # Decide to retrieve a new MAC
        if not mac_good:

            if not assign:
                # This flag indicates the programming step has already occured upstream in the UUT process.
                # Offical MAC Assignment should only occur in one test area (PCBST).
                log.critical("=" * 60)
                log.critical("*** MAC is NOT verified and no new assignment is allowed. ***")
                log.critical("Check the process and check this UUT's MAC!")
                log.critical("MAC assignment is only done on the first station after ICT.")
                log.critical("Ensure that this UUT's MAC was not reprogrammed during debug.")
                log.critical("=" * 60)
                return aplib.FAIL, 'MAC did not verify and cannot assign a new one!'

            # Since generating a MAC is highly crucial, no retries attempted!
            try:
                log.debug("Generating a new MAC...")
                machine_config = aplib.get_machine_config()
                mac_group = 'T' if mode == aplib.MODE_DEBUG or machine_config.get('machineFamily',
                                                                                  'unknown') != 'apolloprod' else 'M'
                mac_block_size = int(self._ud.uut_config.get('MAC_BLOCK_SIZE', 0))
                if not mac_block_size:
                    msg = "MAC Block Size is indeterminant!  Cannot continue."
                    log.critical("=" * 60)
                    log.critical(msg)
                    log.critical("=" * 60)
                    return aplib.FAIL, msg
                log.debug("MAC Group = {0}".format(mac_group))
                mac, block_size = cesiumlib.generate_mac(serial_number=sernum,
                                                         uut_type=uuttype,
                                                         mac_group=mac_group,
                                                         block_size=mac_block_size)
            except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
                log.error(e)
                log.error("MAC generation FAILED!")
                log.error("Check the Cesium Services; cannot continue.")
                return aplib.FAIL, "MAC generation FAILED!"

            # Getting here means the generate_mac() did not throw an exception and a mac is created.
            # Note: A backup copy is created since PCAMAP activites could clear the MAC_ADDR setting
            #       prior to writting to the UUT flash/act2 space.
            self._ud.uut_config['MAC_ADDR'] = common_utils.convert_mac(mac, '6:')
            self._ud.uut_config['MAC_BLOCK_SIZE'] = str(block_size)
            self._ud.uut_config['new_mac_backup'] = (self._ud.uut_config['MAC_ADDR'], str(block_size))

            aplib.set_container_text('MAC VERIFY: {0}'.format(self._ud.uut_config['MAC_ADDR']))
            log.info("=" * 30)
            log.info("New MAC    = {0}".format(self._ud.uut_config['MAC_ADDR']))
            log.info("Block Size = {0}".format(self._ud.uut_config['MAC_BLOCK_SIZE']))
            if mode == aplib.MODE_DEBUG:
                log.warning("DEBUG Mode")
                log.warning("The generated MAC is NOT a valid Cisco Production MAC!")
            log.info("=" * 30)

        return aplib.PASS

    # Labels -------------------------------
    @apollo_step
    def verify_quack_label(self, **kwargs):
        """ Verify Quack Label

        NOTE: This label verification process requires 3 steps:
              1. Register label s/n at first functional sequence (BST)
              2. Confirm registration downstream early (ASSY)
              3. Verify label again late in process (i.e. DF site).

        :param (dict) kwargs:
                      (str) sn_key: Key of uut_config for UUT serial number associated with the quack label
                      (str) label_key: Key of uut_config for quack label s/n
        :return (str): aplib.PASS/FAIL
        """

        @cesium_srvc_retry
        def verify_quack_label(sernum, label_sernum):
            return cesiumlib.verify_quack_label(serial_number=sernum,
                                                quack_label_number=label_sernum)

        # Inputs
        quack_label_sn_key = kwargs.get('quack_label_sn_key', 'QUACK_LABEL_SN')
        quack_label_sn = self._ud.uut_config.get(quack_label_sn_key, None)

        # Get properly associated data.
        # This is typically motherboard sernum & motherboard uut_type.
        # Note: Setting the ud.puid_keys = [...] will automatically update the ud.puid from uut_config.
        # Note2: The uut_config must already have been loaded.
        sernum = self._ud.puid.sernum

        aplib.set_container_text('QUACK LABEL VERIFY: {0}'.format(quack_label_sn))
        log.info('STEP: Quack label verify.')
        log.debug("{0:<25} : {1}".format(self._ud.puid_key.sernum, sernum))
        log.debug("{0:<25} : {1}".format(quack_label_sn_key, quack_label_sn))

        if not quack_label_sn:
            errmsg = "Quack Label S/N is MISSING!"
            log.error(errmsg)
            return aplib.FAIL, errmsg

        try:
            verify_quack_label(sernum, quack_label_sn)
        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.debug(e)
            return aplib.FAIL, e.message

        return aplib.PASS

    # CMPD ---------------------------------
    @apollo_step
    def load_cmpd_to_uut(self, **kwargs):
        """Load CMPD Table to UUT

        This loads the 'PROGRAMMING' CMPD template to the uut_config.

        Note1: description = 'SPROM' as default.
        Note2: password_family = 'dsbu' is used for C2K/C3K (C9200/C9300)
                               = 'cat4k' is used for C4K/C9400

        :menu: (enable=True, name=LOAD CMPD to UUT, section=Config, num=1,  args={'menu': True})
        :return:
        """
        def __load_cmpd_to_uut_config(cmpd_types, cmpd_values, tlv_style=False):

            def __print_status():
                if key in self._ud.uut_config:
                    if self._ud.uut_config[key] != value:
                        log.debug("UPDATED   : {0:<30} = {1}   (old={2})".format(key, value, self._ud.uut_config[key]))
                    else:
                        log.debug("NO CHANGE : {0:<30} = {1}".format(key, value))
                else:
                    log.debug("NEW       : {0:<30} = {1}".format(key, value))
                return

            log.debug("Updating uut_config with CMPD data...")
            log.debug("CMPD data has TLV style keys.") if tlv_style else None
            for key, value in zip(cmpd_types, cmpd_values):
                if "SKIP" not in value and "IGNORE" not in value and 'NONE' not in value:
                    if not tlv_style:
                        # Legacy style
                        __print_status()
                        self._ud.uut_config[key] = value
                    else:
                        # TLV style
                        tlv_key = key
                        key = self._ud.tlv_map.get(tlv_key, (None, None))[1]
                        if key:
                            __print_status()
                            log.debug("          : {0}".format(tlv_key))
                            self._ud.uut_config[key] = value
                        else:
                            log.debug("NO KEY MAP: {1:<30} = {2}".format(key, tlv_key, value))

            return

        strict = kwargs.get('strict', True)
        kwargs['eco_type'] = self._ud.PRGM
        cmpd_types, cmpd_values, _ = self.__fetch_cmpd(**kwargs)

        if not cmpd_types:
            if not strict:
                log.warning("CMPD types were not available; however, CMPD programming is NOT strictly enforced.")
                log.warning("This activity will be SKIPPED.")
                return aplib.SKIPPED
            else:
                msg = "Cannot PROGRAM UUT since the CMPD types are not available."
                log.error(msg)
                return aplib.FAIL, msg

        # Move CMPD data to UUT Config
        cmpd_tlv_style = kwargs.get('cmpd_tlv_style', self._ud.uut_config.get('cmpd', {}).get('tlv_style', False))
        __load_cmpd_to_uut_config(cmpd_types, cmpd_values, cmpd_tlv_style)
        return aplib.PASS

    @apollo_step
    def fetch_cmpd_fr_db(self, **kwargs):
        """ Fetch CMPD record
        :menu: (enable=True, name=FETCH CMPD, section=Config, num=1,  args={'menu': True})
        :param kwargs:
        :return:
        """
        t, _, _ = self.__fetch_cmpd(**kwargs)
        if not t:
            return aplib.FAIL, 'CMPD fetch.'
        return aplib.PASS

    @apollo_step
    def verify_cmpd(self, **kwargs):
        """ Verify CMPD
         Use this to confirm UUT cookie data (aka flash/tlv params) are correct for the revision & deviation of the product
         being built.
        :menu: (enable=True, name=VERIFY CMPD, section=Config, num=1,  args={'menu': True})
        :param (**dict) kwargs:
                        strict: SKIP or FAIL step
                        skip_value:
                        cmpd_description:
                        password_family:
                        test_site:
                        previous_area:
                        eco_deviation_key:
                        eco_type: PROGRAMMING, VERIFICATION
        :return:
        """
        @cesium_srvc_retry(max_attempts=2)
        def verify_cmpd(uut_type, **kwargs):
            return cesiumlib.verify_cmpd(uut_type=uut_type, **kwargs)

        # Setup defaults
        strict = kwargs.get('strict', True)
        skip_value = kwargs.get('skip_value', 'SKIP SPROM CHECK')

        cmpd_types, cmpd_values, cmpd_params = self.__fetch_cmpd(**kwargs)  # future params: template_type='VERIFICATION', duplicates='LATEST'
        area = cmpd_params.get('area')

        if not cmpd_params.get('eco_deviation_number'):
            if not strict:
                log.warning("ECO Number for CMPD Verification not found.")
                log.warning("CMPD Verification is NOT strictly enforced so this activity will be skipped.")
                return aplib.SKIPPED
            else:
                log.error("ECO Number for CMPD Verification NOT found.")
                log.error("Since no ECO/Deviation number exists for the VERIFICATION template in area {0},".format(area))
                log.error("this step will fail.  Please check CMPD database and ECO manifest in product definition.")
                return aplib.FAIL, "ECO Number for CMPD Verification not found."

        # STEP 1: Get CMPD Types that can be Verified
        # -------------------------------------------
        # Note: CMPD "Record Function": PROGRAMMING vs. VERIFICATION entries can be different and have different
        #       ECO/Deviation numbers. No method for getting CMPD Items in the VERIFICATION template!
        #       Solution: use a predefined list (put in product definition).
        # TODO: Ticket #5852 need resolution
        #
        if not cmpd_types:
            cmpd_types_dict = self.get_cmpd_types_dict_from_manifest()
            cmpd_types = self.get_cmpd_types_by_area(cmpd_types_dict, area)

        cmpd_type_len = len(cmpd_types) if cmpd_types else 0
        if cmpd_type_len == 0:
            log.error("CMPD types are empty; cannot verify!")
            return aplib.FAIL, "CMPD types are empty"
        log.debug("CMPD Types count = {0}".format(cmpd_type_len))

        # STEP 2: Get values we want to verify against CMPD
        # -------------------------------------------------
        uut_types = self._ud.get_flash_params().keys()
        cmpd_values = [self._ud.uut_config.get(i, None) for i in cmpd_types]
        log.debug("CMPD Types  = {0}".format(cmpd_types))
        log.debug("CMPD Values = {0}".format(cmpd_values))
        # Show column comparison: UUT vs. CMPD
        log.debug("{0:<40}  {1:<40}  {2:<40}".format('UUT Params', 'CMPD Types', 'UUT Param Value'))
        log.debug("{0:<40}  {1:<40}  {2:<40}".format('-' * 40, '-' * 40, '-' * 40))
        for i in list(set(uut_types) | set(cmpd_types)):
            left = i if i in uut_types else '.'
            right = i if i in cmpd_types else '.'
            log.debug("{0:<40}  {1:<40}  {2:<40}".format(left, right,
                                                         self._ud.uut_config.get(right, '<missing>') if right != '.' else ''))

        # STEP 3: Verify CMPD Values against the Types
        # ---------------------------------------------
        # The UUT Config space will contain more items than the CMPD record defines; therefore we must determine
        # the list prior to verify (i.e. STEP 1).
        # IMPORTANT: The cmpd_types_list MUST have the same order as the DB record!!!
        #            Of course the cmpd_values_list MUST have 1:1 correspondence with cmpd_types_list.
        # ITEMS not in CMPD and not in the product definition should be removed at the final test station.
        try:
            cmpd_result = verify_cmpd(skip_value=skip_value,
                                      cmpd_value_list=cmpd_values,
                                      cmpd_type_list=cmpd_types,
                                      **cmpd_params)
            log.debug("CMPD Result = {0}".format(cmpd_result))
            ret = aplib.PASS

        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.error(e)
            ret = aplib.FAIL, e.message

        log.debug("CMPD Verify Result = {0}".format(ret))
        return ret

    # PID-VID ------------------------------
    @apollo_step
    def verify_pidvid(self, **kwargs):
        """ Verify PID/VID
         Use this to confirm UUT PID & VID are correct for the  product.
         :menu: (enable=True, name=VERIFY PIDVID, section=Config, num=1,  args={'menu': True})
        :param kwargs:
        :return:
        """
        @cesium_srvc_retry
        def verify_product_id_version_id(sn, pid, vid, tan):
            return cesiumlib.verify_product_id_version_id(serial_number=sn,
                                                          product_id=pid,
                                                          version_id=vid,
                                                          tan=tan)
        menu = kwargs.get('menu', False)
        sn = self._ud.puid.sernum
        pid = self._ud.puid.pid
        vid = self._ud.puid.vid
        tan = self._ud.puid.partnum
        tan_rev = self._ud.puid.partnum_rev

        sn = common_utils.ask_validated_question(
            "Enter SN:", answers=None, default_ans=sn, validate_func=getattr(common_utils, 'validate_sernum'),
            rsvd_answers=None, force=menu)
        pid = common_utils.ask_validated_question(
            "Enter PID:", answers=None, default_ans=pid, validate_func=getattr(common_utils, 'validate_pid'),
            rsvd_answers=None, force=menu)
        tan = common_utils.ask_validated_question(
            "Enter TAN:", answers=None, default_ans=tan, validate_func=getattr(common_utils, 'validate_cpn'),
            rsvd_answers=None, force=menu)
        vid = common_utils.ask_validated_question(
            "Enter VID:", answers=None, default_ans=vid, validate_func=getattr(common_utils, 'validate_vid'),
            rsvd_answers=None, force=menu)

        # Display
        aplib.set_container_text('VERIFY PIDVID {0} {1}'.format(pid, vid))
        log.debug("SN      = {0} ({1})".format(sn, self._ud.puid_keys.sernum))
        log.debug("PID     = {0}".format(pid))
        log.debug("VID     = {0}".format(vid))
        log.debug("TAN     = {0} ({1})".format(tan, self._ud.puid_keys.partnum))
        log.debug("TAN Rev = {0} ({1})".format(tan_rev, self._ud.puid_keys.partnum_rev))

        # Sanity
        if not all([sn, pid, vid, tan]):
            log.error("Not all values are valid for PIDVID check!")
            return aplib.FAIL, "Invalid values for PIDVID check."

        # Bypass
        if tan_rev and tan_rev < 'A0':
            log.warning("TAN Revision is NOT a production release!")
            log.warning("PIDVID verify will be SKIPPED.")
            return aplib.SKIPPED

        # Check It!
        try:
            verify_product_id_version_id(sn, pid, vid, tan)
            log.info("STEP: Verify PIDVID has PASSED!")
        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.debug(e)
            log.error("STEP: Verify PIDVID has FAILED!")
            return aplib.FAIL, e.message

        return aplib.PASS

    @apollo_step
    def get_vid(self, **kwargs):
        """ Get VID
        Use this to get the UUT VID based on PID and TAN.

        Example usage: cesiumlib.get_vid(tan='800-2707-10', product_id='A9K-24X10GE-TR')
        Sample output: { 'root': { 'vid' : 'V01', 'tan' : '800-2707-10', 'product_id' : 'A9K-24X10GE-TR' } }

        :menu: (enable=True, name=GET VID, section=Config, num=1,  args={'menu': True})
        :param kwargs:
        :return:
        """
        @cesium_srvc_retry
        def get_vid(tan, product_id, is_basepid=True):
            return cesiumlib.get_vid(tan=tan, product_id=product_id, is_basepid=is_basepid)

        menu = kwargs.get('menu', False)
        pid = self._ud.puid.pid
        tan = self._ud.puid.partnum
        tan_rev = self._ud.puid.partnum_rev
        current_vid = self._ud.puid.vid

        pid = common_utils.ask_validated_question(
            "Enter PID:", answers=None, default_ans=pid, validate_func=getattr(common_utils, 'validate_pid'),
            rsvd_answers=None, force=menu)
        tan = common_utils.ask_validated_question(
            "Enter TAN:", answers=None, default_ans=tan, validate_func=getattr(common_utils, 'validate_cpn'),
            rsvd_answers=None, force=menu)

        # Display
        aplib.set_container_text('GET VID {0} {1}'.format(pid, tan))
        log.debug("PID         = {0}".format(pid))
        log.debug("TAN         = {0} ({1})".format(tan, self._ud.puid_keys.partnum))
        log.debug("TAN Rev     = {0} ({1})".format(tan_rev, self._ud.puid_keys.partnum_rev))
        log.debug("Current VID = {0}".format(current_vid))

        # Sanity
        if not all([pid, tan]):
            log.error("Not all values are valid for VID fetch!")
            return aplib.FAIL, "Invalid values for VID fetch."

        # Get It!
        try:
            vid_dict = get_vid(tan=tan, product_id=pid)
            log.info(vid_dict)
            latest_vid = vid_dict.get('vid', None)
            if latest_vid:
                if current_vid == latest_vid:
                    log.info("Currently loaded VID is the latest VID.")
                elif current_vid < latest_vid:
                    log.info(
                        "The currently loaded VID {0} will be overwritten with the latest VID {1}.".format(current_vid,
                                                                                                           latest_vid))
                    self._ud.uut_config[self._ud.puid_keys.vid] = latest_vid
                elif current_vid > latest_vid:
                    log.warning(
                        "Currently loaded VID {0} is newer than the retrieved VID {1} from the database.".format(
                            current_vid, latest_vid))
                    log.warning("Keeping the currently loaded VID.")
            else:
                log.warning("VID retrieval was empty; this is unusual.")
                log.warning("Currently loaded VID will be used.")
            log.info("STEP: Get VID has PASSED!")
        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.debug(e)
            log.error("STEP: Get VID has FAILED!")
            return aplib.FAIL, e.message

        return aplib.PASS

    # CLEI/ECI -----------------------------
    @apollo_step
    def get_clei_eci(self, **kwargs):
        """ Get CLEI and ECI

        :menu: (enable=True, name=GET CLEI/ECI, section=Config, num=1,  args={'menu': True})
        :param kwargs:
        :return:
        """
        @cesium_srvc_retry
        def get_clei(tan):
            return cesiumlib.get_clei(tan=tan)

        # Inputs
        menu = kwargs.get('menu', False)
        clei_key = kwargs.get('clei_key', 'CLEI_CODE_NUMBER')
        eci_key = kwargs.get('eci_key', 'ECI_CODE_NUMBER')

        # Lookups
        tan = self._ud.puid.partnum
        tan = common_utils.ask_validated_question(
            "Enter TAN:", answers=None, default_ans=tan, validate_func=getattr(common_utils, 'validate_cpn'),
            rsvd_answers=None, force=menu)

        # Display
        aplib.set_container_text('GET CLEI/ECI {0}'.format(tan))
        log.debug("TAN = {0}".format(tan))

        # Get It!
        try:
            clei, eci = get_clei(tan)
            log.debug("CLEI = {0}".format(clei))
            log.debug("ECI  = {0}".format(eci))
            if clei:
                current_clei = self._ud.uut_config[clei_key]
                if clei != current_clei:
                    log.debug("The CLEI will be updated...")
                    self._ud.uut_config[clei_key] = clei
            if eci:
                current_eci = self._ud.uut_config[eci_key]
                if eci != current_eci:
                    log.debug("The ECI will be updated...")
                    self._ud.uut_config[eci_key] = eci
            log.info("STEP: CLEI/ECI is loaded to the uut_config; PASSED!")

        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.debug(e)
            log.info("STEP: Get CLEI/ECI has FAILED!")
            return aplib.FAIL

        return aplib.PASS

    @apollo_step
    def verify_clei_eci_label(self, **kwargs):
        """ Verify CLEI ECI label

        Compare CLEI ECI label value against value programmed in EEPROM. Label values are scanned and stored in tst
        during assembly process (SYSASSY), programmed values are read and stored in uut_config['CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER'].
        If they don't match, fail test

        :param kwargs:
        :return:
        """
        aplib.set_container_text('VERIFY CLEI ECI LABEL')
        log.debug("STEP: Verify CLEI ECI Label.")

        # Process inputs
        source_testarea = kwargs.get('source_testarea', ['SYSASSY'])
        label_clei = kwargs.get('label_clei')
        label_eci = kwargs.get('label_eci')
        sernum = kwargs.get('serial_number', self._ud.puid.sernum)

        # If label values are not given explicitly, read them from tst
        if not label_clei or not label_eci:
            tst_record = common_utils.read_sn_data(sernum=sernum,
                                                   db_table_name=['tst'],
                                                   test_area=source_testarea,
                                                   start_datetime='LATEST',
                                                   result_pass_fail='P')
            tst_record = tst_record[0].get('result')[0]
            if not tst_record:
                log.error('No correct SYSASSY record is found.')
                return aplib.FAIL
            log.debug('tst: {}'.format(tst_record))
            label_clei = tst_record.get('clei')
            label_eci = tst_record.get('eci')

        uut_clei = kwargs.get('uut_clei', self._ud.uut_config.get('CLEI_CODE_NUMBER'))
        uut_eci = kwargs.get('uut_eci', self._ud.uut_config.get('ECI_CODE_NUMBER'))

        # Comparison
        log.debug('Label: CLEI[{0}], ECI[{1}]'.format(label_clei, label_eci))
        log.debug('UUT: CLEI[{0}], ECI[{1}]'.format(uut_clei, uut_eci))
        if str(label_clei) != str(uut_clei) or str(label_eci) != str(uut_eci):
            log.error('Label CLEI/ECI do not match UUT CLEI/ECI.')
            return aplib.FAIL

        return aplib.PASS

    # LineID -------------------------------
    @apollo_step
    def analyze_lineid(self, **kwargs):
        """ Analyze line ID and save line ID info in uut_config

        Line ID could come from 2 sources from priority high to low:
            1. kwargs input: major_line_id
            2. serial_number from uut_config['SYSTEM_SERIAL_NUM']

        If neither source can provide valid line ID input, return FAIL.
        Do cesium service calls to get line ID config, and save them in uut_config

        :menu: (enable=True, name=LINEID ANALYZE, section=DF, num=1, args={'menu': True})
        :return:        aplib.PASS/FAIL
        """
        aplib.set_container_text('ANALYZE LINEID')
        log.info('STEP: Analyze Line ID.')

        # Input processing
        menu = kwargs.get('menu', False)
        serial_number = kwargs.get('serial_number', self._ud.puid.sernum)
        line_id = kwargs.get('major_line_id')

        # 1. Manage S/N
        if menu:
            serial_number = common_utils.ask_validated_question('Enter System Serial Number',
                                                                answers=None,
                                                                default_ans=serial_number,
                                                                validate_func=common_utils.validate_sernum,
                                                                rsvd_answers=None,
                                                                force=menu)
        if not serial_number:
            log.error("MUST have a Serial Number.")
            return aplib.FAIL, 'Missing Serial Number'
        log.info("Serial Number: {0}".format(serial_number))

        # 2. Manage LineID
        if not line_id:
            try:
                line_id = cesiumlib.get_line_id(serial_number=serial_number)
            except (apexceptions.ServiceFailure, apexceptions.ResultFailure) as err:
                log.debug(err.message)
                log.warning('LineID not retrieved based on S/N; enter manually...')
                line_id = common_utils.ask_validated_question('Enter LineID',
                                                              answers=None,
                                                              default_ans=line_id,
                                                              validate_func=common_utils.validate_lineid,
                                                              rsvd_answers=None,
                                                              force=menu)
                if not line_id:
                    msg = 'No LineID available.'
                    log.error(msg)
                    return aplib.FAIL, msg
        line_id = int(line_id)
        log.info("Line ID      : {0}".format(line_id))

        # 3. Get the LID config
        try:
            line_id_cfg = cesiumlib.get_lineid_config(major_line_id=line_id)
        except (apexceptions.ServiceFailure, apexceptions.ResultFailure) as err:
            log.debug(err)
            return aplib.FAIL, err.message

        # 4. Save info in uut_config
        self._ud.uut_config.update({'major_line_id': line_id, 'lineid': line_id, 'major_line_id_cfg': line_id_cfg})
        log.info('Output: major_line_id: {0}, major_line_id_cfg: {1}'.format(line_id, line_id_cfg))

        return aplib.PASS

    @apollo_step
    def get_hw_modules_from_lineid(self, **kwargs):
        """ Get Hardware Authentication Modules from Line ID (Step)

        This step looks through lineid config_data to get installed hardware authentication modules, assemble them to a list,
        then save it in uut_config for later use (step__ios_verify_idpro). There is a default item 'Mainboard' in auth_modules.

        Generated list is saved in uut_config['hw_modules'].
        ex: ['Mainboard', 'FRU', 'Stack Cable A', 'Stack Cable B']

        :param (dict) kwargs:
                      (int) major_line_id: Top level line id, (optional)
                      (list) major_line_id_cfg: config_data from top level line id (preferred input)
                      (dict) order_cfg: Standardized config info from order (NOT used in production, for debug purpose)

        :return:
        """
        aplib.set_container_text('GET HARDWARE AUTHENTICATION MODULES')
        log.debug("STEP: Get Authentication Modules from Line ID.")

        auth_modules = ['Mainboard']

        # Process input
        major_line_id = kwargs.get('major_line_id', self._ud.uut_config.get('major_line_id'))
        major_line_id_cfg = kwargs.get('major_line_id_cfg', self._ud.uut_config.get('major_line_id_cfg', {})).get('config_data')
        order_cfg = kwargs.get('order_config', {})

        if not major_line_id_cfg and not major_line_id and not order_cfg:
            log.error('No valid line ID info input')
            return aplib.FAIL
        elif not major_line_id_cfg and major_line_id and not order_cfg:
            major_line_id_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id).get('config_data')
            if not major_line_id_cfg:
                log.error('No valid line ID config_data for {0}'.format(major_line_id))
                return aplib.FAIL

        # Process major_line_id_cfg to get hw_modules
        for item in major_line_id_cfg:
            auth_module = cnf_utils.get_cnf_pid_info(item['prod_name']).get('auth_mod', [])
            auth_module = auth_module if isinstance(auth_module, list) else [auth_module]
            auth_modules += auth_module

        self._ud.uut_config['hw_modules'] = auth_modules
        log.info('Authentication Modules: {0}'.format(auth_modules))

        return aplib.PASS

    @apollo_step
    def get_swpid_from_lineid(self, **kwargs):
        """ Get IOS SWPID from LINE ID (Step)

        Look up in major_line_id_cfg to search for IOS PID. The IOS PID must exist in ios.ios_manifest.
        If major_line_id_cfg is not given, use cesium service call to get it from major_line_id.
        If no major_line_id_cfg available from kwargs or uut_config, return FAIL
        If no IOS PID is found in major_line_id_cfg, return FAIL.

        :param (dict) kwargs:
                     (int) major_line_id: Mfg mapped sales order
                     (dict) major_line_id_cfg: LineID config from cesiumlib DB.

        :return:aplib.PASS if IOS PID is found in major_line_id_cfg, aplib.FAIL otherwise
        """
        aplib.set_container_text('GET IOS PID')
        log.info('STEP: Get IOS PID From Line ID.')

        # Input processing
        major_line_id = kwargs.get('major_line_id', self._ud.uut_config.get('major_line_id'))
        major_line_id_cfg = kwargs.get('major_line_id_cfg', self._ud.uut_config.get('major_line_id_cfg'))

        # Get the LID config
        if not major_line_id_cfg:
            try:
                major_line_id_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id)
            except (apexceptions.ServiceFailure, apexceptions.ResultFailure) as err:
                log.debug(err)
                return aplib.FAIL, err.message

        # Get SW PID from lineid config data
        ios_customer_pid = None
        for item in major_line_id_cfg.get('config_data', []):
            if self._ud.ios_manifest.get(item['prod_name']):
                ios_customer_pid = item['prod_name']
                break
        if not ios_customer_pid:
            msg = 'Cannot find IOS PID in lineid'
            log.error(msg)
            return aplib.FAIL, msg

        # Save info in uut_config
        self._ud.uut_config['ios_customer_pid'] = ios_customer_pid
        log.info('Software PID {}.'.format(ios_customer_pid))

        return aplib.PASS

    # TST & CNF related --------------------
    @apollo_step
    def update_cfg_model_num(self, **kwargs):
        """ Update CFG_MODEL_NUM in uut_config

        Use tst data from source_testarea (default SYSASSY) to update uut_config['CFG_MODEL_NUM']. This value will be used
        as uut_type and add to tst later, it is also used for areacheck to ensure current area has the same uut_type as
        the area checked against (default SYSASSY)

        :param kwargs:
        :return:
        """
        aplib.set_container_text('UPDATE TOP LEVEL PID')
        log.info('STEP: Update Top Level PID with SYSASSY data.')

        # Input processing
        menu = kwargs.get('menu', False)
        serial_number = kwargs.get('serial_number', self._ud.puid.sernum)
        cfg_model_num = kwargs.get('cfg_model_num')
        source_testarea = kwargs.get('source_testarea', ['SYSASSY'])

        # 1. Manage S/N
        if menu:
            serial_number = common_utils.ask_validated_question('Enter System Serial Number',
                                                                answers=None,
                                                                default_ans=serial_number,
                                                                validate_func=common_utils.validate_sernum,
                                                                rsvd_answers=None,
                                                                force=menu)
        if not serial_number:
            log.error("MUST have a Serial Number.")
            return aplib.FAIL, 'Missing Serial Number'
        log.info("Serial Number: {0}".format(serial_number))

        # 2. Get TST data from source_testarea
        if not cfg_model_num:
            sn_tst = common_utils.read_sn_data(sernum=serial_number,
                                               db_table_name=['tst'],
                                               test_area=source_testarea,
                                               start_datetime='LATEST',
                                               result_pass_fail='P')
            log.info('tst is {}'.format(sn_tst))
            cfg_model_num = sn_tst[0]['result'][0]['uut_type']

        # 3. Save info in uut_config
        self._ud.uut_config['CFG_MODEL_NUM'] = cfg_model_num
        log.info('CFG_MODEL_NUM is updated to {}'.format(cfg_model_num))

        return aplib.PASS

    @apollo_step
    def populate_dsc_pcamap(self, **kwargs):
        """ Populate Data Stack Cable PCAMAP

        This step gets Data stack cable information from SYSASSY and populate it to uut_config['pcamaps'].
        If there is no DSC installed in system, this step is skipped.

        When getting to this step, UUT should already passes SYSASSY and genealogy and tst records are available.

        :param kwargs:
        :return:
        """
        # PCAMAP and tst data key mapping
        _tst_to_pcamap = {
            'pid': 'uut_type',
            'vid': 'hwrev',
            'sn': 'serial_number',
            'vpn': 'tan'
        }

        p_ud = self._callback.peripheral.pd
        peri_manifest = p_ud.product_manifest
        self._ud.uut_config['pcamaps'] = kwargs.get('pcamaps', self._ud.uut_config.get('pcamaps', {}))

        if not peri_manifest:
            log.error('Peripheral Manifest is not correctly loaded.')
            return aplib.FAIL

        # Process inputs
        source_testarea = kwargs.get('source_testarea', ['SYSASSY'])

        parent_sn = self._ud.puid.sernum
        parent_pid = self._ud.puid.pid

        # Process line_id_cfg to find out DSC requirement
        line_id_cfg = self._ud.uut_config.get('major_line_id_cfg', {}).get('config_data', [])
        dsc_required = False
        for component in line_id_cfg:
            pid_info = cnf_utils.get_cnf_pid_info(component['prod_name'])
            if pid_info.get('type') == 'DSC':
                dsc_required = True
                break
        if not dsc_required:
            log.info('DSC is not included in system')
            return aplib.SKIPPED

        log.debug('DSC is required.')
        # Get genealogy and children tst records
        current_genealogy = cesiumlib.get_genealogy(serial_number=parent_sn, product_id=parent_pid).get('genealogy_structure', [])
        cable_sn = None
        pid_info = None
        for component in current_genealogy:
            pid_info = cnf_utils.get_cnf_pid_info(component['product_id'])
            log.debug(pid_info)
            log.debug(component)
            if pid_info.get('type') == 'DSC':
                cable_sn = component['serial_number']
                break

        p_ud.product_selection = pid_info.get('pid')
        peri_pcamaps = p_ud.uut_config['pcamaps']
        cable_bid = p_ud.uut_config['BID']

        log.info('cable sn is {}'.format(cable_sn))
        log.info('pcamap is {}'.format(peri_pcamaps))

        if not cable_sn:
            log.info('No DSC installed in system')
            self._ud.uut_config['dsc_installed'] = False
            aplib.apdicts.userdict['dsc_installed'] = False
            return aplib.SKIPPED

        cable_tst = common_utils.read_sn_data(sernum=cable_sn,
                                              db_table_name=['tst'],
                                              test_area=source_testarea,
                                              start_datetime='LATEST',
                                              result_pass_fail='P')
        log.info('tst is {}'.format(cable_tst))

        cable_tst = cable_tst[0]['result'][0]

        for pcamap in peri_pcamaps.values():
            for key in pcamap.keys():
                pcamap[key] = str(cable_tst.get(_tst_to_pcamap.get(key), ''))
            pcamap['bid'] = str(cable_bid)
            pcamap['pid'] = pcamap['pid'][:-1] if pcamap['pid'].endswith('=') else pcamap['pid']

        self._ud.uut_config['pcamaps'].update(peri_pcamaps)
        # use this flag to control seq flow
        self._ud.uut_config['dsc_installed'] = True
        aplib.apdicts.userdict['dsc_installed'] = True
        log.info('UUT config PCAMAPS: {0}'.format(self._ud.uut_config['pcamaps']))

        return aplib.PASS

    @apollo_step
    def configuration_check(self, **kwargs):
        """ Configuration Check (Step)

         Compare installed components against ordered components, ensure configuration is correct.
         Ordered components are retrieved from line id config_data, and installed components are discovered through various
         sources electronically during test.
         Currently this step supports below components:
            -PSU, discovered through stardust diag
            -Network Module, discovered through stardust diag using quack params, information saved in uut_config['pcamaps']
            -Data Stack Cable, same as Network Module

        :param (dict) kwargs:
                      (int) major_line_id: Top level line id, (optional).
                      (list) major_line_id_cfg: The config_data from top level line id (preferred input).
                      (dict) order_cfg: Standardized config info from order (NOT used in production, for debug purpose).
                      (dict) installed_cfg: Standardized config info for installed components (NOT used in production, for debug purpose).

        :return: aplib.PASS if ordered configuration matches installed configuration, otherwise aplib.FAIL
        """
        aplib.set_container_text('CONFIGURATION CHECK')
        log.debug("STEP: Configuration Check.")

        # Process input
        major_line_id = kwargs.get('major_line_id', self._ud.uut_config.get('major_line_id'))
        major_line_id_cfg = kwargs.get('major_line_id_cfg', self._ud.uut_config.get('major_line_id_cfg', {})).get('config_data')
        order_cfg = kwargs.get('order_config', {})
        installed_cfg = kwargs.get('installed_cfg', {})

        if not major_line_id_cfg and not major_line_id and not order_cfg:
            log.error('No valid line ID info input')
            return aplib.FAIL
        elif not major_line_id_cfg and major_line_id and not order_cfg:
            major_line_id_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id).get('config_data')
            if not major_line_id_cfg:
                log.error('No valid line ID config_data for {0}'.format(major_line_id))
                return aplib.FAIL

        psu_uut_type_keys = self._ud.uut_config.get('cnf_psu_keys', {}).get('uut_type', ['PS PID'])
        psu_sn_keys = self._ud.uut_config.get('cnf_psu_keys', {}).get('sn', ['PS SN'])
        pcamap_uut_type_keys = self._ud.uut_config.get('cnf_pcamap_keys', {}).get('uut_type', ['pid'])
        pcamap_sn_keys = self._ud.uut_config.get('cnf_pcamap_keys', {}).get('sn', ['sn'])
        psu_info = self._ud.uut_config.get('psu_info')

        if not psu_info:
            self._callback.diags.psu_check()
            psu_info = self._ud.uut_config['psu_info']

        # Get order configuration from line_id
        if not order_cfg:
            order_cfg = cnf_utils.get_config_to_check(major_line_id_cfg=major_line_id_cfg)

        # Get installed configuration from UUT (discover through diags/stardust)
        if not installed_cfg:
            psu_config = cnf_utils.parse_component_config(components_info=psu_info,
                                                          component_uut_type_keys=psu_uut_type_keys,
                                                          component_sn_keys=psu_sn_keys)
            if not psu_config:
                log.error('PSU [{0}]config is invalid'.format(psu_config))
                return aplib.FAIL
            else:
                installed_cfg.update(psu_config)

            pcamap_config = cnf_utils.parse_component_config(components_info=self._ud.uut_config.get('pcamaps', {}),
                                                             component_uut_type_keys=pcamap_uut_type_keys,
                                                             component_sn_keys=pcamap_sn_keys)
            if pcamap_config is None:
                log.error('Configuration in PCAMAP [{0}] is invalid'.format(pcamap_config))
                return aplib.FAIL
            else:
                installed_cfg.update(pcamap_config)

        log.info('Configuration comparison')
        log.info('ORDER:\t {0}'.format(order_cfg))
        log.info('INSTALLED:\t {0}'.format(installed_cfg))

        if order_cfg != installed_cfg:
            all_keys = set(order_cfg.keys()).union(set(installed_cfg.keys()))
            log.error('*' * 20 + 'ERROR' + '*' * 20)
            for key in all_keys:
                if order_cfg.get(key) != installed_cfg.get(key):
                    log.error(
                        '{0}: order[{1}] vs installed[{2}]'.format(key, order_cfg.get(key), installed_cfg.get(key)))
            log.error('*' * 20 + 'ERROR' + '*' * 20)

        return aplib.PASS if order_cfg == installed_cfg else aplib.FAIL

    @apollo_step
    def get_rfid_db(self, **kwargs):
        """ STEP: Get RFID Record from TST
        :menu: (enable=True, name=GET RFID DB, section=Data, num=01, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('GET RFID DATA')
        log.info('STEP: Get RFID Data.')

        # Inputs
        menu = kwargs.get('menu', False)
        area = kwargs.get('area', 'PTXCAL')
        chassis_enabled = kwargs.get('chassis_enabled', self._ud.uut_config.get('rfid', {}).get('chassis_enabled', False))
        sernum = self._ud.puid.sernum
        mode = aplib.get_apollo_mode()

        if menu:
            sernum = aplib.ask_question("Enter System Serial Number:") if not sernum else sernum
        elif not chassis_enabled:
            log.warning("RFID is not enabled for this product. (See product definition.)")
            return aplib.SKIPPED
        else:
            # Not menu AND chassis enabled for RFID
            log.debug("RFID required.")

        # Pull it!
        rfid_data = self.__read_tst_rfid_data(sernum, area)

        log.debug("TST RFID Data = {0}".format(rfid_data))
        # Store to uut_config and for flash/tlv
        self._ud.uut_config['rfid'] = rfid_data
        self._ud.uut_config['RFID_TID'] = rfid_data.get('tid', None)
        if not self._ud.uut_config['RFID_TID']:
            msg = "No RFID TID data in the TST {0} database for this serial number ({1}).".format(mode, sernum)
            if mode == aplib.MODE_DEBUG:
                log.warning(msg)
                return aplib.SKIPPED
            else:
                log.error(msg)
                return aplib.FAIL

        log.debug("RFID data retrieval was successful.")
        return aplib.PASS

    # ----------------------------------------
    # Debug/Utility STEPS (Not for Production)
    #
    @apollo_step(s='Debug')
    def uut_debug_scan(self, **kwargs):
        """ UUT Debug Scan
        *** Do this only for DBGSYS which is used by the Eng Menu***
        :param kwargs:
        :return:
        """
        product_line = kwargs.get('product_line', 'catalyst')
        if aplib.apdicts.test_info.test_area == 'DBGSYS':
            sd = {'SYSTEM_SERIAL_NUM': common_utils.generate_offline_cisco_sernum()}
        else:
            sd = self.__uut_scan_info(['SYSTEM_SERIAL_NUM'])
        sd.update({'MODEL_NUM': product_line})
        # Update descriptor
        self._ud.product_line = product_line
        self._ud.uut_config.update(sd)
        return aplib.PASS

    @apollo_step(s='Debug')
    def manual_select_family(self, area_seq_module, **kwargs):
        """ Manual Select Product Family
        Intended for use by area_sequences where an operator prompt is desired.
        Typically used for DBGSYS (but could be used by others).
        Alternative is to run the uut_discover() method and select automatically based on data.
        :param area_seq_module: The area_sequence module calling this method.
                                Used for relative searching of product families.
        :return:
        """
        filter = kwargs.get('filter', '').upper()
        log.debug("Filter for family selection = {0}".format(filter))
        fam_dir = os.path.dirname(os.path.dirname(area_seq_module.__file__))
        log.debug("Family dir = {0}".format(fam_dir))
        pfl = [f.split('.')[0][6:].upper() for f in os.listdir(fam_dir) if f[:6] == 'steps_' and f[-3:] == '.py']
        apfl = [f for f in pfl if filter in f] if filter else pfl
        log.debug("Available product families = {0}".format(apfl))
        if len(apfl) == 0:
            raise Exception("Product family step files are missing. Must be of form 'steps_<family>.py'.")
        elif len(apfl) == 1:
            pf = apfl[0]
        else:
            pf = aplib.ask_question("Select a Product Family:", answers=apfl)
        self._ud.product_family = pf.lower()
        return aplib.PASS

    @apollo_step(s='Debug')
    def manual_select_product(self):
        self._ud.product_selection = aplib.ask_question('Select Product:', answers=self._ud.products_available)
        return aplib.PASS

    @apollo_step(s='Utility')
    def read_sn_data(self, **kwargs):
        """ Read the SN Data from TST Database
        :menu: (enable=True, name=READ SN DATA, section=Data, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        # Process Input.
        menu = kwargs.get('menu', False)
        sernum_key = kwargs.get('sernum_key', 'MOTHERBOARD_SERIAL_NUM')
        # Set entry params.
        sernum = self._ud.uut_config[sernum_key] if sernum_key in self._ud.uut_config else None

        # Operator prompts if params not provided or if menu is invoked.
        log.debug("From menu={0}".format(menu))
        sernum = common_utils.ask_validated_question("Read TST - Enter S/N:",
                                                     default_ans=sernum,
                                                     validate_func=getattr(common_utils, 'validate_sernum'),
                                                     force=menu)

        start_datetime = aplib.ask_question("Start Date:")
        start_datetime = None if start_datetime.lower() == 'skip' or start_datetime == '' else start_datetime
        end_datetime = aplib.ask_question("End Date:")
        end_datetime = None if end_datetime.lower() == 'skip' or end_datetime == '' else end_datetime
        area = aplib.ask_question("Area:")
        area = None if area == '' else [a.strip(' ') for a in area.split(',')]

        # Run it.
        data = common_utils.read_sn_data(sernum, db_table_name=['tst'], area=area,
                                         start_datetime=start_datetime,
                                         end_datetime=end_datetime)
        # Display
        log.debug("UUT S/N = {0}".format(sernum))
        log.debug("SN DATA:")
        log.debug("-" * 40)
        common_utils.print_large_dict(data)

        return aplib.PASS

    @apollo_step(s='Utility')
    def lookup_mac(self, **kwargs):
        """ Lookup MAC
        :menu: (enable=True, name=GET MAC, section=Data, num=2, args={'menu': True})
        :param kwargs:
        :return:
        """
        # Setup defaults
        menu = kwargs.get('menu', False)
        # Process Input.
        sernum_key = kwargs.get('sernum_key', 'MOTHERBOARD_SERIAL_NUM')

        # Set entry params.
        sernum = self._ud.uut_config[sernum_key] if sernum_key in self._ud.uut_config else None

        # Operator prompts if params not provided or if menu is invoked.
        log.debug("From menu={0}".format(menu))
        sernum = common_utils.ask_validated_question("Get MAC - Enter S/N:",
                                                     default_ans=sernum,
                                                     validate_func=getattr(common_utils, 'validate_sernum'),
                                                     force=menu)
        mac = common_utils.get_mac(sernum)
        log.debug("MAC = {0}".format(mac))

        return aplib.PASS

    @apollo_step(s='Utility')
    def get_sw_configs(self, **kwargs):
        """ Get SW Configs
        1. MUST have a released product_id and have OSCAR mapping.
        2. Alternatively, use CNFv2: CNFexp tool to create a custom entry
        :menu: (enable=True, name=GET SW DETAILS, section=Data, num=3, args={'menu': True})
        :param kwargs:
        :return:
        """
        # Inputs
        menu = kwargs.get('menu', False)
        pids = kwargs.get('pids', [])
        verbose = kwargs.get('verbose', False)

        log.debug("menu = {0}".format(menu))

        if not pids:
            ans = aplib.ask_question("Entry type:", answers=['Manual', 'Load from File'])
            if ans == 'Manual':
                pids_str = aplib.ask_question("Enter PIDs (cvs):")
                pids = [pid.strip(' ') for pid in pids_str.split(',')]
            else:
                pidfile = aplib.ask_question("Enter PID file:")
                if os.path.exists(pidfile):
                    pids = common_utils.readfiledata(pidfile, ast_flag=False, raw=False)

        log.debug("PIDs:")
        sw_data = ["Index | SWPID | Version | CCO Loc | Image Name | MD5 | Image Size | Image ID | Init Ver | Source"]

        def __make_line(sw, i, pid, source, verbose):
            if verbose:
                log.debug("keys = {0}".format(sw.keys()))
                for k, v in sw.items():
                    log.debug("{0:<20} = {1}".format(k, v))
            line = "{0:>03} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9}". \
                format(i, pid,
                       sw.get('version', ''),
                       sw.get('image_name', ''),
                       sw.get('cco_location', ''),
                       sw.get('md5', ''),
                       sw.get('imagesize', ''),
                       sw.get('image_id', ''),
                       sw.get('initiated_version', ''),
                       source
                       )
            return line

        for i, pid in enumerate(pids, 1):
            try:
                source = 'OSCAR'
                log.debug("Get OSCAR mapped PID...")
                pid = re.search('([A-Za-z0-9\-\+\.\=]+)', pid).group(0)
                sw = cesiumlib.get_sw_config(product_id=pid)
                line = __make_line(sw, i, pid, source, verbose)
            except apexceptions.ApolloException:
                try:
                    source = 'CNFv2-Exp'
                    log.debug("No OSCAR mapped PID; get CNFv2-Exp custom (pre-release)...")
                    sw = cesiumlib.product_id_config(product_id=pid)
                    line = __make_line(sw, i, pid, source, verbose)
                except:
                    log.debug("SW details are NOT avaialble anywhere!")
                    line = "{0:>03} | {1} | NOT AVAILABLE".format(i, pid)

            log.debug(line)
            sw_data.append(line)
            common_utils.print_large_dict(sw) if verbose else None

        file = '/tmp/sw_configs.txt'
        common_utils.writefiledata(file, sw_data)
        log.debug("Data written to {0}".format(file))
        return aplib.PASS

    @apollo_step(s='Utility')
    def get_container_details(self, **kwargs):
        """ Get Container Details
        :menu: (enable=True, name=CONT DETAILS, section=Data, num=4, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('CONTAINER DETAILS')
        log.info("STEP: Get Container details.")

        common_utils.container_details()
        return aplib.PASS

    @apollo_step(s='Utility')
    def get_lineid_data(self, **kwargs):
        """ Get LineID Data
        :menu: (enable=True, name=GET LINEID, section=Data, num=5, args={'menu': True, 'exploded': False})
        :param kwargs:
        :return:
        """
        # Inputs
        menu = kwargs.get('menu', False)
        major_line_ids = kwargs.get('major_line_ids', [])
        print_exploded = kwargs.get('print_exploded', False)

        if menu:
            ans = aplib.ask_question("Enter Major LineIDs:")
            if ans.upper() == 'ABORT':
                return aplib.SKIPPED
            major_line_ids = common_utils.expand_comma_dash_num_list(ans)
            log.debug("Major LineIDs  = {0}".format(major_line_ids))

        major_line_ids = [major_line_ids] if not isinstance(major_line_ids, list) else major_line_ids

        for major_line_id in major_line_ids:
            log.debug("=" * 100)
            try:
                lineid_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id)
                common_utils.print_large_dict(lineid_cfg, exploded=print_exploded)
            except apexceptions.ServiceFailure as e:
                log.debug(e)
        return aplib.PASS

    # ==================================================================================================================
    # USER METHODS   (step support)
    # ==================================================================================================================
    @func_details
    def get_cmpd_types_by_area(self, cmpd_types_dict, area):
        """ Search through cmpd_types_dict to find a matching entry for area

        :param cmpd_types_dict:     (list) a list of cmpd_types
        :param area:                (str)  current test_area
        :return:                    (list) cmpd_types
        """
        cmpd_types = []
        for i in cmpd_types_dict:
            if area in cmpd_types_dict[i].get('areas', []) or cmpd_types_dict[i].get('areas', []) == 'ALL':
                log.debug("Found CMPD Types for this area ({0}).".format(area))
                cmpd_types = cmpd_types_dict[i].get('types', [])
                break
        else:
            log.warning("No CMPD Types found for the area ({0}).".format(area))

        return cmpd_types

    @func_details
    def get_cmpd_types_dict_from_manifest(self):
        """ Get CMPD types dict from manifest (aka product definition)

        :return: (dict) cmpd_types_dict, if nothing is found, return a empty dict
        """
        log.debug("Getting CMPD types from product definition...")
        prod_def_cmpd_types = self._ud.uut_config.get('cmpd_types', None)
        cmpd_types_dict = {}
        if isinstance(prod_def_cmpd_types, tuple):
            log.debug("CMPD Types Reference was specified.")
            for i in prod_def_cmpd_types[1]:
                cmpd_types_dict[i] = (self._ud.uut_config.get(prod_def_cmpd_types[0], {}).get(i, {}))
                log.debug("CMPD Types Reference index {0} has content.".format(i)) if cmpd_types_dict[i] else None
        elif isinstance(prod_def_cmpd_types, dict):
            log.debug("CMPD Types was specified.")
        else:
            log.warning("No CMPD Types available or form is not correct!  Check product definition.")

        return cmpd_types_dict

    # ==================================================================================================================
    # INTERNAL
    # ==================================================================================================================
    def __uut_scan_info(self, required_items, optional_items=None):
        if not required_items:
            log.debug("No data items to scan.")
            return {}

        # Present operator with required items to scan/enter and save to dict for later use.
        log.info('1. Get required data...')
        scanned_data = common_utils.get_data_from_operator(self._ud.category,
                                                           product_desc=self._ud.product_line,
                                                           data_items=required_items,
                                                           rev_map=self._ud.DEFAULT_REVISION_MAP,
                                                           gui=self._ud.apollo_go)

        # Now select the optional params appropriate for the selected product
        # (i.e. filter the master optional_items list with the actual uut_config params and find a common set)
        if not optional_items:
            return scanned_data
        log.info('2. Get filtered optional data...')
        filtered_optional_keys = self._ud.get_filtered_keys(optional_items)

        # Present operator with the filtered optional items to scan/enter, then save to dict for later use.
        log.info('3. Scan/enter additional data...')
        scanned_option_data = common_utils.get_data_from_operator(self._ud.category,
                                                                  product_desc=self._ud.product_line,
                                                                  data_items=filtered_optional_keys,
                                                                  rev_map=self._ud.DEFAULT_REVISION_MAP,
                                                                  gui=self._ud.apollo_go)
        scanned_data.update(scanned_option_data)
        log.debug("Scanned data = {0}".format(scanned_data))
        return scanned_data

    def __uut_process_prepopulated_info(self, prepopulated_items):
        # Scan Loop for all items
        retrieved_data = {}
        log.info('Prepopulated entry retrieval of UUT ({0}) info from product definition...'.format(self._ud.category))
        for prepop_item in prepopulated_items:
            log.info("Searching for item: {0}".format(prepop_item))
            data = {}
            if prepop_item == 'DEVIATION_NUM' or prepop_item == 'ECO_NUM':
                value = self._ud.get_eco_num_in_manifest(eco_type=self._ud.PRGM,
                                                         test_area=aplib.apdicts.test_info.test_area,
                                                         update=True)
                if value:
                    log.debug("Item: {0} = {1}".format(prepop_item, value))
                    data = {prepop_item: value}
                else:
                    log.warning("Item: {0} is NOT set.".format(prepop_item))

            elif prepop_item == 'SOMETHING_ELSE':
                # Add functionality here as needed.
                pass
            else:
                log.warning("Unrecognized prepopulated item.")
        return data

    def __uut_boot_retrieve_info(self, **kwargs):
        self._mode_mgr.power_on()
        params = self._callback.pcamap.read(device_instance=0)
        for p in ['MOTHERBOARD_ASSEMBLY_NUM', 'SYSTEM_ASSEMBLY_NUM', 'VPN', 'MODEL_NUM', 'PID']:
            prod_select = params.get(p, None)
            log.debug("Checking {0} = {1}".format(p, prod_select))
            if prod_select:
                try:
                    self._ud.product_selection = prod_select
                    self._ud.uut_config.smart_update(params)
                    break
                except Exception as e:
                    log.debug("Continue searching...")
        else:
            log.warning("Could not find any data from the UUT to identify the product.")
            self.manual_select_product()
            self._ud.uut_config.smart_update(params)

        return aplib.PASS

    def __uut_rd_database_info(self, **kwargs):
        return aplib.PASS

    def __fetch_cmpd(self, **kwargs):
        """Fetch CMPD Table
        This fetches the 'PROGRAMMING'  or 'VERIFICATION' CMPD template from the DB.
        Note1: description = 'SPROM' as default.
        Note2: password_family = 'dsbu' is used for C2K/C3K (C9200/C9300)
                               = 'cat4k' is used for C4K/C9400
        :return:
        """
        @cesium_srvc_retry
        def get_cmpd(cmpd_description, uut_type, part_number, part_revision, area, test_site, eco_deviation_number,
                     password_family):
            return cesiumlib.get_cmpd(cmpd_description=cmpd_description,
                                      uut_type=uut_type,
                                      part_number=part_number,
                                      part_revision=part_revision,
                                      area=area,
                                      test_site=test_site,
                                      eco_deviation_number=eco_deviation_number,
                                      password_family=password_family)

        # Setup defaults
        menu = kwargs.get('menu', False)
        area = kwargs.get('previous_area', aplib.apdicts.test_info.test_area)
        area, _, _, _, _ = common_utils.enter_cmpd_params('Fetch', menu, area=area)

        # Process Input.
        cmpd_description = kwargs.get('cmpd_description', self._ud.uut_config.get('cmpd', {}).get('description', 'SPROM'))
        password_family = kwargs.get('password_family', self._ud.uut_config.get('cmpd', {}).get('password_family', 'dsbu'))
        test_site = kwargs.get('test_site', 'ALL')
        eco_deviation_key = kwargs.get('eco_deviation_key', 'DEVIATION_NUM')
        eco_type = kwargs.get('eco_type', self._ud.PRGM)

        # Set CMPD entry params.
        container = aplib.get_my_container_key().split('|')[-1]
        uut_type = self._ud.puid.pid
        part_number = self._ud.puid.partnum
        part_revision = self._ud.puid.partnum_rev

        # Operator prompts if params not provided or if menu is invoked.
        log.debug("From menu={0}".format(menu))
        if not cmpd_description:
            cmpd_description = aplib.ask_question("Enter CMPD Description:",
                                                  answers=['SPROM', 'SOFTWARE', 'FIRMWARE', 'DIAG ITEM'])
        if not password_family:
            password_family = aplib.ask_question("Enter Password Family:")
        if menu:
            eco_type = aplib.ask_question('CMPD ECO Type:', answers=[self._ud.PRGM, self._ud.VRFY])
        eco_num = self._ud.get_eco_num_in_manifest(eco_type=eco_type, cpn=part_number, cpn_rev=part_revision, test_area=area)
        if not eco_num:
            eco_num = self._ud.uut_config.get(eco_deviation_key, 'NONE')
        eco_deviation_number = eco_num[2:] if eco_num and eco_num[:2] == '0x' else eco_num
        _, uut_type, part_number, part_revision, eco_deviation_number = \
            common_utils.enter_cmpd_params('GET', menu, uut_type=uut_type, part_number=part_number,
                                           part_revision=part_revision, eco_deviation_number=eco_deviation_number)
        eco_deviation_number = None if eco_deviation_number in ['NONE', 'SKIP', 'IGNORE', ''] else eco_deviation_number

        # Display params.
        log.debug("Container     = {0}".format(container))
        log.debug("Description   = {0}".format(cmpd_description))
        log.debug("UUT Type      = {0}".format(uut_type))
        log.debug("Part Number   = {0} ({1})".format(part_number, self._ud.puid_keys.partnum))
        log.debug("Part Revision = {0} ({1})".format(part_revision, self._ud.puid_keys.partnum_rev))
        log.debug("Area          = {0}".format(area))
        log.debug("Test Site     = {0}".format(test_site))
        log.debug("Pswd Family   = {0}".format(password_family))
        log.debug("ECO Deviation = {0}".format(eco_deviation_number))
        log.debug("ECO Type      = {0}".format(eco_type))

        cmpd_params = dict(cmpd_description=cmpd_description,
                           uut_type=uut_type,
                           part_number=part_number,
                           part_revision=part_revision,
                           area=area,
                           test_site=test_site,
                           password_family=password_family,
                           eco_deviation_number=eco_deviation_number)

        # Perform the service.
        cmpd_types, cmpd_values = None, None
        try:
            if eco_deviation_number:
                cmpd_types, cmpd_values = get_cmpd(**cmpd_params)
                log.debug("CMPD Types:  {0}".format(cmpd_types))
                log.debug("CMPD Values: {0}".format(cmpd_values))
            else:
                msg = "No ECO Deviation Number available."
                log.warning(msg)

        except (apexceptions.ApolloException, apexceptions.ServiceFailure) as e:
            log.error(e)

        return cmpd_types, cmpd_values, cmpd_params

    def __read_tst_rfid_data(self, sernum, area='PTXCAL'):
        """ Read TST RFID Data

        Example:
            Note1: top-level data is a list.
            Note2: 'result' data is also a list.
            This is for compatibility w/ legacy Autotest TST records and RFID data.
            TODO: Convert to FPAV and attribute saving.

        TST RFID Data = [{u'code': 0,
                           'filtered_records_found': 1,
                          u'records_found': 633,
                           'result': [{u'uut_type': u'WS-C3K',
                                       u'machine_name': u'ausapp-citp01',
                                       u'test_area': u'DBGSYS',
                                       u'test_container': u'UUT03',
                                       u'clei': u'IPMW100ARA',
                                       u'tan': u'800-41087-05',
                                       u'hwrev': u'V01',
                                       u'partnum2': u'73-14445-05',
                                       u'hwrev2': u'A0',
                                       u'hwrev3': u'A0',
                                       u'result_pass_fail': u'P',
                                       u'serial_number': u'FOC1851X13Y',
                                       u'username': u'bborel',
                                       u'basepid': u'WS-C3850-24S',
                                       u'test_mode': u'DEBUG1',
                                       u'eci': 466431,
                                       u'apollo_version': u'Apollo-98-3',
                                       u'vendpartnum': u'WS-C3850-24S-S',
                                       u'test_id': u'2018-03-23 18:53:51',
                                       u'diagrev': u'stardust_planckcr.2014Apr25',
                                       u'test_record_time': u'2018-03-23 18:55:04',
                                       u'testr1': u'123456789ABCDEF',
                                       u'labelnum': u'A32345678',
                                       u'runtime': 88, u'te_scripts':
                                       u'ausapp-citp01_20180306212311859138_bcfcecf8c6104444c9cf2c78e11ed623.tar.gz'}],
                          u'db_table_name': u'tst',
                          u'serial_number': u'FOC1851X13Y',
                          u'message': u'SUCCESS'}]

        :param sernum:
        :param area:
        :return:
        """
        data = common_utils.read_sn_data(sernum, db_table_name=['tst'], test_area=[area], start_datetime=None, end_datetime=None, result_pass_fail='P', latest=True)
        log.debug("TST RFID Data = {0}".format(data))
        if not data:
            log.warning("No TST data.")
            return {}
        tst_data = data[0].get('result', []) if data[0].get('result', []) else {}
        if not tst_data:
            log.warning("No 'result' data in TST record.")
            return {}

        rfid = dict()
        rfid['epc'] = tst_data[0].get('testr2', '')
        rfid['tid'] = tst_data[0].get('testr1', '')
        rfid['user'] = '{0}{1}'.format(tst_data[0].get('testr3', ''), tst_data[0].get('tenum1name', ''))
        rfid['apswd'] = tst_data[0].get('tenum3', '')

        log.debug("-" * 50)
        log.debug("RFID TID   = {0}".format(rfid['tid']))
        log.debug("RFID EPC   = {0}".format(rfid['epc']))
        log.debug("RFID USER  = {0}".format(rfid['user']))
        log.debug("RFID APSWD = {0}".format(rfid['apswd']))
        return rfid
