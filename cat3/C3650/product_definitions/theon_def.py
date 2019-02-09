"""
PRODUCT DEFINITIONS for C3K Theon

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

__title__ = "C3K Theon Product Definitions"
__version__ = '0.2.0'
__family__ = "theon"
__consumer__ = 'c3650.Theon'


family = {
    'COMMON': {
        'product_family': "theon",

        # Product Generation: 'GEN1', 'GEN2', 'GEN3'
        'product_generation': 'GEN2',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE'
        'uut_category': 'SWITCH',

        # Test Area process flow
        'process_flow': ['ICT', 'PCBST', 'PCB2C', 'ASSY', 'SYSBI', 'HIPOT', 'SYSFT'],

        # Flash Params
        'DDR_SPEED': '667',
        'LINUX_COREMASK': '15',
        'STKPWR_SERIAL_NUM': '',
        'STKPWR_ASSEMBLY_NUM': '',
        'STKPWR_REVISION_NUM': '',
        'USB_SERIAL_NUM': '',
        'USB_ASSEMBLY_NUM': '',
        'USB_REVISION_NUM': '',
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '128',

        # Images
        'btldr': {'image': 'cat3k_caa_loader.img.SSA',
                  'rev': {'ver': '', 'date': ''}},
        'linux': {'image': 'vmlinux13Sep03.mzip.SSA',  # 'vmlinux2015Apr22.mzip.SSA',
                  'rev': ''},
        'diag': {'image': 'stardust2016Jan18',
                 'rev': ''},
        'fpga': {'image': 'hypatia.hex',
                 'rev': '0001',
                 'name': 'hypatia'},
        # MCU images given by a subdir as the dict keys.
        'mcu': {'images': {'kirch90': ['app_data.srec_V90', 'app_flash.bin_V90', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                       'c_kirchhoff_swap_33.bin', 'coulomb_kirchhoff_33.bin']},
                'name': 'alchemy',
                'rev': {'ios': '', 'coulomb': ''}},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S3850UK9-162',
        'ios_pkg': '',
        'ios_supp_files': {8: [],
                           9: [('ACTUAL', 'recovery')]},

        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        # Sequence to program all IdPro, valid types: QUACK, ACT, X509-n (n=1 to total_hashes)
        'idpro_sequence': ['X509-1', 'ACT', 'X509-2'],
        # Access Point SUDI params
        'x509_sudi_hash': ['SHA1', 'SHA256'],
        'x509_sudi_request_type': 'PROD',
        'x509_sudi_cert_method': 'KEY',
        'hidden_device': '/dev/sda5',

        # ASIC
        'asic': {'type_ids': ['0x3ce']},

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

        # Psuedo-SLC mode (Linux macros required - one-shot)
        'set_pSLC_mode': True,

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
        'serdeseye': {'interfaces': ['SIF', 'NIF']},

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
                       ('PsDet',           {'areas': ['PCBST', 'PCB2C', 'ASSY', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('JJDet',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('JJReg',           {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('JJCtrl',          {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('JJBackup',        {'areas': ['ASSY'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('StackPwrDet',     {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('StackPwrCtrl',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('PoeDetTest_CSCO', {'cmd': 'PoeDetTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test', 'func_args': {'detecttype': [1], 'mdimode': [0, 1]}}),
                       ('PoeDetTest_IEEE', {'cmd': 'PoeDetTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test', 'func_args': {'detecttype': [2], 'mdimode': [1]}}),
                       ('PoeClassTest_0',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [0]}}),
                       ('PoeClassTest_1',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [1]}}),
                       ('PoeClassTest_2',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [2]}}),
                       ('PoeClassTest_3',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [3]}}),
                       ('PoeClassTest_4',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [4]}}),
                       ('PoePowerTest',    {'cmd': 'PoePowerTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'}),
                       ],

        'cmpd_type_verify_manifest': {
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

    'THEON24P': {
        'cfg_pids': ['WS-C3650-24PDM-L', 'WS-C3650-24PDM-E', 'WS-C3650-24PDM-S'],
        'MODEL_NUM': 'WS-C3650-24PDM',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '68-100561-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-17735-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],
        'asic': {'core_count': 1, 'locations': ['U0']},
        'poe': {'uut_ports': '1-24', 'type': 'POE+', 'volt_range': (47.0, 56.0), 'current_range': (486, 594)},
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.24.1', 'P.24.2', 'P.24.3']),
        'eco_manifest': {('68-100561-02E0', 'FTX'): (None, 'EA556109', ['SYSFT'], ''),
                         ('68-100561-02D0', 'FTX'): (None, '91370', ['SYSFT'], ''),
                         ('68-100561-02C0', 'FTX'): (None, '89850', ['SYSFT'], ''),
                         ('68-100561-02B0', 'FTX'): (None, 'EA546824', ['SYSFT'], ''),
                         ('68-100561-02A0', 'FTX'): (None, 'EA546824', ['SYSFT'], ''),
                         ('68-100561-01B0', 'FTX'): (None, 'EA536296', ['SYSFT'], ''),
                         ('68-100561-01A0', 'FTX'): (None, '77531', ['SYSFT'], ''),
                         },

    },

    'THEON48P': {
        'cfg_pids': ['WS-C3650-48FQM-L', 'WS-C3650-48FQM-E', 'WS-C3650-48FQM-S'],
        'MODEL_NUM': 'WS-C3650-48FQM',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '68-100560-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-17734-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'core_count': 2, 'locations': ['U0']},
        'poe': {'uut_ports': '1-48', 'type': 'POE+', 'volt_range': (47.0, 56.0), 'current_range': (486, 594)},
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.48.1', 'P.48.2', 'P.48.3']),
        'eco_manifest': {('68-100560-02E0', 'FTX'): (None, '91801', ['SYSFT'], ''),
                         ('68-100560-02D0', 'FTX'): (None, 'EA555740', ['SYSFT'], ''),
                         ('68-100560-02C0', 'FTX'): (None, 'EA550284', ['SYSFT'], ''),
                         ('68-100560-02B0', 'FTX'): (None, 'EA550284', ['SYSFT'], ''),
                         ('68-100560-02A0', 'FTX'): (None, '84570', ['SYSFT'], ''),
                         ('68-100560-01B0', 'FTX'): (None, 'EA543277', ['SYSFT'], ''),
                         ('68-100560-01A0', 'FTX'): (None, '77540', ['SYSFT'], ''),
                         }

    },

}  # family_end
