"""
Equipment
"""

# Python
# ------
import sys
import logging

import apollo.libs.lib as aplib

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "Equipment Module"
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

func_details = common_utils.func_details
func_retry = common_utils.func_retry
apollo_step = common_utils.apollo_step

class Equipment(object):
    """ Equipment
    *** DO NOT add any code to this class! ***
    Use this class as a parent class to ALL external equipment for product testing.
    The purpose of this class is to provide a nested layer for all equipment to keep better organization and to 
    standardized the framework.  This should only be used for cataloging equipment classes used by the product.
    For example:
      1. PoE Loadbox
      2. Stack Power Loadbox
      3. Traffic Generators
      4. Station fans
      5. etc...

    Usage Form:
    From your product class __init__() inititalize in the form of
    self.equip = Equipment(ud=my_ud, modules=[myequip1_module, myequip2_module, ...])
    
    Usage Example for two pieces of equipment:
    import libs.equip_drivers.poe_loadbox as poe_loadbox
    import libs.equip_drivers.traffic_generator as traffic_generator
    self.equip = Equipment(ud=self.ud, modules=[poe_loadbox, traffic_generator])
    
    REQUIREMENT:
    You equipment modules need to have two global functions: 
        1. "select()" REQUIRED,
           This function should be used to automatically connect to the equipment (given by standardized connections)
           and detect the model/version of equipment in order to select the appropriate driver class.
           Note: This function should only return the class object (do not init).
        2. "init()"   OPTIONAL
           This function can perform an initialization of the equipment driver class that was selected.
           Its purpose is to provide capability of gathering additional information needed to instantiate the class.
           If it is not provided then the class is instantiated directly.
    
    """
    def __init__(self, ud, modules, **kwargs):
        log.info(self.__repr__())
        self._ud = ud
        self._modules = modules
        self._callback = kwargs.get('callback', None)
        self._equipments = {}

        # Select class from modules (no init)
        for module in self._modules:
            if hasattr(module, 'select'):
                equip_attr = module.__name__.split('.')[-1:][0]
                self._equipments[equip_attr] = (module, module.select())
            else:
                log.warning("The module {0} does not have a 'select()' function.".format(module.__name__))
                log.warning("Cannot determine what class to setup.")
                log.warning("Please check the module and add the function.")

        # Direct assignments
        for equip, v in kwargs.items():
            setattr(self, equip, v)
            self._equipments[equip] = ('(direct)', None)
            log.debug("  {0} = {1}".format(equip, v))

        log.debug("Equipments:")
        common_utils.print_large_dict(self._equipments, exploded=False)
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    @apollo_step
    def setup(self, **kwargs):
        kwargs['ud'] = self._ud

        # Process each piece of equipment that was detected or directly assigned.
        for equip, v in self._equipments.items():
            module, mclass = v
            if mclass:
                if hasattr(module, 'init'):
                    log.debug("External initialization of equipment attribute {0} with class {1}".format(equip, mclass.__name__))
                    setattr(self, equip, module.init(mclass, **kwargs))
                else:
                    log.debug("Internal initialization of equipment attribute {0} with class {1}".format(equip, mclass.__name__))
                    setattr(self, equip, mclass(**kwargs))
            else:
                log.warning("Cannot instantiate the equipment class since no class is available for {0}".format(equip))
                setattr(self, equip, None)

        # Setup/update dependancies
        if hasattr(self, '_callback'):
            log.debug("Refreshing dependancies...")
            if hasattr(self._callback, 'diags'):
                log.debug("Diags...")
                self._callback.diags._equip = self
            if hasattr(self._callback, 'traffic') and hasattr(self._callback.traffic, 'fmdiags'):
                log.debug("Traffic...")
                self._callback.traffic.fmdiags.set_attrs()

        return aplib.PASS

    def disconnect(self, **kwargs):
        """ Disconnect
        Provides a centralized mechanism for closing all known equipment connections.
        :param kwargs:
        :return:
        """
        if self._ud.keep_connected:
            log.warning("All equipment will remain connected.")
            return aplib.PASS

        log.debug("Equipment List for disconnection: {0}".format(self._equipments.keys()))
        for equip in self._equipments.keys():
            log.debug("Equipment Member: {0}".format(equip))
            if hasattr(self, equip):
                e = getattr(self, equip)
                if hasattr(e, 'close'):
                    log.debug("Disconnecting {0} ({1})...".format(e, e.__class__.__name__))
                    e.close()
        return

    # *** DO NOT ADD ANY ADDITIONAL METHODS ***
