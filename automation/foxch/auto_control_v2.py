"""
Automation Control
"""

# Python
# ------
import logging
import os
import subprocess
import time
import ConfigParser
import re

# Apollo
# ------
from apollo.libs import lib
from apollo.libs import locking

__title__ = "Automation Module"
__version__ = '0.2.0'
__author__ = ['steli2', 'bborel']

log = logging.getLogger(__name__)

uuttype = {
    '1': 'N24',
    '2': 'N48',
    '3': 'N24P',
    '4': 'N48P',
    '5': 'N24U',
    '6': 'N48U',
    '7': 'P12',
    '8': 'P24',
    '9': 'O24',
    'A': 'O48',
    'B': 'G12',
    'C': 'G48',
    '0': 'NULL',
    'E': 'ALL'
}

slot_index = {
    '1-1': 0, '1-2': 1, '1-3': 2, '1-4': 3, '1-5': 4, '1-6': 5,
    '1-7': 6, '1-8': 7, '1-9': 8, '1-10': 9, '1-11': 10, '1-12': 11,
    '2-1': 12, '2-2': 13, '2-3': 14, '2-4': 15, '2-5': 16, '2-6': 17,
    '2-7': 18, '2-8': 19, '2-9': 20, '2-10': 21, '2-11': 22, '2-12': 23,
    '3-1': 24, '3-2': 25, '3-3': 26, '3-4': 27, '3-5': 28, '3-6': 29,
    '3-7': 30, '3-8': 31, '3-9': 32, '3-10': 33, '3-11': 34, '3-12': 35,
    '4-1': 36, '4-2': 37, '4-3': 38, '4-4': 39, '4-5': 40, '4-6': 41,
    '4-7': 42, '4-8': 43, '4-9': 44, '4-10': 45, '4-11': 46, '4-12': 47,
    '5-1': 48, '5-2': 49, '5-3': 50, '5-4': 51, '5-5': 52, '5-6': 53,
    '5-7': 54, '5-8': 55, '5-9': 56, '5-10': 57, '5-11': 58, '5-12': 59,
    '6-1': 60, '6-2': 61, '6-3': 62, '6-4': 63, '6-5': 64, '6-6': 65,
    '6-7': 66, '6-8': 67, '6-9': 68, '6-10': 69, '6-11': 70, '6-12': 71,
    '7-1': 72, '7-2': 73, '7-3': 74, '7-4': 75, '7-5': 76, '7-6': 77,
    '7-7': 78, '7-8': 79, '7-9': 80, '7-10': 81, '7-11': 82, '7-12': 83,
    '8-1': 84, '8-2': 85, '8-3': 86, '8-4': 87, '8-5': 88, '8-6': 89,
    '8-7': 90, '8-8': 91, '8-9': 92, '8-10': 93, '8-11': 94, '8-12': 95,
}


# ------------------------------------------------------------------------------------------------------------
# SEQUENCES: SEQ & PRE-SEQ
#
def pre_control_sequence_definition():
    """EdisonCSR auto test scan-sequence

    :return:
    """
    seq = lib.get_sequence_definition('FST AUTOMATION PRE SEQ')
    seq.add_step(prestep__set_test_mode, name='SET TEST MODE', group_level=lib.INITIALIZATION)
    seq.add_step(prestep__restore_container, name='Restore Running Container')
    seq.add_step(step__auto_monitor, name='AUTOMATION MONITOR')
    seq.add_step(prestep__clean_up, name='SLOT STATUS CLEANUP', group_level=lib.FINALIZATION)
    return seq


def main_control_sequence_definition():
    """EdisonCSR ASSY Pre-sequence

    :return:
    """
    seq = lib.get_sequence_definition('FST AUTOMATION SEQ')
    seq.add_step(step__auto_monitor, name='AUTOMATION MONITOR')
    return seq


# ------------------------------------------------------------------------------------------------------------
# Steps: Automation PreSeq & Seq
#
def prestep__clean_up():
    """

    :return:
    """
    log.info('******* Clean UP ***********')
    cap_slot_status()
    log.info('*******Save Slot Status***********')
    return lib.PASS


def prestep__set_test_mode():
    """Set Test Mode
    set test mode for automation monitor container, Default: DEBUG
    :return:
    """
    lib.set_apollo_mode('DEBUG')
    log.info("get_apollo_mode is {}".format(lib.get_apollo_mode()))

    return lib.PASS


