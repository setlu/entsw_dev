"""
PRODUCT DEFINITIONS for C9300 Bardeen

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

__title__ = "C9300 Bardeen Product Definitions"
__version__ = '0.1.1'
__author__ = ['bborel', 'steli2']
__family__ = 'bardeen'
__consumer__ = 'c9300.Nyquist'


family = {

    'COMMON': {
        'product_family': 'bardeen',

        # Product Generation: 'GEN1', 'GEN2', 'GEN3'
        'product_generation': 'GEN3',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE'
        'uut_category': 'SWITCH',

        # Test Area process flow
        'process_flow': ['ICT', 'PCBST', 'PCB2C', 'ASSY', 'PTXCAL', 'STXCAL', 'SYSBI', 'HIPOT', 'SYSFT'],

        # Flash Params
        'PS1': 'switch:',
        'DDR_SPEED': '667',
        'LINUX_COREMASK': '15',
        'TERMINAL_LINES': '0',
        'MAC_BLOCK_SIZE': '128',
        'IMAGE_UPGRADE': 'no',
        'flash_vb_params': ['MAC_ADDR', 'MANUAL_BOOT', 'PS1', 'IMAGE_UPGRADE'],
        'flash_vb_sync_params': ['MOTHERBOARD_SERIAL_NUM', 'MODEL_NUM', 'SYSTEM_SERIAL_NUM'],

        # Images
        'btldr': {'image': '20180319_cat9K_x86_RM_16_8_1r_FC4.SPA',
                  'rev': {'ver': '16.8.1r [FC4]', 'date': '03/19/2018'},
                  'params': '-s:0x0 -b:0x1000000'},
        'linux': {'image': 'bzImage.120817.SSA',
                  'rev': ''},
        'diag': {'image': 'stardust2018July19',
                 'rev': ''},
        'fpga': {'images': ['strutt_cr_02_05_03272018_A1_mb_gld.hex', 'strutt_cr_02_06_03272018_A1_mb_upg.hex'],
                 'rev': '00000206',
                 'revreg': 'fpga_rev',
                 'name': 'strutt'},
        'nic': {1: {'image': 'BDXDE_P0_1G_P1_XFI_PV_80000636.bin',
                    'rev': '',
                    'cmd': 'eeupdate64e_new /NIC=1 /DATA %image% /DEBUG'},
                2: {'cmd': 'POWERCYCLE'},
                3: {'image': 'I211_Invm_APM_v0.6.1.txt',
                    'rev': '',
                    'cmd': 'eeupdate64e_new /NIC=2 /INVMUPDATE /MAC=%MAC_ADDR% /FILE=%image%'},
                4: {'image': 'eeupdate64e_new',
                    'cmd': 'eeupdate64e_new /ALL /MAC_DUMP'},
                },
        # MCU images given by a subdir as the dict keys.
        'mcu': {'images': {'kirch114': ['app_flash.bin.v114-02', 'app_data.srec.v114-02', 'c_kirchhoff_swap.bin', 'coulomb_kirchhoff.bin']},
                'name': 'alchemy',
                'rev': {'ios': 'APPL 0.114 (0x72)  41 (0x29)  17 (0x11)', 'coulomb': 'APPL 0.34 (0x22)  41 (0x29)  0 (0x00)'}},
        'ios_dirs': {'local': '', 'remote': 'NG3K_IOS'},
        'ios_test_pid': 'S9300UK9-168a',
        'ios_pkg': '',
        'ios_supp_files': {7: [],
                           2: [('ACTUAL', 'recovery')]},

        # IOS clean up items
        'ios_cleanup_items': ['obfl', 'crashinfo', 'startup-config'],
        # Rommon params to keep
        'rommon_params_to_keep': ['BOOT'],
        # default license files/dirs
        'default_license_files': {1: ['tracelogs'],
                                  4: ['dyn_eval', 'eval', 'persist', 'pri', 'red', '*d_license*.*'],
                                  5: ['dyn_eval', 'eval', 'persist', 'pri', 'red', '*d_license*.*']},

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
        # ACT2 Stardust Auth
        'stardust_act2_authentication': True,

        # Disk enumeration specifies the rank of all attached disks.  Primary is mandatory and is the target disk for all images (diags & IOS).
        'disk_enums': {'primary': 'sda', 'secondary': None, 'tertiary': None},
        # Flash Device is the directory mapped location of the primary parent mounted device as seen by the bootloader. Relative dir is from the mount point.
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        # Disk Enumerated Device Mounts must have an ordered precedence for dependent mount locations.
        # Parent mounts are placed first in the list.  Specified mounts should correspond to enumerated disks.
        # Format is a list of tuples: [(<device number>, <mount point>), ...]
        'device_mounts': {
            'primary': [(3, '/mnt/flash3'), (1, '/mnt/flash1'), (2, '/mnt/flash2'), (4, '/mnt/flash4'),
                        (5, '/mnt/flash5'), (6, '/mnt/flash6'), (7, '/mnt/flash7')],
            # 'primary': [(3, '/mnt/flash3'), (1, '/mnt/flash1'), (2, '/mnt/flash2'), (4, '/mnt/flash4'),
            #             (5, '/mnt/flash5'), (6, '/mnt/flash6'), (7, '/mnt/flash7'), (8, '/mnt/flash8'), (9, '/mnt/flash9')],
            'secondary': None,
            'tertiary': None,
        },
        # Partition definition for each device type.  Populated AFTER the OS determines the device size.
        'partitions': {
            'primary': None,
            'secondary': None,
            'tertiary': None,
        },
        'partition_init_macro_func': '_prepare_emmc_v2',
        'fdisk_cmd': 'gdisk',

        # ASIC
        # 'asic': {'type_ids': ['0x3e1']},

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
            2: {'cmd': 'BeaconLed On', 'op': ['Blue']}
        },

        # Passive RFID Tag
        'rfid': {'chassis_enabled': True},

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
        'cpu': {'cmd': 'BroadWellTempRead'},

        # SerDesEye
        # 'serdeseye': {'interfaces': ['SIF', 'NIF'], 'PCBST': {'nif_options': '-pd:4 -o:0'}},

        # SBC params
        'sbc': {'enable': True, 'temperature_reg': 'READ_TEMPERATURE_2', 'op': True,
                'label': {'program_begin_label': 'EXEC_LABEL_Prog_1',
                          'sync_begin_label': '',
                          'verify_begin_label': 'EXEC_LABEL_Check_1'
                          }
                },

        # Sysinit messages required for passing.
        # Format: list of tuples form of [(<regex message pattern>, <total number of msgs>), (<regex message pattern2>, <total number of msgs>), ...]
        # 'sysinit_required_to_pass': [('PCIE[0-4]: \(RC\) X[1-4] GEN-2 link UP', 1)],

        # Chamber Corners (N-Corners)
        #  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
        #  The temp+voltage designations are 2+2letters:
        #    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
        'chamber_corners': [('LTHV', True), ('LTLV', True), ('HTLV', True), ('HTHV', True)],

        # Power cycling test (FST)
        'max_power_cycles': 4,

        # Product Sequence Definition Settings
        # (Parameters that are passed to the sequence definition build-out.)
        'prod_seq_def': {
            'PCBST': {},
            'PCB2C': {},
            'ASSY': {},
            'PCBFT': {'total_loop_time_secs':  3000, 'idpro_periphs': False},
            'SYSBI': {'total_loop_time_secs':  7200, 'idpro_periphs': False},
        },

        # Voltage Margin Table for Level Check
        #  Format is {'<voltage rail name>': {...values...}, ...}
        #         or {'<voltage rail name>': {'bins': {<bin# 0-x>: {...values...}, ...}}, ...}
        #  Values: trim     = Trim voltage level from nominal.
        #          vnom     = Nominal Voltage rating.
        #          mhi, mlo = Margin Percentage for high and low independently.
        #          gb       = Guard Band Percentage (+/-).
        'vmargin_table': {
            'S_3.3V':                   {'trim': 0, 'vnom': 3.3,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_2.5V-LDO':               {'trim': 0, 'vnom': 2.5,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.8V':                   {'trim': 0, 'vnom': 1.8,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.8V-LDO':               {'trim': 0, 'vnom': 1.8,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.7V-LDO':               {'trim': 0, 'vnom': 1.7,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.5V-LDO':               {'trim': 0, 'vnom': 1.5,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.3V-LDO':               {'trim': 0, 'vnom': 1.3,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.2V-LDO':               {'trim': 0, 'vnom': 1.2,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.2V-DDQ':               {'trim': 0, 'vnom': 1.2,   'mhi': 0,    'mlo': 0,    'gb': 0.025},
            'S_1.0V':                   {'trim': 0, 'vnom': 1.0,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.035},
            'S_1.05V-CPU':              {'trim': 0, 'vnom': 1.05,  'mhi': 0,    'mlo': 0,    'gb': 0.025},
            'S_1.8V-CPUcore':           {'trim': 0, 'vnom': 1.8,   'mhi': 0,    'mlo': 0,    'gb': 0.025},
            'S_0.875VDP0-VDD':          {'trim': 0, 'vnom': 0.875, 'mhi': 0.02, 'mlo': 0.02, 'gb': 0.025},
            'S_0.910VDP0-VDD':          {'trim': 0, 'vnom': 0.910, 'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_1.1VDopSVRef':           {'trim': 0, 'vnom': 1.1,   'mhi': 0.03, 'mlo': 0.03, 'gb': 0.025},
            'S_0.85VDopSVDD':           {'trim': 0, 'vnom': 0.85,  'mhi': 0.03, 'mlo': 0.03, 'gb': 0.035},
        },

        # Temperature Table
        # Table MUST account for 1) Test Area, 2) Environmental temperature, and 3) Operational State of UUT.
        # Format is {'<index name>': {'<testarea>': {'<environ temp>': {'idle': xx, 'traf': xx, 'diag': xx, 'gb': xx}, ...}, ...}, ...}
        # 'idle' = State of UUT powered on but not doing much.
        # 'traf' = State of UUT running full bandwidth traffic
        # 'diag' = State of UUT running diagnostic tests (might have to average over serveral tests)
        # 'gb'   = Guard Band +/-% for pass or fail; 0.20 = +/-20% of the selected limit value above.
        'temperature_table': {
            'Exhaust':   {'PCB2C':  {'AMBIENT': {'idle': 36, 'traf': 40, 'diag': 35, 'gb': 0.35},
                                     'HOT':     {'idle': 60, 'traf': 65, 'diag': 65, 'gb': 0.25},
                                     'COLD':    {'idle': 5,  'traf': 20, 'diag': 20, 'gb': 1.0}},
                          'DBGSYS': {'AMBIENT': {'idle': 38, 'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'PCBST':  {'AMBIENT': {'idle': 38, 'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'PCBFT':  {'AMBIENT': {'idle': 38, 'traf': 40, 'diag': 40, 'gb': 0.30}},
                          'SYSBI':  {'AMBIENT': {'idle': 38, 'traf': 40, 'diag': 40, 'gb': 0.30}}},
            'Intake':    {'PCB2C':  {'AMBIENT': {'idle': 28, 'traf': 28, 'diag': 28, 'gb': 0.25},
                                     'HOT':     {'idle': 60, 'traf': 65, 'diag': 65, 'gb': 0.25},
                                     'COLD':    {'idle': 3,  'traf': 10, 'diag': 10, 'gb': 1.0}},
                          'DBGSYS': {'AMBIENT': {'idle': 35, 'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'PCBST':  {'AMBIENT': {'idle': 35, 'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'PCBFT':  {'AMBIENT': {'idle': 35, 'traf': 30, 'diag': 30, 'gb': 0.30}},
                          'SYSBI':  {'AMBIENT': {'idle': 35, 'traf': 32, 'diag': 32, 'gb': 0.30}}},
            'Doppler_0': {'PCB2C':  {'AMBIENT': {'idle': 50, 'traf': 50, 'diag': 50, 'gb': 0.35},
                                     'HOT':     {'idle': 70, 'traf': 80, 'diag': 80, 'gb': 0.30,  'delta': 35},
                                     'COLD':    {'idle': 10, 'traf': 30, 'diag': 30, 'gb': 1.0,   'delta': 35}},
                          'DBGSYS': {'AMBIENT': {'idle': 60, 'traf': 50, 'diag': 50, 'gb': 0.30,  'delta': 35}},
                          'PCBST':  {'AMBIENT': {'idle': 60, 'traf': 50, 'diag': 50, 'gb': 0.30,  'delta': 35}},
                          'PCBFT':  {'AMBIENT': {'idle': 60, 'traf': 50, 'diag': 50, 'gb': 0.30,  'delta': 35}},
                          'SYSBI':  {'AMBIENT': {'idle': 60, 'traf': 50, 'diag': 50, 'gb': 0.30,  'delta': 35}}},
            'CPU':       {'PCB2C':  {'AMBIENT': {'idle': 50, 'traf': 50, 'diag': 50, 'gb': 0.35},
                                     'HOT':     {'idle': 60, 'traf': 60, 'diag': 60, 'gb': 0.30},
                                     'COLD':    {'idle': 10, 'traf': 30, 'diag': 30, 'gb': 1.0}},
                          'DBGSYS': {'AMBIENT': {'idle': 60, 'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'PCBST':  {'AMBIENT': {'idle': 60, 'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'PCBFT':  {'AMBIENT': {'idle': 60, 'traf': 60, 'diag': 60, 'gb': 0.30}},
                          'SYSBI':  {'AMBIENT': {'idle': 60, 'traf': 60, 'diag': 60, 'gb': 0.30}}},
        },

        # Diag Tests within the Stardust testlist
        # For product-specific tests, place them in the product sections for appending.
        'diag_tests': [('DopSetVoltage',   {'category': 'UTIL', 'areas': ['PCBDL'], 'enabled': True, 'adt_enabled': False, 'args': '', 'func': 'step__dopsetvolt', 'func_args': {}, 'timeout': 1000}),
                       ('SysMem',          {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('SysRegs',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('RTCTest',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('SpqFramesTest',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('CdeFrameCopy',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopRegs',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopMem',          {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1000}),
                       ('DopIntr',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopOffload',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('TcamSearch',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('SupFrames',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('SupJumboFrames',  {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DpuFrames',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('CoreToCore',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopEEE',          {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopMACsecDiag',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('PortFrames',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('JumboFrames',     {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('RcpFrames',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopPtpFlexTimer', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopPtpIngTest',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopPtpEgrTest',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopPSRO',         {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('CrayCorePSRO',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('DopMBIST',        {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('DopCiscoPRBS',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('OOBM',            {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('Cable',           {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('PowerDown',       {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('PortIntrDiag',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('PortCableDiag',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('CpuToDopFrames',  {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 1200}),
                       ('REProtocol',      {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('REI2C',           {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('AlchemySystem',   {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('AlchemyCommands', {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('PsDet',           {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('StackPwrDet',     {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ('StackPwrCtrl',    {'areas': ['PCBST', 'PCB2C', 'PCBFT', 'SYSBI'], 'enabled': True, 'adt_enabled': True, 'args': '', 'timeout': 600}),
                       ],

        'traffic_cases_library': {
            '24': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-32': {'speed': '10G'}},
                },
                'TrafCase_NIF_2': {
                    'downlink_ports': {'1-24': {'speed': '1000'}},
                    'uplink_ports': {'25-26,29-30': {'speed': '1000'}, '27-28,31-32': {'speed': '10G'}},
                },
                'TrafCase_EXT_AUTO_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-24': {'speed': 'AUTO', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'NOMINAL',
                    'poe_enabled': True,
                    'poe_and_upoe': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_100_512': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-24': {'speed': '100', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'LOW',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_10_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-24': {'speed': '10', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'HIGH',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1000_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'NOMINAL',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_100_512': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '100', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'LOW',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_10_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-24': {'speed': '10', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '25-32': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': True,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'HIGH',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },
            '48': {
                'TrafCase_NIF_1': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-56': {'speed': '10G'}},
                },
                'TrafCase_NIF_2': {
                    'downlink_ports': {'1-48': {'speed': '1000'}},
                    'uplink_ports': {'49-50,53-54': {'speed': '1000'}, '51-52,55-56': {'speed': '10G'}},
                },
                'TrafCase_EXT_AUTO_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-48': {'speed': 'AUTO', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'NOMINAL',
                    'poe_enabled': False,
                    'poe_and_upoe': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_100_512': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-48': {'speed': '100', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'LOW',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_EXT_10_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCBST'],
                    'downlink_ports': {
                        '1-48': {'speed': '10', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Bidirectional',
                    'loopback_point': 'External',
                    'vmargin': 'HIGH',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_1000_64': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-48': {'speed': '1000', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 64, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'NOMINAL',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_100_512': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-48': {'speed': '100', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 512, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'LOW',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
                'TrafCase_PHY_10_1518': {
                    'enabled': True,
                    'areas': ['DBGSYS', 'PCB2C', 'PCB4C', 'PCBFT', 'SYSBI', 'SYSFT'],
                    'downlink_ports': {
                        '1-48': {'speed': '10', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                 'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'uplink_ports': {
                        '49-56': {'speed': '10G', 'duplex': 'AUTO', 'crossover': 'AUTO', 'size': 1518, 'stress': True, 'forwarding_schm': 'bridging',
                                  'iteration': 1, 'fifo': 8, 'lifo': 1, 'frames_link': 'norestart', 'macsec_mode': 'nomacsec'},
                    },
                    'stackswitching': False,
                    'breakout_ports': {'40G': None, '100G': None},
                    'loopback_direction': 'Forward',
                    'loopback_point': 'PHY0',
                    'vmargin': 'HIGH',
                    'poe_enabled': False,
                    'runtime': 120,
                    'pretraf_cmds': [], 'traf_cmds': [],
                },
            },
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
        },  # cmpd

    },

    'BARDEEN24': {
        'tlv_type': 'B24',
        'cfg_pids': ['C9300-24S'],
        'MODEL_NUM': 'C9300-24S',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '68-102037-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-19406-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '17-15208-01_SCR24_SBC',
        'CLEI_CODE_NUMBER': '',
        'ECI_CODE_NUMBER': '',
        'mcu_settings': {
            'cmd': 'sendredearthframe 0 %data% -e -p:5000',
            'update': {
                1: {'data': 'f1.06', 'op': 'READ', 'label': 'Fan curve coeff'},
                2: {'data': '71.60.59.14.09.22.26', 'op': 'WRITE', 'label': 'Fan curve coeff'},
                3: {'data': 'f7.04', 'op': 'READ', 'label': 'UCSDS coeff'},
                4: {'data': '77.5f.36.32.e9', 'op': 'WRITE', 'label': 'UCSDS coeff'},
                5: {'data': 'ef.02', 'op': 'READ', 'label': 'Read Pmin'},
                6: {'data': '6f.00.f0', 'op': 'WRITE', 'label': 'Pmin 248W'},
            },
        },
        'asic': {'type_ids': ['0x3e1'], 'core_count': 1, 'locations': ['U0']},
        'serdeseye': {'interfaces': ['SIF', 'NIF'], 'PCBST': {'nif_options': '-pd:4 -o:0'}},
        'traffic_cases': ('traffic_cases_library', '24'),
        'sysinit_required_to_pass': [('PCIE[0-4]: \(RC\) X[1-4] GEN-2 link UP', 1)],
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
        'eco_manifest': {('73-18270-03A0', 'ALL'): ('EA557099', '96749', ['PCBDL', 'PCBST', 'PCB2C'], ''),
                         ('68-101188-01A0', 'ALL'): ('EA557099', '96777', ['ASSY', 'SYSBI', 'PCBFT'], ''),
                         }
    },

    'BARDEEN48': {
        'tlv_type': 'B48',
        'cfg_pids': ['C9300-48S'],
        'MODEL_NUM': 'C9300-48S',
        'MODEL_REVISION_NUM': '',
        'TAN_NUM': '68-102038-01',
        'TAN_REVISION_NUMBER': '',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-19406-01',
        'MOTHERBOARD_REVISION_NUM': '04',
        'VERSION_ID': 'V01',
        'SBC_CFG':   '',
        'CLEI_CODE_NUMBERE': '',
        'ECI_CODE_NUMBER': '',
        'mcu_settings': {
            'cmd': 'sendredearthframe 0 %data% -e -p:5000',
            'update': {
                1: {'data': 'f1.06', 'op': 'READ', 'label': 'Fan curve coeff'},
                2: {'data': '71.60.59.14.09.22.26', 'op': 'WRITE', 'label': 'Fan curve coeff'},
                3: {'data': 'f7.04', 'op': 'READ', 'label': 'UCSDS coeff'},
                4: {'data': '77.5f.36.32.e9', 'op': 'WRITE', 'label': 'UCSDS coeff'},
                5: {'data': 'ef.02', 'op': 'READ', 'label': 'Read Pmin'},
                6: {'data': '6f.00.f8', 'op': 'WRITE', 'label': 'Pmin 248W'},
            },
        },
        'asic': {'type_ids': ['0x3e1'], 'core_count': 1, 'locations': ['U0']},
        'serdeseye': {'interfaces': ['SIF', 'NIF'], 'PCBST': {'nif_options': '-pd:4 -o:0'}},
        'traffic_cases': ('traffic_cases_library', '48'),
        'sysinit_required_to_pass': [('PCIE[0-4]: \(RC\) X[1-4] GEN-2 link UP', 1)],
        'cmpd_types': ('cmpd_type_verify_manifest', ['T.All.1', 'T.All.2', 'T.All.3']),
        'eco_manifest': {('73-18273-04A0', 'ALL'): ('EA557099', '96779', ['PCBDL', 'PCBST', 'PCB2C'], ''),
                         ('68-101191-01A0', 'ALL'): ('EA557099', '96781', ['ASSY', 'SYSBI', 'PCBFT'], ''),
                         }
    },
}
