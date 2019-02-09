"""
C3K, C9300 Config
"""

from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations


__version__ = "2.0.0"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ['bborel', 'steli2', 'rotian']
__copyright__ = "Copyright 2015, Cisco Systems"

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def cat3_config():
    show_version()

    config = lib.get_station_configuration()

    uut_count = 8  # temporary until the station is properly wired
    #
    # FST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_01', uut_count=uut_count,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.6', ts_start_port=TS_START_PORT['2900'],
        assign_abort_user=['steli2', 'bborel', 'rotian'],
    )
    cat3_stations.switch_sysbi(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)
    return
