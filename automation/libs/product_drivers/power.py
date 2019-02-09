"""
Power
"""

# Python
# ------
import sys
import time
import re
import logging

# Apollo
# ------
import apollo.libs.lib as aplib
import apollo.libs.locking as locking

# BU Lib
# ------
from apollo.scripts.entsw.libs.utils.common_utils import apollo_step

__title__ = "Catalyst Power General Module"
__version__ = '2.0.0'
__author__ = ['bborel']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

if not hasattr(aplib.conn, 'uutTN'):
    setattr(aplib.conn, 'uutTN', type('Conn', (), {'uid': 1, 'send': 1, 'power_on': 1}))


class Power(object):
    POTENTIAL_CHANNELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

    def __init__(self, mode_mgr, ud):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._uut_conn = self._mode_mgr.uut_conn
        self.connA, self.connB, self.connC, self.connD = None, None, None, None
        self.connE, self.connF, self.connG, self.connH = None, None, None, None
        self.__available_channels = []
        if self._ud.apollo_go:
            all_conn_names = aplib.getconnections().keys()
            log.debug("Scanning for power connections in: {0}".format(all_conn_names))
            setattr(self, 'connA', getattr(aplib.conn, 'uutTN', None))         # Default (tied to uut console)
            if getattr(aplib.conn, 'uutPOWER', None):
                setattr(self, 'connA', getattr(aplib.conn, 'uutPOWER', None))  # 2nd choice; USB equipment
            self.__available_channels.append(('A', self.connA)) if self.connA else None
            for c in self.POTENTIAL_CHANNELS:
                conn_name = 'conn{0}'.format(c)
                conn = getattr(aplib.conn, 'uutPS{0}'.format(c), None)         # 3rd choice: separate conns
                if conn:
                    setattr(self, conn_name, conn)
                    log.debug("Found uutPS{0}".format(c))
                    self.__available_channels.append((c, conn))
        log.info("Available power channels = {0}".format(self.__available_channels))
        self._callback = None
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    @property
    def available_channels(self):
        return self.__available_channels
    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def on(self, **kwargs):
        """ ON
        :param kwargs:
        :return:
        """
        channels = kwargs.get('channels', 'ALL')
        wait_for_boot = kwargs.get('wait_for_boot', True)

        bypass = False
        container_key = aplib.get_my_container_key()
        log.info('CONTAINER_KEY:')
        log.info('{0}'.format(container_key))
        container = container_key.split("|")[-1]
        pl, ar, ts, _ = container_key.split("|", 3)

        # 1. Check for power dependencies
        if self._ud.category == 'MODULAR':
            active_modular_name = '_'.join([pl, ar, ts, 'ActiveModular'])
            with locking.ContainerPriorityLock('__active_modular__'):
                active_modular = aplib.get_cached_data(active_modular_name)
                if not active_modular:
                    log.error("No active modular stations; please activate a UUT for allocation.")
                    return aplib.FAIL
                if container == active_modular[0] and self._uut_conn.status != aplib.STATUS_OPEN:
                    log.debug("Modular; primary connection for power on.")
                    bypass = False
                else:
                    log.debug("Modular; shared connection and/or connection already open.")
                    bypass = True

        # 2. Skip power if allowed
        if bypass:
            log.info("BYPASS: No power cycle.")
            return aplib.PASS

        # 3. Perform the power operation !!
        self.__power_operation(op='ON', channels=channels)

        # 4. UUT Boot process
        if not wait_for_boot:
            log.warning("Skip standard wait for boot after power on.")
            return aplib.PASS
        aplib.set_container_text('BOOT')
        log.info('Booting up unit')
        # Standard search for bootup after a power cycle.
        time.sleep(5.0)
        result, _ = self._mode_mgr.wait_for_boot()

        # NOTE: If the UUT is hardwired for "constant on" then this has no effect.
        return aplib.PASS if result else (aplib.FAIL, 'UUT wait for boot did not complete.')

    @apollo_step
    def off(self, **kwargs):
        """ OFF
        :param kwargs:
        :return:
        """
        channels = kwargs.get('channels', 'ALL')

        container_key = aplib.get_my_container_key()
        log.info('CONTAINER_KEY:')
        log.info('{0}'.format(container_key))
        pl, ar, ts, _ = container_key.split("|", 3)

        # 1. Check for power dependencies
        if self._ud.category == 'MODULAR':
            active_modular_name = '_'.join([pl, ar, ts, 'ActiveModular'])
            with locking.ContainerPriorityLock('__active_modular__'):
                active_modular = aplib.get_cached_data(active_modular_name)
                if active_modular:
                    if len(active_modular) > 1:
                        log.debug("More than one modular UUT container is active; cannot power off.")
                        log.debug("Active: {0}".format(active_modular))
                        return aplib.SKIPPED
                    elif len(active_modular) == 1:
                        log.debug("One active modular container left; stay powered on.")
                        log.debug("Active: {0}".format(active_modular))
                        return aplib.SKIPPED
                    else:
                        log.debug("NO active modular containers!")
                        log.debug("Power OFF is allowed.")

        # 2. Determine OFF state
        if self._ud.keep_connected:  # or aplib.get_apollo_mode() == aplib.MODE_DEBUG:
            log.warning("*" * 50)
            log.warning("UUT CONNECTION IS STILL OPEN.\n"
                        " This can occur on an error, on abort, or intentionally by script.\n"
                        " If this connection is used by a different container, it will fail to start until"
                        " the connection is manually closed.\n"
                        " The connection is typically left in this state for production debug.\n"
                        " Close the connection when done OR restart this same container.")
            log.warning("*" * 50)
            return aplib.PASS

        # 3. Perform the power operation !!
        self.__power_operation(op='OFF', channels=channels)
        return aplib.PASS

    @apollo_step
    def cycle_on(self, **kwargs):
        """ Cycle ON
        :param kwargs:
        :return:
        """
        kwargs.setdefault('channels', 'ALL')
        self.off(**kwargs)
        time.sleep(3)
        self.on(**kwargs)
        return aplib.PASS

    @apollo_step
    def power_cycle_testing(self, **kwargs):
        """ Power Cycle Testing (STEP)
        :param (dict) kwargs:
        :return (str): aplib.PASS/FAIL
        """
        if 'max_power_cycles' in self._ud.uut_config:
            max_power_cycles = self._ud.uut_config['max_power_cycles']
            log.debug("Max power cycles from product definition: {0}.".format(max_power_cycles))
        else:
            max_power_cycles = kwargs.get('max_power_cycles', 2)
            log.debug("Max power cycles from args/default: {0}.".format(max_power_cycles))

        result_list = []
        for cycle in range(1, max_power_cycles + 1):
            msg = "POWER CYCLE: Loop #{0}/{1}".format(cycle, max_power_cycles)
            log.info("-" * len(msg))
            log.info(msg)
            log.info("-" * len(msg))
            result_list.append(True) if self.cycle_on() == aplib.PASS else result_list.append(False)

        result = all(result_list)
        msg = "POWER CYCLE SUMMARY: {0}".format(result)
        log.info("POWER CYCLE: END")
        log.info("-" * len(msg))
        log.info(msg)
        log.info("-" * len(msg))
        return aplib.PASS if result else aplib.FAIL

    # ==================================================================================================================
    # USER Methods (step support +)
    # ==================================================================================================================
    def _open_on(self):
        channels_to_power_on = []
        log.debug("Available channels: {0}".format(self.__available_channels))
        for channel, uut_pwr_conn in self.__available_channels:
            if uut_pwr_conn:
                status = self.__power_operation_workhorse(op='STATUS', channel=channel, verbose=True)
                if status != aplib.STATUS_OPEN:
                    log.debug("'{0}' != '{1}'".format(status, aplib.STATUS_OPEN))
                    log.info("Channel={0} power control for UUT needs to be opened...".format(channel))
                    channels_to_power_on.append(channel)

        log.debug("Channels to open on: {0}".format(channels_to_power_on))
        if channels_to_power_on:
            result = self.on(channels=channels_to_power_on)
        else:
            log.debug("No power on required.")
            result = True
        return True if result == aplib.PASS else False

    # INTERNAL ---------------------------------------------------------------------------------------------------------
    #
    def __power_operation(self, op='', channels=[], verbose=True):
        """ Power Operation (INTERNAL)
        Wrapper for __power_operation_workhorse()... see docstring there.

        USAGE:
        See cycle_on(...)
            off(...)

        For multi power supplies, this will perform one op at a time for all power supplies (i.e. channels)
        :param op:
        :param channels:
        :param verbose:
        :return:
        """
        channels = [c for c, o in self.__available_channels] if str(channels).upper() == 'ALL' else channels
        channels = [channels] if not isinstance(channels, list) else channels
        op = ['OFF', 'ON'] if op == 'CYCLE' else [op]
        for op_step in op:
            for channel in channels:
                self.__power_operation_workhorse(op=op_step, channel=channel, verbose=verbose)
        return True

    def __power_operation_workhorse(self, op='', channel='', verbose=True):
        """ (INTERNAL) Power Operation Workhorse
        Do not call this directly, instead use "__power_operation()".

        This is a power operation routine (on/off) for the UUT using one of two devices:
         1) the standard RS-232 console with modem-DTR attached to a relay box, or
         2) the two USB Term Server vendors: Lantronix & OpenGear also using the RS-232 ports for modem-DTR control.

        This routine is also used for 1:1 UUT based equipment that needs power on/off coordination with the UUT.
        Currently, some stations (e.g. BST) use independent fan modules for UUT cooling;
        these are controlled via the 'stnFAN' connection.

        Power Connection (NOT USED)
        ---------------------------
        The desired solution is to use the Apollo 'power_connection' attrib of the UUT connection in _config.py.
        The RS-232 port MUST have automatic assert/deassert of DTR when making the connection to the RS-232 ports.
        Lantronix:
            1) Does not currently have this capability (Dec 2017); but they are building it in.
            2) Current solution: use "assertdtr enable/disable"
        OpenGear:
            1) Does have this feature with dtrmode=activeuser BUT the power connection must be setup in config.py.
               We will currently NOT use this feature; therefore NO power connection.
            2) Current solution: use dtrmode=activeuser/alwayson  AND NO RS-232 telent connection via Apollo.

        USB Reset
        ----------
        Lantronix:
            1) Automatically resets but must wait after UUT power-on.
        OpenGear:
            1) Needs explicit reset of the USB port after the UUT powers on; must have im72xx-4.0.1u1.flash or newer image.
            2) For a small percentage of time, a USB connection failure can occur IF the USB reset is NOT done.

        Note: Both USB Terminal Servers require a specific configuration. (See docs for further details. TBD)

        :param (str) channel: Specific power equipment controller- 'A', 'B', 'C', 'D', etc.
                              This will correspond to the UUT's PSUs.
        :param (str) op: 'CYCLE', 'ON', 'OFF', 'STATUS'
        :param (bool) verbose:
        :return:
        """

        def __logdebug(msg):
            log.debug(msg) if verbose else None

        def __loginfo(msg):
            log.info(msg) if verbose else None

        op = op.upper()
        log.info("POWER {0} for {1}...".format(op, channel))

        port_offset = 0
        channel = channel.upper()
        uut_pwr_conn = None
        conn = None

        OPENGEAR_USB_HUB_PORT_MAP = {
            # Syntax = <UUT#>: (<hub loc>, <hub port>, <physical port>)
            1: ('3-1', 1, 17), 2: ('3-1', 2, 18), 3: ('3-1', 3, 19), 4: ('3-1', 4, 20), 5: ('3-1', 5, 21),
            6: ('3-1', 6, 22),
            7: ('3-2', 1, 23), 8: ('3-2', 2, 24), 9: ('3-2', 3, 25), 10: ('3-2', 4, 26), 11: ('3-2', 5, 27),
            12: ('3-2', 6, 28),
            13: ('5-3', 1, 29), 14: ('5-3', 2, 30), 15: ('5-3', 3, 31), 16: ('5-3', 4, 32),
            # These USB ports are NOT used since we do NOT have matching RS-232 ports!
            # 17: ('5-3', 5, 33), 18: ('5-3', 6, 34),
            # 19: ('5-4', 1, 35), 20: ('5-4', 2, 36), 21: ('5-4', 3, 37), 22: ('5-4', 4, 38), 23: ('5-4', 5, 39), 24: ('5-4', 6, 40),
        }

        # Assign alias' --------
        if channel == 'A':
            if self.connA and self.connA != self._mode_mgr.uut_conn:
                uut_pwr_conn = self.connA
            conn = self._mode_mgr.uut_conn
        elif channel == 'B' and self.connB:
            uut_pwr_conn = self.connB
            port_offset = 16 if uut_pwr_conn.model.lower() == 'lantronix' or uut_pwr_conn.model.lower() == 'opengear' else 0
        elif channel == 'C' and self.connC:
            uut_pwr_conn = self.connC
        elif channel == 'D' and self.connD:
            uut_pwr_conn = self.connD
        elif channel == 'E' and self.connE:
            uut_pwr_conn = self.connE
        elif channel == 'F' and self.connF:
            uut_pwr_conn = self.connF
        elif channel == 'G' and self.connG:
            uut_pwr_conn = self.connG
        elif channel == 'H' and self.connH:
            uut_pwr_conn = self.connH

        if not uut_pwr_conn and not conn:
            __logdebug("Power channel: '{0}' is NOT available.".format(channel))
            return

        uut_pwr_conn.clear_recbuf() if uut_pwr_conn else None
        __logdebug("Channel     : {0}".format(channel))
        __logdebug("UUT Pwr Conn: {0}".format(uut_pwr_conn))
        __logdebug("UUT Conn    : {0}".format(conn))
        time.sleep(1.0)

        # Both Lantronix & OpenGear have 16 usable USB ports so normalize UUT index against their max usable port count.
        port_boundary = 16
        normalized_uut_index = ((self._ud.uut_index - 1) % port_boundary) + 1 if ((self._ud.uut_index - 1) % port_boundary) != 0 else 1

        # Power OFF ----------
        if op in ['CYCLE', 'OFF']:
            __logdebug("OFF-->") if verbose else None
            if conn and not uut_pwr_conn:
                __loginfo("Integrated {0} PSU OFF.".format(channel))
                conn.power_off()
                conn.close()
            if conn and uut_pwr_conn:
                __loginfo("Separate console; disconnect.")
                conn.close()
            if uut_pwr_conn:
                p = normalized_uut_index + port_offset
                __loginfo("Separate {0} PSU OFF.".format(channel))
                uut_pwr_conn.open()
                time.sleep(1)
                if uut_pwr_conn.model.lower() == 'lantronix':
                    __logdebug("Lantronix")
                    uut_pwr_conn.send('set deviceport port {0} assertdtr disable\r'.format(p), expectphrase='> ',
                                      timeout=30)
                    __logdebug("Disconnect USB port={0}".format(p))
                    time.sleep(1)
                    uut_pwr_conn.close() if op == 'OFF' else None
                elif uut_pwr_conn.model.lower() == 'opengear':
                    __logdebug("OpenGear")
                    # Note: For this to work, the RS-232 port must NOT be connected by Apollo via telnet/ssh.
                    # uut_pwr_conn.send('config -s config.ports.port{0}.dtrmode=activeuser -r serialconfig\r'.format(p), expectphrase='# ', timeout=30)
                    uut_pwr_conn.send('config -s config.ports.port{0}.dtrmode=alwayson -r serialconfig\r'.format(p),
                                      expectphrase='# ', timeout=30)
                    __logdebug("Disconnect USB port={0}".format(p))
                    usb_hub_loc = OPENGEAR_USB_HUB_PORT_MAP[p][0]
                    usb_hub_port = OPENGEAR_USB_HUB_PORT_MAP[p][1]
                    __logdebug("Connect USB port={0}  Location={1}  HubPort={2}".format(p, usb_hub_loc, usb_hub_port))
                    uut_pwr_conn.send('uhubctl -l {0} -p {1} -a 0\r'.format(usb_hub_loc, usb_hub_port),
                                      expectphrase='# ', timeout=30)
                    uut_pwr_conn.send('pmshell -l port{0:02d} --dtr 0\r'.format(p), expectphrase='# ', timeout=30)
                    time.sleep(1)
                    uut_pwr_conn.close() if op == 'OFF' else None
                else:
                    uut_pwr_conn.power_off()
            # if 'FANGROUP' in aplib.get_container_sync_groups():
            #    _op_station_fans('OFF')
            __logdebug("<--OFF")
            time.sleep(5.0)

        # Power ON -----------
        if op in ['CYCLE', 'ON']:
            __logdebug("ON-->")
            if conn and uut_pwr_conn:
                __loginfo("Separate console; connect.")
                conn.open()
                time.sleep(2)
            if conn and not uut_pwr_conn:
                __loginfo("Integrated {0} PSU ON.".format(channel))
                conn.power_on()
            if uut_pwr_conn:
                p = normalized_uut_index + port_offset
                __loginfo("Separate {0} PSU ON.".format(channel))
                uut_pwr_conn.open()
                time.sleep(1)
                if uut_pwr_conn.model.lower() == 'lantronix':
                    __logdebug("Lantronix")
                    uut_pwr_conn.send('set deviceport port {0} assertdtr enable\r'.format(p), expectphrase='> ',
                                      timeout=30)
                    __logdebug("Connect USB port={0}".format(p))
                elif uut_pwr_conn.model.lower() == 'opengear':
                    __logdebug("OpenGear")
                    # Note: For this to work, the RS-232 port must NOT be connected by Apollo via telnet/ssh.
                    usb_hub_loc = OPENGEAR_USB_HUB_PORT_MAP[p][0]
                    usb_hub_port = OPENGEAR_USB_HUB_PORT_MAP[p][1]
                    __logdebug("Connect USB port={0}  Location={1}  HubPort={2}".format(p, usb_hub_loc, usb_hub_port))
                    # uut_pwr_conn.send('uhubctl -l {0} -p {1} -a 2\r'.format(usb_hub_loc, usb_hub_port), expectphrase='# ', timeout=30)
                    # __logdebug("OpenGear waiting 10 secs...")
                    # time.sleep(10.0)
                    uut_pwr_conn.send('pmshell -l port{0:02d} --dtr 1\r'.format(p), expectphrase='# ', timeout=30)
                    uut_pwr_conn.send('uhubctl -l {0} -p {1} -a 1\r'.format(usb_hub_loc, usb_hub_port),
                                      expectphrase='# ', timeout=30)
                    # uut_pwr_conn.send('pmshell -l port{0:02d}\r'.format(p + port_boundary), expectphrase='# ', timeout=30)
                    # uut_pwr_conn.send('config -s config.ports.port{0}.dtrmode=alwayson -r serialconfig\r'.format(p), expectphrase='# ', timeout=30)
                    # __logdebug("OpenGear waiting 10 secs...")
                    time.sleep(1.0)
                    conn.send('\r', expectphrase='.*', timeout=30, regex=True) if conn else None
                else:
                    uut_pwr_conn.power_on()
            #if 'FANGROUP' in aplib.get_container_sync_groups():
            #    _op_station_fans('ON')
            __logdebug("<--ON")
            time.sleep(2)

        # Power STATUS -----------
        if op == 'STATUS':
            __logdebug("STATUS-->")
            status = None
            if uut_pwr_conn:
                p = normalized_uut_index + port_offset
                __loginfo("Separate {0} PSU STATUS.".format(channel))
                uut_pwr_conn.open()
                time.sleep(1)
                if uut_pwr_conn.model.lower() == 'lantronix':
                    __logdebug("Lantronix")
                    pat = 'Assert D[ST]R: (disabled|enabled)'
                    uut_pwr_conn.send('admin version\r', expectphrase='> ', timeout=30)
                    uut_pwr_conn.send('show deviceport port {0} display data\r'.format(p), expectphrase='> ', timeout=30)
                    time.sleep(3)
                    m = re.search(pat, uut_pwr_conn.recbuf)
                    status = aplib.STATUS_OPEN if m and m.group(1) == 'enabled' else aplib.STATUS_CLOSED
                elif uut_pwr_conn.model.lower() == 'opengear':
                    __logdebug("OpenGear")
                    pat = 'label (.*)'
                    uut_pwr_conn.send('cat /etc/version\r', expectphrase='# ', timeout=30)
                    uut_pwr_conn.send('config -g config.ports.port{0}\r'.format(p), expectphrase='# ', timeout=30)
                    time.sleep(3)
                    m = re.search(pat, uut_pwr_conn.recbuf)
                    __logdebug(m)
                    status = aplib.STATUS_OPEN if m and m.group(1) != '' else aplib.STATUS_CLOSED
                else:
                    status = uut_pwr_conn.status
            if conn and not uut_pwr_conn:
                __loginfo("Integrated {0} PSU STATUS.".format(channel))
                status = conn.status
            __loginfo("Power Status = {0}".format(status))
            __logdebug("<--STATUS")
            return status

        return

