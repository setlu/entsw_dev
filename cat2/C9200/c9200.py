"""
C9200

[Catalyst]---->[Catalyst2]---->[C9200]
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
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonC9200 as _RommonC9200
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapC9200 as _PcamapC9200
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC2K as _PeripheralC2K
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.traffic.traffic import Traffic as _Traffic
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.idpro.act2 import ACT2 as _ACT2
from apollo.scripts.entsw.libs.idpro.x509 import X509Sudi as _X509Sudi
import apollo.scripts.entsw.libs.equip_drivers.poe_loadbox as poe_loadbox

# Product Specific
# ----------------
from ..common.catalyst2 import Catalyst9200 as _Catalyst9200
from ..common.stardust2 import StardustC9200 as _StardustC9200
from ..common.traffic2 import TrafficDiagsC9200 as _TrafficDiagsC9200
from ..common.process2 import Process2 as _Process2
from ..common import modes2 as _modes2
from ..common import _common_def
from ..common import _ios_manifest2
from .product_definitions import _product_line_def

__title__ = "C9200 Product Module"
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


class _C9200(_Catalyst9200):
    def __init__(self, family_filter):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, ios_manifest=_ios_manifest2,
                                uut_conn=self.uut_conn, family_filter=family_filter)
        self.mode_mgr = _ModeManager(mode_module=_modes2, statemachine=self.ud.uut_state_machine,
                                    uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process2(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonC9200(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[poe_loadbox], traf_generator=None)
        self.diags = _StardustC9200(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip, power=self.power)
        self.peripheral = _PeripheralC2K(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapC9200(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self.act2 = _ACT2(mode_mgr=self.mode_mgr, ud=self.ud)
        self.x509sudi = _X509Sudi(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux)
        self.traffic = _Traffic(fmdiags=_TrafficDiagsC9200(mode_mgr=self.mode_mgr, ud=self.ud, diags=self.diags),
                                fmgenerator=None)
        self._callback_()
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
    

class Quake(_C9200):
    def __init__(self):
        self.show_version()
        super(Quake, self).__init__(family_filter='quake')
        return

