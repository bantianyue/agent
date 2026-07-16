const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || null;
console.error("[dbg] proxyUrl =", JSON.stringify(proxyUrl));
const url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=test&secret=test";
const res = await fetch(url, { proxy: proxyUrl as any });
console.error("[dbg] status =", res.status);
const txt = await res.text();
console.error("[dbg] body =", txt.slice(0, 200));
// also resolve what IP we hit via ipify through same proxy
const r2 = await fetch("https://api.ipify.org", { proxy: proxyUrl as any });
console.error("[dbg] ipify via same proxy =", await r2.text());
