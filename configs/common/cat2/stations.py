"""
========================================================================================================================
C9200 COMMON Configs
========================================================================================================================
Quake

***IMPORTANT***
The following stations are STANDARDIZED for ALL C9200 SWITCH products at ALL EMS PCBA & DF/ATO Partner sites:
    1. PCBA: Pre2CornerTest                               TAs = PCBP2
    2. PCBA: PoE                                          TAs = PCBPM
    2. PCBA: 2-Corner/4-Corner Temperature Chamber Test   TAs = PCB2C, PCB4C
    4. PCBA(ATO): FinalSystemTest (FST)                   TAs = PCBFT
    5. DF or PCBA(pick-pack):   SystemTest                TAs = SYSFT

Please contact Cisco TDE ProdOps/GMO TDEs if the standard configs do not provide the necessary setup!
These configs will be highly governed and should not be changed unless by team review.

***WARNING***
DO NOT perform any IP calculation based on UUT number for config storage; this can create potential conflicts
with multi-stations on the Apollo server and/or same test network!!
Please use the IP assignment utility within a step.  The test network mask should be adjusted for 255.255.0.0.
Refer to "common_utils.get_ip_addr_assignment(...)" for more details.
------------------------------------------------------------------------------------------------------------------------
"""
from collections import namedtuple

__version__ = "2.0.0"
__title__ = "Enterprise Switching CATALYST Series 2 Common Station Configs"
__author__ = ['bborel', 'jpe_team']


ApolloSeq = namedtuple('ApolloSeq', 'preseq preseq2 seq')

# ALL PIDs/CPNs Supported
PID_CPN_MAPS = {
    'C2960':    ['WS-C2960*', '73-*'],
    'C9200':    ['C9200*', '73-*'],
    'ALL':      ['WS-C2960*', 'C9200*', 'C2*', '73-*'],
    'CATALYST': ['WS-C2960*', 'C9200*', 'C2*', '73-*']
}


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# ======================================================================================================================
# SWITCHES

# ----------------------------------------------------------------------------------------------------------------------
def switch_pcbp2(config, **kwargs):
    """ Switch PCBP2
    :param config: 
    :param kwargs: 
    :return: 
    """
    product_line = kwargs.get('product_line', 'GENERIC')
    test_area = kwargs.get('test_area', 'PCBP2')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)
    virtual = kwargs.get('virtual', False)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)            # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

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
    if ts_user:
        print("     USB T/S in use for UUT connection & power control.")
    containers = []
    container_names = 'Containers='
    for i in range(0, uut_count, 1):
        cont_name = "UUT{0:02}".format(i + 1)
        cont = ts.add_container(name=cont_name)
        container_names = '  '.join([container_names, cont_name])
        # Connections
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER', timeout=120)
            cont.add_connection(name='uutPOWER', **uut_pwr) if not virtual else cont.add_connection(name='uutPOWER', **server)
            cont.add_connection(name='uutTN', **uut) if not virtual else cont.add_connection(name='uutTN', **server)
        else:
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            cont.add_connection(name='uutTN', **uut) if not virtual else cont.add_connection(name='uutTN', **server)
        cont.add_connection(name='serverSSH', **server)
        print("      {0} = {1}:{2}".format(cont_name, ts_ip, ts_start_port + i))
        if psB_ts_ip and psB_ts_start_port:
            cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i, timeout=60)
            print("      {0} = {1}:{2}".format('uutPSB', psB_ts_ip, psB_ts_start_port + i))
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

    return


def switch_pcbpm(config, **kwargs):
    kwargs['test_area'] = 'PCBPM'
    return switch_pcbp2(config, **kwargs)


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
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre2'.format(pl=pl, ta=ta),
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 16)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)          # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

    chamber_ts_ip = kwargs.get('chamber_ts_ip', None)
    chamber_ts_port = kwargs.get('chamber_ts_port', 0)
    chamber_model = kwargs.get('chamber_model', 'simulator')
    chamber_name = kwargs.get('chamber_name', 'Chamber1')
    chamber_sync_group = kwargs.get('chamber_sync_group', 'ChamberSync1')
    pcbox_ip = kwargs.get('pcbox_ip', None)
    pcbox_port = kwargs.get('pcbox_port', None)

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
    pcbox = dict(protocol="telnet", host=pcbox_ip, port=pcbox_port, timeout=60) if pcbox_ip else None
    ts.add_connection(name='PCBox_shared', **pcbox) if pcbox else None
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    ts.add_configuration_data(key='CHAMBER_SYNC_GROUP', value=chamber_sync_group)  # Make this available to SC and Containers.
    # Supercontainer
    print("    SC={0}".format(sc_name))
    sc = ts.add_super_container(sc_name)
    sc.add_connection(name='Chamber', shared_conn=chamber_name)  # **chamber
    sc.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')  # **server
    sc.add_connection(name='PCBox', shared_conn='PCBox_shared') if pcbox else None

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
        cont.add_connection(name='PCBox', shared_conn='PCBox_shared') if pcbox else None
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER', timeout=120)
            cont.add_connection(name='uutPOWER', **uut_pwr)
            cont.add_connection(name='uutTN', **uut)
        else:
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            cont.add_connection(name='uutTN', **uut)
        containers.append(cont)
    ts.add_sync_group(chamber_sync_group, containers)
    print("      {0} = {1}".format(chamber_sync_group, containers))
    return


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
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 20)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)          # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

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
        cont.add_connection(name='serverSSH', **server)
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER', timeout=120)
            cont.add_connection(name='uutPOWER', **uut_pwr)
            cont.add_connection(name='uutTN', **uut)
        else:
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            cont.add_connection(name='uutTN', **uut)
        containers.append(cont)

    return


