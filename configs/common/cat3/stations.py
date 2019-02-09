"""
========================================================================================================================
C9300/C38xx COMMON Configs
========================================================================================================================
Edison/Archimedes
Nyquist/Franklin

***IMPORTANT***
The following stations are STANDARDIZED for ALL C3K/C9300 SWITCH products at ALL EMS PCBA & DF/ATO Partner sites:
    1. PCBA: BoardSystemTest (BST) or Pre2CornerTest      TAs = PCBST
    2. PCBA: 2-Corner/4-Corner Temperature Chamber Test   TAs = PCB2C, PCB4C
    3. PCBA: Assembly Test                                TAs = ASSY
    4. PCBA: FinalSystemTest (FST)                        TAs = PCBFT, SYSBI(legacy)
    5. DF:   SystemTest                                   TAs = SYSFT

Please contact Cisco TDE ProdOps/GMO TDEs if the standard configs do not provide the necessary setup!
These configs will be highly governed and should not be changed unless by team review.

***WARNING***
DO NOT perform any IP calculation based on UUT number for config storage; this can create potential conflicts
with multi-stations on the Apollo server and/or same test network!!
Please use the IP assignment utility within a step.  The test network mask should be adjusted for 255.255.0.0.
Refer to "common_utils.get_ip_addr_assignment(...)" for more details.
------------------------------------------------------------------------------------------------------------------------
"""
# (see separate project) import apollo.scripts.uniassy.configs.uniassy_config as uniassy_config

from collections import namedtuple

__title__ = "Enterprise Switching CATALYST Series 3 Common Station Configs"
__version__ = "2.0.1"
__author__ = ['bborel', 'qingywu']

ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

# ALL PIDs/CPNs Supported
PID_CPN_MAPS = {
    'C3650': ['WS-C3650*', '73-*'],
    'C3850': ['WS-C3850*', '73-*'],
    'C9300': ['C9300-*', '73-*'],
    'C9300L': ['C9300L-*', '73-*'],
    'ALL': ['WS-C3650*', 'WS-C3850*', 'C9300*', 'C3*', '73-*'],
    'CATALYST': ['WS-C3650*', 'WS-C3850*', 'C9300*', 'C3*', '73-*', '*WSC3850*'],
}


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# ======================================================================================================================
# SWITCHES

