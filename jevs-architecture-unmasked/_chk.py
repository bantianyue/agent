import importlib, sys
for m in ("playwright", "bs4", "PIL", "jinja2", "pygments", "fitz", "httpx"):
    try:
        mod = importlib.import_module(m)
        print(m, "OK", getattr(mod, "__version__", "?"))
    except Exception as e:
        print(m, "MISSING", e)
print(sys.version)
