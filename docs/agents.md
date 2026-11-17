# 用 Agent 选型

克隆仓库后，给 Codex 或 Claude Code 以下任务。安装前可直接读取目录和运行 `bin/plan <feature> --json`。如果已注册 MCP，可以换用 `local_specialists.plan_deployment`，参数和逻辑相同。

> 先读仓库的 docs/deployment.md 和 docs/agents.md，并调用 plan_deployment 或 bin/plan 查看决策树。我的任务是「填入预期输出」，设备是「填入 macOS 版本、芯片、内存和可用空间」，用途是「个人、商业、生产或研究」，硬性要求是「填入坐标、词时间、说话人、术语、素材留在本机等要求」。
>
> 给出首选、备选和被排除的理由，标明已有实测、还需配置或需上游试跑。列出与我任务对应的部署说明、安装命令，以及一条用合成数据检查结果的步骤。若有一个答案会改变选择，先问我这一项。部署时按我已明确的安装范围执行。

也可传 `profile=default` 优先检查默认安装，或指定 `profile=optional` 查专项路径。每个候选的 `mcp` 和 `local_cli` 给出实际调用。`mcp.server` 区分 `local-lfm` 与 `local_specialists`。`status` 中的 `lfm_models` 来自本机回环服务，代表服务可见的型号。验证仍用实际任务的样例。

规划另一台机器时，向 `plan_deployment` 传 `target`，例如 `{"machine":"arm64","macos":"27.2","disk_gib":100,"memory_gib":24}`。显式目标使用 `unknown_on_target` 标记，提醒 Agent 在那台机器上复核实际安装和资源。给 LFM 复核选型时，把选定候选 `mcp.arguments` 中的 `model` 一并传给工具。

在本机查询用户指定的资料目录时，把获准的绝对路径传给 `plan_deployment.folder`。只在选型返回需要准备索引时查阅索引配方，已就绪时用返回的 `mcp.arguments` 加上用户的查询词调用 `search`。

## 两个示例

**「需要从校订稿生成单词时间，录音和文本留在本机。」**

```sh
bin/plan align-transcript --execution local --require corrected_transcript --verified-only --json
```

最合适的是 Qwen3-ForcedAligner。需提供同一段录音、校订稿和语言，单次最多 120 秒。执行阶段直接在本机用 `bin/local align_audio`。

**「公司资料需要按含义检索，要求能商用。」**

```sh
bin/plan semantic-search --use commercial --execution mcp --verified-only --json
```

选 DigUp。安装后为获准的目录运行 `bin/local index-digup <目录>`，再用 `search` 查询并核对页码或时间。查代码时给建索引命令加 `--code`，查询时传 `code=true`。Omni 的 Jina 权重适用非商业条款。

## 从选择到部署

1. 读取返回的 `recipe`，检查 `evidence`、`readiness` 和 `reasons`。如果没有推荐项，保留导致排除的硬性条件。
2. 对照目标和安装范围，说明磁盘估算、外部 App 和所需系统资源。按路线检查索引、配对、麦克风或硬件。上游路线在独立环境试跑。
3. 用户要求部署后，按步骤安装指定路线。校验来源和版本，先用合成样例得到预期格式和定位信息。
4. MCP 路线用 `status` 和一条工具实跑检查客户端连接。CLI 路线在本机检查输出。处理实际资料前，确认资料可走的路径和可返回的证据范围。

`plan_deployment` 只返回选型信息。云端 Agent 可能收到推理工具的参数和返回内容。对于要求完全留在本机的材料，可运行 `bin/local`、上游本机命令，或以 `bin/lfm codex --with-specialists`、`bin/lfm claude --with-specialists` 启动本机 LFM 会话。 [离线客户端调用专项工具](deployment.md#offline-specialists)