# ----------------------------------------------------------------------------------------------------------------------
def switch_pcbst(config, **kwargs):
    """ Switch PCBST
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBST')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)
    virtual = kwargs.get('virtual', False)

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
    poe_sync_gp = kwargs.get('poe_sync_gp', 'PoESync1')
    poe_ports_to_map = kwargs.get('poe_ports_to_map', '1-24')
    poe_share_ports = kwargs.get('poe_share_ports', 0)
    poe_model = kwargs.get('poe_model', 'Edgar4')
    poe_mfgr = kwargs.get('poe_mfgr', 'Reach')

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    fan_ts_ip = kwargs.get('fan_ts_ip', None)
    fan_ts_start_port = kwargs.get('fan_ts_start_port', 0)
    fan_count = kwargs.get('fan_count', 0)
    fan_sync_gp = kwargs.get('fan_sync_gp', 'FanGroup1')

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    if fan_ts_ip and fan_ts_start_port and fan_count > 0:
        for k in range(1, fan_count + 1):
            ts.add_connection(name='stnFAN_shared{0:02}'.format(k), protocol='telnet', host=fan_ts_ip,
                              port=fan_ts_start_port + k - 1, timeout=60)
            print("      {0} = {1}:{2}".format('stnFAN{0:02}'.format(k), fan_ts_ip, fan_ts_start_port + k - 1))

    containers = []
    container_names = 'Containers='
    for i in range(0, uut_count, 1):
        cont_name = "UUT{0:02}".format(i + 1)
        cont = ts.add_container(name=cont_name)
        container_names = '  '.join([container_names, cont_name])
        # Connections
        uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='uutTN', **uut) if not virtual else cont.add_connection(name='uutTN', **server)
        cont.add_connection(name='serverSSH', **server)
        print("      {0} = {1}:{2}".format(cont_name, ts_ip, ts_start_port + i))
        if psB_ts_ip and psB_ts_start_port:
            cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i, timeout=60)
            print("      {0} {1} = {2}:{3}".format(cont_name, 'uutPSB', psB_ts_ip, psB_ts_start_port + i))
        if fan_ts_ip and fan_ts_start_port and fan_count > 0:
            for k in range(1, fan_count + 1):
                cont.add_connection(name='stnFAN{0:02}'.format(k), shared_conn='stnFAN_shared{0:02}'.format(k))
                print("      {0} {1} = {2}:{3}".format(cont_name, 'stnFAN{0:02}'.format(k), fan_ts_ip, fan_ts_start_port + k - 1))
        #
        if (poe1_ts_ip and poe1_ts_start_port) and not (poe3_ts_ip and poe3_ts_start_port):
            name = 'POELB1'
            poe1 = poe1_ts_start_port[i] if isinstance(poe1_ts_start_port, list) else poe1_ts_start_port + i
            cont.add_connection(name=name, protocol='telnet', host=poe1_ts_ip, port=poe1, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'shareports': poe_share_ports})
            print("      {0} ({1} {2}) = {3}:{4}".format(name, cont_name, poe_model, poe1_ts_ip, poe1))
        elif (poe1_ts_ip and poe1_ts_start_port) and (poe3_ts_ip and poe3_ts_start_port):
            name_a, name_b = 'POELB1a', 'POELB1b'
            poe1 = poe1_ts_start_port[i] if isinstance(poe1_ts_start_port, list) else poe1_ts_start_port + i
            poe3 = poe3_ts_start_port[i] if isinstance(poe3_ts_start_port, list) else poe3_ts_start_port + i
            cont.add_connection(name=name_a, protocol='telnet', host=poe1_ts_ip, port=poe1, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name_a, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'shareports': poe_share_ports})
            cont.add_connection(name=name_b, protocol='telnet', host=poe3_ts_ip, port=poe3, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name_b, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'pair': 'POELB1a', 'shareports': poe_share_ports})
            print("      {0},{1} ({2} {3}) = {4}:{5} + {6}:{7}".format(name_a, name_b, cont_name, poe_model, poe1_ts_ip, poe1, poe3_ts_ip, poe3))
        #
        if (poe2_ts_ip and poe2_ts_start_port) and not (poe4_ts_ip and poe4_ts_start_port):
            name = 'POELB2'
            poe2 = poe2_ts_start_port[i] if isinstance(poe2_ts_start_port, list) else poe2_ts_start_port + i
            cont.add_connection(name=name, protocol='telnet', host=poe2_ts_ip, port=poe2, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'shareports': poe_share_ports})
            print("      {0} ({1} {2}) = {3}:{4}".format(name, cont_name, poe_model, poe2_ts_ip, poe2))
        elif (poe2_ts_ip and poe2_ts_start_port) and (poe4_ts_ip and poe4_ts_start_port):
            name_a, name_b = 'POELB2a', 'POELB2b'
            poe2 = poe2_ts_start_port[i] if isinstance(poe2_ts_start_port, list) else poe2_ts_start_port + i
            poe4 = poe4_ts_start_port[i] if isinstance(poe4_ts_start_port, list) else poe4_ts_start_port + i
            cont.add_connection(name=name_a, protocol='telnet', host=poe2_ts_ip, port=poe2, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name_a, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'shareports': poe_share_ports})
            cont.add_connection(name=name_b, protocol='telnet', host=poe4_ts_ip, port=poe4, timeout=60, model=poe_model, manufacturer=poe_mfgr)
            cont.add_configuration_data(key=name_b, value={'portmap': poe_ports_to_map, 'syncgroup': poe_sync_gp, 'pair': 'POELB2a', 'shareports': poe_share_ports})
            print("      {0},{1} ({2} {3}) = {4}:{5} + {6}:{7}".format(name_a, name_b, cont_name, poe_model, poe2_ts_ip, poe2, poe4_ts_ip, poe4))
        #
        containers.append(cont)

    print("      {0}".format(container_names))
    ts.add_sync_group(poe_sync_gp, containers)
    print("      {0} = {1}".format(poe_sync_gp, containers))
    ts.add_sync_group(fan_sync_gp, containers)
    print("      {0} = {1}".format(fan_sync_gp, containers))

    return


def switch_pcbdl(config, **kwargs):
    """ Switch PCBDL
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBDL')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)
    virtual = kwargs.get('virtual', False)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    fan_ts_ip = kwargs.get('fan_ts_ip', None)
    fan_ts_start_port = kwargs.get('fan_ts_start_port', 0)
    fan_count = kwargs.get('fan_count', 0)
    fan_sync_gp = kwargs.get('fan_sync_gp', 'FanGroup1')

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    if fan_ts_ip and fan_ts_start_port and fan_count > 0:
        for k in range(1, fan_count + 1):
            ts.add_connection(name='stnFAN_shared{0:02}'.format(k), protocol='telnet', host=fan_ts_ip,
                              port=fan_ts_start_port + k - 1, timeout=60)
            print("      {0} = {1}:{2}".format('stnFAN{0:02}'.format(k), fan_ts_ip, fan_ts_start_port + k - 1))

    containers = []
    container_names = 'Containers='
    for i in range(0, uut_count, 1):
        cont_name = "UUT{0:02}".format(i + 1)
        cont = ts.add_container(name=cont_name)
        container_names = '  '.join([container_names, cont_name])
        # Connections
        uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='uutTN', **uut) if not virtual else cont.add_connection(name='uutTN', **server)
        cont.add_connection(name='serverSSH', **server)
        print("      {0} = {1}:{2}".format(cont_name, ts_ip, ts_start_port + i))
        if psB_ts_ip and psB_ts_start_port:
            cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i, timeout=60)
            print("      {0} {1} = {2}:{3}".format(cont_name, 'uutPSB', psB_ts_ip, psB_ts_start_port + i))
        if fan_ts_ip and fan_ts_start_port and fan_count > 0:
            for k in range(1, fan_count + 1):
                cont.add_connection(name='stnFAN{0:02}'.format(k), shared_conn='stnFAN_shared{0:02}'.format(k))
                print("      {0} {1} = {2}:{3}".format(cont_name, 'stnFAN{0:02}'.format(k), fan_ts_ip, fan_ts_start_port + k - 1))
        #
        containers.append(cont)

    print("      {0}".format(container_names))
    ts.add_sync_group(fan_sync_gp, containers)
    print("      {0} = {1}".format(fan_sync_gp, containers))

    return


