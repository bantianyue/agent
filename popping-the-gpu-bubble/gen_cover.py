import subprocess, os

cwd = 'D:\\06_Hermes\\articles\\popping-the-gpu-bubble'
os.chdir(cwd)

font = 'msyhbd_font.ttc'
font2 = 'msyh_font.ttc'

# Write text files - avoid % character in textfile (ffmpeg interprets it)
with open('cover_title.txt', 'w', encoding='utf-8') as f:
    f.write('Popping the GPU Bubble')
with open('cover_sub.txt', 'w', encoding='utf-8') as f:
    f.write('Photon引擎pipelined decoding提速35%')
with open('cover_footer.txt', 'w', encoding='utf-8') as f:
    f.write('Moondream Engineering')

# cover.png (900x383) - use -update 1
vf = (
    'drawbox=x=0:y=0:w=900:h=383:color=#0c0e12:t=fill,'
    'drawbox=x=0:y=0:w=900:h=5:color=#3b82f6:t=fill,'
    "drawtext=textfile=cover_title.txt:fontfile=" + font + ":fontsize=40:fontcolor=white:x=30:y=250,"
    "drawtext=textfile=cover_sub.txt:fontfile=" + font2 + ":fontsize=15:fontcolor=#94a3b8:x=30:y=300,"
    "drawtext=textfile=cover_footer.txt:fontfile=" + font2 + ":fontsize=13:fontcolor=#64748b:x=30:y=340"
)

cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=#0c0e12:s=900x383:d=1', '-vf', vf, '-update', '1', '-frames:v', '1', 'cover.png']
print('Generating cover.png...')
subprocess.run(cmd, check=True)
print('cover.png OK')

# cover-square.png
with open('sq_title.txt', 'w', encoding='utf-8') as f:
    f.write('Popping the GPU Bubble')
with open('sq_sub.txt', 'w', encoding='utf-8') as f:
    f.write('pipelined decoding +35%')

vf2 = (
    'drawbox=x=0:y=0:w=500:h=500:color=#0c0e12:t=fill,'
    'drawbox=x=0:y=0:w=500:h=5:color=#3b82f6:t=fill,'
    "drawtext=textfile=sq_title.txt:fontfile=" + font + ":fontsize=32:fontcolor=white:x=20:y=200,"
    "drawtext=textfile=sq_sub.txt:fontfile=" + font2 + ":fontsize=15:fontcolor=#94a3b8:x=20:y=250"
)
cmd2 = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=#0c0e12:s=500x500:d=1', '-vf', vf2, '-update', '1', '-frames:v', '1', 'cover-square.png']
subprocess.run(cmd2, check=True)
print('cover-square.png OK')

for f in ['cover.png', 'cover-square.png']:
    sz = os.path.getsize(f)
    print(f'{f}: {sz} bytes')
