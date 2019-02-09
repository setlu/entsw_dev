"""
C3K, C9300 Config
"""

from apollo.libs import lib
import apollo.config.common.c3k.c3k_common_stations as c3k_common_stations


__version__ = "0.2.3"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ['bborel', 'steli2', 'rotian']
__copyright__ = "Copyright 2015, Cisco Systems"

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}

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
    '73-19171-*', '73-19172-*', '73-19177-*'
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

    uut_count = 2  # temporary until the station is properly wired
    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='WS-C3K', generation='GEN2',
        station='Station_A_01', uut_count=uut_count,
        pid_cpn_list=PIDS_GEN2,
        server_ip='10.1.1.250', dwnld_server_ip='10.1.1.250',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2800'],
        psB_ts_ip='10.1.1.2', psB_ts_start_port=TS_START_PORT['2800'] + uut_count,
        poe1_ts_ip='10.1.1.2', poe1_ts_start_port=TS_START_PORT['2800'] + (uut_count * 2),
        poe2_ts_ip='10.1.1.2', poe2_ts_start_port=TS_START_PORT['2800'] + (uut_count * 3),
        poe_model='Edgar4', poe_mfgr='Reach'

    )
    c3k_common_stations.c3k_switch_pcbst_common(config, **station_details)
    c3k_common_stations.c3k_switch_debug_common(config, **station_details)

    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300', generation='GEN3',
        station='Station_A_01', uut_count=uut_count,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.250', dwnld_server_ip='10.1.1.250',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2800'],
        psB_ts_ip='10.1.1.2', psB_ts_start_port=TS_START_PORT['2800'] + uut_count,
        poe1_ts_ip='10.1.1.2', poe1_ts_start_port=TS_START_PORT['2800'] + (uut_count * 2),
        poe2_ts_ip='10.1.1.2', poe2_ts_start_port=TS_START_PORT['2800'] + (uut_count * 3),
        poe_model='Edgar4', poe_mfgr='Reach'

    )
    c3k_common_stations.c3k_switch_pcbst_common(config, **station_details)
    c3k_common_stations.c3k_switch_debug_common(config, **station_details)

    #
    # BST (Part1 + Part2) ---------------------------------------------------------
    station_details = dict(
        product_line='C9300', generation='GEN3',
        test_area='PCBDL',
        seq_def_lookup={('PCBDL', 'GEN3'): ('apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst_gen3',
                                            'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch_part1')},
        station='StationPart1_A_01', uut_count=uut_count,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.250', dwnld_server_ip='10.1.1.250',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2800'],
        psB_ts_ip='10.1.1.2', psB_ts_start_port=TS_START_PORT['2800'] + uut_count,
    )
    c3k_common_stations.c3k_switch_pcbst_common(config, **station_details)
    c3k_common_stations.c3k_switch_debug_common(config, **station_details)
    #
    station_details = dict(
        product_line='C9300', generation='GEN3',
        seq_def_lookup={('PCBST', 'GEN3'): ('apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst_gen3_auto',
                                            'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch_part2')},
        station='StationPart2_A_01', uut_count=uut_count,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.250', dwnld_server_ip='10.1.1.250',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2800'],
        psB_ts_ip='10.1.1.2', psB_ts_start_port=TS_START_PORT['2800'] + uut_count,
        poe1_ts_ip='10.1.1.2', poe1_ts_start_port=TS_START_PORT['2800'] + (uut_count * 2),
        poe2_ts_ip='10.1.1.2', poe2_ts_start_port=TS_START_PORT['2800'] + (uut_count * 3),
        poe_model='Edgar4', poe_mfgr='Reach'
    )
    c3k_common_stations.c3k_switch_pcbst_common(config, **station_details)
    c3k_common_stations.c3k_switch_debug_common(config, **station_details)

    #
    # BST ---------------------------------------------------------
    station_details = dict(
        product_line='C9300L', generation='GEN3L',
        station='Station_A_01', uut_count=uut_count,
        pid_cpn_list=PIDS_GEN3,
        server_ip='10.1.1.250', dwnld_server_ip='10.1.1.250',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['2800'],
        psB_ts_ip='10.1.1.2', psB_ts_start_port=TS_START_PORT['2800'] + uut_count,
        poe1_ts_ip='10.1.1.2', poe1_ts_start_port=TS_START_PORT['2800'] + (uut_count * 2),
        poe2_ts_ip='10.1.1.2', poe2_ts_start_port=TS_START_PORT['2800'] + (uut_count * 3),
        poe_model='Edgar4', poe_mfgr='Reach'
    )
    c3k_common_stations.c3k_switch_pcbst_common(config, **station_details)
    c3k_common_stations.c3k_switch_debug_common(config, **station_details)

    return
