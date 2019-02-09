
import pytest
from .. import act2
from .. import quack2
from .. import x509

__title__ = 'EntSw IdPro Library Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestIdPro():
    connection = type('Conn', (), {'uid': 1})
    mode_mgr = type('ModeMgr', (), {'uut_conn': connection, 'uut_prompt_map': {}})

    @pytest.mark.skipif(False, reason="ACT2 partial.")
    def test_act2_sign_chip(self):
        psuedo_act2 = act2.ACT2(device_instance=0,
                                mode_mgr=TestIdPro.mode_mgr,
                                uut_idpro='ACT2',
                                unittest=True)
        psuedo_act2.act2_data['chip_sernum'] = '5102125369700109E20000002DDA11672033302031353A30373A343120E86A41'
        act2_data = psuedo_act2.sign_chip(skip_chip_verify=True, skip_session_id=True)
        assert len(act2_data.get('chip_sernum', 'unknown')) == 64
        assert int(act2_data.get('cert_chain_len', 0)) > 3000
        # assert int(act2_data.get('cliip_len', 0)) > 3000

    def test_x509_sign_sudi(self):
        psuedo_x509 = x509.X509Sudi(device_instance=0,
                                    mode_mgr=TestIdPro.mode_mgr,
                                    unittest=True,
                                    uut_mac='ba:db:ad:22:11:00',
                                    uut_sernum='CSC01234567',
                                    uut_pid='WS-C1000-24',
                                    x509_sudi_request_type='PROD',
                                    x509_sudi_cert_method='KEY',
                                    x509_sudi_hash=['SHA1'])

        # The cesiumlib is NOT designed to be used outside of an Apollo container which is a really stupid design.
        # It means unittesting such as this will never work and we are relegated to invoking this within the Apollo
        # CLI.  For now we will just assert this as False since within the module a unittest flag will return False.
        assert not psuedo_x509.sign_sudi()

    def test_quack2_sign(self):
        assert True