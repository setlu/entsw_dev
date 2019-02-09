""" CNF Utility Module
========================================================================================================================

This module contains various utilities and support functions to process and verify customer configurations

IMPORTANT: All functions must NOT interact with UUT through connection, strictly data process and manipulation.

========================================================================================================================
"""
# Python
# ------
import sys
import logging

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Configuration Module"
__version__ = '0.8.2'
__author__ = 'qingywu'

log = logging.getLogger(__name__)
func_details = common_utils.func_details
func_retry = common_utils.func_retry
thismodule = sys.modules[__name__]

# ======================================================================================================================
# Sub-Assembly list
#   This dict contains all PIDs that are installed in DF assembly process, and need to be verified in SYSFT.
#   The key is PID that shows up in line ID, value is actual hardware PID and hardware type (PSU, DSC, NM, etc).
#
#   This dict should not be access outside of this module
# ======================================================================================================================
_sub_assemblies = {
    # PSUs, -P for 80+ platinum
    'PWR-C1-1100WAC': {'pid': 'PWR-C1-1100WAC', 'type': 'PSU'},
    'PWR-C1-1100WAC/2': {'pid': 'PWR-C1-1100WAC', 'type': 'PSU'},
    'PWR-C1-1100WAC-P': {'pid': 'PWR-C1-1100WAC-P', 'type': 'PSU'},
    'PWR-C1-1100WAC-P/2': {'pid': 'PWR-C1-1100WAC-P', 'type': 'PSU'},
    'PWR-C1-350WAC': {'pid': 'PWR-C1-350WAC', 'type': 'PSU'},
    'PWR-C1-350WAC/2': {'pid': 'PWR-C1-350WAC', 'type': 'PSU'},
    'PWR-C1-350WAC-P': {'pid': 'PWR-C1-350WAC', 'type': 'PSU'},
    'PWR-C1-350WAC-P/2': {'pid': 'PWR-C1-350WAC', 'type': 'PSU'},
    'PWR-C1-715WAC': {'pid': 'PWR-C1-715WAC', 'type': 'PSU'},
    'PWR-C1-715WAC/2': {'pid': 'PWR-C1-715WAC', 'type': 'PSU'},
    'PWR-C1-715WAC-P': {'pid': 'PWR-C1-715WAC', 'type': 'PSU'},
    'PWR-C1-715WAC-P/2': {'pid': 'PWR-C1-715WAC', 'type': 'PSU'},
    'PWR-C1-715WDC': {'pid': 'PWR-C1-715WDC', 'type': 'PSU'},
    'PWR-C1-715WDC/2': {'pid': 'PWR-C1-715WDC', 'type': 'PSU'},
    'PWR-C1-440WDC': {'pid': 'PWR-C1-440WDC', 'type': 'PSU'},
    'PWR-C1-440WDC/2': {'pid': 'PWR-C1-440WDC', 'type': 'PSU'},
    'PWR-C4-950WAC-R': {'pid': 'PWR-C4-950WAC-R', 'type': 'PSU'},
    'PWR-C4-950WAC-R/2': {'pid': 'PWR-C4-950WAC-R', 'type': 'PSU'},

    # Data Stack Cables
    'STACK-T1-50CM': {'pid': 'STACK-T1-50CM', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},
    'STACK-T1-1M': {'pid': 'STACK-T1-1M', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},
    'STACK-T1-3M': {'pid': 'STACK-T1-3M', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},
    # TODO: need to confirm auth_mod for 3 new stack cable below
    'STACK-T3-50CM': {'pid': 'STACK-T1-50CM', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},
    'STACK-T3-1M': {'pid': 'STACK-T1-1M', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},
    'STACK-T3-3M': {'pid': 'STACK-T1-3M', 'type': 'DSC', 'auth_mod': ['Stack Cable A', 'Stack Cable B']},

    # Uplink Network Modules
    'C3850-NM-2-10G': {'pid': 'C3850-NM-2-10G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C3850-NM-2-40G': {'pid': 'C3850-NM-2-40G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C3850-NM-4-10G': {'pid': 'C3850-NM-4-10G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C3850-NM-4-1G': {'pid': 'C3850-NM-4-1G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C3850-NM-8-10G': {'pid': 'C3850-NM-8-10G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9300-NM-2Q': {'pid': 'C9300-NM-2Q', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9300-NM-2Y': {'pid': 'C9300-NM-2Y', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9300-NM-4G': {'pid': 'C9300-NM-4G', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9300-NM-4M': {'pid': 'C9300-NM-4M', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9300-NM-8X': {'pid': 'C9300-NM-8X', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9500-NM-2Q': {'pid': 'C9500-NM-2Q', 'type': 'NM', 'auth_mod': 'FRU'},
    'C9500-NM-8X': {'pid': 'C9500-NM-8X', 'type': 'NM', 'auth_mod': 'FRU'},
}


# ======================================================================================================================
# Utility functions
# ======================================================================================================================
@func_details
def get_cnf_pid_info(uut_type=None):
    """ Get CNF PID Info
    This func provide a wrapper to access _sub_assemblies without the risk of modifying it
    :param (str) uut_type: PID in line_id          ex: 'C9500-NM-8X'
    :return(dict): CNF info related to input PID   ex: {'pid': 'C9500-NM-8X', 'type': 'NM', 'auth_mod': 'FRU'}
    """
    return dict(_sub_assemblies.get(uut_type, {}))


@func_details
def get_config_to_check(major_line_id_cfg=None):
    """ Get customer configurations for config check
    This function takes major_line_id_cfg as input. Returns a processed/standardized dict for config
    check in later test process. Use major_line_id_cfg as input to avoid cesium service call.
    :param (list) major_line_id_cfg: config_data from cesiumlib.get_lineid_config()
                                     ex: [{u'lineid': 1027402446, u'level': 0, u'ob_trans_id': 407857584, u'atlinenum': 0, u'qty': 1, u'linenum': 0, u'parent_lineid': 1027402446, u'prod_name': u'C9300-48U-A'},
                                          {u'lineid': 1027402486, u'level': 1, u'ob_trans_id': 407857596, u'atlinenum': 1, u'qty': 1, u'linenum': 18, u'parent_lineid': 1027402446, u'prod_name': u'C1A1TCAT93002'},
                                          {u'lineid': 1027402488, u'level': 1, u'ob_trans_id': 407857585, u'atlinenum': 6, u'qty': 1, u'linenum': 24, u'parent_lineid': 1027402446, u'prod_name': u'C1AA1TCAT93001'},
                                          {u'lineid': 1027402577, u'level': 1, u'ob_trans_id': 407857607, u'atlinenum': 10, u'qty': 1, u'linenum': 6, u'parent_lineid': 1027402446, u'prod_name': u'PWR-C1-1100WAC'},
                                          {u'lineid': 1027402578, u'level': 1, u'ob_trans_id': 407857608, u'atlinenum': 11, u'qty': 1, u'linenum': 8, u'parent_lineid': 1027402446, u'prod_name': u'PWR-C1-1100WAC/2'},
                                          {u'lineid': 1027402579, u'level': 1, u'ob_trans_id': 407857609, u'atlinenum': 12, u'qty': 1, u'linenum': 2, u'parent_lineid': 1027402446, u'prod_name': u'C9300-NW-A-48'},
                                          {u'boot_image': None, u'flashchksum': None, u'cco_location': u'/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES', u'qty': 1, u'group_id': None, u'dos_name': None,
                                           u'image_version': u'16.8.1a', u'image_type': None, u'config': None, u'prod_name': u'S9300UK9-168', u'var5': None, u'var4': None, u'var1': None, u'imagesize': 667244461,
                                           u'var3': None, u'var2': None, u'ob_trans_id': 407857610, u'image_name': u'cat9k_iosxe.16.08.01a.SPA.bin', u'atlinenum': 13, u'image_id': 103872, u'product_label': None,
                                           u'cco_check': u'Y', u'md5': u'5a7ebf6cfc15b83125819b13feec25a9', u'lineid': 1027402580, u'product_id': u'S9300UK9-168', u'linenum': 4, u'level': 1,
                                           u'parent_lineid': 1027402446, u'initiated_version': u'16.8.1a'},
                                          {u'lineid': 1027402581, u'level': 1, u'ob_trans_id': 407857611, u'atlinenum': 14, u'qty': 2, u'linenum': 10, u'parent_lineid': 1027402446, u'prod_name': u'CAB-TA-NA'},
                                          {u'lineid': 1027402582, u'level': 1, u'ob_trans_id': 407857612, u'atlinenum': 15, u'qty': 1, u'linenum': 12, u'parent_lineid': 1027402446, u'prod_name': u'STACK-T1-50CM'},
                                          {u'lineid': 1027402583, u'level': 1, u'ob_trans_id': 407857598, u'atlinenum': 16, u'qty': 1, u'linenum': 14, u'parent_lineid': 1027402446, u'prod_name': u'CAB-SPWR-30CM'},
                                          {u'lineid': 1027402584, u'level': 1, u'ob_trans_id': 407857599, u'atlinenum': 17, u'qty': 1, u'linenum': 16, u'parent_lineid': 1027402446, u'prod_name': u'C9300-NM-8X'},
                                          {u'lineid': 1027402585, u'level': 2, u'ob_trans_id': 407857600, u'atlinenum': 2, u'qty': 1, u'linenum': 20, u'parent_lineid': 1027402486, u'prod_name': u'C1-C9300-48-DNAA-T'},
                                          {u'lineid': 1027402586, u'level': 2, u'ob_trans_id': 407857601, u'atlinenum': 3, u'qty': 25, u'linenum': 21, u'parent_lineid': 1027402486, u'prod_name': u'C1-SWATCH-T'},
                                          {u'lineid': 1027402587, u'level': 2, u'ob_trans_id': 407857602, u'atlinenum': 4, u'qty': 25, u'linenum': 22, u'parent_lineid': 1027402486, u'prod_name': u'C1-ISE-PLS-T'},
                                          {u'lineid': 1027402588, u'level': 2, u'ob_trans_id': 407857603, u'atlinenum': 5, u'qty': 25, u'linenum': 23, u'parent_lineid': 1027402486, u'prod_name': u'C1-ISE-BASE-T'},
                                          {u'lineid': 1027402589, u'level': 2, u'ob_trans_id': 407857604, u'atlinenum': 7, u'qty': 25, u'linenum': 26, u'parent_lineid': 1027402488, u'prod_name': u'C1-SWATCH-T'},
                                          {u'lineid': 1027402590, u'level': 2, u'ob_trans_id': 407857605, u'atlinenum': 8, u'qty': 25, u'linenum': 27, u'parent_lineid': 1027402488, u'prod_name': u'C1-ISE-PLS-T'},
                                          {u'lineid': 1027402591, u'level': 2, u'ob_trans_id': 407857606, u'atlinenum': 9, u'qty': 25, u'linenum': 28, u'parent_lineid': 1027402488, u'prod_name': u'C1-ISE-BASE-T'}]
    :return (dict) order_config: Standardized dict contains ordered components and quantities
                                 ex: {'PWR-C1-1100WAC': 2, 'C9300-NM-8X': 1, 'STACK-T1-50CM': 1}
    """
    if not major_line_id_cfg or not isinstance(major_line_id_cfg, list):
        log.warning('Invalid configuration input: {0}'.format(major_line_id_cfg))
        return None

    order_config = {}
    for item in major_line_id_cfg:
        uut_type = get_cnf_pid_info(item.get('prod_name'))
        uut_type = uut_type.get('pid') if uut_type else uut_type
        qty = item.get('qty')
        if uut_type and qty:
            order_config[uut_type] = order_config.get(uut_type, 0) + qty

    log.info('order_config: {0}'.format(order_config))

    return order_config


def parse_component_config(components_info=None, component_uut_type_keys=None, component_sn_keys=None):
    """ Get Configuration from Input info

    This function parses components_info values to get installed components and returns a standardized dict with config info.
    components_info could come from stardust_driver.get_psu(), or from PCAMAP, it must be a dict that contains component information.


    :param (dict) components_info: pcamaps from uut_config, this information should be prepared in previous steps and available in uut_config by now.
                                   Or PSU info from stardust, stardust_driver.get_psu()
                        ex:
                                {
                                    '2': {'pid': 'STACK-T1-50CM', 'bid': 8001, 'vid': 'V01', 'sn': 'MOC2026A5GJ', 'vpn': '800-40403-01', 'pcapn': 0, 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0},
                                    '3': {'pid': 'STACK-T1-50CM', 'bid': 8001, 'vid': 'V01', 'sn': 'MOC2026A5GJ', 'vpn': '800-40403-01', 'pcapn': 0, 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0},
                                    '1': {'pid': 'C3K80-NM-HILBERT', 'bid': 'f001', 'vid': 'P2', 'sn': 'FOC15461WAR', 'vpn': '73-14102-02', 'pcapn': '0x13', 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0}
                                }
                        ex:     {
                                    'A': {
                                        'PS Check-code base': '0x35',
                                        'I_in': '0xE006',
                                        'P_in': '0x081F',
                                        'PS VID': 'V02',
                                        'PS TAN': '341-0562-02',
                                        'T_spot': '0x0027',
                                        'V_in': '0xF999',
                                        'PS SN': 'LIT214525AG',
                                        'PS CLEI': 'IPUPAJZAAB',
                                        'Status Temp': '0x00',
                                        'Power Class': '350W (0x40)',
                                        'PS Power Class': '350W',
                                        'PS Fan Curve Coef.': '0x60 0x90 0x8A 0xB4',
                                        'I_out': '0xE00F',
                                        'Hardware status': '0x03( Present - Power Good - )',
                                        'V_out Mode': '0x1C',
                                        'V_out': '0x0380',
                                        'T_out': '0x0027',
                                        'T_in': '0x0024',
                                        'PS TAN Rev': 'A0',
                                        'Status Word': '0x0000',
                                        'PS Vendor Name': 'LITE-ON',
                                        'P_out': '0x081C',
                                        'Status Fan': '0x00',
                                        'PS PID': 'PWR-C1-350WAC'
                                    },
                                    'B': {}
                                }
    :param (list) component_uut_type_keys: Possible keys in components_info that contains uut_type info
    :param (list) component_sn_keys: Possible keys in components_info that contains serial number info
    :return (dict) pcamap_config: Standardized configuration dict
                                  ex:     {'STACK-T1-50CM': 1, 'C3K80-NM-HILBERT': 1}
                                  ex:     {'PWR-C1-350WAC': 1}
    """
    # Process input
    if not isinstance(components_info, dict):
        log.warning('Invalid components info input: {0}, it must be a dict.'.format(components_info))
        return None
    if not component_uut_type_keys or not component_sn_keys:
        log.warning('Params component_uut_type_keys [{0}] or component_sn_keys [{1}] is invalid'.format(component_uut_type_keys, component_sn_keys))
        log.warning('Both params must not be blank')
        return None

    components_config = {}

    component_sn_list = []

    for component in components_info.values():
        pid = None
        sernum = None
        for pid_key in component_uut_type_keys:
            if pid_key in component.keys():
                pid = component.get(pid_key)
        for sn_key in component_sn_keys:
            if sn_key in component.keys():
                sernum = component.get(sn_key)
        if pid and sernum and sernum not in component_sn_list:
            log.info('Found component {0}'.format(sernum))
            component_sn_list.append(sernum)
            components_config[pid] = components_config.get(pid, 0) + 1

    return components_config
