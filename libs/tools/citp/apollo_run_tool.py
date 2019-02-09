#!/usr/bin/python
# encoding: utf-8

"""Apollo Run Tool
Use this tool for running containers from the CLI.
Typical usage is for unit testing.
"""

import subprocess
from time import time
from time import sleep
from collections import namedtuple
import ConfigParser
import os


__title__ = "Apollo Run Tool"
__version__ = '1.4.1'
__author__ = ['sdubrul', 'bborel']


ContainerId = namedtuple("ContainerId", ["prod_line", "area", "test_station", "container", "mode", "answers", "start_delay", "timeout"])


class Timer(object):
    """Timer context manager that helps to time actual execution time"""
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time()
        return self

    def __exit__(self, *args):
        self.end = time()
        self.seconds = self.end - self.start
        if self.verbose:
            print("Elapsed time: %s sec" % self.seconds)


class TestResult(object):

    PASS = "PASS"
    FAIL = "FAIL"
    ABORT = "ABORT"
    HTTP_ERROR = "HTTP_ERROR"
    GEN_ERROR = "ERROR"

    error_lookup = {
        200: PASS,
        417: FAIL,
        500: ABORT
    }

    def __init__(self, status, log, error, time, identifier):
        self.status = status
        self.log = log
        self.time = time
        self.error = error
        self.identifier = identifier

    def __str__(self):
        return "{0}: {1} in {2} sec".format(self.identifier, self.status, self.time)

    def __eq__(self, other):
        return True if self.status == other else False


def delay(start_delay, identifier):
    if start_delay != 0:
        print(str(identifier) + ": sleep " + str(start_delay))
        sleep(start_delay)


def _run_apollo_container_with_container_id(c):
    """
    Helper function that accepts a tuple rather than separate keyword arguments
    :param c:
    :return:
    """
    return run_apollo_container(prod_line=c.prod_line, area=c.area, test_station=c.test_station,
                                container=c.container, mode=c.mode, answers=c.answers, start_delay=c.start_delay, timeout=c.timeout)


def run_apollo_containers(prod_line, area, test_station, containers, mode='PROD', answers=None, start_delay=0, timeout=10000):
    """
    Call a bunch of apollo containers through the apollo cli in parallel.
    Note: This assumes ALL containers have the same prod_line, area, test_station, mode, answers, and start_delay.
    :param prod_line:
    :param area:
    :param test_station:
    :param containers:
    :param mode:
    :param answers:
    :param start_delay:
    :param label:
    :return:
    """
    container_ids = [ContainerId(prod_line, area, test_station, container, mode, answers, index * start_delay, timeout)
                     for index, container in enumerate(containers)]

    # setup a process pool
    from multiprocessing import Pool
    process_count = len(container_ids)
    print("Pool process count = {0}".format(process_count))
    pool = Pool(processes=process_count)

    # launch & return
    results = pool.map(_run_apollo_container_with_container_id, container_ids)
    return results


def run_apollo_containers_explicitly(run_dict):
    """
    Call a set of apollo containers (each with explicit data) through the apollo cli in parallel.
    :param run_dict = {
     index: {
        prod_line:
        area:
        test_station:
        container:
        mode:
        answers:
        start_delay:
        timeout:
        }, ... }
    :return:
    """
    container_ids = []
    for index in sorted(run_dict):
        ctdict = run_dict[index]
        container_ids.append(ContainerId(ctdict['prod_line'], ctdict['area'], ctdict['test_station'], ctdict['container'],
                                         ctdict['mode'], ctdict['answers'], index * ctdict['start_delay'], ctdict['timeout']))

    # setup a process pool for an iterable
    from multiprocessing import Pool
    process_count = len(container_ids)
    print("Pool process count = {0}".format(process_count))
    pool = Pool(processes=process_count)

    # launch & return
    results = pool.map(_run_apollo_container_with_container_id, container_ids)
    return results


def load_cli_cmd():
    """
    Return the default command if is not overwritten in a settings file
    This is created per request of the developers to try out our test suite on non supported Apollo boxes.
    :return:
    """
    default = "python2.7 /opt/cisco/constellation/apollocli.py"

    folder = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(folder, "settings.ini")

    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(path))
        cli_cmd = config.get("settings", "cli_cmd")
        print("Custom cli_cmd: %s" % cli_cmd)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, IOError):
        cli_cmd = default

    return cli_cmd


