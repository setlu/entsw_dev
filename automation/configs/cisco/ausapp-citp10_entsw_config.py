""" CITP USTX Configuration File

Continuous Integration Test Platform - Austin,TX
Enterprise Switching & IoT
Host: ausapp-citp10
Primary IP   (eth0): 10.89.133.152
Secondary IP (eth1): 10.1.10.1
CIMC IP: 10.89.133.153
"""

from apollo.libs import lib
import apollo.scripts.entsw.configs.cisco.ausapp_citp_entsw_common as ausapp_citp_entsw_common

__title__ = "Enterprise Switching Config for CITP Austin"
__version__ = "2.0.0"
__author__ = ['bborel']


def entsw_cat3_config():
    ausapp_citp_entsw_common.cat3_lab('10.89.133.152', '10.1.1.1')
    return


def entsw_cat2_config():
    ausapp_citp_entsw_common.cat2_lab('10.89.133.152', '10.1.1.1')
    return
#
#
# ------------------------------------------------------------------------

TS_CONN_ARGS = dict(protocol='terminalserver',
                    host='10.89.133.200')
# ,                     password='c')
PATH = 'apollo.scripts.te_scripts.users.detravis.abel.trunk'
MAX_CONTAINERS = 5

# ABEL
apollo_config = lib.get_station_configuration()
abel_production_line = apollo_config.add_production_line('Abel')
area = abel_production_line.add_area('PCBP2')
test_station = area.add_test_station('PCBP2_001')

test_station.assign_pre_sequence('{}.abel_pcbp2_run.abel_pre'.format(PATH))
test_station.add_pid_map(pid='ABEL', sequence_definition='{}.abel_pcbp2_run.abel'.format(PATH))

for uut_num in xrange(MAX_CONTAINERS):
    uut = test_station.add_container('UUT{:02d}'.format(uut_num))
    uut.add_connection(name='uut', port=2003, **TS_CONN_ARGS)
