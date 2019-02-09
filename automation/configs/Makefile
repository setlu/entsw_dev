# ====================================================================================
# Makefile
#
# Specific for ENTSW Configs
#
# bborel 2018.11.27
# ====================================================================================
#
#---------------------------------
# Standard commands
#---------------------------------
define clean_workspace
        rm -rfv build/
        rm -rfv dist/
        rm -rfv *.egg-info
endef

define install_package
    rm -fv dist/*.tar.
    @echo "__version__ = '$(TIMESTAMP)'" > version.py
    /usr/local/bin/python setup.py sdi
    @rm version.py
    export base_dir=users/${USER};/usr/local/bin/pip install --user dist/*.tar.gz
    $(clean_workspace)
    $(link_apollo)
endef

define install_package_release
    @git -c http.sslVerify=false pull 2>/dev/null
    @git branch -a | sed s/'remotes\/origin\/'//
    @read -p "Enter the branch to be built: " choice; git checkout $${choice}
    @read -p "Confirm to proceed with build (y/[n]): " proceed; if test $${proceed} != "y" ;then exit 1;fi
    rm -fv dist/*.tar.gz
    @echo "__version__ = '$(TIMESTAMP)'" > version.py
    /usr/local/bin/python setup.py sdist
    @rm version.py
    export base_dir=projects;/usr/local/bin/pip install --user dist/*.tar.gz
    $(clean_workspace)
    $(link_apollo_release)
endef

TIMESTAMP=$(shell date +%Y%m%d.%H%M%S)

private:
	$(call install_package)

release:
	$(call install_package_release)

clean:
	$(call clean_workspace)

link:
	$(call link_apollo_source)

#---------------------------------
# Custom commands/functions
#---------------------------------
REPO=configs
APOLLO_CONFIG=/opt/cisco/constellation/apollo/config
site=$(shell cat ${APOLLO_CONFIG}/apollo_registry.json | python -c "import sys, json; print json.load(sys.stdin)['Machine']['siteCode']")
export SITE=${site}
ENTSW_STATION_CONFIG=${APOLLO_CONFIG}/${HOSTNAME}_entsw_config.py
APOLLO_SCRIPTS=/opt/cisco/constellation/apollo/scripts
ENTSW_SCRIPTS=${APOLLO_SCRIPTS}/entsw
CFG_SPACE=${ENTSW_SCRIPTS}/${REPO}

define link_apollo
    rm -f ${ENTSW_STATION_CONFIG}
    ln -s /opt/cisco/te/scripts/users/${USER}/entsw/${REPO}/${SITE}/${HOSTNAME}_entsw_config.py ${ENTSW_STATION_CONFIG}
    rm -rf ${CFG_SPACE}
    ln -s /opt/cisco/te/scripts/users/${USER}/entsw/${REPO} ${CFG_SPACE}
endef

define link_apollo_release
    rm -f ${ENTSW_STATION_CONFIG}
    ln -s /opt/cisco/te/scripts/projects/entsw/${REPO}/${SITE}/${HOSTNAME}_entsw_config.py ${ENTSW_STATION_CONFIG}
    rm -rf ${CFG_SPACE}
    ln -s /opt/cisco/te/scripts/projects/entsw/${REPO} ${CFG_SPACE}
endef

define link_apollo_source
    rm -f ${ENTSW_STATION_CONFIG}
    ln -s ${PWD}/${SITE}/${HOSTNAME}_entsw_config.py ${ENTSW_STATION_CONFIG}
    rm -rf ${CFG_SPACE}
    ln -s ${PWD} ${CFG_SPACE}
endef