def run_apollo_container(prod_line, area, test_station, container, mode='PROD', log_level='DEBUG', answers=None, start_delay=0, timeout=10000):
    """Run a container through cli

    usage: apollocli.py [-h] [--url URL] [--action ACTION] [--body BODY]
                        [--content-type CONTENT_TYPE] [--input-file INPUT_FILE]
                        [--production-line PRODUCTION_LINE] [--area AREA]
                        [--test-station TEST_STATION] [--name CONTAINER]
                        [--log-level LOG_LEVEL] [--schedule] [--job-name JOBNAME]
                        [--job-schedule JOBSCHEDULE] [--trigger-type TRIGGER_TYPE]
                        [--version APOLLO_VERSION] [--user USERNAME]
                        [--pass PASSWORD] [--mode MODE] [--timeout TIMEOUT]

    optional arguments:
      -h, --help            show this help message and exit
      --url URL, -url URL   URL of the webservice
      --action ACTION, -a ACTION
                            GET/POST
      --body BODY, -b BODY  This option can be used for multiple purposes: (a)
                            inline dictionary when calling a cesium webservice;
                            this can be the inputdictionary (b) inline list
                            (answers list) when running a container that requires
                            answers to pre-sequence questions e.g: ['sn123',
                            'pid2322'] Note: Using --input-file is easier to not
                            have to escape quotes and foramtting correctly than
                            when used inline
      --content-type CONTENT_TYPE, -c CONTENT_TYPE
                            Content-type of --input-file argument. One of ['JSON',
                            'XML']
      --input-file INPUT_FILE, -i INPUT_FILE
                            input body as a json or xml file for cesium
                            webservices; answers-list when running containers for
                            answering pre-sequence questions
      --production-line PRODUCTION_LINE, -pl PRODUCTION_LINE
                            Production line of this container
      --area AREA, -ar AREA
                            Test area
      --test-station TEST_STATION, -ts TEST_STATION
                            Test Station
      --name CONTAINER, -cn CONTAINER
                            Container name
      --log-level LOG_LEVEL, -ll LOG_LEVEL
                            Set the log level of the sequence logs of interest.
                            The log messages will appear on stdout just as the
                            response to all cli calls
      --schedule, -s        Don't run this container, but schedule it instead.
                            Optional options --trigger-type and --job-schedule may
                            be used to conform t
      --job-name JOBNAME, -jn JOBNAME
      --job-schedule JOBSCHEDULE, -js JOBSCHEDULE
                            File containing a dict conforming to jobschedule as
                            defined in apollo/websvcs/scheduling/schedule
      --trigger-type TRIGGER_TYPE, -tt TRIGGER_TYPE
                            Trigger type attribute of the scheduling webservice
      --version APOLLO_VERSION, -v APOLLO_VERSION
                            check if running the latest version of apollo
      --user USERNAME, -u USERNAME
      --pass PASSWORD, -p PASSWORD
      --mode MODE, -m MODE  The mode to run a container in: DEBUG/PROD
      --timeout TIMEOUT, -t TIMEOUT
                            Time to wait until, for a response

    Ex.
    python apollocli.py -pl UAT -ar SYSFT -ts "Test helloworld" -cn "hello world"

    :param prod_line:
    :param area:
    :param test_station:
    :param container:
    :param mode:
    :param answers:
    :param start_delay:
    :param timeout:
    :return:

    """

    cli_cmd = load_cli_cmd()

    status = None

    delay(start_delay, container)

    if True:
        call = '{cli_cmd} -pl "{prod_line}" --area "{area}" -ts "{test_station}" -cn "{container}" --log-level {log_level} ' \
               '--timeout {timeout} --m {mode}'.format(cli_cmd=cli_cmd, prod_line=prod_line, area=area,
                                                       test_station=test_station, container=container,
                                                       log_level=log_level, timeout=timeout, mode=mode)
        # add the answer list to the call if there is one provided
        if answers:
            answers_string = ' --body "{}"'.format(answers.__str__())
            call = call + answers_string
        print("{}: {}".format(container, call))
        # call_split = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', call)  # prepare the call for calling

    if False:
        # James Blue method (does not work for subprocess).
        call_args = cli_cmd.split()
        call_args += ['-pl', prod_line, '--area', area, '-ts', test_station, '-cn', container, '--timeout', timeout, '-m', mode, '-ll', log_level]
        if answers:
            call_args.append('--body')
            call_args.append(str(answers))

    raw_output = ''
    log = ''
    error = ''
    with Timer() as timer:
        try:
            raw_output = subprocess.check_output(call, shell=True)
        except subprocess.CalledProcessError as e:
            # Executing the command failed.
            # Returning gracefully with ERROR as status and the exception as error message
            print(e)
            status = "ERROR"
            error = str(e)
            log = raw_output
        except Exception as e:
            # Any other general exceptions?
            print(e)
            status = "ERROR"
            error = str(e)
            log = raw_output

    # if all went well we can start processing the output
    print("=" * 30)
    if status != "ERROR":
        print("INFO: Subprocess result scanning...")
        # split the log and the result dict from the last line out of the raw output
        output_list = raw_output.splitlines()
        log = "\n".join(output_list[:-1])
        output_dict = ''
        for line in output_list:
            # run thru all, we want the "last appearance"
            if ('Container: ' in line) and (', Result: ' in line):
                output_dict = line
            elif 'Result: ' in line:
                output_dict = line

        # get the results from the output dict.
        # Kinda hacky for now..
        items = output_dict.split('Error: ')

        # grab error
        if len(items) > 1:
            error = items[1]
        else:
            error = ""

        # grab status
        result_raw = items[0]
        if "PASS" in result_raw:
            status = TestResult.PASS
        elif "FAIL" in result_raw:
            status = TestResult.FAIL
        elif "SKIPPED" in result_raw:
            # Mark any SKIPPED as a PASS since skips are considered "don't care"
            status = TestResult.PASS
        else:
            # Something went wrong as we didn't got a status back. (Like container not found)
            # Set status to error and save the output as error
            status = "ERROR"
            error = result_raw
    else:
        print("NOTICE: Subprocess produces an exception error!")

    result = TestResult(status, log, error, timer.seconds, container)

    print("=" * 30)
    print("RESULT")
    print("=" * 30)
    print("result.status     = {0}".format(result.status))
    print("result.log (len)  = {0}".format(len(result.log)))
    print("result.error      = {0}".format(result.error))
    print("result.timer      = {0}".format(result.time))
    print("result.container  = {0}".format(result.identifier))
    print("result.log        = \n{0}".format(result.log))

    return result


