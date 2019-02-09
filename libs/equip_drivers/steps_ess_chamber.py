""" Environmental Stress Screen (ESS) Chamber Steps
========================================================================================================================

Use these steps for both PRE-SEQ and SEQ when operating a 2C/4C Chamber that uses the standard Cisco Library
for the Chamber driver.
These step functions were modeled after the 2C Template.

Additional features include:
    1. Default profiles for Commercial, Industrial, and QuickSimulation
    2. Product specific profiles can be used also (defined in the product definition)


========================================================================================================================
"""

# Python
# ------
import logging
import collections
import re

# Apollo
# ------
import apollo.libs.lib as aplib
from apollo.libs import locking
from apollo.engine import apexceptions

# Cisco Lib
# ---------
from apollo.scripts.cisco.libs.chamber.chamber_interface import HOT, COLD, AMBIENT, DRY, ChamberInterface

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils


__title__ = "EntSw ESS Chamber Steps"
__version__ = '2.0.0'
__author__ = 'bborel'

# Chamber globals
# ---------------
last_action = None
chamber_handler = None
MONITOR_IN_TEST = True                       # NOTE: True if want to monitor temperature during test
CHAMBER_SYNC_GROUP = 'ChamberSync1'          # NOTE: Default if the group name is not defined in the x_config.py
ALLOWED_CORNERS = [HOT, COLD, AMBIENT, DRY]
DEFAULT_MAX_CHAMBER_SLOTS = 16

log = logging.getLogger(__name__)
ChamberProfileDesc = collections.namedtuple('ChamberProfileDesc', 'temperature rate margin duration max_humidity')

