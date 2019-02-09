import abc

__author__ = 'bborel'
__title__ = "Rommon Base"
__version__ = '0.1.0'


class RommonBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, mode_mgr, ud, **kwargs):
        self._mode_mgr = mode_mgr
        self._ud = ud

    # Properties -------------------------------------------------------------------------------------------------------
    @abc.abstractproperty
    def version(self):
        raise NotImplementedError("Need 'version' property implementation.")

    # Methods ----------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def get_devices(self):
        raise NotImplementedError("Need 'get_devices' method implementation.")

    @abc.abstractmethod
    def get_device_files(self, device_name, sub_dir, file_filter, attrib_flags):
        raise NotImplementedError("Need 'get_device_files' method implementation.")

    @abc.abstractmethod
    def get_params(self):
        raise NotImplementedError("Need 'get_params' method implementation.")

    @abc.abstractmethod
    def set_params(self, input_params):
        raise NotImplementedError("Need 'set_params' method implementation.")

    @abc.abstractmethod
    def ping(self, ip):
        raise NotImplementedError("Need 'ping' method implementation.")

    @abc.abstractmethod
    def check_version(self, version=None):
        raise NotImplementedError("Need 'check_version' method implementation.")

    @abc.abstractmethod
    def upgrade(self, image, image_type=None, device_src_dir=None, network_src_url=None, modemgr=None):
        raise NotImplementedError("Need 'upgrade' method implementation.")
