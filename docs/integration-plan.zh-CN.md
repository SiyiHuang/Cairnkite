# Cairnkite 整合计划

[English](integration-plan.md)

目标是在 Apple Silicon Mac 上给 Codex 和 Claude Code 提供一套可安装、可选择、可验证的本地工具。先完成默认安装，再为按需方案做复现和客户端验收。两边的运行时各自管理依赖，Agent 共用一份部署目录与选型逻辑。

## 项目结构

`bin/` 提供安装、规划和客户端注册入口。`catalog/` 描述候选能力、许可、资源要求与验收状态。`native/` 封装 Apple 框架，`src/` 实现专项 MCP 和 CLI。`backends/lfm/` 管理 LFM 的运行时、模型锁和客户端入口。下载、索引、日志、客户端认证与运行状态在本机管理。

## 默认安装

| 功能 | 默认路径 | 实际部署与验证 |
| --- | --- | --- |
| PDF、扫描和截图 | PDFKit 读文字层；Vision 读扫描页、坐标、简单表格和条码 | 编译 Swift helper，准备两页 PDF 和条码，核对页码、原句、坐标、表格及编号。 |
| 文本 | Natural Language 做识别和内置实体；LFM Fast 做来源可核对的字段抽取、摘要 | 使用现有 LFM Metal 服务和 MCP；测试已有与缺失字段、摘要事实和本地文本调用。 |
| 图像问答 | LFM Vision 解释图片中可见内容；文字和坐标由 Vision OCR 提供 | 用合成截图核对已知值，并核对只读用户暂存的图像。 |
| 音频和翻译 | Apple Speech 与 Apple Translation 在需要的语言资源就绪时启用 | 先跑中英文环境探测，再分别验证真正的转写和翻译。记录地区、语言资源状态、词句和段时间。 |
| 文件定位 | `rg` 查字面和代码符号，Spotlight 查已索引文件的元数据 | 用合成目录确认覆盖范围，返回文件与对应定位。语义结果走独立选项。 |
| Agent 接入 | `local_specialists` 管选型和专用工具，`local-lfm` 管已有 LFM 调用 | 一个项目负责安装、状态、验证和卸载；两个 MCP 名称保留现有调用兼容。Codex 与 Claude Code 各做真实工具往返。 |

默认常驻 LFM Fast，其余运行时和权重按需加载。默认安装可重跑，复用已验过的工具链、权重、语言资源和服务。字段提取沿用 LFM Fast，Apple Swift 路线可在启用 Apple Intelligence 的机器上按需选用。实测差异见[本机验收记录](verification.zh-CN.md)。

## 可选路径与晋级条件

| 任务分支 | 优先验证的路线 | 晋级证据 |
| --- | --- | --- |
| 复杂文档 | PaddleOCR-VL 完整版面流水线；MiniCPM-OCR 独立二读；Jev 局部复核 | 双栏、公式、表格分别比较误差。同页检验源坐标和结构。Jev 比较正确与错误候选。 |
| 音频 | MOSS 8-bit 匿名说话人；Qwen ASR 0.6B／1.7B、ForcedAligner 和流式；Apple SpeechDetector | 实测中文、英文、重叠发言、长录音截断、校订字幕。验证秒数、终稿及说话人标签。 |
| 资料和代码检索 | Omni/Jina 个人资料；DigUp/EmbeddingGemma 2 商用候选；Omni 多 Mac；Core Spotlight 的 App 索引；jina-grep 和 Qwen3-VL-Reranker | 用同一批带答案查询对比 `rg` 和初排，记录命中页、行号或时间码及延迟。先核对权重许可和索引范围。 |
| 文本和通用推理 | Apple Foundation Models 短文本与结构化生成；Hy-MT2 术语；GLiNER2.5 跨度；Privacy Filter；Clef-Flash；LFM Tools 与 Reason、不同量化 | 对比字段与原文定位、空值、术语和分类分数。验证 LFM 工具调用、较大模型并发占用及本地客户端备用模式。隐私过滤使用本机 CLI 并查看剩余敏感信息。 |
| 圆桌和媒体 | TalkNet 活动人脸；SAM 3 掩膜与跟踪；SAM Audio 分音轨；Kokoro 朗读；SwiftVR 与 SeedVR2；Apple Vision 媒体及 Sound Analysis | 用带时间码的短片比较同步、跟踪、声音类别、视频伪影和峰值内存。再试 X4 的可授权片段。 |
| 专项计算和系统动作 | Chronos-2 与 TimesFM；Goedel＋Lean；Core ML Depth Anything 与 Core ML 路径；SmolVLA 回放；Shortcuts | 与时间序列简单基线比较；用 Lean 内核验证固定命题；核对深度排序和回放动作。只有任务需要系统界面状态时使用 Shortcuts 或 Computer Use。 |

