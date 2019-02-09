"""
Cisco Labs Common
"""
from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat2 import stations as cat2_stations
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations
from apollo.scripts.entsw.configs.common.cat4 import stations as cat4_stations
from apollo.scripts.entsw.configs.common.universal import stations as universal_stations


__title__ = "Enterprise Switching Common Config for Cisco Labs"
__version__ = '2.0.0'
__author__ = 'bborel'

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def cat3_lab(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat3_stations.show_version()

    config = lib.get_station_configuration()

    # ==========================================================================================================================================================
    # C3850
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    #
    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C3850.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C3850.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C3850.area_sequences.pcb2c.standard_switch_unittest'),
        station='Chamber_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.89.133.9', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber1', chamber_sync_group='ChamberSync1'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        loadbox_ts_ip=None, loadbox_ts_start_port=0,
        loadbox_sync_gp='StackPwrSync1', loadbox_sync_gp_size=4,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_assy(config, **station_details)
    #
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    cat3_stations.switch_sysbi(config, **station_details)
    #
    #
    # SYSASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Line 03 UABU', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
    )
    cat3_stations.switch_sysassy(config, **station_details)
    #
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_sysft(config, **station_details)
    #
    #
    # DEBUG ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_debug(config, **station_details)
    #
    #

    # ==========================================================================================================================================================
    # C3650
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    #
    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C3650.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C3650.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C3650.area_sequences.pcb2c.standard_switch_unittest'),
        station='Chamber_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.89.133.9', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber1', chamber_sync_group='ChamberSync1'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        loadbox_ts_ip=None, loadbox_ts_start_port=0,
        loadbox_sync_gp='StackPwrSync1', loadbox_sync_gp_size=4,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_assy(config, **station_details)
    #
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    cat3_stations.switch_sysbi(config, **station_details)
    #
    #
    # SYSASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Line 03 UABU', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
    )
    cat3_stations.switch_sysassy(config, **station_details)
    #
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_sysft(config, **station_details)
    #
    #
    # DEBUG ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    cat3_stations.switch_debug(config, **station_details)
    #
    #

    # ==========================================================================================================================================================
    # C9300
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_03', uut_count=5,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    station_details = dict(
        product_line='C9300',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
        poe1_ts_ip='10.89.133.8', poe1_ts_start_port=2018,
        poe_sync_gp='PoESync1',
        poe_model='Edgar4', poe_mfgr='Reach',
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    #
    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.standard_switch_unittest'),
        station='Chamber_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.89.133.56', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber3', chamber_sync_group='ChamberSync3'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    station_details = dict(
        product_line='C9300',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C9300.area_sequences.pcb2c.standard_switch_unittest'),
        station='Chamber_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.89.133.8', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber2', chamber_sync_group='ChamberSync2'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
        loadbox_ts_ip=None, loadbox_ts_start_port=0,
        loadbox_sync_gp='StackPwrSync3', loadbox_sync_gp_size=4,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_assy(config, **station_details)
    #
    station_details = dict(
        product_line='C9300',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
        loadbox_ts_ip=None, loadbox_ts_start_port=0,
        loadbox_sync_gp='StackPwrSync2', loadbox_sync_gp_size=4,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_assy(config, **station_details)
    #
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    cat3_stations.switch_sysbi(config, **station_details)
    #
    station_details = dict(
        product_line='C9300',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    cat3_stations.switch_sysbi(config, **station_details)
    #
    #
    # SYSASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Line 03 UABU', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
    )
    cat3_stations.switch_sysassy(config, **station_details)
    #
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
    )
    cat3_stations.switch_sysft(config, **station_details)
    station_details = dict(
        product_line='C9300',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
    )
    cat3_stations.switch_sysft(config, **station_details)
    #
    #
    # DEBUG ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
    )
    cat3_stations.switch_debug(config, **station_details)
    #
    station_details = dict(
        product_line='C9300',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
        poe1_ts_ip='10.89.133.8', poe1_ts_start_port=2018,
        # poe2_ts_ip='10.89.133.8', poe2_ts_start_port=2016,
        # poe3_ts_ip='10.89.133.8', poe3_ts_start_port=2015,
        # poe4_ts_ip='10.89.133.8', poe4_ts_start_port=2014,
        poe_sync_gp='PoESync1',
        poe_share_ports=24,
        poe_model='Edgar4', poe_mfgr='Reach',
        fan_ts_ip='10.89.133.8', fan_ts_start_port=2011, fan_count=1,
    )
    cat3_stations.switch_debug(config, **station_details)

    # ==========================================================================================================================================================
    # C9300L
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    #
    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.standard_switch_unittest'),
        station='Chamber_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.89.133.56', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber3', chamber_sync_group='ChamberSync3'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
        loadbox_ts_ip=None, loadbox_ts_start_port=0,
        loadbox_sync_gp='StackPwrSync3', loadbox_sync_gp_size=4,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_assy(config, **station_details)
    #
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    cat3_stations.switch_sysbi(config, **station_details)
    #
    #
    # SYSASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Line 03 UABU', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
    )
    cat3_stations.switch_sysassy(config, **station_details)
    #
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
    )
    cat3_stations.switch_sysft(config, **station_details)
    #
    #
    # DEBUG ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_03', uut_count=3,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003 + 5,
    )
    cat3_stations.switch_debug(config, **station_details)

    return


