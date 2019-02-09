"""
C4500

[Catalyst]---->[Catalyst5]---->[C4500]
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

# BU Libs
# ------
from apollo.scripts.entsw.libs.cat.uut_descriptor import UutDescriptor as _UutDescriptor
from apollo.scripts.entsw.libs.mode.modemanager import ModeManager as _ModeManager
from apollo.scripts.entsw.libs.mfg.process import Process as _Process
from apollo.scripts.entsw.libs.product_drivers.power import Power as _Power
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonC4000 as _RommonC4000
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapC4000 as _PcamapC4000
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC4K as _PeripheralC4K
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.traffic.traffic import Traffic as _Traffic
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.idpro.quack2 import Quack2 as _Quack2


# Product Specific
# ----------------
from ..common.catalyst4 import Catalyst4000 as _Catalyst4000
from ..common.stardust4 import StardustC4000 as _StardustC4000
from ..common.traffic4 import TrafficDiagsC4000 as _TrafficDiagsC4000
from ..common import modes4 as _modes4
from ..common import _common_def
from ..common import _ios_manifest4
from .product_definitions import _product_line_def

__title__ = "C4500 Product Module"
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


class _C4500(_Catalyst4000):
    def __init__(self, family_filter):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, ios_manifest=_ios_manifest4,
                                uut_conn=self.uut_conn, family_filter=family_filter)
        self.mode_mgr = _ModeManager(mode_module=_modes4, statemachine=self.ud.uut_state_machine,
                                    uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.process = _Process(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonC4000(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[], poe_loadbox=None, traf_generator=None)
        self.diags = _StardustC4000(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip, power=self.power)
        self.peripheral = _PeripheralC4K(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapC4000(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self.quack2 = _Quack2(mode_mgr=self.mode_mgr, ud=self.ud)
        self.traffic = _Traffic(fmdiags=_TrafficDiagsC4000(mode_mgr=self.mode_mgr, ud=self.ud, diags=self.diags),
                                fmgenerator=None)
        self._callback_()
        return


class K10(_C4500):
    def __init__(self):
        self.show_version()
        super(K10, self).__init__(family_filter='k10')
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class K5(_C4500):
    def __init__(self):
        self.show_version()
        super(K5, self).__init__(family_filter='k5')
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
