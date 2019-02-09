"""
COMMON PRODUCT DEFINITIONS for ALL CATALYST-Series5 Products

The common product definition file contains descriptive data about all UUTs of the product line for the purposes of
test automation.

Structure:
uut_prompt_map = [(<mode>, <prompt regex pattern>), ...]
uut_state_machine = {<mode>: [(dstmode, cost), ...], ...}
disk_partition_tables = {<device size index>: {<sequence index>: {partition details per device enumeration}, ...}, ...}
revision_map = {'primary param item': 'revision param item', ...}
tlv_map = {'TVL Desc': 'Traditional Desc', ...}
common_shared = {<item>: <value>, ...}

"""

from collections import OrderedDict

__title__ = "Catalyst-Series5 Common Product Definitions"
__version__ = '2.0.0'
__line__ = 'cat5'

uut_prompt_map = [
    ('BTLDR', 'switch:'),
    ('IOS', '[sS]witch>'),
    ('IOSE', '[sS]witch#'),
    ('DIAG', 'Diag>'),
    ('LINUX', r'(?:# )|(?:[a-zA-Z][\S]*# )'),
    ('STARDUST', r'(?:Stardust> )|(?:[A-Z][\S]*> )'),
]

# State machine definition for UUT modes and mode paths.
# REQUIRED for use with "<product>_mode.py" using ModeManager.
uut_state_machine = {
    'BTLDR':         [('LINUX', 5), ('IOS', 10)],
    'LINUX':         [('BTLDR', 7), ('STARDUST', 3)],
    'IOS':           [('IOSE', 2)],
    'IOSE':          [('BTLDR', 10), ('IOS', 2)],
    'STARDUST':      [('LINUX', 4), ('DIAG', 2)],
    'DIAG':          [('STARDUST', 1)],
}
