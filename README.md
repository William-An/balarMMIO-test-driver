# SST Test Run

## Run script

```bash
# Get trace
python3 get_traces.py -B [BENCHMARKS]

# Run traces
python3 run_traces.py -B [BENCHMARKS]

# Example
python3 run_traces.py -B GPU_Microbenchmark,rodinia_2.0-ft --original_balar_sst_exe=~/SST-Integration/sstcore-11.0.0-release/bin/sst
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

1. Use gpu app from accel sim
    1. Need automatic script to do the work
1. [ ] Python script launch cannot find cudart for app
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
