console.error("HTTPS_PROXY=", process.env.HTTPS_PROXY);
console.error("HTTP_PROXY=", process.env.HTTP_PROXY);
const proxyArg = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || null;
console.error("proxyArg=", proxyArg);
const r = await fetch("https://api.ipify.org", { proxy: proxyArg as any });
console.error("ipify via proxyArg:", await r.text());
