"""
========================================================================================================================
C9400 COMMON Configs
========================================================================================================================
Macallan

    Below are the following chassis arrangements possible for the Macallan family.
    Container assignments depend on the type of station required.

    --------------------------------------------
    Sup Container:             1  2
    LC Container:  1  2  3  4        5  6  7  8
    Chassis:       1  2  3  4  S1 S2 7  8  9  10
    --------------------------------------------
    ----------------------------------
    Sup Container:       1  2
    LC Container:  1  2        3  4  5
    Chassis:       1  2  S1 S2 5  6  7
    ----------------------------------
    -------------------------
    Sup Container:    1  2
    LC Container:  1        2
    Chassis:       1  S1 S2 4
    -------------------------

***IMPORTANT***
The following stations are STANDARDIZED for ALLC9400 SWITCH products at ALL EMS PCBA & DF/ATO Partner sites:
    1. PCBA: BoardSystemTest or Pre2CornerTest            TAs = PCBP2
    2. PCBA: PoE Test (LineCards ONLY)                    TAs = PCBPM
    3. PCBA: 2-Corner/4-Corner Temperature Chamber Test   TAs = PCB2C
    4. PCBA: FinalSystemTest (SNT)                        TAs = PCBST
    5. DF:   SystemTest                                   TAs = SYSFT

Please contact Cisco TDE ProdOps/GMO TDEs if the standard configs do not provide the necessary setup!
These configs will be highly governed and should not be changed unless by team review.

***WARNING***
DO NOT perform any IP calculation based on UUT number for config storage; this can create potential conflicts
with multi-stations on the Apollo server and/or same test network!!
Please use the IP assignment utility within a step.  The test network mask should be adjusted for 255.255.0.0.
Refer to "common_utils.get_ip_addr_assignment(...)" for more details.
"""
from collections import namedtuple

__version__ = "2.0.0"
__title__ = "Enterprise Switching CATALYST Series 4 Common Station Configs"
__author__ = ['bborel']

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

