
real_ns = {**locals, real_tools}
shadow_ns = replace_tools(real_ns)

# speculate while LLM is streaming
while not LLM.done:
    code += LLM.next_tokens()
    parse_and_peek(code, shadow_ns)  # queue without code execution
    parse_and_speculate(code, shadow_ns)  # re-run shadow REPL

# real tools now route to promised tools
exec(code, real_ns)
