"""
C4K Config (Lab Development)
"""

from apollo.libs import lib

__version__ = "0.0.1"
__title__ = "Enterprise Switching C4k Config for Cisco Labs"
__author__ = ['gchew', 'bborel', 'rluktong', 'jioh']

# All possible chassis arrangements in production testing for linecards.
# NOTE: These tables assume the single-SUP arrangement is always in the "primary sup slot".
LINECARD_TEN_SLOT_2S = {
    1: {'physical_slot': 1, 'sup_prime': 5, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 2, 'sup_prime': 5, 'device_instance': 2000, 'slot_map': 'b'},
    3: {'physical_slot': 3, 'sup_prime': 5, 'device_instance': 3000, 'slot_map': 'c'},
    4: {'physical_slot': 4, 'sup_prime': 5, 'device_instance': 4000, 'slot_map': 'd'},
    5: {'physical_slot': 7, 'sup_prime': 6, 'device_instance': 7000, 'slot_map': 'e'},
    6: {'physical_slot': 8, 'sup_prime': 6, 'device_instance': 8000, 'slot_map': 'f'},
    7: {'physical_slot': 9, 'sup_prime': 6, 'device_instance': 9000, 'slot_map': 'g'},
    8: {'physical_slot': 10, 'sup_prime': 6, 'device_instance': 10000, 'slot_map': 'h'}}
LINECARD_TEN_SLOT_1S = {
    1: {'physical_slot': 1, 'sup_prime': 5, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 2, 'sup_prime': 5, 'device_instance': 2000, 'slot_map': 'b'},
    3: {'physical_slot': 3, 'sup_prime': 5, 'device_instance': 3000, 'slot_map': 'c'},
    4: {'physical_slot': 4, 'sup_prime': 5, 'device_instance': 4000, 'slot_map': 'd'},
    5: {'physical_slot': 7, 'sup_prime': 5, 'device_instance': 7000, 'slot_map': 'e'},
    6: {'physical_slot': 8, 'sup_prime': 5, 'device_instance': 8000, 'slot_map': 'f'},
    7: {'physical_slot': 9, 'sup_prime': 5, 'device_instance': 9000, 'slot_map': 'g'},
    8: {'physical_slot': 10, 'sup_prime': 5, 'device_instance': 10000, 'slot_map': 'h'}}
LINECARD_SEVEN_SLOT_2S = {
    1: {'physical_slot': 1, 'sup_prime': 3, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 2, 'sup_prime': 3, 'device_instance': 2000, 'slot_map': 'b'},
    3: {'physical_slot': 5, 'sup_prime': 4, 'device_instance': 5000, 'slot_map': 'c'},
    4: {'physical_slot': 6, 'sup_prime': 4, 'device_instance': 6000, 'slot_map': 'd'},
    5: {'physical_slot': 7, 'sup_prime': 4, 'device_instance': 7000, 'slot_map': 'e'}}
LINECARD_SEVEN_SLOT_1S = {
    1: {'physical_slot': 1, 'sup_prime': 3, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 2, 'sup_prime': 3, 'device_instance': 2000, 'slot_map': 'b'},
    3: {'physical_slot': 5, 'sup_prime': 3, 'device_instance': 5000, 'slot_map': 'c'},
    4: {'physical_slot': 6, 'sup_prime': 3, 'device_instance': 6000, 'slot_map': 'd'},
    5: {'physical_slot': 7, 'sup_prime': 3, 'device_instance': 7000, 'slot_map': 'e'}}
LINECARD_FOUR_SLOT_2S = {
    1: {'physical_slot': 1, 'sup_prime': 2, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 4, 'sup_prime': 3, 'device_instance': 4000, 'slot_map': 'b'}}
LINECARD_FOUR_SLOT_1S = {
    1: {'physical_slot': 1, 'sup_prime': 2, 'device_instance': 1000, 'slot_map': 'a'},
    2: {'physical_slot': 4, 'sup_prime': 2, 'device_instance': 4000, 'slot_map': 'b'}}


