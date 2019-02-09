"""
C2K Config (JPE dev)
"""

from apollo.libs import lib
import apollo.config.common.c2k.c2k_common_stations as c2k_common_stations

__version__ = "0.0.2"
__title__ = "Enterprise Switching C2k Config for JPE"
__author__ = ['bborel', 'jpe_team']


TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, 'LantronixUSB': 2017, 'LantronixCon': 2001}

QUAKE_MOTHERBOARD_PIDS = ['73-18785-*', '73-18785-*', '73-18775-*', '73-18831-*', '73-18775-*']

QUAKE_BASE_PIDS = ['C9200-48T-4G', 'C9200-24T-4G', 'C9200-48P-4G', 'C9200-24P-4X', 'C9200-48P-4X',
                   'C9200-24T-4X', 'C9200-48T-4X', 'C9200-48P8X-2Y', 'C9200-24P8X-2Y', 'C9200-24P8X-4X',
                   'C9200-48P12X-4X', 'C9200-24P-4G', 'C9200L-48P-4G', 'C9200L-48P-4X', 'C9200L-48T-4G',
                   'C9200L-48T-4X', 'C9200L-24P-4G', 'C9200L-24P-4X', 'C9200L-24T-4G', 'C9200L-24T-4X',
                   'C9200L-48PXG-2Y', 'C9200L-48PXG-4X', 'C9200L-24PXG-2Y', 'C9200L-24PXG-4X',
                   'C9200-48T', 'C9200-48P', 'C9200-24P', 'C9200-24T', 'C9200-24PXG', 'C9200-48PXG']


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
        pid_cpn_list=QUAKE_MOTHERBOARD_PIDS + QUAKE_MOTHERBOARD_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.200', ts_start_port=TS_START_PORT['LantronixUSB'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip='10.1.1.3', poe1_ts_start_port=TS_START_PORT['2900'],
    )
    c2k_common_stations.c2k_switch_pcbp2_common(config, **station_details)
    # c2k_common_stations.c2k_switch_debug_common(config, **station_details)

    #
    # PCB2C
    station_details = dict(
        product_line='C9200', generation='GEN3',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=QUAKE_BASE_PIDS + QUAKE_MOTHERBOARD_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip='10.1.1.200', ts_start_port=TS_START_PORT['LantronixCon'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0,
        chamber_ts_ip='10.1.1.61', chamber_ts_port=36888,
        chamber_model="watlow_vostron", chamber_name="Chamber",
        pcbox_ip='10.1.1.3', pcbox_port=2003
    )
    # c2k_common_stations.c2k_switch_pcb2c_common(config, **station_details)
    quake_switch_pcb2c_common(config, **station_details)

    #
    # SYSFT ---------------------------------------------------------
    # station_details = dict(
    #     product_line='C9200', generation='GEN3',
    #     station='Station_A_01', uut_count=16,
    #     pid_cpn_list=QUAKE_BASE_PIDS + QUAKE_MOTHERBOARD_PIDS,
    #     server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
    #     ts_ip='10.1.1.200', ts_start_port=TS_START_PORT['LantronixUSB'],
    #     ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
    #     poe1_ts_ip=None, poe1_ts_start_port=0,
    # )
    # c2k_common_stations.c2k_switch_sysft_common(config, **station_details)
    # station_details = dict(
    #     product_line='C9200', generation='GEN3',
    #     station='Station_A_02', uut_count=16,
    #     pid_cpn_list=QUAKE_BASE_PIDS + QUAKE_MOTHERBOARD_PIDS,
    #     server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
    #     ts_ip='10.1.1.201', ts_start_port=TS_START_PORT['LantronixUSB'],
    #     ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
    #     poe1_ts_ip=None, poe1_ts_start_port=0,
    # )
    # c2k_common_stations.c2k_switch_sysft_common(config, **station_details)

    station_details = dict(
        product_line='C9200', generation='GEN3',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=QUAKE_BASE_PIDS + QUAKE_MOTHERBOARD_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip=['10.1.1.200', '10.1.1.201'], ts_start_port=TS_START_PORT['LantronixCon'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0, sc_name=["Master1", "Master2"],
        pcbox_ip='10.1.1.3', pcbox_port=[2003, 2004]
    )
    # c2k_common_stations.c2k_switch_sysft_common_at(config, **station_details)
    quake_switch_pcbft_common(config, **station_details)
    return


def quake_switch_pcb2c_common(config, **kwargs):
    SEQ_DEF_LOOKUP = {
        ('PCB2C', 'ANY'): ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcb2c',
                           'apollo.scripts.entsw.cat2.area_sequences.c2k_pcb2c_run.standard_switch'),
        ('PCB2C', 'GEN3'): ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcb2c_gen3',
                            'apollo.scripts.entsw.cat2.area_sequences.c2k_pcb2c_run.standard_switch'),
        ('PCB2C', 'PROTO'): ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcb2c_gen3',
                             'apollo.scripts.entsw.cat2.area_sequences.c2k_pcb2c_run.proto_switch'),
    }

    product_line = kwargs.get('product_line', 'C2K')
    generation = kwargs.get('generation', 'ANY')
    test_area = kwargs.get('test_area', 'PCB2C')
    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 16)

    pid_cpn_list = kwargs.get('pid_cpn_list', list())
    seq_def_lookup = kwargs.get('seq_def_lookup', SEQ_DEF_LOOKUP)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', 'root')  # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')  # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')  # 'Lantronix' or 'OpenGear'

    chamber_ts_ip = kwargs.get('chamber_ts_ip', None)
    chamber_ts_port = kwargs.get('chamber_ts_port', 0)
    chamber_model = kwargs.get('chamber_model', 'simulator')
    chamber_name = kwargs.get('chamber_name', 'Chamber1')
    chamber_sync_group = kwargs.get('chamber_sync_group', 'ChamberSync1')
    pcbox_ip = kwargs.get('pcbox_ip', '10.1.1.3')
    pcbox_port = kwargs.get('pcbox_port', 2003)

    sc_name = kwargs.get('sc_name', 'Master1')

    assign_abort_user = kwargs.get('assign_abort_user', None)

    # Sanity check
    if not c2k_common_stations.__sanity_check1(
            dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port, chamber_ts_ip=chamber_ts_ip,
                 chamber_ts_port=chamber_ts_port)):
        return

    # PL, TA, TS
    pl, ta, ts = c2k_common_stations.__build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list,
                                                      generation, seq_def_lookup, assign_abort_user)
    # Chamber controller - connection
    chamber = dict(protocol="telnet", host=chamber_ts_ip, port=chamber_ts_port, timeout=60, model=chamber_model)
    ts.add_connection(name=chamber_name, **chamber)
    print("    Chamber={0}:{1}".format(chamber_ts_ip, chamber_ts_port))
    # Connections
    server = dict(protocol='ssh', host=server_ip, user='gen-apollo', password='Ad@pCr01!')
    ts.add_connection(name='serverSSH_shared1', **server)
    ts.add_configuration_data(key='REMOTE_SERVER', value={'IP': dwnld_server_ip})
    ts.add_configuration_data(key='CHAMBER_SYNC_GROUP',
                              value=chamber_sync_group)  # Make this available to SC and Containers.
    # Supercontainer
    print("    SC={0}".format(sc_name))
    sc = ts.add_super_container(sc_name)
    sc.add_connection(name='Chamber', shared_conn=chamber_name)  # **chamber
    sc.add_connection(name='serverSSH', shared_conn='serverSSH_shared1')  # **server
    pcbox = dict(protocol="telnet", host=pcbox_ip, port=pcbox_port, timeout=60)  # power cycling box connection conf
    sc.add_connection(name='PCBox', **pcbox)  # Add port cycling box connection
    sc_conn_names = 'SC-Connections='
    # SC connections for PRESEQ
    for i in range(0, uut_count, 1):
        conn_name_uut = "uutTN_{0:02}".format(i + 1)
        conn_name_uutpwr = "uutPOWER_{0:02}".format(i + 1)
        sc_conn_names = '  '.join([sc_conn_names, conn_name_uut])
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection=conn_name_uutpwr,
                       timeout=120)
            sc.add_connection(name=conn_name_uutpwr, **uut_pwr)
            sc.add_connection(name=conn_name_uut, **uut)
            sc.add_connection(name='PCBox', shared_conn='PCBox')
        else:
            sc_conn = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            sc.add_connection(name=conn_name_uut, **sc_conn)
    print("      {0}".format(sc_conn_names))
    # Containers
    containers = []
    for i in range(0, uut_count, 1):
        c_name = "UUT{0:02}".format(i + 1)
        cont = sc.add_container(name=c_name)
        print("      {0} = {1}:{2}".format(c_name, ts_ip, ts_start_port + i))
        # Connections
        cont.add_connection(name='uutTN', host=ts_ip, protocol="telnet", port=ts_start_port + i)
        cont.add_connection(name='serverSSH', **server)
        cont.add_connection(name='Chamber', shared_conn=chamber_name)  # **chamber
        if ts_user:
            uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER', timeout=120)
            cont.add_connection(name='uutPOWER', **uut_pwr)
            cont.add_connection(name='uutTN', **uut)
            cont.add_connection(name='PCBox', shared_conn='PCBox')
        else:
            uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
            cont.add_connection(name='uutTN', **uut)
        containers.append(cont)
    ts.add_sync_group(chamber_sync_group, containers)
    print("      {0} = {1}".format(chamber_sync_group, containers))
    return


