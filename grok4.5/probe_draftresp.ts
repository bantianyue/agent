import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "C:/Users/twfehh7/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";
const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const token = (await (await fetch(tokenUrl)).json()).access_token;
const r = await fetch(`https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ offset: 0, count: 5 })
});
const j = await r.json();
console.log(JSON.stringify(j, null, 2).slice(0, 1500));
