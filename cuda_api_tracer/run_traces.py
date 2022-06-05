#!/usr/bin/env python3
"""

Run the binary and traces in traces folder with 
both original balar and mmio balar

"""

import subprocess
import logging
import os, stat
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

parser = OptionParser()
parser.add_option("-B", "--benchmark_list", dest="benchmark_list",
                 help="a comma seperated list of benchmark suites to run. See ../define-all-apps.yml for " +\
                       "the benchmark suite names.",
                 default="rodinia_2.0-ft")
parser.add_option("-l", "--loglevel", dest="loglevel", help="logging level, support: [debug, info, warning, error, critical]", default="info")
parser.add_option("-t", "--trace_folder", dest="trace_folder", help="trace folder path", default="./hw_traces")
# TODO Implement the dump memcpy control
# parser.add_option("--dump_memcpy", dest="dump_memcpy", help="Dump simulation run memcpy data (default)", action="store_true")
# parser.add_option("--no_dump_memcpy", dest="dump_memcpy", help="Do not to dump simulation run memcpy data", action="store_false")
# parser.set_default(dump_memcpy=True)
parser.add_option("--mmio_balar_sst_exe", dest="mmio_sst", help="mmio balar built sst exe path", default="sst")
parser.add_option("--original_balar_sst_exe", dest="original_sst", help="original balar built sst exe path", default="sst")
parser.add_option("--apps_config", dest="apps_config", help="path to yaml config file of benchmark apps", default="../define-all-apps.yml")
(options, args) = parser.parse_args()

# TODO Loop through subfolders in the trace folder and run both versions of balar

# Get arguments
benchmark_suites_list = options.benchmark_list.split(",")
benchmark_suites_list = [i.strip() for i in benchmark_suites_list]
logging_level = options.loglevel.upper()
trace_folder = os.path.abspath(options.trace_folder)
# dump_memcpy = options.dump_memcpy
mmio_balar_sst_exe = options.mmio_sst
original_balar_sst_exe = options.original_sst
apps_yaml_config = os.path.abspath(options.apps_config)

# Logging config
launch_counter = Counter()
logging.basicConfig(level=getattr(logging, logging_level))
root_logger = logging.getLogger()

# Prepare variable for runs
benchmark_suites_table = yaml.load(open(apps_yaml_config), Loader=Loader)
top_dir = os.path.abspath(".")
repo_dir = os.path.abspath(os.getenv("BALAR_DRIVER_ROOT"))

# Supporting launch files to be soft linked in run dir for each app
GPGPUSIM_CONFIG_NAME    = "gpgpusim.config"
SST_GPU_CONFIG_NAME     = "ariel-gpu-v100.cfg"
MMIO_BALAR_UTIL_NAME    = "utils_mmio.py"
MMIO_BALAR_LAUNCH_NAME  = "testBalar-mmio.py"
ORIGINAL_BALAR_UTIL_NAME      = "utils_original.py"
ORIGINAL_BALAR_LAUNCH_NAME    = "testBalar-original.py"
launch_files_names = [GPGPUSIM_CONFIG_NAME, 
                        SST_GPU_CONFIG_NAME,
                        MMIO_BALAR_UTIL_NAME,
                        MMIO_BALAR_LAUNCH_NAME,
                        ORIGINAL_BALAR_UTIL_NAME,
                        ORIGINAL_BALAR_LAUNCH_NAME]
launch_files_paths = [os.path.join(repo_dir, i) for i in launch_files_names]


# Benchmark runner
# Make this into an generator?
# Each app in benchmark gets generated
logging.info("Sim run starting")
for app_record in get_benchmark_app(benchmark_suites_list, trace_folder, benchmark_suites_table, root_logger):
      # TODO Run with original balar and mmio balar
      # Chdir into the run dir
      run_dir = app_record["run_dir"]
      trace_dir = app_record["trace_dir"]
      app_name = app_record["app_name"]
      benchmark_suite_name = app_record["benchmark_suite_name"]
      app_exec_path = app_record["app_exec_path"]
      app_args = app_record["app_args"]
      try:
            os.chdir(run_dir)
      except OSError:
            root_logger.warning("run dir {} does not exist/cannot access, maybe the trace is not generated for {} in {}?".format(run_dir, app_name, benchmark_suite_name))
            continue

      # Link the run scripts for SST
      sym_launch_files_paths = [os.path.join(run_dir, i) for i in launch_files_names]
      launch_files_pairs = zip(launch_files_paths, sym_launch_files_paths)
      for pair in launch_files_pairs:
            real = pair[0]
            sym = pair[1]
            if os.path.islink(sym):
                  os.unlink(sym)
            os.symlink(real, sym)

      # Launch shell script for MMIO
      mmio_shell_script = "# Launch app: {} in benchmark suite: {}\n".format(app_name, benchmark_suite_name)

      # Run
      mmio_shell_script += "{} {} --model-options='--statfile=mmio_stats.out -c {} --trace=trace/cuda_calls.trace --binary=run {} '\n".format(mmio_balar_sst_exe,
                  MMIO_BALAR_LAUNCH_NAME,
                  SST_GPU_CONFIG_NAME,
                  "" if app_args == "" else "-a \"{}\"".format(app_args))
      
      # Write mmio script
      mmio_shell_path = os.path.join(run_dir, "sst_mmio.sh")
      open(mmio_shell_path, "w").write(mmio_shell_script)
      os.chmod(mmio_shell_path, stat.S_IRWXU | stat.S_IRWXG)

      # Run script
      # TODO Run the original balar as well
      # TODO Handle the gpgpusim stat ouput as well, rename differently with respect to mmio and ariel versions
      outFile = open(os.path.join(run_dir, "sst_mmio.log"), "w")
      errFile = open(os.path.join(run_dir, "sst_mmio.err"), "w")
      res = subprocess.run(["bash", "sst_mmio.sh"], check=False, stdout=outFile, stderr=errFile)
      outFile.close()
      errFile.close()

      # Check err status
      if (res.returncode == 0):
            # Success
            logging.info("app {} in benchmark suite {} ran successfully".format(app_name, benchmark_suite_name))
            launch_counter["succ"] += 1
      else:
            # Failure
            logging.warning("app {} in benchmark suite {} failed to run with args: {}".format(app_name, benchmark_suite_name, app_args))
            launch_counter["fail"] += 1

      os.chdir(top_dir)


# Print run summary
logging.info("Sim run finished")
logging.info("Benchmarks completed: {}".format(launch_counter["succ"]))
logging.info("Benchmarks failed: {}".format(launch_counter["fail"]))