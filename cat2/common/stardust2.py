"""
Stardust2
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
from apollo.scripts.entsw.libs.diags.stardust import Stardust as _Stardust
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Stardust Series2 Module"
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
func_details = common_utils.func_details
func_retry = common_utils.func_retry


class StardustC2000(_Stardust):
    def __init__(self, **kwargs):
        super(StardustC2000, self).__init__(**kwargs)
        return


class StardustC9200(_Stardust):
    def __init__(self, **kwargs):
        super(StardustC9200, self).__init__(**kwargs)
        return