def prestep__restore_container():
    """Restore running status container
    read local slots status from /tftpboot/slot_status/slot_status, restore start containers
    :return:
    """
    area = 'SYSBI'
    slot_status_file = r'/tftpboot/slot_status/slot_status'
    with open(slot_status_file, 'r') as f:
        slot_status = [cell.strip() for cell in f.readlines() if ':' in cell]

    lib.cache_data('slot_status', slot_status)
    log.info('Local: {}'.format(slot_status))
    log.debug('******************')
    for i in range(1, 9):
        log.info('{}'.format(slot_status[(i - 1) * 12: i * 12]))
    log.debug('******************')

    keep_status = ['ERRO', 'FAIL', 'PASS', 'IDLE', 'NULL']

    for ctr in slot_status:
        station = 'Station'
        cell = 'AUTO:UUT{:02}_{:02}'.format(int(ctr.split(':')[1].split('-')[0]),
                                            int(ctr.split(':')[1].split('-')[1]))
        log.info('Station: {}, Cell: {}'.format(station, cell))
        if any(status in ctr for status in keep_status):
            log.info('Container [{}] Keep {}'.format(cell, ctr))
            continue
        log.info('Container ctr restore to running'.format(ctr))
        while True:
            run_apollo_container(prod_line='UAG_C3K', area=area, test_station=station, container=cell, mode='PROD')
            if lib.get_container_status(cell) == 'RUNNING':
                time.sleep(60)
                break
            log.info('{} running meet issue, re-start'.format(cell))
            continue

    return lib.PASS


