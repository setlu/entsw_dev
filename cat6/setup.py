"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/pabuproject
"""
from setuptools import setup, find_packages
from os import path, walk
import sys
import argparse


# All functions
def traverse_dir(dir_name):
    output = []
    for root, subdirs, files in walk(dir_name):
        files_with_path = []
        for fi in files:
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
    'c6k'
]

# Include required files and directories
install_data_files = required_files
for r in required_dirs:
    install_data_files += traverse_dir(r)

setup(
    name='entsw_c6k_test_scripts',
    version=pkg_ver,
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'c6k.*', 'c6k']),
    install_requires=[
      'entsw_libs',
      'entsw_configs'
    ],
    data_files=install_data_files
)