# All possible chassis arrangements in production testing for Linecards.
# NOTE: These tables assume the single-SUP arrangement is always in the "primary sup slot".
LINECARD_CHASSIS = {
    'LINECARD_TEN_SLOT_2S': {
        1: {'physical_slot': 1, 'sup_prime': 5, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 2, 'sup_prime': 5, 'device_instance': 2000, 'slot_map': 'b', 'conn_suffix': '1'},
        3: {'physical_slot': 3, 'sup_prime': 5, 'device_instance': 3000, 'slot_map': 'c', 'conn_suffix': '1'},
        4: {'physical_slot': 4, 'sup_prime': 5, 'device_instance': 4000, 'slot_map': 'd', 'conn_suffix': '1'},
        5: {'physical_slot': 7, 'sup_prime': 6, 'device_instance': 7000, 'slot_map': 'e', 'conn_suffix': '2'},
        6: {'physical_slot': 8, 'sup_prime': 6, 'device_instance': 8000, 'slot_map': 'f', 'conn_suffix': '2'},
        7: {'physical_slot': 9, 'sup_prime': 6, 'device_instance': 9000, 'slot_map': 'g', 'conn_suffix': '2'},
        8: {'physical_slot': 10, 'sup_prime': 6, 'device_instance': 10000, 'slot_map': 'h', 'conn_suffix': '2'}},
    'LINECARD_TEN_SLOT_1S': {
        1: {'physical_slot': 1, 'sup_prime': 5, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 2, 'sup_prime': 5, 'device_instance': 2000, 'slot_map': 'b', 'conn_suffix': '1'},
        3: {'physical_slot': 3, 'sup_prime': 5, 'device_instance': 3000, 'slot_map': 'c', 'conn_suffix': '1'},
        4: {'physical_slot': 4, 'sup_prime': 5, 'device_instance': 4000, 'slot_map': 'd', 'conn_suffix': '1'},
        5: {'physical_slot': 7, 'sup_prime': 5, 'device_instance': 7000, 'slot_map': 'e', 'conn_suffix': '1'},
        6: {'physical_slot': 8, 'sup_prime': 5, 'device_instance': 8000, 'slot_map': 'f', 'conn_suffix': '1'},
        7: {'physical_slot': 9, 'sup_prime': 5, 'device_instance': 9000, 'slot_map': 'g', 'conn_suffix': '1'},
        8: {'physical_slot': 10, 'sup_prime': 5, 'device_instance': 10000, 'slot_map': 'h', 'conn_suffix': '1'}},
    'LINECARD_SEVEN_SLOT_2S': {
        1: {'physical_slot': 1, 'sup_prime': 3, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 2, 'sup_prime': 3, 'device_instance': 2000, 'slot_map': 'b', 'conn_suffix': '1'},
        3: {'physical_slot': 5, 'sup_prime': 4, 'device_instance': 5000, 'slot_map': 'c', 'conn_suffix': '2'},
        4: {'physical_slot': 6, 'sup_prime': 4, 'device_instance': 6000, 'slot_map': 'd', 'conn_suffix': '2'},
        5: {'physical_slot': 7, 'sup_prime': 4, 'device_instance': 7000, 'slot_map': 'e', 'conn_suffix': '2'}},
    'LINECARD_SEVEN_SLOT_1S': {
        1: {'physical_slot': 1, 'sup_prime': 3, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 2, 'sup_prime': 3, 'device_instance': 2000, 'slot_map': 'b', 'conn_suffix': '1'},
        3: {'physical_slot': 5, 'sup_prime': 3, 'device_instance': 5000, 'slot_map': 'c', 'conn_suffix': '1'},
        4: {'physical_slot': 6, 'sup_prime': 3, 'device_instance': 6000, 'slot_map': 'd', 'conn_suffix': '1'},
        5: {'physical_slot': 7, 'sup_prime': 3, 'device_instance': 7000, 'slot_map': 'e', 'conn_suffix': '1'}},
    'LINECARD_FOUR_SLOT_2S': {
        1: {'physical_slot': 1, 'sup_prime': 2, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 4, 'sup_prime': 3, 'device_instance': 4000, 'slot_map': 'b', 'conn_suffix': '2'}},
    'LINECARD_FOUR_SLOT_1S': {
        1: {'physical_slot': 1, 'sup_prime': 2, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        2: {'physical_slot': 4, 'sup_prime': 2, 'device_instance': 4000, 'slot_map': 'b', 'conn_suffix': '1'}}
}

# All possible chassis arrangements in production testing for Supervisors.
SUPERVISOR_CHASSIS = {
    'SUPERVISOR_FOUR_SLOT_A': {
        1: {'physical_slot': 2, 'linecards': [1, 4], 'physical_slot_auxsup': 3, 'device_instance': 0},
        2: {'physical_slot': 3, 'linecards': [4, 1], 'physical_slot_auxsup': 2, 'device_instance': 0}},
    'SUPERVISOR_SEVEN_SLOT_A': {
        1: {'physical_slot': 3, 'linecards': [5, 7], 'physical_slot_auxsup': 4, 'device_instance': 0},
        2: {'physical_slot': 4, 'linecards': [7, 5], 'physical_slot_auxsup': 3, 'device_instance': 0}},
    'SUPERVISOR_TEN_SLOT_A': {
        1: {'physical_slot': 5, 'linecards': [7, 8], 'physical_slot_auxsup': 6, 'device_instance': 0},
        2: {'physical_slot': 6, 'linecards': [8, 7], 'physical_slot_auxsup': 5, 'device_instance': 0}}
}

# ALL PIDs/CPNs Supported
PID_CPN_MAPS = {
    'C4500':    ['WS-C4500*', '73-*'],
    'C9400':    ['C9400*', '73-*'],
    'ALL':      ['WS-C4500*', 'C9400*', 'C4*', '73-*'],
    'CATALYST': ['WS-C4500*', 'C9400*', 'C4*', '73-*']
}


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# ======================================================================================================================
# SUPERVISOR

# ----------------------------------------------------------------------------------------------------------------------
def sup_pcbp2(config, **kwargs):
    """ Supervisor PCBP2
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBP2')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chassis=chassis)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-SUP'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    # TS
    two_sups = True  # Required for sup testing!
    for chassis_num in range(0, chassis_count, 1):
        st_name = "{0}_Chassis_{1:02}".format(station, chassis_num + 1)
        print("    {0}".format(st_name))
        ts = ta.add_test_station(name=st_name)
        ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
        for pid in pid_cpn_list:
            ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
        # Containers
        cont1 = ts.add_container(name="UUT01")
        cont2 = ts.add_container(name="UUT02")
        # Connections
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, p = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared1', **server)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2)
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        print("    UUT01 = {0}:{1}".format(ts_ip, p))
        print("    UUT02 = {0}:{1}".format(ts_ip, p + 1))
        # Containers
        cont1.add_connection(name='uutTN', shared_conn='uutTN_shared1', **sup1)
        cont1.add_connection(name='uutTN_aux', shared_conn='uutTN_shared2', **sup2)
        cont1.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont1.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        cont2.add_connection(name='uutTN', shared_conn='uutTN_shared2', **sup2)
        cont2.add_connection(name='uutTN_aux', shared_conn='uutTN_shared1', **sup1)
        cont2.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont2.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        # Configuration Data
        cont1.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(1, {}))
        cont2.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(2, {}))
        # Sync groups for sequence flow control
        for sg in ['SUPsync', 'SUPsync2', 'SUPsyncPwr', 'SUPsyncACT2', 'SUPsyncDiags', 'SUPsyncTraf', 'SUPsyncFinal']:
            ts.add_sync_group(sg, [cont1, cont2])
    return


# ----------------------------------------------------------------------------------------------------------------------
def sup_pcb2c(config, **kwargs):
    """ Supervisor PCB2C
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCB2C')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.pre'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.pre2'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    chamber_ts_ip = kwargs.get('chamber_ts_ip', None)
    chamber_ts_port = kwargs.get('chamber_ts_port', 0)
    chamber_model = kwargs.get('chamber_model', 'simulator')
    chamber_name = kwargs.get('chamber_name', 'Chamber1')
    chamber_sync_group = kwargs.get('chamber_sync_group', 'ChamberSync1')

    sc_name = kwargs.get('sc_name', 'Master1')

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chamber_ts_ip=chamber_ts_ip, chamber_ts_port=chamber_ts_port)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-SUP'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    # TS - Chamber
    print("    {0}".format(chamber_name))
    ts = ta.add_test_station(name=chamber_name)
    ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
    for pid in pid_cpn_list:
        ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    ts.add_configuration_data(key='CHAMBER_SYNC_GROUP', value=chamber_sync_group)  # Make this available to SC and Containers.
    # Chamber controller
    chamber = dict(telnet=chamber_ts_ip, port=chamber_ts_port, timeout=60, model=chamber_model)
    ts.add_connection(name='Chamber1', **chamber)
    print("    Chamber1={0}:{1}".format(chamber_ts_ip, chamber_ts_port))
    # Supercontainer
    sc = ts.add_super_container(sc_name)
    containers = []
    two_sups = True  # Required for sup testing!
    # Per chassis in chamber
    for chassis_num in range(0, chassis_count, 1):
        chassis_name = "Chassis{0:02}".format(chassis_num + 1)
        print("    {0}".format(chassis_name))
        # Containers
        uut1_name = "{0}_UUT01".format(chassis_name)
        uut2_name = "{0}_UUT02".format(chassis_name)
        cont1 = sc.add_container(name=uut1_name)
        cont2 = sc.add_container(name=uut2_name)
        # Connections
        sup1, sup2, psu1, p = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2)
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        print("    {0} = {1}:{2}".format(uut1_name, ts_ip, p))
        print("    {0} = {1}:{2}".format(uut2_name, ts_ip, p + 1))
        # Containers
        cont1.add_connection(name='uutTN', shared_conn='uutTN_shared1', **sup1)
        cont1.add_connection(name='uutTN_aux', shared_conn='uutTN_shared2', **sup2)
        cont1.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont1.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        cont2.add_connection(name='uutTN', shared_conn='uutTN_shared2', **sup2)
        cont2.add_connection(name='uutTN_aux', shared_conn='uutTN_shared1', **sup1)
        cont2.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont2.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        # Configuration Data
        cont1.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(1, {}))
        cont2.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(2, {}))
        # Collect all containers for the chamber
        containers.append(cont1)
        containers.append(cont2)

    # Sync groups for sequence flow control
    for sg in ['SUPsync', 'SUPsync2', 'SUPsyncPwr', 'SUPsyncACT2', 'SUPsyncDiags', 'SUPsyncTraf', 'SUPsyncFinal']:
        ts.add_sync_group(sg, containers)
    # SyncGroup for chamber monitor
    ts.add_sync_group(chamber_sync_group, containers)

    return


