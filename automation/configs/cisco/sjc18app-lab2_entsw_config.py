"""
9300 Config (Lab)
"""
from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations

__version__ = "2.0.0"
__title__ = "Enterprise Switching C9300 Config for Cisco Labs "
__author__ = ['bborel', 'gchew', 'tnnguyen']

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

def c9300_config():
    config = lib.get_station_configuration()

    my_apollo_server_ip = '10.1.1.1'

    # C9300L
    #
    # BST & Debug: One PoE Slot ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='StationPoE_A_01', uut_count=1,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
        psB_ts_ip=None, psB_ts_start_port=0,
        poe1_ts_ip='10.1.1.3', poe1_ts_start_port=2006,
        poe2_ts_ip='10.1.1.3', poe2_ts_start_port=2007,
        poe_sync_gp='PoESync1',
        poe_model='Edgar4', poe_mfgr='Reach',
    )
    cat3_stations.switch_pcbst(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)
    #
    station_details = dict(
        product_line='C9300L',
        station='Station_A_02', uut_count=4,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_pcbst(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)

    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        seq_def=ApolloSeq(
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.pre',
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.pre2',
            'apollo.scripts.entsw.cat3.C9300L.area_sequences.pcb2c.standard_switch_unittest'),
        station='ChamberSimulated_A_01', uut_count=4,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.1.1.3', chamber_ts_port=2018,
        chamber_model='simulator', chamber_name='Chamber3', chamber_sync_group='ChamberSync1'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_01', uut_count=4,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_pcbassy(config, **station_details)
    #
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_01', uut_count=4,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
    )
    cat3_stations.switch_pcbft(config, **station_details)
    #
    #
    # DF SYS Final ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_01', uut_count=4,
        server_ip=my_apollo_server_ip, dwnld_server_ip=my_apollo_server_ip,
        ts_ip='10.1.1.3', ts_start_port=2002,
    )
    cat3_stations.switch_sysft(config, **station_details)