def step__auto_monitor():
    """Auto Monitor
    monitor and communicate with Robot
    :return:
    """
    container = lib.get_pre_sequence_info().containers[0]
    log.info('This is Auto[{}]'.format(container[0]))
    area = 'SYSBI'

    pc = lib.conn.PC
    pc.power_on()
    log.info('waiting command....')
    time.sleep(0.5)
    pc.clear_recbuf()
    time.sleep(0.5)
    out_type = 'X'
    while True:
        null_seq = []
        pc.send('')
        if '#' in pc.recbuf:
            slot_status = lib.get_cached_data('slot_status')
            comm = pc.recbuf.upper()
            log.info('received command [{}]'.format(comm))

            if comm[-1] != '#':
                log.debug('invalid command, skip')
                pc.clear_recbuf()
                continue

            if comm.count('#') > 1:
                comm = comm.split('#')[-2]+'#'
                log.info('fix command ->{}'.format(comm))

            if 'ASK' in comm:
                if "ALL#" in comm:
                    pc.send('{}#'.format(cap_slot_status()))
                else:
                    r = int(comm.split(':')[1].split('_')[0]) - 1
                    r = 0 if r < 1 else r
                    action_seq = []
                    if '_I#' in comm or '_C#' in comm:
                        in_slot_status = slot_status
                        action_seq = [slot for slot in in_slot_status if 'NULL' in slot]
                        # log.debug('I output seq is {}, len is {}'.format(action_seq, len(action_seq)))
                        if len(action_seq) < 2:
                            action_seq = ['0NI']
                    elif '_O#' in comm:
                        out_slot_status = slot_status[(r+1)*12-1::-1] + slot_status[(r+1)*12:]
                        if out_type == 'E':
                            action_seq = [slot for slot in out_slot_status if any(ctr in slot for ctr in ['PASS', 'FAIL'])]
                        else:
                            action_seq = [slot for slot in out_slot_status
                                          if slot[0] in ["0", out_type] and any(ctr in slot for ctr in ['PASS', 'FAIL'])]
                        while action_seq:
                            if "FAIL1" not in action_seq[0]:
                                break
                            else:
                                null_seq = [slot for slot in out_slot_status if 'NULL' in slot]
                                if null_seq:
                                    break
                                else:
                                    action_seq.remove(action_seq[0])
                                    continue
                    elif '_X#' in comm:
                        out_slot_status = slot_status[(r+1)*12-1::-1]
                        if out_type == 'E':
                            out_seq = [slot for slot in out_slot_status if any(ctr in slot for ctr in ['PASS', 'FAIL2'])]
                        else:
                            out_seq = [slot for slot in out_slot_status
                                       if slot[0] == out_type and any(ctr in slot for ctr in ['PASS', 'FAIL2'])]
                        idle_seq = [slot for slot in out_slot_status if 'IDLE' in slot]
                        in_seq = [slot for slot in slot_status if 'NULL' in slot]
                        if len(in_seq) < 2:
                            in_seq = []
                        action_seq = out_seq + idle_seq + in_seq
                        if not action_seq:
                            out_slot_status = slot_status[(r+1)*12:]
                            if out_type == 'E':
                                out_seq = [slot for slot in out_slot_status if any(ctr in slot for ctr in ['PASS', 'FAIL2'])]
                            else:
                                out_seq = [slot for slot in out_slot_status
                                           if slot[0] == out_type and any(ctr in slot for ctr in ['PASS', 'FAIL2'])]
                            idle_seq = [slot for slot in out_slot_status if 'IDLE' in slot]
                            action_seq = out_seq + idle_seq
                    elif '_N#' in comm:
                        out_slot_status = slot_status[(r+1)*12-1::-1] + slot_status[(r+1)*12:]
                        null_seq = [slot for slot in out_slot_status if 'NULL' in slot]
                        if null_seq:
                            action_seq = [slot for slot in out_slot_status if 'FAIL1' in slot]
                    elif '_R#' in comm:
                        out_slot_status = slot_status[(r + 1) * 12 - 1::-1] + slot_status[(r + 1) * 12:]
                        action_seq = [slot for slot in out_slot_status if 'IDLE' in slot]
                    else:
                        log.error('Comm format wrong [{}]'.format(comm))
                    log.info('Action SEQ -> [{}]'.format(action_seq))
                    action = "0NA"
                    if action_seq:
                        for slot in action_seq:
                            action = slot
                            if "FAIL1" in action:
                                null_slot = null_seq[0]
                                action = action + ',' + null_slot.split(':')[1]
                            break
                    if any(ctr in action for ctr in ["IDLE", "PASS", "NULL"]):
                        action = action.split(':')[0][:5] + ':' + action.split(':')[1]
                    log.info('Next action [{}]'.format(action))
                    pc.send('{}#'.format(action[1:]))

            elif '-' in comm and ':' in comm:
                slot = comm.split(':')[1].split('#')[0]
                status = comm.split(':')[0]
                if 'TEST' in status:
                    station = 'Station'
                    cell = 'AUTO:UUT{:02}_{:02}'.format(int(slot.split('-')[0]), int(slot.split('-')[1]))
                    status = '0TEST{}'.format(2 if 'RE' in status else 1)
                    pc.send('OK#')
                    while True:
                        run_apollo_container(prod_line='UAG_C3K',
                                             area=area,
                                             test_station=station,
                                             container=cell,
                                             mode='PROD')
                        if lib.get_container_status(cell) == 'RUNNING':
                            log.info('{} running ok'.format(cell))
                            break
                        log.info('{} running meet issue, re-start'.format(cell))
                        continue
                    change_slot_status(slot, status, False)
                    continue
                elif 'FIN' in status:
                    slot = comm.split(':')[1].split('#')[0]
                    log.debug('Remove {} UUT'.format(slot))
                    status = '0NULL1'
                elif 'IDLE' in status:
                    slot = comm.split(':')[1].split('#')[0]
                    log.debug('Input IDLE {} UUT'.format(slot))
                    status = '0IDLE1'
                elif 'ERRO' in status:
                    status = '0ERRO1'
                elif 'FAIL' in status:
                    status = '0FAIL2'
                elif 'OPEN0' in status:
                    status = '0NULL1'
                elif 'OPEN1' in status:
                    status = '0IDLE1'
                elif 'OPEN2' in status:
                    status = '0FAIL2'
                else:
                    log.info('received command [{}]issue'.format(comm))
                pc.send('OK#')
                change_slot_status(slot, status, False)

            elif 'OUTPUT' in comm:
                out_type = comm.split(':')[1].split('#')[0]
                log.info('Output {} Product'.format(uuttype[out_type]))
                pc.send('OK#')
            else:
                log.info('received invalid command {}'.format(comm))

        else:
            continue

    return lib.PASS


