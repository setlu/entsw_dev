"""
-----------
C3650 SYSFT
-----------
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
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_archimedes

__product_line__ = 'C3650'
__desc__ = 'SYSFT'
__title__ = "{0} {1} Sequence Module".format(__product_line__, __desc__)
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


def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE_SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __desc__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER',
                 kwargs={'method': 'boot'})
    seq.add_step(steps_catalyst.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    seq.add_step(steps_catalyst.process_add_tst, name='ADD TST')
    seq.add_step(steps_catalyst.ud_save, name='SAVE UUT DESCRIPTOR')
    seq.add_step(steps_catalyst.ud_cache_ud_data, name='CACHE UUT DATA')
    seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def standard_switch_sequence_definition():
    try:
        container = aplib.get_my_container_key()
    except Exception:
        raise Exception("Cannot use this Apollo version!")
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(container))
    pf = udd.get('product_family').upper()
    pc = udd.get('product_codename').upper()
    seq = aplib.get_sequence_definition('{0} {1} {2} {3} SEQ'.format(__product_line__, pf, pc, __desc__), jump_on_error='FINAL')
    # -------
    subseq__init(seq)
    #
    # PUT DF SEQ HERE !
    #
    subseq__final(seq)
    return seq


#=======================================================================================================================
# Library of Common Main Sub-Sequences
#=======================================================================================================================
def subseq__init(seq):
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(steps_archimedes.init, name='INIT', kwargs={})
    init_seq.add_step(steps_archimedes.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(steps_archimedes.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(steps_archimedes.ud_print_uut_config, name='PRINT UUT CONFIG')
    return seq


def subseq__final(seq):
    final_seq = seq.add_sequence('FINAL', finalization=True)
    seq.add_step(steps_archimedes.power_off, name='POWER OFF', kwargs={}, group_level=1000)
    final_seq.add_step(steps_archimedes.clean_up, name='CLEAN UP')
    final_seq.add_step(steps_archimedes.final, name='END')
