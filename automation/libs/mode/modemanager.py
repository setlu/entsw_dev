"""
========================================================================================================================
Mode Manager
========================================================================================================================

Use this module to create a "Mode Manager" which can manage all modes of a UUT.
(See the class docstring for more details.)

This is STRICTLY for UUT modes ONLY.
========================================================================================================================
"""

# Python
# ------
import os
import sys
import collections
import logging
import re
import time
import importlib
import parse
import inspect
import argparse

# BU Lib
# ------
from ..utils.common_utils import func_details
from pathfinder import PathFinder

# Apollo
# ------
# Excluded for standalone execution.
if __name__ != '__main__':
    import apollo.libs.lib as aplib
    from apollo.engine import apexceptions

__title__ = "Mode Manager"
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


class ExceptionModeManager(Exception):
    pass


class ModeManager(PathFinder):
    """
    This class facilitates using the PathFinder class (node/path navigation) to manage entering/exiting
    the entire set of modes a UUT is capable of having.
    Since mode manipulation can include rebooting or waiting on a power cycle, two additional functions are
    included for use or override.

    Intended user methods for use in sequence steps or support functions are the following:
        1. is_mode(...)
        2. goto_mode(...)
        3. wait_for_boot(...)
        4. power_on(...)
        5. print_uut_prompt_map()

    User properties:
        1. mode_module            = (obj) Module containing product-specific transition functions used by this class.
        2. current_mode           = (str) Current mode of the UUT (read only).
        3. current_prompt         = (str) Current prompt of the UUT (read only).
        4. current_prompt_pattern = (str) Regex prompt pattern for the current mode.
        5. uut_prompt_map         = (list of tuples) Mode and associated prompt of form [('MODE', 'prompt'), ...]
        6. uut_conn               = (obj) Apollo connection for the UUT.

    A special method for 'standalone' mode to create a product-specific skeleton for all the transition functions
    defined by the product state machine:
        1. build_product_skeleton()

    """
    MODE_RETRY_COUNT = 2
    RECBUF_TIME = 5.0
    RECBUF_CLEAR_TIME = 3.0
    USE_CLEAR_RECBUF = False
    DEFAULT_PROMPT_MAP = [
        ('BTLDR', 'switch:'),
        ('IOS', 'Switch>'),
        ('IOSE', 'Switch#'),
        ('SYMSH', '-> '),
        ('LINUX', r'(?:# )|(?:[\S]*# )'),
        ('STARDUST', r'(?:[A-Z][\S]*> )')]
    DEFAULT_BOOT_MODES = ['BTLDR', 'IOS', 'IOSE']
    DEFAULT_STATEMACHINE = {
        'BTLDR': [('LINUX', 5), ('IOS', 10)],
        'LINUX': [('BTLDR', 7), ('STARDUST', 3)],
        'IOS': [('IOSE', 2)],
        'IOSE': [('BTLDR', 10), ('IOS', 2)],
        'STARDUST': [('LINUX', 4), ('TRAF', 3), ('DIAG', 2)],
        'TRAF': [('STARDUST', 1)],
        'DIAG': [('STARDUST', 1)],
    }

    def __init__(self, standalone=False, **kwargs):
        log.info(self.__repr__())
        kwargs['statemachine'] = kwargs.get('statemachine', ModeManager.DEFAULT_STATEMACHINE)
        PathFinder.__init__(self, **kwargs)

        self.verbose_level = kwargs.get('verbose_level', 1)               # Verbosity level for log.debug in SEQ LOG
        self.auto_connect = kwargs.get('auto_connect', True)              # Turn on UUT conn if necessary when True
                                                                          # Note: This might require a power_on &
                                                                          #       a wait_for_boot routine.
        self.uut_prompt_map = \
            kwargs.get('uut_prompt_map', ModeManager.DEFAULT_PROMPT_MAP)       # UUT prompt map dict (processed)
        self.possible_boot_modes = \
            kwargs.get('possible_boot_modes', ModeManager.DEFAULT_BOOT_MODES)  # Default modes to boot up in

        # Internals/Derived
        self._callback = kwargs.get('callback', None)
        self.__apollo_go = kwargs.get('apollo_go', True)
        self.__mode_module = kwargs.get('mode_module', None)              # Prod-specific module for transistion funcs
        self.__uut_conn = kwargs.get('uut_conn', None)                    # UUT connection object (from Apollo)
        self.__current_mode = kwargs.get('current_mode', None)            # Current mode (defined in UUT statemachine)
        self.__current_prompt = None                                      # Actual UUT prompt (for the current mode)
        self.__current_prompt_pattern = None                              # Regex prompt pattern (for current mode)
        self.__uut_active_prompts = dict()                                # Dynamically updated dict of live UUT prompts
        self.__path = []                                                  # Path to get from src to dst node
        self.__pathhistory = []                                           # List of previous nodes already traversed
        self.__standalone = standalone                                    # True = this module running as a CLI
        self.__trans_func_args = kwargs.get('trans_func_args', None)      # (Option) args for each trans func
        self.__wait_for_boot_custom = kwargs.get('wait_for_boot', None)   # (Option) custom 'wait_for_boot'
        self.__uut_mode_output = dict()                                   # Output of UUT console keyed by trans funcs
        ModeManager.USE_CLEAR_RECBUF = kwargs.get('use_clear_recbuf', False)
        ModeManager.MODE_RETRY_COUNT = kwargs.get('mode_retry_count', 2)

        if not self.__standalone:
            if not self.__uut_conn:
                msg = "Mode Manager requires a UUT connection!"
                log.error(msg)
                raise ExceptionModeManager(msg)
            # Clear any previous data for good measure in case connections remained open & power was left on for debug.
            log.debug("  Clear recbuf...")
            self.__clear_recbuf()
            # Load product-specific mode module
            log.debug("  Load module...")
            self.__load_module()
            # Display structure data
            self.print_state_machine()
            self.__check_transition_functions()

        else:
            # Running in stand-alone; the mode module may or may not exist.
            # If a string for the mode module is given (NOT the object) then assume the module does not
            # exist while in stand-alone.
            if inspect.ismodule(self.__mode_module):
                log.debug("  Valid module.")
            else:
                module_name = str(self.__mode_module) if self.__mode_module else 'unknown'
                self.__mode_module = type('DummyObject', (), {'create_mode_manager': None})
                self.__mode_module.__name__ = module_name

        return

    def __str(self):
        doc = "{0}{1}\n{2}{3}\n{4}{5}\n{6}{7}\n{8}{9}".\
            format(self.__class__.__name__, self.__doc__,
                   self.is_mode.__name__, self.is_mode.__doc__,
                   self.goto_mode.__name__, self.goto_mode.__doc__,
                   self.wait_for_boot.__name__, self.wait_for_boot.__doc__,
                   self.power_on.__name__, self.power_on.__doc__)
        return doc

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ATTRIBUTES -------------------------------------------------------------------------------------------------------
    @property
    def mode_module(self):
        return self.__mode_module

    @property
    def uut_conn(self):
        return self.__uut_conn

    @property
    def current_mode(self):
        return self.__get_current_mode()

    @current_mode.setter
    def current_mode(self, newvalue):
        if newvalue in self.__uut_prompt_map.keys():
            self.__current_mode = newvalue
            self.__current_prompt = self.__uut_prompt_map.get(newvalue)
            self.__current_prompt_pattern = self.__uut_prompt_map.get(newvalue)
        else:
            log.error("Cannot set current_mode = {0}".format(newvalue))

    @property
    def uut_prompt_map(self):
        return self.__uut_prompt_map

    @uut_prompt_map.setter
    def uut_prompt_map(self, newvalue):
        self.__uut_prompt_map_raw = newvalue
        self.__uut_prompt_map = collections.OrderedDict(self.__reduce_uut_prompt_map())
        self.__reset_active_uut_prompt_map()
        self.__available_modes = self.__uut_prompt_map.keys()

    @property
    def current_prompt(self):
        self.__current_prompt = self.__get_current_prompt()
        return self.__current_prompt

    @property
    def current_prompt_pattern(self):
        return self.__current_prompt_pattern

    @property
    def uut_mode_output(self):
        return self.__uut_mode_output

    # USER Methods -----------------------------------------------------------------------------------------------------
    #
    def show_version(self):
        log.info(self.__repr__())

    @func_details
    def is_mode(self, query_mode, refresh=False):
        """ Is Mode
        Compare current mode to the mode in question.
        If this object's attribute has not been initialized then actively get the current mode.
        :param query_mode: The mode we are asking about.
        :param refresh: Force to get the current prompt/mode and reset the current_mode setting.
        :return: True if actual mode is the same as query.
        """
        if self.__need_to_abort():
            log.warning("ABORT in progress...")
            return False

        if self.__current_mode and not refresh:
            log.debug("Using existing current mode...") if self.verbose_level > 0 else None
        else:
            log.debug("Updating current mode...") if self.verbose_level > 0 else None
            self.__current_mode = self.__get_current_mode()
        # Now test it
        ret = True if query_mode == self.__current_mode else False
        msg = " Mode NOT confirmed." if not ret else ''
        log.info("Is mode: current='{0}'  query='{1}'  ({2}{3})".format(self.__current_mode, query_mode, ret, msg))
        return ret

    @func_details
    def goto_mode(self, dstmode, srcmode='', funcargs=None, pathtype='MINCOST', statefulreturn=False, **kwargs):
        """ Goto Mode
        User interface for getting the UUT into the requested mode.
        This function can also automatically detect the current mode so that the user only needs to provide the
        destination mode!  Example script usage:  xx.goto_mode('MYMODE')
        NOTE: This function requires inheritance from PathFinder class!
        :param (str) dstmode: Destination mode to go to. [REQUIRED]
        :param (str) srcmode: Current mode if not specified. (OPTIONAL)
        :param (dict) funcargs: Any optional function arguments to be passed to the transition functions.
                         This is a dictionary of dicts with top-level keys set as the name of the transition functions
                         and the values set as the dicts to pass to the functions.
                         This allows specific dicts each of which maps to a specific transition function.
                         It is up to the user to define the function specific dicts and how they are used.
                         This is a flexibility feature for generic parameter passing and should only be used on an
                         as-needed basis to keep code complication to a minimum.
        :param (str) pathtype: Optional to override if something other than default 'MINCOST' is desired.
                         Valid selections: 'MINCOST', 'MAXCOST', 'MINHOP', 'MAXHOP'
        :param (bool) statefulreturn: Force the previous state to be used when returning from the destination
                               (overrides the state machine).  Normally not needed since the sm definition has
                               stateful data but it is provided as an optional override feature.
        :param (**dict) kwargs: Options for passing to ALL transistion functions from a direct call.
                            Provides the most flexibility; the transistion functions must understand what is being
                            pushed as input.

        :return (bool): True if the UUT arrived at the destination mode.
        """
        ret = False
        if self.__need_to_abort():
            log.warning("ABORT in progress...")
            return ret

        try:
            if not funcargs and self.__trans_func_args:
                # If transistion function arguments not explicitly given then use instantiated if available.
                # Note: Explicit overrides instantiated.
                funcargs = self.__trans_func_args
            if self.__mode_module is None:
                raise ExceptionModeManager("A product (or product family) module for mode transition functions is unknown.")
            # Always autodetect current mode (time consuming but fool-proof)
            current_mode = self.__get_current_mode()
            # Check to make sure we determined a mode.
            if not current_mode:
                raise ExceptionModeManager("Cannot process goto_mode due to null current mode.")
            # Set source mode based on this function call or history.
            if not srcmode:
                # Source mode (aka current mode) was not explicitly provided; check if it was already set.
                if self.__current_mode:
                    if current_mode != self.__current_mode:
                        log.warning("Current mode was changed outside of the normal process!")
                        self.__current_mode = current_mode
                else:
                    self.__current_mode = current_mode
                    log.debug("Current mode was auto-detected.") if self.verbose_level > 0 else None
                # Now set the source mode since 1) it was not given and 2) the current mode has been established.
                srcmode = self.__current_mode
            else:
                log.info("Source mode was explicitly provided.")
                if not isinstance(srcmode, str):
                    raise ExceptionModeManager("Source mode must be a string; explicit type is incorrect.")
                if current_mode != srcmode:
                    log.warning("Explicit source mode ({0}) does NOT match current mode ({1}); "
                                "explicit will be overridden.".format(srcmode, current_mode))
                    srcmode = current_mode
                    self.__current_mode = current_mode
                else:
                    self.__current_mode = srcmode
            # Final current & source mode
            log.info("Current mode = {0}".format(self.__current_mode))
            if srcmode == dstmode:
                ret = True
                log.info("Already in requested mode; no action to take.")

            # State Machine processing
            recalc_loop_count = 0
            while not ret \
                    and self.__current_mode != dstmode \
                    and recalc_loop_count < ModeManager.MODE_RETRY_COUNT \
                    and not self.__need_to_abort():
                log.debug("Process path...") if self.verbose_level > 0 else None
                if self.__pathhistory and self.__pathhistory[-1][1]:
                    # A previous most recent stateful node was detected.
                    previousstate = [self.__pathhistory[-1][0]]
                    log.debug("Using previous state = {0}".format(previousstate)) if self.verbose_level > 0 else None
                else:
                    previousstate = []

                # Get the path from state machine and run the transition functions!
                self.__path = self.get_path(srcmode, dstmode,
                                            pathtype=pathtype, withcost=False, followpath=previousstate)
                ret = self.__walkpath(self.__path, self.__mode_module, funcargs, **kwargs)
                if not ret and self.__current_mode != dstmode:
                    # Attempt path recalculation at point of mode failure and try again.
                    # This allows "stateful" modes with no history to be adjusted on the fly.
                    # This usually happens when a stateful mode was entered manually and then
                    # automation is started (without history).
                    # It can also happen if a "stubborn" condition exists, e.g. the image file is non-existent.
                    srcmode = self.__current_mode
                    recalc_loop_count += 1
                    log.info("Path recalculation attempt {0}...".format(recalc_loop_count))
                elif ret and self.__current_mode != dstmode:
                    # This condition can occur when mode path is empty and nothing to do for the walk
                    # BUT dstmode is not reached which means an interruption in the mode walk occurred
                    # so the walkpath result must be changed.
                    ret = False
                    recalc_loop_count += 1
                    log.info("Path recalculation attempt {0} due to interrupt...".format(recalc_loop_count))

            # endwhile

            if self.statefulnodes[dstmode] or statefulreturn:
                # Statetful node was indicated (or a stateful return was forced) therefore we need to SET the flag
                # in the historical path for the last previous state.
                log.debug("Stateful") if self.verbose_level > 0 else None
                if self.__pathhistory:
                    previous_state = self.__pathhistory.pop()
                    self.__pathhistory.append((previous_state[0], True))

            log.debug("Final path history = {0}".format(self.__pathhistory)) if self.verbose_level > 0 else None

        except apexceptions.ScriptAbortException as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        except Exception as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
            ret = False
        finally:
            log.debug("Goto Mode status = {0}".format(ret)) if self.verbose_level > 0 else None
            if not ret:
                log.error("UUT mode not reachable!")
                # Do not raise Exception("UUT mode not reachable!") here.
                # Allow higher level to handle.
            return ret

    @func_details
    def goto_mode_of_least_cost(self, target_modes):
        """ Mode
        Go to the mode among a list of modes that has the least cost (i.e. shortest time scale).
        Return both the original mode and the new mode so that a return to the original mode can be done later.
        :param (list or str) target_modes:
        :return (tuple): new_mode, old_mode
        """
        new_mode = None
        if not target_modes:
            return None, None
        target_modes = [target_modes] if not isinstance(target_modes, list) else target_modes
        old_mode = self.current_mode
        for tmode in target_modes:
            if old_mode and old_mode == tmode:
                new_mode = old_mode
                log.debug("Already in requested mode.")
                break
        else:
            log.debug("Current mode is not any of the target modes.")
            log.debug("Looking for an easy mode move...")
            change_mode = self.get_least_cost_node(old_mode, target_modes)
            log.debug("Going to mode: {0}".format(change_mode))
            if self.goto_mode(change_mode):
                new_mode = change_mode
            else:
                log.error("Problem trying to change mode.")
        return new_mode, old_mode

    @func_details
    def wait_for_boot(self, boot_mode=None, boot_msg=None, boot_interim_msgs=None, capture=None,
                      timeout=600, idle_timeout=200):
        """ Wait For Boot
        Method wrapper to "wait for boot" using one of the following:
            1. Internal "generic" __wait_for_boot()
            2. External "custom"  __wait_for_boot_custom()

        Both methods can use the following parameters:
        :param (list|str) boot_mode: Possible boot mode(s) from the UUT.  Derived from state machine definitions.
                                     This may be a single mode or a list of modes for more than one boot scenario
                                     (e.g. bootloader or IOS).
        :param (str) boot_msg: The product specific boot START UP message; should be only one.
                               This may be a regex pattern.
        :param (str) boot_interim_msgs: Regex patterns for subsequent messages before the final state.
        :param (list) capture: Any product specific boot messages to be searched and saved. Given by a list of
                               tuples in the form (id, pattern) where id=arbitrary string, pattern is a "parse"
                               module pattern that is saved as a key:value pair to the uut_config.
        :param (int) timeout: Time to wait for prompt after power-on or command boot.
        :param (int) idle_timeout: Time to wait if the connection is not receiving.
        :return : tuple of boolean for success, and dict of values found based on interim_msgs' parse patterns
        """
        found_prompt = False
        found_items = None
        self.__reset_active_uut_prompt_map()

        if self.__need_to_abort():
            log.warning("ABORT in progress...")
            return found_prompt, found_items

        if not boot_mode:
            log.debug("Using default boot modes since the modes were not provided.")
            boot_mode = self.DEFAULT_BOOT_MODES
            # raise ExceptionModeManager("A boot mode from the state machine must be provided.")

        log.debug("Possible boot modes searched  = {0}".format(boot_mode)) if self.verbose_level > 0 else None
        log.debug("Available modes for uut       = {0}".format(self.__available_modes)) if self.verbose_level > 0 else None

        # Custom wait_for_boot
        if self.__wait_for_boot_custom:
            log.debug("Custom 'wait_for_boot'...")
            return self.__wait_for_boot_custom(boot_mode=boot_mode,
                                               boot_msg=boot_msg,
                                               boot_interim_msgs=boot_interim_msgs,
                                               capture=capture,
                                               timeout=timeout, idle_timeout=idle_timeout)

        log.debug("Generic 'wait_for_boot'...")
        return self.__wait_for_boot(boot_mode=boot_mode,
                                    boot_msg=boot_msg,
                                    boot_interim_msgs=boot_interim_msgs,
                                    capture=capture,
                                    timeout=timeout, idle_timeout=idle_timeout)

    @func_details
    def power_on(self, **kwargs):
        """ Power On
        Method wrapper to run a power on function for connecting the UUT to the connection object.
        This is only needed when attempting to get the current UUT mode AND the UUT has not yet been powered on.
        It is typically used in automatic electronic detection of a UUT PID.
        A product/station's power on/off routines will be a separate class; this method is a placeholder for the
        'ON' function.
        NOTE: This is accessed via a callback property.
        :param kwargs: Any params the routine might need.
        :return (bool): True = connection and power on was successful.
        """
        if self.__need_to_abort():
            log.warning("ABORT in progress...")
            return False

        if self._callback:
            log.debug("Connect to UUT via 'power._open_on()'...")
            return self._callback.power._open_on()

        log.debug("There is no connect/power routine available.")
        return True

    @func_details
    def print_uut_prompt_map(self):
        """ Show UUT Prompt Map
        Print the prompt map table.
        :return:
        """
        log.info("=" * 80)
        log.info("PROMPT MAP")
        log.info("{0:<25} {1:<45} {2}".format("Node", "Prompt", "Raw"))
        log.info("-" * 25 + " " + "-" * 45 + "-" * 70)
        i = 0
        for node in self.__uut_prompt_map.keys():
            log.info("{0:<25} {1:<45} {2}".format(node, self.__uut_prompt_map[node], self.__uut_prompt_map_raw[i]))
            i += 1
        log.info("=" * 80)
        return

    @func_details
    def build_product_mode_skeleton(self):
        """
        Use this method to produce a product-specific skeleton mode module with all the transistion functions defined by
        the product's state machine.  The output could be printed to the screen for copy and paste or saved
        to a file directly.
        Note: This should only be called from 'standalone' mode.
        """
        log.info("Printing transistion functions skeleton mode for product UUT...")
        title = "Transistion Functions for {0}\n".format(self.__mode_module.__name__)
        skeleton = ""
        skeleton += r'"""' + "\n" + \
                    "-" * len(title) + "\n" \
                    "{0}".format(title) + \
                    "-" * len(title) + "\n" \
                    r'"""' + "\n" + \
                    "# Python Imports\n" \
                    "# --------------\n" \
                    "import sys\n" \
                    "import os\n" \
                    "import re\n" \
                    "import logging\n" \
                    "import time\n" \
                    "import collections\n" \
                    "\n" \
                    "# Apollo  Imports\n" \
                    "# ---------------\n" \
                    "from apollo.libs import lib as aplib\n" \
                    "from apollo.engine import apexceptions\n" \
                    "from apollo.engine import utils\n" \
                    "\n" \
                    "# Cisco Library Imports\n" \
                    "# ---------------------\n" \
                    "# import here\n" \
                    "\n" \
                    "# BU Specific Imports\n" \
                    "# -------------------\n" \
                    "# <ADD YOUR BU IMPORTS HERE WHICH SUPPORT YOUR PRODUCT TRANSISTION FUNCTIONS.>\n" \
                    "# from apollo.scripts.<bu>.libs.utils.common_utils import func_details\n" \
                    "\n" \
                    "log = logging.getLogger(__name__)\n" \
                    "thismodule = sys.modules[__name__]\n"
        skeleton += "\n\n" \
                    "# Product specific transisiton functions given below.\n" \
                    "# DO NOT call these directly; use the ModeManager class instance and the goto_mode() method.\n" \
                    "# ------------------------------------------------------------------------------------------\n"
        for mode in sorted(self.statedefinitions.keys()):
            for nextmode in sorted(self.statedefinitions[mode]):
                funcname = "{0}_to_{1}".format(mode, nextmode[0]).lower()
                skeleton += "def {0}\n".format(funcname + "(pp, **kwargs):") + \
                            r'    """ Product specific transition from {0} to {1}'.format(mode, nextmode[0]) + "\n" + \
                            "    :param pp: Product Pointer class object.\n" \
                            "    :param kwargs: optional.\n" \
                            r'    """' + "\n" + \
                            "    # Place product specific code here.\n" + \
                            "    ret = True\n" + \
                            "    return ret\n" + \
                            "\n"
        return skeleton

    # INTERNAL Methods -------------------------------------------------------------------------------------------------
    #
    def __reduce_uut_prompt_map(self):
        """ Reduce the UUT Prompt Map
        This routine converts the UUT prompt map from a 3-element per tuple list to the
        standard 2-element per tuple list.  The "extension" is used for additional commands to get to the
        target mode when the prompt is IDENTICAL to another mode
        (e.g. "rommon" and "gold rommon" where the prompt is "switch:" for both).
        """
        if not self.__uut_prompt_map_raw:
            return ''
        upm = []
        for item_set in self.__uut_prompt_map_raw:
            mode, pattern, extension = item_set if len(item_set) == 3 else (item_set[0], item_set[1], None)
            upm.append((mode, pattern))
        return upm

    def __load_module(self):
        # Load product-specific module
        if self.__mode_module is not None:
            if isinstance(self.__mode_module, str):
                module_name = self.__mode_module
                try:
                    self.__mode_module = importlib.import_module(module_name, package=None)
                except (ExceptionModeManager, ImportError, ImportWarning) as e:
                    msg = "{0} {1} {2}".format(module_name, type(e).__name__.upper(), e.message)
                    log.error(msg)
                    raise ExceptionModeManager(msg)
            elif inspect.ismodule(self.__mode_module):
                log.debug("  Valid module: {0}".format(self.__mode_module))
            else:
                raise ExceptionModeManager("Cannot load module; possibly invalid name or non-existant.")
        else:
            raise ExceptionModeManager(
                "A product module defining the mode transitions must be given."
                "Use either the fullly pathed name of the module to import, or"
                "the actual imported module object.")

    def __mode_to_prompt(self, mode, use_map_only=False):
        """
        Look up the prompt (from the active repository or the prompt map) based on the mode provided.
        :param mode: A specific mode from the UUT state machine definition.
        :param use_map_only: Allows to bypass the active prompt repository.
        :return: The prompt or regex prompt pattern for the given mode.
        """
        if mode in self.__uut_active_prompts and not use_map_only:
            # Get the prompt from the active prompt repository.
            prompt = self.__uut_active_prompts[mode]
        else:
            # Get the prompt pattern from the prompt map.
            if mode in [a for a, b in self.__uut_prompt_map]:
                prompt = (b for a, b in self.__uut_prompt_map if a == mode).next()
            else:
                prompt = None
        return prompt

    def __prompt_to_mode(self, prompt):
        """
        Look up mode (defined by statemachine) based on prompt pattern match in the ordered tuple list (uut_prompt_map).
        If a pattern match occurs, update the current prompt repository with the match.
        Note: Mutually exclusive prompt patterns must exist when multiple patterns are made available to search from.
        The search order is important as the first pattern match gets the associated mode;
        it should therefore be the first and only match.
        RULE CONVENTION: Each UUT mode MUST have a mutually exclusive prompt.  However, there are instances where this
                         is NOT the case (ex. bootloader and golden bootloader both have the same prompt).
                         To accomodate this an extension element can be used which provides for a command and match
                         pattern to make a determination which mode the UUT is in.  Form is ('<command>', '<pattern>')

        :param (str) prompt: The active prompt pulled from the UUT.
        :return (str): The state machine mode associated with the UUT prompt.
        """
        ret_mode = None
        extension_flag = False
        log.debug("Prompt to match = '{0}'".format(prompt)) if self.verbose_level > 1 else None
        # Find pattern match(es)
        for item_set in self.__uut_prompt_map_raw:
            log.debug("PM Item = {0}".format(item_set)) if self.verbose_level > 1 else None
            mode, pattern, extension = item_set if len(item_set) == 3 else (item_set[0], item_set[1], None)
            log.debug("mode={0}  pattern={1},  extension={2}".
                      format(mode, pattern, extension)) if self.verbose_level > 1 else None
            try:
                re.match(pattern, prompt).group()
                ret_mode = mode
                # Dynamically update the prompt repository used by the transistion functions
                self.__uut_active_prompts[mode] = prompt
                log.debug("Match.") if self.verbose_level > 1 else None
                if not extension:
                    # Exit on first match if no extension command.
                    break
                else:
                    # Extension command allows different mode determination when the prompt is the same
                    # for multiple modes.
                    log.debug("Extension.") if self.verbose_level > 0 else None
                    extension_flag = True
                    if len(extension) != 2:
                        log.warning("Prompt map extension element MUST be of the form: ('<command>', '<pattern>').")
                        continue
                    self.__uut_conn.send('{0}\r'.format(extension[0]), expectphrase=prompt, timeout=30, regex=True)
                    if re.search(extension[1], self.__uut_conn.recbuf):
                        log.debug("Extension match.") if self.verbose_level > 0 else None
                        break
            except AttributeError:
                # Catch regex group() that are null items to allow iteration.
                log.debug("No match.") if self.verbose_level > 2 else None
        else:
            # Iterated thru all items and no match (i.e. did not catch a break).
            if not extension_flag:
                log.warning("Cannot find a matching prompt.")
            else:
                log.warning("Prompt match(s) found but no extension match. The last extension prompt will be used.")

        return ret_mode

    def __get_current_prompt(self):
        """
        Send a carriage return to the UUT and process the response with the expectation a prompt of some type is
        contained within the last line of the response.
        Wait time is required since the "send" intentionally has expectphrase as a regex general pattern with
        carriage return/line feed..
        NOTE: This function should not be called directly; obtain the current mode and the current prompt
        will also be updated.

        This module makes extensive use of Apollo's connection object for the UUT.
        Below are a handy list of known connection properites:
        my_attributes = dict(
                         uid=self.uid,
                         name=self.name,
                         protocol=self.protocol,
                         elapsedsec=self.elapsedsec,
                         error_phrases=self.error_phrases,
                         errormessage=self.errormessage,
                         foundphrase=self.foundphrase,
                         power_connection=self.power_connection,
                         power_status=self.power_status,
                         recbuf_size=len(self.recbuf),
                         sendesize=self.sendesize,
                         status=self.status,
                         timeout=self.timeout,
                         )
        :return: The processed prompt response from the UUT.
        """

        prompt = None
        try:
            if not hasattr(self.__uut_conn, 'status'):
                log.error("The connection object has no status attribute; cannot determine state.")
                return prompt

            if self.__uut_conn.status != aplib.STATUS_OPEN:
                log.debug("Connection status = {0}".format(self.__uut_conn.status))
                if not self.auto_connect:
                    log.warning("The UUT is NOT connected and auto-connect is disabled.")
                    log.warning("No prompt available for discovery.")
                    return prompt

                log.warning("The UUT connection needs to be opened...")
                self.__uut_conn.open()
                time.sleep(2)
                if self.__uut_conn.status != aplib.STATUS_OPEN:
                    raise ExceptionModeManager('The UUT connection is NOT open!')
                # The connection is newly opened so the UUT could be booting from power up.
                # If the unit was already powered up, the timeout will occur while waiting for boot
                # and this is a "don't care".

                if self.__need_to_abort():
                    log.debug("Aborting prompt detection (prior to power up)...")
                    return None

                log.warning("Since the connection was newly opened while attempting to get the current UUT prompt,")
                log.warning("a 'power on' routine might be needed. Check specific product and station requirements.")
                log.warning("If a 'power on' was performed here, then a 'wait_for_boot' needs to execute also.")
                if self.power_on():
                    self.wait_for_boot(boot_mode=self.possible_boot_modes)

            if self.__need_to_abort():
                log.warning("Aborting prompt detection (prior to stimulus)...")
                return None

            # Some amount of time is needed for the recbuf to populate, esp. on slow BAUD systems or loaded servers.
            # Do this because the receive is completely unknown and we do not know what to expect or WHEN to expect it.
            # After the first send do not check for any specific response, instead wait for a potential prompt
            # only if the communication is not idle for the indicated time.
            # Look for anything with a carriage return/new line OR
            #  the Linux prompt without a carriage return (special break case).
            speculative_prompt = r'(?:.*[\r\n]+)|(?: # )'
            log.debug("Stimulus 1") if self.verbose_level > 0 else None
            self.__uut_conn.send('\r', expectphrase=None, timeout=30, regex=True)
            try:
                self.__uut_conn.waitfor(speculative_prompt, timeout=90, idle_timeout=60, regex=True)
            except apexceptions.IdleTimeoutException:
                log.debug("Idle with no previous prompt.") if self.verbose_level > 0 else None

            if self.__need_to_abort():
                log.warning("Aborting prompt detection (during stimulus)...")
                return None

            log.debug("Stimulus 2") if self.verbose_level > 0 else None
            self.__uut_conn.send('\r', expectphrase=speculative_prompt, timeout=30, idle_timeout=60, regex=True)
            # Used for deep debug; comment out normally. log.debug('recbuf = {!r}'.format(self.__uut_conn.recbuf))
            recbuf_list = self.__uut_conn.recbuf.splitlines()
            if recbuf_list and len(recbuf_list) > 0:
                prompt = self.__uut_conn.recbuf.splitlines()[-1]
            else:
                log.debug("Stimulus did NOT produce any discernable prompt!") if self.verbose_level > 0 else None
        except Warning as w:
            log.warning('{0}'.format(w))
        except apexceptions.ConnectionFailure as e:
            log.error('UUT connection error.')
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
            # Don't re-raise exception; allow unknown prompt to return status.
            # All other exceptions will cause seq to fail.
        except (apexceptions.TimeoutException, apexceptions.IdleTimeoutException) as e:
            log.error('UUT connection timeout.')
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        except Exception as e:
            log.error("UUT general exception.")
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
            # Do we need to propagate outside of this function.
        finally:
            log.info("Prompt = '{0}'".format(prompt))
            return prompt

    def __get_current_mode(self):
        """ Get Current Mode
        Get the current mode of the UUT assuming nothing is previously known.
        Look for the return prompt from a list of prompts for the product family.
        Since some prompts are specific to the image loaded and therefore dynamic, a pattern matching scheme is also
        employed when the default is not found and a search pattern is present.
        NOTE: Well known query prompts are answered by default as a best effort to avoid a non-matching situation.
        Multiple attempts are limited to prevent an infinite loop.
        :return (str): The mode based on the prompt map or search pattern that was found.
        """
        mode = None
        if self.__need_to_abort():
            log.warning("ABORT in progress...")
            return mode

        done = False
        last_effort = 0
        loop_count = 0
        while not done and loop_count < 3 and not self.__need_to_abort():
            loop_count += 1
            log.debug("Current mode determination attempt: {0}".format(loop_count))
            prompt = self.__get_current_prompt()

            if not prompt:
                log.debug("Did not get a prompt.  Keep trying...") if self.verbose_level > 0 else None
                continue

            mode = self.__prompt_to_mode(prompt)
            log.info('Mode = [{0}]'.format(mode))
            if mode:
                self.__current_mode = mode
                self.__current_prompt = prompt
                self.__current_prompt_pattern = self.__uut_prompt_map.get(mode, None)
                break
            else:
                # Try to check if unit is in some query prompt mode and answer default if so.
                # Since these are somewhat specific, not all 'query prompts' will be handled!
                # The UUT may also be in the middle of a long output.
                # (Also possibility of a bad recbuf; TBD.)
                log.debug("Unknown mode prompt = '{0}'".format(prompt))
                if re.match(r'(?i)(?:\[yes\])|(?i)(?:\[y\])', prompt):
                    log.info("A well known 'yes query' prompt detected; the default response will be provided.")
                    self.__uut_conn.send('y\r', expectphrase='.*', timeout=30, regex=True)
                elif re.match(r'(?i)(?:\[return\])', prompt):
                    log.info("A well known 'return' prompt detected; the default response will be provided.")
                    self.__uut_conn.send('\r', expectphrase='.*', timeout=30, regex=True)
                elif re.match(r'(?i)(?:command.*: )', prompt):
                    log.info("A well known 'command' prompt detected; the default response will be provided.")
                    self.__uut_conn.send('quit\r', expectphrase='.*', timeout=30, regex=True)
                elif re.match(r'.* > .*', prompt):
                    log.info("Inside a possible diags command; attempt break-out and reset.")
                    self.__uut_conn.send('\x03', expectphrase='.*', timeout=30, regex=True)
                    self.__uut_conn.send('\r', expectphrase='.*', timeout=30, regex=True)
                    self.__uut_conn.send('reset\r', expectphrase='.*', timeout=30, regex=True)
                    self.__uut_conn.send('\r', expectphrase='.*', timeout=30, regex=True)
                else:
                    if last_effort == 0:
                        log.info("Attempting to clear recbuf and try again...")
                        self.__clear_recbuf(force=True)
                        # Do not send anything here; just try to get a known prompt again.
                        # self.__uut_conn.send('\r', expectphrase='.*', timeout=60, idle_timeout=40, regex=True)
                        last_effort += 1
                    elif last_effort == 1:
                        log.info("Attempting <ctrl-C> exit from unknown state.")
                        self.__uut_conn.send('\x03', expectphrase='.*', timeout=30, regex=True)
                        self.__uut_conn.send('\r', expectphrase='.*', timeout=30, regex=True)
                        last_effort += 1
                    else:
                        done = True
                        log.info("Check the uut_prompt_map dictionary and the current UUT mode.")
                        # Allow null return; no raise Exception("Mode is indeterminant.")
                        log.warning("Mode is still unknown.  Keep trying...")
                        self.__clear_recbuf(force=True)
        else:
            # Did not catch a break; no mode was determined based on prompts that the unit presented and what is
            # known in the prompt map or in well-known query prompts.
            # raise Exception("Mode is indeterminant due to unknown prompt.") --> allow null return
            log.error("Mode is indeterminant due to unknown prompt, bad UUT state, or abort.")

        return mode

    def __reset_active_uut_prompt_map(self):
        """ Reset Active prompts
        This should be performed after a power cycle since prompts are context sensitive and are saved.
        :return:
        """
        self.__uut_active_prompts = dict()
        for mode, prompt_pattern in self.__uut_prompt_map.items():
            self.__uut_active_prompts[mode] = prompt_pattern
        return

    def __walkpath(self, modepath, moduleobj=None, argdicts=None, **kwargs):
        """
        A generic processing function to run the code for each transition function defined by the statemachine best path
        (modepath) until the UUT arrives at the destination mode.
        Run the product functions for each path transition to "walk" or complete the entire path of modes
        thereby getting into the destination mode requested from the originating source mode.
        The output of the UUT for each transition function is saved and could be used for later processing by the user.
        The history of the path "walk" is also saved in case any statefule mode must be returned to while
        processing the state machine.
        :param modepath: Path to follow from mode A to mode B; output from the get_path() method.
        :param moduleobj: Product module object containing all the functions for the given transitions.
        :param argdicts: Nested dicts for the specific transition function's args.
        :param kwargs:  External args applied by the user when calling "goto_mode(...)"; passed to all transition funcs.
        :return: True if the entire path was successfully "walked".
        """
        ret = True
        funcname = 'none'
        try:
            if len(modepath) == 0:
                raise Warning("Empty mode path; nothing to do!")

            log.info("Mode Path to Walk = {0}".format(modepath))

            funcnameformat = "{0}_to_{1}"
            for index in range(0, len(modepath) - 1):
                if type(modepath[index]) is tuple:
                    funcname = funcnameformat.format(modepath[index][0], modepath[index + 1][0]).lower()
                elif type(modepath[index]) is str:
                    funcname = funcnameformat.format(modepath[index], modepath[index + 1]).lower()
                else:
                    raise ExceptionModeManager("Path type is not a string or a tuple.")
                # Create the function name.
                # The convention is to use the mode names in lower case separated by "_to_" !
                func = getattr(moduleobj, funcname, None)
                if func is None:
                    raise ExceptionModeManager("Function not found '{0}'".format(funcname))

                # Get the specific dict for the corresponding function if there is one (optional).
                tkwargs = {}
                if argdicts:
                    tkwargs = argdicts.get(funcname, {})
                    if type(tkwargs) is not dict:
                        log.warning("Transition function '{0}' has the wrong ".format(funcname) +
                                    "data type for argument passing ({0}).".format(tkwargs))
                        tkwargs = {}

                # Append UUT Configuration for use by transition functions as tkwargs???
                # Note: There is no appending of uut_config: tkwargs.update(self._uut_config)
                # The transistion functions should pull in the UUT data.

                # Append kwargs from external call to the transition specific tkwargs.
                # Every transition function will get the external call kwargs data.
                tkwargs.update(kwargs) if kwargs else tkwargs

                # Now run the function and its arguments.
                # Pass this object's instance and the composite parameters.
                # if not func(self, **tkwargs):
                if not func(self._callback, **tkwargs):
                    ret = False
                    # Since the current mode could be unknown; attempt to get it by brute force when raising exception.
                    raise ExceptionModeManager("Transition function '{0}' returned unsuccessful result.".format(funcname))
                else:
                    # Capture all messages generated while making the transition.
                    # Indexed by the destination mode when saving.
                    self.__uut_mode_output[modepath[index + 1]] = self.__uut_conn.recbuf
                    # Update the current mode since the transition function was successful.
                    self.__current_mode = modepath[index + 1]

                    # Update path history
                    # This is a tuple list [(<state>, <use_flag>), ...]
                    if self.__pathhistory and self.__pathhistory[-1][0] == modepath[index + 1]:
                        # Backtracking
                        self.__pathhistory.pop()
                    else:
                        # New ground
                        self.__pathhistory.append((modepath[index], False))
                    log.debug("Current path history = {0}".
                              format(self.__pathhistory)) if self.verbose_level > 0 else None

                # Also check for abort
                if self.__need_to_abort():
                    log.exception("Walkpath node abort...")
                    raise apexceptions.ScriptAbortException("An ABORT was requested!")

        except Warning as w:
            log.info("{0}: {1}".format(type(w).__name__.upper(), w.message))
        except (Exception, apexceptions.ScriptAbortException, apexceptions.AbortException) as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
            log.warning("Transition function '{0}' FAILED.".format(funcname))
            self.__current_mode = self.__get_current_mode()
            ret = False
        finally:
            return ret

    def __wait_for_boot(self, boot_mode=None, boot_msg=None, boot_interim_msgs=None, capture=None,
                        timeout=600, idle_timeout=200):
        """ Generic Wait for Boot
        Generic boot processor that waits for a product to boot
            1) after a power cycle, OR
            2) after issuing some type of boot or load command while in IOS, or a rommon, etc.
        Success is given by finding the boot prompt.  Other messages can be parsed while the unit is booting but
        only after the boot was successful.
        Regex patterns may be supplied to support multiple boot scenarios; these should be coordinated among the
        patterns for boot_msg and the boot_mode list (if supplied).
        Some well known patterns for IOS are included by default.
        Note: The active prompt repository is cleared when an implied boot occurs.

        Example of using this method:
        result, _ = xx.wait_for_boot(boot_mode=['BTLDR', 'IOS', 'IOSE'],
                                     boot_msg='(?:Booting)|(?:System Bootstrap)|(?:Initializing)',
                                     capture=['MAC Address: {MAC_ADDR:S}', 'Model Number {MODEL_NUM:S}'])

        :param (list|str) boot_mode: Possible boot mode(s) from the UUT.  Derived from state machine definitions.
                                     This may be a single mode or a list of modes for more than one boot scenario
                                     (e.g. bootloader or IOS).
        :param (str) boot_msg: The product specific boot START UP message; should be only one.
                               This may be a regex pattern.
        :param (str) boot_interim_msgs: Regex patterns for subsequent messages before the final state.
        :param (list) capture: Any product specific boot messages to be searched and saved. Given by a list of
                               tuples in the form (id, pattern) where id=arbitrary string, pattern is a "parse"
                               module pattern that is saved as a key:value pair to the uut_config.
        :param (int) timeout: Time to wait for prompt after power-on or command boot.
        :return (bool, dict): Tuple of boolean for success, and dict of values found based on interim_msgs'
                              parse patterns.
        """
        found_prompt = False
        all_found_items = {}
        firmware_update_event = False
        reload_event = True

        try:
            # Beginning
            if boot_msg:
                log.debug("Waiting for start boot message...") if self.verbose_level > 0 else None
                log.debug("Startup boot message patterns = {0}".format(boot_msg)) if self.verbose_level > 0 else None
                try:
                    # There has to be sufficient idle time for some UUTs that do stackpower discovery.
                    self.__uut_conn.waitfor(boot_msg, timeout=240, idle_timeout=idle_timeout, regex=True)
                    log.debug("Starting boot message found = {0}".format(boot_msg))
                except (apexceptions.TimeoutException, apexceptions.IdleTimeoutException):
                    log.warning("Start boot message not found (timed-out).")
                    log.warning("IOS variants can ignore the initial message; boot processing will proceed anyway...")
            else:
                log.debug("No start boot message to wait for.") if self.verbose_level > 0 else None

            # Create prompt pattern from modes specified
            # The patterns must be in the correct regex form.
            boot_prompt_pattern = ''
            if isinstance(boot_mode, list):
                boot_prompt_list = [self.__mode_to_prompt(m) for m in boot_mode if m in self.__available_modes]
                bp_list = []
                for bp in boot_prompt_list:
                    bp = r'(?:{0})'.format(bp) if bp[:3] != '(?:' and bp[-1:] != ')' else bp
                    bp_list.append(bp)
                boot_prompt_pattern = '|'.join(bp_list)
            elif isinstance(boot_mode, str):
                bp = self.__mode_to_prompt(boot_mode)
                boot_prompt_pattern = r'(?:{0})'.format(bp) if bp[:3] != '(?:' and bp[-1:] != ')' else bp

            # Build boot pattern (adding "built-in" rommon & IOS patterns)
            boot_pattern = '|'.join([boot_prompt_pattern])
            rommon_question = r'(?:booting anyway (y/n)?)'
            reload_msg = r'(?:(?i)reload)'
            ios_booting = r'(?:(?i)switch[ _]?booting)'
            ios_fw_update = r'(?:(?i)Programming device)'
            ios_cfg_dialog = r'(?:configuration dialog\? \[yes/no\])'
            ios_return_prompt = r'(?:Press RETURN)'
            ios_pswd_prompt = r'(?:Password:)'
            ios_default_passwords = ['c', 'cisco', 'C', 'Cisco', 'cisco123']
            if 'IOS' in boot_mode:
                boot_pattern = '|'.join([boot_pattern,
                                         ios_booting,
                                         ios_fw_update,
                                         ios_cfg_dialog,
                                         ios_return_prompt,
                                         ios_pswd_prompt,
                                         reload_msg])
            if 'BTLDR' in boot_mode:
                boot_pattern = '|'.join([boot_pattern, rommon_question])

            # Build interim messages
            if boot_interim_msgs:
                if isinstance(boot_interim_msgs, list):
                    # Make the list into a regex non-capture OR'ed string
                    tmp = '|'.join([r'(?:{0})'.format(item) for item in boot_interim_msgs])
                    boot_interim_msgs = tmp
                elif boot_interim_msgs[:3] != '(?:' and boot_interim_msgs[-1:] != ')':
                    # Put string in correct regex form: non-capture OR'ed
                    boot_interim_msgs = r'(?:{0})'.format(boot_interim_msgs)
                # Other common misc boot interim patterns
                tftp_boot_prompt = '(?:reset? \[y\])'
                # Combine
                boot_interim_msgs = '|'.join([boot_interim_msgs, tftp_boot_prompt])

            # Pattern search
            if boot_prompt_pattern:
                log.debug("Search for boot pattern(s): 'bp={0}  bim={1}'".
                          format(boot_pattern, boot_interim_msgs)) if self.verbose_level > 0 else None
                loop_count = 1
                while not found_prompt and loop_count < 50 and not self.__need_to_abort():

                    active_pattern = '|'.join([boot_pattern, boot_interim_msgs]) if boot_interim_msgs else boot_pattern
                    time.sleep(2)
                    log.debug("Wait for active pattern: loop count = {0}".
                              format(loop_count)) if self.verbose_level > 0 else None
                    log.debug("Active pattern = {0}".format(active_pattern)) if self.verbose_level > 0 else None
                    self.__uut_conn.waitfor(active_pattern, timeout=timeout, idle_timeout=idle_timeout, regex=True)
                    time.sleep(self.RECBUF_TIME)

                    # Logic tree for all patterns (well known and provided)
                    # -----------------------------------------------------
                    if re.search(boot_prompt_pattern, self.__uut_conn.recbuf):
                        log.debug("Boot prompt pattern found!.") if self.verbose_level > 0 else None
                        found_prompt = True

                    elif boot_interim_msgs and re.search(boot_interim_msgs, self.__uut_conn.recbuf):
                        # The interim messages during boot up are a "one-shot" occurrence so as they are
                        # found, they are removed from the search pattern via a new pattern build up.
                        new_bim_list = []
                        for bim in boot_interim_msgs.split('|'):
                            if re.search(bim, self.__uut_conn.recbuf):
                                log.debug("Found: {0}".format(bim[3:-1])) if self.verbose_level > 0 else None
                                if bim == rommon_question:
                                    self.__uut_conn.send('y\r', expectphrase='.*[\r\n]+', timeout=90, idle_timeout=60,
                                                       regex=True)
                            else:
                                # Have NOT found yet, so keep it in the new list.
                                new_bim_list.append(bim)
                        boot_interim_msgs = '|'.join(new_bim_list)
                        if not boot_interim_msgs:
                            log.debug("Done with interim boot messages.") if self.verbose_level > 0 else None
                        log.debug("boot_interim_msgs logic done") if self.verbose_level > 0 else None

                    elif re.search(rommon_question, self.__uut_conn.recbuf):
                        log.debug("Rommon boot question...") if self.verbose_level > 0 else None
                        self.__uut_conn.send('n\r', expectphrase='.*[\r\n]+', timeout=90, idle_timeout=60, regex=True)
                        time.sleep(self.RECBUF_TIME)
                        log.debug("rommon_question logic done") if self.verbose_level > 0 else None

                    elif re.search(ios_return_prompt, self.__uut_conn.recbuf):
                        log.debug("IOS return prompt...") if self.verbose_level > 0 else None
                        # Send <return> to respond to the RETURN prompt!
                        self.__uut_conn.send('\r', expectphrase='.*[\r\n]+', timeout=90, idle_timeout=60, regex=True)
                        time.sleep(self.RECBUF_TIME)
                        # Note: After 'press RETURN' some units may take additional time before
                        #       getting to the prompt (e.g. stack manager activity).
                        #       Only send one carriage return!
                        log.debug("ios_return_prompt logic done") if self.verbose_level > 0 else None

                    elif re.search(ios_pswd_prompt, self.__uut_conn.recbuf):
                        log.debug("IOS password prompt...") if self.verbose_level > 0 else None
                        if len(ios_default_passwords) > 0:
                            self.__uut_conn.send('{0}\r'.format(ios_default_passwords.pop(0)),
                                               expectphrase=None, timeout=90, idle_timeout=60, regex=True)
                            time.sleep(self.RECBUF_TIME)
                        else:
                            log.warning("IOS default password attempts exhausted.")
                            log.warning("Manually remove the password for automation.")
                            log.error("Cannot fully complete boot process.")
                            break
                        log.debug("ios_pswd_prompt logic done") if self.verbose_level > 0 else None

                    elif re.search(ios_booting, self.__uut_conn.recbuf):
                        log.debug("IOS boot detected...") if self.verbose_level > 0 else None
                        # self.__uut_conn.send('\r', expectphrase=None, timeout=30)
                        log.debug("ios_booting logic done") if self.verbose_level > 0 else None

                    elif re.search(ios_cfg_dialog, self.__uut_conn.recbuf):
                        log.debug("IOS 'configuration dialog' prompt...") if self.verbose_level > 0 else None
                        self.__uut_conn.send('no\r', expectphrase='.*', timeout=30, regex=True)
                        time.sleep(self.RECBUF_TIME)
                        if re.search(r'terminate autoinstall\?', self.__uut_conn.recbuf):
                            log.debug("IOS 'terminate autoinstall' prompt...")
                            self.__uut_conn.send('yes\r', expectphrase=None, timeout=60, idle_timeout=30, regex=True)
                        log.debug("ios_cfg_dialog logic done") if self.verbose_level > 0 else None

                    elif re.search(ios_fw_update, self.__uut_conn.recbuf):
                        # This can take a long time > 5mins (allow for 12 mins timeout).
                        # After the update, IOS will force a reboot.
                        log.debug("IOS firmware update in progress...") if self.verbose_level > 0 else None
                        firmware_update_event = True
                        self.__clear_recbuf(force=True)
                        self.__uut_conn.send('', expectphrase=None, timeout=90, idle_timeout=60, regex=True)
                        log.debug("Waiting for: {0}".format(boot_msg)) if self.verbose_level > 0 else None
                        self.__uut_conn.waitfor(boot_msg, timeout=900, idle_timeout=200, regex=True)
                        log.debug("IOS firmware update reboot detected.") if self.verbose_level > 0 else None
                        self.__clear_recbuf(force=True)
                        log.debug("ios_fw_update logic done") if self.verbose_level > 0 else None
                        # no break   loop and continue checking...

                    elif re.search(reload_msg, self.__uut_conn.recbuf):
                        # Can be caused by multiple reboots of firmware upgrades.
                        # Can also be caused by the reload command.
                        log.debug("Reload message...") if self.verbose_level > 0 else None
                        reload_event = True
                        self.__clear_recbuf(force=True)
                        if 'software does not support this model' in self.__uut_conn.recbuf:
                            log.error("Unsupported software for this model!")
                            break
                        try:
                            self.__uut_conn.waitfor('.*', timeout=40, idle_timeout=20, regex=True)
                        except apexceptions.IdleTimeoutException:
                            self.__uut_conn.send('\r', expectphrase=None, timeout=40, idle_timeout=20, regex=True)
                        log.debug("reload_msg logic done") if self.verbose_level > 0 else None

                    else:
                        log.warning("Boot pattern found but no logic to process.")
                        log.warning("This could be an Apollo recbuf problem or a script oversight.")
                        log.warning("Sending a return and trying again...")
                        self.__uut_conn.send('\r', expectphrase=None, timeout=90, idle_timeout=60, regex=True)
                        log.debug("'catch all other' logic done")

                    # Prevent infinite loop
                    loop_count += 1
            else:
                # Need to ensure a prompt is associated with the requested mode.
                log.error("A boot prompt has NOT been established.")

            log.info("Wait for boot: DONE.")

            # Boot messages to capture (post processing)
            if capture:
                for pattern in capture:
                    found_items = parse.search(pattern, self.__uut_conn.recbuf)
                    if found_items:
                        for key in found_items.named.keys():
                            all_found_items[key] = found_items[key]
                            log.debug('Found {0} = {1}'.
                                      format(key, found_items[key])) if self.verbose_level > 0 else None

            else:
                log.debug("No interim boot messages to capture.") if self.verbose_level > 0 else None

            # Confirm
            if found_prompt:
                log.debug("Confirming prompt...") if self.verbose_level > 0 else None
                self.__uut_conn.send('\r', expectphrase=boot_prompt_pattern, timeout=60, regex=True)
                log.debug("The wait is over: prompt confirmed!") if self.verbose_level > 0 else None
                self.__clear_recbuf()

        except apexceptions.ConnectionFailure:
            log.error("Boot is incomplete.")
        except apexceptions.TimeoutException:
            if firmware_update_event:
                log.warning("Boot response timed out due to firmware update.")
            elif reload_event:
                log.error("Boot response timed out due to reload.")
            else:
                log.error("Boot response timed out.")
            found_prompt = False
        except apexceptions.IdleTimeoutException:
            if firmware_update_event:
                log.warning("Boot response stopped sending due to firmware update.")
            elif reload_event:
                log.error("Boot response stopped sending due to reload.")
            else:
                log.error("Boot response stopped sending.")
            found_prompt = False
        except apexceptions.ScriptAbortException as e:
            log.error("Aborting script...")
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        except Exception as e:
            log.warning("Wait for boot is incomplete.")
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
            raise ExceptionModeManager(e.message)
        finally:
            log.debug("Is prompt found: {0}".format(found_prompt))
            return found_prompt, all_found_items

    def __check_transition_functions(self):
        """
        Check that all of the transistion functions actually exist in the product module.
        The function list is a direct map of the state machine created for all the modes of a product.
        :return: True if all transition functions exist in the product module.
        """
        if self.verbose_level > 0:
            log.info("-" * 60)
            log.info("TRANSISTION FUNCTIONS REQUIRED")
        ret = True
        for mode in sorted(self.statedefinitions.keys()):
            for nextmode in sorted(self.statedefinitions[mode]):
                funcname = "{0}_to_{1}".format(mode, nextmode[0]).lower()
                func = None
                if self.__mode_module is not None:
                    func = getattr(self.__mode_module, funcname, None)
                if func is None:
                    stat = "  <--- ** NOT FOUND! **"
                    ret = False
                else:
                    stat = "  Good."
                log.info("{0:<30}{1}".format(funcname + "():", stat)) if self.verbose_level > 0 else None
        if self.verbose_level > 0:
            log.info("Module '{0}' status = {1}".format(self.__mode_module.__name__, ret))
            log.info("")
        return ret

    def __clear_recbuf(self, force=False, waittime=None):
        if self.USE_CLEAR_RECBUF or force:
            self.__uut_conn.clear_recbuf() if self.__apollo_go else None
            _waittime = waittime if waittime else self.RECBUF_CLEAR_TIME
            time.sleep(_waittime)
        return

    def __need_to_abort(self):
        return True if self.__apollo_go and aplib.need_to_abort() else False


