"""
CITP Presequnce Module
"""
from apollo.libs import lib
import logging
import uuid

log = logging.getLogger(__name__)


# PreSequences
# ------------------------------------------------------------
def single_pid_sequence_definition():
    """ Single PID: Stand-alone container
    :return:
    """
    seq = {
        'name': 'Run a single pid on a single container',
        'steps': [{'name': 'pre_test', 'codepath': __name__, 'function': 'run_single_pid'}]
    }
    return seq


def super_single_pid_sequence_definition():
    """Single PID: Child container
    :return:
    """
    seq = {
        'name': 'Run a single pid on all child containers',
        'steps': [{'name': 'pre_test', 'codepath': __name__, 'function': 'super_run_single_pid'}]
    }
    return seq


# Steps
# ------------------------------------------------------------
def run_single_pid():
    """ Run Single PID
    :return:
    """
    log.debug("Run single PID in pre-sequence used to automatically start a single container.")
    info = lib.get_pre_sequence_info()
    areas = info.areas

    if len(areas) != 1:
        return lib.FAIL, "Only a single area can be handled by the pre-sequence 'run_single_pid'."

    containers = info.containers

    if len(containers) != 1:
        return lib.FAIL, "Only a single container can be handled by the pre-sequence 'run_single_pid'."

    area = areas[0]
    pids = info.pids_by_area(area)

    log.debug('areas: {}'.format(areas))
    log.debug('PIDS: {}'.format(pids))
    log.debug('containers: {}'.format(containers))

    if len(pids) == 0:
        return lib.FAIL, "There is no PID assigned to this container."

    if len(pids) != 1:
        return lib.FAIL, "Only a single PID can be handled by the pre-sequence 'run_single_pid'."

    # All is well let us kick this off
    container = containers[0]
    pid = pids[0]
    serial_number = str(uuid.uuid4().fields[-1])[:11]
    log.debug("Pre-sequence single_pid: serial_number={0}, container={1}, uuttype={2}".format(serial_number, container, pid))
    lib.add_tst_data(serial_number=serial_number, test_container=container, uut_type=pid, test_area=area)
    return lib.PASS


def super_run_single_pid():
    """ Run Single PID (Super container control)
    :return:
    """
    log.debug("Super run single PID in pre-sequence used to automatically start all child containers of a super container.")
    info = lib.get_pre_sequence_info()
    areas = info.areas

    if len(areas) != 1:
        return lib.FAIL, "Only a single area can be handled by the pre-sequence 'super_run_single_pid'."

    containers = info.containers
    area = areas[0]
    pids = info.pids_by_area(area)

    log.debug('areas: {}'.format(areas))
    log.debug('PIDS: {}'.format(pids))
    log.debug('containers: {}'.format(containers))

    if len(pids) == 0:
        return lib.FAIL, "There is no PID assigned to this container."

    if len(pids) != 1:
        return lib.FAIL, "Only a single PID can be handled by the pre-sequence 'super_run_single_pid'."

    # All is well let us kick this off
    pid = pids[0]
    for index, container in enumerate(containers):
        serial_number = str(uuid.uuid4().fields[-1])[:11]
        log.debug("Pre-sequence super_single_pid {0}: serial_number={1}, container={2}, uuttype={3}".format(index, serial_number, container, pid))
        lib.add_tst_data(serial_number=serial_number, test_container=container, uut_type=pid, test_area=area)
    return lib.PASS
