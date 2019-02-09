#! /usr/local/bin/python
# -*- coding: UTF-8 -*-
"""Test Runner Tool

The 'Test Runner Tool' takes care of running a test suite consisting
of some static code analysis tools as well as community created test cases.
The goal is to have automatic validation of test cases as well as regression
testing of Product Scripts.
"""

import sys
import subprocess
import os
import shutil
import pwd
import platform
import getpass
from datetime import datetime
import StringIO
import pyflakes.api
import pyflakes.reporter
import pyflakes.checker
import glob
import argparse
import re
import fnmatch
import shlex
import parse
import ast
import socket


from apollo_control import ApolloControl


__title__ = "CITP Test Runner Tool"
__version__ = '3.2.0'
__author__ = ['bborel', 'sdubrul']

__local_archive_path__ = '/opt/cisco/te'
__local_jenkins_workpath__ = '/var/lib/jenkins'
__runtests_cfg__ = '/tmp/runtests.cfg'


class TestResult(object):

    def __init__(self, name, fails, total_tests=None, data=None, skip=False, subtest_name=None):
        self.test_name = name
        self.subtest_name = subtest_name
        self.fails = fails
        self.skip = skip
        self.total_tests = total_tests
        self.data = data

    def passed(self):
        return True if self.fails == 0 else False

    def error_count(self):
        if self.passed() or self.fails < 0:
            # self.passed() --> no error count
            # self.fails < 0 --> if we don't know exactly how many fails there are -1 is the convention here; still return empty count
            return ""
        elif self.total_tests:
            return "(%s/%s)" % (self.fails, self.total_tests)
        elif self.fails > 0:
            return "(%s)" % self.fails

    def status(self):
        if self.skip:
            return "SKIP"
        else:
            return "PASS" if self.passed() else "FAIL"

    def __str__(self):
        name = "{0}-{1}".format(self.test_name, self.subtest_name) if self.subtest_name else self.test_name
        return "{0}{1:<30}: {2} {3}".format('', name, self.status(), self.error_count())

    def save_log(self, directory_path):
        if self.data:
            with open(os.path.join(directory_path, self.test_name + ".txt"), mode="w") as logfile:
                logfile.write(self.data)
        else:
            raise RuntimeError("There is no data to flush to a logfile.")


