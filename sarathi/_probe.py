# -*- coding: utf-8 -*-
import re, os, sys, html as H, json

ART = r"D:\06_Hermes\articles\sarathi"
raw = open(os.path.join(ART, "_raw.html"), encoding="utf-8").read()

try:
    from bs4 import BeautifulSoup
    print("BS4 OK")
except Exception as e:
    print("BS4 FAIL", e)
try:
    import playwright
    print("PLAYWRIGHT OK")
except Exception as e:
    print("PLAYWRIGHT FAIL", e)
try:
    import PIL
    print("PIL OK", PIL.__version__)
except Exception as e:
    print("PIL FAIL", e)
try:
    import fitz
    print("FITZ OK")
except Exception as e:
    print("FITZ FAIL", e)
try:
    import cairosvg
    print("CAIROSVG OK")
except Exception as e:
    print("CAIROSVG FAIL", e)
