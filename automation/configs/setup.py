"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/pabuproject
"""
from setuptools import setup, find_packages
from os import path, walk, environ, getenv
import sys
import argparse
import re


# ------------------------------------------------------
# Change the entries at "CHANGE THIS" comments below
pkg_name = 'entsw_configs'


# Set required common files
required_files = [
]

# Set required common directories
required_dirs = [
    '.'    # CHANGE THIS - to your source code directory under repo directory
]


# CHANGE THIS - packages to be excluded from ".../site-packages"
exclude_list = [
    'a*', 'b*', 'c*', 'd*', 'e*', 'f*', 'g*', 'h*', 'i*', 'j*', 'k*', 'l*', 'm*',
    'n*', 'o*', 'p*', 'q*', 'r*', 's*', 't*', 'u*', 'v*', 'w*', 'x*', 'y*', 'z*'
]

# CHANGE THIS - add your dependent packages, packages should be built/hosted within TE script distribution system
script_dependencies = [
    # 'entsw_libs'
]

# ------------------------------------------------------

# Base path default
try:
    environ['base_dir'] = getenv('base_dir', 'projects')
except:
    print 'ERROR: Invalid environment'
    sys.exit(1)


# All functions
def traverse_dir(dir_name, **kwargs):
    output = []
    exclude_files = kwargs.get('exclude_files', {dir_name: ['Makefile',
                                                            'setup.cfg',
                                                            'setup.py',
                                                            'LICENSE.txt',
                                                            'Jenkinsfile',
                                                            'sonar-project.properties',
                                                            'pip-delete-this-directory.txt',
                                                            'PKG-INFO',
                                                            'README.rst'
                                                            ]})
    exclude_dirs = kwargs.get('exclude_dirs', ['{0}/~($|/.*)'.format(dir_name),
                                               '{0}/.git.*'.format(dir_name),
                                               '{0}/dist($|/.*)'.format(dir_name),
                                               '{0}/{1}.*'.format(dir_name, pkg_name),
                                               '{0}/pip-egg-info'.format(dir_name)])
    print('dir_name={0}'.format(dir_name))
    print('exclude_dirs={0}'.format(exclude_dirs))

    for root, subdirs, files in walk(dir_name):
        files_with_path = []
        exclude_dir = any([re.search(d, root) for d in exclude_dirs])
        if not exclude_dir:
            for fi in files:
                if fi not in exclude_files.get(root, []):
                    files_with_path.append(root + '/' + fi)
            output.append((root, files_with_path))
    return output

# Main

# TBR -----
p = argparse.ArgumentParser()
p.add_argument(
    '--pkg_version',
    dest='pkg_version',
    help='required for package ver',
    action='store',
    required=False
)

args, unknown = p.parse_known_args()
sys.argv = [sys.argv[0]] + unknown
pkg_ver = args.pkg_version
# -------

execfile('version.py')

# Include required files and directories
install_data_files = required_files
for r in required_dirs:
    install_data_files += traverse_dir(r)

setup(
    name=pkg_name,
    version=__version__,
    packages=find_packages(exclude=['contrib', 'docs', 'tests'] + exclude_list),
    install_requires=script_dependencies,
    data_files=install_data_files
)
