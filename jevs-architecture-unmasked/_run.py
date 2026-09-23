# -*- coding: utf-8 -*-
import sys, traceback, io
name = sys.argv[1]
try:
    code = open(name, encoding="utf-8").read()
    g = {"__name__": "__main__", "__file__": name}
    exec(compile(code, name, "exec"), g)
except Exception:
    open("_run_err.txt", "w", encoding="utf-8").write(traceback.format_exc())
    sys.exit(1)
