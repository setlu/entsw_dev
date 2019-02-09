""" Engineering Menu Utility
========================================================================================================================

This module provides a class to setup an interactive command menu system that will run a given set of
    1. test steps for a product,
    2. other custom misc functions.

The test steps employed come from a "test step collection module" given as part of the product descriptor input.

This menu system can be used for:
 a. Bench-style test/debug of UUT for early protos, production debug, etc.
 b. Iterative script debug,
 c. Test step development and validation.

The menu items come from two sources:
 1. Established menu items predefined in the class,
 2. Dynamically assigned menu items defined in the test step collection function's docstrings.
    The docstring item format for including the step function is as follows:
    ":menu: (enable=True, name=MyMenuItem, section=SomeSection, num=1, args=None)"
             enable: Turns menu item on/off
             name: Menu item name
             section: Locates the menu item in a specific section
             num: Numerical order of the dynamic items (predefined items are always listed first)
             args: Param is a textualized dict, e.g. args={'myparam': 'value'}.
    If the :menu: item does NOT contain all params, it will be ignored.

========================================================================================================================
"""

# Python
# ------
import sys
import logging
import collections
import inspect
import re
import ast

# Apollo
# ------
from apollo.libs import lib as aplib

# BU Lib
# ------
from common_utils import validate_ip_addr
from common_utils import validate_username
from common_utils import print_large_dict
from common_utils import ask_dict_question

__title__ = "Engineering Debug Menu Utility"
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
thismodule = sys.modules[__name__]


