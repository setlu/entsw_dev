"""
PRODUCT DEFINITIONS for C3K Planck

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

__title__ = "C3K Planck Product Definitions"
__version__ = '0.1.3'
__family__ = "edison"
__consumer__ = 'c3850.Edison'


family = {
    'COMMON': {
        'product_family': "edison",

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
        'btldr': {'image': 'cat3k_caa_loader_dev.img.14Mar24.SSA',
                  'rev': {'ver': '1.1', 'date': 'Mar 11 2014'}},
        'linux': {'image': 'vmlinux2013Sep23.mzip.SSA',
                  'rev': ''},
        'diag': {'image': 'stardust_planckcr.2014Apr25',
                 'rev': ''},
        'fpga': {'image': '17-12265-V01_0A_relkey_hmac.hex',
                 'rev': '010a',
                 'name': 'morse'},
        # MCU images given by a subdir as the dict keys.
        'mcu': {'images': {'kirch83': ['app_data_kirchhoff.srec', 'app_flash_kirchhoff.bin', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                       'c_kirchhoff_swap_31.bin', 'coulomb_kirchhoff_31.bin']},
                'name': 'alchemy',
                'rev': {'ios': 'APPL 0.83 (0x53)  41 (0x29)  16 (0x10)', 'coulomb': ''}},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S3850UK9-37E',  # 'S3850UK9-166',
        'ios_supp_files': {8: [('S3850UK9-32-0SE', 'SR_pkgs'), ('S3850UK9-33SE', 'SR_pkgs')],
                           9: [('ACTUAL', 'recovery')]},

        # settings before IOS main image installation
        'ios_pre_install_params': {'ASIC_PCI_RESET': '1', 'EI_NOPROG': '1'},
        # IOS clean up items
        'ios_cleanup_items': ['obfl', 'crashinfo', 'startup-config'],
        # Rommon params to keep
        'rommon_params_to_keep': ['ASIC_PCI_RESET', 'BOOT_LOADER_UPGRADE_DISABLE' 'SWITCH_NUMBER', 'BOOT', 'BAUD',
                                  'CFG_MODEL_NUM', 'RECOVERY_BUNDLE', 'TERMLINES', 'SBC_CFG', 'MANUAL_BOOT'],
        # default license files/dirs
        'default_license_files': {1: ['tracelogs'],
                                  5: ['dyn_eval', 'eval', 'persist', 'pri', 'red', '*d_license*.*'],
                                  6: ['dyn_eval', 'eval', 'persist', 'pri', 'red', '*d_license*.*']},

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
        # 'asic': {'type_ids': ['0x390']},

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

        # Cpu tests
        'cpu': {'cmd': 'CvmTempRead'},

        # SerDesEye
        'serdeseye': {'interfaces': ['SIF', 'NIF']},

        # SBC params
        'sbc': {'enabled': True, 'temperature_reg': 'READ_TEMPERATURE_2'},

        # PSU
        'psu': {'slots': ['A', 'B']},

        # Configuration check
        'cnf_psu_keys': {'uut_type': ['PID'], 'sn': ['SN']},
        'cnf_pcamap_keys': {'uut_type': ['pid'], 'sn': ['sn']},

        # TST recording
        'pcamap_to_tst_keymap': {'pid': 'uut_type', 'vid': 'version_id', 'sn': 'serial_number', 'hwv': 'tan_hw_rev',
                                 'vpn': 'tan', 'eci': 'eci'},
        'psu_to_tst_keymap': {'PID': 'uut_type', 'SN': 'serial_number', 'TAN': 'tan', 'TAN Rev': 'tan_hw_rev',
                              'VID': 'version_id', 'CLEI': 'clei'},
        'pcamap_items_for_tst': ['1', '2'],

        # Led Test
        'led': {
            1: {'cmd': 'SetLed all %op%', 'op': ['Green', 'Amber', 'Off']},
            2: {'cmd': 'BeaconLed On', 'op': ['Bule']}
        },

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        'sysinit_required_to_pass': [('Doppler 0 PCIe link lane width is 4', 1)],

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

        # Voltage Margin Table for Level Check
        #  Format is {'<voltage rail name>': {...values...}, ...}
        #         or {'<voltage rail name>': {'bins': {<bin# 0-x>: {...values...}, ...}}, ...}
        #  Values: trim     = Trim voltage level from nominal.
        #          vnom     = Nominal Voltage rating.
        #          mhi, mlo = Margin Percentage for high and low independently.
        #          gb       = Guard Band Percentage (+/-).
        'vmargin_table': {
            '3.3V':                   {'trim': 0, 'vnom': 3.3,  'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '2.5V':                   {'trim': 0, 'vnom': 2.5,  'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.8V':                   {'trim': 0, 'vnom': 1.8,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.5V':                   {'trim': 0, 'vnom': 1.5,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.2V':                   {'trim': 0, 'vnom': 1.2,  'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.15V':                  {'trim': 0, 'vnom': 1.15, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.0V':                   {'trim': 0, 'vnom': 1.0,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '0.98V-DP0': {'bins': {0: {'trim': 0, 'vnom': 0.98, 'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
                                   1: {'trim': 0, 'vnom': 0.98, 'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025}}},
            '1.5V-DOP':  {'bins': {0: {'trim': 0, 'vnom': 1.5,  'mhi': 0.05, 'mlo': 0.05, 'gb': 0.030},
                                   1: {'trim': 0, 'vnom': 1.5,  'mhi': 0.05, 'mlo': 0.05, 'gb': 0.030}}},
        },

        # Temperature Table
        # Table MUST account for 1) Test Area, 2) Environmental temperature, and 3) Operational State of UUT.
        # Format is {'<index name>': {'<testarea>': {'<environ temp>': {'idle': xx, 'traf': xx, 'diag': xx, 'gb': xx}, ...}, ...}, ...}
        # 'idle' = State of UUT powered on but not doing much.
        # 'traf' = State of UUT running full bandwidth traffic
        # 'diag' = State of UUT running diagnostic tests (might have to average over serveral tests)
        # 'gb'   = Guard Band +/-% for pass or fail; 0.20 = +/-20% of the selected limit value above.
        'temperature_table': {
            'Exhaust':   {'PCB2C':  {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 35, 'gb': 0.35},
                                     'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.25},
                                     'COLD':    {'idle': 5,   'traf': 20, 'diag': 20, 'gb': 1.00}},
                          'PCBST':  {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.35}},
                          'PCBFT':  {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.35}},
                          'SYSBI':  {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.25}}},
            'Intake':    {'PCB2C':  {'AMBIENT': {'idle': 28,  'traf': 28, 'diag': 28, 'gb': 0.25},
                                     'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.25},
                                     'COLD':    {'idle': 2.5, 'traf': 10, 'diag': 10, 'gb': 1.00}},
                          'PCBST':  {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.25}},
                          'PCBFT':  {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.25}},
                          'SYSBI':  {'AMBIENT': {'idle': 32,  'traf': 32, 'diag': 32, 'gb': 0.25}}},
            'Doppler_0': {'PCB2C':  {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.30},
                                     'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.30},
                                     'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST':  {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT':  {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}},
                          'SYSBI':  {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'CPU':       {'PCB2C':  {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                     'HOT':     {'idle': 60,  'traf': 60, 'diag': 60, 'gb': 0.30},
                                     'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.0}},
                          'DBGSYS': {'AMBIENT': {'idle': 55,  'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'PCBST':  {'AMBIENT': {'idle': 55,  'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'PCBFT':  {'AMBIENT': {'idle': 55,  'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'SYSBI':  {'AMBIENT': {'idle': 55,  'traf': 60, 'diag': 60, 'gb': 0.30}}},
        },

        # Diag Tests within the Stardust testlist
        # For product-specific tests, place them in the product sections for appending.
        'diag_tests': [('SysMem',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SysRegs',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('RTCTest',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('UsbDet',          {'areas': ['PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       # ('UsbConsoleLB',    {'areas': ['PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopReg',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopMem',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPSRO',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopMBIST',        {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopLBIST',        {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopInterrupt',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopNifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopOffload',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('DopPtpFlexTimer', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('DopPtpIngTest',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('DopPtpEgrTest',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('SupFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SupJumboFrames',  {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortFrames',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('JumboFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('RcpFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DebugFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('DopEEE',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('MacSecBistTest',  {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('MACsecDiag',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('CoreSwitch',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('OOBM',            {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopSifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('InsideLoop',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('Cable',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PowerDown',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortIntrDiag',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('REProtocol',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('REI2C',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('AlchemySystem',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('AlchemyCommands', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('PsDet',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('StackPwrDet',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('StackPwrCtrl',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ],

        'traffic_cases_library': {
            '12': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-12': {'speed': '1000'}},
                    'uplink_ports': {'13-14': {'speed': '1000'}, '15-16': {'speed': '10G'}}
                },
                'TrafCase_EXT_1G_1518_a': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {
                        '1-12': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '13-14': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '15-16': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_1518_b': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {
                        '1-12': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '13-14': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '15-16': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['ALL'],
                    'downlink_ports': {
                        '1-12': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '13-14': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '15-16': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['ALL'],
                    'downlink_ports': {
                        '1-12': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '13-14': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '15-16': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },

            },

            '24': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-26': {'speed': '1000'}, '27-28': {'speed': '10G'}}
                },
                'TrafCase_EXT_1G_1518_a': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_1518_b': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['ALL'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_64': {
                    'enabled': True,
                    'areas': ['ALL'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },

            },

        },  # traffic_cases

        'cmpd_type_verify_manifest': {
            'S.All.1': {'areas': ['PCBST', 'PCB2C'],
                        'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                  'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                  'MODEL_NUM', 'MODEL_REVISION_NUM',
                                  'DDR_SPEED', 'TERMLINES'
                                  ],
                        },
            'S.All.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
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
            'S.All.3': {'areas': ['SYSFT'],
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
        },  # cmpd

    },

    'PLANCKCR12': {
        'cfg_pids': ['WS-C3850-12S-L', 'WS-C3850-12S-E', 'WS-C3850-12S-S'],
        'MODEL_NUM': 'WS-C3850-12S',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '800-41089-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15839-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '17-12196-05.SBC_cfg',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'asic': {'type_ids': ['0x390'], 'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '12'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['S.All.1', 'S.All.2', 'S.All.3']),
        'eco_manifest': {('73-15839-07B0', 'ALL'): ('EA526167', '73535', ['PCBST', 'PCB2C'], ''),
                         ('73-15839-07A0', 'ALL'): ('EA520237', '66900', ['PCBST', 'PCB2C'], ''),
                         ('73-15839-06A0', 'ALL'): ('E119776', '60739', ['PCBST', 'PCB2C'], ''),
                         ('73-15839-05A0', 'ALL'): ('E119229', '59242', ['PCBST', 'PCB2C'], ''),
                         ('73-15839-0407', 'ALL'): ('E030614', '56595', ['PCBST', 'PCB2C'], ''),
                         ('73-15839-0204', 'ALL'): ('E092313', '55094', ['PCBST', 'PCB2C'], ''),
                         ('800-41089-06F0', 'ALL'): ('EA556798', '92855', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06E0', 'ALL'): ('EA555228', '91795', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06D0', 'ALL'): ('EA550394', '86990', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06C0', 'ALL'): ('EA536283', '76905', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06B0', 'ALL'): ('EA534730', '75683', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06A0', 'ALL'): ('EA526167', '73537', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-05F0', 'ALL'): ('EA530824', '72994', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-05E0', 'ALL'): ('EA529465', '71358', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-05D0', 'ALL'): ('EA520237', '66904', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-05C0', 'ALL'): ('E119776', '60741', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-05A0', 'ALL'): ('E119229', '59244', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-0404', 'ALL'): ('E030614', '56597', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-0205', 'ALL'): ('E092313', '55114', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41089-06C0', 'FTX'): (None, '77089', ['SYSFT'], ''),
                         ('800-41089-06B0', 'FTX'): (None, '75893', ['SYSFT'], ''),
                         ('800-41089-06A0', 'FTX'): (None, '74153', ['SYSFT'], ''),
                         ('800-41089-05F0', 'FTX'): (None, '73359', ['SYSFT'], ''),
                         ('800-41089-05E0', 'FTX'): (None, '71642', ['SYSFT'], ''),
                         ('800-41089-05D0', 'FTX'): (None, '67068', ['SYSFT'], ''),
                         ('800-41089-05C0', 'FTX'): (None, '61148', ['SYSFT'], ''),
                         ('800-41089-05A0', 'FTX'): (None, '59411', ['SYSFT'], ''),
                         ('800-41089-0404', 'FTX'): (None, '59151', ['SYSFT'], ''),
                         }
    },

    'PLANCKCR24': {
        'cfg_pids': ['WS-C3850-24S-L', 'WS-C3850-24S-E', 'WS-C3850-24S-S'],
        'MODEL_NUM': 'WS-C3850-24S',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '800-41087-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-14445-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '17-12196-05.SBC_cfg',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'asic': {'type_ids': ['0x390'], 'core_count': 1, 'locations': ['U0']},
        'traffic_cases': ('traffic_cases_library', '24'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['S.All.1', 'S.All.2', 'S.All.3']),
        'eco_manifest': {('73-14445-07B0', 'ALL'): ('EA526167', '73539', ['PCBST', 'PCB2C'], ''),
                         ('73-14445-07A0', 'ALL'): ('EA520237', '66899', ['PCBST', 'PCB2C'], ''),
                         ('73-14445-06A0', 'ALL'): ('E119776', '60735', ['PCBST', 'PCB2C'], ''),
                         ('73-14445-05A0', 'ALL'): ('E119229', '59238', ['PCBST', 'PCB2C'], ''),
                         ('73-14445-0407', 'ALL'): ('E030614', '56599', ['PCBST', 'PCB2C'], ''),
                         ('73-14445-0204', 'ALL'): ('E092313', '55089', ['PCBST', 'PCB2C'], ''),
                         ('800-41087-07F0', 'ALL'): ('EA556798', '92858', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07E0', 'ALL'): ('EA555228', '91780', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07D0', 'ALL'): ('EA550394', '86992', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07C0', 'ALL'): ('EA536283', '76903', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07B0', 'ALL'): ('EA534730', '75685', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07A0', 'ALL'): ('EA526167', '73541', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-06C0', 'ALL'): ('EA530824', '72992', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-06B0', 'ALL'): ('EA529465', '71360', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-05E0', 'ALL'): ('EA520237', '66908', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-05C0', 'ALL'): ('E119776', '60737', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-05A0', 'ALL'): ('E119229', '59240', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-0404', 'ALL'): ('E030614', '56601', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-0205', 'ALL'): ('E092313', '55112', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41087-07C0', 'FTX'): (None, '77466', ['SYSFT'], ''),
                         ('800-41087-07B0', 'FTX'): (None, '75744', ['SYSFT'], ''),
                         # ('800-41087-07B0', 'FTX'): (None, '75743', ['SYSFT'], ''),
                         ('800-41087-06B0', 'FTX'): (None, '75741', ['SYSFT'], ''),
                         # ('800-41087-06B0', 'FTX'): (None, '73753', ['SYSFT'], ''),
                         # ('800-41087-06B0', 'FTX'): (None, '75132', ['SYSFT'], ''),
                         # ('800-41087-06B0', 'FTX'): (None, '75131', ['SYSFT'], ''),
                         ('800-41087-07A0', 'FTX'): (None, '74360', ['SYSFT'], ''),
                         # ('800-41087-07C0', 'FTX'): (None, '73747', ['SYSFT'], ''),
                         ('800-41087-06C0', 'FTX'): (None, '73725', ['SYSFT'], ''),
                         # ('800-41087-07B0', 'FTX'): (None, '73718', ['SYSFT'], ''),
                         # ('800-41087-07B0', 'FTX'): (None, '73441', ['SYSFT'], ''),
                         # ('800-41087-06C0', 'FTX'): (None, '73321', ['SYSFT'], ''),
                         # ('800-41087-06B0', 'FTX'): (None, '71950', ['SYSFT'], ''),
                         ('800-41087-05C0', 'FTX'): (None, '71917', ['SYSFT'], ''),
                         ('800-41087-0504', 'FTX'): (None, '62187', ['SYSFT'], ''),
                         # ('800-41087-05C0', 'FTX'): (None, '59412', ['SYSFT'], ''),
                         ('800-41087-05A0', 'FTX'): (None, '59284', ['SYSFT'], ''),
                         ('800-41087-0404', 'FTX'): (None, '59188', ['SYSFT'], ''),
                         },
    },

}  # family_end
