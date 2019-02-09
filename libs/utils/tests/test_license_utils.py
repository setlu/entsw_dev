import pytest
import unittest
import apollo.scripts.entsw.libs.utils.license_utils as license_utils


__version__ = '0.5.0'
__author__ = 'qingywu@cisco.com'


class TestLicenseUtils(unittest.TestCase):

    def test_is_dna_license(self):
        assert license_utils.is_dna_license('ABCD') is False
        assert license_utils.is_dna_license('DNA') is False
        assert license_utils.is_dna_license('C9500-DNA-E') is True
        assert license_utils.is_dna_license('C9500-DNA-A-24') is True
        assert license_utils.is_dna_license('C1-C9300-48-DNAA-T') is True
        assert license_utils.is_dna_license('C1-C3850-24-DNAA+') is True
        assert license_utils.is_dna_license('C1-C9500-24Y4C-DNA') is True
        assert license_utils.is_dna_license('C3650-24-DNA-A-UP=') is True
        assert license_utils.is_dna_license('C3650-DNA-E-48') is True
        assert license_utils.is_dna_license('C3850XS-DNA-24P-A') is True
        assert license_utils.is_dna_license('C3850XS-DNA-L-A') is True
        assert license_utils.is_dna_license('C9500H-DNA-32C-A') is True
        assert license_utils.is_dna_license('C9500DNA-E') is True
        assert license_utils.is_dna_license('C3850-24-L-S') is False
        assert license_utils.is_dna_license('WS-C3650-12X48FD-L') is False
        assert license_utils.is_dna_license('C1-WS3650-48FQM/K9') is False
        assert license_utils.is_dna_license('C1-WS3850-24P/K9') is False
        assert license_utils.is_dna_license('WS-C3850-48XS-F-S') is False
        assert license_utils.is_dna_license('C9300-NW-E-48') is True
        assert license_utils.is_dna_license('C9300-NW-A-48') is True
        assert license_utils.is_dna_license('C9300-NW-E-24-1Y') is True
        assert license_utils.is_dna_license('C9300-NW-10A-48') is True
        assert license_utils.is_dna_license('C9300-NW-1E-48') is True
        assert license_utils.is_dna_license('C9500-NW-A-EDU') is True
        assert license_utils.is_dna_license('C9500-NW-L-10A') is True
        assert license_utils.is_dna_license('C9500-NW-L-10E') is True
        assert license_utils.is_dna_license('C9500-NW-10E') is True
        assert license_utils.is_dna_license('C9500-NW-L-1E') is True
        assert license_utils.is_dna_license(u'C9300-NW-1E-48') is True
        assert license_utils.is_dna_license(u'C9500-NW-A-EDU') is True
        assert license_utils.is_dna_license(u'C9500-NW-L-10A') is True
        assert license_utils.is_dna_license(u'C9500-NW-L-10E') is True
        assert license_utils.is_dna_license(u'C9500-NW-10E') is True
        assert license_utils.is_dna_license(u'C9500-NW-L-1E') is True
        assert license_utils.is_dna_license(u'C3850-NW-L-1E') is False
        assert license_utils.is_dna_license(u'C3850-DNA-OPTOUT') is False
        assert license_utils.is_dna_license(u'C9300-DNA-OPTOUT') is False
        self.assertRaises(Exception, license_utils.is_dna_license, 100)
        self.assertRaises(Exception, license_utils.is_dna_license, [1, 2, 3])
        self.assertRaises(Exception, license_utils.is_dna_license)

    def test_is_rtu_license(self):
        assert license_utils.is_rtu_license('C3850-24-L-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C3850-48-L-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C3650-24-L-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C3650-48-L-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C3850-12-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C3850-24-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C3850-48-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C3650-12-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C3650-24-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C3650-48-S-E') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('S3850UK9-166') is False
        assert license_utils.is_rtu_license('C9300-NW-E-48') is False
        assert license_utils.is_rtu_license('C1-WS3850-24P/K9') is False
        assert license_utils.is_rtu_license('WS-C3850-48XS-F-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('WS-C3850-48P-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license('WS-C3850-48F-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license('WS-C3650-48PQ-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license('WS-C3650-12X48UR-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license(u'WS-C3850-48XS-F-S') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license(u'WS-C3850-48P-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license(u'WS-C3850-48F-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license(u'WS-C3650-48PQ-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license(u'WS-C3650-12X48UR-L') == 'LIC-LAN-BASE-L'
        assert license_utils.is_rtu_license('C1-WSC3850-48XS-FS') is False
        assert license_utils.is_rtu_license('C9300-NW-E-48') is False
        assert license_utils.is_rtu_license('C9300-NW-A-48') is False
        assert license_utils.is_rtu_license('C9300-NW-E-24-1Y') is False
        assert license_utils.is_rtu_license('C9300-NW-10A-48') is False
        assert license_utils.is_rtu_license('C9300-NW-1E-48') is False
        assert license_utils.is_rtu_license('C9500-NW-A-EDU') is False
        assert license_utils.is_rtu_license('C9500-NW-L-10A') is False
        assert license_utils.is_rtu_license('C9500-NW-L-10E') is False
        assert license_utils.is_rtu_license('C9500-NW-10E') is False
        assert license_utils.is_rtu_license('C9500-NW-L-1E') is False
        assert license_utils.is_rtu_license('C3850-NW-L-1E') is False
        assert license_utils.is_rtu_license('C1FPCAT38503K9') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C1APCAT38503K9') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C1FPCAT36501K9') == 'LIC-IP-BASE-S'
        assert license_utils.is_rtu_license('C1APCAT36501K9') == 'LIC-IP-SRVCS-E'
        assert license_utils.is_rtu_license('C1F1VCAT38503-04') is False
        assert license_utils.is_rtu_license('C1-ISE-BASE-12P') is False
        self.assertRaises(Exception, license_utils.is_rtu_license, 100)
        self.assertRaises(Exception, license_utils.is_rtu_license, [1, 2, 3])
        self.assertRaises(Exception, license_utils.is_rtu_license)

    def test_is_apcount_license(self):
        assert license_utils.is_apcount_license('LIC-CT5760-25') == 25
        assert license_utils.is_apcount_license('LIC-CT5760-50') == 50
        assert license_utils.is_apcount_license('LIC-CT5760-100') == 100
        assert license_utils.is_apcount_license('LIC-CT5760-250') == 250
        assert license_utils.is_apcount_license('LIC-CT5760-500') == 500
        assert license_utils.is_apcount_license('LIC-CT5760-1K') == 1000
        assert license_utils.is_apcount_license(u'LIC-CT5760-25') == 25
        assert license_utils.is_apcount_license(u'LIC-CT5760-50') == 50
        assert license_utils.is_apcount_license(u'LIC-CT5760-100') == 100
        assert license_utils.is_apcount_license(u'LIC-CT5760-250') == 250
        assert license_utils.is_apcount_license(u'LIC-CT5760-500') == 500
        assert license_utils.is_apcount_license(u'LIC-CT5760-1K') == 1000
        assert license_utils.is_apcount_license('LIC-CT5760-BASE') is False
        assert license_utils.is_apcount_license('LIC-CTIOS-1A') == 1
        assert license_utils.is_apcount_license('AIR-CT5760-K9') is False
        assert license_utils.is_apcount_license('C3650-12-S-E') is False
        assert license_utils.is_apcount_license('C3650-24-S-E') is False
        assert license_utils.is_apcount_license('C3650-48-S-E') is False
        assert license_utils.is_apcount_license('S3850UK9-166') is False
        assert license_utils.is_apcount_license('C9300-NW-E-48') is False
        assert license_utils.is_apcount_license('C1-WS3850-24P/K9') is False
        assert license_utils.is_apcount_license('WS-C3850-48XS-F-S') is False
        assert license_utils.is_apcount_license('WS-C3850-48P-L') is False
        assert license_utils.is_apcount_license('WS-C3850-48F-L') is False
        assert license_utils.is_apcount_license('WS-C3650-48PQ-L') is False
        assert license_utils.is_apcount_license('WS-C3650-12X48UR-L') is False
        assert license_utils.is_apcount_license('C1-WSC3850-48XS-FS') is False
        assert license_utils.is_apcount_license('C9300-NW-E-48') is False
        assert license_utils.is_apcount_license('C9300-NW-A-48') is False
        assert license_utils.is_apcount_license('C9300-NW-E-24-1Y') is False
        assert license_utils.is_apcount_license('C9300-NW-10A-48') is False
        assert license_utils.is_apcount_license('C9300-NW-1E-48') is False
        assert license_utils.is_apcount_license('C9500-NW-A-EDU') is False
        assert license_utils.is_apcount_license('C9500-NW-L-10A') is False
        assert license_utils.is_apcount_license('C9500-NW-L-10E') is False
        assert license_utils.is_apcount_license('C9500-NW-10E') is False
        assert license_utils.is_apcount_license('C9500-NW-L-1E') is False
        assert license_utils.is_apcount_license('C3850-NW-L-1E') is False
        self.assertRaises(Exception, license_utils.is_apcount_license, 100)
        self.assertRaises(Exception, license_utils.is_apcount_license, {'license_pid': [1, 2, 3]})
        self.assertRaises(Exception, license_utils.is_apcount_license)

    def test_get_license_feature(self):
        assert license_utils.get_license_feature('ABCD', license_type='DNA') is None
        assert license_utils.get_license_feature('ABCD', license_type='RTU') is None
        assert license_utils.get_license_feature('ABCD') is None
        assert license_utils.get_license_feature('DNA', license_type='DNA') is None
        assert license_utils.get_license_feature('DNA', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-DNA-E') is None
        assert license_utils.get_license_feature('C9500-DNA-E', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9500-DNA-E', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-DNA-A-24', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C1-C9300-48-DNAA-T', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C1-C3850-24-DNAA+', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C1-C9500-24Y4C-DNA', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C3650-24-DNA-A-UP=', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C3650-DNA-E-48', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C3850XS-DNA-24P-A', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C3850XS-DNA-L-A', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9500H-DNA-32C-A', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9500DNA-E', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C3850-24-L-S', license_type='DNA') is None
        assert license_utils.get_license_feature('C3850-24-L-S', license_type='RTU') is None
        assert license_utils.get_license_feature('WS-C3650-12X48FD-L', license_type='DNA') is None
        assert license_utils.get_license_feature('WS-C3650-12X48FD-L', license_type='RTU') is None
        assert license_utils.get_license_feature('WS-C3650-12X48FD-L', license_type='RTU') is None
        assert license_utils.get_license_feature('C1-WS3650-48FQM/K9', license_type='DNA') is None
        assert license_utils.get_license_feature('C1-WS3650-48FQM/K9', license_type='RTU') is None
        assert license_utils.get_license_feature('C1-WS3850-24P/K9', license_type='DNA') is None
        assert license_utils.get_license_feature('C1-WS3850-24P/K9', license_type='DNA') is None
        assert license_utils.get_license_feature('WS-C3850-48XS-F-S', license_type='DNA') is None
        assert license_utils.get_license_feature('WS-C3850-48XS-F-S', license_type='RTU') is None
        assert license_utils.get_license_feature('S3850UK9-166', license_type='DNA') is None
        assert license_utils.get_license_feature('S3850UK9-166', license_type='RTU') is None
        assert license_utils.get_license_feature('LIC-LAN-BASE-L') is None
        assert license_utils.get_license_feature('LIC-LAN-BASE-L', license_type='RTU') == 'lanbase'
        assert license_utils.get_license_feature('LIC-LAN-BASE-L', license_type='DNA') is None
        assert license_utils.get_license_feature('LIC-IP-BASE-S') is None
        assert license_utils.get_license_feature('LIC-IP-BASE-S', license_type='RTU') == 'ipbase'
        assert license_utils.get_license_feature('LIC-IP-BASE-S', license_type='DNA') is None
        assert license_utils.get_license_feature('LIC-IP-SRVCS-E') is None
        assert license_utils.get_license_feature('LIC-IP-SRVCS-E', license_type='RTU') == 'ipservices'
        assert license_utils.get_license_feature('LIC-IP-SRVCS-E', license_type='DNA') is None
        assert license_utils.get_license_feature('LIC-IP-SRVCS-E', license_type='whatever') is None
        assert license_utils.get_license_feature('C9300-NW-E-48', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9300-NW-E-48', license_type='RTU') is None
        assert license_utils.get_license_feature('C9300-NW-A-48', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9300-NW-A-48', license_type='RTU') is None
        assert license_utils.get_license_feature('C9300-NW-E-24-1Y', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9300-NW-10A-48', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9300-NW-10A-48', license_type='RTU') is None
        assert license_utils.get_license_feature('C9300-NW-1E-48', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9300-NW-1E-48', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-NW-A-EDU', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9500-NW-A-EDU', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-NW-L-10A', license_type='DNA') == 'advantage'
        assert license_utils.get_license_feature('C9500-NW-L-10A', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-NW-L-10E', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9500-NW-L-10E', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-NW-10E', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9500-NW-10E', license_type='RTU') is None
        assert license_utils.get_license_feature('C9500-NW-L-1E', license_type='DNA') == 'essentials'
        assert license_utils.get_license_feature('C9500-NW-L-1E', license_type='RTU') is None
        assert license_utils.get_license_feature('C3850-NW-L-1E', license_type='DNA') is None
        assert license_utils.get_license_feature('C3850-NW-L-1E', license_type='RTU') is None

    def test_normalize_sw_licenses(self):
        assert license_utils.normalize_sw_licenses([]) == []
        assert sorted(license_utils.normalize_sw_licenses([{'sku': 'C9300-48-DNA-E', 'quantity': 1}, {'sku': 'LIC-CTIOS-1A', 'quantity': 10}])) \
            == sorted([{'sku': 'C9300-48-DNA-E', 'quantity': 1}, {'sku': 'LIC-CTIOS-1A', 'quantity': 10}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': u'C9500-NW-A-EDU', 'quantity': 1}])) \
            == sorted([{'sku': u'C9500-NW-A-EDU', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': u'C9300-NW-E-48', 'quantity': 1}, {'sku': u'C9300-DNA-E-48', 'quantity': 1}])) \
            == sorted([{'sku': u'C9300-NW-E-48', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': u'C9300-NW-A-48', 'quantity': 1}, {'sku': u'C1-C9300-48-DNAA-T', 'quantity': 1}])) \
            == sorted([{'sku': u'C9300-NW-A-48', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': 'LIC-LAN-BASE-L', 'quantity': 1}])) \
            == sorted([{'sku': 'LIC-LAN-BASE-L', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': 'LIC-LAN-BASE-L', 'quantity': 1}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}])) \
            == sorted([{'sku': 'LIC-IP-BASE-S', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}])) \
            == sorted([{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}])
        assert sorted(license_utils.normalize_sw_licenses([{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}, {'sku': 'LIC-LAN-BASE-L', 'quantity': 1}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}])) \
            == sorted([{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}])
        self.assertRaises(Exception, license_utils.normalize_sw_licenses, {'sw_license': {'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}})
        self.assertRaises(Exception, license_utils.normalize_sw_licenses, {'sw_license': 'LIC-IP-SRVCS-E'})
        self.assertRaises(Exception, license_utils.normalize_sw_licenses, 'WHATEVER')
        self.assertRaises(Exception, license_utils.normalize_sw_licenses, 1234)

    def test_get_license_detail(self):
        assert license_utils.get_license_detail(lic_feature='ipbase', license_type='RTU') == [{'name': 'ipbase', 'type': '[Pp]ermanent'}]
        assert license_utils.get_license_detail(lic_feature='lanbase', license_type='RTU') == [{'name': 'lanbase', 'type': '[Pp]ermanent'}]
        assert license_utils.get_license_detail(lic_feature='ipservices', license_type='RTU') == [{'name': 'ipservices', 'type': '[Pp]ermanent'}]
        assert license_utils.get_license_detail(lic_feature='advantage', license_type='DNA') \
            == [{'name': 'network-advantage', 'type': 'Permanent'}, {'name': 'dna-advantage', 'type': 'Subscription'}]
        assert license_utils.get_license_detail(lic_feature='essentials', license_type='DNA') \
            == [{'name': 'network-essentials', 'type': 'Permanent'}, {'name': 'dna-essentials', 'type': 'Subscription'}]
        self.assertRaises(Exception, license_utils.get_license_detail, dict(lic_feature='ipbase', license_type='DNA'))
        self.assertRaises(Exception, license_utils.get_license_detail, dict(lic_feature='whatever', license_type='DNA'))
        self.assertRaises(Exception, license_utils.get_license_detail, dict(lic_feature='advantage', license_type='RTU'))
        self.assertRaises(Exception, license_utils.get_license_detail, dict(lic_feature='ipbase', license_type='WHATEVER'))
        assert sorted(license_utils.get_license_detail(lic_feature='ipbase', license_type='RTU', all_levels=True)) \
            == sorted([{'name': 'lanbase', 'type': '[Pp]ermanent'}, {'name': 'ipbase', 'type': '[Pp]ermanent'}, {'name': 'ipservices', 'type': '[Pp]ermanent'}])
        assert sorted(license_utils.get_license_detail(lic_feature='ipbase', license_type='RTU', all_levels=True)) \
            == sorted([{'name': 'lanbase', 'type': '[Pp]ermanent'}, {'name': 'ipbase', 'type': '[Pp]ermanent'}, {'name': 'ipservices', 'type': '[Pp]ermanent'}])
        assert sorted(license_utils.get_license_detail(lic_feature='whatever', license_type='DNA', all_levels=True)) \
            == sorted([{'name': 'network-advantage', 'type': 'Permanent'}, {'name': 'dna-advantage', 'type': 'Subscription'},
                      {'name': 'network-essentials', 'type': 'Permanent'}, {'name': 'dna-essentials', 'type': 'Subscription'}])
