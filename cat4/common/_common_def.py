"""
COMMON PRODUCT DEFINITIONS for ALL CATALYST-Series4 Products

The common product definition file contains descriptive data about all UUTs of the product line for the purposes of
test automation.

Structure:
uut_prompt_map        = [(<mode>, <prompt regex pattern>), ...]
uut_state_machine     = {<mode>: [(dstmode, cost), ...], ...}
:EndStructure

"""

__title__ = "Catalyst-Series4 Common Product Definitions"
__version__ = '2.0.0'
__line__ = 'cat4'
__category__ = 'GENERIC'

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

puid_key_manifest = {
    'SUP': {
        'PCBA': ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
                 'MOTHERBOARD_SERIAL_NUM', 'MOTHERBOARD_ASSEMBLY_NUM'],
        'SYS': ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SERIAL_NUM', 'MODEL_NUM'],
    },
    'LINECARD': {
        'PCBA': ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
                 'MOTHERBOARD_SERIAL_NUM', 'MOTHERBOARD_ASSEMBLY_NUM'],
        'SYS': ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SERIAL_NUM', 'MODEL_NUM'],
    },
}