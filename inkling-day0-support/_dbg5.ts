const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || null;
const url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=test&secret=test";
let directCount = 0, proxyCount = 0;
for (let i = 0; i < 15; i++) {
  try {
    const res = await fetch(url, { proxy: proxyUrl as any });
    const body = await res.text();
    if (body.includes("40164")) { directCount++; console.error(`#${i} DIRECT-FALLBACK (40164)`); }
    else { proxyCount++; console.error(`#${i} proxy-ok (${res.status})`); }
  } catch (e:any) { console.error(`#${i} ERR ${e.message.slice(0,60)}`); }
}
console.error(`\nSUMMARY: proxy-ok=${proxyCount}, direct-fallback=${directCount}`);
