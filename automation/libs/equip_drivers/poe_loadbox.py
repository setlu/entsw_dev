""" PoE Loadbox Driver Module
========================================================================================================================

This module provides a set of classes for operating PoE LoadBoxes.
To date, there are only 2 manufacturers that provide a scalable solution for mfg test application:
  1. Reach Technologies (Edgar load boxes),
  2. Cisco Systems (Odin load box system).

All classes are REQUIRED to use the 'PoEbase' abstract base class (in poe_base.py) for interface definition.

The format of this module contains the following:

  1) Driver selector function: 'select()' (also initializes the class that is selected),
  2) Class for Reach Edgar line (generic)
  3) Class for Reach Edgar3,
  4) Class for Reach Edgar4,
  5) Class for Cisco Odin.

------------------------------------------------------------------------------------
Multiple UUT configurations scenarios can exist; the following setups are supported:

  Scenario A) 1 UUT    <-->   1  PoE_Load_Box
  Scenario B) 1 UUT    <-->   2+ PoE_Load_Boxes
  Scenario C) 2+ UUTs  <-->   1  PoE_Load_Box  (requires shared connections AND a syncgroup)

IMPORTANT:
    This driver module REQUIRES the use of Apollo connections for the PoE equipment to support the
    above configurations.   The connections also use 'model' and 'manufacturer' params.
    The container's PoE Equipment connection 'name' param MUST contain "POE" as the prefix.

    The "configuration data" describes the portmap, syncgroup, and pair that a container connection should use.
    The 'portmap' is the actual PoE Equipment port numbers that attach to the UUT.
    The 'syncgroup' MUST be added for multi UUT or multi PoE Equip scenarios ("B" & "C" above).
    The 'syncgroup' name should contain "PoESync" as a prefix and it MUST match the appropriate container
    connection syncgroup described in the configuration data.
    The 'pair' is only used in a dual load box situation (i.e. 2 x POE+ w/ wired-splitter = UPOE).
    The 'pair' param is ONLY used on the secondary unit and the pair value is the primary load box
     connection name (see example Scenario "B" Case 2).
    The configuration data is placed at the container level!
    Examples:
    (Scenario A)
    container1.add_configuration_data(key='POELB1',  value={'portmap': '1-24', 'syncgroup': 'PoESync1'})
    container1.add_configuration_data(key='POELB2',  value={'portmap': '1-24', 'syncgroup': 'PoESync1'})

    (Scenario B)
    container3.add_configuration_data(key='POELB1',  value={'portmap': '1-24', 'syncgroup': 'PoESync2'})
    container3.add_configuration_data(key='POELB2',  value={'portmap': '1-24', 'syncgroup': 'PoESync2'})

    (Scenario B)
    container2.add_configuration_data(key='POELB1a', value={'portmap': '1-24', 'syncgroup': 'PoESync3'})
    container2.add_configuration_data(key='POELB1b', value={'portmap': '1-24', 'syncgroup': 'PoESync3', 'pair': 'POELB1a'})
    container2.add_configuration_data(key='POELB2a', value={'portmap': '1-24', 'syncgroup': 'PoESync3'})
    container2.add_configuration_data(key='POELB2b', value={'portmap': '1-24', 'syncgroup': 'PoESync3', 'pair': 'POELB2a'})

    (Scenario C)
    container4.add_configuration_data(key='POELB1',  value={'portmap': '1-12', 'syncgroup': 'PoESync4'})
    container5.add_configuration_data(key='POELB1',  value={'portmap': '13-24', 'syncgroup': 'PoESync4'})


    For the above configuration data:
        1) UUT01 has 2 loadboxes using 24 ports/box
        2) UUT02 has 4 loadboxes using 24 ports/box; the "a" & "b" match up
        3) UUT03 & UUT04 each use 1 loadbox using 24 ports/box.
        4) UUT05 & UUT06 SHARE one loadbox; UUT05 has first group of ports and UUT06 has second group.


    --------------------------------------------------------------------------------------------------
    Scenarios given below describe the prerequisites-
        1) 'prod_def_subdict' which is part of the uut_config (loaded from product_definition (x_def.py))
           Note: for driver purposes this can be your own arbitrary dict you provide as a param when calling the .select() function.
        2) the 'connection_config' in the Apollo config (x_config.py),
        3) the 'x.add_...' functions also in the Apollo config (x_config.py):

    Scenario "A" Prerequisite:
    --------------------------
    prod_def_subdict = {'poe': {'uut_ports': '1-24', 'type': 'POE+'}}
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2018, timeout=60, model='Edgar4', manufacturer='Reach')
    container.add_connection(name='POELB1', **connection_config)
    test_station.add_sync_group('PoESync16', ['UUT16'])
    container.add_configuration_data(key='UUT16', value={'POELB1': {'portmap': '1-24', 'syncgroup': 'PoESync1'}}})


    Scenario "B" Prerequisite:
    --------------------------
    Case 1
    prod_def_subdict = {'poe': {'uut_ports': '1-48', 'type': 'UPOE'}}
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2017, timeout=60, model='Edgar4', manufacturer='Reach')
    container.add_connection(name='POELB1', shared_conn='', **connection_config)
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2018, timeout=60, model='Edgar4', manufacturer='Reach')
    container.add_connection(name='POELB2', **connection_config)
    test_station.add_sync_group('PoESync16', ['UUT16'])
    container.add_configuration_data(key='POELB1',  value={'portmap': '1-24', 'syncgroup': 'PoESync2'})
    container.add_configuration_data(key='POELB2',  value={'portmap': '1-24', 'syncgroup': 'PoESync2'})

    Case 2
    prod_def_subdict = {'poe': {'uut_ports': '1-48', 'type': 'UPOE'}}
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2015, timeout=60, model='Edgar3', manufacturer='Reach')
    container.add_connection(name='POELB1a', shared_conn='', **connection_config)
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2016, timeout=60, model='Edgar3', manufacturer='Reach')
    container.add_connection(name='POELB1b', shared_conn='', **connection_config)
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2017, timeout=60, model='Edgar3', manufacturer='Reach')
    container.add_connection(name='POELB2a', shared_conn='', **connection_config)
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2018, timeout=60, model='Edgar3', manufacturer='Reach')
    container.add_connection(name='POELB2b', **connection_config)
    test_station.add_sync_group('PoESync16', ['UUT16'])
    container.add_configuration_data(key='POELB1a', value={'portmap': '1-24', 'syncgroup': 'PoESync3'})
    container.add_configuration_data(key='POELB1b', value={'portmap': '1-24', 'syncgroup': 'PoESync3', 'pair': 'POELB1a'})
    container.add_configuration_data(key='POELB2a', value={'portmap': '1-24', 'syncgroup': 'PoESync3'})
    container.add_configuration_data(key='POELB2b', value={'portmap': '1-24', 'syncgroup': 'PoESync3', 'pair': 'POELB2a'})

    Scenario "C" Prerequisite:
    --------------------------
    prod_def_subdict = {'poe': {'uut_ports': '1-8', 'type': 'POE+'}}
    connection_config = dict(protocol='telnet', host='10.89.133.8', port=2003, timeout=60, model='Edgar3', manufacturer='Reach')
    test_station.add_connection(name='Shared_POELB_01', **connection_config)
    container1.add_connection(name='POELB1', shared_conn='Shared_POELB_01')
    container2.add_connection(name='POELB1', shared_conn='Shared_POELB_01')
    test_station.add_sync_group('PoESync8', ['UUT01', 'UUT02'])
    container.add_configuration_data(key='POELB1',  value={'portmap': '1-12', 'syncgroup': 'PoESync4'})
    container.add_configuration_data(key='POELB1',  value={'portmap': '13-24', 'syncgroup': 'PoESync4'})


PRODUCT DEFINITIONS: Each Base PID must describe the PoE capability it has.
                     Example entry in the product definition as
                     'prod_def_subdict': {'poe': {'uut_ports': '1-24', 'type': 'POE+'}} is just a representative dict,
                     Where, 'uut_ports' is a (str) range corresponding to the actual port numbers with poe capability,
                            and 'type' is a (str) of 'POE', 'POE+', or 'UPOE'.


USAGE in SCRIPT:

    # Instantiate PoE driver class
    # ----------------------------
    poe_connections = [getattr(aplib.conn, conn_name) for conn_name in sorted(aplib.getconnections().keys()) if 'POE' in conn_name]
    poe = poe_loadbox_driver.select(connections=poe_connections,
                                    uut_poe_ports=prod_def_subdict['poe']['uut_ports'],
                                    uut_poe_type=prod_def_subdict['poe']['type'])

    # Use the driver (Example 1: Simple)
    # ----------------------------------
    <do some UUT setup stuff>
    poe.show_equipment()
    poe.reset()
    poe.set_power_load(current_limit_mA=640)
    poe.set_class(load_class=4)
    poe.connect(detect_signature='ok', external='on', auto='on', ieee=False)
    poe.set_load_on()
    <do some UUT POE stuff, turn on power, measure, run other diags poe, etc.>
    poe.set_load_off()
    poe.disconnect()

    # Use the driver (Example 2: Power Budget <*=your_functions>)
    # -------------------------------------------------------------
    <do some UUT setup stuff>
    poe.show_equipment()
    poe.reset()
    poe.set_power_load(current_limit_mA=640)
    poe.set_class(load_class=4)
    poe.connect(detect_signature='ok', external='on', auto='on', ieee=False)
    poe.set_load_on()
    my_uut_total_power = get_uut_power()*
    my_poe_pwr_budget_groups = calc_uut_power_budget(poe_type=poe_type, poe_ports=poe_ports, uut_power=my_uut_total_power)*
    for group in range(1, my_poe_pwr_budget_groups + 1):
        active_poe_ports = my_build_pwr_budget_port_list(ports=poe_ports, group_index=group, poe_pwr_budget_groups=my_poe_pwr_budget_groups)*
        <do some UUT POE stuff, turn on power ONLY for the active_poe_ports, measure, run diags poe, etc.>
    poe.set_load_off()
    poe.disconnect()

    -------------------------------------------------------------------------------------------------------------------

    Classes
    --------------
    Class   PMIN       PMAX           ICLASS (MIN)  ICLASS (MAX)   RCLASS
    0       0.44 W     15.40 W         0 mA          4 mA            Open
    1       0.44 W      3.84 W         9 mA         12 mA         150.0 ohm
    2       3.84 W      6.49 W        17 mA         20 mA          82.5 ohm
    3       6.49 W     15.40 W        26 mA         350 mA         53.6 ohm
    4                  30.40 W        36 mA         600 mA         38.3 ohm
    4 (x2)             60.00 W/pair                 600 mA/pair

========================================================================================================================
"""

