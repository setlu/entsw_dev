"""
=========================================================
CATALYST Series3 CITP Unittests for Production Simulation
=========================================================

This requires a dedicated test platform with "gold units".
The platform station setup can be placed anywhere.
Each test area should mimic the actual production test station.
The Apollo x_config.py MUST conform to the standard station definition as detailed in the entsw.config.common modules.
The golden UUTs and all data for production prompting are stored in a definition module of a specific format.
(See the "citp_uut_unittest_def.py" as the default community module.)
A custom module can be provided as gold_uuts_def.py.

"""
import pytest
from apollo.scripts.entsw.libs.tools.citp.citp_unittest_framework import CITPUnittestFramework
import gold_uuts_def


__title__ = 'CATALYST Series3 Production Simulation Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestC3650ProductionSim(CITPUnittestFramework):
    if gold_uuts_def and hasattr(gold_uuts_def, 'gold_uuts'):
        CITPUnittestFramework.uut_defs = gold_uuts_def.gold_uuts

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3650_pcbst(self, tss, uuts):
        self.run_multi_container('C3650', 'PCBST', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3650_pcb2c(self, tss, uuts):
        self.run_multi_container('C3650', 'PCB2C', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3650_assy(self, tss, uuts):
        self.run_multi_container('C3650', 'ASSY', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3650_sysbi(self, tss, uuts):
        self.run_multi_container('C3650', 'SYSBI', tss=tss, uuts=uuts)


class TestC3850ProductionSim(CITPUnittestFramework):
    if gold_uuts_def and hasattr(gold_uuts_def, 'gold_uuts'):
        CITPUnittestFramework.uut_defs = gold_uuts_def.gold_uuts

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3850_pcbst(self, tss, uuts):
        self.run_multi_container('C3850', 'PCBST', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3850_pcb2c(self, tss, uuts):
        self.run_multi_container('C3850', 'PCB2C', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3850_assy(self, tss, uuts):
        self.run_multi_container('C3850', 'ASSY', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c3850_sysbi(self, tss, uuts):
        self.run_multi_container('C3850', 'SYSBI', tss=tss, uuts=uuts)


class TestC9300ProductionSim(CITPUnittestFramework):
    if gold_uuts_def and hasattr(gold_uuts_def, 'gold_uuts'):
        CITPUnittestFramework.uut_defs = gold_uuts_def.gold_uuts

    @pytest.mark.skipif(True, reason="Not ready.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300_pcbdl(self, tss, uuts):
        self.run_multi_container('C9300', 'PCBDL', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300_pcbst(self, tss, uuts):
        self.run_multi_container('C9300', 'PCBST', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300_sysbi(self, tss, uuts):
        self.run_multi_container('C9300', 'SYSBI', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300_pcb2c(self, tss, uuts):
        self.run_multi_container('C9300', 'PCB2C', tss=tss, uuts=uuts)
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300_assy(self, tss, uuts):
        self.run_multi_container('C9300', 'ASSY', tss=tss, uuts=uuts)


class TestC9300LProductionSim(CITPUnittestFramework):
    if gold_uuts_def and hasattr(gold_uuts_def, 'gold_uuts'):
        CITPUnittestFramework.uut_defs = gold_uuts_def.gold_uuts

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300l_pcbdl(self, tss, uuts):
        self.run_multi_container('C9300L', 'PCBDL', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300l_pcbst(self, tss, uuts):
        self.run_multi_container('C9300L', 'PCBST', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300l_pcb2c(self, tss, uuts):
        self.run_multi_container('C9300L', 'PCB2C', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300l_pcbassy(self, tss, uuts):
        self.run_multi_container('C9300L', 'PCBASSY', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9300l_pcbft(self, tss, uuts):
        self.run_multi_container('C9300L', 'PCBFT', tss=tss, uuts=uuts)


# class TestCat3EngMenu(CITPUnittestFramework):
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_showconfig(self):
#         self.run_multi_container('C3K', 'DBGSYS', answers=['COF', 'False', 'SHOW CONFIG', 'ALL-compact', 'QUIT'])
#
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_stardust(self):
#         self.run_multi_container('C3K', 'DBGSYS', answers=['COF', 'False', 'POWER CYCLE ON', 'AUTO-LOAD UUT DEFINITION', 'STARDUST', 'SOFT QUIT'])
#
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_ios(self):
#         self.run_multi_container('C3K', 'DBGSYS', answers=['COF', 'False', 'AUTO-LOAD UUT DEFINITION', 'IOS', 'SOFT QUIT'])
#
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_tftp(self):
#         src_images = ['test_image.bin']
#         dst_images = src_images
#         mode_answers = ['COF', 'False', 'AUTO-LOAD UUT DEFINITION', 'LINUX', 'SET NET INTF']
#         tftp_image_answers = ['TFTP get'] + src_images + dst_images
#         answers_flow = mode_answers + tftp_image_answers + ['SOFT QUIT']
#         self.run_multi_container('C3K', 'DBGSYS', answers=answers_flow)
#
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_idpro(self):
#         self.run_multi_container('C3K', 'DBGSYS', answers=['COF', 'False', 'AUTO-LOAD UUT DEFINITION', 'STARDUST', 'SYSINIT', 'IDPRO', '0', 'SOFT QUIT'])
#
#     @pytest.mark.skipif(False, reason="None.")
#     @pytest.mark.parallel
#     def test_c3k_eng_menu_quit(self):
#         self.run_multi_container('C3K', 'DBGSYS', answers=['COF', 'False', 'QUIT'])
