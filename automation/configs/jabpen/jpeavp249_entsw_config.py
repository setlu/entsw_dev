"""
C2K Config (JPE dev)
"""

from apollo.libs import lib
import apollo.config.common.c2k.c2k_common_stations as c2k_common_stations

__version__ = "0.0.2"
__title__ = "Enterprise Switching C2k Config for JPE"
__author__ = ['bborel', 'JPE_Team']


TS_START_PORT = {'2500': 2001, '2600': 2033, '2800': 2002, '2900': 2003, 'LantronixUSB': 2017, 'LantronixCon': 2001}

QUAKE_MOTHERBOARD_PIDS = ['73-18785-*', '73-18785-*', '73-18775-*', '73-18831-*', '73-18775-*']

QUAKE_BASE_PIDS = ['C9200-48T-4G', 'C9200-24T-4G', 'C9200-48P-4G', 'C9200-24P-4X', 'C9200-48P-4X',
                   'C9200-24T-4X', 'C9200-48T-4X', 'C9200-48P8X-2Y', 'C9200-24P8X-2Y', 'C9200-24P8X-4X',
                   'C9200-48P12X-4X', 'C9200-24P-4G', 'C9200L-48P-4G', 'C9200L-48P-4X', 'C9200L-48T-4G',
                   'C9200L-48T-4X', 'C9200L-24P-4G', 'C9200L-24P-4X', 'C9200L-24T-4G', 'C9200L-24T-4X',
                   'C9200L-48PXG-2Y', 'C9200L-48PXG-4X', 'C9200L-24PXG-2Y', 'C9200L-24PXG-4X',
                   'C9200-48T', 'C9200-48P', 'C9200-24P', 'C9200-24T', 'C9200-24PXG', 'C9200-48PXG']


def show_version():
    print("{0:<30}  v:{1}  ({2})".format(__title__, __version__, __name__))


def entsw_c2k_config():
    """
    :return:
    """
    show_version()
    c2k_common_stations.show_version()

    config = lib.get_station_configuration()

    #
    # SYSFT ---------------------------------------------------------
    station_details = dict(
        product_line='C9200', generation='GEN3',
        station='Station_A_01', uut_count=16,
        pid_cpn_list=QUAKE_BASE_PIDS + QUAKE_MOTHERBOARD_PIDS,
        server_ip='10.1.1.1', dwnld_server_ip='10.1.1.1',
        ts_ip=['10.1.1.200', '10.1.1.201'], ts_start_port=TS_START_PORT['LantronixCon'],
        ts_user='sysadmin', ts_pswd='PASS', ts_model='Lantronix',
        poe1_ts_ip=None, poe1_ts_start_port=0, sc_name=["Master1", "Master2"],
        pcbox_ip='10.1.1.3', pcbox_port=[2003, 2004]
    )
    c2k_common_stations.quake_switch_pcbft_common(config, **station_details)

    return
