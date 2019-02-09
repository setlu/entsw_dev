"""
IOS Manifest for ALL Catalyst Series 4 Products

The manifest file contains descriptive data about all shippable IOS images and support images.
Note: This data MUST match the entries in OSCAR & CNFwork for it to be the most current.

Structure for each entry:
'SW-PID': {
    'name': <str>,
    'platforms': <str> or <list> of PID prefix,
    'cco_location': <str> of unix path,
    'image_name': <str> filename,
    'md5': <str> hex,
    'rec':  <str> filename,
    'SR_pkgs': <list> of filenames
}
"""

# TODO: Mechanism to automatically update the manifest entry's content.  New entires are created as part of the NPI process.

__title__ = "Catalyst Series 4 IOS Manifest"
__version__ = '2.0.0'

ios_manifest = {
    # GENERIC -------------------------------------------------------------------
    'SGENERIC-0SE': {
        'name': 'GENERIC',
        'platforms': ['C9400'],
        'product_id': 'SGENERIC-0SE',
        'cco_location': '',
        'image_name': 'cat4k_caa-universalk9.bin',
        'md5': '',
        'recovery':  'cat4k_caa-recovery.bin',
        'SR_pkgs': []
    },

    # TEST -------------------------------------------------------------------
    'STEST': {
        'name': 'POLARIS',
        'platforms': ['C9400'],
        'product_id': 'STEST',
        'cco_location': '',
        'image_name': 'cat9k_iosxe.v169_throttle.bundle_180520005742.SSA.bin',
        'version': '16.9',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },
    'STEST1': {
        'name': 'POLARIS',
        'platforms': ['C9400'],
        'product_id': 'STEST1',
        'cco_location': '',
        'image_name': 'cat9k_iosxe.BLD_V166_1_THROTTLE_LATEST_20170725_143356_V16_6_0_272.SSA.bin',
        'version': '16.6',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },
    'STEST2': {
        'name': 'POLARIS',
        'platforms': ['C9400'],
        'product_id': 'STEST2',
        'cco_location': '',
        'image_name': 'cat9k_iosxe.BLD_V166_THROTTLE_LATEST_20171101_032038.SSA.bin',
        'version': '16.6',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },

    # POLARIS ------------------------------------------------------------------------
    'S9400UK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9400',
        'product_id': 'S9400UK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.3/.3DES',
        'image_name': 'cat9k_iosxe.16.06.03.SPA.bin',
        'version': '16.6.3',
        'md5': 'db5697a5b0b69da7d17f19548d5330e1',
        'recovery': ('cat9k_caa-recovery.SPA.16.06.03.bin', 'cat9k_caa-recovery.SPA.bin'),
        'SR_pkgs': []
    },
    'S9400ULPEK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9400',
        'product_id': 'S9400ULPEK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.3/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.06.03.SPA.bin',
        'version': '16.6.3',
        'md5': '',
        'recovery': ('cat9k_caa-recovery.SPA.16.06.03.bin', 'cat9k_caa-recovery.SPA.bin'),
        'SR_pkgs': []
    },

}