# ------------------------------------------------------------------------------------------------------------
# Support functions
#
def auto_record():
    """Auto Record
    record for monitor container, set dummy SN and uut type on here.
    :return:
    """
    area = lib.get_pre_sequence_info().areas[0]
    container = lib.get_pre_sequence_info().containers[0]
    system_tst_data = dict(serial_number='FOCAUTOMAIN',
                           uut_type='73-AUTOM-AN',
                           )

    lib.add_tst_data(test_area=area,
                     test_container=container,
                     **system_tst_data
                     )

    return lib.PASS


def cap_slot_status():
    """Capture slot status
    capture slot status from  cached data 'slot_status' and sync up to '/tftpboot/slot_status/slot_status'
    :return:
    """
    time.sleep(1)
    log.info('record Slot Status lock...')
    with locking.named_priority_lock(lockname='slot_status_lock',
                                     release_timeout=60,
                                     wait_timeout=30*60):
        slot_status = lib.get_cached_data('slot_status')
        log.debug('Current status ')
        log.debug('******************')
        for i in range(1, 9):
            log.info('{}'.format(slot_status[(i - 1) * 12: i * 12]))
        log.debug('******************')
        slot_status_file = r'/tftpboot/slot_status/slot_status'
        return_slot_status = ''
        with open(slot_status_file, 'w') as f:
            f.close()
        for ctr in slot_status:
            if ':8-12' in ctr:
                return_slot_status += ctr
            else:
                return_slot_status += ctr + ','
            os.system('echo {} >> {}'.format(ctr, slot_status_file))
    # log.info('return {}'.format(return_slot_status))
    return return_slot_status


def change_slot_status(slot, status, skip_error=True):
    """Change Slot Status
    Change slot status in local file
    :param slot:
    sample: Station_B_01 = 1-1: first 1 is Rack number , second 1 is Cell number
    :param status:
    sample: status: Pass, Fail1, Fail2, Idel.
    pass: product_name,1-1,Pass
    Fail1: product_name,1-1,Fail1,num-num.   #num-num:re-test cell
    Fail2: product_name,1-1,Fail2
    IDEL:
    :param skip_error:
    :return:
    """
    log.info('{} {} change lock...'.format(slot, status))
    with locking.named_priority_lock(lockname='slot_status_lock',
                                     release_timeout=60,
                                     wait_timeout=30*60):
        slot_status = lib.get_cached_data('slot_status')
        log.debug('>>>>> ')
        for i in range(1, 9):
            log.info('{}'.format(slot_status[(i-1)*12: i*12]))
        log.debug('>>>>> '.format(slot_status))
        if 'ERRO' in slot_status[slot_index[slot]] and skip_error:
            log.debug('ERROR cannot change')
        else:
            if "ERRO" in status:
                status = "0ERRO1"
            slot_status[slot_index[slot]] = "{}:{}".format(status, slot)
            lib.cache_data('slot_status', slot_status)
        log.debug('<<<<< ')
        for i in range(1, 9):
            log.info('{}'.format(slot_status[(i-1)*12: i*12]))
        log.debug('<<<<< ')
    cap_slot_status()
    log.info('Change local OK')
    return True


def automatic_clear_pre():
    """Automatic Clear Pre
    Clear slot status in pre-sequences
    pass pre-sequences uuts, clear auto_pass in userdict
    fail pre-sequences uuts, record status in local with SN, FAIL steps,
    :return:
    """
    mm = lib.apdicts.userdict['mm']
    current_sernum = mm.uut_config.get('SYSTEM_SERIAL_NUM', 'NOPOWERON')
    # Get Step dict
    current_status, steps_ret = auto_get_test_status()
    slot = "{}-{}".format(int(lib.get_my_container_key().split('|')[-1].split('_')[0][-2:]),
                          int(lib.get_my_container_key().split('|')[-1].split('_')[1][:2]))
    slot_status = lib.get_cached_data('slot_status')
    slot_info = slot_status[slot_index[slot]]
    uut_type = slot_info[0]
    if current_status != 'PASS':
        status = '{}{}{}'.format(uut_type, current_status, slot_info.split(':')[0][-1])
        change_slot_status(slot, status)
        for k, v in steps_ret.items():
            if 'FAIL' in v:
                local_record(current_sernum, slot, status, k)

    return


