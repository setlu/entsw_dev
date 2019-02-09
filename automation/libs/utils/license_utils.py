""" License Utility Module
========================================================================================================================

This module contains various utilities and support functions to process license PIDs.

IMPORTANT: All functions must NOT interact with UUT through connection, strictly data process and manipulation.


License Rules:

    There are 2 types of lisenses, one is RTU (Right-To-Use), one is DNA ( Digital Network Architecture).

    RTU is legacy type, DNA is subscription base license.

    All license information is contained in line id, search priority is
        DNA PID
     -->(if not found) RTU PID
     -->(if not found) top level PID suffix

C1 bundle license rules:

Cisco ONE is a bundle of SW features, sold at a discount.  However, SWSS  (SW Service and Support) is required.
That's the business model for C1 is to increase recurring revenue - via service contracts.

Originally, we created unique Cisco ONE PIDs for HW  (e.g. C1-WS3850-48P/K9).
We did this because SW Service & Support (aka SWSS) pricing was different b/n ALC and C1 versions.
Recently, Services adjusted their pricing strategy on some PFs - this allowed us to configure CiscoONE SW Bundles under ALC HW  (e.g.,  WS-C3850-24XU-S) in CCW.


Cisco ONE Foundation is the basic package. For Cat3k, it includes the following:  (example only, there are 5 different versions of C1-Foundation for C3850)
C1FPCAT38502K9      Cisco ONE Foundation Perpetual - Catalyst 3850 48-port  SEULA printed out at jigsaw station
C3850-48-L-S        C3850-48 LAN Base to IP Base Paper RTU License  Downloaded in the factory
C1-PI-LFAS-2K3K-K9  Cisco ONE PI Device License for LF & AS for Cat 2k, 3k  Claim Certificate printed at jigsaw
C1-ISE-BASE-48P     Cisco ONE Identity Services Engine 50 EndPoint Base Lic Claim Certificate printed at jigsaw
C1F1VCAT38502-03    Tracker PID v03 Fnd Perpetual CAT38502 - no delivery    Version tracking pid only, nothing delivered

Cisco ONE Advanced is the next level up.
C1APCAT38502K9      Cisco ONE Advanced Perpetual - Catalyst 3850 48-port    SEULA printed out at jigsaw station
C3850-48-S-E        C3850-48 IP Base to IP Services Paper RTU License   Downloaded in the factory

As you can see, C1-Foundation includes the upgrade from LAN BASE to IP BASE
C1-Advanced contains *only* the upgrade from IP BASE to IP SERVICES.  (if customers want to buy C1-Advanced, they must also purchase C1-Foundation)


To answer your questions below:
1)   If a customer buys C1 HW SKU, then they must buy C1-Foundation (at a minimum).
              a)  If a customer buys ALC HW SKU, then they may or may not purchase C1  (their option).

2)  For Cat3k, yes  C1-Foundation and Advanced will always contain the upgrade  (see exceptions below).

3)  For Cat3k, there are a couple of scenarios:
              Scenario 1. Customer buys C1-Foundation ONLY, C1-Foundation ( C1FPCAT38502K9) will always contain C3XXX-PP-L-S  (C3850-48-L-S) and
                          IP Base will be downloaded in the factory.
              Scenario 2. Customer buys C1-FND  *and* C1-Advanced, C1-Foundation will *not* contain C3XXX-PP-L-S. Instead,  C1-Advanced ( C1APCAT38502K9)
                          will contain C3XXX-PP-S-E (C3850-48-S-E) and the factory will download IP Services.

********************
Example LINE IDs
********************

1. C1 SW PID (Fou) with no upgrade PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1033307580           C1-WS3850-12XS-S           1               1033307580
1033315611             C1FPCAT38503K9           1               1033307580
1033315644            C1-ISE-BASE-12P           1               1033315611
1033315645         C1-PI-LFAS-2K3K-K9           1               1033315611
1033315646           C1F1VCAT38503-04           1               1033315611
1033315637              CAB-SPWR-30CM           1               1033307580
1033315638              PWR-C1-350WAC           1               1033307580
1033315639            PWR-C1-350WAC/2           1               1033307580
1033315640              STACK-T1-50CM           1               1033307580
1033315641               S3850UK9-166           1               1033307580
1033315642                  CAB-TA-EU           2               1033307580
1033315643             C3850-NM-BLANK           1               1033307580

2. C1 SW PID (both Adv and Fou) with upgrade PID C3850-12-S-E
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1034837851           C1-WS3850-12XS-S           1               1034837851
1034837854               S3850UK9-163           1               1034837851
1034837856              PWR-C1-350WAC           1               1034837851
1034837858            PWR-C1-350WAC/2           1               1034837851
1034837860             C3850-NM-4-10G           1               1034837851
1034837862                STACK-T1-3M           1               1034837851
1034837864            C3850-SPWR-NONE           1               1034837851
1034837866                  CAB-TA-UK           2               1034837851
1034837868             C1FPCAT38503K9           1               1034837851
1034837871         C1-PI-LFAS-2K3K-K9           1               1034837868
1034837872            C1-ISE-BASE-12P           1               1034837868
1034837873           C1F1VCAT38503-04           1               1034837868
1034837874             C1APCAT38503K9           1               1034837851
1034837877               C3850-12-S-E           1               1034837874

3. C1 SW PID (Fou) with DNA license, w/o NW license
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1034950619           C1-WS3850-12XS-S           1               1034950619
1034950687             C1FPCAT38503K9           1               1034950619
1034950740            C1-ISE-BASE-12P           1               1034950687
1034950741         C1-PI-LFAS-2K3K-K9           1               1034950687
1034950742           C1F1VCAT38503-04           1               1034950687
1034950694             C1A1ATCAT38503           1               1034950619
1034950743                C1-SWATCH-T           25              1034950694
1034950744               C1-ISE-PLS-T           25              1034950694
1034950745              C1-ISE-BASE-T           25              1034950694
1034950746         C1-C3850-12-DNAA-T           1               1034950694
1034950733              CAB-SPWR-30CM           1               1034950619
1034950734              PWR-C1-350WAC           1               1034950619
1034950735           PWR-C1-1100WAC/2           1               1034950619
1034950736             C3850-NM-4-10G           1               1034950619
1034950737              STACK-T1-50CM           1               1034950619
1034950738               S3850UK9-163           1               1034950619
1034950739                  CAB-TA-NA           2               1034950619

4. C1 SW PID (both Adv and Fou) with upgrade PID C3850-12-S-E and DNA License C1-C3850-12-DNAA-T ??????????????
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1036260813           C1-WS3850-12XS-S           1               1036260813
1036260825             C1APCAT38503K9           1               1036260813
1036260839               C3850-12-S-E           1               1036260825
1036260827             C1FPCAT38503K9           1               1036260813
1036260840            C1-ISE-BASE-12P           1               1036260827
1036260841         C1-PI-LFAS-2K3K-K9           1               1036260827
1036260842           C1F1VCAT38503-04           1               1036260827
1036260830             C1A1ATCAT38503           1               1036260813
1036260843                C1-SWATCH-T           25              1036260830
1036260844               C1-ISE-PLS-T           25              1036260830
1036260845              C1-ISE-BASE-T           25              1036260830
1036260846         C1-C3850-12-DNAA-T           1               1036260830
1036260832              CAB-SPWR-30CM           1               1036260813
1036260833              PWR-C1-350WAC           1               1036260813
1036260834           PWR-C1-1100WAC/2           1               1036260813
1036260835              STACK-T1-50CM           1               1036260813
1036260836               S3850UK9-163           1               1036260813
1036260837                  CAB-TA-NA           2               1036260813
1036260838             C3850-NM-BLANK           1               1036260813

5. No License PID in LINE ID, inferred in top level PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1032069684             WS-C3850-12S-E           1               1032069684
1032069784              CAB-SPWR-30CM           1               1032069684
1032069786              PWR-C1-350WAC           1               1032069684
1032069787            PWR-C1-350WAC/2           1               1032069684
1032069789              STACK-T1-50CM           1               1032069684
1032069791               S3850UK9-163           1               1032069684
1032069792                  CAB-TA-EU           2               1032069684
1032069794             C3850-NM-BLANK           1               1032069684

6. No License PID in LINE ID, inferred in top level PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1031000288          WS-C3850-12X48U-S           1               1031000288
1031000322              CAB-SPWR-30CM           1               1031000288
1031000323             PWR-C1-1100WAC           1               1031000288
1031000324           PWR-C1-1100WAC/2           1               1031000288
1031000325              STACK-T1-50CM           1               1031000288
1031000326               S3850UK9-163           1               1031000288
1031000327                  CAB-TA-EU           2               1031000288
1031000328             C3850-NM-BLANK           1               1031000288

7. C1 SW PID (Fou) and upgrade PID, no inference in top level PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1031443775           C1-WS3850-48U/K9           1               1031443775
1031443824             C1FPCAT38502K9           1               1031443775
1031443900               C3850-48-L-S           1               1031443824
1031443901            C1-ISE-BASE-48P           1               1031443824
1031443902         C1-PI-LFAS-2K3K-K9           1               1031443824
1031443903           C1F1VCAT38502-03           1               1031443824
1031443893            C3850-SPWR-NONE           1               1031443775
1031443894             PWR-C1-1100WAC           1               1031443775
1031443895           PWR-C1-1100WAC/2           1               1031443775
1031443896           C3850-STACK-NONE           1               1031443775
1031443897               S3850UK9-36E           1               1031443775
1031443898                CAB-C15-CBN           2               1031443775
1031443899             C3850-NM-BLANK           1               1031443775

8 DNA License with NW License
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1032351680                C9300-24P-E           1               1032351680
1032351970              PWR-C1-715WAC           1               1032351680
1032351971             C9300-SPS-NONE           1               1032351680
1032351972              C9300-NW-E-24           1               1032351680
1032351973             C9300-DNA-E-24           1               1032351680
1032351974               S9300UK9-168           1               1032351680
1032351975                  CAB-TA-IT           1               1032351680
1032351976              STACK-T1-50CM           1               1032351680
1032351977              CAB-SPWR-30CM           1               1032351680
1032351978               PWR-C1-BLANK           1               1032351680
1032351979                C9300-NM-8X           1               1032351680

9. NW License w/o DNA License
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1032286513                C9300-24P-E           1               1032286513
1032286558              PWR-C1-715WAC           1               1032286513
1032286559              C9300-NW-E-24           1               1032286513
1032286560             DISTI-STOCKING           1               1032286513
1032286561               S9300UK9-168           1               1032286513
1032286562                  CAB-TA-EU           1               1032286513
1032286563               PWR-C1-BLANK           1               1032286513
1032286564                NM-BLANK-T1           1               1032286513

10. DNA with NW License, C1 SW PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1028462528                C9300-48P-A           1               1028462528
1028462578              C1A1TCAT93002           1               1028462528
1028462673         C1-C9300-48-DNAA-T           1               1028462578
1028462674                C1-SWATCH-T           25              1028462578
1028462675               C1-ISE-PLS-T           25              1028462578
1028462676              C1-ISE-BASE-T           25              1028462578
1028462665              PWR-C1-715WAC           1               1028462528
1028462666            PWR-C1-715WAC/2           1               1028462528
1028462667              C9300-NW-A-48           1               1028462528
1028462668               S9300UK9-168           1               1028462528
1028462669                  CAB-TA-EU           2               1028462528
1028462670              STACK-T1-50CM           1               1028462528
1028462671              CAB-SPWR-30CM           1               1028462528
1028462672                C9300-NM-8X           1               1028462528
1028462677              C1-ADD-OPTOUT           1               1028462528

11. DNA with NW License, EDU PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1024522527              C9500-24Q-EDU           1               1024522527
1024522547               S9500UK9-166           1               1024522527
1024522548                 C9500-NW-A           1               1024522527
1024522549                  CAB-TA-NA           2               1024522527
1024522550          PWR-C4-950WAC-R/2           1               1024522527
1024522551            PWR-C4-950WAC-R           1               1024522527
1024522552            C9500-DNA-24Q-A           1               1024522527

12. NW License w/o DNA, EDU PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1024346473              C9500-24Q-EDU           1               1024346473
1024346487               S9500UK9-166           1               1024346473
1024346488             C9500-NW-A-EDU           1               1024346473
1024346489                  CAB-TA-NA           2               1024346473
1024346490          PWR-C4-950WAC-R/2           1               1024346473
1024346491            PWR-C4-950WAC-R           1               1024346473

13. DNA w/o NW, -P PID,  what level is C9500-DNA-P?????? not specified in Agile
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1028103563                C9500-40X-P           1               1028103563
1028103645               S9500UK9-166           1               1028103563
1028103646                  CAB-TA-NA           2               1028103563
1028103647          PWR-C4-950WAC-R/2           1               1028103563
1028103648            PWR-C4-950WAC-R           1               1028103563
1028103649                C9500-DNA-P           1               1028103563
1028103650             C9500-NM-BLANK           1               1028103563
1028103651                 SFP-10G-SR           16              1028103563
1028103652                 SFP-10G-LR           8               1028103563

14. DNA with NW License, FTTD PID
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
1028117881           C9500-40X-A-FTTD           1               1028117881
1028117890               S9500UK9-168           1               1028117881
1028117891                 C9500-NW-A           1               1028117881
1028117892               PWR-C4-BLANK           1               1028117881
1028117893                  CAB-TA-NA           1               1028117881
1028117894             C9500-SPS-NONE           1               1028117881
1028117895            PWR-C4-950WAC-R           1               1028117881
1028117896         C9500-DNA-40X-ABDL           1               1028117881
1028117897                C9500-NM-2Q           1               1028117881

15. RTU with AP count
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
956627960             WS-C3850-24UW-S           1               956627960
956627985                LIC-CTIOS-1A           5               956627960
956627986               CAB-SPWR-30CM           1               956627960
956627987              PWR-C1-1100WAC           1               956627960
956627988            PWR-C1-1100WAC/2           1               956627960
956627989              C3850-NM-2-10G           1               956627960
956627990               STACK-T1-50CM           1               956627960
956627991                S3850UK9-36E           1               956627960
956627992                   CAB-TA-NA           2               956627960

16. Katana PID with 100 AP count
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
978489531           AIR-CT5760-100-K9           1               978489531
978489547                   CAB-TA-NA           2               978489531
978489548               PWR-C1-350WAC           1               978489531
978489549             PWR-C1-350WAC/2           1               978489531
978489550               SW5760K9-32SE           1               978489531
978489551               AIR-CT5760-K9           1               978489531
978489552             LIC-CT5760-BASE           1               978489531
978489553              LIC-CT5760-100           1               978489531
978489554           AIR-CT5760-RK-MNT           1               978489531

17. Katana w/o AP count
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
956679444            AIR-CT5760-CA-K9           1               956679444
956679450                   CAB-TA-NA           1               956679444
956679451               PWR-C1-350WAC           1               956679444
956679452               SW5760K9-32SE           1               956679444
956679453               AIR-CT5760-K9           1               956679444
956679454             LIC-CT5760-BASE           1               956679444
956679455             CT5760-BLNK-PLT           1               956679444
956679456           AIR-CT5760-RK-MNT           1               956679444

18. Katana w/o AP count
LineID                  Prodname                Prod_qty        Parentlineid
------                  --------                --------        ------------
974667597            AIR-CT5760-HA-K9           1               974667597
974669835                   CAB-TA-NA           1               974667597
974669836               PWR-C1-350WAC           1               974667597
974669838               SW5760K9-32SE           1               974667597
974669839               AIR-CT5760-K9           1               974667597
974669841             LIC-CT5760-BASE           1               974667597
974669842             CT5760-BLNK-PLT           1               974667597
974669844               STACK-T1-50CM           1               974667597
974669846           AIR-CT5760-RK-MNT           1               974667597

========================================================================================================================
"""
# Python
# ------
import sys
import logging
import re

