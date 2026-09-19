import fitz, glob, os
pairs={"fig00":"data/ablation.pdf","fig05":"data/e2e-moe.pdf","fig06":"data/e2e-multi-step.pdf","fig07":"data/e2e-throughput.pdf","fig08":"data/motiv-acc-len.pdf","fig11":"data/motiv-rollout.pdf","fig15":"data/timeline.pdf"}
for out,pdf in pairs.items():
    d=fitz.open("_src_tmp/"+pdf); p=d[0]
    z=1400.0/p.rect.width
    pix=p.get_pixmap(matrix=fitz.Matrix(z,z), alpha=False)
    pix.save(out+".png"); print(out,pdf,"->",pix.width,pix.height)
    d.close()