def auto_get_test_status():
    """Auto get test status
    get test status from aplib.apdicts.stepdict
    return: current_status: Pass/ Fail
            test_steps_result, it's a dict {steps_name: result}

    Sample

     'name'               = 'CLEAN UP',
     'configuration_data' = {
                            'AUTOMATION' = {
                                           'enabled' = 'True'
                                           }
                            },
     'start_user'         = 'steli2',
     'current_status'     = 'PASS',
     'question_event'     = '<RLock(None, 0)>',
     'container_key'      = 'EntSw_EngUtility-C3K|DBGSYS|Station_D_05|UUT01',
     'goldboard_enabled'  = '',
     'mode'               = 'DEBUG',
     'attributes'         = {
                            'iteration_value'    = '1',
                            'current_iterations' = '',
                            'iteration_type'     = 'quantity'
                            },
     'application_name'   = 'apollo.scripts.entsw.c3k.area_sequences.c3k_eng_menu_run.eng_utility_menu',
     'step_id'            = 'SWITCH PRODUCT SEQ.CLEAN UP',
     'release_uuid'       = '04fe6971-30cb-4efd-8b28-20172f576f10',
     'data'               = {
            'qupre_seence'     = '',
            'step_number'      = '2',
            'measurementsdata' = {
                 'ENG UTIL PRESEQ' = {
                         'FOC2215U0TH' = {
                                         '75e51da10bc146bc9eda43f67e40a2b8' =
                                            {
                                          'limit_def'        = 'sequence log',
                                          'uut_type'         = 'C3K',
                                          'machine_name'     = 'fxcavp389',
                                          'test_record_time' = '2018-04-14 00	11	21',
                                          'name'             = 'pre_sequence_log',
                                          'measure_time'     = '2018-04-14 00	11	21',
                                          'limit_id'         = 'ENG UTIL PRESEQ.pre_sequence_log',
                                          'value'            = '/opt/cisco/constellation/apollo/logs/containers
                                          /fxcavp389/EntSw_EngUtility-C3K/DBGSYS/Station_D_05/UUT01/20180414_001109_144774/sequence.log',
                                          'test_unique_id'   = '1',
                                          'test_area'        = 'DBGSYS',
                                          'test_step_id'     = 'ENG UTIL PRESEQ',
                                          'result_pass_fail' = 'P',
                                          'serial_number'    = 'FOC2215U0TH',
                                          'test_id'          = '2018-04-14 00	11	21',
                                          'type'             = 'B'
                                          }
                                         }
                                     }
                                 },
            'stepdata'         = {
                     'PRE-SEQ FINAL'   = {
                                         'FOC2215U0TH' = {
                                                         'uut_type'         = 'C3K',
                                                         'machine_name'     = 'fxcavp389',
                                                         'test_record_time' = '2018-04-14 00	11	21',
                                                         'start_time'       = '2018-04-14 00	11	21',
                                                         'iterations_type'  = 'quantity',
                                                         'telcordia_retry'  = '',
                                                         'test_unique_id'   = '2',
                                                         'test_area'        = 'DBGSYS',
                                                         'end_time'         = '2018-04-14 00	11	21',
                                                         'iterations'       = '1',
                                                         'test_step_id'     = 'ENG UTIL PRESEQ.PRE-SEQ FINAL',
                                                         'result_pass_fail' = 'PASS',
                                                         'serial_number'    = 'FOC2215U0TH',
                                                         'test_id'          = '2018-04-14 00	11	21',
                                                         'iterations_value' = '1'
                                                         }
                                         },
                     'SET UP'          = {
                                         'FOC2215U0TH' = {
                                                         'uut_type'         = 'C3K',
                                                         'machine_name'     = 'fxcavp389',
                                                         'test_record_time' = '2018-04-14 00	11	22',
                                                         'start_time'       = '2018-04-14 00	11	21',
                                                         'iterations_type'  = 'quantity',
                                                         'telcordia_retry'  = '',
                                                         'test_unique_id'   = '1',
                                                         'test_area'        = 'DBGSYS',
                                                         'end_time'         = '2018-04-14 00	11	22',
                                                         'iterations'       = '1',
                                                         'test_step_id'     = 'SWITCH PRODUCT SEQ.SET UP',
                                                         'result_pass_fail' = 'PASS',
                                                         'serial_number'    = 'FOC2215U0TH',
                                                         'test_id'          = '2018-04-14 00	11	21',
                                                         'iterations_value' = '1'
                                                         }
                                         },
                     'UTILITY MENU'    = {
                                         'FOC2215U0TH' = {
                                                         'uut_type'         = 'C3K',
                                                         'machine_name'     = 'fxcavp389',
                                                         'test_record_time' = '2018-04-14 00	12	31',
                                                         'start_time'       = '2018-04-14 00	11	24',
                                                         'iterations_type'  = 'quantity',
                                                         'telcordia_retry'  = '',
                                                         'test_unique_id'   = '2',
                                                         'test_area'        = 'DBGSYS',
                                                         'end_time'         = '2018-04-14 00	12	31',
                                                         'iterations'       = '1',
                                                         'test_step_id'     = 'SWITCH PRODUCT SEQ.UTILITY MENU',
                                                         'result_pass_fail' = 'PASS',
                                                         'serial_number'    = 'FOC2215U0TH',
                                                         'test_id'          = '2018-04-14 00	11	21',
                                                         'iterations_value' = '1'
                                                         }
                                         },
                     'ADD TST DATA'    = {
                                         'FOC2215U0TH' = {
                                                         'uut_type'         = 'C3K',
                                                         'machine_name'     = 'fxcavp389',
                                                         'test_record_time' = '2018-04-14 00	11	21',
                                                         'start_time'       = '2018-04-14 00	11	21',
                                                         'iterations_type'  = 'quantity',
                                                         'telcordia_retry'  = '',
                                                         'test_unique_id'   = '1',
                                                         'test_area'        = 'DBGSYS',
                                                         'end_time'         = '2018-04-14 00	11	21',
                                                         'iterations'       = '1',
                                                         'test_step_id'     = 'ENG UTIL PRESEQ.ADD TST DATA',
                                                         'result_pass_fail' = 'PASS',
                                                         'serial_number'    = 'FOC2215U0TH',
                                                         'test_id'          = '2018-04-14 00	11	21',
                                                         'iterations_value' = '1'
                                                         }
                                         },
                     'ENG UTIL PRESEQ' = {
                                         'FOC2215U0TH' = {
                                                         'uut_type'         = 'C3K',
                                                         'machine_name'     = 'fxcavp389',
                                                         'test_record_time' = '2018-04-14 00	11	21',
                                                         'start_time'       = '2018-04-14 00	11	09',
                                                         'iterations_type'  = 'quantity',
                                                         'telcordia_retry'  = '',
                                                         'test_unique_id'   = '3',
                                                         'test_area'        = 'DBGSYS',
                                                         'end_time'         = '2018-04-14 00	11	21',
                                                         'iterations'       = '1',
                                                         'test_step_id'     = 'ENG UTIL PRESEQ',
                                                         'result_pass_fail' = 'PASS',
                                                         'serial_number'    = 'FOC2215U0TH',
                                                         'test_id'          = '2018-04-14 00	11	21',
                                                         'iterations_value' = '1'
                                                         }
                                         }
                     },
            'tstdata'          = [
                               = {
                                 'deviation'        = '91541',
                                 'uut_type'         = 'C3K',
                                 'machine_name'     = 'fxcavp389',
                                 'test_record_time' = '2018-04-14 00	11	21',
                                 'basepid'          = 'WS-C3850-48P',
                                 'partnum2'         = '73-15800-08',
                                 'eci'              = '470022',
                                 'hwrev3'           = 'B0',
                                 'test_area'        = 'DBGSYS',
                                 'test_container'   = 'UUT01',
                                 'clei'             = 'IPM8E00ARC',
                                 'hwrev2'           = 'D0',
                                 'result_pass_fail' = 'S',
                                 'serial_number'    = 'FOC2215U0TH',
                                 'tan'              = '800-43041-03',
                                 'test_id'          = '2018-04-14 00	11	21',
                                 'hwrev'            = 'V07',
                                 'diagrev'          = 'stardust_ecsr_th_011516'
                                 }
                                 ]
            'attributes'       = {
                                 'uut_type'          = 'C3K',
                                 'area'              = 'DBGSYS',
                                 'start_time_utc'    = '2018-04-14 00	11	21',
                                 'logging_enabled'   = '',
                                 'start_time_utc_dt' = '2018-04-14 00	11	21.615051',
                                 'log_filename'      = '/opt/cisco/constellation/apollo/logs/containers/fxcavp389/
                                 EntSw_EngUtility-C3K/DBGSYS/Station_D_05/UUT01/20180414_001109_144774/sequence.log',
                                 'start_sent'        = 'True',
                                 'tst_id_dt'         = '2018-04-14 00	11	21.615051',
                                 'serial_number'     = 'FOC2215U0TH',
                                 'tst_id'            = '2018-04-14 00	11	21'
                                 },
            'meas_number'      = ''
            },
            'sync_containers'    = {
    }

    :return:
    """
    test_steps_result = dict()

    # Get Current status
    current_status = lib.apdicts.stepdict.get('current_status', None)
    log.debug(current_status)
    # Get test steps result
    test_steps = lib.apdicts.stepdict.get('data')['stepdata']
    log.debug(test_steps)
    for k, v in test_steps.items():
            for i in v.values():
                test_steps_result[k] = i.get('result_pass_fail')

    log.debug(current_status, test_steps_result)

    return current_status, test_steps_result


