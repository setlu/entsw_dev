#! /usr/local/bin/python
# -*- coding: UTF-8 -*-
"""
========================================================================================================================
Pathfinder
========================================================================================================================
"""

# Python
# ------
import sys
import logging
import argparse
import importlib

# BU Lib
# ------
from ..utils.common_utils import func_details

__author__ = "bborel"
__title__ = "Pathfinder"
__version__ = "2.0.0"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s | %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


class PathFinder(object):
    """
    This class allows for the following:
      1) the creation of a psuedo-State Machine with N number of nodes and up to N*(N-1) number of paths, and
      2) a method of finding the "best path" to get from one arbitrary node to another arbitrary node as required by
         a given request.
    The psuedo-state machine is made up of nodes and path segments. Each node represents a "state" and each
    path segment represents the most immediate next state a node can transistion to with a single step.
    This class does not retain any historical information (hence psuedo description) but it does provide
    for a way to describe any node that needs to use its previous node(s) via a "stateful" boolean flag descriptor.
    It is the job of the inheriting parent class to keep track of path history where it is needed and use the "stateful"
    flagged nodes as required.

    An example of creating a psuedo-state machine definition is given below for a sample product mode arrangement.
    The entire node table can be created in a dictionary first and passed when instantiating the class
    or the table can be created via the object method.
    Adding nodes in the table have the following syntax:
         .add_node(<STRING of node name>, <TUPLE LIST of next immediate node hops>)
         The tuple list contains (<STRING of node name>, <INTEGER path cost>).

                                                 smd = {'statemachine': {<state table dict>}}
                                                 pf = PathFinder(**smd)
                      [ BTLDR ]                  --OR--
                     * /    * \                  pf = PathFinder()
                   5/ /      \ \9                pf.add_node('BTLDR',      [('LINUX', 10),('IOS', 9)])
                   / /10     5\ \                pf.add_node('LINUX',      [('BTLDR', 5),('STARDUST', 4)])
                  / *          \ *               pf.add_node('IOS',        [('BTLDR', 5)])
               [LINUX]         [IOS]             pf.add_node('STARDUST',   [('LINUX', 3),('TRAF', 10),('DIAG', 8)])
                 * |                             pf.add_node('TRAF',       [('STARDUST', 5), ('DIAG', 1), ('SYMSH', 5)])
                3| |4                            pf.add_node('DIAG',       [('STARDUST', 3),('SYMSH', 3), ('TRAF',  1)])
                 | *                             pf.add_node('SYMSH',      [('DIAG', 3), ('TRAF', 5)], stateful=True)
               [STARDUST]
               * /    * \                        Each transition or "path segment" from one node to the next is given a
             5/ /      \ \8                      relative number (usually time-based measure) for "cost". This is useful
             / /10     3\ \                      if 3 or more state nodes can transition between each other.  (Our
            / *    1     \ *                     specific example has multiple routes between Stardust, Traf, & Diag.)
         [TRAF]--------*[DIAG]
         [  " ]*--------[ "  ]                   Ex.#1: Obtain least cost path
          * |      1     * |                            from "modeA" (bootloader) to "modeB" (sym shell):
         5| |5          3| |3                    bestpath = pf.get_path('BTLDR', 'SYMSH')
          | |            | *                     bestpath  is  ['BTLDR', 'LINUX', 'STARDUST', 'DIAG', 'SYMSH']
          | +---------*[SYMSH]                   Ex.#2: Obtain min cost path
          +------------[  "  ]                          from "modeA" (sym shell) to "modeB" (traf):
                                                 bestpath = pf.get_path('SYMSH', 'TRAF')
                                                 bestpath is  ['SYMSH', 'DIAG', 'TRAF']

    As previously noted, if a dict is defined for the state machine table it will have the form:
    statetable = {
    <node> or (<node>, <0 or 1>) :  [list of destination nodes w/ cost values],
    ...
    }
    Key is either the node or a tuple with node and 0/1 boolean to indicate if the node is "stateful"

    Application of this class should be to inherit it with a higher-level class that can use the
    bestpaths for device manipulation.
    See "machinemanager.py" as an example of using this class.
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: Dictionary input
                      'statemachine' is optional; it can be predefined and supplied here or built using the
                          'add_node()' method as described above.
        :return:
        """
        sys.setrecursionlimit(1000)

        self.__statemachine_define = kwargs.get('statemachine', {})  # Required when not using .add_node()
        self.verbose = kwargs.get('verbose', False)

        self.__initialize_statemachine(self.__statemachine_define)
        return

    def __str(self):
        doc = "{0}{1}\n{2}{3}\n{4}{5}\n{6}{7}\n{8}{9}".\
            format(self.__class__.__name__, self.__doc__,
                   self.add_node.__name__, self.add_node.__doc__,
                   self.get_path.__name__, self.get_path.__doc__,
                   self.get_path_cost.__name__, self.get_path_cost.__doc__,
                   self.get_least_cost_node.__name__, self.get_least_cost_node.__doc__)
        return doc

    def __repr__(self):
        return "{0} v{1} ({2})".format(self.__class__.__name__, __version__, __name__)

    # Properties -------------------------------------------------------------------------------------------------------
    @property
    def statemachine(self):
        return self.statedefinitions, self.statefulnodes

    @statemachine.setter
    def statemachine(self, newvalue):
        self.__statemachine_define = newvalue
        self.__initialize_statemachine(newvalue)

    # USER Methods ----------------------------------------------------------------------------------------------------------
    #
    def show_version(self):
        log.info(self.__repr__())

    @func_details
    def add_node(self, node, destnodelist=[], stateful=False):
        """
        Add a "node" to the state machine.  Each node contains a list of "next immediate nodes" that the
        indicated (source) node can go to (i.e. destination nodes).
        :param (str) node: String tag describing the node for adding in the dictionary of nodes (ex. node='DIAG').
        :param (list) destnodelist: A tuple list describing all "next immediate nodes" & the path costs that lead from
               node A to node B, node A to node C, etc.
               The format is '(<next node>, <cost>), (<next node>, <cost>), ...';
               ex. destnodelist=[('BOOTLDR', 3), ('LINUX', 1), ('IOS', 8)].
               The "cost" number is typically set relative to a measure of time it takes to transition
               from one node to the next. Type is int.
        :param (bool) stateful: True = A stateful node, whereby entry/exit must be tracked.
        :return: True if the node add was successful.
        """
        ret = False
        try:
            if node in self.statedefinitions:
                log.warning("{0} already exists, destination node list will be updated instead.".format(node))
            if len(destnodelist) == 0:
                # Cannot get into this node.
                raise Exception("{0} is an isolated node.".format(node))
            else:
                result = self.__validatedestnodelist(destnodelist)
                if not result[0]:
                    raise Exception("{0}".format(result[1]))
            # Append this node to the state table definition and indicate it is not stateful.
            self.statedefinitions[node] = destnodelist
            self.statefulnodes[node] = stateful
            ret = True
        except Exception as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        finally:
            return ret

    @func_details
    def get_path(self, srcnode='', dstnode='', pathtype='MINCOST', withcost=False, followpath=[]):
        """
        Get the path for the given source & destination nodes and path type.
        Primarily intended to be used by other processing functions which should provide direct action to
        act on the "best path" that is returned.
        :param (str) srcnode: Source node; starting point.
        :param (str) dstnode: Destination node; ending point.
        :param (str) pathtype: Type of path to return: MINCOST, MAXCOST, MINHOP, MAXHOP.
        :param (bool) withcost: The return output will include costs for each transition as a tuple.
        :param (list) followpath: Force the output path to follow this path or path segment.
                                  If this is not possible, the follow path will be ignored.
        :return: List of nodes in ordered sequence representing a 'path' to the desired destination.
        """
        pathsequence = []
        try:
            allpossiblepaths = {}
            allpossiblepathmetrics = {}

            # Validate the inputs
            if srcnode not in self.statedefinitions:
                msg = "Source Mode '{0}' is unknown.".format(srcnode)
                raise Exception(msg)
            if dstnode not in self.statedefinitions:
                msg = "Destination Mode '{0}' is unknown.".format(dstnode)
                raise Exception(msg)
            if type(followpath) is not list:
                msg = "Followpath '{0}' is not a list.".format(followpath)
                raise Exception(msg)

            # Do the heavy work!
            self.__traverse(srcnode, dstnode, allpossiblepaths)
            pathmetrics = self.__pathmetrics(allpossiblepaths, allpossiblepathmetrics)

            # More input validation at post-processing.
            if pathtype not in pathmetrics:
                raise Exception("Unknown path type requested.")

            # Do some detailed printing if requested.
            if self.verbose:
                log.debug("-" * 60)
                log.debug("ALL_PATHS = {0} --> {1}".format(srcnode, dstnode))
                for i in range(1, len(allpossiblepaths) + 1):
                    log.debug("{0} : {1}  Metrics={2}".format(i, allpossiblepaths[i], allpossiblepathmetrics[i]))
                log.debug("Summary Metrics = {0}".format(pathmetrics))

            # Build the specific return output format
            # Samples:
            #  allpossiblepathmetrics = {1: (11, 4), 2: (9, 4), 3: (11, 5), 4: (4, 3), 5: (6, 4), 6: (11, 3),
            #                            7: (9, 3), 8: (11, 4), 9: (11, 2), 10: (21, 4), 11: (23, 5)}
            #  allpossiblepaths = {1: [('s1', 0), ('s2', 1), ('s3', 5), ('s4', 4), ('s5', 1)],
            #                      2: [('s1', 0), ('s2', 1), ('s3', 5), ('s6', 1), ('s5', 2)],
            #                      3: [('s1', 0), ('s2', 1), ('s3', 5), ('s6', 1), ('s7', 3), ('s5', 1)],
            #                      4: [('s1', 0), ('s2', 1), ('s6', 1), ('s5', 2)],
            #                      5: [('s1', 0), ('s2', 1), ('s6', 1), ('s7', 3), ('s5', 1)],
            #                      6: [('s1', 0), ('s3', 6), ('s4', 4), ('s5', 1)],
            #                      7: [('s1', 0), ('s3', 6), ('s6', 1), ('s5', 2)],
            #                      8: [('s1', 0), ('s3', 6), ('s6', 1), ('s7', 3), ('s5', 1)],
            #                      9: [('s1', 0), ('s4', 10), ('s5', 1)],
            #                     10: [('s1', 0), ('s4', 10), ('s3', 8), ('s6', 1), ('s5', 2)],
            #                     11: [('s1', 0), ('s4', 10), ('s3', 8), ('s6', 1), ('s7', 3), ('s5', 1)]}
            #  pathmetrics = {'MAXHOP': (3, 5), 'MAXCOST': (11, 23), 'MINCOST': (4, 4), 'MINHOP': (9, 2)}
            #  pathtype = 'MINCOST'
            #  pathsequence = ['s1', 's2', 's6', 's5']
            #  pathsequence (withcost) = [('s1', 0), ('s2', 1), ('s6', 1), ('s5', 2)]
            #
            if len(allpossiblepaths) > 0:
                statesonlypathsequence = [segment[0] for segment in allpossiblepaths[pathmetrics[pathtype][0]]]

                # 1. Check if a "followpath" was stipulated.
                followpathmsg = ''
                if followpath:
                    if str(followpath)[1:-1] in str(statesonlypathsequence)[1:-1]:
                        log.info("Followpath confirmed.")
                        followpathmsg = ' w/ {0}'.format(followpath)
                    else:
                        # Is there a path that includes the "followpath". Have to hunt thru allpossiblepaths.
                        allpossiblefollowpaths = {}
                        allpossiblefollowpathmetrics = {}
                        i = 0
                        for pathindex in range(1, len(allpossiblepaths) + 1):
                            statesonlypathsequence = [segment[0] for segment in allpossiblepaths[pathindex]]
                            if str(followpath)[1:-1] in str(statesonlypathsequence)[1:-1]:
                                i += 1
                                allpossiblefollowpaths[i] = allpossiblepaths[pathindex]
                        if allpossiblefollowpaths:
                            # Rebuild allpossible... based on the 'followpath' matches.
                            pathmetrics = self.__pathmetrics(allpossiblefollowpaths, allpossiblefollowpathmetrics)
                            allpossiblepaths = allpossiblefollowpaths
                            allpossiblepathmetrics = allpossiblefollowpathmetrics
                            statesonlypathsequence = [segment[0] for segment in allpossiblepaths[pathmetrics[pathtype][0]]]
                            followpathmsg = ' w/ {0}'.format(followpath)
                            if self.verbose:
                                log.debug("ALL_PATHS w/ {2} = {0} --> {1}".format(srcnode, dstnode, followpath))
                                for i in range(1, len(allpossiblepaths) + 1):
                                    log.debug("{0} : {1}  Metrics={2}".format(i, allpossiblepaths[i], allpossiblepathmetrics[i]))
                                log.debug("Summary Metrics w/ {1} = {0}".format(pathmetrics, followpath))
                        else:
                            log.info("No followpath alternatives found. The standard path will be used.")

                # 2. Check if the "costing feature" was requested.
                if withcost:
                    pathsequence = allpossiblepaths[pathmetrics[pathtype][0]]
                else:
                    pathsequence = statesonlypathsequence

                # Print detail
                log.info("Best Path for {0}{2} = {1}\n".format(pathtype, pathsequence, followpathmsg)) if self.verbose else None

        except Exception as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        finally:
            return pathsequence

    @func_details
    def get_path_cost(self, srcnode='', dstnode='', pathtype='MINCOST'):
        """ Get the Path Cost
        :param (str) srcnode: Starting node
        :param (str) dstnode: Ending node
        :param (str) pathtype:
        :return:
        """
        pathsequence = self.get_path(srcnode=srcnode, dstnode=dstnode, pathtype=pathtype, withcost=True)
        cost = 0
        for node in pathsequence:
            cost += node[1]
        return cost

    @func_details
    def get_least_cost_node(self, srcnode, dstnodes):
        """ Get the Least Costly Path
        Select one node from a list of nodes which has the least cost path starting at the srcnode.
        :param (str) srcnode: Staring node
        :param (list) dstnodes: Nodes to choose from
        :return (str): Single node name.
        """
        dstnodes = [dstnodes] if not isinstance(dstnodes, list) else dstnodes
        costs = [self.get_path_cost(srcnode=srcnode, dstnode=dstnode, pathtype='MINCOST') for dstnode in dstnodes]
        n = costs.index(min(costs))
        if self.verbose:
            log.debug("Search Nodes = {0}".format(dstnodes))
            log.debug("Costs        = {0}".format(costs))
        return dstnodes[n]

    @func_details
    def print_state_machine(self):
        """
        Print the state machine table and check that it is a valid table.
        :return:
        """
        log.info("=" * 80)
        log.info("STATE MACHINE TABLE")
        log.info("{0:<25} {1:<8} {2}".format("Node", "Stateful", "Destination Nodes"))
        log.info("-" * 25 + " " + "-" * 8 + " " + "-" * 45)
        for node in sorted(self.statedefinitions.keys()):
            log.info("{0:<25} {1:<8} {2}".format(node, self.statefulnodes[node], self.statedefinitions[node]))
        if not self.__validatemachinetable():
            log.info("Table did NOT validate!")
        else:
            log.info("Table is valid.")
        log.info("=" * 80)
        return

    # INTERNAL methods -------------------------------------------------------------------------------------------------
    #
    def __initialize_statemachine(self, statemachine_define):
        self.statedefinitions = {}
        self.statefulnodes = {}

        # If a dict method was used for input, process the data into the appropriate attributes.
        #  The keys in a statemachine_define dict can be a tuple (for stateful nodes), therefore need to break apart.
        if statemachine_define:
            for k in statemachine_define:
                if type(k) is str:
                    self.statedefinitions[k] = statemachine_define[k]
                    self.statefulnodes[k] = False
                elif type(k) is tuple:
                    kn = k[0]
                    self.statedefinitions[kn] = statemachine_define[k]
                    self.statefulnodes[kn] = k[1]

    def __traverse(self, src, dst, validpathcollection={}, currentpath=[], _pathindex=1, _originalsrc=None):
        """
        Recursively traverse the the entire state machine of nodes and their paths to determine all possible paths from
        the given source to the given destination.
        :param src: Source Node
        :param dst: Destination Node
        :param validpathcollection: Dictionary collection of all possible valid paths indexed by incremental key number.
        :param currentpath: Recorded history of the recursed path.  If the destination is hit, the currentpath is copied
        to the collection of valid paths.
        :param _pathindex: (Internal only) Keeps track of the valid path collection count throughout the recursion.
        :param _originalsrc: (Internal only) Keeps track of the original source requested throughout the recursion.
        :return: True if node in branch list was a valid path (for future use if needed, serves as placeholder).
        """
        validpath = False

        # First time into the routine
        if _originalsrc is None:
            # Save the original starting point to allow propagation.
            _originalsrc = src

        # Src and Dst are the same; done with traverse.
        if src == dst:
            return validpath

        # No current path; new path from starting node.
        if len(currentpath) == 0:
            # Set the starting node.
            currentpath = [(_originalsrc, 0)]

        # Get all of the next possible paths (next one-level deep)
        if src in self.statedefinitions:
            branch_list = self.statedefinitions[src]
        else:
            return validpath

        # Iterate through all node branches
        for node in branch_list:

            if node[0] == dst:
                # Reached destination!
                # Copy the current path into the collection and append final destination.
                _pathindex = len(validpathcollection) + 1
                validpathcollection[_pathindex] = list(x for x in currentpath)
                validpathcollection[_pathindex].append(node)
                validpath = True

            elif node[0] == src or node[0] == _originalsrc or (len(currentpath) > 0 and node[0] in [x[0] for x in currentpath]):
                # node[0] == src --> Sanity check with "current src".
                # node[0] == _originalsrc --> Sanity check with original src
                # (len(currentpath) > 0 and node[0] in [x[0] for x in currentpath]) --> Any previous node; infinite loop avoidance
                validpath = False

            else:
                # Node branch is somewhere in the middle of a path of nodes other than the previous node,
                # the original starting node, or the current node.
                # Therefore record the current path for this node branch and go deeper with recursive calls.
                nextcurrentpath = list(i for i in currentpath)
                nextcurrentpath.append(node)
                validpath = True
                if self.__traverse(node[0], dst,
                                   validpathcollection=validpathcollection,
                                   currentpath=nextcurrentpath,
                                   _pathindex=_pathindex,
                                   _originalsrc=_originalsrc):
                    # Recursive return with valid path.
                    pass

        return validpath

    def __pathmetrics(self, allpossiblepaths, metriccollection={}):
        """
        Collect the minimum and maximum cost & hop for each path of all possible paths.
        From the metric collection, determine the first paths of minimum and maximum for cost and hop.
        :param allpossiblepaths: Dictionary of all possible valid paths from source to destination.
        :param metriccollection: Dictionary of the path metrics for each path in the collection.
        :return: Dictionary of tuple metrics: min/max cost & hops and associated collection index of the paths.
        {'MINCOST':tuple, 'MAXCOST':tuple, 'MINHOP':tuple, 'MAXHOP':tuple} where tuple = (<pathindex>, <value>).
        """
        pathmetrics = {'MINCOST': None, 'MAXCOST': None, 'MINHOP': None, 'MAXHOP': None}
        try:
            # Collect up costs and hops for each possible path.
            for pathindex in range(1, len(allpossiblepaths) + 1):
                cost = 0
                for segment in allpossiblepaths[pathindex]:
                    cost += segment[1]
                metriccollection[pathindex] = (cost, len(allpossiblepaths[pathindex]) - 1)

            if len(allpossiblepaths) != len(metriccollection):
                raise Exception("Path and metrics table index length mismatch")

            # Determine min and max metrics
            if len(metriccollection) > 0:
                mincost = (1, metriccollection[1][0])
                maxcost = (1, metriccollection[1][0])
                minhop = (1, metriccollection[1][1])
                maxhop = (1, metriccollection[1][1])
                for index in range(2, len(metriccollection) + 1):
                    cost = metriccollection[index][0]
                    hop = metriccollection[index][1]
                    if mincost[1] > cost:
                        mincost = (index, cost)
                    if maxcost[1] < cost:
                        maxcost = (index, cost)
                    if minhop[1] > hop:
                        minhop = (index, hop)
                    if maxhop[1] < hop:
                        maxhop = (index, hop)
                pathmetrics = {'MINCOST': mincost, 'MAXCOST': maxcost, 'MINHOP': minhop, 'MAXHOP': maxhop}

        except Exception as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))

        finally:
            return pathmetrics

    def __validatemachinetable(self):
        """
        Validate that the machine definition table has the correct format and nomenclature.
        :return: True if good.
        """
        ret = False
        try:
            if len(self.statedefinitions) == 0:
                raise Exception("State Machine Definition is undefined.")
            for key in self.statedefinitions.keys():
                if len(self.statedefinitions[key]) == 0:
                    raise Exception("State Machine Definition has an empty node.")
                result = self.__validatedestnodelist(self.statedefinitions[key])
                if not result[0]:
                    raise Exception("{0}".format(result[1]))
            ret = True
        except Exception as e:
            log.exception("{0}: {1}".format(type(e).__name__.upper(), e.message))
        finally:
            return ret

    def __validatedestnodelist(self, destnodelist):
        """
        Validate the destination nodes for a single given node.
        :param destnodelist (list): List of all immediate single-step nodes the source node can go to.
        :return: Tuple of (True|False, msg)
        """
        retval = True
        msg = ""
        for path in destnodelist:
            if type(path) is not tuple:
                msg = "Path items in destination node list must be of tuple type."
                retval = False
                break
            if len(path) != 2:
                msg = "{0} path in destination node list has bad format: " + \
                      "use '(<destination node>, <cost>)'".format(path)
                retval = False
                break
            if type(path[1]) is not int:
                msg = "<cost> in '(<destination node>, <cost>)' must be a positive integer {0}.".format(path)
                retval = False
                break
            if type(path[0]) is not str:
                msg = "<destination node> in '(<destination node>, <cost>)' must be a string {0}.".format(path)
                retval = False
                break
            if not set(path[0]).isdisjoint(set(" !@#$%^&*()+=-?/~`|\\\"")):
                msg = "<destination node> in '(<destination node>, <cost>)' " + \
                      "must NOT contain any special characters {0}.".format(path)
                retval = False
                break
        return retval, msg


