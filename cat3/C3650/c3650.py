"""
C3650

[Catalyst]---->[Catalyst3]---->[C3650]
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
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonC3000 as _RommonC3000
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapC3000 as _PcamapC3000
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC3K as _PeripheralC3K
from apollo.scripts.entsw.libs.equip_drivers.equipment import Equipment as _Equipment
from apollo.scripts.entsw.libs.traffic.traffic import Traffic as _Traffic
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS
from apollo.scripts.entsw.libs.idpro.quack2 import Quack2 as _Quack2
from apollo.scripts.entsw.libs.idpro.act2 import ACT2 as _ACT2
from apollo.scripts.entsw.libs.idpro.x509 import X509Sudi as _X509Sudi
import apollo.scripts.entsw.libs.equip_drivers.poe_loadbox as poe_loadbox

# Product Specific
# ----------------
from ..common.catalyst3 import Catalyst3000 as _Catalyst3000
from ..common.stardust3 import StardustC3000 as _StardustC3000
from ..common.traffic3 import TrafficDiagsC3000 as _TrafficDiagsC3000
from ..common import modes3 as _modes3
from ..common import _common_def
from ..common import _ios_manifest3
from .product_definitions import _product_line_def

__title__ = "Archimedes Product Module"
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


class _C3650(_Catalyst3000):
    def __init__(self, family_filter):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, ios_manifest=_ios_manifest3,
                                uut_conn=self.uut_conn, family_filter=family_filter)
        self.mode_mgr = _ModeManager(mode_module=_modes3, statemachine=self.ud.uut_state_machine,
                                    uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonC3000(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.equip = _Equipment(ud=self.ud, modules=[poe_loadbox])
        self.diags = _StardustC3000(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=self.equip, power=self.power)
        self.peripheral = _PeripheralC3K(mode_mgr=self.mode_mgr, ud=self.ud, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapC3000(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self.x509sudi = _X509Sudi(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux)
        self.traffic = _Traffic(fmdiags=_TrafficDiagsC3000(mode_mgr=self.mode_mgr, ud=self.ud, diags=self.diags),
                                fmgenerator=None)
        self._callback_()
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class Archimedes(_C3650):
    def __init__(self):
        self.show_version()
        super(Archimedes, self).__init__(family_filter='archimedes')
        self.quack2 = _Quack2(mode_mgr=self.mode_mgr, ud=self.ud)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class Euclid(_C3650):
    def __init__(self):
        self.show_version()
        super(Euclid, self).__init__(family_filter='euclid')
        self.act2 = _ACT2(mode_mgr=self.mode_mgr, ud=self.ud)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


class Theon(_C3650):
    def __init__(self):
        self.show_version()
        super(Theon, self).__init__(family_filter='theon')
        self.act2 = _ACT2(mode_mgr=self.mode_mgr, ud=self.ud)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)
