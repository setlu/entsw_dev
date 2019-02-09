""" Common Utility Module
========================================================================================================================

Intended for general purpose utilities that are product and product family agnostic.

Categories include:
  1. Decorators
  2. IP Addr
  3. Data Vaildation
  4. Data Presentation
  5. Numerical
  6. Linux OS Related
  7. Server Related
  8. Python Related
  9. UUT Related (may not be product agnostic)

========================================================================================================================
"""

# Python
# ------
import sys
import ast
import os
import re
import time
import datetime
import subprocess
import logging
import collections
import netifaces
import functools
import inspect
import platform
import ipaddress
import operator
import shutil
import random
import itertools
import json


# Apollo
# ------
from apollo.libs import lib as aplib
from apollo.engine import apexceptions
from apollo.engine import utils as aputils
from apollo.libs import cesiumlib
from apollo.libs import locking


__title__ = "EntSw Common Utility Module"
__version__ = '2.0.0'
__author__ = 'bborel'

DEPTH = 0
IP_RESERVED_SPACE = 20
CESIUM_MAX_SERVICE_ATTEMPTS = 3
CESIUM_MAX_SERVICE_TIME = 10.00
CESIUM_LOCKED_SERVICES = {'ACT2': ['get_act2_certificate_chain',
                                   'sign_act2_challenge_data',
                                   'get_act2_cliip',
                                   'record_act2_cliip_insertion_status',
                                   'get_act2_sudi_certificate',
                                   'get_act2_resudi_certificate',
                                   'record_act2_sudi_cert_installation_status',
                                   ]
                          }
VALIDATION_PATTERNS = {
    'ipv4':   r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    'ipv6':   r"^(?:(?:[A-Fa-f0-9]{1,4})?[\:\.\- ]){7}[A-Fa-f0-9]{1,4}$",
    'mac':    r"(?:^(?:[A-Fa-f0-9]{2}[\.\:\- ]){5}[A-Fa-f0-9]{2}$)|"
              r"(?:^(?:[A-Fa-f0-9]{4}[\.\:\- ]){2}[A-Fa-f0-9]{4}$)|"
              r"(?:^(?:0x)?(?:[A-Fa-f0-9]{12})$)",
    'csn':    r"^[A-Z]{3}[0-9]{4}[A-HJ-NP-Z0-9]{4}$",
    'pid':    r"^[A-Z][A-Za-z0-9\-\=\+]{2,17}$",
    'cpn':    r"^[0-9]{2,3}\-[0-9]{4,6}\-[0-9]{2}$",
    'cpn73':  r"^73\-[0-9]{4,6}\-[0-9]{2}$",
    'cpn68':  r"^68\-[0-9]{4,6}\-[0-9]{2}$",
    'cpn800': r"^800\-[0-9]{4,6}\-[0-9]{2}$",
    'crev':   r"^[A-HJ-NP-Z0-9]{2,3}$",
    'vid':    r"^[A-HJ-NP-Z0-9]{2,3}$",
    'user':   r"^[a-z_][a-z0-9_-]{0,31}$",
    'qckl':   r"^[A-HJ-NP-Z][0-9]{8}$",
    'eco':    r"^(?:0x)?[A-F0-9]{1,2}[0-9]{3,6}$",
    'eci':    r"^[0-9]{6}$",
    'clei':   r"^[A-Z0-9]{10}$",
    'lineid': r"^[0-9]{8,10}$",
}
CISCO_SERNUM_PREFIXES = {
    # <Apollo CHM site>: [<prefix>, <prefix>, ...]
    'cisco': ['TST', '*ANY*'],
    'celtha': ['CTH'],
    'foxch': ['FOC', 'FOX', 'FCW', 'FCH'],
    'fxh2': ['FOC', 'FCW', 'FTX', 'FHH', 'FTH'],
    'fjz': ['FOC', 'FCW', 'FJZ'],
    'fcz': ['FOC', 'FCW', 'FCZ'],
    'fdo': ['FDO'],
    'solpen': ['SOL', 'PEN'],
    'fgn': ['FGN', 'LCC', 'LRM'],
    'jabpen': ['JPE', 'JAE'],
    'jmx2': ['JMX', 'JPE', 'JAE','JAD'],
    'jmx3': ['JMX', 'JPE', 'JAE','JAD'],
}

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


