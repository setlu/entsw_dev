"""
Austin Lab - Jon Wilson's Apollo
---------------------------------------------
Host: cisappm5
Primary IP   (eth0): 10.89.133.107
Secondary IP (eth1): 10.1.1.2  <-- CONFLICTS w/ ausdev11; need 10.1.1.3/255.255.0.0  (no permissions to change)
CIMC IP: 10.89.133.108

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
    # uabu_cfg() (use new structure)
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
