# 依赖记录

[English](README.md)

验证平台为 Apple Silicon、macOS 26.5.2、Xcode SDK 26.5、Python 3.12。Python 环境按功能安装。每个 `.in` 文件列出直接依赖，对应的 `.lock` 文件列出已解析版本。MOSS 以外的 PyPI 归档带哈希。Git 依赖固定到指定提交。

| 组件 | 安装版本或权重提交 | 许可及来源 |
| --- | --- | --- |
| MCP Python SDK | 2.3.0 | [MIT](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE) |
| PaddleOCR / PaddleX / PaddlePaddle | 3.7.0 / 3.7.2 / 3.3.1 | Apache 2.0。[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) · [PaddleX](https://github.com/PaddlePaddle/PaddleX) · [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) |
| MLX-VLM | 0.7.12 | [MIT](https://github.com/Blaizzy/mlx-vlm/blob/main/LICENSE) |
| PaddleOCR-VL-1.6 | `132c45f52c0a26ed5a6b2f6bd8e3985794cc27dd` | [Apache 2.0 模型卡](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6/tree/132c45f52c0a26ed5a6b2f6bd8e3985794cc27dd) |
| PP-DocLayoutV3 | `241f8bdfc77a7c7bee915a5057aaee58c235a8d3` | [Apache 2.0 模型卡](https://huggingface.co/PaddlePaddle/PP-DocLayoutV3/tree/241f8bdfc77a7c7bee915a5057aaee58c235a8d3) |
| MOSS MLX | `d2546316f76e93947e8d99a17fb88652f8ad6ab2` | [Apache 2.0](https://github.com/vanch007/mlx-MOSS-Transcribe-Diarize/tree/d2546316f76e93947e8d99a17fb88652f8ad6ab2) |
| MOSS MLX 8-bit | `7210aef739be6b9e068fba9b1d60369ec053655b` | [Apache 2.0 模型卡](https://huggingface.co/vanch007/mlx-MOSS-Transcribe-Diarize-8bit/tree/7210aef739be6b9e068fba9b1d60369ec053655b) |
| MiniCPM-OCR 1.0 8-bit | `4196fbbad59fd7a87647abf8cd36be25ad9c5c8f` | Apache 2.0。[MLX 权重](https://huggingface.co/nativ-community/MiniCPM-OCR-1.0-8bit/tree/4196fbbad59fd7a87647abf8cd36be25ad9c5c8f) · [OpenBMB 原模型](https://huggingface.co/openbmb/MiniCPM-OCR-1.0) |
| MiniCPM-OCR Jev 8-bit | `fa1b463e56835d5d6b68253d8cd13f2f1cd54975` | Apache 2.0。[MLX 权重](https://huggingface.co/nativ-community/MiniCPM-OCR-Jev-8bit/tree/fa1b463e56835d5d6b68253d8cd13f2f1cd54975) · [OpenBMB 原模型](https://huggingface.co/openbmb/MiniCPM-OCR-Jev) |
| mlx-qwen3-asr | 0.4.4 | [Apache 2.0 源码](https://github.com/moona3k/mlx-qwen3-asr) |
| whisper.cpp 与 Whisper large-v3-turbo Q8_0 | v1.9.5 源码、固定 GGML 权重及 Silero VAD v6.2.0 | MIT。[whisper.cpp 发布](https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.5) · [Whisper 许可](https://github.com/openai/whisper#license) · [Silero VAD 许可](https://github.com/snakers4/silero-vad/blob/master/LICENSE) |
| Silero VAD | v6.2.2 序列 ONNX，提交 `60b7ffa243625ebdc1070275a29f18c87843786a`，ONNX Runtime 1.32.0 | [MIT](https://github.com/snakers4/silero-vad/blob/v6.2.2/LICENSE) · [官方发布](https://github.com/snakers4/silero-vad/releases/tag/v6.2.2) |
| Qwen3-ASR 0.6B 8-bit | `83ce2a8ef9a382d2ba2209aab383bc51fff366f5` | [Apache 2.0 模型卡](https://huggingface.co/moona3k/mlx-qwen3-asr-0.6b-8bit/tree/83ce2a8ef9a382d2ba2209aab383bc51fff366f5) |
| Qwen3-ASR 1.7B 8-bit | `22c8abe6a6772122dda5905967d7496d1d3e8dd2` | [Apache 2.0 模型卡](https://huggingface.co/moona3k/mlx-qwen3-asr-1.7b-8bit/tree/22c8abe6a6772122dda5905967d7496d1d3e8dd2) |
| Qwen3-ForcedAligner 0.6B | `c7cbfc2048c462b0d63a45797104fc9db3ad62b7` | [Apache 2.0 模型卡](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/tree/c7cbfc2048c462b0d63a45797104fc9db3ad62b7) |
| Hy-MT2 1.8B 8-bit 与 mlx-lm | 权重 `f54bb3b8885363fd8b83d63d50b50a12a138321f`，源码 `56230fa02b8ff8330daf26dc95c28480423ed5fe` | 权重 Apache 2.0、运行时 MIT。[MLX 权重](https://huggingface.co/mlx-community/Hy-MT2-1.8B-8bit/tree/f54bb3b8885363fd8b83d63d50b50a12a138321f) · [腾讯原模型](https://huggingface.co/tencent/Hy-MT2-1.8B) · [mlx-lm](https://github.com/ml-explore/mlx-lm/tree/56230fa02b8ff8330daf26dc95c28480423ed5fe) |
| GLiNER2.5 Multi | `gliner2` 2.1.0，权重 `7b005274e82da37dcf1f5fd9d6a2ef413c6a004c` | [Apache 2.0 模型卡](https://huggingface.co/fastino/gliner2.5-multi-v1/tree/7b005274e82da37dcf1f5fd9d6a2ef413c6a004c) |
| Chronos-2 | `chronos-forecasting` 2.3.2，权重 `29ec3766d36d6f73f0696f85560a422f50e8498c` | [Apache 2.0 模型卡](https://huggingface.co/amazon/chronos-2/tree/29ec3766d36d6f73f0696f85560a422f50e8498c) |
| TimesFM 3.0 | `timesfm[mlx]` 3.0.2，权重 `43046b85ec22d584a13f8098c2ed39c889e129c2` | 代码 Apache 2.0，下载权重限非商业、非生产。[固定权重和许可](https://huggingface.co/google/timesfm-3.0-pytorch/tree/43046b85ec22d584a13f8098c2ed39c889e129c2) |
| Depth Anything V2 Small FP16 | Apple `DepthAnythingV2SmallF16.mlpackage`，权重 `cfef6f6f2a70783dedc0bfae40cecbc2052285d3` | [Apache 2.0 模型卡](https://huggingface.co/apple/coreml-depth-anything-v2-small/tree/cfef6f6f2a70783dedc0bfae40cecbc2052285d3) |
| OpenAI Privacy Filter | 权重 `7ffa9a043d54d1be65afb281eddf0ffbe629385b`，源码 `f7f00ca7fb869683eb732c010299d901457f19c3`，tiktoken 0.14.0 的 `o200k_base` 词表在安装时校验 SHA-256 | Apache 2.0。[原始权重](https://huggingface.co/openai/privacy-filter/tree/7ffa9a043d54d1be65afb281eddf0ffbe629385b/original) · [OPF CLI](https://github.com/openai/privacy-filter/tree/f7f00ca7fb869683eb732c010299d901457f19c3) · [词表来源](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py) |
| Omni | v0.20.5，`86bdf26f33e3bc5d8fb9c066db54bda5b6f69ff6` | 代码 Apache 2.0。[签名发布包](https://github.com/hanxiao/omni-macos/releases/tag/v0.20.5) |
| Jina v5 Omni Small 检索权重 | `embed-weights-v1` Small 分卷，合并后 3.118 GB | 权重 CC BY-NC 4.0。[Jina 模型](https://jina.ai/models/jina-embeddings-v5-omni-small/) · [发布分卷](https://github.com/hanxiao/omni-macos/releases/tag/embed-weights-v1) |
| Jina Code Embeddings 0.5B | 固定的 MLX 模型实现及权重 `62add943d3052062c67b0d73b42ce9c671b9051f` | 权重 CC BY-NC 4.0。[模型及实现](https://huggingface.co/jinaai/jina-code-embeddings-0.5b-mlx/tree/62add943d3052062c67b0d73b42ce9c671b9051f) |
| Qwen3-VL-Reranker-2B | BF16 权重及精排模板 `4bd860ac4f15ad1897a214615cccc700f8f71818`，MLX 4-bit 权重 `374a7dc08e7c3b553c8b2730a425e53c7a926510` | Apache 2.0。[官方模型和模板](https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B/tree/4bd860ac4f15ad1897a214615cccc700f8f71818) · [4-bit 权重](https://huggingface.co/mlx-community/Qwen3-VL-Reranker-2B-4bit/tree/374a7dc08e7c3b553c8b2730a425e53c7a926510) |
| DigUp 和 EmbeddingGemma 2 | 签名 CLI v0.6.2，GGUF Q8_0 权重 `bfcd298762cc34d0357ece5ebdd31791a3a374d8` | CLI MIT、权重 Apache 2.0。[DigUp 发布包](https://github.com/ARahim3/DigUp/releases/tag/v0.6.2) · [GGUF 权重](https://huggingface.co/ggml-org/embeddinggemma-2-GGUF/tree/bfcd298762cc34d0357ece5ebdd31791a3a374d8) |
| Kokoro 82M | MLX Audio 0.6.5、Misaki 0.9.4、spaCy 英语资源 3.8.0，权重 `a71e4d38b236d968966a2002c4c895dbd12b1c3c` | 权重 Apache 2.0。[权重与音色](https://huggingface.co/mlx-community/Kokoro-82M-bf16/tree/a71e4d38b236d968966a2002c4c895dbd12b1c3c) · [Misaki](https://github.com/hexgrad/misaki) |
| SAM-Audio Small 与 T5 Base | 权重 `4ca84acc5c47f64bb2acee448f835dfac65ed318`，编码器 `a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1` | SAM Audio License、T5 Apache 2.0。[SAM-Audio MLX](https://huggingface.co/mlx-community/sam-audio-small/tree/4ca84acc5c47f64bb2acee448f835dfac65ed318) · [T5](https://huggingface.co/google-t5/t5-base/tree/a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1) |
| SAM3 BF16 | `dfe573c3171dbcfda8399c650d9135afa7e94592`，同时校验权重与 tokenizer | [SAM 权重与条款](https://huggingface.co/mlx-community/sam3-bf16/tree/dfe573c3171dbcfda8399c650d9135afa7e94592) |
| TalkNet-ASD | Apple Silicon 移植 `ac6bbdf175d57500e9f9c3fb1bb12779242d2b95`。安装器校验源码、TalkSet 及 S3FD 权重。 | 代码 MIT，上游未注明两份权重的许可。[上游移植与权重说明](https://github.com/nawta/TalkNet-ASD-py312/tree/ac6bbdf175d57500e9f9c3fb1bb12779242d2b95) |
| SwiftVR | MLX-Gen 0.38.0，Pillow 12.2.0，权重 `a0b09461bd89847712dd91dbb4c63541b4693936` | [SwiftVR Research License 1.0](https://huggingface.co/H-oliday/SwiftVR/blob/a0b09461bd89847712dd91dbb4c63541b4693936/LICENSE) · [MLX-Gen](https://github.com/lpalbou/mlx-gen) |
| SeedVR2-3B | 共用固定的 MLX-Gen 0.38.0。8-bit 权重 `6e6b162d1e96c873ad93645508bbc4636814c0c7`，校验配置、模型分片及 VAE。 | Apache 2.0。[原始权重](https://huggingface.co/ByteDance-Seed/SeedVR2-3B) · [8-bit 权重](https://huggingface.co/AbstractFramework/seedvr2-3b-8bit/tree/6e6b162d1e96c873ad93645508bbc4636814c0c7) |
| Clef-Flash | 固定 MLX 4-bit 模型、联合决策头与运行代码 `b5adbe2c3a95200d4bf04a0727c8ec457157d5e1` | Apache 2.0。[原模型](https://huggingface.co/Cloudflare/clef-flash) · [MLX 4-bit 转换](https://huggingface.co/mlx-community/clef-flash-4bit/tree/b5adbe2c3a95200d4bf04a0727c8ec457157d5e1) |
| Lean | 4.9.0 官方 ARM64 Darwin 归档 | [Apache 2.0](https://github.com/leanprover/lean4/blob/v4.9.0/LICENSE) · [官方发布](https://github.com/leanprover/lean4/releases/tag/v4.9.0) |
| Mathlib | Lean 4.9.0 配套的 Mathlib `f0957a7575317490107578ebaee9efaf8e62a4ab` | [Apache 2.0](https://github.com/leanprover-community/mathlib4/blob/f0957a7575317490107578ebaee9efaf8e62a4ab/LICENSE) |
| Goedel-Prover-V2 8B | Q4_K_M GGUF `43fab68ec71738a75b0a84738e18b222d2d4e249`，使用 LFM 固定的 llama.cpp b12444 运行。 | Apache 2.0。[原始模型](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-8B) · [GGUF 权重](https://huggingface.co/mradermacher/Goedel-Prover-V2-8B-GGUF/tree/43fab68ec71738a75b0a84738e18b222d2d4e249) |
| SmolVLA | LeRobot 0.7.0，策略 `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6`，SmolVLM 配置与 tokenizer `4cde9d208e19519c36917aa170fffc7e381aa0ad` | Apache 2.0。[策略和处理器](https://huggingface.co/lerobot/smolvla_base/tree/5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6) · [骨干配置](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct/tree/4cde9d208e19519c36917aa170fffc7e381aa0ad) |

`scripts/fetch_model.py` 核验直接下载权重的 SHA-256。`bin/install omni` 校验磁盘映像、应用签名、公证状态及检索权重。`bin/install depth-anything` 校验 Core ML 包内文件后用系统框架编译。MOSS 上游包在导入时依赖 PyTorch，本项目的转写路径使用 MLX。Hy-MT2 和 Privacy Filter 的安装器从固定 Git 提交构建源码包，运行依赖按对应的带哈希锁文件安装。

Apple Vision、PDFKit、Speech、Translation、Natural Language 和 Foundation Models 随系统提供。本项目使用 macOS 26 的公开 Swift API。各语言资源和本机系统模型由 macOS 管理。

可选的 `apple-fm-python` 使用 Apple Python SDK 0.2.2 源包及固定的 `ctypesgen` 1.1.1。安装器用现有 macOS SDK 编译官方 Swift-C 绑定，运行时复用系统的模型和语言资产。 [Apple Python SDK 发布包](https://pypi.org/project/apple-fm-sdk/0.2.2/)

实现参考。[PaddleOCR Apple Silicon 教程](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-Apple-Silicon.html) · [Apple Vision 文档识别](https://developer.apple.com/documentation/vision/recognizedocumentsrequest) · [Apple Speech](https://developer.apple.com/documentation/speech/) · [Apple Foundation Models](https://developer.apple.com/documentation/foundationmodels) · [Codex 配置参考](https://developers.openai.com/codex/config-reference) · [Claude Code MCP](https://code.claude.com/docs/en/mcp)
