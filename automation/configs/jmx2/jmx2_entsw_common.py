"""
JMX Common Production Stations

Note: This file contains a set of common production stations for the site.
      ALL stations MUST use the appropriate 'CATALYST common station' configs!
      **WARNING**: Do not build custom stations. Please consult Cisco TDE if a 'CATALYST common station' config
                   does not meet the site needs.
                   'CATALYST common station' configs are found in apollo.scripts.entsw.configs.common
"""
from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat2 import stations as cat2_stations


__title__ = "Enterprise Switching Common Config for JMX"
__version__ = '2.0.0'
__author__ = 'bborel'

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, '4300': 2002, 'LantronixUSB': 2017}
QUAKE_MOTHERBOARD_PIDS = ['73-18785-*', '73-18785-*', '73-18775-*', '73-18831-*', '73-18775-*']
QUAKE_BASE_PIDS = ['C9200L-48T-4G', 'C9200L-24T-4G', 'C9200L-48P-4G', 'C9200L-24P-4X', 'C9200L-48P-4X', 'C9200L-24T-4X',
                   'C9200L-48T-4X', 'C9200-48P8X-2Y', 'C9200-24P8X-2Y', 'C9200-24P8X-4X', 'C9200-48P12X-4X',
                   'C9200L-24P-4G',
                   'C9200-*']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def cat2_dbgsys_production(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat2_stations.show_version()
    config = lib.get_station_configuration()
    #
    # PCBFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_01', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.3', ts_start_port=TS_START_PORT['2900'],
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_debug(config, **station_details)
    #
    return


def cat2_pcbft_production(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat2_stations.show_version()
    config = lib.get_station_configuration()
    #
    # PCBFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_01', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.3', ts_start_port=TS_START_PORT['2900'],
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_pcbft(config, **station_details)
    #
    return


def cat2_sysft_production(server_ip, dwnld_server_ip):
    """
    :return:
    """
    show_version()
    cat2_stations.show_version()
    config = lib.get_station_configuration()
    #
    # PCBFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200',
        station='Station_A_01', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_BASE_PIDS,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip='10.1.1.3', ts_start_port=TS_START_PORT['2900'],
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_sysft(config, **station_details)
    #
    return
