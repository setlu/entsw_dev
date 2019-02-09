"""
--------------
Catalyst Steps

Use this for the PRE-SEQ of all products.
This is the core set of steps used by the base Catalyst() class to get basic information before starting a SEQ.

[Catalyst] --> [CatalystX] --> [Catalyst<Product>]
    ^
    |
The Catalyst() class is at the root of the inheritance for the product class.
The steps using this class should be kept at a minimum.

--------------
"""
import logging
import apollo.libs.lib as aplib
import catalyst

global c

log = logging.getLogger(__name__)


# ----------------------------------------------------------------------------------------------------------------------
# INIT + FINAL
# ----------------------------------------------------------------------------------------------------------------------
def init_catalyst():
    global c
    c = catalyst.Catalyst()
    return aplib.PASS

def final():
    global c
    c = None
    return aplib.PASS

# ----------------------------------------------------------------------------------------------------------------------
# GENERAL MANAGEMENT (UUT Descriptor, Mode Mgr, Process)
# ----------------------------------------------------------------------------------------------------------------------
def ud_print_uut_descriptor():
    return c.ud.print_uut_descriptor()

def ud_print_product_manifest():
    return c.ud.print_product_manifest()

def ud_print_uut_config():
    return c.ud.print_uut_config()

def ud_set_puid_keys(**kwargs):
    return c.ud.set_puid_keys(**kwargs)

def process_uut_discover(method, **kwargs):
    return c.process.uut_discover(method, **kwargs)

def process_uut_scan(**kwargs):
    return c.process.uut_scan(**kwargs)

def ud_save():
    return c.ud.save()

def ud_retrieve():
    return c.ud.retrieve()

def ud_cache_ud_data():
    return c.process.cache_ud_data()

def process_add_tst():
    return c.process.add_tst()

def process_update_cfg_model_num(**kwargs):
    return c.process.update_cfg_model_num(**kwargs)

def process_analyze_lineid(**kwargs):
    return c.process.analyze_lineid(**kwargs)

def process_get_serial_num(**kwargs):
    return c.process.get_serial_num(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# Debug
# ----------------------------------------------------------------------------------------------------------------------
def process_manual_select_family(area_seq_module, **kwargs):
    return c.process.manual_select_family(area_seq_module, **kwargs)

def process_uut_debug_scan(**kwargs):
    return c.process.uut_debug_scan(**kwargs)

# ----------------------------------------------------------------------------------------------------------------------
# POWER
# ----------------------------------------------------------------------------------------------------------------------
def power_cycle_on(**kwargs):
    return c.power.cycle_on(**kwargs)

def power_on(**kwargs):
    return c.power.on(**kwargs)

def power_off(**kwargs):
    return c.power.off(**kwargs)

