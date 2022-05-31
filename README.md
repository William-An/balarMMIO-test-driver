# SST Test Run

## Run script

### MMIO Balar

1. `sst testBalar-simple.py --model-options='-c ariel-gpu-v100.cfg -v -x run -t trace/cuda_calls.trace'`
1. Use sst 10.1 env setup script

### Original Balar

1. `~/SST-Integration/sstcore-11.1.0-release/bin/sst cuda-test.py --model-options='-c ariel-gpu-v100.cfg -v -x vectorAdd/vectorAdd'`
    1. Use the other sst installation

## Note

1. NVBit tool should compiled with nvcc version >= 10.2
1. Test app are compiled with CUDA 10.1 version

## TODO

1. Use gpu app from accel sim
    1. Need automatic script to do the work
1. [ ] Python script launch cannot find cudart for app
1. [ ] Rodinia backprop benchmark cannot trace, kernel parameter is null
1. Rodinia 2.0 Backprop
    1. second kernel has issue
    1. Due to alignment setting
        1. Irregular argument size need to align properly?
        2. Implement this in the testcpu
1. [ ] Link the python run script and cfg file for SST in run script?
