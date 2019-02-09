"""
PRODUCT LINE DEFINITIONS for ALL Catalyst Series 2 Peripherals

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
from collections import OrderedDict, namedtuple

__title__ = "Catalyst Series-2 Peripherals Product Line Definitions"
__version__ = '2.0.0'
__line__ = 'cat2'
__category__ = 'PERIPH'


# C9300 UUT modes and their associated prompts
# Note: All modes and prompts should be unique (i.e. two modes cannot share the same prompt).
# For dynamic prompts a pattern matching scheme can be used.
# Take care not to have "overlapping" patterns for multiple modes.  The order is preserved to help prevent overlap.
# For multi-mode identical prompts, the last of that group in the order list becomes the default IF there is no extension match.
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
    ('LINUX', r'(?:# )|(?:[a-zA-Z][\S]*# )'),
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

# Mapping of TLV Type Descriptors to the TLV filed type and the uut_config param names (a.k.a. traditional
# flash param names).
# NOTE: The order is important when dealing with 0xE6 (DB Info) field since the tlv type + field determine the
# prompting order; hence, an OrderedDict is used instead of the standard python dict.
# An inverse dict is dynamically created to reference the TLV using traditional flash params.
tlv_map_list = [
    ('Part Number - PCA',          ('0x82', 'MOTHERBOARD_ASSEMBLY_NUM')),
    ('Revision number - PCA',      ('0x42', 'MOTHERBOARD_REVISION_NUM')),
    # ('Deviation Number',           ('0x88', 'DEVIATION_NUM')),
    ('Serial Number - PCA',        ('0xC1', 'MOTHERBOARD_SERIAL_NUM')),
    ('RMA test history',           ('0x03', 'RMA_TEST_HISTORY')),
    ('RMA Number',                 ('0x81', 'RMA_NUM')),
    ('RMA history',                ('0x04', 'RMA_HISTORY')),
    ('Part Number -TAN',           ('0x87', 'TAN_NUM')),
    ('Part Number - TAN(6-byte)',  ('0xC0', 'TAN_NUM')),
    ('Revision number - TAN',      ('0x8D', 'TAN_REVISION_NUMBER')),
    ('CLEI codes',                 ('0xC6', 'CLEI_CODE_NUMBER')),
    ('ECI number',                 ('0x8E', 'ECI_CODE_NUMBER')),
    ('Product number/identifier',  ('0xCB', 'CFG_MODEL_NUM')),
    ('Hardware Version',           ('0x41', 'MODEL_REVISION_NUM')),
    ('UDI name/Base PID',          ('0xDB', 'MODEL_NUM')),
    ('Version identifier',         ('0x89', 'VERSION_ID')),
    ('Serial number',              ('0xC2', 'SYSTEM_SERIAL_NUM')),
    ('MAC address - Base',         ('0xCF', 'MAC_ADDR')),
    ('MAC address - block size',   ('0x43', 'MAC_BLOCK_SIZE')),
    ('RFID - chassis',             ('0xE4', 'RFID_TID')),
    ('Manufacturing test data',    ('0xC4', 'MFG_TEST_DATA')),
    ('part number - USB',          ('0xE6', 'USB_ASSEMBLY_NUM')),
    ('rev number - USB',           ('0xE6', 'USB_REVISION_NUM')),
    ('serial number - USB',        ('0xE6', 'USB_SERIAL_NUM')),
    ('part number - StackPower',   ('0xE6', 'STKPWR_ASSEMBLY_NUM')),
    ('rev number - StackPower',    ('0xE6', 'STKPWR_REVISION_NUM')),
    ('serial number - StackPower', ('0xE6', 'STKPWR_SERIAL_NUM')),
    ('part number - POE1',         ('0xE6', 'POE1_ASSEMBLY_NUM')),
    ('rev number - POE1',          ('0xE6', 'POE1_REVISION_NUM')),
    ('serial number - POE1',       ('0xE6', 'POE1_SERIAL_NUM')),
    ('part number - POE2',         ('0xE6', 'POE2_ASSEMBLY_NUM')),
    ('rev number - POE2',          ('0xE6', 'POE2_REVISION_NUM')),
    ('serial number - POE2',       ('0xE6', 'POE2_SERIAL_NUM')),
]
tlv_map = OrderedDict(tlv_map_list)

# Chamber Profile (Temperature Corners)
# These may be overridden by the family specific product definitions.
ChamberProfileDesc = namedtuple('ChamberProfileDesc', 'temperature rate margin duration max_humidity')
chamber_profile = [
    ('COLD',    {'ramp': ChamberProfileDesc(0, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 3, 5, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)}),
    ('HOT',     {'ramp': ChamberProfileDesc(50, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 3, 5, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)}),
    ('AMBIENT', {'ramp': ChamberProfileDesc(28, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 3, 1, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)}),
    ('DRY',     {'ramp': ChamberProfileDesc(25, 1.5, 0, None, 0),
                 'soak': ChamberProfileDesc(None, None, 3, 1, 0),
                 'test': ChamberProfileDesc(None, None, 3, None, 0)})
]

# Default Chamber Corners (5-Corner)
#  Format = [('<chamber corner temp+voltage>', adt_enabled), ...]
#  The temp+voltage designations are 2+2letters:
#    HT = High Temp,  LT = Low Temp,  HV = High Voltage, LV = Low Voltage, Nx = Nominal/Ambient
# These may be overridden by the family specific product definitions.
chamber_corners = [('NTNV', True), ('LTHV', True), ('LTLV', True), ('HTLV', True), ('HTHV', True)]
