"""Unit Tests for pcamap module"""
from unittest import TestCase
from mock import patch

from apollo.scripts.entsw.libs.product_drivers import pcamap

class PcamapTest(TestCase):
    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_wrong_deveice_instance(self, aplib, mode_mgr, ud):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='0'), aplib.FAIL)
        self.assertEqual(p.write_uut_peripheral(device_instance='10'), aplib.FAIL)

    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_both_keys_params(self, aplib, mode_mgr, ud):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='1',
                                                keys=['keya', 'keyb'], params={'keya': 'vala'}), aplib.FAIL)

    @patch.object(pcamap.Pcamap, 'write')
    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_empty_uut_config(self, aplib, mode_mgr, ud, mock_write):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        ud_1.uut_config.get.return_value = {}
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='1'), aplib.PASS)
        mock_write.assert_not_called()

    @patch.object(pcamap.Pcamap, 'write')
    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_with_keys(self, aplib, mode_mgr, ud, mock_write):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        ud_1.uut_config.get.return_value = {'1': {'keya': 'vala', 'keyb': 'valb'}}
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='1', keys=['keyb']), aplib.PASS)
        mock_write.assert_called_once_with('1', {'keyb': 'valb'})

    @patch.object(pcamap.Pcamap, 'write')
    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_uut_config(self, aplib, mode_mgr, ud, mock_write):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        ud_1.uut_config.get.return_value = {'1': {'keya': 'vala', 'keyb': 'valb'}}
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='1'), aplib.PASS)
        mock_write.assert_called_once_with('1', {'keya': 'vala', 'keyb': 'valb'})

    @patch.object(pcamap.Pcamap, 'write')
    @patch('apollo.scripts.entsw.libs.cat.uut_descriptor.UutDescriptor')
    @patch('apollo.scripts.entsw.libs.mode.modemanager.ModeManager')
    @patch('apollo.scripts.entsw.libs.product_drivers.pcamap.aplib')
    def test_write_uut_peripheral_with_params(self, aplib, mode_mgr, ud, mock_write):
        mode_mgr_1 = mode_mgr()
        ud_1 = ud()
        ud_1.uut_config.get.return_value = {'1': {'keya': 'vala', 'keyb': 'valb'}}
        p = pcamap.Pcamap(mode_mgr_1, ud_1)
        self.assertEqual(p.write_uut_peripheral(device_instance='1', params={'keyc': 'valc'}), aplib.PASS)
        mock_write.assert_called_once_with('1', {'keyc': 'valc'})


