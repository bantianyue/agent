# On the CPU host
kcoral server --device cpu --num-workers 8 --host 0.0.0.0 --port 8000
# On the GPU host
kcoral server --device gpu --gpus 0 --host 0.0.0.0 --port 8001
