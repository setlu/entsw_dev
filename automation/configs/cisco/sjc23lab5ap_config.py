from apollo.libs import lib

apollo_config = lib.get_station_configuration()
mackinac_production_line = apollo_config.add_production_line('Mackinac')


def drivers_config():
    path = 'apollo.libs.te_libs.instrument.trunk.driver.gigatronics.pwrmeter.example'
    production_line = apollo_config.add_production_line('Instrument Drivers')
    area = production_line.add_area('PCBP2')
    test_station = area.add_test_station('Drivers')
    test_station.assign_pre_sequence('{}.example_gig865x.drivers_pre'.format(path))
    test_station.add_pid_map(pid='asdf123', sequence_definition='{}.example_gig8651b.example_gig865x'.format(path))
    test_station.add_container('Gigatronics-8651b')
    test_station.add_connection(name='gig865x', host='10.1.1.19', port=2550, protocol='telnet')
    path2 = 'apollo.libs.te_libs.instrument.trunk.driver.gigatronics.pwrmeter.apollo'

    test_station2 = area.add_test_station('DriversTEST')
    test_station2.assign_pre_sequence('{}.example_gig865x.drivers_pre'.format(path2))
    cont1 = test_station2.add_container('Gigatronics-1')
    cont1.add_pid_map(pid='asdf123', sequence_definition='{}.example_gig865x.example_gig865x'.format(path2))

    cont2 = test_station2.add_container('Gigatronics-8651bTN')
    cont2.add_connection(name='gig865x', host='10.1.1.19', port=2550, protocol='telnet')
    cont2.add_pid_map(pid='asdf123', sequence_definition='{}.example_gig865xTN.example_gig865xTN'.format(path2))