# BU Lib
# ------
from ..utils import common_utils

__title__ = "License Utility Module"
__version__ = '0.5.2'
__author__ = 'qingywu'

log = logging.getLogger(__name__)
func_details = common_utils.func_details
func_retry = common_utils.func_retry
thismodule = sys.modules[__name__]

# ======================================================================================================================
# Internal variables
#
#   These vars are not to access directly outside of this module, use provided functions to get return
#
#   TODO: These variables need to be updated by TE when new license PID releases
# ======================================================================================================================

# dna_feature_map: look for DNA license feature (advantage/essentials) by license PID
_dna_feature_map = {
    re.compile(r'DNAA'): 'advantage',
    re.compile(r'DNAE'): 'essentials',
    re.compile(r'DNA-A-'): 'advantage',
    re.compile(r'DNA-E-'): 'essentials',
    re.compile(r'DNA-1A-'): 'advantage',
    re.compile(r'DNA-1E-'): 'essentials',
    re.compile(r'DNA-10A-'): 'advantage',
    re.compile(r'DNA-10E-'): 'essentials',
    re.compile(r'-DNA-P$'): 'advantage',
    re.compile(r'C9500-NW(\S*?)-(1|10)?A(-|$)'): 'advantage',
    re.compile(r'C9300-NW(\S*?)-(1|10)?A(-|$)'): 'advantage',
    re.compile(r'C9500-NW(\S*?)-(1|10)?E(-|$)'): 'essentials',
    re.compile(r'C9300-NW(\S*?)-(1|10)?E(-|$)'): 'essentials',
    re.compile(r'E$'): 'essentials',
    re.compile(r'A$'): 'advantage',
}