def switch_pcb2c(config, **kwargs):
    """ Switch PCB2C
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCB2C')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre2'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 16)

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

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chamber_ts_ip=chamber_ts_ip, chamber_ts_port=chamber_ts_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Chamber controller - connection
    chamber = dict(protocol="telnet", host=chamber_ts_ip, port=chamber_ts_port, timeout=60, model=chamber_model)
    ts.add_connection(name=chamber_name, **chamber)
    print("    Chamber={0}:{1}".format(chamber_ts_ip, chamber_ts_port))
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    ts.add_configuration_data(key='CHAMBER_SYNC_GROUP', value=chamber_sync_group)  # Make this available to SC and Containers.
    # Supercontainer
    print("    SC={0}".format(sc_name))
    sc = ts.add_super_container(sc_name)
    sc.add_connection(name='Chamber', shared_conn=chamber_name)  # **chamber
    sc.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')  # **server

    # Containers
    containers = [sc]
    print("      {0} = {1}".format('UUT Pre-seq', seq_def.preseq2))
    for i in range(0, uut_count, 1):
        c_name = "UUT{0:02}".format(i + 1)
        cont = sc.add_container(name=c_name)
        print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
        # Pre-seq's per container: CASCADE feature for Supercontainer_preseq (.preseq) --> Container_preseq (.preseq2)
        cont.assign_pre_sequence(sequence_definition=seq_def.preseq2)
        # Connections
        cont.add_connection(name='uutTN', host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='serverSSH', **server)
        cont.add_connection(name='Chamber', shared_conn=chamber_name)  # **chamber
        containers.append(cont)

    ts.add_sync_group(chamber_sync_group, containers)
    print("      {0} = {1}".format(chamber_sync_group, containers))
    return


def switch_pcbassy(config, **kwargs):
    """ Switch ASSY
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBASSY')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    loadbox_ts_ip = kwargs.get('loadbox_ts_ip', None)
    loadbox_ts_start_port = kwargs.get('loadbox_ts_start_port', 0)
    loadbox_sync_gp_size = kwargs.get('loadbox_sync_gp_size', 4)
    loadbox_sync_gp = kwargs.get('loadbox_sync_gp', 'StackPwrSync1')

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    if uut_count % loadbox_sync_gp_size != 0:
        print("ERROR: The ASSY Station UUT count MUST be a multiple of the StackPower Loadbox group size (typically 4).")
        return
    lb_group_count = uut_count / loadbox_sync_gp_size
    for g in range(0, lb_group_count, 1):
        containers = []
        loadbox = dict(protocol='telnet', host=loadbox_ts_ip, port=loadbox_ts_start_port + g, timeout=60)
        ts.add_connection(name='SPLB_{0}_shared'.format(g), **loadbox)
        for i in range(0, loadbox_sync_gp_size, 1):
            c = g * loadbox_sync_gp_size + i
            c_name = "UUT{0:02}".format(c + 1)
            cont = ts.add_container(name=c_name)
            print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
            # Connections
            cont.add_connection(name='uutTN', host=ts_ip, protocol="telnet", port=ts_start_port + c)
            cont.add_connection(name='serverSSH', **server)
            if psB_ts_ip and psB_ts_start_port:
                cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + c, timeout=60)
            if loadbox_ts_ip and loadbox_ts_start_port:
                cont.add_connection(name='SPLB', shared_conn='SPLB_{0}_shared'.format(g))  # **loadbox
                cont.add_configuration_data(key='SPLB', value={'syncgroup': '{0}_{1}'.format(loadbox_sync_gp, g)})
            #
            containers.append(cont)

        ts.add_sync_group('{0}_{1}'.format(loadbox_sync_gp, g), containers)
        print("      {0} = {1}".format('{0}_{1}'.format(loadbox_sync_gp, g), containers))

    return


