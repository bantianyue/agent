
@spec.tool(speculatable=True, pure=True)
def tool(...) -> OutputType:
    ...

# Speculated version
def tool_spec(...):
    promise = launch(tool(...))
    register_speculation(promise)

# Hooked version run in real REPL
def tool_real(...):
    if exists(promise, ID(...)):
        return promise
    else:
        return tool(...)