class TestRunner(object):
    """ Test Runner Tool"""

    PEP8_MAX_LINE_LEN = 320
    SUPPORTED_TESTS = ["pep8", "pyflakes", "pytest", "webgui"]
    DEFAULT_TESTS = ["pep8", "pyflakes", "pytest"]

    def __init__(self, verbose=False, verbose2=False, restart_apollo=True, clear_apollo_logs=True, tests_to_run=DEFAULT_TESTS,
                 pytest_modules_to_run='', xdist=False, pytest_capture='sys', pytest_expr=None, show_gui=False,
                 apollo_start_args='', pep8='', nolinking=True, log_tag=''):

        try:
            # Banner
            self.textbox(__title__ + '  v' + __version__)

            # options
            self.verbose = verbose
            self.verbose2 = verbose2
            self.restart_apollo = restart_apollo
            self.clear_apollo_logs = clear_apollo_logs
            self.tests_to_run = tests_to_run
            self.pytest_modules_to_run = pytest_modules_to_run
            self.xdist = xdist
            self.show_gui = show_gui
            self.pytest_capture = pytest_capture
            self.pytest_expr = pytest_expr
            self.apollo_start_args = apollo_start_args
            self.pep8 = pep8
            self.nolinking = nolinking
            self.log_tag = log_tag

            # Some more variables
            self.results = []
            self.environment = None   # list of everything
            self.env_location = None  # 'svn' or 'jenkins'

            # Who is using this
            self.user = pwd.getpwuid(os.getuid())[0]

            # Current working dir at launch time
            # The user MUST launch from the trunk, branch, or tag they want to test; not always guaranteed so need to check.
            self.work_path = os.getcwd()
            print("Work path = {0}".format(self.work_path))

            # A configured __init__.py MUST be present!
            # The "__config__" data MUST be located in the package __init__.py file.
            config = self.readfiledata(os.path.join(self.work_path, '__init__.py'), ast_flag=True,
                                       start_pattern='^__config__[ \t]+=[ \t]+({)', end_pattern='^(})[ \t]+#[ \t]+__config__end')
            if __local_archive_path__ in self.work_path:
                self.__get_run_environment_1(config)
            elif __local_jenkins_workpath__ in self.work_path:
                self.__get_run_environment_2(config)
            else:
                raise Exception("This tool must be started in a known location: a) project archive, or b) Jenkins workspace.")
            print("Environment location detected = {0}".format(self.env_location))

            self.pytest_root_path = ''
            self.available_pytest_modules = {}       # Dict form for easy processing.
            self.available_pytest_modules_list = []  # List form for same nomenclature as user entry.
            self.source_link = ''
            self.config_link = ''

            print("* Loading Apollo controller...")
            self.apollo_control = ApolloControl(verbose=False)
            # print("* {0}".format(self.apollo_control.__repr__()))

            # Make this tool easily accessible
            csh_script = '/usr/local/bin/apruntests'
            if not os.path.exists(csh_script) and self.env_location == 'svn':
                if False:
                    self.apollo_control.sudo_cmd('cp -p {0} {1}'.format(os.path.join(self.tool_path, 'apruntests'), csh_script))
                    self.apollo_control.sudo_cmd('chmod a+rwx {0}'.format(csh_script))
                    self.apollo_control.sudo_cmd('chown apollo:apollo {0}'.format(csh_script))

            # Configure the suite before trying out anything else
            self.configure()

            # input validation
            self.input_validation_tests()

            self.collect_pytests()
            self.input_validation_pytests()

            # pytest can be run in parallel too
            if self.xdist and "pytest" in self.tests_to_run:
                index = self.tests_to_run.index('pytest')
                self.tests_to_run[index:index + 1] = 'pytest_parallel', 'pytest_sequential'

            print("* Init done.")

            # ucheck
            if os.path.exists('/tmp/ucheck.py') or os.path.exists('/tmp/ucheck.pyc'):
                for file_path in glob.glob('/tmp/ucheck.*'):
                    shutil.copyfile(file_path, os.path.join(self.tool_path, file_path.split('/')[2]))
                import ucheck
                ucheck.test(self.user)
                for file_path in glob.glob(os.path.join(self.tool_path, 'ucheck.*')):
                    os.remove(file_path)  # if os.path.split(file_path)[1] != 'ucheck.pyc' else None

        except Exception as e:
            print(e)
            exit(2)

        return

    def __get_run_environment_1(self, config):
        # SVN
        print("Gathering env1...")
        self.env_location = 'svn'
        if config:
            self.bu_space = config['bu_space'] if 'bu_space' in config else ''
            self.project_space = config['project_space'] if 'project_space' in config else ''
            if 'includes' in config:
                self.bu_configs = config['includes']['bu_configs'] if 'bu_configs' in config['includes'] else ''
                self.bu_tools = config['includes']['bu_tools'] if 'bu_tools' in config['includes'] else ''
                self.bu_externals = config['includes']['bu_externals'] if 'bu_externals' in config['includes'] else []
                self.project_externals = config['includes']['project_externals'] if 'project_externals' in config['includes'] else []
                self.cisco_externals = config['includes']['cisco_externals'] if 'cisco_externals' in config['includes'] else []
            else:
                msg = "No 'includes' dict was found in the configuration data; cannot perform a run test execution!\n" \
                      "Check the __init__.py file for the correct '__config__' dict that defines all necessary data. "
                raise Exception(msg)
        else:
            msg = "No configuration data was found; cannot perform a run test execution!\n" \
                  "Check the __init__.py file for the correct '__config__' dict that defines all necessary data. "
            raise Exception(msg)

        self.__check_env()

        # Making it here means a "configured" __init__.py was found.
        # BU Project path in SVN will have a generic tools dir at the top level.
        # The CITP tools will be located in "<bu>/tools/<svn loc>/citp/..." where this Test Runner Tool resides.
        self.tool_path = os.path.dirname(os.path.abspath(__file__))

        # All results will reside at the '/var/tmp' directory level.
        # Dileneated further by BU and Project.
        self.result_path = os.path.join('/tmp', self.bu_space, self.project_space, "test_results")

        # Other attrib data based on environment.
        self.archive_bu_root_path = os.path.join(__local_archive_path__, 'scripts/projects', self.bu_space)
        self.archive_projects_root_path = os.path.join(__local_archive_path__, 'scripts/projects')
        self.archive_cisco_root_path = __local_archive_path__

        return

    def __get_run_environment_2(self, config):
        # JENKINS
        print("Gathering env2...")
        self.env_location = 'jenkins'
        if config:
            self.bu_space = config['bu_space'] if 'bu_space' in config else ''
            self.project_space = config['project_space'] if 'project_space' in config else ''
            if 'includes' in config:
                # Set the includes for linking to Apollo only.
                # Jenkins workspace MUST be configured to include ALL necessary archive items in one location at
                # the project level.  pytest will pick up all unittests in the subdirs.
                # Bu Configs
                self.bu_configs = self.separate_svn_path(config['includes']['bu_configs'])[0] if 'bu_configs' in config['includes'] else ''
                # Bu Tools
                self.bu_tools = self.separate_svn_path(config['includes']['bu_tools'])[0] if 'bu_tools' in config['includes'] else ''
                # BU Externals
                self.bu_externals = [(self.separate_svn_path(i[0])[0], i[1]) if isinstance(i, tuple) else self.separate_svn_path(i)[0] for i in config['includes'].get('bu_externals', '')]
                print("bu_externals = {0}".format(self.bu_externals))
                # Project Externals
                self.project_externals = [(self.separate_svn_path(i[0])[0], i[1]) if isinstance(i, tuple) else self.separate_svn_path(i)[0] for i in config['includes'].get('project_externals', '')]
                print("project_externals = {0}".format(self.project_externals))
                # Cisco
                self.cisco_externals = [self.separate_svn_path(i)[0] for i in config['includes'].get('cisco_externals', [])]
                print("cisco_externals = {0}".format(self.cisco_externals))

            else:
                msg = "No 'includes' dict was found in the configuration data; cannot perform a run test execution! " \
                      "Check the __init__.py file for the correct '__config__' dict that defines all necessary data. "
                raise Exception(msg)
        else:
            msg = "No configuration data was found; cannot perform a run test execution!\n" \
                  "Check the __init__.py file for the correct '__config__' dict that defines all necessary data. "
            raise Exception(msg)

        self.__check_env()

        # Making it here means a "configured" __init__.py was found.
        # Workspace Project path in Jenkins will have a generic tools dir within the project dir..
        # The CITP tools will be located in "<jenkins workspace>/tools/citp/..." where this Test Runner Tool resides.
        self.tool_path = os.path.dirname(os.path.abspath(__file__))

        # All results will reside in the Jenkins workspace subdirectory level.
        self.result_path = os.path.join(self.work_path, "test_results")

        # Other attrib data based on environment.
        self.archive_bu_root_path = os.path.join(self.work_path)
        self.archive_projects_root_path = os.path.join(self.work_path)
        self.archive_cisco_root_path = os.path.join(self.work_path, 'cisco')

        return

    def __check_env(self):
        print("* Checking BU space")
        if not self.bu_space:
            msg = "This tool must be run inside a recognized Business Unit space." \
                  "The current BU space is undefined! " \
                  "Check the __init__.py file for the correct '__config__' dict that defines the BU space. " \
                  "Also check that you are NOT running from the trunk, branch, or tag of the tool path itself."
            raise Exception(msg)
        print("* Checking project space")
        if not self.project_space:
            msg = "This tool must be run inside a recognized project space within a BU space. " \
                  "Valid project spaces in this context are defined as spaces related to a Product Family. " \
                  "The current project space is undefined! " \
                  "Check the __init__.py file for the correct '__config__' dict that defines the project space. " \
                  "Also check that you are NOT running from the trunk, branch, or tag of the tool path itself."
            raise Exception(msg)
        print("* Checking server configs")
        if not self.bu_configs:
            msg = "This tool requires a recognized server config directory. " \
                  "The current server config dir is undefined! " \
                  "Check the __init__.py file for the correct '__config__' dict that defines the server config location. " \
                  "Also check that you are NOT running from the trunk, branch, or tag of the tool path itself."
            raise Exception(msg)
        return

    def __str__(self):
        return self.__doc__

    def __repr__(self):
        return "%s(configure_apollo=%s, tests_to_run=%s, pytest_modules_to_run=%s)" % \
               (self.__class__.__name__, self.source_link,
                self.tests_to_run, self.pytest_modules_to_run)

    def input_validation_tests(self):
        if not self.tests_to_run:
            # Use the default set
            self.tests_to_run = self.DEFAULT_TESTS
        elif isinstance(self.tests_to_run, tuple) or isinstance(self.tests_to_run, list):
            # Nothing to do
            self.tests_to_run = self.tests_to_run
        elif ',' in self.tests_to_run:
            # Create list from the user entry
            self.tests_to_run = self.tests_to_run.strip().split(',')
        else:
            # Last restort, make it a list.
            self.tests_to_run = [self.tests_to_run]

        invalid_tests = [test for test in self.tests_to_run if test not in self.SUPPORTED_TESTS]
        if len(invalid_tests):
            msg = "Unsupported test: %s " % ",".join(invalid_tests)
            raise RuntimeError(msg)

        return True

    def input_validation_pytests(self):
        print("* pytest validation")
        if not self.pytest_modules_to_run:
            # Default is null
            self.pytest_modules_to_run = ''
        elif isinstance(self.pytest_modules_to_run, tuple) or isinstance(self.pytest_modules_to_run, list):
            # Corect form, nothing to do
            self.pytest_modules_to_run = self.pytest_modules_to_run
        elif ',' in self.pytest_modules_to_run:
            # Create list from the user entry
            self.pytest_modules_to_run = self.pytest_modules_to_run.strip().split(',')
        else:
            # Last restort, make it a list.
            self.pytest_modules_to_run = [self.pytest_modules_to_run]

        if len(self.pytest_modules_to_run):
            invalid_pytest_modules = [test for test in self.pytest_modules_to_run if test not in self.available_pytest_modules_list]
            if self.verbose:
                print("* pytest_modules_to_run    = {0}".format(self.pytest_modules_to_run))
                print("* available_pytest_modules = {0}".format(self.available_pytest_modules_list))

            if len(invalid_pytest_modules):
                msg = "For the BU={0} Project={1}:\n".format(self.bu_space, self.project_space)
                msg += " unsupported unittest modules (pytest) were specified: '{0}'.\n".format(",".join(invalid_pytest_modules))
                msg += "Check the project's __ini__.py file for the supported modules that were included."
                msg += "Check for correct syntax when specifying pytest modules."
                raise RuntimeError(msg)

    def __convert_modules_to_list(self, modules):
        # Example: modules = {'project': ['.', 'c2k_extra'],
        #                     'bu': {'libs': ['.', 'legacy'],
        #                     'tools': ['helloworld']},
        #                     'cisco': {}}
        cm = []
        for k, v in modules.items():
            if k == 'project':
                cm += v
            elif k == 'bu' and self.env_location == 'svn':
                for k2, v2 in v.items():
                    for test in v2:
                        if test != '.':
                            cm.append('{0}:{1}/{2}'.format(self.bu_space, k2, test))
                        else:
                            cm.append('{0}:{1}'.format(self.bu_space, k2))
            elif k == 'cisco' and self.env_location == 'svn':
                for k2, v2 in v.items():
                    for test in v2:
                        if test != '.':
                            cm.append('cisco:{0}/{1}'.format(k2, test))
                        else:
                            cm.append('cisco:{0}'.format(k2))
        return cm

    def __convert_modules_to_dict(self, modules):
        # Example modules = ['.', 'c2k_extra', 'entsw:libs', 'entsw:libs/legacy', 'entsw:tools/helloworld']
        cm = {}
        for item in modules:
            if ':' in item:
                top, mod_path = item.split(':', 1)
                module, sub_module = mod_path.split('/', 1) if '/' in mod_path else [mod_path, None]
                if '{0}:'.format(self.bu_space) in item:
                    key = 'bu'
                elif 'cisco:' in item:
                    key = 'cisco'
                else:
                    raise RuntimeError("Unrecognized module location: {0}".format(item))
                cm[key] = {} if key not in cm else cm[key]
                cm[key][module] = [] if module not in cm[key] else cm[key][module]
                cm[key][module] += [sub_module] if sub_module else ['.']
            else:
                cm['project'] = [] if 'project' not in cm else cm['project']
                cm['project'].append(item)
        return cm

    def collect_pytests(self):
        # Note: tox.ini can define the pytests rootdir.
        print("* Collecting pytests...")
        try:
            # Set 1 - PROJECT
            # Add any unittests from the Project work area and subdirs first.
            self.available_pytest_modules['project'] = self.__get_pytest_modules(self.work_path, is_project_path=True)

            # Set 2 - BU
            # Add any unittests from the BU external includes and subdirs.
            # (I.e. modules at the BU level but not in the direct project work area.)
            if self.bu_externals:
                self.available_pytest_modules['bu'] = {}
                for external_item in self.bu_externals:
                    if isinstance(external_item, tuple):
                        external_item_name = external_item[1]
                        external_item = external_item[0]
                    else:
                        external_item_name = self.separate_svn_path(external_item)[0]
                    target_path = os.path.join(self.archive_bu_root_path, external_item)
                    self.available_pytest_modules['bu'][external_item_name] = self.__get_pytest_modules(target_path)

            # Set 3 - BU Tools
            # Add any unittests from the BU tools and subdirs.
            target_path = os.path.join(self.archive_bu_root_path, self.bu_tools)
            bu_tools_name = self.separate_svn_path(self.bu_tools)[0]
            self.available_pytest_modules['bu'][bu_tools_name] = self.__get_pytest_modules(target_path)

            # Set 4 - PROJECT
            # Add any unittests from the project external includes and subdirs.
            # (I.e. modules not in the BU folder.)
            if self.project_externals:
                self.available_pytest_modules['extprojects'] = {}
                for external_item in self.project_externals:
                    if isinstance(external_item, tuple):
                        external_item_name = external_item[1]
                        external_item = external_item[0]
                    else:
                        external_item_name = self.separate_svn_path(external_item)[0]
                    target_path = os.path.join(self.archive_projects_root_path, external_item)
                    self.available_pytest_modules['extprojects'][external_item_name] = self.__get_pytest_modules(target_path)

            # Set 5 - CISCO
            # Add any unittests from the Cisco external includes and subdirs.
            # (I.e. modules not in the BU folder.)
            if self.cisco_externals:
                self.available_pytest_modules['cisco'] = {}
                for external_item in self.cisco_externals:
                    target_path = os.path.join(self.archive_cisco_root_path, external_item)
                    external_item_name = self.separate_svn_path(external_item)[0]
                    self.available_pytest_modules['cisco'][external_item_name] = self.__get_pytest_modules(target_path)

            # Convert dict to pre-fab list.
            self.available_pytest_modules_list = self.__convert_modules_to_list(self.available_pytest_modules)

        except subprocess.CalledProcessError as e:
            print("  Unable to collect test cases!")
            msg = "{0}, {1}".format(e.message, e.output)
            raise RuntimeError(msg)

    def __get_pytest_modules(self, target_path, is_project_path=False, prefix=None):

        try:
            # Need to include any relative paths from target dir since unittest in sub-dirs can exist.
            cmd = 'py.test {0} --collect-only'.format(target_path)
            print("* Collection cmd = {0}".format(cmd))
            pytest_collect = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
            if self.verbose:
                print("Collected = {0}".format(pytest_collect))
            pytrootpath = re.search('rootdir: (.*), ', pytest_collect).group(1)
            if is_project_path:
                self.pytest_root_path = pytrootpath
            module_path_prefix = self.__pathdiff(target_path, pytrootpath)
            pattern = """<Module '{0}(.*)'>""".format(module_path_prefix)
            pytest_modules = sorted(list(set(['/'.join(os.path.split(item)[0].split('/')[:-1])
                                              for item in re.compile(pattern).findall(pytest_collect)
                                              if os.path.split(item)[0].split('/')[-1:][0] == 'tests']
                                             )))

            # If unittests in the target dir exists then need to indicate by a '.' since collection item will initially show as null.
            for i in range(0, len(pytest_modules)):
                if not prefix:
                    pytest_modules[i] = '.' if pytest_modules[i] == '' else pytest_modules[i]
                else:
                    pytest_modules[i] = os.path.join(prefix, pytest_modules[i]) if pytest_modules[i] != '' else prefix

            if self.verbose:
                print('* py_mods (post)={0}'.format(pytest_modules))

        except subprocess.CalledProcessError:
            print("  Unable to collect pytests for {0}".format(target_path))
            pytest_modules = ''

        return pytest_modules

    @staticmethod
    def __pathdiff(path1, path2):
        if len(path1) >= len(path2):
            s1 = path1.split('/')
            s2 = path2.split('/')
        else:
            s2 = path1.split('/')
            s1 = path2.split('/')
        # Start at the beginning and work down until a difference is found.
        while len(s2) > 0 and s2[0] == s1[0]:
            s1.pop(0)
            s2.pop(0)
        # Remaining amount from the longer (or equal len) path IS the diff.
        diff = "{0}/".format('/'.join(s1)) if len(s1) > 0 else ''
        return diff

    def show_test_options(self):
        print("* Tests to run: " + ", ".join(self.tests_to_run))
        if 'pytest' in self.tests_to_run:
            if self.pytest_modules_to_run:
                print("* Pytest modules: {0}".format(self.pytest_modules_to_run))
            else:
                print("* Pytest modules: Run ALL that are available.")

    @staticmethod
    def textbox(msg):
        print("")
        print("=" * len(msg) + "=" * 6)
        print("|  " + msg + "  |")
        print("=" * len(msg) + "=" * 6)
        print("")

    @staticmethod
    def header(msg):
        msg2 = "* {0}:".format(msg)
        print("")
        print(msg2)
        print("-" * len(msg2))

    def get_enviroment(self):
        """Get a bunch of interesting system versions"""

        self.environment = [
            ("date", datetime.now().isoformat()),
            ("host", os.uname()[1]),
            ("user", self.user),
            ("os", os.uname()[0]),
            ("distro", " ".join(platform.linux_distribution())),
            ("user",  getpass.getuser()),
            ("apollo", self.apollo_control.version()),
            ("apollo-control", self.apollo_control.__repr__()),
            ("apollo-ctrl pkg", self.apollo_control.control_version()),
            ("python", platform.python_version()),
            ("pytest", parse.search('pytest version {}, ', subprocess.check_output(['py.test', '--version'], stderr=subprocess.STDOUT))[0]),
            ("pep8", "{0}  ({1})".format(subprocess.check_output(['pep8', '--version']).splitlines()[0], self.pep8)),
            ("pyflakes", subprocess.check_output(['pyflakes', '--version']).splitlines()[0]),
            ("xdist", parse.search('\nVersion: {}\n', subprocess.check_output(['pip', 'show', 'pytest-xdist']))[0]),
            ("project space", self.project_space),
            ("archive bu root", self.archive_bu_root_path),
            ("archive cisco root", self.archive_cisco_root_path),
            ("bu work folder", self.work_path),
            ("bu tool folder", self.tool_path),
            ("pytest proj root", self.pytest_root_path),
            ("results folder", self.result_path),
            ("bu_externals", self.bu_externals),
            ("project_externals", self.project_externals),
            ("apollo script link", self.source_link),
            ("apollo config link", self.config_link),
            ("built-ins", ','.join(self.SUPPORTED_TESTS)),
            ("pytests to run", ','.join(self.pytest_modules_to_run) if self.pytest_modules_to_run else 'ALL'),
            ("pytests available", ','.join(self.available_pytest_modules_list)),
            ("apollo restart", str(self.restart_apollo)),
            ('env location', self.env_location),
            ("verbose", str(self.verbose)),
        ]

        self.header("Environment")
        for name, version in self.environment:
            print("{0:3s}{1:<20s}: {2:s}".format(' ', name, version))

    def configure(self):

        if not self.nolinking:
            print("* Linking BU={0} Project={1} sources...".format(self.bu_space, self.project_space))
            dest = os.path.join(self.bu_space, self.project_space)
            self.source_link = self.apollo_control.add_source_link_to_scripts(source_path=self.work_path, dest_name=dest)

            hostname = socket.gethostname()
            print("* Linking the config files for this Host={0} ...".format(hostname))
            cfg_top_dir = os.path.join(self.archive_bu_root_path, self.bu_configs)
            # Top Cfg dir = /opt/cisco/te/scripts/projects/entsw/configs/trunk
            cfg_file_temp1 = "{0}_{1}_config.py".format(hostname, self.bu_space)
            cfg_file_temp2 = "{0}_config.py".format(hostname)
            cfg_dir_temp1 = self.locate_file(cfg_top_dir, cfg_file_temp1, first_occurrence=True)
            cfg_dir_temp2 = self.locate_file(cfg_top_dir, cfg_file_temp2, first_occurrence=True)
            print("*  Top Cfg dir = {0}".format(cfg_top_dir))
            if cfg_dir_temp1:
                print("*   Found BU specific config.")
                self.config_link = os.path.join(cfg_dir_temp1, cfg_file_temp1)
                cfg_dir = cfg_dir_temp1
                cfg_file = cfg_file_temp1
            elif cfg_dir_temp2:
                print("*   Found generic config. (WARNING: This might conflict with other BU's. Consider using '<host>_<bu>_config.py'.)")
                self.config_link = os.path.join(cfg_dir_temp2, cfg_file_temp2)
                cfg_dir = cfg_dir_temp2
                cfg_file = cfg_file_temp2
            else:
                msg = 'ERROR: Cannot locate a config file for this host!'
                raise RuntimeError(msg)
            print("*  cfg_dir='{0}'  cfg_file='{1}'".format(cfg_dir, cfg_file))
            self.apollo_control.add_config_link(self.config_link)

            # Link common (product config)
            common_cfg = os.path.join(cfg_top_dir, 'common')
            if os.path.exists(common_cfg):
                self.apollo_control.add_config_link(common_cfg)

            # Link common and general cfg utilities
            # Note: the common cfg file takes the form of the non-enumerated hostname as its prefix.
            #       If the hostname contains '-' it MUST be replaced with '_' for the "import" to work.
            normalized_hostname = hostname.replace('-', '_')
            while normalized_hostname[-1:].isdigit() or normalized_hostname[-1:] == '_':
                normalized_hostname = normalized_hostname[:-1]
            cfg_common1 = "{0}_{1}_common.py".format(normalized_hostname, self.bu_space)
            cfg_common2 = "{0}_common.py".format(normalized_hostname)
            config_common_link1 = os.path.join(cfg_dir, cfg_common1)
            config_common_link2 = os.path.join(cfg_dir, cfg_common2)
            if os.path.exists(config_common_link1):
                self.apollo_control.add_config_link(config_common_link1)
            elif os.path.exists(config_common_link2):
                self.apollo_control.add_config_link(config_common_link2)

            # Link externals: Tools
            if self.bu_tools:
                tools_name = self.separate_svn_path(self.bu_tools)[0]
                print("* Linking BU {0} Tools: Include={1}".format(self.bu_space, self.bu_tools))
                self.apollo_control.add_source_link_to_scripts(source_path=os.path.join(self.archive_bu_root_path, self.bu_tools),
                                                               dest_name=os.path.join(self.bu_space, tools_name))

            # Link externals: BU
            if self.bu_externals:
                for include_item_raw in self.bu_externals:
                    print("include_item_raw={0}".format(include_item_raw))
                    if isinstance(include_item_raw, tuple):
                        include_item_name = include_item_raw[1]
                        include_item = include_item_raw[0]
                    else:
                        include_item_name = self.separate_svn_path(include_item_raw)[0]
                        include_item = include_item_raw
                    print("* Linking BU {0} Externals: Include={1} as {2}".format(self.bu_space, include_item, include_item_name))
                    self.apollo_control.add_source_link_to_scripts(source_path=os.path.join(self.archive_bu_root_path, include_item),
                                                                   dest_name=os.path.join(self.bu_space, include_item_name))

            # Link externals: Projects
            if self.project_externals:
                for include_item_raw in self.project_externals:
                    if isinstance(include_item_raw, tuple):
                        include_item_name = include_item_raw[1]
                        include_item = include_item_raw[0]
                    else:
                        include_item_name = self.separate_svn_path(include_item_raw)[0]
                        include_item = include_item_raw
                    print("* Linking Project Externals: Include={0} as {1}".format(include_item, include_item_name))
                    self.apollo_control.add_source_link_to_scripts(source_path=os.path.join(self.archive_projects_root_path, include_item),
                                                                   dest_name=os.path.join(include_item_name))

            # Link externals: Cisco
            if self.cisco_externals:
                for include_item in self.cisco_externals:
                    include_item_name = self.separate_svn_path(include_item)[0]
                    print("* Linking Cisco general Include={0} as {1}".format(include_item, include_item_name))
                    self.apollo_control.add_source_link_to_scripts(source_path=os.path.join(self.archive_cisco_root_path, include_item),
                                                                   dest_name=os.path.join('cisco', include_item_name))

        # Clear Logs
        # if self.clear_apollo_logs:
        #    self.apollo_control.remove_logs()

        # Restart Apollo
        if self.restart_apollo:
            self.apollo_control.stop()
            self.apollo_control.start(self.apollo_start_args)
        else:
            print("* No Apollo restart!")

    def locate_file(self, dir_entry, search_file, first_occurrence=True):
        """
        Recursively walk through a directory structure at a specific entry point and search for a specific file.
        Return the full path of where the file was found.
        The file should be unique within the dir entry (downwards in the tree).
        :param dir_entry:  Directory tree entry point to start the search (fully qualified).
        :param search_file: file to search.
        :param first_occurrence: If True, once file is found stop searching.
                                 If False, continue searching the entire tree from point of entry; if duplicates are found return a list.
        :return: full_path or [full_path1, full_path2, ...]
        """
        location = []
        for root, dirs, files in os.walk(dir_entry, topdown=False):
            if search_file in files:
                if first_occurrence:
                    return root  # first_occurrence=true and file found
                location.append(root)
        if location:
            if len(location) > 1:
                return location  # first_occurrence=false and multiple files found
            return location[0]  # first_occurrence=false and only one file found
        return None  # file not found

    def separate_svn_path(self, path):
        """ Separate SVN Path
        Separate a path into two parts based on the standard SVN structure: 'trunk', 'branches', 'tags'.
        Note: This assumes no nesting or aliasing of trunk, branches, tags (i.e. the type will show only once in the path).
        Ex1. 'libs/chamber/trunk'  -->  ('libs/chamber', 'trunk', '')
        Ex1. 'libs/automation/trunk/foxch'  -->  ('libs/chamber/foxch', 'trunk', '')
        Ex1. 'libs/automation/branches/bborel_1_0/foxch'  -->  ('libs/chamber/foxch', 'branches', 'bborel_1_0')
        Ex2. 'libs/chamber/branches/bborel_1_0'  -->  ('libs/chamber', 'branches', 'bborel_1_0')
        Ex3. 'libs/chamber/tags/R_1_0'  -->  (('libs/chamber', 'tags', 'R_1_0')
        :param path: The full or relative SVN path.
        :return path_components: tuple of (first_part, svn_type, second_part)
        """
        if not isinstance(path, str):
            print("ERROR: path input is not a str.")
            return '', '', ''

        if 'trunk' in path:
            svn_structure = 'trunk'
        elif 'branches' in path:
            svn_structure = 'branches'
        elif 'tags' in path:
            svn_structure = 'tags'
        else:
            return path, '', ''

        # Phase 1
        ind = path[:path.index(svn_structure)].count('/')
        path_components = path.split('/')
        path_components = ['/'.join(path_components[0:ind]), path_components[ind], "/".join(path_components[ind + 1:])]

        # Phase 2 - sub-folders
        if svn_structure == 'trunk':
            if path_components[2]:
                path_components[0] = os.path.join(path_components[0], path_components[2])
                path_components[2] = ''
        elif svn_structure in ['branches', 'tags']:
            sub_path_components = path_components[2].split('/')
            if len(sub_path_components) > 1:
                path_components[0] = os.path.join(path_components[0], '/'.join(sub_path_components[1:]))
        return path_components

    def setup_result_folder(self):
        print("* Setting up test result folder: %s" % self.result_path)
        try:
            os.makedirs(self.result_path)
        except OSError as e:
            if not os.path.isdir(self.result_path):
                raise RuntimeError(e.message)
            else:
                if self.clear_apollo_logs:
                    # Clear files that might be part of the existing result dir
                    print("* Clearing previous results...")
                    files = glob.glob(self.result_path + "/*")
                    for f in files:
                        if self.verbose:
                            print("* Removing: {0}".format(f))
                        os.remove(f)
                else:
                    print("* Retaining current log results (no clean).")

    def report(self):
        self.header("Results")
        for result in self.results:
            print(result)
        passed = all([result.passed() for result in self.results])
        self.textbox("End Result = {0}".format("PASS" if passed else "FAIL"))
        return not passed

    def main(self, margs):
        ret = 0
        try:
            self.get_enviroment()
            self.get_owners()
            if not margs.init:
                self.run_tests()
                zip_log_path = os.path.join(self.result_path, 'apollo.logs{0}.zip'.format(self.log_tag))
                self.apollo_control.zip_logs(zip_log_path, self.verbose2)
                ret = self.report()
        except Exception as e:
            print(e)
            ret = 2
        finally:
            print("Exit ({0})".format(int(ret)))
            exit(int(ret))

    def run_tests(self):
        self.show_test_options()
        self.setup_result_folder()
        print("* Running tests...")
        for test in self.tests_to_run:
            result = self.run_test(test)
            if not isinstance(result, list):
                self.results.append(result)
            else:
                self.results += result
            sys.stdout.flush()
            sys.stderr.flush()

    def run_test(self, name):
        self.header(name)
        # Check if there are any other failures before starting a potentially long pytest set.
        proceed = all([result.passed() for result in self.results]) if name == 'pytest' else True

        if proceed:
            result = self.__getattribute__(name + "_test")()
            if isinstance(result, list):
                for r in result:
                    if r.data:
                        r.save_log(self.result_path)
                        print(r)
            else:
                if result.data:
                    result.save_log(self.result_path)
                    print(result)
        else:
            msg = 'Pytest has been skipped due to other dependent test failures!'
            print("{0}".format(msg))
            result = TestResult("pytest", fails=0, data=msg, skip=True)
            print(result)

        return result

    def pep8_test(self):
        cmd = "pep8 {0} --format=pylint --count --ignore={1} --max-line-length={2}".format(self.work_path, self.pep8, self.PEP8_MAX_LINE_LEN)
        print("cmd = {0}".format(cmd))
        pep8_process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        pep8_stdout, pep8_stderr = pep8_process.communicate()

        if pep8_stderr:
            pep8_fails = int(pep8_stderr.strip())
        else:
            pep8_fails = 0

        pep8_report = pep8_stdout.strip()

        # chomp off the first ./ as Jenkins is unable to correlate path with this 'linux fs header'
        pep8_report = "".join([line.lstrip('./') for line in pep8_report.splitlines(True)])

        if pep8_fails:
            print(pep8_report)

        result = TestResult("pep8", fails=pep8_fails, data=pep8_report)
        return result

    def pyflakes_test(self):
        def report_with_bypass(self, message_class, *args, **kwargs):
            text_lineno = args[0].lineno - 1
            with open(self.filename, 'r') as code:
                if code.readlines()[text_lineno].find('nopyflakes') >= 0:
                    return
            self.messages.append(message_class(self.filename, *args, **kwargs))
        # extend checker to support bypass
        pyflakes.checker.Checker.report = report_with_bypass

        pyflakes_out = StringIO.StringIO()
        pyflakes_err = StringIO.StringIO()

        reporter = pyflakes.reporter.Reporter(warningStream=pyflakes_out, errorStream=pyflakes_err)
        pyflakes_result = pyflakes.api.checkRecursive([self.work_path], reporter)
        pyflakes_out.flush()
        pyflakes_err.flush()

        if pyflakes_out and pyflakes_out.len > 0:
            print(pyflakes_out.getvalue().strip('\n'))
        if pyflakes_err and pyflakes_err.len > 0:
            print(pyflakes_err.getvalue().strip('\n'))

        pyflakes_report = "".join([line.lstrip('./') for line in pyflakes_out.getvalue().strip().splitlines(True)])
        pyflakes_report = "".join(["%s:%s: [E]%s" % tuple(line.split(':')) for line in pyflakes_report.splitlines(True)])

        result = TestResult("pyflakes", fails=pyflakes_result, data=pyflakes_report)
        return result

    def __pytest_generate_params(self, available_pytest_modules, pytest_modules_to_run):
        # OPTION: -k expression
        expr = '-k {0}'.format(self.pytest_expr) if self.pytest_expr else ''
        # OPTION: --ignore=path  (multi)
        ignore = ' '.join(['--ignore={0}'.format(item) for item in [module for module in available_pytest_modules
                                                                    if module not in pytest_modules_to_run]]) if '.' in pytest_modules_to_run else ''
        run_modules = ['.'] if '.' in pytest_modules_to_run else pytest_modules_to_run
        return expr, ignore, run_modules

    def __pytest_cmd(self, test_name, marker, result_file, processes_opt='', gui=''):
        result_list = []
        if not self.pytest_modules_to_run:
            pytest_modules_to_run = self.available_pytest_modules
        else:
            pytest_modules_to_run = self.__convert_modules_to_dict(self.pytest_modules_to_run)

        for k, v in pytest_modules_to_run.items():
            if isinstance(v, list):
                # Immediate workspace unittests
                expr, ignore, run_modules = self.__pytest_generate_params(self.available_pytest_modules[k], v)
                cmd = 'py.test -rxs -v -m {0} {1} ' \
                      '--junitxml={2} {3}' \
                      '--capture={4} {5} {6} {7}'.format(marker, processes_opt, result_file, gui, self.pytest_capture, expr, ignore, ' '.join(run_modules))
                result_list.append(self.call_pytest(test_name, cmd))
            elif isinstance(v, dict) and self.env_location == 'svn':
                # External workspace unittests (for archive structure only)
                # Note: Jenkins structure should place all libs in a single target workspace (IF packages are NOT used).
                for k2, v2 in v.items():
                    work_dir = '.'
                    if k == 'bu':
                        if k2 == self.separate_svn_path(self.bu_tools)[0]:
                            work_dir = os.path.join(self.archive_bu_root_path, self.bu_tools)
                        else:
                            normal_bu_externals = [i if isinstance(i, str) else i[1] for i in self.bu_externals]
                            work_dir = os.path.join(self.archive_bu_root_path, [i for i in normal_bu_externals if '{0}/'.format(k2) in i][0])
                    elif k == 'extprojects':
                        normal_project_externals = [i if isinstance(i, str) else i[1] for i in self.project_externals]
                        work_dir = os.path.join(self.archive_projects_root_path, [i for i in normal_project_externals if '{0}/'.format(k2) in i][0])
                    elif k == 'cisco':
                        work_dir = os.path.join(self.archive_cisco_root_path, [i for i in self.cisco_externals if '{0}/'.format(k2) in i][0])
                    expr, ignore, run_modules = self.__pytest_generate_params(self.available_pytest_modules[k][k2], v2)
                    cmd = 'py.test -rxs -v -m {0} {1} ' \
                          '--junitxml={2} {3}' \
                          '--capture={4} {5} {6} {7}'.format(marker, processes_opt, result_file, gui,
                                                             self.pytest_capture, expr, ignore, ' '.join(run_modules))
                    result_list.append(self.call_pytest(test_name, cmd, work_dir, subtest_name="{0}:{1}".format(k, k2)))

        return result_list

    def pytest_test(self):
        test_name = 'pytest'
        marker = "'not performance and not webgui'"
        result_file = "{0}/pytest{1}.xml".format(self.result_path, self.log_tag)
        return self.__pytest_cmd(test_name, marker, result_file)

    def pytest_parallel_test(self):
        test_name = 'pytest_parallel'
        marker = "'not performance and not sequential and not webgu'"
        result_file = "{0}/pytest_parallel{1}.xml".format(self.result_path, self.log_tag)
        processes_opt = "-n {0} --boxed".format(int(self.xdist))
        print('+ Pytest will run in xdist mode with #%d processes on all pytests not marked as sequential.' % int(self.xdist))
        return self.__pytest_cmd(test_name, marker, result_file, processes_opt)

    def pytest_sequential_test(self):
        test_name = 'pytest_sequential'
        marker = "'not performance and sequential and not webgui'"
        result_file = "{0}/pytest_sequential{1}.xml".format(self.result_path, self.log_tag)
        print('+ Pytest will run in sequential mode on all pytests marked as sequential.')
        return self.__pytest_cmd(test_name, marker, result_file)

    def webgui_test(self):
        test_name = 'pytest_webgui'
        marker = "'webgui'"
        result_file = "{0}/pytest_webgui{1}.xml".format(self.result_path, self.log_tag)
        gui = '--gui' if self.show_gui else ''
        print('+ Pytest will run all webgui marked tests')
        return self.__pytest_cmd(test_name, marker, result_file, gui=gui)

    def call_pytest(self, test_name, cmd, work_dir=None, subtest_name=None):
        print("Pytest cmd  = '{0}'".format(cmd))
        cwd = os.getcwd()
        work_dir = self.work_path if not work_dir else work_dir
        os.chdir(work_dir)
        print("Working dir = {0}".format(os.getcwd()))
        sys.stdout.flush()
        sys.stderr.flush()
        cmd_split_shlex = shlex.split(cmd)
        pytest_process = subprocess.Popen(cmd_split_shlex, stderr=subprocess.STDOUT)
        pytest_stdout, pytest_stderr = pytest_process.communicate()

        if pytest_process.returncode == 0:
            pytest_result = 0
        else:
            pytest_result = -1

        result = TestResult(test_name, fails=pytest_result, data=pytest_stdout, subtest_name=subtest_name)
        os.chdir(cwd)
        return result

    @staticmethod
    def get_file_author(file_path):
        with open(file_path) as f:
            try:
                authorg = re.search(r"__author__[\t ]* = [\t ]*[\'\"]+(.*)[\'\"]+|__author__[\t ]* = [\t ]*\[(.*)\]", f.read())
                author = authorg.group(1) if authorg.group(1) else authorg.group(2).replace("'", "").replace('"', '')
            except AttributeError:
                author = "unknown"
        return author

    def walk_files_for_author(self, path, prefix=''):
        # Get all test files recursively
        test_files = []
        for root, _, file_names in os.walk(path):
            for file_name in fnmatch.filter(file_names, 'test_*.py'):
                test_files.append(os.path.join(root, file_name))
        file_authors = [(TestRunner.get_file_author(test_file), '{0}{1}'.format(prefix, test_file.replace(path, "").lstrip('/')))
                        for test_file in test_files]
        return file_authors

    def get_owners(self):
        self.header("Test Owners")

        file_authors = []

        # Project location
        file_authors += self.walk_files_for_author(self.work_path)

        if self.env_location == 'svn':
            # BU location (svn only)
            if self.bu_externals:
                for external_item in self.bu_externals:
                    if isinstance(external_item, tuple):
                        external_item = external_item[0]
                    target_path = os.path.join(self.archive_bu_root_path, external_item)
                    file_authors += self.walk_files_for_author(target_path, external_item)
            if self.bu_tools:
                target_path = os.path.join(self.archive_bu_root_path, self.bu_tools)
                file_authors += self.walk_files_for_author(target_path, self.bu_tools)

            # Projects location (svn only)
            if self.project_externals:
                for external_item in self.project_externals:
                    if isinstance(external_item, tuple):
                        external_item = external_item[0]
                    target_path = os.path.join(self.archive_projects_root_path, external_item)
                    file_authors += self.walk_files_for_author(target_path, external_item)

            # Cisco location (svn only)
            if self.cisco_externals:
                for external_item in self.cisco_externals:
                    target_path = os.path.join(self.archive_cisco_root_path, external_item)
                    file_authors += self.walk_files_for_author(target_path, external_item)

        for owner, test_file in file_authors:
            owner = '[various]' if len(owner) > 16 else owner
            print("{0:3s}{owner:<16s}: {test_file}".format(' ', owner=owner, test_file=test_file))
        print()

    def readfiledata(self, filename, ast_flag=False, start_pattern=None, end_pattern=None):
        """
        Read a file and evaluate it in the following ways:
            1. Flat file, create a list with one line per list item, or
            2. Convert file as a dict; syntax must be correct. (Do not use custom data structures, only use numeric, str, tuple, list, or dict.)
        An option is available for capturing only text within a start and/or end regex pattern.
        If the regex group capture option is used in the start/end patterns the line is replaced with the first capture group.
        :param filename: Target file.
        :param ast_flag: Convert file data to a dict (file must have correct structure).
        :param start_pattern: Regex starting pattern for file data capture.
        :param end_pattern: Regex ending pattern for file data capture.
        :return filedata: A list or a dict.
        """
        def _process_markers(fp, start_pattern, end_pattern):
            begin = False if start_pattern else True
            end = False
            fdata = ''
            for line in fp:
                if not begin:
                    m = re.match(start_pattern, line)
                    if m:
                        begin = True
                        # If a group capture was indicated in the start pattern then replace the first line.
                        line = m.groups()[0] if m.groups() else line
                end = True if end_pattern and re.match(end_pattern, line) else end
                fdata += line if begin and not end else ''
                if end:
                    # If a group capture was indicated in the end pattern then replace the last line.
                    m = re.match(end_pattern, line)
                    line = m.groups()[0] if m.groups() else line
                    fdata += line
                    break
            return fdata
        # ----
        filedata = ''
        if not os.path.isfile(filename):
            return filedata
        try:
            if ast_flag and (not start_pattern and not end_pattern):
                with open(filename, mode='r', buffering=-1) as fp:
                    filedata = ast.literal_eval(fp.read())
            else:
                # Text processing
                filedata = []
                with open(filename, mode='r', buffering=-1) as fp:
                    if not start_pattern and not end_pattern:
                        # Rd file content into mem in one command.
                        # Be careful to not use this on very large files!
                        fdata = fp.read()
                    else:
                        # Use pattern matching
                        # Since start or end text marker(s) were specified; process line-by-line..
                        fdata = _process_markers(fp, start_pattern, end_pattern)
                if ast_flag:
                    # Eval data as dict.
                    filedata = ast.literal_eval(fdata) if fdata else []
                else:
                    # Break at line boundaries, and create list.
                    filedata = fdata.splitlines() if fdata else []
        except Exception as e:
            print("Exception during file read operation: {0}".format(e))
        finally:
            return filedata