# rtu_feature_map: look for RTU license feature (lanbase/ipbase/ipservices) by license PID (pseudo-PID)
_rtu_feature_map = {
    'LIC-LAN-BASE-L': 'lanbase',
    'LIC-IP-BASE-S': 'ipbase',
    'LIC-IP-SRVCS-E': 'ipservices',
}

_rtu_pid_patterns = {
    # C1 upgrade PIDs
    re.compile(r'^\S*?C3650-(12|24|48)-L-S$'): 'LIC-IP-BASE-S',
    re.compile(r'^\S*?C3650-(12|24|48)-S-E$'): 'LIC-IP-SRVCS-E',
    re.compile(r'^\S*?C3850-(12|24|48)-L-S$'): 'LIC-IP-BASE-S',
    re.compile(r'^\S*?C3850-(12|24|48)-S-E$'): 'LIC-IP-SRVCS-E',

    # C1 bundle SW
    re.compile(r'^C1FPCAT2900\dK9$'): 'LIC-IP-BASE-S',
    re.compile(r'^C1FPCAT3650\dK9$'): 'LIC-IP-BASE-S',
    re.compile(r'^C1FPCAT3850\dK9$'): 'LIC-IP-BASE-S',
    re.compile(r'^C1APCAT3650\dK9$'): 'LIC-IP-SRVCS-E',
    re.compile(r'^C1APCAT3850\dK9$'): 'LIC-IP-SRVCS-E',

    # top level PIDs below
    re.compile(r'^WS-C3650-(12|24|48)\S*?-L$'): 'LIC-LAN-BASE-L',
    re.compile(r'^WS-C3650-(12|24|48)\S*?-S$'): 'LIC-IP-BASE-S',
    re.compile(r'^WS-C3650-(12|24|48)\S*?-E$'): 'LIC-IP-SRVCS-E',
    re.compile(r'^WS-C3850-(12|24|48)\S*?-L$'): 'LIC-LAN-BASE-L',
    re.compile(r'^WS-C3850-(12|24|48)\S*?-S$'): 'LIC-IP-BASE-S',
    re.compile(r'^WS-C3850-(12|24|48)\S*?-E$'): 'LIC-IP-SRVCS-E',

    # Katana PID
    re.compile(r'^AIR-CT5760'): 'LIC-IP-BASE-E',

    # Pseudo PID
    re.compile(r'^LIC-LAN-BASE-L$'): 'LIC-LAN-BASE-L',
    re.compile(r'^LIC-IP-BASE-S$'): 'LIC-IP-BASE-S',
    re.compile(r'^LIC-IP-SRVCS-E$'): 'LIC-IP-SRVCS-E',
}

