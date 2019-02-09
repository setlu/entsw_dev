import abc

__author__ = 'bborel'
__title__ = "Traffic Driver Base"
__version__ = '0.1.0'


class TrafficBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, uut_conn, uut_prompt, **kwargs):

        # Internals
        self._kwargs = kwargs
        self._uut_conn = uut_conn
        self._uut_prompt = uut_prompt
        self._poe_loadbox_driver = kwargs.get('poe_loadbox_driver', None)  # poe equip driver object
        self._poe_uut_func = kwargs.get('poe_uut_func', None)              # poe function for UUT
        self._vmargin_func = kwargs.get('vmargin_func', None)              # voltage margining function
        self._traffic_cases = kwargs.get('traffic_cases', {})              # traffic cases dict
        self._mm = kwargs.get('mm', None)                                  # MachineManager

    # Properties -------------------------------------------------------------------------------------------------------
    # Read-only
    @abc.abstractproperty
    def container(self):
        raise NotImplementedError("Need 'container' getter property implementation.")

    # Read/Write
    @abc.abstractproperty
    def uut_conn(self):
        raise NotImplementedError("Need 'uut_conn' getter property implementation.")

    @uut_conn.setter
    def uut_conn(self, newvalue):
        self._uut_conn = newvalue
        raise NotImplementedError("Need 'uut_conn' setter property implementation.")

    @abc.abstractproperty
    def uut_prompt(self):
        raise NotImplementedError("Need 'uut_prompt' getter property implementation.")

    @uut_prompt.setter
    def uut_prompt(self, newvalue):
        self._uut_prompt = newvalue
        raise NotImplementedError("Need 'uut_prompt' setter property implementation.")

    @abc.abstractproperty
    def uut_ports(self):
        raise NotImplementedError("Need 'uut_ports' getter property implementation.")

    @uut_ports.setter
    def uut_ports(self, newvalue):
        self._uut_ports = newvalue
        raise NotImplementedError("Need 'uut_ports' setter property implementation.")

    @abc.abstractproperty
    def traffic_cases(self):
        raise NotImplementedError("Need 'traffic_cases' getter property implementation.")

    @traffic_cases.setter
    def traffic_cases(self, newvalue):
        raise NotImplementedError("Need 'traffic_cases' setter property implementation.")

    @abc.abstractproperty
    def poe_loadbox_driver(self):
        raise NotImplementedError("Need 'poe_loadbox_driver' getter property implementation.")

    @poe_loadbox_driver.setter
    def poe_loadbox_driver(self, newvalue):
        self._poe_loadbox_driver = newvalue
        raise NotImplementedError("Need 'poe_loadbox_driver' setter property implementation.")

    @abc.abstractproperty
    def poe_uut_func(self):
        raise NotImplementedError("Need 'poe_uut_func' getter property implementation.")

    @poe_uut_func.setter
    def poe_uut_func(self, newvalue):
        self._poe_uut_func = newvalue
        raise NotImplementedError("Need 'poe_uut_func' setter property implementation.")

    @abc.abstractproperty
    def vmargin_func(self):
        raise NotImplementedError("Need 'vmargin_func' getter property implementation.")

    @vmargin_func.setter
    def vmargin_func(self, newvalue):
        self._vmargin_func = newvalue
        raise NotImplementedError("Need 'vmargin_func' setter property implementation.")

    # Methods ----------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError("Need 'reset' method implementation.")

    @abc.abstractmethod
    def run_traf_cases(self, cases):
        raise NotImplementedError("Need 'run_traf_cases' method implementation.")

    @abc.abstractmethod
    def set_pretraf_config(self, **kwargs):
        raise NotImplementedError("Need 'set_pretraf_config' method implementation.")

    @abc.abstractmethod
    def set_conversation(self, **kwargs):
        raise NotImplementedError("Need 'set_conversation' method implementation.")

    @abc.abstractmethod
    def print_conversation(self, name, runtime):
        raise NotImplementedError("Need 'print_conversation' method implementation.")

    @abc.abstractmethod
    def run_conversation(self):
        raise NotImplementedError("Need 'run_conversation' method implementation.")
