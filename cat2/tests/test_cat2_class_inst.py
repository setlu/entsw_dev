
# from ..C2960 import c2960
from ..C9200 import c9200
from ..common import catalyst2

__title__ = 'CATALYST Series2 Class Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestCatalystClass():

    def test_class_c9200(self):
        q = c9200.Quake()
        for prod in [q]:
            assert 'UutDescriptor' in str(prod.ud)
            assert 'ModeManager' in str(prod.mode_mgr)
            assert 'StardustC9200' in str(prod.diags)
            assert 'Linux' in str(prod.linux)
            assert 'ACT2' in str(prod.act2)
            assert 'IOS' in str(prod.ios)
            assert 'PcamapC9200' in str(prod.pcamap)
            assert 'RommonC9200' in str(prod.rommon)
            assert 'PeripheralC2K' in str(prod.peripheral)
            assert len(prod.ud.product_manifest) > 1
            for codename in prod.ud.product_manifest.keys():
                prod.ud.product_selection = codename
                assert len(prod.ud.uut_config.keys()) > 1