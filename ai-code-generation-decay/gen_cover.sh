# 封面：从推文卡片图生成

cd "D:\\06_Hermes\\articles\\ai-code-generation-decay"

# img1.jpg 是推文封面图（900×360），直接拉伸到 900×383
ffmpeg -y -i img1.jpg -vf "scale=900:383,format=yuv420p" -update 1 cover.png

# 1:1 方形封面
ffmpeg -y -i img1.jpg -vf "scale=500:500,format=yuv420p" -update 1 cover-square.png

echo "Covers generated"
ls -la cover*.png
