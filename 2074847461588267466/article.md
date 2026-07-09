<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>一键配置体检</strong>：Claude Code新命令 /checkup把七类工程配置整理工作打包成一个命令，扫描并清理碍事、过期、重复的配置<br><br>
- <strong>七件事一次做对</strong>：清理闲置技能/MCP/插件省上下文、本地与签入CLAUDE.md去重、拆分根CLAUDE.md、关慢钩子、升级到最新、默认开auto模式、预批准常被拒的只读命令<br><br>
- <strong>先确认再动手</strong>：任何改动前都会先跟用户确认，只给方案不静默执行，治理权留在人手里
</div>
</div>

---

## 它到底帮你做什么

Claude Code新上了一个 /checkup命令。它把自己定位成工程的"配置体检员"：扫描你当前的项目配置，把那些碍事、过期、重复的东西一次性整理干净。

具体能做的，原帖列了七件：

1. **清理未使用的技能、MCP、插件**，把被占着的上下文腾出来
2. **把本地CLAUDE.md和仓库里签入的CLAUDE.md去重**，避免两份配置各说各话
3. **把根目录那个越来越大的CLAUDE.md拆成嵌套的CLAUDE.md加技能**，分模块管理
4. **关掉那些跑得慢、拖节奏的钩子**
5. **把Claude Code自身更新到最新版本**
6. **默认开启自动模式（auto mode）**
7. **预批准那些你老是一遍遍拒绝的只读命令**，少打断你

<div style="font-size:14px;line-height:1.75;color:#3f3f3f;">

除了这七条，原帖还留了句"还有几个其他的小惊喜"，没有展开。

![](img1.png)
<span style="font-size:12px;color:rgb(153,153,153);">Claude Code官方演示视频截图</span>

</div>

## 关键设计：先确认，再动手

最值得注意的不是它能做多少事，而是它的克制：/checkup在做出任何改动之前，都会先跟你确认。

换句话说，它只负责"发现问题和给出方案"，真正的执行权还在你手里。这一点对配置类操作格外重要，CLAUDE.md、钩子、MCP都是牵一发动全身的东西，自动改了容易翻车。

<div style="font-size:14px;line-height:1.75;color:#3f3f3f;">

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">Claude Code官方演示视频截图</span>

</div>

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这类"自查加整理"命令的出现，说明AI编码工具已经从"能帮你写代码"进入"能帮你治理工程配置"的阶段。上下文膨胀、配置漂移，是重度用户真实的痛点。<br><br>
"先确认再动手"的设计也暴露了一个现实：Agent现在还不敢对工程配置完全自主，治理权依然是人机共持，而这恰恰是这类工具能被信任的前提。<br><br>
七件事里有四件（清理、去重、拆分、关钩子）都是在做减法。Claude Code越堆功能，越需要有人帮用户把复杂度收回来。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/christinexzhu/status/2074847461588267466</span>
