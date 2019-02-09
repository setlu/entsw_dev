"""
IOS Manifest for ALL Catalyst Series 5 Products

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

__title__ = "Catalyst Series 5 IOS Manifest"
__version__ = '2.0.0'

ios_manifest = {
    # POLARIS ------------------------------------------------------------------------
    # 16.8 ----------------------------------------------------------------------------
    'S9500UK9-168': {
        'name': 'POLARIS',
        'platforms': 'C9500',
        'product_id': 'S9500UK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat9k_iosxe.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': '5a7ebf6cfc15b83125819b13feec25a9',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9500ULPEK9-168': {
        'name': 'POLARIS',
        'platforms': 'C9500',
        'product_id': 'S9500ULPEK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': '95be5c0ee5f8e800948564456182ae7e',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    # 16.9 ----------------------------------------------------------------------------
    'S9500UK9-169': {
        'name': 'POLARIS',
        'platforms': 'C9500',
        'product_id': 'S9500UK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.1/.3DES',
        'image_name': 'cat9k_iosxe.16.09.01.SPA.bin',
        'version': '16.9.1',
        'md5': '258fb60ca843a2db78d8dba5a9f64180',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9500ULPEK9-169': {
        'name': 'POLARIS',
        'platforms': 'C9500',
        'product_id': 'S9500ULPEK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.1/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.09.01.SPA.bin',
        'version': '16.9.1',
        'md5': 'eb1c08fbd3d7fcf9130258f982917448',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
}
