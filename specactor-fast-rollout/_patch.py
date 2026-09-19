import io
p = "_assemble.py"
s = open(p, encoding="utf-8").read()
s = s.replace('eq_i, alg_i = 0, 0', 'eq_i, alg_i = 0, 0\ncarry_figs = []')
s = s.replace("""    sections.append(cur)
    pending_figs = []""", """    sections.append(cur)
    pending_figs = list(carry_figs)
    carry_figs.clear()""")
s = s.replace("""    elif k == "fig":
        if cur is None or not cur["paras"]:
            pending_figs.append(i)
        else:
            attach_fig(i, cur)""", """    elif k == "fig":
        nxt = items[i+1] if i+1 < len(items) else None
        if (nxt is not None and nxt["kind"] in ("h2", "h3")) or cur is None or not cur["paras"]:
            if nxt is not None and nxt["kind"] in ("h2", "h3"):
                carry_figs.append(i)
            else:
                pending_figs.append(i)
        else:
            attach_fig(i, cur)""")
open(p, "w", encoding="utf-8").write(s)
print("patched")
