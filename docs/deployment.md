# Deployment and tool selection

[简体中文](deployment.zh-CN.md)

Run `bin/plan` from the repository root. Python 3.10 or later can run the planner before installation. Inference backends require Apple Silicon and macOS 26 or later.

| Needed output | Example |
| --- | --- |
| Document layout and formulas | `bin/plan complex-layout --require formula_markup` |
| Speaker labels | `bin/plan speaker-transcript --execution mcp` |
| Commercial semantic search | `bin/plan semantic-search --use commercial` |
| Local glossary translation | `bin/plan glossary-translation --execution local` |
| Video upscaling | `bin/plan restore-video --require upscale_video` |
| Production forecasts | `bin/plan forecast --use production` |

Use `--profile default` for bundled routes, `--profile optional` for specialists, and `--verified-only` for routes with acceptance evidence. `--execution mcp` limits the results to MCP routes, while `--execution local` selects routes with a documented terminal command. Excluded candidates appear with their reasons. Commercial and production filters apply the restrictions recorded in the catalog. Check the upstream terms for the individual component. [Dependency and license records](../dependencies/README.md)

To target another Mac, add `--machine arm64 --macos 27.2 --disk-gib 100 --memory-gib 24`. The MCP planner accepts `machine`, `macos`, `disk_gib`, and `memory_gib` in its `target` object. An explicit target excludes this Mac's installed state from ranking. A focused review target with 24 GiB can select Reason Q4, 32 GiB can select Q8, and 16 GiB has no candidate under the current presets. Weight size is the lower bound for memory. Allow space for context, the runtime, and macOS.

Pass an approved absolute directory with `--folder` or the MCP `folder` field when planning semantic or code search. The planner will prefer a ready index for that directory and return its location in the search arguments. DigUp checks document and code indexes separately. Omni must be running and report a completed, nonempty index.

| Evidence or readiness | Meaning |
| --- | --- |
| `verified` | A local test confirmed the stated output |
| `integrated` | An entry point exists and still needs setup or acceptance |
| `upstream` | An upstream implementation is available |
| `installed` | Required files or known system assets are ready |
| `needs_setup` | Install assets, prepare an index, or confirm configuration |
| `trial_required` | Run an upstream trial |

## Install and register

```sh
bin/install default
bin/register
bin/register --check
.runtime/mcp/bin/python tests/smoke.py
```

