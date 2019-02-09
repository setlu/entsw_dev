"""
9400 Config (Lab)
Macallan
"""

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat4 import stations as cat4_stations

__version__ = "2.0.0"
__title__ = "Enterprise Switching C4k Config for Cisco Labs "
__author__ = ['gchew', 'bborel', 'krauss']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c9400_config():
    """
    :return:
    """
    show_version()
    cat4_stations.show_version()

    config = lib.get_station_configuration()

    # SUPERVISOR STATIONS PCBP2, PCBST
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip='172.28.106.19',
        ts_ip='10.1.1.3',
        ts_start_port=2003,
        psu_separate_control=False,
        chassis='SUPERVISOR_SEVEN_SLOT_A',
        chassis_count=1
    )
    cat4_stations.sup_pcbp2(config, **station_details)
    cat4_stations.sup_pcbst(config, **station_details)
    cat4_stations.sup_debug(config, **station_details)

    # SUPERVISOR STATIONS PCB2C
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip='172.28.106.19',
        ts_ip='10.1.1.3',
        ts_start_port=2003,
        psu_separate_control=False,
        chamber_ts_ip='10.1.1.3',
        chamber_ts_port=2007,
        chassis='SUPERVISOR_SEVEN_SLOT_A',
        chassis_count=1
    )
    cat4_stations.sup_pcb2c(config, **station_details)

    # LINECARD STATIONS
    # -----------------------------------------------------------------
    station_details = dict(
        product_line='C9400',
        server_ip='172.28.106.19',
        ts_ip='10.1.1.3',
        ts_start_port=2003,
        chamber_ts_ip='10.1.1.3',
        chamber_ts_port=2009,
        poe_ts_ip=None,
        poe_ts_start_port=None,
        chassis='LINECARD_SEVEN_SLOT_2S',
        chassis_count=1
    )
    cat4_stations.linecard_pcbp2(config, **station_details)
    cat4_stations.linecard_pcb2c(config, **station_details)
    cat4_stations.linecard_pcbpm(config, **station_details)
    cat4_stations.linecard_pcbst(config, **station_details)
    cat4_stations.linecard_debug(config, **station_details)

    return