def get_uut_statemachine_promptmap(cfg_module_name):
    """ Get UUT Config
    Use this in conjunction with standalone mode to read in the UUT state machine & prompt map.
    :param cfg_module_name:
    :return:
    """
    _uut_state_machine = dict()
    _uut_prompt_map = dict()
    try:
        cfg_module = importlib.import_module(cfg_module_name, package=None)
        if cfg_module.uut_state_machine:
            _uut_state_machine = cfg_module.uut_state_machine
        else:
            log.error("No UUT State Machine!")
        if cfg_module.uut_prompt_map:
            _uut_prompt_map = cfg_module.uut_prompt_map
        else:
            log.error("No UUT Prompt Map!")
    except ImportError as e:
        log.error("Cannot import {0}".format(cfg_module_name))
        log.error(e)
    finally:
        return _uut_state_machine, _uut_prompt_map


if __name__ == '__main__':
    # Use this for standalone execution.
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="Turn on verbosity for extra information (default off).")
    parser.add_argument("-d", "--docstring", dest="docstring", default=False, action="store_true",
                        help="Print ModeManager docstring..")
    parser.add_argument("-k", "--skeletonfile", dest="skeletonfile", default="myprodline_mode.py", action="store",
                        help="Skeleton file for the product mode file to be used by this module.")
    parser.add_argument("-c", "--configmodule", dest="configmodule", default=None, action="store",
                        help="Module containing the UUT statemachine and prompt map."
                             "Both of these are dicts with the required names:"
                             "'uut_state_machine', 'uut_prompt_map'.")
    args = parser.parse_args()
    mmd = {}
    if args.docstring:
        mm = ModeManager(True, **mmd)
        print(str(mm))
        print(repr(mm))

    if args.configmodule:
        uut_state_machine, uut_prompt_map = get_uut_statemachine_promptmap(args.configmodule)
        mmd = {
            'mode_module': os.path.splitext(os.path.basename(args.skeletonfile))[0],
            'uut_conn': None,
            'verbose': args.verbose,
            'statemachine': uut_state_machine,
            'uut_prompt_map': uut_prompt_map
        }
        mm = ModeManager(True, **mmd)
        mfile_content = mm.build_product_mode_skeleton()
        if args.skeletonfile == "myprodline_mode.py":
            print(mfile_content)
        else:
            try:
                fp = open(args.skeletonfile, mode='w+')
                log.debug("Writing...")
                fp.write(mfile_content)
                log.info("Your product mode skeleton file is at '{0}'".format(args.skeletonfile))
            except Exception as e:
                log.error("Exception during file write operation.")
                log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
                sys.exit(1)
    sys.exit(0)
