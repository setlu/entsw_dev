"""
C4K Config (Lab)
"""

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat4 import stations as cat4_stations

__version__ = "2.0.0"
__title__ = "Enterprise Switching C4k Config for Cisco Labs "
__author__ = ['bborel', 'gchew']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c4k_config():
    """
    :return:
    """
    show_version()
    cat4_stations.show_version()

    config = lib.get_station_configuration()

    # SUP STATIONS
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip='172.28.106.75',
        ts_ip='10.1.1.2',
        ts_start_port=2005,
        chamber_ts_ip='10.1.1.2',
        chamber_ts_port=2021,
        poe_ts_ip=None,
        poe_ts_start_port=None,
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
        server_ip='172.28.106.75',
        ts_ip='10.1.1.2',
        ts_start_port=2005,
        chamber_ts_ip='10.1.1.2',
        chamber_ts_port=2021,
        poe1_ts_ip=None,
        poe1_ts_start_port=None,
        poe_model='Edgar5',
        chassis='LINECARD_SEVEN_SLOT_1S',
        chassis_count=1
    )
    cat4_stations.linecard_pcbp2(config, **station_details)
    cat4_stations.linecard_pcb2c(config, **station_details)
    cat4_stations.linecard_pcbpm(config, **station_details)
    cat4_stations.linecard_pcbst(config, **station_details)
    cat4_stations.linecard_debug(config, **station_details)

    return
