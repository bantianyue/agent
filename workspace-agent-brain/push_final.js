const { execSync } = require("child_process");
const push = execSync(
  `npx -y bun "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts\\wechat-api.ts" "D:\\06_Hermes\\articles\\workspace-agent-brain\\formatted_content.html" --theme default --cover "D:\\06_Hermes\\articles\\workspace-agent-brain\\cover2.jpg" --title "Anthropic用J透镜打开LLM意识黑箱 J-Space,揭秘干预LLM内部思维的新训练技术" --author "AI圈的9527" --no-cite`,
  { cwd: "D:\\06_Hermes\\bak_another\\private_agent\\skills\\baoyu-post-to-wechat\\scripts", timeout: 300000 }
);
console.log(push.toString());
