import { readFileSync } from "fs";

const envPath = `${process.env.HOME}/.baoyu-skills/.env`;
const envTxt = readFileSync(envPath, "utf-8");
const env: Record<string, string> = {};
for (const line of envTxt.split("\n")) {
  const i = line.indexOf("=");
  if (i > 0) env[line.slice(0, i).trim()] = line.slice(i + 1).trim();
}
const appId = env["WECHAT_APP_ID"];
const appSecret = env["WECHAT_APP_SECRET"];

const tokenResp = await fetch(
  `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`,
);
const tokenData: any = await tokenResp.json();
if (tokenData.errcode) {
  console.error("token error", tokenData);
  process.exit(1);
}
const accessToken = tokenData.access_token;
console.error("token ok");

const badIds = [
  "TIqnnVEu6Oy3-wtKttGa0ddYYxGKxxjMyl3DNcvMXFnJ4L0nFdiR-_BXkrMGhDD3",
];

for (const mediaId of badIds) {
  const r = await fetch(
    `https://api.weixin.qq.com/cgi-bin/draft/delete?access_token=${accessToken}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ media_id: mediaId }),
    },
  );
  const d: any = await r.json();
  console.error(`delete ${mediaId}: errcode=${d.errcode} errmsg=${d.errmsg}`);
}