# ----------------------------------------------------------------------------------------------------------------------
def sup_pcbst(config, **kwargs):
    """ Supervisor PCBST
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBST')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    traffic_generator_ip = kwargs.get('traffic_generator_ip', None)

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chassis=chassis)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-SUP'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    two_sups = True
    # TS
    for chassis_num in range(0, chassis_count, 1):
        st_name = "{0}_Chassis_{1:02}".format(station, chassis_num + 1)
        print("    {0}".format(st_name))
        ts = ta.add_test_station(name=st_name)
        ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
        for pid in pid_cpn_list:
            ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
        # Containers
        cont1 = ts.add_container(name="UUT01")
        cont2 = ts.add_container(name="UUT02")
        # Connections
        print("      connections...")
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, p = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared1', **server)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2)
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        ts.add_connection(name='TrafficGen', protocol='ssh', host=traffic_generator_ip) if traffic_generator_ip else None
        ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        print("    UUT01 = {0}:{1}".format(ts_ip, p))
        print("    UUT02 = {0}:{1}".format(ts_ip, p + 1))
        # Containers
        print("      containers...")
        cont1.add_connection(name='uutTN', shared_conn='uutTN_shared1', **sup1)
        cont1.add_connection(name='uutTN_aux', shared_conn='uutTN_shared2', **sup2)
        cont1.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont1.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        cont2.add_connection(name='uutTN', shared_conn='uutTN_shared2', **sup2)
        cont2.add_connection(name='uutTN_aux', shared_conn='uutTN_shared1', **sup1)
        cont2.add_connection(name='serverSSH', shared_conn='serverSSH_shared1', **server)
        cont2.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
        # Configuration Data
        print("      config data...")
        cont1.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(1, {}))
        cont2.add_configuration_data(key='SUPERVISOR', value=SUPERVISOR_CHASSIS.get(chassis, {}).get(2, {}))
        # Sync groups for sequence flow control
        print("      sync groups...")
        for sg in ['SUPsync', 'SUPsync2', 'SUPsyncPwr', 'SUPsyncACT2', 'SUPsyncDiags', 'SUPsyncTraf', 'SUPsyncFinal']:
            ts.add_sync_group(sg, [cont1, cont2])
        print("      done with station...")
    return


# ======================================================================================================================
# LINECARD

# ----------------------------------------------------------------------------------------------------------------------
def linecard_pcbp2(config, **kwargs):
    """ Linecard PCBP2
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBP2')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chassis=chassis)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-LC'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    two_sups = True if '2S' in chassis else False
    # TS
    for chassis_num in range(0, chassis_count, 1):
        st_name = "{0}_Chassis_{1:02}".format(station, chassis_num + 1)
        print("    {0}".format(st_name))
        ts = ta.add_test_station(name=st_name)
        ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
        for pid in pid_cpn_list:
            ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
        # Connections
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, _ = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared1', **server)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2) if two_sups else None
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        containers = []
        for k, v in sorted(LINECARD_CHASSIS.get(chassis, {}).items()):
            cont = ts.add_container(name="UUT{0:02}".format(k))
            # Connections
            conn_suffix = v.get('conn_suffix', '1')
            cont.add_connection(name='uutTN', shared_conn='uutTN_shared{0}'.format(conn_suffix))
            cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')
            cont.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
            # Configuration Data
            cont.add_configuration_data(key='LINECARD', value=v)
            containers.append(cont)
        # Sync groups for sequence flow control
        for sg in ['LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal']:
            ts.add_sync_group(sg, containers)

    return


