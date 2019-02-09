"""
===============
PYTEST conftest
===============
Used for parameterization of unittest functions.
"""
import pytest

__author__ = ['bborel']
__version__ = '1.0.1'


def pytest_addoption(parser):
    parser.addoption("--tss", action='store', default='ALL', help="Test station(s) to target.")
    parser.addoption("--uuts", action='store', default='ALL', help="UUT(s) to target.")


@pytest.fixture
def tss(request):
    return request.config.getoption("--tss")


@pytest.fixture
def uuts(request):
    return request.config.getoption("--uuts")


# def pytest_addoption(parser):
#     parser.addoption("--tss", action='append', type='string', default=[], help="Test station(s) to target.")
#     parser.addoption("--uuts", action='append', type='string', default=[], help="UUT(s) to target.")
# def pytest_generate_tests(metafunc):
#     if 'tss' in metafunc.fixturenames:
#         metafunc.parametrize("tss", metafunc.config.getoption('tss'))
#     if 'uuts' in metafunc.fixturenames:
#         metafunc.parametrize("uuts", metafunc.config.getoption('uuts'))
