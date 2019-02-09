"""
Catalyst Series 2 Peripherals

[Catalyst]---->[Catalyst2]---->[C_PERIPH]
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
from apollo.scripts.entsw.libs.product_drivers.rommon import RommonGen3 as _RommonGen3
from apollo.scripts.entsw.libs.product_drivers.pcamap import PcamapGen3 as _PcamapGen3
from apollo.scripts.entsw.libs.product_drivers.peripheral import PeripheralC2K as _PeripheralC2K
from apollo.scripts.entsw.libs.opsys.linux import Linux as _Linux
from apollo.scripts.entsw.libs.opsys.ios import IOS as _IOS


# Product Specific
# ----------------
from ..common.catalyst2 import _Catalyst2
from ..common.stardust2 import _Stardust2
from ..common import modes2 as _modes2
from ..common import _common_def
from .product_definitions import _product_line_def

__title__ = "Catalyst Series 2 Peripheral Module"
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


class Cat2Peripherals(_Catalyst2):
    def __init__(self):
        self.uut_conn = aplib.conn.uutTN
        self.ud = _UutDescriptor(common_def=_common_def, product_line_def=_product_line_def, uut_conn=self.uut_conn,
                                 parent_module=thismodule)
        self.mode_mgr = _ModeManager(mode_module=_modes2, statemachine=self.ud.uut_state_machine,
                                     uut_prompt_map=self.ud.uut_prompt_map, uut_conn=self.uut_conn)
        self.process = _Process(mode_mgr=self.mode_mgr, ud=self.ud)
        self.power = _Power(mode_mgr=self.mode_mgr, ud=self.ud)
        self.rommon = _RommonGen3(mode_mgr=self.mode_mgr, ud=self.ud)
        self.linux = _Linux(mode_mgr=self.mode_mgr, ud=self.ud)
        self.diags = _Stardust2(mode_mgr=self.mode_mgr, ud=self.ud, linux=self.linux, equip=None)
        self.peripheral = _PeripheralC2K(mode_mgr=self.mode_mgr, sysinit=self.diags.sysinit)
        self.pcamap = _PcamapGen3(mode_mgr=self.mode_mgr, ud=self.ud, rommon=self.rommon, peripheral=self.peripheral)
        self.ios = _IOS(mode_mgr=self.mode_mgr, ud=self.ud)
        self._callback_()

        return
