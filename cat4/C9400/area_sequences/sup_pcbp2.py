"""
----------------------
C9400 Supervisor PCBP2
----------------------
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
import apollo.scripts.entsw.libs.seq.dynamic_sequence_builder as dynamic_sequence_builder
import apollo.scripts.entsw.libs.cat.steps_catalyst as steps_catalyst
from .. import steps_macallan_sup
from .. import steps_macallan_sup as steps_macallan2_sup  # fake-out placeholder


__product_line__ = 'C9400'
__desc__ = 'PCBP2'
__title__ = "{0} Supervisor {1} Sequence Module".format(__product_line__, __desc__)
__version__ = '2.0.0'
__author__ = ['krauss', 'bborel']

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
    'MACALLAN_SUP': SeqStep(steps_macallan_sup, 'macallan_sup_sequence'),
    'MACALLAN2_SUP': SeqStep(steps_macallan2_sup, 'macallan2_sup_sequence'),
}

def show_version():
    log.info("{0}  ({1})   v:{2}".format(__title__, __name__, __version__))


# ======================================================================================================================
# PRE-SEQ
# ======================================================================================================================
def pre_sequence_definition():
    seq = aplib.get_sequence_definition('{0} {1} PRESEQ'.format(__product_line__, __desc__), jump_on_error='FINAL')
    seq.add_step(steps_catalyst.init_catalyst, name='INIT', kwargs={})
    seq.add_step(steps_catalyst.ud_set_puid_keys, name='SET PUID',
                 kwargs={'keys': ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
                                  'SERIAL_NUM', 'MODEL_NUM']})
    seq.add_step(steps_catalyst.process_uut_discover, name='UUT DISCOVER',
                 kwargs={'method': 'scan',
                         'required_items': ['MODEL_NUM',
                                            'SERIAL_NUM',
                                            'MOTHERBOARD_ASSEMBLY_NUM',
                                            'QUACK_LABEL_SN'],
                         'optional_items': [],
                         })
    seq.add_step(steps_catalyst.process_add_tst, name='ADD TST')
    seq.add_step(steps_catalyst.ud_save, name='SAVE UUT DESCRIPTOR')
    seq.add_step(steps_catalyst.ud_cache_ud_data, name='CACHE UUT DATA')
    seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


# ======================================================================================================================
# SEQ
# ======================================================================================================================
def standard_modular_switch_sequence_definition():
    try:
        container = aplib.get_my_container_key()
    except Exception:
        raise Exception("Cannot use this Apollo version!")
    udd = aplib.get_cached_data('{0}_uut_descriptor'.format(container))
    pf = udd.get('product_family').upper()
    pc = udd.get('product_codename').upper()
    seq = aplib.get_sequence_definition('{0} {1} {2} {3} SEQ'.format(__product_line__, pf, pc, __desc__), jump_on_error='FINAL')
    if pf in SEQ_STEP_MAP:
        func = getattr(thismodule, SEQ_STEP_MAP[pf].seq_function_name)
        return func(seq, pf, udd, container)
    else:
        seq.add_step(err_product_family, kwargs={'pf': pf})
        seq.add_step(steps_catalyst.final, name='FINAL')
    return seq


def err_product_family(pf):
    errmsg = "The product family '{0}' is NOT known or has a problem".format(pf)
    log.critical(errmsg)
    return aplib.FAIL, errmsg


#-----------------------------------------------------------------------------------------------------------------------
# MACALLAN Sups
#-----------------------------------------------------------------------------------------------------------------------
def macallan_sup_sequence(seq, pf, udd, container):

    # Init
    subseq__init(seq, pf)

    # Area Check
    seq.add_step(steps_macallan_sup.process_area_check, name='AREACHECK',
                 kwargs={'previous_area': 'ICT',
                         'previous_uuttype_and_sn_source': ('MOTHERBOARD_ASSEMBLY_NUM', 'SERIAL_NUM')},
                 enabled=True)

    # Assemble Motherboard Geneaology
    # seq.add_step(steps_macallan_sup.process_register_genealogy,
    #             name='REGISTER SUP GENEALOGY',
    #             kwargs={'parent_sernum_item': 'SERIAL_NUM',
    #                     'parent_pid_item': 'MODEL_NUM',
    #                     'optional_child_sernum_items': [],
    #                     'optional_child_pid_items': []})

    seq.add_step(steps_macallan_sup.allocate_supervisor_container, name='ACTIVATE SUP', group_level=4,
                 kwargs={'action': 'activate', 'priority': 5})

    # Power ON & Boot
    seq.add_step(steps_macallan_sup.power_cycle_on, name='POWER ON BOOT', group_level=5)

    # Basic Mode & Get UUT Params (if any)
    seq.add_step(steps_macallan_sup.goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    seq.add_step(steps_macallan_sup.pcamap_read_uut, name='IMPORT PARAMS', kwargs={'device_instance': 0})

    # MAC Verify and Assign
    seq.add_step(steps_macallan_sup.process_assign_verify_mac, name='ASSIGN-VERIFY MAC',
                 kwargs={'assign': True})

    # ------------------------------------------------------------------------------------------------------------------
    # Rommon and FPGA Updating
    # rommon_fpga_seq = seq.add_sequence('ROMMON AND FPGA UPDATES', jump_on_error='CLEAN UP', enabled=False)
    # rommon_fpga_seq.add_step(common_test_step_collection.step__goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    # rommon_fpga_seq.add_step( NEED STEP TO PERFORM UPDATE )

    # ------------------------------------------------------------------------------------------------------------------
    # Several critical items - partition, mkdir bootflash, copy in stardust, TLV, DopSetVolt
    #key_items_seq = seq.add_sequence('KEY ITEMS 1', jump_on_error='CLEAN UP', enabled=False)
    #key_items_seq.add_step(common_test_step_collection.step__goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    # key_items_seq.add_step( NEED STEP TO PARTITION FLASH )
    # key_items_seq.add_step( NEED STEP TO CREATE BOOTFLASH DIRECTORY )
    # key_items_seq.add_step( NEED STEP TO COPY STARDUST INTO BOOTFLASH )
    #key_items_seq.add_step(c4k_test_step_collection.step__lock_sup_test_resource, name='LOCK SUP-SUP RESC', kwargs={})
    #key_items_seq.add_step(common_test_step_collection.step__goto_mode, name='MODE STARDUST',
    #                       kwargs={'mode': 'STARDUST'})
    #key_items_seq.add_step(c4k_test_step_collection.step__unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC',
    #                       kwargs={})
    # key_items_seq.add_step( NEED STEP TO WRITE TLV )
    # key_items_seq.add_step( NEED STEP TO ISSUE DOP SET VOLT )
    #key_items_seq.add_step(common_test_step_collection.step__goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})

    # ------------------------------------------------------------------------------------------------------------------
    # GOLDEN ROMMON TESTING
    #gold_rommon_seq = seq.add_sequence('KEY ITEMS 2', jump_on_error='CLEAN UP', enabled=False)
    #gold_rommon_seq.add_step(common_test_step_collection.step__goto_mode, name='MODE BTLDR', kwargs={'mode': 'BTLDR'})
    # gold_rommon_seq.add_step( NEED STEP TO ISSUE BOOT FROM GOLDEN COPY OF ROMMON )
    # gold_rommon_seq.add_step( NEED STEP TO SET GOLDEN ROMMON PARAMETERS )
    # gold_rommon_seq.add_step( NEED STEP TO BOOT BACK UP WITH PRIMARY ROMMON )

    # ------------------------------------------------------------------------------------------------------------------
    # Identity Protection Programming
    idpro_seq = seq.add_sequence('IDENTITY PROTECTION', enabled=False)
    idpro_seq.add_step(steps_macallan_sup.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    idpro_seq.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC-1', kwargs={})
    idpro_seq.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    idpro_seq.add_step(steps_macallan_sup.diags_sysinit, name='DIAG SYSINIT')
    idpro_seq.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    idpro_seq.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncACT2'})
    idpro_seq.add_step(steps_macallan_sup.x509sudi_sign_certificate, name='ID PRO X509-1',
                       kwargs={'x509_sudi_hash': 'SHA1',  'keytype': 'ACT2-RSA'}, enabled=True)
    idpro_seq.add_step(steps_macallan_sup.act2_sign_chip, name='ID PRO ACT2', kwargs={}, enabled=True)
    idpro_seq.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC-2', kwargs={})
    idpro_seq.add_step(steps_macallan_sup.x509sudi_sign_certificate, name='ID PRO X509-2',
                       kwargs={'x509_sudi_hash': 'SHA256', 'keytype': 'ACT2-RSA'}, enabled=True)
    idpro_seq.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC-2', kwargs={})

    # ------------------------------------------------------------------------------------------------------------------
    # Main Testing
    diag_seq = seq.add_sequence('DIAGNOSTIC TESTS', enabled=True)
    diag_seq.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsync'})
    diag_seq.add_step(steps_macallan_sup.goto_mode, name='MODE LINUX', kwargs={'mode': 'LINUX'})
    # Diag Testlist build-out
    # cat1 and cat3
    diag_seq_sub1 = diag_seq.add_sequence('DEPENDENT DIAG TESTS', enabled=False)
    diag_seq_sub1.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsync'})
    diag_seq_sub1.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    diag_seq_sub1.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    diag_seq_sub1.add_step(steps_macallan_sup.auxsup_mode, name='AUXSUP MODE-L', kwargs={'mode': 'LINUX'})
    diag_seq_sub1.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': None, 'auxsup': True})
    diag_seq_sub1.add_step(steps_macallan_sup.diags_sysinit, name='DIAG SYSINIT', kwargs={'timeout': 500})
    diag_seq_sub1.add_step(steps_macallan_sup.goto_mode, name='MODE DIAG', kwargs={'mode': 'DIAG'})
    diag_seq_sub1_a = diag_seq_sub1.add_sequence('MODE DEPENDENT TESTS', enabled=True)
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq_sub1_a, container=container, udd=udd, step_module=steps_macallan_sup, category=1, enabled=True)
    diag_seq_sub1_b = diag_seq_sub1.add_sequence('RESOURCE DEPENDENT TESTS', enabled=True)
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq_sub1_b, container=container, udd=udd, step_module=steps_macallan_sup, category=3, enabled=True)
    diag_seq_sub1.add_step(steps_macallan_sup.auxsup_mode, name='AUXSUP MODE-S', kwargs={'mode': 'STARDUST'})
    diag_seq_sub1.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST-2', kwargs={'mode': 'STARDUST'})
    diag_seq_sub1.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    # cat2
    diag_seq_sub2 = diag_seq.add_sequence('INDEPENDENT DIAG TESTS', enabled=False)
    diag_seq_sub2.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsync'})
    diag_seq_sub2.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    diag_seq_sub2.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    diag_seq_sub2.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': None, 'auxsup': False})
    diag_seq_sub2.add_step(steps_macallan_sup.diags_sysinit, name='DIAG SYSINIT', kwargs={'timeout': 500})
    diag_seq_sub2.add_step(steps_macallan_sup.goto_mode, name='MODE DIAG', kwargs={'mode': 'DIAG'})
    diag_seq_sub2.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    diag_seq_sub2.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync2'})
    dynamic_sequence_builder.build_diag_testlist_subseq(diag_seq=diag_seq_sub2, container=container, udd=udd, step_module=steps_macallan_sup, category=2, enabled=True)
    diag_seq_sub2.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST-2', kwargs={'mode': 'STARDUST'})

    #  -----------------------------------------------------------------------------------------------------------------
    # Traffic  Tests
    traf_seq = seq.add_sequence('TRAFFIC TESTS', jump_on_error='CLEAN UP', enabled=True)
    traf_seq_sub1 = traf_seq.add_sequence("1G TRAF TESTS SUP")
    traf_seq_sub1.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncTraf'})
    traf_seq_sub1.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub1.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    traf_seq_sub1.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': 'first', 'auxsup': False})
    traf_seq_sub1.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub1.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync'})
    #dynamic_sequence_builder.build_traffic_cases_seq(traf_seq_sub1, container)  # , category=1)
    traf_seq_sub2 = traf_seq.add_sequence("10G TRAF TESTS SUP")
    traf_seq_sub2.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncTraf'})
    traf_seq_sub2.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub2.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    traf_seq_sub2.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': 'second', 'auxsup': False})
    traf_seq_sub2.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub2.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync'})
    #dynamic_sequence_builder.build_traffic_cases_seq(traf_seq_sub2, container)  # , category=2)
    traf_seq_sub3 = traf_seq.add_sequence("25G TRAF TESTS SUP")
    traf_seq_sub3.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncTraf'})
    traf_seq_sub3.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub3.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    traf_seq_sub3.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': 'first', 'auxsup': False})
    traf_seq_sub3.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub3.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync'})
    #dynamic_sequence_builder.build_traffic_cases_seq(traf_seq_sub2, container)  # , category=2)
    traf_seq_sub4 = traf_seq.add_sequence("40G TRAF TESTS SUP")
    traf_seq_sub4.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncTraf'})
    traf_seq_sub4.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub4.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    traf_seq_sub4.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': 'second', 'auxsup': False})
    traf_seq_sub4.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub4.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync'})
    #dynamic_sequence_builder.build_traffic_cases_seq(traf_seq_sub2, container)  # , category=2)
    traf_seq_sub5 = traf_seq.add_sequence("TRAF TESTS SUP")
    traf_seq_sub5.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS', kwargs={'sync_group': 'SUPsyncTraf'})
    traf_seq_sub5.add_step(steps_macallan_sup.lock_sup_as_resource, name='LOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub5.add_step(steps_macallan_sup.goto_mode, name='MODE STARDUST', kwargs={'mode': 'STARDUST'})
    traf_seq_sub5.add_step(steps_macallan_sup.setuserslot_sup, name='SET USERSLOT', kwargs={'linecards': None, 'auxsup': False})
    traf_seq_sub5.add_step(steps_macallan_sup.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    traf_seq_sub5.add_step(steps_macallan_sup.sync_supervisors, name='SYNC SUPS-2', kwargs={'sync_group': 'SUPsync'})
    #dynamic_sequence_builder.build_traffic_cases_seq(traf_seq_sub2, container)  # , category=2)

    # ------------------------------------------------------------------------------------------------------------------
    # Clean up & Power OFF
    #cleanup_seq = seq.add_sequence('CLEAN UP', finalization=True)
    #cleanup_seq.add_step(c4k_test_step_collection.step__allocate_supervisor_container, name='DEACTIVATE SUP',
    #                    group_level=1000, kwargs = {'action': 'deactivate', 'priority': 10})
    #cleanup_seq.add_step(common_test_step_collection.step__power_off, name='POWER OFF', group_level=1000, kwargs={'modular': True})
    #cleanup_seq.add_step(c4k_test_step_collection.step__unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    #cleanup_seq.add_step(common_test_step_collection.step__clean_up, name='CLEAN', kwargs={'modular': True})

    # ------------------------------------------------------------------------------------------------------------------
    # Final (Power off, clean up, end)
    subseq_final(seq, pf)
    return seq


#-----------------------------------------------------------------------------------------------------------------------
# MACALLAN2 Sups
#-----------------------------------------------------------------------------------------------------------------------
def macallan2_sup_sequence(seq, pf, udd):
    subseq__init(seq, pf)
    seq.add_step(steps_macallan2_sup.final, name='FINAL')
    return seq


#=======================================================================================================================
# Library of Common Main SEQ Subsequences
#=======================================================================================================================
def subseq__init(seq, pf):
    pf_steps = SEQ_STEP_MAP[pf].step_module
    init_seq = seq.add_sequence('INITIALIZATION')
    init_seq.add_step(pf_steps.init, name='INIT', kwargs={})
    init_seq.add_step(pf_steps.ud_retrieve, name="RETRIEVE UUT DESCRIPTOR")
    init_seq.add_step(pf_steps.ud_print_uut_descriptor, name='PRINT DESCRIPTOR')
    init_seq.add_step(pf_steps.ud_print_uut_config, name='PRINT UUT CONFIG')
    return seq


def subseq_final(seq, pf):
    pf_steps = SEQ_STEP_MAP[pf].step_module
    cleanup_seq = seq.add_sequence('FINAL', finalization=True)
    cleanup_seq.add_step(pf_steps.allocate_supervisor_container, name='DEACTIVATE SUP', group_level=1000,
                         kwargs={'action': 'deactivate', 'priority': 10})
    cleanup_seq.add_step(pf_steps.clean_up, name='CLEAN UP', kwargs={})
    seq.add_step(pf_steps.power_off, name='POWER OFF')
    cleanup_seq.add_step(pf_steps.unlock_sup_test_resource, name='UNLOCK SUP-SUP RESC', kwargs={})
    cleanup_seq.add_step(pf_steps.final, name='END', kwargs={})