文档、会议和资料检索分别由 Paddle、MOSS、词级对齐和语义检索等选项补充。凡能带来可复现的独立输出或同质量下的成本／隐私收益，就给出安装和两客户端调用方式。依赖第二台 Mac、机械臂或系统资源的路线，先做同机可验证的部分，再记录实际缺少的条件。落选路线记录本机试跑结果或上游明确的限制。

## Agent 怎么选

在 `bin/plan` 和 `plan_deployment` 的同一目录中加 `default` / `optional`、本机证据及调用契约。输入任务和硬约束。先按输出粒度、机器与内存、语言资产、许可、执行位置筛掉不可用路线，再根据样本表现、资源占用和已安装状态排序。返回首选、其独特能力、失败条件、备用、安装命令、调用参数和验收样例。`bin/plan` 只读。已有 `bin/install` 的子命令继续可用，新增显式的默认安装和按选项安装入口。

- PDF 有可用文字层 → PDFKit。扫描 → Vision。公式或复杂阅读顺序 → Paddle。疑点 → MiniCPM 二读或原始区域＋候选渲染用 Jev 打分。
- 普通语音 → Apple Speech。需要发言归属 → MOSS。需要词时间 → Qwen。已有校订稿 → ForcedAligner。
- 文件名或符号已知 → Spotlight 或 `rg`。只知道语义 → 已选定资料源的索引。需要图文精排 → 引入专用候选重排。
- 短摘要或原文可核对的字段 → LFM Fast。固定 schema 比较 Apple Foundation Models 的 Swift 实现；正文跨度比较 GLiNER。需要独立复核或本地试用 Coding Agent 时才加载 LFM Reason。
- 私密输入 → 从本机终端运行 CLI 或经实测隔离的本地客户端。由云端主 Agent 委派时，MCP 推理在本机，但工具参数和返回内容可能进入主模型上下文。文件型工具用允许的根目录、内容指针和可分页的证据。优先使用公开框架、CLI、文件和本地 MCP。只有可量化地改善结果，或任务本身依赖界面时，才走 Computer Use。 [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP](https://code.claude.com/docs/en/mcp) · [Apple Foundation Models CLI 和 SDK](https://developer.apple.com/videos/play/wwdc2026/334/)

## 交付顺序与验收

1. 在专用模型仓库运行选型测试，安装并实测 Apple 原生基础功能。用合成数据核对默认行为和客户端连接。查询 Foundation Models 可用性优先用现有 Swift helper。现场 `fm --help` 需机器级 CLI 条款接受，Swift 结果单独记录。
2. 依据 LFM 的版本锁、部署代码和实测结果维护默认方案。保留正在运行的回环地址、服务身份和现有权重。私有输入、模型权重、运行状态、日志和客户端认证留在本机。切换路径前用合成样本跑新工作树，另记录旧路径回滚方式。
3. 合并默认安装、状态、选型和验收入口。至少演练一次重跑安装、未就绪选项、权限拒绝、工具参数错误和本地服务不可用。验证两套 CLI 调用相同工具并拿到可核对结果。Codex 与 Claude Code 的云端主模型会话和本地隔离会话分别记录验收结果。
4. 按上表推进可选方案。每条发布路线记录固定版本、来源、许可、所需资源、本机 CLI、Codex 和 Claude Code 接入方式、合成输入、期待输出及实际结果。仅确认 MCP 工具列表或模型文件存在时，路线上保留待验状态。
5. 默认路线在实际 Mac 上可重复调用，可选路线按各自范围验收。依赖第二台 Mac、机械臂或实拍素材的现场验收标为待验证，本阶段跳过。改名后复查仓库地址与客户端注册。 [验收状态](verification.zh-CN.md)
