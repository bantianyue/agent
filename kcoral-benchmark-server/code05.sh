# Point every kcoral command at the GPU server.
export KCORAL_URL='http://gpu.example.com:8000'

# Upload the experiment/ directory and run check.py with the worker's Python.
kcoral run python --send experiment -- experiment/check.py

# Run the same script under compute-sanitizer to catch CUDA memory errors.
kcoral run compute-sanitizer --send experiment -- python experiment/check.py

# Profile capture.py with Nsight Compute and download the report to artifacts/ncu.
kcoral run ncu --send experiment --out artifacts/ncu -- --set basic -- python experiment/capture.py

# Run an arbitrary shell script in the remote working directory.
kcoral run shell --send experiment -- bash experiment/setup.sh