def switch_assy(config, **kwargs):
    """ Switch ASSY
    :param config:
    :param kwargs:
    :return:
    """
    kwargs['test_area'] = 'ASSY'
    return switch_pcbassy(config, **kwargs)


def switch_pcbft(config, **kwargs):
    """ Switch PCBFT
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBFT')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 20)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    containers = []
    for i in range(0, uut_count, 1):
        c_name = "UUT{0:02}".format(i + 1)
        cont = ts.add_container(name=c_name)
        print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
        # Connections
        cont.add_connection(name='uutTN', host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='serverSSH', **server)
        containers.append(cont)

    return


def switch_sysbi(config, **kwargs):
    #product_line = kwargs.get('product_line', 'CATALYST')
    #pl = product_line.upper()
    # kwargs['seq_def'] = ApolloSeq(
    #    'apollo.scripts.entsw.cat3.{pl}.area_sequences.pcbft.pre'.format(pl=pl),
    #    None,
    #    'apollo.scripts.entsw.cat3.{pl}.area_sequences.pcbft.standard_switch'.format(pl=pl))
    kwargs['test_area'] = 'SYSBI'
    return switch_pcbft(config, **kwargs)


def switch_sysassy(config, **kwargs):
    product_line = kwargs.get('product_line', 'CAT3')
    pl = config.add_production_line(name=product_line)  # 'FTX UNIVERSAL ASSY-HIPOT')
    assy = pl.add_area(name='SYSASSY')
    assy.add_test_station(name='NA')
    # (see separate project) uniassy_config.assembly_tester(area=assy)
    return


def switch_sysft(config, **kwargs):
    """ Switch SYSFT
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'SYSFT')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user)
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    containers = []
    for i in range(0, uut_count, 1):
        c_name = "UUT{0:02}".format(i + 1)
        cont = ts.add_container(name=c_name)
        print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
        # Connections
        cont.add_connection(name='uutTN', host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='serverSSH', **server)
        if psB_ts_ip and psB_ts_start_port:
            cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i, timeout=60)
        #
        containers.append(cont)

    return