# dnc_lic_pattern: DNA license PID pattern
_dna_pid_pattern = re.compile(r'-DNA-|-DNA[AE]|-DNA$|C9500DNA|C9500-NW-|C9300-NW-')

# apcount_pid_pattern: AP count PID pattern
_apcount_pid_pattern = {
    re.compile(r'^LIC-CTIOS-1A$'): 1,
    re.compile(r'^LIC-CT5760-25$'): 25,
    re.compile(r'^LIC-CT5760-50$'): 50,
    re.compile(r'^LIC-CT5760-100$'): 100,
    re.compile(r'^LIC-CT5760-250$'): 250,
    re.compile(r'^LIC-CT5760-500$'): 500,
    re.compile(r'^LIC-CT5760-1K$'): 1000,
}

_dna_license_detail = {
    'advantage': [{'name': 'network-advantage', 'type': 'Permanent'}, {'name': 'dna-advantage', 'type': 'Subscription'}],
    'essentials': [{'name': 'network-essentials', 'type': 'Permanent'}, {'name': 'dna-essentials', 'type': 'Subscription'}],
}

_rtu_license_detail = {
    'lanbase': [{'name': 'lanbase', 'type': '[Pp]ermanent'}],
    'ipbase': [{'name': 'ipbase', 'type': '[Pp]ermanent'}],
    'ipservices': [{'name': 'ipservices', 'type': '[Pp]ermanent'}],
}


