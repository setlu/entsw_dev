"""
PRODUCT DEFINITIONS for C3K ArchimedesCR

The product definition file contains descriptive data about a "family" or set of UUTs for the purposes of test automation.
This file should be atomic to the product family defined by Cisco marketing for release (i.e. DO NOT mix product familiy releases).

Convention:
For embedded dict keys
1. All upper case = flash/cookie parameters (Note: CMPD data should be used for the latest revision data and per Area data if available and/or applicable.)
2. All lower case = internal script parameters

Structure:
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

__title__ = "C3K ArchimedesCR Product Definitions"
__version__ = '0.1.1'
__family__ = "archimedes"
__consumer__ = 'c3650.Archimedes'


family = {
    'COMMON': {
        'product_family': "archimedes",

        # Product Generation: 'GEN1', 'GEN2', 'GEN3'
        'product_generation': 'GEN2',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE'
        'uut_category': 'SWITCH',

        # Test Area process flow
        'process_flow': ['ICT', 'PCBST', 'PCB2C', 'ASSY', 'SYSBI', 'HIPOT', 'SYSFT'],

        # Flash Params
        'DDR_SPEED': '667',
        'LINUX_COREMASK': '15',
        'USB_SERIAL_NUM': '',
        'USB_ASSEMBLY_NUM': '',
        'USB_REVISION_NUM': '',
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '128',

        # Images
        'btldr': {'image': '',  # 'cat3k_caa_loader.img.14Jul10.SSA',
                  'rev': {'ver': '', 'date': ''}},
        'linux': {'image': 'vmlinux2013Sep23.mzip.SSA',
                  'ver': ''},
        'diag': {'image': 'stardustThrArchimedes.2014Apr30',
                 'rev': ''},
        'fpga': {'image': '',
                 'rev': '',
                 'name': ''},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S3650UK9-37E',
        'ios_supp_files': {8: [],
                           9: [('ACTUAL', 'recovery')]},

        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        # Sequence to program all IdPro, valid types: QUACK, ACT, X509-n (n=1 to total_hashes)
        'idpro_sequence': ['X509-1', 'ACT'],
        # Access Point SUDI params
        'x509_sudi_hash': ['SHA1'],
        'x509_sudi_request_type': 'PROD',
        'x509_sudi_cert_method': 'KEY',
        'hidden_device': '/dev/sda5',

        # ASIC
        'asic': {'type_ids': ['0x390']},

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'sda', 'secondary': None, 'tertiary': None},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader. Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mounts are placed first in the list.  Specified mounts should correspond to enumerated disks.
        # Format is a list of tuples: [(<device number>, <mount point>), ...]
        'device_mounts': {
            'primary': [(3, '/mnt'), (1, '/mnt/sd1'), (5, '/mnt/sd5'), (6, '/mnt/sd6'), (7, '/mnt/sd7'), (8, '/mnt/sd8'), (9, '/mnt/sd9')],
            'secondary': None,
            'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {
            'primary': None,
            'secondary': None,
            'tertiary': None,
        },

        # Fan tests; TBD is this supported in WS-C3650 ?
        'no_fan': {
            'status_value': '0x0000002A',
            'regs': {'fan1': '0x3C', 'fan2': '0x44', 'fan3': '0x4C'},
            'speed_settings': {'LOW': '0x0A', 'HIGH': '0xFF', 'NOMINAL': '0x7B'},
        },
        # RTC tests
        'rtc': {'time_zone': 'GMT'},

        # StackRac tests
        'stackrac': {'datastack': 0},

        # SerDesEye
        'serdeseye': {'interfaces': ['NIF']},

        # Uplink is a FRU (Field Replaceable Unit); Default is True. False for built-in.
        'uplink_is_fru': False,

        # SBC params
        'sbc': {'enabled': False},

        # PSU
        'psu': {'slots': ['A', 'B']},

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        # 'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        # See PRODUCT sections.

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
        'diag_tests': [('SysMem',          {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('SysRegs',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('RTCTest',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbDet',          {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('UsbConsoleLB',    {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopRegs',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMem',          {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('DopPSRO',         {'areas': ['PCBST', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopMBIST',        {'areas': ['PCBST', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopLBIST',        {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopInterrupt',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopNifCiscoPRBS', {'areas': ['PCBST', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopOffload',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SupFrames',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SupJumboFrames',  {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('PortFrames',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('JumboFrames',     {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('RcpFrames',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DebugFrames',     {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('OOBM',            {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopSifCiscoPRBS', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('InsideLoop',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('Cable',           {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PowerDown',       {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PortIntrDiag',    {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PortCableDiag',   {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('MacSecBistTest',  {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('MACsecDiag',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('EEEDiagTest',     {'areas': ['PCBST', 'PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('REProtocol',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('REI2C',           {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('AlchemySystem',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('AlchemyCommands', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ],

        'traffic_cases_library': {
            '24_U4': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-28': {'speed': '1000'}}
                },
                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-28': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-28': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-28': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-28': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_24_U4

            '24_U4X': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-28': {'speed': '10G'}}
                },

                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-28': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-28': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-28': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-28': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_24_U4X

            '24_U2': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-26': {'speed': '1000'}, '27-28': {'speed': '10G'}}
                },

                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-26': {'speed': '1000', 'size': 1518}, '27-28': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-26': {'speed': '1000', 'size': 64}, '27-28': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'25-26': {'speed': '1000', 'size': 1518}, '27-28': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-24': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'25-26': {'speed': '1000', 'size': 64}, '27-28': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_24_U2

            '48_U4': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-52': {'speed': '1000'}}
                },
                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-52': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-52': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-52': {'speed': '1000', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-52': {'speed': '1000', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_48_U4

            '48_U4X': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-52': {'speed': '10G'}}
                },
                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-52': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-52': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-52': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-52': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_48_U4X

            '48_U2': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-50': {'speed': '1000'}, '51-52': {'speed': '10G'}}
                },
                'TrafCase_EXT_1G_1518': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-50': {'speed': '1000', 'size': 1518}, '51-52': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_64': {
                    'enabled': False,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-50': {'speed': '1000', 'size': 64}, '51-52': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 1518}},
                    'uplink_ports': {'49-50': {'speed': '1000', 'size': 1518}, '51-52': {'speed': '10G', 'size': 1518}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {'1-48': {'speed': '1000', 'size': 64}},
                    'uplink_ports': {'49-50': {'speed': '1000', 'size': 64}, '51-52': {'speed': '10G', 'size': 64}},
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },  # end_48_U2

        },  # traffic_cases

        'cmpd_type_verify_manifest': {
            'T.All.1': {'areas': ['PCBST', 'PCB2C'],
                        'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                  'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                  'MODEL_NUM', 'MODEL_REVISION_NUM',
                                  'DDR_SPEED', 'TERMLINES'
                                  ],
                        },
            'T.All.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
                        'types': ['MAC_ADDR',
                                  'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                  'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                  'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                  'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                  'TAN_NUM', 'TAN_REVISION_NUMBER',
                                  'VERSION_ID', 'DDR_SPEED',
                                  'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                  ],
                        },
            'T.All.3': {'areas': ['SYSFT'],
                        'types': ['MAC_ADDR',
                                  'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                  'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                  'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                  'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                  'TAN_NUM', 'TAN_REVISION_NUMBER',
                                  'VERSION_ID', 'DDR_SPEED',
                                  'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                  ],
                        },

            'P.24.1': {'areas': ['PCBST', 'PCB2C'],
                       'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'DDR_SPEED', 'TERMLINES'
                                 ],
                       },
            'P.24.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 # 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID', 'DDR_SPEED',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },
            'P.24.3': {'areas': ['SYSFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID', 'DDR_SPEED',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },
            'P.48.1': {'areas': ['PCBST', 'PCB2C'],
                       'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'POE2_ASSEMBLY_NUM', 'POE2_REVISION_NUM', 'POE2_SERIAL_NUM',
                                 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'DDR_SPEED', 'TERMLINES'
                                 ],
                       },
            'P.48.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 # 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 # 'POE2_ASSEMBLY_NUM', 'POE2_REVISION_NUM', 'POE2_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID', 'DDR_SPEED',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },
            'P.48.3': {'areas': ['SYSFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'POE2_ASSEMBLY_NUM', 'POE2_REVISION_NUM', 'POE2_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID', 'DDR_SPEED',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },
        },  # cmpd

    },

    'SALINONCR24': {
        'cfg_pids': ['WS-C3650-24TS-L', 'WS-C3650-24TS-E', 'WS-C3650-24TS-S'],
        'MODEL_NUM': 'WS-C3650-24TS',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39319-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15127-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24_U4'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
    },

    'SALINONCR24P': {
        'cfg_pids': ['WS-C3650-24PS-L', 'WS-C3650-24PS-E', 'WS-C3650-24PS-S', 'WS-C3650-24PWS-S'],
        'MODEL_NUM': 'WS-C3650-24PS',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39321-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15128-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '',
        'POE1_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],
        'asic': {'core_count': 1, 'locations': ['U0']},
        'poe': {'uut_ports': '1-24', 'type': 'POE+'},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '24_U4'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.24.1', 'P.24.2', 'P.24.3']),
    },

    'SALINONCR48': {
        'cfg_pids': ['WS-C3650-48TS-L', 'WS-C3650-48TS-E', 'WS-C3650-48TS-S'],
        'MODEL_NUM': 'WS-C3650-48TS',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39284-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15130-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48_U4'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
    },

    'SALINONCR48P': {
        'cfg_pids': ['WS-C3650-48PS-L', 'WS-C3650-48PS-E', 'WS-C3650-48PS-S',
                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWS-S'],
        'MODEL_NUM': 'WS-C3650-48PS',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39286-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15131-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '',
        'POE1_REVISION_NUM': '',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '',
        'POE2_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'poe': {'uut_ports': '1-48', 'type': 'POE+'},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48_U4'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.48.1', 'P.48.2', 'P.48.3']),
    },


    'ARBELOSCR24': {
        'cfg_pids': ['WS-C3650-24TD-L', 'WS-C3650-24TD-E', 'WS-C3650-24TD-S'],
        'MODEL_NUM': 'WS-C3650-24TD',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39313-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15121-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],
        'asic': {'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24_U2'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
    },

    'ARBELOSCR24P': {
        'cfg_pids': ['WS-C3650-24PD-L', 'WS-C3650-24PD-E', 'WS-C3650-24PD-S', 'WS-C3650-24PWD-S'],
        'MODEL_NUM': 'WS-C3650-24PD',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39315-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15122-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '',
        'POE1_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],
        'asic': {'core_count': 1, 'locations': ['U0']},
        'poe': {'uut_ports': '1-24', 'type': 'POE+'},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '24_U2'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.24.1', 'P.24.2', 'P.24.3']),
    },

    'ARBELOSCR48': {
        'cfg_pids': ['WS-C3650-48TD-L', 'WS-C3650-48TD-E', 'WS-C3650-48TD-S'],
        'MODEL_NUM': 'WS-C3650-48TD',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39272-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15124-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48_U2'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
    },

    'ARBELOSCR48P': {
        'cfg_pids': ['WS-C3650-48PD-L', 'WS-C3650-48PD-E', 'WS-C3650-48PD-S',
                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWD-S'],
        'MODEL_NUM': 'WS-C3650-48PD',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-39274-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15125-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '',
        'POE1_REVISION_NUM': '',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '',
        'POE2_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'poe': {'uut_ports': '1-48', 'type': 'POE+'},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48_U2'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.48.1', 'P.48.2', 'P.48.3']),
    },

    'PAPPUSCR48': {
        'cfg_pids': ['WS-C3650-48TQ-L', 'WS-C3650-48TQ-E', 'WS-C3650-48TQ-S'],
        'MODEL_NUM': 'WS-C3650-48TQ',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-40912-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15775-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '48_U4X'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
    },

    'PAPPUSCR48P': {
        'cfg_pids': ['WS-C3650-48PQ-L', 'WS-C3650-48PQ-E', 'WS-C3650-48PQ-S',
                     'WS-C3650-48FQ-L', 'WS-C3650-48FQ-E', 'WS-C3650-48FQ-S', 'WS-C3650-48FWQ-S'],
        'MODEL_NUM': 'WS-C3650-48PQ',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '800-40910-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15776-01',
        'MOTHERBOARD_REVISION_NUM': '',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '',
        'POE1_REVISION_NUM': '',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '',
        'POE2_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'poe': {'uut_ports': '1-48', 'type': 'POE+'},
        'diag_tests': [('PoeDetTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test'}),
                       ('PoeClassTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test'}),
                       ('PoePowerTest', {'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'})],
        'traffic_cases': ('traffic_cases_library', '48_U4X'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.48.1', 'P.48.2', 'P.48.3']),
    },


}  # family_end
