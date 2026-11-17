# 选型与部署

在仓库根目录运行 `bin/plan` 查看决策树。选择与所需输出最相近的分支，然后添加硬性要求。安装前可用 Python 3.10 或更新版本运行选型工具。仓库内置的推理后端需要 Apple Silicon 和 macOS 26 或更新版本。

| 任务 | 先确定输出 | 选择示例 |
| --- | --- | --- |
| 文档 | 原文、区域坐标、表格结构、独立 OCR 或候选分数 | `bin/plan complex-layout --require formula_markup` |
| 音频 | 段时间、说话人、词时间、校订稿对齐、流式输入或独立音轨 | `bin/plan speaker-transcript --execution mcp` |
| 检索 | 文件名、语义匹配、代码、跨 Mac 或图文精排 | `bin/plan semantic-search --use commercial` |
| 文本 | 翻译、固定术语、字段、隐私标记或分流 | `bin/plan glossary-translation --execution local` |
| 图像和视频 | 活跃说话人、对象掩膜、修复、相对深度或原生动作 | `bin/plan restore-video --require upscale_video` |
| 其他任务 | 数值预测、Lean 证明或机械臂动作 | `bin/plan forecast --use production` |

`--execution mcp` 要求已接入仓库的 MCP。`--execution local` 要求有文档记录的本机命令。`--verified-only` 要求路线和指定能力均已实测。输出仍列出被排除的候选和原因。

`--profile default` 查看默认路线。`--profile optional` 可查询专项选项。`plan_deployment` 用同名 `profile` 参数。可把档位与输出约束组合，例如 `bin/plan scan --profile optional --require table_structure`。

准备另一台 Mac 时，用 `--machine arm64 --macos 27.2 --disk-gib 100 --memory-gib 24` 设置目标。MCP 的 `plan_deployment` 接受同一组 `target` 字段 `machine`、`macos`、`disk_gib` 和 `memory_gib`。显式指定目标时，本机的已安装状态不会参与排序。

LFM 的权重大小来自固定版本的文件清单，默认部署还计入常驻 Fast 和适用的视觉组件。规划 `focused-review` 时，24 GiB 的目标会选 Q4，16 GiB 的目标在当前标准配置下没有候选，32 GiB 的目标可选 Q8。权重大小仅是内存下限，实际运行还需给上下文、进程和 macOS 留空间。

