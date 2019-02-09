"""
PRODUCT LINE DEFINITIONS for ALL C3850 Products
    1. Edison/CR/CSR - Newton
    2. Planck
    3. Orsted
    4. Gladiator

The family product definition file contains descriptive data about all UUTs of the product family for the purposes of
test automation.

Structure:
uut_prompt_map        = [(<mode>, <prompt regex pattern>), ...]
uut_state_machine     = {<mode>: [(dstmode, cost), ...], ...}
disk_partition_tables = {<device size index>: {<sequence index>: {partition details per dev enum}, ...}, ...}
revision_map          = {'primary param item': 'revision param item', ...}
tlv_map_list          = [...]
tlv_map               = OrderedDict of {'TVL Desc': (<field type>, 'Traditional Desc'), ...}
chamber_profile       = [('<CORNER>', {ramp, soak, test nested dicts of namedtuples}), ...}
chamber_corners       = [(<composite corner>, <adt>), ...]
asic_type_table       = {...}
:EndStructure

"""

# Python
# ------
from collections import namedtuple

__title__ = "C3850 Product Line Definitions"
__version__ = '2.0.0'
__line__ = 'C3850'
__category__ = 'SWITCH'

# C3850 UUT modes and their associated prompts
# Note: All modes and prompts should be unique (i.e. two modes cannot share the same prompt).
# For dynamic prompts a pattern matching scheme can be used.
# Take care not to have "overlapping" patterns for multiple modes.  The order is preserved to help prevent overlap.
# All patterns are standard regex patterns.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_prompt_map = [
    ('BTLDR', 'switch:'),
    ('IOS', '[sS]witch>'),
    ('IOSE', '[sS]witch#'),
    ('IOSECFG', r'[sS]witch\(config\)#'),
    ('DIAG', 'Diag>'),
    ('TRAF', 'Traf>'),
    ('SYMSH', '-> '),
    ('LINUX', r'(?:~ # )|(?:/[a-zA-Z][\S]* # )'),
    ('STARDUST', r'(?:Stardust> )|(?:[A-Z][\S]*> )'),
]

# State machine definition for UUT modes and mode paths.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_state_machine = {
    'BTLDR':         [('LINUX', 5), ('IOS', 10)],
    'LINUX':         [('BTLDR', 7), ('STARDUST', 3)],
    'IOS':           [('IOSE', 2)],
    'IOSE':          [('BTLDR', 10), ('IOS', 2), ('IOSECFG', 3)],
    'IOSECFG':       [('IOSE', 2)],
    'STARDUST':      [('LINUX', 4), ('TRAF', 3), ('DIAG', 2), ('SYMSH', 2)],
    'TRAF':          [('STARDUST', 1), ('SYMSH', 2)],
    'DIAG':          [('STARDUST', 1), ('SYMSH', 2)],
    ('SYMSH', 1):    [('STARDUST', 2), ('DIAG', 2), ('TRAF', 2)],
}


