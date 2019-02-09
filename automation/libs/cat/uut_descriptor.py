"""
UUT Descriptor
"""

# Python
# ------
import sys
import os
import re
import collections
import importlib
import logging
import redis
import uuid

# Apollo
# ------
import apollo.libs.lib as aplib
from toolbox.utils import serialize
from toolbox.utils import deserialize

# BU Lib
# ------
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = "UUT Descriptor"
__version__ = '2.0.0'
__author__ = 'bborel'

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

func_details = common_utils.func_details
apollo_step = common_utils.apollo_step

class CustomDict(dict):

    def __init__(self, func=None, **kwargs):
        self.__func = func
        super(CustomDict, self).__init__(**kwargs)

    def __getitem__(self, k):
        return super(CustomDict, self).__getitem__(k)

    def __setitem__(self, k, v):
        ret = super(CustomDict, self).__setitem__(k, v)
        self.__func([k]) if self.__func else None
        return ret

    def update(self, *args, **kwargs):
        """ update
        Do normal dict.update() then run a specified function using the keys from the update.
        :param args: 
        :param kwargs: 
        :return: 
        """
        super(CustomDict, self).update(*args, **kwargs)
        keys = []
        for arg in args:
            keys += arg.keys()
        keys += kwargs.keys()
        self.__func(list(set(keys))) if self.__func else None
        return True

    def smart_update(self, *args, **kwargs):
        log.debug("Smart update (exclude nulls & invalids) ...")
        def __smart(d):
            for k, v in d.items():
                if self.get(k, None) and v == '':
                    log.debug("{0:<30}:{1:<30}  (Ignore null value; no set.)".format(k, '--'))
                else:
                    result, msg = common_utils.validate_entry(k, v, silent=True, retmsg=True)
                    if result:
                        self[k] = v
                        log.debug("{0:<30}:{1:<30}  (Set value.) {2}".format(k, v, msg))
                    else:
                        log.debug("{0:<30}:{1:<30}  (Invalid value; no set.)".format(k, v))

        for arg in args:
            __smart(arg)
        __smart(kwargs) if kwargs else None
        return True


class ApolloAddon(object):
    def __init__(self, **kwargs):
        try:
            self.__apollo_go = True
            self.__container_key = aplib.get_my_container_key()
            self.__test_area = aplib.apdicts.test_info.test_area
            self.__apollo_mode = aplib.get_apollo_mode()
            self.__uut_index = common_utils.get_uut_suffix_index()
            log.info("Apollo engine/container is available")
        except (RuntimeError, KeyError):
            log.critical("Apollo engine/container not available!")
            log.warning("Container key will be a UUID.")
            log.warning("Test area and mode are defaulted.")
            self.__apollo_go = False
            self.__container_key = uuid.uuid4().get_hex()
            self.__test_area = 'DGBSYS'
            self.__apollo_mode = 'DEBUG'
            self.__uut_index = 1
        self.print_apollo_details()
        return

    @property
    def uut_index(self):
        return self.__uut_index

    @property
    def container_key(self):
        if self.__apollo_go:
            self.__container_key = aplib.get_my_container_key()
        return self.__container_key

    @property
    def container_name(self):
        return self.container_key.split('|')[-1:][0]

    @property
    def test_area(self):
        if self.__apollo_go:
            self.__test_area = aplib.apdicts.test_info.test_area
        return self.__test_area

    @property
    def apollo_mode(self):
        if self.__apollo_go:
            self.__apollo_mode = aplib.get_apollo_mode()
        return self.__apollo_mode

    @property
    def apollo_go(self):
        return self.__apollo_go

    def container_details(self):
        common_utils.container_details()
        return aplib.PASS

    def print_apollo_details(self):
        log.debug("  Go            = {0}".format(self.__apollo_go))
        log.debug("  Container Key = {0}".format(self.__container_key))
        log.debug("  Test Area     = {0}".format(self.__test_area))
        log.debug("  Mode          = {0}".format(self.__apollo_mode))
        log.debug("  UUT Index     = {0}".format(self.__uut_index))
        return aplib.PASS


class ServerDescriptor(object):
    def __init__(self, **kwargs):
        self.__server_config = common_utils.get_server_info()
        return

    @property
    def server_config(self):
        return self.__server_config

    def print_server_config(self, exploded=False):
        common_utils.print_large_dict(self.__server_config, sort=True, exploded=exploded)
        return aplib.PASS


class UutDescriptorException(Exception):
    """Raise for specific UutDescriptor exceptions."""
    pass


