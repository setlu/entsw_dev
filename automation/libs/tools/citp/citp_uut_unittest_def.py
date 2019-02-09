"""
=============================
CITP UUT Unittest Definitions
=============================

All UUTs allocated to automated regression testing of production code can be placed here.

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

__title__ = 'CITP UUT Unittest Definitions'
__author__ = ['bborel']
__version__ = '2.0.0'

mode = 'DEBUG'
citp_uuts = {

    # Please use the <repo>/tests/gold_uuts_def.py modules per the product space repo.
}
