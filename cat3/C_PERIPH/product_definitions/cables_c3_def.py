"""
PRODUCT DEFINITIONS for C3000 Stack Cables

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

__title__ = "C3000 Stack Cable Product Definitions"
__version__ = '2.0.0'
__family__ = 'cables_c3'

family = {
    'COMMON': {
        'product_family': 'cables_c3',

        # UUT Categories: 'SWITCH', 'PERIPH'
        'uut_category': 'PERIPH',

        # Test Area process flow (see PID specific sections)
        # 'process_flow': ['ASSY', 'SYSFT'],

        # Images needed to run the uplink Host
        'linux': {'image': 'vmlinux2015Apr22.mzip.SSA', 'rev': ''},  # 'vmlinux13Sep03.mzip.SSA'
        'diag': {'image': 'stardustThrArchimedes.2014Apr30', 'rev': ''},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S3850UK9-36E',
        'ios_pkg': '',

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'sda', 'secondary': None, 'tertiary': None},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader. Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mounts are placed first in the list.  Specified mounts should correspond to enumerated disks.
        # Format is a list of tuples: [(<device number>, <mount point>), ...]
        'device_mounts': {
            'primary': [(3, '/mnt'), (1, '/mnt/sd1'), (5, '/mnt/sd5'), (6, '/mnt/sd6'), (7, '/mnt/sd7'), (8, '/mnt/sd8'), (9, '/mnt/sd9')],
            'secondary': None, 'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {'primary': None, 'secondary': None, 'tertiary': None},

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],

        # SBC params
        'sbc': {'enabled': True, 'temperature_reg': 'READ_TEMPERATURE_2', 'op': False,
                'label': {'program_begin_label': 'EXEC_LABEL_Prog_1',
                          'sync_begin_label': '',
                          'verify_begin_label': 'EXEC_LABEL_Check_1'
                          }
                },

        # Led Test
        'led': {1: {'cmd': 'SetLed all %op%', 'op': ['Green', 'Amber', 'Off']}},

        # Chamber Corners (N-Corners)
        #  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
        #  The temp+voltage designations are 2+2letters:
        #    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
        'chamber_corners': [('LTHV', True), ('HTLV', True)],

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

    'CABLE-EDISON': {
        'PID': 'STACK-T1-50CM',
        'BID': '8001',
        'VPN': '800-40403-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '72-5125-01',
        'PCAREV': '01',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
        'pcamaps': {'2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '3': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},

    },

    'CABLE-EDISON-1': {
        'PID': 'STACK-T1-1M',
        'BID': '8002',
        'VPN': '800-40404-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '72-5126-01',
        'PCAREV': '01',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
        'pcamaps': {'2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '3': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},

    },

    'CABLE-EDISON-3': {
        'PID': 'STACK-T1-3M',
        'BID': '8003',
        'VPN': '800-40405-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '72-5123-01',
        'PCAREV': '01',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
        'pcamaps': {'2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '3': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},

    },

    'CABLE-ARCH': {
        'PID': 'STACK-T2-50CM',
        'BID': '800A',
        'VPN': '800-40805-03',
        'VID': 'V03',
        'SN': '',
        'PCAPN': '73-15203-03',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '06',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2'],
        'backflush_status': 'YES',
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},
    },

    'CABLE-ARCH-1': {
        'PID': 'STACK-T2-1M',
        'BID': '800B',
        'VPN': '800-40806-03',
        'VID': 'V03',
        'SN': '',
        'PCAPN': '73-15203-03',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '06',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2'],
        'backflush_status': 'YES',
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},
    },

    'CABLE-ARCH-3': {
        'PID': 'STACK-T2-3M',
        'BID': '800C',
        'VPN': '800-40807-03',
        'VID': 'V03',
        'SN': '',
        'PCAPN': '73-15203-03',
        'PCAREV': 'A0',
        'CLEI': '0',
        'ECI': '0',
        'HWV': '06',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
        'idpro_sequence': ['ACT2'],
        'backflush_status': 'YES',
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''},
                    '2': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},
    },

}  # family_end
