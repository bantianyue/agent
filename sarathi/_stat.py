# -*- coding: utf-8 -*-
import json, os, traceback
from collections import OrderedDict
ART = r"D:\06_Hermes\articles\sarathi"
LOG = os.path.join(ART, "_stat_out.txt")
buf = []
try:
    items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
    cur2 = cur3 = ""
    stat = OrderedDict()
    for it in items:
        if it["kind"] == "head":
            t = it["text"].strip()
            if it["level"] == "h2":
                cur2, cur3 = t, ""
                stat[cur2] = OrderedDict()
                stat[cur2]["__total__"] = 0
            elif it["level"] == "h3":
                cur3 = t
                stat.setdefault(cur2, OrderedDict())
                stat[cur2].setdefault("__total__", 0)
                stat[cur2][cur3] = 0
            continue
        if cur2 not in stat:
            stat[cur2] = OrderedDict()
            stat[cur2]["__total__"] = 0
        if it["kind"] == "p":
            stat[cur2]["__total__"] += 1
            if cur3:
                stat[cur2][cur3] = stat[cur2].get(cur3, 0) + 1
        elif it["kind"] == "fig":
            stat[cur2].setdefault("__figs__", [])
            b = os.path.basename(it["src"])
            if b not in stat[cur2]["__figs__"]:
                stat[cur2]["__figs__"].append(b)
        elif it["kind"] == "table":
            stat[cur2].setdefault("__tables__", []).append(it["caption"][:44])

    lines = []
    for k, v in stat.items():
        lines.append("## %s  (paras=%d)" % (k, v.get("__total__", 0)))
        for kk, vv in v.items():
            if kk.startswith("__"):
                continue
            lines.append("   ### %s : %d" % (kk, vv))
        if "__figs__" in v:
            lines.append("   FIGS: " + ", ".join(v["__figs__"]))
        if "__tables__" in v:
            lines.append("   TABLES: " + " | ".join(v["__tables__"]))
    buf = lines
except Exception:
    buf = ["EXC\n" + traceback.format_exc()]
open(LOG, "w", encoding="utf-8").write("\n".join(buf))
