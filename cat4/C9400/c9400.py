"""
C9400

[Catalyst]---->[Catalyst4]---->[C9400]
                                  ^
                                  |
                                  +--- Product Specific class objects.

NOTE: These class objects are used as a single instance to realize the entire functionality for end-to-end mfg testing
      of a specific product line.
      (Do not change the init order!)
"""
# Python
# ------
import sys
import logging

# Apollo
# ------
import apollo.libs.lib as aplib
import apollo.libs.locking as locking
import apollo.engine.apexceptions as apexceptions

# BU Libs
# ------
from apollo.scripts.entsw.libs.cat.uut_descriptor import UutDescriptor as _UutDescriptor
from apollo.scripts.entsw.libs.mode.modemanager import ModeManager as _ModeManager
from apollo.scripts.entsw.libs.mfg.process import Process as _Process
from apollo.scripts.entsw.libs.product_drivers.power import Power as _Power
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonC9400 as _RommonC9400
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapC9400 as _PcamapC9400
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC4K as _PeripheralC4K
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.traffic.traffic import Traffic as _Traffic
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.idpro.act2 import ACT2 as _ACT2
from apollo.scripts.entsw.libs.idpro.x509 import X509Sudi as _X509Sudi
import apollo.scripts.entsw.libs.equip_drivers.poe_loadbox as poe_loadbox
import apollo.scripts.entsw.libs.equip_drivers.traf_generator as traf_generator
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

# Product Specific
# ----------------
from ..common.catalyst4 import Catalyst9400 as _Catalyst9400
from ..common.stardust4 import StardustC9400 as _StardustC9400
from ..common.traffic4 import TrafficDiagsC9400 as _TrafficDiagsC9400
from ..common.traffic4 import TrafficSNTC9400 as _TrafficSNTC9400
from ..common import modes4 as _modes4
from ..common import _common_def
from ..common import _ios_manifest4
from .product_definitions import _product_line_def

