import {
  loadWechatExtendConfig,
  resolveAccount,
  loadCredentials,
} from "./_wechat_extend_config.ts";

const mediaId = process.argv[2];
if (!mediaId) { console.error("usage: fetch_draft_urls.ts <media_id>"); process.exit(1); }

const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
console.error(`[debug] appId=${creds.appId} source=${creds.source}`);

const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const tokenRes = await fetch(tokenUrl);
const tokenData: any = await tokenRes.json();
if (tokenData.errcode) { console.error("token err", tokenData); process.exit(1); }
const token = tokenData.access_token;

const getUrl = `https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${token}`;
const res = await fetch(getUrl, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ media_id: mediaId }),
});
const data: any = await res.json();
if (data.errcode) { console.error("draft/get err", data); process.exit(1); }

const news = data.news_item || [];
for (const item of news) {
  const content = item.content || "";
  const imgRegex = /<img[^>]*\ssrc=["']([^"']*mmbiz\.qpic\.cn[^"']*)["'][^>]*>/gi;
  const matches = [...content.matchAll(imgRegex)];
  console.error(`TITLE: ${item.title} | IMG COUNT: ${matches.length}`);
  for (const m of matches) {
    console.log(m[1]);
  }
}