def auto_get_model():
    """Get Uut type model
    Get automation flag in pre-sequences.
    :return:
    """
    mm = lib.apdicts.userdict['mm']
    uuttype = mm.uut_config.get('MODEL_NUM', 'NA')
    # TODO: re-design for no hardcode
    uuttype_maps = {"WS-C3850-24T": "1", "WS-C3850-48T": "2", "WS-C3850-24P": "3", "WS-C3850-48P": "4",
                    "WS-C3850-24U": "5", "WS-C3850-48U": "6", "WS-C3850-12S": "7", "WS-C3850-24S": "8",
                    "WS-C3850-24XU": "9", "WS-C3850-12X48U": "A", "WS-C3850-12XS": "B", "WS-C3850-24XS": "C",}
    uut_type = uuttype_maps[uuttype]

    slot = "{}-{}".format(int(lib.get_my_container_key().split('|')[-1].split('_')[0][-2:]),
                          int(lib.get_my_container_key().split('|')[-1].split('_')[1][:2]))
    status = "{}TEST{}".format(uut_type, lib.get_cached_data('slot_status')[slot_index[slot]].split(':')[0][-1])
    log.info('{}:{}'.format(status, slot))
    change_slot_status(slot, status)

    return


def local_record(sernum=None, cell=None, status=None, steps=None):
    """ record fail info to local file
    :param sernum: System serial num
    :param cell: test slots
    :param status: pass or fail(failures)
    :param steps: failure step name default None
    :return:
    """
    time_ctr = time.localtime(time.mktime(time.localtime())+15*3600)
    local_time = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(time_ctr.tm_year, time_ctr.tm_mon, time_ctr.tm_mday,
                                                                time_ctr.tm_hour, time_ctr.tm_min, time_ctr.tm_sec)
    record_info = "{}\t{}\t{}\t{}\r\n".format(local_time, sernum, cell, status, steps)
    log.info('record test info to local [{}]'.format(record_info))
    os.system('mkdir /tftpboot/test_records')
    local_record_file = r'/tftpboot/test_records/auto_record_{}{:02d}{:02d}'.format(time_ctr.tm_year, time_ctr.tm_mon, time_ctr.tm_mday)
    with open(local_record_file, 'a+') as f:
        f.write(record_info)
    log.info('record finish')

    monitor_slots(cell, status)

    return


