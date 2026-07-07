const { execSync } = require("child_process");
const fs = require("fs");

console.error("Step 1: Render markdown...");
const mdResult = execSync(
  'npx -y tsx "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\md-to-wechat.ts" "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_human.md" --theme default --no-cite',
  { cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts", timeout: 60000 }
);
const data = JSON.parse(mdResult.toString());
let html = fs.readFileSync(data.htmlPath, "utf-8");

for (const img of data.contentImages) {
  const tag = `<img src="${img.localPath}" alt="${img.alt || ""}" style="display: block; width: 100%; margin: 1.5em auto;">`;
  const escaped = img.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  html = html.replace(new RegExp(escaped + '\\b', 'g'), tag);
}

const out = "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_with_images.html";
fs.writeFileSync(out, html, "utf-8");

console.error(`Images: ${data.contentImages.length}, HTML saved`);

// Create NEW draft (no --draft-media-id)
console.error("Step 2: Push as new draft...");
const push = execSync(
  `npx -y bun "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\wechat-api.ts" "${out}" --theme default --cover "D:\\06_Hermes\\articles\\workspace-agent-brain\\anthropic_hero.jpg" --no-cite`,
  { cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts", timeout: 300000 }
);
console.log("PUSH:", push.toString());
