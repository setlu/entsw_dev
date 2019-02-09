
from ..C9500 import c9500
from ..common import catalyst5


__title__ = 'CATALYST Series5 Class Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestCatalystClass():

    def test_class_c9500(self):
        a = c9500.Adelphi()
        for prod in [a]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC9500' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC9500' in str(prod.pcamap)
            assert 'RommonC9500' in str(prod.rommon)
            assert 'PeripheralC5K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) >= 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20