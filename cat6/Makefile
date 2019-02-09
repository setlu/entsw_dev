#---------------------------------
# Standard commands
#---------------------------------

define install_package
	rm -fv dist/*.tar.gz
	/usr/local/bin/python setup.py sdist --pkg_version $(TIMESTAMP)
	export base_dir=${USER};/usr/local/bin/pip install --user --install-option="--pkg_version=$(TIMESTAMP)" dist/*.tar.gz
endef

TIMESTAMP=$(shell date +%s)

pkg:
	$(call install_package)

clean:
	rm -rfv build/
	rm -rfv dist/
	rm -rfv *.egg-info

#---------------------------------
# Custom commands
#---------------------------------