def run_apollo_test(url, identifier=0, start_delay=0):
    """
    Call an apollo sequence trough the apollo cli.
    :param url:
    :param identifier:
    :param start_delay:
    :return:
    """

    delay(start_delay, identifier)

    call = "python2.7 /opt/cisco/constellation/apollocli.py --url %s" % url
    print(str(identifier) + ": " + call)

    # call a sequence and capture the elapsed time
    with Timer() as timer:
        output = subprocess.check_output(call.split())

    # Harsh has a function lib.recursive_eval for dict in dict kinda things
    print(str(identifier) + ": " + output)

    # parse the return code, default to HTTP_ERROR
    status_code = eval(output)["status"]
    status = TestResult.error_lookup.get(status_code, status_code)

    return TestResult(status, "", timer.seconds, identifier)


def run_apollo_test_with_tuple(tuple_urls):
    """
    Helper function that accepts a tuple rather then separate keyword arguments
    :param tuple_urls:
    :return:
    """
    url, identifier, start_delay = tuple_urls
    return run_apollo_test(url, identifier, start_delay)


def run_apollo_tests(urls, start_delay=1):
    """
    Call a bunch of apollo sequence through the apollo cli in parallel.
    :param urls:
    :param start_delay:
    :return:
    """

    # make a new list containing a typle of url, identifier & start delay
    url_tuples = [(url, identifier, identifier * start_delay) for identifier, url in enumerate(urls)]

    # setup a process pool
    from multiprocessing import Pool
    pool = Pool(processes=len(urls))

    # launch & return
    results = pool.map(run_apollo_test_with_tuple, url_tuples)
    return results


if __name__ == "__main__":
    print("If you run this file it's only to test it out..")
    result = run_apollo_container("UAT", "SYSFT", "HELLOWORLD", 'HELLOWORLD')
