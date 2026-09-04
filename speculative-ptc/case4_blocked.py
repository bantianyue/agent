
a = llm_query("Triage: " + doc)  # speculated
notes = open("/tmp/scratch.txt").read()  # blocked
b = llm_query("Annotate with notes: " + notes)  # blocked
c = llm_query("Summarize: " + a)  # speculated after a