# ------
import sys
import re
import logging
import time

# Apollo
# ------
from apollo.libs import lib as aplib
from apollo.libs import locking
from apollo.engine import apexceptions

# BU Lib
# ------
from ..bases.poe_loadbox_base import PoE_Loadbox_Base
from ..utils import common_utils

__title__ = "PoE Loadbox Driver Module"
__version__ = '0.7.4'
__author__ = ['bborel', 'tnnguyen']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

func_details = common_utils.func_details

global equip_status
equip_status = {}

# ======================================================================================================================
# External User functions
#
def select(**kwargs):
    """ Driver Selector
    Selects the class object based on the PoE Instrument Model connected.
    Output is the class object (NOT initialized) to use in sequences.

    SAMPLE EDGAR:
    ------------------------------------------------------
    RT-PoE3>version
    Reach PoE Tester Model RT-PoE3/24 Rev A HW 1.0 SW 1.01/2 04/02/2010
    Copyright (C) 2005-2010 by Reach Technology Inc.

    RT-PoE4>version
    Reach PoE Tester Model RT-PoE4/10G/24
    PN 53-0004-01 Rev A 01 SW 1.03 11/01/2016
    Copyright (C) 2005-2016 by Reach Technology Inc.

    # SAMPLE ODIN:
    # ------------------------------------------------------
    # <Boot up>
     Chassis: WS-C4948E

    rommon 1 >
    rommon 1 >version
    Primary Rom Monitor Version 12.2(44r)SG(100)
    Compiled Wed 12-Oct-11 15:52 by ridikula-k5rommonodin

    Supervisor: WS-C4948E  Chassis: WS-C4948E
    CPU Rev: 3.1, Board Rev: 5, Board Type: 104
    CPLD Hobgoblin Rev: 6, Installed memory: 1024 MBytes

    # MAY HAVE TO LOAD AN IMAGE TO ODIN BOX (EXAMPLE):
    # (SJ Lab unit: 172.28.106.68,  and then 10.1.1.2 2006)
    # ----------
    rommon 1 > boot -o tftp://10.1.1.1/diagsk5.odinSA2

    Odin():/>
    result:  (00000000)
    Odin():/> version
    Diag Software, Version DiagsSW:  5.1.5.0
    Copyright (c) 2008-2010 by Cisco Systems
    Diags S/W compiled on 2013.04.08 12:04:00 by rarulana
    System image file is ""
    Rommon Version is ""
    Odin():/>

    :param (dict) kwargs:
    :return (obj): class
    """
    global equip_status

    def _get_model_version(conn, sync_group):
        """ Get Model and Version
        Operate on a single connection only.
        Since it is possible for multiple UUT containers to share a single PoE Load Box,
        the locking mechanism must be used with a sync group.
        The PoE sync group is tied only to the containers sharing the connection.

        Example:
        Reach PoE Tester Model RT-PoE4/10G/24
        PN 53-0004-01 Rev A 01 SW 1.03 11/01/2016
        Copyright (C) 2005-2016 by Reach Technology Inc.

        :param (obj) conn: PoE Equipment connection
        :param (obj) sync_group: PoE Sync Group for UUT containers sharing the device.
        :return:
        """
        log.debug("Getting PoE Equipment Info...")
        if not hasattr(conn, 'status'):
            msg = "PoE Driver = NONE. (The connection given is NOT a valid Apollo connection.)"
            log.warning(msg)
            # TBD: raise aplib.apexceptions.AbortException
            return None, None

        mod, ver = None, None
        log.debug("PoE Driver connection lock...")
        with locking.named_priority_lock('__poe_equip__' + sync_group):
            if conn.status != aplib.STATUS_OPEN:
                log.warning('The PoE Instrument connection needs to be open...')
                try:
                    conn.open()
                    time.sleep(5)
                except Exception as e:
                    log.warning("PoE Equipment connection exception will disallow driver load.")
                    log.warning("PoE Driver = NONE. (The PoE Instrument connection CANNOT open!)")
                    if aplib.get_apollo_mode() != 'DEBUG':
                        log.error(e)
                        raise aplib.apexceptions.AbortException("No PoE instrument connection available.")
                    return None, None
            else:
                log.debug("PoE Driver connection status is open.")

            # Get Model and Version
            conn.clear_recbuf()
            try:
                conn.sende('\r\r', expectphrase='.*', timeout=20, regex=True)
                conn.sende('version\r', expectphrase='>', timeout=30)
                time.sleep(2.0)
            except aplib.apexceptions.TimeoutException as e:
                log.error("PoE Driver = NONE. (The PoE Instrument connection is not responding!)")
                log.error("Please check that you have the correct connection.")
                conn.close()
                if aplib.get_apollo_mode() != 'DEBUG':
                    log.error(e)
                    raise aplib.apexceptions.AbortException("No PoE instrument version available.")
                return None, None

            # Parse Model
            m = re.search('(RT-PoE[\S]*)|(Edgar[\S]*)|(WS-C49[\S]*)|(Odin)', conn.recbuf)
            mod = m.group(0) if m and m.group(0) else None
            if conn.model and conn.model != mod:
                log.warning("Model name from Apollo config connection is different than the detected name.")
                log.warning("Model detected='{0}'  Model expected='{1}'".format(mod, conn.model))
                log.warning("The config will be ignored and the actual detected name will be used.")

            # Parse Version
            v = re.search('(?:(PN.*[^\n\r]))|(?:DiagsSW:[ ]*([0-9\.]+))|(Rev .*? HW [0-9\.]+)', conn.recbuf)
            ver = v.group(0) if v and v.group(0) else None

        return mod, ver

    log.debug("Select PoE Loadbox driver class...")

    # Inputs
    verbose = kwargs.get('verbose', True)

    # Predefines
    try:
        container_key = aplib.get_my_container_key()
        station_key = '|'.join(container_key.split('|')[:-1])
        container = container_key.split('|')[-1]
        if not container:
            log.warning("No container specified.")
            log.warning("A container must be associated with the PoE equipment.")
            return None
    except:
        log.debug("No container available.")
        return None

    connections = [getattr(aplib.conn, conn_name) for conn_name in sorted(aplib.getconnections().keys()) if 'POE' in conn_name]

    # Check for at least one connection.
    # REQUIRED for the driver to be initialized; otherwise null is returned.
    if not connections:
        log.warning("PoE Loadbox Driver = NONE. (No connections provided.)")
        return None

    # Arrange the lists.
    # Note: Some PoE setups involve multiple connections to 1,2 or 4 PoE LoadBoxes.
    num_loadboxes = len(connections)
    log.debug("Loadboxes available per UUT: {0}".format(num_loadboxes))
    models = [None for _ in range(0, num_loadboxes)]
    versions = [None for _ in range(0, num_loadboxes)]
    configuration_data = [None for _ in range(0, num_loadboxes)]

    # Scan each connection.
    # Attempt to Autodetect the PoE equipment via the connection provided.
    # Note: All connections MUST be provided.
    log.debug("Attempting autodetect of PoE Equipment via connection(s)...")
    log.debug("Station                   : {0}".format(station_key))
    log.debug("Target LB Connection Count: {0}".format(num_loadboxes))
    log.debug("Configuration Data:")
    for k, v in aplib.apdicts.configuration_data.items():
        log.debug("{0:<20}: {1}".format(k, v))
    for i, connection in enumerate(connections):
        if connection:
            try:
                # Extract additional PoE Equipment Setup data from the Apollo configuration data in _config.py.
                # This is a convention chosen to allow more detail about the connections.
                # configuration_data[i] = aplib.apdicts.configuration_data[container][common_utils.get_conn_name(connection)]
                configuration_data[i] = aplib.apdicts.configuration_data[common_utils.get_conn_name(connection)]
                if 'syncgroup' not in configuration_data[i]:
                    configuration_data[i]['syncgroup'] = container
            except KeyError:
                log.warning("Using DEFAULT connection configuration data.")
                configuration_data[i] = {'syncgroup': container}
            models[i], versions[i] = _get_model_version(connection, configuration_data[i]['syncgroup'])
            status = 'good' if models[i] and versions[i] else 'NOT good'
            log.debug("PoE Connection {0} of {1} is {2}.".format(i + 1, num_loadboxes, status))
        else:
            log.error("Need a connection object for the PoE Equipment {0} of {1}!".format(i + 1, num_loadboxes))
            raise aplib.apexceptions.AbortException

    if not all(models) or not all(versions):
        errmsg = "All PoE Equipment models/versions were NOT determined."
        if aplib.get_apollo_mode() != 'DEBUG':
            raise aplib.apexceptions.AbortException(errmsg)
        log.warning(errmsg)
        return None

    # Check that all models are the same for multi-equip scenarios.
    if models.count(models[0]) != len(models):
        errmsg = "Equipment setup: Model NOT established (group mismatch)!"
        for i, model in enumerate(models, 1):
            log.debug("Model {0}: {1}".format(i, model))
        if aplib.get_apollo_mode() != 'DEBUG':
            raise aplib.apexceptions.AbortException(errmsg)
        log.warning(errmsg)
        return None
    else:
        log.debug("Equipment setup: Model established.")
        model = models[0]
        version = versions[0]

    # Save model & version later for setup (to be done AFTER the UUT is known).
    equip_status['model'] = model
    equip_status['version'] = version

    # Instantiate the class based on model (either provided or auto-detected).
    # Pass 'poe_equip' details to the class init.
    log.debug("Selecting PoE Driver for Model: {0}".format(model))
    if model in PoEedgar3.MODELS:
        log.debug("Reach Edgar3")
        return getattr(thismodule, 'PoEedgar3')
    elif model in PoEedgar4.MODELS:
        log.debug("Reach Edgar4")
        return getattr(thismodule, 'PoEedgar4')
    elif model in PoEedgar5.MODELS:
        log.debug("Reach Edgar5")
        return getattr(thismodule, 'PoEedgar5')
    elif model in PoEodin.MODELS:
        log.debug("Cisco Odin")
        return getattr(thismodule, 'PoEOdin')
    else:
        log.warning("PoE Driver = NONE. (Model was unrecognized.)")
        return None


