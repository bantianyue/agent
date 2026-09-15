import re,sys
sys.stdout.reconfigure(encoding="utf-8")
t=open("_raw_text.txt",encoding="utf-8").read()
for m in re.finditer(r"Figure\s*\d+[:.]?", t):
    s=max(0,m.start()-20); print(repr(t[s:m.start()+160].replace("\n"," ")))
print("=== tables ===")
for m in re.finditer(r"Table\s*\d+[:.]?", t):
    s=max(0,m.start()-20); print(repr(t[s:m.start()+140].replace("\n"," ")))
