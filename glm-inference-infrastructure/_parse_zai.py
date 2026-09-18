import io,re,json,sys

SRC = r"D:\06_Hermes\articles\_zai.js"
t = io.open(SRC, encoding="utf-8", errors="ignore").read()

CALL = re.compile(r"\(0,u\.jsxs?\)\(t\.([A-Za-z0-9_]+),\{")

def read_string(p):
    assert t[p] == "`", t[p:p+20]
    p += 1
    out = []
    while True:
        c = t[p]
        if c == "\\":
            out.append(t[p:p+2]); p += 2; continue
        if c == "`":
            p += 1; break
        out.append(c); p += 1
    s = "".join(out)
    s = s.replace("\\`", "`").replace("\\$", "$").replace("\\\\", "\\")
    return s, p

def parse_element(p):
    m = CALL.match(t, p)
    if not m:
        raise ValueError("no call at %d: %s" % (p, t[p:p+60]))
    tag = m.group(1)
    p = m.end()
    props = {}
    children = []
    while True:
        if t.startswith("children:", p):
            p += len("children:")
            if t[p] == "`":
                s, p = read_string(p)
                children = [("text", s)]
            elif t[p] == "[":
                p += 1
                children = []
                while True:
                    if t[p] == "`":
                        s, p = read_string(p)
                        children.append(("text", s))
                    elif t[p] == "(":
                        node, p = parse_element(p)
                        children.append(node)
                    else:
                        raise ValueError("array item %s" % t[p:p+60])
                    if t[p] == ",":
                        p += 1; continue
                    if t[p] == "]":
                        p += 1; break
                    raise ValueError("array parse %s" % t[p:p+60])
            elif t[p] == "(":
                node, p = parse_element(p)
                children = [node]
            else:
                raise ValueError("children form %s" % t[p:p+60])
            continue
        m2 = re.compile(r"([a-zA-Z_][A-Za-z0-9_]*):").match(t, p)
        if m2:
            key = m2.group(1)
            p = m2.end()
            if t[p] == "`":
                val, p = read_string(p)
            elif t[p] == '"':
                end = t.index('"', p+1)
                val = t[p+1:end]; p = end+1
            elif t[p] == "{":
                depth = 0; start = p
                while True:
                    if t[p] == "{": depth += 1
                    elif t[p] == "}":
                        depth -= 1
                        if depth == 0: break
                    p += 1
                val = t[start:p+1]; p += 1
            else:
                end = p
                while end < len(t) and t[end] not in ",}":
                    end += 1
                val = t[p:end]; p = end
            props[key] = val
            continue
        break
    if t[p] == ",":
        p += 1
    if t[p] == "}":
        p += 1
    return (tag, props, children), p

start = t.find("(0,u.jsx)(t.p,{children:`As we develop GLM")
nodes = []
p = start
while True:
    try:
        node, p = parse_element(p)
    except Exception as e:
        print("stop:", e, file=sys.stderr)
        break
    nodes.append(node)
    if t[p] == ",":
        p += 1
    if t[p] == "`":
        _, p = read_string(p)
    if t[p] == ",":
        p += 1
    while p < len(t) and t[p] in "\n\r \t":
        p += 1
    if not CALL.match(t, p):
        break

print("nodes:", len(nodes), file=sys.stderr)

def inline(nodes):
    out = []
    for n in nodes:
        if n[0] == "text":
            out.append(n[1])
        else:
            tag, props, kids = n
            inner = inline(kids)
            if tag == "code":
                out.append("`" + inner + "`")
            elif tag == "strong":
                out.append("**" + inner + "**")
            elif tag == "a":
                out.append("[LINK:%s]%s[/LINK]" % (props.get("href", ""), inner))
            elif tag == "img":
                out.append("[IMG:%s]" % props.get("src", ""))
            else:
                out.append(inner)
    return "".join(out)

lines = []
for n in nodes:
    tag, props, kids = n
    if tag == "img":
        lines.append("[IMG]" + props.get("src", ""))
    elif tag == "pre":
        inner = "\n".join(inline(k[2]) for k in kids if k[0] != "text")
        lines.append("[CODE]\n" + inner)
    elif tag in ("h1", "h2", "h3", "h4"):
        lines.append("[" + tag.upper() + "]" + inline(kids))
    elif tag == "p":
        lines.append(inline(kids))
    elif tag in ("ul", "ol"):
        for k in kids:
            if k[0] != "text":
                lines.append("[LI]" + inline(k[2]))
    elif tag == "li":
        lines.append("[LI]" + inline(kids))
    elif tag == "blockquote":
        lines.append("[QUOTE]" + inline(kids))
    else:
        lines.append("[" + tag.upper() + "]" + inline(kids))

body = "\n\n".join(lines)
io.open(r"D:\06_Hermes\articles\glm-inference-infrastructure\_zai_body.txt", "w", encoding="utf-8").write(body)
print("chars", len(body))