# ======================================================================================================================
# External variables
#
#   These vars can be used directly from outside of this module
#
# ======================================================================================================================
# AP count PID (SKU)
apcount_sku = 'LIC-CTIOS-1A'


# *******************************************
# License related utility functions
# *******************************************
def is_dna_license(license_pid=None):
    """ IS input PID a DNA license PID

    NOTE: If OPTOUT is in PID, return False, it is not a DNA License PID even DNA is in it.

    :param (str) license_pid: SW License PID
    :return (bool): True if license_pid is a DNA license PID,  False otherwise
    """
    if not isinstance(license_pid, (str, unicode)):
        raise Exception('Invalid Input type {0}({1}), must be str or unicode'.format(license_pid, type(license_pid)))

    license_pid = license_pid.strip('=').strip('+')
    ret = True if _dna_pid_pattern.search(license_pid) else False
    if 'OPTOUT' in license_pid:
        ret = False

    return ret


def is_rtu_license(license_pid=None):
    """ IS input PID a RTU (right-to-use) license PID

    :param (str) license_pid: SW License PID
    :return (bool): False if license_pid is not a RTU license PID,  pseudo-RTU license PID if input is a RTU PID
    """
    if not isinstance(license_pid, (str, unicode)):
        raise Exception('Invalid Input type {0}({1}), must be str or unicode'.format(license_pid, type(license_pid)))

    ret = False
    for pattern, lic_pid in _rtu_pid_patterns.iteritems():
        if pattern.search(license_pid):
            ret = lic_pid
            break

    return ret


