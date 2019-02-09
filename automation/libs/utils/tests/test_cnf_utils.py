import logging
import pytest

import apollo.scripts.entsw.libs.utils.cnf_utils as cnf_utils
import apollo.scripts.entsw.libs.opsys.ios as ios

__title__ = 'EntSw CNF Utils Unit Tests'
__author__ = ['bborel', 'qingywu']
__version__ = '0.2.0'

log = logging.getLogger(__name__)


class TestCnfUtils(object):

    # TODO: move to individual sections within the libs
    #
    # cnf_utils
    #
    def test_cnf_utils_get_config_to_check(self):
        config_input1 = [
            {u'lineid': 1030645642, u'level': 0, u'ob_trans_id': 414559404, u'atlinenum': 0, u'qty': 1, u'linenum': 0, u'parent_lineid': 1030645642, u'prod_name': u'C9300-48U-A'},
            {u'lineid': 1030645821, u'level': 1, u'ob_trans_id': 414559412, u'atlinenum': 1, u'qty': 1, u'linenum': 8, u'parent_lineid': 1030645642, u'prod_name': u'PWR-C1-1100WAC'},
            {u'lineid': 1030645823, u'level': 1, u'ob_trans_id': 414559413, u'atlinenum': 2, u'qty': 1, u'linenum': 10, u'parent_lineid': 1030645642, u'prod_name': u'PWR-C1-1100WAC/2'},
            {u'lineid': 1030645825, u'level': 1, u'ob_trans_id': 414559414, u'atlinenum': 3, u'qty': 1, u'linenum': 2, u'parent_lineid': 1030645642, u'prod_name': u'C9300-NW-A-48'},
            {u'lineid': 1030645827, u'level': 1, u'ob_trans_id': 414559415, u'atlinenum': 4, u'qty': 1, u'linenum': 4, u'parent_lineid': 1030645642, u'prod_name': u'C9300-DNA-A-48'},
            {u'boot_image': None, u'flashchksum': None, u'cco_location': u'/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES', u'qty': 1, u'group_id': None,
             u'dos_name': None, u'image_version': u'16.8.1a', u'image_type': None, u'config': None, u'prod_name': u'S9300UK9-168', u'var5': None, u'var4': None,
             u'var1': None, u'imagesize': 667244461, u'var3': None, u'var2': None, u'ob_trans_id': 414559416, u'image_name': u'cat9k_iosxe.16.08.01a.SPA.bin',
             u'atlinenum': 5, u'image_id': 103872, u'product_label': None, u'cco_check': u'Y', u'md5': u'5a7ebf6cfc15b83125819b13feec25a9',
             u'lineid': 1030645830, u'product_id': u'S9300UK9-168', u'linenum': 6, u'level': 1, u'parent_lineid': 1030645642, u'initiated_version': u'16.8.1a'},
            {u'lineid': 1030645832, u'level': 1, u'ob_trans_id': 414559406, u'atlinenum': 6, u'qty': 2, u'linenum': 12, u'parent_lineid': 1030645642, u'prod_name': u'CAB-TA-NA'},
            {u'lineid': 1030645834, u'level': 1, u'ob_trans_id': 414559407, u'atlinenum': 7, u'qty': 1, u'linenum': 14, u'parent_lineid': 1030645642, u'prod_name': u'STACK-T1-50CM'},
            {u'lineid': 1030645836, u'level': 1, u'ob_trans_id': 414559408, u'atlinenum': 8, u'qty': 1, u'linenum': 16, u'parent_lineid': 1030645642, u'prod_name': u'C9300-SPWR-NONE'},
            {u'lineid': 1030645838, u'level': 1, u'ob_trans_id': 414559409, u'atlinenum': 9, u'qty': 1, u'linenum': 18, u'parent_lineid': 1030645642, u'prod_name': u'NM-BLANK-T1'},
            {u'lineid': 1030645840, u'level': 1, u'ob_trans_id': 414559410, u'atlinenum': 10, u'qty': 1, u'linenum': 20, u'parent_lineid': 1030645642, u'prod_name': u'C9300-NM-NONE'},
            {u'lineid': 1030645841, u'level': 1, u'ob_trans_id': 414559405, u'atlinenum': 11, u'qty': 1, u'linenum': 22, u'parent_lineid': 1030645642, u'prod_name': u'C1-ADD-OPTOUT'}]
        config_output1 = {'PWR-C1-1100WAC': 2, 'STACK-T1-50CM': 1}
        config_input2 = [
            {u'lineid': 1027402446, u'level': 0, u'ob_trans_id': 407857584, u'atlinenum': 0, u'qty': 1, u'linenum': 0, u'parent_lineid': 1027402446, u'prod_name': u'C9300-48U-A'},
            {u'lineid': 1027402486, u'level': 1, u'ob_trans_id': 407857596, u'atlinenum': 1, u'qty': 1, u'linenum': 18, u'parent_lineid': 1027402446, u'prod_name': u'C1A1TCAT93002'},
            {u'lineid': 1027402488, u'level': 1, u'ob_trans_id': 407857585, u'atlinenum': 6, u'qty': 1, u'linenum': 24, u'parent_lineid': 1027402446, u'prod_name': u'C1AA1TCAT93001'},
            {u'lineid': 1027402577, u'level': 1, u'ob_trans_id': 407857607, u'atlinenum': 10, u'qty': 1, u'linenum': 6, u'parent_lineid': 1027402446, u'prod_name': u'PWR-C1-1100WAC'},
            {u'lineid': 1027402578, u'level': 1, u'ob_trans_id': 407857608, u'atlinenum': 11, u'qty': 1, u'linenum': 8, u'parent_lineid': 1027402446, u'prod_name': u'PWR-C1-1100WAC/2'},
            {u'lineid': 1027402579, u'level': 1, u'ob_trans_id': 407857609, u'atlinenum': 12, u'qty': 1, u'linenum': 2, u'parent_lineid': 1027402446, u'prod_name': u'C9300-NW-A-48'},
            {u'boot_image': None, u'flashchksum': None, u'cco_location': u'/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES', u'qty': 1, u'group_id': None,
             u'dos_name': None, u'image_version': u'16.8.1a', u'image_type': None, u'config': None, u'prod_name': u'S9300UK9-168', u'var5': None, u'var4': None,
             u'var1': None, u'imagesize': 667244461, u'var3': None, u'var2': None, u'ob_trans_id': 407857610, u'image_name': u'cat9k_iosxe.16.08.01a.SPA.bin',
             u'atlinenum': 13, u'image_id': 103872, u'product_label': None, u'cco_check': u'Y', u'md5': u'5a7ebf6cfc15b83125819b13feec25a9',
             u'lineid': 1027402580, u'product_id': u'S9300UK9-168', u'linenum': 4, u'level': 1, u'parent_lineid': 1027402446, u'initiated_version': u'16.8.1a'},
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
        config_output2 = {'PWR-C1-1100WAC': 2, 'C9300-NM-8X': 1, 'STACK-T1-50CM': 1}
        config_input3 = [
            {u'lineid': 1027558388, u'level': 0, u'ob_trans_id': 407245582, u'atlinenum': 0, u'qty': 1, u'linenum': 0, u'parent_lineid': 1027558388, u'prod_name': u'C9300-24P-1E'},
            {u'lineid': 1027558416, u'level': 1, u'ob_trans_id': 407245593, u'atlinenum': 1, u'qty': 1, u'linenum': 19, u'parent_lineid': 1027558388, u'prod_name': u'PWR-C1-715WAC'},
            {u'lineid': 1027558417, u'level': 1, u'ob_trans_id': 407245583, u'atlinenum': 2, u'qty': 1, u'linenum': 21, u'parent_lineid': 1027558388, u'prod_name': u'C9300-SPS-NONE'},
            {u'lineid': 1027558418, u'level': 1, u'ob_trans_id': 407245584, u'atlinenum': 3, u'qty': 1, u'linenum': 13, u'parent_lineid': 1027558388, u'prod_name': u'C9300-NW-1E-24'},
            {u'lineid': 1027558419, u'level': 1, u'ob_trans_id': 407245585, u'atlinenum': 4, u'qty': 1, u'linenum': 11, u'parent_lineid': 1027558388, u'prod_name': u'C9300-DNA-1E-24'},
            {u'boot_image': None, u'flashchksum': None, u'cco_location': u'/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES', u'qty': 1, u'group_id': None,
             u'dos_name': None, u'image_version': u'16.8.1a', u'image_type': None, u'config': None, u'prod_name': u'S9300UK9-168', u'var5': None, u'var4': None,
             u'var1': None, u'imagesize': 667244461, u'var3': None, u'var2': None, u'ob_trans_id': 407245586, u'image_name': u'cat9k_iosxe.16.08.01a.SPA.bin',
             u'atlinenum': 5, u'image_id': 103872, u'product_label': None, u'cco_check': u'Y', u'md5': u'5a7ebf6cfc15b83125819b13feec25a9',
             u'lineid': 1027558420, u'product_id': u'S9300UK9-168', u'linenum': 5, u'level': 1, u'parent_lineid': 1027558388, u'initiated_version': u'16.8.1a'},
            {u'lineid': 1027558421, u'level': 1, u'ob_trans_id': 407245587, u'atlinenum': 6, u'qty': 1, u'linenum': 9, u'parent_lineid': 1027558388, u'prod_name': u'CAB-TA-NA'},
            {u'lineid': 1027558422, u'level': 1, u'ob_trans_id': 407245588, u'atlinenum': 7, u'qty': 1, u'linenum': 17, u'parent_lineid': 1027558388, u'prod_name': u'C9300-STACK-NONE'},
            {u'lineid': 1027558423, u'level': 1, u'ob_trans_id': 407245589, u'atlinenum': 8, u'qty': 1, u'linenum': 15, u'parent_lineid': 1027558388, u'prod_name': u'C9300-SPWR-NONE'},
            {u'lineid': 1027558424, u'level': 1, u'ob_trans_id': 407245590, u'atlinenum': 9, u'qty': 1, u'linenum': 2, u'parent_lineid': 1027558388, u'prod_name': u'PWR-C1-BLANK'},
            {u'lineid': 1027558425, u'level': 1, u'ob_trans_id': 407245591, u'atlinenum': 10, u'qty': 1, u'linenum': 3, u'parent_lineid': 1027558388, u'prod_name': u'NM-BLANK-T1'},
            {u'lineid': 1027558426, u'level': 1, u'ob_trans_id': 407245592, u'atlinenum': 11, u'qty': 1, u'linenum': 7, u'parent_lineid': 1027558388, u'prod_name': u'C9300-NM-NONE'}]
        config_output3 = {'PWR-C1-715WAC': 1}
        invalid_input1 = [
            {u'lineid': 1027558388, u'level': 0, u'ob_trans_id': 407245582, u'atlinenum': 0, u'qty': 1, u'linenum': 0, u'parent_lineid': 1027558388, u'prod_name': u'C9300-24P-1E'},
            {u'lineid': 1027558417, u'level': 1, u'ob_trans_id': 407245583, u'atlinenum': 2, u'qty': 1, u'linenum': 21, u'parent_lineid': 1027558388, u'prod_name': u'C9300-SPS-NONE'},
            {u'lineid': 1027558418, u'level': 1, u'ob_trans_id': 407245584, u'atlinenum': 3, u'qty': 1, u'linenum': 13, u'parent_lineid': 1027558388, u'prod_name': u'C9300-NW-1E-24'},
            {u'lineid': 1027558419, u'level': 1, u'ob_trans_id': 407245585, u'atlinenum': 4, u'qty': 1, u'linenum': 11, u'parent_lineid': 1027558388, u'prod_name': u'C9300-DNA-1E-24'},
            {u'boot_image': None, u'flashchksum': None, u'cco_location': u'/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES', u'qty': 1, u'group_id': None,
             u'dos_name': None, u'image_version': u'16.8.1a', u'image_type': None, u'config': None, u'prod_name': u'S9300UK9-168', u'var5': None, u'var4': None,
             u'var1': None, u'imagesize': 667244461, u'var3': None, u'var2': None, u'ob_trans_id': 407245586, u'image_name': u'cat9k_iosxe.16.08.01a.SPA.bin',
             u'atlinenum': 5, u'image_id': 103872, u'product_label': None, u'cco_check': u'Y', u'md5': u'5a7ebf6cfc15b83125819b13feec25a9',
             u'lineid': 1027558420, u'product_id': u'S9300UK9-168', u'linenum': 5, u'level': 1, u'parent_lineid': 1027558388, u'initiated_version': u'16.8.1a'},
            {u'lineid': 1027558421, u'level': 1, u'ob_trans_id': 407245587, u'atlinenum': 6, u'qty': 1, u'linenum': 9, u'parent_lineid': 1027558388, u'prod_name': u'CAB-TA-NA'},
            {u'lineid': 1027558422, u'level': 1, u'ob_trans_id': 407245588, u'atlinenum': 7, u'qty': 1, u'linenum': 17, u'parent_lineid': 1027558388, u'prod_name': u'C9300-STACK-NONE'},
            {u'lineid': 1027558423, u'level': 1, u'ob_trans_id': 407245589, u'atlinenum': 8, u'qty': 1, u'linenum': 15, u'parent_lineid': 1027558388, u'prod_name': u'C9300-SPWR-NONE'},
            {u'lineid': 1027558424, u'level': 1, u'ob_trans_id': 407245590, u'atlinenum': 9, u'qty': 1, u'linenum': 2, u'parent_lineid': 1027558388, u'prod_name': u'PWR-C1-BLANK'},
            {u'lineid': 1027558425, u'level': 1, u'ob_trans_id': 407245591, u'atlinenum': 10, u'qty': 1, u'linenum': 3, u'parent_lineid': 1027558388, u'prod_name': u'NM-BLANK-T1'},
            {u'lineid': 1027558426, u'level': 1, u'ob_trans_id': 407245592, u'atlinenum': 11, u'qty': 1, u'linenum': 7, u'parent_lineid': 1027558388, u'prod_name': u'C9300-NM-NONE'}]
        assert cnf_utils.get_config_to_check(major_line_id_cfg=config_input1) == config_output1
        assert cnf_utils.get_config_to_check(major_line_id_cfg=config_input2) == config_output2
        assert cnf_utils.get_config_to_check(major_line_id_cfg=config_input3) == config_output3
        assert cnf_utils.get_config_to_check(major_line_id_cfg=invalid_input1) == {}

    def test_cnf_utils_parse_component_config(self):
        psu_uut_type_keys = ['PS PID']
        psu_sn_keys = ['PS SN']
        pcamap_uut_type_keys = ['pid']
        pcamap_sn_keys = ['sn']
        invalid_input1 = {
            '1': {
                'WARNING': 'DopNifI2cCurrentRW()',
                'ERR': 'func_SCCReadQuackFruEeprom:',
                'bid': None,
                'succeed': '(i2cDone',
                'USAGE': 'SCCReadQuackFruEeprom',
                'include': 'pid,'
            },
            '3': {
                'USAGE': 'SCCReadQuackFruEeprom',
                'include': 'pid,',
                'bid': None,
                'WARNING': 'DopNifI2cCurrentRW()',
                'ERR': 'func_SCCReadQuackFruEeprom:'
            },
            '2': {
                'USAGE': 'SCCReadQuackFruEeprom',
                'include': 'pid,',
                'bid': None,
                'WARNING': 'DopNifI2cCurrentRW()',
                'ERR': 'func_SCCReadQuackFruEeprom:'
            }
        }
        invalid_input2 = 'C3K80-NM-HILBERT'
        config_input1 = {
            '2': {'pid': 'STACK-T1-50CM', 'bid': 8001, 'vid': 'V01', 'sn': 'MOC2026A5GJ', 'vpn': '800-40403-01', 'pcapn': 0, 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0},
            '3': {'pid': 'STACK-T1-50CM', 'bid': 8001, 'vid': 'V01', 'sn': 'MOC2026A5GJ', 'vpn': '800-40403-01', 'pcapn': 0, 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0},
            '1': {'pid': 'C3K80-NM-HILBERT', 'bid': 'f001', 'vid': 'P2', 'sn': 'FOC15461WAR', 'vpn': '73-14102-02', 'pcapn': '0x13', 'pcarev': 0, 'clei': 0, 'eci': 0, 'hwv': 0, 'cnt': 0}
        }
        config_output1 = {'STACK-T1-50CM': 1, 'C3K80-NM-HILBERT': 1}
        psu_info1 = {
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
        psu_config1 = {'PWR-C1-350WAC': 1}
        psu_info2 = {
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
            'B': {
                'PS Check-code base': '0x35',
                'I_in': '0xE006',
                'P_in': '0x081F',
                'PS VID': 'V02',
                'PS TAN': '341-0562-02',
                'T_spot': '0x0027',
                'V_in': '0xF999',
                'PS SN': 'LIT214525AF',
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
            }
        }
        psu_config2 = {'PWR-C1-350WAC': 2}
        invalid_psu_info1 = 'PWR-C1-350WAC'
        assert cnf_utils.parse_component_config(psu_info1, psu_uut_type_keys, psu_sn_keys) == psu_config1
        assert cnf_utils.parse_component_config(psu_info2, psu_uut_type_keys, psu_sn_keys) == psu_config2
        assert cnf_utils.parse_component_config(invalid_psu_info1) is None
        assert cnf_utils.parse_component_config(psu_info1) is None
        assert cnf_utils.parse_component_config(invalid_input1, pcamap_uut_type_keys, pcamap_sn_keys) == {}
        assert cnf_utils.parse_component_config(invalid_input2, pcamap_uut_type_keys, pcamap_sn_keys) is None
        assert cnf_utils.parse_component_config(None) is None
        assert cnf_utils.parse_component_config(config_input1, pcamap_uut_type_keys, pcamap_sn_keys) == config_output1
        assert cnf_utils.parse_component_config(config_input1, psu_uut_type_keys, psu_sn_keys) == {}

    @pytest.mark.skipif(True, reason="Not feasible the way Apollo is desgined.")
    def test_get_sw_licenses(self):
        sample_lids = {
            1004831736: ([{'sku': 'LIC-IP-BASE-S', 'quantity': 1}], [{'sku': 'LIC-CT5760-BASE', 'quantity': 1}], 'RTU'),
            1021811104: ([{'sku': 'C9300-DNA-E-48', 'quantity': 1}], [{'sku': 'C9300-DNA-E-48', 'quantity': 1}], 'DNA'),
            1022670829: ([{'sku': 'LIC-CTIOS-1A', 'quantity': 5}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}], [{'sku': 'LIC-CTIOS-1A', 'quantity': 5}], 'RTU'),
            1022133594: ([{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}], [], 'RTU'),
            1004543914: ([{'sku': 'LIC-IP-BASE-S', 'quantity': 1}, {'sku': 'LIC-CTIOS-1A', 'quantity': 100}], [{'sku': 'LIC-CT5760-BASE', 'quantity': 1}, {'sku': 'LIC-CT5760-100', 'quantity': 1}], 'RTU'),
            993752211: ([{'sku': 'LIC-CTIOS-1A', 'quantity': 50}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}], [{'sku': 'LIC-CT5760-50', 'quantity': 1}, {'sku': 'LIC-CT5760-BASE', 'quantity': 1}], 'RTU'),
            994040425: ([{'sku': 'LIC-CTIOS-1A', 'quantity': 5}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}], [{'sku': 'LIC-CTIOS-1A', 'quantity': 5}], 'RTU'),
            1024137411: ([{'sku': 'LIC-IP-SRVCS-S', 'quantity': 1}], [], 'RTU'),
            1024225063: ([{'sku': 'C1-C9300-24-DNAA-T', 'quantity': 1}], [{'sku': 'C1-C9300-24-DNAA-T', 'quantity': 1}], 'DNA'),
            1024454904: ([{'sku': 'C9300-DNA-E-24', 'quantity': 1}], [{'sku': 'C9300-DNA-E-24', 'quantity': 1}], 'DNA')
        }
        for k, v in sample_lids.items():
            assert v == ios.IOS._get_sw_licenses(k)
