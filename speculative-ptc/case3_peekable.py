
def gist(t):
    return llm_query("One-line gist: " + t)  # non-peekable

parts = [gist(c) for c in chunks]

side = llm_query("Give me a random title for:", chunks[0])  # peekable
print(side, parts)