class EngineeringDebugMenu(object):

    MenuItem = collections.namedtuple('MenuItem', 'enable name section num args')

    CATEGORY_DEFAULTS = ['SWITCH', 'SUP', 'LINECARD', 'PERIPH']
    MENU_WIDTH = 25
    MD_DEFAULT = [
        ('________Power__________', ('', None)),
        ('POWER CYCLE ON',          ('_menu_power_cycle_on', None)),
        ('POWER OFF',               ('_menu_power_off', None)),
        ('________UUT____________', ('', None)),
        ('UUT CATEGORY',            ('_menu_uut_category', None)),
        ('UUT DESCRIPTOR',          ('_menu_uut_descriptor', None)),
        ('UUT CONFIG',              ('_menu_uut_config', None)),
        ('UUT STATUS',              ('_menu_uut_status', None)),
        ('MANUAL UUT CONFIG',       ('_menu_manual_uut_config', None)),
        ('________Config_________', ('', None)),
        ('________Mode___________', ('', None)),
        ('________Upgrade________', ('', None)),
        ('________Linux__________', ('', None)),
        ('________PCAMAP_________', ('', None)),
        ('________Diags__________', ('', None)),
        ('_______DiagTests_______', ('', None)),
        ('________IdPro__________', ('', None)),
        ('________Traffic________', ('', None)),
        ('_________IOS___________', ('', None)),
        ('_________DF____________', ('', None)),
        ('_________Ops___________', ('', None)),
        ('PAUSE',                   ('_menu_pause', None)),
        ('SOFT QUIT',               ('_menu_quit_soft', None)),
        ('QUIT',                    ('_menu_quit_hard', None)),
        ('COF',                     ('_menu_cof', None)),
        ('REM STATION CFG',         ('_menu_config_remote_station', None)),
        ('_________Data__________', ('', None)),
        ('_________Misc__________', ('', None)),
        ('__________-____________', ('', None)),

    ]

    def __init__(self, product_step_modules, ud, menu_descriptor=None, category=None):
        """ Start up the class
        :param (obj|list) product_step_modules: The modules containing the test "steps" for the product.
        :param (obj) ud: UUT Descriptor
        :param (list) menu_descriptor: Menu Descriptor data consists of a list of nested tuples in the following way:
                [('menu item', ('menu function name', <dict of args>)),  ...]
                Note: The 'menu_item' can be a "section title" whereby the function is null.
                      Section titles are identified by the name starting & ending with '_'.
                All menu functions can be from:
                    a) this class,
                    b) inherited from a subclass, or
                    c) built dynamically from docstrings in the Test Step Collection.
                This list defines what methods are used for the active menu from the class(es).
                The naming convention of the menu methods is '_menu_xxx'.
                Many of the menu functions just call a test step for a given product module.
                Some menu functions have specific roles defined in the class.
                Dynamic menu items are ADDED in addition to the standard items.
                The goal here is to offer flexibility with structure.

        :param (str) category: 'SWITCH', 'SUP', 'LINECARD', 'CABLE', etc.
        :return:
        """
        # INPUTS
        self._psms = product_step_modules if isinstance(product_step_modules, list) else [product_step_modules]
        self._ud = ud
        self._md = menu_descriptor if isinstance(menu_descriptor, list) else self.MD_DEFAULT
        self._category = category if category else self.CATEGORY_DEFAULTS

        self.result_list = []
        self.menu_cof = True
        self.menu_product_codename = 'Unknown'

        # Check some dicts
        if not self._psms:
            log.error("A Step Module MUST be included.")
            raise aplib.apexceptions.AbortException("Product Step module is missing.")

        return

    def __str__(self):
        doc = "{0}".format(self.__repr__())
        return doc

    def __repr__(self):
        return "{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__)

    def show_version(self):
        log.info(self.__repr__())

    def run(self):
        """ Run the Menu System
        Note: ALL _menu_xxx() functions must return the Apollo PASS/FAIL result.
        Many menu items directly call the step functions used in production; this should be from the
        'common_test_step_collection' AND '<product>_test_step_collection'.
        :return:
        """
        # Now add any dynamic menu items based on Test Step Collection docstrings.
        self._dynamic_menu_build()

        menu_dict = collections.OrderedDict(self._md)
        menu_list = menu_dict.keys()

        try:
            # Loop on Menu until user quits.
            cmd = None
            while cmd != 'QUIT' and cmd != 'SOFT QUIT' and not aplib.need_to_abort():
                log.info(' ')
                log.info('Engineering Utility')
                log.info('=' * 20)
                ps = ' ({})'.format(self._ud.product_selection) if self._ud.product_selection != self._ud.product_codename else ''
                msg = '{0} {1} {2} v{3}\n  Product: {4}{10}  PUID: [{5} {6}, {7} {8}, {9}]'.\
                    format(self._ud.product_line,
                           self._ud.product_family.upper(), __title__, __version__,
                           self._ud.product_codename,
                           self._ud.puid.pid, self._ud.puid.vid,
                           self._ud.puid.partnum, self._ud.puid.partnum_rev,
                           self._ud.puid.sernum,
                           ps)
                cmd = aplib.ask_question(msg, answers=menu_list, multi_select=False)
                log.info("Cmd = '{0}'".format(cmd))
                if cmd not in menu_dict.keys():
                    log.error("Fatal error with menu; command not recognized!")
                    log.error("This can occur when using the Apollo CLI with the '--body' option "
                              "and input items become out of sync.")
                    log.error("This can also occur when Apollo has an orphaned process via abort.")
                    raise Exception("Eng Menu sync.")
                if menu_dict[cmd] and cmd[0:3] != '___':
                    if isinstance(menu_dict[cmd][0], str):
                        func = getattr(self, menu_dict[cmd][0], None)
                    elif inspect.isfunction(menu_dict[cmd][0]):
                        func = menu_dict[cmd][0]
                    else:
                        func = None
                    kwargs = menu_dict[cmd][1]
                    # Execute function and collect results
                    if func:
                        full_result = func(**kwargs) if kwargs else func()
                        if isinstance(full_result, tuple):
                            result = full_result[0]
                            msg = full_result[1]
                        else:
                            result = full_result
                            msg = ''
                        if result == aplib.PASS:
                            self.result_list.append((cmd, True, msg))
                        elif result == aplib.SKIPPED:
                            # SKIPPED is a don't care therefore allow pass.
                            self.result_list.append((cmd, True, msg))
                        elif result == aplib.FAIL:
                            self.result_list.append((cmd, False, msg))
                        else:
                            # Other unknown results are a fail by default.
                            self.result_list.append((cmd, False, msg))
                        # Print results
                        log.info("Cmd Result: {0}.".format(result))
                        if not self.menu_cof and not all(self.result_list):
                            break
                    else:
                        log.debug("Cannot find function for menu entry: {0}".format(menu_dict[cmd][0]))

            else:
                # Exit the menu
                # Check for user abort
                if aplib.need_to_abort():
                    log.warning("An ABORT was requested!")
                    self.result_list.append((cmd, False, 'ABORT'))
                else:
                    # Graceful exit
                    self.result_list.append((cmd, True, ''))

        except (aplib.apexceptions.AbortException, aplib.apexceptions.ScriptAbortException, Exception) as e:
            log.exception(e)
            log.warning("Aborting Menu Utility")
            self.result_list.append(('ABORT', False, 'Menu ABORT'))
            self._menu_quit_soft()

        finally:
            # Consolidate for final result
            ret = aplib.PASS if all([r for c, r, m in self.result_list]) else aplib.FAIL
            log.debug("Final menu: {0}".format(ret))
            return ret

    # ==================================================================================================================
    # DYNAMIC MENU ITEMS
    def _dynamic_menu_build(self, verbose=False):
        """ Dynamically Build Menu
        Get Test Step functions documented in docstring in the test step collection module.
        Insert step items as part of the menu.

        Modifies the self._md (menu descriptor) list that was provided by the class user.
        :param (bool) verbose:
        :return:
        """
        all_step_functions = []
        for psm in self._psms:
            all_step_functions += [f for f in inspect.getmembers(psm, inspect.isfunction)]  # if f[0][0:6] == 'step__']
        if verbose:
            for i in all_step_functions:
                log.debug("{0}".format(i))

        menuized_step_functions = []
        p = re.compile(':menu:[ ]+\(enable=([\S]+),[ ]+name=(.*),[ ]+section=(.*),[ ]+num=(.*),[ ]+args=(.*)\)')
        log.debug("Dynamic Menu Build...")
        for f in all_step_functions:
            menu_items = p.findall(f[1].__doc__) if f[1].__doc__ else None
            log.debug("{0} --> {1}".format(f, menu_items)) if verbose else None
            if menu_items:
                for i in menu_items:
                    menu_item = self.MenuItem(i[0], i[1], i[2], i[3], i[4])
                    if menu_item.enable == 'True':
                        try:
                            args_d = ast.literal_eval(menu_item.args)
                        except (ValueError, SyntaxError):
                            log.warning("Problem with args param: '{0}' on menu item: '{1}".format(menu_item.args, menu_item.name))
                            args_d = None
                        menuized_step_functions.append((menu_item.section,
                                                        menu_item.num,
                                                        menu_item.name,
                                                        args_d,
                                                        f[0], f[1]))
                        if verbose:
                            log.debug("Section:{0}, {1}-Item:{2}, Args:{3}".format(menu_item.section,
                                                                                   menu_item.num,
                                                                                   menu_item.name,
                                                                                   args_d))
        menuized_step_functions.sort()
        for section, _, name, args, fname, func in menuized_step_functions:
            p = '[_]+{0}[_]+'.format(section)
            s = re.search(p, str(self._md)).group(0) if re.search(p, str(self._md)) else None
            t = (s, ('', None))
            if s:
                # section found
                i = self._md.index(t)
                for n in range(i + 1, len(self._md)):
                    if self._md[n][0][0:3] == '___':
                        # next section found, insert as last item to previous section
                        self._md.insert(n, (name, (func, args)))
                        break
                else:
                    # item append to last section
                    self._md.append((name, (func, args)))
            else:
                # new section and item append
                pad = (self.MENU_WIDTH - len(section)) / 2
                s2 = '_' * pad + section + '_' * pad
                s2 += '_' if len(s2) == self.MENU_WIDTH - 1 else ''
                self._md.append((s2, ('', None)))
                self._md.append((name, (func, args)))
        return

    # ==================================================================================================================
    # REQUIRED PREDEFINED MENU ITEMS
    # Power -----------------------------------------------------------------
    def _menu_power_cycle_on(self):
        for psm in self._psms:
            if hasattr(psm, 'power_cycle_on'):
                return psm.power_cycle_on()
        else:
            log.warning("The Product Step Modules have no 'power_cycle_on'.")
            log.warning("This menu item will be SKIPPED.")
            return aplib.SKIPPED

    def _menu_power_off(self):
        for psm in self._psms:
            if hasattr(psm, 'power_off'):
                return psm.power_off()
        else:
            log.warning("The Product Step Modules have no 'power_off'.")
            log.warning("This menu item will be SKIPPED.")
            return aplib.SKIPPED

    def _menu_clean_up(self):
        for psm in self._psms:
            if hasattr(psm, 'clean_up'):
                return psm.clean_up()
        else:
            log.warning("The Product Step Modules have no 'clean_up'.")
            log.warning("This menu item will be SKIPPED.")
            return aplib.SKIPPED

    # UUT --------------------------------------------------------------------
    def _menu_uut_category(self):
        self._ud.category = aplib.ask_question("Select the UUT Category:", answers=self._category)
        log.info("UUT category = {0}".format(self._ud.category))
        return aplib.PASS

    def _menu_uut_config(self):
        ans = aplib.ask_question("Select what to show:", answers=['ALL-compact', 'ALL-exploded', 'LOOKUP'], timeout=30)
        if ans == 'ALL-exploded':
            self._ud.print_uut_config(exploded=True)
        elif ans == 'ALL-compact':
            self._ud.print_uut_config()
        elif ans == 'LOOKUP':
            ans = aplib.ask_question("Enter key:")
            if ans in self._ud.uut_config:
                log.debug(print_large_dict(self._ud.uut_config[ans]))
            else:
                log.debug("Does not exist in uut_config.")
        return aplib.PASS

    def _menu_uut_descriptor(self):
        log.debug(self._ud.print_uut_descriptor())
        return aplib.PASS

    def _menu_uut_status(self):
        log.debug(self._ud.uut_status)
        return aplib.PASS

    def _menu_manual_uut_config(self):
        d = ask_dict_question("MANUAL uut_config Entry.\n"
                              "------------------------\n"
                              "WARNING: Use care when manipulating this data structure.\n")
        if d:
            self._ud.uut_config.update(d)
            log.debug("Saved.")
        else:
            log.debug("Nothing saved.")
        return aplib.PASS

    # Ops --------------------------------------------------------------------
    def _menu_pause(self):
        aplib.PAUSE()
        return aplib.PASS

    def _menu_quit_soft(self):
        log.debug("Soft quit...")
        self._ud.keep_connected = True
        self._show_menu_summary()
        self._menu_clean_up()
        # self._menu_power_off()
        return aplib.PASS

    def _menu_quit_hard(self):
        log.debug("Hard quit...")
        self._ud.keep_connected = False
        self._show_menu_summary()
        self._menu_clean_up()
        self._menu_power_off()
        return aplib.PASS

    def _menu_cof(self, preset=None):
        answer = aplib.ask_question('COF-Continue On Fail [{0}]:'.
                                    format(self.menu_cof), answers=['True', 'False']) if preset is None else preset
        if answer == 'True':
            self._ud.cof = True
        elif answer == 'False':
            self._ud.cof = False
        return aplib.PASS

    def _menu_config_remote_station(self):
        ud = aplib.apdicts.userdict

        # A Remote host server (hop for when the Apollo server cannot directly access the T/S or UUT)
        input_done = False
        ud['remote_station'] = {'server': {'ip': '', 'user': '', 'password': ''},
                                'uut': {'ip': '', 'port': '', 'user': '', 'password': ''}}
        while not input_done:
            ud['remote_station']['server']['ip'] = aplib.ask_question("Enter Remote Station Server IP (blank=none):")
            input_done = validate_ip_addr(ud['remote_station']['server']['ip']) if \
                ud['remote_station']['server']['ip'] else True
        if ud['remote_station']['server']['ip']:
            input_done = False
            while not input_done:
                ud['remote_station']['server']['user'] = aplib.ask_question("Enter Remote Station Username:")
                input_done = validate_username(ud['remote_station']['server']['user'])
            ud['remote_station']['server']['password'] = aplib.ask_question("Enter Remote Station Password:", ask_question_hidden=True)

        # A remote T/S
        input_done = False
        while not input_done:
            ud['remote_station']['uut']['ip'] = aplib.ask_question("Enter Remote Station UUT Console T/S IP:")
            input_done = validate_ip_addr(ud['remote_station']['uut']['ip'])
        ud['remote_station']['uut']['port'] = aplib.ask_question("Enter Remote Station UUT Console T/S Port:")

        if ud['remote_station']['uut']['ip']:
            ud['remote_station']['uut']['user'] = aplib.ask_question("Enter T/S Username:")
            if ud['remote_station']['uut']['user'].lower() == 'none' or ud['remote_station']['uut']['user'].lower() == 'skip':
                ud['remote_station']['uut']['user'] = None
            if ud['remote_station']['uut']['user']:
                ud['remote_station']['uut']['password'] = aplib.ask_question("Enter T/S Password:", ask_question_hidden=True)

        log.info("Remote Station")
        log.info("-" * 50)
        log.info("  Server IP            = '{0}'".format(ud['remote_station']['server']['ip']))
        log.info("  Server User          = '{0}'".format(ud['remote_station']['server']['user']))
        log.info("  UUT Console T/S IP   = '{0}'".format(ud['remote_station']['uut']['ip']))
        log.info("  UUT Console T/S Port = '{0}'".format(ud['remote_station']['uut']['port']))
        log.info("  UUT Console T/S User = '{0}'".format(ud['remote_station']['uut']['user']))
        log.info("  UUT Console T/S Pswd = '{0}'".format(ud['remote_station']['uut']['password']))

        return aplib.PASS

    def _show_menu_summary(self):
        log.debug(" ")
        title = "Sequential Summary Results of Menu Commands"
        log.debug(title)
        log.debug("-" * len(title))
        if len(self.result_list) > 0:
            index = 0
            for cmd, result, msg in self.result_list:
                index += 1
                log.debug("{0:>3d}. {1:<{2}s} = {3}  {4}".format(index, cmd, len(title) - 12, 'PASS' if result else 'FAIL', msg))
            log.debug("-" * len(title))
        else:
            log.debug("Nothing to report.")
        return