# Partitioning tables and device enumeration mapping for all C3K products based on flash device size.
# (sdx is the appropriate enumerated device e.g. sda, sdb, etc.)
# WARNING: These tables are standardized for all C3K products and IOS releases (EX, Darya, Amur, Beni, Polaris, etc).
# DO NOT MODIFY!
# NOTE: All partitions must be indexed in device size magnitude of 'xGB' where x = total device size.
#
#   ================================================================================================================
#   GEN2 (Cavium)
#                                                              #
#   *********  Partition for 8G device  ***********            #   *********  Partition for 4G device  ***********
#    sdx1: +256M                          (primary)            #    sdx1: +256M                          (primary)
#          +144M                          (extended)           #          +144M                          (extended)
#    sdx3: (8G - (256M + 144M)) = 7600M   (primary)            #    sdx3: (4G - (256M + 144M)) = 3600M   (primary)
#    sdx5: +2M                            (logical)-+          #    sdx5: +2M                            (logical)-+
#    sdx6: +2M                            (logical) |          #    sdx6: +2M                            (logical) |
#    sdx7: +40M                           (logical) |          #    sdx7: +40M                           (logical) |
#    sdx8: +40M                           (logical) |          #    sdx8: +40M                           (logical) |
#    sdx9: (144M - 84M) = 60M             (logical)-+          #    sdx9: (144M - 84M) = 60M             (logical)-+
#                                                              #
#   *********  Partition for 2G device  ***********            #    *********  Partition for 1G device  ***********
#    sdx1: +256M                          (primary)            #    sdx1: +150M                          (primary)
#          +144M                          (extended)           #          +120M                          (extended)
#    sdx3: (2G - (256M + 144M)) = 1600M   (primary)            #    sdx3: (1G - (150M + 120M)) = 730M    (primary)
#    sdx5: +2M                            (logical)-+          #    sdx5: +2M                            (logical)-+
#    sdx6: +2M                            (logical) |          #    sdx6: +2M                            (logical) |
#    sdx7: +40M                           (logical) |          #    sdx7: +32M                           (logical) |
#    sdx8: +40M                           (logical) |          #    sdx8: +32M                           (logical) |
#    sdx9: (144M - 84M) = 60M             (logical)-+          #    sdx9: (120M - 68M) = 52M             (logical)-+
#
#    Notes GEN2:
#      1. sys_id is ONLY applied to primary partitions.
#      2. device_num may not be contiguous.
#
disk_partition_tables = {
    # GEN2 -------------------------------------------------------------------------------------------------------------
    '8GB': {
        1: {'device_num': 1,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '1',  'first_cylinder': '1', 'last_cylinder': '+256M'},
        2: {'device_num': None, 'sys_id': '',   'partition_type': 'e', 'partition_number': '2',  'first_cylinder': '',  'last_cylinder': '+144M'},
        3: {'device_num': 3,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '3',  'first_cylinder': '',  'last_cylinder': ''},
        4: {'device_num': 5,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        5: {'device_num': 6,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        6: {'device_num': 7,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        7: {'device_num': 8,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        8: {'device_num': 9,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': ''},
    },
    '4GB': {
        1: {'device_num': 1,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '1',  'first_cylinder': '1', 'last_cylinder': '+256M'},
        2: {'device_num': None, 'sys_id': '',   'partition_type': 'e', 'partition_number': '2',  'first_cylinder': '',  'last_cylinder': '+144M'},
        3: {'device_num': 3,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '3',  'first_cylinder': '',  'last_cylinder': ''},
        4: {'device_num': 5,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        5: {'device_num': 6,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        6: {'device_num': 7,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        7: {'device_num': 8,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        8: {'device_num': 9,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': ''},
    },
    '2GB': {
        1: {'device_num': 1,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '1',  'first_cylinder': '1', 'last_cylinder': '+256M'},
        2: {'device_num': None, 'sys_id': '',   'partition_type': 'e', 'partition_number': '2',  'first_cylinder': '',  'last_cylinder': '+144M'},
        3: {'device_num': 3,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '3',  'first_cylinder': '',  'last_cylinder': ''},
        4: {'device_num': 5,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        5: {'device_num': 6,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        6: {'device_num': 7,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        7: {'device_num': 8,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+40M'},
        8: {'device_num': 9,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': ''},
    },
    '1GB': {
        1: {'device_num': 1,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '1',  'first_cylinder': '1', 'last_cylinder': '+150M'},
        2: {'device_num': None, 'sys_id': '',   'partition_type': 'e', 'partition_number': '2',  'first_cylinder': '',  'last_cylinder': '+120M'},
        3: {'device_num': 3,    'sys_id': '83', 'partition_type': 'p', 'partition_number': '3',  'first_cylinder': '',  'last_cylinder': ''},
        4: {'device_num': 5,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        5: {'device_num': 6,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+2M'},
        6: {'device_num': 7,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+32M'},
        7: {'device_num': 8,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': '+32M'},
        8: {'device_num': 9,    'sys_id': '83', 'partition_type': 'l', 'partition_number': None, 'first_cylinder': '',  'last_cylinder': ''},
    },

}

# Supplemental data on UUT labels mapped to their associated primary item.
# Specifically, this is the revision type added to the barcode after a CPN or PID.
revision_map = {
    'MOTHERBOARD_ASSEMBLY_NUM': 'MOTHERBOARD_REVISION_NUM',
    'TAN_NUM': 'TAN_REVISION_NUMBER',
    'MODEL_NUM': 'VERSION_ID',
    'PID': 'VID',
    'VPN': 'HWV',
    'PCAPN': 'PCAREV',
    'STKPWR_ASSEMBLY_NUM': 'STKPWR_REVISION_NUM',
    'USB_ASSEMBLY_NUM': 'USB_REVISION_NUM',
    'POE1_ASSEMBLY_NUM': 'POE1_REVISION_NUM',
    'POE2_ASSEMBLY_NUM': 'POE2_REVISION_NUM',
    'POE3_ASSEMBLY_NUM': 'POE3_REVISION_NUM',
    'POE4_ASSEMBLY_NUM': 'POE4_REVISION_NUM',
}

# No TLV maps for C3K Gen2 products
# (Placeholder variable for compatibility.)
tlv_map_list = []
tlv_map = {}

# Chamber Profile (Temperature Corners)
# These may be overridden by the family specific product definitions.
ChamberProfileDesc = namedtuple('ChamberProfileDesc', 'temperature rate margin duration max_humidity')
chamber_profile = [
    ('COLD',    {'ramp': ChamberProfileDesc(0, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 2, 5, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)}),
    ('HOT',     {'ramp': ChamberProfileDesc(50, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 2, 5, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)}),
    ('AMBIENT', {'ramp': ChamberProfileDesc(28, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 2, 1, 0),
                 'test': ChamberProfileDesc(None, None, 2, None, 0)}),
    ('DRY',     {'ramp': ChamberProfileDesc(25, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 2, 1, 0),
                 'test': ChamberProfileDesc(None, None, 2, None, 0)})
]

# Default Chamber Corners (5-Corner)
#  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
#  The temp+voltage designations are 2+2letters:
#    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
# These may be overridden by the family specific product definitions.
chamber_corners = [('NTNV', True), ('LTHV', True), ('LTLV', True), ('HTLV', True), ('HTHV', True)]

# ASIC Table for chip type details
asic_type_table = {
    '0x0351': {'name': 'Doppler',    'ver': {'0x1': {'cpn': '08-0849-01', 'freq': '100 Mhz', 'vendor': 'IBM'},
                                             '0x2': {'cpn': '08-0849-02', 'freq': '100 Mhz', 'vendor': 'IBM'}}},
    '0x0390': {'name': 'DopplerCR',  'ver': {'0x1': {'cpn': '08-0912-01', 'freq': '300 Mhz', 'vendor': 'IBM'},
                                             '0x2': {'cpn': '08-0912-02', 'freq': '300 Mhz', 'vendor': 'IBM'}}},
    '0x03ce': {'name': 'DopplerCSR', 'ver': {'0x1': {'cpn': '08-0973-01', 'freq': '375 Mhz', 'vendor': 'STMICRO'},
                                             '0x2': {'cpn': '08-0974-01', 'freq': '500 Mhz', 'vendor': 'STMICRO'},
                                             '0x3': {'cpn': '08-1001-01', 'freq': '500 Mhz', 'vendor': 'STMICRO'}}},
    '0x03e1': {'name': 'DopplerD',   'ver': {'0x1': {'cpn': '08-0000-01', 'freq': '500 Mhz', 'vendor': 'STMICRO'}}},
    '0x03xy': {'name': 'DopplerE',   'ver': {'0x1': {'cpn': '08-0000-01', 'freq': '500 Mhz', 'vendor': 'STMICRO'}}},
}
