"""
-----------
C9300 SYSBI
-----------

NOTE: This is a legacy replacement to mimic pcbft as sysbi.
      The configs.common.cat3.stations provide for an alias of SYSBI to work as PCBFT via switch_sysbi().
"""

from pcbft import *

__product_line__ = 'C9300'
__area__ = 'SYSBI'
__title__ = "{0} {1} Sequence Module".format(__product_line__, __area__)
__version__ = '2.0.0'
__author__ = 'bborel'