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


def cat3_lab_config():
    """
    :return:
    """
    show_version()
    cat3_stations.show_version()

    config = lib.get_station_configuration()
    uut_count = 10

    # ================================================================================
    # C3650
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C3650',
        station='Station_A_01', uut_count=uut_count,
        server_ip='10.79.216.243', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.10', ts_start_port=TS_START_PORT['2900'],
        poe1_ts_ip='10.1.1.11', poe1_ts_start_port=TS_START_PORT['2900'] + (uut_count * 2),
        poe2_ts_ip='10.1.1.11', poe2_ts_start_port=TS_START_PORT['2900'] + (uut_count * 3),
        poe_model='Edgar3', poe_mfgr='Reach'
    )
    cat3_stations.switch_pcbst(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)
    # ================================================================================
