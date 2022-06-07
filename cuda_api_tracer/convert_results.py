#!/usr/bin/env python3
"""

Convert SST results to json format

"""

import subprocess
import logging
import os, stat, re, json
from yaml import load, dump
from optparse import OptionParser
from collections import Counter
import yaml

from common import *
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from common import get_argfoldername

def parse_sst_statfile(statfile : str, components : list):
    """Parse sst statfile into a dictionary

    Args:
        statfile (str): filepath to sst statfile
        components (list[str]): list of str which used to filter line starting with terms in the list
    """
    with open(statfile, "r") as fp:
        map = dict()
        while True:
            line = fp.readline()
            if line == "":
                # EOF
                return map
            else:
                for term in components:
                    if line.startswith(term):
                        # Find a match, insert to map
                        tokens = [i.strip() for i in line.split(": Accumulator :")]
                        component_names = re.split(r"\W+", tokens[0])
                        raw_data_pairs = [i.strip() for i in tokens[1].split(";")]
                        
                        # Find/construct the leaf map
                        node_map = map
                        for name in component_names:
                            node_map = node_map.setdefault(name, dict())

                        # Insert the data value pairs
                        for raw_pair in raw_data_pairs:
                            if raw_pair == "":
                                continue
                            tmp = [i.strip() for i in raw_pair.split("=")]
                            key = tmp[0]
                            val = eval(tmp[1])
                            node_map[key] = val
                        
                        # Skip the rest of component list once we found a match
                        break


def parse_gpgpusim_statfile(statfile):
    """Parse gpgpusim statfile into a dictionary

    Args:
        statfile (str): filepath to gpgpusim statfile
    """
    with open(statfile, "r") as fp:
        map = dict()
        while True:
            line = fp.readline()
            if line == "":
                # EOF
                return map
            else:
                tokens = [i.strip() for i in line.split(":")]

                # Skip header line
                if tokens[0] == "kernel line":
                    continue
                else:
                    # Prepare data
                    tmp = tokens[0].split(" ")
                    kernel_name = tmp[0]
                    line = tmp[1]
                    data = [eval(i.strip()) for i in tokens[1].split(" ")]
                    
                    # Insert to map
                    kernel_map : dict
                    kernel_map = map.setdefault(kernel_name, dict()) 
                    kernel_map[line] = data



parser = OptionParser()
parser.add_option("-B", "--benchmark_list", dest="benchmark_list",
                 help="a comma seperated list of benchmark suites to run. See ../define-all-apps.yml for " +\
                       "the benchmark suite names.",
                 default="rodinia_2.0-ft")
parser.add_option("-l", "--loglevel", dest="loglevel", help="logging level, support: [debug, info, warning, error, critical]", default="info")
parser.add_option("-t", "--trace_folder", dest="trace_folder", help="trace folder path", default="./hw_traces")
parser.add_option("--statfile", dest="statfile", help="sst stat file name", default="stats.txt")
parser.add_option("--gpgpusim_statfile", dest="gpgpusim_statfile", help="gpgpusim stat file name", default="gpgpu_inst_stats.txt")
parser.add_option("--sst_components", dest="sst_components", help="comma separated component name to be filtered in when reading sst stat file", default="cpu,l1gcache,l2gcache,Simplehbm")
parser.add_option("--apps_config", dest="apps_config", help="path to yaml config file of benchmark apps", default="../define-all-apps.yml")
parser.add_option("-o", "--output", dest="output", help="Output json file path", default="out.json")

(options, args) = parser.parse_args()

# Get arguments
benchmark_suites_list = [i.strip() for i in options.benchmark_list.split(",")]
benchmark_suites_list = [i.strip() for i in benchmark_suites_list]
logging_level = options.loglevel.upper()
trace_folder = os.path.abspath(options.trace_folder)
sst_statfile = options.statfile
gpgpusim_statfile = options.gpgpusim_statfile
sst_components = [i.strip() for i in options.sst_components.split(",")]
apps_yaml_config = os.path.abspath(options.apps_config)
output = options.output

# Logging config
launch_counter = Counter()
logging.basicConfig(level=getattr(logging, logging_level))
root_logger = logging.getLogger()

# Prepare variable for runs
benchmark_suites_table = yaml.load(open(apps_yaml_config), Loader=Loader)
top_dir = os.path.abspath(".")
stats_map = dict()

logging.info("Collecting stats...")
for app_record in get_benchmark_app(benchmark_suites_list, trace_folder, benchmark_suites_table, root_logger):
    # Chdir into the run dir
    run_dir = app_record["run_dir"]
    trace_dir = app_record["trace_dir"]
    app_name = app_record["app_name"]
    benchmark_suite_name = app_record["benchmark_suite_name"]
    app_exec_path = app_record["app_exec_path"]
    app_args = app_record["app_args"]
    # Convert to something matches the dir name
    app_args_name = get_argfoldername(app_args)
    try:
        os.chdir(run_dir)
    except OSError:
        root_logger.warning("run dir {} does not exist/cannot access, maybe the simulation result is not generated for {} in {}?".format(run_dir, app_name, benchmark_suite_name))
        continue

    # Set variable types, so that linter gives hints
    benchmark_map: dict
    app_total_map: dict
    app_specific_map: dict

    # Get benchmark mapping
    benchmark_map = stats_map.setdefault(benchmark_suite_name, dict())

    # Get app mapping (include all arg configuration)
    app_total_map = benchmark_map.setdefault(app_name, dict())
    app_specific_map = app_total_map.setdefault(app_args_name, dict())

    # Parsing the stat file
    sst_statfile_path = os.path.join(run_dir, sst_statfile)
    gpgpusim_statfile_path = os.path.join(run_dir, gpgpusim_statfile)

    try: 
        app_specific_map["sst"] = parse_sst_statfile(sst_statfile_path, sst_components)
        app_specific_map["gpgpusim"] = parse_gpgpusim_statfile(gpgpusim_statfile_path)
    except FileNotFoundError:
        root_logger.warning("Stats for app {} in benchmark {} with arg name {} cannot be collected".format(app_name, benchmark_suite_name, app_args_name))

    # Back to top dir
    root_logger.info("Finish collection for {} in {} with {}".format(app_name, benchmark_suite_name, app_args_name))

    os.chdir(top_dir)


# Dumping into json file
with open(output, "w") as outfp:
    json.dump(stats_map, outfp)

