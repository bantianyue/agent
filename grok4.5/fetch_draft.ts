import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "C:/Users/twfehh7/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";
import fs from "node:fs";

const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const token = (await (await fetch(tokenUrl)).json()).access_token;

const target = fs.readFileSync("draft.id", "utf8").trim();
const r = await fetch(`https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ offset: 0, count: 20 })
});
const j = await r.json();
const item = (j.item || []).find((it:any)=> it.media_id === target);
if (!item) { console.error("DRAFT NOT FOUND"); process.exit(2); }
const article = item.content.news_item[0];
fs.writeFileSync("server_draft.html", article.content);
fs.writeFileSync("server_meta.json", JSON.stringify({ title: article.title, author: article.author, digest: article.digest }, null, 2));
// collect mmbiz image urls
const urls = [...article.content.matchAll(/https:\/\/mmbiz\.qpic\.cn\/[^\s"'`)]+/g)].map(m=>m[0]);
fs.writeFileSync("server_imgs.txt", urls.join("\n"));
console.error("title:", article.title);
console.error("html len:", article.content.length, "imgs:", urls.length);