def auto_finish(serial=None, steps=''):
    """Automatic Finish
    record test status Pass/Fail in local file
    :return:
    """
    current_status, steps_ret = auto_get_test_status()
    slot = "{}-{}".format(int(lib.get_my_container_key().split('|')[-1].split('_')[0][-2:]),
                          int(lib.get_my_container_key().split('|')[-1].split('_')[1][:2]))
    slot_status = lib.get_cached_data('slot_status')
    slot_info = slot_status[slot_index[slot]]
    uut_type = slot_info[0]
    status = "{}{}{}".format(uut_type, current_status, slot_info.split(':')[0][-1])
    if current_status != 'PASS':
        for k, v in steps_ret.items():
            if 'FAIL' in v:
                steps = k
    local_record(serial, slot, status, steps)
    change_slot_status(slot, status)

    return


def monitor_slots(container=None, status=None):
    """Monitor slots
    record slots pass/fail status in local file '/tftpboot/cellctr', fail two times in same slot will disable it.
    Todo: get fail step name record in local file, two times fail in same steps(equipment issues) will disable slot
    :param container:
    :param status:
    :return:
    """
    record_dir = '/tftpboot/cellctr'
    if not container:
        try:
            container = lib.get_pre_sequence_info().containers[0]
        except Exception, e:
            log.info('This Main SEQ, {}'.format(e))
            container = lib.get_my_container_key().split('|')[-1]
    container = container.replace(' ', '')
    record_f = '{}/{}'.format(record_dir, container)
    log.info('Check Container [{}] status'.format(record_f))
    if not os.path.exists(record_f):
        log.info('Monitor file not exists')
        if not os.path.isdir(record_dir):
            log.info('Monitor directory not exists')
            os.makedirs('{}'.format(record_dir))
        os.system('echo 0 >> {}'.format(record_f))
    local_status = open('{}'.format(record_f)).read()
    ctr = 0
    if status:
        if 'FAIL' in status or status in local_status:
            for i in open('{}'.format(record_f)).readlines():
                if status in i:
                    ctr += 1
            if ctr >= 2:
                log.error("Disable this test Cell")
                os.system('echo disable >> {}'.format(record_f))
                change_slot_status(container, 'ERROR')
            else:
                log.debug("record Fail Status in local")
                os.system('echo {} >> {}'.format(status, record_f))
        elif "PASS" in status:
            with open('{}'.format(record_f), 'w') as f:
                f.write('\n')
    else:
        if 'disable' in local_status:
            msg = "\nThis CELL locking can't use, Please Call TE solve\n" \
                  "Fail info: {}".format(status.split(os.linesep)[0])
            log.info(msg)
            change_slot_status(container, 'ERROR', skip_error=False)
            raise lib.apexceptions.EquipmentFailure(msg)

    return


