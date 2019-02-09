import abc

__author__ = 'bborel'
__title__ = "PCAMAP Base"
__version__ = '2.0.0'


class PCAMapBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, mode_mgr, ud, **kwargs):
        self._mode_mgr = mode_mgr
        self._ud = ud

    # Properties -------------------------------------------------------------------------------------------------------
    # No user properties

    # Methods ----------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def read(self, device_instance, slot_number=None, **kwargs):
        raise NotImplementedError("Need 'read' method implementation.")

    @abc.abstractmethod
    def write(self, device_instance, set_params, slot_number=None, **kwargs):
        raise NotImplementedError("Need 'write' method implementation.")
