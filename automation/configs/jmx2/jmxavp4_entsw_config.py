"""
C2K Config (JMX dev)
"""

from apollo.libs import lib

__version__ = "0.0.1"
__title__ = "Enterprise Switching C2k Config for JMX"
__author__ = ['bborel', 'JMX_Team']


def uabu_c2k_config():
    """ C9200 family
    :return:
    """
    config = lib.get_station_configuration()

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C9200_EntSw"
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
    ts.add_pid_map(pid='C9200*', sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_pcbp2c_run.standard_switch')
    server = dict(protocol='ssh', host='10.1.1.1', user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    # Containers & Connections
    for i in range(1, 5, 1):
        cont = ts.add_container(name="UUT{0:02d}".format(i))
        # cont.add_connection(name='uutPOWER', host='10.1.1.3', protocol="ssh", user='root', password='default', timeout=120, model='Opengear')
        cont.add_connection(name='uutPOWER', host='10.1.1.3', protocol="ssh", user='sysadmin', password='PASS', timeout=120, model='Lantronix')
        cont.add_connection(name='uutTN', host='10.1.1.3', protocol="telnet", port=2017 + i - 1, power_connection='uutPOWER', timeout=120)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "EntSw_EngUtility-C2K"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))
    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "DBGSYS"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_eng_utility')
    ts.add_pid_map(pid='C2K', sequence_definition='apollo.scripts.entsw.cat2.area_sequences.c2k_eng_menu_run.eng_utility_menu')
    # Connections
    server = dict(protocol='ssh', host='10.1.1.1', user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    containers = []
    # Containers & Connections
    for i in range(1, 5, 1):
        cont = ts.add_container(name="UUT{0:02d}".format(i))
        # cont.add_connection(name='uutPOWER', host='10.1.1.3', protocol="ssh", user='root', password='default', timeout=120, model='Opengear')
        cont.add_connection(name='uutPOWER', host='10.1.1.3', protocol="ssh", user='sysadmin', password='PASS', timeout=120, model='Lantronix')
        cont.add_connection(name='uutTN', host='10.1.1.3', protocol="telnet", port=2017 + i - 1, power_connection='uutPOWER', timeout=120)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        containers.append(cont)
    return
