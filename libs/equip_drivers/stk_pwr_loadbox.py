"""
Stack Power LoadBox Driver
"""

# Python
# ------
import sys
import logging

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Stack Power Loadbox Driver Module"
__version__ = '0.0.1'
__author__ = ['steli2', 'bborel']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

func_details = common_utils.func_details


def select_and_init(**kwargs):
    """ Select & Init
    Use this routine to select the appropriate equipment class based on the model that was detected
    per the Apollo x_config.py connection to the equipment.
    :param kwargs:
    :return:
    """
    splb_conn = getattr(aplib.conn, 'stkpwrLB') if hasattr(aplib.conn, 'stkpwrLB') else None
    model = 'StkPwrLoadboxX'  # from detection routine that uses 'splb_conn'

    log.debug("Instantiating Stack Power LoadBox for Model: {0}".format(model))
    if model == 'StkPwrLoadbox1':
        equip_driver = getattr(thismodule, 'StkPwrLoadbox1')
        return equip_driver(splb_conn, **kwargs)
    elif model == 'StkPwrLoadbox2':
        equip_driver = getattr(thismodule, 'StkPwrLoadbox2')
        return equip_driver(splb_conn, **kwargs)
    else:
        log.warning("Stack Power Loadbox Driver = NONE. (Model was unrecognized.)")
        return None

# <PUT EQUIPMENT LOADBOX CLASSES HERE>
# <  This should be equipment commands, status, & data only. >
# <  No UUT related items in here.  >

class StkPwrLoadboxX(object):
    pass