"""
C2K Config (JPE dev)
"""

from apollo.libs import lib
import apollo.config.common.c2k.c2k_common_stations as c2k_common_stations

__version__ = "0.0.2"
__title__ = "Enterprise Switching C2k Config for JPE"
__author__ = ['bborel', 'JPE_Team']


TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, 'LantronixUSB': 2017}

QUAKE_MOTHERBOARD_PIDS = ['73-18785-*', '73-18785-*', '73-18775-*', '73-18831-*', '73-18775-*']

QUAKE_BASE_PIDS = ['C9200-48T-4G', 'C9200-24T-4G', 'C9200-48P-4G', 'C9200-24P-4X', 'C9200-48P-4X', 'C9200-24T-4X',
                   'C9200-48T-4X', 'C9200-48P8X-2Y', 'C9200-24P8X-2Y', 'C9200-24P8X-4X', 'C9200-48P12X-4X', 'C9200-24P-4G']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c2k_config():
    """
    :return:
    """
    show_version()
    c2k_common_stations.show_version()

    config = lib.get_station_configuration()

    #
    # PCBP2 ---------------------------------------------------------
    station_details = dict(
        product_line='C9200', generation='GEN3',
        station='Station_A_01', uut_count=8,
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    c2k_common_stations.c2k_switch_pcbp2_common(config, **station_details)
    c2k_common_stations.c2k_switch_debug_common(config, **station_details)

    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200', generation='GEN3',
        station='Station_A_01', uut_count=8,
        pid_cpn_list=QUAKE_BASE_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.2', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='root', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
    )
    c2k_common_stations.c2k_switch_sysft_common(config, **station_details)

    return


def uabu_c2k_config_OBSOLETE():
    """ C9200 family
    :return:
    """
    config = lib.get_station_configuration()

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C9200"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBP2"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    name = "Station_A_01"
    ts = testarea.add_test_station(name=name)
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcbp2_gen3')
    ts.add_pid_map(pid='73-*', sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_pcbp2_run.standard_switch')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutPOWER', host='10.1.1.2', protocol="ssh", user='root', password='default', timeout=120, model='Opengear')
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2003, power_connection='uutPOWER', timeout=120)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C9200"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBP2C"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    name = "Station_A_01"
    ts = testarea.add_test_station(name=name)
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcbp2c_gen3')
    ts.add_pid_map(pid='73-*', sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_pcbp2c_run.standard_switch')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutPOWER', host='10.1.1.2', protocol="ssh", user='root', password='default', timeout=120, model='Opengear')
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2003, power_connection='uutPOWER', timeout=120)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C9200"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "SYSFT"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    name = "Station_A_01"
    ts = testarea.add_test_station(name=name)
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_sysft_gen3')
    ts.add_pid_map(pid='73-*', sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_sysft_run.standard_switch')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutPOWER', host='10.1.1.2', protocol="ssh", user='root', password='default', timeout=120, model='Opengear')
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2003, power_connection='uutPOWER', timeout=120)
