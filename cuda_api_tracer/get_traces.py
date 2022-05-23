#!/usr/bin/env python3
"""

CUDA Version: 10.1
GCC Version: 7.5.0

"""

import subprocess
import os, re, hashlib
from yaml import load, dump
from optparse import OptionParser
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

benchmark_suites_table = yaml.load(open(APPS_YAML_FILEPATH), Loader=Loader)
launch_env = {"CUDA_INJECTION64_PATH": os.path.abspath(TRACER_TOOL_SO)}
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

            # Create link to app exec path
            app_sym_link = os.path.join(run_dir, "run")
            if os.path.islink(app_sym_link):
                os.unlink(app_sym_link)
            os.symlink(app_exec_path, app_sym_link)

            # Launch command
            launch_cmd = []
            launch_cmd.append("run")
            if app_args:
                launch_cmd.append(app_args)
            print("Running app {} with args: {} at dir: {}".format(app_exec_path, app_args, run_dir))
            print(launch_cmd)

            subprocess.run(launch_cmd, shell=True, check=True, env=launch_env)

            os.chdir(top_dir)

