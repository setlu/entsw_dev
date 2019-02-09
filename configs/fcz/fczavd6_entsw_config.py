"""
CATALYST Series 3 Config
"""

from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations
from apollo.scripts.entsw.configs.common.universal import stations as universal_stations


__title__ = "Enterprise Switching CATALYST Series 3 Config for DF Site Foxconn, Czech"
__version__ = '2.0.0'
__author__ = ['bborel', 'DF_Team']

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')


def entsw_cat3_config():
    """ CAT3 Config
    :return:
    """
    config = lib.get_station_configuration()

    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='CATALYST',
        station='Station_A_01', uut_count=16,
        server_ip='10.63.33.6', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.2', ts_start_port=2003,
    )
    universal_stations.switch_sysft(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)
