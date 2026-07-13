import { loadWechatExtendConfig, resolveAccount, loadCredentials } from "./_wechat_extend_config.ts";
import fs from "node:fs";
const extConfig = loadWechatExtendConfig();
const resolved = resolveAccount(extConfig, undefined);
const creds = loadCredentials(resolved);
const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
const token = (await (await fetch(tokenUrl)).json()).access_token;
fs.writeFileSync("./_token.txt", token);
console.log("ok");
