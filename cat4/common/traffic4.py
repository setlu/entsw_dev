"""
Traffic Ctalyst Series 4
"""

# Python
# ------
import sys
import logging

# Apollo
# ------
# from apollo.engine import apexceptions
# from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.traffic.traffic_diags import TrafficDiags as _TrafficDiags
from apollo.scripts.entsw.libs.traffic.traffic_snt import TrafficSNT as _TrafficSNT
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Traffic Catalyst Series 4 Module"
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

# ======================================================================================================================
# Traffic w/ Diags
# ======================================================================================================================
class _TrafficDiags4(_TrafficDiags):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(_TrafficDiags4, self).__init__(mode_mgr, ud, **kwargs)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class TrafficDiagsC4000(_TrafficDiags4):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficDiagsC4000, self).__init__(mode_mgr, ud, **kwargs)
        return


class TrafficDiagsC9400(_TrafficDiags4):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficDiagsC9400, self).__init__(mode_mgr, ud, **kwargs)
        return


# ======================================================================================================================
# Traffic w/ SNT Generator
# ======================================================================================================================
class _TrafficSNT4(_TrafficSNT):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(_TrafficSNT4, self).__init__(mode_mgr, ud, **kwargs)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class TrafficSNTC4000(_TrafficSNT4):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficSNTC4000, self).__init__(mode_mgr, ud, **kwargs)
        return


class TrafficSNTC9400(_TrafficSNT4):
    def __init__(self, mode_mgr, ud, **kwargs):
        super(TrafficSNTC9400, self).__init__(mode_mgr, ud, **kwargs)
        return
