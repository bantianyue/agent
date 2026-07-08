import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "C:/Users/twfehh7/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";
import { wechatHttp } from "C:/Users/twfehh7/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-http.ts";

const mediaId = process.argv[2];
if (!mediaId) { console.error("usage: fetch_draft.ts <media_id>"); process.exit(1); }

const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);

const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const tokenRes = await wechatHttp(tokenUrl);
const tokenData = await tokenRes.json<any>();
if (tokenData.errcode) { console.error("token err", tokenData); process.exit(1); }
const token = tokenData.access_token;

const getUrl = `https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${token}`;
const res = await wechatHttp(getUrl, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ media_id: mediaId }),
});
const data = await res.json<any>();
if (data.errcode) { console.error("draft/get err", data); process.exit(1); }

const news = data.news_item || [];
for (const item of news) {
  const content = item.content || "";
  const imgRegex = /<img[^>]*\ssrc=["']([^"']*mmbiz\.qpic\.cn[^"']*)["'][^>]*>/gi;
  const matches = [...content.matchAll(imgRegex)];
  console.error(`TITLE: ${item.title}`);
  console.error(`IMG COUNT: ${matches.length}`);
  for (const m of matches) {
    console.log(m[1]);
  }
}
