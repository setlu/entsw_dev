"""
PRODUCT DEFINITIONS for C9200 Quake

The product definition file contains descriptive data about a "family" or set of UUTs for the purposes of test automation.
This file should be atomic to the product family defined by Cisco marketing for release (i.e. DO NOT mix product familiy releases).

Convention:
For embedded dict keys
1. All upper case = flash/cookie parameters (Note: CMPD data should be used for the latest revision data and per Area data if available and/or applicable.)
2. All lower case = internal script parameters

Structure:
  uut_prompt = [...]  **optional override**
  uut_state_machine = {...}  **optional override**
  family = {
      'COMMON': {...}
      '<PRODUCT_A>': {...}
      '<PRODUCT_B>': {...}
      ...
      '<PRODUCT_N>': {...}
  } # family_end
  Note1: Product "codenames" MUST be used as the '<PRODUCT_X>' names in the family structure.
         This is done to discern the difference between any cost reduced or improved products having the same
         PIDs as it's previous generation (both codename and CPN should be unique).

  WARNING: All dict elements in this structure must be of numeric, str, tuple, list, or dict types.
           Do not use complex elements (e.g. named tuples, imported objects, etc.),
           as this will cause malformed string input for some processing of the ast function.
"""

__title__ = "C9200 Quake Product Definitions"
__version__ = '2.0.0'
__family__ = "quake"