# -----------------------------------------------------------------
def step__clean_up():
    """ Main SEQ PASS update status
    :return (str): aplib.PASS/FAIL
    """
    if 'auto_pass' in lib.apdicts.userdict:
        slot = "{}-{}".format(int(lib.get_my_container_key().split('|')[-2][-2:]),
                              int(lib.get_my_container_key().split('|')[-1][-2:]))
        slot_status = lib.get_cached_data('slot_status')
        slot_info = slot_status[slot_index[slot]]
        uut_type = slot_info[0]
        if lib.apdicts.userdict['auto_pass']:
            status = '{}PASS{}'.format(uut_type, slot_info.split(':')[0][-1])
        else:
            status = '{}FAIL{}'.format(uut_type, slot_info.split(':')[0][-1])

        change_slot_status(slot, status)
    return


def read_slot_status(slot):
    """
    :param slot:
    :return:
    """
    slot_status_dir = r'/tftpboot/slot_status/'
    work_file = [f for f in os.listdir(slot_status_dir) if slot in f and '.sw' not in f][0]
    log.info('slot status is {}'.format(work_file))
    return work_file


# -----------------------------------------------------------------
# Container handling
#
def delay(start_delay, identifier):
    if start_delay != 0:
        print("{}: sleep {}".format(identifier, start_delay))
        time.sleep(start_delay)


def load_cli_cmd():
    """Return the default command if is not overwritten in a settings file
    This is created per request of the developers to try out our test suite on non supported Apollo boxes.
    """
    default = "python2.7 /opt/cisco/constellation/apollocli.py"

    folder = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(folder, "settings.ini")

    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(path))
        cli_cmd = config.get("settings", "cli_cmd")
        print("Custom cli_cmd: {}".format(cli_cmd))
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, IOError):
        cli_cmd = default

    return cli_cmd


def run_apollo_container(prod_line, area, test_station, container, start_delay=0, mode='DEBUG', timeout=1):
    """Run Apollo Container
    Backend start containers
    :param prod_line:
    :param area:
    :param test_station:
    :param container:
    :param start_delay:
    :param mode:
    :param timeout:
    :return:
    """
    cli_cmd = load_cli_cmd()
    # print(cli_cmd)

    delay(start_delay, container)

    call = '{cli_cmd} -pl "{prod_line}" --area "{area}" -ts "{test_station}" -cn "{container}" --log-level DEBUG ' \
           '--timeout {timeout} --m {mode}'.format(cli_cmd=cli_cmd, prod_line=prod_line, area=area,
                                                   test_station=test_station, container=container,
                                                   timeout=timeout, mode=mode)

    # print("{}: {}".format(container, call))
    call_split = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', call)

    subprocess.check_output(call_split)
    return
