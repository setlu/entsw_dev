"""
Catalyst Series 2

[Catalyst]---->[Catalyst2]---->[<ProductLine class>]
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
# ------
from apollo.scripts.entsw.libs.cat.catalyst import Catalyst as _Catalyst


# Product Specific
# ----------------
#

__title__ = "Catalyst Series 2 Module"
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
#
# Catalyst2 (shared)
# ______________________________________________________________________________________________________________________
class _Catalyst2(_Catalyst):
    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)


# ______________________________________________________________________________________________________________________
#
# Catalyst2000
# ______________________________________________________________________________________________________________________
class Catalyst2000(_Catalyst2):
    pass


# ______________________________________________________________________________________________________________________
#
# Catalyst9200
#  ______________________________________________________________________________________________________________________
class Catalyst9200(_Catalyst2):
    pass
