"""
PRODUCT DEFINITIONS for C3K Orsted

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

__title__ = "C3K Orsted Product Definitions"
__version__ = '0.2.1'
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
        'btldr': {'image': 'cat3k_caa_loader_dev.img.15Jan29.SSA',
                  'rev': {'ver': '', 'date': ''}},
        'linux': {'image': 'vmlinux2015Apr22.mzip.SSA',
                  'rev': ''},
        'diag': {'image': 'stardustOrstedThr_Csr21_062116',  # 'stardustThrCSR.2015Sep11',
                 'rev': ''},
        'fpga': {'image': 'BellOr_03_00_20150112_pp_relkey_hmac.hex',
                 'rev': '0300',
                 'name': 'bell'},
        # MCU images given by a subdir as the dict keys.
        'mcu': {'images': {'kirch90': ['app_data.srec_V90', 'app_flash.bin_V90', 'kirchhoff_swap.bin', 'Cisco_loader.srec',
                                       'c_kirchhoff_swap_33.bin', 'coulomb_kirchhoff_33.bin']},
                'name': 'alchemy',
                'rev': {'ios': '', 'coulomb': ''}},
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
        # 'asic': {'type_ids': ['0x3ce']},

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
            '2.1V':                   {'trim': 0, 'vnom': 2.1,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.8V':                   {'trim': 0, 'vnom': 1.8,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.5V':                   {'trim': 0, 'vnom': 1.5,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '1.2V':                   {'trim': 0, 'vnom': 1.2,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.15V':                  {'trim': 0, 'vnom': 1.15,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.0V-LDO':               {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '1.2V-LDO':               {'trim': 0, 'vnom': 1.2,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            '0.9V':                   {'trim': 0, 'vnom': 0.9,   'mhi': 0.04, 'mlo': 0.04, 'gb': 0.025},
            '0.85V':                  {'trim': 0, 'vnom': 0.85,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '0.85V-MPHYR':            {'trim': 0, 'vnom': 0.85,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            '2.5V-MPHYR':             {'trim': 0, 'vnom': 2.5,   'mhi': 0.05, 'mlo': 0.05, 'gb': 0.025},
            'DP0-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'DP2-vdd_1.085V':         {'trim': 0, 'vnom': 1.085, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'DP-ser_1.0V':            {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
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
            'Exhaust':   {'PCB2C': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 35, 'gb': 0.35},
                                    'HOT':     {'idle': 60,  'traf': 65, 'diag': 65, 'gb': 0.35},
                                    'COLD':    {'idle': 5,   'traf': 20, 'diag': 20, 'gb': 1.00}},
                          'PCBST': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.35}},
                          'PCBFT': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.35}},
                          'SYSBI': {'AMBIENT': {'idle': 36,  'traf': 40, 'diag': 40, 'gb': 0.35}}},
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
                       # ('DopLBIST',        {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopInterrupt',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopNifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopOffload',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpFlexTimer', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpIng',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopPtpEgr',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SupFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('SupJumboFrames',  {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortFrames',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('JumboFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('RcpFrames',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DebugFrames',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopEEE',          {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopMACsecDiag',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopFssDiag',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('CoreSwitch',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('OOBM',            {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopSifCiscoPRBS', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('InsideLoop',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('Cable',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PowerDown',       {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortIntrDiag',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       # ('PortCableDiag',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('REProtocol',      {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('REI2C',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('AlchemySystem',   {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('AlchemyCommands', {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PsDet',           {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('StackPwrDet',     {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('StackPwrCtrl',    {'areas': ['PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PoeDetTest_CSCO', {'cmd': 'PoeDetTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test', 'func_args': {'detecttype': [1], 'mdimode': [0, 1]}}),
                       ('PoeDetTest_IEEE', {'cmd': 'PoeDetTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_detect_test', 'func_args': {'detecttype': [2], 'mdimode': [1]}}),
                       ('PoeClassTest_0',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [0]}}),
                       ('PoeClassTest_1',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [1]}}),
                       ('PoeClassTest_2',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [2]}}),
                       ('PoeClassTest_3',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [3]}}),
                       ('PoeClassTest_4',  {'cmd': 'PoeClassTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_class_test', 'func_args': {'poe_classes': [4]}}),
                       ('PoePowerTest',    {'cmd': 'PoePowerTest', 'areas': ['PCBST'], 'enabled': True, 'adt_enabled': True, 'args': '', 'func': 'diags_poe_power_test'}),
                       ],

        'traffic_cases_library': {
            '24': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-26': {'speed': '1000'}, '27-28': {'speed': '10G'}}
                },
                'TrafCase_NIF_2': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-26': {'speed': '10G'}, '27-28': {'speed': '1000'}}
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
                    'areas': ['DBGSYS', 'PCBST'],
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
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
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
                'TrafCase_PHY_2G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '2500', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_5G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '5G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_10G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '25-26': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '27-28': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },
            '48': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-50,53-54': {'speed': '1000'}, '51-52,55-56': {'speed': '10G'}}
                },
                'TrafCase_NIF_2': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-50,53-54': {'speed': '10G'}, '51-52,55-56': {'speed': '1000'}}
                },
                'TrafCase_EXT_1G_1518_a': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST', 'ASSY'],
                    'downlink_ports': {
                        '1-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_1G_1518_b': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'poe_enabled': True,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1G_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_2G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-12': {'speed': '2500', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                        '13-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_5G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-12': {'speed': '5G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                        '13-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_10G_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-12': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                        '13-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'macsec'},
                    },
                    'uplink_ports': {
                        '49-50,53-54': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                        '51-52,55-56': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                        'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },
        },  # traffic_cases

        'cmpd_type_verify_manifest': {
            'P.24.1': {'areas': ['PCBST', 'PCB2C'],
                       'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 # 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
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
                       'types': ['BAUD', 'MAC_ADDR', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'TERMLINES',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER',  'SYSTEM_SERIAL_NUM',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 'VERSION_ID', 'CFG_MODEL_NUM'
                                 'MANUAL_BOOT', 'BOOT', 'RECOVERY_BUNDLE'
                                 ],
                       },
            'P.48.1': {'areas': ['PCBST', 'PCB2C'],
                       'types': ['MAC_ADDR', 'MANUAL_BOOT',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 # 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 # 'POE2_ASSEMBLY_NUM', 'POE2_REVISION_NUM', 'POE2_SERIAL_NUM',
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
                       'types': ['BAUD', 'MAC_ADDR', 'MODEL_NUM', 'MODEL_REVISION_NUM',
                                 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM', 'MOTHERBOARD_SERIAL_NUM',
                                 'POE1_ASSEMBLY_NUM', 'POE1_REVISION_NUM', 'POE1_SERIAL_NUM',
                                 'POE2_ASSEMBLY_NUM', 'POE2_REVISION_NUM', 'POE2_SERIAL_NUM',
                                 'TERMLINES',
                                 'STKPWR_ASSEMBLY_NUM', 'STKPWR_REVISION_NUM', 'STKPWR_SERIAL_NUM',
                                 'USB_ASSEMBLY_NUM', 'USB_REVISION_NUM', 'USB_SERIAL_NUM',
                                 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SYSTEM_SERIAL_NUM',
                                 'CLEI_CODE_NUMBER', 'ECI_CODE_NUMBER',
                                 'VERSION_ID', 'CFG_MODEL_NUM'
                                 'MANUAL_BOOT', 'BOOT', 'RECOVERY_BUNDLE'
                                 ],
                       },
        },  # cmpd

    },

    'ORSTED24': {
        'cfg_pids': ['WS-C3850-24XU-L', 'WS-C3850-24XU-E', 'WS-C3850-24XU-S'],
        'MODEL_NUM': 'WS-C3850-24XU',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '800-41072-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15756-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-16439-01',
        'POE1_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   'OrstedCSR_24U_P3B_SBC_Config_03_09_15.txt',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-1] PCIe link lane width is 4', 2)],
        'asic': {'type_ids': ['0x3ce'], 'core_count': 4, 'locations': ['U6', 'U98']},
        'poe': {'uut_ports': '1-24', 'type': 'UPOE', 'volt_range': (47.0, 56.0), 'current_range': (1008, 1232)},
        'traffic_cases': ('traffic_cases_library', '24'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.24.1', 'P.24.2', 'P.24.3']),
        'eco_manifest': {('73-15756-06B0', 'ALL'): ('EA554154', '90635', ['PCBST', 'PCB2C'], ''),
                         ('73-15756-0703', 'ALL'): ('CA580938', '87067', ['PCBST', 'PCB2C'], ''),
                         ('73-15756-06A0', 'ALL'): ('EA538051', '77129', ['PCBST', 'PCB2C'], ''),
                         ('73-15756-05B0', 'ALL'): ('EA536747', '76898', ['PCBST', 'PCB2C'], ''),
                         ('73-15756-05A0', 'ALL'): ('EA529893', '71159', ['PCBST', 'PCB2C'], ''),
                         ('73-15756-0402', 'ALL'): ('E052015', '59728', ['PCBST', 'PCB2C'], ''),
                         ('800-41072-03F0', 'ALL'): ('EA555228', '91793', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-03E0', 'ALL'): ('EA554154', '90644', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-0403', 'ALL'): ('CA580938', '87069', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-03D0', 'ALL'): ('EA550394', '86988', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-03B0', 'ALL'): ('EA543491', '80554', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-02D0', 'ALL'): ('EA536747', '77508', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-03A0', 'ALL'): ('EA538051', '77132', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-02C0', 'ALL'): ('EA536283', '76901', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-02B0', 'ALL'): ('EA534681', '75679', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-02A0', 'ALL'): ('EA531644', '74278', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-01B0', 'ALL'): ('EA530824', '73143', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-01A0', 'ALL'): ('EA529893', '71162', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-0163', 'ALL'): ('E052015', '59730', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         # ('800-41072-02D0', 'ALL'): (None, '77413', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41072-03B0', 'FTX'): (None, '81669', ['SYSFT'], ''),
                         ('800-41072-03A0', 'FTX'): (None, '80791', ['SYSFT'], ''),
                         # ('800-41072-03A0', 'FTX'): (None, '80101', ['SYSFT'], ''),
                         ('800-41072-02D0', 'FTX'): (None, '77511', ['SYSFT'], ''),
                         ('800-41072-01B0', 'FTX'): (None, '74180', ['SYSFT'], ''),
                         ('800-41072-01A0', 'FTX'): (None, '72839', ['SYSFT'], ''),
                         ('800-41072-02A0', 'FTX'): (None, '75223', ['SYSFT'], ''),
                         ('800-41072-02B0', 'FTX'): (None, '77279', ['SYSFT'], ''),
                         },
    },

    'ORSTED48': {
        'cfg_pids': ['WS-C3850-12X48U-L', 'WS-C3850-12X48U-E', 'WS-C3850-12X48U-S'],
        'MODEL_NUM': 'WS-C3850-12X48U',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '800-41071-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-15755-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'POE1_SERIAL_NUM': '',
        'POE1_ASSEMBLY_NUM': '73-16439-01',
        'POE1_REVISION_NUM': 'A0',
        'POE2_SERIAL_NUM': '',
        'POE2_ASSEMBLY_NUM': '73-16439-01',
        'POE2_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   'OrstedCSR_48U_SBC_Config_4_9_15.txt',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'sysinit_required_to_pass': [('Doppler [0-3] PCIe link lane width is 4', 4)],
        'asic': {'type_ids': ['0x3ce'], 'core_count': 4, 'locations': ['U6', 'U98']},
        'poe': {'uut_ports': '1-48', 'type': 'UPOE', 'volt_range': (47.0, 56.0), 'current_range': (1008, 1232)},
        'traffic_cases': ('traffic_cases_library', '48'),
        'cmpd_types': ('cmpd_type_verify_manifest', ['P.48.1', 'P.48.2', 'P.48.3']),
        'eco_manifest': {('73-15755-08B0', 'ALL'): ('EA554154', '91822', ['PCBST', 'PCB2C'], ''),
                         ('73-15755-08A0', 'ALL'): ('EA538051', '77124', ['PCBST', 'PCB2C'], ''),
                         ('73-15755-07B0', 'ALL'): ('EA536747', '76895', ['PCBST', 'PCB2C'], ''),
                         ('73-15755-07A0', 'ALL'): ('EA529474', '71475', ['PCBST', 'PCB2C'], ''),
                         # ('73-15755-07A0', 'ALL'): ('EA527599', '59339', ['PCBST', 'PCB2C'], ''),
                         ('73-15755-0603', 'ALL'): ('E012615', '69498', ['PCBST', 'PCB2C'], ''),
                         ('800-41071-02F0', 'ALL'): ('EA555228', '91784', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-02E0', 'ALL'): ('EA554154', '90646', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-02D0', 'ALL'): ('EA550394', '86986', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-02B0', 'ALL'): ('EA543491', '80556', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01H0', 'ALL'): ('EA536747', '78079', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-02A0', 'ALL'): ('EA538051', '77126', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01G0', 'ALL'): ('EA536283', '76897', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01F0', 'ALL'): ('EA534681', '75681', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01E0', 'ALL'): ('EA530824', '73141', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01D0', 'ALL'): ('EA530740', '72133', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01C0', 'ALL'): ('EA530419', '72132', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01B0', 'ALL'): ('EA529474', '71478', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-01A0', 'ALL'): ('EA527599', '59342', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-0173', 'ALL'): ('E012615', '69980', ['ASSY', 'SYSBI', 'PCBFT', 'SYSFT'], ''),
                         ('800-41071-02F0', 'FTX'): (None, '92322', ['SYSFT'], ''),
                         ('800-41071-02B0', 'FTX'): (None, '82624', ['SYSFT'], ''),
                         ('800-41071-01H0', 'FTX'): (None, '82623', ['SYSFT'], ''),
                         # ('800-41071-02B0', 'FTX'): (None, '81679', ['SYSFT'], ''),
                         # ('800-41071-02B0', 'FTX'): (None, '81678', ['SYSFT'], ''),
                         ('800-41071-02A0', 'FTX'): (None, '81672', ['SYSFT'], ''),
                         # ('800-41071-02A0', 'FTX'): (None, '80091', ['SYSFT'], ''),
                         # ('800-41071-02A0', 'FTX'): (None, '79530', ['SYSFT'], ''),
                         # ('800-41071-02A0', 'FTX'): (None, '79529', ['SYSFT'], ''),
                         # ('800-41071-01H0', 'FTX'): (None, '78200', ['SYSFT'], ''),
                         # ('800-41071-01H0', 'FTX'): (None, '78199', ['SYSFT'], ''),
                         ('800-41071-01F0', 'FTX'): (None, '77250', ['SYSFT'], ''),
                         ('800-41071-01E0', 'FTX'): (None, '77249', ['SYSFT'], ''),
                         ('800-41071-01D0', 'FTX'): (None, '77248', ['SYSFT'], ''),
                         ('800-41071-01B0', 'FTX'): (None, '77247', ['SYSFT'], ''),
                         ('800-41071-01A0', 'FTX'): (None, '77246', ['SYSFT'], ''),
                         },
    },

}  # family_end
