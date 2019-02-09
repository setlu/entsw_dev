"""
C3K, C9300 Config
"""

from apollo.libs import lib
import apollo.scripts.entsw.configs.common.c3k.c3k_common_stations as c3k_common_stations


__version__ = "0.2.3"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ['bborel', 'steli2']
__copyright__ = "Copyright 2015, Cisco Systems"

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}

PIDS_GEN2 = [
    '73-16285-*', '73-16649-*', '73-16622-*',                # GladiatorCSR - 12/24/48
    '73-16297-*', '73-15805-*', '73-15804-*',                # Edison-NewtonCSR - 24T/24P/24U
    '73-16296-*', '73-15800-*', '73-15799-*',                # Edison-NewtonCSR - 48T/48P/48U
    '73-15756-*', '73-15755-*',                              # OrstedCR - 24/48
    '73-15839-*', '73-14445-*',                              # PlanckCR - 12/24
]
PIDS_GEN3 = [
    # '73-17952-*', '73-17953-*', '73-17954-*',                # Nyquist-Shannon - 24T/24P/24U
    # '73-17955-*', '73-17956-*', '73-17957-*',                # Nyquist-Shannon - 48U/48P/48U
    # '73-17958-*', '73-17959-*',                              # Nyquist-Hartely - 24U/48U
    # '73-18270-*', '73-18271-*', '73-18272-*',                # NyquistCR-Shannon - 24T/24P/24U
    '73-18273-*',  # '73-18274-*', '73-18275-*',               # NyquistCR-Shannon - 48U/48P/48U
    # '73-18276-*', '73-18277-*',                              # NyquistCR-Hartely - 24U/48U
    # '73-18506-*',                                            # NyquistCR-Whittaker - 48
    # '73-19168-*', '73-19170-*', '73-19167-*', '73-19169-*',  # Franklin-DOGOOD24
    # '73-19103-*', '73-19131-*', '73-19102-*', '73-19130-*',  # Franklin-DOGOOD48
]


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c3k_config():
    """
    :return:
    """
    show_version()
    c3k_common_stations.show_version()

    config = lib.get_station_configuration()

    # PCB2C ---------------------------------------------------------
    station_details = dict(
        product_line='C9300', generation='GEN3',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.5', ts_start_port=TS_START_PORT['2900'] + 8,
        chamber_ts_ip='10.1.1.5', chamber_ts_port=TS_START_PORT['2900'] + 1,
        chamber_model='watlow_yinhe',
        psB_ts_ip=None, psB_ts_start_port=0,
        assign_abort_user=['steli2', 'bborel', 'rotian'],
    )
    c3k_common_stations.c3k_switch_pcb2c_common(config, **station_details)

    return
