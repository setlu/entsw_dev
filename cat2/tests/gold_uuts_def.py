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
        'C9200': {
            'PCBP2': {
                'Station_A_02': {
                    # 'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9200-24P-4X', '73-18699-01 10', 'JAE21290EJ4', '68-101386-01 01', 'JAE21290EJ5', 'C12345678', 'NONE', '73-18831-01 A0', 'TST00000QP1', '73-18785-01 A0', 'TST00000QU1', 'NO']},
                    # 'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9200R-24P', '73-18793-01 04', 'JAE213902Z7', '68-101488-01 01', 'JAE213902Z8', 'C12345678', 'NONE', '73-18831-01 A0', 'TST20000QP1', '73-18785-01 A0', 'TST20000QU1', 'NO']},
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCB2C': {},
            'SYSFT': {},
        },
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
    'sjc18app-lab1': {
        'C2960': {},
        'C9200': {
            'PCBP2': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCBPM': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCB2C': {
                'Chamber_A_01': {
                    'Master1': {},
                },
            },
            'PCBFT': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
        },
    },
    'sjc18app-lab2': {
        'C2960': {},
        'C9200': {},
    },
    'sjc18app-lab3': {
        'C2960': {},
        'C9200': {},
    },
    'sjc18app-lab4': {
        'C2960': {},
        'C9200': {},
    },

    # JPE - Jabil-Penang (Development)
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    'jpeavp140': {
        'C9200': {
            'PCBP2': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCBPM': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCB2C': {
                'Chamber_A_01': {
                    'Master1': {},
                },
            },
            'PCBFT': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
        },

    },

    # JMX - Jabil-Mexico (Development)
    # ----------------------------------------------------------------------------------------------------------------------------------------------------------
    'jmxavp101': {
        'C9200': {
            'PCBP2': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCBPM': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
            'PCB2C': {
                'Chamber_A_01': {
                    'Master1': {},
                },
            },
            'PCBFT': {
                'Station_A_01': {
                    'UUT01': {},
                },
            },
        },

    },

}
