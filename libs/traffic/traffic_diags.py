"""
Traffic w/ Diags
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
from collections import OrderedDict

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils import common_utils


__title__ = "Traffic w/ Diags Generic Module"
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


class TrafficDiags(object):
    """ Traffic
    This class is responsible for:
    1. Running multiple traffic cases
    2. Performing pre-traf configuration
    3. Setting up each traffic case conversation in the traf engine
    4. Starting traf, Monitoring, stopping traf
    5. Report results

    NOTE1: Some UUT status data is recorded in the MachineManager's uut_status property:
          (bool) poe_active
          (dict) poe_equip_meas
          (str) active_temperature      (set by self._vmargin_func)
          (str) active_voltage_margin   (set by self._temperature_func)

    NOTE2: For PoE to be engaged during traffic testing the following criteria must be met:
        1. poe_active = True  which is derived from,
           a. poe_enabled = True in the Traffic Case being run.
           b. poe['type'] (dict key/value) is set in the uut_config (from product definition)
           c. _poe_loadbox_driver MUST be initialized  (the x_config.py defines the equipment setup)

    Example of Traffic Cases loaded to the uut_config (typically defined in product_definition):
        'traffic_cases': {
            'TrafCase_EXT_1G_1518_a': {
                'enabled': True,
                'downlink_ports': {
                    '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                             'iteration': 1, 'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                },
                'uplink_ports': {
                    '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                              'iteration': 1, 'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    '27-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                              'iteration': 1, 'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                },
                'stackswitching': True,
                'breakout_ports': {'40G': None, '100G': None},
                'loopback_direction': 'Bidirectional',
                'loopback_point': 'External',
                'vmargin': 'NOMINAL',
                'poe_enabled': True,
                'runtime': 120,
                'pretraf_cmds': [], 'traf_cmds': [],
            },
        },

    """
    
    RECBUF_TIME = 5.0
    RECBUF_CLEAR_TIME = 2.0
    USE_CLEAR_RECBUF = False

    def __init__(self, mode_mgr, ud, **kwargs):
        # Inputs
        log.debug(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._diags = kwargs.get('diags', None)

        # Derived
        self.set_attrs(**kwargs)

        # Dependent (Internal)
        self._container = self._ud.container_key
        self._conversation = None
        self._uplink_card = (None, None)  # (standard_card, test_card)
        self._poe_active = False
        self._active_temperature = None
        self._active_voltage_margin = None
        # Internals
        self._kwargs = kwargs
        self.__verbose = True

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # Properties
    # ==================================================================================================================
    #
    # Read-only  ------------------
    @property
    def container(self):
        return self._container

    @property
    def conversation(self):
        return self._conversation

    @property
    def uplink_card(self):
        return self._uplink_card

    # Read/Write ------------------
    @property
    def uut_ports(self):
        return self._uut_prompt

    @uut_ports.setter
    def uut_ports(self, newvalue):
        self._uut_ports = newvalue

    @property
    def traffic_cases(self):
        return self._traffic_cases

    @traffic_cases.setter
    def traffic_cases(self, newvalue):
        if isinstance(newvalue, tuple):
            # tuple form: e.g. 'traffic_cases': ('traffic_cases_library', '48')
            log.debug("Traffic Cases are referenced by: {0}".format(newvalue))
            if self._ud.uut_config:
                self._traffic_cases = self._ud.uut_config.get(newvalue[0], {}).get(newvalue[1], None)
            else:
                log.error("No UUT Config loaded for traffic reference look up.")
        elif isinstance(newvalue, dict):
            log.debug("Traffic cases set by new dict.")
            self._traffic_cases = newvalue
        elif isinstance(newvalue, str) and newvalue.lower() == 'uut_config':
            self._traffic_cases = self._ud.uut_config.get('traffic_cases', None)
        else:
            log.warning("Cannot set traffic_cases; input error.")

    @property
    def poe_pwr_budget_groups(self):
        return self._ud.uut_status.get('poe_pwr_budget_groups', self._poe_pwr_budget_groups)

    @poe_pwr_budget_groups.setter
    def poe_pwr_budget_groups(self, newvalue):
        self._poe_pwr_budget_groups = newvalue
        self._ud.uut_status['poe_pwr_budget_groups'] = newvalue

    @property
    def poe_active(self):
        return self._ud.uut_status.get('poe_active', self._poe_active)

    @poe_active.setter
    def poe_active(self, newvalue):
        self._poe_active = newvalue
        self._ud.uut_status['poe_active'] = newvalue

    @property
    def active_temperature(self):
        return self._ud.uut_status.get('active_temperature', self._active_temperature)

    @active_temperature.setter
    def active_temperature(self, newvalue):
        self._active_temperature = newvalue
        self._ud.uut_status['active_temperature'] = newvalue

    @property
    def active_voltage_margin(self):
        return self._ud.uut_status.get('active_voltage_margin', self._active_voltage_margin)

    @active_voltage_margin.setter
    def active_voltage_margin(self, newvalue):
        self._active_voltage_margin = newvalue
        self._ud.uut_status['active_voltage_margin'] = newvalue

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def traffic_test(self, **kwargs):
        """ Traffic Test (STEP)
        Perform traffic testing per the product_definition traffic cases (if loaded).

        action='run_all'
        Automatically run ALL cases loaded to the driver automatically by the product definition.
        NOTE: Use caution as the product might need external loopbacks if the traffic cases have that option turned on.
        WARNING: This option should NOT be used for production!

        action='run'
        Selectively run only the cases explicitly provided.  If none provided, then it is operator choice based on
        driver preload from product definition.
        This option should normally be used in the production sequence to selectively pick the traffic cases
        appropriate for the given test area.

        :menu: (enable=True, name=SHOW TRAF DRVR CFG, section=Traffic, num=2, args={'action': 'showcfg'})
        :menu: (enable=True, name=RUN ALL TRAFFIC, section=Traffic, num=3, args={'action': 'run_all'})
        :menu: (enable=True, name=RUN TRAFFIC, section=Traffic, num=4, args={'action': 'run', 'traffic_cases': None})
        :menu: (enable=True, name=GET CONVERSATION, section=Traffic, num=5, args={'action': 'getc'})

        :param kwargs:
        :return:
        """

        # Optional Input
        action = kwargs.get('action', None)
        traffic_cases = kwargs.get('traffic_cases', self._ud.uut_config.get('traffic_cases', None))

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['STARDUST']:
            log.error(
                "Wrong mode ({0}) for this operation. Mode STARDUST is initially required.".format(mode))
            return aplib.FAIL, 'Wrong mode.'

        # Show driver cfg summary
        if action == 'showcfg':
            self.show_config()
            return aplib.PASS

        # Perform the traffic action specified.
        if action == 'getc':
            self._mode_mgr.goto_mode('TRAF')
            self.get_conversation()
            self.print_conversation()
            self._mode_mgr.goto_mode('STARDUST')
            return aplib.PASS

        elif action == 'run_all':
            return self.run_traf_cases()

        elif action == 'run':
            if traffic_cases:
                log.debug("Run specific traffic case(s)...")
                traffic_cases = [traffic_cases] if not isinstance(traffic_cases, list) else traffic_cases
                return self.run_traf_cases(cases=traffic_cases)
            else:
                if not self.traffic_cases:
                    log.debug("Attempting to initialize traffic cases from the product definition...")
                    self.traffic_cases = 'uut_config'
                if self.traffic_cases:
                    ans = aplib.ask_question("Choose a Traffic Case:", answers=sorted(self.traffic_cases.keys()))
                    if ans.upper() == 'ABORT':
                        return aplib.SKIPPED
                    return self.run_traf_cases(cases=[ans])
                else:
                    log.warning("No traffic cases loaded to the driver.")
                    return aplib.SKIPPED

        else:
            log.error("STEP: Traffic TEST action={0} not recognized.".format(action))
            return aplib.FAIL, "Unrecognized action for traf."

        return

    # ==================================================================================================================
    # User Methods (step support)
    # ==================================================================================================================
    def reset(self):
        return

    def show_config(self):
        log.debug("TRAFFIC DRIVER")
        log.debug("--------------")
        log.debug("{0:<30} : {1} {2}".format('Module', __title__, __version__))
        log.debug("{0:<30} : {1}".format('Class', self.__class__.__name__))
        log.debug("{0:<30} : {1}".format('Container', self.container))
        log.debug("{0:<30} : {1}".format('ModeManager', self._mode_mgr.__class__.__name__))
        log.debug("{0:<30} : {1}".format('PoE Loadbox Driver', self._poe_loadbox_driver.__class__.__name__))
        log.debug("{0:<30} : {1}".format('PoE UUT Func', self._poe_uut_func.__name__))
        log.debug("{0:<30} : {1}".format('VMargin Func', self._vmargin_func))
        log.debug("{0:<30} : {1}".format('Temperature Func', self._temperature_func))
        log.debug("{0:<30} : Count={1}".format('UUT Config', len(self._ud.uut_config.keys())))
        log.debug("{0:<30} ----".format('Traffic Cases'))
        if self._traffic_cases:
            for c in self._traffic_cases:
                log.debug("{0:<30} : {1}".format(c, self._traffic_cases[c]))
        else:
            log.debug("{0:<30} : {1}".format('Traffic Cases', 'NONE! (driver needs data update)'))

    def run_traf_cases(self, cases=None, **kwargs):
        """ Run Traffic Cases
        Process entire list of traffic cases.
        Setup and run each one sequentially.
        :param (dict|list) cases:
        :return (str): aplib.PASS/FAIL
        """

        # Determine source of cases.  Explicit param overrides class property.
        if cases:
            if isinstance(cases, dict):
                log.debug("Explicit traffic cases provided.")
            elif isinstance(cases, list):
                log.debug("Explicit traffic case names provided indirectly via a name list.")
                cases_from_list = dict()
                if not isinstance(self._traffic_cases, dict):
                    log.error("The Traffic Cases class property is not set for case list lookup.")
                    log.error("Traffic Driver initialization is incomplete!  Check the product definition file.")
                    return aplib.FAIL
                for name in cases:
                    if name not in self._traffic_cases:
                        log.error("Traffic case '{0}' NOT in preloaded traffic cases.".format(name))
                        return aplib.FAIL
                    else:
                        cases_from_list[name] = self._traffic_cases[name]
                cases = cases_from_list
            else:
                log.error("The Traffic Cases parameter MUST be in dict form or list form.")
                return aplib.FAIL
        elif self._traffic_cases:
            if not isinstance(self._traffic_cases, dict):
                log.error("The Traffic Cases class property MUST be in dict form.")
                return aplib.FAIL
            log.debug("Class property traffic cases provided.")
            cases = self._traffic_cases
        else:
            log.warning("No traffic cases provided; cannot perform traf run.")
            return aplib.FAIL

        # Get optional args
        uut_config = kwargs.get('uut_config', self._ud.uut_config)
        poe_type = uut_config.get('poe', {}).get('type', None)

        # Save starting mode
        mode = self._mode_mgr.current_mode

        # Pre-process the Traf Cases
        processed_cases = {}
        for k, v in cases.items():
            if v.get('poe_and_upoe', False) and poe_type == 'UPOE':
                processed_cases['{0}_p'.format(k)] = v
                processed_cases['{0}_p'.format(k)]['poe_type'] = 'POE+'
                processed_cases['{0}_u'.format(k)] = v
                processed_cases['{0}_u'.format(k)]['poe_type'] = 'UPOE'
            else:
                processed_cases[k] = v
        cases = processed_cases

        # Cycle thru each traf case that was provided.
        results = dict()
        total_cases = len(cases.keys())
        common_utils.uut_comment(self._uut_conn, 'TRAFFIC',
                                 '{0} Case{1}'.format(total_cases, 's' if total_cases > 1 else ''))
        for i, case in enumerate(sorted(cases), 1):
            title = "TRAFFIC{0}: {1}".format(' {0}/{1}'.format(i, total_cases) if total_cases > 1 else '', case)
            log.info(" ")
            log.info("=" * len(title))
            log.info(title)
            log.info("=" * len(title))
            results[case] = {}
            if cases[case].get('enabled', True):
                results[case]['enabled'] = True
                results[case]['ressum'] = True

                loopbacks_required = True if cases[case].get('loopback_point', 'UNK').upper()[
                                             0:3] == 'EXT' else False

                if (self._ud.uut_status.get('portstat', None) == aplib.SKIPPED) and loopbacks_required:
                    log.warning(
                        "Traffic case has been DISABLED due to 1) portstat being SKIPPED and 2) the case requires loopbacks.")
                    log.warning("This is not normal for production (used for debug/development only).")
                    log.warning("Please confirm the setup is correct.")
                    results[case]['enabled'] = False
                    results[case]['pretraf'] = aplib.SKIPPED
                    results[case]['convcfg'] = aplib.SKIPPED
                    results[case]['convrun'] = aplib.SKIPPED
                    results[case]['ressum'] = None
                    continue

                # Pre-Traf
                uut_params = dict(uut_config=uut_config, name=case) if uut_config else None
                pretraf_params = dict(cases[case], **uut_params) if uut_params else cases[case]
                if not self.set_pretraf_config(case_num=i, **pretraf_params):
                    log.error("Pre-Traf Config: FAILED.")
                    results[case]['pretraf'] = aplib.FAIL
                    results[case]['convcfg'] = aplib.SKIPPED
                    results[case]['convrun'] = aplib.SKIPPED
                    results[case]['ressum'] = False
                    continue
                else:
                    log.info("Pre-Traf Config: PASSED.")
                    results[case]['pretraf'] = aplib.PASS

                # Conversation
                for group in range(1, self._poe_pwr_budget_groups + 1):
                    if self._poe_pwr_budget_groups > 1 and self.poe_active:
                        title2 = "Traf Port SubGroup {0}/{1}".format(group, self._poe_pwr_budget_groups)
                        log.info(" ")
                        log.info(title2)
                        log.info("-" * len(title2))
                        conv_params = dict(cases[case], **dict(poe_port_group=group))
                        name = "{0}-{1}".format(case, group)
                    else:
                        conv_params = cases[case]
                        name = "{0}".format(case)
                    # Cfg
                    if not self.set_conversation(**conv_params):
                        log.error('Conversation Config: FAILED.')
                        results[case]['convcfg-{0}'.format(group)] = aplib.FAIL
                        results[case]['convrun-{0}'.format(group)] = aplib.SKIPPED
                        results[case]['ressum'] = False
                        continue
                    else:
                        log.info("Conversation Config: PASSED.")
                        results[case]['convcfg-{0}'.format(group)] = aplib.PASS
                    # Run
                    if not self.run_conversation(name=name, **conv_params):
                        log.error('Conversation Run: FAILED.')
                        results[case]['convrun-{0}'.format(group)] = aplib.FAIL
                        results[case]['ressum'] = False
                    else:
                        log.info("Conversation Run: PASSED.")
                        results[case]['convrun-{0}'.format(group)] = aplib.PASS

            else:
                log.debug("Traffic case is DISABLED.")
                results[case]['enabled'] = False

        log.debug("TRAFFIC RESULTS SUMMARY:")
        # Special handling if only 1 case and disabled.
        if len(cases) == 1 and not results[cases.keys()[0]]['enabled']:
            log.debug("{0:<30} = {1}".format(cases.keys()[0], results[cases.keys()[0]]))
            return aplib.SKIPPED
        # Standard handling
        result = True
        for case in sorted(cases):
            log.debug("{0:<30} = {1}".format(case, results[case]))
            if results[case]['enabled']:
                result = False if not results[case]['ressum'] else result

        # Restore original mode
        if mode:
            self._mode_mgr.goto_mode(mode)

        return aplib.PASS if result else aplib.FAIL

    def set_pretraf_config(self, case_num, **kwargs):
        """ Set Pre-Traf Configuration
        Perform setup functions outside of "traf" mode for the following:
            1) Uplink Test Cards
            2) Breakout ports
            3) Any Modular items
            4) Custom pre-traf commands in product definition
            5) General PoE settings & Power Budget

        For the uplink test cards, some examples:
        HilbertSetPort 1/XG;2/G
        HilbertSetPort 1/XG;2/G;3/XG;4/G
        HilbertSetPort 1/G;2/XG;3/G;4/XG

        For breakout, some examples:
        set40 25 -d
        set40 29 -d

        USAGE: Set40GPort <masterPort> [-b | -d]
        <masterPort> -- 1st port of the 4-port group valid for 40G/10G
        -b -- Set a 4-port group back to 10G from 40G mode.
        -d -- Set a 4-port group back to HW default mode:
             . 10G mode: no module or loopback & break-out QSFP/QSFP+
             . 40G mode: the rest of QSFP/QSFP+ types

        :param (int) case_num: Case number
        :param kwargs: All params for one traffic case + all uut_config
               (str)  name: Traffic case name
               (dict) uplink_ports: {'25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518},
                                     '27-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518},}
               (dict) breakout_ports: {'40G': [<port list>], '100G': [<port list>]}
               (list) pretraf_cmds: String list of commands.
               (bool) poe_enabled: True if Traffic test should use PoE (when available from UUT).
        :return:
        """
        log.info("Pre-Traf settings...")
        result = True

        if not self._mode_mgr.goto_mode('STARDUST'):
            log.warning("Unable to enter STARDUST pre-traf mode.")
            return False
        self._uut_prompt = self._mode_mgr.current_prompt


        # Input
        name = kwargs.get('name', 'Traf')
        common_utils.uut_comment(self._uut_conn, 'TRAFFIC CASE {0}'.format(case_num), '{0}'.format(name))
        poe_type = kwargs.get('poe_type', self._ud.uut_config.get('poe', {}).get('type', None))

        # 1. Uplink Test Card config (STARDUST only)
        # --------------------------
        uplink_ports = kwargs.get('uplink_ports', {})
        self.config_uplink_test_card(uplink_ports)

        # 2. Special "Breakout" Ports (STARDUST only)
        # ---------------------------
        breakout_ports = kwargs.get('breakout_ports', {'40G': None, '100G': None})
        if isinstance(breakout_ports, dict):
            if '40G' not in breakout_ports.keys() and '100G' not in breakout_ports.keys():
                log.warning("Breakout Port types not recognized.")
                log.warning("Breakout port setting will be skipped.")
            else:
                if breakout_ports['40G'] and isinstance(breakout_ports['40G'], list):
                    for bo_master_port in breakout_ports['40G']:
                        self._uut_conn.send("Set40GPort {0} -b\r".format(bo_master_port),
                                            expectphrase=self._uut_prompt, timeout=30, regex=True)
                        time.sleep(self.RECBUF_TIME)
                        if re.search('(?:ERR)|(?:FAIL)', self._uut_conn.recbuf):
                            log.error("Problem with Set40GPort.")
                            result = False
                else:
                    log.debug("40G breakout setting will be skipped.")
                if breakout_ports['100G'] and isinstance(breakout_ports['100G'], list):
                    pass  # TODO: Future placeholder
                else:
                    log.debug("100G breakout setting will be skipped.")
        else:
            log.warning("Breakout ports must be in dict form.")
            log.debug("Breakout port settings will be skipped.")

        # 3. Modular platforms: SUP modes for Traffic (STARDUST only)
        # -------------------------------------------
        if self._modular:
            log.debug("Modular SUP Pre-Traf settings...")
            sup_port_groups = kwargs.get('sup_ports', {})
            sup_ports = sorted(sup_port_groups.keys())[0] if sup_port_groups else None
            sup_speed = sup_port_groups.get(sup_ports, {}).get('speed', '10G')
            log.debug("SUP: Ports = {0}  Mode(Speed) = {1}".format(sup_ports, sup_speed))
            sup_port_list = common_utils.expand_comma_dash_num_list(sup_ports)
            if sup_speed == '1G':
                self._uut_conn.send("DTMSetTo1GSpeed\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            elif sup_speed == '10G':
                self._uut_conn.send("DTMSetTo1GSpeed -t\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
            elif sup_speed == '25G':
                # self._uut_conn.send("Set25GPort {0}\r".format(sup_port_list), expectphrase=self._uut_prompt, timeout=30, regex=True)
                pass
            elif sup_speed == '40G':
                self._uut_conn.send("Set40GPort {0}\r".format(sup_port_list), expectphrase=self._uut_prompt,
                                    timeout=30, regex=True)
            else:
                log.debug("Unknown SUP speed mode {0}".format(sup_speed))

        # 4. Custom pre-traf commands per traffic case (STARDUST only)
        # --------------------------------------------
        pretraf_cmds = kwargs.get('pretraf_cmds', list())
        for pretraf_cmd in pretraf_cmds:
            self._uut_conn.send("{0}\r".format(pretraf_cmd), expectphrase=self._uut_prompt, timeout=30, regex=True)
            if re.search('(?:ERR)|(?:FAIL)', self._uut_conn.recbuf):
                log.error("Problem with {0}.".format(pretraf_cmd))
                result = False

        # 5. UUT Pre-Traffic Diag Configuration (DIAG only)
        # -------------------------------------

        if not self._mode_mgr.goto_mode('DIAG'):
            log.warning("Unable to enter DIAG pre-traf mode.")
            result = False
        self._uut_prompt = self._mode_mgr.current_prompt

        uut_config = kwargs.get('uut_config', self._ud.uut_config)
        poe_enabled = kwargs.get('poe_enabled', False)
        self.poe_active = False
        if uut_config:
            log.info("UUT Config data available for pre-traf configuration.")
            if uut_config.get('poe', None):
                log.info("UUT PoE pre-traf setup...")
                if poe_enabled:
                    log.info("Traffc case allows PoE.")
                    if self._poe_loadbox_driver:
                        log.info("PoE loadbox is available.")
                        self.poe_active = True
                        self._poe_uut_func(action='CFG',
                                           poe_type=poe_type,
                                           poe_params=uut_config.get('poe', {}))
                        if self._poe_pwr_budget_groups == 0:
                            self._poe_pwr_budget_groups = self._poe_uut_func(action='BUDGET',
                                                                             poe_type=uut_config.get('poe', {}).get('type', None),
                                                                             poe_ports=uut_config.get('poe', {}).get('uut_ports', None))
                    else:
                        log.info("No PoE Loadbox Driver to engage power.")
                else:
                    log.info("PoE Traffic is NOT enabled.")
            else:
                log.info("No PoE definition for UUT.")
        else:
            log.info("No UUT Config data available for pre-traf configuration.")
        if self._poe_pwr_budget_groups == 0:
            # The poe power budget MUST ALWAYS be set, regardless if PoE is not on the UUT.
            log.warning("No power budget established. Defaulting to 1 port group.")
            self._poe_pwr_budget_groups = 1

        self._ud.uut_status['pretraf_cfg_result'] = result

        return result

    def set_conversation(self, **kwargs):
        """
        USAGE: ConfConversation
            [<conversation list>]
            [-default]
            [-speed:<speed>]
            [-duplex:<duplex>]
            [-crossover:<crossover>]
            [-size:<size>]
            [-frame:<frameID>]
            [-n:<framecount> | -stress | -linerate]
            [-bridging | -routing]
            [-iteration:<maxiteration>]
            [-fifo:<logdepth> | -lifo:<logdepth>]
            [-restart | -norestart]
            [-macsec | -nomacsec]

            <conversation_list> -- Format: <conversation>[,<conversation>]*,
                where <conversation> is integer > 0

            -default -- restore specified conversation(s) to default configuration
            -speed:<speed> -- port speed: 10|100|1000|GIG|2500|2.5G|5G|10G|40G|AUTO (default: AUTO)
            -duplex:<duplex> -- port duplex: FULL|HALF|AUTO (default: AUTO)
            -crossover:<crossover> -- port MDI/MDIX mode: MDIX|MDI|AUTO (default:AUTO)
            -size:<size> -- frame size CRC included (range: 64..9400 default: 64)
            -frame:<frameID> -- frame identifier (default: 0)
            -n:<framecount> -- number of frames to send (range: 1..2^32 - 2  default: 1)
            -stress -- stress mode (default: FALSE)
            -linerate -- linerate mode (default: FALSE),
                Send frames in configured speed or Max speed of the port in Auto speed mode
            -bridging -- use bridging as forwarding scheme (default: TRUE)
            -routing -- use routing as forwarding scheme (default: FALSE)
            -iteration:<maxiteration> -- max# iterations (range: 0..2^32  default: 1)
            -fifo:<logdepth> -- first in error log (range: 1..99  default: 8)
            -lifo:<logdepth> -- last in error log (range: 1..99  default: 0)
            -restart -- restart frames when link up detected (default: FALSE)
            -norestart -- do not restart frames when link up detected (default: TRUE)
            -macsec -- Enable MACsec (default: FALSE)
            -nomacsec -- Disable MACsec (default: TRUE)


        USAGE: ConfMode  <direction> <loopback point> [<conversation list>]
                <Direction> -- traffic direction
              Bidirectional - transmit frames from both conversation ports
              Forward       - transmit frames from lower numbered port to partner port
              Reverse       - transmit frames from higher numbered port to partner port
                <Loopback Point> -- Loopback point
              External   - loopback by external connector
              CPU0..CPU4 - loopback at CPU device (architecture dependent)
              MAC0..MAC4 - loopback at MAC device (architecture dependent)
              PHY0..PHY4 - loopback at Phy device (architecture dependent)
              LCL0..LCL4 - loopback at local MAC/Phy device (architecture dependent)
              RMT0..RMT4 - loopback at remote MAC/Phy device (architecture dependent)

              INT0..INT4 - loopback at an internal point (architecture dependent)
                <conversation_list> -- Format: <conversation>[,<conversation>]*,
                    where <conversation> is integer > 0


        USAGE: ConfPort
            [<port list>]
            [-speed:<speed>]
            [-duplex:<duplex>]
            [-crossover:<crossover>]
            [-auto:<abilities>]
            [-size:<size>]
            [-n:<framecount>]

            <port_list> -- Format: <port>[,<port>]*,
                where <port> is integer > 0

            -speed:<speed> -- port speed: 10|100|1000|GIG|2500|2.5G|5G|10G|40G|AUTO (default: AUTO)
            -duplex:<duplex> -- port duplex: FULL|HALF|AUTO (default: AUTO)
            -crossover:<crossover> -- port MDI/MDIX mode: MDIX|MDI|AUTO (default:AUTO)
            -auto:<abilities> -- Autonegotiate with advertised abilities.
                <ability>[/<ability>]...,
                <ability> is 10H/10F/10A/100H/100F/100A/1000H/1000F/1000A/2.5G/5G/10G/ALL
            -size:<size> -- frame size CRC included (range: 64..9400 default: 64)
            -n:<framecount> -- number of frames to send (range: 1..2^32 - 2  default: 1)


        USAGE: ConfPairs [<port_pair_list>] [-add | -delete | -dual | -single]
            <port_pair_list> -- Format: <port>,<port>[/<port>,<port>]*
                where <port> is integer > 0
            -add -- add port pairs to current port pair list
            -delete -- delete port pairs from current port pair list
            -dual -- reset conversation list to dual port pair configuration
            -single -- reset conversation list to single port pair configuration


    traffic_case example:
                {
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'framecount': 1,
                                 'stress': True, 'linerate': False, 'forwarding_schm': 'bridging', 'iteration': 1,
                                 'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec',
                                 },
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'framecount': 1,
                                  'stress': True, 'linerate': False, 'forwarding_schm': 'bridging', 'iteration': 1,
                                  'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec',
                                  },
                        '27-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'framecount': 1,
                                  'stress': True, 'linerate': False, 'forwarding_schm': 'bridging', 'iteration': 1,
                                  'fifo': 8, 'lifo': 0, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec',
                                  },
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'NOMINAL',
                    'poe': None,
                    'runtime': 120,
                    'pretraf_cmds': [],
                    'traf_cmds': [],
                },

        :param kwargs:
        :return:
        """
        log.info("Set Traffic Conversation...")

        if not self._mode_mgr.goto_mode('TRAF'):
            log.warning("Unable to enter TRAF mode.")
            return False
        self._uut_prompt = self._mode_mgr.current_prompt

        # Applicable Inputs
        downlink_ports = kwargs.get('downlink_ports', list())
        uplink_ports = kwargs.get('uplink_ports', list())
        sup_ports = kwargs.get('sup_ports', list())
        stackswitching = 1 if kwargs.get('stackswitching', False) else 0
        loopback_direction = kwargs.get('loopback_direction', 'Forward')
        loopback_point = kwargs.get('loopback_point', 'PHY0')
        termwidth = kwargs.get('termwidth', 120)
        vmargin = kwargs.get('vmargin', None)
        poe_enabled = kwargs.get('poe_enabled', False)
        poe_port_group = kwargs.get('poe_port_group', 1)
        traf_cmds = kwargs.get('traf_cmds', list())
        poe_type = kwargs.get('poe_type', self._ud.uut_config.get('poe', {}).get('type', None))

        # Dependents
        # ----------
        # Uplink ports
        if self._uplink_card[0] or (self._uplink_card[1] and loopback_point.upper() == 'EXTERNAL'):
            # Note: An uplink test card can only perform External loopbacks!
            log.debug("Uplink card: {0}".format(self._uplink_card))
            log.debug("Port Groups: Downlink and Uplink.")
            available_port_groups = [downlink_ports, uplink_ports]
        else:
            log.debug("Port Groups: Downlink.")
            available_port_groups = [downlink_ports]
        log.debug("Available Port Groups = {0}".format(available_port_groups)) if self.__verbose else None
        # Aux ports
        if sup_ports:
            log.debug("Aux Port Groups: Supervisor (Modular).")
            available_aux_port_groups = [sup_ports]
        else:
            available_aux_port_groups = list()
        log.debug("Available Aux Port Groups = {0}".format(available_aux_port_groups)) if self.__verbose else None

        # Gather Current Conversation (determine active ports for traf)
        # -------------------------------------------------------------
        self.get_conversation()
        self.print_conversation()
        self._reconcile_port_pairs(available_port_groups, available_aux_port_groups)

        # Stardust Environment
        # --------------------
        stackrac_status = self._ud.uut_status.get('stackrac', aplib.FAIL)
        if stackrac_status == aplib.PASS:
            log.debug("StackRAC is operational; allow stackswitching setting.")
            self._uut_conn.send("SetEnv StackSwitching {0}\r".format(stackswitching), expectphrase=self._uut_prompt,
                                timeout=30, regex=True)
        else:
            log.warning("StackRAC is NOT operational; NO stack switching allowed.")
            self._uut_conn.send("SetEnv StackSwitching 0\r", expectphrase=self._uut_prompt, timeout=30, regex=True)
        self._uut_conn.send("SetEnv TermWidth {0}\r".format(termwidth), expectphrase=self._uut_prompt, timeout=30,
                            regex=True)
        self._uut_conn.send("SetEnv\r", expectphrase=self._uut_prompt, timeout=30, regex=True)

        # Voltage Margin
        # --------------
        if vmargin:
            for i in range(1, 4):
                if self._vmargin_func(device_instance=0, margin_level=vmargin) == aplib.PASS:
                    log.info("Voltage margin {0} for Traffic: PASSED.".format(vmargin))
                    break
            else:
                log.error("Cannot set traffic conversation since the voltage margin was NOT successful.")
                return False
        else:
            log.info("Using current voltage margin for traffic.")

        # Mode Config
        # -----------
        self._clear_recbuf()
        self._uut_conn.send("ConfMode {0} {1}\r".format(loopback_direction, loopback_point),
                            expectphrase=self._uut_prompt, timeout=30, regex=True)
        result, err_msgs = self._recbuf_good(err_msg="TRAFFIC ERROR: Error detected in ConfMode.",
                                              err_pattern='(?:ERR)|(?:FAIL)')
        if not result:
            return False

        # Conversation Config
        # -------------------
        if not self._config_conversation(available_port_groups):
            return False
        if not self._config_conversation(available_aux_port_groups, adjust=False):
            return False

        # PoE Equipment Configuration and Load Engagement
        # -----------------------------------------------
        if poe_enabled:
            log.info("PoE ENABLED for Traffic.")
            all_uut_poe_ports = self._ud.uut_config.get('poe', {}).get('uut_ports', None)
            if poe_type:
                active_uut_poe_ports = self._diags._build_pwr_budget_port_list(ports=all_uut_poe_ports,
                                                                               group_index=poe_port_group,
                                                                               poe_pwr_budget_groups=self._poe_pwr_budget_groups)
                log.info("UUT has {0} capability.".format(poe_type))
                log.info("All UUT PoE ports       : {0}".format(all_uut_poe_ports))
                log.info("Active PoE ports for Pwr: {0}".format(active_uut_poe_ports))

                if self._poe_loadbox_driver:
                    self._poe_loadbox_driver.show_equipment()
                    self._poe_loadbox_driver.reset()
                    self._poe_loadbox_driver.set_power_load()
                    self._poe_loadbox_driver.set_class(load_class=poe_type)
                    self._poe_loadbox_driver.connect(detect_signature='ok', external='on', auto='on')
                    self._poe_loadbox_driver.set_load_on()
                    time.sleep(2.0)
                    self._poe_uut_func(action='ON', poe_type=poe_type, poe_ports=active_uut_poe_ports)
                    poe_data = self._poe_loadbox_driver.get_instrument_data()
                    log.debug(poe_data)
                    common_utils.uut_comment(self._uut_conn, 'PoE Equip Measurements', poe_data)
                    self.poe_active = True
                    self._ud.uut_status['poe_equip_meas'] = poe_data

                else:
                    log.warning("No PoE Equipment Driver available for Traffic, therefore PoE will not be engaged.")
            else:
                log.info("UUT has NO PoE capability indicated by product definition.")
        else:
            log.info("PoE DISABLED for Traffic.")

        # Custom Traffic Commands per traffic case
        # ----------------------------------------
        for traf_cmd in traf_cmds:
            self._clear_recbuf()
            self._uut_conn.send("{0}\r".format(traf_cmd), expectphrase=self._uut_prompt, timeout=30, regex=True)
            time.sleep(self.RECBUF_TIME)
            result, err_msgs = self._recbuf_good(err_msg="TRAFFIC ERROR: Problem with {0}.".format(traf_cmd),
                                                  err_pattern='(?:ERR)|(?:FAIL)')
            if not result:
                return False

        # Final Conversation Config
        # -------------------------
        self._clear_recbuf()
        self._uut_conn.send("ApplyConfig\r", expectphrase=self._uut_prompt, timeout=120, regex=True)
        time.sleep(self.RECBUF_TIME)
        result, err_msgs = self._recbuf_good(err_msg="TRAFFIC ERROR: Problem applying conversation config.",
                                              err_pattern='(?:ERR)|(?:FAIL)')
        self.get_conversation()
        self.print_conversation()

        self._ud.uut_status['traf_conversation_result'] = result

        return result

    def print_conversation(self):
        """
        :return:
        """
        log.debug("Traffic Conversation")
        if self._conversation:
            for c in self._conversation:
                log.debug('{0}'.format(c))
        else:
            log.debug("No conversation captured.")
        return

    def get_conversation(self):
        """ Get Conversation (INTERNAL)
        Pull the traffic conversation setup from diags.

        Example snippet:
        GEN2
        C# Ports Lpbk Dir  Speed  Dpl Crossover FID FrameSize  FrameCount F MaxIt Log Aneg  R   Pwr   Disconn  MACSec  UPOE
        ---------------------------------------------------------------------------------------------------------------------
        01 01/02 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F08 00/00 F OFF/OFF -D-/-D- OFF/OFF OFF/OFF
        02 03/04 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F08 00/00 F OFF/OFF -D-/-D- OFF/OFF OFF/OFF
        03 05/06 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F08 00/00 F OFF/OFF -D-/-D- OFF/OFF OFF/OFF
        25 49/50 Phy0 Fwd   A/A   A/A  -- / --  Def   64/         1/      B 1     F08 00/00 F               OFF/OFF
        26 51/52 Phy0 Fwd   A/A   A/A  -- / --  Def   64/         1/      B 1     F08 00/00 F               OFF/OFF
        27 53/54 Phy0 Fwd   A/A   A/A  -- / --  Def   64/         1/      B 1     F08 00/00 F               OFF/OFF
        28 55/56 Phy0 Fwd   A/A   A/A  -- / --  Def   64/         1/      B 1     F08 00/00 F               OFF/OFF

        GEN3
        C#  Ports Lpbk Dir  Speed  Dpl Crossover FID FrameSize  FrameCount F MaxIt Log Aneg  R   Pwr   Disconn  MACSec  UPOE  PCH
        ------------------------------------------------------------------------------------------------------------------------------
        001  1/2  Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        002  3/4  Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        003  5/6  Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        004  7/8  Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        010 19/20 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        011 21/22 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        012 23/24 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF OFF/OFF
        013 25/26 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF
        014 27/28 Phy0 Fwd   A/A   A/A Auto/Auto Def   64/         1/      B 1     F008 00/00 F OFF/OFF

        Parse data and provide list of tuples.
        Output:
        [('01','01/02','Phy0','Fwd','A/A','A/A','Auto/Auto','Def','64/','1/','B','1','F08','00/00','F','OFF/OFF','-D-/-D-','OFF/OFF','OFF/OFF'),
         ('02','03/04','Phy0','Fwd','A/A','A/A','Auto/Auto','Def','64/','1/','B','1','F08','00/00','F','OFF/OFF','-D-/-D-','OFF/OFF','OFF/OFF'),
         ('03','05/06','Phy0','Fwd','A/A','A/A','Auto/Auto','Def','64/','1/','B','1','F08','00/00','F','OFF/OFF','-D-/-D-','OFF/OFF','OFF/OFF')]
        :return:
        """
        log.debug("Getting current conversation...")
        self._clear_recbuf()
        p = re.compile(
            '(?m)^[ \t]*(?P<conv>[0-9]+)[ \t]+(?P<pair>[0-9]+/[0-9]+)[ \t]+(?P<lpbk>[\S]+)[ \t]+(?P<dir>[\S]+)[ \t]+(?P<speed>[\S]+)[ \t]+'
            '(?P<dplx>[\S]+)[ \t]+(?P<xover>.*?/.*?)[ \t]+(?P<fid>[\S]+)[ \t]+(?P<size>[\S]+)[ \t]+(?P<fcnt>[\S]+)[ \t]+(?P<fwd>[\S]+)[ \t]+'
            '(?P<iter>[0-9]+)[ \t]+(?P<log>[\S]+)[ \t]+(?P<aneg>[\S]+)[ \t]+(?P<restart>[\S])[ \t](?P<remaining>.*)')

        self._uut_conn.send("ShowConf\r", expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(self.RECBUF_TIME)
        m = p.findall(self._uut_conn.recbuf)
        # Note: Conversation MUST be put in a standardized format since diag versions print differently (leading vs. no-leading zeroes).
        self._conversation = list()
        for c in m:
            r = ['', '', '', '']
            c15 = c[15].split(' ')
            for i, v in enumerate(c15):
                if i < 4:
                    r[i] = v
            self._conversation.append((c[0],
                                       '{0:02d}/{1:02d}'.format(int(c[1].split('/')[0]), int(c[1].split('/')[1])),
                                       c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13],
                                       c[14], r[0], r[1], r[2], r[3]))
        return True

    def run_conversation(self, name, **kwargs):
        """ Run Conversation

        **WARNING**: Entry in & out of monitor mode must allow some settling time (e.g. 1 min)
                     before reading results!!

                     Use 'showresult' after stopping traffic!

        :param name:
        :param kwargs:
        :return:
        """
        log.info("Run Traffic Conversation...")

        if not self._mode_mgr.goto_mode('TRAF'):
            log.warning("Unable to enter traf mode.")
            return False
        self._uut_prompt = self._mode_mgr.current_prompt

        # Input
        runtime = kwargs.get('runtime', 120)
        status_interval = kwargs.get('status_interval', 100)
        monitor_prompt = kwargs.get('monitor_prompt', 'Monitor]')
        poe_type = kwargs.get('poe_type', self._ud.uut_config.get('poe', {}).get('type', None))

        log.info("RUNNING: {0} ...".format(name))
        log.info("Traffic Runtime        : {0} secs".format(runtime))
        log.info("Traffic Status Interval: {0} secs".format(status_interval))

        # Start and Monitor
        # -----------------
        result_list = []
        _, server_mktime = common_utils.getservertime()
        try:
            self._uut_conn.send("Start\r", expectphrase=monitor_prompt, timeout=180, regex=True)
        except apexceptions.TimeoutException:
            log.warning("Did NOT see Monitor prompt after traffic Start!")
            log.warning("Trying second attempt...")
            self._uut_conn.send("\r", expectphrase=monitor_prompt, timeout=60, regex=True)
        except apexceptions.IdleTimeoutException:
            log.warning("No activity with Monitor prompt after traffic Start!")
            log.warning("Trying second attempt...")
            self._uut_conn.send("\r", expectphrase=monitor_prompt, timeout=60, regex=True)

        _, server_mktime1 = common_utils.getservertime()
        elapsed_time = server_mktime - server_mktime1
        while elapsed_time < runtime:
            _, server_mktime1 = common_utils.getservertime()
            self._clear_recbuf()
            log.debug("Traffic Status...")
            self._uut_conn.send(" ", expectphrase=monitor_prompt, timeout=60, regex=True)
            log.debug("Checking for error conditions...")
            time.sleep(self.RECBUF_TIME)
            if re.search('(?:ERR)|(?:FAIL)', self._uut_conn.recbuf):
                log.error('TRAFFIC ERROR: Traffic packet status.')
                result_list.append(False)
                break
            log.debug("Traffic Counters...")
            self._uut_conn.send("=", expectphrase=monitor_prompt, timeout=60, regex=True)
            log.debug("Checking system status...")
            self._uut_conn.send("X", expectphrase=self._uut_prompt, timeout=60, regex=True)
            if not self._get_sysstat(**kwargs):
                log.error('TRAFFIC ERROR: System status.')
                result_list.append(False)
                log.debug("Graceful return to traffic monitor...")
                self._uut_conn.send("monitor\r", expectphrase=monitor_prompt, timeout=30, regex=True)
                break
            log.debug("Returning to traffic monitor...")
            self._uut_conn.send("monitor\r", expectphrase=monitor_prompt, timeout=30, regex=True)
            _, server_mktime2 = common_utils.getservertime()
            status_time = server_mktime2 - server_mktime1
            elapsed_time = server_mktime2 - server_mktime
            remaining_time = runtime - elapsed_time if runtime >= elapsed_time else 0
            log.info("Time: Elapsed/Remaining = {0} / {1} secs, (for status = {2} secs).".format(elapsed_time,
                                                                                                 remaining_time,
                                                                                                 status_time))
            sit_time = status_interval if status_interval < remaining_time else remaining_time
            if sit_time > 0:
                log.info("Time: Continue traffic run = {0}".format(sit_time))
                time.sleep(sit_time)
        # Exit
        # MUST get a final traffic result since diags queue is not completely updated from above loop (even if result_list has failures).
        log.debug("Traffic Status (Final)...")
        self._clear_recbuf()
        self._uut_conn.send(" ", expectphrase=monitor_prompt, timeout=60, regex=True)
        time.sleep(self.RECBUF_TIME)
        self._uut_conn.send("=", expectphrase=monitor_prompt, timeout=60, regex=True)
        self._uut_conn.send("Q", expectphrase=self._uut_prompt, timeout=60, regex=True)
        time.sleep(5.0)
        self._uut_conn.send("ShowResult -l:2\r", expectphrase=self._uut_prompt, timeout=60, regex=True)
        result, err_msgs = self._recbuf_good(err_msg="TRAFFIC ERROR: Traffic packet status (final).",
                                              err_pattern='(?:ERR)|(?:FAIL)')
        result_list.append(result)
        if all(result_list):
            # Additional data for Eng Debug.
            self._uut_conn.send("ShowResult -l:4\r", expectphrase=self._uut_prompt, timeout=60, regex=True)
        log.info("Traffic Conversation Done.")

        # Shutdown PoE Power (if required)
        # --------------------------------
        if self.poe_active:
            log.info("{0} Shutdown...".format(poe_type))
            self._poe_uut_func(action='OFF', poe_type=poe_type)
            time.sleep(1.0)
            self._poe_loadbox_driver.set_load_off()
            self._poe_loadbox_driver.reset()
            log.info("PoE Shutdown: DONE.")

        return all(result_list)

    def config_uplink_test_card(self, uplink_ports):
        if not uplink_ports:
            log.debug("No uplink ports defined.")
            self._uplink_card = (None, None)
            self._uplink_is_fru = False
            return self._uplink_card

        uplink_port_pairs_and_speed = []
        for port_set in uplink_ports.keys():
            port_pairs, _ = self._build_port_pairs(port_set)
            for port_pair in port_pairs:
                uplink_port_pairs_and_speed.append(
                    (port_pair[0], port_pair[1], uplink_ports[port_set].get('speed', None)))
        if uplink_port_pairs_and_speed:
            log.debug("Uplink Port Pairs and Speed: {0}".format(
                uplink_port_pairs_and_speed if uplink_port_pairs_and_speed else 'NOT defined; default will be used.'))
        if self._uplink_is_fru:
            log.debug('Uplink is FRU type.')
            self._uplink_card = self._callback.peripheral.get_uplink_card_type()
            self._callback.peripheral.set_uplink_test_card(self._uplink_card[1], uplink_port_pairs_and_speed)
        else:
            log.debug('Uplink is built-in.')
            self._uplink_card = ('Built-in NM', None)

        return self._uplink_card

    def set_attrs(self, **kwargs):
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt = self._mode_mgr.uut_prompt_map['STARDUST']
        self._poe_loadbox_driver = self._diags._equip.poe_loadbox if hasattr(self._diags._equip, 'poe_loadbox') else None
        self._poe_uut_func = self._diags._operate_poe_uut
        self._poe_pwr_budget_groups = kwargs.get('poe_pwr_budget_groups', 0)  # Number of port groups to subdivide
        self._vmargin_func = self._diags.vmargin_test
        self._temperature_func = self._diags.temperature_test
        self._serdeseye_func = None
        self._uut_ports = kwargs.get('uut_ports', self._ud.uut_config.get('uut_ports', None))  # UUT ports for traf
        self._uplink_is_fru = kwargs.get('uplink_is_fru', self._ud.uut_config.get('uplink_is_fru', True))
        self._modular = True if self._ud.category == 'MODULAR' else False
        self._traffic_cases = kwargs.get('traffic_cases', self._ud.uut_config.get('traffic_cases', None))
        return

    # Internal methods ----------------------------------------------------------------------------------------
    def _build_port_pairs(self, ports, adjust=True):
        """ Build Port Pairs (INTERNAL)
        Create a standard list of port pairs based on a string range or list.
        Note: If the range is odd numbered; the LAST port in the list is dropped!!
        :param (str) ports: Represents a range or list of ports to be paired up.
        :param (bool) adjust: True if need to make port numbering adjustment (e.g. modular)
        :return (tuple):[(a, b), ...] , ['a/b', ...]
        """
        log.debug("Build port pairs '{0}'...".format(ports)) if self.__verbose else None
        if not ports:
            return [], []
        port_list_interim = common_utils.expand_comma_dash_num_list(ports)
        if adjust:
            port_list = self._adjust_uut_modular_ports(port_list_interim)
        else:
            port_list = port_list_interim
        if len(port_list) % 2 != 0:
            log.warning(
                "The ports {0} do not contain an even number for pairing; last port will be ignored!".format(ports))
            port_list.pop()
        port_pairs = sorted([(a, b) for a, b in zip(port_list[::2], port_list[1::2])])
        conv_pairs = sorted(['{0:02d}/{1:02d}'.format(a[0], a[1]) for a in port_pairs])
        log.debug("Port Pairs: '{0}'".format(port_pairs)) if self.__verbose else None
        log.debug("Conv Pairs: '{0}'".format(conv_pairs)) if self.__verbose else None
        return port_pairs, conv_pairs

    def _build_conversation_list(self, ports, adjust=True):
        log.debug("Build conversation list from '{0}'...".format(ports)) if self.__verbose else None
        _, conv_pairs = self._build_port_pairs(ports, adjust=adjust)
        conv_map = {t[1]: int(t[0]) for t in self._conversation}
        conv_list = [conv_map[cp] for cp in conv_pairs if cp in conv_map]
        log.debug("Conversation List: '{0}'".format(conv_list)) if self.__verbose else None
        return conv_list

    def _reconcile_port_pairs(self, port_group_list, aux_port_group_list):
        """ Reconcile Port Pairs (INTERNAL)
        Check the current conversation port pairs and compare them to the traffic case port pairs being requested.
        If there are differences, some current port pairs may be removed and the new port pairs will be added.

        Examples of elements of port_grouped_sets/aux_port_grouped_sets:
        downlink_ports = {'1-48':  {'speed': '10', 'size': 1518}}
        sup_ports =      {'1-8':   {'speed': '10', 'size': 1518}}
        uplink_ports =   {'25-26': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518},
                          '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518}}
        The dict is the port group.
        The dict key is the port set.

        :param (list) port_group_list: List of dicts of Traf case port descriptions
                                         Ex. [downlink_ports, uplink_ports]
        :param (list) aux_port_group_list: List of dicts of Traf case port descriptions for ports other than the primary.
                                           These are supplemental ports, e.g. virtual ports on modular systems.
                                         Ex. [sup_ports, other_ports]
        :return (list): Form of ['01/02', '03/04', ...]
        """
        log.debug("Reconcile ports...")
        log.debug("Port group list = {0}".format(port_group_list))

        # Standard Ports
        port_set_list = []
        for port_group in port_group_list:
            port_set_list += port_group.keys()
        new_standard_port_pairs = []
        for port_set in port_set_list:
            _, conv_pairs = self._build_port_pairs(port_set, adjust=True)
            new_standard_port_pairs += conv_pairs

        # Aux Ports
        aux_port_set_list = []
        for port_group in aux_port_group_list:
            aux_port_set_list += port_group.keys()
        new_aux_port_pairs = []
        for port_set in aux_port_set_list:
            _, conv_pairs = self._build_port_pairs(port_set, adjust=False)
            new_aux_port_pairs += conv_pairs

        # All Traffic port pairs
        log.debug("Standard Port Pairs = {0}".format(new_standard_port_pairs))
        log.debug("Aux Port Pairs      = {0}".format(new_aux_port_pairs))
        new_port_pairs = sorted(new_standard_port_pairs + new_aux_port_pairs)
        log.debug("Traf Case port pairs requested : {0}".format(new_port_pairs))
        current_port_pairs = sorted([p[1] for p in self._conversation]) if self._conversation else []
        log.debug("Currently configured port pairs: {0}".format(current_port_pairs))
        if new_port_pairs != current_port_pairs:
            diff_pairs = sorted(list(set(new_port_pairs).symmetric_difference(set(current_port_pairs))))
            log.debug("Reconfiguring port pairs: {0}".format(diff_pairs))
            for p in diff_pairs:
                if p in current_port_pairs:
                    log.debug("Removing {0}".format(p))
                    p2s = p.split('/')
                    self._uut_conn.send("ConfPairs {0},{1} -delete\r".format(int(p2s[0]), int(p2s[1])),
                                        expectphrase=self._uut_prompt, timeout=30, regex=True)
                if p in new_port_pairs:
                    log.debug("Adding {0}".format(p))
                    p2s = p.split('/')
                    self._uut_conn.send("ConfPairs {0},{1} -add\r".format(int(p2s[0]), int(p2s[1])),
                                        expectphrase=self._uut_prompt, timeout=30, regex=True)
            # Get the new conversation after it was modified.
            self.get_conversation()
        else:
            log.debug("New port pairs match currently configured pairs.")
        return new_port_pairs

    def _config_conversation(self, target_port_groups, adjust=True):
        if not target_port_groups:
            return True
        for ports_group in target_port_groups:
            for ports in ports_group:
                conversation_list = str(self._build_conversation_list(ports, adjust=adjust)).replace(' ', '')[1:-1]
                log.debug("Ports: {0} --> Conv: {1}".format(ports, conversation_list))
                # platform generic
                confc_params = '-speed:{0} -duplex:{1} -crossover:{2} -size:{3}'. \
                    format(ports_group[ports].get('speed', 'AUTO'),
                           ports_group[ports].get('duplex', 'AUTO'),
                           ports_group[ports].get('crossover', 'AUTO'),
                           ports_group[ports].get('size', 64))
                confc_params += ' -n:{0}'.format(ports_group[ports]['framecount']) if ports_group[ports].get(
                    'framecount', None) else ''
                confc_params += ' -stress' if ports_group[ports].get('stress', None) else ''
                confc_params += ' -linerate' if ports_group[ports].get('linerate', None) else ''
                confc_params += ' -{0}'.format(ports_group[ports].get('forwarding_schm', 'bridging'))
                confc_params += ' -iteration:{0}'.format(ports_group[ports].get('iteration', 1))
                # platform specific (no defaulting)
                confc_params += '{0}'.format(
                    ' -fifo:{0}'.format(ports_group[ports]['fifo']) if 'fifo' in ports_group[ports] else '')
                confc_params += '{0}'.format(
                    ' -lifo:{0}'.format(ports_group[ports]['lifo']) if 'lifo' in ports_group[ports] else '')
                confc_params += '{0}'.format(
                    ' -{0}'.format(ports_group[ports]['frames_link']) if 'frames_link' in ports_group[
                        ports] else '')  # norestart (default)
                confc_params += '{0}'.format(
                    ' -{0}'.format(ports_group[ports]['macsec_mode']) if 'macsec_mode' in ports_group[
                        ports] else '')  # nomacsec (default)
                # do the big config!
                self._clear_recbuf()
                self._uut_conn.send("ConfConversation {0} {1}\r".format(conversation_list, confc_params),
                                    expectphrase=self._uut_prompt, timeout=120, regex=True)
                time.sleep(self.RECBUF_TIME)
                result, err_msgs = self._recbuf_good(err_msg="TRAFFIC ERROR: Error detected in ConfConversation.",
                                                      err_pattern='(?:ERR)|(?:FAIL)')
                if not result:
                    return False

                # Mode Config again (but with specific conversation list IF it was specified in the traffic case).
                # This allows a traffic case to be built where some ports may have external while others have internal loopback for example.
                # Typically NOT used but provides flexibilty (esp. for proto testing).
                confm_params = ''
                confm_params += ' {0}'.format(ports_group[ports]['loopback_direction']) if ports_group[ports].get(
                    'loopback_direction', None) else ''
                confm_params += ' {0}'.format(ports_group[ports]['loopback_point']) if ports_group[ports].get(
                    'loopback_point', None) else ''
                if confm_params:
                    self._clear_recbuf()
                    self._uut_conn.send("ConfMode {0} {1}\r".format(confm_params, conversation_list),
                                        expectphrase=self._uut_prompt, timeout=30, regex=True)
                    time.sleep(self.RECBUF_TIME)
                    result, err_msgs = self._recbuf_good(
                        err_msg="TRAFFIC ERROR: Error detected in ConfMode for specific conversations.",
                        err_pattern='(?:ERR)|(?:FAIL)')
                    if not result:
                        return False
        return True

    def _get_sysstat(self, **kwargs):
        """ Get System Status (INTERNAL)
            1. Info on PoE
            2. Voltage check based on margin*
            3. Temperature check based on corner*
        *Note: Temperature and voltage test steps MUST have been previously run to get an "active" status.
               Once the status is established, then checking can occur during traffic testing.
               A SKIP is allowed for all status types assuming it is a valid skip (e.g. simulated temperature).
        :return:
        """
        result = True
        if self.poe_active:
            regs = self._poe_uut_func(action='GETREG')
            common_utils.print_large_dict(regs)

        if self.active_voltage_margin:
            for i in range(1, 4):
                voltage_margin_result = self._vmargin_func(device_instance=0,
                                                           margin_level=self.active_voltage_margin, check_only=True)
                if voltage_margin_result == aplib.PASS or voltage_margin_result == aplib.SKIPPED:
                    break
            else:
                log.error("TRAFFIC Voltage Margin: FAILED. Attempt = {}".format(i))
                result = False

        if self.active_temperature:
            temperature_result = self._temperature_func(operational_state='traffic',
                                                        temperature_corner=self.active_temperature)
            if temperature_result != aplib.PASS and temperature_result != aplib.SKIPPED:
                log.error("TRAFFIC Temperature Check: FAILED.")
                result = False

        if self._serdeseye_func:
            serdeseye_result = self._serdeseye_func(**kwargs)
            if serdeseye_result != aplib.PASS and serdeseye_result != aplib.SKIPPED:
                log.error("SERDESEYE Check: FAILED.")
                result = False

        return result

    def _adjust_uut_modular_ports(self, ports):
        if not self._modular:
            return ports
        if self._ud.modular_type == 'linecard':
            log.debug("Modular linecard ports, redefining...")
            di = int(self._ud.device_instance)
            log.debug("Device instance = {0}".format(di))
            log.debug("Ports = {0}".format(ports))
            new_ports = [di + p for p in ports]
            return new_ports
        else:
            log.warning("Modular device was indicated but there is no uut_config data available.")
            return ports

    def _recbuf_good(self, err_msg, err_pattern='(?:ERR)|(?:FAIL)'):
        result = True
        err_msgs = list()
        if re.search(err_pattern, self._uut_conn.recbuf):
            log.error(err_msg)
            result = False
            for line in self._uut_conn.recbuf.splitlines():
                if re.search(err_pattern, line):
                    log.debug(line)
                    err_msgs.append(line)
        return result, err_msgs

    def _clear_recbuf(self, force=False, waittime=None):
        if self.USE_CLEAR_RECBUF or force:
            self._uut_conn.clear_recbuf()
            _waittime = waittime if waittime else self.RECBUF_CLEAR_TIME
            time.sleep(_waittime)
        return

