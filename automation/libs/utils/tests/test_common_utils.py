import logging


from .. import common_utils

__title__ = 'EntSw General Library Unit Tests'
__author__ = ['bborel', 'qingywu']
__version__ = '0.2.0'

log = logging.getLogger(__name__)


class TestCommonUtils(object):

    def test_validate_ip_addr(self):
        assert common_utils.validate_ip_addr('1.1.1.1')
        assert not common_utils.validate_ip_addr('1.1.1.1', 'IPv6')
        assert common_utils.validate_ip_addr('255.255.255.255')
        assert not common_utils.validate_ip_addr('1.1.1')
        assert not common_utils.validate_ip_addr('....')
        assert not common_utils.validate_ip_addr('A.B.C.D')
        assert common_utils.validate_ip_addr('192.168.1.0')
        assert not common_utils.validate_ip_addr('192.268.1.0')
        assert common_utils.validate_ip_addr('001.001.001.0')
        assert common_utils.validate_ip_addr('ABCD:9876:0001:6789:4321:1234:0001:0002')
        assert common_utils.validate_ip_addr('1:2:3:4:5:6:7:8')
        assert not common_utils.validate_ip_addr('ABCD:9876:0001:6789:4321:1234:0001:0002', 'IPv4')
        assert common_utils.validate_ip_addr('ABCD:9876:0001::4321:1234:0001:0002')
        assert not common_utils.validate_ip_addr('ABCD:9876:0001::4321:1234:0001:000Z')
        assert common_utils.validate_ip_addr('ABCD::0001::4321:1234::0002')
        assert common_utils.validate_ip_addr('ABCD:::::::0002')
        assert common_utils.validate_ip_addr(':::::::0002')
        assert not common_utils.validate_ip_addr(':::::::')

    def test_validate_mac_addr(self):
        assert common_utils.validate_mac_addr('00:11:22:88:99:00')
        assert common_utils.validate_mac_addr('0011:2288:9900')
        assert common_utils.validate_mac_addr('00-11-22-88-99-00')
        assert common_utils.validate_mac_addr('00 11 22 88 99 00')
        assert common_utils.validate_mac_addr('00.11.22.88.99.00')
        assert common_utils.validate_mac_addr('001122889900')
        assert common_utils.validate_mac_addr('0x001122889900')
        assert not common_utils.validate_mac_addr('00:00:00:00:00:00')
        assert not common_utils.validate_mac_addr('BA:DB:AD:BA:DB:AD')
        assert not common_utils.validate_mac_addr('00:11:22:34:56:00')
        assert not common_utils.validate_mac_addr('11:22:33:44:55:00')
        assert not common_utils.validate_mac_addr('FF:FF:FF:FF:FF:FF')
        assert not common_utils.validate_mac_addr('FG:FF:FF:FF:FF:FF')
        assert not common_utils.validate_mac_addr('FF:FF:FF:FF:FF')

    def test_convert_mac(self):
        assert common_utils.convert_mac('BA:DB:AD:BA:DB:AD', '6.', case=None) == 'BA.DB.AD.BA.DB.AD'
        assert common_utils.convert_mac('0x11.22.33.44.55.66', '1', case=None) == '112233445566'
        assert common_utils.convert_mac('0x11.22.33.44.55.66', '2-', case=None) == '112233-445566'
        assert common_utils.convert_mac('112233445566', '3 ', case=None) == '1122 3344 5566'
        assert common_utils.convert_mac('ba.db.ad.ba.db.ad', '0x', case='upper') == '0xBADBADBADBAD'
        assert common_utils.convert_mac('0xBADBADBADBAD', '6:', case='lower') == 'ba:db:ad:ba:db:ad'

    def test_datetimestr(self):
        print(common_utils.datetimestr())
        assert len(common_utils.datetimestr()) == 8

    def test_num2base(self):
        assert '1100100' == common_utils.num2base(100, 2)
        assert '100' == common_utils.num2base(100, 10)
        assert '64' == common_utils.num2base(100, 16)
        assert '3N' == common_utils.num2base(100, 26)
        assert '2Y' == common_utils.num2base(100, 34)
        assert [90, 438207500, 880449001] == common_utils.num2base(99**10, 10**9)

    def test_expand_comma_dash_num_list(self):
        assert [1, 2, 3, 4, 5] == common_utils.expand_comma_dash_num_list('1-5')
        assert [1, 2, 3, 4, 5, 8, 9, 10, 12] == common_utils.expand_comma_dash_num_list('1-5,8-10,12')
        assert [1, 2, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 20] == common_utils.expand_comma_dash_num_list('1,2, 5 -7,,,a,apollo1,,9---, -, 10-12-15, 17-18-, -20')

    def test_split_scanned_uut_data(self):
        revision_map = {
            'MB_ASSEMBLY_NUM': 'MB_REVISION_NUM',
            'TAN_NUM': 'TAN_REVISION_NUMBER',
            'MODEL_NUM': 'VERSION_ID',
            'PID': 'VID',
            'VPN': 'HWV',
            'PCAPN': 'PCAREV',
        }
        assert [('MB_ASSEMBLY_NUM', '73-12345-01')] == common_utils.split_scanned_uut_data('MB_ASSEMBLY_NUM', '73-12345-01 A0')
        assert [('MB_ASSEMBLY_NUM', '73-12345-01'), ('MB_REVISION_NUM', '')] == common_utils.split_scanned_uut_data('MB_ASSEMBLY_NUM', '73-12345-01', revision_map)
        assert [('MB_ASSEMBLY_NUM', '73-12345-01'), ('MB_REVISION_NUM', 'A0')] == common_utils.split_scanned_uut_data('MB_ASSEMBLY_NUM', '73-12345-01 A0', revision_map)
        assert [('NOT_IN_revision_map', 'ANY-TYPE-OF-THING')] == common_utils.split_scanned_uut_data('NOT_IN_revision_map', 'ANY-TYPE-OF-THING', revision_map)

    def test_get_ip_addr_assignment(self, max_idx=5000):
        class Conn:
            def __init__(self, uid):
                self.uid = uid
        connection = Conn(0)
        ipl = []
        for i in range(0, max_idx):
            connection.uid = i
            ipl.append(common_utils.get_ip_addr_assignment(connection, '10.1.1.1', '255.255.0.0'))
        # Check for count and duplicates
        assert max_idx == len(ipl)
        assert list(set([x for x in ipl if ipl.count(x) > 1])) == []

    def test_is_version_greater(self):
        version1 = '3.5.6'
        version2 = '3.12.2'
        version3 = '16.8.1a'
        version4 = '16.8.1b'
        version5 = '16.7.8a'
        version6 = '16.8.4'
        version7 = '16.10'
        version8 = '16.10.2'
        assert common_utils.is_version_greater(version1, version2) is False
        assert common_utils.is_version_greater(version2, version1) is True
        assert common_utils.is_version_greater(version3, version2) is True
        assert common_utils.is_version_greater(version2, version3) is False
        assert common_utils.is_version_greater(version4, version3) is True
        assert common_utils.is_version_greater(version3, version4) is False
        assert common_utils.is_version_greater(version3, version3) is True
        assert common_utils.is_version_greater(version6, version6) is True
        assert common_utils.is_version_greater(version4, version5) is True
        assert common_utils.is_version_greater(version5, version4) is False
        assert common_utils.is_version_greater(version5, version6) is False
        assert common_utils.is_version_greater(version6, version5) is True
        assert common_utils.is_version_greater(version6, version7) is False
        assert common_utils.is_version_greater(version7, version6) is True
        assert common_utils.is_version_greater(version7, version8) is False
        assert common_utils.is_version_greater(version8, version7) is True
        assert common_utils.is_version_greater(version7, version4) is True
        assert common_utils.is_version_greater(version4, version7) is False
        assert common_utils.is_version_greater(version1, version2, inclusive=False) is False
        assert common_utils.is_version_greater(version2, version1, inclusive=False) is True
        assert common_utils.is_version_greater(version3, version2, inclusive=False) is True
        assert common_utils.is_version_greater(version2, version3, inclusive=False) is False
        assert common_utils.is_version_greater(version4, version3, inclusive=False) is True
        assert common_utils.is_version_greater(version3, version4, inclusive=False) is False
        assert common_utils.is_version_greater(version3, version3, inclusive=False) is False
        assert common_utils.is_version_greater(version6, version6, inclusive=False) is False
        assert common_utils.is_version_greater('16.10', '16.10', inclusive=True) is True
