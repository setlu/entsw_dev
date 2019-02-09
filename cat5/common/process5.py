"""
Process5
"""

# Python
# ------
import sys
import logging


# Apollo
# ------
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.mfg.process import Process as _Process
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Process Series5 Module"
__version__ = '1.0.0'
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
func_details = common_utils.func_details
func_retry = common_utils.func_retry


class Process5(_Process):
    def __init__(self, mode_mgr, ud):
        super(Process5, self).__init__(mode_mgr, ud)