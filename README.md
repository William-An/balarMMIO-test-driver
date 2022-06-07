# SST Test Run

Run the gpu applications with both ariel and mmio balar.

## Prerequisite

1. Two SST installations
    1. One with MMIO balar
    1. One with ariel balar
1. Need to download [gpu-app-collection](https://github.com/accel-sim/gpu-app-collection) from accel-sim repo
    1. Compile with both CUDA 9.1 and 10.1
1. Need to download NVBIT tool in `cuda_api_tracer/` folder
1. Need to have a python environment installing the packages in `requirements.txt`, could use `virtualenv` to create a sandbox
1. `get_traces.py` script
    1. Need to `source gpu-app-collection/src/setup_environment` before calling
    1. Runs with CUDA 10.1 and GCC 5.5.0
    1. But higher GCC version should also work
1. `run_traces.py` script
    1. Need to `source setup_environment` before calling
    1. Need CUDA 9.1 and GCC 4.9.2 for the ariel balar to works
    1. MMIO balar works with CUDA 10.1 and GCC 5.5.0

## Run script

```bash
# Get trace
python3 get_traces.py -B [BENCHMARKS]

# Run traces
python3 run_traces.py -B [BENCHMARKS]

# Example
python3 run_traces.py -B GPU_Microbenchmark,rodinia_2.0-ft --original_balar_sst_exe=~/SST-Integration/sstcore-11.0.0-release/bin/sst

# Collecting stats
## MMIO example
python3 convert_results.py -B GPU_Microbenchmark,rodinia_2.0-ft --statfile=mmio_stats.out --gpgpusim_statfile=gpgpu_inst_stats_mmio.log -o mmio_stats.json
## Ariel/Original balar example
python3 convert_results.py -B GPU_Microbenchmark,rodinia_2.0-ft --statfile=original_stats.out --gpgpusim_statfile=gpgpu_inst_stats_original.log -o original_stats.json

```

### MMIO Balar

1. `sst testBalar-simple.py --model-options='-c ariel-gpu-v100.cfg -v -x run -t trace/cuda_calls.trace'`
1. Use sst 10.1 env setup script

### Original Balar

1. `~/SST-Integration/sstcore-11.1.0-release/bin/sst cuda-test.py --model-options='-c ariel-gpu-v100.cfg -v -x vectorAdd/vectorAdd'`
    1. Use the other sst installation
    1. Need to use cuda 9.1?

## Note

1. NVBit tool should compiled with nvcc version >= 10.2
    1. `tracer_tool` setup script
1. Test app are compiled with CUDA 10.1 version
    1. `test_app` setup script
1. Need both 9.1 and 10.1 app
    1. 9.1 for simulation run
    1. 10.1 for tracer tool run

## TODO

1. [x] Use gpu app from accel sim
    1. [x] Need automatic script to do the work
1. [x] Python script launch cannot find cudart for app
1. [x] Rodinia backprop benchmark cannot trace, kernel parameter is null
1. [x] Rodinia 2.0 Backprop
    1. second kernel has issue
    1. Due to alignment setting
        1. Irregular argument size need to align properly?
        2. Implement this in the testcpu
1. [x] Link the python run script and cfg file for SST in run script?
1. [x] Create a clean script to clear all tmp files and option to not dump test data?
    1. Due to disk space concern
1. [ ] In hw traces, save multiple cuda version traces?
1. [ ] Parallelize the run traces
1. [ ] Minimize the python requirement file? (iPython not needed, just the YAML file?)