def switch_pcbft_at(config, **kwargs):
    """ Switch PCBFT Automation
    Automation ('_at') uses the Supercontainer for "batch" run of a group of UUTs.
    :param config: 
    :param kwargs: 
    :return: 
    """

    def create_container(uut_count, last_stg, ts_ip, ts_start_port, ts_model, ts_user, ts_pswd, psB_ts_ip,
                         psB_ts_start_port, dwnld_server_ip):
        server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
        last_stg.add_connection(name='serverSSH_shared1', **server)
        last_stg.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
        containers = []
        for i in range(0, uut_count, 1):
            c_name = "UUT{0:02}".format(i + 1)
            cont = last_stg.add_container(name=c_name)
            print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
            # Connections
            cont.add_connection(name='serverSSH', **server)
            cont.add_connection(name='PCBox', shared_conn='PCBox') if pcbox_ip else None
            if ts_user:
                uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
                uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER',
                           timeout=120)
                cont.add_connection(name='uutPOWER', **uut_pwr)
                cont.add_connection(name='uutTN', **uut)
            else:
                uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
                cont.add_connection(name='uutTN', **uut)

            if psB_ts_ip and psB_ts_start_port:
                cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i,
                                    timeout=60)
            #
            containers.append(cont)
        return containers

    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'PCBFT')
    pl = product_line.upper()
    ta = test_area.lower()
    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = kwargs.get('pid_cpn_list', list())
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)  # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')  # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')  # 'Lantronix' or 'OpenGear'

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)
    pcbox_ip = kwargs.get('pcbox_ip', None)
    pcbox_port = kwargs.get('pcbox_port', None)
    batch_sync_group = kwargs.get('batch_sync_group', 'BATCH_SYNC_GROUP')

    # Super Container
    sc_name = kwargs.get('sc_name', '')
    sc_count = len(sc_name) if isinstance(sc_name, list) else 0
    # Sanity check
    if not __sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = __build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, seq_def)
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    if sc_count >= 1:
        for j in xrange(0, sc_count):
            sc_name_tmp = sc_name[j] if isinstance(sc_name, list) else sc_name
            ts_ip_tmp = ts_ip[j] if isinstance(ts_ip, list) else ts_ip
            uut_count_tmp = uut_count[j] if isinstance(uut_count, list) else uut_count
            ts_user_tmp = ts_user[j] if isinstance(ts_user, list) else ts_user
            ts_pswd_tmp = ts_pswd[j] if isinstance(ts_pswd, list) else ts_pswd
            ts_model_tmp = ts_model[j] if isinstance(ts_model, list) else ts_model
            ts_start_port_tmp = ts_start_port[j] if isinstance(ts_start_port, list) else ts_start_port
            psB_ts_ip_tmp = psB_ts_ip[j] if isinstance(psB_ts_ip, list) else psB_ts_ip
            psB_ts_start_port_tmp = psB_ts_start_port[j] if isinstance(psB_ts_start_port, list) else psB_ts_start_port
            dwnld_server_ip_tmp = dwnld_server_ip[j] if isinstance(dwnld_server_ip, list) else dwnld_server_ip
            pcbox_ip_tmp = pcbox_ip[j] if isinstance(pcbox_ip, list) else pcbox_ip
            pcbox_port_tmp = pcbox_port[j] if isinstance(pcbox_port, list) else pcbox_port

            print("    SC={0}".format(sc_name_tmp))
            sc = ts.add_super_container(sc_name_tmp)
            last_stg = sc
            sc.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')  # **server
            pcbox = dict(protocol="telnet", host=pcbox_ip_tmp, port=pcbox_port_tmp, timeout=60) if pcbox_ip else None
            sc.add_connection(name='PCBox', **pcbox) if pcbox else None
            sc_conn_names = 'SC-Connections='
            # SC connections for PRESEQ
            for i in range(0, uut_count_tmp, 1):
                conn_name_uut = "uutTN_{0:02}".format(i + 1)
                conn_name_uutpwr = "uutPOWER_{0:02}".format(i + 1)
                sc_conn_names = '  '.join([sc_conn_names, conn_name_uut])
                if ts_user_tmp:
                    uut_pwr = dict(host=ts_ip_tmp, protocol="ssh", user=ts_user_tmp, password=ts_pswd_tmp,
                                   model=ts_model_tmp, timeout=120)
                    uut = dict(host=ts_ip_tmp, protocol="telnet", port=ts_start_port_tmp + i,
                               power_connection=conn_name_uutpwr,
                               timeout=120)
                    sc.add_connection(name=conn_name_uutpwr, **uut_pwr)
                    sc.add_connection(name=conn_name_uut, **uut)
                else:
                    sc_conn = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
                    sc.add_connection(name=conn_name_uut, **sc_conn)
            print("      {0}".format(sc_conn_names))
            containers = create_container(uut_count_tmp, last_stg, ts_ip_tmp, ts_start_port_tmp, ts_model_tmp,
                                          ts_user_tmp,
                                          ts_pswd_tmp, psB_ts_ip_tmp, psB_ts_start_port_tmp, dwnld_server_ip_tmp)
            print("      {0} = {1}".format('SYNC GROUP NAME', batch_sync_group + "_{}".format(j + 1)))
            ts.add_sync_group(batch_sync_group + "_{}".format(j + 1), containers)
    else:
        # Connections
        last_stg = ts
        create_container(uut_count, last_stg, ts_ip, ts_start_port, ts_model, ts_user, ts_pswd, psB_ts_ip,
                         psB_ts_start_port, dwnld_server_ip)
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
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.standard_switch'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = kwargs.get('pid_cpn_list', PID_CPN_MAPS.get(product_line))
    seq_def = kwargs.get('seq_def', seq_def_default)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)          # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

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
        cont.add_connection(name='serverSSH', **server)
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER', timeout=120)
            cont.add_connection(name='uutPOWER', **uut_pwr)
            cont.add_connection(name='uutTN', **uut)
        else:
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            cont.add_connection(name='uutTN', **uut)

        if psB_ts_ip and psB_ts_start_port:
            cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i, timeout=60)
        #
        containers.append(cont)

    return


