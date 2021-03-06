"""
--------------------
C9400 Linecard PCB2C
--------------------
"""

# Python
# ------
import logging
import sys

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Specific
# -----------
# import apollo.scripts.entsw.libs.seq.dynamic_sequence_builder as dynamic_sequence_builder


__title__ = "C9400 Linecard PCB2C Sequence Module"
__version__ = '2.0.0'
__author__ = 'bborel'

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    """ SUPERCONTAINER
    :return:
    """
    return


def pre2_sequence_definition():
    """ UUT CONTAINER
    :return:
    """
    return


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def standard_switch_sequence_definition():
    return
