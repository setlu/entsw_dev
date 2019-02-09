"""
C3650 Config
"""

from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations


__title__ = "Enterprise Switching C3650 for Flextronics (FDO) SAMPLE"
__version__ = '2.0.0'
__author__ = 'bborel'
__copyright__ = "Copyright 2015, Cisco Systems"

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}


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
        product_line='C3650',
        station='Station_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2900'],
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_pcbst(config, **station_details)
    #
    #
    # 2C ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Chamber_A_01', uut_count=16,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2900'],
        psB_ts_ip=None, psB_ts_start_port=0,
        chamber_ts_ip='10.1.1.3', chamber_ts_port=TS_START_PORT['2900'],
        chamber_model='simulator', chamber_name='Chamber1', chamber_sync_group='ChamberSync1'
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    #
    #
    # ASSY ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=10,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2900'],
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
        station='Station_A_01', uut_count=10,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2900'],
    )
    cat3_stations.switch_sysbi(config, **station_details)
