"""
Process3
"""

# Python
# ------
import sys
import logging


# Apollo
# ------
from apollo.libs import lib as aplib

# BU Lib
# ------
from apollo.scripts.entsw.libs.mfg.process import Process as _Process
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Process Series3 Module"
__version__ = '1.0.0'
__author__ = ['qingywu']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

apollo_step = common_utils.apollo_step
func_details = common_utils.func_details
func_retry = common_utils.func_retry


class Process3(_Process):
    def __init__(self, mode_mgr, ud):
        super(Process3, self).__init__(mode_mgr, ud)

    # ------------------------------------------------------------------------------------------------------------------
    # Apollo Step methods
    # ------------------------------------------------------------------------------------------------------------------
    @apollo_step
    def add_tst_data_for_children(self, **kwargs):
        """ Add TST Data for Children (step)

        This step generates tst record for components in system (children). It covers PSU and and device shows up in
        PCAMAPS, which includes Uplink module, Data Stack cable, etc.

        PSU data is from diags.get_psu, saved in uut_config['psu_info'] in previous step.
        PCAMAP data includes device instance defined in uut_config['pcamap_items_for_tst'].

        :param kwargs:
        :return:
        """
        def _map_to_tst(data, keymap):
            # Input check
            if not isinstance(data, dict) or not isinstance(keymap, dict):
                raise Exception('Input error, data and keymap must be dicts')

            ret = {}
            for key, value in data.iteritems():
                if keymap.get(key) and value != '0':
                    ret[keymap.get(key)] = value if keymap.get(key) != 'eci' else int(value)

            return ret

        aplib.set_container_text('ADD TST DATA')
        log.info('STEP: Add TST Data For Children.')

        # Input processing
        major_line_id = self._ud.uut_config.get('major_line_id', 0)
        backflush_status = kwargs.get('backflush_status', self._ud.uut_config.get('backflush_status', 'NO'))
        pcamap_to_tst_keymap = self._ud.uut_config.get('pcamap_to_tst_keymap', {})
        psu_to_tst_keymap = self._ud.uut_config.get('psu_to_tst_keymap', {})
        pcamap_dev_list = self._ud.uut_config.get('pcamap_items_for_tst', [])
        pcamaps = self._ud.uut_config.get('pcamaps', {})
        if not pcamap_to_tst_keymap or not psu_to_tst_keymap or not pcamap_dev_list:
            log.error('Required Input missing')
            log.error('Make sure pcamap_to_tst_keymap, psu_to_tst_keymap, pcamap_dev_list are '
                      'all defined in product definition')
            return aplib.FAIL
        if not pcamaps:
            log.error('PCAMAPS is missing in uut_config')
            log.error('Make sure pcamaps is populated before this step')
            return aplib.FAIL

        # PSU data
        psu_data = self._ud.uut_config.get('psu_info', {}).values()

        # PCAMAP data
        pcamap_data = [value for key, value in pcamaps.iteritems() if key in pcamap_dev_list]

        # Generate add_tst_data dict and add tst data
        for item in psu_data:
            tst_dict = _map_to_tst(data=item, keymap=psu_to_tst_keymap)
            if tst_dict:
                tst_dict['lineid'] = major_line_id
                tst_dict['backflush_status'] = backflush_status
                log.info('Add tst data for {0}'.format(tst_dict))
                aplib.add_tst_data(**tst_dict)
        for item in pcamap_data:
            tst_dict = _map_to_tst(data=item, keymap=pcamap_to_tst_keymap)
            if tst_dict:
                tst_dict['lineid'] = major_line_id
                tst_dict['backflush_status'] = backflush_status
                log.info('Add tst data for {0}'.format(tst_dict))
                aplib.add_tst_data(**tst_dict)

        return aplib.PASS
