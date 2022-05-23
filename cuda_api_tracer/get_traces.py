#!/usr/bin/env python3
"""

CUDA Version: 10.1
GCC Version: 7.5.0

"""

import subprocess
import logging
import os, re, hashlib
from yaml import load, dump
from optparse import OptionParser
from collections import Counter
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# Config yaml file path
APPS_YAML_FILEPATH = "../define-all-apps.yml"
CONFIGS_YAML_FILEPATH = "../define-standard-cfgs.yml"
TRACES_FOLDER = "./hw_traces"
TRACER_TOOL_SO = "./cuda_call_tracer/cuda_call_tracer.so"
benchmark_suites_list = "rodinia_2.0-ft,GPU_Microbenchmark".split(",")
benchmark_suites_list = [i.strip() for i in benchmark_suites_list]

def get_argfoldername( args ):
    if args == "" or args == None:
        return "NO_ARGS"
    else:
        foldername = re.sub(r"[^a-z^A-Z^0-9]", "_", str(args).strip())
        # For every long arg lists - create a hash of the input args
        if len(str(args)) > 256:
            foldername = "hashed_args_" + hashlib.md5(args).hexdigest()
        return foldername

# parser = OptionParser()
# parser.add_option("-B", "--benchmark_list", dest="benchmark_list",
#                  help="a comma seperated list of benchmark suites to run. See ../define-all-apps.yml for " +\
#                        "the benchmark suite names.",
#                  default="rodinia_2.0-ft")

# Envs for launch
cuda_version = os.getenv("CUDA_VERSION")
cuda_api_tracer_tool = os.path.abspath(TRACER_TOOL_SO)


# Logging config
launch_counter = Counter()
logging.basicConfig(level=logging.INFO)

# Benchmark runner
benchmark_suites_table = yaml.load(open(APPS_YAML_FILEPATH), Loader=Loader)
top_dir = os.path.abspath(".")
for benchmark_suite_name in benchmark_suites_list:
    benchmark_suite_root = os.path.join(os.path.abspath(TRACES_FOLDER), benchmark_suite_name)
    benchmark_suite = benchmark_suites_table[benchmark_suite_name]
    exec_dir = os.path.expandvars(benchmark_suite["exec_dir"])
    data_dir = os.path.expandvars(benchmark_suite["data_dirs"])
    benchmark_apps = benchmark_suite["execs"]
    for app in benchmark_apps:
        app_name = list(app.keys())[0]
        app_dir = os.path.join(benchmark_suite_root, app_name)
        app_configs = app[app_name]
        app_exec_path = os.path.join(exec_dir, app_name)
        app_data_dir = os.path.join(data_dir, app_name, "data")
        for config in app_configs:
            # Create folder to keep run data and traces
            app_args = config["args"]
            run_dir = os.path.join(app_dir, get_argfoldername(app_args))
            trace_dir = os.path.join(run_dir, "trace")
            if not os.path.exists(run_dir):
                os.makedirs(run_dir)
            if not os.path.exists(trace_dir):
                os.makedirs(trace_dir)

            # Prepare to launch
            os.chdir(run_dir)
            if os.path.lexists("./data"):
                os.remove("./data")

            # Create softlinks to data folder
            app_sym_data_dir = os.path.join(run_dir, "data")
            if os.path.islink(app_sym_data_dir):
                os.unlink(app_sym_data_dir)
            os.symlink(app_data_dir, app_sym_data_dir)

            # Launch shell script
            shell_script = "# Launch app: {} in benchmark suite: {}\n".format(app_name, benchmark_suite_name)
            
            # Prepare envars
            shell_script += "export CUDA_VERSION={}\n".format(cuda_version)
            shell_script += "export CUDA_INJECTION64_PATH={}\n".format(cuda_api_tracer_tool)
            shell_script += "export NOBANNER={}\n".format(0)
            
            # Run
            shell_script += "{} {}\n".format(app_exec_path, app_args)

            # Move traces
            shell_script += "mv ./*.trace ./trace\n"
            shell_script += "mv ./*.data ./trace\n"

            # Write script
            open(os.path.join(run_dir, "run.sh"), "w").write(shell_script)

            # Run script
            outFile = open(os.path.join(run_dir, "run.log"), "w")
            errFile = open(os.path.join(run_dir, "run.err"), "w")
            res = subprocess.run(["bash", "run.sh"], check=False, stdout=outFile, stderr=errFile)
            outFile.close()
            errFile.close()

            # Check err status
            if (res.returncode == 0):
                # Success
                logging.info("app {} in benchmark suite {} ran successfully".format(app_name, benchmark_suite_name))
                launch_counter["succ"] += 1
            else:
                # Failure
                logging.warning("app {} in benchmark suite {} failed to run with args: {}".format(app_name, benchmark_suite_name, res.args))
                launch_counter["fail"] += 1

            os.chdir(top_dir)

# Print run summary
logging.info("Traces run finished")
logging.info("Benchmarks completed: {}".format(launch_counter["succ"]))
logging.info("Benchmarks failed: {}".format(launch_counter["fail"]))
