"""
IOS Manifest for ALL Catalyst Series 3 Products

The manifest file contains descriptive data about all shippable IOS images and support images.
Note: This data MUST match the entries in OSCAR & CNFwork/CNFv2Exp for it to be the most current.

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

__title__ = "Catalyst Series 3 IOS Manifest"
__version__ = '2.0.0'

ios_manifest = {
    # GENERIC -------------------------------------------------------------------
    'SGENERIC-0SE': {
        'name': 'GENERIC',
        'platforms': ['WS-C3850', 'WS-C3650'],
        'product_id': 'SGENERIC-0SE',
        'cco_location': '',
        'image_name': 'cat3k_caa-universalk9.bin',
        'version': '1.0.0',
        'md5': '',
        'recovery':  'cat3k_caa-recovery.bin',
        'SR_pkgs': []
    },

    'STEST': {
        'name': 'POLARIS',
        'platforms': ['WS-C3850', 'C9300'],
        'product_id': 'STEST',
        'cco_location': 'tftpboot',
        'image_name': 'cat9k_iosxe.SPA.bin',
        'version': '1.0.0',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },
    'STEST2': {
        'name': 'POLARIS',
        'platforms': ['WS-C3850', 'C9300'],
        'product_id': 'STEST2',
        'cco_location': 'tftpboot',
        'image_name': 'cat9k_iosxe.SPA.bin',
        'version': '1.0.0',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },
    'STEST-C9300L-P2': {
        'name': 'POLARIS',
        'platforms': ['C9300L'],
        'product_id': 'STEST-C9300L-P2',
        'cco_location': 'tftpboot',
        'image_name': 'cat9k_iosxe.BLD_POLARIS_DEV_LATEST_20180921_002213.SSA.bin',
        'version': '16.9.0',
        'md5': '',
        'recovery': '',
        'SR_pkgs': []
    },

    # EX ------------------------------------------------------------------------
    'S3850UK9-32-0SE': {
        'name': 'EX',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-32-0SE',
        'cco_location': '/auto/beyond.150.bin2/03.02.03.SE.150-1.EX3/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.02.03.SE.150-1.EX3.bin',
        'version': '3.2.3',
        'md5': '1f4673f287c85ed7e1dd39b6040be5f1',
        'recovery':  ('cat3k_caa-recovery.SPA.03.02.03.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.02.03.XSR1.73.pkg']
    },
    'S3850ULPEK9-32-0SE': {
        'name': 'EX',
        'platforms': 'WS-C3850',
        'product_id': 'S3850LPEUK9-32-0SE',
        'cco_location': '/auto/beyond.150.bin2/03.02.03.SE.150-1.EX3/.3DES',
        'image_name':  'cat3k_caa-universalk9ldpe.SPA.03.02.03.SE.150-1.EX3.bin',
        'version': '3.2.3',
        'md5': '7c6fd9ae49cb637dca5cc7765c9061d3',
        'recovery':  ('cat3k_caa-recovery.SPA.03.02.03.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.02.03.XSR1.73.pkg']
    },

    # DARYA ------------------------------------------------------------------------
    'S3850UK9-33SE': {
        'name': 'DARYA',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-33SE',
        'cco_location': '/auto/beyond.150.bin2/03.03.05.SE.150-1.EZ5/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.03.05.SE.150-1.EZ5.bin',
        'version': '3.3.5',
        'md5': 'ae2c090fa71bb1dd08daae4e74e9305e',
        'recovery':  ('cat3k_caa-recovery.SPA.03.03.05.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.03.05.ZSR2.35.pkg']
    },
    'S3850ULPEK9-33SE': {
        'name': 'DARYA',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-33SE',
        'cco_location': '/auto/beyond.150.bin2/03.03.05.SE.150-1.EZ5/.3DES',
        'image_name':  'cat3k_caa-universalk9ldpe.SPA.03.02.03.SE.150-1.EX3.bin',
        'version': '3.3.5',
        'md5': '95594a60301f0aa9d88273db27a7d650',
        'recovery':  ('cat3k_caa-recovery.SPA.03.03.05.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.03.05.ZSR2.35.pkg']
    },
    'S3650UK9-33SE': {
        'name': 'DARYA',
        'platforms': 'WS-C3650',
        'product_id': 'S3650UK9-33SE',
        'cco_location': '/auto/beyond.150.bin2/03.03.05.SE.150-1.EZ5/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.03.05.SE.150-1.EZ5.bin',
        'version': '3.3.5',
        'md5': 'ae2c090fa71bb1dd08daae4e74e9305e',
        'recovery':  ('cat3k_caa-recovery.SPA.03.03.05.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.03.05.ZSR2.35.pkg']
    },
    'S3650ULPEK9-33SE': {
        'name': 'DARYA',
        'platforms': 'WS-C3650',
        'product_id': 'S3650ULPEK9-33SE',
        'cco_location': '/auto/beyond.150.bin2/03.03.05.SE.150-1.EZ5/.3DES',
        'image_name':  'cat3k_caa-universalk9ldpe.SPA.03.03.05.SE.150-1.EZ5.bin',
        'version': '3.3.5',
        'md5': '95594a60301f0aa9d88273db27a7d650',
        'recovery':  ('cat3k_caa-recovery.SPA.03.03.05.SE.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.03.05.ZSR2.35.pkg']
    },

    # AMUR ------------------------------------------------------------------------
    'S3850UK9-36E': {
        'name': 'AMUR',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-36E',
        'cco_location': '/auto/beyond.152.bin02/03.06.06.E.152-2.E6/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.06.06.E.152-2.E6.bin',
        'version': '3.6.6',
        'md5': '7c2abd4f5856b80afbcc283f6f12797a',
        'recovery': ('cat3k_caa-recovery.SPA.03.06.06.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.06.02.PSR3.65.pkg']
    },
    'S3850ULPEK9-36E': {
        'name': 'AMUR',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-36E',
        'cco_location': '/auto/beyond.152.bin02/03.06.06.E.152-2.E6/.3DES',
        'image_name': 'cat3k_caa-universalk9ldpe.SPA.03.06.06.E.152-2.E6.bin',
        'version': '3.6.6',
        'md5': '23b7f2a268ffa60089a18c6c9cc54c38',
        'recovery': ('cat3k_caa-recovery.SPA.03.06.06.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.06.02.PSR3.65.pkg']
    },
    'S3650UK9-36E': {
        'name': 'AMUR',
        'platforms': 'WS-C3650',
        'product_id': 'S3650UK9-36E',
        'cco_location': '/auto/beyond.152.bin02/03.06.06.E.152-2.E6/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.06.06.E.152-2.E6.bin',
        'version': '3.6.6',
        'md5': '7c2abd4f5856b80afbcc283f6f12797a',
        'recovery': ('cat3k_caa-recovery.SPA.03.06.06.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.06.02.PSR3.65.pkg']
    },
    'S3650ULPEK9-36E': {
        'name': 'AMUR',
        'platforms': 'WS-C3650',
        'product_id': 'S3650ULPEK9-36E',
        'cco_location': '/auto/beyond.152.bin02/03.06.06.E.152-2.E6/.3DES',
        'image_name': 'cat3k_caa-universalk9ldpe.SPA.03.06.06.E.152-2.E6.bin',
        'version': '3.6.6',
        'md5': '23b7f2a268ffa60089a18c6c9cc54c38',
        'recovery': ('cat3k_caa-recovery.SPA.03.06.06.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.06.02.PSR3.65.pkg']
    },

    # BENI ------------------------------------------------------------------------
    'S3850UK9-37E': {
        'name': 'BENI',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-37E',
        'cco_location': '/auto/beyond.152.bin02/03.07.05.E.152-3.E5/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.07.05.E.152-3.E5.bin',
        'version': '3.7.5',
        'md5': 'd6f1f24a30dc67697a0c815661ba670c',
        'recovery':  ('cat3k_caa-recovery.SPA.03.07.05.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.07.01.BSR3.03.pkg']
    },
    'S3850ULPEK9-37E': {
        'name': 'BENI',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-37E',
        'cco_location': '/auto/beyond.152.bin02/03.07.05.E.152-3.E5/.3DES',
        'image_name':  'cat3k_caa-universalk9ldpe.SPA.03.07.05.E.152-3.E5.bin',
        'version': '3.7.5',
        'md5': '3a0d8a882b5927ed6394e6958be59e2e',
        'recovery':  ('cat3k_caa-recovery.SPA.03.07.05.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.07.01.BSR3.03.pkg']
    },
    'S3650UK9-37E': {
        'name': 'BENI',
        'platforms': 'WS-C3650',
        'product_id': 'S3650UK9-37E',
        'cco_location': '/auto/beyond.152.bin02/03.07.05.E.152-3.E5/.3DES',
        'image_name': 'cat3k_caa-universalk9.SPA.03.07.05.E.152-3.E5.bin',
        'version': '3.7.5',
        'md5': 'd6f1f24a30dc67697a0c815661ba670c',
        'recovery':  ('cat3k_caa-recovery.SPA.03.07.05.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.07.01.BSR3.03.pkg']
    },
    'S3650ULPEK9-37E': {
        'name': 'BENI',
        'platforms': 'WS-C3650',
        'product_id': 'S3650ULPEK9-37E',
        'cco_location': '/auto/beyond.152.bin02/03.07.05.E.152-3.E5/.3DES',
        'image_name':  'cat3k_caa-universalk9ldpe.SPA.03.07.05.E.152-3.E5.bin',
        'version': '3.7.5',
        'md5': '3a0d8a882b5927ed6394e6958be59e2e',
        'recovery':  ('cat3k_caa-recovery.SPA.03.07.05.E.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': ['cat3k_caa-drivers.SSA.03.07.01.BSR3.03.pkg']
    },

    # POLARIS ------------------------------------------------------------------------
    'S3850UK9-162': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-162',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.2.2/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.02.02.SPA.bin',
        'version': '16.2.2',
        'md5':       '29efb2fb7e461d7b683602a616c69d53',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3850ULPEK9-162': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-162',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.2.2/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.02.02.SPA.bin',
        'version': '16.2.2',
        'md5':       '86db34bb86558ac785a27393fd2c83d0',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3650UK9-162': {
        'name': 'POLARIS',
        'platforms': 'WS-C3650',
        'product_id': 'S3650UK9-162',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.2.2/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.02.02.SPA.bin',
        'version': '16.2.2',
        'md5':       '29efb2fb7e461d7b683602a616c69d53',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3650ULPEK9-162': {
        'name': 'POLARIS',
        'platforms': 'WS-C3650',
        'product_id': 'S3650ULPEK9-162',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.2.2/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.02.02.SPA.bin',
        'version': '16.2.2',
        'md5':       '86db34bb86558ac785a27393fd2c83d0',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },

    # 16.3 ----------------------------------------------------------------------------
    'S3850UK9-163': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-163',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.3.7/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.03.07.SPA.bin',
        'version': '16.3.7',
        'md5':       '0c29b6f652d85c69c90b5c921a5a343b',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3850ULPEK9-163': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-163',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.3.7/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.03.07.SPA.bin',
        'version': '16.3.7',
        'md5':       '5d370835a2b6add55063c811da00acb0',
        'recovery':  ('cat3k_caa-recovery.16.02.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },

    # 16.4 ----------------------------------------------------------------------------
    'S3850UK9-164': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-164',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.4.1/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.04.01.SPA.bin',
        'version': '16.3.5b',
        'md5':       'b27903e798f1b0831f921184117d34e7',
        'recovery':  ('cat3k_caa-recovery.16.04.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3850ULPEK9-164': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-164',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.4.1/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.04.01.SPA.bin',
        'version': '16.3.5b',
        'md5':       'df3069c70325ba716e8f58d0a5ed69b4',
        'recovery':  ('cat3k_caa-recovery.16.04.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },

    # 16.5 ----------------------------------------------------------------------------
    'S3850UK9-165': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-165',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.5.1a/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.05.01a.SPA.bin',
        'version': '16.5.1a',
        'md5':       '1647cc3e84126147da5cd36c0b6c8f2a',
        'recovery':  ('cat3k_caa-recovery.16.05.01a.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S3850ULPEK9-165': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-165',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.5.1a/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.05.01a.SPA.bin',
        'version': '16.5.1a',
        'md5':       'cf2d9a8a5c399f900956cb66ae417947',
        'recovery':  ('cat3k_caa-recovery.16.05.01a.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S9300UK9-165': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300UK9-165',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.5.1a/.3DES',
        'image_name': 'cat9k_iosxe.16.05.01a.SPA.bin',
        'version': '16.5.1a',
        'md5': '3a631744b172c14fffb349de0921b0e6',
        'recovery': ('cat9k-recovery.16.05.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9300ULPEK9-165': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300ULPEK9-165',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.5.1a/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.05.01a.SPA.bin',
        'version': '16.5.1a',
        'md5': '6946877461b1345411daa2b471581b41',
        'recovery': ('cat9k-recovery.16.05.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },

    # 16.6 ----------------------------------------------------------------------------
    'S3850UK9-166': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850UK9-166',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.6.4/.3DES',
        'image_name':     'cat3k_caa-universalk9.16.06.04.SPA.bin',
        'version': '16.6.4',
        'md5':       '8635172564abd2e6c7a48791f2695e14',
        'recovery':  ('cat3k_caa-recovery.16.06.04.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   [],
    },
    'S3850ULPEK9-166': {
        'name': 'POLARIS',
        'platforms': 'WS-C3850',
        'product_id': 'S3850ULPEK9-166',
        'cco_location':  '/auto/beyond.iosxe-4/16/bin/16.6.4/.3DES',
        'image_name':     'cat3k_caa-universalk9ldpe.16.06.04.SPA.bin',
        'version': '16.6.4',
        'md5':       '552e349473ae1f7752ed53d4843e43c0',
        'recovery':  ('cat3k_caa-recovery.16.06.04.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs':   []
    },
    'S9300UK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300UK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.4/.3DES',
        'image_name': 'cat9k_iosxe.16.06.04.SPA.bin',
        'version': '16.6.4',
        'md5': 'd3c46a054bb31773e4090899b193c949',
        'recovery': ('cat9k-recovery.16.06.04.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': [(('cat9k-srdriver.V166_851_CAT9KSR_FC1.SPA.pkg', '251fbb5a605987b2118617cd121d84e2'), ('cat9k-srdriver.V166_851_CAT9KSR_FC1.SPA.pkg', '251fbb5a605987b2118617cd121d84e2')),
                    (('cat9k-srdriver.V166_896_CAT9KSR_FC8.SPA.pkg', 'cdf2e858a04bfcb6fa8dd6c65b66aca1'), ('cat9k-srdriver.V166_896_CAT9KSR_FC8.SPA.pkg', 'cdf2e858a04bfcb6fa8dd6c65b66aca1'))]
    },
    'S9300ULPEK9-166': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300ULPEK9-166',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.4/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.06.04.SPA.bin',
        'version': '16.6.4',
        'md5': '1f76532b01b24d30b0e3246ee82923ba',
        'recovery': ('cat9k_recovery.16.06.04.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': [(('cat9k-srdriver.V166_901_CAT9KSR_FC6.SPA.pkg', '2f23ec6693b076e8d52b6dbc0400b57a'), ('cat9k-srdriver.V166_901_CAT9KSR_FC6.SPA.pkg', '2f23ec6693b076e8d52b6dbc0400b57a'))]
    },

    # 16.8 ----------------------------------------------------------------------------
    'S3850UK9-168': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850UK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat3k_caa-universalk9.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': 'ce4dd8f684f11a6605c6194395f28487',
        'recovery': ('cat3k_caa-recovery.16.08.01a.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S3850ULPEK9-168': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850ULPEK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat3k_caa-universalk9ldpe.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': 'f3b52f18bbcb5a16ae0fe5407ed68a35',
        'recovery': ('cat3k_caa-recovery.16.08.01a.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S9300UK9-168': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300UK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat9k_iosxe.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': '5a7ebf6cfc15b83125819b13feec25a9',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9300ULPEK9-168': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300ULPEK9-168',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.8.1a/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.08.01a.SPA.bin',
        'version': '16.8.1a',
        'md5': '95be5c0ee5f8e800948564456182ae7e',
        'recovery': ('cat9k-recovery.16.08.01a.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    # 16.9 ----------------------------------------------------------------------------
    'S3850UK9-169': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850UK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.2/.3DES',
        'image_name': 'cat3k_caa-universalk9.16.09.02.SPA.bin',
        'version': '16.9.2',
        'md5': '1440b1249d762ccfd0b3fd327c3e7158',
        'recovery': ('cat3k_caa-recovery.16.09.02.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S3850ULPEK9-169': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850ULPEK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.2/.3DES',
        'image_name': 'cat3k_caa-universalk9ldpe.16.09.02.SPA.bin',
        'version': '16.9.2',
        'md5': 'c50f853c743368192d8b7e1ca2cd999e',
        'recovery': ('cat3k_caa-recovery.16.09.02.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S9300UK9-169': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300UK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.2/.3DES',
        'image_name': 'cat9k_iosxe.16.09.02.SPA.bin',
        'version': '16.9.2',
        'md5': '8257b6be4bce32db972e14c32bc3968f',
        'recovery': ('cat9k-recovery.16.09.02.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9300ULPEK9-169': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300ULPEK9-169',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.9.2/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.09.02.SPA.bin',
        'version': '16.9.2',
        'md5': 'd84d5ae59c5a5cc07580927a29ef40dd',
        'recovery': ('cat9k-recovery.16.09.02.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },

    # 16.10 ----------------------------------------------------------------------------
    'S3850UK9-1610': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850UK9-1610',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.10.1/.3DES',
        'image_name': 'cat3k_caa-universalk9.16.09.02.SPA.bin',
        'version': '16.10.1',
        'md5': 'd9688ab68ddd7f61f10c083b463467e2',
        'recovery': ('cat3k_caa-recovery.16.10.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S3850ULPEK9-1610': {
        'name': 'POLARIS',
        'platforms': 'C3850',
        'product_id': 'S3850ULPEK9-1610',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.10.1/.3DES',
        'image_name': 'cat3k_caa-universalk9.16.10.01.SPA.bin',
        'version': '16.10.1',
        'md5': '621b97ea25e880829e45d83fd67a6451',
        'recovery': ('cat3k_caa-recovery.16.10.01.SPA.bin', 'cat3k_caa-recovery.bin'),
        'SR_pkgs': []
    },
    'S9300UK9-1610': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300UK9-1610',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.10.1/.3DES',
        'image_name': 'cat9k_iosxe.16.10.01.SPA.bin',
        'version': '16.10.1',
        'md5': '9d3db9aa393108904fa93c4e79206d3e',
        'recovery': ('cat9k-recovery.16.10.01.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
    'S9300ULPEK9-1610': {
        'name': 'POLARIS',
        'platforms': 'C9300',
        'product_id': 'S9300ULPEK9-1610',
        'cco_location': '/auto/beyond.iosxe-4/16/bin/16.10.1/.3DES',
        'image_name': 'cat9k_iosxeldpe.16.10.01.SPA.bin',
        'version': '16.10.1',
        'md5': 'f161ae2ca4fe335d8cd14963bea6674a',
        'recovery': ('cat9k-recovery.16.10.01.SPA.bin', 'cat9k-recovery.SSA.bin'),
        'SR_pkgs': []
    },
}