def quake_switch_pcbft_common(config, **kwargs):

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
            if ts_user:
                uut_pwr = dict(host=ts_ip, protocol="ssh", user=ts_user, password=ts_pswd, model=ts_model, timeout=120)
                uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, power_connection='uutPOWER',
                           timeout=120)
                cont.add_connection(name='uutPOWER', **uut_pwr)
                cont.add_connection(name='uutTN', **uut)
                cont.add_connection(name='PCBox', shared_conn='PCBox')
            else:
                uut = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
                cont.add_connection(name='uutTN', **uut)

            if psB_ts_ip and psB_ts_start_port:
                cont.add_connection(name='uutPSB', protocol='telnet', host=psB_ts_ip, port=psB_ts_start_port + i,
                                    timeout=60)
            #
            containers.append(cont)
        return containers

    SEQ_DEF_LOOKUP = {
        ('SYSFT', 'ANY'):  ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcbft',
                            'apollo.scripts.entsw.cat2.area_sequences.c2k_pcbft_run.standard_switch_spcbft'),
        ('SYSFT', 'GEN2'): ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcbft_gen2',
                            'apollo.scripts.entsw.cat2.area_sequences.c2k_pcbft_run.standard_switch_pcbft'),
        ('SYSFT', 'GEN3'): ('apollo.scripts.entsw.cat2.area_sequences.c2k_all_pre_sequences.pre_pcbft_gen3_bts_at',
                            'apollo.scripts.entsw.cat2.area_sequences.c2k_sysft_run.standard_switch_sysft'),
    }
    product_line = kwargs.get('product_line', 'C2K')
    generation = kwargs.get('generation', 'ANY')
    test_area = kwargs.get('test_area', 'SYSFT')
    station = kwargs.get('station', 'Station_A_01')
    uut_count = kwargs.get('uut_count', 10)

    pid_cpn_list = kwargs.get('pid_cpn_list', list())
    seq_def_lookup = kwargs.get('seq_def_lookup', SEQ_DEF_LOOKUP)

    server_ip = kwargs.get('server_ip', None)
    dwnld_server_ip = kwargs.get('dwnld_server_ip', '10.1.1.1')

    ts_ip = kwargs.get('ts_ip', None)
    ts_start_port = kwargs.get('ts_start_port', 0)
    ts_user = kwargs.get('ts_user', 'root')          # 'sysadmin' or  'root'
    ts_pswd = kwargs.get('ts_pswd', 'PASS')          # 'PASS' or      'default'
    ts_model = kwargs.get('ts_model', 'Lantronix')   # 'Lantronix' or 'OpenGear'

    psB_ts_ip = kwargs.get('psB_ts_ip', None)
    psB_ts_start_port = kwargs.get('psB_ts_start_port', 0)
    pcbox_ip = kwargs.get('pcbox_ip', '10.1.1.3')
    pcbox_port = kwargs.get('pcbox_port', 2003)
    sysft_sync_group = "SYSFT_SYNC_GROUP"
    # Super Container
    sc_name = kwargs.get('sc_name', '')
    sc_count = len(sc_name) if isinstance(sc_name, list) else 0
    # Sanity check
    if not c2k_common_stations.__sanity_check1(dict(server_ip=server_ip, ts_ip=ts_ip, ts_start_port=ts_start_port)):
        return

    # PL, TA, TS
    pl, ta, ts = c2k_common_stations.__build_pl_ta_ts(config, product_line, test_area, station, pid_cpn_list, generation, seq_def_lookup)
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
            pcbox = dict(protocol="telnet", host=pcbox_ip_tmp, port=pcbox_port_tmp,
                         timeout=60)  # power cycling box connection conf
            sc.add_connection(name='PCBox', **pcbox)  # Add port cycling box connection
            sc_conn_names = 'SC-Connections='
            # SC connections for PRESEQ
            for i in range(0, uut_count_tmp, 1):
                conn_name_uut = "uutTN_{0:02}".format(i + 1)
                conn_name_uutpwr = "uutPOWER_{0:02}".format(i + 1)
                sc_conn_names = '  '.join([sc_conn_names, conn_name_uut])
                if ts_user_tmp:
                    uut_pwr = dict(host=ts_ip_tmp, protocol="ssh", user=ts_user_tmp, password=ts_pswd_tmp, model=ts_model_tmp, timeout=120)
                    uut = dict(host=ts_ip_tmp, protocol="telnet", port=ts_start_port_tmp + i, power_connection=conn_name_uutpwr,
                               timeout=120)
                    sc.add_connection(name=conn_name_uutpwr, **uut_pwr)
                    sc.add_connection(name=conn_name_uut, **uut)
                else:
                    sc_conn = dict(host=ts_ip, protocol="telnet", port=ts_start_port + i, timeout=120)
                    sc.add_connection(name=conn_name_uut, **sc_conn)
            print("      {0}".format(sc_conn_names))
            containers = create_container(uut_count_tmp, last_stg, ts_ip_tmp, ts_start_port_tmp, ts_model_tmp, ts_user_tmp,
                                          ts_pswd_tmp, psB_ts_ip_tmp, psB_ts_start_port_tmp, dwnld_server_ip_tmp)
            print("      {0} = {1}".format('SYNC GROUP NAME', sysft_sync_group + "_{}".format(j + 1)))
            ts.add_sync_group(sysft_sync_group + "_{}".format(j + 1), containers)
    else:
        # Connections
        last_stg = ts
        create_container(uut_count, last_stg, ts_ip, ts_start_port, ts_model, ts_user, ts_pswd, psB_ts_ip,
                         psB_ts_start_port, dwnld_server_ip)
    return
