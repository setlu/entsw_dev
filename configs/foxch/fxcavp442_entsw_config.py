"""
C3K C9300 Config
"""

from apollo.libs import lib
import apollo.scripts.entsw.configs.common.c3k.c3k_common_stations as c3k_common_stations

__version__ = "0.2.1"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ['bborel', 'steli2']
__copyright__ = "Copyright 2015, Cisco Systems"

TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003}

PIDS_GEN2 = ['WS-C3850-12XS', 'WS-C3850-24XS', 'WS-C3850-48XS',                    # Gladiator
             'WS-C3850-24T', 'WS-C3850-24P', 'WS-C3850-24U',                       # Edison-Newton
             'WS-C3850-48T', 'WS-C3850-48P', 'WS-C3850-48U',                       # Edison-Newton
             'WS-C3850-24XU', 'WS-C3850-12X48U',                                   # Orsted
             'WS-C3850-12S', 'WS-C3850-24S',                                       # Planck
             ]
PIDS_GEN3 = ['C9300-24T', 'C9300-24P', 'C9300-24U',                                # Nyquist-Shannon
             'C9300-48T', 'C9300-48P', 'C9300-48U',                                # Nyquist-Shannon
             'C9300-24UX', 'C9300-48UXM',                                          # Nyquist-Hartely
             'C9300-48UN'                                                          # Nyquist-Whittaker
             ]


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def uabu_c3k_config():
    """ WS-C3000, C9300
    :return:
    """

    show_version()
    c3k_common_stations.show_version()

    config = lib.get_station_configuration()

    station_lookup = {'Station_A_01': {'ip': '10.1.1.2', 'ts': 2003, 'uut_count': 16},
                      'Station_A_02': {'ip': '10.1.1.2', 'ts': 2019, 'uut_count': 16},
                      'Station_A_03': {'ip': '10.1.1.3', 'ts': 2003, 'uut_count': 16},
                      'Station_A_04': {'ip': '10.1.1.3', 'ts': 2019, 'uut_count': 16},
                      'Station_A_05': {'ip': '10.1.1.4', 'ts': 2003, 'uut_count': 16},
                      'Station_A_06': {'ip': '10.1.1.4', 'ts': 2019, 'uut_count': 16},
                      }

    #
    # SYSBI ---------------------------------------------------------
    for i in sorted(station_lookup):
        station_details = dict(
            product_line='WS-C3K', generation='GEN2',
            station='{}'.format(i), uut_count=int('{}'.format(station_lookup[i]['uut_count'])),
            pid_cpn_list=PIDS_GEN2,
            server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
            ts_ip='{}'.format(station_lookup[i]['ip']), ts_start_port=int('{}'.format(station_lookup[i]['ts'])),
            assign_abort_user=['steli2', 'bborel', 'rotian'],
        )
        c3k_common_stations.c3k_switch_sysbi_common(config, **station_details)

        # C9300
        station_details = dict(
            product_line='C9300', generation='GEN3',
            station='{}'.format(i), uut_count=int('{}'.format(station_lookup[i]['uut_count'])),
            pid_cpn_list=PIDS_GEN3,
            server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
            ts_ip='{}'.format(station_lookup[i]['ip']), ts_start_port=int('{}'.format(station_lookup[i]['ts'])),
            assign_abort_user=['steli2', 'bborel', 'rotian'],
        )
        c3k_common_stations.c3k_switch_sysbi_common(config, **station_details)

    return
