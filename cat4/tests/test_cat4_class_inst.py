
from ..C4500 import c4500
from ..C9400 import c9400
from ..common import catalyst4


__title__ = 'CATALYST Series4 Class Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestCatalystClass():
    def test_class_c9400(self):
        ml = c9400.MacallanLinecard()
        ms = c9400.MacallanSupervisor()
        for prod in [ml, ms]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC9400' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC9400' in str(prod.pcamap)
            assert 'RommonC9400' in str(prod.rommon)
            assert 'PeripheralC4K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 20

    def test_class_c4500(self):
        k1 = c4500.K10()
        k2 = c4500.K5()
        for prod in [k1, k2]:
            assert 'UutDescriptor' in str(prod.ud)
