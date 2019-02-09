

from ..C3650 import c3650
from ..C3850 import c3850
from ..C9300 import c9300
from ..C9300L import c9300l
from ..common import catalyst3

__title__ = 'CATALYST Series3 Class Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestCatalystClass():

    def test_class_c3650(self):
        a = c3650.Archimedes()
        e = c3650.Euclid()
        t = c3650.Theon()
        for prod in [a, e, t]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC3000' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            if prod == a:
                assert 'Quack2' in str(prod.quack2)
            else:
                assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC3000' in str(prod.pcamap)
            assert 'RommonC3000' in str(prod.rommon)
            assert 'PeripheralC3K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20

    def test_class_c3850(self):
        e = c3850.Edison()
        for prod in [e]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC3000' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC3000' in str(prod.pcamap)
            assert 'RommonC3000' in str(prod.rommon)
            assert 'PeripheralC3K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20

    def test_class_c9300(self):
        n = c9300.Nyquist()
        for prod in [n]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC9300' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC9300' in str(prod.pcamap)
            assert 'RommonC9300' in str(prod.rommon)
            assert 'PeripheralC3K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20

    def test_class_c9300l(self):
        f = c9300l.Franklin()
        for prod in [f]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC9300' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC9300L' in str(prod.pcamap)
            assert 'RommonC9300L' in str(prod.rommon)
            assert 'PeripheralC3K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20
