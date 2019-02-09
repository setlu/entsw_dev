""" Dev Apollo

Continuous Integration Test Platform
Enterprise Switching
Host: cisavdams004
Primary IP   (eth0): 10.61.6.55
Secondary IP (eth1): 10.1.1.1
CIMC IP: 10.61.6.xx

"""
from apollo.libs import lib
import apollo.config.common.cat3.stations as cat3_stations


__title__ = "Enterprise Switching Common Config"
__version__ = '2.0.0'
__author__ = ['bborel']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c3k_config():
    """
    :return:
    """
    show_version()
    cat3_stations.show_version()

    config = lib.get_station_configuration()

    # ==========================================================================================================================================================
    # C3K
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C3850',
        station='Station_A_01', uut_count=1,
        server_ip='10.61.6.55', dwnld_server_ip='10.1.1.4',
        ts_ip='10.1.1.10', ts_start_port=2006,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_sysft(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)

    # ==========================================================================================================================================================
    # C9300
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_01', uut_count=1,
        server_ip='10.61.6.55', dwnld_server_ip='10.1.1.4',
        ts_ip='10.1.1.10', ts_start_port=2006,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_sysft(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)

    # ==========================================================================================================================================================
    # C9300L
    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L',
        station='Station_A_01', uut_count=1,
        server_ip='10.61.6.55', dwnld_server_ip='10.1.1.4',
        ts_ip='10.1.1.10', ts_start_port=2006,
        psB_ts_ip=None, psB_ts_start_port=0
    )
    cat3_stations.switch_sysft(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)
