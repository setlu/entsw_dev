"""
ENTSW CATALYST Series 2
"""

import apollo.scripts.entsw.configs.jmx2.jmx2_entsw_common as jmx2_entsw_common


__title__ = "Enterprise Switching CATALYST Series 2"
__version__ = '2.0.0'
__author__ = 'bborel'


def entsw_cat2_config():
    jmx2_entsw_common.cat2_pcbft_production('172.30.55.147', '10.1.1.1')
    jmx2_entsw_common.cat2_sysft_production('172.30.55.147', '10.1.1.1')
    return