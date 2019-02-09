"""
Enterprise Switching Config File
--------------------------------
Host: fgnavp31
Primary IP   (eth0): 172.30.121.160
Secondary IP (eth1): 10.1.1.1

"""
from apollo.libs import lib


__version__ = "0.0.2"
__title__ = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__ = ''
__credits__ = ["UAT Team"]


def entsw_config():
    """ EntSw Config
    """
    entsw_development()
    return


def entsw_development():
    """ EntSw Cfg for Development
    :return:
    """
    config = lib.get_station_configuration()

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C3k_EntSw"
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
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft')
    ts.add_pid_map(pid='WS-C3850-*', sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch')
    server = dict(protocol='ssh', host='10.1.1.1', user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)

    # Containers
    for i in range(1, 5, 1):
        cont = ts.add_container(name="UUT{0:02d}".format(i))
        cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2003 + i - 1, timeout=120)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "EntSw_EngUtility-C3K"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))
    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "DBGSYS"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_eng_utility')
    ts.add_pid_map(pid='C3K', sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_eng_menu_run.eng_utility_menu')
    # Connections
    server = dict(protocol='ssh', host='10.1.1.1', user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    containers = []
    for i in range(1, 5, 1):
        cont = ts.add_container(name="UUT{0:02}".format(i))
        # Connections
        # The UUT connections are NOT shared since we must avoid interference from other running containers
        cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2003 + i - 1, timeout=120)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        containers.append(cont)
    return
