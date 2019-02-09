"""
------------
C9200 DBGSYS
------------
"""

# Python
# ------
import logging
import sys
from collections import namedtuple

# Apollo
# ------
import apollo.libs.lib as aplib

# BU Specific
# -----------
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_quake


__product_line__ = 'C9200'
__title__ = "{0} Eng Debug Sequence Module".format(__product_line__)
__version__ = '2.0.0'
__author__ = 'bborel'

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

SeqStep = namedtuple('SeqStep', ' step_module seq_function_name')
SEQ_STEP_MAP = {
    'QUAKE': SeqStep(steps_quake, 'quake_sequence'),
}

def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE-SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} PRESEQ DEBUG'.format(__product_line__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.process_manual_select_family, name='SELECT FAMILY', kwargs={'area_seq_module': thismodule})
    seq.add_step(steps_catalyst.process_uut_debug_scan, name='DEBUG SETUP', kwargs={'product_line': __product_line__})
    seq.add_step(steps_catalyst.process_add_tst, name='ADD TST')
    seq.add_step(steps_catalyst.ud_save, name='SAVE UUT DESCRIPTOR')
    seq.add_step(steps_catalyst.ud_cache_ud_data, name='CACHE UUT DATA')
    seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def eng_utility_menu_sequence_definition():
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(aplib.get_my_container_key()))
    pf = udd.get('product_family').upper()
    seq = aplib.get_sequence_definition('{0} {1} SEQ ENG MENU DEBUG'.format(__product_line__, pf), jump_on_error='FINAL')
    if pf in SEQ_STEP_MAP:
        func = getattr(thismodule, SEQ_STEP_MAP[pf].seq_function_name)
        return func(seq, pf, udd)
    else:
        seq.add_step(err_product_family, kwargs={'pf': pf})
        seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


def err_product_family(pf):
    errmsg = "The product family '{0}' is NOT known or has a problem".format(pf)
    log.critical(errmsg)
    return aplib.FAIL, errmsg


#-----------------------------------------------------------------------------------------------------------------------
# QUAKE
#-----------------------------------------------------------------------------------------------------------------------
def quake_sequence(seq, pf, udd):
    subseq__init(seq, pf)
    seq.add_step(steps_quake.debug_menu, name="MENU", kwargs={})
    seq.add_step(steps_quake.final, name='FINAL')
    return seq


#=======================================================================================================================
# Library of Common Main SEQ Subsequences
#=======================================================================================================================
def subseq__init(seq, pf):
    steps_pf = SEQ_STEP_MAP[pf].step_module
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_pf.init, name='INIT', kwargs={})
    init_seq.add_step(steps_pf.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_pf.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_pf.ud_print_uut_config, name='PRINT UUT CONFIG')
    return seq
