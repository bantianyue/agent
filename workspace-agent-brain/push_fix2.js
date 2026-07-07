const { execSync } = require("child_process");
const fs = require("fs");

// Step 1: Run md-to-wechat fresh
console.error("Step 1: Rendering markdown...");
const mdResult = execSync(
  'npx -y tsx "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\md-to-wechat.ts" "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_human.md" --theme default --no-cite',
  { cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts", timeout: 60000 }
);

const data = JSON.parse(mdResult.toString());
const htmlPath = data.htmlPath;
const contentImages = data.contentImages;

console.error(`HTML: ${htmlPath}, Images: ${contentImages.length}`);

// Step 2: Read fresh HTML
let html = fs.readFileSync(htmlPath, "utf-8");

// Replace each placeholder with <img> tag — use word boundary regex to avoid WECHATIMGPH_1 matching WECHATIMGPH_10
for (const img of contentImages) {
  const imgTag = `<img src="${img.localPath}" alt="${img.alt || ""}" style="display: block; width: 100%; margin: 1.5em auto;">`;
  // Use word boundary to prevent WECHATIMGPH_1 matching WECHATIMGPH_10
  const escaped = img.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(escaped + '\\b', 'g');
  html = html.replace(regex, imgTag);
}

// Verify no placeholders remain
const remaining = html.match(/WECHATIMGPH_\d+/g);
if (remaining) {
  console.error(`ERROR: ${remaining.length} placeholders remain: ${remaining.slice(0,5)}`);
  process.exit(1);
}

const outPath = "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_with_images.html";
fs.writeFileSync(outPath, html, "utf-8");
console.error(`Saved HTML with images`);

// Verify images
const imgMatch = html.match(/<img[^>]+src="([^"]+)"/g);
console.error(`Image tags in HTML: ${imgMatch ? imgMatch.length : 0}`);

// Step 3: Push
console.error("Step 3: Pushing draft...");
try {
  const pushOut = execSync(
    `npx -y bun "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\wechat-api.ts" "${outPath}" --theme default --cover "D:\\06_Hermes\\articles\\workspace-agent-brain\\anthropic_hero.jpg" --draft-media-id "TIqnnVEu6Oy3-wtKttGa0ap7nwQNHG7H3F3RH_JXTXsvGR-5RkSBbMPNDNhmA62d" --no-cite`,
    { cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts", timeout: 300000 }
  );
  console.log("PUSH:", pushOut.toString());
} catch (e) {
  console.error("ERR:", e.stderr ? e.stderr.toString() : e.message);
  if (e.stdout) console.error("OUT:", e.stdout.toString());
}