DEFAULT_PROFILES = {
    'commercial': [
        ('COLD',    {'ramp': ChamberProfileDesc(0, 3, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 3, 5, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)}),
        ('HOT',     {'ramp': ChamberProfileDesc(50, 3, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 3, 5, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)}),
        ('AMBIENT', {'ramp': ChamberProfileDesc(28, 3, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 3, 1, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)}),
        ('DRY',     {'ramp': ChamberProfileDesc(25, 3, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 3, 1, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)})],
    'commercial_yinhe': [
        ('COLD',    {'ramp': ChamberProfileDesc(0, 1.5, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 5, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)}),
        ('HOT',     {'ramp': ChamberProfileDesc(50, 1.5, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 5, 0),
                     'test': ChamberProfileDesc(None, None, 3, None, 0)}),
        ('AMBIENT', {'ramp': ChamberProfileDesc(28, 1.5, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 1, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('DRY',     {'ramp': ChamberProfileDesc(25, 1.5, 0, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 1, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)})],
    'industrial': [
        ('COLD',    {'ramp': ChamberProfileDesc(-30, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('HOT',     {'ramp': ChamberProfileDesc(60, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('AMBIENT', {'ramp': ChamberProfileDesc(25, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('DRY',     {'ramp': ChamberProfileDesc(35, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)})],
    'quicksim':   [
        ('COLD',    {'ramp': ChamberProfileDesc(22, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('HOT',     {'ramp': ChamberProfileDesc(28, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('AMBIENT', {'ramp': ChamberProfileDesc(25, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)}),
        ('DRY',     {'ramp': ChamberProfileDesc(26, 3, 2, None, 0),
                     'soak': ChamberProfileDesc(None, None, 2, 0, 0),
                     'test': ChamberProfileDesc(None, None, 2, None, 0)})],
}


# ======================================================================================================================
# STEPS
# ======================================================================================================================
def step__chamber_init(first_init=True, fi_action='ask', profile_type=None, corners=None):
    """
    Chamber initialize - create object and set temperature profile
    :param (bool) first_init: True if this is first initialization of the chamber.
                              If this is done in PRE-SEQ, then it should be set to False in SEQ.
    :param (str) fi_action:
    :param (str) profile_type: Recognized profile types.
    :return:
    """
    global chamber_handler

    log.debug(r"//" + "-" * 50)
    log.debug("STEP: Chamber Init.")

    profile_table = {
        'commercial': chamber_default_commercial_profile,
        'commercial_yinhe': chamber_default_commercial_yinhe_profile,
        'industrial': chamber_default_industrial_profile,
        'productdef': chamber_product_profile,
        'quicksim': chamber_quick_simulation_profile
    }
    if profile_type:
        profile_type = profile_type.lower()
        if profile_type not in profile_table.keys():
            log.error("Chamber profile type '{0}' not recognized.".format(profile_type))
            raise apexceptions.ApolloException
    else:
        log.debug("Chamber profile will default to the profile in the product definition.")
        profile_type = 'productdef'

    sync_group = get_chamber_sync_group()

    log.info("Chamber Profile Type      = {0}".format(profile_type))
    log.info("Chamber Profile Name      = {0}".format(profile_table[profile_type].__name__))
    log.info("Container Sync Groups     = {0}".format(aplib.get_container_sync_groups()))
    log.info("Chamber Target Sync Group = {!r}".format(sync_group))
    log.info("Container                 = {0}".format(aplib.get_my_container_key()))

    # All containers need to sync up
    log.debug("Chamber Init sync 1...")
    sync_chamber_group(sync_group)

    # Init the Chamber
    log.debug("Performing ChamberInterface.init...")
    if not chamber_handler:
        log.debug("The global chamber_handler is new.")
    else:
        log.debug("The global chamber_handler will be reset.")
        chamber_handler = None
    chamber_handler = ChamberInterface.init(profile=profile_table[profile_type],
                                            connection=aplib.conn.Chamber,
                                            sync_group=sync_group,
                                            logger=log,
                                            save_to_chart='entsw_thermal.svg',
                                            first_init=first_init,
                                            fi_action=fi_action)
    log.debug("Chamber Init sync 2...")
    sync_chamber_group(sync_group)

    log.debug("Handler Profile")
    for k, v in chamber_handler.profiles.items():
        log.debug("  {0:<20}: {1}".format(k, v))

    log.debug("STEP: Chamber Init PASSED.")
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def step__chamber_start():
    """
    Chamber start - config chamber and start to run
    :return:
    """
    log.debug(r"//" + "-" * 50)
    log.debug("STEP: Chamber Start.")
    log.debug("chamber_handler = {0}".format(chamber_handler))
    ChamberInterface.start(chamber_handler)
    log.debug("STEP: Chamber Start PASSED")
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def step__chamber_final():
    """
    Go to room temperature, and stop chamber
    Only allow the last container do chamber finalization
    """
    log.debug(r"//" + "-" * 50)
    log.debug("STEP: Chamber Final.")
    ChamberInterface.stop(chamber_handler, AMBIENT, DRY, -10)
    log.debug("STEP: Chamber Final {0}".format(aplib.apdicts.stepdict['current_status']))
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def step__chamber_ramp(action=AMBIENT):
    """
    Chamber temperature ramp up/down to the temperature defined in profile
    :param action
    """
    log.debug(r"//" + "-" * 50)
    msg = "STEP: Chamber Ramp --> {0}.".format(action)
    log.debug(msg)
    log.debug("-" * len(msg))
    log.debug("Global Corners = {0}".format(get_global_corners()))
    log.debug("Global Profile")
    for k, v in get_global_profile().items():
        log.debug("  {0:<20}: {1}".format(k, v))
    log.debug("Handler Profile")
    for k, v in chamber_handler.profiles.items():
        log.debug("  {0:<20}: {1}".format(k, v))

    global last_action
    last_action = action
    ChamberInterface.ramp(chamber_handler, action=action)
    log.debug("STEP: Chamber Ramp PASSED")
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def step__chamber_start_monitor():
    """
    Start to monitor temperature in chamber during test.
    If set MONITOR_IN_TEST as True, this step will be bypassed.
    :return:
    """
    log.debug(r"//" + "-" * 50)
    log.debug("STEP: Chamber Start Monitor.")
    log.debug("chamber_handler = {0}".format(chamber_handler))
    ChamberInterface.monitor_start(chamber_handler, monitor_in_test=MONITOR_IN_TEST)
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def step__chamber_stop_monitor():
    """
    Stop to monitor temperature in chamber after test is done.
    If set MONITOR_IN_TEST as True, this step will be bypassed.
    :return:
    """
    log.debug(r"//" + "-" * 50)
    log.debug("STEP: Chamber Stop Monitor.")
    ChamberInterface.monitor_stop(monitor_in_test=MONITOR_IN_TEST)
    log.debug(r"\\" + "-" * 50)
    return aplib.PASS


def prestep__chamber_staging(area):
    """ Chamber Staging
    Run by Supercontainer
    Operator selects which UUT slots to run for the chamber.
    :param (str) area: Test Area
    :return:
    """
    info = aplib.get_pre_sequence_info()
    active_chamber_slots = '0'
    max_chamber_slots = len(info.containers)
    log.debug("MAX Chamber SLots = {0}".format(max_chamber_slots))
    ans_good = False
    while not ans_good:
        ans = aplib.ask_question("Enter sequential UUT slots for chamber testing [Default = 1-{0}]:\n"
                                 " Ex1. 1-10,12,15\n"
                                 " Ex2. 2,4,6,8\n"
                                 " Ex3. 2-11\n".format(max_chamber_slots))
        ans = '1-{0}'.format(max_chamber_slots) if ans == '' else ans
        ans_good = True if re.match("(^[0-9]+[0-9,\-]*$)", ans) else False
        if ans.upper() == 'ABORT':
            raise apexceptions.AbortException("Operator aborted chamber staging of UUT slots.")

        active_chamber_slots = common_utils.expand_comma_dash_num_list(ans)
        if max(active_chamber_slots) > max_chamber_slots:
            log.warning("Chamber UUT slot selection exceeds maximum available; please re-enter.")
            ans_good = False

    log.debug("Active Chamber SLots accepted: {0}".format(active_chamber_slots))
    ACTIVECS_KEY, MAXCS_KEY = get_chamber_slots_keys()
    aplib.cache_data(ACTIVECS_KEY, active_chamber_slots)
    aplib.cache_data(MAXCS_KEY, str(max_chamber_slots))

    # Reset globals
    reset_globals()

    return aplib.PASS


def prestep__set_chamber_attributes():
    log.debug("Chamber attribute processing...")
    set_global_corners()
    set_global_profile()
    return aplib.PASS


def prestep__chamber_post_staging():
    ACTIVECS_KEY, _ = get_chamber_slots_keys()
    active_chamber_slots = aplib.get_cached_data(ACTIVECS_KEY)
    log.debug("Active chamber slots: {0}".format(active_chamber_slots))
    return aplib.PASS


# ======================================================================================================================
# Support Functions
# ======================================================================================================================
def __load_chamber_profile(obj, chamber_profile):
    """ (INTERNAL) Driver to load a profile to the chamber handler.
    DO NOT call this directly, use the chamber_xxx_profile() functions.
    :param obj: chamber handler object
    :param chamber_profile:
    :return:
    """
    log.info("Installing chamber profile to handler...")
    for corner in chamber_profile.keys():
        if corner in ALLOWED_CORNERS:
            ramp = chamber_profile[corner]['ramp']
            soak = chamber_profile[corner]['soak']
            test = chamber_profile[corner]['test']
            obj.set_profile_ramp(corner, temperature=ramp.temperature, rate=ramp.rate, margin=ramp.margin, max_humidity=ramp.max_humidity)
            obj.set_profile_soak(corner, margin=soak.margin, duration=soak.duration, max_humidity=soak.max_humidity)
            obj.set_profile_test(corner, margin=test.margin, max_humidity=test.max_humidity)
            log.debug("Corner = {0}".format(corner))
            log.debug("  Ramp = {0}".format(ramp))
            log.debug("  Soak = {0}".format(soak))
        else:
            log.warning("An unknown corner ({0}) was specified in the profile. It will NOT be loaded to the handler.".format(corner))
    return True


def show_container_info():
    container_name = aplib.get_container_name()
    aplib.get_container_status(container_name)
    container_key = aplib.get_my_container_key()
    station_key = '|'.join(container_key.split('|')[:-1])
    log.debug("Container = {0}".format(container_name))
    log.debug("Station   = {0}".format(station_key))
    log.debug("Cfg       = {0}".format(aplib.apdicts.configuration_data))
    return


def sync_chamber_group(group_name):
    # All containers need to sync up
    try:
        aplib.sync_group(group_name=group_name, timeout=300)
    except apexceptions.TimeoutException as e:
        log.error(e.message)
        msg = "Container could not sync up chamber group."
        log.error(msg)
        return False, msg + e.message
    return True, None


def get_chamber_sync_group():
    """ Get Chamber Sync Group
    Tiered get (first occurance)
        1. 'ChamberSync' in the container's list of sync groups, OR
        2. "CHAMBER_SYNC_GROUP" key in the configuration_data for the station, OR
        3. Use the default: CHAMBER_SYNC_GROUP.
    :return:
    """
    global CHAMBER_SYNC_GROUP
    log.debug("Determine sync group for chamber...")

    for k in aplib.get_container_sync_groups():
        if 'ChamberSync'.upper() in k.upper():
            CHAMBER_SYNC_GROUP = k
            log.debug("Using syncgroup name from existing container sync groups.")
            break
    else:
        csg = aplib.apdicts.configuration_data.get('CHAMBER_SYNC_GROUP', None).upper()
        if csg:
            log.debug("Using syncgroup name from cfg data.")
            CHAMBER_SYNC_GROUP = csg
        else:
            log.debug("Using default syncgroup name.")

    log.debug("Calculated Sync Group Name = {0}".format(CHAMBER_SYNC_GROUP))
    log.debug("The CHAMBER_SYNC_GROUP is now set.")
    return CHAMBER_SYNC_GROUP


def chamber_product_profile(obj):
    """ Product Chamber Profile
    Pull in the profile from the cached data global space.
    It will be referenced by 'chamber_profile_' + station key
    The global profile MUST have been resolved in the PRE-SEQ after loading the product definitions
    for each UUT in the chamber.
    See the DEFAULT_PROFILES for an example of the required format.
    :param obj: Chamber handler object
    :return:
    """
    log.info("Loading custom chamber profile...")
    chamber_profile = collections.OrderedDict(get_global_profile())
    return __load_chamber_profile(obj, chamber_profile)


def chamber_default_commercial_profile(obj):
    """ Default Commercial Chamber Profile
    :param obj: Chamber handler object
    :return:
    """
    log.info("Loading default commercial chamber profile...")
    chamber_profile = collections.OrderedDict(DEFAULT_PROFILES['commercial'])
    return __load_chamber_profile(obj, chamber_profile)


def chamber_default_commercial_yinhe_profile(obj):
    """ Default Commercial Chamber Profile
    :param obj: Chamber handler object
    :return:
    """
    log.info("Loading default commercial_yinhe chamber profile...")
    chamber_profile = collections.OrderedDict(DEFAULT_PROFILES['commercial_yinhe'])
    return __load_chamber_profile(obj, chamber_profile)


def chamber_default_industrial_profile(obj):
    """ Default Industrial Chamber Profile
    :param obj: Chamber handler object
    :return:
    """
    log.info("Loading default industrial chamber profile...")
    chamber_profile = collections.OrderedDict(DEFAULT_PROFILES['industrial'])
    return __load_chamber_profile(obj, chamber_profile)


def chamber_quick_simulation_profile(obj):
    """ Quick Simulation Chamber Profile
    Note: *** NOT FOR PRODUCTION ***
    Use this for unittest chamber simulation.
    :param obj: Chamber handler object
    :return:
    """
    log.info("Loading quick simulation chamber profile...")
    chamber_profile = collections.OrderedDict(DEFAULT_PROFILES['quicksim'])
    return __load_chamber_profile(obj, chamber_profile)


def reset_globals():
    """ Reset Globals
    Used by Supercontainer in SC-PreSeq
    """
    log.debug("Chamber globals: reset...")
    container = aplib.get_my_container_key()
    S_KEY = '_'.join(container.split('|')[:-1])
    cp_key = 'chamber_profile_' + S_KEY
    cc_key = 'chamber_corners_' + S_KEY
    aplib.cache_data(cp_key, None)
    aplib.cache_data(cc_key, None)
    log.debug("Chamber globals reset done!")
    return


def set_global_profile(forced_profile=None):
    """ Set Global Chamber Profile
    Used by the UUT Container PRE-SEQ.
    This sets the profile to be used by ALL UUTs in the chamber via a global data cache.
    IMPORTANT: Global cache key is the station path (i.e. chamber).
    Differing product families are allowed to run but their profile selections MUST match; if not then it will abort.
    :param (list) forced_profile:
    :return:
    """

    log.debug("Global Profile: set...")
    container = aplib.get_my_container_key()
    # Source the profile.
    try:
        udd = aplib.apdicts.userdict.get('udd')
        if not udd:
            log.error("The UutDescriptor Dict was not available.")
            log.error("Please confirm proper application of the application software!")
            raise Exception("The UutDescriptor Dict was not available.")

        chamber_profile = udd.get('chamber_profile')

        if forced_profile:
            profile = collections.OrderedDict(forced_profile)
            log.debug("Chamber Profile Source: FORCED.")
        elif chamber_profile:
            profile = collections.OrderedDict(chamber_profile)
            log.debug("Chamber Profile Source: UUT DESCRIPTOR.")
        else:
            log.warning("No UutDescriptor chamber_profile, or forced_profile available.")
            log.warning("Check the product definitions and common definition for 'chamber_profile'.")
            log.warning("The default commercial profile will be used.")
            profile = collections.OrderedDict(DEFAULT_PROFILES['commercial'])
    except (KeyError, AttributeError):
        log.error("Chamber profile data is not available or not in correct form.")
        return False

    log.debug('-' * 50)
    log.debug("{0} : Chamber Profile = {1}".format(container, profile))

    # Get the current profile definition (possibly set by another container in the same chamber)
    # Global cache key is the station path (i.e. chamber)
    S_KEY = '_'.join(container.split('|')[:-1])
    cp_key = 'chamber_profile_' + S_KEY
    with locking.named_priority_lock('__profile__' + S_KEY):
        try:
            log.debug("Chamber profile cache key (set) = {0}".format(cp_key))
            established_profile = aplib.get_cached_data(cp_key)
        except (KeyError, apexceptions.ApolloException):
            established_profile = None

        if not forced_profile:
            # Save the product-specific profile selections for use by SEQ.
            if not established_profile:
                established_profile = profile
                aplib.cache_data(cp_key, established_profile)
                log.debug("*** A new chamber profile set has been established. ***")

            # All UUT profile definitions must match.  This allows different PIDs in the same chamber BUT requires
            # them to all have the same profile definition.
            if profile != established_profile:
                log.error("Chamber profile: REJECTED!")
                log.error("There is a mismatch of chamber_profiles in {0}.  This is NOT allowed.".format(container))
                log.error("Please correct the situation before running the chamber.  Inspect UUT product definitions.")
                raise apexceptions.AbortException("MISMATCH of chamber profiles in {0}.".format(container))
            else:
                log.debug("Chamber profile: ACCEPTED.  {0}".format(established_profile))
        else:
            aplib.cache_data(cp_key, profile)
            log.debug("Chamber profile: FORCED.  {0}".format(profile))

    return True


def get_global_profile(container_key=None):
    """ Get Profile
    This is strictly a read of the global cache; therefore no locking required.
    IMPORTANT: This is done by sequence_definition() so MUST be compatible with Apollo main process.
               Global cache key is the station path (i.e. chamber).
    :return:
    """
    log.debug("Global Profile: get...")
    if not container_key:
        log.debug("Need to get container key...")
        container_key = aplib.get_my_container_key()
    S_KEY = '_'.join(container_key.split('|')[:-1])
    cp_key = 'chamber_profile_' + S_KEY
    try:
        log.debug("Global profile cache key (get) = {0}".format(cp_key))
        chamber_profile = aplib.get_cached_data(cp_key)
    except (KeyError, apexceptions.ApolloException):
        log.exception("Problem with chamber profile in global cache.")
        chamber_profile = None

    if not chamber_profile:
        log.error("Global profile: ABSENT!")
        log.error("Global cache key = {0}".format(cp_key))
        log.error("Please correct the situation before running the chamber.  Inspect UUT product definitions.")
        raise apexceptions.AbortException("Chamber profile: ABSENT!")
    else:
        log.debug("Global profile: PRESENT.")
    return chamber_profile


def set_global_corners(forced_corners=None):
    """ Set Global ChamberCorners
    Used by the UUT Container PRE-SEQ.
    This sets the corners to be used by ALL UUTs in the chamber via a global data cache.
    IMPORTANT: Global cache key is the station path (i.e. chamber).
    Differing product families are allowed to run but their corner selections MUST match; if not then it will abort.

    Example set in product_definition:
    'chamber_corners': [('NTNV', False), ('HTLV', True), ('HTHV', True), ('LTLV', True)]

    Example of globally saved after processing:
    OrderedDict([('NTNV', ('AMBIENT', 'NOMINAL', False)),
             ('HTLV', ('HOT', 'LOW', True)),
             ('HTHV', ('HOT', 'HIGH', True)),
             ('LTLV', ('COLD', 'LOW', True))])

    :param (list) forced_corners:
    :return:
    """
    log.debug("Global Corners: set...")
    # Check for a product-specific corner definition.
    _lookup = {'HT': HOT, 'LT': COLD, 'NT': AMBIENT, 'HV': 'HIGH', 'LV': 'LOW', 'NV': 'NOMINAL'}
    container = aplib.get_my_container_key()

    try:
        udd = aplib.apdicts.userdict.get('udd')
        if not udd:
            log.error("The UutDescriptor Dict was not available.")
            log.error("Please confirm proper application of the application software!")
            raise Exception("The UutDescriptor Dict was not available.")

        chamber_corners = udd.get('chamber_corners')

        if forced_corners:
            listed_corners = collections.OrderedDict(forced_corners)
            log.debug("Chamber Corners Source: FORCED.")
        elif chamber_corners:
            listed_corners = collections.OrderedDict(chamber_corners)
            log.debug("Chamber Corners Source: UUT DESCRIPTOR.")
        else:
            log.warning("No UutDescriptor chamber_corners, or forced_corners available.")
            log.warning("Check the product definitions and common definition for 'chamber_corners'.")
            log.warning("The default '2-Corner' sequence (HTLV, LTHV) will be used.")
            listed_corners = [('LTHV', True), ('HTLV', True)]

        processed_corners = []
        if listed_corners:
            for lc in listed_corners:
                name = lc[0] if isinstance(lc, tuple) else lc
                adt = lc[1] if isinstance(lc, tuple) and len(lc) > 1 else False
                if len(name) == 4:
                    temp = _lookup.get(name[:2], AMBIENT)
                    volt = _lookup.get(name[2:4], 'NOMINAL')
                elif len(name) == 2:
                    temp = _lookup.get(name, AMBIENT)
                    volt = 'NOMINAL'
                else:
                    temp = AMBIENT
                    volt = 'NOMINAL'
                processed_corners.append((name, (temp, volt, adt)))
        corners = collections.OrderedDict(processed_corners) if processed_corners else None
    except (KeyError, AttributeError):
        log.warning("Chamber corner data is not available or not in correct form.")
        return False

    log.debug('-' * 20)
    log.debug("{0} : Chamber Corners = {1}".format(container, listed_corners))

    # Now check for proper form of corners dict.
    for corner in corners:
        if not isinstance(corners[corner], tuple):
            log.error("Product specific corners are not in the proper form.")
            raise apexceptions.AbortException

    # Get the current corner definition (possibly set by another container in the same chamber)
    S_KEY = '_'.join(container.split('|')[:-1])
    cc_key = 'chamber_corners_' + S_KEY
    with locking.named_priority_lock('__corners__' + S_KEY):
        try:
            log.debug("Chamber corner cache key (set) = {0}".format(cc_key))
            established_corners = aplib.get_cached_data(cc_key)
        except (KeyError, apexceptions.ApolloException):
            established_corners = None

        if not forced_corners:
            # Save the product-specific corner selections for use by SEQ.
            if not established_corners:
                established_corners = corners
                aplib.cache_data(cc_key, established_corners)
                log.debug("*** A new chamber corner set has been established. ***")

            # All UUT corner definitions must match.  This allows different PIDs in the same chamber BUT requires them
            # to all have the same corner definition.
            if corners != established_corners:
                log.error("Chamber corners: REJECTED!")
                log.error("There is a mismatch of chamber_corners in {0}.  This is NOT allowed.".format(container))
                log.error("Please correct the situation before running the chamber.  Inspect UUT product definitions.")
                raise apexceptions.AbortException("MISMATCH of chamber corners in {0}.".format(container))
            else:
                log.debug("Chamber corners: ACCEPTED.  {0}".format(established_corners))
        else:
            aplib.cache_data(cc_key, corners)
            log.debug("Chamber corners: FORCED.  {0}".format(corners))

    return True


def get_global_corners(container_key=None):
    """ Get Corners
    This is strictly a read of the global cache; therefore no locking required.
    IMPORTANT: This is done by sequence_definition() so MUST be compatible with Apollo main process.
               Global cache key is the station path (i.e. chamber).
    :return:
    """
    log.debug("Global Corners: get...")
    if not container_key:
        log.debug("Need to get container key...")
        container_key = aplib.get_my_container_key()
    S_KEY = '_'.join(container_key.split('|')[:-1])
    cc_key = 'chamber_corners_' + S_KEY
    try:
        log.debug("Chamber corner cache key (get) = {0}".format(cc_key))
        corners = aplib.get_cached_data(cc_key)
    except (KeyError, apexceptions.ApolloException) as e:
        log.exception("Problem with chamber corners in global cache.")
        log.exception(e.message)
        corners = None

    if not corners:
        log.error("Chamber corners: ABSENT!")
        log.error("Global cache key = {0}".format(cc_key))
        log.error("Please correct the situation before running the chamber.  Inspect UUT product definitions.")
        raise apexceptions.AbortException("Chamber corners: ABSENT!")
    else:
        log.debug("Chamber corners: PRESENT.")
    return corners


def set_chamber_slots(max_chamber_slots=None):
    active_chamber_slots_key, max_chamber_slots_key = get_chamber_slots_keys()
    max_slots = str(DEFAULT_MAX_CHAMBER_SLOTS) if not max_chamber_slots else max_chamber_slots
    aplib.cache_data(active_chamber_slots_key, [])
    aplib.cache_data(max_chamber_slots_key, max_slots)
    return True


def get_chamber_slots_keys(container_key=None):
    station = common_utils.get_station_key(container_key)
    active_chamber_slots_key = 'active_chamber_slots_{0}'.format(station)
    max_chamber_slots_key = 'max_chamber_slots_{0}'.format(station)
    return active_chamber_slots_key, max_chamber_slots_key
