# -*- coding: utf-8 -*-
from apollo.libs import lib

__version__ = '0.1'


# Test production line definition
PROD_LINE = 'SPARROW'
# Test area definition
TEST_AREA = 'PCBP2'
# PID list definition
SPARROW_PID_DICT = ['IR1101-K9', ]
# Root Path
ROOT_PATH = 'apollo.scripts.te_scripts.projects.iot.ir1100'

# UUT = dict(protocol='ssh', host='localhost', user='gen-apollo', password='Ad@pCr01!', timeout='300')
UUT = dict(protocol='telnet', user='', password='', timeout='300')
POWER = dict(protocol='telnet', user='', password='', timeout='300')
KGB = dict(protocol='telnet', host='10.1.1.2', port=2003, user='', password='', timeout='300')


# define UUT Qty, from which number to which number
uut_range = range(0, 1)
# define console range, in case it is not serial by HW setup.
# 2003 means Terminal Server is 2900
# 2002 means Terminal Server is 2800
power_range = ['10.1.1.2:2004', ]

# it is for UUT connection to telnet to unit.
console_range = ['10.1.1.4:4001', ]


def sjc23labap2_config():

    config = lib.get_station_configuration()
    # production line
    pl = config.add_production_line(PROD_LINE)
    # test area
    ar = pl.add_area(TEST_AREA)

    # test station for Coronado
    ts = ar.add_test_station('Sparrow BST')
    ts.assign_pre_sequence('{}.sparrow.trunk.area_sequences.lab_run.pre'.format(ROOT_PATH))

    # It will work base on the uuttype of add_tst_data
    for pid in SPARROW_PID_DICT:
        ts.add_pid_map(pid=pid,
                       sequence_definition='{}.sparrow.trunk.area_sequences.lab_run.sparrow_main'.format(ROOT_PATH))

    ts.add_connection(name='KGB', **KGB)
    sync_group = []
    for idx in uut_range[0:1]:
        container = ts.add_container('UUT{:02d}'.format(idx))
        uut = dict(host=console_range[idx].split(':')[0], port=console_range[idx].split(':')[1], **UUT)
        container.add_connection(name='UUT', **uut)

        power = dict(host=power_range[idx].split(':')[0], port=power_range[idx].split(':')[1], **POWER)
        container.add_connection(name='POWER', **power)
        container.add_connection(name='KGB', shared_conn='KGB')

        # container.add_configuration_data('console_port', console_range[idx])
        container.add_configuration_data('ip_address', '10.1.1.{}'.format(50 + idx))
        container.add_configuration_data('rf_group', 'GROUP_1')
        sync_group.append(container)

    ts.add_sync_group(name="GROUP_1", containers=sync_group)