def init(poe_obj, **kwargs):
    """ Driver Initializer
    Instantiates the class object based on the PoE Instrument Model connected.
    The class object MUST have been previously selected.

    # -------------------------------------------------------------------
    # ALL POE EQUIPMENT CONNECTIONS ARE EXPECTED TO BE APOLLO CONNECTIONS
    # The following dict is created from the connection(s) details.
    # -------------------------------------------------------------------
    poe_equip = {
        'POELB1': {'conn': <obj>, 'portmap': <pm>, 'syncgroup': <sg>},
        'POELB2': {'conn': <obj>, 'portmap': <pm>, 'syncgroup': <sg>, 'pair': <pr>},
        ...
    }

    :param (obj) poe_obj: Class object for PoE detected equipment
    :param (str) model: PoE Model name
    :param (str) version: PoE Version
    :param (dict) kwargs:
                  uut_config (dict): The uut_config (product definition) data.
                  uut_poe_ports (str): Range of PoE ports on the UUT.
                  uut_poe_type(str): The type of PoE supported by the UUT ('POE', 'POE+', or 'UPOE').
    :return (obj): class
    """
    global equip_status

    def _choose_appropriate_connections(_connections, _uut_poe_type, _uut_poe_ports):
        """ Choose Appropriate Connections for PoE Loadbox
        Do this to allow "flexible" stations.
        Ex. A. 20 boxes for 1 station x 48ports/uut  or  B. 10 boxes for 2 stations x 24ports/uut.
        The Apollo config will have 2 Station entries; however, when running scenario A the station in scenario B
        is not allowed to run.
        NOTE: MUST follow PoE loadbox naming convention!  "POELB<1|2>[a|b]"  (letter suffix used in "splitter config")
        :param _connections: all connections of a container
        :param _uut_poe_type:
        :param _uut_poe_ports:
        :return:
        """
        log.debug("Selecting appropriate loadbox connections...")
        appropos_conn_table = {('POE', 24): ['POELB1[a]?$'],
                               ('POE', 48): ['POELB1[a]?$', 'POELB2[a]?$'],
                               ('POE+', 24): ['POELB1[a]?$'],
                               ('POE+', 48): ['POELB1[a]?$', 'POELB2[a]?$'],
                               ('UPOE', 24): ['POELB1[ab]?$'],
                               ('UPOE', 48): ['POELB1[ab]?$', 'POELB2[ab]?$']}
        port_count = len(common_utils.expand_comma_dash_num_list(_uut_poe_ports))
        log.debug("UUT PoE Type      : {0}".format(_uut_poe_type))
        log.debug("UUT PoE Port Count: {0}".format(port_count))
        if (_uut_poe_type, port_count) not in appropos_conn_table:
            appropos_conns = _connections
        else:
            target_conn_names = appropos_conn_table[_uut_poe_type, port_count]
            log.debug("LB Target conn names = {0}".format(target_conn_names))
            appropos_conns = [conn for conn in _connections if any([re.search(pat, common_utils.get_conn_name(conn)) for pat in target_conn_names])]
            # log.debug("LB Appropos conns = {0}".format(appropos_conns))
        log.debug("Selected PoE Loadbox connections: {0}".format([common_utils.get_conn_name(conn)] for conn in appropos_conns))
        return appropos_conns

    log.debug("Init PoE Loadbox driver...")

    # Inputs
    ud = kwargs.get('ud', None)
    uut_poe_ports = kwargs.get('uut_poe_ports', ud.uut_config.get('poe', {}).get('uut_ports', None))
    uut_poe_type = kwargs.get('uut_poe_type', ud.uut_config.get('poe', {}).get('type', 'unknown'))
    model = equip_status.get('model')
    version = equip_status.get('version')
    verbose = kwargs.get('verbose', True)

    # Check Class selection
    if not poe_obj:
        log.debug("No PoE Class Driver available.")
        log.debug("Init will be skipped.")
        return None

    # Predefines
    try:
        container_key = aplib.get_my_container_key()
        station_key = '|'.join(container_key.split('|')[:-1])
        container = container_key.split('|')[-1]
    except:
        log.warning("No container available.")
        log.warning("Cannot initialize the PoE Loadbox driver.")
        log.warning("A container must be associated with the PoE equipment.")
        return None

    connections = [getattr(aplib.conn, conn_name) for conn_name in sorted(aplib.getconnections().keys()) if 'POE' in conn_name]

    if uut_poe_type in [None, '', 'nonPOE', 'unknown']:
        log.warning("PoE Loadbox Driver cannot be initialized due to uut_poe_type.")
        log.warning("Current UUT PoE type: {0}".format(uut_poe_type))
        return None

    # Check for at least one connection.
    # REQUIRED for the driver to be initialized; otherwise null is returned.
    if not connections:
        log.warning("PoE Loadbox Driver = NONE. (No connections provided.)")
        return None

    if not uut_poe_ports:
        log.warning("The UUT PoE ports were forced to None.")
        log.warning("Check the product definition; correct as necessary.")
        log.warning("PoE Loadbox Driver will NOT be initialized.")
        return None

    # Arrange the lists.
    # Note: Some PoE setups involve multiple connections to 1,2 or 4 PoE LoadBoxes.
    all_poe_connections = [connections] if not isinstance(connections, list) else connections
    # log.debug("All LB Connections: {0}".format(all_connections))
    connections = _choose_appropriate_connections(all_poe_connections, uut_poe_type, uut_poe_ports)
    models = [None for _ in range(0, len(connections))]
    versions = [None for _ in range(0, len(connections))]
    configuration_data = [None for _ in range(0, len(connections))]
    poe_equip = {}

    # Scan each connection.
    # Attempt to Autodetect the PoE equipment via the connection provided.
    # Note: All connections MUST be provided.
    log.debug("Attempting autodetect of PoE Equipment via connection(s)...")
    log.debug("Station              : {0}".format(station_key))
    log.debug("Target LB Connections: {0}".format(connections))
    log.debug("Configuration Data:")
    for k, v in aplib.apdicts.configuration_data.items():
        log.debug("{0:<20}: {1}".format(k, v))
    for i, connection in enumerate(connections):
        if connection:
            try:
                # Extract additional PoE Equipment Setup data from the Apollo configuration data in _config.py.
                # This is a convention chosen to allow more detail about the connections.
                # configuration_data[i] = aplib.apdicts.configuration_data[container][common_utils.get_conn_name(connection)]
                configuration_data[i] = aplib.apdicts.configuration_data[common_utils.get_conn_name(connection)]
                if 'portmap' not in configuration_data[i]:
                    configuration_data[i]['portmap'] = ''
                if 'syncgroup' not in configuration_data[i]:
                    configuration_data[i]['syncgroup'] = container
                if 'shareports' not in configuration_data[i]:
                    configuration_data[i]['shareports'] = 0
            except KeyError:
                log.warning("Using DEFAULT connection configuration data.")
                configuration_data[i] = {'portmap': '', 'syncgroup': container, 'shareports': 0}
            models[i], versions[i] = model, version
            status = 'good' if models[i] and versions[i] else 'NOT good'
            log.debug("PoE Connection {0} of {1} is {2}.".format(i + 1, len(connections), status))
        else:
            log.error("Need a connection object for the PoE Equipment {0} of {1}!".format(i + 1, len(connections)))
            raise aplib.apexceptions.AbortException

    # Assemble details for each piece of PoE Equipment; optional print.
    for i, mvcps in enumerate(zip(models, versions, connections, configuration_data), start=1):
        poe_equip[common_utils.get_conn_name(mvcps[2])] = dict(index=i,
                                                               model=mvcps[0],
                                                               version=mvcps[1],
                                                               conn=mvcps[2],
                                                               portmap=mvcps[3]['portmap'],
                                                               syncgroup=mvcps[3]['syncgroup'],
                                                               shareports=mvcps[3]['shareports'])
        if 'pair' in mvcps[3]:
            poe_equip[common_utils.get_conn_name(mvcps[2])].update(dict(pair=mvcps[3]['pair']))

        if verbose:
            log.debug("PoE Instrument #{0} : Conn={1}  Model={2}  Ver={3}  PortMap={4}  SyncGroup={5}{6}  Shareports={7}".
                      format(i, common_utils.get_conn_name(mvcps[2]), mvcps[0], mvcps[1],
                             mvcps[3]['portmap'], mvcps[3]['syncgroup'],
                             '  Pair={}'.format(mvcps[3]['pair']) if 'pair' in mvcps[3] else '',
                             mvcps[3]['shareports']))
    if verbose:
        log.debug("UUT PoE Ports       : {0}".format(uut_poe_ports))
        log.debug("UUT PoE Type        : {0}".format(uut_poe_type))
        log.debug("UUT Container       : {0}".format(container))

    # Instantiate the class that was provided.
    # Pass 'poe_equip' details to the class init.
    log.debug("Instantiating PoE Driver: {0} for Model: {1}".format(poe_obj, model))
    return poe_obj(poe_equip, uut_poe_ports, **kwargs)


