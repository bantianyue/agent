const fs = require("fs");
const { execSync } = require("child_process");

// Step 1: Run md-to-wechat, capture stdout
console.error("Step 1: Rendering markdown...");
const mdResult = execSync(
  'npx -y tsx "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\md-to-wechat.ts" "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_human.md" --theme default --no-cite',
  {
    cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts",
    timeout: 60000,
  }
);

const data = JSON.parse(mdResult.toString());
const htmlPath = data.htmlPath;
const contentImages = data.contentImages;

console.error(`HTML: ${htmlPath}`);
console.error(`Images: ${contentImages.length}`);

// Step 2: Read HTML and replace placeholders with <img> tags
let html = fs.readFileSync(htmlPath, "utf-8");

for (const img of contentImages) {
  const imgTag = `<img src="${img.localPath}" alt="${img.alt || ""}" style="display: block; width: 100%; margin: 1.5em auto;">`;
  const regex = new RegExp(img.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
  html = html.replace(regex, imgTag);
}

// Save modified HTML
const outPath = "D:\\06_Hermes\\articles\\workspace-agent-brain\\article_with_images.html";
fs.writeFileSync(outPath, html, "utf-8");
console.error(`Saved HTML with images to: ${outPath}`);

// Step 3: Push via wechat-api
console.error("Step 3: Pushing draft...");
try {
  const pushOut = execSync(
    `npx -y bun "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\wechat-api.ts" "${outPath}" --theme default --cover "D:\\06_Hermes\\articles\\workspace-agent-brain\\anthropic_hero.jpg" --draft-media-id "TIqnnVEu6Oy3-wtKttGa0ap7nwQNHG7H3F3RH_JXTXsvGR-5RkSBbMPNDNhmA62d" --no-cite`,
    {
      cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts",
      timeout: 180000,
    }
  );
  console.log("STDOUT:", pushOut.toString());
} catch (e) {
  console.error("STDERR:", e.stderr ? e.stderr.toString() : e.message);
  console.error("STDOUT:", e.stdout ? e.stdout.toString() : "");
}
