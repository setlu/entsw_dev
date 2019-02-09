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
        'C3650': {
            'PCBST': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT06': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15127-05 A0', 'FDO173217Q2', 'A62345678', 'NONE', 'NO']},
                    'UUT07': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15775-03 A0', 'FDO17331ALT', 'A72345678', 'NONE', 'NO']},
                    'UUT08': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT09': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT10': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT11': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT12': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT13': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15898-05 02', 'FDO18480EVE', 'A14345678', 'NONE', 'NO']},
                    'UUT14': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15894-05 A0', 'FDO1852188X', 'A15345678', '73-14095-01', 'FDO141234567', 'NO']},
                    'UUT15': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15900-04 02', 'FDO184801U0', 'A15345678', 'NONE', 'NO']},
                    'UUT16': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
        },
        'C3850': {
            'DBGSYS': {
                'Station_A_01': {
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCBST': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-16622-03 03', 'FOC19160UJJ', 'A22345678', 'NO']},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-14445-06 A0', 'FOC18498NCD', 'A32345678', 'NONE', 'NO']},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-14441-06 A0', 'FHH16360011', 'A42345678', '73-14095-01 08', 'FOC16342HJV', 'NO']},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15804-04 03', 'FOC18476XYK', 'A52345678', '73-16123-02 02', 'FOC18476A2F', 'NO']},
                    'UUT06': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT07': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT08': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15799-07 A0', 'FOC18476XXS', 'A82345678', '73-16123-02 02', 'FOC18476A31', '73-16123-02 02', 'FOC18476A2R', 'NO']},
                    'UUT09': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-15756-05 A0', 'FOC193366L2', 'A92345678', '73-16123-02 A0', 'FOC19326Q15', 'NONE', 'NO']},
                    'UUT10': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-16296-07 A0', 'FOC184769P5', 'A10345678', 'NO']},
                    'UUT11': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-16285-04 05', 'FOC19120N56', 'A11345678', 'NO']},
                    'UUT12': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-16649-03 03', 'FOC18472NN5', 'A01234567', 'NO']},
                    'UUT13': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT14': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT15': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT16': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'PCB2C': {
                'Chamber_A_01': {
                    # 09: CMPD fails> MODEL_VERSION = Pilot
                    'Master1': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 20000, 'answers': ['GEN2', '2,3,5,7-8,10-12,15']},
                },
            },
            'ASSY': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3850-24S', '73-14445-06 A0', 'FOC18498NCD', 'A32345678', '800-41087-05 C0', 'FOC18508DNS', '73-11956-08 B0', 'FOC18498BQW', '73-16576-02 A0', 'Manual Scan/Enter', 'FOC1851X13Y']},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3850-24U', '73-15804-04 03', 'FOC18476XYK', 'A52345678', '800-43052-01 A0', 'FOC18481N4X', '73-11956-08 B0', 'FOC18457VY9', '73-16576-01 A0', 'Manual Scan/Enter', 'FOC1849V00R']},
                    'UUT06': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3650-24TS', '73-15127-05 A0', 'FDO173217Q2', 'A62345678', '800-39319-01 A0', 'NONE', 'FOC10000001', '73-16576-01 A0', 'Manual Scan/Enter', 'FDO1733Q017']},
                    'UUT07': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3650-48TQ', '73-15775-03 A0', 'FDO17331ALT', 'A72345678', '800-40912-01 A0', 'NONE', 'FOC10000002', '73-16576-01 A0', 'Manual Scan/Enter', 'FDO1734Q003']},
                    'UUT08': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3850-48U', '73-15799-07 A0', 'FOC18476XXS', 'A82345678', '800-43050-01 A0', 'FOC184832CL', '73-11956-08 B0', 'FOC18457W04', '73-16576-01 A0', 'Manual Scan/Enter', 'FOC1849V03S']},
                    'UUT09': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT10': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3850-48T', '73-16296-07 A0', 'FOC184769P5', 'A10345678', '800-43043-01 A0', 'FOC18481MYN', '73-11956-08 B0', 'FOC18457W03', '73-16576-01 A0', 'Manual Scan/Enter', 'FOC1849V00N']},
                    'UUT11': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['WS-C3850-12XS', '73-16285-04 05', 'FOC19120N56', 'A11345678', '68-5292-01 A0', 'FOC19131MSU', '73-11956-08 B0', 'FOC19133SV8', '73-16167-02 A0', 'Manual Scan/Enter', 'FOC1913X14C']},
                    'UUT12': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT13': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT14': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT15': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT16': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},

                },
            },
            'SYSBI': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['no']},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT06': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['no']},
                    'UUT07': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['no']},
                    'UUT08': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT09': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT10': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT11': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['no']},
                    'UUT12': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT13': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT14': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT15': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT16': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['no']},
                },
            },
        },
        'C9300': {
            'PCBST': {
                'Station_A_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-17954-05 05', 'FOC21094MWR', 'A16345678', '73-16123-03 A0', 'FOC21083X9C', 'NO']},
                },
                'Station_A_02': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-17954-05 05', 'FOC21094MW5', 'B12345678', '73-16123-03 A0', 'FOC21083WR6', 'NONE', 'NO']},
                },
                'Station_A_03': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-18506-02 05', 'FOC213901TB', 'B12345678', '73-16123-03 A0', 'FOC21387L7M', '73-16123-03 A0', 'FOC21387L7L', 'NONE', 'NO']},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-17959-06 05', 'FOC21260XVF', 'B22345678', '73-16123-03 A0', 'FOC21262D8Y', '73-16123-03 A0', 'FOC21262D91', 'NONE', 'NO']},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-17958-06 A0', 'FOC21319TC7', 'B32345678', '73-16123-03 A0', 'TST50000011', 'NONE', 'NO']},
                    'UUT04': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-18274-03 05', 'FOC21376DU1', 'B42345678', '73-16439-02 A0', 'FOC21374QWN', '73-16439-02 A0', 'FOC21374QWQ', 'NONE', 'NO']},
                    'UUT05': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-17957-06 05', 'FOC21094MTH', 'B52345678', '73-16123-03 A0', 'FOC21083XCQ', '73-16123-03 A0', 'FOC21083YQG', 'NONE', 'NO']},
                },
            },
            'PCB2C': {
                'Chamber_A_03': {
                    # 02: STARDUST fails> Segmentation fault (intermittent)
                    'Master1': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 20000, 'answers': ['1,3-5']},
                },
            },
            'ASSY': {
                'Station_A_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-24U', '73-17954-05 05', 'FOC21094MWR', 'A16345678', '68-5994-01 35', 'NONE', 'FOC21104W9Z', '73-11956-08 B0', 'FOC21104P32', '73-16167-02 A0', 'Manual Scan/Enter', 'FCW2111G01L']},
                },
                'Station_A_03': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-48UN', '73-18506-02 05', 'FOC213901TB', 'B12345678', '68-101202-01 25', 'NONE', '73-11956-08 B0', 'FOC21421JBX', '73-16167-02 A0', 'FOC2139494L', 'Manual Scan/Enter', 'FCW2143L019']},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-48UXM', '73-17959-06 05', 'FOC21260XVF', 'B22345678', '68-100712-01 46', 'NONE', '73-11956-08 B0', 'FOC2129398D', '73-16167-02 A0', 'FOC2129060G', 'Manual Scan/Enter', 'FCW2130G0NH']},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-24UX', '73-17958-06 A0', 'FOC21319TC7', 'B32345678', '68-100711-01 A0', 'NONE', '73-11956-08 B0', 'TST50000012', '73-16167-02 A0', 'TST50000013', 'Manual Scan/Enter', 'FCW2134L0RN']},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-48P', '73-18274-03 05', 'FOC21376DU1', 'B42345678', '68-101192-01 20', 'NONE', '73-11956-08 B0', 'FOC21390BSV', '73-16167-02 A0', 'FOC21383M3F', 'Manual Scan/Enter', 'FCW2141L042']},
                    'UUT05': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['C9300-48U', '73-17957-06 05', 'FOC21094MTH', 'B52345678', '68-5995-01 37', 'NONE', '73-11956-08 B0', 'FOC21106HK5', '73-16167-02 A0', 'FOC21113QVD', 'Manual Scan/Enter', 'FCW2112G040']},
                },
            },
            'SYSBI': {
                'Station_A_03': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT05': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
        },
        'C9300L': {
            'PCBST': {
                'Station_A_03': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19171-01 05', 'FOC1114567L', 'A42345679', '73-16123-03 A0', 'FOC323456PL', 'NONE', 'YES']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19177-01 04', 'FOC2224567L', 'A22345679', '73-16123-03 A0', 'FOC12345PPL', '73-16123-03 A0', 'FOC22345PPL', 'NONE', 'NO']},
                    # 'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19176-02 03', 'FOC22204U8Q', 'A32345679', '73-16167-02 A0', 'FOC222043T5', '73-16167-02 A0', 'FOC222043T3', 'NONE', 'NO']},
                    # 'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19102-02 01', 'FOC22345678', 'A12345679', '73-16123-03 A0', 'FOC22345677', '73-16123-03 A0', 'FOC22345676', 'NONE', 'NO']},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19176-03 10', 'FOC22381281', 'A12345679', '73-16123-03 A0', 'FOC2238327F', '73-16123-03 A0', 'FOC2238327G', 'NO']},
                },
            },
            'PCB2C': {
                'Chamber_A_03': {
                    'Master1': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['1,2']},
                },
            },
            'PCBASSY': {
                'Station_A_03': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},  # 'FOC123456AX']},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'SYSBI': {
                'Station_A_03': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
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

    # CISCO - San Jose (CITP & Lab)
    # ------------------------------------------------------------------------------------------------------------------
    'sjc18app-lab2': {
        'C9300': {},
        'C9300L': {
            'PCBST': {
                'StationPoE_A_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000,
                              'answers': ['73-19177-03 09', 'FJZ224305J2', 'S12345679', '73-16123-03 A0', 'FOC22310X0X', '73-16123-03 A0', 'FOC22310TRW', 'NONE', 'YES']},
                },
                'Station_A_02': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT02': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT03': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                    'UUT04': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                }
            },
            'PCB2C': {
                'Chamber_A_01': {
                    'Master1': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['1,2']},
                },
            },
            'ASSY': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },
            'SYSBI': {
                'Station_A_01': {
                    'UUT01': {'enabled': False, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': []},
                },
            },

        },
    },

    # FOC - Foxconn-Shenzhen (Development)
    # ------------------------------------------------------------------------------------------------------------------
    'fxcavp86': {
        'C9300L': {
            'PCBST': {
                'Station_A_01': {
                    'UUT01': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19130-03 07', 'FOC22414XNS', 'SKIP', '73-16439-02 A0', 'FOC224147GD', '73-16439-02 A0', 'FOC224146R1', 'NONE', 'YES']},
                    'UUT02': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19169-02 07', 'FOC22371M36', 'SKIP', '73-16439-02 A0', 'FOC22366J1J', 'NONE', 'YES']},
                    'UUT03': {'enabled': True, 'mode': mode, 'start_delay': 1, 'timeout': 10000, 'answers': ['73-19130-03 07', 'FOC223717NU', 'SKIP', '73-16439-02 A0', 'FOC22361TRM', '73-16439-02 A0', 'FOC22361TQT', 'NONE', 'YES']},
                    'UUT04': {},
                    'UUT05': {},
                },
            },
        },
    },

    # FJZ - Foxconn-Juarez (Development)
    # ------------------------------------------------------------------------------------------------------------------
    'fjzavp1': {
    },
    'fjzavp2': {
    },

}