class UutDescriptor(ServerDescriptor, ApolloAddon):
    PUID = collections.namedtuple('PUID', 'pid vid partnum partnum_rev sernum uut_type')
    Manifest = collections.namedtuple('Manifest', 'module pid cpns')
    ECOMani = collections.namedtuple('ECOMani', 'programming verification areas desc')
    IOSMani = collections.namedtuple('IOSMani', 'name platforms product_id cco_location image_name version md5 recovery SR_pkgs')
    PRGM, VRFY = 'PROGRAMMING', 'VERIFICATION'
    UDParams = collections.namedtuple('UDParams', 'pm_type pm_key_pairs pm_locator_module uut_config_assem_section '
                                                  'remote_server_key eco_key')
    DEFAULT_PROPERTIES = ['product_line', 'product_family', 'product_codename', 'product_selection', 'puid_keys', 'puid', 'consumer',
                          'uut_index', 'container_key', 'container_name', 'test_area', 'apollo_mode']
    DEFAULT_REVISION_MAP = {
        'MOTHERBOARD_ASSEMBLY_NUM': 'MOTHERBOARD_REVISION_NUM',
        'TAN_NUM': 'TAN_REVISION_NUMBER',
        'MODEL_NUM': 'VERSION_ID',
    }

    def __init__(self, common_def, product_line_def, uut_conn, **kwargs):
        ServerDescriptor.__init__(self, **kwargs)
        ApolloAddon.__init__(self, **kwargs)
        log.info(self.__repr__())
        self.__verbose_level = 1
        self.__standalone = kwargs.get('standalone', False)
        if self.__standalone:
            log.debug("  This instance of UutDescriptor is in STANDALONE mode.")
        self._callback = None
        self.__uut_conn = uut_conn
        # data
        self.uut_config = CustomDict(func=self.__source_puid)
        self.uut_status = dict()
        self.ios_manifest = getattr(kwargs.get('ios_manifest', None), 'ios_manifest', {})
        # definitions + paths ----------------------------------
        self.__product_specific_def = None
        self.__product_line_def = product_line_def
        self.__common_def = common_def
        self.__pd_modulepath = None
        self.__pd_dir = None
        self.__parent_module = kwargs.get('parent_module', None)
        self.__consumer = None
        # descriptions ------------------------------------------
        self.__product_line = self.__pl()
        self.__category = self.__ca()
        self.__product_selection = None
        self.__product_codename = None
        self.__product_family = None
        self.__device_instance = None
        self.__physical_slot = None
        self.__modular_type = None
        self._dynamic_properties = list()
        # other -------------------------------------------------
        self.__load_dynamic_properties(modules=[self.__common_def, self.__product_line_def])
        self.descriptor_params = self.UDParams(
            'STANDARD',
            {'MAIN': (['MOTHERBOARD_ASSEMBLY_NUM', 'TAN_NUM'], 'MODEL_NUM'), 'PERIPH': (['VPN', 'PCAPN'], 'PID')},
            self.__product_line_def,
            'BOTH',
            'REMOTE_SERVER',
            'DEVIATION_NUM',)
        pk = self.__select_puid_keys(process_type='SYS')
        self.__puid_keys = kwargs.get('puid_keys', self.PUID(*pk))
        self.__puid = self.PUID(None, None, None, None, None, None)
        self.__family_filter = kwargs.get('family_filter', '.*')
        self.__line_filter = kwargs.get('line_filter', '.*')
        self.__automation = False
        self.__max_attempts = 3
        self.__keep_connected = False
        self.__cof = False
        # data assembly ------------------------------------------
        self.__get_product_manifest()
        self.__assemble_uut_network()
        self.__save_to_userdict()
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    def __setattr__(self, key, value):
        if hasattr(self, '_dynamic_properties'):
            if key not in self._dynamic_properties and key[0:1] != '_':
                self._dynamic_properties.append(key)
        return super(UutDescriptor, self).__setattr__(key, value)

    @property
    def verbose_level(self):
        return self.__verbose_level

    @verbose_level.setter
    def verbose_level(self, newvalue):
        self.__verbose_level = newvalue

    @property
    def product_line(self):
        return self.__product_line

    @product_line.setter
    def product_line(self, newvalue):
        if self.test_area == 'DBGSYS':
            self.__product_line = newvalue
        else:
            raise Exception("Setting product line is not allowed except in DBGSYS.")

    @property
    def category(self):
        return self.__category

    @category.setter
    def category(self, newvalue):
        if self.test_area == 'DBGSYS':
            self.__category = newvalue
        else:
            raise Exception("Setting category is not allowed except in DBGSYS.")

    @property
    def product_family(self):
        return self.__product_family

    @product_family.setter
    def product_family(self, newvalue):
        if self.test_area == 'DBGSYS':
            self.__product_family = newvalue
        else:
            raise Exception("Setting product family is not allowed except in DBGSYS.")

    @property
    def product_manifest(self):
        return self.__product_manifest

    @property
    def products_available(self):
        return sorted(self.__product_manifest.keys())

    @property
    def product_codename(self):
        return self.__product_codename

    @property
    def consumer(self):
        return self.__consumer

    @property
    def product_selection(self):
        return self.__product_selection

    @product_selection.setter
    def product_selection(self, newvalue):
        self.__clear_selection()
        self.__get_codename(newvalue)
        self.__load_module()
        self.__assemble_product_definition()
        self.__update_traffic()
        self.__product_selection = newvalue
        self.__source_puid()
        self.derive_device_info()
        self.__update_pd_location()
        self.__get_uut_network()
        self.__update_dyn_prop_from_uut_config()
        self.__update_mode_mgr()
        self.__save_to_userdict()

    @property
    def uut_conn(self):
        return self.__uut_conn

    @property
    def puid(self):
        return self.__puid

    @property
    def puid_keys(self):
        return self.__puid_keys

    @puid_keys.setter
    def puid_keys(self, newvalue):
        if isinstance(newvalue, list):
            self.__puid_keys = self.PUID(*newvalue)
        elif isinstance(newvalue, self.PUID):
            self.__puid_keys = newvalue
        else:
            raise Exception("The puid_keys setter expects a list or a PUID namedtuple.")
        self.__source_puid()

    @property
    def device_instance(self):
        return self.__device_instance

    @device_instance.setter
    def device_instance(self, newvalue):
        self.__device_instance = newvalue

    @property
    def physical_slot(self):
        return self.__physical_slot

    @physical_slot.setter
    def physical_slot(self, newvalue):
        self.__physical_slot = newvalue

    @property
    def modular_type(self):
        return self.__modular_type

    @property
    def automation(self):
        return self.__automation

    @automation.setter
    def automation(self, newvalue):
        self.__automation = newvalue
        if self.__automation:
            log.info("-" * 50)
            log.info("AUTOMATION")
            log.info("Robotic automation is enabled for this container!")
            log.info("No retries allowed.")
            log.info("-" * 50)
            self.__max_attempts = 1

    @property
    def eco_manifest(self):
        return self.uut_config.get('eco_manifest', {})

    @property
    def max_attempts(self):
        return self.__max_attempts

    @max_attempts.setter
    def max_attempts(self, newvalue):
        if self.__automation and newvalue > 1:
            log.warning("Cannot set max_attempts >1 since automation is enabled.")
        else:
            self.__max_attempts = newvalue

    @property
    def keep_connected(self):
        return self.__keep_connected

    @keep_connected.setter
    def keep_connected(self, newvalue):
        self.__keep_connected = newvalue

    @property
    def cof(self):
        return self.__cof

    @keep_connected.setter
    def cof(self, newvalue):
        self.__cof = newvalue

    # ==================================================================================================================
    # Apollo Step Methods
    # ==================================================================================================================
    @apollo_step
    def print_product_manifest(self):
        if not self.__product_manifest:
            log.warning("No manifest available.")
            return aplib.FAIL
        mani = self.Manifest([], [], [])
        for k, v in self.__product_manifest.items():
            mani.module.append(v.module)
            mani.pid.append(v.pid)
            mani.cpns.append(v.cpns)
        mmax = self.Manifest(max([len(i) for i in mani.module]),
                             max([len(i) for i in mani.pid]),
                             max([len(i) for i in mani.cpns]))
        pm_list = self.__product_manifest.keys()
        kmax = max([len(i) for i in pm_list])
        pm_list.sort()
        log.debug("Product Definition Module Base Path = {0}".format(self.__pd_modulepath))
        log.debug("Product Definition Base Dir         = {0}".format(self.__pd_dir))
        log.debug("Manifest:")
        for prod in pm_list:
            mv = self.__product_manifest[prod]
            log.debug("{0:<{4}}: ({1:<{5}},  {2:<{6}},  {3:<{7}})".format(prod, mv.module, mv.pid, mv.cpns,
                                                                          kmax, mmax.module, mmax.pid, mmax.cpns))
        return aplib.PASS

    @apollo_step
    def print_eco_manifest(self):
        ecod = self.ECOMani([], [], [], [])
        for k, v in self.uut_config.get('eco_manifest', {}).items():
            e = self.ECOMani(*v)
            ecod.programming.append(e.programming)
            ecod.verification.append(e.verification)
            ecod.areas.append(e.areas)
        if not ecod.programming and not ecod.verification:
            log.warning("No ECO manifest available.")
            return aplib.SKIPPED
        emax = self.ECOMani(max([len(str(i)) for i in ecod.programming]),
                            max([len(str(i)) for i in ecod.verification]),
                            max([len(str(i)) for i in ecod.areas]), 0)
        e_list = self.uut_config.get('eco_manifest', {}).keys()
        kmax = max([len(str(i)) for i in e_list])
        e_list.sort()
        for eco in e_list:
            ev = self.ECOMani(*self.uut_config.get('eco_manifest', {}).get(eco))
            log.debug("{0:<{5}}: ({1:<{6}},  {2:<{7}},  {3:<{8}}, {4})".format(eco, ev.programming, ev.verification,
                                                                               ev.areas, ev.desc, kmax,
                                                                               emax.programming, emax.verification,
                                                                               emax.areas))
        return aplib.PASS

    @apollo_step
    def print_ios_manifest(self):
        if not self.ios_manifest:
            log.warning("No IOS manifest available.")
            return aplib.SKIPPED
        iosd = self.IOSMani([], [], [], [], [], [], [], [], [])
        for k, v in self.ios_manifest.items():
            iosd.name.append(v.get('name'))
            iosd.platforms.append(v.get('platforms'))
            iosd.product_id.append(v.get('product_id'))
            iosd.cco_location.append(v.get('cco_location'))
            iosd.image_name.append(v.get('image_name'))
            iosd.version.append(v.get('version'))
            iosd.md5.append(v.get('md5'))
            iosd.recovery.append(v.get('recovery'))
            iosd.SR_pkgs.append(v.get('SR_pkgs'))
        imax = self.IOSMani(max([len(str(i)) for i in iosd.name]),
                            max([len(str(i)) for i in iosd.platforms]),
                            max([len(str(i)) for i in iosd.product_id]),
                            max([len(str(i)) for i in iosd.cco_location]),
                            max([len(str(i)) for i in iosd.image_name]),
                            max([len(str(i)) for i in iosd.version]),
                            max([len(str(i)) for i in iosd.md5]),
                            max([len(str(i)) for i in iosd.recovery]),
                            max([len(str(i)) for i in iosd.SR_pkgs]),
                            )
        i_list = self.ios_manifest.keys()
        kmax = max([len(str(i)) for i in i_list])
        i_list.sort()
        log.debug(
            "{0:<{10}}:  {1:<{11}}  {2:<{12}}  {3:<{13}}  {4:<{14}}  {5:<{15}}  {6:<{16}}  {7:<{17}}  {8:<{18}}  {9}".
            format('key', 'name', 'platforms', 'product_id', 'cco_location', 'image_name', 'version', 'md5', 'recovery', 'SR_pkgs',
                   kmax, imax.name, imax.platforms, imax.product_id, imax.cco_location, imax.image_name,
                   imax.version, imax.md5, imax.recovery, imax.SR_pkgs))
        for ios in i_list:
            v = self.ios_manifest[ios]
            log.debug("{0:<{10}}:  {1:<{11}}  {2:<{12}}  {3:<{13}}  {4:<{14}}  {5:<{15}}  {6:<{16}}  {7:<{17}}  {8:<{18}}  {9}".
                      format(ios, v.get('name'), v.get('platforms'), v.get('product_id'), v.get('cco_location'), v.get('image_name'),
                             v.get('version'), v.get('md5'), v.get('recovery'), v.get('SR_pkgs'),
                             kmax, imax.name, imax.platforms, imax.product_id, imax.cco_location, imax.image_name,
                             imax.version, imax.md5, imax.recovery, imax.SR_pkgs))
        return aplib.PASS

    @apollo_step
    def print_traffic_cases(self):
        common_utils.print_large_dict(self.uut_config.get('traffic_cases'), title='TRAFFIC CASES', exploded=False)
        return aplib.PASS

    @apollo_step
    def print_uut_config(self, exploded=False):
        common_utils.print_large_dict(self.uut_config, sort=True, exploded=exploded)
        return aplib.PASS

    @apollo_step
    def print_uut_status(self, exploded=False):
        common_utils.print_large_dict(self.uut_status, sort=True, exploded=exploded)
        return aplib.PASS

    @apollo_step
    def print_uut_descriptor(self):
        desc  = "UUT DESCRIPTOR\n"
        desc += "--------------\n"
        desc += " Static Properties\n"
        desc += " .product_line            = {0}\n".format(self.__product_line)
        desc += " .product_family          = {0}\n".format(self.__product_family)
        desc += " .product_codename        = {0}\n".format(self.__product_codename)
        desc += " .product_selection       = {0}\n".format(self.__product_selection)
        desc += " .product_manifest        = Products:[see .print_product_manifest()]\n"
        desc += " .products_available      = Count:{0}\n".format(len(self.products_available))
        desc += " .category                = {0}\n".format(self.__category)
        desc += " .modular_type            = {0}\n".format(self.__modular_type) if self.__category == 'MODULAR' else ''
        desc += " .device_instance         = {0}\n".format(self.__device_instance)
        desc += " .physical_slot           = {0}\n".format(self.__physical_slot) if self.__category == 'MODULAR' else ''
        desc += " .puid_keys               = {0}\n".format(self.__puid_keys)
        desc += " .puid                    = {0}\n".format(self.__puid)
        desc += " .uut_config              = Count:{0}  Items:[see .print_uut_config()]\n".format(len(self.uut_config.keys()))
        desc += " .uut_status              = Count:{0}  Items:[see .print_uut_status()]\n".format(len(self.uut_status.keys()))
        desc += " .ios_manifest            = Count:{0}  Items:[see .print_ios_manifest()]\n".format(len(self.ios_manifest.keys()))
        desc += " .eco_manifest            = Count:{0}  Items:[see .print_eco_manifest()]\n".format(len(self.uut_config.get('eco_manifest', {}).keys()))
        desc += " .server_config           = Count:{0}  Items:[see .print_server_config()]\n".format(len(self.server_config.keys()))
        desc += " .automation              = {0}\n".format(self.__automation)
        desc += " .max_attempts            = {0}\n".format(self.__max_attempts)
        desc += " .keep_connected          = {0}\n".format(self.__keep_connected)
        desc += " .cof                     = {0}\n".format(self.__cof)
        desc += "Dynamic Properties\n"
        for p in sorted(self._dynamic_properties):
            desc += " .{0:<23} = {1}\n".format(p, type(getattr(self, p)))
        desc += "Other\n"
        desc += " PD Dir                   = {0}\n".format(self.__pd_dir)
        desc += " PD Module Path           = {0}\n".format(self.__pd_modulepath)
        desc += " Consumer                 = {0}\n".format(self.__consumer)
        desc += " Callback                 = {0}\n".format(self._callback if hasattr(self, '_callback') else None)
        desc += " Filters                  = Line:{0}  Family:{1}\n".format(self.__line_filter, self.__family_filter)

        for line in desc.splitlines():
            log.debug(line)

        return aplib.PASS

    @apollo_step
    def save(self, manual_key=None):
        rdb = redis.StrictRedis()
        key = "{0}_uut_descriptor".format(self.container_key) if not manual_key else manual_key
        saved_dict = self.convert_to_dict()
        log.debug("Saving at key={0}".format(key))
        if not rdb.set(key, serialize(saved_dict)):
            raise UutDescriptorException("Cannot save UUT Descriptor.")
        return aplib.PASS

    @apollo_step
    def retrieve(self, manual_key=None):
        rdb = redis.StrictRedis()
        key = "{0}_uut_descriptor".format(self.container_key) if not manual_key else manual_key
        log.debug("Retrieving at key={0}".format(key))
        serdes_data = rdb.get(key)
        if not serdes_data:
            raise UutDescriptorException("No UUT data in Redis for the container.")
        retrieved_dict = deserialize(serdes_data)
        rdb.delete(key)
        if not retrieved_dict:
            raise UutDescriptorException("Cannot deserialize UUT Descriptor.")
        if not retrieved_dict.get('uut_config'):
            raise UutDescriptorException("No uut_config available for UUT Descriptor init.")
        if not retrieved_dict.get('product_selection'):
            if self.test_area != 'DBGSYS':
                raise UutDescriptorException("No product selection available for UUT Descriptor init.")
        # Update
        self.__product_family = retrieved_dict.get('product_family')
        if retrieved_dict.get('product_selection'):
            log.debug("Loading retrieved product selection...")
            # Load the previously selected product (from PRE-SEQ)
            self.product_selection = retrieved_dict.get('product_selection')
        # Override with previous PRE-SEQ data
        self.uut_config = CustomDict(func=self.__source_puid, **retrieved_dict.get('uut_config'))
        self.puid_keys = list(retrieved_dict.get('puid_keys'))
        return aplib.PASS

    @apollo_step
    def get_eco_num_in_manifest(self, eco_type=PRGM, cpn=None, cpn_rev=None, test_area=None, update=False):
        eco_num = self.__parse_eco_manifest(eco_type=eco_type, cpn=cpn, cpn_rev=cpn_rev, test_area=test_area)
        if update:
            eco_key = self.descriptor_params.eco_key
            if common_utils.validate_eco_deviation(eco_num):
                # Update the UUT Config with the appropriate ECO/Deviation number.
                log.debug("ECO number updating to key: {0}".format(eco_key))
                self.uut_config[eco_key] = eco_num
            else:
                log.debug("Asking for operator input (ECO/Dev num)...")
                eco_data = common_utils.get_data_from_operator(self.__category,
                                                               self.__product_codename,
                                                               eco_key,
                                                               self.revision_map,
                                                               gui=self.apollo_go)
                if eco_data:
                    log.debug("Updating {0}".format(eco_data))
                    self.uut_config[eco_key] = eco_data[eco_key]
                else:
                    log.debug("No ECO data to update uut_config.")
        else:
            log.debug("No ECO/Dev num update.")

        return eco_num

    @apollo_step
    def get_flash_mapped_dir(self):
        """ Get Flash Mapped Dir
        Uses the uut_config to determine the primary location that bootloader maps to the 'flash:' device.
        This is the location where all images are used by Diags & IOS (i.e. the "active" flash area).
        Below is a snippet from a sample uut_config that is used:
        'flash_device': {'name': 'flash', 'relative_dir': 'user', 'device_num': 3},
        'device_mounts': {
            'primary': [(3, '/mnt/flash3'), (1, '/mnt/flash1'), (2, '/mnt/flash2'),
                        (4, '/mnt/flash4'), (5, '/mnt/flash5'), (6, '/mnt/flash6'), (7, '/mnt/flash7')],
            'secondary': None,
            'tertiary': None,
        },
        :return:
        """
        if not self.uut_config.get('device_mounts', {}).get('primary', None):
            log.warning("Missing uut_config['device_mounts']['primary'].")
            return ''
        if 'flash_device' not in self.uut_config:
            log.warning("Missing uut_config['flash_device'].")
            return ''

        dev_num = self.uut_config.get('flash_device', {}).get('device_num', 3)
        rel_dir = self.uut_config.get('flash_device', {}).get('relative_dir', 'user')
        if not isinstance(self.uut_config['device_mounts']['primary'], list):
            self.uut_config['device_mounts']['primary'] = [(3, '/mnt')]

        for dn, directory in self.uut_config['device_mounts']['primary']:
            if dn == dev_num:
                dev_dir = directory
                break
        else:
            dev_dir = '/mnt'

        pfd = os.path.join(dev_dir, rel_dir)
        log.info("Prime flash dir = '{0}'".format(pfd))
        return pfd

    # ADMIN Methods ----------------------------------------------------------------------------------------------------
    #
    @apollo_step
    def set_puid_keys(self, keys):
        self.puid_keys = keys
        return aplib.PASS

    @apollo_step
    def select_puid_keys(self, **kwargs):
        pk = self.__select_puid_keys(**kwargs)
        if not pk:
            errmsg = 'PUID Key selection incomplete.'
            log.error(errmsg)
            return aplib.FAIL
        self.puid_keys = pk
        return aplib.PASS

    # ==================================================================================================================
    # User Methods  (step support & internal)
    # ==================================================================================================================
    def convert_to_dict(self):
        log.debug("Convert to dict...")
        ud_dict = dict()
        for prop in self.DEFAULT_PROPERTIES + self._dynamic_properties:
            ud_dict[prop] = getattr(self, prop)
            if len(str(ud_dict[prop])) < 100:
                log.debug("  {0} = {1}".format(prop, ud_dict[prop])) if self.__verbose_level > 2 else None
            else:
                log.debug("  {0} = ... ".format(prop)) if self.__verbose_level > 2 else None
        ud_dict['uut_config'] = self.uut_config.copy()  # removes CustomDict
        log.debug("  uut_config = {...}") if self.__verbose_level > 2 else None
        return ud_dict

    def get_flash_params(self):
        """ Get Flash Params
        Obtain only the flash params from the uut_config data.
        The flash params are indicated by convention which is all upper case in the naming.
        :return (dict): Flash params only.
        """
        return {k: self.uut_config[k] for k in self.uut_config.keys() if k.isupper()}

    def get_script_params(self):
        """ Get Script Params
        Obtain only the script params from the uut_config data.
        The script params are indicated by convention which is all lower case in the naming.
        :return (dict): Script params only.
        """
        return {k: self.uut_config[k] for k in self.uut_config.keys() if k.islower()}

    def get_str_valued_params(self):
        """ Get String-Valued Params
        Obtain only the params that have a string value from the uut_config data.
        :return (dict): String-valued params only.
        """
        return {k: self.uut_config[k] for k in self.uut_config.keys() if type(self.uut_config[k]) is str}

    def get_filtered_params(self, keys):
        """ Get Filtered Params
        Obtain only the params that match the key list.
        :param (list) keys:
        :return (dict): String-valued params only.
        """
        if not isinstance(keys, list):
            log.warning("The 'keys' param must be a list.")
            return {}
        return {k: self.uut_config[k] for k in self.uut_config.keys() if k in keys}

    def get_filtered_keys(self, allowed_params):
        """ Filtered Key List
        Takes all uut_config params and extracts ONLY those from the allowed list.
        For the params extracted, place in the order dictated by the allowed_param list.
        :param (list) allowed_params:
        :return:
        """
        if not allowed_params or not isinstance(allowed_params, list):
            log.warning("The 'allowed_params' is empty or not a list.")
            return []
        verbose = False
        uut_params = self.get_flash_params()
        log.debug("All UUT params    : {0}".format(uut_params)) if verbose else None
        log.debug("Allowed UUT params: {0}".format(allowed_params)) if verbose else None
        unsorted_filtered_params = list(set(allowed_params) & set(uut_params.keys()))
        log.debug(unsorted_filtered_params) if verbose else None
        # Sort filtered params based on allowed_params order
        filtered_params = []
        for i in range(0, len(allowed_params)):
            if allowed_params[i] in unsorted_filtered_params:
                filtered_params.append(allowed_params[i])
        log.debug("UUT filtered params: {0}".format(filtered_params))
        return filtered_params

    def derive_device_info(self):
        """ Derive Device Info (INTERNAL)
        Get the device_instance and physicial_slot (if modular).

        Modular Examples of configuration data
        ----------------
        LINECARD:
        1: {'physical_slot': 1, 'sup_prime': 3, 'device_instance': 1000, 'slot_map': 'a', 'conn_suffix': '1'},
        SUPERVISOR:
        1: {'physical_slot': 2, 'linecards': [1, 4], 'physical_slot_auxsup': 3, 'device_instance': 0},
        :return:
        """
        if not self.apollo_go:
            log.debug("Cannot derive device info: not running from an Apollo container.")
            return
        log.debug("Configuration Data")
        for k, v in aplib.apdicts.configuration_data.items():
            log.debug("{0:<20} : {1}".format(k, v))
        if self.__category == 'SWITCH':
            self.device_instance = self.uut_config.get('device_instance', 0)
        elif self.__category == 'MODULAR':
            log.debug("Searching for modular config data...")
            for entry in ['linecard', 'supervisor', 'chassis', 'fantry']:
                cfg_data = aplib.apdicts.configuration_data.get(entry.upper(), None)
                if cfg_data:
                    log.debug("Modular data found!")
                    log.debug("{0} = {1}".format(entry, cfg_data))
                    self.uut_config[entry] = cfg_data
                    self.__device_instance = self.uut_config[entry].get('device_instance', None)
                    self.__physical_slot = self.uut_config[entry].get('physical_slot', None)
                    self.__modular_type = entry
                    break
            else:
                errmsg = "No modular config data.  Check the Apollo x_config.py files!"
                log.error(errmsg)
                raise UutDescriptorException(errmsg)

        return

    # INTERNAL Methods -------------------------------------------------------------------------------------------------
    #
    def __save_to_userdict(self):
        if self.__standalone:
            log.debug("  Standalone; not allowed in userdict.")
            return
        if self.apollo_go:
            log.debug("Saving UUT Descriptor to userdict...")
            try:
                aplib.apdicts.userdict['udd'] = self.convert_to_dict()
            except Exception as e:
                log.error(e)
                raise("FATAL error attempting to save UUT Descriptor dict to userdict!")
        else:
            log.debug("Cannot save UutDescriptor dict to userdict: not running from an Apollo container.")
        return

    def __pl(self):
        if hasattr(self.__product_specific_def, '__line__'):
            pl = self.__product_specific_def.__line__
        elif hasattr(self.__product_line_def, '__line__'):
            pl = self.__product_line_def.__line__
        elif hasattr(self.__common_def, '__line__'):
            pl = self.__common_def.__line__
        else:
            pl = 'cat'
        return pl

    def __ca(self):
        if hasattr(self.__product_specific_def, '__category__'):
            c = self.__product_specific_def.__category__
        elif hasattr(self.__product_line_def, '__category__'):
            c = self.__product_line_def.__category__
        elif hasattr(self.__common_def, '__category__'):
            c = self.__common_def.__category__
        else:
            c = 'GENERIC'
        return c

    def __clear_selection(self):
        self.uut_config = CustomDict(func=self.__source_puid)
        self.__product_selection = None
        self.__product_codename = None
        self.__product_family = None
        self.__product_specific_def = None
        for p in self._dynamic_properties:
            try:
                delattr(self, p, None)
            except Exception:
                pass
        self._dynamic_properties = list()
        self.uut_status = dict()
        return

    def __source_puid(self, keys=None):
        """ Source PUID
        Update the PUID keyed items specified:  uut_config-->PUID
        :param keys: 
        :return: 
        """
        if keys and not list(set(keys) & set(self.__puid_keys)):
            return
        v = []
        for k in self.__puid_keys:
            # log.debug("  PUID:  k={0}  v={1}".format(k, self.uut_config.get(k)))
            v.append(self.uut_config.get(k))
        self.__puid = self.PUID(*v)
        return

    def __select_puid_keys(self, **kwargs):
        """
        Format of the manifest:
        {'<category>': {'<process_type>': [<list of keys per PUID>], ...}, ...}
        The PUID list consists of 'pid vid partnum partnum_rev sernum uut_type'

        Ex.
        puid_key_manifest = {
            'SWITCH': {
                'PCBA': ['MODEL_NUM', 'VERSION_ID', 'MOTHERBOARD_ASSEMBLY_NUM', 'MOTHERBOARD_REVISION_NUM',
                         'MOTHERBOARD_SERIAL_NUM', 'MOTHERBOARD_ASSEMBLY_NUM'],
                'SYS': ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SYSTEM_SERIAL_NUM', 'MODEL_NUM'],
            },
            'PERIPH': {
                'PCBA': ['PID', 'VID', 'PCAPN', 'PCAREV', 'SN', 'PID'],
                'SYS': ['PID', 'VID', 'VPN', 'VID', 'SN', 'PID'],
            },
        }
        :param kwargs: 
        :return: 
        """
        PK_DEFAULT = ['MODEL_NUM', 'VERSION_ID', 'TAN_NUM', 'TAN_REVISION_NUMBER', 'SYSTEM_SERIAL_NUM', 'MODEL_NUM']
        category = kwargs.get('category', self.__category)
        process_type = kwargs.get('process_type', None)

        if not hasattr(self, 'puid_key_manifest'):
            log.debug("  NOTICE: PUID Key manifest is NOT available from the definitions.")
            log.debug("  The puid_key_manifest can reside in _common_def, _product_line_def, or <prod specific>_def.")
            log.debug("  Using built-in default.")
            return PK_DEFAULT

        process_type_keys = self.puid_key_manifest.get(category, {}).keys()
        if not process_type_keys:
            log.debug("  NOTICE: No PUID process_type(s) for the category={0}".format(category))
            log.debug("  Using built-in default.")
            return PK_DEFAULT

        if not process_type:
            if self.apollo_go:
                process_type = aplib.ask_question("Select PUID Process Type:", answers=process_type_keys)
            else:
                process_type = input('Select PUID Process Type {0}:'.format(process_type_keys))
                process_type = "'{0}'".format(process_type)

        # Get the PUID keys
        puid_keys = self.puid_key_manifest.get(category, {}).get(process_type)
        if not puid_keys:
            log.debug("  NOTICE: No PUID keys for the process_type={0}.".format(process_type))
            log.debug("  Using built-in default.")
            return PK_DEFAULT

        log.debug("PUID Category     = {0}".format(category))
        log.debug("PUID Process Type = {0}".format(process_type))
        log.debug("PUID Keys         = {0}".format(puid_keys))
        return puid_keys

    def __load_dynamic_properties(self, modules):
        """ Preload
        Inspect the modules and preload all UUT descriptor data with the items allowed.
        :param (list) modules:
        :return:
        """
        log.debug("  Preloading properties...")
        for module in modules:
            if module:
                properties = []
                for p in [i for i in dir(module) if i[0] != '_']:
                    if type(getattr(module, p)) in [dict, list, str, int, collections.OrderedDict]:
                        properties.append(p)

                col = max([len(i) for i in properties]) if properties else 1
                log.debug("  {0:<{2}} = {1}".format('Module', module, col))
                for property in properties:
                    if hasattr(module, property):
                        log.debug("  {0:<{2}} = {1}".format(property, type(getattr(module, property)), col))
                        setattr(self, property, getattr(module, property))
        self._dynamic_properties = list(set(self._dynamic_properties))

        return

    def __import_reload_dynamic_properties(self, pd_module_name):
        """ Import and reload dynamic Properties
        Use this AFTER a product_selection has been made since we should now know the associated modules:
        _common_def & _product_line_def and can import their properties.
        :param pd_module_name:
        :return:
        """
        # 1. Derive
        log.debug("Deriving modules from hierarchy of {0}".format(pd_module_name))
        pl_mod_name = '.'.join(pd_module_name.split('.')[:-1] + ['_product_line_def'])
        common_mod_name = '.'.join(pd_module_name.split('.')[:-3] + ['common', '_common_def'])
        log.debug("pl_mod_name = {0}".format(pl_mod_name))
        log.debug("common_mod_name = {0}".format(common_mod_name))
        # 2. Import
        try:
            self.__common_def = importlib.import_module(common_mod_name)
            self.__product_line_def = importlib.import_module(pl_mod_name)
        except ImportError as e:
            log.error("The import of generic properties failed.")
            raise UutDescriptorException(e.message)
        # 3. Reload
        self.__load_dynamic_properties(modules=[self.__common_def, self.__product_line_def])
        return

    def __update_dyn_prop_from_uut_config(self):
        """ Update Dynamic Property based on uut_config
        If a dynamic property shows up in the uut_config then copy what is in the uut_config!
        Remember: "dynamic properties" show up as module properties in the _common_def & _product_line_def modules.
        This has to be done AFTER the uut_config is loaded (i.e. product_selection is determined).
        Order of precedence: _common_def --> _product_line_def --> uut_config
        :return:
        """
        for p in self._dynamic_properties:
            if self.uut_config.get(p) and self.uut_config.get(p) != getattr(self, p):
                setattr(self, p, self.uut_config.get(p))
                log.debug("  uut_config[{0}] --> self.ud.{0} = {1}".format(p, self.uut_config.get(p)))
        return

    def __extract_pd_base_location(self):
        """ Extract Product Definition Base Module directory and module path (INTERNAL)
        Get the product_definitions directory and module prefix based on a "locator module".
        This is typically a known module (_product_line_def.py) in the same dir as all the
        product definitions but could also be _common_def.py in the common section for the entire product space.
        :return:
        """
        log.debug("  Extracting product definition base location:")
        if self.__product_line_def:
            log.debug("  Using _product_line_def module...")
            self.__pd_dir = os.path.dirname(self.__product_line_def.__file__)
            self.__pd_modulepath = '.'.join(self.__product_line_def.__name__.split('.')[0:-1])
            # self.__consumer = '.'.join(self.__pd_modulepath.split('.')[0:-1] + [self.__product_line_def.__consumer__])
        elif self.__common_def:
            log.debug("  Using _common_def module...")
            self.__pd_dir = os.path.dirname(os.path.dirname(self.__common_def.__file__))
            self.__pd_modulepath = '.'.join(self.__common_def.__name__.split('.')[0:-1])
            # self.__consumer = '.'.join([self.__pd_modulepath, self.__common_def.__consumer__])
        elif self.__parent_module:
            log.debug("  Using parent module...")
            self.__pd_dir = os.path.dirname(os.path.dirname(os.path.dirname(self.__parent_module.__file__)))
            self.__pd_modulepath = '.'.join(self.__parent_module.__name__.split('.')[0:-3])
            # self.__consumer = self.__parent_module.__name__
        else:
            raise UutDescriptorException("No Parent, No Common Definition, No Product Line Definition for reference.")
        log.debug("  PD Dir   ={0}".format(self.__pd_dir))
        log.debug("  PD Module={0}".format(self.__pd_modulepath))
        log.debug("  Consumer ={0}".format(self.__consumer))
        return

    def __update_pd_location(self):
        """ Update Product Definition Location
        Do this AFTER a product_selection has been made.
        :return:
        """
        if self.__product_specific_def:
            self.__pd_dir = os.path.dirname(self.__product_specific_def.__file__)
            self.__pd_modulepath = '.'.join(self.__product_specific_def.__name__.split('.')[0:-1])
            if hasattr(self.__product_specific_def, '__consumer__'):
                self.__consumer = '.'.join(self.__pd_modulepath.split('.')[0:-1] + [self.__product_specific_def.__consumer__])
        return

    def __get_product_manifest(self):
        """ Get Manifest
        :return:
        """

        def __generate_manifest(pid_param, cpn_params):
            """ Generate Product List
            -------------------------
            Build a product list to select from based on the 'product_definitions' directory content.

            Example of manifest (snippet):
            {
            'ADAPTER-ARCH': ('apollo.scripts.entsw.cat3.product_definitions.c3k_uplinks_def',
                             'C3650-STACK', '800-41681-01'),
            'NEWTONCR24': ('apollo.scripts.entsw.cat3.product_definitions.c3k_newtoncr_def',
                           'WS-C3850-24T', ['73-14443-08', '68-12345-01']),
            'WHITTAKERCR48U': ('apollo.scripts.entsw.cat3.product_definitions.c3k_nyquistcr_def',
                               'C9300-48UN', ['73-18506-01', '68-12346-01'])
            }
            :param (str) pid_param: flash parameter unique identifier1 (pid)
            :param (str|list) cpn_params: flash parameter unique identifier2,(3,4..)  i.e. cisco part number(s) CPN
            :return: Ordered Dict of tuples (fully qualified module, BasePID, CPN)
            """

            def __extract_pd_pids(_mfiles, _pd_dir, _module_path):
                log.debug("  filtering...") if self.__verbose_level >= 3 else None
                for mfile in _mfiles:
                    modulename = os.path.splitext(mfile)[0]
                    # Get family data without loading all the modules.
                    # Converting string to dict with ast has strict rules (see product definition header comments).
                    try:
                        family = common_utils.readfiledata(os.path.join(_pd_dir, mfile),
                                                           ast_flag=True,
                                                           start_pattern='^family[ \t]+=[ \t]+({)',
                                                           end_pattern='^(})[ \t]+#[ \t]+family_end')
                    except Exception:
                        family = None

                    # Check for data structure
                    if not family:
                        log.warning("No family definition found in {0}".format(mfile))
                        continue

                    log.debug("  family def captured.") if self.__verbose_level >= 3 else None
                    # Check for family filter
                    file_content = common_utils.readfiledata(os.path.join(_pd_dir, mfile), raw=True)
                    if not re.search("""__family__[ \t]*=[ \t]*['"]({0}).*?['"]""".format(self.__family_filter), file_content):
                        log.warning("  Prod Def '{0}' does not have a __family__ property!".format(mfile))
                        continue

                    # Get PIDs in Product Definition
                    for product in family.keys():
                        log.debug("    product={0}".format(product)) if self.__verbose_level >= 3 else None
                        if product.upper() != "COMMON":
                            pid = family.get(product, {}).get(pid_param, None)
                            cpns = []
                            for cpn_param in cpn_params:
                                cpn = family.get(product, {}).get(cpn_param, None)
                                cpns.append(cpn) if cpn else None
                            if pid and cpns:
                                # MUST have BOTH PID and CPN defined or it does NOT go in the manifest!!
                                qualified_module = '{0}.{1}'.format(_module_path, modulename)
                                product_mainfest[product] = UutDescriptor.Manifest(qualified_module, pid, cpns)
                return

            # deep debug: log.debug("Product Definition dir = {0}".format(pd_dir))
            log.debug("  Generating...")
            log.debug("  Filters = Line:{0}  Family:{1}".format(self.__line_filter, self.__family_filter))
            if not all([pid_param, cpn_params]):
                log.error("A PID param key name, and a CPN param key name MUST be provided.")
                return None

            cpn_params = [cpn_params] if not isinstance(cpn_params, list) else cpn_params
            product_mainfest = collections.OrderedDict()

            self.__extract_pd_base_location()
            for path, dirs, files in os.walk(self.__pd_dir, followlinks=True):
                if not re.search(self.__line_filter, path):
                    log.debug("  filtering...") if self.__verbose_level >= 3 else None
                    continue
                if os.path.basename(path) == 'product_definitions':
                    mfiles = [f for f in files if os.path.splitext(f)[1] == '.py' and f[0] != '_']
                    log.debug("  mfiles = {0}".format(mfiles)) if self.__verbose_level >= 3 else None
                    if '.common' in self.__pd_modulepath:
                        module_path = '.'.join(self.__pd_modulepath.split('.')[:-1] + path.split('/')[-2:])
                    elif '.cat' not in self.__pd_modulepath:
                        module_path = '.'.join(self.__pd_modulepath.split('.') + path.split('/')[-3:])
                    else:
                        module_path = self.__pd_modulepath
                    __extract_pd_pids(mfiles, path, module_path)

            return product_mainfest

        # Inputs
        locator_module = self.descriptor_params.pm_locator_module
        key_pairs = self.descriptor_params.pm_key_pairs
        mani_types = self.descriptor_params.pm_type
        if mani_types == 'STANDARD':
            mani_types = ['MAIN', 'PERIPH']
        elif not isinstance(mani_types, list):
            mani_types = [mani_types]

        # Generate a complete product list (a.k.a manifest)
        log.debug("  Generating Product Manifest...")
        product_manifest = dict()
        for mani_type in mani_types:
            cpn_params, pid_param = key_pairs.get(mani_type, (None, None))
            log.debug("  Get {0}, {1} manifest...".format(cpn_params, pid_param))
            product_manifest.update(__generate_manifest(pid_param=pid_param, cpn_params=cpn_params))

        self.__product_manifest = product_manifest
        return

    def __search_codename(self, product_selection, title=None):
        """ Search Codename (INTERNAL)
        Find the codename based on the product selection within the manifest.
        If a selection was NOT provided, the user will be prompted.
        :param (str) product_selection:
        :param (str) title:
        :param (bool) verbose:
        :return: product_codename or False
        """
        title = self.__product_line if not title else title
        if not product_selection:
            if self.apollo_go:
                product_selection = aplib.ask_question("Select a {0} Product: ".format(title),
                                                       answers=sorted(self.products_available))
            else:
                product_selection = input("Select a {0} Product [{1}]: ".format(title, self.products_available))

        log.debug("Product selection = '{0}'".format(product_selection))
        product_codename = ''

        # Determine the form of the product selection ---------------------
        cnames_frm_cpns = []
        cnames_frm_pids = []
        if common_utils.validate_cpn(product_selection, silent=True):
            # It is a CPN (can be 73-level or 68-level; i.e. PCBA or TAN)
            # Find all codenames matching this CPN; ignore the -xx suffix.
            # All 73-level CPNs may not be unique since multi PIDs can share the same PCBA and enable HW by SW option!
            # All 68-level CPNs are expected to be unique.
            # Product selection and manifest build
            log.debug("Product selection is a CPN.")
            cnames_frm_cpns = [k for k, v in self.__product_manifest.items() if
                               any([cpn[:-3] == product_selection[:-3] for cpn in v.cpns])]

        elif common_utils.validate_pid(product_selection, silent=True):
            # It is a PID or a codename.
            # Multiple codenames are possible since the same PID can show up on multi NPI programs (i.e. CR, CSR, etc.)
            if product_selection in self.__product_manifest.keys():
                log.debug("Product selection is a codename.")
                product_codename = product_selection
            else:
                log.debug("Product selection is a PID.")
                cnames_frm_pids = [k for k, v in self.__product_manifest.items() if v.pid == product_selection]
        else:
            log.error("Product selection not recognized as a PID/Codename or CPN!")
            log.error("Cannot continue. Please check the data entry when prompted for CPN/PID.")
            return None

        # Must have at least one codename.
        if not cnames_frm_pids and not cnames_frm_cpns and not product_codename:
            log.error("Product is not in the manifest.")
            log.error("Check the product definition files! The product selection='{0}'.!".format(product_selection))
            return None

        # Must have a unique codename!
        # 1. Check CPN's and use if unique
        # 2. Check PIDs and use if unique
        # 3. Check if selection IS a codename
        if len(cnames_frm_cpns) == 1:
            product_codename = cnames_frm_cpns[0]
        elif len(cnames_frm_pids) == 1:
            product_codename = cnames_frm_pids[0]
        elif product_codename:
            pass
        else:
            log.warning("Could not find a Product Codename since there was not a unique CPN or PID in the manifest!")
            log.warning("Check the product definition files and make sure the entries are correct!")
            log.warning("Also, the product selection might have to be a different type,")
            log.warning(" (e.g. 68-level instead of 73-level).  Refer to the 'Codenames from' lists below.")
            log.debug("Codenames from PID = {0}".format(cnames_frm_pids)) if cnames_frm_pids else None
            log.debug("Codenames from CPN = {0}".format(cnames_frm_cpns)) if cnames_frm_cpns else None
            return None

        ps_msg = "Product Codename = {0}".format(product_codename)
        log.info('-' * len(ps_msg))
        log.info(ps_msg)
        log.info('-' * len(ps_msg))

        return product_codename

    def __get_codename(self, product_selection, title=None):
        """ Get Codename
        Find the UNIQUE codename based on the product selection(s) within the manifest.
        See __search_codename(...) for more details.
        :param (str|list) product_selection:
        :param (str) title:
        :return: product_codename or False
        """
        product_selections = [product_selection] if not isinstance(product_selection, list) else product_selection

        for prod_select in product_selections:
            product_codename = self.__search_codename(prod_select, title=title)
            if product_codename:
                break
        else:
            raise UutDescriptorException("Product Selection '{0}' NOT available.".format(product_selection))

        self.__product_codename = product_codename
        return

    def __load_module(self):
        """ Load Product Definition Module
        :return:
        """
        if not self.__product_codename:
            msg = "Missing product codename."
            log.error(msg)
            log.error("A product selection must be made to obtain the product code.")
            raise UutDescriptorException(msg)

        if self.__product_codename not in self.__product_manifest:
            msg = "The product codename is not in the manifest!"
            log.error(msg)
            log.error("This can happen if the original manifest was changed while not updating the")
            log.error(" codename per the product selection.")
            raise UutDescriptorException(msg)

        pd_full_module_name = self.__product_manifest[self.__product_codename].module
        pd_module_name = pd_full_module_name.split('.')[-1:][0]
        log.debug("Prod Def Module file = {0}.py".format(pd_module_name))

        # Reload of heirarchy properties based on product selection
        self.__import_reload_dynamic_properties(pd_full_module_name)

        try:
            product_obj = importlib.import_module(self.__product_manifest[self.__product_codename].module) \
                if self.__product_manifest[self.__product_codename].module else None
        except ImportError as e:
            log.error("The Product Codename does not have a product definition module available to import.")
            log.error("Please check the product definitions directory for the product family.")
            log.error("Product Codename          = {0}".format(self.__product_codename))
            log.error("Product Definition Module = {0}".format(pd_full_module_name))
            raise UutDescriptorException(e.message)

        self.__product_specific_def = product_obj
        if not hasattr(self.__product_specific_def, '__family__'):
            raise UutDescriptorException("All product definition modules MUST have a '__family__' attribute.")
        self.__product_family = self.__product_specific_def.__family__
        return

    def __assemble_product_definition(self):
        verbose = True if self.__verbose_level > 2 else False
        section = self.descriptor_params.uut_config_assem_section
        # Sanity checks
        if not self.__product_specific_def:
            msg = 'The product definition is null; cannot assemble.'
            raise UutDescriptorException(msg)
        if not hasattr(self.__product_specific_def, 'family'):
            log.error("No 'family' data for the chosen product '{0}'.".format(self.__product_codename))
            log.error("Check the product definition; it MUST have the correct form.")
            raise UutDescriptorException("Missing 'family' in product definition.")

        # Update internal properties
        self.__product_line = self.__pl()
        self.__category = self.__ca()

        # Update all non-"family" properties.
        # -----------------------------------
        properties = []
        for p in [i for i in dir(self.__product_specific_def) if i[0] != '_' and i != 'family']:
            if type(getattr(self.__product_specific_def, p)) in [dict, list, str, int, collections.OrderedDict]:
                properties.append(p)
        for property in properties:
            if hasattr(self, property):
                action = 'override'
            else:
                action = 'assign new'
                self._dynamic_properties.append(property)
            setattr(self, property, getattr(self.__product_specific_def, property))
            log.debug("{0:<20} = {1} ({2})".format(property, type(getattr(self, property)), action))

        # Update the "family" properties (a.k.a. assembled uut_config)
        # ------------------------------------------------------------
        log.debug("{0:<20} = {1}".format('Product', self.__product_codename))
        log.debug("{0:<20} = {1}".format('Section', section))
        log.debug("{0:<20} = {1} ({2})".format('ProdDef Module',
                                               self.__product_specific_def.__name__,
                                               self.__product_specific_def.__file__))
        log.debug("{0:<20} = {1}".format('Category', self.__category))

        # Product Common section
        # ----------------------
        uut_config_common = dict()
        if section in ['BOTH', 'COMMON']:
            log.debug("Assembling section: COMMON ...")
            if 'COMMON' not in self.__product_specific_def.family:
                log.error("No 'COMMON' section for the chosen product definition '{0}'.".format(self.__product_codename))
                log.error("Check the product definition; it MUST have the correct form.")
                raise UutDescriptorException('Product definition needs COMMON section.')
            # Save common section
            uut_config_common = self.__product_specific_def.family['COMMON']

        # Product Specific section
        # ------------------------
        replace_list = False
        uut_config_pid_specific = dict()
        if section in ['BOTH', 'PROD']:
            log.debug("Assembling section: Product/PID ...")
            if self.__product_codename not in self.__product_specific_def.family:
                log.error("No product codename section for the chosen product definition '{0}'.".format(self.__product_codename))
                log.error("Check the product definition; it MUST have the correct form.")
                raise UutDescriptorException('Product codename not in product definition.')
            uut_config_pid_specific = self.__product_specific_def.family[self.__product_codename]
            # Do some extra loading of pcamaps if a peripheral
            if self.__category in ['PERIPH']:
                if 'pcamaps' in self.__product_specific_def.family['COMMON']:
                    pcamaps = self.__product_specific_def.family['COMMON'].get('pcamaps', {})
                if 'pcamaps' in self.__product_specific_def.family[self.__product_codename]:
                    pcamaps = self.__product_specific_def.family[self.__product_codename].get('pcamaps', {})
                log.debug("  Selection is a Perihperal: {0}".format(self.__category))
                replace_list = True
                log.debug(" (Note: COMMON keys that have list values will be replaced if the keys are in the product section. Periphs only.)")
                for i in range(1, 0x10):
                    dev_inst = str(i)
                    if dev_inst in pcamaps:
                        keys = pcamaps[dev_inst].keys()
                        log.debug("  Peripheral instance: {0}".format(i))
                        log.debug("  Items: {0}".format(keys))
                        for k in keys:
                            pcamaps[dev_inst][k] = self.__product_specific_def.family[self.__product_codename][k.upper()]
                uut_config_pid_specific.update({'pcamaps': pcamaps})

        # Add-in (another module not considered the UUT)
        # ----------------------------------------------
        uut_config_addin = dict()
        if section in ['ADD-IN']:
            log.debug("Assembling section: Product/PID Addition ...")
            if self.__product_codename not in self.__product_specific_def.family:
                log.error("No add-in available for the chosen product definition '{0}'.".format(self.__product_codename))
                log.error("Check the product definition; it MUST have the correct form.")
                raise UutDescriptorException("No add-in codename in the product definition.")
            log.debug("Add-in Selection: {0}".format(self.__product_codename))
            uut_config_addin = {'add-in': {self.__product_codename: self.__product_specific_def.family[self.__product_codename]}}

        # Combine recursively
        # -------------------
        uut_config = dict()
        common_utils.update_dict_recursively(uut_config, uut_config_common, verbose=verbose)
        common_utils.update_dict_recursively(uut_config, uut_config_pid_specific, list_replace=replace_list, verbose=verbose)
        common_utils.update_dict_recursively(uut_config, uut_config_addin, list_replace=False, verbose=verbose)

        # Special PID-specific updates for list replacement (i.e. no append)
        # ------------------------------------------------------------------
        pid_replace_lists = ['chamber_corners', 'chamber_profile', 'process_flow']
        if uut_config.get('pid_replace_lists'):
            pid_replace_lists.append(uut_config['pid_replace_lists'])
        for target_list in pid_replace_lists:
            if uut_config_pid_specific.get(target_list):
                uut_config[target_list] = uut_config_pid_specific[target_list]

        # Save the results
        # ----------------
        self.uut_config.update(uut_config)
        return

    def __update_traffic(self):
        # Update traffic cases
        traffic_cases = self.uut_config.get('traffic_cases', None)
        if not traffic_cases:
            log.debug("No Traffic Cases defined for the UUT. Please confirm product definition.")
            return
        if isinstance(traffic_cases, dict) and len(traffic_cases.keys()) > 0:
            log.debug("Traffic cases are loaded.  Removing library.")
            self.uut_config.pop('traffic_cases_library')
        elif isinstance(traffic_cases, tuple) and len(traffic_cases) == 2:
            log.debug("Checking reference traffic_cases={0}".format(traffic_cases))
            ref_cases = self.uut_config.get(traffic_cases[0], {}).get(traffic_cases[1], None)
            if not ref_cases or not isinstance(ref_cases, dict):
                log.warning("The 'traffic_cases' reference was not found!")
                return
            self.uut_config['traffic_cases'] = ref_cases
            log.debug("Traffic cases are loaded.  Removing library.")
            self.uut_config.pop(traffic_cases[0])
        else:
            log.warning("The traffic_cases={0} form is not recognized. Please correct the product definition.".format(traffic_cases))
            return
        log.debug("Traffic Cases: {0}".format(self.uut_config['traffic_cases'].keys()))
        if hasattr(self._callback, 'traffic') and hasattr(self._callback.traffic, 'fmdiags'):
            log.debug("Updating traffic.fmdiags ...")
            setattr(self._callback.traffic.fmdiags, '_traffic_cases', self.uut_config['traffic_cases'])
            # Add other updates here related to UUT selection.
            self._callback.traffic.fmdiags.set_attrs()
        return

    def __assemble_uut_network(self):
        if self.__standalone:
            log.debug("  Standalone; therefore no UUT network setup.")
            return

        log.debug("Assembling UUT Test Network...")
        log.debug("uut_conn = {0}".format(self.uut_conn))
        try:
            rs_key = self.descriptor_params.remote_server_key
            cfg_remote_server = aplib.apdicts.configuration_data.get(rs_key, {'IP': '', 'NETMASK': ''})
        except KeyError:
            log.warning("No Apollo configuration data for {0}.".format(rs_key))
            cfg_remote_server = {}

        # Get netmask first (server always has precedent)
        if self.server_config.get('eth1_nm', None):
            log.info("Using Local Server netmask.")
            target_netmask = self.server_config.get('eth1_nm')
        elif cfg_remote_server.get('NETMASK', None):
            log.info("Using Apollo Config netmask.")
            target_netmask = cfg_remote_server.get('NETMASK')
        else:
            log.warning("Using default netmask.")
            target_netmask = '255.255.255.0'

        # Get IP
        if cfg_remote_server.get('IP', None):
            log.info("Using Apollo Config {0} IP!".format(rs_key))
            target_server_ip = cfg_remote_server['IP']
        elif self.server_config.get('eth1_ip', None):
            log.info("Using Local Server IP.")
            target_server_ip = self.server_config.get('eth1_ip')
        else:
            log.warning("Using default IP.")
            target_server_ip = '10.1.1.1'

        self.server_config['server_ip'] = target_server_ip
        self.server_config['netmask'] = target_netmask
        self.server_config['uut_ip'] = common_utils.get_ip_addr_assignment(self.uut_conn, target_server_ip, target_netmask)

        self.__get_uut_network()
        log.debug("UUT Server IP = {0}".format(self.uut_config['server_ip']))
        log.debug("UUT Netmask   = {0}".format(self.uut_config['netmask']))
        log.debug("UUT IP        = {0}".format(self.uut_config['uut_ip']))
        return

    def __get_uut_network(self):
        self.uut_config['server_ip'] = self.server_config['server_ip']
        self.uut_config['netmask'] = self.server_config['netmask']
        self.uut_config['uut_ip'] = self.server_config['uut_ip']
        return

    def __parse_eco_manifest(self, eco_type=PRGM, cpn=None, cpn_rev=None, test_area=None):
        """ Parse ECO Manifest

        IMPORTANT: The 'eco_mainfest' SHOULD be present in the product definition.
               If it is not present, the operator will be prompted to enter the appropriate ECO; this is error
               prone and should be avoided by keeping the eco manifest up to date.

        The ECO Manifest item format is as follows:
        (partnum+rev, site): (programming_num, verification_num, [areas list], optional_desc)

        ECO Manifest Example:
            'eco_manifest': {
                ('73-14445-07B0', 'ALL'): ('EA526167', '73539', ['PCBST','PCB2C'], ''),
                ('73-14445-07A0', 'ALL'): ('EA520237', '66899', ['PCBST','PCB2C'], ''),
                ('73-14445-06A0', 'ALL'): ('E119776', '66899', ['PCBST','PCB2C'], ''),
                ('73-14445-0204', 'ALL'): ('E092313', '55089', ['PCBST','PCB2C'], ''),
                ('800-41087-07E0', 'ALL'): ('EA555228', '91780', ['ASSY','SYSBI','SYSFT'], ''),
                ('800-41087-07D0', 'ALL'): ('EA550394', '86992', ['ASSY','SYSBI','SYSFT'], ''),
                ('800-41087-0404', 'ALL'): ('E030614', '56601', ['ASSY','SYSBI','SYSFT'], ''),
                ('800-41087-0205', 'ALL'): ('E092313', '55112', ['ASSY','SYSBI','SYSFT'], ''),
                ('800-41087-07C0', 'FTX'): (None, '77466', ['SYSFT'], ''),
                ('800-41087-07C0', 'FTX'): (None, '73747', ['SYSFT'], ''),
                ...
            }

        :param eco_type: 'PRGM' or 'VRFY'
        :param cpn:
        :param cpn_rev:
        :param test_area:
        :return:
        """

        if eco_type not in [self.PRGM, self.VRFY]:
            log.error("Unrecognized ECO eco_type: '{0}'  (Must be PROGRAMMING or VERIFICATION.)".format(eco_type))
            return None

        test_area = self.test_area if not test_area else test_area
        location_prefix = common_utils.get_cmpd_testsite()

        if cpn and cpn_rev:
            log.debug("Explicit ECO lookup with CPN and Rev...")
        else:
            log.debug("Implicit ECO lookup based on PUID...")
            cpn = self.__puid.partnum
            cpn_rev = self.__puid.partnum_rev

        log.debug("CPN for ECO     = '{0}'".format(cpn))
        log.debug("CPN Rev for ECO = '{0}'".format(cpn_rev))
        log.debug("Site for ECO    = '{0}'".format(location_prefix))
        log.debug("Test Area       = {0}".format(test_area))
        cpn_and_rev = '{0}{1}'.format(cpn, cpn_rev)

        # Determine usable key from smallest to largest scope.
        if (cpn_and_rev, location_prefix) in self.uut_config.get('eco_manifest', {}):
            log.debug("Scope = location indicated.")
            eco_index = (cpn_and_rev, location_prefix)
        elif (cpn_and_rev, 'ALL') in self.uut_config.get('eco_manifest', {}):
            log.debug("Scope = ALL locations.")
            eco_index = (cpn_and_rev, 'ALL')
        else:
            log.debug("Scope = UNDETERMINED!")
            eco_index = None
            common_utils.print_large_dict(self.uut_config.get('eco_manifest', {}), sort=True, exploded=False)

        if not eco_index:
            log.error("No ECO index: {0} in the ECO manifest.".format(eco_index))
            return None

        log.debug("ECO index       = {0}".format(eco_index))

        raw_eco = self.uut_config.get('eco_manifest', {}).get(eco_index, (None, None, [], ''))
        eco = self.ECOMani(*raw_eco)

        if test_area not in eco.areas:
            if test_area != 'DBGSYS':
                log.error("ECO manifest test areas entry ({0}) does NOT have this test area ({1}).".
                          format(eco.areas, test_area))
                log.error("Please check the ECO manifest in the product definition file.")
                return None
            else:
                log.warning(
                    "ECO manifest test areas entry ({0}) will be IGNORED for ({1}).".format(eco.areas, test_area))

        eco_num = getattr(eco, eco_type.lower())

        log.debug("ECO Type        = {0}".format(eco_type))
        log.debug("ECO Num         = {0}".format(eco_num))
        log.debug("ECO Desc        = {0}".format(eco.desc))

        return eco_num

    def __update_mode_mgr(self):
        if not self._callback:
            if not self.__standalone:
                log.error("Cannot update the Mode Manager since the callback is missing.")
                log.error("An update of Mode Manger should only occur with a new product_selection.")
                log.error("Please check the class usage.")
                raise UutDescriptorException('Callback error for Mode Manager.')
            else:
                log.debug("UutDescriptor in standalone mode (i.e. data usage only).")
                return
        self._callback.mode_mgr.uut_state_machine = self.uut_state_machine
        self._callback.mode_mgr.uut_prompt_map = self.uut_prompt_map
        return