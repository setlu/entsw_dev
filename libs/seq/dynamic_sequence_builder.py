""" Dynamic Sequence Builder
========================================================================================================================

This module is used to build sub-sequences dynamically.
The steps are derived from the product definitions.

Support sub-sequences:
    1. Diagnostics test list
    2. Traffic test cases

NOTE: This is dependent on the global cache for UUT Descriptor set in PRE-SEQ.


APOLLO STEP PARAMS (reference)
Supported keywords: 
* (str|dict|StepDefinition|FunctionType) step: 
* str name: name to assign to this step/sequence, as displayed by the UI. 
* str module_name: dot or slash delimited import path to module containing the step function. 
* (str|FunctionType) function: name of function within our module path, or function instance./ref. 
* tuple args: arguments to pass as-is to our step function. 
* dict kwargs: keyword arguments to pass as-is to our step function. 
* bool enabled: If true, the step is executed by the sequencer. Default is True. 
* int group_level: Integer used to group steps together. Used by adaptive test algorithms. 
* str jump_on_branch: step name to execute next if step result is BRANCH 
* str jump_on_error: step name to execute next if step resut is FAIL 
* int loop_on_error: Number of times to repeat this step if initial result is FAIL. This does NOT change the final result. 
* (tuple|Iteration) iterations: Iteration instance, or tuple of (type, value) that defines looping logic for this step, either quantity of loops or loop for a duration of time. 
* str precondition: A python string that specifies a pre-condition to determine if we run the step. 
* bool stop_on_error: If True, sequence execution branches to a finalization step if defined, and then exists if the result of this step is FAIL. Default is True. 
* bool telcordia_retry: If True, the step will loop up to three times if the first result is FAIL. If the next three results are PASS, the final step result will be PASS. Default is False. 
* bool initialization: If True, this is the first step executed by this sequence. Only one step per sequence can have this enabled. Default is False. 
* bool finalization: If True, this is the last step executed by this sequence even if a previous step fails. Only one step per sequence can have this enabled. Default is False. 
* list adt_enabled: ADT algorithms that should be applied.

========================================================================================================================
"""

# Python
# ------
import logging
from collections import OrderedDict


__title__ = "Dynamic Sequence Builder"
__version__ = '2.0.0'

log = logging.getLogger(__name__)


def build_diag_testlist_subseq(diag_seq, container, udd, step_module, category=None, enabled=True):
    """ Build Diags TestList SubSequence Dynamically
    NOTE: When Apollo builds this, the seq param MUST be a "clean" subseq (i.e. new with no other steps attached.)
    :param (obj) diag_seq: From the main sequence
    :param (str) container: Full container path (REQUIRED as unique!)
    :param (dict) udd: UUT Descriptor in Dict form
    :param (obj) step_module: Object pointer to step file module that contains the functions to run.
    :param (int|str|None) category: If used, it MUST match the product definition diag testlist test item entry.
    :param (bool) enabled: Build if True
    :return:
    """
    if not enabled:
        log.debug("Dynamic Diag Testlist NOT enabled.")
        return diag_seq

    area = container.split('|')[1]

    # Diag Testlist build-out
    diag_tests = OrderedDict(udd.get('uut_config', {}).get('diag_tests', []))
    if not diag_tests:
        log.warning("Nothing in the Diags Testlist.")
        return diag_seq


    for test_name in diag_tests:
        diag_test_areas = diag_tests[test_name].get('areas', [])
        diag_test_category = diag_tests[test_name].get('category', None)
        if diag_tests[test_name].get('enabled', True) and (area in diag_test_areas or 'ALL' in diag_test_areas) and (category == diag_test_category):

            # Get function and function args
            fname = diag_tests[test_name].get('func', None)
            if fname:
                func = getattr(step_module, fname) if hasattr(step_module, fname) else None
                func_args = diag_tests[test_name].get('func_args', {})
            else:
                func = step_module.diags_run_testlist_item
                func_args = {}

            # Set name prefix
            name_prefix = 'DIAG TEST' if 'UTIL' not in str(category) else 'DIAG UTIL'

            # Create the step
            if func:
                kwargs = {'test_name': test_name,
                          'timeout': diag_tests[test_name].get('timeout', 300),
                          'args': diag_tests[test_name].get('args', None)}
                kwargs.update(func_args)
                diag_seq.add_step(func,
                                  name='{0} {1}'.format(name_prefix, test_name),
                                  adt_enabled=diag_tests[test_name].get('adt_enabled', False),
                                  telcordia_retry=diag_tests[test_name].get('telcordia_retry', False),
                                  kwargs=kwargs)
                log.debug("{0} added ({1} {2} {3} {4}).".format(test_name, fname, func, diag_test_category, diag_test_areas))
            else:
                log.error("Problem with adding diag step function: {0} ({1})".format(fname, func))
        else:
            log.debug("{0} NOT added ({1} {2}).".format(test_name, diag_test_category, diag_test_areas))


def build_traffic_cases_subseq(traffic_seq, container, udd, step_module, category=None, enabled=True):
    """ Build Traffic Cases SubSequence Dynamically
    NOTE: When Apollo builds this, the seq param MUST be a "clean" seq (i.e. new with no other steps attached.)
    :param (obj) traffic_seq: From the main sequence
    :param (str) container: Full container path (REQUIRED as unique!)
    :param (dict) udd: UUT Descriptor in Dict form
    :param (obj) step_module: Object pointer to step file module that contains the functions to run.
    :param (int|str|None) category: If used, it MUST match the product definition tarffic case item entry.
    :param (bool) enabled: Build if True
    :return:
    """
    if not enabled:
        log.debug("Dynamic Traffic Cases NOT enabled.")
        return traffic_seq

    area = container.split('|')[1]

    # Traffic Cases build-out
    traffic_cases = OrderedDict(udd.get('uut_config', {}).get('traffic_cases', []))
    if not traffic_cases:
        log.warning("Nothing in the Traffic Cases.")
        return traffic_seq

    for case in sorted(traffic_cases):
        traf_case_source = traffic_cases[case].get('source', 'fmdiags')
        traf_case_areas = traffic_cases[case].get('areas', [])
        traf_case_category = traffic_cases[case].get('category', None)
        if traffic_cases[case].get('enabled', True) and (area in traf_case_areas or 'ALL' in traf_case_areas) and (category == traf_case_category):

            fname = traffic_cases[case].get('func', None)
            if fname:
                func = getattr(step_module, fname) if hasattr(step_module, fname) else None
            else:
                if traf_case_source == 'fmdiags':
                    func = step_module.traffic_fmdiags_traffic_test
                elif traf_case_source == 'fmgenerator':
                    func = step_module.traffic_fmgenerator_traffic_test
                else:
                    func = None
            if func:
                traffic_seq.add_step(func,
                                     name='{0}'.format(case),
                                     adt_enabled=traffic_cases[case].get('adt_enabled', False),
                                     telcordia_retry=traffic_cases[case].get('telcordia_retry', False),
                                     kwargs={'action': 'run',
                                             'traffic_cases': [case]})
                log.debug("{0} added ({1} {2}).".format(case, traf_case_category, traf_case_areas))
            else:
                log.error("Problem with adding traffic step function: {0} ({1})".format(fname, func))
        else:
            log.debug("{0} NOT added ({1} {2}).".format(case, traf_case_category, traf_case_areas))

    return traffic_seq
