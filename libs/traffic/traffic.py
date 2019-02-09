"""
Traffic
"""

# Python
# ------
import sys
import re
import logging
import time
import parse
import os

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Traffic Module"
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

class Traffic(object):
    """ Traffic
    Use this class as a parent class to ALL TrafficXXX classes for product testing.
    The purpose of this class is to provide a nested layer for all traffic classes to keep better organization and
    to provide a single point of access.
    For example:
      1. Traffic Stardust
      2. Traffic Agilent generator
    Usage Example:
    From your product class __init__() inititalize in the form of
    self.traffic = Traffic(diags=TrafficDiagsXXX(...), snt=TrafficSNTxxx())
    """
    def __init__(self, **kwargs):
        log.info(self.__repr__())
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)
                log.debug("  {0} = {1}".format(k, v))
            else:
                log.warning("The traffic attribute {0} is null.".format(k))
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
