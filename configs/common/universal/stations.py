"""
========================================================================================================================
CATALYST Universal COMMON Configs
========================================================================================================================

***IMPORTANT***
The following stations are STANDARDIZED for ALL CATALYST SWITCH products at ALL EMS PCBA & DF/ATO Partner sites:
    1. DF:   SystemTest                                   TAs = SYSFT

Please contact Cisco TDE ProdOps/GMO TDEs if the standard configs do not provide the necessary setup!
These configs will be highly governed and should not be changed unless by team review.
------------------------------------------------------------------------------------------------------------------------
"""
# (see separate project) import apollo.scripts.uniassy.configs.uniassy_config as uniassy_config

from collections import namedtuple

__title__ = "Enterprise Switching Catalyst Universal Common Station Configs"
__version__ = "2.0.0"
__author__ = ['bborel']

ApolloSeq = namedtuple('ApolloSeq', 'preseq seq')

# ALL PIDs/CPNs Supported
PID_CPN_MAPS = {
    'ALL':      ['WS-C2*', 'C9200*', 'WS-C3*', 'C9300*', 'WS-C4*', 'C9400*', 'C9500*'],
    'CATALYST': ['WS-C2*', 'C9200*', 'WS-C3*', 'C9300*', 'WS-C4*', 'C9400*', 'C9500*'],
}

def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


# ======================================================================================================================

def switch_sysft(config, **kwargs):
    """ Switch SYSFT
    :param config:
    :param kwargs:
    :return:
    """
    product_line = kwargs.get('product_line', 'CATALYST')
    test_area = kwargs.get('test_area', 'SYSFT')

    seq_def_default = ApolloSeq(
        'apollo.scripts.entsw.libs.cat.CATALYST.area_sequences.universal_sysft.prepare',
        'apollo.scripts.entsw.libs.cat.CATALYST.area_sequences.universal_sysft.standard_switch')

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

    uut_start_ip = kwargs.get('uut_start_ip', None)
    uut_station_index = kwargs.get('uut_station_index', 0)

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
        __uut_ip(cont, uut_start_ip, uut_station_index, uut_count, i)
        #
        containers.append(cont)

    return



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
    print("     {0}".format(pid_cpn_list))
    for pid in pid_cpn_list:
        ts.add_pid_map(pid=pid, sequence_definition=seq_def.seq)
    return pl, ta, ts


def __uut_ip(cont, uut_start_ip, uut_station_index, uut_count, i, sc=False):
    if not uut_start_ip:
        return
    uut_ip_D_subnet = str(int(uut_start_ip.split('.')[3]) + i + (uut_count * uut_station_index))
    uut_ip = '.'.join(uut_start_ip.split('.')[0:3] + [uut_ip_D_subnet])
    if uut_ip_D_subnet <= 253:
        key = 'UUT{0:02}_IP'.format('' if not sc else i)
        print("      {0} = {1}".format(key, uut_ip))
        cont.add_configuration_data(key=key, value=uut_ip)
    return


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
