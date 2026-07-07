import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Dynamically resolve the wechat script paths relative to this script's location
const baseDir = path.resolve(__dirname, "..", "..", "bak_another", "private_agent", "skills", "baoyu-post-to-wechat", "scripts");

// We need to import from the resolved absolute paths
const extendConfigPath = path.join(baseDir, "wechat-extend-config.ts");
const httpPath = path.join(baseDir, "wechat-http.ts");

// Dynamic import using absolute paths
const { loadCredentials, resolveAccount, loadWechatExtendConfig } = await import(extendConfigPath);
const { wechatHttp } = await import(httpPath);

const TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get";

async function main() {
  const draftMediaId = process.argv[2];
  if (!draftMediaId) {
    console.error("Usage: bun download_draft.ts <draft_media_id>");
    process.exit(1);
  }

  const extConfig = loadWechatExtendConfig();
  const resolved = resolveAccount(extConfig);
  const creds = loadCredentials(resolved);

  // Get access token
  const tokenUrl = `${TOKEN_URL}?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`;
  const tokenRes = await wechatHttp(tokenUrl);
  const tokenData = await tokenRes.json<{ access_token?: string; errcode?: number; errmsg?: string }>();
  if (tokenData.errcode) {
    throw new Error(`Token error ${tokenData.errcode}: ${tokenData.errmsg}`);
  }
  const accessToken = tokenData.access_token!;
  console.error(`[download_draft] Got access token`);

  // Get draft content
  const getUrl = `${DRAFT_GET_URL}?access_token=${accessToken}`;
  const res = await wechatHttp(getUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ media_id: draftMediaId }),
  });
  const data = await res.json<any>();
  if (data.errcode) {
    throw new Error(`Draft get error ${data.errcode}: ${data.errmsg}`);
  }

  // Extract the article content
  const article = data.news_item?.[0];
  if (!article) {
    throw new Error("No news_item in draft response");
  }

  // Save full response for reference
  fs.writeFileSync(
    path.join(__dirname, "draft_response.json"),
    JSON.stringify(data, null, 2),
    "utf-8"
  );

  // Also save the content HTML to a file
  fs.writeFileSync(
    path.join(__dirname, "server_content.html"),
    article.content || "",
    "utf-8"
  );

  // Output metadata + first 500 chars of content
  console.log(JSON.stringify({
    title: article.title || "",
    author: article.author || "",
    digest: article.digest || "",
    content_length: (article.content || "").length,
    content_source_url: article.content_source_url || "",
    thumb_media_id: article.thumb_media_id || "",
    thumb_url: article.thumb_url || "",
    need_open_comment: article.need_open_comment ?? 1,
    only_fans_can_comment: article.only_fans_can_comment ?? 0,
  }, null, 2));

  console.error(`[download_draft] Done! Content length: ${(article.content || "").length}`);
}

await main().catch((err) => {
  console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