给本机已有资料选语义或代码索引时，运行 `bin/plan semantic-search --use personal --folder "$HOME/LocalSpecialists/demo"`，或给 `plan_deployment` 传获准目录的绝对 `folder`。选型会优先使用该目录已就绪的索引，并把 `folder` 放进返回的 `search` 参数。DigUp 的文档索引与代码索引各自检查。Omni 仅在 App 已运行且报告该目录有完成的非空索引时标为就绪。检查只读取索引状态，目录内容变化后按相应配方刷新。 [DigUp CLI](https://github.com/ARahim3/DigUp) · [Omni CLI](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

| 标记 | 含义 |
| --- | --- |
| `verified` | 项目在本机用样例验收过指定输出。以各候选的验收范围为准。 |
| `integrated` | 本仓库已有调用入口，仍有材料、系统资源或功能验收条件待满足。 |
| `upstream` | 上游提供路线。按对应章节固定版本、试跑和记录结果。 |
| `installed` | 本机文件或已知系统资源已就绪。实际路径与输入仍须验收。 |
| `needs_setup` | 还需下载系统资产、准备索引或确认软件配置。 |
| `trial_required` | 适合进入上游试跑。 |

在任务内，选型工具优先建议符合条件且本机已就绪的路线，再按决策树顺序建议候选。结果的 `question` 表示许可或硬件信息会影响下一步。商业或生产场景会过滤已知受限权重和待核对条款。`permissive` 表示该路线没有记录上述限制，系统框架仍适用 Apple 软件条款。需要数据严格留在本机时，使用 `bin/local` 或上游本机命令，在本机审阅输出。

## 准备内置后端

```sh
bin/install default
bin/register
bin/register --check
.runtime/mcp/bin/python tests/smoke.py
```

`bin/install default` 需要 `uv`、Swift 6 及 macOS 26.4 或更新的 SDK。Xcode 或 Command Line Tools 都可提供编译环境。跟在 `default` 之后的地区码会安装相应的 Apple Speech 语言资源。只用 CLI 时可以跳过客户端注册。专用工具的参数 JSON 可以通过标准输入传给 `bin/local <工具>`。LFM 工具使用 `bin/lfm local <工具>`。文件存放在 `~/LocalSpecialists` 或配置中明确选定的目录。示例使用测试脚本准备的合成材料。

<a id="client-registration"></a>
### 仓库迁移后的客户端注册

在新仓库路径运行 `bin/register --check`。它会检查两个客户端为已安装后端配置的启动命令和参数。无参数的 `bin/register` 会在新增条目之前检查所有现存同名条目。发生冲突时，先用 `codex mcp get <名称> --json` 或 `claude mcp get <名称>` 看清现有路径、参数和作用域，再保留需要的自定义超时、环境和权限配置。 [Codex MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP 作用域](https://code.claude.com/docs/en/mcp#mcp-installation-scopes)

如果确认条目属于旧工作树，可直接在原配置作用域改启动路径。也可用 `codex mcp remove <名称>` 或 `claude mcp remove <名称> --scope <实际作用域>` 移除该条目，再从新路径运行 `bin/register`，补回需要的自定义设置。新会话里分别试一次 `local_specialists.status` 和 `local-lfm.extract_fields`，确认选中的服务器和现场结果。 [Codex MCP CLI](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP CLI](https://code.claude.com/docs/en/mcp)

## Liquid AI LFM

默认档位安装 Fast 和 Vision。llama.cpp 通过 Metal 使用 Apple Silicon，监听 `127.0.0.1:8080`。`bin/lfm status` 查看模型，`bin/lfm verify --profile default` 验收默认档位。`bin/register` 在 LFM 环境已建立时也注册 `local-lfm`。 [运行时和命令](../backends/lfm/README.md) · [LFM Open License](https://www.liquid.ai/lfm-license)

<a id="lfm-fast"></a>
### LFM Fast 摘要与字段

`bin/install default` 或 `bin/install lfm-fast`。两客户端调用 `local-lfm.extract_fields` 或 `local-lfm.summarize`。本机命令接收同一工具的 JSON 参数。

```sh
printf '%s\n' '{"text":"Marina inspected the prism.","fields":{"owner":"Name of the person who inspected it"}}' | bin/lfm local extract_fields
```

核对 `owner` 为 `Marina`。缺失字段、中文改期和原文中带有指令分别用 `bin/lfm verify --profile default` 的合成样本验收。

<a id="lfm-vision"></a>
### LFM Vision 静态图像问答

`bin/install default` 或 `bin/install lfm-vision`。把 PNG 或 JPEG 主动暂存到 LFM MCP 所用的 `inbox/`。两客户端调用 `local-lfm.inspect_image`，参数是文件名和问题。验收脚本从含有系统状态数字的合成截图读值，同时检查目录越界拒绝。OCR、表格和原图定位可用 Apple Vision 文档工具。

<a id="lfm-tools"></a>
### LFM Tools 函数调用

`bin/install lfm-tools`。在任一客户端的 shell 工具里，把 `messages` 和 `tools` 的 JSON 请求通过 stdin 传给 `bin/lfm chat lfm-tools`。从 `choices[].message.tool_calls` 取名称和参数，由执行器验证并调用，再将结果回填。工具调用结束后，明确让模型根据结果作答，并传 `tool_choice="none"`。`bin/lfm verify --profile all` 用有干扰选项的库存工具验证选择、参数和收尾。

<a id="lfm-reason"></a>
### LFM Reason 复核与本地 Agent

`bin/install lfm-reason`。两个常用客户端可把文本和复核问题交给 `local-lfm.review`。完全本机的客户端试跑用 `bin/lfm codex` 和 `bin/lfm claude`，验证用 `bin/lfm verify_clients`。复核样本包含相加后的资源超出量。工具调用以隔离客户端日志和正确结果为准。

<a id="offline-specialists"></a>
#### 离线 Codex 和 Claude Code 调用专项工具

先运行 `bin/install core`。需要 Lean、PaddleOCR 等可选后端时，按各自章节安装。`--with-specialists` 放在 `codex` 或 `claude` 后面，给当前会话加载 `local_specialists`。

```sh
bin/lfm codex --with-specialists
bin/lfm claude --with-specialists
```

例如，让任一客户端用 `local_specialists.document` 的 `barcodes` 后端读取 `~/LocalSpecialists` 下的二维码。也可以让 Codex 把本次会话的 MCP 限于一个工具。

```sh
bin/lfm codex --with-specialists exec --strict-config --ephemeral \
  -c 'mcp_servers.local_specialists.enabled_tools=["extract_apple_fields"]' \
  '用 extract_apple_fields 从「Remi booked the lab for October 31」提取人名和日期。'
```

Codex 通过临时回环端口连接现有 LFM 服务。Lean 和 PaddleOCR 通过会话专用的 Unix socket 委派给各自的工作进程。离线 Codex 将工具产物写到 `backends/lfm/.state/codex-local/specialists/artifacts/`。下一个工具可以直接使用返回的文件路径。例如，用 `synthesize_speech` 生成 WAV，再让 `classify_sound` 读取该 WAV。结果截断时用 `read_evidence` 和返回的 `result_id` 继续读。MLX-Gen 的常规视频修复在同一项目内共用运行锁。 [Codex MCP 配置](https://learn.chatgpt.com/docs/config-file/config-reference)

自备 Core ML 模型在离线 Codex 中使用已编译且位于获准目录内的 `.mlmodelc`。Apple 的编译 API 需要写系统临时目录，可在离线会话外运行 `native/.build/release/apple-specialists compile-coreml <源模型绝对路径> <目标.mlmodelc绝对路径>`，再把编译产物交给 `predict_coreml`。需要写到其他目录的任务可以直接用 `bin/local`。

<a id="lfm-quantization"></a>
### LFM Q4 对照

安装 `lfm-fast-q4` 或 `lfm-reason-q4`，把相同的 JSON 请求通过 stdin 交给 `bin/lfm chat <模型 ID>`。Reason Q4 也可用标准 MCP `local-lfm.review` 或 `bin/lfm local review`，参数是 `text`、`question` 和 `model="lfm-reason-q4"`。省略 `model` 会用原来的 Reason Q8。对照同一输入集的正确率、首轮加载延迟、热运行耗时和内存，再决定是否选 Q4。

## 文档

<a id="pdfkit"></a>
### Apple PDFKit

安装 `core`。调用 `document`，指定 PDF 和 `backend="auto"`。用带文字层的第一页核对型号、编号和页码。返回 `pdfkit` 表明取到了文字层。对图片页，`auto` 会转到 Vision。 [PDFPage 文档](https://developer.apple.com/documentation/pdfkit/pdfpage/string)

<a id="vision"></a>
### Apple Vision OCR 与 Document Recognition

安装 `core`。调用 `document`，用 `backend="vision"` 强制逐页 OCR。用合成 PDF 第 2 页检查 `ORBIT-741`、表格及归一化坐标。用实际样页检查多栏顺序和单元格。 [Vision 文档识别](https://developer.apple.com/documentation/vision/recognizedocumentsrequest)

<a id="paddle"></a>
### PaddleOCR-VL 1.6 与 PP-DocLayoutV3

运行 `bin/install paddle`。调用 `document`，用 `backend="paddle"` 处理需要版面的单页。检查 `blocks` 的类别、框和文本。公式块的 `latex` 提供去掉外层数学定界符的表达式，`text` 保留原始输出，公式编号是单独的块。合成样例有时会漏掉一侧定界符，渲染时可使用 `latex` 自行加定界符。离线客户端以 `--with-specialists` 启动，由本机 Unix socket 委派给 Paddle 工作进程。用 `tests/fixtures/formula-page.png` 核对求和上下限、分母、积分根号和坐标。 [Paddle Apple Silicon 安装文档](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-Apple-Silicon.html)

<a id="minicpm"></a>
### MiniCPM-OCR 1.0

运行 `bin/install minicpm`。用 `document` 的 `backend="minicpm"` 对同一页生成第二套文字。用合成扫描页核对 `ORBIT-741`、`FILTER-193` 和表格时间。公式页可以同时核对表达式和编号。工具返回整页文本和生成上限标记。需要区块坐标时选 Vision 或 Paddle。 [OpenBMB 模型卡](https://huggingface.co/openbmb/MiniCPM-OCR-1.0)

<a id="jev"></a>
### MiniCPM-OCR Jev

运行 `bin/install jev`。将原始裁图、候选文本及该文本的渲染图一并送给 `score_ocr`，对应 `original_path`、`text`、`rendered_path`。用上游的文字、公式、表格样例验证评分，再用自己标注的同类样本比较正确与错误候选。项目使用上游文字错误样例完成推理。批量筛选前按字体和渲染方式校准，仓库未设阈值。 [OpenBMB 输入与验收说明](https://github.com/OpenBMB/MiniCPM-OCR/blob/main/docs/minicpm_ocr_jev_tutorial_en.md)

<a id="barcodes"></a>
### Apple Vision 条码检测

安装 `core`。用 `document` 的 `backend="barcodes"` 读取已知二维码或普通条码。核对 `codes[].payload` 和 `bbox`。编码值按输入数据处理。 [Vision 条码接口](https://developer.apple.com/documentation/vision/detectbarcodesrequest)

## 音频

<a id="apple-speech"></a>
### Apple SpeechTranscriber

运行 `bin/install speech en-US` 或 `bin/install speech zh-CN`。用 `status` 确认所需地区码的 `speech_asset` 为 `installed`。用 `transcribe` 的 `backend="apple"` 检查合成录音的 `copper prism`、分段和时间。也可用识别段近似定位有人发言的区间。 [SpeechTranscriber](https://developer.apple.com/documentation/speech/speechtranscriber)

<a id="moss"></a>
### MOSS-Transcribe-Diarize

运行 `bin/install moss`。用 `transcribe` 的 `backend="moss"` 检查两人合成样本返回 `S01` 和 `S02`。在真实长录音上检查 `may_be_truncated`、发言结束时间和重叠发言，同一人的编号跨文件可能变化。 [MLX 适配](https://github.com/vanch007/mlx-MOSS-Transcribe-Diarize)

<a id="qwen-asr"></a>
### Qwen3-ASR 0.6B 与词级时间

运行 `bin/install qwen`，同时安装 0.6B 识别器和对齐器。用 `transcribe` 的 `backend="qwen"` 处理合成录音。检查 `text`、`segment_unit` 和对应时间。对齐可能会归一化数字或标点。

首次可用 16 kHz WAV。其他格式需 `ffmpeg`。需要匿名说话人时，试用 [MOSS](#moss)。 [MLX 转写与时间戳说明](https://github.com/moona3k/mlx-qwen3-asr#word-level-timestamps)

<a id="qwen-large"></a>
### Qwen3-ASR 1.7B 与词级时间

运行 `bin/install qwen-large`。用 `transcribe` 的 `backend="qwen-large"` 处理同一段音频。它和 0.6B 共用对齐器。1.7B 权重更大，可用同一批术语、口音样本比较转写和耗时。 [1.7B 8-bit 权重](https://huggingface.co/moona3k/mlx-qwen3-asr-1.7b-8bit)

<a id="qwen-align"></a>
### Qwen3-ForcedAligner 0.6B

运行 `bin/install qwen-align`。调用 `align_audio`，用 `path` 和 `text` 提供原音与校订稿，`language` 填 `English` 或上游支持的语言。单次音频最多 120 秒。试听词起止位置，再拼接较长字幕。此路使用已知文本，对不上时先检查语言和录音是否对应。 [Qwen 官方对齐器](https://github.com/QwenLM/Qwen3-ASR)

<a id="speech-detector"></a>
### Apple SpeechDetector

目前 Apple 用此模块在转写中降低功耗。用 `bin/plan speech-detector-probe` 查看接口诊断。`transcribe` 的 `backend="activity"` 保留了原生探针，带语音样本中未返回区间。Apple 文档说明结果流当前只会报告错误。需要时间范围时用 Silero VAD、Apple 转写或 Sound Analysis。 [SpeechDetector 结果流](https://developer.apple.com/documentation/speech/speechdetector/results)

<a id="silero-vad"></a>
### Silero VAD

准备 `ffmpeg`，运行 `bin/install silero` 和 `bin/register`。Codex、Claude Code 或 `bin/local transcribe` 使用 `backend="silero"` 和音频绝对路径 `path`。模型以 16 kHz 单声道处理首条音轨，最长 30 分钟，返回有声区间的秒数。当前参数针对一般语音，短于 250 毫秒的语音不会返回。需要说话人、正文或逐词时间时选用转写路线。 [Silero 序列 ONNX 发布](https://github.com/snakers4/silero-vad/releases/tag/v6.2.2)

<a id="qwen-stream"></a>
### Qwen3-ASR 流式 CLI

运行 `bin/install qwen`。`bin/stream-asr` 从 stdin 读 16 kHz 单声道、16 位小端 PCM，每轮输出一行 NDJSON。`text` 是当前整段文本，`stable_text` 是稳定前缀。更新显示时以新一轮 `text` 替换旧版本。输入结束后返回 `final` 和改写计数。可用下列命令按实时时钟重放合成录音。

```sh
ffmpeg -hide_banner -loglevel error -re -i tests/fixtures/meeting.wav \
  -ac 1 -ar 16000 -f s16le - | bin/stream-asr --language English
```

Codex 和 Claude Code 可用 `transcribe` 的 `backend="qwen-stream"` 回放获准目录中最长 30 分钟的文件，并在结束后一次取得 `partials`、`metrics` 和终稿。要逐条接收实时转写，用本机 PCM 管道。以下命令通过 AVFoundation 从指定麦克风采集，结束后给出终稿。先在 macOS 授权发起采集的应用，设备名按本机实际名称填写。

```sh
ffmpeg -nostdin -hide_banner -f avfoundation -i ':MacBook Pro Microphone' \
  -t 5 -vn -ac 1 -ar 16000 -f s16le - | bin/stream-asr --chunk-seconds 1 --language English
```

本机用自带麦克风听到扬声器播放的合成句。首条部分结果认出目标名称，第二条已包含编号，终稿也包含编号。 [流式接口](https://github.com/moona3k/mlx-qwen3-asr#streaming)

<a id="sam-audio"></a>
### SAM Audio small

运行 `bin/install sam-audio` 安装固定的 MLX 权重和 T5 编码器。两个客户端及 `bin/local separate_audio` 接收获准的本机音频路径和 `description`，例如 `"human speech and spoken conversation"`。单段最多 30 秒，输出两条 48 kHz WAV。用已知两个声源的样本核对目标轨、残余轨、串音和失真。 [MLX 模型卡](https://huggingface.co/mlx-community/sam-audio-small) · [Meta 权重与条款](https://huggingface.co/facebook/sam-audio-small)

<a id="kokoro"></a>
### Kokoro 82M

运行 `bin/install kokoro` 安装固定的 MLX 权重、语言前端和两款音色。两个客户端调用 `synthesize_speech` 时设 `backend="kokoro"`，英语用 `voice="af_heart"`，普通话用 `voice="zf_xiaobei"`。默认语速系数为 1，对应参数 `words_per_minute=175`，其他值按比例调整。先检查 WAV 的音色标识、24 kHz 采样率及内容，长稿和混语另做样例。 [Kokoro MLX 指南](https://github.com/Neywa-Labs/mlx-audio/blob/main/docs/models/tts/kokoro.md) · [原模型与许可证](https://huggingface.co/hexgrad/Kokoro-82M)

<a id="apple-tts"></a>
### macOS 系统语音合成

运行 `bin/install core` 和 `bin/register`。Codex 与 Claude Code 调用 `local_specialists.synthesize_speech`，终端可把同一 JSON 参数交给 `bin/local synthesize_speech`。例如 `{"text":"周岩在上海复核仪器。","voice":"Tingting"}`。用 `say -v '?'` 查看系统音色，调整 `words_per_minute` 控制速度。结果给出本机 22.05 kHz WAV 路径和时长，保存在 `.runtime/artifacts/`。 [Apple 系统音色](https://support.apple.com/guide/mac-help/mchlp2290/mac)

<a id="sound-analysis"></a>
### Apple Sound Analysis

运行 `bin/install core` 和 `bin/register`。Codex 与 Claude Code 调用 `local_specialists.classify_sound`，终端可把同一 JSON 参数交给 `bin/local classify_sound`。传入 `path`，按需调整 `threshold` 与每窗分类数 `limit`。工具返回分类、置信度和可能重叠的时间窗。合成录音已验出 `speech`。用自己的背景声样本校准分类阈值。 [Apple 文件分类流程](https://developer.apple.com/documentation/soundanalysis/classifying-sounds-in-an-audio-file)

## 检索

<a id="omni"></a>
### Omni 与 Jina v5 Omni Small

运行 `bin/install omni` 下载并校验 App 和固定的 Small 权重。通过 Omni CLI 的 `add_source` 加入指定目录，用 `list_sources` 查看进度。用 `search` 的 `backend="omni"` 搜索望远镜校准，核对结果指向合成指南。实测返回文本行和 PDF 页，短音视频返回文件路径。需要媒体时间码时可用 DigUp。权重按 CC BY-NC 4.0 使用。普通 Agent 会话由 MCP 连接 Omni 的本机 Unix socket。 [Omni 使用与索引](https://github.com/hanxiao/omni-macos)

离线会话先启动 Omni，再运行下列命令之一。`--with-omni` 开放所选 Omni Unix socket。默认使用 Omni 的标准 socket，隔离实例可用 `LFM_OMNI_SOCKET` 指定一个绝对路径。

```sh
bin/lfm codex --with-omni --with-specialists
bin/lfm claude --with-omni --with-specialists
```

<a id="digup"></a>
### DigUp 与 EmbeddingGemma 2

运行 `bin/install digup` 安装签名命令行组件及校验过的 EmbeddingGemma 2 权重。无需启动 App。建索引时只传获准目录，建议先用项目合成样本。

```sh
.runtime/mcp/bin/python tests/smoke.py
bin/local index-digup "$HOME/LocalSpecialists/demo"
jq -nc --arg folder "$HOME/LocalSpecialists/demo" \
  '{folder:$folder,backend:"digup",query:"ORBIT-741 11:40"}' | bin/local search
.runtime/mcp/bin/python tests/smoke.py --digup
```

结果应指向 `calibration.pdf` 第 2 页。Codex 和 Claude Code 使用同样的 `search` 参数。要查代码，运行 `bin/local index-digup --code <目录>`，并在查询中传 `code=true`。目录内容变化后重跑相应建索引命令。默认语义阈值为 2 个标准差。小型索引的改写查询若返回空候选，可用 `min_semantic_z=1` 再查并逐项核对。 [DigUp 安装与使用](https://github.com/ARahim3/DigUp) · [Google 模型卡](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)

<a id="omni-pairing"></a>
### Omni 跨 Mac

两台 Mac 分别安装 Omni、准备各自愿意共享的索引目录。在应用的「File」菜单选「Link a Mac」，在设备间比对配对码，并按需要启用搜索与文件读取。先用合成文件验证所属设备、关闭其中一端时的返回和共享范围。

将下面的 `omni_linked_macs` 字段并入 `.runtime/config.json`。使用唯一的已配对名称或 ID，并填写对方 Mac 的绝对目录。调用 `search_linked_mac` 会将查询发给指定设备，项目按这些路径筛选返回结果。对端搜索的原始索引范围由对端 Omni 的共享设置决定。

```json
{"omni_linked_macs":{"Studio":["/Users/me/LocalSpecialists/shared"]}}
```

```sh
printf '%s\n' '{"peer":"Studio","query":"Violet Sextant"}' | bin/local search_linked_mac
```

Codex 和 Claude Code 可传入相同参数。离线会话按上面的 Omni 启动方式开放本机 socket，查询由 Omni 转给所选的已配对设备。本机版本已通过两个隔离应用实例的配对、查询和文件读取。局域网发现与跨两台硬件的行为待验收。 [Omni CLI](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

<a id="omni-linked-copy"></a>
### 取回已配对 Mac 的原件

在上一步配置两台 Mac，并在文件所在设备上允许读取文件。`search_linked_mac` 返回获准命中及其大小。对要保留的命中调用 `fetch_linked_mac`，传入同一个 `peer`、`query` 和命中的完整 `path`。省略 `output_folder` 会在工具产物目录中为此副本创建单独的子目录，适用于离线 Codex。手动指定时应选客户端可写、已存在且位于本机允许范围内的目录。终端可把同一 JSON 交给 `bin/local fetch_linked_mac`，两客户端可调用同名 MCP 工具。 [Omni 文件取回](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

工具重查该命中与对方的文件读取许可。索引报告的文件大小至多 16 MiB，并且必须与 Omni 缓存中读到的实际字节数一致。目录中的同名文件会保留。工具返回本机 `path`、原始 `remote_path`、字节数及 `sha256`，可把本机路径交给后续工具读取。Omni 同时保留自己的拉取缓存。用独立数据目录启动 Omni 时，可在 `.runtime/config.json` 的 `omni_link_cache_root` 填写该实例的缓存绝对路径。实体双机验收待完成。 [Omni 本机缓存实现](https://github.com/hanxiao/omni-macos/blob/v0.20.5/App/Link/RemoteFiles.swift)

<a id="spotlight"></a>
### Spotlight 文件名搜索

安装 `core`，在系统已索引的目录放一个唯一文件名。可用 `mdls` 核对索引，再比较 `mdfind -onlyin "$PWD" -name <文件名>` 和 MCP 的 `search(backend="spotlight")`。本项目测试目录无命中时，用 `rg --files` 定位路径。 [Apple Spotlight 指南](https://support.apple.com/guide/mac-help/search-with-spotlight-mchlp1008/mac)

<a id="core-spotlight"></a>
### SpotlightSearchTool 自有 App 索引

用 macOS 27 和 27 SDK 运行 `bin/install apple-spotlight`，启用 Apple Intelligence。此安装编译一个有独立身份的本机辅助 App。用 `search_apple_notes` 或 `bin/local search_apple_notes` 查询获准目录内的 JSON，传 `path` 和 `question`。JSON 是含 `id`、`title`、`text` 的短笔记数组，最多 24 条、32 KiB。

每次查询把这组笔记登记到辅助 App 的索引，返回 `matches` 中的原文，完成后移除当次索引。默认 `mode="answer"` 由设备模型用 `SpotlightSearchTool` 搜索，描述性问题会尝试改写成短关键词。合成海边步道的样本用 `ocean` 命中。查看 `matches` 核对模型回答，空命中时以空结果为准。 [Apple 自然语言查询示例](https://developer.apple.com/documentation/corespotlight/searching-indexed-content-with-natural-language)

<a id="core-spotlight-semantic"></a>
### Core Spotlight 语义检索

用相同的 `bin/install apple-spotlight` 安装辅助 App，在 `search_apple_notes` 或 `bin/local search_apple_notes` 中传 `mode="semantic"`。`question` 传要搜索的短语。`CSUserQuery` 启用系统词面和语义排序，返回最多五条 `matches` 原文，`text` 为 `null`。新批次首次未命中时最多再查两次，让索引完成更新。此模式直接调用 Core Spotlight，不启动 Foundation Models 会话。 [Apple Core Spotlight 搜索接口](https://developer.apple.com/documentation/corespotlight/building-a-search-interface-for-your-app)

可用 `tests/fixtures/spotlight-notes.json` 或 `tests/smoke.py --apple` 复跑。`pastries made with tree nuts` 在本机找到了标题为 `Almond Nutmeg Cookies` 的笔记，同一个查询关闭语义时返回空。`marine mammals` 没有召回海豹笔记。碰到漏召回时可试 `mode="answer"`，让设备模型改写关键词。 [Apple Core Spotlight 语义开关](https://developer.apple.com/documentation/corespotlight/csuserquerycontext/disablesemanticsearch)

<a id="jina-grep"></a>
### Jina Code Embeddings 与 jina-grep

运行 `bin/install jina-grep`。在 Codex 或 Claude Code 调用 `search_code`，传入行为描述 `query` 和已圈定的 UTF-8 源文件绝对路径数组 `files`。同一请求可交给 `bin/local search_code`。上限为 64 个文件、合计 128 KiB，返回片段、行号和相似度。整仓重复搜索可先建立 DigUp 索引；已知符号可使用 `rg` 或语言服务器。0.5B 权重限非商业使用。 [Jina 的语义代码检索](https://github.com/jina-ai/jina-grep-cli#code-search) · [0.5B MLX 权重](https://huggingface.co/jinaai/jina-code-embeddings-0.5b-mlx)

<a id="qwen-reranker"></a>
### Qwen3-VL-Reranker-2B

运行 `bin/install qwen-reranker`，然后将 `query` 和最多 12 个 `candidates` 交给 `rerank_visual`。PDF 候选使用 `path` 和 `page`，图像使用 `path`，候选也可带 `text`。输出按相关性排序，并保留候选的 `input_index`。本机命令为 `bin/local rerank_visual`。 [官方模型和评分方法](https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B)

先用 Omni、DigUp 或关键词召回候选，再用同一查询比较精排前后正确页的排名。MLX 路线使用官方模板及 yes/no logits 的差值计算相关性分数。图像长边限制为 1,344 像素，细小字的区域可以先单独截取。

空间有限时运行 `bin/install qwen-reranker-4bit`，调用时设置 `precision="4bit"`。权重约 1.78 GB，BF16 约 4.26 GB。两个样本中的首选相同，4-bit 分数较低。根据自己的材料重新设分数阈值。 [MLX 4-bit 权重](https://huggingface.co/mlx-community/Qwen3-VL-Reranker-2B-4bit)

## 文本

<a id="apple-translation"></a>
### Apple Translation

安装 `core`。在「系统设置 → 通用 → 语言与地区 → 翻译语言」下载目标两种语言。用 `native/.build/release/apple-specialists translation-status en zh-Hans` 确认 `asset` 为 `installed`。调用 `translate`，用 `texts` 给一组短文本，`source_language="en"`，`target_language="zh-Hans"`。验收输出条数及含义。本机用英译简中验证。 [Apple 离线翻译设置](https://support.apple.com/guide/mac-help/mchldd8b3c15/mac) · [TranslationSession](https://developer.apple.com/documentation/translation/translationsession)

<a id="hy-mt"></a>
### Hy-MT2

运行 `bin/install hy-mt`。调用 `translate` 的 `backend="hy-mt"`，需要术语时传入 `glossary`，键是原文词，值是预期译法。核对译文数量、`truncated` 和术语命中。批量输出按输入顺序返回。长文或字幕切成小批，保留原 ID、时间轴和术语检查。7B 可按官方说明单独部署并与 1.8B 用同一语料对比。 [腾讯模型卡与术语示例](https://huggingface.co/tencent/Hy-MT2-1.8B#hy-mt2-translation-task-instruction-examples-chinese-english-comparison)

<a id="natural-language"></a>
### Apple Natural Language

安装 `core`，调用 `text_analysis`。使用含地名、人名和 emoji 的文本，检查语种、词性和内置实体，按 UTF-16 单元回查位置。语言或实体标签可用性因文本和系统而异。 [Natural Language](https://developer.apple.com/documentation/naturallanguage)

<a id="foundation-models"></a>
### Apple Foundation Models 短文本问答

安装 `core`，在兼容设备启用 Apple Intelligence 并等待资源可用。用 `status` 检查 `foundation_models` 为 `available`。调用 `focus_text`，给出有已知事实的短文本和定位问题，逐条查原句。macOS 27.2.1 的 Swift 路线已用合成样本答出负责人和日期。 [Apple Foundation Models](https://developer.apple.com/documentation/foundationmodels)

<a id="foundation-structured"></a>
### Apple Foundation Models 结构化生成

运行 `bin/install core`，用 `status` 确认 `foundation_models` 为 `available`。Codex 和 Claude Code 可调用 `local_specialists.extract_apple_fields`，参数和本机 CLI 相同。Swift 动态 schema 约束字段，模型省略或留空的字段为 `null`。工具核对每个非空值与原文连续字符串一致。需要「已确认」的值时仍应核对上下文，测试发现 Apple 会把「待定」当作交付方式填回。LFM Fast 在本项目样本上更稳定，保留为默认。 [Apple Swift Guided Generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation)

```sh
printf '%s\n' '{"text":"Marina owns the inspection. The budget is pending.","fields":{"owner":"Name of the person responsible","budget":"Confirmed budget amount"}}' | bin/local extract_apple_fields
```

验收 `owner` 为 `Marina`、`budget` 为 `null`。系统的 `fm` CLI 和 Apple Python SDK 也提供结构化路径。 [Apple CLI 与 SDK](https://developer.apple.com/videos/play/wwdc2026/334/) · [Apple Python SDK](https://github.com/apple/python-apple-fm-sdk)

本节的结构化抽取使用 Swift。macOS 27 的系统 `fm` 完成机器级条款流程后，也可用终端或 Agent 的 shell 调用设备模型。用 `fm respond --model system --no-stream --greedy 'Return only the code BASALT-814.'` 检查本机调用。使用 Python 回调时可选下节的本地绑定。 [Apple CLI 与 SDK](https://developer.apple.com/videos/play/wwdc2026/334/)

<a id="apple-fm-python"></a>
### Apple Foundation Models Python 工具回调

运行 `bin/install apple-fm-python`，启用 Apple Intelligence。项目固定官方 0.2.2 源包，使用当前 SDK 直接编译 Swift-C 绑定，生成 Python 接口。此安装用本机 26.5 和 27.2 Command Line Tools 验收。官方 `pip` 构建流程要求完整 Xcode。

用 `bin/apple-fm-python your_script.py` 运行 `import apple_fm_sdk` 的脚本。实际调用可以使用 SDK 的 `LanguageModelSession`、自定义 `Tool` 和 `@generable`。为两个 Agent 提供的 `lookup_apple_record` 可让系统模型在配置目录的 JSON 对象中选键，再由 Python 返回对应的原值。JSON 文件最多 32 KiB，最多 32 个键。已知可以返回哪些记录时，传 `keys` 限定范围。`lookups` 给出实际调用的键、命中状态和原值，`text` 是模型给出的说明。

```sh
bin/plan apple-record-lookup --execution mcp --verified-only --json
printf '%s\n' '{"path":"/Users/me/LocalSpecialists/calibration.json","question":"Use read_record to get the service code for beacon_amber."}' |
  bin/local lookup_apple_record
```

用 `{"beacon_amber":{"service_code":762},"beacon_blue":{"service_code":481}}` 作为验收内容。核对 `lookups` 中只有所需键的真实值，再对照模型的说明。Codex 和 Claude Code 通过已注册的 MCP 传入相同参数。 [Apple Python SDK](https://github.com/apple/python-apple-fm-sdk) · [Apple 图像输入 API](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting)

<a id="apple-fm-image"></a>
### Apple Foundation Models 原生图像问答

在 macOS 27 上用 `xcrun --sdk macosx --show-sdk-version` 确认已启用 27 SDK，运行 `bin/install apple-fm-python`。检查 `status.apple_fm_attachments`，然后向 `inspect_apple_attachment` 传获准目录内的图像 `path` 和 `question`。这条路线把图像作为 `ImageAttachment` 直接交给本机系统模型。用两张只有图形而无文字的图片核对颜色及位置。需要精确文字和坐标时用 `document` 的 `backend="vision"`。 [Apple 原生图像输入](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting)

<a id="gliner"></a>
### GLiNER2.5 multi-v1

运行 `bin/install core`、`bin/install gliner` 和 `bin/register`。Codex 与 Claude Code 调用 `local_specialists.extract_entities`，终端可把同一 JSON 参数交给 `bin/local extract_entities`。例如 `{"texts":["周岩在上海复核仪器。"],"labels":{"person":"人名","city":"城市名"}}`。一批最多八段。返回置信度和 Unicode 码点半开区间，按 `[start:end]` 回读原句。在带标注的同类材料上检查阈值、跨度和漏检。 [Fastino 模型卡](https://huggingface.co/fastino/gliner2.5-multi-v1)

<a id="privacy-filter"></a>
### OpenAI Privacy Filter

运行 `bin/install privacy`。安装器同时准备模型权重和校验过的 `o200k_base` 词表。终端、离线 Codex 与离线 Claude Code 均可用 `bin/redact < input.txt > redacted.txt` 在本机 CPU 处理文件。命令先校验本地词表，离线会话沿用客户端的网络隔离。离线 Codex 的输出路径应位于它自己的状态目录。一个合成样本替换了人名、日期、电邮和电话，另一个样本漏掉人名。检查剩余敏感信息后，再决定哪些内容可以出机。需要跨度与类别时，可在本机设置 `TIKTOKEN_CACHE_DIR` 为项目的 `.runtime/models/privacy/tiktoken`，再以 `opf redact --checkpoint .runtime/models/privacy/original --device cpu --format json` 调用上游入口。 [OpenAI OPF 安装和命令](https://github.com/openai/privacy-filter#how-to-use) · [词表与校验值](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py)

<a id="clef"></a>
### Cloudflare Clef-Flash

运行 `bin/install clef` 和 `bin/register`。Codex、Claude Code 或 `bin/local decide` 接收 `state`、`questions` 与可选 `image_path`。每题给出 `instructions`。二元题用 `type="binary"`，返回命题为真、为假的分数。选项题用 `type="choice"` 与候选名到描述的映射。分档题用 `type="score"` 与从低到高的描述列表，返回每档分数及从 0 起算的期望分档。

固定问题顺序及候选定义，用带标注的样本比较误分率，并在留出集上确定复核阈值。发布方建议 16 GB 或更多内存。 [Clef 原模型](https://huggingface.co/Cloudflare/clef-flash) · [MLX 4-bit 权重与运行代码](https://huggingface.co/mlx-community/clef-flash-4bit)

## 图像与视频

<a id="talknet"></a>
### TalkNet-ASD

准备 `ffmpeg`，运行 `bin/install talknet`。在 Codex、Claude Code 或 `bin/local active_video_speakers` 传入 `path`、开始秒数 `start` 和片段秒数 `duration`。可选 `device="mps"` 或 `"cpu"`。结果包含活跃轨迹、源视频时间、像素框和带音轨的标注 AVI。360° 素材先转成常规视角。画外说话、遮挡和音画偏移需要对照片段复核。代码为 MIT，TalkSet 和 S3FD 的预训练权重许可未明确。 [Mac 适配及权重来源](https://github.com/nawta/TalkNet-ASD-py312) · [原项目](https://github.com/TaoRuijie/TalkNet-ASD)

<a id="sam3"></a>
### Segment Anything 3

运行 `bin/install sam3` 安装固定的 BF16 权重和随权重发布的 tokenizer。两个客户端和 `bin/local segment_objects` 使用 `path` 和简短对象名，例如 `prompt="a cat"`。`task="segment"` 返回各对象的 PNG 掩膜和像素框。`task="track"` 处理最长 30 秒的 1080p 像素量以内视频，返回标注画面的 MP4 和按采样时刻列出的框及编号。时间由帧号和标称帧率换算。编号按框重叠关联，遮挡及切镜需复核。 [MLX 模型卡](https://huggingface.co/mlx-community/sam3-bf16) · [Meta 源码与许可](https://github.com/facebookresearch/sam3)

<a id="apple-video-upscale"></a>
### Apple VideoToolbox 视频超分

在 macOS 26 或更新版本运行 `bin/install core`，并准备 `ffmpeg` 与 `ffprobe`。先以输入的像素宽高查询系统支持的倍率，例如 `native/.build/release/apple-specialists video-scale-status 320 192`。倍率由设备和输入尺寸决定。本机的 320 × 192 支持 2 倍和 4 倍，1920 × 1080 返回空列表。 [Apple 支持倍率接口](https://developer.apple.com/documentation/videotoolbox/vtlowlatencysuperresolutionscalerconfiguration)

在 Codex、Claude Code 或 `bin/local restore_video` 中传入 `path`、`backend="apple"` 和 `scale="2x"` 或 `"4x"`。入口处理 SDR 短片。可用 `start_seconds` 和 `max_frames` 指定片段，返回实际首帧时间、宽高、帧数、帧率和音轨数。输出为 H.264 MP4，有音轨时将相应片段编码为 AAC。`bin/plan upscale-video-4x` 返回 4 倍调用参数和尺寸检查提示。 [Apple 视频处理示例](https://developer.apple.com/documentation/videotoolbox/enhancing-your-app-with-machine-learning-based-video-effects)

<a id="swiftvr"></a>
### SwiftVR

准备 `ffmpeg` 与 `ffprobe`，运行 `bin/install swiftvr` 和 `bin/register`。给 Codex、Claude Code 或 `bin/local restore_video` 传入 `path`、可选 `start_seconds`、`max_frames` 和 `seed`。工具处理不超过 1080p 像素量的短片段，返回原分辨率 MP4、帧数、帧率和音轨数。SwiftVR 按 `4n + 1` 帧处理，可能裁掉尾部。更高分辨率或长视频可以按上游命令直接测试。 [SwiftVR 参数与实测](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md#swiftvr-one-step-restoration)

先用有参考的短片比较运动、局部细节、帧数和音轨。项目的两个退化样本经 SwiftVR 后，与参考相比的 SSIM 均下降。当前固定权重适用 SwiftVR Research License。选型时用 `bin/plan restore-video --use research`。 [固定权重许可](https://huggingface.co/H-oliday/SwiftVR/blob/a0b09461bd89847712dd91dbb4c63541b4693936/LICENSE)

<a id="seedvr2"></a>
### SeedVR2

运行 `bin/install seedvr2` 和 `bin/register`。静图用 `restore_image`，传入 `path` 和 `scale="2x"`。视频需 `ffmpeg` 与 `ffprobe`，使用 `restore_video`、`backend="seedvr2"`。先用 `scale="1x"` 检查帧数、画面和音轨。终端可把同一参数交给 `bin/local restore_image` 或 `bin/local restore_video`。

视频只有在显式传入 `scale="2x"` 和 `allow_high_memory=true` 时才启用上游的放大模式。项目的 320 × 192、9 帧样本测得约 52.7 GB MLX 峰值。先从短片试跑，并比较同一参考下的细节重建。 [MLX-Gen 运行参数](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md) · [固定权重](https://huggingface.co/AbstractFramework/seedvr2-3b-8bit/tree/6e6b162d1e96c873ad93645508bbc4636814c0c7)

<a id="apple-foreground"></a>
### Apple Vision 前景分离

运行 `bin/install core`。给 `extract_apple_foreground` 传入图片的绝对路径 `path`，从结果取 `instances` 和 `foreground_png`。两端 MCP 与 `bin/local extract_apple_foreground` 共用同一接口。先检查导出尺寸和 alpha 通道，再检查实际样本的轮廓。需按文字指定对象时使用 SAM3。 [Apple Vision 实例遮罩](https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest)

<a id="vision-media"></a>
### Apple Vision 媒体预处理

运行 `bin/install core` 和 `bin/register`。Codex 与 Claude Code 调用 `local_specialists.inspect_apple_image`，终端可把同一 JSON 参数交给 `bin/local inspect_apple_image`。传入 `path` 可看类别和外观分，提供 `comparison` 返回两张图的特征距离，数值越小越相似。用同图和异图核对距离，再用业务素材找适用阈值。可先抽取视频帧，再调用同一入口。抠图、光流和姿态有各自的 Vision API。 [Apple Vision 请求目录](https://developer.apple.com/documentation/vision) · [Apple 缩略图示例](https://developer.apple.com/documentation/Vision/generating-thumbnails-from-videos)

<a id="depth-anything"></a>
### Depth Anything V2 Small Core ML

运行 `bin/install depth-anything` 和 `bin/register`。安装器校验 Apple 的 FP16 `.mlpackage`，使用系统 Core ML 编译。Codex 与 Claude Code 调用 `local_specialists.estimate_depth`，终端可把同一 JSON 参数交给 `bin/local estimate_depth`。传入图片 `path`，`compute` 可选 `all`、`cpu`、`cpu-gpu`。结果为与解码后输入图对齐的本地相对深度 PNG，最长边至多 4000 像素。先用轮廓明确的前景和远景核对深度顺序。物理距离需要额外标定。 [Apple Core ML 模型卡与 Swift 集成](https://huggingface.co/apple/coreml-depth-anything-v2-small)

<a id="core-ml"></a>
### Apple Core ML

运行 `bin/install core` 与 `bin/register`。将自备的 `.mlmodel`、`.mlpackage` 或 `.mlmodelc` 放到允许读取的目录。Codex 与 Claude Code 调用 `predict_coreml`，终端可用 `bin/local predict_coreml`。只给 `model` 路径可以查看输入名、类型和形状。预测时通过 `inputs` 按名称传入 `image` 路径、`number`、`integer`、`text` 或 `values`，张量可附 `shape`。图像结果保存为模型原始输出尺寸的 PNG，张量返回形状、总长度和前 1,024 个值。序列与模型状态需在专门适配中处理。

`compute` 可选 `all`、`cpu` 或 `cpu-gpu`。实际算子调度可用 Xcode 模型报告或 Instruments 核对。许可按具体模型判断。 [Apple Core ML 开发文档](https://developer.apple.com/documentation/coreml)

<a id="shortcuts"></a>
### Apple Shortcuts

运行 `bin/install core` 和 `bin/register`。在快捷指令 App 创建单独的文本快捷指令。添加 **Use Model**，选择 **On-Device**，用 **Shortcut Input** 作为提示。再添加 **Stop and Output**，选择上一动作的 **Response**。用 `shortcuts list --show-identifiers` 查找 UUID，并把它填入本项目 `.runtime/config.json` 的 `allowed_shortcut_ids` 数组。已配置的 ID 可从 `status` 获得。 [Apple 设备模型动作](https://support.apple.com/guide/shortcuts-mac/use-apple-intelligence-in-shortcuts-mchl91750563/mac)

用合成文本直接验证 `shortcuts run "<UUID>" -i input.txt --output-type public.plain-text`。Codex 与 Claude Code 调用 `run_apple_shortcut`，传入 `shortcut_id`、`text`，或者在终端把同一 JSON 交给 `bin/local run_apple_shortcut`。Codex 的调用按其工具审批配置执行。只把准备交给 agent 运行的快捷指令 ID 加入数组。快捷指令自身决定是否访问系统应用、网络或用户资料。 [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac) · [Codex 配置参考](https://developers.openai.com/codex/config-reference)

图像工作流添加 **Extract Text from Image**，选 **Shortcut Input** 为图像，再通过 **Stop and Output** 返回 **Extracted Text**。登记其单独的 UUID，用 `run_apple_shortcut` 的 `path` 传获准目录内的图像。每次传 `path` 或 `text` 其中一项。本机用真实的合成 App 窗口截图跑通了命令行和两客户端。 [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)

<a id="screenshot-folder"></a>
### 指定目录收到截图后自动 OCR

运行 `bin/install core`。用 `bin/local watch-screenshots "$HOME/LocalSpecialists/screenshots"` 持续等待新文件并输出 NDJSON。也可在任一客户端调用 `wait_for_screenshot`，用 `folder` 指定获准目录，并指定 1–45 秒的 `wait_seconds`。MCP 返回新增文件的 Vision OCR 与坐标，空等待返回 `timed_out`。

先将截图写完，再移动到监视目录的最终文件名，使用 PNG、JPEG 或 HEIC。监视范围是该目录的直接文件。验收时由 `SCShareableContent.currentProcess` 捕获测试应用自己的窗口，移入目录后两客户端都读到了 `NATIVE-482`。 [Apple ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit)

<a id="shortcuts-folder"></a>
### Shortcuts Folder 自动化

在 Shortcuts 的 **Automation** 中新建 **Folder** 触发器，选一个专门收截图的目录，开启 **Added Files** 和 **Ignore Subfolders**，选择 **Run Immediately**。用 **Extract Text from Image** 接收 **Shortcut Input**，把 **Extracted Text** 交给 **Save File**，保存到另外一个目录。Codex 和 Claude Code 可读获准输出目录里的文本。本地 Claude Code 可以用 `bin/lfm claude --with-specialists --add-dir <输出目录>` 给当前会话加入这个目录。随时调用已登记的图像快捷指令也可走 `run_apple_shortcut`。

用两张新的测试截图确认输出。本机测试的两次触发都成功，第一次从触发到文本写出约 53 秒。项目的目录监视工具可直接返回文字和坐标，且可经 MCP 调用。 [Apple Shortcuts 自动化](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac)

<a id="shortcuts-screenshot"></a>
### 系统 Screenshot 触发

在快捷指令编辑器搜索 **Screenshot**，添加 **When a screenshot is saved** 触发器，再选择 **Files**。添加 **Text** 和 **Save File**，用固定测试标记确认触发。按 `Shift⌘4` 后按空格，选取合成测试窗口并保存文件。本机验收中，系统日志记录了 `WFScreenshotTrigger`，后台工作流写出了 `SCREEN-EVENT-571`。将这张截图移入获准目录后，可由 Codex 或 Claude Code 调用 `document(backend="vision")` 读取；两端都读到 `WINDOW-EVENT-684`。 [Apple Shortcuts 自动化](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac) · [Apple 截图快捷键](https://support.apple.com/en-au/guide/mac-help/mh26782/27/mac/27)

macOS 27.2.1 的截图触发器提供 Files、Photos 和 Clipboard 三种目的地类别。需要仅监听指定目录并自动产出 OCR 时，使用项目的目录监视工具或 Shortcuts 的 Folder 触发器。

## 专项任务

<a id="timesfm"></a>
### TimesFM 3.0

运行 `bin/install timesfm` 安装 Google 的 MLX 后端和固定权重。Codex、Claude Code 和 `bin/local forecast_series` 均使用 `backend="timesfm"`，沿用 Chronos 的字段与三档分位数。在自己的时间顺序留出集与简单基线对照，分别检查预测误差、区间覆盖和未来协变量是否事先可用。本机权重限非商业、非生产，生产场景可用本项目的 Chronos-2。 [Google TimesFM 源码与许可](https://github.com/google-research/timesfm) · [3.0 模型卡](https://huggingface.co/google/timesfm-3.0-pytorch)

<a id="chronos"></a>
### Chronos-2

运行 `bin/install core`、`bin/install chronos` 和 `bin/register`。Codex 与 Claude Code 调用 `local_specialists.forecast_series`，终端可把同一 JSON 参数交给 `bin/local forecast_series`。例如 `{"targets":{"count":[11,12,12,14,15,16,18,19]},"horizon":2}`。多条目标与历史协变量共用等间隔时间网格。已知未来的每条数值协变量须有同名历史序列，且未来长度等于 `horizon`。预测行依次为 0.1、0.5、0.9 分位数。留出一段已知真值，与最近值或季节性基线比较误差和区间覆盖率。 [Amazon Chronos-2 模型卡](https://huggingface.co/amazon/chronos-2)

<a id="lean-kernel"></a>
### Lean 内核核对已有证明

运行 `bin/install lean`。将 Lean 代码 `source`、定理名 `declaration` 和预期命题类型 `statement` 交给 `check_lean_proof`。终端可将同一组 JSON 参数交给 `bin/local check_lean_proof`。验收重新检查编译声明，并审计指定定理的公理依赖。提供 `statement` 时，独立编译目标命题并核对定理类型。依赖 `sorryAx` 或自定义公理，以及命题不符，均返回 `accepted=false`。项目使用 Lean 4.9.0，需 Mathlib 时运行 `bin/install lean-mathlib` 并传入 `library="mathlib"`。 [Lean 的证明验收说明](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

离线 Codex 与 Claude Code 均可用 `--with-specialists`。当前会话的 MCP 通过临时 Unix socket 连接单独隔离的 Lean 进程，退出后清理 socket。常规注册的 Codex 与 Claude Code 直接使用 `bin/register` 配置的入口。

<a id="goedel"></a>
### Goedel-Prover-V2 与 Lean

运行 `bin/install goedel` 与 `bin/register`。给 Codex、Claude Code 或 `bin/local generate_lean_proof` 提供已形式化的 Lean 命题 `statement`。输出包含候选 Lean 代码和 `verification`，使用前检查 `accepted`、`statement_checked` 和 `axioms`。例如，可用 `∀ p q : Prop, p ∧ q → q ∧ p` 检查标准库路径。

需要 Mathlib 时另运行 `bin/install lean-mathlib` 并传入 `library="mathlib"`。此安装走 Lean 4.9.0 正式版和配套 Mathlib，Goedel 官方 Linux 批处理实验有自己的依赖固定。命题与自然语言原题的对应关系仍需检查。 [Goedel 官方环境与示例](https://github.com/Goedel-LM/Goedel-Prover-V2#5-environment-setup) · [固定 8B GGUF](https://huggingface.co/mradermacher/Goedel-Prover-V2-8B-GGUF/tree/43fab68ec71738a75b0a84738e18b222d2d4e249)

<a id="smolvla"></a>
### SmolVLA 与 LeRobot 离线预览

运行 `bin/install smolvla` 和 `bin/register`。Codex、Claude Code 或 `bin/local preview_robot_actions` 传入 `camera_images`、六维 `state` 和 `instruction`。图片按训练时的相机名映射。公开 SO100 样本使用 `camera1` 对应 `top`，`camera2` 对应 `wrist`。用 `statistics_path` 提供同一数据集的 LeRobot `stats.json` 时，输入状态和输出动作使用该数据集单位。省略时提供已归一化的状态，返回归一化动作。

`device` 可选 `mps` 或 `cpu`。`seed` 可用于重复采样，`steps` 控制取回 50 步动作中的前几步。用与相机帧对齐的状态和对应动作空间核对形状、尺度及偏差。工具读取记录数据并返回预览。 [模型卡](https://huggingface.co/lerobot/smolvla_base) · [SO100 样本集](https://huggingface.co/datasets/lerobot/svla_so100_pickplace)

<a id="smolvla-preflight"></a>
### LeRobot 现场运行前检查

运行 `bin/install core` 和 `bin/install smolvla`，再调用 `bin/local check_smolvla_rollout`。两客户端可用 MCP 的同名工具。省略参数时检查 `lerobot-rollout` 和原生电机驱动，并枚举系统报告的 USB 串口。也可传入 `port`、获准目录下的本机 `policy_path` 和 `calibration_path`，检查匹配的端口、模型文件及 SO-100／SO-101 六轴元数据。 [LeRobot 硬件配置](https://huggingface.co/docs/lerobot/main/en/so100)

`matching_metadata` 表示文件结构匹配。相机映射、真实机械臂校准和任务表现需现场确认。预检只枚举串口及读取文件，`hardware_verified` 保持为 `false`。

<a id="smolvla-rollout"></a>
### LeRobot 现场运行

`bin/install smolvla` 安装固定的 LeRobot 0.7.0、数据集依赖和 Feetech 驱动。现场入口为 `.runtime/smolvla/bin/lerobot-rollout`。使用与机械臂、动作空间、相机布局和任务对应的校准与示教数据，按官方文档传入 `--policy.path`、`--robot.type`、`--robot.port`、`--robot.id` 和 `--robot.cameras`。先对同一配置运行预检，并在回放或仿真核对策略动作。本项目实测了本机 CLI 加载、预检及公开记录回放。实机任务、摄像头和运动质量仍待验收。 [LeRobot SmolVLA 部署](https://huggingface.co/docs/lerobot/main/en/smolvla#evaluate-the-finetuned-model-and-run-it-in-real-time) · [现场 CLI](https://huggingface.co/docs/lerobot/main/en/inference)
