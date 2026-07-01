<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>X发布两套MCP Server</strong>：XMCP将200+ 个X API端点暴露为AI可调用的工具；Docs MCP提供搜索/读取文档的能力<br><br>
- <strong>本地部署配置</strong>：XMCP需Python 3.9+、OAuth 1.0a凭证和浏览器授权，支持工具白名单限制<br><br>
- <strong>同时使用两套即可用AI做完整X操作</strong>：一边查文档、一边发推、搜索用户、管理帖子
</div>
</div>

X在官方的开发者文档中正式发布了两个MCP（Model Context Protocol）Server，一套旨在将X API的200多个端点直接暴露为AI工具：这意味着你的Cursor、Windsurf或自定义Agent可以直接发帖、搜用户、查时间线，而不用写一行curl。

---

**XMCP — 真正的X API工具化**

XMCP是本地运行的服务端，它会根据X API v2的OpenAPI规范自动生成200多个可调用工具。你只需运行一个Python服务器，然后配置你的MCP客户端指向 `http://127.0.0.1:8000/mcp`。

配置方式很直接：克隆 `xdevplatform/xmcp` 仓库，建Python虚拟环境，装依赖，在 `.env` 中填入开发者控制台拿到的OAuth 1.0a consumer key/secret和bearer token，设置回调URL，然后 `python server.py` 启动。

认证走的是浏览器授权流程：首次连接时会弹出一个OAuth页面让你点确认，之后的会话token保存在内存中。**Token不会跨重启持久化**，这是一个设计上的安全考量，但也意味着每次重启服务器都需要重新认证。

**XMCP还支持工具白名单**：设置环境变量 `X_API_TOOL_ALLOWLIST`，只允许特定工具可用。比如你想让Agent只读不写，就只允许 `getUsersByUsername` 和 `searchPostsRecent`，不暴露 `createPosts`。

限制方面：不支持streaming和webhook端点，因为这类API需要持久连接。此外API规格在启动时从远程加载并缓存，要更新规格就必须重启服务器。

---

**Docs MCP — 文档搜索即工具**

Docs MCP是一个托管的MCP Server（即不需要你在本地跑代码），可以直接在你的MCP客户端配置中指向 `https://docs.x.com/mcp`。它提供两个工具：`search_x` 搜索X开发者文档（API参考、代码示例、指南），`get_page_x` 获取某个文档页面的完整内容。

这对开发者来说极其实用：你可以在写代码的同时，让Agent查文档找参数签名和代码示例，不必离开编辑器开浏览器。再加上XMCP，你甚至可以让Agent：从文档中查到某个端点的用法，然后用实际API调用去验证。

---

**同时使用，实现能力闭环**

X官方推荐的做法是把两个Server一起配到MCP Client的配置文件中：

```json
{
  "mcpServers": {
    "xmcp": {
      "url": "http://127.0.0.1:8000/mcp"
    },
    "x-docs": {
      "url": "https://docs.x.com/mcp"
    }
  }
}
```

一个查文档，一个调接口。对于自己的Agent来说，这个组合基本覆盖了所有X相关的操作需求。

此外X还专门提到了OpenAPI规范的位置：`https://api.x.com/2/openapi.json`。这个JSON可以直接下载后用来自动生成API客户端、导入Postman、或喂给自定义AI Agent做快速原型验证。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
MCP生态中有大量"非官方"的X适配器，但官方出手意味着两件事：一是工具数量和参数覆盖率的差异（200+ 工具vs社区版的5-10个），二是接口稳定性的保障。<br><br>
更值得关注的是design pattern：把文档也做成MCP Server。这比传统RAG方案更直接：文档不是"外部知识"而是"一个工具"，Agent不用事先检索，用的时候直接调用即可。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://docs.x.com/tools/mcp</span>