family = {
    'COMMON': {
        'product_family': "quake",

        # Product Generation: 'GEN1', 'GEN2', 'GEN3'
        'product_generation': 'GEN3',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE'
        'uut_category': 'SWITCH',

        # Test Area process flow
        # 'process_flow': ['ICT', 'PCBP2', 'PCB2C', 'PTXCAL', 'STXCAL', 'PCBFT', 'HIPOT', 'SYSFT'],

        # Flash Params
        'USB_SERIAL_NUM': '',
        'USB_ASSEMBLY_NUM': '73-18785-01',
        'USB_REVISION_NUM': 'A0',
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '128',
        'flash_vb_params': 'ALL',

        # Images
        'btldr': {'image': ['sboot1s_1221.bin', 'sboot2v64s-1221.bin'],
                  'rev': {'ver': '6.2', 'date': '20170919'}},
        'linux': {'image': 'uImage64s.180904',  # 'uImage64.180403',  # 'uImage64.180206',  # 'uImage64.180118',  # 'uImage64.171213',  # 'uImage64.171206',  # 'uImage64.171114',
                  'cfg': 'dtb.171023',  # 'dtb.171020',  # 'dtb_4cores.170810',
                  'rev': ''},
        'diag': {'image': '',
                 'rev': ''},
        'fpga': {'image': '',
                 'rev': '',
                 'revreg': 'fpga_rev',
                 'name': 'strutt'},
        'ios_dirs': {'local': '', 'remote': 'NG2K_IOS'},
        'ios_bin': 'STEST',
        'ios_pkg': '',
        'ios_test_pid': 'STEST',
        'ios_supp_files': {8: [],
                           9: [('ACTUAL', 'recovery')]},

        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        # Sequence to program all IdPro, valid types: QUACK, ACT, X509-n (n=1 to total_hashes)
        'idpro_sequence': ['ACT'],
        # Access Point SUDI params
        # 'x509_sudi_hash': ['SHA1', 'SHA256'],
        # 'x509_sudi_request_type': 'PROD',
        # 'x509_sudi_cert_method': 'KEY',
        # 'hidden_device': '/dev/sda4',

        # ASIC
        'asic': {'type_ids': ['0x3e1']},

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'mmcblk0p', 'secondary': None, 'tertiary': None},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader. Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': '', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mounts are placed first in the list.  Specified mounts should correspond to enumerated disks.
        # Format is a list of tuples: [(<device number>, <mount point>), ...]
        'device_mounts': {
            'primary': [(3, '/mnt/flash3'), (1, '/mnt/flash1'), (2, '/mnt/flash2'), (4, '/mnt/flash4'), (5, '/mnt/flash5'), (6, '/mnt/flash6'), (7, '/mnt/flash7')],
            'secondary': None,
            'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {
            'primary': None,
            'secondary': None,
            'tertiary': None,
        },

        'partition_macro_func': '_partition_format_emmc_v1',

        # Fan tests
        'fan': {
            'status_value': '0x0000002A',
            'regs': {'fan1': '0x3C', 'fan2': '0x44', 'fan3': '0x4C'},
            'speed_settings': {'LOW': '0x0A', 'HIGH': '0xFF', 'NOMINAL': '0x7B'},
        },
        # RTC tests
        'rtc': {'time_zone': 'GMT'},

        # StackRac tests
        'stackrac': {'datastack': 1},

        # SerDesEye
        'serdeseye': {'interfaces': ['NIF']},

        # Uplink is a FRU (Field Replaceable Unit); Default is True. False for built-in.
        'uplink_is_fru': False,

        # SBC params
        'sbc': {'enabled': False},

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        # 'sysinit_required_to_pass': [('PCIE[0-4]: \(RC\) X[1-4] GEN-2 link UP', 1)],
        'sysinit_ignore_errors': ['ERR: ProcessQuackFruEepromAccess failed at QuackReadEeprom',
                                  'ERR: cannot rx data from Quack for cmd type',
                                  'ERR: RxI2cQuackMessage failed at idx'],

        # Chamber Corners (N-Corners)
        #  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
        #  The temp+voltage designations are 2+2letters:
        #    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
        'chamber_corners': [('LTHV', True), ('HTLV', True)],

        # Power cycling test (FST)
        'max_power_cycles': 4,

        # Product Sequence Definition Settings
        # (Parameters that are passed to the sequence definition build-out.)
        'prod_seq_def': {
            'PCBST': {},
            'PCB2C': {},
            'ASSY': {},
            'PCBFT': {'total_loop_time_secs':  3000, 'idpro_periphs': False},
            'SYSBI': {'total_loop_time_secs':  3000, 'idpro_periphs': False},
        },

        # Diag Tests within the Stardust testlist
        # For product-specific tests, place them in the product sections for appending.
        'diag_tests': [('SysMem',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('SysRegs',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('RTCTest',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbDetect',       {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbConsoleIntLB', {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('SqpFramesTest',   {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('CdeFrameCopy',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('MceCryptoOps',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('DopRegs',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMem',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('DopIntr',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopOffload',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('TcamSearch',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('SupFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SupJumboFrames',  {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DpuFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CoreToCore',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopEEE',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopMACsecDiag',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('PortFrames',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('JumboFrames',     {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('RcpFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),

                       ('DopPtpFlexTimer', {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopPtpIngTest',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopPtpEgrTest',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('DopPSRO',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('CrayCorePSRO',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMBIST',        {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopCiscoPRBS',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('OOBM',            {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('Cable',           {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PowerDown',       {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('PortIntrDiag',    {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PortCableDiag',   {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),

                       ('REProtocol',      {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('REI2C',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PsDet',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ],

        'traffic_cases_library': {
            '24': {
                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBP2C'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    # 'uplink_ports': {'25-28': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBP2C'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    # 'uplink_ports': {'25-28': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C', 'PCB2C', 'PCBFT', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    # 'uplink_ports': {'25-28': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C', 'PCB2C', 'PCBFT', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    # 'uplink_ports': {'25-28': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },

            },
            '48': {
                'TrafCase_EXT_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    # 'uplink_ports': {'49-52': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    # 'uplink_ports': {'49-52': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C', 'PCB2C', 'PCBFT', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    # 'uplink_ports': {'49-52': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBP2C', 'PCB2C', 'PCBFT', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    # 'uplink_ports': {'49-52': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },

            },
        },

    },

    'VORE48P': {
        'tlv_type': 'V48P_GIG',
        # V48P_GIG/V48P_10G/V48_GIG/V48_10G/V24P_GIG/V24P_10G/V24_GIG/V24_10G/E48Y/E48M/E24Y/E24M/G48P/G48/G24P/G24/H48/H24
        'cfg_pids': ['C9200L-48P-4G-E', 'C9200L-48P-4G-A'],
        'MODEL_NUM': 'C9200L-48P-4G',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101381-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18365-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '73-18831-01',
        'POE2_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'VORE48PX': {
        'tlv_type': 'V48P_10G',
        'cfg_pids': ['C9200L-48P-4X-E', 'C9200L-48P-4X-A'],
        'MODEL_NUM': 'C9200L-48P-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101382-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18365-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '73-18831-01',
        'POE2_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'VORE48': {
        'tlv_type': 'V48_GIG',
        'cfg_pids': ['C9200L-48T-4G-E', 'C9200L-48T-4G-A'],
        'MODEL_NUM': 'C9200L-48T-4G',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101383-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18698-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'VORE48X': {
        'tlv_type': 'V48_10G',
        'cfg_pids': ['C9200L-48T-4X-E', 'C9200L-48T-4X-A'],
        'MODEL_NUM': 'C9200L-48T-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101384-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18698-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48'),
        'linux': {'image': 'uImage64.180316',
                  'cfg': 'dtb.171020',
                  'rev': ''},

    },

    'VORE24P': {
        'tlv_type': 'V24P_GIG',
        'cfg_pids': ['C9200L-24P-4G-E', 'C9200L-24P-4G-A'],
        'MODEL_NUM': 'C9200L-24P-4G',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101385-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18699-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'VORE24PX': {
        'tlv_type': 'V24P_10G',
        'cfg_pids': ['C9200L-24P-4X-E', 'C9200L-24P-4X-A'],
        'MODEL_NUM': 'C9200L-24P-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101386-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18699-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'VORE24': {
        'tlv_type': 'V24_GIG',
        'cfg_pids': ['C9200L-24T-4G-E', 'C9200L-24T-4G-A'],
        'MODEL_NUM': 'C9200L-24T-4G',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101387-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18700-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'VORE24X': {
        'tlv_type': 'V24_10G',
        'cfg_pids': ['C9200L-24T-4X-E', 'C9200L-24T-4X-A'],
        'MODEL_NUM': 'C9200L-24T-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101388-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18700-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('SysMem', {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 1000})],
        'traffic_cases': ('traffic_cases_library', '24'),
        'linux': {'image': 'uImage64.180306', 'cfg': 'dtb.171020', 'rev': ''},
        'eco_manifest': {('73-18700-01', 'ALL'): ('D999999', None, ['PCBP2'])}
    },

    'GUNNER48P': {
        'tlv_type': 'G48P',
        'cfg_pids': ['C9200-48P-E', 'C9200-48P-A'],
        'MODEL_NUM': 'C9200-48P',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101490-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18791-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '73-18831-01',
        'POE2_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'GUNNER48': {
        'tlv_type': 'G48',
        'cfg_pids': ['C9200-48T-E', 'C9200-48T-A'],
        'MODEL_NUM': 'C9200-48T',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101489-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18792-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'GUNNER24P': {
        'tlv_type': 'G24P',
        'cfg_pids': ['C9200-24P-E', 'C9200-24P-A'],
        'MODEL_NUM': 'C9200-24P',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101488-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18793-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18831-01',
        'POE1_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'GUNNER24': {
        'tlv_type': 'G24',
        'cfg_pids': ['C9200-24T-E', 'C9200-24T-A'],
        'MODEL_NUM': 'C9200-24T',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101487-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18794-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'ENFORCER48Y': {
        'tlv_type': 'E48Y',
        'cfg_pids': ['C9200-48P8X-2Y-E', 'C9200-48P8X-2Y-A'],
        'MODEL_NUM': 'C9200-48P8X-2Y',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101389-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18701-03',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-18775-01',
        'POE1_REVISION_NUM': '04',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48'),
        'linux': {'image': 'uImage64.180306', 'cfg': 'dtb.171020', 'rev': ''},
        'poe': {'uut_ports': '1-48', 'type': 'POE+', 'icutcode': '-v1:0x8'},
        'diag_tests': [('SysMem',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('SysRegs',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('RTCTest',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbDetect',       {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbConsoleIntLB', {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('SqpFramesTest',   {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('CdeFrameCopy',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('MceCryptoOps',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopRegs',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMem',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('DopIntr',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopOffload',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('TcamSearch',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('SupFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SupJumboFrames',  {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DpuFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CoreToCore',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopEEE',          {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopMACsecDiag',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('PortFrames',      {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('JumboFrames',     {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('RcpFrames',       {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopPtpFlexTimer', {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopPtpIngTest',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopPtpEgrTest',   {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopPSRO',         {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('CrayCorePSRO',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMBIST',        {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopCiscoPRBS',    {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('OOBM',            {'areas': ['PCBP2C', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('Cable',           {'areas': ['PCBP2C', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PowerDown',       {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PortIntrDiag',    {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PortCableDiag',   {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('REProtocol',      {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('REI2C',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PsDet',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PoeDetTest',      {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest',    {'areas': ['PCBP2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest',    {'areas': ['PCBP2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
    },

    'ENFORCER48M': {
        'tlv_type': 'E48M',
        'cfg_pids': ['C9200-48P12X-4X-E', 'C9200-48P12X-4X-A'],
        'MODEL_NUM': 'C9200-48P12X-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101390-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18702-02',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48'),
    },

    'ENFORCER24Y': {
        'tlv_type': 'E24Y',
        'cfg_pids': ['C9200-24P8X-2Y-E', 'C9200-24P8X-2Y-A'],
        'MODEL_NUM': 'C9200-24P8X-2Y',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101391-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18703-02',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24'),
    },

    'ENFORCER24M': {
        'tlv_type': 'E24M',
        'cfg_pids': ['C9200-24P8X-4X-E', 'C9200-24P8X-4X-A'],
        'MODEL_NUM': 'C9200-24P8X-4X',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101392-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18704-02',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'CLEI_CODE_NUMBER': '1234567890',
        'ECI_CODE_NUMBER': '123456',
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24'),
    },

}  # family_end
