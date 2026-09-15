import sys,re
sys.stdout.reconfigure(encoding="utf-8")
t=open("_raw_text.txt",encoding="utf-8").read()
parts=re.split(r"===== PAGE (\d+) =====",t)
pages={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
lo,hi=int(sys.argv[1]),int(sys.argv[2])
for n in range(lo,hi+1):
    print("\n########## PAGE %d ##########"%n)
    print(pages[n].strip())
