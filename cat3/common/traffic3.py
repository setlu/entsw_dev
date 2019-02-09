"""
Traffic Ctalyst Series 3
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
from apollo.scripts.entsw.libs.traffic.traffic_diags import TrafficDiags as _TrafficDiags
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Traffic Catalyst Series 3 Module"
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


class _TrafficDiags3(_TrafficDiags):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(_TrafficDiags3, self).__init__(mode_mgr, ud, **kwargs)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class TrafficDiagsC3000(_TrafficDiags3):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficDiagsC3000, self).__init__(mode_mgr, ud, **kwargs)
        return


class TrafficDiagsC9300(_TrafficDiags3):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficDiagsC9300, self).__init__(mode_mgr, ud, **kwargs)
        return
