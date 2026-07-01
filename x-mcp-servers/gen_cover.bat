@echo off
cd /d D:\06_Hermes\articles\x-mcp-servers
ffmpeg -y -f lavfi -i "color=c=#0c0e12:s=900x383:d=1" -vf "drawbox=x=0:y=0:w=900:h=4:color=#1d9bf0:t=fill,drawtext=text='X Official MCP Server':fontfile=C\:/Windows/Fonts/msyhbd.ttc:fontsize=32:fontcolor=white:x=30:y=260,drawtext=text='AI Tools -> X API Gateway':fontfile=C\:/Windows/Fonts/msyh.ttc:fontsize=17:fontcolor=#a0b4c8:x=30:y=303,drawtext=text='XMCP  |  Docs MCP  |  OpenAPI':fontfile=C\:/Windows/Fonts/msyh.ttc:fontsize=13:fontcolor=#8ca0b4:x=12:y=355" -frames:v 1 cover.png
ffmpeg -y -i cover.png -vf "scale=500:500,format=yuv420p" cover-square.png
echo DONE