# ======================================================================================================================
# DEBUG

def switch_debug(config, **kwargs):
    """ Switch DBGSYS
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = 'DBGSYS'
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def = ApolloSeq(
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat3.{pl}.area_sequences.{ta}.eng_utility_menu'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = PID_CPN_MAPS.get('ALL')  # Hardcoded

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
    poe_sync_gp = kwargs.get('poe_sync_gp', 'PoESync1')
    poe_ports_to_map = kwargs.get('poe_ports_to_map', '1-24')
    poe_share_ports = kwargs.get('poe_share_ports', 0)
    poe_model = kwargs.get('poe_model', 'Edgar4')
    poe_mfgr = kwargs.get('poe_mfgr', 'Reach')

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    fan_ts_ip = kwargs.get('fan_ts_ip', None)
    fan_ts_start_port = kwargs.get('fan_ts_start_port', 0)
    fan_count = kwargs.get('fan_count', 0)
    fan_sync_gp = kwargs.get('fan_sync_gp', 'FanGroup1')

    virtual = kwargs.get('virtual', False)

    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    station_details = dict(
        product_line=product_line,
        test_area=test_area,
        station=station, uut_count=uut_count,
        server_ip=server_ip, dwnld_server_ip=dwnld_server_ip,
        pid_cpn_list=pid_cpn_list,
        seq_def=seq_def,
        ts_ip=ts_ip, ts_start_port=ts_start_port,
        psB_ts_ip=psB_ts_ip, psB_ts_start_port=psB_ts_start_port,
        poe1_ts_ip=poe1_ts_ip, poe1_ts_start_port=poe1_ts_start_port,
        poe2_ts_ip=poe2_ts_ip, poe2_ts_start_port=poe2_ts_start_port,
        poe3_ts_ip=poe3_ts_ip, poe3_ts_start_port=poe3_ts_start_port,
        poe4_ts_ip=poe4_ts_ip, poe4_ts_start_port=poe4_ts_start_port,
        poe_sync_gp=poe_sync_gp, poe_ports_to_map=poe_ports_to_map,
        poe_share_ports=poe_share_ports,
        poe_model=poe_model, poe_mfgr=poe_mfgr,
        fan_ts_ip=fan_ts_ip, fan_ts_start_port=fan_ts_start_port,
        fan_count=fan_count, fan_sync_gp=fan_sync_gp,
        virtual=virtual
    )
    switch_pcbst(config, **station_details)

    return


# ======================================================================================================================
# PERIPHERALS

# TODO: add here

# ======================================================================================================================
# INTERNAL SUPPORT
#
def __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def, assign_abort_user=None):
    # PL
    print("-" * 100)
    pl = config.add_production_line(name=product_line)
    print("{0}".format(product_line))
    pl.assign_abort_users(assign_abort_user) if assign_abort_user else None
    # TA
    ta = pl.add_area(name=test_area)
    print("  {0}".format(test_area))
    # TS
    ts = ta.add_test_station(name=station)
    print("    {0}".format(station))
    ts.assign_pre_sequence(sequence_definition=seq_def.preseq)
    print("     Station Pre-seq = {0}".format(seq_def.preseq))
    print("     Station Seq = {0}".format(seq_def.seq))
    print("     {0}".format(pid_cpn_list))
    for pid in pid_cpn_list:
        ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
    return pl, ta, ts


def __sanity_check1(items):
    # Sanity check
    ret = True
    for k, v in items.items():
        if not v:
            print("ERROR: {0} = (empty)".format(k))
            ret = False
    if not ret:
        print("SANITY ERROR on: {0}".format(items))
    return ret