__title__ = "C9400 Product Module"
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
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1}))
if not hasattr(aplib.conn, 'uutTN_aux'):
    setattr(aplib.conn, 'uutTN_aux', type('Conn', (), {'uid': 1, 'send': 1}))


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# C9400 (shared)
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class _C9400(_Catalyst9400):
    def __init__(self, family_filter):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, ios_manifest=_ios_manifest4,
                                uut_conn=self.uut_conn, family_filter=family_filter)
        self.mode_mgr = _ModeManager(mode_module=_modes4, statemachine=self.ud.uut_state_machine,
                                    uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonC9400(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[poe_loadbox, traf_generator])
        self.diags = _StardustC9400(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip, power=self.power)
        self.peripheral = _PeripheralC4K(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapC9400(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self.act2 = _ACT2(mode_mgr=self.mode_mgr, ud=self.ud)
        self.x509sudi = _X509Sudi(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux)
        self.traffic = _Traffic(fmdiags=_TrafficDiagsC9400(mode_mgr=self.mode_mgr, ud=self.ud, diags=self.diags),
                                fmgenerator=_TrafficSNTC9400(mode_mgr=self.mode_mgr, ud=self.ud, ios=self.ios, equip=self.equip))
        self._callback_()
        return

    def _sync_to_group(self, sync_group, timeout=300):
        """ Sync to Group (INTERNAL)

        Generic routine for syncing to a group.

        :param sync_group: From the Apollo x_config.py
        :return:
        """
        container_key = aplib.get_my_container_key()
        pl, ar, ts, _ = container_key.split("|", 3)
        sync_group_path = '|'.join([pl, ar, ts, sync_group]).upper()
        cont_attrb = aplib.get_container_attributes()
        cont_sync_groups = cont_attrb.sync_groups
        log.debug("Sync groups = {0}".format(cont_sync_groups))
        if sync_group_path not in cont_sync_groups:
            log.error("The requested sync group '{0}' is not available for this container!".format(sync_group_path))
            log.error("Check the _config.py for the presence of {0}".format(sync_group))
            return aplib.FAIL

        container_key = aplib.get_my_container_key()
        log.info('{} syncing with group {!r}'.format(container_key, sync_group))
        result = aplib.sync_group(group_name=sync_group, function=self._leader_function, timeout=timeout)
        log.info("SYNC Done!")
        log.debug("Result = {0}".format(result))
        return result

    def _allocate_card(self, action, priority=100, card_name='card', keep_last=False):
        """ Allocate Card (INTERNAL)

        Activating a linecard or Supervisor = start using it.
        Deactivating a linecard or Supervisor = done using it and no longer need to talk to the card.

        This routine uses an "active card" list maintained in global cache to keep track of all linecards/Supervisors in use.
        Also a 'remove from list' is performed on all non-running containers still in the 'active card list'
        (could happen with abort or exception w/ no cleanup).

        :param (str) action: 'deactivate', 'activate', 'show'
        :param (int) priority: lower number is higher priority
        :param (bool) keep_last: Future feature (NOT USED); use to keep last container when deactivating to stay
                          powered on for something else prior to cleanup.
        :return: True|False
        """
        log.debug("Configuration Data")
        self.ud.derive_device_info()
        card_config = self.ud.uut_config.get(card_name.lower(), None)
        if not card_config:
            log.warning("No configuration data for the UUT card: {0}".format(card_name))
            log.warning("Please check the card name and the Apollo x_config.py.")
            return False
        log.debug("Card config = {0}".format(card_config))

        container_key = aplib.get_my_container_key()
        container = container_key.split("|")[-1]
        pl, ar, ts, _ = container_key.split("|", 3)
        active_name = '_'.join([pl, ar, ts, 'ActiveModular'])
        with locking.ContainerPriorityLock('__active_modular__', priority=priority):
            log.debug("Lock    : {0}".format(active_name))
            log.debug("Priority: {0}".format(priority))

            active_cards = aplib.get_cached_data(active_name)
            if active_cards:
                idx = active_cards.index(container) if container in active_cards else -1
            else:
                active_cards = []

            if action == 'activate':
                log.debug("Active {0}.".format(card_name))
                if not active_cards:
                    log.debug("First {0} container to use: '{1}'".format(card_name.lower(), container))
                    active_cards = [container]
                    aplib.cache_data(active_name, active_cards)
                else:
                    if container not in active_cards:
                        log.debug("Adding {0} container to the active list: {1}".format(card_name.lower(), container))
                        active_cards.append(container)
                        aplib.cache_data(active_name, active_cards)
                    else:
                        log.debug("{0} container already active: {1}".format(card_name, container))

            elif action == 'deactivate':
                log.debug("Deactive {0}.".format(card_name))
                for c in active_cards:
                    # Check & remove orphaned containers (not running but still in the active list due to no cleanup).
                    status = aplib.get_container_status(c)
                    log.debug("{0:<10} = {1}{2}".format(c, status, '*' if status != 'RUNNING' else ''))
                    if status != 'RUNNING':
                        idx = active_cards.index(c)
                        active_cards.pop(idx)
                if len(active_cards) > 1:
                    if idx >= 0:
                        log.info("Deactivating {0} container: '{1}'...".format(card_name.lower(), container))
                        active_cards.pop(idx)
                        aplib.cache_data(active_name, active_cards)
                        log.info("{0} container deactivated.".format(card_name))
                    else:
                        log.info("{0} container already deactivated.".format(card_name))
                elif len(active_cards) == 1:
                    if not keep_last:
                        log.info("Only one {0} container remains active and it will be deactivated.".format(
                            card_name.lower()))
                        aplib.cache_data(active_name, [])
                    else:
                        log.warning(
                            "Only one {0} container remains active; deactivate is bypassed.".format(card_name.lower()))
                        log.warning("This should only be done when the chassis needs to stay powered on.")
                else:
                    log.info("No {0} containers were activated; nothing to deactivate.".format(card_name.lower()))

            elif action == 'show':
                log.debug("Show {0}.".format(card_name))

            else:
                log.error("Unknown action for {0} allocation.".format(card_name.lower()))
                return False

            msg = "Active {0}s".format(card_name)
            log.info(msg)
            log.info("-" * len(msg))
            for lc in active_cards:
                log.info("{0} {1}".format(lc, '*' if lc == container else ''))

        return True

    def _leader_function(self):
        return aplib.get_my_container_key()

# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# MacallanSupervisor
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class MacallanSupervisor(_C9400):
    def __init__(self):
        self.show_version()
        super(MacallanSupervisor, self).__init__(family_filter='macallan_sup')
        self.uut_conn_aux = aplib.conn.uutTN_aux
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def sync_supervisors(self, **kwargs):
        """ Sync Supervisors
        Use this for dual supervisors that share a chassis and require syncing.
        All the Supervisor syncgroups: 'SUPsync', 'SUPsyncPwr', 'SUPsyncDiags', 'SUPsyncTraf', 'SUPsyncFinal'
        WARNING: This will not work if both sups are NOT started together within the timeout period.
                 Out-of-sync conditions can occur which create DEADLOCKS and timeouts!
        IMPORTANT: Must have a mechanism during PRE-SEQ to ensure both sup containers get synced at the beginning.
        :param kwargs:
        :return:
        """
        aplib.set_container_text('SYNC SUPERVISORS')
        log.info('STEP: Sync Supervisors.')

        # Input
        sync_group = kwargs.get('sync_group', 'SUPsync')
        timeout = kwargs.get('timeout', 1800)

        ret = self._sync_to_group(sync_group, timeout)
        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def allocate_supervisor_container(self, **kwargs):
        """ Allocate Supervisor Container
        :menu: (enable=True, name=ALLOCATE SUP (ON), section=Diags, num=1, args={'menu': True, 'action': 'activate'})
        :menu: (enable=True, name=ALLOCATE SUP (OFF), section=Diags, num=1, args={'menu': True, 'action': 'deactivate'})
        :param kwargs:
        :return:
        """
        # Input
        action = kwargs.get('action', 'show')
        priority = kwargs.get('priority', 100)

        aplib.set_container_text('{0} SUP CONT'.format(action.upper()))
        log.info('STEP: {0} supervisor container.'.format(action))

        self._allocate_card(action=action, priority=priority, card_name='Supervisor')

        return aplib.PASS

    @apollo_step
    def setuserslot_sup(self, **kwargs):
        """ SetUserSlot for Sup
        :menu: (enable=True, name=SETUSERSLOT SUP, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('SET USERSLOT SUP')
        log.info('STEP: Set user slot for sup.')

        # Input
        linecards = kwargs.get('linecards', None)
        auxsup = kwargs.get('auxsup', False)

        ret = self._sup_set_userslot(target_linecards=linecards, auxsup=auxsup)
        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def lock_sup_as_resource(self, **kwargs):
        """ Lock Sup
        :param kwargs:
        :return:
        """
        aplib.set_container_text('ACQUIRE SUP-SUP RESOURCE')
        log.info('STEP: Acquire Supervisor-Supervisor as a resource.')

        # Inputs
        wait_timeout = kwargs.get('wait_timeout', 4800)
        release_timeout = kwargs.get('release_timeout', 2400)
        priority = kwargs.get('priority', None)

        ret, msg = self._sup_acquire(priority=priority, wait_timeout=wait_timeout, release_timeout=release_timeout)

        return (aplib.PASS, msg) if ret else (aplib.FAIL, msg)

    @apollo_step
    def unlock_sup_test_resource(self, **kwargs):
        """ Unlock Sup
        :param kwargs:
        :return:
        """
        aplib.set_container_text('RELEASE SUP-SUP RESOURCE')
        log.info('STEP: Release Supervisor-Supervisor as a resource.')

        self._sup_release()

        return aplib.PASS

    @apollo_step
    def auxsup_mode(self, **kwargs):
        # Inputs
        mode = kwargs.get('mode', 'STARDUST')

        # Do the mode transistion for the other sup
        log.debug("Re-assign mode_mgr connection and use.")
        self.mode_mgr.uut_conn = self.uut_conn_aux
        result = self.mode_mgr.goto_mode(mode)

        # Restore original
        log.debug("Restore original mode_mgr connection.")
        self.mode_mgr.uut_conn = self.uut_conn
        log.debug("Current mode = {0}".format(self.mode_mgr.current_mode))

        return aplib.PASS if result else aplib.FAIL

    @apollo_step
    def clean_up(self, **kwargs):

        # Disconnect other auxillary/shared connections
        self.uut_conn_aux.close()

        # All Equipment disconnect
        self.equip.disconnect()

        # Automation
        if self.ud.automation:
            # auto_control.auto_finish(self.ud.puid.sernum)
            pass

        return aplib.PASS

    # ==================================================================================================================
    # USER/Internal METHODS   (step support)
    # ==================================================================================================================
    def _sup_set_userslot(self, target_linecards=None, auxsup=False):
        """ SUP SetUserSlot (INTERNAL)

        Set the user slots for diag and traf testing of Supervisor cards.
        Possible combinations:
        1. SUP only
        2. SUP-SUP
        3. SUP-FirstLinecard
        4. SUP-SecondLinecard

        :param (list|str) target_linecards: One or more linecards specified by ordinal name.
                                            For example: 'first', 'second', etc. in the ordinal position refers to the
                                            linecard list from the configuration_data in the _config.py file, like
                                            SUPERVISOR_SEVEN_SLOT_A = {
                                            1: {'physical_slot': 3, 'linecards':[5,7], 'physical_slot_auxsup': 4},
                                            2: {'physical_slot': 4, 'linecards':[7,5], 'physical_slot_auxsup': 3}}
                                            In this case, 'second' for UUT01 (SUP1) is 7.
        :param (bool) auxsup: True = Auxillary (aka Remote) Sup is specified.
        :return:
        """
        # Station path (MUST be associated to ONE CHASSIS!!)
        container_key = aplib.get_my_container_key()
        pl, ar, ts, _ = container_key.split("|", 3)
        if 'supervisor' not in self.ud.uut_config:
            log.error("Supervisor config data has not been loaded.")
            return False, 'No supervisor config data.'

        sup_slot = self.ud.uut_config['supervisor'].get('physical_slot', None)
        auxsup_slot = self.ud.uut_config['supervisor'].get('physical_slot_auxsup', None)
        available_linecards = self.ud.uut_config['supervisor'].get('linecards', [])
        linecard_slots = common_utils.get_ordinal(target_linecards, available_linecards)

        param_list = list()
        ret = False
        if sup_slot:
            param_list.append(sup_slot) if sup_slot else None
        if auxsup_slot and auxsup:
            param_list.append(auxsup_slot) if auxsup_slot else None
        if linecard_slots:
            param_list += linecard_slots
        params = ','.join([str(i) for i in param_list])

        self.mode_mgr.auto_connect = False
        mode = self.mode_mgr.current_mode
        self.mode_mgr.auto_connect = True
        if 'STARDUST' in mode:
            self.uut_conn.send("SetUserSlot {0}\r".format(params), expectphrase=self.mode_mgr.uut_prompt_map['STARDUST'], regex=True)
            ret = True
        else:
            log.error("Supervisor is NOT in the correct mode.")

        return ret

    def _sup_acquire(self, priority, wait_timeout, release_timeout):
        """ SUP Acquire Lock (INTERNAL)
        Lock for the SUP-SUP pair so that only one SUP is active at a time.
        :param priority:
        :param wait_timeout:
        :param release_timeout:
        :return:
        """

        # Station path (MUST be associated to ONE CHASSIS!!)
        container_key = aplib.get_my_container_key()
        pl, ar, ts, _ = container_key.split("|", 3)

        # Sup resource: Create a new one or pull the existing one.
        sup_resource_name = '_'.join([pl, ar, ts, 'SupSupResource'])
        log.debug("Sup resource : {0}".format(sup_resource_name))
        log.debug("Lock priority: {0}".format(priority))

        if priority:
            log.debug("Creating the SUP Priority Lock resource...")
            sup_lock = locking.ContainerPriorityLock(sup_resource_name, priority=priority, wait_timeout=wait_timeout,
                                                     release_timeout=release_timeout)
        else:
            log.debug("Creating the SUP FIFO Lock resource...")
            sup_lock = locking.FIFOLock(sup_resource_name, wait_timeout=wait_timeout, release_timeout=release_timeout)
        # Now save.
        setattr(self.ud, 'sup_lock', sup_lock)

        # Acquire the lock
        try:
            log.info("Acquiring Resource Lock: '{0}'".format(sup_resource_name))
            log.info("Wait timeout = {0},  Release timeout = {1}".format(wait_timeout, release_timeout))
            log.info("Waiting for lock...")
            sup_lock.acquire()
            log.info("*** SUP-SUP LOCK ACQUIRED! ***")

        except (apexceptions.AbortException, apexceptions.ScriptAbortException) as e:
            log.error("Aborting...")
            log.error(e)
            sup_lock.release()
            return False, str(e)

        except apexceptions.TimeoutException as e:
            return False, str(e)

        except Exception as e:
            log.error("General exception during lock...")
            log.error(e)
            sup_lock.release()
            return False, str(e)

        return True, ''

    def _sup_release(self):
        """ Supervisor-Supervisor Release (INTERNAL)

        Use this to release the lock on the SUP-SUP pair.
        :return:
        """
        # Station path (MUST be associated to ONE CHASSIS!!)
        container_key = aplib.get_my_container_key()
        pl, ar, ts, _ = container_key.split("|", 3)

        # Sup resource
        sup_resource_name = '_'.join([pl, ar, ts, 'SupSupResource'])
        log.debug("Sup resource: {0}".format(sup_resource_name))

        sup_lock = getattr(self.ud, 'sup_lock')
        if not sup_lock:
            log.info("The sup-sup lock resource does not exist.")
            log.info("Nothing to release.")
            log.warning("This could be an error in the sequence not first locking the sup for the container.")
            return False
        else:
            # Release it!
            self.ud.sup_lock.release()
            log.info("*** SUP-SUP LOCK RELEASED! ***")
        return True


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# MacallanLinecard
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class MacallanLinecard(_C9400):
    def __init__(self):
        self.show_version()
        super(MacallanLinecard, self).__init__(family_filter='macallan_linecard')
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def acquire_sup_resource(self, **kwargs):
        """ Acquire Sup Resource
        Use this for multi-linecards that share the sup as a resource.
        The lock timeouts must be calculated based on total possible linecard running.
        The rule here is wait_time = max runtime for one linecard container * number of containers * 2.1

        :menu: (enable=True, name=ACQUIRE SUP RSC, section=Diags, num=1, args={})

        :param kwargs:
        :return:
        """
        label = kwargs.get('label', '')
        aplib.set_container_text('ACQUIRE SUP RESOURCE - {0}'.format(label))
        log.info('STEP: Acquire Supervisor as a resource.')

        max_linecard_testtime = 4200  # 1 hr 10 mins; TBD
        total_possible_linecards = len(aplib.apdicts.configuration_data.get('LINECARD', {}).keys())
        if total_possible_linecards < 1:
            log.error("No linecards possible.")
            log.error("Please check the _config.py for configuration data of the chassis.")
            return aplib.FAIL
        wait_timeout_default = int(max_linecard_testtime * total_possible_linecards * 2.1)
        release_timeout_default = int(wait_timeout_default / 2)

        # Inputs
        wait_timeout = kwargs.get('wait_timeout', wait_timeout_default)
        release_timeout = kwargs.get('release_timeout', release_timeout_default)
        priority = kwargs.get('priority', None)

        ret, msg = self._linecard_sup_acquire(priority=priority, wait_timeout=wait_timeout, release_timeout=release_timeout, label=label)

        return (aplib.PASS, msg) if ret else (aplib.FAIL, msg)

    @apollo_step
    def release_sup_resource(self, **kwargs):
        """ Release Sup Resource
        Use this for multi-linecards that share the sup as a resource.

        :menu: (enable=True, name=RELEASE SUP RSC, section=Diags, num=1, args={})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('RELEASE SUP RESOURCE')
        log.info('STEP: Release Supervisor as a resource.')

        # Input
        label = kwargs.get('label', '')

        self._linecard_sup_release(label=label)

        return aplib.PASS

    @apollo_step
    def allocate_linecard_container(self, **kwargs):
        """ Allocate Linecard Container
        :menu: (enable=True, name=ALLOCATE LINE CARD (ON), section=Diags, num=1, args={'menu': True, 'action': 'activate'})
        :menu: (enable=True, name=ALLOCATE LINE CARD (OFF), section=Diags, num=1, args={'menu': True, 'action': 'deactivate'})
        :param kwargs:
        :return:
        """
        # Input
        action = kwargs.get('action', 'show')
        priority = kwargs.get('priority', 100)

        aplib.set_container_text('{0} LC CONT'.format(action.upper()))
        log.info('STEP: {0} linecard container.'.format(action))

        self._allocate_card(action=action, priority=priority, card_name='Linecard')

        return aplib.PASS

    @apollo_step
    def setuserslot_linecard(self, **kwargs):
        """ SetUserSlot for Linecard
        :menu: (enable=True, name=SETUSERSLOT LC, section=Diags, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('SET USERSLOT LINECARD')
        log.info('STEP: Set user slot for linecard.')

        # Input
        linecard = kwargs.get('linecard', self.ud.uut_config.get('linecard', {}))
        linecard_physical_slot = linecard.get('physical_slot', None)

        if not linecard_physical_slot:
            log.error("No physical slot described for the linecard!")
            return aplib.FAIL

        self.mode_mgr.auto_connect = False
        mode = self.mode_mgr.current_mode
        self.mode_mgr.auto_connect = True
        if 'STARDUST' in mode:
            self.uut_conn.send("SetUserSlot {0}\r".format(linecard_physical_slot),
                               expectphrase=self.mode_mgr.uut_prompt_map['STARDUST'], regex=True)
            ret = True
        else:
            log.error("Linecard's supervisor is NOT in the correct mode.")
            ret = False

        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def sync_linecards(self, **kwargs):
        """ Sync Linecards
        Use this for multi-linecards that share the sup as a resource and require syncing.
        All the Linecard syncgroups: 'LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal'

        WARNING: This will not work if all linecards are NOT started together within the timeout period.
                 Out-of-sync conditions can occur which create DEADLOCKS and timeouts!

        IMPORTANT: Must have a mechanism during PRE-SEQ to ensure all containers get synced at the beginning AND that no other
        available containers for a given chassis that were not started initially are not started later after the first sync.

        :param kwargs:
        :return:
        """

        aplib.set_container_text('SYNC LINECARDS')
        log.info('STEP: Sync Linecards.')

        # Input
        sync_group = kwargs.get('sync_group', 'LCsync')
        timeout = kwargs.get('timeout', 1200)

        result = self._sync_to_group(sync_group, timeout)
        return aplib.PASS

    # ==================================================================================================================
    # USER/Internal METHODS   (step support)
    # ==================================================================================================================
    def _linecard_sup_acquire(self, priority, wait_timeout, release_timeout, label=''):
        """ Linecard Supervisor Acquire (INTERNAL)

        Create the locking resource (if it has not been previously created) and then lock it for use.
        This enables the linecard container to use the Sup singularly (one container at a time).
        All other containers that arrive at the lock point are queued and have to wait for the lock
        to release.
        If the priority parameter is given with a number then the PriorityLock() class is used, otherwise
        the FIFOLock() class is used.

        **IMPORTANT**: The uut_config is updated here for the 'linecard' key to dynamically reflect the
                       linecard that is being operated on.  This data is meant to be used elsewhere by
                       other modules and drivers and its source is the configuration data from the apollo
                       _config.py file.

        :param (int) priority: lower number is higher priority, or None
        :param (int) wait_timeout:
        :param (int) release_timeout:
        :return:
        """

        # Station path (MUST be associated to ONE CHASSIS!!)
        container_key = aplib.get_my_container_key()
        pl, ar, ts, _ = container_key.split("|", 3)
        if 'linecard' not in self.ud.uut_config:
            log.error("Linecard config data has not been loaded.")
            return False, 'No linecard config data.'
        sup_num = self.ud.uut_config['linecard'].get('sup_prime', 1)
        linecard_physical_slot = self.ud.uut_config['linecard']['physical_slot']

        # Sup resource: Create a new one or pull the existing one.
        sup_resource_name = '_'.join([pl, ar, ts, 'SupLinecardResource_supslot{0}'.format(sup_num)])
        log.info("Linecard's Sup Resource : {0} (for {1})".format(sup_resource_name, label))
        log.info("Lock priority           : {0}".format(priority))

        if priority:
            log.debug("Creating the SUP Priority Lock resource...")
            sup_lock = locking.ContainerPriorityLock(sup_resource_name, priority=priority, wait_timeout=wait_timeout,
                                                     release_timeout=release_timeout)
        else:
            log.debug("Creating the SUP FIFO Lock resource...")
            sup_lock = locking.FIFOLock(sup_resource_name, wait_timeout=wait_timeout, release_timeout=release_timeout)
        # Now save
        setattr(self.ud, 'sup_lock', sup_lock)

        # Acquire the lock
        try:
            log.info("Acquiring Resource Lock: '{0}'".format(sup_resource_name))
            log.info("Wait timeout = {0},  Release timeout = {1}".format(wait_timeout, release_timeout))
            log.info("Waiting for lock...")
            sup_lock.acquire()
            log.info("*** SUP LOCK ACQUIRED! ***")

            # Set Linecard for diags
            # Note: This does NOT preclude the use of "-slot:x" param for diags commands.
            # It at least will indicate (via prompt) which Linecard belongs to the target UUT.
            self.mode_mgr.auto_connect = False
            mode = self.mode_mgr.current_mode
            self.mode_mgr.auto_connect = True
            if mode in ['STARDUST']:
                self.uut_conn.send("SetUserSlot {0}\r".format(linecard_physical_slot))

        except (apexceptions.AbortException, apexceptions.ScriptAbortException) as e:
            log.error("Aborting...")
            log.error(e)
            sup_lock.release()
            return False, str(e)

        except apexceptions.TimeoutException as e:
            return False, str(e)

        except Exception as e:
            log.error("General exception during lock...")
            log.error(e)
            sup_lock.release()
            return False, str(e)

        return True, ''


    def _linecard_sup_release(self, label=''):
        """ Linecard Supervisor Release (INTERNAL)

        Use this to release the lock on the SUP which is used for linecard testing.
        :return:
        """
        # Station path (MUST be associated to ONE CHASSIS!!)
        container_key = aplib.get_my_container_key()
        container = container_key.split("|")[-1]
        pl, ar, ts, _ = container_key.split("|", 3)
        sup_num = self.ud.uut_config.get('linecard', {}).get('sup_prime', 1)

        # Sup resource
        sup_resource_name = '_'.join([pl, ar, ts, 'SupLinecardResource_supslot{0}'.format(sup_num)])
        active_name = '_'.join([pl, ar, ts, 'ActiveModular'])
        log.info("Linecard's Sup Lock Resource: {0} (for {1})".format(sup_resource_name, label))

        sup_lock = getattr(self.ud, 'sup_lock')
        if not sup_lock:
            log.info("The sup lock resource does not exist.")
            log.info("Nothing to release.")
            log.warning("This could be an error in the sequence not first locking the sup for the container.")
            return False
        else:
            try:
                # Provide a status.
                active_linecards = aplib.get_cached_data(active_name)
                if active_linecards and container in active_linecards:
                    log.info("This container is active.")
            except Exception as e:
                log.warning(e)

            # Release it!
            self.ud.sup_lock.release()
            log.info("*** SUP LOCK RELEASED! ***")
        return True
