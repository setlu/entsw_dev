import abc

__author__ = 'bborel'
__title__ = "PoE Loadbox Driver Base"
__version__ = '0.3.0'


class PoE_Loadbox_Base(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self,  poe_equip, uut_poe_ports, **kwargs):
        # Internals
        self._poe_equip = poe_equip
        self._uut_poe_ports = None
        self._prompt = kwargs.get('prompt', '>')
        self._container = kwargs.get('container', None)
        self._uut_poe_type = kwargs.get('uut_poe_type', 'POE')  # types: POE, POE+, UPOE
        self._kwargs = kwargs
        # Dependent
        self.uut_poe_ports = uut_poe_ports

    # Properties -------------------------------------------------------------------------------------------------------
    # Read-only
    @abc.abstractproperty
    def poe_equip(self):
        raise NotImplementedError("Need 'poe_equip' property implementation.")

    @abc.abstractproperty
    def container(self):
        raise NotImplementedError("Need 'container' getter property implementation.")

    @abc.abstractproperty
    def prompt(self):
        raise NotImplementedError("Need 'prompt' getter property implementation.")

    # Read/Write
    @abc.abstractproperty
    def uut_poe_ports(self):
        raise NotImplementedError("Need 'uut_poe_ports' getter property implementation.")

    @uut_poe_ports.setter
    def uut_poe_ports(self, newvalue):
        raise NotImplementedError("Need 'uut_poe_ports' setter property implementation.")

    @abc.abstractproperty
    def uut_poe_type(self):
        raise NotImplementedError("Need 'uut_poe_type' getter property implementation.")

    @uut_poe_type.setter
    def uut_poe_type(self, newvalue):
        raise NotImplementedError("Need 'uut_poe_type' setter property implementation.")

    # Methods ----------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError("Need 'reset' method implementation.")

    @abc.abstractmethod
    def connect(self, **kwargs):
        raise NotImplementedError("Need 'connect' method implementation.")

    @abc.abstractmethod
    def disconnect(self):
        raise NotImplementedError("Need 'disconnect' method implementation.")

    @abc.abstractmethod
    def set_class(self, load_class=4):
        raise NotImplementedError("Need 'set_class' method implementation.")

    @abc.abstractmethod
    def set_power_load(self, current_limit_mA=None):
        raise NotImplementedError("Need 'set_power_load' method implementation.")

    @abc.abstractmethod
    def set_load_on(self):
        raise NotImplementedError("Need 'set_load_on' method implementation.")

    @abc.abstractmethod
    def set_load_off(self):
        raise NotImplementedError("Need 'set_load_off' method implementation.")

    @abc.abstractmethod
    def get_instrument_data(self):
        raise NotImplementedError("Need 'get_instrument_data' method implementation.")