def handle_no_poe_equip():
    """ Handle No PoE Equipment
    Determine PROD vs. DEBUG mode and what to do when UUT has PoE capability but no PoE Equipment was detected.
    :return:
    """
    log.warning("PoE uut_config is present but NO PoE Loadbox Driver was loaded.")
    if aplib.get_apollo_mode() == aplib.MODE_PROD:
        log.error("Production Mode requires a PoE Loadbox Driver.")
        log.error("Check the config file and ensure connections are set for this container.")
        log.error("The connection name should contain the string 'POE'.")
        log.error("Please consult the configs.common.<catX>.stations routines for proper connection names.")
        return aplib.FAIL
    elif aplib.get_apollo_mode() == aplib.MODE_DEBUG:
        log.warning("Debug Mode will SKIP any PoE tests while the driver is not loaded.")
        return aplib.SKIPPED
    else:
        log.critical("Unknown Apollo mode!")
        raise apexceptions.AbortException("Unknown Apollo mode.")


# ======================================================================================================================
# Internal functions
#
def __sync_reset(self):
    """ Synchronized Reset
    This is a syncgroup leader funtion ONLY.
    (NOTE: Leader functions are not allowed as static methods within a class; hence this is at global module level.)
    :param (obj) self: Initialized driver class
    :return:
    """
    for k in self.conn_names:
        log.debug("{0} Reset the PoE equipment...".format(k))
        conn = self._poe_equip[k]['conn']
        conn.sende('reset\r', expectphrase=self.prompt, regex=True)
    return


