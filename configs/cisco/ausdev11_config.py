"""
Enterprise Switching Config File (Austin Lab)
---------------------------------------------
Host: ausdev11
Primary IP   (eth0): 10.89.133.11
Secondary IP (eth1): 10.1.1.2
CIMC IP: 10.89.133.52

Description:
This is the Apollo server configuration file for Enterprise Switching products.
The file is designed as an example template of how to setup various product families and their associated test
stations using only dictionaries and lists.

Design Philosophy:
The current structure of Apollo _config.py files is extremely flexible allowing for a variety of
coding solutions test engineers can implement to accomplish their station deployments.
The approach taken here attempts to combine the best of the following schemes:
  1. flexibility to accommodate all features and a broad spectrum of needs,
  2. explicit assignment of configurations for clarity,
  3. strict use of dictionaries & lists for a singular approach to managing all data,
  4. naming conventions for consistency and algorithmic requirement.

All aspects of a Business Unit's product line that the Apollo server could support are created in 3 entities:
    1. Product Families- UUTs (PIDs/CPNs) w/ Test Areas    (uut_map)
    2. Sequences                                           (seq_map)
    3. Stations/Connections                                (station_conn_map)
       a. holds Containers & their Connections
     These entities are either lists or dictionaries (see the example given below).

    Once the 3 items above are created, it is just a matter of calling the single build function:
    build_product_line_configurations(uut_map, sequence_map, connection_map)

"""
from apollo.config.config_builder import cdict
from apollo.libs import lib
import config_builder


__version__    = "0.0.3"
__title__      = "Enterprise Switching (a.k.a. UABU, UAG, ESTG, DSBU) Config"
__author__     = 'bborel'
__credits__    = ["UAT Team"]


def austin_lab_config():
    """ Austin dev lab Config

    Production line: LAB
    Area: SYSFT
    Testers: Add separate functions for specific platform testing.
    Pre-sequence: See tools/citp/presequence.py; has a single pid-container map for automatic testing without parameter input.
    If needed the user can override this at any level.
    """

    apollo_config = lib.get_station_configuration()
    pl = apollo_config.add_production_line(name='CITP-USTX')
    # default pre sequence, expects a single PID/container
    pl.assign_pre_sequence('apollo.scripts.entsw.tools.citp.presequence.single_pid')
    area = pl.add_area(name='SYSFT')

    # add configs here
    # -------------------------
    hello_world_tester(area)
    uabu_cfg()
    return


def hello_world_tester(area):
    """ Hello World Tester
    Configure for hellow world test.
    :param area:
    :return:
    """
    ts = area.add_test_station(name='HELLOWORLD')
    ct = ts.add_container(name="HELLOWORLD")
    ct.add_pid_map(pid='HELLOWORLD', sequence_definition='apollo.scripts.entsw.tools.helloworld.helloworld.seq')
    return


