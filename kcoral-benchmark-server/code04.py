with Client(CPU_URL) as cpu_client, Client(GPU_URL) as gpu_client:
    arch = gpu_client.target()["arch"]

    # Request 1: compile on the CPU server and return the shared library.
    compiled = cpu_client.execute(compile_program(arch))

    # Request 2: upload the library to the GPU server, check, and benchmark.
    result = gpu_client.execute(benchmark_program(compiled.results["library"]))
    print(result.results["check"], result.results["timing"])