def show_version():
    log.info("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# ----------------------------------------------------------------------------------------------------------------------
# Decorators
# ----------------------------------------------------------------------------------------------------------------------
def func_details(func=None, show=True, show_args=False):
    """ DECORATOR Function Details
    Use this as a decorator to show function info in the SEQLOG.
    :param (obj) func: Calling Function
    :param (bool) show: Toggle to display the decorator output
    :param (bool) show_args: Toggle display of function arguments.
    :return:
    """
    global DEPTH

    if func is None:
        return functools.partial(func_details, show_args=show_args)

    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        if not show:
            return func(*args, **kwargs)
        # Add code here for before function
        global DEPTH
        DEPTH += 1
        ident = '-' * DEPTH
        # frame = inspect.stack()[DEPTH]                <-- future use
        # calling_module = inspect.getmodule(frame[0])  <-- future use
        funcmodule = inspect.getmodule(func)
        qualified_function_name = '{0}.{1}'.format(funcmodule.__name__, func.__name__)
        if kwargs:
            if show_args:
                append_args_text = "{0}".format(args[0:])
                append_kwargs_text = "{0}".format(kwargs)
                log.debug(r"{0}> {1}{2} ...".format(ident, qualified_function_name, append_args_text))
                step = 800
                for i in range(0, len(append_kwargs_text), step):
                    log.debug("{0} {1}  {2}".format(' ' * len(ident),
                                                    ' ' * len(qualified_function_name),
                                                    append_kwargs_text[i:i + step]))
            else:
                log.debug(r"{0}> {1}".format(ident, qualified_function_name))
            r = func(*args, **kwargs)
        else:
            append_text = "{0}".format(args[0:]) if show_args else ''
            log.debug(r"{0}> {1}{2}".format(ident, qualified_function_name, append_text))
            r = func(*args)
        # Add code here for after function
        log.debug(r"<{0} {1}".format(ident, qualified_function_name))
        DEPTH -= 1
        return r

    return func_wrapper


def cesium_srvc_retry(func=None, record=True, max_attempts=CESIUM_MAX_SERVICE_ATTEMPTS, max_time=CESIUM_MAX_SERVICE_TIME, lock_enabled=True):
    """ DECORATOR Cesium Service Retry

    USAGE INSTRUCTIONS:
        1. Create a "wrapper" function with the SAME NAME as the cesiumlib method to call.
        2. Place this decorator on that function.
        Ex1.
            @cesium_srvc_retry
            def verify_quack_label(sernum, label_sernum):
                return cesiumlib.verify_quack_label(serial_number=sernum, quack_label_number=label_sernum)

        If optional params are desired to change the defaults, then use as follows:
        Ex2.
            @cesium_srvc_retry(record=True, max_attempts=5, max_time=15.0, lock_enabled=False)
            def verify_quack_label(sernum, label_sernum):
                return cesiumlib.verify_quack_label(serial_number=sernum, quack_label_number=label_sernum)


    :param (obj) func:
    :param (bool) record: Flag to record retries to the measurements db.
    :param (int) max_attempts: Maximum attempts to call the given service.
    :param (int) max_time: Maximum time allowed for a service call to respond.
    :param (bool) lock_enabled: If the service is tagged for locking then this will disable the locking when False.
    :return:
    """
    if func is None:
        return functools.partial(cesium_srvc_retry,
                                 record=record,
                                 max_attempts=max_attempts,
                                 max_time=max_time,
                                 lock_enabled=lock_enabled)

    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        """ (INTERNAL) Function Wrapper
        Perform the wrapped process.
        :param args:
        :param kwargs:
        :return:
        """

        def __find_service_lock(name):
            """ (INTERNAL) Find Service Lock
            Check to see if the service requires a lock.
            :param name:
            :return (str): The lock category name (semaphore for locking a set of services).
            """
            log.debug("Checking lock requirement for '{0}' ...".format(name))
            category = None
            if lock_enabled:
                for category in CESIUM_LOCKED_SERVICES.keys():
                    if name in CESIUM_LOCKED_SERVICES[category]:
                        log.info("This {0} Cesium Service will be LOCKED while in use: {1}".format(category, name))
                        break
                else:
                    category = None
            return category

        def __do_service_retrys(_func, _lock_name):
            """ (INTERNAL) Do the service
            Attempt a service call; multiple retries.
            :param _func:
            :param _lock_name:
            :return:
            """
            _success = False
            lp_cnt = 0
            r, e = None, None
            srvc_times = []
            while not _success and lp_cnt < max_attempts:
                lp_cnt += 1
                mktime, mktime2 = 0.0, 0.0
                try:
                    log.debug("Cesium Srvc: {0} attempt={1}...".format(_func.__name__.lstrip('_'), lp_cnt))
                    time.sleep(lp_cnt ** 2)  # Back-off wait time, exponential
                    if _lock_name:
                        log.debug("Cesium service lock attempt...")
                        with locking.named_priority_lock('cesium_service_lock_{0}'.format(_lock_name)):
                            log.debug("Cesium service running LOCKED ({0})...".format(_lock_name))
                            _, mktime = getservertime()
                            r = _func(*args, **kwargs)
                            _, mktime2 = getservertime()
                    else:
                        log.debug("Cesium service running unlocked...")
                        _, mktime = getservertime()
                        r = _func(*args, **kwargs)
                        _, mktime2 = getservertime()
                    _success = True
                    e = None
                except (apexceptions.ServiceFailure, apexceptions.ApolloException, Exception) as e:
                    log.error("{0}: {1}".format(type(e).__name__.upper(), e.message))
                    _, mktime2 = getservertime()
                    mktime = mktime2 if not mktime else mktime
                finally:
                    call_time = mktime2 - mktime
                    log.debug("Cesium service call time: {0} secs.".format(call_time))
                    srvc_times.append(call_time)
            return r, _success, lp_cnt, srvc_times, e

        # Setup for recording.
        srvc_name = func.__name__.lstrip('_')
        lim_d_retry = dict(type='numeric', limit='1 <= value <= {0}'.format(max_attempts))
        lim_n_retry = 'CSA_{0}'.format(srvc_name)
        lim_d_time = dict(type='numeric', limit='0.00 <= value <= {0}'.format(max_time))
        lim_n_time = 'CST_{0}'.format(srvc_name)

        # Prep record
        limits_are_available = False
        if record:
            try:
                aplib.add_limits(limit_data=lim_d_retry, limit_name=lim_n_retry)
                aplib.add_limits(limit_data=lim_d_time, limit_name=lim_n_time)
                limits_are_available = True
                log.debug("Tracking cesium srvc '{0}' and '{1}'.".format(lim_n_retry, lim_n_time))
            except (apexceptions.ServiceFailure, apexceptions.ApolloException, Exception):
                log.debug("No srvc limit add.")

        # Determine if the service should be locked.
        lock_name = __find_service_lock(srvc_name)

        # Run the Service w/ retrys
        ret, success, lp_cnt, srvc_times, cesium_err = __do_service_retrys(func, lock_name)

        # Record
        if limits_are_available:
            try:
                aplib.verify_measure(limit_name=lim_n_retry, value=lp_cnt)
                for t in srvc_times:
                    aplib.verify_measure(limit_name=lim_n_time, value=t)
            except apexceptions.ValidationError:
                log.warning("Measurement outside of limits.")
            except AttributeError:
                log.debug("Cannot record.")
            except (apexceptions.ServiceFailure, apexceptions.ApolloException, Exception):
                log.debug("No verify/record service.")

        # Process exit
        if not success:
            raise apexceptions.ServiceFailure("Cesium Service call {0}: FAILED, exceeded retries!  ERROR: {1}".format(srvc_name, cesium_err))
        else:
            log.info("Cesium Service call {0}: PASSED!".format(srvc_name))
        return ret

    return func_wrapper


def func_retry(func=None, max_attempts=3, ask_yn=None):
    """ DECORATOR Function Retry
    Use this as a decorator to retry a function that returns None/False on failure and a non-null/True on passing.
    :param (obj) func: Calling Function
    :param (int) max_attempts:
    :param (str) ask_yn: Text for an ask Yes/No question to confirm retry; Yes=Continue, No=Fail
    :return:
    """

    if func is None:
        return functools.partial(func_retry, max_attempts=max_attempts, ask_yn=ask_yn)

    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        cnt = 0
        r = None
        f_err = ''
        done = False
        while cnt < max_attempts:
            cnt += 1
            log.debug("FUNC {0} attempt: {1}".format(func.__name__, cnt))
            try:
                r = func(*args, **kwargs)
                done = r[0] if isinstance(r, tuple) else r
            except Exception as e:
                f_err = e.message
                log.error(f_err)
            #
            if done:
                log.debug("FUNC {0} done!".format(func.__name__))
                break
            #
            if ask_yn and cnt < max_attempts:
                if aplib.ask_question(ask_yn, answers=['YES', 'NO']) == 'NO':
                    log.error("The retry prompt was refused.")
                    return r
        else:
            log.debug("FUNC {0} max attempts met!  ERROR: {1}".format(func.__name__, f_err))
        return r

    return func_wrapper


def apollo_step(func=None, s='', ctx=''):
    """ DECORATOR Apollo Step
    Use this as a decorator to indicate a function/method is an Apollo step.
    :param (obj) func: Calling Function
    :param (str) ctx: Container Text add-on
    :param (str) s: Type of step ''=(aka Standard) or 'Debug'=Eng Debug Menu
    :return:
    """

    if func is None:
        return functools.partial(apollo_step, s=s, ctx=ctx)

    setattr(func, 'decorator', 'apollo_step')

    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        addon1 = ' {0}'.format(ctx) if ctx else ''
        addon2 = '  ({0})'.format(s) if s else ''
        try:
            aplib.set_container_text('{0}{1}'.format(func.__name__.upper(), addon1))
        except RuntimeError:
            pass
        desc1 = '> STEP: {0}{1}{2}'.format(func.__name__.title().replace('_', ' '), addon1, addon2)
        log.info('-' * len(desc1))
        log.info(desc1)
        r = func(*args, **kwargs)
        desc2 = '< STEP: {0}{1}'.format(func.__name__.title().replace('_', ' '), addon1)
        log.debug(desc2)
        log.debug('-' * len(desc2))
        return r

    return func_wrapper


# ----------------------------------------------------------------------------------------------------------------------
# Class Usage
# ----------------------------------------------------------------------------------------------------------------------
def select_class(class_generic_name, owner_module, product_family, product_generation, product_variant=None):
    """ Select Class

    :param (str) class_generic_name: Generic name of class indicating a certain category.
                                     E.g. "Traffic", "Stardust", "Rommon", etc.
    :param (obj) owner_module: The import python module that contains the class to select.
    :param (str) product_family: "C2K", "C3K", "C4K", etc.
    :param (str) product_generation: "GEN2", "GEN3", etc.
    :param (str) product_variant: Any variation nomenclature for class name (not typically used).
    :return (obj) class:
    """
    log.debug("Input: {0}, {1}, {2}, {3}, {4}".format(class_generic_name, owner_module, product_family, product_generation, product_variant))
    if not isinstance(product_family, str) or len(product_family) < 2:
        log.error("Parameter (product_family) requirement NOT met; cannot select class.")
        return None
    if not isinstance(product_generation, str) or len(product_generation) < 2:
        log.error("Parameter (product_generation) requirement NOT met; cannot select class.")
        return None
    if not isinstance(class_generic_name, str) or len(class_generic_name) < 2:
        log.error("Parameter (product_category) requirement NOT met; cannot select class.")
        log.error("Note: This parameter is NOT optional.")
        return None

    pfam = product_family.title() if product_family else ''
    pgen = product_generation.title() if product_generation else ''
    pvar = product_variant.title() if product_variant else ''
    cgn = class_generic_name.title()
    log.debug("Class Driver selection...")
    log.debug("Module       = {0}".format(owner_module))
    log.debug("Family       = {0}".format(pfam))
    log.debug("Generation   = {0}".format(pgen))
    log.debug("Variant      = {0}".format(pvar))
    log.debug("Generic Name = {0}".format(cgn))

    # Look for most specific class first then progressively less specific until one is found.
    possible_class_names = ['{0}{1}{2}{3}'.format(pfam, pgen, pvar, cgn),
                            '{0}{1}{2}'.format(pfam, pgen, cgn),
                            '{0}{1}'.format(pfam, cgn),
                            '{0}'.format(cgn)]
    log.debug("Possible Class Drivers: {0}".format(possible_class_names))
    for class_name in possible_class_names:
        if hasattr(owner_module, class_name):
            class_object = getattr(owner_module, class_name)
            log.info("Class driver selected = {0}".format(class_object.__name__))
            break
    else:
        log.error("No class drivers to select.")
        log.error("Check {0} and the selection parameters.".format(owner_module))
        class_object = None

    return class_object


# ----------------------------------------------------------------------------------------------------------------------
# Data Validation
# ----------------------------------------------------------------------------------------------------------------------
def validate_ip_addr(ip, ip_type=None):
    """ IP Format Validation
    ------------------------
    Check for a valid form of an IPv4 or IPv6 address.
    :param ip: Can be IPv4 or IPv6 string.
    :param ip_type: 'IPv4' or 'IPv6'  If not specified then check for both.
    :return: True if valid.
    """
    if not ip:
        return False
    m4 = re.match(VALIDATION_PATTERNS['ipv4'], ip)
    m6 = re.match(VALIDATION_PATTERNS['ipv6'], ip)
    if ip_type == 'IPv4':
        ret = True if m4 else False
    elif ip_type == 'IPv6':
        ret = True if m6 else False
    elif ip_type is None:
        ret = True if m4 or m6 else False
        ip_type = 'IPv4 or IPv6'
    else:
        log.warning("IP type is unknown.")
        ret = False
    log.error("IP Addr ({0}) is NOT a valid {1}!".format(ip, ip_type)) if not ret else None
    return ret


def validate_mac_addr(mac, silent=False):
    """ MAC Format Validation
    Check for a valid form of a MAC address.

    :param mac: String of MAC address.
    :param silent:
    :return: True if valid.
    """
    INVALID_MACS = [
        ('00:00:00:00:00:00', 'Zero MAC'),
        ('FF:FF:FF:FF:FF:FF', 'FF MAC'),
        ('00:11:22:34:56:00', 'TLV Default MAC'),
        ('BA:DB:AD:BA:DB:AD', "Full BAD MAC"),
        ('11:22:33:44:55:00', "1-5 Default MAC")
    ]
    if not mac:
        return False

    mac2 = convert_mac(mac, conv_type='6:', case='upper')
    for bad_mac, desc in INVALID_MACS:
        if mac2 == bad_mac:
            log.warning("{0} = {1} is not valid!".format(mac2, desc))
            return False

    if aplib.get_apollo_mode() == aplib.MODE_PROD:
        if mac2[:8] == 'BA:DB:AD':
            log.error("Production mode does not allow BA:DB:AD for MAC prefix.")
            log.error("Please reprogram the MAC_ADDR to a valid value.")
            return False

    m = re.match(VALIDATION_PATTERNS['mac'], mac)
    ret = True if m else False
    log.warning("MAC Addr ({0}) is NOT valid!".format(mac)) if not ret and not silent else None
    return ret


def validate_sernum(sernum, silent=False, site_check=False):
    """ Validate Cisco Serial Number
    Refer to Document: 95-1766-01  SPEC,LBL,GLOBAL,SN BARCODE,MECH/PCBA
    Note: The letters "I" and "O" were excluded due to potential confusion with "1" & "0".
    :param (str) sernum: CSN in the form LLLYYWWSSSS  (SSSS is Base-34)
    :param (bool) silent:
    :param (bool) site_check: Check sernum prefix for proper site code.  The 'cisco' site code will accept any prefix.
                              Note: This function uses the CISCO_SERNUM_PREFIXES dict.
    :return:
    """
    if not sernum:
        log.warning("No sernum.")
        return False

    if site_check:
        allowed_prefixes = get_cisco_sernum_prefixes(silent=silent)
        log.debug("Allowed sernum prefixes: {0}".format(allowed_prefixes)) if not silent else None
        if sernum[:3] not in allowed_prefixes and '*ANY*' not in allowed_prefixes:
            log.warning("Serial Number ({0}) is NOT valid for the site!".format(sernum))
            return False

    m = re.match(VALIDATION_PATTERNS['csn'], sernum)
    ret = True if m else False
    log.warning("Serial Number ({0}) is NOT valid!".format(sernum)) if not ret and not silent else None

    if sernum[0:3] == 'TST':
        log.debug("Ignore SN validation for development puroposes.")
        return True

    return ret


def validate_pid(pid, silent=False):
    """ Validate Product Identifier (PID)
    Note: Must begin with a letter.  Max of 18 chars.
    :param pid:
    :param silent:
    :return:
    """
    if not pid:
        return False
    m = re.match(VALIDATION_PATTERNS['pid'], pid)
    ret = True if m else False
    log.warning("PID ({0}) is NOT valid!".format(pid)) if not ret and not silent else None
    return ret


def validate_cpn(cpn, silent=False, pattern_key='cpn'):
    """ Validate Cisco Part Number (CPN)
    Note: Must have 3 parts:
          Class Code = 2-3 digits
          Base Num = 4-6 digits
          Version = 2 digits ONLY
    See EDCS-615470 for more details.
    :param cpn:
    :param silent:
    :param pattern_key:
    :return:
    """
    if not cpn:
        return False
    m = re.match(VALIDATION_PATTERNS[pattern_key], cpn)
    ret = True if m else False
    log.warning("CPN ({0}) is NOT valid (key={1})!".format(cpn, pattern_key)) if not ret and not silent else None
    return ret


def validate_rev(rev, silent=False):
    """ Validate Cisco Revision Number (REV)
    Only 2 chars that can be alpha-numeric.  (no "I" or "O")
    :param rev:
    :param silent:
    :return:
    """
    if not rev:
        return False
    m = re.match(VALIDATION_PATTERNS['crev'], rev)
    ret = True if m else False
    log.warning("Revision Number ({0}) is NOT valid!".format(rev)) if not ret and not silent else None
    return ret


def validate_vid(vid, silent=False):
    """ Validate Cisco Version ID (VID)
    Only 3 chars that can be alpha-numeric.  (no "I" or "O")
    :param vid:
    :param silent:
    :return:
    """
    if not vid:
        return False
    m = re.match(VALIDATION_PATTERNS['vid'], vid)
    ret = True if m else False
    if not silent:
        if ret:
            if len(m.group(0)) == 2 or m.group(0)[:1].isalpha():
                log.warning("Non-standard VID ({0}); typically proto.".format(vid))
        else:
            log.warning("Version ID ({0}) is NOT valid!".format(vid))
    return ret


def validate_username(username, silent=False):
    """ Validate a Username format
    :param username:
    :param silent:
    :return:
    """
    if not username:
        return False
    m = re.match(VALIDATION_PATTERNS['user'], username)
    ret = True if m else False
    log.warning("Username ({0}) is NOT valid!".format(username)) if not ret and not silent else None
    return ret


def validate_quack(quack_sn, silent=False):
    """ Validate Quack/ACT Chip Serial Number
    Note: This is scanned from the tiny label on the chip.
    :param quack_sn:
    :param silent:
    :return:
    """
    if not quack_sn:
        return False
    m = re.match(VALIDATION_PATTERNS['qckl'], quack_sn)
    ret = True if m else False
    log.warning("Quack Label Serial Number ({0}) is NOT valid!".format(quack_sn)) if not ret and not silent else None
    return ret


def validate_eco_deviation(eco_deviation_num, silent=False):
    """ Validate Cisco QUACK/ACT Chip Serial Number
    Note: This is scanned from the tiny label on the chip.
    :param eco_deviation_num;
    :param silent:
    :return:
    """
    if not eco_deviation_num:
        return False
    m = re.match(VALIDATION_PATTERNS['eco'], eco_deviation_num)
    ret = True if m else False
    log.warning("ECO Deviation Number ({0}) is NOT valid!".format(eco_deviation_num)) if not ret and not silent else None
    return ret


def validate_eci(eci, silent=False):
    """
    This function will validate if provided number is valid ECI number
    :param eci: String, ECI number
    :param silent: Boolean, (default false): print warning to log
    :return: Boolean
    """
    if not eci:
        return False
    m = re.match(VALIDATION_PATTERNS['eci'], eci)
    ret = True if m else False
    log.warning("ECI Number ({0}) is NOT valid!".format(eci)) if not ret and not silent else None
    return ret


def validate_lineid(lineid, silent=False):
    """ Validate LineID
    :param lineid:
    :param silent:
    :return:
    """
    if not lineid:
        return False
    m = re.match(VALIDATION_PATTERNS['lineid'], lineid)
    ret = True if m else False
    log.warning("LineID ({0}) is NOT valid!".format(lineid)) if not ret and not silent else None
    return ret


def convert_mac(mac, conv_type='6:', case=None):
    """ Convert MAC Format
    Change the nomenclature of the MAC to the desired type.
    The separator character can be anything except a hex digit.
    Some examples are given below.
    :param (str) mac:
    :param (str) conv_type: '0x' = 0xbadbadbadbad    (examples)
                            '1'  = badbadbadbad
                            '6.' = ba.db.ad.ba.db.ad
                            '6:' = ba:db:ad:ba:db:ad
                            '6-' = ba-db-ad-ba-db-ad
                            '6 ' = ba db ad ba db ad
                            '3.' = badb.adba.dbad
                            '3:' = badb:adba:dbad
                            '3-' = badb-adba-dbad
                            '3 ' = badb adba dbad
                            '2-' = badbad-badbad
                            '2 ' = badbad badbad
    :param (str) case: 'upper', 'lower', None/other (leave as-is)
    :return (str): New MAC
    """
    if not isinstance(conv_type, str):
        log.error("The 'conv_type' parameter must be a str (see the docstring).")
        log.warning("Returning the original MAC.")
        return mac

    if len(mac) < 12:
        log.error("The mac input did not meet minimum length.")
        return mac

    _mac = str(mac)
    _mac = _mac[2:] if _mac[0:2] == '0x' else _mac
    m = re.sub('[^a-fA-F0-9]', '', str(_mac))
    if conv_type == '0x':
        new_mac = '0x{0}'.format(m)
    elif conv_type == '1':
        new_mac = ''.join(a + b for a, b in itertools.izip_longest(m[::2], m[1::2], fillvalue=''))
    elif re.match('^6[^a-fA-F0-9]$', conv_type):
        new_mac = conv_type[1:2].join(a + b for a, b in
                                      itertools.izip_longest(m[::2], m[1::2], fillvalue=''))
    elif re.match('^3[^a-fA-F0-9]$', conv_type):
        new_mac = conv_type[1:2].join(a + b + c + d for a, b, c, d in
                                      itertools.izip_longest(m[::4], m[1::4], m[2::4], m[3::4], fillvalue=''))
    elif re.match('^2[^a-fA-F0-9]$', conv_type):
        new_mac = conv_type[1:2].join(a + b + c + d + e + f for a, b, c, d, e, f in
                                      itertools.izip_longest(m[::6], m[1::6], m[2::6], m[3::6], m[4::6], m[5::6], fillvalue=''))
    else:
        log.warning("Conversion type unknown; returning original MAC.")
        return mac

    case = case.lower() if case else case
    if case == 'upper':
        return re.sub('X', 'x', new_mac.upper())
    elif case == 'lower':
        return new_mac.lower()
    else:
        return new_mac


def convert_mac_single_upper(mac):
    return convert_mac(mac, conv_type='0x', case='upper')


def prepare_tst_data(tst_data_dict):
    """
    This function will filter given dictionary and removes items which have None values and prepare the dict to
    be used as **kwargs for cesiumlib.add_tst_data function
    :param tst_data_dict: Dictionary of data which should be registered into tst
    :return: dictionary: dictionary with tst data prepared to be used as argument for cesiumlib.add_tst_data()
    """
    pre_sequence_info = aplib.get_pre_sequence_info()
    tst_data_dict = {k: v for k, v in tst_data_dict.items() if v is not None}
    tst_data_dict['test_container'] = pre_sequence_info.container
    return tst_data_dict


def convert_eco_deviation(eco_deviation_num):
    """ Convert ECO/Deviation Number
    Use this for TLV programming whereby the ECO/Deviation number MUST be in hex form.
    :param eco_deviation_num:
    :return:
    """
    if eco_deviation_num == 'NONE' or eco_deviation_num is None or eco_deviation_num == '' or eco_deviation_num == 'SKIP':
        value = '0x00000000'
    else:
        value = str(eco_deviation_num)
    try:
        int(value, 16)
        value = '0x{0}'.format(value) if value[:2] != '0x' else value
    except ValueError:
        log.error("ECO/Deviation Number cannot convert to a hexidecimal!")
        log.error("A new number MUST be assigned that follows the proper format.")
        value = '0x00000000'
    return value


# ----------------------------------------------------------------------------------------------------------------------
# Data Entry
# ----------------------------------------------------------------------------------------------------------------------
def get_data_from_operator(uut_category, product_desc, data_items, rev_map, upper_only=True, gui=True):
    """ Get Data from the Operator (EXTERNAL)
    Scan/enter a certain amount of items about the UUT.
    If a given item being scanned also has a supplementary suffix (e.g. REVISION number) then a map must be provided to
    extract the proper element name for the suffix value scanned/entered.
    Note: Params with SKIP or blank values will NOT be returned.

    :param (str) uut_category: Type of UUT (SWITCH, UPLINK_MODULE, etc).
    :param (str) product_desc: Anything to identify the product
    :param (list) data_items: A list of the flash params (or other) items to scan/enter.
    :param (dict) rev_map: Revision map for lookup of item key paired with revision key.
    :param (bool) upper_only: Answers are in upper case only
    :param (bool) gui: Use the Apollo gui
    :return (dict) scanned_data:
    """
    if not data_items:
        return {}
    try:
        # Ensure items to scan is a list.
        if type(data_items) is str:
            data_items = [data_items]

        # Scan Loop for all items
        scanned_data = {}
        log.info('Scanning (or manual entry) of UUT ({0}) info from label(s)...'.format(uut_category))
        if not upper_only:
            log.info("Answers will be left as-is; no change to upper case automatically.")
        for scan_item in data_items:
            data_valid = [False]
            ree = ''  # re-enter prefix
            while scan_item and not all(data_valid):
                # Prompt operator; keep prompting until the entry is valid!
                log.info("{0}Scan/Enter item: {1} gui:{2}".format(ree, scan_item, gui))
                prompt = "{0}Scan/Enter {1} ({2} {3}): ".format(ree, scan_item, product_desc, uut_category)
                raw_answer = aplib.ask_question(prompt) if gui else raw_input(prompt)
                if raw_answer:
                    raw_answer = raw_answer.upper() if upper_only else raw_answer
                else:
                    raw_answer = ''

                # Parse any supplementary data (e.g. revision suffix) and put all info in a list
                # Return example: answers = [('TAN_NUM', '800-12345-01'), ('TAN_REVISION_NUMBER', 'A0')]
                answers = split_scanned_uut_data(scan_item, raw_answer, supp_key_map=rev_map)

                # Check the entry (might have to cycle thru any supplemental data if present)
                # Allow for 'SKIP'; primary entry will NOT be included in the returned data! (Avoid preloaded overwrite.)
                # Blank primary entries must be re-scanned/re-entered with valid data.
                data_valid = []
                for i, (param, value) in enumerate(answers):
                    if value and value != 'SKIP' and value != 'ABORT' and value != 'NONE':
                        # Check if the single scanned/entered data item has the correct form.
                        datum_valid = validate_entry(param, value)
                        # Collect
                        data_valid.append(datum_valid)
                        # Only capture the scanned values that have validated content,
                        # (i.e. operator did not leave blank and it was scanned/entered correctly).
                        if datum_valid:
                            # Populate the dict
                            scanned_data[param] = value
                        else:
                            log.warning("Entered data {0} = '{1}' is NOT valid!  Please re-enter.".format(param, value))
                            ree = 'Re-'
                    elif value == 'SKIP':
                        log.warning("SKIP entry for item '{0}'!".format(param))
                        data_valid.append(True)
                        # DO NOT return!  scanned_data[param] = '' as this could overwrite already preloaded data.
                    elif value == 'NONE':
                        log.warning("NONE entry for item '{0}', this is a special case and will be set and override previous data.".format(param))
                        data_valid.append(True)
                        scanned_data[param] = 'NONE'
                    elif value == 'ABORT':
                        log.warning("ABORT entry and process!")
                        raise apexceptions.AbortException("Operator aborted data entry process in pre-seq.")
                    else:
                        if i == 0:
                            # Primary is NOT allowed to be blank.
                            log.warning("No value entered for item '{0}'! Please re-enter.".format(param))
                            data_valid.append(False)
                            ree = 'Re-'
            # endwhile
        # endfor

    except (aplib.apexceptions.AbortException, Exception) as e:
        log.error(e)
        log.warning("Aborting Operator Entry")
        raise apexceptions.AbortException('Operator Entry Aborted')

    return scanned_data


def validate_entry(param, value, silent=False, retmsg=False):
    """ Validate Entry
    Use known keys or key suffixes to determine type of validation.
    Note: For any unknown keys return 'True' to prevent infinite validation loops.
    :param (str) param:
    :param (str) value:
    :param (bool) silent:
    :param (bool) retmsg:
    :return:
    """
    msg = ''
    if 'MODEL_NUM' in param or 'PID' == param:
        log.debug("PID validation...") if not silent else None
        ret = validate_pid(value, silent=silent)
    elif 'SERIAL_NUM' in param or 'SN' == param:
        log.debug("CSN validation...") if not silent else None
        ret = validate_sernum(value, silent=silent, site_check=True)
    elif 'TAN_NUM' in param:
        log.debug("68/800-CPN validation...") if not silent else None
        ret = any([validate_cpn(value, silent=True, pattern_key='cpn68'), validate_cpn(value, silent=True, pattern_key='cpn800')])
        log.warning("CPN TAN ({0}) is NOT valid!".format(value)) if not silent and not ret else None
    elif 'MOTHERBOARD_ASSEMBLY_NUM' in param or 'VPN' == param:
        log.debug("73-CPN validation...") if not silent else None
        ret = validate_cpn(value, silent=silent, pattern_key='cpn73')
    elif 'ASSEMBLY_NUM' in param:
        log.debug("CPN validation...") if not silent else None
        ret = validate_cpn(value, silent=silent)
    elif 'VID' in param:
        log.debug("VID validation...") if not silent else None
        ret = validate_vid(value, silent=silent)
    elif 'REVISION_NUM' in param or 'PCAREV' == param or 'HWV' == param:
        log.debug("REV validation...") if not silent else None
        ret = validate_rev(value, silent=silent)
    elif 'QUACK_LABEL_SN' in param:
        log.debug("QUACK LABEL SN validation...") if not silent else None
        ret = validate_quack(value, silent=silent)
    elif 'DEVIATION_NUM' in param or 'ECO_NUM' in param:
        log.debug('DEVIATION/ECO validation...') if not silent else None
        ret = validate_eco_deviation(value, silent=silent)
    elif 'MAC_ADDR' in param:
        log.debug('MAC_ADDR validation...') if not silent else None
        ret = validate_mac_addr(value, silent=silent)
    else:
        msg = "Unknown key: '{0}'; SKIP validation.".format(param)
        ret = True

    log.debug(msg) if not silent else None

    if retmsg:
        return ret, msg
    else:
        return ret


def enter_parent_child(desc='', names=['Parent', 'Child']):
    """ Enter Parent/Child data manually
    :param desc:
    :param names:
    :return:
    """
    data = []
    for name in names:
        sn, pid = None, None
        while not validate_sernum(sn) and sn != '':
            sn = aplib.ask_question("{0} GENEALOGY - {1} S/N:".format(desc, name))
            if sn.upper() == 'ABORT':
                raise apexceptions.AbortException
        while not validate_pid(pid, silent=True) and not validate_cpn(pid, silent=True) and pid != '':
            pid = aplib.ask_question("{0} GENEALOGY - {1} PID:".format(desc, name))
            if pid.upper() == 'ABORT':
                raise apexceptions.AbortException
        data.append(sn)
        data.append(pid)
    return data


def ask_validated_question(question, answers=None, default_ans=None, validate_func=None, rsvd_answers=None, force=False):
    """ Ask Validated Question
    Function provides mechanism for allowing a default answer and validating the answer via a validation function.
    If a default answer is NOT provided, the ask_question will be raised.
    If a default answer IS provided, the ask_question will only be raised if the default is not valid OR the
    question is forced.
    :param (str) question:
    :param (list) answers:
    :param (str) default_ans:
    :param (obj) validate_func:
    :param (list) rsvd_answers: Reserved answers with special meaning that will bypass the ask_question
    :param (bool) force: Force the ask_question once; ignore validation and rsvd_answers.
    :return:
    """
    question = '{0} [{1}]:'.format(question, default_ans) if default_ans else question
    ans = default_ans if default_ans else None
    if validate_func:
        # A validation function is provided, so loop until the answer is good.
        def __notvalid(_ans, _rsvd_answers):
            return not validate_func(_ans) if not _rsvd_answers else (not validate_func(_ans) and _ans not in _rsvd_answers)
        while __notvalid(ans, rsvd_answers) or force:
            ans = aplib.ask_question(question, answers=answers) if answers else aplib.ask_question(question)
            ans = default_ans if ans == '' else ans
            if ans == 'ABORT':
                raise apexceptions.AbortException
            force = False  # Prevent infinite
    else:
        # No validation function provided so only "one-shot".
        def __notvalid(_ans, _rsvd_answers):
            return not _ans if not _rsvd_answers else (not _ans and _ans not in _rsvd_answers)
        if __notvalid(ans, rsvd_answers) or force:
            ans = aplib.ask_question(question, answers=answers) if answers else aplib.ask_question(question)
            ans = default_ans if ans == '' else ans
            if ans == 'ABORT':
                raise apexceptions.AbortException
    return ans


def enter_cmpd_params(op, menu, **kwargs):
    """ Enter CMPD Params manually
    Note: If the param was NOT provided, then do NOT ask the question.
    :param op:
    :param menu:
    :param kwargs:
    :return:
    """
    area = kwargs.get('area', 'n/a')
    uut_type = kwargs.get('uut_type', 'n/a')
    part_number = kwargs.get('part_number', 'n/a')
    part_revision = kwargs.get('part_revision', 'n/a')
    eco_deviation_number = kwargs.get('eco_deviation_number', 'n/a')

    area = ask_validated_question(question="{0} CMPD - Enter Test Area:".format(op),
                                  answers=list(aplib.TST_AREAS),
                                  default_ans=area,
                                  validate_func=None,
                                  force=menu) if area != 'n/a' else None

    uut_type = ask_validated_question(question="{0} CMPD - Enter UUT Type (Model/PID):".format(op),
                                      answers=None,
                                      default_ans=uut_type,
                                      validate_func=validate_pid,
                                      force=menu) if uut_type != 'n/a' else None

    part_number = ask_validated_question(question="{0} CMPD - Enter Part Number:".format(op),
                                         answers=None,
                                         default_ans=part_number,
                                         validate_func=validate_cpn,
                                         force=menu) if part_number != 'n/a' else None

    part_revision = ask_validated_question(question="{0} CMPD - Enter Part Revision:".format(op),
                                           answers=None,
                                           default_ans=part_revision,
                                           validate_func=validate_rev,
                                           force=menu) if part_revision != 'n/a' else None

    eco_deviation_number = ask_validated_question(question="{0} CMPD - Enter ECO Deviation Number:".format(op),
                                                  answers=None,
                                                  default_ans=eco_deviation_number,
                                                  validate_func=validate_eco_deviation,
                                                  rsvd_answers=['NONE', 'SKIP', '', None],
                                                  force=menu) if eco_deviation_number != 'n/a' else None

    return area, uut_type, part_number, part_revision, eco_deviation_number


def get_coo_from_sn(sn):
    """
    This function will return COO based on SN. COOs data file should be located in folder defined by DATA_FILES_DIR
    :param sn: String: Serial number
    :return: coo: String: COO code
    """
    # coo = COOS.get(sn[:3])
    coo = None
    if not coo:
        raise ValueError('COO not found for SN {}'.format(sn))
    return coo


def ask_dict_question(question):
    qq = question + "All entries must be in dict format.\n" \
                    "Dict entry format examples: 'key_str': 'value_str', key_int: value_int, " \
                    "'key_str': [list], 'key_str': {dict}, ... (Values may be num, str, lists, or dicts.)\n" \
                    "Follow quoting rules for all strings."
    valid_entry = False
    d = dict()
    while not valid_entry:
        answer = aplib.ask_question(qq)
        answer = answer.strip(' ')

        if answer.upper() == 'ABORT' or answer.upper() == 'EXIT' or answer == '':
            return aplib.PASS
        if answer[0:1] != '{':
            answer = '{' + answer
        if answer[-1:] != '}':
            answer = answer + '}'
        try:
            d = ast.literal_eval(answer)
            valid_entry = True
        except ValueError as ve:
            log.warning("Entry is not vaild.")
            log.warning(ve)
            return None

    log.debug("Dict = {0}".format(d))
    yn = aplib.ask_question("Confirm to save:", answers=['YES', 'NO'])
    return d if yn == 'YES' else None


# ----------------------------------------------------------------------------------------------------------------------
# Data Presentation
# ----------------------------------------------------------------------------------------------------------------------
def print_large_dict(data_obj, title=None, max_display_length=512, sort=False, _offset=0, print_ctrl=False, exploded=True):
    """ Organized Print
    Neatly displays nested dicts and lists with large values in the SEQ LOG window.
    Note: PrettyPrint only goes to standard pipes and doesn't work in the SEQLOG in its native operation.
    :param (dict) data_obj: Data object to display
    :param (str) title: Optional title
    :param (int) max_display_length: Maximum display width of dict values
    :param (bool) sort: Sort dict keys if True
    :param (int) _offset: Key column start (internal for recursion only)
    :param (bool) print_ctrl: Flag to print CTRL chars
    :param (bool) exploded: all items, one per line
    :return:
    """
    def clean_str(data):
        """ Clean String (helper)
        :param data:
        :return:
        """
        if not print_ctrl and not isinstance(data, int) and not isinstance(data, float):
            new_str = re.sub('[\s]+', ' ', data)
            new_str = re.sub('[ ]{2,}', ' ', new_str)
            return new_str
        else:
            return data

    def _process_dict(_data, _key, _ec=''):
        log.debug("{0}{1:<{2}}: {3}".format(indent, _key, column, '{'))
        new_offset = _offset + column + 3
        print_large_dict(_data, max_display_length=max_display_length, sort=sort, _offset=new_offset)
        log.debug("{0}{1:<{2}}  {3}{4}".format(indent, ' ', column, '}', _ec))
        return

    def _process_list(_data, _key, _ec=''):
        log.debug("{0}{1:<{2}}: {3}".format(indent, _key, column, '['))
        for _i, item in enumerate(_data):
            _ec = '' if _i + 1 == len(_data) else ','
            if isinstance(item, dict):
                _process_dict(item, ' ', _ec)
            elif isinstance(item, list):
                _process_list(item, _key, _ec)
            else:
                pitem = "'{}'".format(item) if not isinstance(item, int) and not isinstance(item, float) else item
                log.debug("{0}{1:<{2}}  {3}{4}".format(indent, ' ', column, pitem, _ec))
        log.debug("{0}{1:<{2}}  {3}{4}".format(indent, ' ', column, ']', _ec))
        return

    def _process_other(_data, _key, _ec=''):
        v = str(_data) if _data else ''
        if len(v) > max_display_length:
            _i = 0
            log.debug("{0}{1:<{2}}: '{3}'".format(indent, _key, column, clean_str(v[0:max_display_length])))
            # Break-up any very large data into multiple lines.
            for row in range(1, int(round(len(v) / max_display_length)) + 1):
                _i += max_display_length
                log.debug("{0}{1:>{2}}  '{3}'".format(indent, ' ', column, clean_str(v[_i:_i + max_display_length])))
        else:
            v = clean_str(v)
            pv = "'{}'".format(v) if not isinstance(v, int) and not isinstance(v, float) else v
            log.debug("{0}{1:<{2}}: {3}{4}".format(indent, _key, column, pv, _ec))
        return

    if title and _offset == 0:
        log.debug(title)
        log.debug("-" * (max_display_length + 3))

    if not exploded:
        max_k_width = 10
        for k in data_obj.keys():
            max_k_width = len(k) if len(k) > max_k_width else max_k_width
        data_keys = sorted(data_obj.keys()) if sort else data_obj.keys()
        for k in data_keys:
            v = data_obj[k]
            if isinstance(v, list):
                if len(v) == 0:
                    log.debug("{0:<{width}}: []".format(k, width=max_k_width + 1))
                elif len(v) == 1:
                    log.debug("{0:<{width}}: [{1}]".format(k, v[0], width=max_k_width + 1))
                else:
                    if len(str(v)) > max_display_length:
                        log.debug("{0:<{width}}: [{1}".format(k, v[0], width=max_k_width + 1))
                        for item in v[1:-1]:
                            log.debug("{0:<{width}}: {1}".format(' ', item, width=max_k_width + 1))
                        log.debug("{0:<{width}}: {1}]".format(' ', v[-1:][0], width=max_k_width + 1))
                    else:
                        log.debug("{0:<{width}}: {1}".format(k, v, width=max_k_width + 1))
            else:
                log.debug("{0:<{width}}: {1}".format(k, v, width=max_k_width + 1))
        return

    if isinstance(data_obj, dict):
        data_keys = sorted(data_obj.keys()) if sort else data_obj.keys()
        max_str = max([str(d) for d in data_keys], key=len) if data_keys else ''
        indent = ' ' * _offset
        column = len(max_str) + 2
        for i, key in enumerate(data_keys):
            ec = '' if i + 1 == len(data_keys) else ','
            pkey = "'{}'".format(key) if not isinstance(key, int) and not isinstance(key, float) else key
            if isinstance(data_obj[key], dict):
                _process_dict(data_obj[key], pkey, ec)
            elif isinstance(data_obj[key], list):
                _process_list(data_obj[key], pkey, ec)
            else:
                _process_other(data_obj[key], pkey, ec)

    elif isinstance(data_obj, list):
        indent = ' ' * _offset
        str_list = [str(d) for d in data_obj if isinstance(d, str) or isinstance(d, int) or isinstance(d, float)] if data_obj else None
        max_str = max(str_list, key=len) if str_list else ''
        column = len(max_str) + 2
        _process_list(data_obj, ' ')

    else:
        indent = ' ' * _offset
        str_list = [str(d) for d in data_obj if isinstance(d, str) or isinstance(d, int) or isinstance(d, float)] if data_obj else None
        max_str = max(str_list, key=len) if str_list else ''
        column = len(max_str) + 2
        _process_other(data_obj, ' ')

    return


def datetimestr(form='week'):
    """ Date & Time String
    ----------------------
    Format the current date & time into a standardized string base on the form type.
    This can be used generically to time/date stamp filenames or anything needing a t/d stamp.

    Full list of formatting:
    %a  Locale's abbreviated weekday name.
    %A  Locale's full weekday name.
    %b  Locale's abbreviated month name.
    %B  Locale's full month name.
    %c  Locale's appropriate date and time representation.
    %d  Day of the month as a decimal number [01,31].
    %f  Microsecond as a decimal number [0,999999], zero-padded on the left
    %H  Hour (24-hour clock) as a decimal number [00,23].
    %I  Hour (12-hour clock) as a decimal number [01,12].
    %j  Day of the year as a decimal number [001,366].
    %m  Month as a decimal number [01,12].
    %M  Minute as a decimal number [00,59].
    %p  Locale's equivalent of either AM or PM.
    %S  Second as a decimal number [00,61].
    %U  Week number of the year (Sunday as the first day of the week)
    %w  Weekday as a decimal number [0(Sunday),6].
    %W  Week number of the year (Monday as the first day of the week)
    %x  Locale's appropriate date representation.
    %X  Locale's appropriate time representation.
    %y  Year without century as a decimal number [00,99].
    %Y  Year with century as a decimal number.
    %z  UTC offset in the form +HHMM or -HHMM.
    %Z  Time zone name (empty string if the object is naive).
    %%  A literal '%' character.
    :param (str) form: Name of format to use.
    :return:
    """
    if form == 'week':
        dtformat = '%W%H%M%S'       # 8 chars
    elif form == 'year':
        dtformat = '%y%m%d%H%M%S'   # 12 chars
    elif form == 'bigyear':
        dtformat = '%Y%m%d%H%M%S'   # 14 chars
    elif form == 'ymd':
        dtformat = '%y%m%d'         # 7 chars
    elif form == 'ymd2':
        dtformat = '%y%b%d'         # 9 chars
    elif form == 'ftime':
        dtformat = '%H%M%S%f'       # 12 chars
    elif '%' == form[0]:
        dtformat = form             # custom
    else:
        dtformat = '%Y%M%d%H%M%S'   # 14 chars
    d = datetime.datetime.now().strftime(dtformat)
    return d


def split_scanned_uut_data(main_key, raw_data, supp_key_map=None, sep_char=' '):
    """ Split Scanned UUT Data
    --------------------------
    Separate the main item and the supplemental item (suffix) given by barcode labels for UUT pids and part numbers.
    This is typically the REVISION number appended to the main item with a single space separator char by default
    or some other char specified.
    If a suffix is expected but NO value is found, it will be assigned an empty string.

    Note: The operator can input in 2 ways:
      1) barcode scanner
      2) manually type  (error prone or might exclude supplemental data)

    The routine maps certain main param key types to the supplemental key type automatically.
    Example of a supplemental map; primary key maps to supplementary (suffix) item.
    supp_key_map = {
        'MOTHERBOARD_ASSEMBLY_NUM': 'MOTHERBOARD_REVISION_NUM',
        'TAN_NUM': 'TAN_REVISION_NUMBER',
        'MODEL_NUM': 'MODEL_REVISION_NUM',
    }

    Barcode Examples representing raw_data:
      "73-12345-01 A2"  <-- Acceptable
      "WS-C3850-24T A0" <-- Acceptable

      It's important the barcode is properly formed and printed. Note:
      "73-12345-01A2"   <-- NOT Acceptable

    NOTE: There is no content format checking! That should be done outside this function.

    :param (str) main_key: Primary data item.
    :param (str) raw_data: Data that was scanned or entered.
    :param (dict) supp_key_map: Supplemental key map that associates the main key to the additional piece of data.
    :param (str) sep_char: Separator character
    :return (list): List of 2 x tuples  ex: [('TAN_NUM', '800-12345-01'), ('TAN_REVISION_NUMBER', 'A0')]
    """
    raw_data = raw_data.strip(' ')
    pattern = '[{0}]+'.format(sep_char)
    split_data = re.sub(pattern, sep_char, raw_data).split(sep_char)  # normalize multi sep_char's to one then split
    output_data = []
    supp_key_map = {} if not supp_key_map else supp_key_map

    supplemental_key = supp_key_map[main_key] if main_key in supp_key_map else None

    output_data.append((main_key, split_data[0]))
    if supplemental_key:
        if len(split_data) > 1:
            output_data.append((supplemental_key, split_data[1]))
        else:
            output_data.append((supplemental_key, ''))

    log.debug("Data = {0}".format(output_data))
    return output_data


def expand_comma_dash_num_list(delimited_list, string=False):
    """ Expand a compact list of positive numbers.
    The numbers may show a CSV list or a range via dash '-' or a combination of both.
    Examples:  '1,2,5-7'  -->  [1,2,5,6,7]
               Note: The function was designed to handle extra spaces, duplicates, and garbage in the
               string (manages accidental/bad entry format).
               '2-apollo,5,8--xxxxxx--10,,,  ,,,1,1,1,12' --> [1, 2, 5, 8, 9, 10, 12]
    :param (str) delimited_list:
    :param (bool) string: Elements are str instead of int if True
    :return (list): Sorted integer list
    """
    a_list = []
    if not delimited_list:
        return a_list
    # First clean up the list: remove all chars except numbers, dashes, commas; remove repeating commas & dashes; create CSV list.
    a_interim = sorted(list(set(re.sub('[,]{2,}', ',', re.sub('[\-]{2,}', '-', re.sub('[^0-9\-,]', '', delimited_list))).split(','))))
    for s in a_interim:
        if s:
            if '-' in s:
                r_list = s.split('-')
                for i, _ in enumerate(r_list):
                    if i + 1 < len(r_list) and r_list[i] and r_list[i + 1]:
                        for a in range(int(r_list[i]), int(r_list[i + 1]) + 1):
                            a_list.append(a)
                    elif r_list[i]:
                        a_list.append(int(r_list[i]))
            else:
                a_list.append(int(s))
    expanded_list = sorted(list(set(a_list))) if not string else [str(i) for i in sorted(list(set(a_list)))]
    return expanded_list


def rebuild_cmd(entry_dict, uut_config, command=None, special_key=None, special_func=None):
    """ Rebuild Cmd

    Uses a dict that contains keys of 'cmd' + others.
    The 'cmd' value is a str that can have "%mysub%" items which will be substituted by the value of the item name.
    The substitutions can also be an expression to evaluate.
    The "item name" can be from two sources (must match case):
        1. entry_dict
        2. uut_config
    Ex1.
    entry_dict = {'cmd': 'utility -v -m:%MAC_ADDR% -f:%image%',
                  'image': 'test_image_123.bin'}
    uut_config = {...,
                  'MAC_ADDR': '0xbadbadbadbad',
                  ...}
    output cmd = utility -v -m:0xbadbadbadbad -f:test_image_123.bin'

    Ex2.
    entry_dict = {'cmd': 'utility /ABC /MAC:%MAC_ADDR%+0x64 /FILE:%image%',
                  'image': 'test_image_123.bin'}
    uut_config = {...,
                  'MAC_ADDR': '0xbadbadbadc11',
                  ...}
    output cmd = utility /ABC /MAC:0xbadbadbadc11 /FILE:test_image_123.bin'

    :param (dict) entry_dict:
    :param (dict) uut_config: The standard uut_config dict.
    :param (str) command: Specified command (when not part of entry_dict)
    :param (str) special_key: Dict key to check for running the special_func.
    :param (obj) special_func:
    :return (str): cmd
    """
    if entry_dict.get('cmd', None):
        cmd = entry_dict['cmd']
    elif command:
        cmd = command
    else:
        cmd = ''

    p = re.compile('%[\S]+%')
    m = p.findall(cmd)
    if m:
        for item in m:
            item_key = item[1:-1]
            # Value retrieve
            if entry_dict.get(item_key, None):
                item_value = entry_dict[item_key]
            elif uut_config.get(item_key, None):
                item_value = uut_config[item_key]
            else:
                log.warning("Item '{0}' NOT recognized!".format(item))
                item_value = None
            # Value special
            if item_value:
                item_value = special_func(item_value) if item_key == special_key and special_func else item_value
                cmd = re.sub(item, item_value, cmd)
                m = re.search(item_value + '[\S]+', cmd)
                if m and m.group() != item_value:
                    item_value_exp = m.group()
                    # More special (if the param is an expression)
                    o = eval(item_value_exp) if item_value_exp[:2] != '0x' else hex(eval(item_value_exp))[2:].upper()
                    cmd = re.sub(re.escape(item_value_exp), o, cmd)
    return cmd


def backup_log(sernum=None, local_path=None, status=None):
    """Backup Log
    backup log to local server if need
    :param sernum: valid tst serial number
    :param local_path:  save local path
    :param status: back up FAIL/PASS log
    :return:
    """

    result = True
    current_log = aplib.get_container_connection_log_path()
    test_current_status = aplib.apdicts.stepdict.get('current_status', None)

    # local back up path
    if not local_path:
        local_path = '/tftpboot/backup_log/'
    local_time = "{:02}{:02}{:02}{:02}{:02}".format(time.localtime().tm_year, time.localtime().tm_mon,
                                                    time.localtime().tm_mday, time.localtime().tm_hour,
                                                    time.localtime().tm_min
                                                    )
    # Backup log
    if test_current_status == status and sernum:
        save_path = '{}{}_{}'.format(local_path, sernum, local_time)
        result = shutil.copytree(current_log, save_path)

    return result


# ----------------------------------------------------------------------------------------------------------------------
# Numerical
# ----------------------------------------------------------------------------------------------------------------------
def num2base(n, b, symbols='0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'):
    """ Number Base Converter
    -------------------------
    Convert any base-10 number to an arbitrary base.
    This is handy for numerical compression.
    :param n: Base-10 number to convert.
    :param b: Base to use.
    :param symbols: Symbol set. Default symbols exclude letters I and O to avoid confusion w/ numerals 1 and 0.
    :return:
    """
    if not isinstance(n, int):
        n = int(n)
    symbol_count = len(symbols)
    if n == 0:
        return [0]
    digits = '' if b <= symbol_count else []
    while n:
        digit = int(n % b)
        if b <= symbol_count:
            digits += symbols[digit]
        else:
            digits.append(digit)
        n /= b
    return digits[::-1]


def ddhhmmss(secs, style='name'):
    """ Convert Seconds
    Convert seconds to a time string.
    :param (float) secs:
    :param (str) style: 'name'  = "[[[[YY yrs, ]DD days, ]HH hrs, ]MM mins, ]SS secs"
                        'short' = "[[[[YY:]DD:]HH:]MM:]SS"
    :return:
    """
    dhms = ''
    for scale, label in zip([86400 * 365.2422, 86400, 3600, 60], ['yrs', 'days', 'hrs', 'mins']):
        result, secs = divmod(secs, scale)
        if dhms != '' or result > 0:
            plabel = ':' if style == 'short' else ' {0}, '.format(label)
            dhms += '{0:02}{1}'.format(int(result), plabel)
    plabel = '' if style == 'short' else ' secs'
    dhms += '{0:02.2f}{1}'.format(secs, plabel)
    return dhms


def is_version_greater(version=None, min_version=None, inclusive=True):
    """ Is version1 greater than version2

    Both input must be strings, and both inputs are required, raise exception otherwise.

    :param version:        (str) input version1
                        ex: '16.8.3a'
    :param min_version:    (str) input version2
    :param inclusive:      (bool) inclusive flag, whether equal yields True return, default True (equal returns True)

    :return:                True if version1 >(=) version2, depending on inclusive
                            False if version1 <(=) version2
    """
    def _try_int(x):
        try:
            return int(x)
        except ValueError:
            return x

    # Handle Nulls
    if not version:
        if min_version:
            log.warning("A > B : A is null. Nothing to compare against.")
            return False
        else:
            return (version > min_version) if not inclusive else (version >= min_version)
    elif not min_version:
        log.debug("A > B : B is null. Nothing to compare against.")
        return True

    invalid_p = re.compile(r'[^0-9a-z.]')
    valid_p = re.compile('^\d+[0-9a-z.]*?[0-9a-z]*?$')
    # Check inputs
    # NOTE: unicode type is not Python3 compatible, but Apollo won't get update to Py3 in a million years
    if not isinstance(version, (str, unicode)) or not isinstance(min_version, (str, unicode)):
        log.error('version:{0}, min_version:{1}'.format(version, min_version))
        raise Exception('Both inputs must be strings.')
    if invalid_p.search(version) or invalid_p.search(min_version):
        log.error('Invalid input version format, only numbers, lowercase letters and dot(.) are allowed')
        log.error('version:{0}, min_version:{1}'.format(version, min_version))
        raise Exception('Invalid input version format')
    if not valid_p.search(version) or not valid_p.search(min_version):
        log.error('Invalid input version format, only numbers, lowercase letters and dot(.) are allowed')
        log.error('version should start with number, end with number or letter. Such as [16.10.1a].')
        log.error('version:{0}, min_version:{1}'.format(version, min_version))
        raise Exception('Invalid input version format')

    vt1 = tuple(_try_int(x) for x in re.split('([0-9]+)', str(version)))
    vt2 = tuple(_try_int(x) for x in re.split('([0-9]+)', str(min_version)))

    if vt1 > vt2:
        return True
    elif vt1 < vt2:
        return False
    elif inclusive:
        return True
    else:
        return False


# ----------------------------------------------------------------------------------------------------------------------
# Server OS Related
# ----------------------------------------------------------------------------------------------------------------------
def shellcmd(command, cwd='.', tsleep=1.0, sudo=False, combine=True):
    """ Shell Command Runner
    ------------------------
    Run a shell command in a separate process and wait for completion.
    :param command: String command
    :param cwd:
    :param tsleep: Sleep time (secs)
    :param sudo: Run command under sudo; graphical passwd dialog will popup.
    :param combine: What to do w/ stdout & stderr -
                    True = return data as single string; False = return data in 2 element tuple.
    :return data: Anything posted to stdout & stderr.
    """
    data_stdout = ''
    data_stderr = ''
    try:
        command = r"sudo -AEP {0}".format(command) if sudo else command
        # For convenient code debug: log.debug("shellcmd={0}".format(command))
        proc = subprocess.Popen(command,
                                shell=True,
                                bufsize=100000000,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=cwd,
                                )
        time.sleep(tsleep)
        data_stdout, data_stderr = proc.communicate()

    except subprocess.CalledProcessError as e:
        log.error("Process error during 'shellcmd'.")
        log.error(e)
        log.error(e.output)

    finally:
        if combine:
            data = data_stdout + '\n' + data_stderr
            return data
        else:
            return data_stdout, data_stderr


def readfiledata(filename, ast_flag=False, start_pattern=None, end_pattern=None, raw=False):
    """ Read File Data
    ------------------
    Read a file on the server and evaluate it in the following ways:
        1. No processing, just return the raw text.
        2. Flat file, create a list with one line per list item, or
        3. Convert file as a dict; syntax must be correct. (Do not use custom data structures,
           only expect numeric, str, tuple, list, or dict in the file.)
    An option is available for capturing only the text within a start and/or end regex pattern.
    If the regex group capture option is used in the start/end patterns the line is replaced
    with the first capture group.
    :param filename: Target file.
    :param ast_flag: Convert file data to a dict (file must have correct structure).
    :param start_pattern: Regex starting pattern for file data capture.
    :param end_pattern: Regex ending pattern for file data capture.
    :param raw: Raw text or processed data. (Ignored when ast_flag is set.)
    :return filedata: A list, a dict, or raw text.
    """
    def _process_markers(fp, start_pattern, end_pattern):
        begin = False if start_pattern else True
        end = False
        fdata = ''
        for line in fp:
            if not begin:
                m = re.match(start_pattern, line)
                if m:
                    begin = True
                    # If a group capture was indicated in the start pattern then replace the first line.
                    line = m.groups()[0] if m.groups() else line
            end = True if end_pattern and re.match(end_pattern, line) else end
            fdata += line if begin and not end else ''
            if end:
                # If a group capture was indicated in the end pattern then replace the last line.
                m = re.match(end_pattern, line)
                line = m.groups()[0] if m.groups() else line
                fdata += line
                break
        return fdata

    filedata = ''
    if not os.path.isfile(filename):
        return filedata
    try:
        if ast_flag and (not start_pattern and not end_pattern):
            with open(filename, mode='r', buffering=-1) as fp:
                filedata = ast.literal_eval(fp.read())
        else:
            # Text processing
            with open(filename, mode='r', buffering=-1) as fp:
                if not start_pattern and not end_pattern:
                    # Rd file content into mem in one command.
                    # Be careful to not use this on very large files!
                    fdata = fp.read()
                else:
                    # Use pattern matching
                    # Since start or end text marker(s) were specified; process line-by-line..
                    fdata = _process_markers(fp, start_pattern, end_pattern)
            if ast_flag:
                # Eval data as dict.
                filedata = ast.literal_eval(fdata) if fdata else []
            else:
                if not raw:
                    # Break at line boundaries, and create list.
                    filedata = fdata.splitlines() if fdata else []
                else:
                    filedata = fdata

    except Exception as e:
        log.error("Problem with file: {0}".format(filename))
        log.error("Exception during file read operation: {0}".format(e))
        raise Exception(e.message)

    return filedata


def data_file_lookup(data_file, column_labels, search_vals, data_separator=';'):
    """
    This function parses given file and returns list of dictionaries. The dictionary keys age taken from [column_labels]
    and values from matched line in data_file
    :param data_file: String: filename which needs to be parsed
    :param column_labels: List: ordered column names which should reflect columns in file and which will be converted
      as keys in return dict
    :param search_vals: List: list of dicts in format [{'column_name': 'searched_value'}, ...]. This function will
      look for value in given column_name
    :param data_separator: String: regular expression which is used to separate values in line
    :return: data_dict_list: List: List of dictionaries where keys are from data_format and values from data file. List
    is empty if no match found

    Example:
        Source:
            data_file_name = '/opt/cisco/constellation/apollo/libs/te_libs/data_files/sfps.txt'
            data_format = ['pid', 'eci', 'tan', 'pn', 'prodarray']
            search_vals_list = [
                {'eci': 131603},
            ]
            print data_file_lookup(data_file_name, data_format, search_vals_list)
        Result:
            [{'pid': 'SFP-GE-S', 'eci': '131603', 'tan': '800-26525-01', 'pn': '10-2143-01', 'prodarray': '940'},]

    """
    data_dict_list = []
    with open(data_file, 'r') as f:
        for line in f:
            if re.match('\s*#', line):
                continue
            line = line.strip()
            line = list(map(lambda x: None if x == '' else x, re.split(data_separator, line)))
            if len(line) != len(column_labels):
                raise ValueError('Invalid data format of {}. Expected {} items, {} found.'.format(
                    line, len(column_labels), len(line)))
            line = {k: v for k, v in zip(column_labels, line)}
            match_check = filter(
                lambda x:
                True if re.match('{}$'.format(x.values()[0]), '{}'.format(line[x.keys()[0]]), flags=re.IGNORECASE)
                else False,
                search_vals
            )
            if len(match_check) == len(search_vals):
                data_dict_list.append(line)
    return data_dict_list


def writefiledata(filename, data, mode='w+', force_raw=False):
    """ Write File Data
    -------------------
    Basic write data to a file on the server.

     r   Open text file for reading.  The stream is positioned at the
             beginning of the file.
     r+  Open for reading and writing.  The stream is positioned at the
             beginning of the file.
     w   Truncate file to zero length or create text file for writing.
             The stream is positioned at the beginning of the file.
     w+  Open for reading and writing.  The file is created if it does not
             exist, otherwise it is truncated.  The stream is positioned at
             the beginning of the file.
     a   Open for writing.  The file is created if it does not exist.  The
             stream is positioned at the end of the file.  Subsequent writes
             to the file will always end up at the then current end of file,
             irrespective of any intervening fseek(3) or similar.
     a+  Open for reading and writing.  The file is created if it does not
             exist.  The stream is positioned at the end of the file.  Subse-
             quent writes to the file will always end up at the then current
             end of file, irrespective of any intervening fseek(3) or similar.

    :param filename:
    :param data:
    :param mode:
    :param force_raw:
    :return:
    """
    try:
        fp = open(filename, mode=mode)
        log.debug("Writing...")
        if isinstance(data, str) or force_raw:
            log.debug("Write str/raw data.")
            fp.write(data)
        elif isinstance(data, list):
            log.debug("Write list data.")
            for item in data:
                item = '{0}\n'.format(item) if item[-1:] not in ['\n', '\r'] else item
                fp.write(item)
        else:
            log.debug("Write repr(str) data.")
            fp.write(repr(data))
    except Exception as e:
        log.error("Exception during file write operation: {0}".format(e))
        return False

    return True


def touch(fname):
    """ Touch
    ---------
    Create an empty file on the server if none exist otherwise update timestamp and leave content.
    :param fname:
    :return:
    """
    try:
        os.utime(fname, None)
    except OSError:
        log.debug("Creating file...")
        shellcmd("touch {0}".format(fname))
        # Don't do this: open(fname, 'a').close()
        return False
    return True


def download_image(src_filepath, dst_filepath=None, apollo_server_conn=None, download_server=None, timeout=120):
    """ Download Image

    Custom download mechanism; currently MUST be Apollo-to-Apollo on a locally accessible network.

    :param (str) src_filepath: Source image path + filename
    :param (str) dst_filepath: Destination image path + filename
    :param (obj) apollo_server_conn: Apollo server connection.
    :param (str) download_server: Common Apollo server in local network
    :param (int) timeout:
    :return:
    """
    log.debug("download_image")
    status = dict(code=0, data='', message='', result=False)

    filename = os.path.basename(src_filepath)
    dst_filepath = os.path.join('/tftpboot', filename) if not dst_filepath else dst_filepath
    # log.debug("Src file={0}".format(src_filepath))
    # log.debug("Dst file={0}".format(dst_filepath))
    dst_path = os.path.dirname(dst_filepath)

    if os.path.exists(dst_filepath):
        log.info("Dst file ({0}) already exists.".format(dst_filepath))
        status['result'] = True
        return status

    if not apollo_server_conn:
        if hasattr(aplib.conn, 'serverSSH'):
            apollo_server_conn = aplib.conn.serverSSH
            log.debug("Using standard local server connection.")
        else:
            log.warning("No standard server connection available.")
            return status

    if not download_server:
        download_server = '10.1.1.1'
        log.warning("No download server specified.")
        log.warning("Defaulting the download server to {0}".format(download_server))

    # Check local server
    if apollo_server_conn.status != aplib.STATUS_OPEN:
        apollo_server_conn.open()
        time.sleep(2)
    speculative_prompt = '[$#%] '
    apollo_server_conn.send('cd {0}\r'.format(dst_path), expectphrase=speculative_prompt, timeout=30, regex=True)
    apollo_server_conn.send('pwd\r', expectphrase=dst_path, timeout=30, regex=True)

    # Check remote server connectivity
    apollo_server_conn.send('ping -c 3 {0}\r'.format(download_server), expectphrase=speculative_prompt, timeout=30, regex=True)
    time.sleep(3.0)
    if not re.search('[123] received', apollo_server_conn.recbuf):
        log.warning("Ping failed; no server connectivity.")
        return status

    # Perform remote copy
    apollo_server_conn.send('scp -p gen-apollo@{0}:{1} {2}\r'.format(download_server, src_filepath, dst_filepath), expectphrase='.*', timeout=30, regex=True)
    time.sleep(3.0)
    if re.search('continue connecting', apollo_server_conn.recbuf):
        apollo_server_conn.send('yes\r', expectphrase='.*', timeout=timeout, regex=True)
        time.sleep(3.0)
    if re.search('[Pp]assword', apollo_server_conn.recbuf):
        apollo_server_conn.send('Ad@pCr01!\r', expectphrase=speculative_prompt, timeout=timeout, regex=True)

    # Check result
    if os.path.exists(dst_filepath):
        status['message'] = 'SUCCESS'
        status['result'] = True
    else:
        status['message'] = 'FAILURE'
    log.debug("Action complete.")
    log.debug("Result = {0} ({1})".format(status['result'], status['message']))

    return status


# ----------------------------------------------------------------------------------------------------------------------
# Server Related
# ----------------------------------------------------------------------------------------------------------------------
def get_server_info():
    """ Get Server Info
    -------------------
    Get various system information about the Apollo server.
    :return (dict) machine: Description of server
    """
    machine = dict()
    machine['platform'] = getplatform()
    machine['system'] = getsystemrelease()
    machine['kernel'] = getkernelrelease()
    machine['hostname'] = gethostname()
    machine['eth0_ip'], machine['eth0_net'], machine['eth0_nm'] = get_system_ip_and_mask('eth0')
    machine['eth1_ip'], machine['eth1_net'], machine['eth1_nm'] = get_system_ip_and_mask('eth1')
    return machine


def getplatform():
    """ Get Platform
    :return (str):
    """
    p = platform.system()
    if p != "Linux":
        raise Exception("Can only run on the Linux platform!")
    return p


def getsystemrelease():
    """ Get System Release
    :return (str):
    """
    sr = readfiledata("/etc/system-release")
    p1 = re.compile(""".* ([0-9.]+ .*)""")
    m1 = p1.findall(sr[0])
    return m1[0]


def getkernelrelease():
    """ Get Kernel Release
    :return (str):
    """
    kr = shellcmd("uname -r").splitlines()
    return kr[0]


def gethostname():
    """ Get Host Name
    :return (str):
    """
    n = platform.node()
    if not n:
        raise Exception("Cannot get hostname!")
    return n


def getservertime(time_zone='GMT'):
    """ Get Server Time
    :param time_zone: 'GMT' or 'Local'
    :return: Tuple of (time_struct, mktime)
    """
    server_time = time.gmtime() if time_zone == 'GMT' else time.localtime()
    server_mktime = time.mktime(server_time)
    return server_time, server_mktime


def getservicestatus(service):
    command = 'service {0} status'.format(service)
    result = shellcmd(command)
    if "is running" in result:
        return True
    else:
        log.warning("Cannot get service status!")
        log.warning(result)
        return False


def network_availability(action, max_container_usage=10, check_interval=20):
    """ Network Availability

    Use this to throttle the network load when many UUT containers are trying to use the test network to download
    large files from the server.

    :param (str) action:  'acquire' or 'release'
    :param (int) max_container_usage: Throttle value; maximum number of containers to simultaneously use the test network.
    :param (int) check_interval: Minimum interval time for 'acquire' (secs).  A 10 sec buffer is always added to prevent resource flood.
    :return:
    """
    container = aplib.get_my_container_key()

    def __acquire():
        log.debug("Network acquire...")
        allowed = False
        with locking.ContainerPriorityLock('__network_availability__', wait_timeout=600, release_timeout=300):
            netusage = aplib.get_cached_data('network_usage')
            if not netusage:
                netusage = dict(containers=[container], count=1, queued=[], qcount=0)

            if netusage.get('count', 0) < max_container_usage:
                log.debug("container is {}, containers is {}".format(container, netusage.get('containers')))
                if container not in netusage.get('containers', []):
                    log.debug("Network usage by container acquire...")
                    netusage['containers'].append(container)
                    netusage['count'] = len(netusage['containers'])
                    allowed = True
                    if container in netusage.get('queued', []):
                        netusage['queued'].pop(netusage['queued'].index(container))
                        netusage['qcount'] = len(netusage['queued'])
                else:
                    allowed = True
                    log.debug("Network usage by container already acquired.")
            else:
                log.warning("Network usage by container is at maximum (Count={0}).".format(netusage.get('count', 0)))
                log.warning("This container needs to wait.")
                if container in netusage.get('containers', []):
                    allowed = True
                    log.debug("Network usage by container already acquired.")
                elif container not in netusage.get('queued', []):
                    log.debug("Container added to queue.")
                    netusage['queued'].append(container)
                    netusage['qcount'] += 1
            aplib.cache_data('network_usage', netusage)
        return allowed, netusage

    def __release():
        log.debug("Network release...")
        with locking.ContainerPriorityLock('__network_availability__', wait_timeout=600, release_timeout=300):
            netusage = aplib.get_cached_data('network_usage')
            if netusage:
                if container in netusage.get('containers', []):
                    log.debug("Network container release.")
                    netusage['containers'].pop(netusage['containers'].index(container))
                    netusage['count'] = len(netusage['containers'])
                else:
                    log.debug("Container already released.")
            aplib.cache_data('network_usage', netusage)
        return True

    if action.lower() == 'acquire':
        acquired = False
        while not acquired:
            acquired, netusage = __acquire()
            log.debug("Count  = {0},  Containers  = {1}".format(netusage.get('count', 0), netusage.get('containers', [])))
            log.debug("QCount = {0},  QContainers = {1}".format(netusage.get('qcount', 0), netusage.get('queued', [])))
            if not acquired:
                waittime = (check_interval + 10)
                log.debug("Waiting for network availability: Wait={0} secs...".format(waittime))
                time.sleep(waittime)

    elif action.lower() == 'release':
        __release()

    else:
        log.warning("Unrecognized action.")

    return


# ----------------------------------------------------------------------------------------------------------------------
# IP Query and Assignment
# ----------------------------------------------------------------------------------------------------------------------
def get_system_ip_and_mask(eth_interface):
    """ Get Apollo IP & Mask
    ------------------------
    Obtain the IP address, network, and netmask that the system OS has assigned for the given
    ethernet interface requested.
    :param eth_interface: Interface name, ex. 'eth0', 'eth1', etc.
    :return: Tuple of (Server IP, Network, Netmask)
    """
    if eth_interface in netifaces.interfaces():
        server_netif = netifaces.ifaddresses(eth_interface)
        if netifaces.AF_INET not in server_netif or len(server_netif[netifaces.AF_INET]) == 0 or 'addr' not in server_netif[netifaces.AF_INET][0]:
            log.debug(server_netif)
            msg = "This Apollo server ethernet interface '{0}' is NOT configured!".format(eth_interface)
            log.error(msg)
            raise Exception(msg)
        server_ip = server_netif[netifaces.AF_INET][0]['addr']
        netmask = netifaces.ifaddresses(eth_interface)[netifaces.AF_INET][0]['netmask']
        network = '.'.join([str(a & b) for a, b in zip([int(octet) for octet in server_ip.split('.')],
                                                       [int(octet) for octet in netmask.split('.')])])
        return server_ip, network, netmask
    else:
        msg = "This Apollo server has no interface named: '{0}'!".format(eth_interface)
        log.error(msg)
        # raise Exception(msg)
        # Allow return in the event the calling routine has multiple interfaces to try.
        return None, None, None


def get_ip_addr_assignment(connection, server_ip, mask):
    """ Get Unique IP for Connection
    Obtain a unique IP Address given the unique connection index (UID), network, and netmask.
    Exclusion of a reserved IP addr count space is available via a global setting: IP_RESERVED_SPACE.
    The exclusion is considered at the front of the D subnet boundaries.
    Network addresses (e.g. x.x.x.0 - x.x.x.1) and broadcast addresses (e.g. x.x.x.254 - x.x.x.255) are also excluded on
    a per subnet basis.
    A connection index that is outside the range of available IPs will raise an exception.
    The server IP associated with the network interface will raise an exception if the assigned IP conflicts.
    NOTE: This function is primarily used when DHCP is NOT available from the UUT (i.e. rommon typically).

    IP_RESERVED_SPACE usage example:
    mask = 255.255.0.0
    IP_RESERVED_SPACE = 20 -->   10.1.0.0 - 10.1.0.21, 10.1.1.0 - 10.1.1.21, 10.1.2.0 - 10.1.2.21, etc...

    :param connection: Apollo connection object (typically for a UUT)
    :param server_ip: String of A.B.C.D
    :param mask: String of w.x.y.z
    :return: String of "W.X.Y.Z/w.x.y.z"  IP & Mask
    """
    if not connection:
        log.warning("Connection object is empty; cannot calculate an IP.")
        return None
    if not server_ip:
        log.warning("Server IP is empty.")
        return None
    if not mask:
        log.warning("IP Mask is empty.")
        return None
    # Skip over the ".0" - ".1", and ".254-.255" boundaries when dealing with IPs; order is important (low to high).
    d_subnet_skip_front = [0, 1]
    d_subnet_skip_back = [254, 255]
    # Add the reserved space to the boundary skip; always assume front of boundary!
    for i in range(d_subnet_skip_front[-1:][0] + 1, IP_RESERVED_SPACE + d_subnet_skip_front[-1:][0] + 1):
        d_subnet_skip_front.append(i)
    d_subnet_skip = d_subnet_skip_front + d_subnet_skip_back
    log.debug("D Subnets Skipped = {0}".format(d_subnet_skip))
    # Create valid D subnet list
    valid_d_subnet = [i for i in range(0, 255) if i not in d_subnet_skip]
    # Calc boundaries UID will cross.
    boundaries = connection.uid / len(valid_d_subnet)

    # Get the adjusted index
    # NOTE: The server netmask setting is crucial for obtaining an IP address based on the UUT index.
    #       DO NOT change this index calc as it can have potential IP conflicts for other connections!
    #       Please see the 'sudo ethchange' command to adjust the private network netmask which should generally be 255.255.0.0
    index = connection.uid + (len(d_subnet_skip) * boundaries) + len(d_subnet_skip_front)

    # Get IP Addr Object of index
    ip_obj = ipaddress.ip_address(index)
    ip_suffix = str(ip_obj)  # required by ipaddress.py
    log.debug("Connection Index (UID, AUID) = {0}, {1} -> IP suffix = {2}".format(connection.uid, index, ip_suffix))
    network = '.'.join([str(a & b) for a, b in zip([int(octet) for octet in server_ip.split('.')],
                                                   [int(octet) for octet in mask.split('.')])])
    ip_net = ipaddress.ip_network(u'{0}/{1}'.format(network, mask))
    log.debug("Network = {0}/{1}".format(network, mask))
    if index >= ip_net.num_addresses:
        msg = "Cannot assign an IP associated with the connection due to unavailable address space! " \
              "Check server network mask and reserved IP space." \
              "Please run 'sudo ethchange -i <eth1 ip> -m 255.255.0.0' to ensure a subnet with enough addresses."
        log.error(msg)
        raise Exception(msg)
    ip = '.'.join([str(a | b) for a, b in zip([int(octet) for octet in network.split('.')],
                                              [int(octet) for octet in ip_suffix.split('.')])])
    if ip == server_ip:
        msg = "Cannot assign an IP associated with the connection due to server IP conflict. " \
              "Ensure your server is set inside the reserved space."
        log.error(msg)
        raise Exception(msg)

    log.debug("IP = {0}/{1}".format(ip, mask))
    return ip


# ----------------------------------------------------------------------------------------------------------------------
# Python Related
# ----------------------------------------------------------------------------------------------------------------------
def update_dict_recursively(orig_dict, new_dict, list_replace=True, verbose=False):
    """ Update a Nested Dict recursively.
    :param (dict) orig_dict: Original
    :param (dict) new_dict: New
    :param (bool) list_replace: Flag to specify how to process a list as a value in k-v pair.
    :param (bool) verbose: Flag for debug
    :return (dict): orig_dict which has been updated as requested by new_dict
    """
    if verbose:
        log.debug("-" * 50)
        log.debug("new: {}".format(new_dict))
        log.debug("org: {}".format(orig_dict))
        log.debug("list_replace={}".format(list_replace))
    for k, v in new_dict.items():
        orig_v = orig_dict.get(k)
        log.debug("{} = {}".format(k, orig_v)) if verbose else None
        if isinstance(v, collections.Mapping) and isinstance(orig_v, collections.Mapping):
            log.debug("recurse") if verbose else None
            update_dict_recursively(orig_v, v, list_replace)
        elif isinstance(v, list) and isinstance(orig_v, list):
            log.debug("list") if verbose else None
            if list_replace:
                log.debug("replacing") if verbose else None
                # Replace old with new
                i = 0
                for i in range(0, len(v)):
                    # Update the list with the new values
                    if i < len(orig_v):
                        if isinstance(v[i], collections.Mapping) and isinstance(orig_v[i], collections.Mapping):
                            orig_dict[k][i] = update_dict_recursively(orig_v[i], v[i], list_replace)
                        else:
                            orig_dict[k][i] = v[i]
                    else:
                        orig_dict[k].append(v[i])
                for j in range(len(orig_v) - 1, i, -1):
                    # Any remaining values in original NOT updated by new will be removed.
                    # Therefore, lists are replaced, not updated (if list_replace flag is set).
                    orig_dict[k].pop(j)
            else:
                # List elements in the dict are NOT replaced.
                # Combine old + new
                new_list = orig_v + v
                log.debug("combining {0}".format(new_list)) if verbose else None
                try:
                    # Union with no repetition; order is preserved.
                    union_list = list(set(new_list))
                    remainder_jumbled_list = [i for i in union_list if i not in orig_v]
                    remainder_list = [i for i in new_list if i in remainder_jumbled_list]
                    orig_dict[k] = orig_v + remainder_list
                except TypeError:
                    # Non-hashable elements (i.e. elements w/ lists or dicts (and possibly nested)).
                    # It is impossible to know which non-hashable items to recursively update and how to sort.
                    # Make an attempt to combine without repetition.
                    log.debug("non-hashable") if verbose else None

                    # Gather info on characteristic of the proposed new list
                    tuple_test = []
                    for i in new_list:
                        tuple_test += [True] if isinstance(i, tuple) and len(i) == 2 else [False]

                    # Check if 2-element tuple list.
                    if not all(tuple_test):
                        # Not a 2-elem tuple list so check for duplicates at macro level, combine, and hope for the best!
                        nonduplicate_orig_list = [item for item in orig_v if item not in v]
                        orig_dict[k] = nonduplicate_orig_list + v
                    else:
                        # Both original and new lists are complete 2-elem tuples, so assume usage as an OrderedDict.
                        # Cycle thru new items and pop duplicates from orig.
                        for new_item in v:
                            o_keys = [a for a, b in orig_v]
                            o_dup_idx = o_keys.index(new_item[0]) if new_item[0] in o_keys else -1
                            orig_v.pop(o_dup_idx) if o_dup_idx >= 0 else None
                        # Now combine with modified orig_v
                        orig_dict[k] = orig_v + v

        else:
            log.debug("hashable") if verbose else None
            orig_dict[k] = v
    return orig_dict


def diff_dict(dict_a, dict_b, full_return=False):
    """ Difference of Dictionary values & keys
    :param dict_a:
    :param dict_b:
    :return: (tuple) diff dict, dict of key lists
    """
    keys = dict()
    keys['left'] = list(set(dict_a) - set(dict_b))
    keys['right'] = list(set(dict_b) - set(dict_a))
    delta = [k for k in set(dict_a) & set(dict_b) if dict_a[k] != dict_b[k]]
    match = [k for k in set(dict_a) & set(dict_b) if dict_a[k] == dict_b[k]]
    keys['match'] = match
    keys['delta'] = delta
    keys['combo'] = delta + keys['left'] + keys['right']

    dicts = dict()
    diff = dict()
    for k in keys['combo']:
        diff[k] = dict_b[k] if k in dict_b else dict_a[k]

    if full_return:
        dicts['left'] = {k: dict_a[k] for k in keys['left']}
        dicts['right'] = {k: dict_b[k] for k in keys['right']}
        dicts['match'] = {k: dict_a[k] for k in keys['match']}
        dicts['delta'] = {k: (dict_a[k], dict_b[k]) for k in keys['delta']}
        return dicts, keys
    else:
        return diff, keys


def getattr_multi(obj, attr, default=None):
    """
    Get a named attribute from an object; multi_getattr(x, 'a.b.c.d') is
    equivalent to x.a.b.c.d. When a default argument is given, it is
    returned when any attribute in the chain doesn't exist; without
    it, an exception is raised when a missing attribute is encountered.
    Source: http://code.activestate.com/recipes/577346-getattr-with-arbitrary-depth

    Example usage
    obj = [1, 2, 3]
    attr = "append.__doc__.capitalize.__doc__"

    multi_getattr(obj, attr)
    Will return the docstring for the capitalize method of the builtin string object.

    :param obj:
    :param attr:
    :param default:
    :return:
    """
    attributes = attr.split(".")
    for i in attributes:
        try:
            obj = getattr(obj, i)
        except AttributeError:
            if default:
                return default
            else:
                raise
    return obj


def get_ordinal(ord_input, available):
    ord_input = [ord_input] if not isinstance(ord_input, list) else ord_input
    available = [available] if not isinstance(available, list) else available
    ORDINAL_LIST = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth']
    try:
        output_list = [available[i] for i in [ORDINAL_LIST.index(i) for i in ord_input]]
    except (IndexError, ValueError):
        output_list = []

    return output_list


def find_in_nested_lists(target_list, search_item, ret=()):
    for i, item in enumerate(target_list):
        if search_item == item:
            ret = (i,) + ret
            rret = reversed(ret)
            return tuple(rret)
        elif isinstance(item, list):
            ret2 = (i,) +  ret
            ret3 = find_in_nested_lists(item, search_item, ret2)
            if ret3:
                ret = ret3
                break
    else:
        return ()
    return ret


# ----------------------------------------------------------------------------------------------------------------------
# Apollo Related
# ----------------------------------------------------------------------------------------------------------------------
def container_details():
    # List info about this container
    cont_path_items = aplib.get_my_container_key().split('|')
    cont_attrb = aplib.get_container_attributes()
    cont_stat = aplib.get_container_status(cont_path_items[-1:][0])
    log.debug('-' * 50)
    log.info("{0:<20} = {1}".format('Container', aplib.get_my_container_key()))
    log.info("{0:<20} = {1}".format('Container Status', cont_stat))
    log.info("{0:<20} = {1}".format('TestArea', aplib.apdicts.test_info.test_area))
    log.info("{0:<20} = {1}".format('Mode', aplib.get_apollo_mode()))
    log.info("{0:<20} = {1}".format('Container Attribs', 'see dict below'))
    for k, v in cont_attrb.__dict__.items():
        log.info("{0:<20}   {1}: {2}".format(' ', k, v))
    for my_conn_name in aplib.getconnections().keys():
        name = "apollo.libs.lib.conn.{0}.host".format(my_conn_name)
        log.info("{0:<20} = {1}".format(name, getattr(aplib.conn, my_conn_name).host))
    log.debug("Connections count = {0}".format(len(aplib.getconnections().keys())))
    log.debug('-' * 50)
    return


def get_station_key(container_key=None):
    if not container_key:
        container_key = aplib.get_my_container_key()
    station_key = '|'.join(container_key.split('|')[:-1])
    log.debug("Station = {0}".format(station_key))
    return station_key


def get_apollo_config():
    """
    linelength                     : 1000
    config_file_refresh_default    : 1500
    multi_version                  : FALSE
    web_socket_timeout             : 180
    apollo_log_level               : DEBUG
    tescripts                      : ../te/scripts
    websvc_request_timeout         : 150
    cassandra_log_level            : INFO
    multi_folder                   : ../multi
    telibs                         : ../te/libs
    max_size_per_file_in_megs      : 50
    max_number_of_files_to_keep    : 10
    ui_log_level                   : DEBUG
    registry_file                  : ./apollo/config/apollo_registry.json
    default_appreg_url             : https://csmstgapp1/apollo/cesiumsvcs/appreg/apollo_config_provisioning/request
    tewebsvcs                      : ../te/websvcs
    support_folder                 : ../support
    logs_folder                    : ./apollo/logs
    cert_location                  : ./apollo/certs/machinecert.pem
    cli_websocket_connection_timeout : 4000
    :return:
    """
    apcfg = aplib.get_apollo_config()
    k_max = max([len(i) for i in apcfg.keys()])
    for k, v in apcfg.items():
        log.debug("{0:<{2}} : {1}".format(k, v, k_max))
    return True


def get_connection(connection_name):
    """Gets the Apollo Connection Object given the connection name.

    Useful when lib.conn.connection_name is not practical

    :param str connection_name: connection named defined in config file
    :rtype Apollo Connection:
    :return Apollo Connection Object
    :raises: KeyError if not found
    """
    return aplib.getconnections()[connection_name]


def get_conn_name(conn):
    """ Get Connection name
    Be careful using this as Apollo releases could change the dict index names.
    :param conn:
    :return:
    """
    if conn.__dict__['alias']:
        name = conn.__dict__['alias']
    else:
        name = conn.__dict__['name']
    # log.debug("Conn name = {0}".format(name))
    return name.split('|')[-1:][0]


def get_chamber_conn():
    """ Get Chamber
    Obtain connection object name and chamber model based on 'Chamber' as part of the connection name.
    The model is used for detecting 'simulator' for unittesting to skip some temperature checking.
    :return (obj, str): conn_name, model
    """
    for conn_name in aplib.getconnections().keys():
        if 'Chamber' in conn_name:
            model = getattr(aplib.conn, conn_name).model
            break
    else:
        model = None
        conn_name = None
    return conn_name, model


def get_testarea():
    """
    This is replaced by the TestInfo() class property.
    c_path = aplib.get_my_container_key().split('|')
    for item in c_path:
        if item in aplib.TST_AREAS:
            return item
    else:
        return None

    class TestInfo(object):
        Class has the following properties:
        class that returns the data that was given in the pre-sequence so the sequence gets easy access to it
        @property
        def step_name(self):
        @property
        def sequence_name(self):
        @property
        def test_area(self):
        @property
        def machine_name(self):
        @property
        def current_iteration(self):
        @property
        def iteration_type(self):
        @property
        def iteration_max_value(self):
        @property
        def serial_number(self):
        @property
        def serial_numbers(self):
        def childs(self, serial_number=''):
        @property
        def test_container(self):
        @property
        def test_data(self, field_name, serial_number=''):
        @property
        def test_data_keys(self, serial_number=''):
        @property
        def user_name(self):
        @property
        def ui_type(self):
        @property
        def current_status(self):
    """
    return aplib.apdicts.test_info.test_area


def read_sn_data(sernum, **kwargs):
    """ Read the TST and MAC records from the CSA based on serial number.

    NOTE: This function is derived from tst_lookup.py.

        Request:
        {
            "root": {
                ("serial_number": SN | "mac_address": MAC | "child_serial_number": SN | "parent_serial_number": SN)
                                                                                                            ---required,
                ("db_table_name": [mac|tst]) ---optional,
                "test_area": [AREA1,  AREA2] ---optional, valid only with sernum & tst
            }
        }

        Response:
        {
            "root": {
                "code": 0/1/2/10xxx,
                "message": message corresponding to the code
                "body": [{
                    "code": 0/1/2/10xxx,
                    "message": message corresponding to the code
                    "serial_number": SN OR "mac_address": MAC,
                    "db_table_name": "tst" OR "mac",
                    "records_found": N,
                    "result": [list of records]
                },
                {
                    "code": 0/1/2/10xxx,
                    "message": message corresponding to the code
                    "serial_number": SN OR "mac_address": MAC,
                    "db_table_name": "tst" OR "mac",
                    "records_found": N,
                    "result": [list of records]
                }]
            }
        }

        SAMPLE OUTPUT of the LIST OF STRUCTURED DICTS
            DEBUG   :    = {
            DEBUG   :      'code'          = '',
            DEBUG   :      'records_found' = '157',
            DEBUG   :      'result'        = [
            DEBUG   :                      = {
            DEBUG   :                        'username'         = 'bborel',
            DEBUG   :                        'uut_type'         = '73-16622-03',
            DEBUG   :                        'machine_name'     = 'ausapp-citp01',
            DEBUG   :                        'test_record_time' = '2017-05-02 21:32:14',
            DEBUG   :                        'basepid'          = 'WS-C3850-48XS',
            DEBUG   :                        'partnum2'         = '73-16622-03',
            DEBUG   :                        'labelnum'         = 'A22345678',
            DEBUG   :                        'hwrev2'           = 'A0',
            DEBUG   :                        'hwrev3'           = '03',
            DEBUG   :                        'test_area'        = 'PCBST',
            DEBUG   :                        'test_container'   = 'UUT02',
            DEBUG   :                        'test_mode'        = 'PROD0',
            DEBUG   :                        'result_pass_fail' = 'S',
            DEBUG   :                        'serial_number'    = 'FOC19160UJJ',
            DEBUG   :                        'tan'              = '68-5295-01',
            DEBUG   :                        'test_id'          = '2017-05-02 21:32:14',
            DEBUG   :                        'runtime'          = '',
            DEBUG   :                        'hwrev'            = 'V01',
            DEBUG   :                        'diagrev'          = 'stardustThrG.2016Jan14'
            DEBUG   :                        },
                            ...
            DEBUG   :                      = {
            DEBUG   :                        'username'         = 'bborel',
            DEBUG   :                        'uut_type'         = '73-16622-03',
            DEBUG   :                        'machine_name'     = 'ausapp-citp01',
            DEBUG   :                        'test_record_time' = '2017-02-14 18:44:08',
            DEBUG   :                        'labelnum'         = 'A22345678',
            DEBUG   :                        'test_area'        = 'PCBST',
            DEBUG   :                        'test_container'   = 'UUT02',
            DEBUG   :                        'test_mode'        = 'PROD0',
            DEBUG   :                        'result_pass_fail' = 'S',
            DEBUG   :                        'serial_number'    = 'FOC19160UJJ',
            DEBUG   :                        'test_id'          = '2017-02-14 18:44:08'
            DEBUG   :                        }
            DEBUG   :                        ],
            DEBUG   :      'db_table_name' = 'tst',
            DEBUG   :      'serial_number' = 'FOC19160UJJ',
            DEBUG   :      'message'       = 'SUCCESS'
            DEBUG   :      },

            DEBUG   :    = {
            DEBUG   :      'code'          = '',
            DEBUG   :      'records_found' = '2',
            DEBUG   :      'result'        = [
            DEBUG   :                      = {
            DEBUG   :                        'uut_type'        = '73-16622-03',
            DEBUG   :                        'machine_name'    = 'ausapp-citp01',
            DEBUG   :                        'mac_block_size'  = '128',
            DEBUG   :                        'mac_group'       = 'T',
            DEBUG   :                        'mac_record_time' = '2017-04-28 16:39:41',
            DEBUG   :                        'mac_address'     = '0xbadbadc54500',
            DEBUG   :                        'serial_number'   = 'FOC19160UJJ'
            DEBUG   :                        },
            DEBUG   :                      = {
            DEBUG   :                        'uut_type'        = '73-16622-03',
            DEBUG   :                        'machine_name'    = 'ausapp-citp01',
            DEBUG   :                        'mac_block_size'  = '128',
            DEBUG   :                        'mac_group'       = 'T',
            DEBUG   :                        'mac_record_time' = '2017-02-14 18:45:29',
            DEBUG   :                        'mac_address'     = '0xbadbadc54100',
            DEBUG   :                        'serial_number'   = 'FOC19160UJJ'
            DEBUG   :                        }
            DEBUG   :                        ],
            DEBUG   :      'db_table_name' = 'mac',
            DEBUG   :      'serial_number' = 'FOC19160UJJ',
            DEBUG   :      'message'       = 'SUCCESS'
            DEBUG   :      }

    :param (str) sernum: serial number requesting mac address
    :param (**dict) kwargs: Filtering items available:
                    Built-ins
                    (list) db_table_name: ['tst', 'mac'] or a subset
                    (str) test_area:
                    Supplemental
                    (str) start_datetime: Form of 'YYYY-MM-DD HH:MM:SS' or 'LATEST'
                    (str) end_datetime:
                    (str) result_pass_fail: 'S', 'P', 'F'
                    (bool) latest: Returns a single result record.
                    (bool) unfiltered: Returns ALL table data (BE CAREFUL!)

    :return (list) filtered_data_dict: All test records of the serial number that met the filter criteria.
    """
    BODY = 'body'
    MESSAGE = 'message'
    OUTPUT_DICT = 'outputdict'
    PULLED_DATA = 'PULLED_DATA'
    ROOT = 'root'
    SNPULL_FUNCTION = 'request'
    SNPULL_MODULE = 'apollo.cesiumsvcs.db_transfer.snpull'
    DATETIME_MAP = {'tst': 'test_record_time', 'mac': 'mac_record_time'}

    # Inputs
    db_table_name = kwargs.get('db_table_name', ['tst', 'mac'])
    db_table_name = [db_table_name] if db_table_name and not isinstance(db_table_name, list) else db_table_name
    test_area = kwargs.get('test_area', None)

    result_pass_fail = kwargs.get('result_pass_fail', None)
    test_mode = kwargs.get('test_mode', None)
    test_mode = [test_mode] if test_mode and not isinstance(test_mode, list) else test_mode
    start_datetime = kwargs.get('start_datetime', None)
    end_datetime = kwargs.get('end_datetime', None)
    latest = kwargs.get('latest', True if start_datetime == 'LATEST' else False)
    unfiltered = kwargs.get('unfiltered', False)
    start_datetime = None if start_datetime == 'LATEST' else start_datetime

    _, _, inputdict, _, userd = aplib.getstepdicts()

    log.debug('Pulling SN Data...')
    data_record = dict(serial_number=sernum)
    if len(db_table_name) == 1:
        data_record['db_table_name'] = db_table_name[0]
    if db_table_name[0] == 'tst' and test_area:
        data_record['test_area'] = test_area
    db_data_dict = dict(root=data_record)
    inputdict = dict(body=db_data_dict)
    log.info("Request = {0}".format(inputdict))
    status, return_dict = aputils.do_internal_service(module=SNPULL_MODULE,
                                                      function=SNPULL_FUNCTION,
                                                      inputdict=inputdict,
                                                      userdict=dict(),
                                                      outputdict=dict(),
                                                      )

    result = return_dict.get(OUTPUT_DICT, {}).get(BODY, {}).get(ROOT, {}).get(MESSAGE, 'UNKNOWN')
    records_found = [i.get('records_found', 0) for i in return_dict.get(OUTPUT_DICT, {}).get(BODY, {}).get(ROOT, {}).get(BODY, {})]
    log.info("Service Status         : {0}".format(status))
    log.info("Pull Result            : {0}".format(result))
    log.info("TST Records Found      : {0}".format(records_found[0] if len(records_found) > 0 else 0))
    log.info("MAC Records Found      : {0}".format(records_found[1] if len(records_found) > 1 else 0))
    # print_large_dict(return_dict)

    if status == aplib.PASS and 'SUCCESS' in result:
        userd[PULLED_DATA] = return_dict.get(OUTPUT_DICT, {}).get(BODY, {}).get(ROOT, {}).get(BODY, [''])
    else:
        log.warning('SN Data cannot be pulled from {0} databases: {1}'.format(db_table_name, result))
        userd[PULLED_DATA] = []
        return userd[PULLED_DATA]
    if unfiltered:
        return userd[PULLED_DATA]

    filtered_data_dicts = []
    # List of dicts (1 or 2: tst & mac)
    for data_dict in userd[PULLED_DATA]:
        if 'db_table_name' in data_dict and data_dict['db_table_name'] in db_table_name and 'result' in data_dict:
            log.debug("Processing {0} records...".format(data_dict['db_table_name']))
            dt_key = DATETIME_MAP.get(data_dict['db_table_name'], 'record_time')
            tst_results = data_dict.get('result', [''])

            # Clear the result list of records and then repopulate based on filters.
            data_dict.pop('result')
            filtered_tst_results = []

            # Process all records against filters.
            # List of dicts; each dict is an individual record.
            # The list is already presorted by rec time; latest is index 0.
            for tst_dict in tst_results:

                # 1. Datetime Filter
                if (start_datetime or end_datetime) and dt_key in tst_dict:
                    if (start_datetime and tst_dict[dt_key] >= start_datetime) and (end_datetime and tst_dict[dt_key] <= end_datetime):
                        get_it = True
                    elif start_datetime and tst_dict[dt_key] >= start_datetime:
                        get_it = True
                    elif end_datetime and tst_dict[dt_key] <= end_datetime:
                        get_it = True
                    else:
                        # Datetime stamp did not meet the criteria
                        get_it = False
                else:
                    # No datetime stamp filtering
                    get_it = True

                # 2. result_pass_fail Filter
                if get_it and result_pass_fail and 'result_pass_fail' in tst_dict:
                    get_it = True if tst_dict['result_pass_fail'] in result_pass_fail else False

                # 3. test_mode Filter
                if get_it and test_mode and 'test_mode' in tst_dict:
                    get_it = True if tst_dict['test_mode'] in test_mode else False

                # Save the record if it met the filter criteria
                if get_it:
                    filtered_tst_results.append(tst_dict)

            # Choose the first record in the filtered list if latest was specified and then reassign.
            if latest:
                one = [filtered_tst_results[0]]
                filtered_tst_results = one

            data_dict['result'] = filtered_tst_results
            data_dict['filtered_records_found'] = len(filtered_tst_results)
            filtered_data_dicts.append(data_dict)

    log.info("Filtered Records Found : {0}".format(len(filtered_data_dicts) if filtered_data_dicts else 0))
    log.info("SN Pull done.")
    return filtered_data_dicts


def get_mac(serial_number):
    """ Get MAC
    Pull the MAC Addr from the POD Label

    Example of format, tags and output:
    label_format = '<label_name>,<printer_name>,<date>,<serial_number>,<clei>,<coo>,<eci>,' \
                   '<tan>,<mac_address>,<mac_block_size>,<mac_address_offset>,' \
                   '<header1>,<hwrev>,<header2>,<data2>,<header3>,<data3>,' \
                   '<header4>,<data4>,<header5>,<data5>,<header6>,<data6>'

    label_tags = dict(label_name='Get-MAC',
                      printer_name='Phantom',
                      date=datetimestr('ymd2'),
                      serial_number=serial_number,
                      areas=['PCBST'],
                      clei='',
                      coo='',
                      eci='',
                      tan='',
                      hwrev='',
                      header1='', data1='',
                      header2='', data2='',
                      header3='', data3='',
                      header4='', data4='',
                      header5='', data5='',
                      header6='', data6='' )

    DEBUG   : POD File = '/tmp/pod_labels/FOC18498NCD_26012017142503.pj'
    DEBUG   : POD File content =
    Get-MAC,Phantom,172426,FOC18498NCD,,,,,76:88:28:00:07:80,128,,,,,,,,,,,,,

    :param (str) serial_number:
    :return (tuple):  (mac, block_size) or (None, 0)
    """
    mac = None
    block_size = 0

    if not validate_sernum(serial_number):
        log.error("Need a valid Serial Number.")
        return mac

    label_tags = dict(label_name='Get-MAC',
                      printer_name='Phantom',
                      date=datetimestr('ymd2'),
                      serial_number=serial_number)

    label_format = '<mac_address>,<mac_block_size>'

    log.debug("label_format = '{0}'".format(label_format))
    log.debug("label_tags = '{0}'".format(label_tags))
    log.debug("Mode = {0}".format(aplib.get_apollo_mode()))

    # TODO: awaiting #5580
    pod_file = cesiumlib.print_label(destination_directory='/tmp', label_format=label_format, **label_tags)

    log.debug("POD File = '{0}'".format(pod_file))
    if pod_file:
        data = readfiledata(pod_file)
        os.remove('{0}'.format(pod_file))
        mac, block_size = data[0].split(',', 1)
        log.info('MAC_ADDR = {0}'.format(mac))
        log.info('MAC_BLOCK_SIZE = {0}'.format(block_size))

    return mac, block_size


def get_area_tst_data(sn_data, test_area=None):
    """
    This function will return last PASS tst data of SN from given area. If area is not set, it will return the most
    recent pass record
    :param sn_data: (list) tst data returned by read_sn_data() function
    :param test_area: (string) test_area
    :return: (dict) tst data for given area. None in case no data found or unit did not pass the area
    """
    tst_data_dict_list = sn_data['result']
    if test_area:
        tst_data_dict_list = filter(lambda x: x['test_area'] == test_area, tst_data_dict_list)
    tst_data_dict_list = filter(lambda x: x['result_pass_fail'] == 'P', tst_data_dict_list)
    tst_data_dict_list = sorted(tst_data_dict_list,
                                key=operator.itemgetter('test_record_time'),
                                reverse=True
                                )
    return tst_data_dict_list[0] if len(tst_data_dict_list) > 0 else None


def get_uut_suffix_index():
    """ Get UUT Suffix Index
    Given a container name like "UUT001", get the integer suffix which is an index.
    :return (int): index
    """
    cname = aplib.get_my_container_key()
    if not cname:
        return 0
    s = ''
    i = len(cname) - 1
    while cname[i].isdigit() and i >= 0:
        s = ''.join((cname[i], s))
        i -= 1
    if s:
        index = int(s)
    else:
        index = 0
    return index


def get_parent_sernum(child_sernum, child_pid):
    """ Get Parent S/N
    :param child_sernum:
    :param child_pid:
    :return:
    """
    sernum = None
    log.debug("Checking genealogy...")
    log.debug("Child S/N: {0}".format(child_sernum))
    log.debug("Child PID: {0}".format(child_pid))
    try:
        g = cesiumlib.get_genealogy(child_sernum, child_pid)
        # Example output
        # {u'code': 0,
        # u'product_id': u'73-14445-06',
        # u'area': u'ASSY',
        # u'level': 0,
        # u'site_id': 360,
        # u'parent_product_id': u'WS-C3850-24S',
        # u'machine': u'ausapp-citp01',
        # u'sort_order': u'0001',
        # u'serial_number': u'FOC18498NCD',
        # u'parent_serial_number': u'FOC1851X13Y',
        # u'message': u'SUCCESS'}
        if g['message'] != 'SUCCESS':
            log.error("Genealogy retrieved but no success was indicated.")
            log.error("genealogy = {0}".format(g))
            raise apexceptions.ServiceFailure("No success on genealogy.")
        log.debug("Genealogy retrieved.")
        sernum = g['parent_serial_number']
    except apexceptions.ServiceFailure as e:
        log.debug("Genealogy service failure.")
        log.debug(e)
    return sernum


def generate_cisco_sernum(**kwargs):
    """ Generate Cisco Serial Number
    If the server is NOT a PRODUCTION server, then the S/N generation will be prompted to the operator:
        1. Auto will give a TST#
        2. Manual will allow scanning.
    WARNING: Therefore, take care in assigning serial numbers in apollodev & apollostage to products that will go
    into production.

    Example of machine_cfg = {
        macAddress          : 00C88B42AF3a
        machineType         : Physical
        cn                  : sj18-apollo1
        downloadPath        : '/tftpboot'
        ipaddress_CIMC      : 172.28.106.74
        reportsTo           : csmstgapp4,csmstgapp3
        appRegProvURL       : https://csmstgapp4/apollo/cesiumsvcs/appreg/apollo_config_provisioning/request
        ipaddr_string       : 172.28.106.75
        username            : gchew
        siteid              : 360
        requestid           : b46c1c6c-65a5-4690-b448-170b4416eab5
        machineFamily       : apollostg
        macaddr_CIMC        : 00:C8:8B:42:AF:37
        macAddress1         : None
        siteCode            : cisco
        description         : Apollo server1 in SJ18
        }
    :param kwargs:
    :return: sernum
    """
    sernum = None
    sernum_item = kwargs.get('sernum_item', 'SERIAL_NUM')
    product_family = kwargs.get('product_family', 'Cisco')
    product_generation = kwargs.get('product_generation', '')
    uut_category = kwargs.get('uut_category', 'UUT')
    ask = kwargs.get('ask', True)
    try:
        machine_cfg = get_machine_config()
        sitecode = machine_cfg.get('siteCode', 'cisco')
        machine_fam = machine_cfg.get('machineFamily', 'apollostg')
        hostname = aplib.get_hostname()
        location_prefix = kwargs.get('location_prefix', hostname[0:3].upper())
        log.debug("Location Prefix: {0}".format(location_prefix))
        log.debug("Site Code      : {0}".format(sitecode))
        log.debug("Machine Family : {0}".format(machine_fam))
        if machine_fam != 'apolloprod':
            # Non-Production server
            ans = aplib.ask_question("NON-PRODUCTION Server\nSelect Action for {0}:".format(sernum_item),
                                     answers=['Manual Scan/Enter', 'Auto-generate']) if ask else 'Auto-generate'

            if ans == 'Auto-generate':
                location_prefix = 'TST'
                log.info('Apollo NON-PRODUCTION server; S/N uses {0} prefix for auto-generate.'.format(location_prefix))
                try:
                    sernum = cesiumlib.generate_serial_number(location_prefix)
                except Exception:
                    log.warning("Cannot generate S/N via Cesium service.")
                    log.warning("Substitute with offline for non-production.")
                    sernum = generate_offline_cisco_sernum()
            else:
                log.info('Apollo NON-PRODUCTION server; S/N is manually scanned.')
                prod = "{0} {1}".format(product_family, product_generation)
                sd = get_data_from_operator(uut_category, prod, sernum_item, rev_map=None)
                sernum = sd[sernum_item]
        else:
            # Production Server (Auto-generate)
            log.info("Apollo PRODUCTION server; S/N is auto-generated.")
            log.info("Location S/N Prefix = {0}".format(location_prefix))
            sernum = cesiumlib.generate_serial_number(location_prefix)

    except apexceptions.ServiceFailure as e:
        log.error("Problem with cesium service or sernum generation routine.")
        log.error(e.message)

    return sernum


def get_cisco_sernum_prefixes(silent=False):
    machine_cfg = get_machine_config()
    site_code = machine_cfg.get('siteCode', 'cisco')
    log.debug("Cisco sernum prefix uses siteCode='{0}'".format(site_code)) if not silent else None
    return CISCO_SERNUM_PREFIXES.get(site_code, [])


def generate_offline_cisco_sernum():
    log.warning("GENERATING SERIAL NUMBER OFFLINE!")
    timestamp = num2base(int(datetimestr('%H%M%S')), 34)
    timestamp = '0' * (4 - len(timestamp)) + timestamp if len(timestamp) < 4 else timestamp
    sid = '{0:04d}'.format(int(aplib.conn.uutTN.uid) if hasattr(aplib.conn, 'uutTN') else random.randrange(0, 9999))
    sn = 'TST{0}{1}'.format(sid, timestamp)
    if not validate_sernum(sn):
        log.error("Offline generation NOT valid ({0}); cannot continue.  Restart and try again.".format(sn))
        sn = None
    return sn


def get_machine_config():
    machine_cfg = aplib.get_machine_config()
    if not machine_cfg:
        log.debug("Using Apollo registry for machine config...")
        machine_cfg = read_apollo_registry().get('Machine', {})
    return machine_cfg


def get_cmpd_testsite():
    """ Get CMPD Test Site
    Return the "Test Site" typically used in the CMPD database.
    This is based on a "mapping" of the Apollo server sitecode.
    :return:
    """
    CMPD_TEST_SITES = {
        'cisco': 'ALL',
        'celtha': 'CTH',
        'foxch': 'FOC',
        'fxh2': 'FTX',
        'fjz': 'FJZ',
        'fcz': 'FCZ',
        'fdo': 'FDO',
        'solpen': 'PEN',
        'fgn': 'FGN',
        'jabpen': 'JPE',
        'jmx2': 'JMX',
    }
    machine_cfg = get_machine_config()
    site_code = machine_cfg.get('siteCode', 'cisco')
    return CMPD_TEST_SITES.get(site_code, 'ALL')


def read_apollo_registry():
    with open('/opt/cisco/constellation/apollo/config/apollo_registry.json') as apollo_reg_file:
        apollo_reg_data = json.load(apollo_reg_file)
    return apollo_reg_data

# ----------------------------------------------------------------------------------------------------------------------
# UUT Related
# ----------------------------------------------------------------------------------------------------------------------
def uut_comment(uut_conn, keyword, comment, uut_comment_char='#'):
    """ UUT Comments
    ----------------
    Function to print comments in the UUT cli under a specific format (i.e. any info sent will be ignored by the UUT).
    NOTE: The UUT CLI must support this type of "commenting".
    :param uut_conn:
    :param keyword:  Keyword describing the comment. For use in dict parsing of log files.
    :param comment:  String comment to display in UUT console.
    :param uut_comment_char: Character used by the UUT to indicate a comment and NOT a cli command to process.
    :return:
    """
    if isinstance(comment, str):
        uut_conn.send("{0} {{'{1}': '{2}'}}\r".format(uut_comment_char, keyword, comment), expectphrase=None)
    elif isinstance(comment, list):
        uut_conn.send("{0} {{'{1}': [\r".format(uut_comment_char, keyword), expectphrase=None)
        for line in comment:
            uut_conn.send("{0} '{1}',\r".format(uut_comment_char, line), expectphrase=None)
        uut_conn.send("{0} ]}}\r".format(uut_comment_char), expectphrase=None)
    elif isinstance(comment, dict):
        uut_conn.send("{0} {{'{1}': {{\r".format(uut_comment_char, keyword), expectphrase=None)
        for key in comment.keys():
            uut_conn.send("{0} '{1}': {2},\r".format(uut_comment_char, key, comment[key]), expectphrase=None)
        uut_conn.send("{0} }}}}\r".format(uut_comment_char), expectphrase=None)
    else:
        # Last effort
        uut_conn.send("{0} {{'{1}': '{2}'}}\r".format(uut_comment_char, keyword, str(comment)), expectphrase=None)

    return True
