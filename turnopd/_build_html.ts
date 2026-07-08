import fs from "node:fs";
const d = JSON.parse(fs.readFileSync("_mdout.json", "utf8"));
let html = fs.readFileSync(d.htmlPath, "utf8");
for (const im of (d.contentImages || [])) {
  const url = im.originalPath.replace(/^http:\/\//, "https://");
  const img = `<img src="${url}" style="display:block;width:100%;margin:1.5em auto;">`;
  html = html.split(im.placeholder).join(img);
}
fs.writeFileSync("_rendered.html", html);
console.log("done, size", html.length);
