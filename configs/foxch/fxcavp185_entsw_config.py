"""
C3K/C9300 Config
"""

from apollo.libs import lib

__version__ = "0.0.2"
__title__ = "Enterprise Switching C3k Config for FOC Automation FST"
__author__ = ['steli2']


def c3k_sysbi_automation_config():
    """
    Super container - automation communicate with Robert
        containers - test container: UUT:slot-number
    configuration AUTOMATION data to  automation enable
    :return:
    """
    path = 'apollo.scripts.entsw.automation.auto_control'  # Standard path required; link must point to specific module (use run_tests2 >=v2.9.0).
    apollo_config = lib.get_station_configuration()
    uag_production_line = apollo_config.add_production_line(name='UAG_C3K')
    pcbst = uag_production_line.add_area(name='SYSBI')
    station = pcbst.add_test_station(name='Station')
    # Configuration Data
    station.add_configuration_data(key='AUTOMATION', value=dict(enabled=True))

    ssh_dictionary = dict(host='localhost', user='gen-apollo', password='Ad@pCr01!', timeout='30')

    auto_container = station.add_super_container(name='AUTO')
    auto_container.add_connection(name='PC', host="10.1.1.12", port=2027, protocol='telnet')
    auto_container.add_connection(name='LOCAL', protocol='ssh', **ssh_dictionary)

    auto_container.assign_pre_sequence(sequence_definition='{}.pre_control'.format(path))
    auto_container.add_pid_map(pid='73-*', sequence_definition='{}.main_control'.format(path))

    for rack in range(1, 3):
        for slot in range(1, 13):
            cell = auto_container.add_container(name='UUT{:02}_{:02}'.format(rack, slot))
            cell.add_connection(name='uutTN', host='10.1.1.12', port=2003 + (rack - 1) * 12 + (slot - 1), protocol='telnet')
            cell.add_connection(name='serverSSH', protocol='ssh', **ssh_dictionary)
            cell.assign_pre_sequence(
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft_gen2'
            )
            cell.add_pid_map(
                pid='WS-C3*',
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch_sysbi'
            )

    for rack in range(3, 5):
        for slot in range(1, 13):
            cell = auto_container.add_container(name='UUT{:02}_{:02}'.format(rack, slot))
            cell.add_connection(name='uutTN', host='10.1.1.6', port=2003 + (rack - 3) * 12 + (slot - 1), protocol='telnet')
            cell.add_connection(name='serverSSH', protocol='ssh', **ssh_dictionary)
            cell.assign_pre_sequence(
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft_gen2'
            )
            cell.add_pid_map(
                pid='WS-C3*',
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch_sysbi'
            )

    for rack in range(5, 7):
        for slot in range(1, 13):
            cell = auto_container.add_container(name='UUT{:02}_{:02}'.format(rack, slot))
            cell.add_connection(name='uutTN', host='10.1.1.5', port=2003 + (rack - 5) * 12 + (slot - 1), protocol='telnet')
            cell.add_connection(name='serverSSH', protocol='ssh', **ssh_dictionary)
            cell.assign_pre_sequence(
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft_gen2'
            )
            cell.add_pid_map(
                pid='WS-C3*',
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch_sysbi'
            )

    for rack in range(7, 9):
        for slot in range(1, 13):
            cell = auto_container.add_container(name='UUT{:02}_{:02}'.format(rack, slot))
            cell.add_connection(name='uutTN', host='10.1.1.4', port=2003 + (rack - 7) * 12 + (slot - 1), protocol='telnet')
            cell.add_connection(name='serverSSH', protocol='ssh', **ssh_dictionary)
            cell.assign_pre_sequence(
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft_gen2'
            )
            cell.add_pid_map(
                pid='WS-C3*',
                sequence_definition='apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch_sysbi'
            )
