# 本机验收记录

2026 年 11 月 16 日，Apple Silicon Mac，macOS 27.2.1。常规 Codex 与 Claude Code 使用已登录的账号。离线 Codex 和离线 Claude Code 均用本机 LFM 作为主模型。专项测试加载同一个 stdio MCP。以下为指定样本的实测范围。

| 路线 | 实测输出 |
| --- | --- |
| 默认 LFM Fast／Vision | 抽取四个有确定答案的字段样本，检查空字段、25,527 token 检索和并发。视觉样本读出了 `17`。图片越界被拒绝。两个用户级注册均切换到本项目；Codex 与本地 Claude Code 用新入口提取出 Avery、June 17 及空预算。 |
| Claude Code 云端会话 | 登录后的 Claude Code 通过用户级 MCP 调用 `local_specialists.plan_deployment`，选到 `barcodes`，并通过 `local-lfm.extract_fields` 提取 `Rowan`、`June 18` 和 `room: null`。 |
| Apple 系统 `fm` CLI | 条款流程完成后，用 `fm respond --model system` 从合成文本返回 `BASALT-814`。离线 Codex 通过 shell 调用同一设备模型并返回 `JASPER-681`。 |
| 安装及注册迁移 | 在绝对路径含空格的新副本，用已有权重装好 core 与 LFM 默认档位，通过 SHA-256 校验，调用原有回环服务返回 Rowan、May 24 和空房间。新副本的两项 Claude Code 注册都显示 Connected。另用隔离配置复现旧路径，预检报错且未新增其他项。Codex 用只读覆盖参数复测旧路径、错误参数和禁用项，三种都被识别。本机原工作树的四项注册通过 `bin/register --check`。 |
| LFM 服务清单复用 | 用隔离目录复现默认工作树覆盖已有服务清单。修正后，共享目录中通过 SHA-256 的 Reason 权重和 Vision 投影文件保留，同大小损坏权重从清单排除。用当前真实共享目录复验，工作树即使没有权重也能识别全部六个型号。已有回环接口通过默认档验收，流式 `/v1/chat/completions` 返回 `COPPER-514` 和 `[DONE]`。 |
| LFM Tools 和 24B Q8 | 8B、24B 各两次选中正确库存工具并回填，最后一轮设置 `tool_choice="none"`，两组精确库存值均为 `37`、`419`。24B Q8 也通过复核，并驱动两个本地客户端读取文件和作答。 |
| 离线 Codex 专项 MCP | 通过 `bin/lfm codex --with-specialists` 实际读取二维码 `LOCAL-SPECIALISTS-QR-731`，Apple Foundation Models 提取 `Remi` 和 `October 31`，PaddleOCR 读出第 2 页表格中的 `11:40`。离线 Codex 和 Claude Code 的 Lean 检查均返回 `accepted` 和 `statement_checked` 为 `true`。Codex 隔离测试允许指定回环端口并拒绝另一端口，拒绝在状态目录外写入。 |
| 离线 Codex 生成文件与长结果 | 系统朗读与 Kokoro 分别生成 22.05 kHz 和 24 kHz WAV。另一场离线 Codex 会话用 Sound Analysis 在系统朗读 WAV 中识别出 `speech`。Depth Anything 输出 1500 × 1800 PNG。Vision 与 Paddle 的扫描结果都在 500 字符预算下产生 `result_id`，通过 `read_evidence` 读回 `ORBIT-741` 和 `11:40`。MiniCPM 在隔离目录内完成 PDF 页面转换并读出同一编号和时间。预编译的 Core ML 模型返回 `[0, 0, 3]`。系统编译 API 需要会话外的系统临时目录。 |
| 离线 Codex 视频修复 | SwiftVR 保存 320 × 192 MP4。`ffprobe` 确认 9 帧和 1 条音轨。另一进程持有项目运行锁时，离线 Codex 和 `bin/local` 都明确返回运行冲突。沙箱允许写入状态目录，并拒绝经符号链接写入目录外。 |
| Apple VideoToolbox 视频超分 | 离线 Codex 与离线 Claude Code 均把 320 × 192、8 fps 的合成短片放大到 1280 × 768，输出 9 帧、1.125 秒及一条 AAC 音轨。本机 CLI 另从 0.25 秒截取 5 帧，输出 640 × 384、0.625 秒和一条音轨。保留了可变帧率样本的帧时间戳和单帧样本的 0.125 秒时长。1920 × 1080 在该 Mac 返回空倍率列表，带 PQ 标记的输入被明确拒绝。 [Apple 倍率接口](https://developer.apple.com/documentation/videotoolbox/vtlowlatencysuperresolutionscalerconfiguration) |
| 离线 Codex 调用 Omni | `--with-omni --with-specialists` 查询本机索引和已配对的隔离实例，均返回 `Line 1`。取回的 126 字节与对端 SHA-256 一致，另一场离线 Codex 会话从已存文件读到 `B-45132`。关闭对端后返回 `offline`。隔离测试允许连接所选 socket，拒绝另一个 socket 和状态目录外的目标目录。两个实例有独立索引和身份，均在同一台 Mac。 |
| LFM Q4 对照 | Fast Q4 与 Reason Q4 均通过短答。Reason Q4 和 Q8 收到同一份来源后均算出 1 GB 差额，并说明原始数字。 |
| 目标 Mac 的 LFM 复核选型 | 同一 CLI 和 MCP 对显式设定的 16、24、32 GiB 目标分别返回无候选、Reason Q4、Reason Q8。固定权重加常驻 Fast 的下限为 16.76 GiB 和 26.97 GiB。常规 Codex 与离线 Claude Code 均对 24 GiB 的目标调用规划工具，再按返回参数调用 `local-lfm.review` 的 Q4，取得 `4 GB + 9 GB − 12 GB = 1 GB` 的结果。推理在验收用 Mac 上运行。 |
| PDFKit、Vision OCR、条码与 Natural Language | 读取文字层、扫描表格、单元格坐标和同一份文档的分页证据。Codex 与 Claude Code 两端均读取了合成二维码 `LOCAL-SPECIALISTS-QR-731`。 |
| Apple Speech、Translation、Foundation Models | 合成英语转写给出起止时间，英译中保留主要名词，系统模型定位人名及日期。结构化抽取支持空值。中文转写样本有术语误识。 |
| LFM Fast 与 Apple 结构化字段对照 | 五个合成样本各跑三次，按整组字段完全匹配计分。LFM Fast 15/15，常驻服务的 CLI 中位数 0.51 秒。Apple 12/15，CLI 中位数 0.80 秒，三次把「待定」当成交付方式。缩小到另一组缺失字段后，原工具会拒绝模型输出的空字符串。修正后，两客户端都得到 `phone=null`、`last_name=null` 与 `status=approved`。 |
| Apple Foundation Models Python SDK | 用 26.5 Command Line Tools 编译官方 Swift-C 绑定。设备模型通过自定义 Python 回调读取 `beacon_amber` 并生成结构化编号 `762`。Codex 与离线 Claude Code 都从 MCP 取得同一个记录和值。通过 `keys` 限定缺失键时，结果没有返回文件中其他键的值。 |
| Apple Shortcuts 设备模型 | 经系统 CLI、Codex 和本地 Claude Code 实测。分别传入不同文本，取回各自正确的编号。Codex 验收使用一次性的单工具审批设置。有一次简短提示被模型拒绝，带项目上下文的提问成功。 |
| Apple 图像快捷指令与截图目录事件 | 用 ScreenCaptureKit 捕获自有窗口，`shortcuts run`、Codex 和离线 Claude Code 都读出 `NATIVE-482`。目录等待开始后的完成截图通过文件事件触发 Vision，两客户端返回同一行。空等待返回超时。Shortcuts 的 Folder 自动化两次均保存 OCR，系统日志为 `WFFolderTrigger`，首次约 53 秒。两客户端均读出产物中的 `NATIVE-482`，Claude Code 会话通过 `--add-dir` 获得输出目录权限。 |
| Shortcuts 系统 Screenshot 事件 | 从实体键盘截取一个合成窗口。系统日志记录 `WFScreenshotTrigger` 完成且无错误，后台快捷指令写出 `SCREEN-EVENT-571`。同一张系统截图交给 Vision MCP 后，Codex 和离线 Claude Code 均读到 `WINDOW-EVENT-684`。验收后撤销了触发器。 |
| Apple Vision 媒体、Sound Analysis、系统朗读 | 同图特征距离为 0，异图约 1.43。合成录音返回了六个 `speech` 时间窗。Samantha 与 Tingting 分别生成英文和中文 22.05 kHz WAV。Codex 与 Claude Code 均实际调用了这些工具。 |
| Apple Vision 前景分离 | 两猫样本返回两个前景实例和 640 × 480 RGBA PNG，含 188,240 个全透明像素。两个客户端均取得 PNG。 [两猫样图](https://github.com/Blaizzy/mlx-vlm/blob/main/examples/images/cats.jpg) |
| Depth Anything V2 Small | 无需完整 Xcode 的系统 Core ML 编译通过。公开街景输出 2048 × 1362 PNG，近处轿车、公交车、远处塔楼的灰度均值约为 243、69、6。Codex 与 Claude Code 均实际取得产物路径。 [样图来源](https://github.com/DepthAnything/Depth-Anything-V2/blob/main/assets/examples/demo01.jpg) |
| 自备 Core ML 模型 | 本机从 `.mlmodel` 编译 ReLU。Codex 与 Claude Code 输入 `[-2, 0, 3]`，都返回 `[0, 0, 3]`。直接传入 Apple 的深度 `.mlpackage`，读取到图像接口并输出 518 × 392 PNG。 |
| GLiNER2.5 Multi | 英文、中文和混语样本的实体都可按 Unicode 码点回读原文。中文默认空白切词曾把整句误识为人名。启用引擎自带的逐字切词后，双客户端均得到「周岩」与「上海」的正确跨度。 |
| Chronos-2 | 两条合成目标和已知未来协变量，返回六步有序分位数。流量样本 MAE 为 0.359，最近值基线为 8.337。另用短序列核对 Codex 和本地 Claude Code，两个客户端返回相同的两步预测。 |
| TimesFM 3.0 MLX | 接受仅历史协变量和已知未来协变量，给两条序列各返回八步有序分位数。在同一留出集上，TimesFM 和 Chronos 的流量 MAE 为 0.247 和 0.149，用量 MAE 为 0.030 和 0.075。两个客户端对短序列返回相同结果。 |
| Paddle、MiniCPM 与 Jev | Paddle 返回包含 `11:40` 的带坐标表格。MiniCPM 独立读出 `ORBIT-741` 与 `11:40`。Jev 对正确文字候选得分 0.9843，对错配候选得分约 0.0000067。另用另一种数学字体渲染求和式，两客户端对正确候选得分 0.9515，本机对同时改错下限和加号的候选得分约 0.0000354。 |
| Paddle 和 MiniCPM 公式 OCR | 双端样本均取得求和式与积分式。Paddle 给出坐标、独立编号及 `latex` 字段。重复识别时，积分上限有时从 `t` 变为 `\dot{t}`，原始定界符也可能缺一侧。两端 MiniCPM 样本读出了原图的 `t`，并给出成对定界符与公式编号。精确转写时可并行对照。 |
| MOSS、Qwen ASR、ForcedAligner | MOSS 从合成会议区分 `S01` 与 `S02`。Qwen 0.6B 和 1.7B 都完成 10.59 秒录音的逐词转写。两者对时间数字的格式不同。0.6B 另通过离线流式文件测试。ForcedAligner 将 `prism` 定位到 0.56–0.96 秒。两个客户端都跑通对齐和 1.7B 转写。 |
| Qwen3-ASR PCM 流、麦克风和回放 | 按实时时钟送入 10.59 秒素材，输出 5 轮中间文本和含 `11:40` 的终稿。两个客户端回放得到相同的 5 轮和 2 次改写。用 AVFoundation 从内置麦克风采集合成语音、按 1 秒块处理，启动约 1.84 秒后识别到名称，约 2.96 秒后识别到编号 `762`，最终也保留编号。只保留合成标记和计时。 |
| Silero VAD | 在开头加 2 秒、末尾加 3 秒静音的合成会议中返回四段语音，首段从 1.986 秒开始，末段在 12.126 秒结束。3 秒纯静音返回空数组。两个客户端返回了相同区间。 |
| DigUp 0.6.2 和 EmbeddingGemma 2 Q8 | 命中望远镜指南、报告截图、PDF 第 2 页、0–10.59 秒录音和 5–12 秒视频片段。代码小索引用默认阈值未找到无关键词的改写，把阈值调到 1 后命中 `retries.py` 第 1–3 行。两客户端均拿到了录音和代码定位。 |
| 按目录选择现有索引 | 四个合成目录分别有 DigUp 文档索引、Omni 索引、DigUp 代码索引或无索引。CLI 按目录区分就绪状态，代码索引只在代码检索中标为就绪。离线 Codex 和离线 Claude Code 各执行一次 `plan_deployment` → `search`，前者使用 DigUp，后者使用 Omni，均命中各自目录里的望远镜指南。 |
| Jina Code Embeddings 0.5B | 五个显式指定的 Python 文件无需建索引。用「出错后指数增加等待时间」的英文改写命中 `retries.py` 第 1–3 行，与 DigUp 的位置一致。首选相似度约 0.654，次选约 0.062。两个客户端都命中。 |
| Qwen3-VL-Reranker-2B | 把包含 `ORBIT-741` 和 `11:40` 的扫描页从第二个候选排到第一，BF16 正确页得分 0.777，次选 0.245。Codex 与 Claude Code 均返回第 2 页和原始索引 1。另用猫图、条码图和无关文字验证。4-bit 在两组测试中首选相同，扫描页得分 0.307。 |
| Clef-Flash 4-bit | Codex 和 Claude Code 对英文字例选中账务，识别到报告重复付款的分数为 0.9812。中文物流样本选中配送，重复付款分数为 0.008。另对图片选中机械臂。把问题顺序反转后，英文字例选项一致，账务分数从 0.9690 变为 0.9891。 |
| Omni 0.20.5 和 Jina v5 Omni Small | 七个合成文件通过索引，望远镜指南命中第 1 行，扫描 PDF 命中第 2 页。另命中录音和视频文件，两个短媒体样本的定位值为空。Codex 和本地 Claude Code 都命中指南。Claude 测试仅额外开放 Omni 本机 socket。 |
| Omni 已链接设备 | 同一台 Mac 上的两个 Omni 实例各有独立身份和索引。CLI 通过配对、按名称查询及文件读取，两端文件的 SHA-256 相同。停掉远端实例后返回 `offline`。Codex 与离线 Claude Code 的 MCP 实测均返回远端标记 `B-83751` 和 `Line 1`。另核对了远程路径过滤。局域网发现和两台硬件待验收。 |
| Omni 原件取回 | 同机隔离实例加密配对后，CLI、Codex 和离线 Claude Code 通过 `fetch_linked_mac` 各保存一份文件，SHA-256 与远端一致。两个客户端又从本机副本读到 `B-45132`。越界、无命中、超过 16 MiB 的文件、同名目标和离线对端均被拒绝。实体双机待验收。 |
| SpotlightSearchTool App 索引 | 27.2 SDK 的 `SpotlightSearchTool` 命中独立 App 索引中的标题。对描述性问题，设备模型尝试 `sea` 和 `ocean`，后者命中原笔记 `coastal`，两个客户端得到原文编号 `ALBATROSS-249`。该工具的纯相似度配置在此样本中没有命中。MCP 空命中时省去模型生成的说明。 |
| `CSUserQuery` 语义排序 | 对同一批合成笔记，从索引登记后约 1 秒到约 60 秒，`pastries made with tree nuts` 只在启用语义时召回 `Almond Nutmeg Cookies`，标题正例两模式均命中。`marine mammals` 在两模式均未命中。Codex 和离线 Claude Code 均通过 `mode="semantic"` 得到 `food` 原文。 |
| Apple `NLEmbedding` 句向量试跑 | 英语的杏仁烘焙和海洋哺乳类样本都把无关笔记排在第一。简体中文海豹样本也误排，法语同类样本首选正确，繁体中文句向量不可用。保留 Core Spotlight 语义查询及索引检索方案作为已部署选项。 [Apple 句向量文档](https://developer.apple.com/documentation/naturallanguage/finding-similarities-between-pieces-of-text) |
| Apple 原生图像问答 | Apple Python 绑定用 27.2 SDK 重新构建后，两张只有图形的 PNG 能直接作为图像附件发送。系统模型区分了左上绿色圆形和绿色三角形。Codex 与离线 Claude Code 均通过 MCP 得到 `green triangle`。 |
| Kokoro 82M | 英语 `af_heart` 与普通话 `zf_xiaobei` 分别生成 4.05 秒和 6.35 秒的 24 kHz 单声道 PCM WAV，本机 ASR 回读了预期内容。两个客户端均取得合成音频。 |
| SAM-Audio Small | 5 秒混合样本分出两条 48 kHz WAV，目标轨的 440 Hz 底音幅度为输入的约 2.1%，本机 ASR 从目标轨回读了说话内容。两个客户端都拿到两条音轨。 |
| SAM3 | 运行时默认 tokenizer 在样本中产生了全空检测。改用随权重发布的 tokenizer 后，Codex 和本地 Claude Code 都从两猫样本拿到了两个掩膜，分数为 0.973 和 0.968。街景合成视频输出了 10 帧，主车在 4 个采样点保持同一编号。另试了 8-bit 静图，掩膜面积和分数接近 BF16。 [两猫样图](https://github.com/Blaizzy/mlx-vlm/blob/main/examples/images/cats.jpg) |
| TalkNet | 上游多人样片前 5 秒，MPS 与 CPU 均处理 126 帧并找到四条人脸轨迹。正分轨迹在画面右侧，对应 0–4.96 秒。两个客户端均返回同一轨迹和标注视频。 [上游样片](https://github.com/nawta/TalkNet-ASD-py312/tree/ac6bbdf175d57500e9f9c3fb1bb12779242d2b95/demo) |
| SwiftVR | Codex 和 Claude Code 对 320 × 192、8 fps 短片均输出 9 帧和 1.125 秒音轨。输入与输出解码后的音频相关系数超过 0.9999。另从 0.125 秒开始的 8 帧请求按模型要求裁为 5 帧。压缩样本与参考的 SSIM 从 0.948 降到 0.923，加噪样本从 0.933 降到 0.922。 |
| SeedVR2 3B 8-bit | Codex 和本地 Claude Code 将一张 320 × 192 静图和一段同尺寸短片放大到 640 × 384，视频保留 9 帧、8 fps 和一条音轨。9 帧的 2 倍路径测得 MLX 峰值 52.71 GB，原尺寸路径为 17.07 GB。同一压缩样本的原尺寸 SSIM 从 0.948 降到 0.906。 |
| Lean 4.9 | 重新检查声明，并与独立编译的目标命题核对。有效证明 `addZero` 经 Codex 与 `bin/lfm claude --with-specialists` 实测。对照样本拒绝了 `sorry`、自定义公理和命题不符，包括用候选源码的局部记法把 `False` 改释为 `True`。 |
| Goedel-Prover-V2 8B + Mathlib | Codex 和离线 Claude Code 均生成同一整数平方恒等式的证明，通过独立命题与内核检查，公理依赖为 `propext`。本机 CLI 另通过合取交换及上游实数等式示例，拒绝了目标 `False` 的生成候选。 |
| SmolVLA 录制回放 | 官方 SO100 示例的第 0 帧，两路相机、六维状态和同数据集统计量都能输入。CPU 与 MPS 各产生 50 × 6 动作，前三步两端最大数值差约 0.087。两个客户端实跑并得到有限数值。机械臂现场表现待硬件验收。 [SO100 记录](https://huggingface.co/datasets/lerobot/svla_so100_pickplace) |
| LeRobot 现场运行前检查 | LeRobot 0.7.0、Rustypot 和串口驱动已安装。上游解析器接受本机 SmolVLA 权重、SO-101 模式、两路相机映射及定时参数。Codex 和离线 Claude Code 均检查了六轴模型与合成校准文件，报告指定端口缺失。错误电机 ID 或字段类型会标记为不兼容。 macOS 日志有 OpenCV 与 PyAV 的 AVFoundation 类重复提示，相机实际运行待验收。 |
| Hy-MT2、Privacy Filter | Hy-MT2 按给定术语保留「青铜棱镜」。Privacy Filter 安装时固定 `o200k_base` 词表。离线 Codex 和离线 Claude Code 通过终端命令替换了合成样本中的人名、日期、电邮及电话，保留正文。独立终端也在关闭出站网络的条件下执行成功，缺失或损坏的词表在推理前报错。另一已知样本曾漏掉人名。 |

复跑默认档、LFM 可选权重及已安装的专项样本。

```sh
python3 tests/planner.py
python3 tests/lfm_service.py
.runtime/mcp/bin/python tests/smoke.py --apple --text-models
.runtime/mcp/bin/python tests/smoke.py --expanded
.runtime/mcp/bin/python tests/smoke.py --digup
bin/lfm verify --profile default
bin/lfm verify --profile all
bin/lfm verify_clients
```

本机最新一次整合复跑中，`bin/lfm verify --profile all`、两套离线客户端文件读取、`bin/register --check` 及 `tests/smoke.py --apple --expanded --text-models --digup` 均通过。另单独复跑 MOSS，返回 `S01` 和 `S02`。Omni 的实际工具调用证据见上表。

## 待验证与可选验收

| 路线 | 已有证据 | 状态与后续条件 |
| --- | --- | --- |
| Omni 双机 | 同机的两个隔离实例完成加密配对、查询和原件哈希校验 | 待验证，本阶段跳过。现场需第二台可配对的实体 Mac 和获准共享的测试目录 |
| SmolVLA 现场运行 | 公开 SO100 双相机回放和两端软件预检通过 | 待验证，本阶段跳过。现场需已校准的机械臂及对应相机 |
| 计划中的 X4 实拍片段 | 媒体工具已分别用合成或上游样本验收 | 待验证，本阶段跳过。补测时提供一段获准使用的 X4 素材 |

Apple SpeechDetector 的结果流目前用于报告错误，本机带语音样本返回零观察。对语音区间有输出要求时，目录中可选择已验证的 Silero VAD、Apple Speech 转写或 Sound Analysis。 [SpeechDetector 结果流](https://developer.apple.com/documentation/speech/speechdetector/results)
