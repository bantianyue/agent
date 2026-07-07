import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const baseDir = path.resolve(__dirname, "..", "..", "bak_another", "private_agent", "skills", "baoyu-post-to-wechat", "scripts");
const { loadCredentials, resolveAccount, loadWechatExtendConfig } = await import(path.join(baseDir, "wechat-extend-config.ts"));
const { wechatHttp } = await import(path.join(baseDir, "wechat-http.ts"));

const TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get";

async function main() {
  const draftMediaId = process.argv[2] || fs.readFileSync(path.join(__dirname, "draft.id"), "utf-8").trim();
  const extConfig = loadWechatExtendConfig();
  const resolved = resolveAccount(extConfig);
  const creds = loadCredentials(resolved);

  const tokenUrl = `${TOKEN_URL}?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
  const tokenRes = await wechatHttp(tokenUrl);
  const tokenData = await tokenRes.json();
  if (tokenData.errcode) throw new Error(`Token error ${tokenData.errcode}: ${tokenData.errmsg}`);
  const accessToken = tokenData.access_token;

  const res = await wechatHttp(`${DRAFT_GET_URL}?access_token=${accessToken}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ media_id: draftMediaId }),
  });
  const data = await res.json();
  if (data.errcode) throw new Error(`Draft get error ${data.errcode}: ${data.errmsg}`);

  const article = data.news_item?.[0];
  if (!article) throw new Error("No news_item in draft response");

  fs.writeFileSync(path.join(__dirname, "server_content.html"), article.content || "", "utf-8");

  console.log(JSON.stringify({
    title: article.title,
    content_length: (article.content || "").length,
    thumb_url: article.thumb_url,
    digest: article.digest,
  }));
}

await main().catch(e => { console.error(e.message); process.exit(1); });
