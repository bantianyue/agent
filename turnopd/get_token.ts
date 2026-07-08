import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "./_wechat_extend_config.ts";
import fs from "node:fs";

const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const r = await fetch(tokenUrl);
const d: any = await r.json();
if (d.errcode) { console.error("token err", d); process.exit(1); }
fs.writeFileSync("./_token.txt", d.access_token);
console.error("token saved");
