import subprocess
import os
import time
import zipfile
import shutil

__title__ = 'Apollo Control'
__author__ = ['sdubrul', 'bborel']
__version__ = '1.7.0'


class ApolloControl(object):
    """
    Apollo control helper class that provides the following:
    1. Start/Stop/Restart/Query Apollo,
    2. Add (with validation) config & script links directly in Apollo, and
    3. Clear the most recent Apollo log.
    """

    PATH = "/opt/cisco/constellation"
    START_CMD = "apollo start",
    STOP_CMD = "apollo stop",
    STATUS_CMD = "apollo status",
    VERSION_CMD = "apollo version",

    APOLLO_PATH = os.path.join(PATH, "apollo")
    CONFIG_PATH = os.path.join(APOLLO_PATH, "config")
    SCRIPTS_PATH = os.path.join(APOLLO_PATH, "scripts")
    LOGFILE_PATH = os.path.join(APOLLO_PATH, "logs")
    APOLLO_LOG_DIRS_TO_ZIP = ['logs', 'connections_logs', 'sequences_logs']

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.thispath = os.path.dirname(os.path.abspath(__file__))

    def __str__(self):
        return "ApolloControl class"

    def __repr__(self):
        return '{0} v{1}'.format(self.__class__.__name__, __version__)

    def status(self):
        """Return True if apollo is running, else False"""
        try:
            if "Apollo daemon is running" in subprocess.check_output("apollo status".split()):
                return True
            else:
                return False
        except subprocess.CalledProcessError:
            print("Unable to get Apollo status.")
            return False

    def stop(self):
        print("* Stopping Apollo")
        for attempt in range(1):
            try:
                subprocess.check_output("apollo stop".split())
            except subprocess.CalledProcessError:
                print("Apollo stop raised an error.")
                raise

    def start(self, args=''):
        """
        $ apollo -h start
        usage: apollo.py [-h] [--consoledebug] [--filter FILTER_PHRASE]
                         [--log_level CONSOLE_LOG_LEVEL] [--noauth]
                         [--auth AUTH_OPTION] [--noproxy] [--noscore] [--nolog]
                         [--noappreg] [--noexamples] [--multiversion] [--monitor]
                         [--verbose] [--noscheduler] [--notestdata]

        optional arguments:
          -h, --help            show this help message and exit
          --consoledebug        enable the log messages to be sent to the console AND
                                to the file
          --filter FILTER_PHRASE
                                filter console ouput (may be comma-delimited)
          --log_level CONSOLE_LOG_LEVEL
                                set console log level ['info', 'debug', 'warning',
                                'error']
          --noauth              disable cert authorization
          --auth AUTH_OPTION    enable cert authorization
          --noproxy             run apollo in standalone mode using port 4433
          --noscore             disable scorekeeper
          --nolog               disable logging
          --noappreg            disable app registry
          --noexamples          do not add examples to configuation
          --multiversion        enable different code versions
          --monitor             monitor system resources (memory, cpu, network
                                connections)
          --verbose             prints --monitor information to screen
          --noscheduler         prints --disable the Apollo scheduler
          --notestdata          prints --disable sending the test data to the CSA
        :param args: string containing any of the optional args above.
        :return:
        """
        print("* Starting Apollo")
        cmd = "{0} {1} {2}".format('apollo', args, 'start')
        print("*  cmd={0}".format(cmd))
        try:
            subprocess.check_call(cmd.split())
        except subprocess.CalledProcessError:
            print("Apollo start raised an error.")
            raise

    def version(self):
        try:
            version = subprocess.check_output("apollo version".split()).strip()
        except Exception:
            version = "unknown"
        if self.verbose:
            print("* Apollo version: %s" % version)
        return version

    def control_version(self):
        try:
            version = subprocess.check_output("rpm -q apollo-ctrl".split()).strip()
        except Exception:
            version = "unknown"
        if self.verbose:
            print("* Apollo-ctrl version: %s" % version)
        return version

    def restart(self):
        print("* Restart Apollo")
        self.stop()
        self.start()

        print("* Waiting for apollo ...")
        start_time = time.time()
        while time.time() < start_time + 10:
            if self.status():
                print("Apollo is running")
                break
            else:
                time.sleep(1)
        else:
            raise RuntimeError("Apollo didn't start within 10 seconds")

    def add_config_link(self, source_path):
        """
        Link a new folder under apollo/config.
        :param source_path:
        :return:
        """
        file_path, file_name = os.path.split(source_path)
        destination_path = os.path.join(self.CONFIG_PATH, file_name)

        return self._add_link_with_validation(source_path, destination_path)

    def add_source_link_to_scripts(self, source_path, dest_name=None):
        """
        Link a new folder under apollo/scripts.
        Main reason to do this is to get a Jenkins workspace linked in apollo/scripts.
        When a dest_name is provided we'll use that one otherwise the source name is used.
        :param source_path:
        :param dest_name:
        :return:
        """
        print("*  {0} {1}".format(source_path, dest_name))
        file_path, file_name = os.path.split(source_path)
        destination_name = dest_name if dest_name else file_name
        destination_path = os.path.join(self.SCRIPTS_PATH, destination_name)

        return self._add_link_with_validation(source_path, destination_path)

    def _add_link_with_validation(self, source_path, destination_path):
        """Add a symlink with some specifics to handle our use cases
        1. If the link doesn't exist: create it
        2. If this exact link exists: fine
        3. If the link point's to somewhere else: overwrite it
        4. If the link would equal the target: doesn't make sense but goal is accomplished anyway. fine
        5. If link is in a directory that doesn't exists create the dir then create the link under it.
        6. If the destination is something else: raise an exception. Nothing we can do in this case.
        :param source_path:
        :param destination_path:
        :return:
        """
        if os.path.islink(destination_path) or os.path.exists(destination_path):
            if source_path == destination_path:
                # case 4
                # No need to link as the target is on the given location already.
                print("*  Symlink: {0} --> {1}".format(source_path, destination_path))
                return destination_path
            elif os.path.islink(destination_path):
                if os.path.realpath(destination_path) == source_path:
                    # case 2
                    #  Link is already in place.
                    print("*  Existing Symlink: {0} --> {1}".format(source_path, destination_path))
                    return destination_path
                else:
                    # case 3
                    print("*  Removing previous source link: {0}".format(destination_path))
                    os.unlink(destination_path)
            else:
                # case 6
                raise EnvironmentError("Can't link as the destination path already exists! %s" % destination_path)
        else:
            # case 1
            # Symlink dst does not exists.
            pass

        # Add any subdirs needed for the links
        self._add_subdir(destination_path)

        # If we reach this point we're actually going to make the symlink
        print("*  Adding Symlink: %s --> %s" % (source_path, destination_path))
        os.symlink(source_path, destination_path)
        # Do not perform chown or chmod on links since its not necessary (links inherit),
        # note: doing so could change the SVN archive!!
        return destination_path

    def _add_subdir(self, path):
        subdir = os.path.dirname(path)
        if not os.path.exists(subdir):
            self._add_subdir(subdir)
            print("*  Creating package dir for symlinks: {0}".format(subdir))
            os.mkdir(subdir)
            # os.chmod(subdir, mode=0777)          <-- need to use sudo  # do this since umask can prevent mode in mkdir
            # gid = grp.getgrnam('apollo').gr_gid  <-- need to use sudo
            # os.chown(subdir, gid, gid)           <-- need to use sudo
            if False:
                self.sudo_cmd('chmod 777 {0}'.format(subdir))
                self.sudo_cmd('chown apollo:apollo {0}'.format(subdir))
            if not os.path.exists(os.path.join(subdir, '__init__.py')):
                shutil.copy2(os.path.join(self.thispath, '__init__.py'), os.path.join(subdir, '__init__.py'))

    def sudo_cmd(self, cmd):
        output = ''
        try:
            cmd = 'sudo {0}'.format(cmd)
            output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e)
            print(e.output)
        finally:
            return output

    def remove_logs(self):
        print('* NOT removing Apollo logs')
        return
        print('* Removing Apollo logs')
        for root, _, files in os.walk(self.LOGFILE_PATH):
            for f in files:
                full_file_path = os.path.join(root, f)
                try:
                    os.remove(full_file_path)
                except OSError as e:
                    if not e.errno == 2:
                        raise

    def zip_logs(self, destination, verbose=False):
        print(' ')
        print('* Zipping logs to %s' % destination)
        zipf = zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.LOGFILE_PATH):
            if verbose:
                print("Root={0}  Dirs={1}".format(root, dirs))
            if os.path.split(root)[1] in self.APOLLO_LOG_DIRS_TO_ZIP:
                for file in files:
                    if verbose:
                        print("File={0}".format(file))
                    zipf.write(os.path.join(root, file))
        zipf.close()
