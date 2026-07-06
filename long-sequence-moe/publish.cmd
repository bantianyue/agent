cd "D:/06_Hermes/articles/long-sequence-moe"
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
npx -y bun "$LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts" article_human.md --theme default --title "Dockerless：无需Docker环境的代码补丁验证器，编码Agent训练不再卡在跑测试" --author "AI圈的9527" --cover cover.png --no-cite --draft-media-id "$(cat draft.id)" 2>&1