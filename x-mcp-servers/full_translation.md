X 官方发布了两个 MCP Server：XMCP（本地运行，将 X API v2 的 200+ 端点暴露为 AI 工具）和 Docs MCP（托管的文档搜索/读取工具）。本页详述了安装、配置、工具白名单、OpenAPI 规格以及如何在同一个 MCP Client 中同时使用两者。注意限制：不支持 streaming 和 webhook，spec 在启动时缓存，token 仅存于内存。
