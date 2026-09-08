# -*- coding: utf-8 -*-
import os,glob,time
root=r"D:/06_Hermes/articles"
names=["b200-attention","b200-matmul-kernels","language-models-control-attention",
"opd-support-in-miles","test-htmlpipe","tp-throughput-sglang",
"ultrascale-p1-singlegpu-dp","ultrascale-p3-ring-pp-expert"]
for n in names:
    d=os.path.join(root,n)
    print("=="*2,n)
    if not os.path.isdir(d): print("  (missing)");continue
    # draft
    print("  draft.id:",open(os.path.join(d,'draft.id')).read()[:14] if os.path.exists(os.path.join(d,'draft.id')) else 'NONE')
    pr=os.path.join(d,'progress.md')
    if os.path.exists(pr):
        t=open(pr,encoding='utf8',errors='ignore').read()
        print("  progress head:", t.splitlines()[0][:110] if t.splitlines() else '')
    # logs
    lg=glob.glob(os.path.join(d,'logs','*.log'))
    print("  log files:",len(lg))
    for h in sorted(lg,key=os.path.getmtime)[-2:]:
        print("    ",os.path.basename(h),time.strftime('%m-%d %H:%M',time.localtime(os.path.getmtime(h))))
    # newest content file mtime for heuristic
    mt=max(os.path.getmtime(os.path.join(d,f)) for f in os.listdir(d) if os.path.isfile(os.path.join(d,f)))
    print("  newest file:",time.strftime('%m-%d %H:%M',time.localtime(mt)))
