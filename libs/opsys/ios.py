""" IOS General Module
========================================================================================================================

This module contains various utilities and support functions to operate specifically on the IOS
Supported product families:
    1. Cisco Catalyst 2000 series (WS-C2960, C9200)
    2. Cisco Catalyst 3000 series (WS-C3850, WS-C3650, C9300)
    3. Cisco Catalyst 4000 series (Macallen series, C9400)

IMPORTANT: All functions must NOT use any MachineManager object; instead use only the UUT connection object
           and the UUT prompt pattern.  All IOS utilities should be machine agnostic!

========================================================================================================================
"""

# Python
# ------
import sys
import time
import re
import logging
import os
import parse
from datetime import datetime

# Apollo
# ------
from apollo.libs import cesiumlib
from apollo.libs import lib as aplib
from apollo.engine import apexceptions

# BU Specific
# -----------
from ..utils import common_utils
from ..utils import license_utils


__title__ = "IOS General Module"
__version__ = '2.0.0'
__author__ = ['bborel', 'detravis', 'qingywu']

thismodule = sys.modules[__name__]
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)

func_details = common_utils.func_details
cesium_srvc_retry = common_utils.cesium_srvc_retry
apollo_step = common_utils.apollo_step


class IOS(object):
    RECBUF_TIME = 3.0
    RECBUF_CLEAR_TIME = 1.0
    USE_CLEAR_RECBUF = False

    def __init__(self, mode_mgr, ud):
        log.info(self.__repr__())
        self._mode_mgr = mode_mgr
        self._ud = ud
        self._uut_conn = self._mode_mgr.uut_conn
        self._uut_prompt_map = self._mode_mgr.uut_prompt_map
        self._uut_prompt = self._uut_prompt_map['IOSE']
        self._callback = None
        return

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # ==================================================================================================================
    # APOLLO STEP Methods
    # ==================================================================================================================
    @apollo_step
    def verify_idpro(self, **kwargs):
        """ Verify IdPro Test (STEP)
        :menu: (enable=True, name=IOS VERIFY IDPRO, section=IOS, num=1, args={'menu': True})
        :param (dict) kwargs: 'device_instance'
        :return (str): aplib.PASS/FAIL
        """
        aplib.set_container_text('IOS VERIFY IDPRO')
        log.debug("STEP: IOS Verify IdPro (Quack2/ACT2/X.509).")

        # Check mode
        if self._mode_mgr.current_mode != 'IOSE':
            log.error("Wrong mode; need to be in IOSE.")
            return aplib.FAIL

        # Input
        x509_hashes = kwargs.get('x509_sudi_hash', self._ud.uut_config.get('x509_sudi_hash', []))
        # TODO: provide hw_modules for L10 test
        hw_modules = kwargs.get('hw_modules', self._ud.uut_config.get('hw_modules'))

        # X.509 Certs
        # -----------
        # 1. Get Certs
        # 2. Check Certs
        if x509_hashes:
            log.debug("Checking X.509 AP SUDI Certs (aka PKI Certs).")
            expected_cert_count = len(x509_hashes) * 3
            certs = self._get_crypto_pki(expected_cert_count)

            pid = self._ud.puid.pid
            sn = self._ud.puid.sernum
            mac = self._ud.uut_config.get('MAC_ADDR', None)
            log.debug("Hashes = {0}".format(x509_hashes))
            log.debug("PID    = {0}".format(pid))
            log.debug("MAC    = {0}".format(mac))
            log.debug("SN     = {0}".format(sn))
            if not all([pid, mac, sn]):
                log.error("Missing parameter data for crypto pki check.")
                return aplib.FAIL

            x509_valid = self._check_crypto_pki(x509_hashes, certs, pid, mac, sn)

        else:
            log.warning("No X.509 SUDI hashes defined.  Confirm product definition.")
            log.warning("X.509 check will be skipped.")
            x509_valid = True

        # HW Authentication
        # -----------------
        hw_valid = self._validate_hw_authentication(hw_modules)

        if not x509_valid or not hw_valid:
            return aplib.FAIL, "IOS IdPro FAILED."

        log.info('IOS Identity Protection: PASSED.')
        return aplib.PASS

    # Images -----------------------------
    @apollo_step
    def download_images(self, **kwargs):
        """ IOS Download Images
        Ensure all images reside in or are downloaded to /tftpboot/ on the local Apollo server.

        :menu: (enable=True, name=IOS DWNLD IMAGES, section=IOS, num=1, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('IOS DOWNLOAD IMAGES')
        log.debug("STEP: IOS Download Images.")

        # Sanity check on IOS Manifest
        if not self._ud.ios_manifest:
            log.error("There is no IOS Manifest loaded.")
            log.error("Please check the common dir to ensure it has a _ios_manifestX.py.")
            return aplib.FAIL

        # Input
        menu = kwargs.get('menu', False)
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid', None))
        ios_test_pid = kwargs.get('ios_test_pid', self._ud.uut_config.get('ios_test_pid', None))
        ios_supp_files = kwargs.get('ios_supp_files', self._ud.uut_config.get('ios_supp_files', None))
        server_dir = kwargs.get('server_dir', self._ud.uut_config.get('ios_dirs', {}).get('remote', ''))

        if menu:
            ios_customer_pid = None
            ios_test_pid = aplib.ask_question("Select IOS SWPID:", answers=sorted(self._ud.ios_manifest.keys()))

        # Get Image Config
        ios_pid, ios_sw_config = self._get_image_config(ios_customer_pid=ios_customer_pid, ios_test_pid=ios_test_pid)
        if not ios_sw_config:
            log.error("Cannot get any IOS SW Config data from Cesium or Local Manifest.")
            return aplib.FAIL

        # Print and save to uut_config
        log.debug("SW Config {0} = {1}".format(ios_pid, ios_sw_config))
        self._ud.uut_config['ios_sw_config'] = ios_sw_config

        # ** PERFORM THE DOWNLOADS **
        result = self._download_images(ios_sw_config, ios_supp_files, local_dir=server_dir)
        if result:
            ret = aplib.PASS
            log.info("STEP: IOS Download Images = PASSED.")
        else:
            ret = aplib.FAIL, "Downloads failed (see log)."
            log.info("STEP: IOS Download Images = FAILED.")

        return ret

    @apollo_step
    def install_main_image(self, **kwargs):
        """ IOS Install Main Image

        This clears flash and installs the complete image from ground up.
        Typical mechanism is via the disaster recovery feature.
        Before executing this step, step__ios_download_images must be done, which generates ios_sw_config in uut_config.

        This step setup
            1. network connection to tftp server,
            2. set parameters per uut definition
            3. use emergency-install to install main IOS image from tftp server

        :param kwargs:
        :return:
        """
        aplib.set_container_text('IOS INSTALL MAIN IMAGE')
        log.debug("STEP: IOS Install Main Image.")

        # Input
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid', None))
        server_ip = kwargs.get('server_ip', self._ud.uut_config.get('server_ip', None))
        netmask = kwargs.get('netmask', self._ud.uut_config.get('netmask', None))
        uut_ip = kwargs.get('uut_ip', self._ud.uut_config.get('uut_ip', None))
        ios_pre_install_params = kwargs.get('ios_pre_install_params', self._ud.uut_config.get('ios_pre_install_params', {}))
        ios_sw_config = kwargs.get('ios_sw_config', self._ud.uut_config.get('ios_sw_config', None))
        ios_dir = kwargs.get('ios_dirs', self._ud.uut_config.get('ios_dirs', {}).get('remote'))
        ios_install_method = kwargs.get('ios_install_method',
                                        self._ud.uut_config.get('ios_install_method', 'emergency_install'))

        if ios_sw_config:
            ios_main_image = str(ios_sw_config.get('image_name'))
        else:
            ios_main_image = None

        # Sanity check on inputs
        if not ios_sw_config or not ios_main_image:
            log.error('Cannot find IOS main image for PID {}'.format(ios_customer_pid))
            log.error("STEP: IOS main Image Install: FAILED.")
            return aplib.FAIL
        if not server_ip or not netmask or not uut_ip:
            log.error("Must provide TFTP server IP, UUT IP, and netmask.")
            log.error("STEP: IOS main Image Install: FAILED.")
            return aplib.FAIL
        if not isinstance(ios_pre_install_params, dict):
            log.error("pre_install_params must be a dict")
            log.error("STEP: IOS main Image Install: FAILED.")
            return aplib.FAIL

        log.info('Use IOS main image {} for PID {}'.format(ios_main_image, ios_customer_pid))
        log.debug("IOS Install Method: {0}".format(ios_install_method))

        if ios_install_method == 'emergency_install':
            log.info('Rommon params to set before installation: {} '.format(ios_pre_install_params))
            # setup network params in rommon
            self._callback.rommon.set_uut_network_params(ip=uut_ip, server_ip=server_ip, tftp_ip=server_ip, netmask=netmask)
            self._callback.rommon.check_network_params(ip=uut_ip, server_ip=server_ip, tftp_ip=server_ip, netmask=netmask)
            # set pre-params before installation
            self._callback.rommon.set_params(setparams=ios_pre_install_params, reset_required=False)
            # perform the installation
            ret = self._callback.rommon.emergency_install(image=ios_main_image, ios_path=ios_dir)
        elif ios_install_method == 'tftp_download':
            if not all([server_ip, uut_ip, netmask]):
                log.error("Network IP/nemask and/or UUT IP is not defined.")
                return aplib.FAIL
            ret = self._callback.linux.transfer_tftp_files(src_files=ios_main_image,
                                                           dst_files=None,  # src_files will be used as dst_files
                                                           direction='get',
                                                           server_ip=server_ip, ip=uut_ip, netmask=netmask, force=True)
            if not ret:
                log.error("IOS image tftp transfer FAILED.")
        else:
            log.error('IOS install method is not recognized.')
            return aplib.FAIL

        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def install_supplemental_images(self, **kwargs):
        """ IOS Install Supplemntal Images

        Note: MUST install ALL SR packages for ALL IOS versions AVAILABLE to a given product!
              This is typically for CR releases that need backward compatibility or IOS versions.
              This is why a static list is specified in the product definition since we have to maintain history.

        :menu: (enable=True, name=IOS SUPP IMAGES, section=IOS, num=2, args={'menu': True})
        :param kwargs:
               (dict) ios_supp_files: {<device_number>: [(<IOS PID>, <image key>), (<IOS PID>, <image key>), ...], ...}
                                      Required library of files that have to be loaded for backward compat of multiple SW PIDs!
               (dict) ios_sw_config: IOS configuration data for the SPECIFIED INSTALL (customer or test)
                                     MUST run step "ios.download_images() to get this into uut_config."

        :return:
        """
        aplib.set_container_text('IOS INSTALL SUPPLEMENTAL IMAGES')
        log.debug("STEP: IOS Install Supplemental Images.")

        # Sanity check on IOS Manifest
        if not self._ud.ios_manifest:
            log.error("There is no IOS Manifest loaded.")
            log.error("Please check the common dir to ensure it has a _ios_manifestX.py.")
            return aplib.FAIL

        # Check mode
        if self._mode_mgr.current_mode != 'LINUX':
            log.error("Wrong mode; need to be in LINUX to download files.")
            return aplib.FAIL

        # Input
        ios_supp_files = kwargs.get('ios_supp_files', self._ud.uut_config.get('ios_supp_files', None))
        ios_sw_config = kwargs.get('ios_sw_config', self._ud.uut_config.get('ios_sw_config', None))
        server_dir = kwargs.get('server_dir', self._ud.uut_config.get('ios_dirs', {}).get('remote', ''))
        uut_dir = kwargs.get('uut_dir', self._ud.uut_config.get('ios_dirs', {}).get('local', ''))
        server_ip = kwargs.get('server_ip', self._ud.uut_config.get('server_ip', None))
        netmask = kwargs.get('netmask', self._ud.uut_config.get('netmask', None))
        uut_ip = kwargs.get('uut_ip', self._ud.uut_config.get('uut_ip', None))

        # Sanity check on inputs
        if not ios_supp_files:
            log.warning("There were no IOS supplemental files in the product definition.")
            log.warning("STEP: IOS Supplemental Image Load: SKIPPED.")
            return aplib.SKIPPED
        if not isinstance(ios_supp_files, dict):
            log.error("The ios_supp_files product definition entry is not in correct form.")
            return aplib.FAIL
        if not server_ip or not netmask or not uut_ip:
            log.error("Must provide TFTP server IP, UUT IP, and netmask.")
            return aplib.FAIL
        if not ios_sw_config:
            log.warning("There is no IOS config data.")
            log.warning("STEP: IOS Supplemental Image Load: SKIPPED.")
            return aplib.SKIPPED
        if not isinstance(ios_sw_config, dict):
            log.error("The ios_sw_config product definition entry is not in correct form.")
            return aplib.FAIL

        result_list = []
        for device_number, image_ref_list in ios_supp_files.items():
            log.debug("-" * 20)
            log.debug("DeviceNum={0}  Image Ref List={1}".format(device_number, image_ref_list))
            image_list_src = []
            image_list_dst = []
            kref_list = []
            if not image_ref_list:
                continue
            for swpid, kref in image_ref_list:
                kref_list.append(kref) if kref not in kref_list else None
                if swpid == 'ACTUAL':
                    # Use the actual sw config setting for this entry!
                    image = ios_sw_config.get(kref, None)
                else:
                    image = self._ud.ios_manifest.get(swpid, {}).get(kref, None)

                # Build image lists
                if isinstance(image, list):
                    log.debug("Image is a list.")
                    for img in image:
                        if isinstance(img, tuple):
                            image_list_src.append(img[0])
                            image_list_dst.append(img[1])
                        else:
                            image_list_src.append(img)
                            image_list_dst.append(img)
                elif isinstance(image, tuple):
                    log.debug("Image is a tuple.")
                    image_list_src.append(image[0])
                    image_list_dst.append(image[1])
                elif image:
                    log.debug("Image is a str.")
                    image_list_src.append(image)
                    image_list_dst.append(image)
                else:
                    log.warning("No image for '{0}'".format(swpid))

            log.info("-" * 50)
            log.info("Device Number:  {0}".format(device_number))
            log.info("Image Ref List: {0}".format(image_ref_list))
            log.info("Src Image List: {0}".format(image_list_src))
            log.info("Dst Image List: {0}".format(image_list_dst))

            # Cross-check
            for kref in kref_list:
                sw_cfg_kref_files = ios_sw_config.get(kref, [])
                sw_cfg_kref_files = [sw_cfg_kref_files] if not isinstance(sw_cfg_kref_files, list) else sw_cfg_kref_files
                for sw_cfg_kref_file_item in sw_cfg_kref_files:
                    sw_cfg_kref_file = sw_cfg_kref_file_item[0] if isinstance(sw_cfg_kref_file_item,
                                                                              tuple) else sw_cfg_kref_file_item
                    if sw_cfg_kref_file not in image_list_src:
                        log.warning("IOS SW Config file {0} of type {1} was not part of the supplemental list.".format(
                            sw_cfg_kref_file, kref))
                        log.warning(
                            "Please check the product definition for the HW PID to ensure all pkgs are identified.")

            # Mount the device per the enumeration
            ret, mounts = self._callback.linux.mount_disks(device_numbers=[int(device_number)],
                                                           disk_type='primary',
                                                           device_mounts=self._ud.uut_config.get('device_mounts', None),
                                                           disk_enums=self._ud.uut_config.get('disk_enums', None))
            if not ret or not mounts:
                log.error("Mount of device {0} FAILED; cannot continue.".format(device_number))
                return aplib.FAIL

            mount = mounts[0]  # Since we are processing one device number at a time, only one mount in the list.
            log.debug("Mount = {0}".format(mount))

            # Perform TFTP transfer
            fullpath_image_list_src = []
            fullpath_image_list_dst = []
            for item in image_list_src:
                fullpath_item = (os.path.join(server_dir, item[0]), item[1]) \
                    if isinstance(item, tuple) else os.path.join(server_dir, item)
                fullpath_image_list_src.append(fullpath_item)
            for item in image_list_dst:
                fullpath_item = (os.path.join(mount.dir, uut_dir, item[0]), item[1]) \
                    if isinstance(item, tuple) else os.path.join(mount.dir, uut_dir, item)
                fullpath_image_list_dst.append(fullpath_item)
            log.debug("Mount is good; performing TFTP transfer...")
            result = self._callback.linux.transfer_tftp_files(src_files=fullpath_image_list_src,
                                                              dst_files=fullpath_image_list_dst,
                                                              direction='get',
                                                              server_ip=server_ip,
                                                              netmask=netmask,
                                                              ip=uut_ip)
            if not result:
                log.error("TFTP transfer error. Check source files and destination mounts.")
            result_list.append(result)

            # Unmount device
            # TODO: Do we need this?
            if ret and mount:
                log.debug("Unmounting the TFTP mounts...")
                self._callback.linux.umount_devices(mounts=mount)

        if all(result_list):
            log.info("STEP: IOS Install Supplemental Image(s) Load: PASSED.")
            ret = aplib.PASS
        else:
            log.error("STEP: IOS Install Supplemental Image(s) Load: FAILED.")
            ret = aplib.FAIL, "IOS supplemental image did not install."

        return ret

    # Licenses -----------------------------
    @apollo_step
    def install_licenses(self, **kwargs):
        """ IOS Install Licenses

        This function will install the following license types:
            1. RTU (legacy - LAN, IP, IP Services)
            2. DNA (NextGen - Essentials, Advantage)
            3. SLR (DNA Registration by the factory)

        RTU
        ===
        use func ios_utils.install_rtu_license to install it.

        DNA
        ===
        use func result = ios_utils.install_dna_license to install it, require IOS version > 16

        SLR
        ===
        The Specified License Reservation (SLR) for Factory Install method requires the following:
        1. Retrieve a "REQUEST CODE" from the UUT.  (This MUST be done while in IOS.)
        2. Pull the "AUTHORIZATION CODE" from the Cisco Back-end Service (via Cesium & CSSM).
        3. Install the Auth Code XML file to the unit via IOS cli.

        :menu: (enable=True, name=IOS LIC INSTALL RTU, section=IOS, num=10.0, args={'license_types': ['RTU'], 'menu': True})
        :menu: (enable=True, name=IOS LIC INSTALL SLR, section=IOS, num=10.0, args={'license_types': ['SLR'], 'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('IOS LICENSE INSTALL')
        log.info('STEP: IOS License Install.')

        # Inputs
        sw_licenses = kwargs.get('sw_licenses', self._ud.uut_config.get('sw_licenses_normalized', []))
        lic_class = kwargs.get('lic_class', self._ud.uut_config.get('lic_class'))
        major_line_id = kwargs.get('major_line_id', self._ud.uut_config.get('major_line_id', None))
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid'))
        ios_version = self._get_image_config(ios_customer_pid=ios_customer_pid)[1].get('version')
        menu = kwargs.get('menu', False)
        # Get AP count
        apcount = sum([lic['quantity'] for lic in sw_licenses if lic['sku'] == 'LIC-CTIOS-1A'])
        # Remove AP count license from sw_licenses
        sw_licenses = [lic for lic in sw_licenses if lic['sku'] != 'LIC-CTIOS-1A']

        if menu:
            if not major_line_id:
                major_line_id = aplib.ask_question("Enter Major LineID:")
                if major_line_id.upper() == 'ABORT':
                    return aplib.SKIPPED
                elif major_line_id.upper() == 'NONE':
                    major_line_id = None
                elif not major_line_id.isdigit():
                    return aplib.FAIL
                else:
                    major_line_id = int(major_line_id)
                log.debug("Major LineID  = {0}".format(major_line_id))

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['IOS', 'IOSE']:
            log.warning("Wrong mode ({0}) for this operation. Mode 'IOS' or 'IOSE' is required.".format(mode))
            return aplib.FAIL

        log.debug("Licenses = {0}".format(sw_licenses))
        log.debug('AP count = {0}'.format(apcount))

        # Perform license installation action
        results = [True]
        if lic_class == 'RTU':
            for lic in sw_licenses:
                result = self._install_rtu_license(license=lic['sku'], apcount=apcount, ios_version=ios_version)
                results.append(result)
        elif lic_class == 'DNA':
            for lic in sw_licenses:
                result = self._install_dna_license(license=lic['sku'], apcount=apcount, ios_version=ios_version)
                results.append(result)
            # Perform SLR action for DNA license
            # SLR only available for IOS version starting from 16.9
            if common_utils.is_version_greater(ios_version, '16.9'):
                request_code = self._get_slr_request_code()
                if not request_code:
                    log.error("Cannot install SLR; no request code.")
                    results.append(False)
                auth_code, auth_code_required, auth_code_filepath = self._pull_slr_auth_codes(request_code,
                                                                                              major_line_id=major_line_id,
                                                                                              license_sku_qty=sw_licenses)
                if auth_code_required:
                    log.info("SLR Auth code installation: REQUIRED.")
                    if not auth_code:
                        log.error("Cannot install SLR; no auth code.")
                        results.append(False)
                    if not self._install_slr_auth_code(auth_code_filepath):
                        log.error("SLR Auth code installation failed.")
                        results.append(False)
                else:
                    log.info("SLR Auth code installation: NOT required.")
                    results.append(True)
        else:
            log.error("Unknown license type: {0}".format(lic_class))
            results.append(False)

        return aplib.PASS if all(results) else aplib.FAIL

    @apollo_step
    def verify_default_licenses(self, **kwargs):
        """ IOS Verify Default Licenses

        Verify correct licenses are installed on UUT.
        License info comes from uut_config['sw_licenses_normalized'], which is generated with self._get_sw_licenses().

        There are 2 types of license, RTU and DNA.
        1. RTU, use ios_utils.verify_rtu_license to verify license level (lanbase, ipbase, ipservices).
        2. DNA, use ios_utils.verify_dna_license to verify license level (essentials, advantage) as well as subscription.
        3. use verify_slr to verify SLR code for DNA license (if required).

        :menu: (enable=True, name=IOS DWNLD IMAGES, section=IOS, num=3, args={'menu': True})
        :param kwargs:
        :return:
        """
        aplib.set_container_text('IOS VERIFY LICENSES')
        log.debug("STEP: IOS Verify Licenses.")

        # Sanity check on IOS Manifest
        if not self._ud.ios_manifest:
            log.error("There is no IOS Manifest loaded.")
            log.error("Please check the common dir to ensure it has a _ios_manifestX.py.")
            return aplib.FAIL

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['IOSE']:
            log.warning("Wrong mode ({0}) for this operation. Mode 'IOSE' is required.".format(mode))
            return aplib.FAIL

        # Input
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid'))
        ios_test_pid = kwargs.get('ios_test_pid', self._ud.uut_config.get('ios_test_pid'))
        sw_licenses = kwargs.get('sw_licenses', self._ud.uut_config.get('sw_licenses_normalized'))
        lic_class = kwargs.get('lic_class', self._ud.uut_config.get('lic_class'))

        # Get IOS config detail
        log.debug("ios_customer_pid={0},  ios_test_pid={1}".format(ios_customer_pid, ios_test_pid))
        ios_pid, ios_sw_detail = self._get_image_config(ios_customer_pid=ios_customer_pid, ios_test_pid=ios_test_pid)
        ios_version = ios_sw_detail.get('version')
        apcount_qty = sum(
            [item.get('quantity') for item in sw_licenses if item.get('sku') == license_utils.apcount_sku])

        # Print details
        log.info("-" * 60)
        log.info("IOS PID:          {0}".format(ios_pid))
        log.info("SW Licenses:      {0}".format(sw_licenses))
        log.info("License Class:    {0}".format(lic_class))
        log.info("IOS Version:      {0}".format(ios_version))
        log.info("AP Count (total): {0}".format(apcount_qty))

        # Perform license check
        results = [True]
        for license in sw_licenses:
            if license_utils.is_dna_license(license['sku']):
                ret = self._default_license_verification(license_pid=license['sku'], ios_version=ios_version, license_type='DNA')
                results.append(ret)
                ret = self._default_license_verification(license_pid=None, ios_version=ios_version, license_type='RTU')
                results.append(ret)
            elif license_utils.is_rtu_license(license['sku']):
                ret = self._default_license_verification(license_pid=license['sku'], ios_version=ios_version, license_type='RTU')
                results.append(ret)
                ret = self._default_license_verification(license_pid=None, ios_version=ios_version, license_type='DNA')
                results.append(ret)
            elif license_utils.is_apcount_license(license['sku']):
                # use verify_apcount_license to verify it
                log.debug("Total AP Count = {0}".format(apcount_qty))
            else:
                # Should never get here
                log.error('Error in sw_licenses list, unrecognized license PID {0}'.format(license['sku']))
                results.append(False)

        return aplib.PASS if all(results) else aplib.FAIL

    @apollo_step
    def verify_apcount_license(self, **kwargs):
        """ Verify AP count License
        Verify AP count license with correct apcount quantity are installed on UUT.
        License info comes from uut_config['sw_licenses_normalized'], which is generated with self._get_sw_licenses().
        use ios._apcount_license_verification to verify AP count quantity
        :param kwargs:
        :return:
        """
        aplib.set_container_text('IOS VERIFY APCOUNT LICENSE')
        log.debug("STEP: IOS Verify AP-count License.")

        # Sanity check on IOS Manifest
        if not self._ud.ios_manifest:
            log.error("There is no IOS Manifest loaded.")
            log.error("Please check the common dir to ensure it has a _ios_manifestX.py.")
            return aplib.FAIL

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['IOSE']:
            log.warning("Wrong mode ({0}) for this operation. Mode 'IOSE' is required.".format(mode))
            return aplib.FAIL

        # Input
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid'))
        ios_test_pid = kwargs.get('ios_test_pid', self._ud.uut_config.get('ios_test_pid'))
        sw_licenses = kwargs.get('sw_licenses', self._ud.uut_config.get('sw_licenses_normalized'))

        # Get IOS config detail
        log.debug('ios_customer_pid {0}, ios_test_pid {1}'.format(ios_customer_pid, ios_test_pid))
        log.debug('sw_licenses {0}'.format(sw_licenses))
        ios_pid, ios_sw_detail = self._get_image_config(ios_customer_pid=ios_customer_pid, ios_test_pid=ios_test_pid)
        ios_version = ios_sw_detail.get('version')
        apcount_qty = sum([item.get('quantity') for item in sw_licenses if item.get('sku') == license_utils.apcount_sku])

        # Check APcount quantity
        ret = self._apcount_license_verification(apcount=apcount_qty, ios_version=ios_version)

        return aplib.PASS if ret else aplib.FAIL

    @apollo_step
    def get_software_licenses(self, **kwargs):
        """ Get Software Licenses (Step)

        Look up in major_line_id_cfg to search for sw license PIDs. If major_line_id_cfg is not available, use cesium
        service call to get it from major_line_id.
        This is a step wrapper of self._get_sw_licenses()

        :param kwargs:
               (int) major_line_id: LineID (top level)
               (dict) major_line_id_cfg: LineID config from cesiumlib.get_lineid_config()

        :return: aplib.PASS
        """
        aplib.set_container_text('GET SW LICENSES')
        log.info('STEP: Get SW Licenses From Line ID.')

        # Input processing
        major_line_id = kwargs.get('major_line_id', self._ud.uut_config.get('major_line_id'))
        major_line_id_cfg = kwargs.get('major_line_id_cfg', self._ud.uut_config.get('major_line_id_cfg'))

        # Get the LID config
        if not major_line_id_cfg:
            try:
                major_line_id_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id)
            except (apexceptions.ServiceFailure, apexceptions.ResultFailure) as err:
                log.debug(err)
                return aplib.FAIL, err.message

        # Save info in uut_config
        self._get_sw_licenses(major_line_id=major_line_id, major_line_id_cfg=major_line_id_cfg)

        return aplib.PASS

    @apollo_step
    def remove_default_licenses(self, **kwargs):
        """ Remove Default Licenses

            :NOTE 1: This step requires mm mode LINUX
        This step removes all previous installed licenses by deleting license files in Linux

        :param kwargs: :default_license_files:  (dict) files to remove, if it is not given, it should get from uut_config

        :return:            aplib.PASS if all licenses are deleted successfully
                            aplib.FAIL otherwise
        """
        aplib.set_container_text('REMOVE DEFAULT LICENSES')
        log.debug("STEP: Remove previously installed licenses.")

        # Check mode
        if self._mode_mgr.current_mode != 'LINUX':
            log.error("Wrong mode; need to be in LINUX to remove licenses.")
            return aplib.FAIL, "Wrong mode."

        # Input
        license_files = kwargs.get('default_license_files', self._ud.uut_config.get('default_license_files', None))

        # Sanity check on inputs
        if not license_files:
            log.warning("There were no license files in the product definition.")
            log.warning("STEP: Remove previously installed licenses: SKIPPED.")
            return aplib.SKIPPED
        if not isinstance(license_files, dict):
            log.error("The license_files product definition entry is not in correct form.")
            return aplib.FAIL

        result_list = []
        for device_number, del_file_list in license_files.items():
            log.debug("-" * 20)
            log.debug("DeviceNum={0}  Delete File List={1}".format(device_number, del_file_list))
            if not del_file_list:
                continue

            log.info("-" * 50)
            log.info("Device Number:    {0}".format(device_number))
            log.info("Delete File List: {0}".format(del_file_list))
            log.info("-" * 50)

            # Mount the device per the enumeration
            ret, mounts = self._callback.linux.mount_disks(device_numbers=[int(device_number)],
                                                           disk_type='primary',
                                                           device_mounts=self._ud.uut_config.get('device_mounts', None),
                                                           disk_enums=self._ud.uut_config.get('disk_enums', None))
            if not ret or not mounts:
                log.error("Mount of device {0} FAILED; cannot continue.".format(device_number))
                return aplib.FAIL

            mount = mounts[0]  # Since we are processing one device number at a time, only one mount in the list.
            log.debug("Mount = {0}".format(mount))

            # Delete all files in del_file_list
            fullpath_del_file_list = [os.path.join(mount.dir, i) for i in del_file_list]
            log.debug("Mount is good; deleting existing licenses...")
            result = self._callback.linux.delete_files(files=fullpath_del_file_list)
            if not result:
                log.error("Failed to delete file, please check UUT console output for detail")
            result_list.append(result)

            # Unmount device
            if ret and mount:
                log.debug("Unmounting the license mounts...")
                self._callback.linux.umount_devices(mounts=mount)

        if all(result_list):
            log.info("STEP: Remove previously installed licenses: PASSED.")
            ret = aplib.PASS
        else:
            log.error("STEP: Remove previously installed licenses: FAILED.")
            ret = aplib.FAIL

        return ret

    # Env -----------------------------
    @apollo_step
    def verify_log_for_empty_poe_ports(self, **kwargs):
        """PoE Verify LOG for Empty Ports (STEP)

            NOTE1: This step requires UUT in 'IOSE' mode.
            NOTE2: This does NOT requires PoE Loadbox, it is testing empty POE ports (no device connected),

        :param kwargs: poe_ports:       POE ports (str), this is for manual override,
                                        usually this value should come from uut_config
                                    ex: '1-48', '1-24', MUST be in this format
        :return:
        """
        # If product definition does not specify PoE (irrespective of any PoE equipment connections),
        # then do not run this step.
        if 'poe' not in self._ud.uut_config:
            log.warning("The 'poe' data dict is not defined for the UUT per the product_definition.")
            log.warning("This test will be disabled.")
            return aplib.DISABLED

        poe = self._ud.uut_config.get('poe', {})
        log.debug("PoE UUT Config: {0}".format(poe))
        if not poe:
            log.error("The 'poe' product definition entry is empty!")
            return aplib.FAIL

        # mode check
        if not self._mode_mgr.is_mode('IOSE'):
            log.warning("Wrong mode ({0}) for this operation. Mode 'IOSE' is required.".format(self._mode_mgr.current_mode))
            return aplib.FAIL
        uut_prompt = self._mode_mgr.uut_prompt_map['IOSE']

        # perform test
        ret = self.verify_log_for_error(search_patterns=['Cisco PD', 'IEEE PD'],
                                        err_patterns='Power Device detected')

        return aplib.PASS if ret else (aplib.FAIL, "PoE Empty Port Status IOS Log not correct.")

    @apollo_step
    def check_environments(self, **kwargs):
        """ Check IOS Environment
        List all environment status, make sure there is no error (fault, FAULTY, false, etc)
        :param kwargs:
        :return:
        """
        aplib.set_container_text('CHECK IOS ENVIRONMENTS')
        log.debug("STEP: Check IOS Environments.")

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['IOS', 'IOSE']:
            log.error("Wrong mode; need to be in IOS to check environments.")
            return aplib.FAIL

        uut_prompt = self._mode_mgr.uut_prompt_map[mode]

        err_pattern = re.compile(r'(FAULTY)|([Ff]alse)|([Ff]ault)|([Ee]rr)')
        self._uut_conn.sende('show env all\n', expectphrase=uut_prompt, regex=True)

        if err_pattern.search(self._uut_conn.recbuf):
            log.error('Error is found in environments, check output')
            log.error(self._uut_conn.recbuf)
            return aplib.FAIL

        log.info('IOS Environment: CLEAN (No errors detected)!')

        return aplib.PASS

    @apollo_step
    def verify_customer_version(self, **kwargs):
        """ Verify Customer IOS version
        Get current installed version from IOS CLI, then compare it to IOS PID in order.
        If they match, step PASS, otherwise step FAIL.
        :param (dict) kwargs:
                      (str) ios_customer_pid: Customer IOS PID in order, this info should come from lineid.
        :return: aplib.PASS if version matches
                 aplib.FAIL if version doesn't match, or current version cannot be found, or ios_customer_pid is not supplied.
        """
        aplib.set_container_text('VERIFY CUSTOMER IOS VERSION')
        log.debug("STEP: Verify Customer IOS Version.")

        # Sanity check on IOS Manifest
        if not self._ud.ios_manifest:
            log.error("There is no IOS Manifest loaded.")
            log.error("Please check the common dir to ensure it has a _ios_manifestX.py.")
            return aplib.FAIL

        # Check mode
        mode = self._mode_mgr.current_mode
        if mode not in ['IOS', 'IOSE']:
            log.error("Wrong mode; need to be in IOS to check environments.")
            return aplib.FAIL

        # Process inputs
        ios_customer_pid = kwargs.get('ios_customer_pid', self._ud.uut_config.get('ios_customer_pid', None))

        # Sanity check on inputs
        if not ios_customer_pid:
            log.error('Cannot find IOS PID {}'.format(ios_customer_pid))
            log.error("STEP: Verify Customer IOS Version: FAILED.")
            return aplib.FAIL

        # Get current installed version
        current_ver = self.get_ios_version()
        if not current_ver:
            log.error('Cannot find IOS version from CLI')
            return aplib.FAIL
        # verify current version against ios manifest
        ret = self.verify_ios_version(target_version=current_ver, ios_customer_pid=ios_customer_pid)
        if not ret:
            log.error(
                'Current IOS version {0} does not match customer order PID {1}'.format(current_ver, ios_customer_pid))
            return aplib.FAIL
        else:
            return aplib.PASS

    @apollo_step
    def clean_up(self, **kwargs):
        """ IOS clean up

        IOS needs to be cleaned up before shipping. This step covers 3 cleanings,
            1. OBFL logging
            2. crashinfo: partition
            3. startup-config

        :param (dict) kwargs:
                      (list) cleanup_items: Items to clean in current call

        :return: aplib.PASS if all 3 cleaning are successful, otherwise aplib.FAIL
        """
        aplib.set_container_text('IOS CLEAN UP')
        log.debug("STEP: IOS Clean Up.")

        _cleanup_funcs = {
            'obfl': self.clear_ios_obfl,
            'startup-config': self.clear_ios_startup_config,
            'crashinfo': self.clear_ios_crashinfo_files,
            'nvram': self.erase_nvram
        }

        # Process input
        cleanup_items = kwargs.get('cleanup_items', self._ud.uut_config.get('ios_cleanup_items'))
        if not isinstance(cleanup_items, list):
            log.error('cleanup_items must be a list')
            return aplib.FAIL
        for item in cleanup_items:
            if item not in _cleanup_funcs:
                log.error('Unrecognized clean up request {}'.format(item))
                log.error('Supported clean up options are {}'.format(_cleanup_funcs.keys()))
                return aplib.FAIL

        # Check mode
        if self._mode_mgr.current_mode != 'IOSE':
            log.error("Wrong mode; need to be in IOS Enable mode to perform clean up.")
            return aplib.FAIL

        # Start cleaning
        result_list = []
        for item in cleanup_items:
            if item != 'obfl':
                ret = _cleanup_funcs[item]()
            else:
                ret = _cleanup_funcs[item](obfl_items=self._ud.uut_config.get('obfl_items', []))
            log.info('Clear {0} result = {1}'.format(item, ret))
            result_list.append(ret)

        return aplib.PASS if all(result_list) else aplib.FAIL

    @apollo_step
    def waitfor_cfg_dialog_boot(self, **kwargs):
        """ Wait For IOS Cfg Dialog Boot Up

        This step should be used after a power cycle, it monitors recbuf and wait for IOS to complete boot up.
        IOS should boot up to "System Configuration Dialog", which is default factory status when customer gets the UUT.
        Expected phrase and time out is configurable through kwargs.

        :param (dict) kwargs:
                      (list|str) bootup_prompt: expected phrase (phrase list) for uut_conn.waitfor,
                                                default = ['--- System Configuration Dialog ---',
                                                           'Would you like to enter the initial configuration dialog? [yes/no]:']
                      (int) timeout: limit in sec, default is 600

        :return: aplib.PASS if UUT boot up successfully, aplib.FAIL otherwise
        """
        aplib.set_container_text('WAITFOR IOS BOOT UP')
        log.debug("STEP: Wait for IOS to boot up.")

        # Process input
        bootup_prompt = kwargs.get('bootup_prompt', ['--- System Configuration Dialog ---',
                                                     'Would you like to enter the initial configuration dialog? [yes/no]:'])
        timeout = kwargs.get('timeout', 600)
        bootup_prompt = [bootup_prompt] if isinstance(bootup_prompt, str) else bootup_prompt

        try:
            self._uut_conn.waitfor(expectphrase=bootup_prompt, timeout=timeout)
            log.info('IOS boot up successfully')
        except apexceptions.TimeoutException as err:
            log.error('IOS failed to boot up to expected prompt in time')
            log.error(err.message)
            return aplib.FAIL
        except Exception as err:
            log.error(err.message)
            return aplib.FAIL

        return aplib.PASS

    # ==================================================================================================================
    # USER METHODS   (step support)
    # ==================================================================================================================
    # ------------------------------------------------------------------------------------------------------------------
    # Identity Protection Verification
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_crypto_pki(self, expected_cert_count):
        """ Get  PKI Certs
        (a.k.a. X.509 SUDI Certs)

        Sample cert chains (SHA1, SHA256):
        ----------------------------------

        Switch#show crypto pki cert
        Switch#show crypto pki cert
        Switch#
        *Aug 31 05:31:47.015: %SSH-5-ENABLED: SSH 1.99 has been enabledshow crypto pki cert
        Certificate
          Status: Available
          Certificate Serial Number (hex): 1476CFCE00000003B911
          Certificate Usage: General Purpose
          Issuer:
            cn=Cisco Manufacturing CA SHA2
            o=Cisco
          Subject:
            Name: WS-C3850-24P-706BB9D88000
            Serial Number: PID:WS-C3850-24P SN:FOC2126L1BE
            cn=WS-C3850-24P-706BB9D88000
            serialNumber=PID:WS-C3850-24P SN:FOC2126L1BE
          CRL Distribution Points:
            http://www.cisco.com/security/pki/crl/cmca2.crl
          Validity Date:
            start date: 05:12:50 UTC Aug 31 2017
            end   date: 05:22:50 UTC Aug 31 2027
          Associated Trustpoints: CISCO_IDEVID_SUDI

        Certificate
          Status: Available
          Certificate Serial Number (hex): 26AF03A3000000047111
          Certificate Usage: General Purpose
          Issuer:
            cn=Cisco Manufacturing CA
            o=Cisco Systems
          Subject:
            Name: WS-C3850-24P-706BB9D88000
            Serial Number: PID:WS-C3850-24P SN:FOC2126L1BE
            cn=WS-C3850-24P-706BB9D88000
            serialNumber=PID:WS-C3850-24P SN:FOC2126L1BE
          CRL Distribution Points:
            http://www.cisco.com/security/pki/crl/cmca.crl
          Validity Date:
            start date: 05:09:30 UTC Aug 31 2017
            end   date: 05:19:30 UTC Aug 31 2027
          Associated Trustpoints: CISCO_IDEVID_SUDI_LEGACY

        CA Certificate
          Status: Available
          Certificate Serial Number (hex): 02
          Certificate Usage: Signature
          Issuer:
            cn=Cisco Root CA M2
            o=Cisco
          Subject:
            cn=Cisco Manufacturing CA SHA2
            o=Cisco
          CRL Distribution Points:
            http://www.cisco.com/security/pki/crl/crcam2.crl
          Validity Date:
            start date: 13:50:58 UTC Nov 12 2012
            end   date: 06:32:01 UTC Oct 7 1901
          Associated Trustpoints: CISCO_IDEVID_SUDI Trustpool

        CA Certificate
          Status: Available
          Certificate Serial Number (hex): 01
          Certificate Usage: Signature
          Issuer:
            cn=Cisco Root CA M2
            o=Cisco
          Subject:
            cn=Cisco Root CA M2
            o=Cisco
          Validity Date:
            start date: 13:00:18 UTC Nov 12 2012
            end   date: 06:32:02 UTC Oct 7 1901
          Associated Trustpoints: CISCO_IDEVID_SUDI0 Trustpool

        CA Certificate
          Status: Available
          Certificate Serial Number (hex): 6A6967B3000000000003
          Certificate Usage: Signature
          Issuer:
            cn=Cisco Root CA 2048
            o=Cisco Systems
          Subject:
            cn=Cisco Manufacturing CA
            o=Cisco Systems
          CRL Distribution Points:
            http://www.cisco.com/security/pki/crl/crca2048.crl
          Validity Date:
            start date: 22:16:01 UTC Jun 10 2005
            end   date: 20:25:42 UTC May 14 2029
          Associated Trustpoints: CISCO_IDEVID_SUDI_LEGACY Trustpool

        CA Certificate
          Status: Available
          Certificate Serial Number (hex): 5FF87B282B54DC8D42A315B568C9ADFF
          Certificate Usage: Signature
          Issuer:
            cn=Cisco Root CA 2048
            o=Cisco Systems
          Subject:
            cn=Cisco Root CA 2048
            o=Cisco Systems
          Validity Date:
            start date: 20:17:12 UTC May 14 2004
            end   date: 20:25:42 UTC May 14 2029
          Associated Trustpoints: CISCO_IDEVID_SUDI_LEGACY0 Trustpool

        Router Self-Signed Certificate
          Status: Available
          Certificate Serial Number (hex): 01
          Certificate Usage: General Purpose
          Issuer:
            cn=IOS-Self-Signed-Certificate-72214765
          Subject:
            Name: IOS-Self-Signed-Certificate-72214765
            cn=IOS-Self-Signed-Certificate-72214765
          Validity Date:
            start date: 09:50:26 UTC May 11 2017
            end   date: 00:00:00 UTC Jan 1 2020
          Associated Trustpoints: TP-self-signed-72214765
          Storage: nvram:IOS-Self-Sig#1.cer

        :param (int) expected_cert_count: Number of certs to expect.
                     **IMPORTANT**: Some IOS versions+platforms can take a long time to retrieve
                                    ALL certs; so there is a built-in wait & retry in this function.
        :returns: (dict) Returns dictionary with SN, PID, MAC, hashtype, node, and status info for available certs
        """
        # Import Configuration information
        log.info('Gathering Crypto PKI (X.509 SUDI) Certificates...')
        log.info("Expecting {0} certs.".format(expected_cert_count))

        # Initialize data structures for certificate validation status
        validated_certs = {}

        ios_cert_waittime = 60

        self._uut_conn.send('terminal length 0\n', expectphrase=self._uut_prompt, regex=True, timeout=30)

        @common_utils.func_retry
        def __crypto():
            self._clear_recbuf()
            self._uut_conn.send('show crypto pki cert\n', expectphrase=self._uut_prompt, regex=True)
            time.sleep(IOS.RECBUF_TIME)
            p = re.compile('(?s)((?:CA )?Certificate.*?Associated Trustpoints:.*?[\n\r]+)')
            m = p.findall(''.join(self._uut_conn.recbuf).replace('\r', '\n'))
            if m:
                if len(m) < expected_cert_count:
                    log.warning("*** Did NOT receive ALL expected certificates! ***")
                    log.warning("Received {0} of {1} certs.".format(len(m), expected_cert_count))
                    log.warning("There will be a wait delay for IOS and another query attempt.")
                    log.debug("Waiting on IOS for {0} secs...".format(ios_cert_waittime))
                    time.sleep(ios_cert_waittime)
                    log.debug("Done waiting.")
                    s = False
                else:
                    log.debug("Minimum expected cert count obtained: Recv:{0}, Expct:{1}".
                              format(len(m), expected_cert_count))
                    s = True
            else:
                log.debug("No cert patterns detected!")
                s = False
            return s, m

        # Obtain certificates
        cert_flag, certs = __crypto()
        if len(certs) == 0:
            log.error("FAILED: Cert data is empty.")
            return None

        # Obtain and validate attributes
        status_reg = re.compile(r'[ \t]*Status:[ \t]*(.*)[ \t]*')  # Finds Status
        cn_reg = re.compile(r'[ \t]*cn=[ \t]*(.*)[ \t]*')  # Finds common names

        for cert in certs:
            log.debug("Processing cert...")
            # Find Status and Common names for cert
            cert_status = status_reg.findall(cert)[0]
            cn1, cn2 = cn_reg.findall(cert)

            # Mac address and serial number default N/A unless leaf
            cert_pid = cert_mac = cert_sn = 'N/A'

            # Determine Hash type (SHA1 or SHA256)
            hash_type = 'SHA256' if 'M2' in cn1 or 'SHA2' in cn1 else 'SHA1'

            # Find node level in chain and necessary attributes, and store to dictionary.
            if cn1 == cn2:
                node_level = 'root'
            elif 'Cisco Root CA' in cn1:
                node_level = 'branch'
            elif 'Cisco Manufacturing CA' in cn1:
                node_level = 'leaf'
                # Capture PID, SN
                p = re.compile(r'[ \t]*PID:[ \t]*([A-Za-z0-9-]*)[ \t]*SN:([A-Za-z]{3}[0-9]{4}[A-Za-z0-9]{4})')
                m = p.findall(cert)
                cert_pid, cert_sn = m[0] if len(m) == 2 else None

                # Capture Mac
                p = re.compile(r'[ \t]*-([a-fA-F0-9]{12})')
                m = p.findall(cn2)
                cert_mac = m[0].upper() if m else None
            else:
                node_level = 'unknown'

            validated_certs[hash_type, node_level, cert_pid, cert_mac, cert_sn] = cert_status

        if validated_certs:
            log.info("Certificates Acquired")
            common_utils.print_large_dict(validated_certs)
        else:
            log.error("Certificate acquisition is empty.")
            log.error("Check X.509 programming. Confirm IOS output.")

        return validated_certs

    @func_details
    def _check_crypto_pki(self, x509_hashes, validated_certs, pid, mac, sn, verbose=False):
        """ Checks Crypto PKI certs and Chains and validates availability.

        :param x509_hashes: (list)(str) List of strings corresponding to available x509 hash types
        :param validated_certs:
        :param pid: Product ID for UUT
        :param mac: MAC Address for UUT
        :param sn: Serial Number for UUT
        :param verbose:
        :returns: (bool) Return True if all certificates exist and attributes are valid, else returns False
        """
        log.info('Validating cert crypto hashes for {} hashtype(s)'.format(', '.join(x509_hashes)))
        mac = common_utils.convert_mac(mac, conv_type='1', case='upper')

        # Confirm 3 Certs per hash
        cert_num = len(x509_hashes) * 3
        found_cert_num = len(validated_certs)
        log.debug("Cert count: Found={0}, Expected={1}".format(found_cert_num, cert_num))
        crypto_failures = []
        if found_cert_num < cert_num:
            log.error('Invalid number of certificates. Expected at least {}, found {}. \
                        Confirm that all available hash types are inputted.'.format(cert_num, found_cert_num))
            return False

        common_utils.print_large_dict(validated_certs) if verbose else None

        # Validate Certs
        for x509_hash in x509_hashes:
            try:
                root = validated_certs[x509_hash, 'root', 'N/A', 'N/A', 'N/A']
                branch = validated_certs[x509_hash, 'branch', 'N/A', 'N/A', 'N/A']
                leaf = validated_certs[x509_hash, 'leaf', pid, mac, sn]

                # Check Status
                log.debug(" Checking hash: {0} with root={1}, branch={2}, leaf={3}".
                          format(x509_hash, root, branch, leaf))
                if root == 'Available' and root == branch == leaf:
                    log.debug('X.509 Certificate valid for {}'.format(x509_hash))
                else:
                    crypto_failures.append('X.509 Certificate Status unavailable for {}'.format(x509_hash))

            except KeyError as e:
                log.debug("{0}".format(e))
                crypto_failures.append('X.509 Certificate Status unavailable for {}'.format(x509_hash))

        # If any Auth failures do not pass, return false. Display failed values
        if crypto_failures:
            for failure in crypto_failures:
                log.error(failure)
            log.error('FAILED. Invalid CERT chain; One or more expected certificates were not found')
            return False

        log.info('{} Cert chains validated'.format(', '.join(x509_hashes)))
        return True

    @func_details
    def _validate_hw_authentication(self, hw_modules=None):
        """ Validate HW authentication status ACT2/QUACK2 for given hardware.
        The validation does both a) get and b) check of the HW status.

        Sample:
        -------
        show platform hardware auth status
        Switch 1:
        Mainboard Authentication:     Passed
        FRU Authentication:           Not Available
        Stack Cable A Authentication: Passed
        Stack Cable B Authentication: Passed

        :param hw_modules: (list)(str) List of strings of HW module identifiers to manually validate ACT2/QUACK2 Auth
        :returns: (bool) Return True if all authentication is available and passes.
        """
        # Validate ACT2 or QUACK2
        log.info('Verifying ACT2/QUACK2 Authentication Status...')
        auth_failures = []
        # Authentication status regex pattern (Platform, Auth Status)
        p = re.compile(r'[ \t]*(.*) Authentication:[ \t]*([\S].*)[ \t]*')

        if hw_modules:
            # Manual HW Module Entry for validation
            try:
                for hw_module in hw_modules:
                    self._uut_conn.send('show platform hardware auth status | i {}\n'.
                                  format(hw_module), expectphrase=self._uut_prompt, regex=True, timeout=30)
                    auth_status = p.findall(self._uut_conn.recbuf.replace('\r', '\n'))[0][1]
                    if auth_status != 'Passed':
                        # This means we are looking for a specific module that MUST pass.
                        auth_failures.append('Authentication status {} for {} '.format(auth_status, hw_module))
            except IndexError:
                auth_failures.append('Hardware auth status for {} module does not exist!!!'.
                                     format(auth_status, hw_module))
        else:
            # Automatic HW Module Retrieval for validation
            self._uut_conn.send('show platform hardware auth status\n', expectphrase=self._uut_prompt, regex=True)
            auth_status = dict(p.findall(self._uut_conn.recbuf.replace('\r', '\n')))
            for hw_module in auth_status:
                if auth_status[hw_module] == 'Failed':
                    # Passed or Not Available is ok when looking at all as a group.
                    auth_failures.append('Authentication status {} for {} module'.
                                         format(auth_status[hw_module], hw_module))

        # If any Auth failures, return false and display failure information.
        if auth_failures:
            for failure in auth_failures:
                log.error(failure)
            log.error('FAILED. Hardware authentication invalid for one or more modules')
            return False

        log.info('Identity Protection authenticated and valid for all available modules')
        return True

    # ----------------------------------------------------------------------------------------------------------------------
    # Image
    # ----------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_image_config(self, ios_customer_pid=None, ios_test_pid=None, source=None):
        """ Get IOS Image Config Details
        Find the image details for a Customer PID or Test PID.
        If both are given, then Customer PID takes precedence.
        The image details can have three different sources:
            1) Cesium DB: OSCAR Mapped in CNFv2
            2) Cesium DB: Custom entry in CNFv2 via CNF-Exp tool
            3) Local Manifest (for prototype NPI stage prior to release, mfg special ios test images,
                               or offline activity)

        The Cesium DB entries (if available) have precedence over the local manifest; however, if the local manifest
        has a newer version of the SW PID then that will override (use case = sustaining a released SW PID with a
        newer build number).

        If the Cesium DB details are used, an attempt will be made to add the supplemental details from the
        manifest's matching PID (i.e. recovery, sr pkgs, etc.).

        Example:
        ios_pid = 'S3850UK9-32-0SE'
        ios_image_details =
        {
            'product_id': 'S3850UK9-32-0SE',
            'name': 'EX',
            'platforms': 'WS-C3850',
            'cco_location': '/auto/beyond.150.bin2/03.02.03.SE.150-1.EX3/.3DES',
            'image_name': 'cat3k_caa-universalk9.SPA.03.02.03.SE.150-1.EX3.bin',
            'version': '3.2.3',
            'md5': '1f4673f287c85ed7e1dd39b6040be5f1',
            'recovery':  'cat3k_caa-recovery.SPA.03.02.03.SE.bin',
            'SR_pkgs': ['cat3k_caa-drivers.SSA.03.02.03.XSR1.73.pkg']
            'hw_pid_owners': []
        },


        :param (str) ios_customer_pid:
        :param (str) ios_test_pid:
        :param (str) source:          if is None, leave it determine by logic (cesium first), this is default
                                      if it is set to 'cesium' or 'manifest', it overrides logic
        :return (dict): <IOS PID chosen>, <IOS SW Details>
        """

        # Choose which type of SW PID to use.
        if ios_customer_pid:
            # Note: when present, customer PID takes precedence always.
            ios_pid = ios_customer_pid
            log.info("IOS Customer PID will be used: {0}".format(ios_pid))
        elif ios_test_pid:
            ios_pid = ios_test_pid
            log.info("IOS Test PID will be used: {0}".format(ios_pid))
        else:
            log.warning("No Customer PID or Test PID for the SW was provided.")
            return None, dict()
        log.debug("Using the following ios_pid={0}".format(ios_pid))

        ios_image_cesium = dict()
        ios_image_manifest = self._ud.ios_manifest.get(ios_pid)

        cesium_source = None
        try:
            log.debug("Get OSCAR mapped PID...")
            ios_image_cesium = cesiumlib.get_sw_config(product_id=ios_pid)
            cesium_source = 'OSCAR'
        except apexceptions.ApolloException:
            try:
                log.debug("No OSCAR mapped PID; get CNFv2-Exp custom (pre-release)...")
                ios_image_cesium = cesiumlib.product_id_config(product_id=ios_pid)
                cesium_source = 'CNFv2-CNFExp'
            except apexceptions.ApolloException:
                log.debug("SW details are NOT avaialble via Cesium sources!")

        # Add supplemental details to the config
        ios_image_cesium['recovery'] = ios_image_manifest.get('recovery', None)
        ios_image_cesium['SR_pkgs'] = ios_image_manifest.get('SR_pkgs', [])
        ios_image_cesium['hw_pid_owners'] = ios_image_manifest.get('hw_pid_owners', [])

        # Choose which information source to use
        log.info("IOS Ver (CesiumDB)     = '{0}'".format(ios_image_cesium.get('version', None)))
        log.info("IOS Ver (Local Mani)   = '{0}'".format(ios_image_manifest.get('version', None)))
        log.info("CesiumDB source        = '{0}'".format(cesium_source)) if cesium_source else None
        log.info("User specified source  = '{0}'".format(source)) if source else None

        if not source:
            if common_utils.is_version_greater(ios_image_cesium.get('version', None),
                                               ios_image_manifest.get('version', '0')):
                ios_image_details = ios_image_cesium.copy()
                log.info("The IOS image details will be used from the Cesium DB.")
            else:
                ios_image_details = ios_image_manifest.copy()
                log.info("The IOS image details will be used from the Local Manifest.")
        else:
            log.debug("Source override...")
            if source is 'cesium':
                ios_image_details = ios_image_cesium.copy()
            elif source is 'manifest':
                ios_image_details = ios_image_manifest.copy()
            else:
                log.error("Unknown source: {0}".format(source))
                return None, dict()

        # Checks
        if not ios_image_details:
            log.error("The SW PID was NOT found in either the 1) Cesium DB or the 2) Local Manifest.")
            return None, dict()
        if not ios_image_cesium['recovery']:
            log.debug("NOTICE: NO recovery image specified. Check IOS manifest for {0} to ensure this is correct.".format(ios_pid))
        if not ios_image_cesium['SR_pkgs']:
            log.debug("NOTICE: NO SR_pkgs specified. Check IOS manifest for {0} to ensure this is correct.".format(ios_pid))
        if not ios_image_cesium['hw_pid_owners']:
            log.debug("NOTICE: NO hw_pid_owners specified. Check IOS manifest for {0} to ensure this is correct.".format(ios_pid))

        # Print details
        log.debug("{0}".format(ios_pid))
        log.debug("-" * 50)
        for k, v in ios_image_details.items():
            log.debug("{0:<20} = {1}".format(k, v))

        return ios_pid, ios_image_details

    @func_details
    def _download_images(self, ios_sw_config, ios_supp_files, local_dir=''):
        """ Download IOS Images to the local server

        NOTE: The cesiumlib.sync_software_by_name(...) function will search in the following order:
              1. local Apollo server /tftpboot
              2. local/regional CSA's
              3. Central "swserver"
        NOTE2: Supplemental images are NOT available on the "swserver"; they must be loaded manually or
               via a separate process. A common_utils.download_image(...) function is given to help which
               allows Apollo servers within a local network to pull the images from a common Apollo server.

        Note: MUST get ALL SR packages for ALL IOS versions AVAILABLE to the product!
              This is why a static list is specified in the product definition.

        TODO: User case for IOS + Supp image downloading external to any product!

        :param (dict) ios_sw_config: Details of the SW config (source is combo of CNFw + IOS manifest).
                          Example: {
                          'product_id': 'S3650UK9-16-6SE',
                          'name': 'POLARIS',
                          'platforms': 'C9200',
                          'cco_location': '/auto/beyond.iosxe-4/16/bin/16.6.2/.3DES',
                          'image_name': 'cat9k_iosxe.16.06.02.SPA.bin',
                          'version': '16.6.2',
                          'md5': 'b8029e3339c1587c386e4cb907ba5daf',
                          'recovery': 'cat9k_caa-recovery.SPA.16.06.02.bin',
                          'SR_pkgs': []
                          }
        :param (dict) ios_supp_files: Other potential files needed in addition to the above config.
                          Example:
                              {8: [('S3850UK9-32-0SE', 'SR_pkgs'), ('S3850UK9-33SE', 'SR_pkgs')],
                               9: [('ANY', 'recovery')]},
         :param (obj) ios_manifest_module:
         :param (str) local_dir:
        :return:
        """
        if not ios_sw_config or not isinstance(ios_sw_config, dict):
            log.warning("IOS SW Config must be available and in dict form.")
            return False
        if not ios_sw_config.get('image_name', None):
            log.warning("No IOS main image name available.")
            return False

        ios_manifest = self._ud.ios_manifest

        result_list = []

        # TODO: User case for IOS + Supp image downloading external to any product!

        # IOS Main
        # --------
        log.debug("-" * 20)
        log.debug("IOS main files")
        cco_filepath = os.path.join(ios_sw_config.get('cco_location', ''), ios_sw_config['image_name'])
        local_filepath = os.path.join('/tftpboot', local_dir, ios_sw_config['image_name'])
        log.debug("CCO Filepath   = {0}".format(cco_filepath))
        log.debug("Local Filepath = {0}".format(local_filepath))
        # TODO: The SW download mechanisms are currently not working (per Bob Hakesly 3/1/2018)
        # status = cesiumlib.sync_software_by_name(ios_sw_config.get('image_name', ''), wait_for_result=True, timeout_minutes=15)
        status = common_utils.download_image(src_filepath=local_filepath, dst_filepath=local_filepath)
        log.info("IOS main image download Results: Status={0} Msg={1}".format(status.get('code', 0), status.get('message', '')))
        result_list.append(status.get('result', False))

        if not ios_supp_files:
            log.warning("NO supplemental files were specified. Please ensure this is correct per the product definition.")
            log.warning("NO additional files will be available.")
            return True

        # Supplemental images
        # -------------------
        log.debug("Supplemental files were specified for {0} : {1}.".format(ios_sw_config['product_id'], ios_supp_files))
        tracking_list = []
        for di, vlist in ios_supp_files.items():
            for swpid, kref in vlist:
                log.debug("-" * 20)
                log.debug('Supplemental Type={0} for SWPID={1}'.format(kref, swpid))
                if swpid == 'ACTUAL':
                    supp_sw_config = ios_manifest.get(ios_sw_config['product_id'], {}) if ios_manifest else {}
                else:
                    supp_sw_config = ios_manifest.get(swpid, {}) if ios_manifest else {}
                log.debug("supp_sw_config={}".format(supp_sw_config))
                supp_files = supp_sw_config.get(kref, [])
                supp_files = [supp_files] if supp_files and not isinstance(supp_files, list) else supp_files
                for supp_file_item in supp_files:
                    supp_file = supp_file_item[0] if isinstance(supp_file_item, tuple) else supp_file_item
                    cco_filepath = os.path.join(supp_sw_config.get('cco_location', ''), supp_file)
                    local_filepath = os.path.join('/tftpboot', local_dir, supp_file)
                    log.debug("CCO Filepath   = {0}".format(cco_filepath))
                    log.debug("Local Filepath = {0}".format(local_filepath))
                    tracking_list.append(supp_file)
                    status = common_utils.download_image(src_filepath=local_filepath, dst_filepath=local_filepath)
                    result_list.append(status.get('result', False))

        # Cross-check
        # -----------
        log.debug("-" * 20)
        log.debug("Cross-check with loaded SW Config...")
        # IOS recovery
        if ios_sw_config.get('recovery', None):
            rec_img = ios_sw_config['recovery'][0] if isinstance(ios_sw_config['recovery'], tuple) else ios_sw_config['recovery']
            if rec_img not in tracking_list:
                log.warning("IOS SW Config recovery image '{0}' was not part of the supplemental list.".format(rec_img))
                log.warning("Please check the product definition for the HW PID to ensure the image is identified if required.")
        # IOS SR Pkgs
        if ios_sw_config.get('SR_pkgs', None):
            for pkg in ios_sw_config['SR_pkgs']:
                if pkg not in tracking_list:
                    log.warning("IOS SW Config pkg image ({0}) was not part of the supplemental list.".format(ios_sw_config['SR_pkgs']))
                    log.warning("Please check the product definition for the HW PID to ensure all pkgs are identified.")

        return all(result_list)

    @func_details
    def get_ios_version(self):
        """ Get current IOS version from CLI

        Current IOS version can be found using show version in CLI, the sample output as below, the version is the one right
        before 'RELEASE SOFTWARE'.
        If no match is found, return False to indicate error to caller.

        Sample
        --------------------
        Switch>show ver | include Software
        Cisco IOS XE Software, Version 16.06.03
        Cisco IOS Software [Everest], Catalyst L3 Switch Software (CAT3K_CAA-UNIVERSALK9-M), Version 16.6.3, RELEASE SOFTWARE (fc8)

        --------------------

        :return current_ver:        (str) current IOS version, if it is found
                                    (bool) False, if current IOS version is not found
        """
        # IOS version search pattern
        ios_pattern = re.compile(r'Version (.+), RELEASE SOFTWARE')

        # get IOS version from CLI
        self._uut_conn.send('show version | include Software\n', expectphrase=self._uut_prompt, regex=True)
        match = ios_pattern.search(self._uut_conn.recbuf)
        if not match:
            log.error('FAILED. Cannot get IOS version from CLI')
            current_ver = False
        else:
            current_ver = match.group(1)
        log.info('Current IOS version is {}'.format(current_ver))

        return current_ver

    @func_details
    def verify_ios_version(self, target_version, ios_customer_pid):
        """ Verify the IOS version against the SW PID.
        :param target_version: Version read from IOS command line.
        :param ios_customer_pid: The SW PID being ordered by the customer
        :param ios_manifest_module: Local manifest
        :return:
        """
        if not target_version:
            log.error("Must have a version to check.")
            return False
        ios_pid, ios_image_details = self._get_image_config(ios_customer_pid=ios_customer_pid)
        if not ios_image_details:
            log.error("Cannot retrieve image details for SW PID = {0}".format(ios_customer_pid))
            return False
        reference_version = ios_image_details.get('version', None)

        # Use common_utils.is_version_greater to deal with version number preceded with 0,
        # 16.05.01a vs 16.5.1a, this consider a match
        # greater 2-ways with inclusive means equal
        if not (common_utils.is_version_greater(target_version, reference_version) and
                common_utils.is_version_greater(reference_version, target_version)):
            log.error("*" * 40)
            log.error("IOS VERSION MISMATCH!")
            log.error("Target Version = {0}".format(target_version))
            log.error("SW PID Version = {0}".format(reference_version))
            log.error("*" * 40)
            return False
        else:
            log.info("IOS Version {0} matches SW PID {1}!".format(target_version, ios_customer_pid))
        return True

    # ------------------------------------------------------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def erase_nvram(self):
        """ erase NVRAM on device
        :return:
        """
        self._uut_conn.sende('write erase\r', expectphrase='confirm', regex=True)
        self._uut_conn.sende('y\r', expectphrase=self._uut_prompt, regex=True)
        return True

    @func_details
    def clear_ios_obfl(self, obfl_items=None):
        """ Clear IOS OBFL (Onboard Failure Logging) logging

        This method clears IOS OBFL logging defined by obfl_items.
        obfl_items must be a list (can be empty), and this should be defined in product definition, passed in from caller.
        This method uses obfl_items and clears every item in it.
        If obfl_items is not a list, returns False to caller to indicate error.

        :param obfl_items:          (list) items to be clear in OBFL (see product definition)
        :return:                    (bool) True if all items are cleared, otherwise False
        """
        # verify input
        if not isinstance(obfl_items, list):
            return False

        # clear items in obfl_items
        log.info('Clearing OBFL logging items: {}'.format(obfl_items))
        for item in obfl_items:
            log.debug('Clearing {}'.format(item))
            self._uut_conn.sende('clear logging {}\r'.format(item), expectphrase='confirm', regex=True)
            self._uut_conn.sende('y\r', expectphrase=self._uut_prompt, regex=True)

        return True

    @func_details
    def clear_ios_crashinfo_files(self, force=True, recursive=True):
        """ Clear IOS crashinfo

        This is part of IOS clean up step, it removes all files in crashinfo:.
        After removal there should be no file existing in crashinfo:, one exception for tracelog.

        :param force:               (bool) whether to remove files regardless, default True
        :param recursive:           (bool) whether to remove files recursively, default True

        :return:                    (bool) True if files are removed successfully, otherwise False
        """

        def __dir_crashinfo():
            self._uut_conn.sende('dir crashinfo:\r', expectphrase=self._uut_prompt, regex=True)
            ret = True if not re.search(r'No files in directory', self._uut_conn.recbuf) else False
            return ret

        # process inputs
        opt_force = '/force' if force else ''
        opt_recursive = '/recursive' if recursive else ''

        # initialize output
        ret = True

        # check crashinfo: for existing files
        self._uut_conn.sende('terminal length 0\r', expectphrase=self._uut_prompt, regex=True)
        if __dir_crashinfo():
            log.info('File exists in crashinfo:')
            self._uut_conn.sende('delete {0} {1} crashinfo:\r'.format(opt_force, opt_recursive),
                           expectphrase=self._uut_prompt, regex=True)
            year = datetime.now().year
            if __dir_crashinfo():
                # Tracelog files get generated automatically; one file is ok due to recent activity.
                self._uut_conn.sende('dir crashinfo: | count {}\r'.format(year), expectphrase=self._uut_prompt, regex=True)
                match = re.search('Number of lines which match regexp = (\d+)', self._uut_conn.recbuf)
                line_qty = int(match.group(1)) if match else 0
                log.debug('line_qty = {}'.format(line_qty))
                if line_qty == 1:
                    self._uut_conn.sende('dir crashinfo: | count tracelogs\r', expectphrase=self._uut_prompt, regex=True)
                    match = re.search('Number of lines which match regexp = (\d+)', self._uut_conn.recbuf)
                    line_qty = int(match.group(1)) if match else 0
                    ret = True if line_qty == 1 else False
                else:
                    ret = False
                    log.error('There are some files cannot be removed')
                    log.error(self._uut_conn.recbuf)
            else:
                log.info('All files are deleted in crashinfo:')

        return ret

    @func_details
    def clear_ios_startup_config(self):
        """ Clear IOS startup-config
        :return: (bool) True
        """
        # TODO: Do we need to worry about SLR here?
        self._uut_conn.sende('erase startup-config\r', expectphrase='confirm', regex=True)
        self._uut_conn.sende('y\r', expectphrase=self._uut_prompt, regex=True)

        return True

    @func_details
    def set_eman_port_config(self, **kwargs):
        """
        Switch(config)#int gig0/0
        Switch(config-if)#ip addr 10.1.2.1 255.255.0.0


        Switch#ping vrf Mgmt-vrf ip 10.1.2.1
        Type escape sequence to abort.
        Sending 5, 100-byte ICMP Echos to 10.1.2.1, timeout is 2 seconds:
        !!!!!
        Success rate is 100 percent (5/5), round-trip min/avg/max = 1/1/1 ms


        Switch#sh run int gig0/0
        Building configuration...

        Current configuration : 126 bytes
        !
        interface GigabitEthernet0/0
         vrf forwarding Mgmt-vrf
         ip address 10.1.2.100 255.255.0.0
         speed 1000
         negotiation auto
        end

        :return:
        """

        # Inputs
        eman_interface = kwargs.get('eman_interface', self._ud.uut_config.get('eman_interface', 'gig0/0'))
        tftp_server = kwargs.get('tftp_server', self._ud.uut_config.get('server_ip', None))
        uut_ip = kwargs.get('uut_ip', self._ud.uut_config.get('uut_ip', None))
        netmask = kwargs.get('netmask', self._ud.uut_config.get('netmask', None))
        if not tftp_server or not netmask:
            log.error("Cannot set the eman port.")
            return False

        if not self._mode_mgr.goto_mode('IOSECFG'):
            log.error("Cannot enter IOS Config mode.")
            return None

        # Configure
        uut_prompt_cfg = self._uut_prompt_map['IOSECFG']
        uut_prompt_cfg_if = '[sS]witch\(config-if\)#'
        self._uut_conn.send('\r', expectphrase=uut_prompt_cfg, regex=True, timeout=30)
        self._uut_conn.send('int {0}\r'.format(eman_interface), expectphrase=uut_prompt_cfg_if, regex=True, timeout=30)
        self._uut_conn.send('ip addr {0} {1}\r'.format(uut_ip, netmask), expectphrase=uut_prompt_cfg_if, regex=True, timeout=30)
        self._uut_conn.send('vrf forwarding Mgmt-vrf\r', expectphrase=uut_prompt_cfg_if, regex=True, timeout=30)
        self._uut_conn.send('shut\r', expectphrase=uut_prompt_cfg_if, regex=True, timeout=30)
        self._uut_conn.send('no shut\r', expectphrase=uut_prompt_cfg_if, regex=True, timeout=30)
        self._uut_conn.send('exit\r', expectphrase=uut_prompt_cfg, regex=True, timeout=30)
        self._uut_conn.send('ip tftp source-interface {0}\r'.format(eman_interface), expectphrase=uut_prompt_cfg, regex=True, timeout=30)
        if not self._mode_mgr.goto_mode('IOSE'):
            log.error("Cannot return to IOS Enable mode.")
            return False
        time.sleep(1.0)

        # Check config
        self._uut_conn.send('sh run int {0}\r'.format(eman_interface), expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
        time.sleep(2.0)
        m = parse.parse("{x1:0}vrf forwarding {vpn:1} {x2:2}", self._uut_conn.recbuf)
        vpn = m.named.get('vpn', None) if hasattr(m, 'named') else None
        if not vpn:
            log.warning("The EMan Port has no VPN name for VRF.")
            ping_param = ''
        else:
            vpn = vpn.strip()
            log.debug("EMan Port VPN = {0}".format(vpn))
            ping_param = ' vrf {0}'.format(vpn)

        log.debug("Wait for EMan port (10 secs)...")
        time.sleep(10.0)
        ping_rate, try_cnt = 0, 0
        while ping_rate != 100 and try_cnt < 10:
            try_cnt += 1
            log.debug("Ping attempt = {0}".format(try_cnt))
            self._uut_conn.send('ping{0} ip {1}\r'.format(ping_param, tftp_server), expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
            time.sleep(3.0)
            m = parse.parse("{x1:0}Success rate is {ping:1} percent {x2:2}", self._uut_conn.recbuf)
            ping_rate = int(m.named.get('ping', 0)) if hasattr(m, 'named') else 0
            log.debug("Ping rate = {0}".format(ping_rate))

        return True if ping_rate > 0 else False

    @func_details
    def verify_log_for_error(self, search_patterns=None, err_patterns=None):
        """ Verify LOG to ensure no error displayed

            :NOTE1 : this method assumes UUT in IOSE mode

        Show log in IOS and search for error patterns, all error patterns will be converted to regex compile obj to use in
        this func. If no search_patterns is given

        :param search_patterns:     (str/list) search phrase to use when show log, could be str or list of str
        :param err_patterns:        (str/list) error patterns, could be str or re.compile or list of str/re.compile


        :return:                    (bool) True if nothing is found in IOS log
                                           False otherwise
        """
        search_patterns = search_patterns if isinstance(search_patterns, list) else [search_patterns]
        err_patterns = err_patterns if isinstance(err_patterns, list) else [err_patterns]
        regex_err_patterns = []
        for item in search_patterns:
            if not isinstance(item, str):
                log.error('Search patterns are in wrong format, must be str')
                return False
        for item in err_patterns:
            if not isinstance(item, str) and not isinstance(item, type(re.compile(''))):
                log.error('Error patterns are in wrong format, must be str or re.compile()')
                return False
            else:
                regex_err_patterns.append(re.compile(item)) if isinstance(item, str) else regex_err_patterns.append(item)

        ret = True

        for phrase in search_patterns:
            self._uut_conn.sende('show log | inc {0}\r'.format(phrase), expectphrase=self._uut_prompt, regex=True)
            log.info('Showing log with {0}'.format(phrase))
            for err_pattern in regex_err_patterns:
                log.info('Searching log for error pattern [{0}]'.format(err_pattern.pattern))
                if err_pattern.search(self._uut_conn.recbuf):
                    ret = False
                    log.error('Detects {0} when searching {1}'.format(err_pattern.pattern, phrase))
                else:
                    log.info('No error pattern [{0}] is detected'.format(err_pattern.pattern))

        return ret

    # ----------------------------------------------------------------------------------------------------------------------
    # Licenses RTU
    # ----------------------------------------------------------------------------------------------------------------------
    @func_details
    def _install_rtu_license(self, license, ios_version, apcount=0, retry=5):
        """ Install RTU (right-to-use) license

        This method takes licenses list as input and install RTU license to UUT base on license PID.
         If installation is not successful, it retries 5 times as default. This has to be executed in IOSE mode.

        :param license:         (str) license SKU
                            Ex: LIC-LAN-BASE-L, LIC-IP-BASE-S, LIC-IP-SRVCS-S
        :param ios_version:     (str) IOS version
                            Ex: 16.6.3
        :param apcount:        (int) AP count quantity
        :param retry:           (int) how many retries before fail for install cmd, default 5

        :return:                (bool)True if install successfully, otherwise False
        """
        def _pre_steps():
            """ Pre steps prior to license installation

            Some extra commands prior to license installation base on IOS version

            :return:
            """
            if common_utils.is_version_greater(ios_version, '16.8'):
                self._uut_conn.sende('configure terminal\r', expectphrase='(config)#')
                self._uut_conn.sende('service internal\r', expectphrase='(config)#')
                self._uut_conn.sende('end\r', expectphrase=self._uut_prompt, regex=True)
                self._uut_conn.sende('write\r', expectphrase=self._uut_prompt, regex=True)
            else:
                pass

        ret = False
        error_pattern = re.compile(r'Invalid|not responding|unavailable')
        major_ver = int(ios_version.split('.')[0])

        # Get rtu_feature
        lic_feature = license_utils.get_license_feature(license, license_type='RTU')
        if not lic_feature:
            log.error('Unrecognized RTU license SKU {0}'.format(license))
            return ret

        # IOS version greater than 16.8 uses a new cmd
        if common_utils.is_version_greater(ios_version, '16.8'):
            lic_inst_cmd = 'request platform software factory-license'
        else:
            lic_inst_cmd = 'license right-to-use factory-default'

        # For IOS version other than 11.x or 16.x with apcount, initilize apcount with apcount_init
        if (apcount == 0 and major_ver == 16) or (major_ver == 11):
            lic_inst_cmd = '{0} {1}\r'.format(lic_inst_cmd, lic_feature)
        else:
            lic_inst_cmd = '{0} {1} apcount {2}\r'.format(lic_inst_cmd, lic_feature, apcount)

        # Send cmd to install license, retry 5 times
        _pre_steps()
        while retry > 0:
            retry -= 1
            self._uut_conn.sende(lic_inst_cmd, expectphrase=self._uut_prompt, regex=True)
            if not error_pattern.search(self._uut_conn.recbuf):
                ret = True
                break

        return ret

    @func_details
    def _default_license_verification(self, license_pid=None, ios_version=None, license_type=None):
        """ Verify Default License

        ex:
        Switch#show license right-to-use default
        Slot#       License Name         Type
        -------------------------------------
            1            lanbase    Permanent
        -------------------------------------

        ex:
        Switch#show license right-to-use default
        Slot#       License Name         Type  Count
        --------------------------------------------
            1  network-advantage    Permanent    N/A
            1      dna-advantage Subscription    N/A
            1            apcount         base      0
        --------------------------------------------

        :param (str) license_pid: License PID    ex: 'LIC-IP-BASE-S'
        :param (str) ios_version: IOS version    ex: '16.6.4'
        :param (str) license_type: License type, either 'RTU' or 'DNA'
        :return:
        """
        if license_type is not 'RTU' and license_type is not 'DNA':
            log.error('Param license_type must be either "DNA" or "RTU", input is {0}'.format(license_type))
            return False

        license_req = license_utils.get_license_feature(license_pid, license_type=license_type)
        log.info('Required license type is {0}'.format(license_req))

        ret = True
        self._uut_conn.sende('show license right-to-use default\r', expectphrase=self._uut_prompt, regex=True)
        if license_req:
            lic_detail = license_utils.get_license_detail(lic_feature=license_req, license_type=license_type)
            for item in lic_detail:
                pattern = '{0}\s*?{1}'.format(item.get('name'), item.get('type'))
                if not re.search(pattern, self._uut_conn.recbuf):
                    log.error('{0} license {1}-{2} info is not found'.format(license_type, item.get('name'), item.get('type')))
                    ret = False
                else:
                    log.info('{0} license {1}-{2} is found'.format(license_type, item.get('name'), item.get('type')))
        else:
            # Check if there is any RTU license installed, fail if yes
            lic_detail = license_utils.get_license_detail(lic_feature=license_req, license_type=license_type, all_levels=True)
            for item in lic_detail:
                pattern = '{0}\s*?{1}'.format(item.get('name'), item.get('type'))
                if re.search(pattern, self._uut_conn.recbuf):
                    log.error('{0} license {1}-{2} info is found, which should NOT be installed'.format(license_type, item.get('name'), item.get('type')))
                    ret = False
                else:
                    log.info('{0} license {1}-{2} is not found'.format(license_type, item.get('name'), item.get('type')))

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Licenses DNA
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _install_dna_license(self, license, ios_version, apcount=0, retry=5):
        """ Install DNA license

        This method takes licenses list as input and install DNA license to UUT base on license PID.
         If installation is not successful, it retries 5 times as default. This has to be executed in IOSE mode.

        :param license:         (str) license SKU
                            Ex: C9300-48-DNA-E
        :param ios_version:     (str) IOS version
                            Ex: 16.6.3
        :param apcount:        (int) AP count quantity
        :param retry:           (int) how many retries before fail for install cmd, default 5

        :return:                (bool)True if install successfully, otherwise False
        """
        def _pre_steps():
            """ Pre steps prior to license installation

            Some extra commands prior to license installation base on IOS version

            :return:
            """
            if common_utils.is_version_greater(ios_version, '16.7'):
                self._uut_conn.sende('configure terminal\r', expectphrase='(config)#')
                self._uut_conn.sende('service internal\r', expectphrase='(config)#')
                self._uut_conn.sende('license boot level network-{0} addon dna-{0}\r'.format(lic_feature), expectphrase='(config)#')
                self._uut_conn.sende('end\r', expectphrase=self._uut_prompt, regex=True)
                self._uut_conn.sende('write\r', expectphrase=self._uut_prompt, regex=True)
            else:
                pass

        error_pattern = re.compile(r'Invalid|not responding|unavailable')
        ret = False
        # get lic_feature
        lic_feature = license_utils.get_license_feature(license, license_type='DNA')
        # if no lic_feature is defined, return False to caller to indicate error
        if not lic_feature:
            log.error('No DNA feature is defined in {0}'.format(license))
            return ret
        if not common_utils.is_version_greater(ios_version, '16'):
            log.error('Subscription license is supported only with IOS version greater than 16.')
            return ret
        now = datetime.now()
        # Default 3 year subscription, a placeholder, doesn't matter
        subscr_date = '{:d}-{:02d}-{:02d}'.format(now.year + 3, now.month, now.day)

        if common_utils.is_version_greater(ios_version, '16.7'):
            apcount_str = 'apcount {0}'.format(apcount) if apcount else ''
            lic_inst_cmd = 'request platform software factory-license network-{0} addon dna-{0} subscription {1}\r'.format(lic_feature, apcount_str)
        elif common_utils.is_version_greater(ios_version, '16.6'):
            lic_inst_cmd = 'license right-to-use factory-default network-{0} addon dna-{0} subscription\r'.format(lic_feature)
        else:
            lic_inst_cmd = 'license right-to-use factory-default network-{0} addon dna-{0} subscription {1}\r'.format(lic_feature, subscr_date)

        # send cmd to install license, retry 5 times
        _pre_steps()
        while retry > 0:
            retry -= 1
            # Must use send instead of sende due to echo issue for long cmd in IOS
            self._uut_conn.send(lic_inst_cmd, expectphrase=self._uut_prompt, regex=True)
            if not error_pattern.search(self._uut_conn.recbuf):
                ret = True
                break

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    # Licenses SLR
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def _get_slr_request_code(self):
        """ Get SLR Request Code

        This function will Retrieve a "REQUEST CODE" from the UUT.
        Requires IOS config setup prior to request.

        Sample command sequence:

        Setup
        -----
        Switch#config t
        Switch(config)#service internal
        Switch(config)#license smart enable
        . . .
        Switch(config)#license smart reservation
        Switch(config)#exit

        First time
        ----------
        Switch#license smart reservation request local
        Enter this request code in the Cisco Smart Software Manager portal:
        CB-ZC9300-24UX:FCW2134L0RN-AK9A6sMTr-86
        Switch#

        Subsequent request AFTER a successful auth code installation
        ------------------------------------------------------------
        Switch#license smart reservation request local
        Already registered
        Switch#

        Resv Return (allows a new reservation)
        --------------------------------------
        Switch#license smart reservation return local
        This command will remove the license reservation authorization code and the device will transition back to the unregistered state.
        Some features may not function properly.
        Do you want to continue? [yes/no]: y
        Enter this return code in Cisco Smart Software Manager portal:
        ChWhde-okvz5f-ckFy8a-aSx4AK-Qf1iFZ-WXYaP1-wwDwmB-K5SEWq-rbr
        Switch#

        NOTE: The "license smart mfg" is a special command mode that expects "no license smart reservation" (i.e. do NOT enable reservation).
        :return:
        """
        if not self._mode_mgr.goto_mode('IOSECFG'):
            log.error("Cannot enter IOS Config mode.")
            return None
        self._uut_conn.send('\r', expectphrase=self._uut_prompt_map['IOSECFG'], regex=True, timeout=30)
        self._uut_conn.send('service internal\r', expectphrase=self._uut_prompt_map['IOSECFG'], regex=True, timeout=30)
        if not self._mode_mgr.goto_mode('IOSE'):
            log.error("Cannot return to IOS Enable mode.")
            return None

        try_cnt = 0
        response = None
        while response != 'GOOD' and try_cnt < 4:
            try_cnt += 1
            log.debug("License attempt {0}".format(try_cnt))
            self._uut_conn.send('\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
            self._uut_conn.send('license smart mfg reservation request\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
            time.sleep(3.0)
            response = self._uut_conn.recbuf.splitlines()[1].rstrip('\r\n ')
            req_code = None
            if 'Already registered' in response:
                log.warning("Already registered.")
                self._mode_mgr.goto_mode('IOSECFG')
                self._uut_conn.send('license smart reservation\r', expectphrase=self._uut_prompt_map['IOSECFG'], regex=True, timeout=30)
                self._mode_mgr.goto_mode('IOSE')
                self._uut_conn.send('license smart reservation return local\r', expectphrase='continue?', regex=True, timeout=30)
                # self._uut_conn.send('license smart mfg reservation cancel\r', expectphrase='continue?', regex=True, timeout=30)
                self._uut_conn.send('yes\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
                time.sleep(3.0)
                return_code = self._uut_conn.recbuf.splitlines()[2].rstrip('\r\n ')
                log.debug("Return code = '{0}'".format(return_code))
                self._mode_mgr.goto_mode('IOSECFG')
                self._uut_conn.send('no license smart reservation\r', expectphrase=self._uut_prompt_map['IOSECFG'], regex=True, timeout=30)
                self._mode_mgr.goto_mode('IOSE')
            elif 'Enter this request code' in response:
                log.debug("Request code was generated.")
                req_code = self._uut_conn.recbuf.splitlines()[2].rstrip('\r\n ')
                response = 'GOOD'
            else:
                log.debug("Unknown response: '{0}'".format(response))

        log.info("SLR Request Code = '{0}'".format(req_code))
        return req_code

    @func_details
    def _pull_slr_auth_codes(self, reservation_request_code, **kwargs):
        """ Pull SLR Auth Codes

        Use the cesiumlib service to obtain the "AUTHORIZATION CODE" based on LineID/Customer Acct.
        The authorization code is in XML form and MUST be saved to a file.
        (It is too long to use directly in the CLI for installation.)

        :param (str) reservation_request_code: Code from IOS CLI on a per UUT basis.
                                               Example: "CB-ZC9300-48UXM:FCW2130G0NH-AK9A6sMTr-BF"
        :param (**dict) kwargs:
                        (str) tftp_auth_code_subdir: Typically a dir under the /tftpboot dir.
                        (int) major_line_id: Reference number to sales order; contains lots of data describing content of order.
                        (str) serial_number: UUT system serial number as seen by the customer.
                        (str) product_id: Top-level PID of the system.
                        (list) license_sku_qty: List of dicts of form [{'sku': '<SW Lic PID>', 'quantity': <int>}, ...] (data from LineID)
                                                Example: [{'sku': 'C9300-48-DNAE-T', 'quantity': 1}]
                        (str) license_pattern: Regex pattern to search for licenses in the LineID data
        :return (str, bool, str): auth_code_xml, auth_code_required, auth_code_filepath
        """
        @cesium_srvc_retry
        def generate_slr(major_line_id, serial_number, product_id, license_sku_qty, reservation_request_code):
            return cesiumlib.generate_slr(major_line_id=major_line_id,
                                          serial_number=serial_number,
                                          product_id=product_id,
                                          license_sku_qty=license_sku_qty,
                                          reservation_request_code=reservation_request_code)


        if not self._mode_mgr:
            log.error("Cannot continue without Machine Manager.")
            return None, None, None

        # Inputs
        tftp_auth_code_subdir = kwargs.get('tftp_auth_code_subdir', 'SLR')
        major_line_id = kwargs.get('major_line_id', 0)
        serial_number = kwargs.get('serial_number', self._ud.uut_config.get('SYSTEM_SERIAL_NUM', self._ud.uut_config.get('SERIAL_NUM', None)))
        product_id = kwargs.get('product_id', self._ud.uut_config.get('CFG_MODEL_NUM', self._ud.uut_config.get('MODEL_NUM', None)))
        license_sku_qty = kwargs.get('license_sku_qty', [])
        license_pattern = kwargs.get('license_pattern', '(?:^.*?-DNA.*$)')
        if not license_sku_qty:
            log.debug("Pulling license SKUs...")
            license_sku_qty, _, license_class = self._get_sw_licenses(major_line_id=major_line_id, license_pattern=license_pattern)

        # Sanity Check
        if not major_line_id or not isinstance(major_line_id, int) or major_line_id < 1000:
            log.error("Major LineID is missing or invalid.")
            return None, None, None
        if not common_utils.validate_sernum(serial_number, silent=True):
            log.error("Serial Number is invalid.")
            return None, None, None
        if not common_utils.validate_pid(product_id, silent=True):
            log.error("Product ID (PID) is invalid.")
            return None, None, None
        if not license_sku_qty or not isinstance(license_sku_qty, list) or not all([isinstance(i, dict) for i in license_sku_qty]):
            log.error("License SKU Quantity is missing or invalid.")
            return None, None, None

        log.debug("=" * 100)
        log.debug("SLR Details")
        log.debug("Major LineID          = {0}".format(major_line_id))
        log.debug("Serial Number         = {0}".format(serial_number))
        log.debug("Product ID            = {0}".format(product_id))
        log.debug("License SKU Qty       = {0}".format(license_sku_qty))
        log.debug("License Class         = {0}".format(license_class))
        log.debug("SLR Request Code      = {0}".format(reservation_request_code))
        log.debug("-" * 50)
        # Perform Cesium SLR request
        auth_code_xml, auth_code_required = generate_slr(major_line_id, serial_number, product_id, license_sku_qty, reservation_request_code)
        log.info("SLR Auth Code (xml)    = '{0}'".format(auth_code_xml))
        log.info("SLR Auth Code Required = '{0}'".format(auth_code_required))

        # Save Auth code to file
        tftp_auth_code_path = os.path.join('/tftpboot', tftp_auth_code_subdir)
        if not os.path.exists(tftp_auth_code_path):
            log.debug("Making subdirs: {0} ...".format(tftp_auth_code_path))
            os.makedirs(tftp_auth_code_path)
        auth_code_file = 'AC_{0}.xml'.format(serial_number)
        auth_code_filepath = os.path.join(tftp_auth_code_path, auth_code_file)
        log.info("AuthCode File Path    = {0}".format(auth_code_filepath))
        log.debug("=" * 100)
        if os.path.exists(auth_code_filepath):
            log.debug("A previous authcode file already exists and will be replaced.")
            os.remove(auth_code_filepath)
        if not common_utils.writefiledata(auth_code_filepath, auth_code_xml, force_raw=True):
            log.error("SLR file write failed.")
            return None, None, None

        auth_code_required_bool = True if auth_code_required.lower() == 'yes' else False
        return auth_code_xml, auth_code_required_bool, auth_code_filepath

    @func_details
    def _install_slr_auth_code(self, auth_code_filepath, **kwargs):
        """ Install SLR Authorization Code

        The installation method can be done in 2 ways:
            1. XML file saved to flash and then installed (LOCAL)
            2. tftp the XML file directly (REMOTE)

        Installation uses an IOS cli.
        Some early test versions of IOS require a "dev-cert" mode to be enabled -- do not use for production.

        Example CLI:

        Pre-setup
        ---------
        Cert Mode
        Switch#test license smart dev-cert ?
            Disable  Dev-cert Disable /Production Certifcate Enable
            Enable   Dev-cert Enable
        Switch#test license smart dev-cert enable

        GOOD (local file)
        -----------------
        Switch#license smart reservation install file flash:AC_FCW2134L0RN.xml
        Reservation install file successful
        Last Confirmation code 17488c1f
        Switch#
        *May  9 21:39:42.799: %SMART_LIC-6-EXPORT_CONTROLLED: Usage of export controlled features is Not Allowed for udi PID:C9300-24UX,SN:FCW2134L0RN
        *May  9 21:39:42.799: %SMART_LIC-6-AGENT_REG_SUCCESS: Smart Agent for Licensing Registration with the Cisco Smart Software Manager or satellitefor udi PID:C9300-24UX,SN:FCW2134L0RN
        *May  9 21:39:42.799: %SMART_LIC-6-AUTH_RENEW_SUCCESS: Authorization renewal with the Cisco Smart Software Manager or satellite. State=authorized for udi PID:C9300-24UX,SN:FCW2134L0RN
        *May  9 21:39:42.799: %SMART_LIC-6-RESERVED_INSTALLED: Specific License Reservation Authorization code installed for udi PID:C9300-24UX,SN:FCW2134L0RN
        *May  9 21:39:42.810: %SMART_LIC-3-NOT_AUTHORIZED: The entitlement regid.2017-03.com.cisco.advantagek9,1.0_bd1da96e-ec1d-412b-a50e-53846b347d53 in Not Authorized to be used. Reason: License not present in SLR auth code

        GOOD (Remote file)
        ------------------
        Switch#license smart reservation install file tftp://10.1.2.1/SLR/FCW2130G0NH.xml
        Loading SLR/AuthCode_C9300-48UXM_FCW2130G0NH.xml from 10.1.2.1 (via GigabitEthernet0/0): !
        [OK - 1335 bytes]
        ASR1000-WATCHDOG: Process = Exec

        BAD
        ---
        Switch#license smart reservation install file flash:AC_FCW2134L0RN.xml
        Reservation install file failed: The Reservation Authorization Code does not match the Reservation Request Code

        :param (str) auth_code_filepath: File name and path from the tftp server relative location.
                                         Example: "SLR/FCW2130G0NH.xml"
        :param (**dict) kwargs:
                        (str) tftp_server: Host IP of tftp server holding the xml file.
                        (str) install_loc: LOCAL | REMOTE
                        (str) cert_mode: DEV | PROD
        :return (bool): True if successful
        """

        # TODO: XML authcode remains in flash for customer?  Is this ok?

        if not self._mode_mgr:
            log.error("Cannot continue without Mode Manager.")
            return False

        # Inputs
        if not auth_code_filepath:
            log.error("Need Auth Code remote file and path.")
        tftp_server = kwargs.get('tftp_server', self._ud.uut_config.get('server_ip', None))
        install_loc = kwargs.get('install_loc', 'LOCAL')
        cert_mode = kwargs.get('cert_mode', 'PROD')  # PROD or DEV

        # Process file name & path
        a = auth_code_filepath.split('/')
        auth_code_file = a[-1]
        a.pop(0) if a[0] == '' else None
        a.pop(0) if a[0] == 'tftpboot' else None
        auth_code_file_src = 'tftp://{0}'.format(os.path.join(tftp_server, '/'.join(a)))
        auth_code_file_dst = 'flash:{0}'.format(auth_code_file)
        log.debug("Auth Code File Src = {0}".format(auth_code_file_src))

        # Set pre-conditions
        if not self._mode_mgr.goto_mode('IOSE'):
            log.error("Cannot enter IOS Enable mode.")
            return False
        if not self.set_eman_port_config(tftp_server=tftp_server):
            return False
        if cert_mode == 'DEV':
            log.warning("*" * 100)
            log.warning("The Smart License Cert Mode = DEV")
            log.warning("THIS IS NOT FOR PRODUCTION!")
            log.warning("*" * 100)
            self._uut_conn.send('test license smart dev-cert enable\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=60)

        # Perform Install
        log.info("*** SLR Factory Installation starting...")
        self._uut_conn.send('\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=30)
        if install_loc == 'LOCAL':
            log.debug("LOCAL SLR install. (Requires TFTP copy to device.)")
            self._uut_conn.send('copy {0} {1}\r'.format(auth_code_file_src, auth_code_file_dst), expectphrase='.*', regex=True, timeout=30)
            time.sleep(2)
            self._uut_conn.send('\r', expectphrase='.*', regex=True, timeout=30) if 'Destination' in self._uut_conn.recbuf else None
            time.sleep(2)
            self._uut_conn.send('\r', expectphrase='.*', regex=True, timeout=30) if 'confirm' in self._uut_conn.recbuf else None
            self._uut_conn.waitfor('bytes copied', timeout=60)
            log.debug("Copy result: {0}".format(self._uut_conn.recbuf))
            self._uut_conn.send('license smart mfg reservation install file {0}\r'.format(auth_code_file_dst), expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=60)
        elif install_loc == 'REMOTE':
            log.debug("REMOTE SLR install.")
            self._uut_conn.send('license smart mfg reservation install file {0}\r'.format(auth_code_file_src), expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=60)
        else:
            log.error("Unknown install location: '{0}'".format(install_loc))
            return False

        # Check install response
        time.sleep(2.0)
        install_response = self._uut_conn.recbuf.splitlines()[1].strip('\r\n')
        log.debug("SLR Install response = {0}".format(install_response))
        if 'Reservation install file successful' in install_response and 'fail' not in install_response:
            log.info("Smart License Reservation: GOOD.")
            ret = True
        else:
            log.error("Smart License Reservation: FAILED!")
            ret = False

        return ret

    @func_details
    def verify_slr(self, license_sku_qty, **kwargs):
        """ Verify SLR

            Switch# show license all

            Smart Licensing Status
            ======================

            Smart Licensing is ENABLED
            License Reservation is ENABLED

            Registration:
              Status: REGISTERED - SPECIFIC LICENSE RESERVATION
              Export-Controlled Functionality: Not Allowed
              Initial Registration: SUCCEEDED on May 24 18:36:44 2018 UTC

            License Authorization:
              Status: NOT AUTHORIZED

            Licensing HA configuration error:
                Entitlement tags in active and standby does not match

            Utility:
              Status: DISABLED

            Data Privacy:
              Sending Hostname: yes
                Callhome hostname privacy: DISABLED
                Smart Licensing hostname privacy: DISABLED
              Version privacy: DISABLED

            Transport:
              Type: Callhome

            License Usage
            ==============

            (C9300_48P_NW_essentialsk9):
              Description:
              Count: 1
              Version: 1.0
              Status: NOT AUTHORIZED
              Reservation:
                Reservation status: SPECIFIC INSTALLED
                Total reserved count: 0

            C9300 48P DNA Essentials (C9300_48P_dna_essentials):
              Description: C9300 48P DNA Essentials
              Count: 0
              Status: NOT IN USE
              Reservation:
                Reservation status: SPECIFIC INSTALLED
                Total reserved count: 1

            Product Information
            ===================
            UDI: PID:C9300-48UXM,SN:FCW2130G0NH

            Agent Version
            =============
            Smart Agent for Licensing: 4.4.5_rel/71
            Component Versions: SA:(1_3_dev)1.0.15, SI:(dev22)1.2.1, CH:(rel5)1.0.3, PK:(dev18)1.0.3

            Reservation Info
            ================

            Overall status:
              Active: PID:C9300-48UXM,SN:FCW2130G0NH
                License reservation: ENABLED
                  Reservation status: SPECIFIC INSTALLED on Jan 01 00:00:00 1970 UTC
                  Export-Controlled Functionality: Not Allowed
                  Last Confirmation code: 110afa79

            Specified license reservations:
              C9300 48P DNA Essentials (C9300_48P_dna_essentials):
                Description: C9300 48P DNA Essentials
                Total reserved count: 1
                Term information:
                  Active: PID:C9300-48UXM,SN:FCW2130G0NH
                    License type: TERM
                      Start Date: 2019-JAN-15 UTC
                      End Date: 2019-JAN-15 UTC
                      Term Count: 1

        :param license_sku_qty:
        :param kwargs:
        :return:
        """
        if not self._mode_mgr:
            log.error("Cannot continue without Mode Manager.")
            return False
        if not self._mode_mgr.goto_mode('IOSE'):
            log.error("Cannot enter IOS Enable mode.")
            return False

        self._uut_conn.send('show license all\r', expectphrase=self._uut_prompt_map['IOSE'], regex=True, timeout=60)

        return

    # ------------------------------------------------------------------------------------------------------------------
    # Licenses APCOUNT
    # ------------------------------------------------------------------------------------------------------------------
    @func_details
    def install_apcount_license(self, apcount, ios_version):
        pass

    @func_details
    def _apcount_license_verification(self, apcount, ios_version):
        """ Verify AP Count License

        Look for apcount license and quantity in 'show license' dump.
        Skip check for IOS 16.5 and 16.6, inherite from AT code.

        :param (int) apcount: license quantity
        :param (str) ios_version: IOS version
        :return (bool): ret, True if apcount qty is correct, False otherwise
        """
        # TODO: skip apcount check for IOS 16.5/16.6, why???
        if common_utils.is_version_greater(ios_version, '16.5') and not common_utils.is_version_greater(ios_version, '16.7'):
            log.warning('AP count check is skipped for IOS ver {0}'.format(ios_version))
            return True

        ret = False
        pattern = r'apcount\s*?base\s*?{0}'.format(apcount)
        if common_utils.is_version_greater(ios_version, '16.9'):
            self._uut_conn.sende('show platform software factory license | include apcount\r', expectphrase=self._uut_prompt, regex=True)
        else:
            self._uut_conn.sende('show license right-to-use default | include apcount\r', expectphrase=self._uut_prompt, regex=True)

        # Look for 'apcount base 50' in dump
        if re.search(pattern, self._uut_conn.recbuf):
            log.info('AP count {0} is found'.format(apcount))
            ret = True
        elif apcount == 0:
            log.info('No AP count required, and it is not found in default license')
            ret = True

        return ret

    @func_details
    def _get_sw_licenses(self, major_line_id, major_line_id_cfg=None, top_level_product_id=None):
        """ Get SW Licenses

        Use the LineID OR the LineID data and PID to determine the SW licenses and qtys based on:
            1. RegEx pattern for SW License PIDs,
            2. Logic for License level defined by configured product PID

        The purpose for _get_sw_licenses() is to standardize license extraction and put it in a predictable & usable form
        for later processing by IOS routines that install these licenses.
        Both a "normalized" license list and the extracted list are returned along with a license class RTU, DNA, or SLR.

        LEGACY IOS LICENSES + Psuedo Ex:
            Note: These SW Lic PIDs don't exist; they are meant as placeholders for later processing
                  of IOS commands to set the LIC level.
            <Base PID>-L  = LAN Base        --> {'sku': 'LIC-LAN-BASE-L', 'quantity': 1}  C1 Bundle
                                                {'sku': 'LIC-LAN-BASE-L', 'quantity': 1}
            <Base PID>-E  = IP Base         --> {'sku': 'LIC-IP-BASE-E', 'quantity': 1}  C1 Bundle
                                                {'sku': 'LIC-IP-BASE-E', 'quantity': 1}
            <Base PID>-S  = IP Services     --> {'sku': 'LIC-IP-SRVCS-S', 'quantity': 1}  C1 Bundle
                                                {'sku': 'LIC-IP-SRVCS-S', 'quantity': 1}

        DNA IOS LICENSES + Ex:
            <Base PID>-E  = DNA Essentials  --> {'sku': 'C9300-48-DNAE-T', 'quantity': 1}  C1 Bundle
                                                {'sku': 'C9300-48-DNA-E', 'quantity': 1}
            <Base PID>-A  = DNA Advantage   --> {'sku': 'C9300-48-DNAA-T', 'quantity': 1}  C1 Bundle
                                                {'sku': 'C9300-48-DNA-A', 'quantity': 1}

        AP COUNT LICENSE + Ex:
            <Most PIDs>                     --> {'sku': 'LIC-CTIOS-1A', 'quantity': 10}
            <AIR-* PIDs>-1000               --> {'sku': 'LIC-CTIOS-1A', 'quantity': 1000}


        USAGE: The resulting list of dicts can be used in a standardized way to
            1. Install the license level (-L/E/S or -A/E)
            2. Install the AP Count (if applicable)
            3. Install SLR auth codes.


        Ex. of LineID Config data (SW License snippet of a DNA C1 Bundle):
        'config_data': [..., {
            'lineid'        = '1017068925',
            'level'         = '2',
            'ob_trans_id'   = '399645932',
            'atlinenum'     = '2',
            'qty'           = '1',
            'linenum'       = '23',
            'parent_lineid' = '1017068799',
            'prod_name'     = 'C1-C9300-48-DNAA-T'
            },...]

        :param (int) major_line_id:
        :param (dict) major_line_id_cfg: Actual LineID config data
        :param (str) top_level_product_id: Configured HW PID
        :return (list, list, str) sw_licenses_normalized, sw_licenses, lic_class:
                       Two lists of dicts for SW Licenses and qty, license class
                       Ex. [{'sku': 'C9300-48-DNA-E', 'quantity': 1}, {'sku': 'LIC-CTIOS-1A', 'quantity': 10}],
                           [{'sku': 'C9300-48-DNA-E', 'quantity': 1}, {'sku': 'LIC-CTIOS-1A', 'quantity': 10}],
                           'DNA'
        """
        IOS_SPECIAL_LIC_ADD = {
            '3.3': None,
            '3.6': None,
            '3.7': dict(sku='LIC-CTIOS-1A', quantity=1),
            '16.5': None,
            '16.6': None,
            '16.8': None,
            '16.9': None,
        }

        def _lic_in_normlicenses(lic):
            for lc in sw_licenses_normalized:
                if lc['sku'] == lic['sku']:
                    return True
            return False

        # Inputs
        if not major_line_id_cfg:
            log.debug("Getting Major LineID data...")
            major_line_id_cfg = cesiumlib.get_lineid_config(major_line_id=major_line_id)
        if not top_level_product_id:
            top_level_product_id = cesiumlib.get_lineid_toplevel_product_id(major_line_id_cfg).get('prod_name')
        if not top_level_product_id or not common_utils.validate_pid(top_level_product_id):
            log.error("Top-level PID is unspecified or has incorrect form!")
            log.error("Any inferred licenses CANNOT be determined.")
            log.error("Check the PID and Major LineID.")
        log.debug("Top-level PID = {0}".format(top_level_product_id))

        # Process the LineID and extract licenses
        sw_licenses = []
        sw_licenses_normalized = []
        ios_version = None
        lic_class = None
        for config_data_item in major_line_id_cfg.get('config_data', []):
            prod_name = config_data_item.get('prod_name', '')
            if prod_name == top_level_product_id:
                continue
            qty = int(config_data_item['qty']) if config_data_item.get('qty', None) else 0
            lic_dict = None
            # License
            if license_utils.is_dna_license(prod_name):
                lic_class = 'DNA'
                log.debug("Detected DNA License: {0}".format(prod_name))
                lic_dict = dict(sku=prod_name, quantity=qty)
            elif license_utils.is_rtu_license(prod_name):
                lic_pid = license_utils.is_rtu_license(prod_name)
                lic_class = 'RTU'
                log.debug("Detected RTU License: {0}".format(prod_name))
                lic_dict = dict(sku=lic_pid, quantity=qty)
            elif license_utils.is_apcount_license(prod_name):
                apcount = license_utils.is_apcount_license(prod_name)
                log.debug("Detected AP count License quantity {0} from {1}: {0}".format(apcount, prod_name))
                lic_dict = dict(sku=license_utils.apcount_sku, quantity=apcount)
            else:
                log.debug("Item: {0}".format(prod_name))

            if lic_dict and lic_dict not in sw_licenses:
                sw_licenses.append(lic_dict)
                sw_licenses_normalized.append(lic_dict)

            # IOS
            if config_data_item.get('image_version'):
                ios_version = config_data_item['image_version'] if not ios_version else ios_version

        # Special process for RTU (legacy) license inferences (i.e. those that are NOT in LineID!)
        if not lic_class:
            lic_pid = license_utils.is_rtu_license(top_level_product_id)
            if lic_pid:
                lic_class = 'RTU'
                log.debug("Detected RTU License {0} from top level PID: {1}".format(lic_pid, top_level_product_id))
                lic_dict = dict(sku=lic_pid, quantity=1)
                sw_licenses_normalized.append(lic_dict)

        # Special process for IOS specific versions
        for ver, lic in IOS_SPECIAL_LIC_ADD.items():
            if ios_version and ios_version[0:len(ver)] == ver:
                if lic and not _lic_in_normlicenses(lic):
                    log.info("Special IOS {0} provision for version {0}.".format(ver, ios_version))
                    log.info("Add lic: {0}".format(lic))
                    sw_licenses_normalized.append(lic)

        # in sw_licenses_normalized list, there should be only ONE item (except APCOUNT item)
        sw_licenses_normalized = license_utils.normalize_sw_licenses(sw_licenses_normalized)
        if sw_licenses_normalized is None:
            log.error('There is something wrong with licenses')

        log.info("License Data")
        log.info("-" * 100)
        log.info("IOS Version                   = {0}".format(ios_version))
        log.info("License Class                 = {0}".format(lic_class))
        log.info("All Licenses/Qty              = {0}".format(sw_licenses))
        log.info("All Licenses/Qty (Normalized) = {0}".format(sw_licenses_normalized))

        # Save to UUT Config
        self._ud.uut_config['sw_licenses'] = sw_licenses
        self._ud.uut_config['sw_licenses_normalized'] = sw_licenses_normalized
        self._ud.uut_config['lic_class'] = lic_class

        return sw_licenses_normalized, sw_licenses, lic_class

    # ------------------------------------------------------------------------------------------------------------------
    # Helper functions (INTERNAL)
    # ------------------------------------------------------------------------------------------------------------------
    def _clear_recbuf(self):
        if IOS.USE_CLEAR_RECBUF:
            self._uut_conn.clear_recbuf()
            time.sleep(IOS.RECBUF_CLEAR_TIME)
        return
