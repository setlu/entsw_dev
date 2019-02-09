"""
========================
CITP Unittests Framework
========================

This class module is inherited by product-family specific unittests.
The unittests are designed for dedicated test platforms with "gold units".

The Apollo x_config.py MUST conform to the standard station definition as detailed in the entsw.config.common modules.
The golden UUTs and all data for production prompting can be stored in a single module of the following form:
-----
citp_uuts = {
    <server_hostname1>: {
        <production_line>: {
            <test_area>: {
                <station_name>: {
                    <container>:
                        {'enabled': True|False, 'mode': 'DEBUG', 'start_delay': <secs>, 'timeout': <secs>, 'answers': [<str>, <str>, ...]},
                    <supercontainer>:
                        {'enabled': True|False, 'mode': 'DEBUG', 'start_delay': <secs>, 'timeout': <secs>, 'answers': [<str>, <str>, ...]},
                        ...
                    }, ...
                }, ...
            }, ...
        }, ...
    <server_hostname2>: <server_hostname1>    <-- reference pointer (only allowed at the "server" level)
}
------
NOTE: A default module can be found at entsw.tools.citp.citp_uut_unittest_def.
      The "citp_uut_unittest_def.py" is currently a community module; please use responsibly.


"""
import sys

import apollo.scripts.entsw.libs.tools.citp.apollo_run_tool as apruntool
import apollo.scripts.entsw.libs.tools.citp.citp_uut_unittest_def as citp_uut_unittest_def
import apollo.scripts.entsw.libs.utils.common_utils as common_utils

__title__ = 'CITP Unittest Framework'
__author__ = ['bborel']
__version__ = '1.0.2'


