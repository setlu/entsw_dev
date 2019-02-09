"""
=============================
Gold UUT Unittest Definitions
=============================

All UUTs allocated to automated unittesting of production code can be placed here.

RULE: 1) All named dict keys for a fully qualified container MUST correspond exactly to the Apollo server x_config.py:
         a) Production Line name,
         b) Test Area label,
         c) Station name,
         d) Container/Supercontainer name.
      2) The server hostname must match.


FORMAT:
citp_uuts = {
    <server_hostname1>: {
        <production_line>: {
            <test_area>: {
                <station_name>: {
                    <container>:
                        {'enabled': True|False, 'mode': 'DEBUG', 'start_delay': <secs>, 'timeout': <secs>, 'answers': [<str>, <str>, ...]},
                    <supercontainer>:
                        {'enabled': True|False, 'mode': 'DEBUG', 'start_delay': <secs>, 'timeout': <secs>, 'answers': [<str>, <str>, ...]},
                        ...
                    }, ...
                }, ...
            }, ...
        }, ...
    <server_hostname2>: <server_hostname1>    <-- reference pointer (only allowed at the "server" level)
}


"""

__title__ = 'Gold UUT Unittest Definitions'
__author__ = ['bborel']
__version__ = '2.0.0'

mode = 'DEBUG'
gold_uuts = {

    # CISCO - Austin (CITP & Lab)
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    'ausapp-citp01': {
        'C9400-LC': {},
        'C9400-SUP': {},
    },
    'ausapp-citp02': 'ausapp-citp01',
    'ausapp-citp03': 'ausapp-citp01',
    'ausapp-citp04': 'ausapp-citp01',
    'ausapp-citp05': 'ausapp-citp01',
    'ausapp-citp06': 'ausapp-citp01',
    'ausapp-citp07': 'ausapp-citp01',
    'ausapp-citp08': 'ausapp-citp01',
    'ausapp-citp09': 'ausapp-citp01',
    'ausapp-citp10': 'ausapp-citp01',

    # CISCO - San Jose (CITP & Lab)
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    'sj18-apollo1': {
        'C9400-LC': {
            'PCBP2': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-LC-48UX', 'JPE10111111', '73-16003-07', 'JPE11111110', '73-16439-02 A0', 'JPE12111111', '73-16439-02 A0', 'NO']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-LC-48P', 'JPE20111111', '73-16885-06', 'JPE21111111', '73-16439-02 A0', 'JPE22111111', '73-16439-02 A0', 'NO']},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-LC-48P', 'JPE30111111', '73-16885-06', 'JPE31111111', '73-16439-02 A0', 'JPE32111111', '73-16439-02 A0', 'NO']},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-LC-48U', 'JPE40111111', '73-16884-07', 'JPE41111111', '73-16439-02 A0', 'JPE42111111', '73-16439-02 A0', 'NO']},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-LC-24XS', 'JPE50111111', '73-16008-05', 'JPE51111111', '73-16439-02 A0', 'JPE52111111', '73-16439-02 A0', 'NO']},
                },
            },
            'PCB2C': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCBPM': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
        },
        'C9400-SUP': {},
    },
    'sjc18app-lab1': {
        'C9400-LC': {},
        'C9400-SUP': {},
    },
    'sjc18app-lab2': {
        'C9400-LC': {},
        'C9400-SUP': {},
    },
    'sjc18app-lab3': {
        'C9400-LC': {},
        'C9400-SUP': {},
    },
    'sjc18app-lab4': {
        'C9400-LC': {},
        'C9400-SUP': {
            'PCBP2': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE22020B0U', '73-101371-02 A0', 'A12345678']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE22020B1H', '73-101371-02 A0', 'A12345679']},
                },
                'Station_A_Chassis_02': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE221505Y8', '73-101371-02 A0', 'A22345678']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE221505WY', '73-101371-02 A0', 'A22345679']},
                },
            },
        },
    },
    'sjc18app-lab12': {
        'C9400-LC': {},
        'C9400-SUP': {
            'PCBP2': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE22020B0U', '73-101371-02 A0', 'A12345678']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9400-SUP-1XL-Y', 'JAE22020B1H', '73-101371-02 A0', 'A12345679']},
                },
            },
        },
    },

    # JPE - Jabil-Penang (Development)
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    'jpeavp140': {
        'C9400-LC': {
            'PCBP2C': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCB2C': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCBPM': {
                'Station_A_Chassis_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
        },
        'C9400-SUP': {},
    },

}
