# Enterprise Switching - CATALYST Series 4

## 1. Project overview

This `cat4` repo is designed for PCBA and DF site mfg testing of ALL Catalyst Series 4 products.

## 2. Code structure

#### Shared Code location (Local Apollo)
<font color=blue>/opt/cisco/te/scripts/projects/entsw2/cat4</font>

Note: The standard location for GIT local archives has been set to "/home/{userid}/..." which allows for feature branches to later be merged to development & master branch on an individual basis.
For "shared" installations running local GIT archive code, this will reside in the "/opt/cisco/te/scripts/projects/..." area.

#### BitBucket

##### Repository
<font color=blue>https://apollohub.cisco.com/bitbucket/scm/entsw/cat4.git</font>

##### URL
<font color=blue>https://apollohub.cisco.com/bitbucket/projects/ENTSW/repos/cat4/browse</font>


### 3. File Structure

#### 3.1 C4xx/C94xx - Catalyst Series 4 "Product Family" Folders

These are the product folders which contain:

    1. Area Sequences (both PRE-SEQ and SEQ),
    2. Product Definitions,
    3. Product family class module (c4xxx/c94xx),
    4. Product steps

#### 3.2 Files

<pre>
cat4
├── C4500
│   ├── area_sequences
│   │   └── __init__.py
│   ├── product_definitions
│   │   ├── __init__.py
│   │   └── _product_line_def.py
│   ├── __init__.py
│   └── c4500.py
├── C9400
│   ├── area_sequences
│   │   ├── __init__.py
│   │   ├── chassis_pcbft.py
│   │   ├── fantray_pcbft.py
│   │   ├── linecard_dbgsys.py
│   │   ├── linecard_pcb2c.py
│   │   ├── linecard_pcbp2.py
│   │   ├── linecard_pcbpm.py
│   │   ├── linecard_pcbst.py
│   │   ├── sup_dbgsys.py
│   │   ├── sup_pcb2c.py
│   │   ├── sup_pcbp2.py
│   │   └── sup_pcbst.py
│   ├── product_definitions
│   │   ├── __init__.py
│   │   ├── _product_line_def.py
│   │   ├── macallan_linecard_def.py
│   │   └── macallan_sup_def.py
│   ├── __init__.py
│   ├── c9400.py
│   ├── steps_macallan_linecard.py
│   └── steps_macallan_sup.py
├── common
│   ├── __init__.py
│   ├── _common_def.py
│   ├── _ios_manifest4.py
│   ├── catalyst4.py
│   ├── modes4.py
│   ├── stardust4.py
│   └── traffic4.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cat4_class_inst.py
│   └── test_cat4_production.py
├── LICENSE.txt
├── Makefile
├── __init__.py
├── setup.cfg
└── setup.py

</pre>

#### 3.3 common

Files common to all Catalyst Series 4 products.
 - `_common_def.py`: Common Product Definition (all Series 4)
 - `catalyst4.py`  : Series 4 Class module
 - `modes.py`      : Series 4 Transistion Functions for all modes; used by Mode Manager
 - `stardust4.py`  : Series 4 Stardust Class module for diag functions

#### 3.4 tests

Strictly for ALL unittests related to Series 4.

### 4 Code Architecture

#### 4.1 Catalyst Series 4 Class modules


![Diagram1](./docs/catalyst4_tree.JPG)


#### 4.2 Product Line Class anatomy (member classes)


![Diagram2](./docs/product_class.JPG)


### Appendix 

#### A.1 Script Links

##### A.1.1 BU Location
<pre>
/opt/cisco/constellation/apollo/scripts/entsw
</pre>

##### A.1.2 BU Links
Note: These links are manually created.
<pre>
lrwxrwxrwx   1 apollo apollo   42 Nov  2 15:42 cat4 -> /opt/cisco/te/scripts/projects/entsw2/cat4
lrwxrwxrwx   1 apollo apollo   42 Nov  2 15:48 libs -> /opt/cisco/te/scripts/projects/entsw2/libs
</pre>

##### A.1.3 Cisco Lib Location
<pre>
/opt/cisco/constellation/apollo/scripts/cisco/libs
</pre>

##### A.1.4 Cisco Links
Note: These links are still using SVN archive.
<pre>
lrwxrwxrwx  1 apollo apollo   32 Feb 23  2018 chamber -> /opt/cisco/te/libs/chamber/trunk
</pre>

#### A.2 Config Links

##### A.2.1 Location
<pre>
/opt/cisco/constellation/apollo/config
</pre>

##### A.2.2 Links
<pre>
lrwxrwxrwx   1 apollo apollo     86 Sep  7 00:29 {hostname}_entsw_config.py -> /opt/cisco/te/scripts/projects/entsw2/configs/{location}/{hostname}_entsw_config.py

{location} = Apollo SiteCode
{hostname} = Apollo server hostname

The config file MUST import the common stations needed and then use as appropriate.
If a station is NOT supported by the common station library, please alert the Cisco ENTSW archive admins.
Ex import:
    <b>from apollo.scripts.entsw.configs.common.cat4 import stations as cat4_stations</b>
    
Ex usage for a station where test area is PCBP2:
    <b>station_details = dict(
        product_line='C9400',
        server_ip='172.28.106.76',
        ts_ip='10.1.1.2',
        ts_start_port=2033,
        psu_separate_control=False,
        chassis='SUPERVISOR_SEVEN_SLOT_A',
        chassis_count=2
    )
    cat4_stations.sup_pcbp2(config, **station_details)

    </b>
</pre>

#### A.3 Cloning for an ENTSW Product Space

This section discusses how to clone the required repos onto an Apollo server for a specific product space.
The cloned repositories are NOT meant for running shippable product.
The cloned repositories are meant for TE development of production scripts.
NOTE1: The default repo will be the "development" branch.
NOTE2: A UMT account userid & password is required.

##### A.3.1 Repositories
1. ENTSW Repos needed:
    1. Product Space (e.g. `cat4`)
    2. `configs`
    3. `libs`

2. Cisco TE Repo (within BitBucket *TestTransformation* project) (optional):
    1. `libs`

##### A.3.2 Instructions
1. Required:

    Create a *project directory*, set permissions, and cd to it (e.g. `/home/<userid>/entsw`).
    Then run the cloning.
    1. `mkdir entsw`
    2. `chmod 777 entsw`
    3. `cd entsw`
    4. `git clone https://apollohub.cisco.com/bitbucket/scm/entsw/cat4.git`
    5. `git clone https://apollohub.cisco.com/bitbucket/scm/entsw/configs.git`
    6. `git clone https://apollohub.cisco.com/bitbucket/scm/entsw/libs.git`
        
2. Optional:    
    
    Create a *cisco te library*, set permissions, and cd to it (e.g. `/home/<userid>/cisco`).
    Then run the cloning.
    1. `mkdir cisco`
    2. `chmod 777 cisco`
    3. `cd cisco`
    4. `git clone https://apollohub.cisco.com/bitbucket/scm/te/libs.git`

