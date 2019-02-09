"""
Catalyst Series 4

[Catalyst]---->[Catalyst4]---->[<ProductLine class>]
                   ^
                   |
                   +--- Mid-Tier class objects.

NOTE: These class objects should normally be used only for overriding the methods of the parent class.
      The class instances available here are for debug purposes only. (Do not change the init order!)

"""

# Python
# ------
import sys
import logging

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Libs
# -------
from apollo.scripts.entsw.libs.cat.catalyst import Catalyst as _Catalyst
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

# Product Specific
# ----------------
#

__title__ = "Catalyst Series 4 Module"
__version__ = '2.0.0'
__author__ = ['bborel']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-7s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

apollo_step = common_utils.apollo_step

if not hasattr(aplib.conn, 'uutTN'):
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1}))


# ______________________________________________________________________________________________________________________
#
# Catalyst4 (shared)
# ______________________________________________________________________________________________________________________
class _Catalyst4(_Catalyst):

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


# ______________________________________________________________________________________________________________________
#
# Catalyst4000
# ______________________________________________________________________________________________________________________
class Catalyst4000(_Catalyst4):
    pass


# ______________________________________________________________________________________________________________________
#
# Catalyst9400
# ______________________________________________________________________________________________________________________
class Catalyst9400(_Catalyst4):

    @apollo_step
    def upgrade_btldr_and_fpga(self, **kwargs):
        """ Upgrade Bootloader/Rommon and FPGA
        :menu: (enable=True, name=UPGRADE BTLDR/FPGA, section=Upgrade, num=1, args={'force': False})
        :menu: (enable=True, name=UPGRADE BTLDR/FPGA force, section=Upgrade, num=1, args={'force': True})
        :param kwargs:
        :return:
        """

        # Process input
        btldr_image = kwargs.get('image', 'LINUX_BATCH')
        force = kwargs.get('force', False)

        # Check mode
        if self.mode_mgr.current_mode not in ['LINUX']:
            errmsg = "Wrong mode; need to be in LINUX."
            log.error(errmsg)
            return aplib.FAIL, errmsg

        # Perform the upgrade
        aplib.set_container_text('UPGRADE BTLDR: {0}'.format(btldr_image))
        result = self.rommon.upgrade(btldr_image, force=force)

        return aplib.PASS if result else aplib.FAIL