# ----------------------------------------------------------------------------------------------------------------------
def linecard_pcb2c(config, **kwargs):
    """ Linecard PCB2C
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCB2C')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre2'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    chamber_ts_ip = kwargs.get('chamber_ts_ip', None)
    chamber_ts_port = kwargs.get('chamber_ts_port', 0)
    chamber_model = kwargs.get('chamber_model', 'simulator')
    chamber_name = kwargs.get('chamber_name', 'Chamber1')
    chamber_sync_group = kwargs.get('chamber_sync_group', 'ChamberSync1')

    sc_name = kwargs.get('sc_name', 'Master1')

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chamber_ts_ip=chamber_ts_ip, chamber_ts_port=chamber_ts_port)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-LC'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    two_sups = True if '2S' in chassis else False
    # TS - Chamber
    print("    {0}".format(chamber_name))
    ts = ta.add_test_station(name=chamber_name)
    ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
    for pid in pid_cpn_list:
        ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
    # Chamber controller
    chamber = dict(telnet=chamber_ts_ip, port=chamber_ts_port, timeout=60, model=chamber_model)
    ts.add_connection(name='Chamber1', **chamber)
    print("    Chamber1={0}:{1}".format(chamber_ts_ip, chamber_ts_port))
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    # Supercontainer
    sc = ts.add_super_container(sc_name)
    containers = []
    # Per chassis in chamber
    for chassis_num in range(0, chassis_count, 1):
        uut_name_prefix = "Chassis{0:02}".format(chassis_num + 1)
        # Connections
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, _ = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared{0}'.format(chassis_num + 1), **server)
        ts.add_connection(name='uutTN_shared{0}_1'.format(chassis_num + 1), **sup1)
        ts.add_connection(name='uutTN_shared{0}_2'.format(chassis_num + 1), **sup2) if two_sups else None
        ts.add_connection(name='psu_shared{0}_1'.format(chassis_num + 1), **psu1) if psu_separate_control else None
        for k, v in sorted(LINECARD_CHASSIS.get(chassis, {}).items()):
            cont = sc.add_container(name="{0}_UUT{1:02}".format(uut_name_prefix, k))
            # Connections
            conn_suffix = v.get('conn_suffix', '1')
            cont.add_connection(name='uutTN', shared_conn='uutTN_shared{0}_{1}'.format(chassis_num + 1, conn_suffix))
            cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared{0}'.format(chassis_num + 1))
            cont.add_connection(name='uutPOWER', shared_conn='psu_shared{0}_1'.format(chassis_num + 1)) if psu_separate_control else None
            # Configuration Data
            cont.add_configuration_data(key='LINECARD', value=v)
            containers.append(cont)
    # Sync groups for sequence flow control
    for sg in ['LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal']:
        ts.add_sync_group(sg, containers)
    # SyncGroup for chamber monitor
    ts.add_sync_group(chamber_sync_group, containers)
    return


# ----------------------------------------------------------------------------------------------------------------------
def linecard_pcbpm(config, **kwargs):
    """ Linecard PCBPM
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBPM')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)
    uut_count_per_chassis = max(LINECARD_CHASSIS.get(chassis, {0: None}).keys())

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    poe1_ts_ip = kwargs.get('poe1_ts_ip', None)
    poe1_ts_start_port = kwargs.get('poe1_ts_start_port', 0)
    poe2_ts_ip = kwargs.get('poe2_ts_ip', None)
    poe2_ts_start_port = kwargs.get('poe2_ts_start_port', 0)
    poe3_ts_ip = kwargs.get('poe3_ts_ip', None)
    poe3_ts_start_port = kwargs.get('poe3_ts_start_port', 0)
    poe4_ts_ip = kwargs.get('poe4_ts_ip', None)
    poe4_ts_start_port = kwargs.get('poe4_ts_start_port', 0)
    poe_sync_gp = kwargs.get('poe_sync_gp', 'PoESync')
    poe_model = kwargs.get('poe_model', 'Edgar4')
    poe_mfgr = kwargs.get('poe_mfgr', 'Reach')

    psu_separate_control = kwargs.get('psu_separate_control', True)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chassis=chassis)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-LC'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    two_sups = True if '2S' in chassis else False
    # TS
    for chassis_num in range(0, chassis_count, 1):
        st_name = "{0}_Chassis_{1:02}".format(station, chassis_num + 1)
        print("    {0}".format(st_name))
        ts = ta.add_test_station(name=st_name)
        ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
        for pid in pid_cpn_list:
            ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
        # Connections
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, p = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared1', **server)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2) if two_sups else None
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        poe_sync_gp = '{0}{1}'.format(poe_sync_gp, chassis_num + 1)
        containers = []
        for k, v in sorted(LINECARD_CHASSIS.get(chassis, {}).items()):
            cont_name = "UUT{0:02}".format(k)
            cont = ts.add_container(name=cont_name)
            # Connections
            conn_suffix = v.get('conn_suffix', '1')
            cont.add_connection(name='uutTN', shared_conn='uutTN_shared{0}'.format(conn_suffix))
            cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')
            cont.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
            # Configuration Data
            cont.add_configuration_data(key='LINECARD', value=v)
            #
            # PoE Connection & Config
            p = k + (uut_count_per_chassis * chassis_num) - 1  # PoE LoadBox telnet port offset
            if (poe1_ts_ip and poe1_ts_start_port) and not (poe3_ts_ip and poe3_ts_start_port):
                cont.add_connection(name='POELB1', protocol='telnet', host=poe1_ts_ip, port=poe1_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB1', value={'portmap': '1-24', 'syncgroup': poe_sync_gp})
                print("     {0} {1} = {2}:{3}".format(cont_name, poe_model, poe1_ts_ip, poe1_ts_start_port + p))
            elif (poe1_ts_ip and poe1_ts_start_port) and (poe3_ts_ip and poe3_ts_start_port):
                cont.add_connection(name='POELB1a', protocol='telnet', host=poe1_ts_ip, port=poe1_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB1a', value={'portmap': '1-24', 'syncgroup': poe_sync_gp})
                cont.add_connection(name='POELB1b', protocol='telnet', host=poe3_ts_ip, port=poe3_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB1b', value={'portmap': '1-24', 'syncgroup': poe_sync_gp, 'pair': 'POELB1a'})
                print("     {0} {1} = {2}:{3} + {4}:{5}".format(cont_name, poe_model, poe1_ts_ip, poe1_ts_start_port + p, poe3_ts_ip, poe3_ts_start_port + p))
            #
            if (poe2_ts_ip and poe2_ts_start_port) and not (poe4_ts_ip and poe4_ts_start_port):
                cont.add_connection(name='POELB2', protocol='telnet', host=poe2_ts_ip, port=poe2_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB2', value={'portmap': '1-24', 'syncgroup': poe_sync_gp})
                print("     {0} {1} = {2}:{3}".format(cont_name, poe_model, poe2_ts_ip, poe2_ts_start_port + p))
            elif (poe2_ts_ip and poe2_ts_start_port) and (poe4_ts_ip and poe4_ts_start_port):
                cont.add_connection(name='POELB2a', protocol='telnet', host=poe2_ts_ip, port=poe2_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB2a', value={'portmap': '1-24', 'syncgroup': poe_sync_gp})
                cont.add_connection(name='POELB2b', protocol='telnet', host=poe4_ts_ip, port=poe4_ts_start_port + p, timeout=60, model=poe_model, manufacturer=poe_mfgr)
                cont.add_configuration_data(key='POELB2b', value={'portmap': '1-24', 'syncgroup': poe_sync_gp, 'pair': 'POELB2a'})
                print("     {0} {1} = {2}:{3} + {4}:{5}".format(cont_name, poe_model, poe2_ts_ip, poe2_ts_start_port + p, poe4_ts_ip, poe4_ts_start_port + p))

            containers.append(cont)
        # Sync groups for sequence flow control
        for sg in ['LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal']:
            ts.add_sync_group(sg, containers)
    return


# ----------------------------------------------------------------------------------------------------------------------
def linecard_pcbst(config, **kwargs):
    """ Linecard PCBST
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBST')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.standard_modular_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psu_separate_control = kwargs.get('psu_separate_control', True)

    traffic_generator_ip = kwargs.get('traffic_generator_ip', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chassis=chassis)):
        return

    # PL
    print("-" * 100)
    pl_name = '{0}-LC'.format(product_line)
    pl = config.add_production_line(name=pl_name)
    print("{0}".format(pl_name))
    print(" Server={0}, TS={1}:{2}".format(server_ip, ts_ip, ts_start_port))
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    print("   Chassis count per station = {0}".format(chassis_count))
    print("   Chassis = {0}".format(chassis))
    two_sups = True if '2S' in chassis else False
    # TS
    for chassis_num in range(0, chassis_count, 1):
        st_name = "{0}_Chassis_{1:02}".format(station, chassis_num + 1)
        print("    {0}".format(st_name))
        ts = ta.add_test_station(name=st_name)
        ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
        for pid in pid_cpn_list:
            ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
        # Connections
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        sup1, sup2, psu1, p = __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control)
        ts.add_connection(name='serverSSH_shared1', **server)
        ts.add_connection(name='uutTN_shared1', **sup1)
        ts.add_connection(name='uutTN_shared2', **sup2) if two_sups else None
        ts.add_connection(name='psu_shared1', **psu1) if psu_separate_control else None
        ts.add_connection(name='TrafficGen', protocol='ssh', host=traffic_generator_ip) if traffic_generator_ip else None
        ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        containers = []
        for k, v in sorted(LINECARD_CHASSIS.get(chassis, {}).items()):
            cont = ts.add_container(name="UUT{0:02}".format(k))
            # Connections
            conn_suffix = v.get('conn_suffix', '1')
            cont.add_connection(name='uutTN', shared_conn='uutTN_shared{0}'.format(conn_suffix))
            cont.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')
            cont.add_connection(name='uutPOWER', shared_conn='psu_shared1') if psu_separate_control else None
            # Configuration Data
            cont.add_configuration_data(key='LINECARD', value=v)
            containers.append(cont)
        # Sync groups for sequence flow control
        for sg in ['LCsync', 'LCsyncPwr', 'LCsyncACT2', 'LCsyncDiags', 'LCsyncTraf', 'LCsyncFinal']:
            ts.add_sync_group(sg, containers)
    return


# ======================================================================================================================
# DEBUG/ENG

# ----------------------------------------------------------------------------------------------------------------------
def sup_debug(config, **kwargs):
    """ Supervisor Debug DBGSYS
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = 'DBGSYS'
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.sup_{ta}.eng_utility_menu'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)

    pid_cpn_list = PID_CPN_MAPS.get('ALL')        # Hardcoded

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psu_separate_control = kwargs.get('psu_separate_control', True)

    station_details = dict(
        product_line=product_line,
        test_area=test_area,
        station=station,
        chassis=chassis, chassis_count=chassis_count,
        pid_cpn_list=pid_cpn_list,
        seq_def=seq_def,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip=ts_ip, ts_start_port=ts_start_port,
        psu_separate_control=psu_separate_control
    )
    sup_pcbp2(config, **station_details)

    return


def linecard_debug(config, **kwargs):
    """ Linecard Debug (DBGSYS)
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = 'DBGSYS'
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def = ApolloSeq(
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat4.{pl}.area_sequences.linecard_{ta}.eng_utility_menu'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A')
    chassis = kwargs.get('chassis', None)
    chassis_count = kwargs.get('chassis_count', 1)
    uut_count_per_chassis = max(LINECARD_CHASSIS.get(chassis, {0: None}).keys())

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    poe1_ts_ip = kwargs.get('poe1_ts_ip', None)
    poe1_ts_start_port = kwargs.get('poe1_ts_start_port', 0)
    poe2_ts_ip = kwargs.get('poe2_ts_ip', None)
    poe2_ts_start_port = kwargs.get('poe2_ts_start_port', 0)
    poe3_ts_ip = kwargs.get('poe3_ts_ip', None)
    poe3_ts_start_port = kwargs.get('poe3_ts_start_port', 0)
    poe4_ts_ip = kwargs.get('poe4_ts_ip', None)
    poe4_ts_start_port = kwargs.get('poe4_ts_start_port', 0)
    poe_sync_gp = kwargs.get('poe_sync_gp', 'PoESync')
    poe_model = kwargs.get('poe_model', 'Edgar4')
    poe_mfgr = kwargs.get('poe_mfgr', 'Reach')

    psu_separate_control = kwargs.get('psu_separate_control', True)

    station_details = dict(
        product_line=product_line,
        test_area=test_area,
        station=station,
        chassis=chassis, chassis_count=chassis_count, uut_count_per_chassis=uut_count_per_chassis,
        pid_cpn_list=pid_cpn_list,
        seq_def=seq_def,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        ts_ip=ts_ip, ts_start_port=ts_start_port,
        poe1_ts_ip=poe1_ts_ip, poe1_ts_start_port=poe1_ts_start_port,
        poe2_ts_ip=poe2_ts_ip, poe2_ts_start_port=poe2_ts_start_port,
        poe3_ts_ip=poe3_ts_ip, poe3_ts_start_port=poe3_ts_start_port,
        poe4_ts_ip=poe4_ts_ip, poe4_ts_start_port=poe4_ts_start_port,
        poe_sync_gp=poe_sync_gp, poe_model=poe_model, poe_mfgr=poe_mfgr,
        psu_separate_control=psu_separate_control
    )
    linecard_pcbpm(config, **station_details)

    return


# ======================================================================================================================
# INTERNAL SUPPORT
#
def __sanity_check1(items):
    ret = True
    for k, v in items.items():
        if not v:
            print("ERROR: {0} = (empty)".format(k))
            ret = False
    if not ret:
        print("SANITY ERROR on: {0}".format(items))
    return ret


def __get_sup_and_psu_conns(ts_ip, ts_start_port, chassis_num, two_sups, psu_separate_control):
    if two_sups:
        if psu_separate_control:
            p = ts_start_port + (chassis_num * 3)
            sup1 = dict(host=ts_ip, protocol="telnet", port=p, timeout=180)
            sup2 = dict(host=ts_ip, protocol="telnet", port=p + 1, timeout=180)
            psu1 = dict(host=ts_ip, protocol="telnet", port=p + 2, timeout=180)
        else:
            p = ts_start_port + (chassis_num * 2)
            sup1 = dict(host=ts_ip, protocol="telnet", port=p, timeout=180)
            sup2 = dict(host=ts_ip, protocol="telnet", port=p + 1, timeout=180)
            psu1 = None
    else:
        if psu_separate_control:
            p = ts_start_port + (chassis_num * 2)
            sup1 = dict(host=ts_ip, protocol="telnet", port=p, timeout=180)
            sup2 = None
            psu1 = dict(host=ts_ip, protocol="telnet", port=p + 1, timeout=180)
        else:
            p = ts_start_port + chassis_num
            sup1 = dict(host=ts_ip, protocol="telnet", port=p, timeout=180)
            sup2 = None
            psu1 = None
    return sup1, sup2, psu1, p