def is_apcount_license(license_pid=None):
    """ IS input PID a AP COUNT license PID

    :param (str) license_pid: SW License PID
    :return (int): apcount quantity if license_pid is a APCOUNT license PID, False otherwise
    """
    if not isinstance(license_pid, (str, unicode)):
        raise Exception('Invalid Input type {0}({1}), must be str or unicode'.format(license_pid, type(license_pid)))

    license_pid = license_pid.strip('=').strip('+')
    ret = False
    for pattern, apcount_qty in _apcount_pid_pattern.iteritems():
        if pattern.search(license_pid):
            ret = apcount_qty
            break

    return ret


@func_details
def get_license_feature(license_pid=None, license_type=None):
    """ Get License Feature

    Get license feature from license PID. It is (essentials/advantage) for DNA lincese,
    (lanbase/ipbase/ipservices) for RTU license.

    :param (str) license_pid: SW License PID
    :param (str) license_type: Either DNA or RTU
    :return (str): License feature, if not found return None
    """
    if license_type is not 'RTU' and license_type is not 'DNA':
        log.warning('Param license_type must be either "DNA" or "RTU", input is {0}'.format(license_type))
        return None
    if not isinstance(license_pid, (str, unicode)):
        log.warning('Invalid Input type {0}({1}), must be str or unicode'.format(license_pid, type(license_pid)))
        return None
    if license_type == 'DNA' and not _dna_pid_pattern.search(license_pid):
        log.warning('Invalid DNA license PID {0} input'.format(license_pid))
        return None
    if license_type == 'RTU' and _dna_pid_pattern.search(license_pid):
        log.warning('Invalid RTU license PID {0} input'.format(license_pid))
        return None

    lic_feature_map = _rtu_feature_map if license_type is 'RTU' else _dna_feature_map
    ret = None

    for pattern, feature in lic_feature_map.iteritems():
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if pattern.search(license_pid):
            ret = feature
            break

    return ret