# ======================================================================================================================
# CLASS DRIVERS
#
# ----------------------------------------------------------------------------------------------------------------------
class PoEedgarGeneric(PoE_Loadbox_Base):
    """ PoE PoEedgarGeneric
   """
    RECBUF_TIME = 5.0
    RECBUF_CLEAR_TIME = 2.0
    USE_CLEAR_RECBUF = True
    MODELS = ['Edgar']
    MAX_PORTS = 24
    DEFAULT_CURRENT_LIMITS = {'IEEE': 200, 'poe': 300, 'POE': 280, 'POE+': 540, 'UPOE': 1120}
    LOAD_CLASSES = {None: 0, 'poe1': 1, 'poe2': 2, 'POE': 3, 'POE+': 4, 'UPOE': 4}

    def __init__(self, poe_equip, uut_poe_ports, **kwargs):
        """ Init
        :param (dict) poe_equip: Form of {'POELBx': {'conn': <obj>, 'portmap': '<pm>', 'syncgroup': '<sg>', 'shareports': 0},...}
        :param (str) uut_poe_ports: Range of UUT ports that have PoE capability
        :param kwargs: Additional (optional) params:
                       (str) prompt: Regex expression for PoE Equipment prompt.
                       (str) container: Name of container (not the full key).
                       (str) uut_poe_type: One of 'POE', 'POE+', 'UPOE'
        :return:
        """
        # super(PoEedgarGeneric, self).__init__(poe_equip, uut_poe_ports)

        # Internals
        self._poe_equip = poe_equip
        self._uut_poe_ports = None
        self._prompt = kwargs.get('prompt', '[A-Za-z0-9_\-]+>')
        self._container = kwargs.get('container', aplib.get_my_container_key().split('|')[-1])
        self._verbose = kwargs.get('verbose', True)
        self._power_load_current_limit = None
        self._port_lookup = {}
        self._full_ports = False
        self._shareports = 0

        # Sanity check
        if not isinstance(self._poe_equip, dict):
            log.error("The 'poe_equip' parameter must be in dict form.")
            raise aplib.apexceptions.AbortException
        for k in self._poe_equip.keys():
            if not all([i in self._poe_equip[k].keys() for i in ['model', 'version', 'conn', 'portmap', 'syncgroup']]):
                log.error("The 'poe_equip' parameter does not contain all the required keys:")
                log.error(" Required: {0}".format(sorted(['model', 'version', 'conn', 'portmap', 'syncgroup'])))
                log.error(" Current : {0}".format(sorted(self._poe_equip[k].keys())))
                raise aplib.apexceptions.AbortException

        # Dependent
        self.uut_poe_ports = uut_poe_ports                     # UUT ports attached to the PoE Equipment
        self.uut_poe_type = kwargs.get('uut_poe_type', 'POE')  # types: POE, POE+, UPOE

        return

    # Properties ------------------------------------------------------
    #
    # Rd Only Properties
    @property
    def poe_equip(self):
        return self._poe_equip

    @property
    def container(self):
        return self._container

    @property
    def conn_names(self):
        return sorted(self._poe_equip.keys())

    @property
    def syncgroup(self):
        sg_list = [self._poe_equip[k]['syncgroup'] for k in self._poe_equip.keys()]
        if sg_list.count(sg_list[0]) != len(sg_list):
            log.error("The sync group for multiple PoE Equipment connections do NOT match.")
            log.error("Sync groups: {0}".format(sg_list))
            raise aplib.apexceptions.AbortException
        return sg_list[0]

    @property
    def prompt(self):
        # Regex prompt to be used for all PoE devices connected to a single UUT.
        return self._prompt

    # Rd/Wr Properties ---
    @property
    def uut_poe_ports(self):
        return self._uut_poe_ports

    @uut_poe_ports.setter
    def uut_poe_ports(self, newvalue):
        """

        Examples:
        1 UUT (24port) : 1 Edgar
        UUT port list = [1, 2, ..., 23, 24]
        PoE Equip Ports : [(1, u'POELB1'), (2, u'POELB1'), ..., (23, u'POELB1'), (24, u'POELB1')]
        UUT PoE Ports   : [1, 2, ..., 23, 24]
        Mapping         : {1: (1, u'POELB1'), 2: (2, u'POELB1'), 3: (3, u'POELB1'), ..., 23: (23, u'POELB1'), 24: (24, u'POELB1')}

        1 UUT (48port) : 2 Edgars
        UUT port list = [1, 2, ..., 47, 48]
        PoE Equip Ports : [(1, u'POELB1'), (2, u'POELB1'), ..., (23, u'POELB1'), (24, u'POELB1'),
                           (1, u'POELB2'), (2, u'POELB2'), ..., (23, u'POELB2'), (24, u'POELB2')]
        UUT PoE Ports   : [1, 2, ..., 47, 48]
        Mapping         : { 1: (1, u'POELB1'),  2: (2, u'POELB1'),  3: (3, u'POELB1'), ..., 23: (23, u'POELB1'), 24: (24, u'POELB1'),
                           25: (1, u'POELB2'), 26: (2, u'POELB2'), 27: (3, u'POELB2'), ..., 47: (23, u'POELB2'), 48: (24, u'POELB2')}


        :param newvalue:
        :return:
        """

        # Expand PoE Equipment ports (based on connections)
        log.debug("PoE Equip Connection Names: {0}".format(self.conn_names))
        poe_equip_port_map_list = []
        for k in self.conn_names:
            ppms = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap'])
            poe_port_map_sublist = [(p, k) for p in ppms]
            if len(poe_port_map_sublist) > self.MAX_PORTS:
                log.error("The number of PoE Equipment ports to map exceeds the equipment capability!")
                log.error("Check the container's connection 'portmap' parameter and correct it.")
                raise aplib.apexceptions.AbortException
            if 'pair' not in self._poe_equip[k]:
                poe_equip_port_map_list += poe_port_map_sublist
            else:
                log.debug("Paired group specified.")
                # A dual load box pair was specified; combine equip "B" into equip "A" for port lookup.
                idx = poe_equip_port_map_list.index((ppms[0], self._poe_equip[k]['pair']))
                for i, p in zip(range(idx, len(ppms) + idx), ppms):
                    p1 = poe_equip_port_map_list[i][0]
                    k1 = poe_equip_port_map_list[i][1]
                    poe_equip_port_map_list[i] = (p1, k1, p, k)
        poe_equip_effective_port_count = len(poe_equip_port_map_list)

        # Expand UUT ports and sanity check
        uut_port_list = [1]
        if isinstance(newvalue, str):
            uut_port_list = common_utils.expand_comma_dash_num_list(newvalue)
        elif isinstance(newvalue, list):
            if not all([True if isinstance(i, int) else False for i in newvalue]):
                log.warning("UUT PoE port list must be a list of integers only!")
                log.warning("Defaulting to a list of UUT sequential ports supported by the detected portmap.")
                uut_port_list = [i for i in range(1, poe_equip_effective_port_count + 1)]
        else:
            log.warning("UUT PoE port list MUST be a string range or an integer list.")
            log.warning("Defaulting to a list of UUT sequential ports supported by the detected portmap.")
            uut_port_list = [i for i in range(1, poe_equip_effective_port_count + 1)]
        log.debug("UUT port list = {}".format(uut_port_list))

        # When setting the UUT PoE ports that are attached; ensure the correct port mapping and connections
        # are available.
        if len(uut_port_list) > len(poe_equip_port_map_list):
            log.warning("UUT PoE port list (larger) does NOT map 1:1 to PoE Equipment port list!")
            first_poe_conn = self.conn_names[0]
            log.debug("Firts conn = {0}".format(first_poe_conn))
            log.debug(self._poe_equip[first_poe_conn])
            self._shareports = self._poe_equip.get(first_poe_conn, {}).get('shareports', 0)
            if self._shareports == 0:
                original_uut_port_list = uut_port_list
                uut_port_list = [i for i in range(1, min(poe_equip_effective_port_count, len(uut_port_list)) + 1)]
                if uut_port_list != original_uut_port_list:
                    log.warning("UUT PoE Ports have been CHANGED to fit the available equipment for debug testing!")
                    log.warning("This is not normal and should NOT be allowed in production!")
                    log.warning("Also check the _config.py to ensure proper setup (esp. add_configuration_data).")
                    if aplib.get_apollo_mode() == 'PROD':
                        log.error("PRODUCTION MODE detected!")
                        raise aplib.apexceptions.AbortException
            elif len(uut_port_list) % self._shareports == 0 and len(uut_port_list) > self._shareports:
                log.warning("The PoE Equipment will be shared across UUT ports (group of {0})".format(self._shareports))
                log.warning("Ensure the test sequencing can pause for any setup change from one shareport group to the next.")
                if False:
                    # No need to change poe_equip_port_map_list since all methods will "see" only the equipment ports available.
                    poe_equip_port_map_list_new = []
                    for g in range(0, (len(uut_port_list) / self._shareports)):
                        for p in range(0, self._shareports):
                            poe_equip_port_map_list_new.append(poe_equip_port_map_list[p])
                    poe_equip_port_map_list = poe_equip_port_map_list_new
            else:
                log.error("The configuartion data for PoE 'shareports'={0} is invalid.".format(self._shareports))
                if aplib.get_apollo_mode() == 'PROD':
                    log.error("PRODUCTION MODE detected!")
                    raise aplib.apexceptions.AbortException
        elif len(uut_port_list) < len(poe_equip_port_map_list):
            log.warning("UUT PoE port list (smaller) does NOT map 1:1 to PoE Equipment port list!")
            log.warning("The extra equipment will be ignored.")

        log.info("PoE Equip Ports : {0}".format(poe_equip_port_map_list))
        log.info("UUT PoE Ports   : {0}".format(uut_port_list))

        # Create a port lookup table  UUT <--> POE Equip
        self._port_lookup = {p: poe_equip_port_map_list[i] for i, p in enumerate(uut_port_list)}
        log.debug("Mapping         : {0}".format(self._port_lookup))

        # Check if ALL ports are used per box. (This helps to speed up command entry.)
        if len(uut_port_list) >= self.MAX_PORTS and len(uut_port_list) % self.MAX_PORTS == 0:
            log.debug("Full port usage per PoE Equipment unit.")
            self._full_ports = True

        self._uut_poe_ports = uut_port_list
        return

    @property
    def uut_poe_type(self):
        return self._uut_poe_type

    @uut_poe_type.setter
    def uut_poe_type(self, newvalue):
        self._uut_poe_type = newvalue

    # User Methods ------------------------------------------------------
    def show_equipment(self):
        """ Show Equipment Setup
        :return:
        """
        log.debug("-" * 50)
        log.debug("UUT Container: {0}".format(self.container))
        log.debug("UUT Ports    : {0}".format(self.uut_poe_ports))
        log.debug("UUT PoE Type : {0}".format(self.uut_poe_type))
        for k in self.conn_names:
            conn = self._poe_equip[k]['conn']
            log.debug("Conn{0}: {1},  Host: {2},  Model: {3},  Ver: {4},  Portmap: {5},  SyncGroup: {6}{7}".
                      format(self._poe_equip[k]['index'],
                             self.get_name(conn),
                             conn.host,
                             self._poe_equip[k]['model'],
                             self._poe_equip[k]['version'],
                             self._poe_equip[k]['portmap'],
                             self._poe_equip[k]['syncgroup'],
                             ',  Pair: {}'.format(self._poe_equip[k]['pair']) if 'pair' in self._poe_equip[k] else ''
                             ))
        log.debug("-" * 50)
        return True

    def get_name(self, conn):
        return common_utils.get_conn_name(conn)

    def close(self):
        log.debug("Closing PoE Equipment...")
        for k in self.conn_names:
            conn = self._poe_equip[k]['conn']
            log.debug("Conn{0}: {1}".format(self._poe_equip[k]['index'], self.get_name(conn)))
            conn.close()
        return True

    def reset_all(self):
        """ Reset ALL
        This will reset all PoE Equipment ports therefore any shared connections to the equipment must be managed
        in the syncgroup.  This method will manage everything automatically.
        :return:
        """
        kwargs = dict(self=self)
        log.debug("Waiting for sync of shared PoE Equipment...")
        aplib.sync_group(self.syncgroup, module='apollo.scripts.entsw.libs.equip_drivers.poe_loadbox', function='__sync_reset', **kwargs)
        return

    def reset(self):
        """ Reset
        This will only reset the respective PoE Equipment ports used by the UUT.
        :return:
        """
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} Reset for {1} ports {2}...".format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not self._full_ports else [1]
                for p in ports:
                    conn.sende('{0}reset\r'.format('p{} '.format(p) if not self._full_ports else ''), expectphrase=self.prompt, regex=True)
        return

    def connect(self, **kwargs):
        """ Connect
        :param (dict) kwargs:
               (str) ieee: Flag for forcing conformance to IEEE: on|off.  Default = 'off'.
               (str) detect_signature: Flag for setting detect signature resistance: ok|hi.
               (str) external: Flag for external reference port enable: on|off.
               (str) cisco: Flag for cisco signal detect: on|off.
               (str) auto: Flag for auto enable load on IEEE power good: on|off.
        :return:
        """
        ieee = kwargs.get('ieee', None)
        detect_signature = kwargs.get('detect_signature', 'ok')
        external = kwargs.get('external', 'on')
        auto = kwargs.get('auto', 'on')
        cisco = kwargs.get('cisco', 'off')
        use_full_ports = self._full_ports

        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} {1}Connect for {2} ports {3}...".format(k, 'IEEE ' if ieee else '', self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                target_ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not use_full_ports else [1]
                for p in target_ports:
                    pp = 'p{} '.format(p) if not use_full_ports else ''
                    if self.__class__.__name__ == 'PoEedgar4':
                        if self.uut_poe_type == 'UPOE':
                            conn.sende('{0}upoe on\r'.format(pp), expectphrase=self.prompt, regex=True)
                        else:
                            conn.sende('{0}upoe off\r'.format(pp), expectphrase=self.prompt, regex=True)
                    conn.sende('{0}detect {1}\r'.format(pp, detect_signature), expectphrase=self.prompt, regex=True)
                    conn.sende('{0}external {1}\r'.format(pp, external), expectphrase=self.prompt, regex=True)
                    conn.sende('{0}cisco {1}\r'.format(pp, cisco), expectphrase=self.prompt, regex=True)
                    if ieee:
                        conn.sende('{0}ieee {1}\r'.format(pp, ieee), expectphrase=self.prompt, regex=True)
                    conn.sende('{0}auto {1}\r'.format(pp, auto), expectphrase=self.prompt, regex=True)
                    conn.sende('{0}connect on\r'.format(pp), expectphrase=self.prompt, regex=True)
        return

    def disconnect(self):
        """ Disconnect
        :return:
        """
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} Disconnect for {1} ports {2}...".format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not self._full_ports else [1]
                for p in ports:
                    conn.sende('{0}connect off\r'.format('p{} '.format(p) if not self._full_ports else ''), expectphrase=self.prompt, regex=True)
        return

    def set_class(self, load_class=4):
        """ Set IEEE Class
        :param load_class: 1 thru 4  OR 'POE', 'POE+', 'UPOE'
        :return:
        """
        if isinstance(load_class, str) and load_class in self.LOAD_CLASSES.keys():
            load_class = self.LOAD_CLASSES[load_class]
        elif isinstance(load_class, int) and (0 <= load_class <= 4):
            pass
        else:
            log.warning("PoE IEEE Load Class not recognized.")
            log.warning("Defaulting to a low class for safety.")
            load_class = 2
        log.debug("PoE Load Class = {0}".format(load_class))

        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} IEEE Class for {1} ports {2}...".format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not self._full_ports else [1]
                for p in ports:
                    conn.sende('{0}class {1}\r'.format('p{} '.format(p) if not self._full_ports else '', load_class), expectphrase=self.prompt, regex=True)
        return

    def set_power_load(self, current_limit_mA=None, ieee=False, rapid=True):
        """ Set Power Load Limits
        If a current limit is not provided, then the default limits will be used based on equipment and poe type.
        :param (int) current_limit_mA: Current limit (milliamps)
        :param (bool) ieee: Flag to use the start-up current limit first (avoid in-rush overspec on older Edgars).
                            Using this requires a 3-step process of set/connect, then PSE power on,
                            then set at higher load.
        :param (bool) rapid: Flag to load many ports rapidly (this is an option to slowly turn on the loads).
        :return:
        """
        default_msg = ''
        if not current_limit_mA:
            default_msg = '  (default)'
            current_limit_mA = self.DEFAULT_CURRENT_LIMITS[self.uut_poe_type]
        self._power_load_current_limit = current_limit_mA
        if ieee:
            log.debug("Using IEEE in-rush current limit.")
            self._power_load_current_limit = self.DEFAULT_CURRENT_LIMITS['IEEE']

        if rapid and self._full_ports:
            use_global_command = True
        else:
            use_global_command = False

        log.debug("Power Load Current Limit: {0} mA{1}".format(self._power_load_current_limit, default_msg))
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} Current Limit for {1} ports {2}...".format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not use_global_command else [1]
                for p in ports:
                    pp = '{0}'.format('p{} '.format(p) if not use_global_command else '')
                    conn.sende('{0}set {1}\r'.format(pp, self._power_load_current_limit), expectphrase=self.prompt, regex=True)
                    if not rapid:
                        time.sleep(1.0)
        return

    def _map_data(self, raw_data, data, key):
        """ Map Data (SHARED METHOD)
        Translate data from PoE Equip ports to UUT ports data structure.
        :param raw_data:
        :param data:
        :param key:
        :return:
        """
        log.debug("Mapping key={0} data for PoE Equip to UUT ports...".format(key))
        for p in self.uut_poe_ports:
            k_port, k_conn = self._port_lookup[p][0], self._port_lookup[p][1]
            data[p] = {} if p not in data else data[p]
            if len(self._port_lookup[p]) == 4:
                k_port2, k_conn2 = self._port_lookup[p][2], self._port_lookup[p][3]
                rawd1 = raw_data.get(k_conn, {}).get(k_port, None)
                rawd2 = raw_data.get(k_conn2, {}).get(k_port2, None)
                data[p].update({key: (rawd1, rawd2)} if rawd2 else {key: rawd1})
            else:
                rawd1 = raw_data.get(k_conn, {}).get(k_port, None)
                data[p].update({key: rawd1})
        return data

    def set_load_on(self):
        """ Load ON
        :return:
        """
        self.__load_op('on')
        return

    def set_load_off(self):
        """ Load OFF
        :return:
        """
        self.__load_op('off')
        return

    def __load_op(self, state='off'):
        """ Load Operation (INTERNAL)
        :param state:
        :return:
        """
        if not any([state.lower() == s for s in ['on', 'off']]):
            log.error("PoE Load operation not recognized.")
            return
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} Load {1} for {2} ports {3}...".format(k, state.upper(), self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                ports = common_utils.expand_comma_dash_num_list(self._poe_equip[k]['portmap']) if not self._full_ports else [1]
                for p in ports:
                    conn.sende('{0}load {1}\r'.format('p{} '.format(p) if not self._full_ports else '', state), expectphrase=self.prompt, regex=True)
        return

    def echo_msg(self, msg):
        log.debug("Sending msg to PoE Equip: {0}".format(msg))
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            for k in self.conn_names:
                log.debug("{0} Msg...".format(k))
                conn = self._poe_equip[k]['conn']
                conn.send('*echo {0}\r'.format(msg), expectphrase=self.prompt, regex=True)

    def get_instrument_data(self):
        return None

    def _clear_recbuf(self, uut_conn, force=False):
        if self.USE_CLEAR_RECBUF or force:
            uut_conn.clear_recbuf()
            time.sleep(self.RECBUF_CLEAR_TIME)
        return