The default install requires `uv`, Swift 6, and the macOS 26.4 SDK or later. Append locales to `default` to install Apple Speech assets. You can use the terminal tools without registering an MCP client. Pipe JSON to `bin/local <tool>` or `bin/lfm local <tool>`. Stage files under `~/LocalSpecialists` or an approved directory. [Installation and client acceptance](../README.md#quick-start)

## Client registration

<a id="client-registration"></a>
### Moving a checkout

Run `bin/register --check` from the new path. Inspect conflicts using `codex mcp get <name> --json` or `claude mcp get <name>`. Save any custom timeouts, environment variables, and permissions. Update the launch command in its existing scope, or remove the stale entry and run `bin/register` from the new path. Test `local_specialists.status` and `local-lfm.extract_fields` in new sessions.

[Upstream reference 1](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Upstream reference 2](https://code.claude.com/docs/en/mcp#mcp-installation-scopes) · [Upstream reference 3](https://code.claude.com/docs/en/mcp) · [中文](deployment.zh-CN.md#client-registration)

## Liquid AI LFM

<a id="lfm-fast"></a>
### LFM Fast for extraction and summaries

Run `bin/install default` or `bin/install lfm-fast`. Call `local-lfm.extract_fields` or `local-lfm.summarize`. Verify verbatim values and nulls with `bin/lfm verify --profile default`. The example below should return `Marina`.

```sh
printf '%s\n' '{"text":"Marina inspected the prism.","fields":{"owner":"Name of the person who inspected it"}}' | bin/lfm local extract_fields
```

[中文](deployment.zh-CN.md#lfm-fast)

<a id="lfm-vision"></a>
### LFM Vision for still images

Run `bin/install default` or `bin/install lfm-vision`. Put a PNG or JPEG in `backends/lfm/inbox/`. Call `local-lfm.inspect_image` with its filename and a question. The default verification reads a number from a synthetic screenshot and checks that paths outside the inbox are rejected.

[中文](deployment.zh-CN.md#lfm-vision)

<a id="lfm-tools"></a>
### LFM Tools for function calls

Run `bin/install lfm-tools`. Pipe a JSON request containing `messages` and `tools` to `bin/lfm chat lfm-tools`. Validate the resulting `choices[].message.tool_calls`, execute the tools, and send back the results. Set `tool_choice="none"` for the final response. Test with `bin/lfm verify --profile all`.

[中文](deployment.zh-CN.md#lfm-tools)

<a id="lfm-reason"></a>
### LFM Reason for review and offline agents

Run `bin/install lfm-reason`. Use `local-lfm.review`, or run `bin/lfm codex` and `bin/lfm claude` for local primary inference. Check with `bin/lfm verify_clients`.

[中文](deployment.zh-CN.md#lfm-reason)

<a id="offline-specialists"></a>
### Specialist tools in offline Codex and Claude Code

Install `core` and any specialist backends you need. Add `--with-specialists` to load `local_specialists`. Codex uses a temporary loopback port and writes artifacts under `backends/lfm/.state/codex-local/specialists/artifacts/`. Lean and PaddleOCR use session-specific Unix sockets. Precompile Core ML models outside the offline session when system temporary storage is needed. Use returned paths as inputs to subsequent tools and page large results with `read_evidence`.

```sh
bin/lfm codex --with-specialists
bin/lfm claude --with-specialists
```

```sh
bin/lfm codex --with-specialists exec --strict-config --ephemeral \
  -c 'mcp_servers.local_specialists.enabled_tools=["extract_apple_fields"]' \
  'Use extract_apple_fields to extract the person and date from: Remi booked the lab for October 31.'
```

[Upstream reference 1](https://learn.chatgpt.com/docs/config-file/config-reference) · [中文](deployment.zh-CN.md#offline-specialists)

<a id="lfm-quantization"></a>
### Comparing LFM quantizations

Install `lfm-fast-q4` or `lfm-reason-q4`. Compare identical requests through `bin/lfm chat <model-id>`. For review, pass `model="lfm-reason-q4"` to `local-lfm.review` or `bin/lfm local review`. Compare answer quality, initial load time, warm latency, and memory.

[中文](deployment.zh-CN.md#lfm-quantization)

## Documents

<a id="pdfkit"></a>
### Apple PDFKit

Install `core` and use `document` with `backend="auto"`. Check text and page number against the first page of the synthetic PDF. A `pdfkit` result comes from the text layer. Image pages fall back to Vision.

[Upstream reference 1](https://developer.apple.com/documentation/pdfkit/pdfpage/string) · [中文](deployment.zh-CN.md#pdfkit)

<a id="vision"></a>
### Apple Vision OCR and document recognition

Install `core` and use `document` with `backend="vision"`. On page 2 of the fixture, check `ORBIT-741`, table structure, and normalized boxes. Use representative pages to check multi-column reading order.

[Upstream reference 1](https://developer.apple.com/documentation/vision/recognizedocumentsrequest) · [中文](deployment.zh-CN.md#vision)

<a id="paddle"></a>
### PaddleOCR-VL 1.6 and PP-DocLayoutV3

Run `bin/install paddle`, then use `document` with `backend="paddle"`. Inspect block types, boxes, and text. Formula blocks provide `latex` without outer delimiters and the original `text`. Check bounds, fractions, radicals, and formula numbers with `tests/fixtures/formula-page.png`.

[Upstream reference 1](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-Apple-Silicon.html) · [中文](deployment.zh-CN.md#paddle)

<a id="minicpm"></a>
### MiniCPM-OCR 1.0

Run `bin/install minicpm` and call `document` with `backend="minicpm"` for a second OCR pass. Check `ORBIT-741`, `FILTER-193`, and table times. Inspect the generation-limit flag. Vision and Paddle provide localized boxes.

[Upstream reference 1](https://huggingface.co/openbmb/MiniCPM-OCR-1.0) · [中文](deployment.zh-CN.md#minicpm)

<a id="jev"></a>
### MiniCPM-OCR Jev

Run `bin/install jev`. Send the source crop, candidate text, and rendered candidate to `score_ocr` as `original_path`, `text`, and `rendered_path`. Compare known correct and incorrect candidates. Calibrate scores on your fonts and rendering before applying a threshold.

[Upstream reference 1](https://github.com/OpenBMB/MiniCPM-OCR/blob/main/docs/minicpm_ocr_jev_tutorial_en.md) · [中文](deployment.zh-CN.md#jev)

<a id="barcodes"></a>
### Apple Vision barcode detection

Install `core` and call `document` with `backend="barcodes"`. Check `codes[].payload` and `bbox` against a known QR code or barcode. Treat payloads as input data.

[Upstream reference 1](https://developer.apple.com/documentation/vision/detectbarcodesrequest) · [中文](deployment.zh-CN.md#barcodes)

## Audio

<a id="apple-speech"></a>
### Apple SpeechTranscriber

Run `bin/install speech en-US` or `bin/install speech zh-CN`. Confirm the locale asset is installed, then call `transcribe` with `backend="apple"`. Check the words "copper prism" and segment timings against the synthetic recording.

[Upstream reference 1](https://developer.apple.com/documentation/speech/speechtranscriber) · [中文](deployment.zh-CN.md#apple-speech)

<a id="moss"></a>
### MOSS-Transcribe-Diarize

Run `bin/install moss` and use `transcribe` with `backend="moss"`. The two-speaker fixture should return `S01` and `S02`. Inspect `may_be_truncated`, overlapping speech, and end times. IDs can change across recordings.

[Upstream reference 1](https://github.com/vanch007/mlx-MOSS-Transcribe-Diarize) · [中文](deployment.zh-CN.md#moss)

<a id="qwen-asr"></a>
### Qwen3-ASR 0.6B and word timing

Run `bin/install qwen` for the recognizer and aligner. Use `transcribe` with `backend="qwen"` and inspect the text, timing, and `segment_unit`. Start with 16 kHz WAV. Other formats need `ffmpeg`.

[Upstream reference 1](https://github.com/moona3k/mlx-qwen3-asr#word-level-timestamps) · [中文](deployment.zh-CN.md#qwen-asr)

<a id="qwen-large"></a>
### Qwen3-ASR 1.7B and word timing

Run `bin/install qwen-large` and use `transcribe` with `backend="qwen-large"`. It shares the aligner with 0.6B. Compare terminology, accents, and latency on the same samples.

[Upstream reference 1](https://huggingface.co/moona3k/mlx-qwen3-asr-1.7b-8bit) · [中文](deployment.zh-CN.md#qwen-large)

<a id="qwen-align"></a>
### Qwen3-ForcedAligner 0.6B

Run `bin/install qwen-align`. Call `align_audio` with `path`, corrected `text`, and a supported `language` such as `English`. The limit is 120 seconds per clip. Spot-check word boundaries against the audio.

[Upstream reference 1](https://github.com/QwenLM/Qwen3-ASR) · [中文](deployment.zh-CN.md#qwen-align)

<a id="speech-detector"></a>
### Apple SpeechDetector

Run `bin/plan speech-detector-probe`. The native `transcribe` probe uses `backend="activity"` and returned no intervals for the speech fixture. When timing is needed, use Silero, Apple transcription, or Sound Analysis.

[Upstream reference 1](https://developer.apple.com/documentation/speech/speechdetector/results) · [中文](deployment.zh-CN.md#speech-detector)

<a id="silero-vad"></a>
### Silero VAD

Install `ffmpeg` and run `bin/install silero`. Pass `backend="silero"` and an absolute audio `path` to `transcribe`. It reads the first track as 16 kHz mono, supports up to 30 minutes, and returns speech intervals. The preset omits speech under 250 ms.

[Upstream reference 1](https://github.com/snakers4/silero-vad/releases/tag/v6.2.2) · [中文](deployment.zh-CN.md#silero-vad)

<a id="qwen-stream"></a>
### Streaming Qwen3-ASR

Run `bin/install qwen`. Pipe 16 kHz mono signed 16-bit little-endian PCM into `bin/stream-asr`. Each NDJSON record provides the current `text` and `stable_text`. Replace the displayed text on each update. The final record includes revisions. MCP replay uses `transcribe` with `backend="qwen-stream"` for files up to 30 minutes and returns partials and the final result together. Use the terminal pipe for live updates and grant microphone access when needed.

```sh
ffmpeg -hide_banner -loglevel error -re -i tests/fixtures/meeting.wav \
  -ac 1 -ar 16000 -f s16le - | bin/stream-asr --language English
```

```sh
ffmpeg -nostdin -hide_banner -f avfoundation -i ':MacBook Pro Microphone' \
  -t 5 -vn -ac 1 -ar 16000 -f s16le - | bin/stream-asr --chunk-seconds 1 --language English
```

[Upstream reference 1](https://github.com/moona3k/mlx-qwen3-asr#streaming) · [中文](deployment.zh-CN.md#qwen-stream)

<a id="sam-audio"></a>
### SAM Audio Small

Run `bin/install sam-audio` for the MLX model and T5 encoder. Pass the approved audio path and a `description` such as "human speech" to `separate_audio`. Clips up to 30 seconds produce target and residual 48 kHz WAV files. Check leakage and distortion with a known mixture.

[Upstream reference 1](https://huggingface.co/mlx-community/sam-audio-small) · [Upstream reference 2](https://huggingface.co/facebook/sam-audio-small) · [中文](deployment.zh-CN.md#sam-audio)

<a id="kokoro"></a>
### Kokoro 82M

Run `bin/install kokoro` and call `synthesize_speech` with `backend="kokoro"`. Try `voice="af_heart"` for English or `voice="zf_xiaobei"` for Mandarin. `words_per_minute=175` is the baseline. Verify the voice, content, and 24 kHz output.

[Upstream reference 1](https://github.com/Neywa-Labs/mlx-audio/blob/main/docs/models/tts/kokoro.md) · [Upstream reference 2](https://huggingface.co/hexgrad/Kokoro-82M) · [中文](deployment.zh-CN.md#kokoro)

<a id="apple-tts"></a>
### macOS system speech synthesis

Install `core` and call `synthesize_speech` with text, a system voice, and optional `words_per_minute`. List voices with `say -v '?'`. Check the 22.05 kHz WAV and duration under `.runtime/artifacts/`.

[Upstream reference 1](https://support.apple.com/guide/mac-help/mchlp2290/mac) · [中文](deployment.zh-CN.md#apple-tts)

<a id="sound-analysis"></a>
### Apple Sound Analysis

Install `core` and call `classify_sound` with `path`. Adjust `threshold` and per-window `limit` as needed. Check labels, confidence, and overlapping windows. The synthetic speech recording should yield `speech`.

[Upstream reference 1](https://developer.apple.com/documentation/soundanalysis/classifying-sounds-in-an-audio-file) · [中文](deployment.zh-CN.md#sound-analysis)

## Search

<a id="omni"></a>
### Omni and Jina v5 Omni Small

Run `bin/install omni` for the signed app and pinned Small weights. Use the Omni CLI's `add_source` and `list_sources` to build an index. Call `search` with `backend="omni"`. Check source lines or PDF pages. The weights use CC BY-NC 4.0. Offline sessions can use a designated Unix socket through `LFM_OMNI_SOCKET`.

```sh
bin/lfm codex --with-omni --with-specialists
bin/lfm claude --with-omni --with-specialists
```

[Upstream reference 1](https://github.com/hanxiao/omni-macos) · [中文](deployment.zh-CN.md#omni)

<a id="digup"></a>
### DigUp and EmbeddingGemma 2

Run `bin/install digup`, then index an approved directory. The commands below should find page 2 of `calibration.pdf`. Use `--code` when indexing code and `code=true` in the query. Reindex when the source changes. For small indexes, try `min_semantic_z=1` if the default threshold of 2 returns no candidates.

```sh
.runtime/mcp/bin/python tests/smoke.py
bin/local index-digup "$HOME/LocalSpecialists/demo"
jq -nc --arg folder "$HOME/LocalSpecialists/demo" \
  '{folder:$folder,backend:"digup",query:"ORBIT-741 11:40"}' | bin/local search
.runtime/mcp/bin/python tests/smoke.py --digup
```

[Upstream reference 1](https://github.com/ARahim3/DigUp) · [Upstream reference 2](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2) · [中文](deployment.zh-CN.md#digup)

<a id="omni-pairing"></a>
### Linking two Macs with Omni

Install Omni on both Macs. Use **File → Link a Mac** and compare pairing codes. Set search and file permissions on each device. Add `omni_linked_macs` to `.runtime/config.json` with the paired name or ID and allowed remote paths. `search_linked_mac` filters returned results by those paths. Pairing and reads passed on two isolated instances on one Mac. Testing on separate Macs remains pending.

```json
{"omni_linked_macs":{"Studio":["/Users/me/LocalSpecialists/shared"]}}
```

```sh
printf '%s\n' '{"peer":"Studio","query":"Violet Sextant"}' | bin/local search_linked_mac
```

[Upstream reference 1](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md) · [中文](deployment.zh-CN.md#omni-pairing)

<a id="omni-linked-copy"></a>
### Copying a result from a linked Mac

Call `fetch_linked_mac` with the same `peer`, `query`, and full hit `path` returned by `search_linked_mac`. Enable reads on the device holding the file. The optional `output_folder` must already exist and be approved and writable. Otherwise the tool creates a separate artifact directory. It checks permission, the 16 MiB limit, and cached size. Compare `sha256` and use the returned local `path` for follow-up.

[Upstream reference 1](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md) · [Upstream reference 2](https://github.com/hanxiao/omni-macos/blob/v0.20.5/App/Link/RemoteFiles.swift) · [中文](deployment.zh-CN.md#omni-linked-copy)

<a id="spotlight"></a>
### Spotlight filename search

Install `core` and use `search` with `backend="spotlight"`. Check a unique filename in an indexed directory with `mdls` and `mdfind -onlyin "$PWD" -name <filename>`. Use `rg --files` for directories Spotlight does not cover.

[Upstream reference 1](https://support.apple.com/guide/mac-help/search-with-spotlight-mchlp1008/mac) · [中文](deployment.zh-CN.md#spotlight)

<a id="core-spotlight"></a>
### SpotlightSearchTool app index

On macOS and SDK 27, enable Apple Intelligence and run `bin/install apple-spotlight`. Call `search_apple_notes` with `path` to approved JSON and a `question`. Provide up to 24 notes with `id`, `title`, and `text`, within 32 KiB. The helper creates its own temporary index and returns the source in `matches`. Compare the answer with those matches.

[Upstream reference 1](https://developer.apple.com/documentation/corespotlight/searching-indexed-content-with-natural-language) · [中文](deployment.zh-CN.md#core-spotlight)

<a id="core-spotlight-semantic"></a>
### Core Spotlight semantic ranking

Use the same helper with `mode="semantic"`. The result includes up to five source matches and `text=null`. Try the fixture `tests/fixtures/spotlight-notes.json`. "pastries made with tree nuts" found "Almond Nutmeg Cookies" in local testing, while "marine mammals" missed the seal note.

[Upstream reference 1](https://developer.apple.com/documentation/corespotlight/building-a-search-interface-for-your-app) · [Upstream reference 2](https://developer.apple.com/documentation/corespotlight/csuserquerycontext/disablesemanticsearch) · [中文](deployment.zh-CN.md#core-spotlight-semantic)

<a id="jina-grep"></a>
### Jina Code Embeddings and jina-grep

Run `bin/install jina-grep` and call `search_code` with a behavior `query` and absolute UTF-8 source paths in `files`. The limit is 64 files and 128 KiB total. Check line numbers and relevance. The 0.5B weights are noncommercial.

[Upstream reference 1](https://github.com/jina-ai/jina-grep-cli#code-search) · [Upstream reference 2](https://huggingface.co/jinaai/jina-code-embeddings-0.5b-mlx) · [中文](deployment.zh-CN.md#jina-grep)

<a id="qwen-reranker"></a>
### Qwen3-VL-Reranker-2B

Run `bin/install qwen-reranker`. Send `query` and up to 12 `candidates` to `rerank_visual`. PDF candidates use `path` and `page`. Images use `path`. Candidates can also contain `text`. Compare rankings against known relevant pages using each candidate's `input_index`. Use `bin/install qwen-reranker-4bit` and `precision="4bit"` for the smaller model. Calibrate thresholds separately.

[Upstream reference 1](https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B) · [Upstream reference 2](https://huggingface.co/mlx-community/Qwen3-VL-Reranker-2B-4bit) · [中文](deployment.zh-CN.md#qwen-reranker)

## Text

<a id="apple-translation"></a>
### Apple Translation

Install `core` and download both languages in System Settings → General → Language & Region → Translation Languages. Check `native/.build/release/apple-specialists translation-status en zh-Hans`. Call `translate` with `texts`, `source_language`, and `target_language` and check the item count and meaning.

[Upstream reference 1](https://support.apple.com/guide/mac-help/mchldd8b3c15/mac) · [Upstream reference 2](https://developer.apple.com/documentation/translation/translationsession) · [中文](deployment.zh-CN.md#apple-translation)

<a id="hy-mt"></a>
### Hy-MT2

Run `bin/install hy-mt` and use `translate` with `backend="hy-mt"`. Pass a `glossary` mapping source terms to requested translations. Check ordering, `truncated`, and glossary matches. Batch long documents and preserve IDs or subtitle timestamps.

[Upstream reference 1](https://huggingface.co/tencent/Hy-MT2-1.8B#hy-mt2-translation-task-instruction-examples-chinese-english-comparison) · [中文](deployment.zh-CN.md#hy-mt)

<a id="natural-language"></a>
### Apple Natural Language

Install `core` and call `text_analysis`. Check language, parts of speech, and named entities against text containing names, locations, and emoji. Offsets use UTF-16 code units.

[Upstream reference 1](https://developer.apple.com/documentation/naturallanguage) · [中文](deployment.zh-CN.md#natural-language)

<a id="foundation-models"></a>
### Apple Foundation Models for text questions

Install `core`, enable Apple Intelligence, and wait for `status` to show `foundation_models` as `available`. Call `focus_text` with a known passage and question, then check each answer against the source.

[Upstream reference 1](https://developer.apple.com/documentation/foundationmodels) · [中文](deployment.zh-CN.md#foundation-models)

<a id="foundation-structured"></a>
### Apple Foundation Models for structured extraction

Install `core` and call `extract_apple_fields`. Its Swift schema returns verbatim values or `null`. Check the example for owner `Marina` and a null budget. The model can return a pending value as confirmed, so inspect the source context. On macOS 27, after accepting system CLI terms, try `fm respond --model system --no-stream --greedy 'Return only the code BASALT-814.'`.

```sh
printf '%s\n' '{"text":"Marina owns the inspection. The budget is pending.","fields":{"owner":"Name of the person responsible","budget":"Confirmed budget amount"}}' | bin/local extract_apple_fields
```

[Upstream reference 1](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation) · [Upstream reference 2](https://developer.apple.com/videos/play/wwdc2026/334/) · [Upstream reference 3](https://github.com/apple/python-apple-fm-sdk) · [中文](deployment.zh-CN.md#foundation-structured)

<a id="apple-fm-python"></a>
### Apple Foundation Models Python callbacks

Run `bin/install apple-fm-python` and enable Apple Intelligence. Use `bin/apple-fm-python your_script.py` with the pinned Apple SDK. Call `lookup_apple_record` on an approved JSON object up to 32 KiB and 32 keys, with optional `keys` to narrow the search. Use `{"beacon_amber":{"service_code":762},"beacon_blue":{"service_code":481}}` in the sample file and verify the actual key and value in `lookups`.

```sh
bin/plan apple-record-lookup --execution mcp --verified-only --json
printf '%s\n' '{"path":"/Users/me/LocalSpecialists/calibration.json","question":"Use read_record to get the service code for beacon_amber."}' |
  bin/local lookup_apple_record
```

[Upstream reference 1](https://github.com/apple/python-apple-fm-sdk) · [Upstream reference 2](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting) · [中文](deployment.zh-CN.md#apple-fm-python)

<a id="apple-fm-image"></a>
### Apple Foundation Models image questions

On macOS and SDK 27, install `apple-fm-python` and check `status.apple_fm_attachments`. Pass an approved image `path` and `question` to `inspect_apple_attachment`. Test colors and positions in images with no text. Use Vision OCR when exact text and coordinates matter.

[Upstream reference 1](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting) · [中文](deployment.zh-CN.md#apple-fm-image)

<a id="gliner"></a>
### GLiNER2.5 multi-v1

Run `bin/install core`, `bin/install gliner`, and `bin/register`. Pass up to eight `texts` and descriptive `labels` to `extract_entities`. Compare confidence and Unicode code-point spans against annotated samples.

[Upstream reference 1](https://huggingface.co/fastino/gliner2.5-multi-v1) · [中文](deployment.zh-CN.md#gliner)

<a id="privacy-filter"></a>
### OpenAI Privacy Filter

Run `bin/install privacy`, then `bin/redact < input.txt > redacted.txt`. The installer checks the tokenizer and weights. Review redacted output for misses. For spans and categories, set `TIKTOKEN_CACHE_DIR` to `.runtime/models/privacy/tiktoken` and use `opf redact --checkpoint .runtime/models/privacy/original --device cpu --format json`.

[Upstream reference 1](https://github.com/openai/privacy-filter#how-to-use) · [Upstream reference 2](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py) · [中文](deployment.zh-CN.md#privacy-filter)

<a id="clef"></a>
### Cloudflare Clef-Flash

Run `bin/install clef` and `bin/register`. Call `decide` with `state`, `questions`, and an optional `image_path`. Define `instructions` for each question. `binary` scores both outcomes, `choice` takes a mapping of labels to descriptions, and `score` uses ordered descriptions. Compare against labeled data and set review thresholds with held-out samples.

[Upstream reference 1](https://huggingface.co/Cloudflare/clef-flash) · [Upstream reference 2](https://huggingface.co/mlx-community/clef-flash-4bit) · [中文](deployment.zh-CN.md#clef)

## Images and video

<a id="talknet"></a>
### TalkNet-ASD

Install `ffmpeg` and run `bin/install talknet`. Pass `path`, start time `start`, and `duration` to `active_video_speakers`. Select `device="mps"` or `"cpu"` as needed. Check source timestamps, pixel boxes, and the annotated AVI. Weight licenses for TalkSet and S3FD are unconfirmed.

[Upstream reference 1](https://github.com/nawta/TalkNet-ASD-py312) · [Upstream reference 2](https://github.com/TaoRuijie/TalkNet-ASD) · [中文](deployment.zh-CN.md#talknet)

<a id="sam3"></a>
### Segment Anything 3

Run `bin/install sam3` and call `segment_objects` with `path` and a prompt such as `prompt="a cat"`. `task="segment"` returns PNG masks and boxes. `task="track"` accepts up to 30 seconds at up to 1080p-equivalent pixel count. Check IDs across cuts and occlusion.

[Upstream reference 1](https://huggingface.co/mlx-community/sam3-bf16) · [Upstream reference 2](https://github.com/facebookresearch/sam3) · [中文](deployment.zh-CN.md#sam3)

<a id="apple-video-upscale"></a>
### Apple VideoToolbox super-resolution

Install `core`, `ffmpeg`, and `ffprobe`. Check device support with `native/.build/release/apple-specialists video-scale-status 320 192`. Call `restore_video` with `backend="apple"` and a supported `scale`. Use SDR input and check dimensions, frame count, timing, and audio in the H.264 MP4.

[Upstream reference 1](https://developer.apple.com/documentation/videotoolbox/vtlowlatencysuperresolutionscalerconfiguration) · [Upstream reference 2](https://developer.apple.com/documentation/videotoolbox/enhancing-your-app-with-machine-learning-based-video-effects) · [中文](deployment.zh-CN.md#apple-video-upscale)

<a id="swiftvr"></a>
### SwiftVR

Install `ffmpeg` and `ffprobe`, then run `bin/install swiftvr`. Call `restore_video` with `path` and optional `start_seconds`, `max_frames`, and `seed`. It restores short clips at the original resolution and may trim the tail to a valid frame count. Two test clips had lower SSIM than their degraded inputs against the reference. The weights use the SwiftVR Research License.

[Upstream reference 1](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md#swiftvr-one-step-restoration) · [Upstream reference 2](https://huggingface.co/H-oliday/SwiftVR/blob/a0b09461bd89847712dd91dbb4c63541b4693936/LICENSE) · [中文](deployment.zh-CN.md#swiftvr)

<a id="seedvr2"></a>
### SeedVR2

Run `bin/install seedvr2`. Call `restore_image` for stills or `restore_video` with `backend="seedvr2"` for video. Video uses `ffmpeg` and `ffprobe`. Begin at `scale="1x"` and inspect frames and audio. Video upscaling requires both `scale="2x"` and `allow_high_memory=true`. A nine-frame 320 × 192 sample peaked at about 52.7 GB in MLX.

[Upstream reference 1](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md) · [Upstream reference 2](https://huggingface.co/AbstractFramework/seedvr2-3b-8bit/tree/6e6b162d1e96c873ad93645508bbc4636814c0c7) · [中文](deployment.zh-CN.md#seedvr2)

<a id="apple-foreground"></a>
### Apple Vision foreground masks

Install `core` and call `extract_apple_foreground` with an absolute image `path`. Check `instances`, the size of `foreground_png`, and its alpha channel. Use SAM3 for text-directed object selection.

[Upstream reference 1](https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest) · [中文](deployment.zh-CN.md#apple-foreground)

<a id="vision-media"></a>
### Apple Vision media inspection

Install `core` and call `inspect_apple_image` with `path` for labels and an aesthetic score. Add `comparison` for a feature distance, where smaller values indicate greater similarity. Use identical and distinct images to establish a baseline.

[Upstream reference 1](https://developer.apple.com/documentation/vision) · [Upstream reference 2](https://developer.apple.com/documentation/Vision/generating-thumbnails-from-videos) · [中文](deployment.zh-CN.md#vision-media)

<a id="depth-anything"></a>
### Depth Anything V2 Small via Core ML

Run `bin/install depth-anything` and call `estimate_depth` with `path`. Set `compute` to `all`, `cpu`, or `cpu-gpu` if needed. Check relative foreground and background ordering in the aligned PNG. Its longest side is limited to 4,000 pixels. Metric distances require calibration.

[Upstream reference 1](https://huggingface.co/apple/coreml-depth-anything-v2-small) · [中文](deployment.zh-CN.md#depth-anything)

<a id="core-ml"></a>
### Apple Core ML

Install `core` and place a model in an approved directory. Pass its `model` path to `predict_coreml` to inspect the schema. For inference, pass named `inputs` such as images, numbers, text, or tensor values with optional `shape`. Inspect exported PNGs or returned tensor shapes and the first 1,024 values.

[Upstream reference 1](https://developer.apple.com/documentation/coreml) · [中文](deployment.zh-CN.md#core-ml)

<a id="shortcuts"></a>
### Apple Shortcuts

Install `core`. Create an on-device text workflow with **Use Model** and **Stop and Output**, or an image workflow with **Extract Text from Image**. List UUIDs with `shortcuts list --show-identifiers` and allow the intended workflow in `.runtime/config.json` under `allowed_shortcut_ids`. Call `run_apple_shortcut` with its `shortcut_id` and either `text` or an approved image `path`. Check with synthetic input. The Shortcut's own actions determine its access to apps, the network, and user data.

[Upstream reference 1](https://support.apple.com/guide/shortcuts-mac/use-apple-intelligence-in-shortcuts-mchl91750563/mac) · [Upstream reference 2](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac) · [Upstream reference 3](https://developers.openai.com/codex/config-reference) · [中文](deployment.zh-CN.md#shortcuts)

<a id="screenshot-folder"></a>
### OCR for new screenshots in a directory

Install `core` and use `bin/local watch-screenshots "$HOME/LocalSpecialists/screenshots"` for NDJSON. For MCP, call `wait_for_screenshot` with an approved `folder` and a `wait_seconds` value between 1 and 45. Move a complete PNG, JPEG, or HEIC into the directory. Check the returned text and boxes, or `timed_out` when nothing arrives.

[Upstream reference 1](https://developer.apple.com/documentation/screencapturekit) · [中文](deployment.zh-CN.md#screenshot-folder)

<a id="shortcuts-folder"></a>
### Shortcuts Folder automation

Create a Folder automation with **Added Files**, **Ignore Subfolders**, and **Run Immediately**. Use **Extract Text from Image** on the Shortcut input and **Save File** to a separate output directory. Try two synthetic screenshots and check that the approved output can be read by the client.

[Upstream reference 1](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac) · [中文](deployment.zh-CN.md#shortcuts-folder)

<a id="shortcuts-screenshot"></a>
### System Screenshot trigger

In Shortcuts, add **When a screenshot is saved** with **Files**. Use **Text** and **Save File** to write a fixed test marker. Take a screenshot of a synthetic window using Shift-Command-4 and Space. Check the marker and OCR from the approved screenshot directory. macOS 27.2.1 also offers Photos and Clipboard destinations.

[Upstream reference 1](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac) · [Upstream reference 2](https://support.apple.com/en-au/guide/mac-help/mh26782/27/mac/27) · [中文](deployment.zh-CN.md#shortcuts-screenshot)

## Specialist tasks

<a id="timesfm"></a>
### TimesFM 3.0

Run `bin/install timesfm` and use `forecast_series` with `backend="timesfm"`. Use the same fields and quantiles as Chronos. Compare with a simple baseline on a time-ordered holdout. The pinned weights are for noncommercial, nonproduction use.

[Upstream reference 1](https://github.com/google-research/timesfm) · [Upstream reference 2](https://huggingface.co/google/timesfm-3.0-pytorch) · [中文](deployment.zh-CN.md#timesfm)

<a id="chronos"></a>
### Chronos-2

Run `bin/install core` and `bin/install chronos`, then call `forecast_series` with `targets` and `horizon`. Use a shared, evenly spaced timeline. Each future covariate needs a corresponding historical sequence and exactly `horizon` values. Compare 0.1, 0.5, and 0.9 quantiles with held-out data and a seasonal or last-value baseline.

[Upstream reference 1](https://huggingface.co/amazon/chronos-2) · [中文](deployment.zh-CN.md#chronos)

<a id="lean-kernel"></a>
### Checking a proof with Lean

Run `bin/install lean`. Call `check_lean_proof` with `source`, `declaration`, and the expected `statement`. Check the exact proposition and audited axiom dependencies. A mismatch, `sorryAx`, or custom axioms yields `accepted=false`. Use `bin/install lean-mathlib` and `library="mathlib"` when needed.

[Upstream reference 1](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) · [中文](deployment.zh-CN.md#lean-kernel)

<a id="goedel"></a>
### Goedel-Prover-V2 and Lean

Run `bin/install goedel` and call `generate_lean_proof` with a formal Lean `statement`. Review `accepted`, `statement_checked`, and `axioms` in the verification output. Check that the Lean statement actually expresses the original problem.

[Upstream reference 1](https://github.com/Goedel-LM/Goedel-Prover-V2#5-environment-setup) · [Upstream reference 2](https://huggingface.co/mradermacher/Goedel-Prover-V2-8B-GGUF/tree/43fab68ec71738a75b0a84738e18b222d2d4e249) · [中文](deployment.zh-CN.md#goedel)

<a id="smolvla"></a>
### SmolVLA with recorded LeRobot data

Run `bin/install smolvla` and call `preview_robot_actions` with `camera_images`, six-dimensional `state`, and `instruction`. Match the recorded camera names, using `camera1` for `top` and `camera2` for `wrist` on the public SO100 sample. Provide matching `statistics_path` to work in dataset units, or pass normalized state. Compare predicted action shape and scale against the recording.

[Upstream reference 1](https://huggingface.co/lerobot/smolvla_base) · [Upstream reference 2](https://huggingface.co/datasets/lerobot/svla_so100_pickplace) · [中文](deployment.zh-CN.md#smolvla)

<a id="smolvla-preflight"></a>
### LeRobot hardware preflight

Install `core` and `smolvla`, then call `check_smolvla_rollout`. It checks the rollout command and motor driver, enumerates serial ports, and can inspect `port`, `policy_path`, and `calibration_path`. Matching metadata confirms file structure. Physical validation remains pending.

[Upstream reference 1](https://huggingface.co/docs/lerobot/main/en/so100) · [中文](deployment.zh-CN.md#smolvla-preflight)

<a id="smolvla-rollout"></a>
### LeRobot live rollout

The installer pins LeRobot 0.7.0 and the Feetech drivers. Use the linked upstream rollout guide for calibration, camera configuration, and policy setup. Check the configuration with the preflight and evaluate recorded data or simulation first. The project verified CLI loading and public replay. Live hardware, camera mapping, and motion quality remain pending.

[Upstream reference 1](https://huggingface.co/docs/lerobot/main/en/smolvla#evaluate-the-finetuned-model-and-run-it-in-real-time) · [Upstream reference 2](https://huggingface.co/docs/lerobot/main/en/inference) · [中文](deployment.zh-CN.md#smolvla-rollout)