def get_config(cfg_module_name):
    """ Get Config
    Use this in conjunction with standalone mode to read in the state machine.
    :param cfg_module_name:
    :return:
    """
    _state_machine = dict()
    try:
        cfg_module = importlib.import_module(cfg_module_name, package=None)
        if cfg_module.uut_state_machine:
            _state_machine = cfg_module.uut_state_machine
        else:
            log.error("No State Machine!")
    except ImportError as e:
        log.debug("Cannot import {0}".format(cfg_module_name))
        log.debug(e)
    finally:
        return _state_machine


if __name__ == '__main__':
    # Use this for standalone execution.
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="Turn on verbosity for extra information (default off).")
    parser.add_argument("-d", "--docstring", dest="docstring", default=False, action="store_true",
                        help="Print PathFinder docstring.")
    parser.add_argument("-m", "--module", dest="module", default=None, action="store",
                        help="Module containing the statemachine descriptor."
                             "This is a dict with the required name:"
                             "'uut_state_machine'.")
    parser.add_argument("-s", "--startnode", dest="startnode", default='', action="store",
                        help="Starting node when determining path.")
    parser.add_argument("-e", "--endnode", dest="endnode", default='', action="store",
                        help="Ending node when determining path.")
    parser.add_argument("-f", "--followpath", dest="followpath", default=None, action="store",
                        help="Follow path for stateful nodes.")

    args = parser.parse_args()
    smd = {}
    if args.docstring:
        pf = PathFinder()
        print(str(pf))
        print(repr(pf))

    if args.module:
        state_machine = get_config(args.module)
        smd = {
            'verbose': args.verbose,
            'statemachine': state_machine
        }
        pf = PathFinder(**smd)
        pf.print_state_machine()
        fp = args.followpath.split(',') if args.followpath else list()
        bestpath = pf.get_path(args.startnode, args.endnode, followpath=fp)
        print(bestpath)

    sys.exit(0)
