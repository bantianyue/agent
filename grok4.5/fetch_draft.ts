import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "C:/Users/twfehh7/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";
import fs from "node:fs";

const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const token = (await (await fetch(tokenUrl)).json()).access_token;

const target = fs.readFileSync("draft.id", "utf8").trim();
console.error("target media_id:", target);

// fetch draft list
const r = await fetch(`https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ offset: 0, count: 20 })
});
const j = await r.json();
console.error("total_count:", j.total_count, "item_count:", (j.item_list||[]).length);
const item = (j.item_list||[]).find((it:any)=> it.media_id === target);
if (!item) { console.error("DRAFT NOT FOUND"); process.exit(2); }
const c = item.content;
const article = c.news_item ? c.news_item[0] : c;
const out = {
  title: article.title,
  author: article.author,
  digest: article.digest,
  content: article.content
};
fs.writeFileSync("server_draft.json", JSON.stringify(out, null, 2));
console.error("saved server_draft.json, html len:", out.content.length);
