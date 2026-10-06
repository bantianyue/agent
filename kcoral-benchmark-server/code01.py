import numpy as np
from kcoral import Client, Program

SOURCE = """
def add_one(x):
    return x + 1
"""

program = Program()
module = program.upload(kind="module", source=SOURCE)
add_one = program.get_function(module=module, name="add_one")
x = program.upload(kind="tensor", value=np.arange(4, dtype=np.float32))
y = program.run(fn=add_one, args=[x])
program.return_(key="output", value=y)

with Client("http://localhost:8000") as client:
    result = client.execute(program)

print(result.results["output"])  # [1. 2. 3. 4.]
