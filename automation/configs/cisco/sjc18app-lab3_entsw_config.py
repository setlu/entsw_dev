"""
C2K Config (JPE dev)
"""

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat2 import stations as cat2_stations

__version__ = "2.0.0"
__title__ = "Enterprise Switching C9200 Config"
__author__ = ['JPE_Team']

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, 'LantronixUSB': 2017}


def entsw_c9200_config():
    config = lib.get_station_configuration()
    station_details = dict(
        product_line='C9200',
        station='Station_A_02', uut_count=1,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.200', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    cat2_stations.switch_pcbp2(config, **station_details)
    cat2_stations.switch_pcbft(config, **station_details)
    # cat2_stations.switch_pcbpm(config, **station_details) (need Edgar)
    cat2_stations.switch_sysft(config, **station_details)
    cat2_stations.switch_debug(config, **station_details)
