import sys, importlib.util, json, time
spec = importlib.util.spec_from_file_location("llm_utils", r"C:\Users\twfehh7\.codex\skills\wechat-article-sop\scripts\llm_utils.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
items = json.load(open("_content.json", encoding="utf-8"))
todo = []
for i, x in enumerate(items):
    if x["kind"] in ("para","bullet","runin","h2","h3"):
        todo.append({"id": i, "type": "text", "content": x["text"]})
    elif x["kind"] == "fig" and x.get("caption"):
        todo.append({"id": "cap" + str(i), "type": "text", "content": x["caption"]})
print("to translate:", len(todo), flush=True)
out = {}
B = 10
t0 = time.time()
for s in range(0, len(todo), B):
    batch = todo[s:s+B]
    res = m.translate_batch(batch, batch_size=B)
    for r in res:
        out[str(r["id"])] = r["content"]
    json.dump(out, open("_translations.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("chunk %d/%d done  elapsed %.0fs" % (s//B+1, (len(todo)+B-1)//B, time.time()-t0), flush=True)
print("ALL DONE", len(out), flush=True)
