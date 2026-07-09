import subprocess, os
os.chdir("D:/06_Hermes/articles/grok4.5")
base="gemini_cover.png"
f_title=os.path.abspath("msyhbd0.ttf")
f_sub=f_title
f_bottom=f_title
flt=(
    "scale=900:383,format=yuv420p,"
    "drawbox=x=0:y=0:w=900:h=128:color=black@0.55:t=fill,"
    "drawbox=x=0:y=312:w=900:h=71:color=black@0.62:t=fill,"
    f"drawtext=text='Grok 4.5':fontfile='{f_title}':fontsize=48:fontcolor=white:x=24:y=18,"
    f"drawtext=text='马斯克的翻身仗':fontfile='{f_sub}':fontsize=30:fontcolor=#FFC832:x=26:y=80,"
    f"drawtext=text='Opus 4.8 的性能   ×   中国开源模型的价格':fontfile='{f_bottom}':fontsize=23:fontcolor=#A0B4C8:x=24:y=342"
)
cmd=["ffmpeg","-y","-i",base,"-vf",flt,"-frames:v","1","cover.png"]
r=subprocess.run(cmd,capture_output=True,text=True)
print("RC",r.returncode, r.stderr[-400:] if r.returncode else "OK cover.png")
if r.returncode==0:
    r2=subprocess.run(["ffmpeg","-y","-i","cover.png","-vf","scale=500:500,format=yuv420p","cover-square.png"],capture_output=True,text=True)
    print("square RC",r2.returncode)
