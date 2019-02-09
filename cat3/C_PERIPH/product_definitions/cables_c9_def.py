"""
PRODUCT DEFINITIONS for C9300 Stack Cables

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

__title__ = "C9300 Stack Cable Product Definitions"
__version__ = '2.0.0'
__family__ = 'cables_c9'

family = {
    'COMMON': {
        'product_family': 'cables_c9',

        # UUT Categories: 'SWITCH', 'PERIPH'
        'uut_category': 'PERIPH',

        # Test Area process flow (see PID specific sections)
        # 'process_flow': ['ASSY', 'SYSFT'],

        # Images needed to run the uplink Host
        'linux': {'image': 'bzImage.082918.SSA', 'rev': ''},
        'diag': {'image': 'stardust2018Sep25', 'rev': 'Sep 25'},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'STEST-C9300L',
        'ios_pkg': '',

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
            'secondary': None, 'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {'primary': None, 'secondary': None, 'tertiary': None},

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        'sysinit_required_to_pass': [('PCIE[0-4]: \(RC\) X[1-4] GEN-2 link UP', 1)],

        # Product Sequence Definition Settings
        # (Parameters that are passed to the sequence definition build-out.)
        'prod_seq_def': {
            'PCBST': {},
            'PCB2C': {},
            'ASSY': {},
            'PCBFT': {},
            'SYSBI': {},
        },
        # Traffic library, delete Mother Board ports
        'traffic_cases_library': {
        }
    },

    'CABLE-FRANK': {
        'PID': 'STACK-T3-50CM',
        'BID': '???',
        'VPN': '800-???-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '74-???-01',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Peripheral device map
        'device_map': {1: 'CABLE', 2: 'CABLE', 3: 'ADAPTER', 4: 'ADAPTER'},
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2-RSA', 'ACT2-HARSA'],
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},
    },

    'CABLE-FRANK-1': {
        'PID': 'STACK-T3-1M',
        'BID': '800A',
        'VPN': '800-105420-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '74-121486-01',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Peripheral device map
        'device_map': {1: 'CABLE', 2: 'CABLE', 3: 'ADAPTER', 4: 'ADAPTER'},
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2-RSA', 'ACT2-HARSA'],
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '',
                          'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '',
                          'sn': '', 'hwv': '', 'vpn': ''}},
    },

    'CABLE-FRANK-3': {
        'PID': 'STACK-T3-3M',
        'BID': '???',
        'VPN': '800-?????-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '74-????-01',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Peripheral device map
        'device_map': {1: 'CABLE', 2: 'CABLE', 3: 'ADAPTER', 4: 'ADAPTER'},
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2-RSA', 'ACT2-HARSA'],
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '',
                          'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '',
                          'sn': '', 'hwv': '', 'vpn': ''}},
    },

}  # family_end
