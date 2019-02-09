"""
PRODUCT DEFINITIONS for ALL C6K Products

The product definition file contains descriptive data about all UUTs of the product line for the purposes of test automation.

Structure:
uut_prompt_map = [(<mode>, <prompt regex pattern>), ...]
uut_state_machine = {<mode>: [(dstmode, cost), ...], ...}
disk_partition_tables = {<device size index>: {<sequence index>: {partition details per device enumeration}, ...}, ...} if any
common_shared = {<item>: <value>, ...}

"""

__title__ = "C6K Common Product Definitions"
__version__ = '0.1.0'


# C6K UUT modes and their associated prompts
# Note: All modes and prompts should be unique (i.e. two modes cannot share the same prompt). For dynamic
# prompts a pattern matching scheme can be used.
# Take care not to have "overlapping" patterns for multiple modes.  The order is preserved to help prevent overlap.
# All patterns are standard regex patterns.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_prompt_map = [
    ('BTLDR', 'switch: '),
    ('IOS', '[sS]witch> '),
    ('IOSE', '[sS]witch# '),
    ('DIAG', 'Diag> '),
    ('TRAF', 'Traf> '),
    ('SYMSH', '-> '),
    ('STARDUST', r'(?:Stardust> )|(?:[A-Z][\S]*> )'),

]

# State machine definition for UUT modes and mode paths.
# REQUIRED for use with "<product>_mode.py" using MachineManager.
uut_state_machine = {
    'BTLDR':         [('STARDUST', 10), ('IOS', 10)],
    'IOS':           [('BTLDR', 10), ('IOSE', 10)],
    'IOSE':          [('IOS', 10)],
    'STARDUST':      [('BTLDR', 10), ('TRAF', 10), ('DIAG', 10), ('SYMSH', 10)],
    'TRAF':          [('STARDUST', 10), ('SYMSH', 10)],
    'DIAG':          [('STARDUST', 10), ('SYMSH', 10)],
    ('SYMSH', 1):    [('STARDUST', 10), ('DIAG', 10), ('TRAF', 10)],
}


# Partitioning tables and device enumeration mapping for all C2K products based on flash device size.
disk_partition_tables = {
}

# Items that all C2K product families share in common.
# These may be overridden by the family specific product definitions.
common_shared = {
    'key': 'value',
}
