"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/pabuproject
"""
from setuptools import setup, find_packages
from os import path, walk
import sys
import argparse
import re

PACKAGE_NAME = 'entsw_automation_test_scripts'

__version__ = '0.2.0'


# All functions (master)
def traverse_dir(dir_name, **kwargs):
    output = []
    exclude_files = kwargs.get('exclude_files', {dir_name: ['Makefile',
                                                            'setup.cfg',
                                                            'setup.py',
                                                            'LICENSE.txt',
                                                            'Jenkinsfile',
                                                            'sonar-project.properties']})
    exclude_dirs = kwargs.get('exclude_dirs', ['{0}/~($|/.*)'.format(dir_name),
                                               '{0}/.git.*'.format(dir_name),
                                               '{0}/dist($|/.*)'.format(dir_name),
                                               '{0}/{1}.*'.format(dir_name, PACKAGE_NAME)])
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

# Set required common files
required_files = []

# Set required common directories
required_dirs = [
    '.'
]

# Include required files and directories
install_data_files = required_files
for r in required_dirs:
    install_data_files += traverse_dir(r)

setup(
    name=PACKAGE_NAME,
    version=pkg_ver,
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'automation.*', 'automation']),
    install_requires=[
      'entsw_libs',
      'entsw_configs'
    ],
    data_files=install_data_files
)
