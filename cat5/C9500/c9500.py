"""
C9500

[Catalyst]---->[Catalyst5]---->[C9500]
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
from apollo.scripts.entsw.libs.product_drivers.power import Power as _Power
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonC9500 as _RommonC9500
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapC9500 as _PcamapC9500
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC5K as _PeripheralC5K
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.traffic.traffic import Traffic as _Traffic
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.idpro.act2 import ACT2 as _ACT2
from apollo.scripts.entsw.libs.idpro.x509 import X509Sudi as _X509Sudi
import apollo.scripts.entsw.libs.equip_drivers.poe_loadbox as poe_loadbox
import apollo.scripts.entsw.libs.equip_drivers.traf_generator as traf_generator

# Product Specific
# ----------------
from ..common.catalyst5 import Catalyst9500 as _Catalyst9500
from ..common.stardust5 import StardustC9500 as _StardustC9500
from ..common.traffic5 import TrafficDiagsC9500 as _TrafficDiagsC9500
from ..common.traffic5 import TrafficSNTC9500 as _TrafficSNTC9500
from ..common.process5 import Process5 as _Process5
from ..common import modes5 as _modes5
from ..common import _common_def
from ..common import _ios_manifest5
from .product_definitions import _product_line_def

__title__ = "C9500 Product Module"
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

if not hasattr(aplib.conn, 'uutTN'):
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1}))


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# C9500 (shared)
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class _C9500(_Catalyst9500):
    def __init__(self, family_filter):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, ios_manifest=_ios_manifest5,
                                uut_conn=self.uut_conn, family_filter=family_filter)
        self.mode_mgr = _ModeManager(mode_module=_modes5, statemachine=self.ud.uut_state_machine,
                                    uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process5(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonC9500(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[poe_loadbox, traf_generator])
        self.diags = _StardustC9500(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip, power=self.power)
        self.peripheral = _PeripheralC5K(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapC9500(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self.act2 = _ACT2(mode_mgr=self.mode_mgr, ud=self.ud)
        self.x509sudi = _X509Sudi(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux)
        self.traffic = _Traffic(fmdiags=_TrafficDiagsC9500(mode_mgr=self.mode_mgr, ud=self.ud, diags=self.diags),
                                fmgenerator=_TrafficSNTC9500(mode_mgr=self.mode_mgr, ud=self.ud, ios=self.ios, equip=self.equip))
        self._callback_()
        return


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
#
# Adelphi
# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
class Adelphi(_C9500):
    def __init__(self):
        self.show_version()
        super(Adelphi, self).__init__(family_filter='adelphi')
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