def cat2_lab(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat2_stations.show_version()

    config = lib.get_station_configuration()

    TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, 'LantronixUSB': 2017}
    QUAKE_MOTHERBOARD_PIDS = ['73-18785-*', '73-18785-*', '73-18775-*', '73-18831-*', '73-18775-*', '73-*']
    QUAKE_BASE_PIDS = ['C9200-48T-4G', 'C9200-24T-4G', 'C9200-48P-4G', 'C9200-24P-4X', 'C9200-48P-4X', 'C9200-24T-4X',
                       'C9200-48T-4X', 'C9200-48P8X-2Y', 'C9200-24P8X-2Y', 'C9200-24P8X-4X', 'C9200-48P12X-4X', 'C9200-24P-4G',
                       'C9200R-*', 'C9200-*', 'C9200L-*']

    #
    # PCBP2 ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_02', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.51', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_pcbp2(config, **station_details)
    cat2_stations.switch_debug(config, **station_details)
    #

    #
    # PCBPM ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_02', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.51', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_pcbpm(config, **station_details)
    #

    # PCB2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Chamber_A_02', uut_count=8,
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat2.C9200.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat2.C9200.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat2.C9200.area_sequences.pcb2c.standard_switch_unittest'),
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.51', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        chamber_ts_ip='10.89.133.9', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber2', chamber_sync_group='ChamberSync2'
    )
    cat2_stations.switch_pcb2c(config, **station_details)

    #
    # PCBFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_02', uut_count=8,
        pid_cpn_list=QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.51', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_pcbft(config, **station_details)

    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_02', uut_count=8,
        pid_cpn_list=QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.51', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_sysft(config, **station_details)

    return


def cat4_lab(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat4_stations.show_version()

    config = lib.get_station_configuration()

    # SUPERVISOR STATIONS PCBP2, PCBST
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        psu_separate_control=False,
        chamber_ts_ip='10.89.133.9', chamber_ts_port=2018,
        chassis='SUPERVISOR_SEVEN_SLOT_A',
        chassis_count=1
    )
    cat4_stations.sup_pcbp2(config, **station_details)
    cat4_stations.sup_pcb2c(config, **station_details)
    cat4_stations.sup_pcbst(config, **station_details)
    cat4_stations.sup_debug(config, **station_details)

    # LINECARD STATIONS
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
        chamber_ts_ip='10.89.133.9', chamber_ts_port=2018,
        poe_ts_ip=None,
        poe_ts_start_port=None,
        chassis='LINECARD_SEVEN_SLOT_2S',
        chassis_count=1
    )
    cat4_stations.linecard_pcbp2(config, **station_details)
    cat4_stations.linecard_pcb2c(config, **station_details)
    cat4_stations.linecard_pcbpm(config, **station_details)
    cat4_stations.linecard_pcbst(config, **station_details)
    cat4_stations.linecard_debug(config, **station_details)

    return


def universal_lab(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    universal_stations.show_version()

    config = lib.get_station_configuration()


    # ==========================================================================================================================================================
    # UNIVERSAL
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='CATALYST',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.9', ts_start_port=2003,
    )
    universal_stations.switch_sysft(config, **station_details)
    station_details = dict(
        product_line='CATALYST',
        station='Station_A_03', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.56', ts_start_port=2003,
    )
    universal_stations.switch_sysft(config, **station_details)
    station_details = dict(
        product_line='CATALYST',
        station='Station_A_02', uut_count=8,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.89.133.8', ts_start_port=2003,
    )
    universal_stations.switch_sysft(config, **station_details)
