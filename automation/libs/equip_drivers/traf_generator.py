"""
Traffic Generator Driver
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

__title__ = "Traffic Generator Module"
__version__ = '2.0.0'
__author__ = ['tnugyen', 'bborel']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

func_details = common_utils.func_details


def select(**kwargs):
    """ Select
    Use this routine to select the appropriate equipment class based on the model that was detected
    per the Apollo x_config.py connection to the equipment.
    :param kwargs: 
    :return: 
    """
    log.debug("Selecting Traffic Generator...")

    gen_conn = getattr(aplib.conn, 'SNT') if hasattr(aplib.conn, 'SNT') else None
    model = 'Generator1'  # from detection routine that uses 'gen_conn'

    log.debug("Instantiating Traffic Generator for Model: {0}".format(model))
    if model == 'Generator1':
        return getattr(thismodule, 'Generator1')
    elif model == 'Generator2':
        return getattr(thismodule, 'Generator2')
    else:
        log.warning("SNT Driver = NONE. (Generator Model was unrecognized.)")
        return None


def init(gen_obj, **kwargs):
    """ Initializer
    Use this function to perform additional activity prior to instantiating the selected generator class.
    :param gen_obj: Generator class object
    :param kwargs:
    :return:
    """
    #
    # put code here as needed
    #
    return gen_obj(**kwargs)


# <PUT EQUIPMENT GENERATOR CLASSES HERE>
# <  This should be equipment commands, status, & data only. >
# <  No UUT related items in here.  >

class Generator1(object):
    def __init__(self, **kwargs):
        return
    pass


class Generator2(object):
    def __init__(self, **kwargs):
        return
    pass
