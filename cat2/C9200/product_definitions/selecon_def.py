"""
PRODUCT DEFINITIONS for C2K Selecon

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

__title__ = "C2K Selecon Product Definitions"
__version__ = '0.1.0'
__family__ = "selecon"


family = {
    'COMMON': {
        'product_family': "selecon",

        # Product Generation: 'GEN1', 'GEN2', 'GEN3'
        'product_generation': 'GEN2',

        # UUT Categories: 'SWITCH', 'UPLINK_MODULE', 'ADAPTER_MODULE', 'CABLE'
        'uut_category': 'SWITCH',

        # Test Area process flow
        # 'process_flow': ['ICT', 'PCBP2', 'PCB2C', 'PTXCAL', 'STXCAL', 'PCBFT', 'HIPOT', 'SYSFT'],

    },

    'SELECON1': {
        'cfg_pids': [''],
        'MODEL_NUM': 'SELECON1',
        'MODEL_REVISION_NUM': 'A0',
        'TAN_NUM': '68-00000-01',
        'TAN_REVISION_NUMBER': 'A0',
        'MOTHERBOARD_ASSEMBLY_NUM': '73-00000-01',
        'MOTHERBOARD_REVISION_NUM': 'A0',
        'VERSION_ID': 'P1',
        'SBC_CFG': '',
        'CLEI_CODE': '',
        'ECI_NUM': '',
        'asic': {'core_count': 1, 'locations': ['U0']},
        # 'traffic_cases': ('traffic_cases_library', '48'),
    },

}
