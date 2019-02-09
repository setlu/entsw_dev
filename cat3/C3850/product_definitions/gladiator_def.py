"""
PRODUCT DEFINITIONS for C3K Gladiator

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

__title__ = "C3K Gladiator Product Definitions"
__version__ = '0.1.4'
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
        'USB_SERIAL_NUM': '',
        'USB_ASSEMBLY_NUM': '',
        'USB_REVISION_NUM': '',
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '128',

        # Images
        'btldr': {'image': 'cat3k_caa_loader.img.15Mar31.SPA',
                  'rev': {'ver': '1.20', 'date': 'Mar 31 2015'}},
        'linux': {'image': 'vmlinux2015Apr22.mzip.SSA',
                  'rev': ''},
        'diag': {'image': 'stardustThrG.2016Jan14',
                 'rev': ''},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S3850UK9-37E',
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

        # Identity Protection types: QUACK2, ACT2, ACT2-ECC
        'identity_protection_type': 'ACT2',
        # Sequence to program all IdPro, valid types: QUACK, ACT, X509-n (n=1 to total_hashes)
        'idpro_sequence': ['X509-1', 'ACT', 'X509-2'],
        # Access Point SUDI params
        'x509_sudi_hash': ['SHA1', 'SHA256'],
        'x509_sudi_request_type': 'PROD',
        'x509_sudi_cert_method': 'KEY',
        'hidden_device': '/dev/sda5',

        # ASIC
        # 'asic': {'type_ids': ['0x03ce']},

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'sda', 'secondary': 'sdb', 'tertiary': None, 'dynamic': True},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader.
        # Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mount is placed first in the list.  Specified mounts will correspond to enumerated disks (i.e. primary, etc.)
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

        # obfl logging items
        'obfl_items': ['xml', 'persistent url flash:', 'persistent url crashinfo:'],

        # Psuedo-SLC mode (Linux macros required - one-shot)
        'set_pSLC_mode': None,  # 'set_emmc_pslc_bash.sh',

        # RTC tests
        'rtc': {'time_zone': 'GMT'},

        # StackRac tests
        # 'stackrac': {'datastack': 0},  # See individual PRODUCTS

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

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        # 'sysinit_required_to_pass': [('Doppler [0-7] PCIe link lane width is 4', 8)],
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

        # Voltage Margin Table for Level Check
        #  Format is {'<voltage rail name>': {...values...}, ...}
        #         or {'<voltage rail name>': {'bins': {<bin# 0-x>: {...values...}, ...}}, ...}
        #  Values: trim     = Trim voltage level from nominal.
        #          vnom     = Nominal Voltage rating.
        #          mhi, mlo = Margin Percentage for high and low independently.
        #          gb       = Guard Band Percentage (+/-).
        'vmargin_table': {
            '3.3V':                   {'trim': 0, 'vnom': 3.3,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '2.5V':                   {'trim': 0, 'vnom': 2.5,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.8V':                   {'trim': 0, 'vnom': 1.8,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.5V':                   {'trim': 0, 'vnom': 1.5,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.2V-LDO':               {'trim': 0, 'vnom': 1.2,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.15V':                  {'trim': 0, 'vnom': 1.15,  'mhi': 0.02, 'mlo': 0.02, 'gb': 0.040},  # need to confirm 4%gb
            '1.0V':                   {'trim': 0, 'vnom': 1.0,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            'DP-vdd_1.085V':          {'trim': 0, 'vnom': 1.085, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'DP0-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'DP2-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'DP4-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'DP6-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'DP-ser_1.0V':            {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'DP0-ser_1.0V':           {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'DP2-ser_1.0V':           {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'DP-pll_1.8V':            {'trim': 0, 'vnom': 1.8,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            # '0.98V-DP0': {'bins': {0: {'trim': 0, 'vnom': 0.98, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.015},
            #                        1: {'trim': 0, 'vnom': 0.98, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.015}}},
            # '1.5V-DOP':  {'bins': {0: {'trim': 0, 'vnom': 1.5,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.015},
            #                        1: {'trim': 0, 'vnom': 1.5,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.015}}},
        },

        # Temperature Table
        # Table MUST account for 1) Test Area, 2) Environmental temperature, and 3) Operational State of UUT.
        # Format is {'<index name>': {'<testarea>': {'<environ temp>': {'idle': xx, 'traf': xx, 'diag': xx, 'gb': xx}, ...}, ...}, ...}
        # 'idle' = State of UUT powered on but not doing much.
        # 'traf' = State of UUT running full bandwidth traffic
        # 'diag' = State of UUT running diagnostic tests (might have to average over serveral tests)
        # 'gb'   = Guard Band +/-% for pass or fail; 0.20 = +/-20% of the selected limit value above.
        'temperature_table': {
            'Exhaust':   {'PCB2C': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 35, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 5,   'traf': 20, 'diag': 20, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}}},
            'Intake':    {'PCB2C': {'AMBIENT': {'idle': 28,  'traf': 28, 'diag': 28, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 2.5, 'traf': 10, 'diag': 10, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 32,  'traf': 32, 'diag': 32, 'gb': 0.30}}},
            'Doppler_0': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_1': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
        },

        # Diag Tests within the Stardust testlist
        # For product-specific tests, place them in the product sections for appending.
        'diag_tests': [('SysMem',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SysRegs',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('RTCTest',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('UsbDet',          {'areas': ['PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       # ('UsbConsoleLB',    {'areas': ['PCB2C'], 'enabled': False, 'adt_enabled': True, 'args': '', 'timeout': 200}),
                       ('DopRegs',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopMem',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPSRO',         {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopMBIST',        {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('DopLBIST',        {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopInterrupt',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopNifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopOffload',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpFlexTimer', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpIngTest',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpEgrTest',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SupFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SupJumboFrames',  {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortFrames',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('JumboFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('RcpFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('DebugFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('DopEEE',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopMACsecDiag',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopFssDiag',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('CoreSwitch',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('OOBM',            {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopSifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('InsideLoop',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('Cable',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('PowerDown',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('PortIntrDiag',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('PortCableDiag',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('REProtocol',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('REI2C',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('AlchemySystem',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('AlchemyCommands', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('PsDet',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('StackPwrDet',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       # ('StackPwrCtrl',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ],

        'traffic_cases_library': {
            '12': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-12': {'speed': '10G'}},
                    'uplink_ports': {'13-14': {'speed': '10G'}, '15-16': {'speed': '10G'}}
                },
                'TrafCase_EXT_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-12': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'13-14': {'speed': '10G'}, '15-16': {'speed': '10G'}},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-12': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'13-14': {'speed': '10G'}, '15-16': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-12': {'speed': '10G', 'size': 64, 'stress': True}},
                    'uplink_ports': {'13-14': {'speed': '10G'}, '15-16': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },

            },
            '24': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '10G'}},
                    'uplink_ports': {'25-26': {'speed': '10G'}, '27-28': {'speed': '10G'}}
                },
                'TrafCase_EXT_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-24': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'25-26': {'speed': '10G'}, '27-28': {'speed': '10G'}},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-24': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'25-26': {'speed': '10G'}, '27-28': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-24': {'speed': '10G', 'size': 64, 'stress': True}},
                    'uplink_ports': {'25-26': {'speed': '10G'}, '27-28': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },

            },
            '48': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '10G'}},
                    'uplink_ports': {'49-50': {'speed': '10G'}, '51-52': {'speed': '10G'}}
                },
                'TrafCase_EXT_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {'1-48': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'49-50': {'speed': '10G'}, '51-52': {'speed': '10G'}},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-48': {'speed': '10G', 'size': 1518, 'stress': True}},
                    'uplink_ports': {'49-50': {'speed': '10G'}, '51-52': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },
                'TrafCase_PHY_10G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCBFT', 'SYSBI'],
                    'downlink_ports': {'1-48': {'speed': '10G', 'size': 64, 'stress': True}},
                    'uplink_ports': {'49-50': {'speed': '10G'}, '51-52': {'speed': '10G'}},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'runtime': 120,
                },

            },

        },  # end of traffic_cases_library

        'cmpd_type_verify_manifest': {
            'S.All.1': {'areas': ['PCBST', 'PCB2C'],
                        'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                  'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                  'MODEL_NUM', 'MODEL_REVISION_NUM',
                                  'DDR_SPEED', 'TERMLINES'
                                  ],
                        },
            'S.12-24.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
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
            'S.48.2': {'areas': ['ASSY', 'SYSBI', 'PCBFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },
            'S.12-24.3': {'areas': ['SYSFT'],
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
            'S.48.3': {'areas': ['SYSFT'],
                       'types': ['MAC_ADDR',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'SYSTEM_SERIAL_NUM', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',
                                 'VERSION_ID',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 ],
                       },

        },  # cmpd

    },

    'GLADIATOR12': {
        'cfg_pids': ['WS-C3850-12XS-E', 'WS-C3850-12XS-S', 'WS-C3850-16XS-E', 'WS-C3850-16XS-S'],
        # MCU images given by a subdir as the dict key.
        'mcu': {'images': {'kirch90': ['app_data.srec_V90', 'app_flash.bin_V90', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                       'c_kirchhoff_swap_33.bin', 'coulomb_kirchhoff_33.bin']},
                'name': 'alchemy',
                'rev': {'ios': 'APPL 0.111 (0x6f)    41 (0x29)    16 (0x10)', 'coulomb': ''}},
        'MODEL_NUM': 'WS-C3850-12XS',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-5292-02',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-16285-05',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'STKPWR_SERIAL_NUM': '',
        'STKPWR_ASSEMBLY_NUM': '',
        'STKPWR_REVISION_NUM': '',
        'VERSION_ID': 'V02',
        'SBC_CFG':   '17-G12CSR-09.SBC_cfg',
        'CLEI_CODE_NUMBER': 'IPMDJ00BRA',
        'ECI_CODE_NUMBER': '467456',
        'fpga': {'image': 'morseG_01_00_A0.hex',
                 'rev': '0100',
                 'name': 'morse'},
        'stackrac': {'datastack': 1},
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'type_ids': ['0x03ce'], 'core_count': 2, 'locations': ['U98']},
        'fan': {
            'status_value': '0x0000002A',
            'regs': {'fan1': '0x3C', 'fan2': '0x44', 'fan3': '0x4C', 'fan4': '0x54'},
            'speed_settings': {'LOW': '0x0A', 'HIGH': '0xFF', 'NOMINAL': '0x7B'},
        },
        # 'diag_tests': [
        #     ('StackPwrDet', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
        #     ('StackPwrCtrl', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
        # ],
        'traffic_cases': ('traffic_cases_library', '12'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['S.All.1', 'S.12-24.2', 'S.12-24.3']),
        'eco_manifest': {('73-16285-0405', 'ALL'): ('E032015', '58990', ['PCBST', 'PCB2C'], 'PP'),
                         ('73-16285-06B0', 'ALL'): ('EA554154', '90629', ['PCBST', 'PCB2C'], ''),
                         ('73-16285-06A0', 'ALL'): ('EA533641', '74285', ['PCBST', 'PCB2C'], ''),
                         ('73-16285-05A0', 'ALL'): ('EA530147', '73032', ['PCBST', 'PCB2C'], ''),
                         # ('73-16285-05A0', 'ALL'): ('E050615', '70794', ['PCBST', 'PCB2C'], ''),
                         ('68-5292-02H0', 'ALL'): ('EA556798', '92849', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02G0', 'ALL'): ('EA555228', '91534', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02F0', 'ALL'): ('EA554154', '90638', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02E0', 'ALL'): ('EA550394', '86984', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02D0', 'ALL'): ('EA535992', '76907', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02C0', 'ALL'): ('EA536283', '76830', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02B0', 'ALL'): ('EA534730', '75689', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-02A0', 'ALL'): ('EA533641', '74287', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-01D0', 'ALL'): ('EA530824', '73145', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-01C0', 'ALL'): ('EA530147', '73064', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-01A0', 'ALL'): ('E050615', '70796', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-0153', 'ALL'): ('E032015', '59000', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5292-01A0', 'FTX'): (None, '77251', ['SYSFT'], ''),
                         ('68-5292-02D0', 'FTX'): (None, '77254', ['SYSFT'], ''),
                         ('68-5292-01D0', 'FTX'): (None, '77253', ['SYSFT'], ''),
                         ('68-5292-02H0', 'FTX'): (None, '93444', ['SYSFT'], ''),
                         },
    },

    'GLADIATOR24': {
        'cfg_pids': ['WS-C3850-24XS-E', 'WS-C3850-24XS-S', 'WS-C3850-32XS-E', 'WS-C3850-32XS-S'],
        # MCU images given by a subdir as the dict key.
        'mcu': {'images': {'kirch90': ['app_data.srec_V90', 'app_flash.bin_V90', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                       'c_kirchhoff_swap_33.bin', 'coulomb_kirchhoff_33.bin']},
                'name': 'alchemy',
                'rev': {'ios': '', 'coulomb': ''}},
        'MODEL_NUM': 'WS-C3850-24XS',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-5294-02',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-16649-05',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'STKPWR_SERIAL_NUM': '',
        'STKPWR_ASSEMBLY_NUM': '',
        'STKPWR_REVISION_NUM': '',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '17-G24CSR-17.SBC_cfg',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'fpga': {'image': 'morseG_01_00_A0.hex',
                 'rev': '0100',
                 'name': 'morse'},
        'stackrac': {'datastack': 1},
        'sysinit_required_to_pass': [('Doppler [0-3] PCIe link lane width is 4', 4)],
        'asic': {'type_ids': ['0x03ce'], 'core_count': 4, 'locations': ['U98', 'U6']},
        'temperature_table': {
            'Exhaust':   {'PCB2C': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 35, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 5,   'traf': 20, 'diag': 20, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}}},
            'Intake':    {'PCB2C': {'AMBIENT': {'idle': 28,  'traf': 28, 'diag': 28, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 2.5, 'traf': 10, 'diag': 10, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 32,  'traf': 32, 'diag': 32, 'gb': 0.30}}},
            'Doppler_0': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_1': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_2': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_3': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
        },
        'fan': {
            'status_value': '0x0000002A',
            'regs': {'fan1': '0x3C', 'fan2': '0x44', 'fan3': '0x4C', 'fan4': '0x54'},
            'speed_settings': {'LOW': '0x0A', 'HIGH': '0xFF', 'NOMINAL': '0x7B'},
        },
        # 'diag_tests': [
        #     ('StackPwrDet', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
        #     ('StackPwrCtrl', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 200}),
        # ],
        'traffic_cases': ('traffic_cases_library', '24'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['S.All.1', 'S.12-24.2', 'S.12-24.3']),
        'eco_manifest': {('73-16649-06B0', 'ALL'): ('EA554154', '90631', ['PCBST', 'PCB2C'], ''),
                         ('73-16649-06A0', 'ALL'): ('EA532102', '74283', ['PCBST', 'PCB2C'], ''),
                         ('73-16649-05A0', 'ALL'): ('EA530589', '73034', ['PCBST', 'PCB2C'], ''),
                         ('73-16649-0603', 'ALL'): ('E071515', '72205', ['PCBST', 'PCB2C'], ''),
                         # ('73-16649-05A0', 'ALL'): ('E050615', '70798', ['PCBST', 'PCB2C'], ''),
                         ('73-16649-0406', 'ALL'): ('E032015', '59391', ['PCBST', 'PCB2C'], ''),
                         ('68-5294-02H0', 'ALL'): ('EA556798', '92851', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02G0', 'ALL'): ('EA555228', '91536', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02F0', 'ALL'): ('EA554154', '90640', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02E0', 'ALL'): ('EA550394', '86982', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02D0', 'ALL'): ('EA535992', '76909', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02C0', 'ALL'): ('EA536283', '76832', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02B0', 'ALL'): ('EA534730', '75687', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-02A0', 'ALL'): ('EA532102', '74280', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-01C0', 'ALL'): ('EA530824', '73147', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-01B0', 'ALL'): ('EA530589', '73066', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-0202', 'ALL'): ('E071515', '72209', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-01A0', 'ALL'): ('E050615', '70800', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-0162', 'ALL'): ('E032015', '59393', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5294-01A0', 'FTX'): (None, '71274', ['SYSFT'], ''),
                         ('68-5294-02A0', 'FTX'): (None, '77141', ['SYSFT'], ''),
                         ('68-5294-01D0', 'FTX'): (None, '77140', ['SYSFT'], ''),
                         # ('68-5294-01A0', 'FTX'): (None, '71297', ['SYSFT'], ''),
                         ('68-5294-02D0', 'FTX'): (None, '77144', ['SYSFT'], ''),
                         ('68-5294-01C0', 'FTX'): (None, '73824', ['SYSFT'], ''),
                         },
    },

    'GLADIATOR48': {
        'cfg_pids': ['WS-C3850-48XS-F-E', 'WS-C3850-48XS-F-S', 'WS-C3850-48XS-B-E', 'WS-C3850-48XS-B-S'],
        'MODEL_NUM': 'WS-C3850-48XS',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-5295-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-16622-04',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '17-G48CSR-04.SBC_cfg',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'fpga': {'image': 'proximo_03_04_A0.hex',
                 'rev': '0304',
                 'name': 'proximo'},
        'stackrac': {'datastack': 0},
        'sysinit_required_to_pass': [('Doppler [0-7] PCIe link lane width is 4', 8)],
        'asic': {'type_ids': ['0x03ce'], 'core_count': 8, 'locations': ['U62', 'U78', 'U76', 'U67']},
        'temperature_table': {
            'Exhaust':   {'PCB2C': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 35, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 5,   'traf': 20, 'diag': 20, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.30}}},
            'Intake':    {'PCB2C': {'AMBIENT': {'idle': 28,  'traf': 28, 'diag': 28, 'gb': 0.30},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.30},
                                    'COLD':    {'idle': 2.5, 'traf': 10, 'diag': 10, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'PCBFT': {'AMBIENT': {'idle': 32,  'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'SYSBI': {'AMBIENT': {'idle': 32,  'traf': 32, 'diag': 32, 'gb': 0.30}}},
            'Doppler_0': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_1': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_2': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_3': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_4': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_5': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_6': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
            'Doppler_7': {'PCB2C': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35},
                                    'HOT':     {'idle': 70,  'traf': 80, 'diag': 80, 'gb': 0.35},
                                    'COLD':    {'idle': 10,  'traf': 30, 'diag': 30, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 50,  'traf': 50, 'diag': 50, 'gb': 0.35, 'delta': 35}}},
        },
        'traffic_cases': ('traffic_cases_library', '48'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['S.All.1', 'S.48.2', 'S.48.3']),
        'eco_manifest': {('73-16622-05B0', 'ALL'): ('EA554154', '90633', ['PCBST', 'PCB2C'], ''),
                         ('73-16622-05A0', 'ALL'): ('EA533641', '74291', ['PCBST', 'PCB2C'], ''),
                         ('73-16622-04A0', 'ALL'): ('EA528584', '60659', ['PCBST', 'PCB2C'], ''),
                         ('68-5295-02G0', 'ALL'): ('EA556798', '92853', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02F0', 'ALL'): ('EA555228', '90642', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02E0', 'ALL'): ('EA554154', '91594', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02D0', 'ALL'): ('EA550394', '86980', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02C0', 'ALL'): ('EA535992', '76911', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02B0', 'ALL'): ('EA533168', '75818', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-01C0', 'ALL'): ('EA530824', '74309', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02A0', 'ALL'): ('EA533641', '74289', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-01A0', 'ALL'): ('EA528584', '60989', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('68-5295-02C0', 'FTX'): (None, '78465', ['SYSFT'], ''),
                         ('68-5295-01A0', 'FTX'): (None, '77278', ['SYSFT'], ''),
                         ('68-5295-01C0', 'FTX'): (None, '77277', ['SYSFT'], ''),
                         ('68-5295-02B0', 'FTX'): (None, '77276', ['SYSFT'], ''),
                         },
    },

}  # family_end
