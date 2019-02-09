"""
-------------------------------------------------------------
Transition Functions for the Catalyst Series-5 product family
-------------------------------------------------------------
"""

# Prod Specific
# -------------
from apollo.scripts.entsw.cat3.common.modes3 import *
import _ios_manifest5 as ios_manifest

__title__ = "Catalyst Series-5 Mode Module"
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
thismodule = sys.modules[__name__]

MAX_IOS_RETRY = 2


def show_version():
    log.info("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))