def uabu_c4k_linecard_config():
    """ Macallan

        The following chassis arrangements are possible for the Macallan family:
        ----------------------------------------
        Container: 1  2  3  4        5  6  7  8
        Chassis:   1  2  3  4  S1 S2 7  8  9  10
        ----------------------------------------
        ------------------------------
        Container: 1  2        3  4  5
        Chassis:   1  2  S1 S2 5  6  7
        ------------------------------
        ---------------------
        Container: 1        2
        Chassis:   1  S1 S2 4
        ---------------------

    :return:
    """

    config = lib.get_station_configuration()

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C4K_Linecard"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBP2C"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    name = "Station_A_Chassis_01"
    chassis = LINECARD_SEVEN_SLOT_1S
    ts = testarea.add_test_station(name=name)
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcbp2c_linecard')
    ts.add_pid_map(pid='C9400-LC-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_linecard_pcbp2c_run.standard_linecard')
    server = dict(protocol='ssh', host='localhost', user='gen-apollo', password='Ad@pCr01!')
    sup1 = dict(host='10.1.1.2', protocol="telnet", port=2006, timeout=180)
    sup2 = dict(host='10.1.1.2', protocol="telnet", port=2007, timeout=180)
    # RUK added
    psu1 = dict(host='10.1.1.2', protocol="telnet", port=2008, timeout=180)
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_connection(name='uutTN_shared1', **sup1)
    ts.add_connection(name='uutTN_shared2', **sup2)
    # RUK added
    ts.add_connection(name='psu1_shared1', **psu1)
    # Containers
    containers = []
    for k, v in sorted(chassis.items()):
        cont = ts.add_container(name="UUT{0:02}".format(k))
        # Connections
        cont.add_connection(name='uutTN', shared_conn='uutTN_shared1', **sup1)
        cont.add_connection(name='uutTN_aux', shared_conn='uutTN_shared2', **sup2)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        # RUK added
        cont.add_connection(name='uutPOWER', shared_conn='psu1_shared1', **psu1)
        # Configuration Data
        cdata = dict(slot=k)
        cdata.update(v)
        cont.add_configuration_data(key='LINECARD', value=cdata)
        containers.append(cont)
    # Sync groups for sequence flow control
    for sg in ['LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal']:
        ts.add_sync_group(sg, containers)

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCB2C"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcb2c_linecard')
    ts.add_pid_map(pid='C9400-LC-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_linecard_pcb2c_run.standard_linecard')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2005, timeout=190)

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBPM"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcbpm_linecard')
    ts.add_pid_map(pid='C9400-LC-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_linecard_pcbpm_run.standard_linecard')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2005, timeout=190)
    cont.add_connection(name='POELB1', host='10.1.1.2', protocol="telnet", port=2006, timeout=190, model='Edgar4', manufacturer='Reach')
    cont.add_connection(name='POELB2', host='10.1.1.2', protocol="telnet", port=2003, timeout=190, model='Edgar4', manufacturer='Reach')
    # Configuration Data
    cont.add_configuration_data(key='POELB1', value={'portmap': '1-24', 'syncgroup': 'PoESync1'})
    cont.add_configuration_data(key='POELB2', value={'portmap': '1-24', 'syncgroup': 'PoESync1'})

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBST"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcbst_linecard')
    ts.add_pid_map(pid='C9400-LC-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_linecard_pcbst_run.standard_linecard')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2005, timeout=190)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "C4K_Supervisor"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBP2C"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcbp2c_sup')
    ts.add_pid_map(pid='C9400-SUP-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_sup_pcbp2c_run.standard_supervisor')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2006, timeout=190)

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCB2C"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcb2c_sup')
    ts.add_pid_map(pid='C9400-SUP-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_sup_pcb2c_run.standard_supervisor')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2005, timeout=190)

    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "PCBST"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_pcbst_sup')
    ts.add_pid_map(pid='C9400-SUP-*', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_sup_pcbst_run.standard_supervisor')
    # Containers
    cont = ts.add_container(name="UUT01")
    # Connections
    cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2005, timeout=190)

    # ==================================================================================================================
    # PL
    print("-" * 100)
    name = "EntSw_EngUtility-C4K"
    pl = config.add_production_line(name=name)
    print("{0}".format(name))
    # ------------------------------------------------------------------------------------------------------------------
    # TA
    name = "DBGSYS"
    testarea = pl.add_area(name=name)
    print("  {0}".format(name))
    # TS
    ts = testarea.add_test_station(name="Station_A_01")
    chassis = LINECARD_SEVEN_SLOT_1S
    ts.assign_pre_sequence(sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_all_pre_sequences.pre_eng_utility')
    ts.add_pid_map(pid='C9400', sequence_definition='apollo.scripts.entsw.cat4.area_sequences.c4k_eng_menu_run.eng_utility_menu')
    # Connections
    server = dict(protocol='ssh', host='172.28.106.75', user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    containers = []
    for k, v in sorted(chassis.items()):
        cont = ts.add_container(name="UUT{0:02}".format(k))
        # Connections
        # The UUT connections are NOT shared since we must avoid interference from other running containers
        cont.add_connection(name='uutTN', host='10.1.1.2', protocol="telnet", port=2006)
        cont.add_connection(name='uutTN_aux', host='10.1.1.2', protocol="telnet", port=2007)
        cont.add_connection(name='uutPOWER', host='10.1.1.2', protocol="telnet", port=2008)
        cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        # Configuration Data
        cdata = dict(slot=k)
        cdata.update(v)
        cont.add_configuration_data(key='LINECARD', value=cdata)
        containers.append(cont)
    return
