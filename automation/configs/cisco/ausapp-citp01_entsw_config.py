""" CITP USTX Configuration File

Continuous Integration Test Platform - Austin,TX
Enterprise Switching
Host: ausapp-citp01
Primary IP   (eth0): 10.89.133.12
Secondary IP (eth1): 10.1.1.1
CIMC IP: 10.89.133.16

NOTE: This is a comprehensive config file; i.e. this config is setup to mimic ALL stations.
      In contrast, a "production server" would only focus on one test area.

"""

import apollo.scripts.entsw.configs.cisco.ausapp_citp_entsw_common as ausapp_citp_entsw_common

__title__ = "Enterprise Switching Config for CITP Austin"
__version__ = "2.0.0"
__author__ = ['bborel']


def entsw_cat3_config():
    ausapp_citp_entsw_common.cat3_lab('10.89.133.12', '10.1.1.1')
    return


def entsw_cat2_config():
    ausapp_citp_entsw_common.cat2_lab('10.89.133.12', '10.1.1.1')
    return