def ixm_pcbp2_config():
    # IXM PCBP2 Config
    path = 'apollo.scripts.te_scripts.projects.iot.wpan.mackinac.trunk'
    rf_config_path = '/opt/cisco/te/scripts/projects/iot/wpan/mackinac/trunk/'
    # uut_cfg_list = []
    max_containers = 2
    base_port = 2006
    sync_group = []
    area = mackinac_production_line.add_area('PCBP2')
    test_station = area.add_test_station('IXM')
    test_station.assign_pre_sequence('{}.area_sequences.ixm_pre_sequences.pcbp2_pre'.format(path))
    test_station = add_ixm_pids(test_station, 'pcbp2', path)
    test_station.add_connection(name='IXM_KGB_1', host='10.1.1.2', port=2013, protocol='telnet')

    for uut_num in xrange(max_containers):
        uut = test_station.add_container('UUT{:02d}'.format(uut_num))
        uut.add_connection(name='UUTTN', host='10.1.1.2', port=base_port + 2 * uut_num + 1, protocol='telnet')
        uut.add_connection(name='PWR', host='10.1.1.2', port=base_port + 2 * uut_num, protocol='telnet')
        uut.add_connection(name='KGB', shared_conn='IXM_KGB_1')
        uut.add_connection(name='LOCALHOST', host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        sync_group.append(uut)
    # test_station.add_sync_group(name='SYNCGROUP_1', containers=sync_group)

    uut_cfg = dict(standard='wpan',
                   uut='api_ixm',
                   kgb='api_ixm',
                   instruments=dict(analyzer=dict(model='api_gig865xx',
                                                  self_calibrate=False,
                                                  port_map=dict(inst_port_0='uut_port_0'),
                                                  interface='ip',
                                                  address='10.1.1.19',
                                                  port='2550'),
                                    attenuator=dict(model='api_agj721xx',
                                                    self_calibrate=False,
                                                    port_map=dict(inst_port_0='uut_port_0'),
                                                    interface='ip',
                                                    address='10.1.1.20',
                                                    port='inst0'),
                                    switch=dict(model='api_ag349xx',
                                                self_calibrate=False,
                                                port_map=dict(inst_port_1='uut_port_0'),
                                                interface='ip',
                                                address='10.1.1.21',
                                                port='inst0',
                                                module='ag34947a')
                                    )
                   )

    rf_config = dict(path_loss='{}/rf_path_loss.csv'.format(rf_config_path),
                     test_plan='{}/rf_test_plan.csv'.format(rf_config_path),
                     UUT00=uut_cfg,
                     UUT01=uut_cfg,
                     # UUT02=uut_cfg,
                     # UUT03=uut_cfg,
                     # UUT04=uut_cfg,
                     # UUT05=uut_cfg,
                     )
    test_station.add_configuration_data('rf_config', rf_config)


def ixm_pcb2c_config():
    # IXM PCB2C Config
    path = 'apollo.scripts.te_scripts.projects.iot.wpan.mackinac.trunk'
    rf_config_path = '/opt/cisco/te/scripts/projects/iot/wpan/mackinac/trunk/'
    rf_config = dict(path_loss='{}/rf_path_loss.csv'.format(rf_config_path), test_plan='{}/rf_test_plan.csv'.format(rf_config_path), )

    area = mackinac_production_line.add_area('PCB2C')
    test_station = area.add_test_station('IXM_PCB2C_1')
    test_station.assign_pre_sequence(sequence_definition='{}.area_sequences.ixm_pre_sequences.pcb2c_pre'.format(path))
    test_station = add_ixm_pids(test_station, 'pcb2c', path)
    super_container = test_station.add_super_container('CHAMBER_1')
    test_station.add_connection(name='Chamber',
                                protocol='telnet',
                                host='10.89.133.60',
                                port=2010,
                                model='watlow_yinhe_simulator')
    max_containers = 4
    base_port = 2010
    uut_objects_list = []
    uut_str_list = []
    sync_group = []
    sync_group_str_list = []
    [super_container.add_connection(name='UUT{:02d}'.format(uut_num), host='10.1.1.2', port=base_port + 1 + uut_num * 2, protocol='telnet') for uut_num in xrange(max_containers)]
    [super_container.add_connection(name='PWR{:02d}'.format(uut_num), host='10.1.1.2', port=base_port + uut_num * 2, protocol='telnet') for uut_num in xrange(max_containers)]
    [super_container.add_connection(name='LH{:02d}'.format(uut_num), host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh') for uut_num in xrange(max_containers)]
    for uut_num in xrange(max_containers):
        kgb_offset = 1
        uut = super_container.add_container('UUT{:02d}'.format(uut_num))
        uut.add_connection(name='PWR', host='10.1.1.2', port=base_port + uut_num * 2, protocol='telnet')
        # kgb_port = -2 if uut_num % 2 == 1 else 2
        # uut.add_connection(name='KGB', host='10.1.1.2', port=base_port + 1 + uut_num * 2 + kgb_port, protocol='Telnet')
        uut.add_connection(name='Chamber', shared_conn='Chamber')
        uut.add_connection(name='LOCALHOST', host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        uut_objects_list.append(uut)
        uut_str_list.append(uut.key)
        sync_group.append(uut)
        sync_group_str_list.append(uut.key)
        rf_config['UUT{:02d}'.format(uut_num)] = dict(standard='wpan', uut='api_ixm', kgb='api_ixm', instruments=None)
        if uut_num % 2:  # odd
            test_station.add_sync_group(name='SYNCGROUP_{}'.format(uut_num / 2), containers=sync_group)
            test_station.add_configuration_data('SYNCGROUP_{}'.format(uut_num / 2), sync_group_str_list)
            sync_group = []
            sync_group_str_list = []
            kgb_offset = -1
        uut.add_connection(name='UUTTN', shared_conn='UUT{:02d}'.format(uut_num))
        uut.add_connection(name='KGB', shared_conn='UUT{:02d}'.format(uut_num + kgb_offset))
    test_station.add_configuration_data('Group1', uut_str_list)
    test_station.add_sync_group(name='Group1', containers=uut_objects_list)
    test_station.add_configuration_data('rf_config', rf_config)


def ixm_rdt_chamber_config():
    # IXM RDT Config
    path = 'apollo.scripts.te_scripts.projects.iot.wpan.mackinac.trunk'
    rf_config_path = '/opt/cisco/te/scripts/projects/iot/wpan/mackinac/trunk'
    rf_config = dict(path_loss='{}/rf_path_loss.csv'.format(rf_config_path), test_plan='{}/rf_test_plan.csv'.format(rf_config_path), )

    area = mackinac_production_line.add_area('SYSBI')
    test_station = area.add_test_station('IXM_RDT_1')
    test_station.assign_pre_sequence(sequence_definition='{}.area_sequences.ixm_pre_sequences.rdt_chamber_pre'.format(path))
    test_station = add_ixm_pids(test_station, 'rdt', path)
    super_container = test_station.add_super_container('CHAMBER_1')
    test_station.add_connection(name='Chamber',
                                protocol='telnet',
                                host='10.89.133.60',
                                port=2010,
                                model='watlow_yinhe_simulator')
    max_containers = 4
    base_port = 2010
    uut_objects_list = []
    uut_str_list = []
    sync_group = []
    sync_group_str_list = []
    for uut_num in xrange(max_containers):
        super_container.add_connection(name='UUT{:02d}'.format(uut_num), host='10.1.1.2', port=base_port + 1 + uut_num * 2, protocol='telnet')
        super_container.add_connection(name='PWR{:02d}'.format(uut_num), host='10.1.1.2', port=base_port + uut_num * 2, protocol='telnet')
        super_container.add_connection(name='LH{:02d}'.format(uut_num), host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        uut = super_container.add_container('UUT{:02d}'.format(uut_num))
        uut.add_connection(name='PWR', host='10.1.1.2', port=base_port + uut_num * 2, protocol='telnet')
        uut.add_connection(name='Chamber', shared_conn='Chamber')
        uut.add_connection(name='LOCALHOST', host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        uut_objects_list.append(uut)
        uut_str_list.append(uut.key)
        sync_group.append(uut)
        sync_group_str_list.append(uut.key)
        rf_config['UUT{:02d}'.format(uut_num)] = dict(standard='wpan', uut='api_ixm', kgb='api_ixm', instruments=None)
        kgb_offset = 1
        if uut_num % 2:  # odd
            test_station.add_sync_group(name='SYNCGROUP_{}'.format(uut_num / 2), containers=sync_group)
            test_station.add_configuration_data('SYNCGROUP_{}'.format(uut_num / 2), sync_group_str_list)
            sync_group = []
            sync_group_str_list = []
            kgb_offset = -1
        uut.add_connection(name='UUTTN', shared_conn='UUT{:02d}'.format(uut_num))
        uut.add_connection(name='KGB', shared_conn='UUT{:02d}'.format(uut_num + kgb_offset))

    test_station.add_configuration_data('Group1', uut_str_list)
    test_station.add_sync_group(name='Group1', containers=uut_objects_list)
    test_station.add_configuration_data('rf_config', rf_config)


def ixm_rdt_config():
    # IXM RDT Config
    path = 'apollo.scripts.te_scripts.projects.iot.wpan.mackinac.trunk'
    rf_config_path = '/opt/cisco/te/scripts/projects/iot/wpan/mackinac/trunk'
    rf_config = dict(path_loss='{}/rf_path_loss.csv'.format(rf_config_path), test_plan='{}/rf_test_plan.csv'.format(rf_config_path), )

    area = mackinac_production_line.add_area('PCBST')
    test_station = area.add_test_station('IXM_RDT_2')
    test_station.assign_pre_sequence(sequence_definition='{}.area_sequences.ixm_pre_sequences.rdt_pre'.format(path))
    test_station = add_ixm_pids(test_station, 'rdt', path)
    max_containers = 2
    base_port = 2014
    uut_objects_list = []
    uut_str_list = []
    sync_group = []
    sync_group_str_list = []
    for uut_num in xrange(max_containers):
        test_station.add_connection(name='UUT{:02d}'.format(uut_num), host='10.1.1.2', port=base_port + 1 + uut_num * 2, protocol='telnet')
        uut = test_station.add_container('UUT{:02d}'.format(uut_num))
        uut.add_connection(name='PWR', host='10.1.1.2', port=base_port + uut_num * 2, protocol='telnet')
        uut.add_connection(name='LOCALHOST', host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        uut_objects_list.append(uut)
        uut_str_list.append(uut.key)
        sync_group.append(uut)
        sync_group_str_list.append(uut.key)
        rf_config['UUT{:02d}'.format(uut_num)] = dict(standard='wpan', uut='api_ixm', kgb='api_ixm', instruments=None)
        kgb_offset = 1
        if uut_num % 2:  # odd
            test_station.add_sync_group(name='SYNCGROUP_{}'.format(uut_num / 2), containers=sync_group)
            test_station.add_configuration_data('SYNCGROUP_{}'.format(uut_num / 2), sync_group_str_list)
            sync_group = []
            sync_group_str_list = []
            kgb_offset = -1
        uut.add_connection(name='UUTTN', shared_conn='UUT{:02d}'.format(uut_num))
        uut.add_connection(name='KGB', shared_conn='UUT{:02d}'.format(uut_num + kgb_offset))
    test_station.add_configuration_data('Group1', uut_str_list)
    test_station.add_sync_group(name='Group1', containers=uut_objects_list)
    test_station.add_configuration_data('rf_config', rf_config)


def ixm_rpcbbi_config():
    # IXM RDT Config
    # power 10.1.1.2  2021, 2022
    # console  10.1.1.3  2037, 2038
    path = 'apollo.scripts.te_scripts.projects.iot.wpan.mackinac.trunk'
    rf_config_path = '/opt/cisco/te/scripts/projects/iot/wpan/mackinac/trunk'
    rf_config = dict(path_loss='{}/rf_path_loss.csv'.format(rf_config_path), test_plan='{}/rf_test_plan.csv'.format(rf_config_path), )

    production_line = apollo_config.add_production_line('FOC Mackinac')
    area = production_line.add_area('RPCBBI')
    test_station = area.add_test_station('IXM_RDT_FOC')
    test_station.assign_pre_sequence(sequence_definition='{}.area_sequences.ixm_pre_sequences.rdt_pre'.format(path))
    test_station = add_ixm_pids(test_station, 'rdt', path)
    max_containers = 2
    # base_port = 2014
    uut_objects_list = []
    uut_str_list = []
    sync_group = []
    sync_group_str_list = []
    for uut_num in xrange(max_containers):
        test_station.add_connection(name='UUT{:02d}'.format(uut_num), host='10.1.1.3', port=2037 + uut_num, protocol='telnet')
    for uut_num in xrange(max_containers):
        uut = test_station.add_container('UUT{:02d}'.format(uut_num))
        uut.add_connection(name='PWR', host='10.1.1.2', port=2021 + uut_num, protocol='telnet')
        uut.add_connection(name='LOCALHOST', host='localhost', user='gen-apollo', password='Ad@pCr01!', protocol='ssh')
        uut_objects_list.append(uut)
        uut_str_list.append(uut.key)
        sync_group.append(uut)
        sync_group_str_list.append(uut.key)
        rf_config['UUT{:02d}'.format(uut_num)] = dict(standard='wpan', uut='api_ixm', kgb='api_ixm', instruments=None)
        kgb_offset = 1
        if uut_num % 2:  # odd
            test_station.add_sync_group(name='SYNCGROUP_{}'.format(uut_num / 2), containers=sync_group)
            test_station.add_configuration_data('SYNCGROUP_{}'.format(uut_num / 2), sync_group_str_list)
            sync_group = []
            sync_group_str_list = []
            kgb_offset = -1
        uut.add_connection(name='UUTTN', shared_conn='UUT{:02d}'.format(uut_num))
        uut.add_connection(name='KGB', shared_conn='UUT{:02d}'.format(uut_num + kgb_offset))
    test_station.add_configuration_data('Group1', uut_str_list)
    test_station.add_sync_group(name='Group1', containers=uut_objects_list)
    test_station.add_configuration_data('rf_config', rf_config)


def add_ixm_pids(test_station_obj, test_station, path):
    """
    Add all of the pids to test station map
    :param test_station_obj: (obj) test station object to add pids to.
    :param test_station: (str) test station name.
    :param path: (str)  Path name.
    :return:
    """
    act2 = 'ixm_act2'
    cookie = 'ixm_cookie'
    rf = 'rf'
    test_station_obj.add_pid_map(pid='IXM-WPAN-800', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, test_station))
    test_station_obj.add_pid_map(pid='IXM-RDT', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, test_station))
    test_station_obj.add_pid_map(pid='IXM-ACT2', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, act2))
    test_station_obj.add_pid_map(pid='IXM-ALL', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, test_station))
    test_station_obj.add_pid_map(pid='IXM-COOKIE', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, cookie))
    test_station_obj.add_pid_map(pid='IXM-RF', sequence_definition='{}.area_sequences.ixm_{}_run.{}'.format(path, test_station, rf))
    return test_station_obj
