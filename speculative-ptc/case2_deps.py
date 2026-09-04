
a = llm_query("Triage: " + doc)  # parses then executes
c = llm_query("Summarize: " + str(a))  # parses, waits on a, then executes
print(c)

if len(doc) > 10_000:  # will evaluate and speculate if safe
    extra = llm_query("Also outline it: " + doc)
