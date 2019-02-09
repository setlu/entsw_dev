"""
--------------
CATALYST SYSFT
--------------

NOTE: This area sequence file supports a UNIVERSAL station.

REQUIREMENTS:
    1. The actual product line/family area sequence (sysft.py) module must be imported here.
    2. The module import MUST be aliased to "<Apollo product line>_sysft".
    3. The BU imports will have to be maintained as new product lines are introduced.

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
import apollo.scripts.entsw.libs.seq.dynamic_sequence_builder as dynamic_sequence_builder
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
# import apollo.scripts.entsw.cat2.C9200.area_sequences.sysft as C9200_sysft
import apollo.scripts.entsw.cat3.C3650.area_sequences.sysft as C3650_sysft
import apollo.scripts.entsw.cat3.C3850.area_sequences.sysft as C3850_sysft
import apollo.scripts.entsw.cat3.C9300.area_sequences.sysft as C9300_sysft
import apollo.scripts.entsw.cat3.C9300L.area_sequences.sysft as C9300L_sysft
# import apollo.scripts.entsw.cat4.C9400.area_sequences.sysft as C9400_sysft
import apollo.scripts.entsw.cat5.C9500.area_sequences.sysft as C9500_sysft


__product_line__ = 'CATALYST'
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

PUID_KEYS = ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SYSTEM_SERIAL_NUM', 'CFG_MODEL_NUM']


# ======================================================================================================================
# PRE-SEQ
# ======================================================================================================================
def prepare_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __desc__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.ud_set_puid_keys, name='SET PUID', kwargs={'keys': PUID_KEYS})
    seq.add_step(steps_catalyst.power_off, name='POWER OFF')
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER', kwargs={'method': 'boot'})
    seq.add_step(steps_catalyst.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    seq.add_step(steps_catalyst.process_analyze_lineid, name='GET LINEID INFO')
    seq.add_step(steps_catalyst.process_update_cfg_model_num, name='UPDATE CFG MODEL NUM')
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
        pass
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(container))
    pl = udd.get('product_line').upper()
    seq_module = getattr(thismodule, pl + '_sysft')
    return seq_module.standard_switch_sequence_definition()
