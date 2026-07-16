const keys = Object.keys(process.env).filter(k => /proxy|PROXY/i.test(k));
for (const k of keys) console.error(k, "=", JSON.stringify(process.env[k]));
console.error("no_proxy lower:", JSON.stringify(process.env.no_proxy), JSON.stringify(process.env.NO_PROXY));