def uabu_cfg():
    """Hierarchy for setup:
    LINE (product_line)
        AREA (test_area) <-- set of UUT PIDs/CPNs for a given test area (a.k.a. "genarea")
            STATION (test_station)  <-- set of Containers with connections (i.e. a "test station" or a "test rack")
                CONTAINERS  <-- UUT automation entity (can contain multiple connections to various equipment)
                    Connections
            STATION
                SUPER CONTAINER  <-- Master container for container grouping and control
                    CONTAINERS
                        Connections
                    CONTAINERS
                        Connections
    UUT PIDs/CPNs + Sequences can be mapped at any hierarchal level from AREA downward.
    Pre-Sequences can be mapped at ANY level (not shown).
    Connections can be mapped at ANY level.
    Lower levels have precedence for identically mapped items.
    """

    # ------------------------------------------------------------------------------------------------------------------
    # PRODUCT LINES: Enterprise Switching
    #
    #
    #
    # UUT MAP
    # -------
    # ProductLine-->ProductFamily-->UUT PID/CPN and TestArea association
    # UUT PIDs & CPNs associated with a product line+family and the testareas for those UUT PIDs/CPNs are defined here.
    # Depending on testarea a specific UUT identifier is used with the product family: BasePID, PID, 73CPN, or 800CPN.
    # Each product family's UUT PID/CPN that is used in mfg should be added to the appropriate identifier.
    # All testareas that require the specific PID or CPN is listed as part of the tuple value and should collectively
    # identify all testareas for that product line/family.
    # Nested Dict format = {
    # '<product_line>': {
    #   '<product_family>': {
    #     '<identifier>': (['<area1>', '<area2>', ...], ['<uut_type1>', '<uut_type2>', ...]), ...},...},...}
    uut_map = {
        'C3K': {
            'test': {
                'PID':       (['PCBST', 'ASSY', 'PCBFT',
                               'SYSBI', 'SYSFT'],   ['WS-CTEST-0', 'WS-CTEST-1']),
            },
            'EngUtility': {
                'BasePID':   (['DBGSYS'],        ['WS-C3850-12XS', 'WS-C3850-24XS', 'WS-C3850-48XS',                    # Gladiator
                                                  'WS-C3850-24T', 'WS-C3850-24P', 'WS-C3850-24U',                       # Edison-Newton
                                                  'WS-C3850-48T', 'WS-C3850-48P', 'WS-C3850-48U',                       # Edison-Newton
                                                  'WS-C3850X-24T', 'WS-C3850X-24P', 'WS-C3850X-24U',                    # Nyquist
                                                  'WS-C3850X-48T', 'WS-C3850X-48P', 'WS-C3850X-48U',                    # Nyquist
                                                  'WS-C3850X-24X', 'WS-C3850-12X48U',                                   # Orsted
                                                  'WS-C3850-12S', 'WS-C3850-24S',                                       # Planck
                                                  'WS-C3650-24TS', 'WS-C3650-24PS', 'WS-C3650-48TS', 'WS-C3650-48PS',   # Archimedes
                                                  'WS-C3650-24TD', 'WS-C3650-24PD', 'WS-C3650-48TD', 'WS-C3650-48PD',   # Archimedes
                                                  'WS-C3650-48TQ', 'WS-C3650-48PQ',                                     # Archimedes
                                                  'WS-C3850-8X24UQ', 'WS-C3850-8X24PD',                                 # Euclid
                                                  'WS-C3850-12X48UQ', 'WS-C3850-12X48FD',                               # Euclid
                                                  'WS-C3850-12X48UR', 'WS-C3850-12X48UZ',                               # Euclid
                                                  'WS-C3850-24PDM', 'WS-C3850-48PQM',                                   # Theon
                                                  ]),
            },
            'NewtonCR': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-14443-*', '73-14441-*', '73-14984-*', '73-14444-*',
                                                     '73-14442-*', '73-14983-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850-24', 'WS-C3850-48', 'WS-C3850-24P', 'WS-C3850-48P']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850-24-L', 'WS-C3850-48-S', 'WS-C3850-24P-E', 'WS-C3850-48P-L']),
                '800CPN':    (['SYSFQA'],           ['800-nnnn1-01', '800-nnnn1-02', '800-nnnn1-03']),
            },
            'NewtonCSR': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-16297-*', '73-15805-*', '73-15804-*',
                                                     '73-16296-*', '73-15800-*', '73-15799-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850-24', 'WS-C3850-48', 'WS-C3850-24P', 'WS-C3850-48P']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850-24-L', 'WS-C3850-48-S', 'WS-C3850-24P-E', 'WS-C3850-48P-L']),
                '800CPN':    (['SYSFQA'],           ['800-nnnn1-01', '800-nnnn1-02', '800-nnnn1-03']),
            },
            'PlanckCR': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-15839-*', '73-14445-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850-12S', 'WS-C3850-24S']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850-12S-E', 'WS-C3850-24S-E']),
                '800CPN':    (['SYSFQA'],           ['800-pppp1-01', '800-pppp1-02']),
            },
            'Gladiator': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-16285-*', '73-16649-*', '73-16622-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850-12X', 'WS-C3850-24X', 'WS-C3850-48X']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850-12X-E', 'WS-C3850-24X-E', 'WS-C3850-48X-E',
                                                     'WS-C3850-12X-S', 'WS-C3850-24X-S', 'WS-C3850-48X-S']),
                '800CPN':    (['SYSFQA'],           ['800-gggg1-01', '800-gggg1-02']),
            },
            'Orsted': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-15756-*', '73-15755-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850-24E', 'WS-C3850-48E']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850-24E-S', 'WS-C3850-48E-E']),
                '800CPN':    (['SYSFQA'],           ['800-oooo1-01', '800-oooo1-02']),
            },
            'ArchimedesCR': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-15127-*', '73-15128-*', '73-15130-*', '73-15131-*',
                                                     '73-15121-*', '73-15122-*', '73-15124-*', '73-15125-*',
                                                     '73-15775-*', '73-15776-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3650-24TS', 'WS-C3650-24PS', 'WS-C3650-48TS', 'WS-C3650-48PS',
                                                     'WS-C3650-24TD', 'WS-C3650-24PD', 'WS-C3650-48TD', 'WS-C3650-48PD']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3650-24TS-L', 'WS-C3650-24TS-E', 'WS-C3650-24TS-S',
                                                     'WS-C3650-24PS-L', 'WS-C3650-24PS-E', 'WS-C3650-24PS-S', 'WS-C3650-24PWS-S',
                                                     'WS-C3650-48TS-L', 'WS-C3650-48TS-E', 'WS-C3650-48TS-S',
                                                     'WS-C3650-48PS-L', 'WS-C3650-48PS-E', 'WS-C3650-48PS-S',
                                                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWS-S',
                                                     'WS-C3650-24TD-L', 'WS-C3650-24TD-E', 'WS-C3650-24TD-S',
                                                     'WS-C3650-24PD-L', 'WS-C3650-24PD-E', 'WS-C3650-24PD-S', 'WS-C3650-24PWD-S',
                                                     'WS-C3650-48TD-L', 'WS-C3650-48TD-E', 'WS-C3650-48TD-S',
                                                     'WS-C3650-48PD-L', 'WS-C3650-48PD-E', 'WS-C3650-48PD-S',
                                                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWD-S',
                                                     'WS-C3650-48TQ-L', 'WS-C3650-48TQ-E', 'WS-C3650-48TQ-S',
                                                     'WS-C3650-48PQ-L', 'WS-C3650-48PQ-E', 'WS-C3650-48PQ-S',
                                                     'WS-C3650-48FQ-L', 'WS-C3650-48FQ-E', 'WS-C3650-48FQ-S', 'WS-C3650-48FWQ-S']),
                '800CPN':    (['SYSFQA'],           ['800-aaaa1-01', '800-aaaa1-02']),
            },
            'ArchimedesCSR': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-15898-*', '73-15899-*', '73-15900-*', '73-15901-*',
                                                     '73-15895-*', '73-15894-*', '73-15896-*', '73-15897-*',
                                                     '73-15902-*', '73-15903-*']),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3650-24TS', 'WS-C3650-24PS', 'WS-C3650-48TS', 'WS-C3650-48PS',
                                                     'WS-C3650-24TD', 'WS-C3650-24PD', 'WS-C3650-48TD', 'WS-C3650-48PD']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3650-24TS-L', 'WS-C3650-24TS-E', 'WS-C3650-24TS-S',
                                                     'WS-C3650-24PS-L', 'WS-C3650-24PS-E', 'WS-C3650-24PS-S', 'WS-C3650-24PWS-S',
                                                     'WS-C3650-48TS-L', 'WS-C3650-48TS-E', 'WS-C3650-48TS-S',
                                                     'WS-C3650-48PS-L', 'WS-C3650-48PS-E', 'WS-C3650-48PS-S',
                                                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWS-S',
                                                     'WS-C3650-24TD-L', 'WS-C3650-24TD-E', 'WS-C3650-24TD-S',
                                                     'WS-C3650-24PD-L', 'WS-C3650-24PD-E', 'WS-C3650-24PD-S', 'WS-C3650-24PWD-S',
                                                     'WS-C3650-48TD-L', 'WS-C3650-48TD-E', 'WS-C3650-48TD-S',
                                                     'WS-C3650-48PD-L', 'WS-C3650-48PD-E', 'WS-C3650-48PD-S',
                                                     'WS-C3650-48FS-L', 'WS-C3650-48FS-E', 'WS-C3650-48FS-S', 'WS-C3650-48FWD-S',
                                                     'WS-C3650-48TQ-L', 'WS-C3650-48TQ-E', 'WS-C3650-48TQ-S',
                                                     'WS-C3650-48PQ-L', 'WS-C3650-48PQ-E', 'WS-C3650-48PQ-S',
                                                     'WS-C3650-48FQ-L', 'WS-C3650-48FQ-E', 'WS-C3650-48FQ-S', 'WS-C3650-48FWQ-S']),
                '800CPN':    (['SYSFQA'],           ['800-aaaa1-01', '800-aaaa1-02']),
            },
            'Nyquist': {
                '73CPN':     (['PCBST', 'PCB2C'],   ['73-17952-*', '73-17955-*', '73-17953-*',                       # Nyquist-Shannon24
                                                     '73-17956-*', '73-17954-*', '73-17957-*',                       # Nyquist-Shannon48
                                                     '73-17958-*', '73-17959-*',                                      # Nyquist-Hartley
                                                     ]),
                'BasePID':   (['ASSY', 'PCBFT'],    ['WS-C3850X-24T', 'WS-C3850X-24P', 'WS-C3850X-24U',
                                                     'WS-C3850X-48T', 'WS-C3850X-48P', 'WS-C3850X-48U']),
                'PID':       (['SYSINT', 'SYSFT'],  ['WS-C3850X-24T-L', 'WS-C3850X-24T-E', 'WS-C3850X-24T-S',
                                                     'WS-C3850X-48T-L', 'WS-C3850X-48T-E', 'WS-C3850X-48T-S']),
                '800CPN':    (['SYSFQA'],           ['800-yyyy1-01', '800-yyyy1-02']),
            },
            'Uplink': {
                'PID':        (['PCBST'],            ['TEST2']),
            }
        },
    }

    #
    # SEQUENCES
    # ---------
    # Specify where the sequences are to be placed; most levels are valid. (Lower levels take precedence.)
    # Valid level hierarchy: LINE+FAMILY|AREA|STATION|SUPERCONTAINER|CONTAINER|(preseq or seq)
    # This inherently defines which objects the "add_pid_map()" or "assign_pre_sequence()" methods are called from.
    # CONVENTION: "line|family" is consider a single entity and is used as the "product_line" wrt the Apollo _config.py.
    # CONVENTION: All UUTs for a given "chain" will be mapped to the given sequence for the AREA specified in the chain.
    #
    # line|seq --> NOT ALLOWED
    # line|family|seq --> NOT ALLOWED
    # line|family|area|seq  --> ar.add_pid_map()
    # line|family|area|station|seq  --> ts.add_pid_map()
    # line|family|area|station|container|seq  --> cont.add_pid_map()
    # line|preseq --> NOT ALLOWED
    # line|family|preseq --> pl.assign_pre_sequence()
    # line|family|area|preseq  --> ar.assign_pre_sequence()
    # line|family|area|station|preseq  --> ts.assign_pre_sequence()
    # line|family|area|station|container|preseq  --> cont.assign_pre_sequence()
    # NOTE: KEEP ASSIGNMENTS EXPLICIT (as much as possible).
    #
    sequence_map = {
        'C3K|test|preseq':                           'apollo.scripts.examples.pre_sequence.discover',
        'C3K|test|PCBST|seq':                        'apollo.scripts.examples.helloworld.helloworld_ui',
        'C3K|test|ASSY|seq':                         'apollo.scripts.examples.helloworld.helloworld_ui',
        'C3K|test|SYSBI|seq':                        'apollo.scripts.examples.asking_questions.asking_question',
        'C3K|test|SYSFT|seq':                        'apollo.scripts.examples.asking_questions.asking_question',

        'C3K|EngUtility|DBGSYS|preseq':              'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_eng_utility',
        'C3K|EngUtility|DBGSYS|seq':                 'apollo.scripts.entsw.cat3.area_sequences.c3k_eng_menu_run.eng_utility_menu',

        'C3K|Newton|PCBST|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Newton|PCBST|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Newton|PCBST|Station_A_1|preseq':       'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Newton|PCBST|Station_A_1|seq':          'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Newton|PCBST|Station_A_1|UUT01|preseq': 'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Newton|PCBST|Station_A_1|UUT01|seq':    'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Newton|PCBST|Station_A_1|UUT02|preseq': 'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Newton|PCBST|Station_A_1|UUT02|seq':    'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Newton|PCBST|Station_A_1|UUT03|preseq': 'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Newton|PCBST|Station_A_1|UUT03|seq':    'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',

        'C3K|Newton|PCB2C|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Newton|PCB2C|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Newton|ASSY|preseq':                    'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Newton|ASSY|seq':                       'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Newton|PCBFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Newton|PCBFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Newton|SYSFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Newton|SYSFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Planck|PCBST|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Planck|PCBST|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Planck|PCB2C|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Planck|PCB2C|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Planck|ASSY|preseq':                    'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Planck|ASSY|seq':                       'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Planck|PCBFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Planck|PCBFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Planck|SYSFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Planck|SYSFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Gladiator|PCBST|preseq':                'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Gladiator|PCBST|seq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Gladiator|PCB2C|preseq':                'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Gladiator|PCB2C|seq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Gladiator|ASSY|preseq':                 'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Gladiator|ASSY|seq':                    'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Gladiator|PCBFT|preseq':                'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Gladiator|PCBFT|seq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Gladiator|SYSFT|preseq':                'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Gladiator|SYSFT|seq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Orsted|PCBST|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Orsted|PCBST|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Orsted|PCB2C|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Orsted|PCB2C|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Orsted|ASSY|preseq':                    'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Orsted|ASSY|seq':                       'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Orsted|PCBFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Orsted|PCBFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Orsted|SYSFT|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Orsted|SYSFT|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Archimedes|PCBST|preseq':               'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst',
        'C3K|Archimedes|PCBST|seq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
        'C3K|Archimedes|PCB2C|preseq':               'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Archimedes|PCB2C|seq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Archimedes|ASSY|preseq':                'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Archimedes|ASSY|seq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Archimedes|PCBFT|preseq':               'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Archimedes|PCBFT|seq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Archimedes|SYSFT|preseq':               'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Archimedes|SYSFT|seq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Nyquist|PCB2C|preseq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcb2c',
        'C3K|Nyquist|PCB2C|seq':                     'apollo.scripts.entsw.cat3.area_sequences.c3k_pcb2c_run.standard_switch',
        'C3K|Nyquist|ASSY|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_assy',
        'C3K|Nyquist|ASSY|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_assy_run.standard_switch',
        'C3K|Nyquist|PCBFT|preseq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbft',
        'C3K|Nyquist|PCBFT|seq':                     'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbft_run.standard_switch',
        'C3K|Nyquist|SYSFT|preseq':                  'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_sysft',
        'C3K|Nyquist|SYSFT|seq':                     'apollo.scripts.entsw.cat3.area_sequences.c3k_sysft_run.standard_switch',

        'C3K|Uplink|PCBST|preseq':                   'apollo.scripts.entsw.cat3.area_sequences.c3k_all_pre_sequences.pre_pcbst_uplink',
        'C3K|Uplink|PCBST|seq':                      'apollo.scripts.entsw.cat3.area_sequences.c3k_pcbst_run.standard_switch',
    }

    #
    # Auxiliary Connections
    # ---------------------
    # Dict of supplemental connections for containers; typically shared connections.
    aux_connections = {
        'serverSSH_1':  dict(protocol='ssh', host='10.89.133.11', user='root', password='cisco123')
    }

    #
    # STATIONS and CONNECTIONS
    # ------------------------
    # Specify the Stations and their containers.
    # Specify where the Connections are to be placed; all levels are valid. (Lower levels take precedence.)
    # Valid level hierarchy: LINE+FAMILY|AREA|STATION|SUPERCONTAINER|CONTAINER.
    # This inherently defines which objects the "add_connection()" method is called from.
    # Note: "line|family" is considered a single entity and is used as the "product_line" wrt the Apollo _config.py
    # Invoked method examples (reference only):
    # line --> NOT ALLOWED
    # line|family --> pl.add_connection()
    # line|family|area  --> ar.add_connection()
    # line|family|area|station  --> ts.add_connection()
    # line|family|area|station|container --> cont.add_connection()
    # line|family|area|station|syncgrp --> ts.add_sync_group()
    # line|family|area|station|supercontainer --> sc.add_connection()
    # line|family|area|station|supercontainer|container --> cont.add_connection()
    #
    # CONVENTION: ALL Supercontainers must contain the label "Master" (case insensitive).
    # CONVENTION: ALL Sync groups must contain the label "Sync" (case insensitive).
    # CONVENTION: ALL Power groups must contain the label "Power" (case insensitive).  *** TBD **
    # CONVENTION: All Areas that are shared must contain the label "Composite".
    # Connections can be either 1) dicts or 2) string reference to another "line|family" to duplicate.
    #
    # NOTE: KEEP ASSIGNMENTS EXPLICIT (as much as possible).
    #
    station_and_connection_map = {
        'C3K|test':                                    {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|test|Composite1':                         ['SYSBI', 'SYSFT'],
        'C3K|test|Composite2':                         ['PCBST', 'ASSY'],
        'C3K|test|SYSBI|Station_T':                    {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|test|PCBST|Station_T':                    {'serverSSH': {'shared_conn': 'shareSSH'}},

        # BST Station --------------------------------------------------------------------------------------------------

        'C3K|Newton':                                  {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|Newton|PCBST':                            {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1':                {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT01':          {'uutTN': cdict('telnet', '10.89.133.9', 2003, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT02':          {'uutTN': cdict('telnet', '10.89.133.9', 2004, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT03':          {'uutTN': cdict('telnet', '10.89.133.9', 2005, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT04':          {'uutTN': cdict('telnet', '10.89.133.9', 2006, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT05':          {'uutTN': cdict('telnet', '10.89.133.9', 2007, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT06':          {'uutTN': cdict('telnet', '10.89.133.9', 2008, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT07':          {'uutTN': cdict('telnet', '10.89.133.9', 2009, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT08':          {'uutTN': cdict('telnet', '10.89.133.9', 2010, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT09':          {'uutTN': cdict('telnet', '10.89.133.9', 2011, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT10':          {'uutTN': cdict('telnet', '10.89.133.9', 2012, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT11':          {'uutTN': cdict('telnet', '10.89.133.9', 2013, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT12':          {'uutTN': cdict('telnet', '10.89.133.9', 2014, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT13':          {'uutTN': cdict('telnet', '10.89.133.9', 2015, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT14':          {'uutTN': cdict('telnet', '10.89.133.9', 2016, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT15':          {'uutTN': cdict('telnet', '10.89.133.9', 2017, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_A_1|UUT16':          {'uutTN': cdict('telnet', '10.89.133.9', 2018, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},

        'C3K|Newton|PCBST|Station_B_1':                {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_B_1|UUT01':          {'uutTN': cdict('telnet', '10.89.133.8', 2003, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_B_1|UUT02':          {'uutTN': cdict('telnet', '10.89.133.8', 2004, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCBST|Station_B_1|UUT03':          {'uutTN': cdict('telnet', '10.89.133.8', 2005, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},

        'C3K|Planck':                                  {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|Planck|PCBST|Station_A_1|UUT01':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT02':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT03':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT04':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT05':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT06':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT07':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT08':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT09':          'C3K|Newton',
        'C3K|Planck|PCBST|Station_A_1|UUT10':          'C3K|Newton',

        'C3K|Gladiator':                               {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|Gladiator|PCBST|Station_A_1|UUT01':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT02':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT03':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT04':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT05':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT06':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT07':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT08':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT09':       'C3K|Newton',
        'C3K|Gladiator|PCBST|Station_A_1|UUT10':       'C3K|Newton',

        'C3K|Orsted':                                  {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|Orsted|PCBST|Station_A_1|UUT01':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT02':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT03':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT04':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT05':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT06':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT07':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT08':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT09':          'C3K|Newton',
        'C3K|Orsted|PCBST|Station_A_1|UUT10':          'C3K|Newton',

        'C3K|Archimedes':                               {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|Archimedes|PCBST':                         {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Archimedes|PCBST|Station_A_1':             {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Archimedes|PCBST|Station_A_1|UUT15':       {'uutTN': cdict('telnet', '10.89.133.9', 2017, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Archimedes|PCBST|Station_A_1|UUT16':       {'uutTN': cdict('telnet', '10.89.133.9', 2018, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},


        # 2C Station --------------------------------------------------------------------------------------------------

        'C3K|Newton|PCB2C|Station_A_1':                {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCB2C|Station_A_1|Master1':        {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT01':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT02':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT03':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT04':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT05':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT06':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT07':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT08':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT09':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT10':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT11':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT12':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT13':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT14':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT15':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Master1|UUT16':  'C3K|Newton',
        'C3K|Newton|PCB2C|Station_A_1|Sync1':          ['Master1|UUT01', 'Master1|UUT02', 'Master1|UUT03', 'Master1|UUT04',
                                                        'Master1|UUT05', 'Master1|UUT06', 'Master1|UUT07', 'Master1|UUT08',
                                                        'Master1|UUT09', 'Master1|UUT10', 'Master1|UUT11', 'Master1|UUT12',
                                                        'Master1|UUT13', 'Master1|UUT14', 'Master1|UUT15', 'Master1|UUT16'],

        'C3K|Planck|PCB2C|Station_A_1|UUT01':          'C3K|Newton',
        'C3K|Planck|PCB2C|Station_A_1|UUT02':          'C3K|Newton',
        'C3K|Planck|PCB2C|Station_A_1|UUT03':          'C3K|Newton',
        'C3K|Planck|PCB2C|Station_A_1|Sync1':          ['UUT01', 'UUT02'],

        # ASSY Station -------------------------------------------------------------------------------------------------

        'C3K|Newton|ASSY|Station_A_1|UUT01':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT02':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT03':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT04':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT05':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT06':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT07':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT08':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT09':          'C3K|Newton',
        'C3K|Newton|ASSY|Station_A_1|UUT10':          'C3K|Newton',

        # FST Station --------------------------------------------------------------------------------------------------

        'C3K|Newton|PCBFT|Station_A_1|UUT01':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT02':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT03':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT04':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT05':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT06':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT07':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT08':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT09':          'C3K|Newton',
        'C3K|Newton|PCBFT|Station_A_1|UUT10':          'C3K|Newton',

        # Eng Utility Menu ---------------------------------------------------------------------------------------------
        'C3K|EngUtility':                           {'shareSSH': aux_connections['serverSSH_1']},
        'C3K|EngUtility|DBGSYS':                    {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1':        {'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'sharePOELB_01': dict(protocol='telnet', host='10.89.133.8', port=2018, timeout=60, model='Edgar4', manufacturer='Reach')},
        'C3K|EngUtility|DBGSYS|Station_A_2':        {'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'sharePOELB_02': dict(protocol='telnet', host='10.89.133.8', port=2018, timeout=60, model='Edgar4', manufacturer='Reach')},

        # ENG1
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT01':  {'uutTN': cdict('telnet', '10.89.133.9', 2003, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1': {'shared_conn': 'sharePOELB_01'},
                                                     'POELB2': {'shared_conn': 'sharePOELB_01'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT02':  {'uutTN': cdict('telnet', '10.89.133.9', 2004, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1a': {'shared_conn': 'sharePOELB_01'},
                                                     'POELB1b': {'shared_conn': 'sharePOELB_01'},
                                                     'POELB2a': {'shared_conn': 'sharePOELB_01'},
                                                     'POELB2b': {'shared_conn': 'sharePOELB_01'},
                                                     },
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT03':  {'uutTN': cdict('telnet', '10.89.133.9', 2005, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT04':  {'uutTN': cdict('telnet', '10.89.133.9', 2006, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT05':  {'uutTN': cdict('telnet', '10.89.133.9', 2007, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT06':  {'uutTN': cdict('telnet', '10.89.133.9', 2008, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT07':  {'uutTN': cdict('telnet', '10.89.133.9', 2009, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT08':  {'uutTN': cdict('telnet', '10.89.133.9', 2010, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT09':  {'uutTN': cdict('telnet', '10.89.133.9', 2011, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT10':  {'uutTN': cdict('telnet', '10.89.133.9', 2012, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT11':  {'uutTN': cdict('telnet', '10.89.133.9', 2013, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT12':  {'uutTN': cdict('telnet', '10.89.133.9', 2014, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT13':  {'uutTN': cdict('telnet', '10.89.133.9', 2015, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT14':  {'uutTN': cdict('telnet', '10.89.133.9', 2016, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT15':  {'uutTN': cdict('telnet', '10.89.133.9', 2017, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1': {'shared_conn': 'sharePOELB_01'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|UUT16':  {'uutTN': cdict('telnet', '10.89.133.9', 2018, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1': {'shared_conn': 'sharePOELB_01'}},
        'C3K|EngUtility|DBGSYS|Station_A_1|PoESync1': ['UUT01', 'UUT02', 'UUT15', 'UUT16'],

        # ENG2
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT01':  {'uutTN': cdict('telnet', '10.89.133.8', 2003, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1': {'shared_conn': 'sharePOELB_02'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT02':  {'uutTN': cdict('telnet', '10.89.133.8', 2004, 60), 'serverSSH': {'shared_conn': 'shareSSH'},
                                                     'POELB1': {'shared_conn': 'sharePOELB_02'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT03':  {'uutTN': cdict('telnet', '10.89.133.8', 2005, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT04':  {'uutTN': cdict('telnet', '10.89.133.8', 2006, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT05':  {'uutTN': cdict('telnet', '10.89.133.8', 2007, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT06':  {'uutTN': cdict('telnet', '10.89.133.8', 2008, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT07':  {'uutTN': cdict('telnet', '10.89.133.8', 2009, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Station_A_2|UUT08':  {'uutTN': cdict('telnet', '10.89.133.8', 2010, 60), 'serverSSH': {'shared_conn': 'shareSSH'}},

        'C3K|EngUtility|DBGSYS|Phantom_Stn':        {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT01':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT02':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT03':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT04':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT05':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT06':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT07':  {'serverSSH': {'shared_conn': 'shareSSH'}},
        'C3K|EngUtility|DBGSYS|Phantom_Stn|UUT08':  {'serverSSH': {'shared_conn': 'shareSSH'}},
    }

    # CONFIGURATION DATA
    # Specify any custom configuration data.
    # Valid level hierarchy: LINE+FAMILY|AREA|STATION|SUPERCONTAINER|CONTAINER.
    # This inherently defines which objects the "add_configuration_data()" method is called from.
    # Note: "line|family" is considered a single entity and is used as the "product_line" wrt the Apollo _config.py
    # NOTE: KEEP ASSIGNMENTS EXPLICIT (as much as possible).
    cfg_data = {
        'C3K|Production-Sim|PCB2C|Station_A_1':  {'ChamberSync1': ['C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT01',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT02',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT03',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT04',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT05',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT06',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT07',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT08',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT09',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT10',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT11',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT12',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT13',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT14',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT15',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_1|Master1:UUT16']},

        'C3K|Production-Sim|PCB2C|Station_A_2':  {'ChamberSync2': ['C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT01',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT02',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT03',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT04',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT05',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT06',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT07',
                                                                   'C3K_Production-Sim|PCB2C|Station_A_2|Master1:UUT08']},

        'C3K|EngUtility|DBGSYS|Station_A_1': {'UUT01': {'POELB1':  {'portmap':  '1-12', 'syncgroup': 'PoESync1'},
                                                        'POELB2':  {'portmap':  '1-12', 'syncgroup': 'PoESync1'}},
                                              'UUT02': {'POELB1a': {'portmap':  '1-12', 'syncgroup': 'PoESync1'},
                                                        'POELB1b': {'portmap':  '1-12', 'syncgroup': 'PoESync1', 'pair': 'POELB1a'},
                                                        'POELB2a': {'portmap':  '1-12', 'syncgroup': 'PoESync1'},
                                                        'POELB2b': {'portmap':  '1-12', 'syncgroup': 'PoESync1', 'pair': 'POELB2a'}},
                                              'UUT15': {'POELB1':  {'portmap':  '1-24', 'syncgroup': 'PoESync1'}},
                                              'UUT16': {'POELB1':  {'portmap':  '1-24', 'syncgroup': 'PoESync1'}},
                                              },
        'C3K|EngUtility|DBGSYS|Station_A_2': {'UUT01': {'POELB1':  {'portmap':  '1-24', 'syncgroup': 'PoESync2'}},
                                              'UUT02': {'POELB1':  {'portmap':  '1-24', 'syncgroup': 'PoESync2'}},
                                              'UUT07': {'POELB1':  {'portmap':  '1-8',  'syncgroup': 'PoESync2'}},
                                              'UUT08': {'POELB1':  {'portmap':  '9-16', 'syncgroup': 'PoESync2'}},
                                              },
        'C3K|Production-Sim|PCBST|Station_A_2': {'UUT01': {'POELB1': {'portmap': '1-24', 'syncgroup': 'PoESync2'}},
                                                 'UUT02': {'POELB1': {'portmap': '1-24', 'syncgroup': 'PoESync2'}},
                                                 },
    }
    # =========
    # Build It!
    # =========
    config_builder.build_product_line_configurations(uut_map=uut_map, seq_map=sequence_map, station_conn_map=station_and_connection_map, cfg_data=cfg_data)
    # ------------------------------------------------------------------------------------------------------------------

    # DONE with this BU!
    return
