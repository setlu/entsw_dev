"""
---------------------------------------------------------------------
Transistion Functions for apollo.scripts.entsw.libs.mode.tests.dummy_mode
---------------------------------------------------------------------
"""
# Python Imports
# --------------
import logging

# Apollo  Imports
# ---------------
# from apollo.libs import lib
# from apollo.engine import apexceptions
# from apollo.engine import utils

# Cisco Library Imports
# ---------------------
# import here

# BU Specific Imports
# -------------------
import libs.mode.modemanager as modemanager
# from <your>_utils import *

log = logging.getLogger(__name__)


# UUT transistion function arguments.
#  key = transisition function name,
#  value = dict of args.
trans_func_args = {
}


def create_mode_manager(uut_state_machine, uut_prompt_map, uut_conn):
    """
    Create the state machine for the given UUT modes, connection, prompts, and this module.
    :param uut_state_machine: Dict of state machine for UUT modes.
    :param uut_prompt_map: Dict of regex prompts per mode.
    :param uut_conn: UUT connection object.
    :return: UUT Machine Manager object.
    """
    mmd = {
        'mode_module': 'apollo.scripts.entsw.libs.tests.dummy_mode',
        'uut_conn': uut_conn,
        'current_mode': '',
        'verbose': True,
        'statemahine': uut_state_machine,
        'uut_prompt_map': uut_prompt_map,
        'trans_func_args': trans_func_args,
    }
    mm = modemanager.ModeManager(**mmd)
    return mm


# Product specific transisiton functions given below.
# DO NOT call these directly; use the ProductMode class instance and the goto_mode() method.
# ------------------------------------------------------------------------------------------
def btldr_to_ios(**kwargs):
    """
    Product specific transition from BTLDR to IOS
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def btldr_to_linux(**kwargs):
    """
    Product specific transition from BTLDR to LINUX
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def diag_to_stardust(**kwargs):
    """
    Product specific transition from DIAG to STARDUST
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def diag_to_symsh(**kwargs):
    """
    Product specific transition from DIAG to SYMSH
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def ios_to_btldr(**kwargs):
    """
    Product specific transition from IOS to BTLDR
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def ios_to_iose(**kwargs):
    """
    Product specific transition from IOS to IOSE
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def iose_to_ios(**kwargs):
    """
    Product specific transition from IOSE to IOS
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def linux_to_btldr(**kwargs):
    """
    Product specific transition from LINUX to BTLDR
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def linux_to_stardust(**kwargs):
    """
    Product specific transition from LINUX to STARDUST
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def stardust_to_diag(**kwargs):
    """
    Product specific transition from STARDUST to DIAG
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def stardust_to_linux(**kwargs):
    """
    Product specific transition from STARDUST to LINUX
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def stardust_to_symsh(**kwargs):
    """
    Product specific transition from STARDUST to SYMSH
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def stardust_to_traf(**kwargs):
    """
    Product specific transition from STARDUST to TRAF
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def symsh_to_diag(**kwargs):
    """
    Product specific transition from SYMSH to DIAG
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def symsh_to_stardust(**kwargs):
    """
    Product specific transition from SYMSH to STARDUST
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def symsh_to_traf(**kwargs):
    """
    Product specific transition from SYMSH to TRAF
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def traf_to_stardust(**kwargs):
    """
    Product specific transition from TRAF to STARDUST
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret


def traf_to_symsh(**kwargs):
    """
    Product specific transition from TRAF to SYMSH
    :param kwargs: optional.
    """
    # Place product specific code here.
    ret = True
    return ret
