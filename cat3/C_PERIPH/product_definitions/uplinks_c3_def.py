"""
PRODUCT DEFINITIONS for C3000 Uplink Modules

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

__title__ = "C3000 Uplink Product Definitions"
__version__ = '2.0.0'
__family__ = 'uplinks_c3'

family = {
    'COMMON': {
        'product_family': 'uplinks_c3',

        # UUT Categories: 'SWITCH', 'PERIPH'
        'uut_category': 'PERIPH',

        # Test Area process flow (see PID specific sections)
        # 'process_flow': ['ASSY', 'SYSFT'],

        # Images needed to run the uplink Host
        'linux': {'image': 'vmlinux2015Apr22.mzip.SSA', 'rev': ''},
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

        # Device instance designation and diags params
        'pcamaps': {'1': {'cnt': '', 'pcapn': '', 'vid': '', 'bid': '', 'pid': '', 'eci': '', 'pcarev': '', 'clei': '', 'sn': '', 'hwv': '', 'vpn': ''}},

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
            'bateman': {
                'TrafCase_PHY_1000_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/28,28'],
                },
                'TrafCase_PHY_2500_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '2.5G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/28,28'],
                },
                'TrafCase_PHY_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/28,28'],
                },
                'TrafCase_PHY_AUTO_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': 'AUTO', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/28,28'],
                },
                'TrafCase_EXT_1000_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/27,28'],
                },
                'TrafCase_EXT_2500_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '2.5G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/27,28'],
                },
                'TrafCase_EXT_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/27,28'],
                },
                'TrafCase_EXT_AUTO_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25-28': {'speed': 'AUTO', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': ['confpairs 25,26/27,28'],
                },
            },
            'legendre': {
                'TrafCase_PHY_25G_AUTO': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25/29': {'duplex': 'AUTO', 'crossover': 'AUTO', 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '29/25': {'duplex': 'AUTO', 'crossover': 'AUTO', 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': ['set25Gport 25,29'], 'traf_cmds': ['confpairs 25,29/29,25'],
                },
                'TrafCase_EXT_25G_AUTO': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {},
                    'uplink_ports': {
                        '25/29': {'duplex': 'AUTO', 'crossover': 'AUTO', 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '29/25': {'duplex': 'AUTO', 'crossover': 'AUTO', 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': ['set25Gport 25,29'], 'traf_cmds': ['confpairs 25,29/29,25'],
                },
            },
        }
    },

    'HILBERT': {
        'PID': 'C3850-NM-HILBERT',
        'BID': 'F001',
        'VPN': '800-0000-01',
        'VID': 'P2',
        'SN': '',
        'PCAPN': '73-14102-02',
        'PCAREV': '',
        'CLEI': '',
        'ECI': '',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
    },

    'LAPLACE': {
        'PID': 'C3850-NM-4-1G',
        'BID': '000A',
        'VPN': '800-33472-01',
        'VID': '',
        'SN': '',
        'PCAPN': '73-12735-01',
        'PCAREV': '',
        'CLEI': '',
        'ECI': '',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
    },

    'FOURIER': {
        'PID': 'C3850-NM-2-1G',
        'BID': '0009',
        'VPN': '800-33471-01',
        'VID': '',
        'SN': '',
        'PCAPN': '73-12734-01',
        'PCAREV': '',
        'CLEI': '',
        'ECI': '',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
    },

    'LORENTZ': {
        'PID': 'C3850-NM-4-10G',
        'BID': '0008',
        'VPN': '800-33470-01',
        'VID': '',
        'SN': '',
        'PCAPN': '73-12732-01',
        'PCAREV': '',
        'CLEI': '',
        'ECI': '',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'QUACK2',
    },

    'FIBONACCI': {
        'PID': 'C3850-NM-2-40G',
        'BID': '002C',
        'VPN': '800-42460-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '73-16294-01',
        'PCAREV': 'A0',
        'CLEI': 'IPU3BAGCAA',
        'ECI': '191771',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
    },

    'SCHRODINGER': {
        'PID': 'C3850-NM-8-10G',
        'BID': '002D',
        'VPN': '800-42461-01',
        'VID': 'V01',
        'SN': '',
        'PCAPN': '73-16295-01',
        'PCAREV': 'A0',
        'CLEI': 'IPU3BAHCAA',
        'ECI': '191772',
        'HWV': '0',
        'CNT': '0',
        # Identity Protection types: QUACK2, ACT2
        'identity_protection_type': 'ACT2',
    },

}  # family_end