# ----------------------------------------------------------------------------------------------------------------------
class PoEedgar3(PoEedgarGeneric):
    """ PoE Edgar3
    Note: Edgar3 has no UPOE capability.  Testing is achieved via dual load boxes connected via an external wire
          splitter.  UPOE current limit is set to half the rated amount which is near max per box (or close to POE+).
    """
    MODELS = ['Edgar', 'Edgar3A', 'Edgar3B', 'RT-PoE3', 'RT-PoE3+', 'RT-PoE3A', 'RT-PoE3B', 'RT-PoE3/24']
    MAX_PORTS = 24
    DEFAULT_CURRENT_LIMITS = {'IEEE': 200, 'poe1': 20, 'poe2': 30, 'POE': 280, 'POE+': 540, 'UPOE': 540}

    def __init__(self, poe_equip, uut_poe_ports, **kwargs):
        super(PoEedgar3, self).__init__(poe_equip, uut_poe_ports, **kwargs)
        return

    def get_instrument_data(self, verbose=False):
        """
        Samples:
        measure
        :p1 0.0V
        :p2 0.0V
        ...
        status
        :p18 PWR 0
        :p19 PWR 0
        ...
        temperature
        :p13  25 C
        :p14  26 C

        :param (bool) verbose:
        :return (dict) data: Form of {<uut port>: <value1>, ...}
        """
        log.debug("Get Instrument (Edgar3)")
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            raw_data = {}
            data = {}
            for k in self.conn_names:
                log.debug("{0} Voltage Data for {1} ports {2}...".
                          format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                self._clear_recbuf(conn)
                conn.sende('measure\r', expectphrase=self.prompt, regex=True)
                pat = re.compile(':p([0-9]{1,2}) ([\S]+)V')
                m = pat.findall(conn.recbuf)
                raw_data[k] = {int(p): float(v1) for p, v1 in m} if m else {}
            data = self._map_data(raw_data, data, key='volt')

            for k in self.conn_names:
                log.debug("{0} Power Data for {1} ports {2}...".
                          format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                self._clear_recbuf(conn)
                conn.sende('status\r', expectphrase=self.prompt, regex=True)
                pat = re.compile(':p([0-9]{1,2}) PWR ([\d]+)')
                m = pat.findall(conn.recbuf)
                raw_data[k] = {int(p): float(v1) for p, v1 in m} if m else {}
            data = self._map_data(raw_data, data, key='power')

            for k in self.conn_names:
                log.debug("{0} NO Temperature Data for {1} ports {2} (not supported).".
                          format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                raw_data[k] = {}
            data = self._map_data(raw_data, data, key='temp')

        log.debug("Instrument data acquisition done.")
        if verbose:
            log.debug("Acquired data:")
            for i in data:
                log.debug("{0}: {1}".format(i, data[i]))
        return data


# ----------------------------------------------------------------------------------------------------------------------
class PoEedgar4(PoEedgarGeneric):
    """ PoE Edgar4

    System Commands:
      he[lp]                        - this output
      vers[ion]                     - display hardware and software version
      err[ors]                      - report command error status
      host[name] name               - set unit's host name; max 31 characters
      *program                      - program the controller or linecard flash
      *baud <baudrate>              - set console baudrate (9600, 19200, etc)
      *boot                         - reset to power-on state
      *echo <string>                - responds with <string> (use to test console port)
      *debug [0|1]                  - debug mode off or on (verbose output)

    Port Command Prefix:
      (none)        - all ports
      pN            - port N only (N is 1 to max # of ports)
      gN            - group N only; N = 1, 2, or 3 for ports 1-8, 9-16, 17-24

    Port Commands:
      auto [on|off]                 - auto enable load on IEEE power good
      cal                           - internally calibrate port class and power load
      cap [on|off]                  - 10uF cap signature
      cisco [on|off]                - cisco signature loopback
      upoe [on|off]                 - set UPOE mode
      cl[ass] [0|1|2|3|4]           - set IEEE class
      conn[ect] [on|off]            - PoE tester circuits on or off
      det[ect] [ok|hi]              - set IEEE detect signature resistance
      ext[ernal] [on|off]           - external reference port enable
      lo[ad] [on|off]               - power load on or off
      meas[ure]                     - measure voltage on PoE pair
      meas[ure]2                    - measure voltage on UPoE pairs
      res[et]                       - reset to fully disconnected state
      set NNN [mA]                  - set power load to NNN milliamps
      sh[ort] [on|off]              - shorting relay applied directly across PoE pair
      stat[us]                      - IEEE PoE power good status
      temp[erature]                 - Get the on board temperature reading

    """
    MODELS = ['Edgar4', 'RT-PoE4/24', 'RT-PoE4/10G/24']
    MAX_PORTS = 24
    DEFAULT_CURRENT_LIMITS = {'IEEE': 200, 'poe1': 20, 'poe2': 30, 'POE': 280, 'POE+': 540, 'UPOE': 1120}

    def __init__(self, poe_equip, uut_poe_ports, **kwargs):
        super(PoEedgar4, self).__init__(poe_equip, uut_poe_ports, **kwargs)
        return

    def get_instrument_data(self, verbose=False):
        """
        Samples:
        measure
        :p1 0.0V
        :p2 0.0V
        ...
        measure2
        :p18 0.0V, 0.0V
        :p19 0.0V, 0.0V
        ...
        status
        :p18 PWR 0,0
        :p19 PWR 0,0
        ...

        :param (bool) verbose:
        :return (dict):
        """
        log.debug("Get Instrument (Edgar4)")
        with locking.named_priority_lock('__poe_equip__' + self.syncgroup):
            raw_data = {}
            data = {}
            log.debug("")
            for k in self.conn_names:
                log.debug("{0} Instrument Data for {1} ports {2}...".
                          format(k, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[k]['conn']
                self._clear_recbuf(conn)
                if self.uut_poe_type == 'UPOE':
                    conn.sende('measure2\r', expectphrase=self.prompt, regex=True)
                    pat = re.compile(':p([0-9]{1,2}) ([\S]+)V, ([\S]+)V')
                    m = pat.findall(conn.recbuf)
                    raw_data[k] = {int(p): (float(v1), float(v2)) for p, v1, v2 in m} if m else {}
                else:
                    conn.sende('measure\r', expectphrase=self.prompt, regex=True)
                    pat = re.compile(':p([0-9]{1,2}) ([\S]+)V')
                    m = pat.findall(conn.recbuf)
                    raw_data[k] = {int(p): float(v1) for p, v1 in m} if m else {}
            data = self._map_data(raw_data, data, key='volt')

            for x in self.conn_names:
                log.debug("{0} Power Data for {1} ports {2}...".
                          format(x, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[x]['conn']
                self._clear_recbuf(conn)
                conn.sende('status\r', expectphrase=self.prompt, regex=True)
                pat = re.compile(':p([0-9]{1,2}) PWR ([\d]+),([\d]+)')
                m = pat.findall(conn.recbuf)
                raw_data[x] = {int(p): (float(v1), float(v2)) for p, v1, v2 in m} if m else {}
            data = self._map_data(raw_data, data, key='power')

            for x in self.conn_names:
                log.debug("{0} Temperature Data for {1} ports {2}...".
                          format(x, self.uut_poe_type, self._poe_equip[k]['portmap']))
                conn = self._poe_equip[x]['conn']
                self._clear_recbuf(conn)
                conn.sende('temperature\r', expectphrase=self.prompt, regex=True)
                pat = re.compile(':p([0-9]{1,2})[ \t]+([\d]+) C')
                m = pat.findall(conn.recbuf)
                raw_data[x] = {int(p): float(v1) for p, v1 in m} if m else {}
            data = self._map_data(raw_data, data, key='temp')

        log.debug("Instrument data acquisition done.")
        if verbose:
            log.debug("Acquired data:")
            for i in data:
                log.debug("{0}: {1}".format(i, data[i]))
        return data


# ----------------------------------------------------------------------------------------------------------------------
class PoEedgar5(PoEedgarGeneric):
    MODELS = ['Edgar5', 'RT-PoE5/24', 'RT-PoE5/10G/24']
    MAX_PORTS = 24
    DEFAULT_CURRENT_LIMITS = {'IEEE': 200, 'poe1': 20, 'poe2': 30, 'POE': 280, 'POE+': 540, 'UPOE': 1120, 'UPOE+': 1600}

    def __init__(self, poe_equip, uut_poe_ports, **kwargs):
        super(PoEedgar5, self).__init__(poe_equip, uut_poe_ports, **kwargs)
        return


# ----------------------------------------------------------------------------------------------------------------------
class PoEodin(PoEedgarGeneric):
    """
        /supervisor/short -d 0
        /supervisor/set_class -p 0..47 -d 0
        /supervisor/set_current_limit -p 0..47 -d 0

        /chassis/powersupply0/supply_shutdown -s off
        /chassis/powersupply1/supply_shutdown -s off

        /supervisor/pd_power_enable -p 0..47 -d 1       <<<<<both PDs are enabled but only pri is up on UUT
        /supervisor/pd_power_enable -p 0..47

        /supervisor/pd_power_enable -p 0..47 -d 0
        /supervisor/pd_power_enable -p 0..47

        /supervisor/set_class -p 0..47 -d 0
        /supervisor/set_class -p 0..47

        /supervisor/voltage -p 0..47

        /supervisor/set_class -p 0..47 -d 1
        /supervisor/set_class -p 0..47

        /supervisor/set_class -p 0..47 -d 2
        /supervisor/set_class -p 0..47

        /supervisor/set_class -p 0..47 -d 3
        /supervisor/set_class -p 0..47

        /supervisor/set_class -p 0..47 -d 4
        /supervisor/set_class -p 0..47

        /supervisor/set_current_limit -p 0..47 -d 100
        /supervisor/set_class -p 0..47

        /supervisor/set_current_limit -p 0..47 -d 250
        /supervisor/set_class -p 0..47

        /supervisor/set_current_limit -p 0..47 -d 500
        /supervisor/set_class -p 0..47

        /supervisor/set_current_limit -p 0..47 -d 560
        /supervisor/set_class -p 0..47

        /supervisor/short -d 0
        /supervisor/set_class -p 0..47 -d 0
        /supervisor/set_current_limit -p 0..47 -d 0

        /chassis/powersupply0/supply_shutdown -s on
        /chassis/powersupply1/supply_shutdown -s on
    """
    MODELS = ['Odin', 'WS-C4948E']
    MAX_PORTS = 48
    DEFAULT_CURRENT_LIMITS = {'IEEE': 200, 'poe1': 20, 'poe2': 30, 'POE': 320, 'POE+': 640, 'UPOE': 1200}

    def __init__(self, poe_equip, uut_poe_ports, **kwargs):
        super(PoEodin, self).__init__(poe_equip, uut_poe_ports, **kwargs)
        self._poe_equip = poe_equip
        self._uut_poe_ports = uut_poe_ports  # UUT ports attached to the PoE Equipment
        self._uut_poe_type = kwargs.get('uut_poe_type', 'POE')  # types: POE, POE+, UPOE
        self._container = kwargs.get('container', aplib.get_my_container_key().split('|')[-1])
        self._verbose = kwargs.get('verbose', False)

        if not isinstance(self._poe_equip, dict):
            log.error("The 'poe_equip' parameter must be in dict form.")
            raise aplib.apexceptions.AbortException

        for k in self._poe_equip.keys():
            if not all([i in self._poe_equip[k].keys() for i in ['model', 'version', 'conn', 'portmap', 'syncgroup']]):
                log.error("The 'poe_equip' parameter does not contain all the required keys:")
                log.error(" Required: {0}".format(sorted(['model', 'version', 'conn', 'portmap', 'syncgroup'])))
                log.error(" Results : {0}".format(sorted(self._poe_equip.keys())))
                raise aplib.apexceptions.AbortException

        return

    def reset(self):
        return

    def connect(self, **kwargs):
        return

    def disconnect(self):
        return

    def set_class(self, load_class=4):
        return

    def set_power_load(self, current_limit_mA=None):
        return

    def set_load_on(self):
        return

    def set_load_off(self):
        return

    def get_instrument_data(self):
        log.debug("Get Instrument (Odin)")
        return
