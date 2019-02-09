"""
C3K, C9300 Config
"""

from collections import namedtuple

from apollo.libs import lib
from apollo.scripts.entsw.configs.common.cat3 import stations as cat3_stations


__version__ = "0.1.1"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ['bborel, steli2']
__copyright__ = "Copyright 2015, Cisco Systems"

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

PIDS_GEN2 = [
    '73-16285-*', '73-16649-*', '73-16622-*',                # Gladiator
    '73-16297-*', '73-15805-*', '73-15799-*',                # Edison-Newton
    '73-16296-*', '73-15800-*', '73-15799-*',                # Edison-Newton
    '73-15756-*', '73-15755-*',                              # Orsted
    '73-15839-*', '73-14445-*',                              # Planck
]
PIDS_GEN3 = [
    '73-17952-*', '73-17953-*', '73-17954-*',                # Nyquist-Shannon
    '73-17955-*', '73-17956-*', '73-17957-*',                # Nyquist-Shannon
    '73-17958-*', '73-17959-*',                              # Nyquist-Hartely
    '73-18270-*', '73-18271-*', '73-18272-*',                # NyquistCR-Shannon
    '73-18273-*', '73-18274-*', '73-18275-*',                # NyquistCR-Shannon
    '73-18276-*', '73-18277-*',                              # NyquistCR-Hartely
    '73-18506-*',                                            # NyquistCR-Whittaker
    '73-19168-*', '73-19170-*', '73-19167-*', '73-19169-*',  # Franklin-DOGOOD24
    '73-19103-*', '73-19131-*', '73-19102-*', '73-19130-*',  # Franklin-DOGOOD48
]


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c3k_config():
    """
    :return:
    """
    show_version()

    config = lib.get_station_configuration()

    #
    # PCB2C ---------------------------------------------------------
    station_details = dict(
        product_line='WS-C3850',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=PIDS_GEN2,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.5', ts_start_port=TS_START_PORT['2800'] + 8,
        chamber_ts_ip='10.1.1.5', chamber_ts_port=TS_START_PORT['2800'] + 1,
        chamber_model='watlow_yinhe',
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)

    #
    # PCB2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9300',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.5', ts_start_port=TS_START_PORT['2800'] + 8,
        chamber_ts_ip='10.1.1.5', chamber_ts_port=TS_START_PORT['2800'] + 1,
        chamber_model='watlow_yinhe',
        psB_ts_ip=None, psB_ts_start_port=0,
    )
    cat3_stations.switch_pcb2c(config, **station_details)
    cat3_stations.switch_debug(config, **station_details)

    return
