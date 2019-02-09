"""
Traffic w/ SNT Generator
"""

# Python
# ------
import sys
import re
import logging
import time
import parse
import os
from collections import namedtuple
from collections import OrderedDict

# Apollo
# ------
from apollo.engine import apexceptions
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils import common_utils


__title__ = "Traffic w/ SNT Generator Generic Module"
__version__ = '2.0.0'
__author__ = ['tnguyen', 'bborel']

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
apollo_step = common_utils.apollo_step


class TrafficSNT(object):
    def __init__(self, mode_mgr, ud, **kwargs):
        # Inputs
        log.debug(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._ios = kwargs.get('ios', None)
        self.equip = kwargs.get('equip', None)

        # Derived
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt = self._mode_mgr.uut_prompt_map['IOSE']

        return

    @property
    def equip(self):
        return self.__equip

    @equip.setter
    def equip(self, newvalue):
        self.__equip = newvalue
        self.__generator = self.__equip.traf_generator if hasattr(self.__equip, 'traf_generator') else None

    @property
    def generator(self):
        return self.__generator

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
