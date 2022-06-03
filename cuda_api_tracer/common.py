import re, hashlib, os, logging

def get_argfoldername( args ):
    if args == "" or args == None:
        return "NO_ARGS"
    else:
        foldername = re.sub(r"[^a-z^A-Z^0-9]", "_", str(args).strip())
        # For every long arg lists - create a hash of the input args
        if len(str(args)) > 256:
            foldername = "hashed_args_" + hashlib.md5(args).hexdigest()
        return foldername

def get_benchmark_app(benchmark_suites_list: list, trace_folder: str,
                        benchmark_suites_table: dict, logger: logging.Logger):
    """A generator to yield app record

    Args:
        benchmark_suites_list (list): list of benchmark suites
        trace_folder (str): folder to trace folder, will generat/consume traces here
        benchmark_suites_table (dict): parsed dict from app config yaml file
        logger (logging.Logger): top logger
    """
    for benchmark_suite_name in benchmark_suites_list:
        benchmark_suite_root = os.path.join(trace_folder, benchmark_suite_name)

        try:
            benchmark_suite = benchmark_suites_table[benchmark_suite_name]
        except KeyError:
            logger.warning("benchmark suite {} does not exist!".format(benchmark_suite_name))
            continue
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
                app_args = config["args"]
                app_args = app_args if app_args else ""
                run_dir = os.path.join(app_dir, get_argfoldername(app_args))
                trace_dir = os.path.join(run_dir, "trace")
                
                # Construct app record
                app_record = dict()
                app_record["app_exec_path"] = app_exec_path
                app_record["app_args"] = app_args
                app_record["run_dir"] = run_dir
                app_record["trace_dir"] = trace_dir
                app_record["data_dir"] = app_data_dir
                app_record["app_name"] = app_name
                app_record["benchmark_suite_name"] = benchmark_suite_name

                # Generate the record
                yield app_record
