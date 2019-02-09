"""
=========================================================
CATALYST Series4 CITP Unittests for Production Simulation
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


__title__ = 'CATALYST Series4 Production Simulation Unit Tests'
__author__ = ['bborel']
__version__ = '2.0.0'


class TestC9400ProductionSim(CITPUnittestFramework):
    if gold_uuts_def and hasattr(gold_uuts_def, 'gold_uuts'):
        CITPUnittestFramework.uut_defs = gold_uuts_def.gold_uuts

    # C9400 SUP-----------------------------------------
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_sup_pcbp2(self, tss, uuts):
        self.run_multi_container('C9400-SUP', 'PCBP2', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_sup_pcb2c(self, tss, uuts):
        self.run_multi_container('C9400-SUP', 'PCB2C', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_sup_pcbst(self, tss, uuts):
        self.run_multi_container('C9400-SUP', 'PCBST', tss=tss, uuts=uuts)

    # C9400 LC-----------------------------------------
    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_lc_pcbp2(self, tss, uuts):
        self.run_multi_container('C9400-LC', 'PCBP2', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_lc_pcbpm(self, tss, uuts):
        self.run_multi_container('C9400-LC', 'PCBPM', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_lc_pcb2c(self, tss, uuts):
        self.run_multi_container('C9400-LC', 'PCB2C', tss=tss, uuts=uuts)

    @pytest.mark.skipif(False, reason="None.")
    @pytest.mark.parallel
    def test_prod_sim_run_c9400_lc_pcbst(self, tss, uuts):
        self.run_multi_container('C9400-LC', 'PCBST', tss=tss, uuts=uuts)
