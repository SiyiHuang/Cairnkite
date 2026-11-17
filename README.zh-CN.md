# 石鸢（Cairnkite）

[English](README.md)

石鸢（Cairnkite）是一套 macOS 本地 AI 工具箱，让 Codex 和 Claude Code 按任务选择并调用 LFM、Apple 原生 AI 和专项模型。

Cairn 是山路上的石堆路标，对应项目的选型决策树。Kite 取「鸢」的意思，呼应 Agent 按需调度本机工具的灵活性。

```sh
bin/plan
bin/plan scan --profile default
bin/plan extract-fields --profile default --use personal
bin/plan complex-layout --require formula_markup --execution mcp
bin/plan semantic-search --use commercial --json
```

已注册的客户端也可以调用 `local_specialists.plan_deployment`。查看[完整部署决策树和操作说明](docs/deployment.zh-CN.md)、[与 LFM 的整合计划](docs/integration-plan.zh-CN.md)，或将[选型提示词](docs/agents.zh-CN.md)交给 Agent。

## 工作流

| 任务 | MCP 调用 | 结果 |
| --- | --- | --- |
| PDF、截图和扫描件 | `document`，`backend="auto"` | PDFKit 优先读 PDF 文字层。Apple Vision 处理图片页，返回文字、边界框和检出的表格。 |
| 复杂布局、公式和表格 | `document`，`backend="paddle"` | PaddleOCR-VL 1.6 先检测版面，再由 MLX-VLM 识别各区域。结果包含 Markdown、版面分类和边界框。 |
| 第二路 OCR、疑难区域复核 | `document`（`backend="minicpm"`）、`score_ocr` | MiniCPM-OCR 输出整页文本，Jev 对原始裁图、候选和渲染图给出一致性分数。 |
| 条码和二维码 | `document`，`backend="barcodes"` | Apple Vision 返回编码值、类型和坐标。 |
| 通用录音转写 | `transcribe`，`backend="apple"` | Apple Speech 返回文字和时间区间。用 `locale` 指定已安装的语言资源。 |
| 只定位语音和静音 | `transcribe`，`backend="silero"` | 小型 ONNX 模型在 CPU 上返回语音区间，不需要语种资源。 |
| 多人录音 | `transcribe`，`backend="moss"` | MOSS MLX 返回文字、时间区间和匿名说话人编号。 |
| 从录音分离声音 | `separate_audio` | SAM Audio 按描述返回目标和残余 WAV。 |
| 词级时间与校订稿对齐 | `transcribe`（`backend="qwen"` 或 `"qwen-large"`）、`align_audio` | Qwen3-ASR 0.6B、1.7B 与 ForcedAligner 返回词或语言单元及时间。 |
| 实时音频与流式回放 | `bin/stream-asr`、`transcribe`（`backend="qwen-stream"`） | 本机 PCM 管道逐块输出暂定文本。MCP 可回放已有录音，返回中间结果和终稿。 |
| 声音事件和朗读 | `classify_sound`、`synthesize_speech` | Apple Sound Analysis 返回分类与时间。系统音色和可选的 Kokoro 生成本机 WAV。 |
| 按含义找资料或代码 | `search`，`backend="digup"` 或 `"omni"` | 查询事先建立的本机索引。DigUp 可提供 PDF 页码、媒体时间或代码行号。 |
| 对少量源文件直接搜索 | `search_code` | Jina 0.5B 按代码行为排序，返回文件和行号。 |
| 按文件名找资料 | `search`，`backend="spotlight"` | 从 Spotlight 的文件元数据索引返回路径。结果受系统索引覆盖范围限制。 |
| 本机翻译 | `translate`，`backend="apple"` 或 `"hy-mt"` | Apple 使用已安装的语言资源。Hy-MT2 可接受术语提示。 |
| 语言、词性与实体 | `text_analysis` | Apple Natural Language 返回语言猜测、词性、内置实体和 UTF-16 位置。 |
| 文本提取和短摘要 | `focus_text` | Apple Foundation Models 根据短文本答问。需要启用 Apple Intelligence。 |
| 有固定字段的短文本 | `extract_apple_fields` | Apple Foundation Models 通过 Swift 动态 schema 返回原文字符串和缺失字段。 |
| Apple 设备模型调用 Python | `lookup_apple_record`、`bin/apple-fm-python` | 从指定 JSON 查原值，也可在 Python 脚本里编写原生设备模型的自有回调。 |
| Apple 原生图像问答和 App 索引 | `inspect_apple_attachment`、`search_apple_notes` | macOS 27 的系统模型接收图像。笔记由 SpotlightSearchTool 问答，或经 Core Spotlight 语义排序返回原文。 |
| 新截图自动 OCR | `wait_for_screenshot`、`bin/local watch-screenshots` | 监视获准目录，新的完整图像文件通过 Vision 识别。也可配置 [Shortcuts Folder 自动化](docs/deployment.zh-CN.md#shortcuts-folder) 自动保存文本。 |
| 多段文本的自定义实体 | `extract_entities` | GLiNER 返回实体与 Unicode 码点位置。 |
| 图片类别、相似度和相对深度 | `inspect_apple_image`、`estimate_depth` | Apple Vision 返回类别或距离，Core ML 生成本机深度 PNG。 |
| 自备 Core ML 模型 | `predict_coreml` | 查看输入输出结构，传入图像或短张量运行预测。 |
| Apple 文本与图像快捷指令 | `run_apple_shortcut` | 给已配置的快捷指令传文本或图像，返回其纯文本结果。 |
| 候选页与图片精排 | `rerank_visual` | 针对当前查询，重排 PDF 页、图片和文字候选。 |
| 视频修复与放大 | `restore_video`、`restore_image` | SwiftVR 修复原尺寸视频，SeedVR2 可放大静图和短片，Apple VideoToolbox 可放大支持尺寸的 SDR 短片。 |
| 固定选项与分档打分 | `decide` | Clef-Flash 在一次推理中对多个二元判断、选项与分档打分。 |
| 静态图片原生抠图 | `extract_apple_foreground` | Apple Vision 返回实例数和透明 PNG。 |
| 对象掩膜和视频关联 | `segment_objects` | SAM3 按对象名称生成图片掩膜，也可给短视频配框和编号。 |
| 判断视频里谁在说话 | `active_video_speakers` | TalkNet 输出人脸编号、源时间、像素框和标注 AVI。 |
| 核验形式化证明 | `check_lean_proof` | Lean 4.9 检查编译、指定命题类型和公理依赖。 |
| 生成形式化证明 | `generate_lean_proof` | Goedel 提议证明，由 Lean 独立核对命题及公理。 |
| 回放机械臂观测 | `preview_robot_actions` | SmolVLA 从已记录的图像、关节状态和指令生成动作预览。 |
| 机械臂现场运行前检查 | `check_smolvla_rollout` | 枚举串口，检查 LeRobot、模型及校准文件。 |
| 时序预测 | `forecast_series` | 默认 Chronos-2，可选 TimesFM 3.0。输出三档分位数和最近观测基线。 |
| 配对设备检索和取回原件 | `search_linked_mac`、`fetch_linked_mac` | 可选 Omni。查询一台已配置的 Mac，并将获准的命中复制到本机目录。 |
| 常用短文本与截图问答 | `local-lfm` 的 `extract_fields`、`summarize`、`inspect_image` | LFM Fast 常驻，LFM Vision 按需加载。 |

PDF 页码从 1 开始。图像使用第 1 页。文档边界框以左上角为原点，使用归一化 `[x0, y0, x1, y1]`。SAM3 和 TalkNet 使用像素框。时间单位为秒，起点为原文件开头。MOSS 的说话人编号仅在单份录音中有效。

## 安装

需要 Apple Silicon、macOS 26 或更新版本、带 macOS 26.4 或更新 SDK 的 Xcode 或 Command Line Tools，以及 `uv`。默认安装包括 Apple 原生工具、LFM Fast 和 LFM Vision，三个 GGUF 文件合计约 7.31 GB。请预留至少 20 GB 磁盘空间供依赖、下载和后台服务使用。服务使用 `127.0.0.1:8080`。Apple Intelligence、Speech 和 Translation 依赖各自的系统设置与语言资源。

1. 准备工具链。尚未安装 Command Line Tools 时，先运行 `xcode-select --install`，完成系统安装窗口后继续。用以下命令核对环境。

   ```sh
   uname -m
   sw_vers -productVersion
   xcrun --sdk macosx --show-sdk-version
   uv --version
   ```

   `uname -m` 应为 `arm64`，SDK 应为 26.4 或更新。尚未安装 `uv` 时，按官方说明安装并重新打开终端。 [uv 安装](https://docs.astral.sh/uv/getting-started/installation/)

2. 克隆项目并进入目录。在固定位置保存仓库，客户端将从此路径启动 MCP。

   ```sh
   git clone https://github.com/SiyiHuang/cairnkite-release.git Cairnkite
   cd Cairnkite
   ```

3. 检查端口并安装默认方案。

   ```sh
   lsof -nP -iTCP:8080 -sTCP:LISTEN
   bin/install default en-US zh-CN
   bin/lfm status
   ```

   首条命令在端口空闲时返回空结果。如果已有服务，请确认其用途后再继续。已有本项目 LFM 服务时，安装会核对同名 LaunchAgent 并复用符合锁定 SHA-256 的权重。安装可重跑，中断的模型下载会续传。Fast 常驻，Vision 在调用时加载。首次启动需等待服务就绪，期间可重新运行 `bin/lfm status`。正常模型列表至少包含 `lfm-fast` 和 `lfm-vision`。

   只安装 Apple 原生工具可运行 `bin/install core`。额外 Speech 语言使用 `bin/install speech ja-JP`。已有 LFM 下载可按 [LFM 部署和迁移说明](backends/lfm/README.zh-CN.md) 使用 `--reuse-from`。

4. 运行默认验收。样本来自仓库的合成材料。

   ```sh
   python3 tests/planner.py
   .runtime/mcp/bin/python tests/codex_specialists.py
   .runtime/mcp/bin/python tests/smoke.py
   bin/lfm verify --profile default
   ```

   原生测试应打印 `Smoke test passed.`。LFM 验收覆盖字段抽取、缺失值、摘要、并发、长文本和图像问答，成功时退出码为 0，并生成本机 `backends/lfm/logs/verification.json`。Apple Intelligence 和语言资源就绪后，可再运行 `.runtime/mcp/bin/python tests/smoke.py --apple`。

## 接入 Codex 和 Claude Code

先安装需要使用的客户端，使 `codex --version` 或 `claude --version` 能在同一个终端执行。Codex 使用 `codex login` 登录，Claude Code 使用 `claude auth login` 登录。云端主模型的调用需要相应账号权限。 [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) · [Claude Code 安装](https://code.claude.com/docs/en/quickstart)

两套客户端都已安装时，在项目根目录运行以下命令。

```sh
bin/register
bin/register --check
codex mcp get local_specialists --json
codex mcp get local-lfm --json
claude mcp get local_specialists
claude mcp get local-lfm
```

只接入一个客户端时，使用 `bin/register codex` 或 `bin/register claude`，并运行对应的 `bin/register --check codex` 或 `bin/register --check claude`。检查应确认两个服务都指向当前仓库的 `bin/serve` 和 `bin/lfm serve`。Claude Code 的检查还应显示已连接。Codex 专用工具超时为 360 秒，Claude Code 使用用户级 MCP 配置。发生旧路径冲突时，按[客户端迁移步骤](docs/deployment.zh-CN.md#client-registration)处理。

分别启动新的 `codex` 和 `claude` 会话。若客户端要求信任仓库或批准工具，请核对当前路径后按其提示操作。在两个会话中分别粘贴以下合成验收任务。

> 请实际调用 local_specialists 的 status，随后调用 plan_deployment，参数为 feature="barcodes"、execution="mcp"、verified_only=true。再调用 local-lfm 的 extract_fields，原文为 "The telescope calibration is scheduled for July 21. Dana is the owner. The room is undecided."，字段为 owner（负责人姓名）、date（计划日期）、room（已确定的房间）。请报告工具结果。

选型结果应为 `barcodes`，字段结果应为 `{"owner":"Dana","date":"July 21","room":null}`。检查客户端的工具调用记录，确认两项 MCP 都有成功返回。

再在项目根目录准备图像验收样本。

```sh
cp tests/fixtures/observatory.png backends/lfm/inbox/observatory.png
```

在两个客户端分别发送以下任务。

> 请调用 local-lfm 的 inspect_image，filename="observatory.png"，question="What is the code for the left bench? Return only that code."。请报告工具返回的编号。

预期图片中左侧实验台的编号为 `ORBIT-741`。这一步使用 LFM Vision。验收后可移走 `backends/lfm/inbox/observatory.png`。可用工具和合成验收的实测范围见[验收记录](docs/verification.zh-CN.md)。

## 按需安装

`bin/plan` 和 MCP 的 `plan_deployment` 返回任务对应的候选、许可、安装命令和验收方式。选择后再运行相应安装命令。

```sh
bin/install paddle
bin/install moss
bin/install qwen
bin/install digup
bin/install omni
```

完整选项见[部署说明](docs/deployment.zh-CN.md)。`bin/install all` 安装组合 `core`、`paddle`、`moss` 和 `omni`。离线隐私检测提供 `bin/redact` 本机入口。

使用 DigUp 时，为指定目录运行 `bin/local index-digup <目录>`，代码索引加 `--code`。使用 Omni 时，先运行 `bin/install omni`，启动 Omni 并为获准目录建索引。下例将默认验收准备的合成目录加入 Omni。

```sh
"$HOME/Applications/Omni.app/Contents/Helpers/omni" add_source "$HOME/LocalSpecialists/demo"
```

## 调用示例

将待处理的材料放入 `~/LocalSpecialists`，然后在客户端指定绝对路径和任务。例如：

> 用 `local_specialists` 的 `document` 读取我指定的 PDF 第 2 页。先用 `auto` 提取，表格列关系不清楚时用 `paddle` 复跑。回答时标明来源页码，并保留两个结果有分歧的字段。

> 用 `transcribe` 的 `moss` 后端转写我指定的录音。总结两位发言人各自的主张，每条附原话和时间区间。

> 用 `search` 在我指定的 Omni 索引目录中查资料。先列最相关的 3 条和定位信息，再检查支撑结论的片段。

`document` 每次处理 1 页。`transcribe` 接收不超过 30 分钟的单个音频文件。MOSS 和 Qwen 长音频可能触及生成上限。检查 `may_be_truncated` 和最后时间码，按需切分原文件。分段后，各段的说话人编号需重新核对。

如果结果超过 `max_chars`，服务返回预览和 `result_id`。用 `read_evidence` 按 `next_offset` 继续读完整 JSON。完整结果存放在 `.runtime/results`。

## 文件和网络范围

文件工具默认只接受 `~/LocalSpecialists` 内的输入。用户可创建 `.runtime/config.json`，将 `allowed_roots` 设为允许的绝对目录数组。服务解析符号链接，再核对目标路径。Omni 和 DigUp 都需要为选定目录建立索引。

```json
{
  "allowed_roots": ["~/LocalSpecialists", "/absolute/path/to/another/approved-folder"]
}
```

MCP 使用 stdio。Paddle 的页内识别子进程只监听临时回环端口，任务结束后退出。Omni 使用本机 Unix socket，搜索限定本机。安装需要联网取依赖和权重。使用云端会话时，客户端服务方可能收到工具参数和返回的证据。需要全程在本机处理时，可用 `bin/local <工具名>`、上游本机命令，或以 LFM 驱动的离线客户端。 [离线客户端调用专项工具](docs/deployment.zh-CN.md#offline-specialists)

Omni 代码采用 Apache 2.0，Jina 权重采用 CC BY-NC 4.0。仓库只分发部署代码、依赖清单与合成样本。权重来源、许可和版本见 [依赖记录](dependencies/README.zh-CN.md)。

## 验证和故障处理

1. 运行决策树及原生验收。

   ```sh
   python3 tests/planner.py
   .runtime/mcp/bin/python tests/codex_specialists.py
   .runtime/mcp/bin/python tests/smoke.py
   bin/lfm verify --profile default
   ```

2. 安装 Apple Speech 资源。使用 Omni 的额外验收时，等待其合成目录完成索引。

   Apple Intelligence 已就绪并安装相应语言资源时，可运行 `.runtime/mcp/bin/python tests/smoke.py --apple`，实测英语转写、英译中与 Apple Foundation Models。
3. 运行已安装模型的对应验收。

   ```sh
   .runtime/mcp/bin/python tests/smoke.py --full
   .runtime/mcp/bin/python tests/smoke.py --expanded
   .runtime/mcp/bin/python tests/smoke.py --text-models
   .runtime/mcp/bin/python tests/smoke.py --digup
   ```

   已验证的样本、客户端与当前缺口见[本机验收记录](docs/verification.zh-CN.md)。

- 客户端找不到 MCP 时，先在当前仓库运行 `bin/register --check`。如果是迁移留下的旧路径，用对应客户端的 `mcp get` 记录启动参数与自定义设置，再只处理报告冲突的条目，运行 `bin/register` 后复查。详细步骤见[客户端迁移](docs/deployment.zh-CN.md#client-registration)。
- `status` 报告 `appleIntelligenceNotEnabled` 时，`focus_text` 无法生成。Vision、Speech 和 Translation 使用独立的系统框架。
- Apple Speech 缺少语言资源时，运行 `bin/install speech <locale>`。如需处理原始语言不确定的多人录音，可试用 MOSS。
- Omni 无结果时，用 `omni list_sources` 检查目录和索引数量。macOS 访问限制可能阻止 Omni 读取「文稿」中的目录。可将待索引材料放入 `~/LocalSpecialists`。
- Spotlight 无结果时，用 `mdls` 检查文件是否已进入系统元数据索引。Omni 使用独立索引。
- Paddle 或 MOSS 调用失败时，检查错误提示中的本机日志路径。复杂页和长录音耗时更长。

## 解除客户端注册

```sh
codex mcp remove local_specialists
claude mcp remove local_specialists --scope user
codex mcp remove local-lfm
claude mcp remove local-lfm --scope user
```

如需卸载本项目管理的 LFM 服务，参见 [LFM 维护](backends/lfm/README.zh-CN.md#维护)。

## 许可

项目代码及本仓库原创合成样本采用 MIT 许可证。下载的模型、第三方组件与 Apple 系统服务分别适用上游条款。 [MIT 许可证](LICENSE) · [依赖和模型许可](dependencies/README.zh-CN.md)