# ======================================================================================================================
# DEBUG
#
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
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.pre'.format(pl=pl, ta=ta),
        None,
        'apollo.scripts.entsw.cat2.{pl}.area_sequences.{ta}.eng_utility_menu'.format(pl=pl, ta=ta))

    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = PID_CPN_MAPS.get('ALL')  # Hardcoded

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', None)          # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

    poe1_ts_ip = kwargs.get('poe1_ts_ip', None)
    poe1_ts_start_port = kwargs.get('poe1_ts_start_port', 0)
    poe2_ts_ip = kwargs.get('poe2_ts_ip', None)
    poe2_ts_start_port = kwargs.get('poe2_ts_start_port', 0)
    poe3_ts_ip = kwargs.get('poe3_ts_ip', None)
    poe3_ts_start_port = kwargs.get('poe3_ts_start_port', 0)
    poe4_ts_ip = kwargs.get('poe4_ts_ip', None)
    poe4_ts_start_port = kwargs.get('poe4_ts_start_port', 0)
    poe_sync_gp = kwargs.get('poe_sync_gp', 'PoESync1')
    poe_model = kwargs.get('poe_model', 'Edgar4')
    poe_mfgr = kwargs.get('poe_mfgr', 'Reach')

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)

    assign_abort_user = kwargs.get('assign_abort_user', None)

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
        ts_user=ts_user, ts_pswd=ts_pswd, ts_model=ts_model,
        psB_ts_ip=psB_ts_ip, psB_ts_start_port=psB_ts_start_port,
        poe1_ts_ip=poe1_ts_ip, poe1_ts_start_port=poe1_ts_start_port,
        poe2_ts_ip=poe2_ts_ip, poe2_ts_start_port=poe2_ts_start_port,
        poe3_ts_ip=poe3_ts_ip, poe3_ts_start_port=poe3_ts_start_port,
        poe4_ts_ip=poe4_ts_ip, poe4_ts_start_port=poe4_ts_start_port,
        poe_sync_gp=poe_sync_gp,
        poe_model=poe_model, poe_mfgr=poe_mfgr,
        assign_abort_user=assign_abort_user
    )
    switch_pcbp2(config, **station_details)

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