class CITPUnittestFramework(object):
    """ Continuous Integration Test Platform (CITP) Unittest Framework

        This class will load the CITP UUT definitions needed for unittesting of production code.
        These definitions contain all operator prompt data as if they were scanning manually.

        The methods allow for multiple containers to run in parallel or single containers to run sequentially.
    """

    uut_defs = citp_uut_unittest_def.citp_uuts
    hostname = common_utils.gethostname()
    pytest_continue = True

    def _build_run_dict(self, pls, areas, tss='ALL', uuts='ALL', answers=None):
        """ Build Run Dict

        This is the required input form for "run_apollo_containers_explicitly".

        Example output with 2 UUTs:
        {1: {'answers': ['GEN2', '73-16649-03 03', 'FOC18472NN5', 'A01234567', 'NONE', 'NO'],
             'area': 'PCBST',
             'container': 'UUT12',
             'mode': 'DEBUG',
             'prod_line': 'C3K',
             'start_delay': 1,
             'test_station': 'Station_A_01',
             'timeout': 10000},
         2: {'answers': ['GEN2', '73-16285-04 05', 'FOC19120N56', 'A11345678', 'NO'],
             'area': 'PCBST',
             'container': 'UUT11',
             'mode': 'DEBUG',
             'prod_line': 'C3K',
             'start_delay': 1,
             'test_station': 'Station_A_01',
             'timeout': 10000},
        }

        :param (str|list) pls: Product Lines
        :param (str|list) areas: Test Areas
        :param (str|list) tss: Test Stations
        :param (str|list) uuts: UUTs
        :param (list) answers: Prepopulated answers to the "ask_questions" that occur in the PRE-SEQ & SEQ.
                               Note: Apollo currently does not have an answers cli provision for containers under a supercontainer; therefore
                                     all questions must only occur in the supercontainer.
        :return (dict): see example above.
        """
        server_uuts = CITPUnittestFramework.uut_defs.get(CITPUnittestFramework.hostname, None)
        if not server_uuts:
            print("No UUTs defined for unittesting on this server.")
            assert False
            return
        if isinstance(server_uuts, str):
            server_uuts = self.uut_defs.get(server_uuts, {})
        pls = [pls] if not isinstance(pls, list) else pls
        areas = [areas] if not isinstance(areas, list) else areas
        tss = [t.strip(' ') for t in tss.split(',')] if not isinstance(tss, list) else tss
        uuts = [u.strip(' ') for u in uuts.split(',')] if not isinstance(uuts, list) else uuts
        print('-' * 50)
        print("Build Run Dict")
        print("Inputs  : pls={0}, areas={1}, tss={2}, uuts={3}".format(pls, areas, tss, uuts))
        print("Hostname: {0}".format(self.hostname))
        print('-' * 50)
        run_dict = {}
        index = 0
        _pls = sorted(server_uuts.keys()) if pls == ['ALL'] else pls
        print(_pls)
        for pl, pl_data in server_uuts.items():
            if pl not in _pls:
                continue
            print("Production Line = {0}".format(pl))
            _areas = sorted(pl_data.keys()) if areas == ['ALL'] else areas
            print(_areas)
            for area, area_data in pl_data.items():
                if area not in _areas:
                    continue
                print("Test Area = {0}".format(area))
                _tss = sorted(area_data.keys()) if tss == ['ALL'] else tss
                print(_tss)
                for ts, ts_data in area_data.items():
                    if ts not in _tss:
                        continue
                    print("Station = {0}".format(ts))
                    _uuts = sorted(ts_data.keys()) if uuts == ['ALL'] else uuts
                    print(_uuts)
                    for uut, uut_data in ts_data.items():
                        if uut not in _uuts:
                            continue
                        if uut_data.get('enabled', False):
                            print("UUT = {0}".format(uut))
                            _answers = uut_data.get('answers', None) if not answers else answers
                            index += 1
                            run_dict[index] = {'prod_line': pl,
                                               'area': area,
                                               'test_station': ts,
                                               'container': uut,
                                               'mode': uut_data.get('mode', 'DEBUG'),
                                               'start_delay': uut_data.get('start_delay', 1),
                                               'timeout': uut_data.get('timeout', 10000),
                                               'answers': _answers}
        print("Run Dict = {0}".format(run_dict))
        return run_dict

    def run_multi_container(self, pl, area, tss, uuts, answers=None):
        """ Run Multiple Containers in Parallel

        :param (str) pl: Product Line (singular)
        :param (str) area: Test Area (singular)
        :param (str) tss: Test Station
        :param (str|list) uuts: UUT(s)
        :param (list) answers: Prepopulated answers.
        :return:
        """

        # Input params
        # ------------
        print("pl={0}, area={1}, tss={2}, uuts={3}, answers={4}".format(pl, area, tss, uuts, answers))
        run_dict = self._build_run_dict(pls=pl, areas=area, tss=tss, uuts=uuts, answers=answers)
        if not run_dict:
            print("*****")
            print("ERROR: Nothing to run; check citp_uut_unittest_def module.")
            print("*****")
            assert False
            return

        # Run it !
        # --------
        if self.pytest_continue:
            results = apruntool.run_apollo_containers_explicitly(run_dict)
        else:
            print("******")
            print("PYTEST: a previous test failed; aborting future tests.")
            print("******")
            assert False
            return

        print("Mult-Container Summary")
        for result in results:
            print("{0} : {1}".format(result.identifier, result.status))

        for result in results:
            if result.status != apruntool.TestResult.PASS:
                for i in range(1, 4):
                    print("=" * 100)
                print("{0} : {1}".format(result.identifier, result.status))
                print("=" * 30)
                print("{0}".format(result.log))
                self.pytest_continue = False

        sys.stdout.flush()
        sys.stderr.flush()

        for result in results:
            assert result.status == apruntool.TestResult.PASS
        return

    def run_single_container(self, pl, area, ts, uut, answers=None):
        result = apruntool.run_apollo_container(prod_line=pl,
                                                area=area,
                                                test_station=ts,
                                                container=uut,
                                                mode='DEBUG',
                                                answers=answers)
        assert result.status == apruntool.TestResult.PASS
        return
