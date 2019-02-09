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
    # ------------------------------------------------------------------------------------------------------------------
    'ausapp-citp01': {
        'C9500': {
            'PCBP2': {
                'Station_A_04': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCB2C': {
                'Chamber_A_04': {
                    'Master1': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['1,2']},
                },
            },
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
}