import fs from "node:fs";
const d = JSON.parse(fs.readFileSync("_mdout.json", "utf-8"));
console.log(d.htmlPath);
