"""
PRODUCT LINE DEFINITIONS for ALL C4500 Products

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

from collections import OrderedDict

__title__ = "C4500 Product Line Definition"
__version__ = '2.0.0'
__line__ = 'C4500'
__category__ = 'MODULAR'

# C9400 UUT modes and their associated prompts
# Note: All modes and prompts should be unique (i.e. two modes cannot share the same prompt).
# For dynamic prompts a pattern matching scheme can be used.
# Take care not to have "overlapping" patterns for multiple modes.  The order is preserved to help prevent overlap.
# All patterns are standard regex patterns.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_prompt_map = [
    ('BTLDR', '(?:switch: )|(?:rommon [0-9]+ >)'),
    ('IOS', '[sS]witch>'),
    ('IOSE', '[sS]witch#'),
    ('IOSECFG', r'[sS]witch\(config\)#'),
    ('SYSSHELL', r'\[Switch_RP_[0-9]:[\S]+\]\$ '),
    ('DIAG', 'Diag>[\S]+> '),
    ('TRAF', 'Traf> '),
    ('SYMSH', '-> '),
    ('LINUX', r'[\S]*?:/[\S]*?# '),
    ('STARDUST', r'(?:Stardust> )|(?:[A-Z][\S]*> )'),
]

# State machine definition for UUT modes and mode paths.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_state_machine = {
    'BTLDR':         [('LINUX', 10), ('IOS', 10)],
    'LINUX':         [('BTLDR', 10), ('STARDUST', 10)],
    'IOS':           [('IOSE', 10)],
    'IOSE':          [('BTLDR', 10), ('IOS', 10), ('IOSECFG', 10), ('SYSSHELL', 10)],
    'IOSECFG':       [('IOSE', 10)],
    'SYSSHELL':      [('IOSE', 10)],
    'STARDUST':      [('BTLDR', 10), ('LINUX', 10), ('TRAF', 10), ('DIAG', 10), ('SYMSH', 10)],
    'TRAF':          [('STARDUST', 10), ('SYMSH', 10)],
    'DIAG':          [('STARDUST', 10), ('SYMSH', 10)],
    ('SYMSH', 1):    [('STARDUST', 10), ('DIAG', 10), ('TRAF', 10)],
}


# Partitioning tables and device enumeration mapping for all C3K products based on flash device size.
# (sdx is the appropriate enumerated device e.g. sda, sdb, etc.)
# WARNING: These tables are standardized for all C3K products and IOS releases (EX, Darya, Amur, Beni, Polaris, etc).
# DO NOT MODIFY!
# NOTE: All partitions must be indexed in device size magnitude of 'xGB' where x = total device size.
#
#   ================================================================================================================
#   GEN3 (Intel)
#                                                              #
#   *********  Partition for 16G device  ***********           #   *********  Partition for32G device  ***********
#    sdx1: +1600M                         (gpt)                #    sdx1: +xM                            (gpt)
#    sdx2: +256M                          (gpt)                #    sdx2: +xM                            (gpt)
#    sdx3: +11000M                        (gpt)                #    sdx3: xM                             (gpt)
#    sdx4: +8M                            (gpt)                #    sdx4: +xM                            (gpt)
#    sdx5: +8M                            (gpt)                #    sdx5: +xM                            (gpt)
#    sdx6: +128M                          (gpt)                #    sdx6: +xM                            (gpt)
#    sdx7: +1000M                         (gpt)                #    sdx7: +xM                            (gpt)
#
#
disk_partition_tables = {}

# Supplemental data on UUT labels mapped to their associated primary item.
# Specifically, this is the revision type added to the barcode after a CPN or PID.
revision_map = {
    'MOTHERBOARD_ASSEMBLY_NUM': 'MOTHERBOARD_REVISION_NUM',
    'TAN_NUM': 'TAN_REVISION_NUM',
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
# NOTE: The order is important when dealing with 0xE6 (DB Info) filed since the tlv type + field determine the
# prompting order; hence, an OrderedDict is used instead of the standard python dict.
# An inverse dict is dynamically created also.
tlv_map_list = []
tlv_map = OrderedDict(tlv_map_list)
tlv_inverse_map_list = [(v[1], (v[0], k)) for k, v in tlv_map.items()]
tlv_inverse_map = OrderedDict(tlv_inverse_map_list)