@func_details
def normalize_sw_licenses(sw_licenses):
    """ Normalize SW Licenses list

    For input sw_licenses list, there should be only ONE item (except APCOUNT item). In _get_sw_licenses function, multiple
    license PID will get populated in sw_licenses. For DNA license, we need to remove redunant item and check any conflict;
    for RTU license, we need to identify the highest level of license and only keep that one.

    :param (list) sw_licenses: SW License list of dicts from _get_sw_licenses
                            ex: [{'sku': u'C9300-NW-A-48', 'quantity': 1}, {'sku': u'C1-C9300-48-DNAA-T', 'quantity': 1}]
                            ex: [{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}, {'sku': 'LIC-IP-BASE-S', 'quantity': 1}]

    :return (list): norm_sw_licenses, normalized list
                            ex: [{'sku': u'C9300-NW-A-48', 'quantity': 1}]
                            ex: [{'sku': 'LIC-IP-SRVCS-E', 'quantity': 1}]
    """
    # RTU level: lanbase < ipbase < ipservices
    _rtu_lic_level = {
        'lanbase': 1,
        'ipbase': 2,
        'ipservices': 3,
    }
    # DNA level (not used, reserved for future) essentials < advantage
    _dna_lic_level = {
        'essentials': 1,
        'advantage': 2,
    }

    if not isinstance(sw_licenses, list):
        raise Exception('Input sw_licenses must be a list')

    norm_sw_licenses = [item for item in sw_licenses if item.get('sku') == 'LIC-CTIOS-1A']
    sw_licenses = [item for item in sw_licenses if item.get('sku') != 'LIC-CTIOS-1A']
    lic_features = []
    current_feature = None

    if not sw_licenses:
        return norm_sw_licenses

    license_type = 'DNA' if is_dna_license(sw_licenses[0]['sku']) else 'RTU'

    if license_type == 'DNA':
        log.debug("DNA License levels: {0}".format(_dna_lic_level))
        for lic in sw_licenses:
            lic_feature = get_license_feature(lic['sku'], license_type=license_type)
            if not lic_feature:
                log.error('No license feature is found, wrong PID {0}'.format(lic['sku']))
                return None
            elif not current_feature:
                norm_sw_licenses.append(lic)
                current_feature = lic_feature
            elif current_feature != lic_feature:
                log.error('Conflict license feature is found in sw_licenses, {0} and {1}'.format(current_feature, lic_feature))
                return None
    if license_type == 'RTU':
        log.debug("RTU License levels: {0}".format(_rtu_lic_level))
        for lic in sw_licenses:
            lic_feature = get_license_feature(lic['sku'], license_type=license_type)
            if not lic_feature:
                log.error('No license feature is found, wrong PID {0}'.format(lic['sku']))
                return None
            else:
                lic_features.append(lic_feature)
        lic_levels = [_rtu_lic_level.get(item) for item in lic_features]
        norm_sw_licenses.append(sw_licenses[lic_levels.index(max(lic_levels))])

    log.info('Normalized sw_licenses: {0}'.format(norm_sw_licenses))

    return norm_sw_licenses


@func_details
def get_license_detail(lic_feature, license_type=None, all_levels=False):
    """ Get License Detail

    Get IOS license detail for lic_feature, including license name/type.
    all_levels is a switch, it overrides lic_feature and return a list of license detail for all aavailable features
    within specifid license_type.

    :param (str) lic_feature: License feature on IOS (lanbase/ipbase/ipservices, essentials/advantage)
    :param (str) license_type: RTU or DNA
    :param (bool) all_levels: If True return detail of all levels, default is False

    :return (list): ret
            (all_level: False) ex:  [{'name': 'lanbase', 'type': 'Permanent'}]
                                    [{'name': 'network-advantage', 'type': 'Permanent'}, {'name': 'dna-advantage', 'type': 'Subscription'}]
            (all_level: True) ex:   [{'name': 'lanbase', 'type': 'Permanent'}, {'name': 'ipbase', 'type': 'Permanent'}, {'name': 'ipservices', 'type': 'Permanent'}]
    """
    if license_type is not 'RTU' and license_type is not 'DNA':
        raise Exception('Param license_type must be either "DNA" or "RTU", input is {0}'.format(license_type))

    license_detail = dict(_dna_license_detail) if license_type is 'DNA' else dict(_rtu_license_detail)

    ret = []

    if all_levels:
        for key, value in license_detail.iteritems():
            ret += value
    else:
        ret = license_detail.get(lic_feature)
        if not ret:
            raise Exception('Unrecognized license feature {0}'.format(lic_feature))

    return ret