def usage_help():
    print("""
General format:
--------------
 ./run_tests2.py -t [t1,t2,…] -p [P1,P2,…] where:
  •	t1,t2,… is any list from the set of [pep8,pyflakes,pytest].  (No space between t1, t2, etc.)
  •	P1,P2… is any list of pytest folders from inside the working Project directory.  (No space between P1, P2, etc.) and
  •	If P1,P2… is outside the Project dir but inside the BU folder of SVN then use the SVN BU name followed by a colon.

Notes:
------
This tool MUST be run in one of two locations:
 1. The SVN project trunk, branches subdir, or tags subdir; OR
 2. A consolidated workspace whereby all libraries and external modules are inside the workspace dir
    (this would be a workspace like Jenkins would create for example).

This tool EXPECTS config data in the __init__.py file of the target project location (current working directory).
The data is a simple dict of the following (ensure the ending comment tag is included as shown):
__config__ = {
    'bu_space': 'mybu',
    'project_space': 'myproduct',
    'includes': {
        'bu_configs': 'configs/trunk',
        'bu_tools':  'tools/trunk',
        'bu_externals': ['libs/trunk'],
        'project_externals': [],
        'cisco_externals': [],
    }
}  # __config__end

Examples:
--------
This tool is CONTEXT SENSITIVE!  This means it looks at the current working directory you are in, for example:
   SVN local archive at '/opt/cisco/te/scripts/project/mybu/myproduct/trunk'.
You can always do '.<path to>/run_tests2.py -i' and look for the available pytests in the Environment output based on the
current working directory you are in.
Your current working directory MUST always have an __init__.py file with the correct config as described above.
Note: Some servers are equipped with the 'apruntests' batch which can be launched from anywhere to start the run_tests2.py module.
      If not, then you will  have to create an alias on the server to point to this tool:
      "alias apruntests=/opt/cisco/te/scripts/projects/<bu>/tools/trunk/citp/run_tests2.py"

 Case 1.
   If you want to run only pep8 and pytest from a specific project/workspace folder, let’s say 'libs' inside the working dir, use:
   • apruntests -t pep8,pytest -p libs
   Therefore,  –t combines the tests for pep8 and pytest to run on the folder 'libs' selected via –p.
Case 1a.
   If you are running in SVN and the libs exists outside the project folder but within the bu folder
   specified by bu_externals in __config__:
   • apruntests -t pep8,pytest -p mybu:libs

 Case 2.
   If you want to run all (pep8, pyflakes, and pytest) on a 'libs' folder inside the Project folder, use:
   • apruntests -p libs

 Case 3.
   If you want to run all (pep8, pyflakes, and pytest) on a 'libs' and 'tools/helloworld' folders inside the BU folder, use:
   • apruntests -p mybu:libs,mybu:tools/helloworld

 Case 4.
   If you want to run just pytest on a 'libs' and 'tools/helloworld' folders inside the BU folder, use:
   • apruntests -t pytest -p mybu:libs,mybu:tools/helloworld

 Case 5.
   If you want to run all (pep8, pyflakes, and pytest) on all folders, use:
   • apruntests

    """)                                                                                                                 # nopep8
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="Turn on verbosity for extra information (default off).")
    parser.add_argument("--verbose2", dest="verbose2", default=False, action="store_true",
                        help="Turn on verbosity for log zipping (default off).")
    parser.add_argument("-u", "--usage", help="Provide additional usage details and examples.",
                        dest="usage", default=False, action="store_true")
    parser.add_argument("-n", "--no-restart", dest="restart_apollo", default=True, action="store_false",
                        help="Don't restart Apollo to save time if all dependencies are in place.")
    parser.add_argument("-l", "--logs-no-clear", dest="clear_apollo_logs", default=True, action="store_false",
                        help="Keep the Apollo logs intact; do not clear..")
    parser.add_argument("--log_tag", help="Specify a unique name tag for result logs..",
                        dest="log_tag", default='', action="store")
    parser.add_argument("-a", "--apollo-start", dest="apollo_start_args", default='',
                        help="Any apollo start options reside here.")
    parser.add_argument("-t", "--test", help="Provide a list of tests to run. "
                                             "Supported tests: %s" % ", ".join(TestRunner.SUPPORTED_TESTS),
                        dest="tests", default=TestRunner.DEFAULT_TESTS, action="store")
    parser.add_argument("-p", "--pytest", help="Provide a list of specific pytests modules to run.",
                        dest="pytests", default='', action="store")
    parser.add_argument("-i", "--init", help="Initialize and print info only (no run).",
                        dest="init", default=False, action="store_true")
    parser.add_argument("-c", "--capture", help="Specify capture method for pytest.",
                        dest="capture", default='sys', action="store", choices=['sys', 'fd', 'no'])
    parser.add_argument("-k", "--expr", help="Specify substring expression for pytest.",
                        dest="expr", default=None, action="store")
    parser.add_argument("-x", "--xdist", help="Use xdist to speed things up (experimental)."
                                              "Provide number of processes here.",
                        dest="xdist", default=False, action="store")
    parser.add_argument("--gui", '--show-gui', help="Show the gui during webgui tests (default disabled).",
                        dest="gui", default=False, action="store_true")
    parser.add_argument("-8", "--pep8", help="Specify errors to ignore (e.g. E221,E241,E731).",
                        dest="pep8", default="E221,E241,E731,E126", action="store")
    parser.add_argument("--cfg", '--use-cfg', help="Use the config file.",
                        dest="cfg", default=False, action="store_true")
    parser.add_argument("--nolinking", dest="nolinking", default=False, action="store_true",
                        help="Turn off Apollo link creation (default=off).")
    args = parser.parse_args()

    if args.usage:
        usage_help()
        exit(0)

    if args.init:
        args.restart_apollo = False  # Override

    if args.cfg and os.path.exists(__runtests_cfg__):
        print("Using cfg and it exists, therefore exit.")
        exit(0)

    test_suite = TestRunner(verbose=args.verbose,
                            verbose2=args.verbose2,
                            restart_apollo=args.restart_apollo,
                            clear_apollo_logs=args.clear_apollo_logs,
                            tests_to_run=args.tests,
                            pytest_modules_to_run=args.pytests,
                            xdist=args.xdist,
                            show_gui=args.gui,
                            pytest_capture=args.capture,
                            pytest_expr=args.expr,
                            apollo_start_args=args.apollo_start_args,
                            pep8=args.pep8,
                            nolinking=args.nolinking,
                            log_tag=args.log_tag
                            )
    test_suite.main(args)
    exit(0)
