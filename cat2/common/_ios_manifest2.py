"""
IOS Manifest for ALL Catalyst Series 2 Products

The manifest file contains descriptive data about all shippable IOS images and support images.
Note: This data MUST match the entries in OSCAR & CNFwork for it to be the most current.

Structure for each entry:
'SW-PID': {
    'name': <str>,
    'platforms': <str> or <list> of PID prefix,
    'cco_location': <str> of unix path,
    'image_name': <str> filename,
    'version': <str> x.x.x,
    'md5': <str> hex,
    'rec':  <str> filename,
    'SR_pkgs': <list> of filenames
}
"""

# TODO: Mechanism to automatically update the manifest entry's content.  New entires are created as part of the NPI process.

__title__ = "Catalyst Series 2 IOS Manifest"
__version__ = '2.0.0'

ios_manifest = {
    # GENERIC -------------------------------------------------------------------
    'SGENERIC-0SE': {
        'name': 'GENERIC',
        'platforms': ['WS-C2960'],
        'product_id': 'SGENERIC-0SE',
        'cco_location': '',
        'image_name': 'cat2k_caa-universalk9.bin',
        'version': '1.0.0',
        'md5': '',
        'recovery':  'cat2k_caa-recovery.bin',
        'SR_pkgs': []
    },

    # EX ------------------------------------------------------------------------
    # None

    # DARYA ------------------------------------------------------------------------
    # None

    # AMUR ------------------------------------------------------------------------
    # None

    # BENI ------------------------------------------------------------------------
    # None

    # POLARIS ------------------------------------------------------------------------
    # 16.6 ----------------------------------------------------------------------------
    'S9300UK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9200',
        'product_id': 'S9200UK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.2/.3DES',
        'image_name': 'cat9k_iosxe.16.06.02.SPA.bin',
        'version': '16.6.2',
        'md5': 'b8029e3339c1587c386e4cb907ba5daf',
        'recovery': ('cat9k_caa-recovery.SPA.16.06.02.bin', 'cat9k_caa-recovery.SPA.bin'),
        'SR_pkgs': []
    },
    'S9300ULPEK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9200',
        'product_id': 'S9200ULPEK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.2/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.06.02.SPA.bin',
        'version': '16.6.2',
        'md5': 'c49c0fc27b06e415d103511db378da4e',
        'recovery': ('cat9k_caa-recovery.SPA.16.06.02.bin', 'cat9k_caa-recovery.SPA.bin'),
        'SR_pkgs': []
    },

}
