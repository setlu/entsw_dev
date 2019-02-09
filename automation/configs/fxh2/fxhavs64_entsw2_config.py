"""
CAT3/5 Config (FTX Lab)
Edison/Nyquist/Franklin/Adelphi
"""
from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations

__version__ = "1.0.0"
__title__ = "Enterprise Switching CATALYST Series 3 Config for FTX (fxh2) Lab"
__author__ = ['gchew', 'bborel', 'qingywu']

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_cat3_config():
    """
    :return:
    """
    show_version()
    cat3_stations.show_version()

    config = lib.get_station_configuration()

    # CAT3 (C9300/C9500) + CAT5 (C9500) STATIONS SYSFT
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='CATALYST',
        station='Station_CATALYST', uut_count=4,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.2', ts_start_port=2003,
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_sysft(config, **station_details)

    return
