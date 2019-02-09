"""
PRODUCT DEFINITIONS for C9400 Macallan Supervisors

The product definition file contains descriptive data about a "family" or set of UUTs for the purposes of test automation.
This file should be atomic to the product family defined by Cisco marketing for release (i.e. DO NOT mix product familiy releases).

Convention:
For embedded dict keys
1. All upper case = flash/cookie/eeprom parameters (Note: CMPD data should be used for the latest revision data and per Area data if available and/or applicable.)
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
from collections import OrderedDict

__title__ = "C9400 Macallan Supervisors Product Definitions"
__version__ = '0.1.1'
__family__ = 'macallan_sup'

# Custom TLV Map for ALL Supervisors
tlv_map_list = [
    ('Hardware Version <major.minor>',  ('0x41', 'MODEL_REVISION_NUM')),
    ('Part Number - PCA',               ('0x82', 'MOTHERBOARD_ASSEMBLY_NUM')),
    ('Revision number - PCA',           ('0x42', 'MOTHERBOARD_REVISION_NUM')),
    ('Deviation Number',                ('0x88', 'DEVIATION_NUM')),
    ('PCB Fab Version',                 ('0x0',  'PCB_REVISION_NUM')),
    ('Serial Number - PCA',             ('0xC1', 'SERIAL_NUM')),
    ('RMA test history',                ('0x03', 'RMA_TEST_HISTORY')),
    ('RMA Number',                      ('0x81', 'RMA_NUM')),
    ('RMA history',                     ('0x04', 'RMA_HISTORY')),
    ('Part Number -TAN',                ('0x87', 'TAN_NUM')),
    ('Revision number - TAN',           ('0x8D', 'TAN_REVISION_NUMBER')),
    ('CLEI codes',                      ('0xC6', 'CLEI_CODE')),
    ('ECI number - Number',             ('0x8E', 'ECI_NUM')),
    ('Product number/identifier',       ('0xCB', 'MODEL_NUM')),
    ('UDI Product Name',                ('0xCB', 'CFG_MODEL_NUM')),
    ('Version identifier',              ('0x89', 'VERSION_ID')),
    ('MAC address - Base',              ('0xC3', 'MAC_ADDR')),
    ('MAC address - block size',        ('0xC4', 'MAC_BLOCK_SIZE')),
    ('RFID - chassis',                  ('0xE4', 'RFID_TID')),
    ('RFID - PCA',                      ('0x0',  'RFID_PCA_TID')),
    ('Manufacturing test data',         ('0xC4', 'MFG_TEST_DATA')),
    ('Field Diagnostic info',           ('0x0',  'FIELD_DIAG_INFO')),
]
tlv_map = OrderedDict(tlv_map_list)

family = {
    'COMMON': {
        'product_family': 'macallan_sup',

        # Product Generation: only GEN3 supported.
        'product_generation': 'GEN3',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE', 'SUP', 'LINECARD'
        'uut_category': 'SUP',

        'modular': True,

        # Flash Params
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '12',

        # Images
        'btldr': {'proto_image': '',  # pre-packaged in linux kernel
                  'production_image': '',
                  'rev': {'ver': '', 'date': ''}},
        'linux': {'image': 'mcln_x86_kernel_20171101.SSA',
                  'rev': ''},
        'diag': {'image': 'sdX86_thr1B.180913',  # 'sdX86_thr1B.180228',
                 'rev': ''},
        'fpga': {'image': '',  # pre-packaged in linux kernel
                 'rev': '',
                 'name': ''},
        'ios_dirs': {'local': '', 'remote': ''},
        'ios_test_pid': 'STEST',
        'ios_supp_files': {},

        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        # Sequence to program all IdPro, valid types: QUACK, ACT, X509-n (n=1 to total_hashes)
        'idpro_sequence': ['X509-1', 'ACT2-RSA', 'X509-2'],  # ['X509-1', 'ACT2-RSA', 'ACT2-HARSA', 'X509-2', 'X509-3'],
        # Access Point SUDI params
        # 'x509_sudi_hash': ['SHA1', 'SHA256', 'CMCA3'],
        'x509_sudi_hash': ['SHA1', 'SHA256'],
        'x509_sudi_request_type': 'PROD',
        'x509_sudi_cert_method': 'KEY',
        'hidden_device': '/dev/sda4',

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'sda', 'secondary': None, 'tertiary': None},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader. Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mounts are placed first in the list.  Specified mounts should correspond to enumerated disks.
        # Format is a list of tuples: [(<device number>, <mount point>), ...]
        'device_mounts': {
            'primary': [(3, '/mnt/flash3'), (1, '/mnt/flash1'), (2, '/mnt/flash2'),
                        (4, '/mnt/flash4'), (5, '/mnt/flash5'), (6, '/mnt/flash6'), (7, '/mnt/flash7')],
            'secondary': None,
            'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {
            'primary': None,
            'secondary': None,
            'tertiary': None,
        },

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
        'sbc': {'enabled': True, 'temperature_reg': 'READ_TEMPERATURE_2'},

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        'sysinit_required_to_pass': [('PCIE[0234]: \(RC\) X4 GEN-2 link UP', 4)],

        # Chamber Corners (N-Corners)
        #  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
        #  The temp+voltage designations are 2+2letters:
        #    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
        'chamber_corners': [('LTHV', True), ('HTLV', True)],

        # Power cycling test (PCBST)
        'max_power_cycles': 4,

        # Product Sequence Definition Settings
        # (Parameters that are passed to the sequence definition build-out.)
        'prod_seq_def': {
            'PCBP2': {},
            'PCB2C': {},
            'PCBST': {'total_loop_time_secs': 3000},
        },

        # Diag Tests within the Stardust testlist - listed in order that follows stardust testlist command output
        # For product-specific tests, place them in the product sections for appending.
        # Category definition
        # 1: Tests that require SUP to be active SUP, hence we run on 1 SUP at a time
        # 2: Tests that can run with SUP in active or standby mode, hence we can run these tests on both SUPs at the same time, hence we run on 1 SUP at a time
        # 3: Tests that can run with SUP in active or standby mode BUT test targets a shared resource like the other SUP, a LC, a PSU, the fan-tray, hence we run on 1 SUP at a time

        'diag_tests': [('SysMem',          {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('PCIeSup2Sup',     {'category': 3, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 300}),
                       ('RTCTest',         {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('IoFpgaLocalQ',    {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('IoFpgaDmaQ',      {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('IoFpgaDmaIndQ',   {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('IoFpgaSpiFlash',  {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SpqFramesTest',   {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CdeFrameCopy',    {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CraySRAMTest',    {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopRegs',         {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopMem',          {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('DopIntr',         {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopOffload',      {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('TcamSearch',      {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SupFrames',       {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('SupJumboFrames',  {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DpuFrames',       {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 400}),
                       ('CoreToCore',      {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('PortFrames',      {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('JumboFrames',     {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopMACsecDiag',   {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('RcpFrames',       {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('NruPortFramesA',  {'category': 1, 'cmd': 'NruPortFrames', 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 600}),
                       ('NruPortFramesB',  {'category': 3, 'cmd': 'NruPortFrames', 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:auxsup', 'timeout': 600}),
                       ('OOBM',            {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopPtpFlexTimer', {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 300}),
                       ('DopPtpIngTest',   {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 300}),
                       ('DopPtpEgrTest',   {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 300}),
                       ('DopPSRO',         {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CrayCorePSRO',    {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('DopMBIST',        {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 800}),
                       ('DopCiscoPRBS',    {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 500}),
                       ('UsbDetect',       {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('UsbConsoleIntLB', {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('UsbConsoleExtLB', {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('CpuToDopFrames',  {'category': 2, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 300}),
                       ('SUP2SUPTest',     {'category': 3, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '-s:sup', 'timeout': 300}),
                       ],

        'traffic_cases_library': {
            'ALL': {
                'TrafCase_MAC_24p_Sup_1_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-24': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '1G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_MAC_24p_Sup_10_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-24': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '10G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_MAC_24p_Sup_40_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-24': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '40G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_MAC_48p_Sup_1_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-48': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '1G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_MAC_48p_Sup_10_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-48': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '10G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_MAC_48p_Sup_40_64': {
                    'enabled': True,
                    'areas': ['PCBP2'],
                    'downlink_ports': {'1-48': {'speed': 'AUTO', 'size': 64}},
                    'sup_ports': {
                        '1-8': {'speed': '40G', 'loopback_direction': 'Bidirectional', 'loopback_point': 'External'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'MAC0',
                    'poe_enabled': False,
                    'runtime': 30,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },
        },  # traffic_cases

        'cmpd_type_verify_manifest': {
        },  # cmpd

    },

    'PASSPORTV1': {
        'cfg_pids': [],
        'MODEL_NUM': 'C9400-SUP-1',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-6264-03',
        'TAN_REVISION_NUMBER': 'B0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-18517-03',
        'MOTHERBOARD_REVISION_NUM': 'C0',
        'VERSION_ID': 'V01',
        'SBC_CFG': '',
        'traffic_cases': ('traffic_cases_library', 'ALL'),
        'cmpd_types': ('cmpd_type_verify_manifest', []),
        'eco_manifest': {},
    },

    'PASSPORTV2': {
        'cfg_pids': [],
        'MODEL_NUM': 'C9400-SUP-1',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-6548-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-19001-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG': '',
        'traffic_cases': ('traffic_cases_library', 'ALL'),
        'cmpd_types': ('cmpd_type_verify_manifest', []),
        'eco_manifest': {},
    },

    'PASSPORTXLV2': {
        'cfg_pids': [],
        'MODEL_NUM': 'C9400-SUP-XL',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-6636-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-19118-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG': '',
        'traffic_cases': ('traffic_cases_library', 'ALL'),
        'cmpd_types': ('cmpd_type_verify_manifest', []),
        'eco_manifest': {},
    },

    'PASSPORT25G': {
        'cfg_pids': [],
        'MODEL_NUM': 'C9400-SUP-1-Y',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-101273-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-19000-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG': '',
        'traffic_cases': ('traffic_cases_library', 'ALL'),
        'cmpd_types': ('cmpd_type_verify_manifest', []),
        'eco_manifest': {},
    },

    'PASSPORT25GXL': {
        'cfg_pids': [],
        'MODEL_NUM': 'C9400-SUP-1XL-Y',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-6516-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-101371-02',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG': '',
        'traffic_cases': ('traffic_cases_library', 'ALL'),
        'cmpd_types': ('cmpd_type_verify_manifest', []),
        'eco_manifest': {},
        'diag_tests': [('PortPtpIngTest', {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 500}),
                        ('PortPtpEgrTest', {'category': 1, 'areas': ['PCBP2', 'PCB2C'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 500}),
                       ]
    },

}  # family_end
