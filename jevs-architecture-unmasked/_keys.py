# -*- coding: utf-8 -*-
import os, json
env = {}
for line in open(os.path.expanduser("~/.baoyu-skills/.env"), encoding="utf-8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
open("_keys.txt", "w", encoding="utf-8").write("\n".join("%s -> len%d" % (k, len(v)) for k, v in env.items()))
