program = Program()
ops = program.upload(kind="module", source=OPERATIONS)

# Compilation runs without the GPU; the GPU is free for other programs.
compile_kernel = program.get_function(module=ops, name="compile_kernel", cpu_only=True)
library = program.run(fn=compile_kernel, args=[KERNEL_SOURCE, {"arch": "sm_100a"}])

# Loading and benchmarking reacquire the GPU.
load_kernel = program.get_function(module=ops, name="load_kernel")
benchmark = program.get_function(module=ops, name="benchmark")
kernel = program.run(fn=load_kernel, args=[library])
timing = program.run(fn=benchmark, args=[kernel])
program.return_(key="timing", value=timing)
