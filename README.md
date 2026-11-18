# Cairnkite

[简体中文](README.zh-CN.md)

Cairnkite is a local AI toolkit for macOS. It lets Codex and Claude Code choose and call Liquid AI models, Apple frameworks, and specialist models through MCP. The tools also run directly from your terminal.

A cairn is a stone trail marker. The kite is a bird. The name reflects how Cairnkite helps agents find the right tool and call it on demand.

```sh
bin/plan
bin/plan scan --profile default
bin/plan extract-fields --profile default --use personal
bin/plan complex-layout --require formula_markup --execution mcp
bin/plan semantic-search --use commercial --json
```

Registered clients can also call `local_specialists.plan_deployment`. [Deployment guide](docs/deployment.md) · [Integration plan](docs/integration-plan.md) · [Agent guide](docs/agents.md)

<a id="工作流"></a>
## Workflows

| Task | MCP call | Result |
| --- | --- | --- |
| PDF, screenshots, and scans | `document`, `backend="auto"` | PDFKit prioritizes reading the PDF text layers. Apple Vision processes image pages and returns text, bounding boxes, and detected tables. |
| Complex layouts, formulas, and tables | `document`, `backend="paddle"` | PaddleOCR-VL 1.6 first detects the layout, and then MLX-VLM identifies each region. The results include Markdown, layout classification, and bounding boxes. |
| Second OCR route, review of difficult areas | `document` (`backend="minicpm"`), `score_ocr` | MiniCPM-OCR outputs the entire page text, and Jev provides consistency scores for the original cutout, candidates, and rendered images. |
| Barcode and QR code | `document`, `backend="barcodes"` | Apple Vision returns the encoding value, type, and coordinates. |
| General Recording Transcription | `transcribe`, `backend="apple"` | Apple Speech returns text and time intervals. Use `locale` to specify the installed language resources. |
| Only locate voice and mute | `transcribe`, `backend="silero"` | The small ONNX model returns speech segments on the CPU, without requiring language resources. |
| Multiple people recording | `transcribe`, `backend="moss"` | MOSS MLX returns text, time interval, and anonymous speaker ID. |
| Separate sound from the recording | `separate_audio` | SAM Audio returns the target and residual WAVs according to the description. |
| Word-level time and proofreading alignment | `transcribe` (`backend="qwen"` or `"qwen-large"`), `align_audio` | Qwen3-ASR 0.6B, 1.7B, and ForcedAligner return words or language units and time. |
| Real-time audio and streaming playback | `bin/stream-asr`, `transcribe` (`backend="qwen-stream"`) | The local PCM pipeline outputs provisional text block by block. MCP can play back existing recordings, returning intermediate results and the final version. |
| Sound events and reading aloud | `classify_sound`, `synthesize_speech` | Apple Sound Analysis returns categories and time. System timbre and optional Kokoro generation provide native WAV files. |
| Find materials or code based on meaning | `search`, `backend="digup"` or `"omni"` | Querying the locally built index. DigUp can provide PDF page numbers, media timestamps, or line numbers. |
| Direct search for a small number of source files | `search_code` | Jina 0.5B sorts by code behavior, returning files and line numbers. |
| Find materials by file name | `search`, `backend="spotlight"` | Path returned from Spotlight’s file metadata index. The results are limited by the system index coverage. |
| Local Translation | `translate`, `backend="apple"` or `"hy-mt"` | Apple uses installed language resources. Hy-MT2 accepts term hints. |
| Language, Part of Speech, and Entities | `text_analysis` | Apple Natural Language returns language guesses, part of speech, built-in entities, and UTF-16 positions. |
| Text extraction and short summary | `focus_text` | Apple Foundation Models answer questions based on short texts. Apple Intelligence must be enabled. |
| Short text with fixed fields | `extract_apple_fields` | Apple Foundation Models return the original string and missing fields through Swift dynamic schema. |
| Apple device model calls Python | `lookup_apple_record`, `bin/apple-fm-python` | Retrieve the original value from the specified JSON, or you can also implement custom callbacks for the native device model in a Python script. |
| Apple native image QA and app index | `inspect_apple_attachment`, `search_apple_notes` | The macOS 27 system model receives images. Notes are answered by SpotlightSearchTool, or the original text is returned after semantic sorting by Core Spotlight. |
| New screenshot auto OCR | `wait_for_screenshot`, `bin/local watch-screenshots` | Monitors the approved directory. New full image files are recognized via Vision. It is also possible to configure [Shortcuts Folder automation for](docs/deployment.md#shortcuts-folder) to automatically save text. |
| Custom entities for multiple texts | `extract_entities` | GLiNER return entity and Unicode code point position. |
| Image category, similarity, and relative depth | `inspect_apple_image`, `estimate_depth` | Apple Vision returns the category or distance, Core ML generates in‑real‑time depth PNG. |
| Self-provided Core ML model | `predict_coreml` | Check the input/output structure, run predictions on the input image or short tensor. |
| Apple Text and Image Quick Actions | `run_apple_shortcut` | Send text or image to a configured shortcut command, and get its plain text result. |
| Candidate page and image precise ranking | `rerank_visual` | For the current query, rearrange PDF pages, images, and text candidates. |
| Video Repair and Zooming | `restore_video`, `restore_image` | SwiftVR fixes original-size videos. SeedVR2 can zoom in on static images and short videos. Apple VideoToolbox can zoom in on SDR short videos in supported sizes. |
| Fixed options and scoring by categories | `decide` | Clef-Flash makes multiple binary judgments, options, and scoring categories during an analysis. |
| Static image native image cutting | `extract_apple_foreground` | Apple Vision return count and transparent PNG. |
| Object mask and video association | `segment_objects` | SAM3 generates image masks based on object names, and can also add frames and labels for short videos. |
| Determine who is speaking in the video | `active_video_speakers` | TalkNet outputs face numbers, source time, pixel boxes, and annotations in AVI format. |
| Verification Formal Proof | `check_lean_proof` | Lean 4.9 checks compilation, specifies proposition types and axiom dependencies. |
| Generating formal proof | `generate_lean_proof` | Gödel proposed proving that Lean independently verifies propositions and axioms. |
| Replay robotic arm observation | `preview_robot_actions` | SmolVLA generates action previews from recorded images, joint states, and instructions. |
| Check before mechanical arm operation on site | `check_smolvla_rollout` | Enumerate serial ports, check LeRobot, models, and calibration files. |
| Time Series Prediction | `forecast_series` | Default: Chronos-2. Optional: TimesFM 3.0. Outputs three quantile levels and the latest observation baseline. |
| Pairing device retrieval and retrieval of originals | `search_linked_mac`, `fetch_linked_mac` | Optional Omni. Query a configured Mac, and copy the allowed hits to the local directory. |
| Common short text and screenshot Q&A | `local-lfm` ’s `extract_fields`, `summarize`, `inspect_image` | LFM Fast is always present, LFM Vision is loaded on demand. |

The PDF page number starts from 1. Images use page 1. The document bounding box uses the top-left corner as the origin, using normalized coordinates `[x0, y0, x1, y1]`. SAM3 and TalkNet use pixel bounding boxes. Time is measured in seconds, with the start point being the beginning of the original file. The speaker numbers in MOSS are valid only for a single recording.

<a id="安装"></a>
<a id="installation"></a>
## Quick start

Requires Apple Silicon, macOS 26 or later, Xcode or Command Line Tools with the macOS 26.4 or later SDK, and `uv`. The default installation includes Apple’s native tools, LFM Fast, and LFM Vision. The three GGUF files total approximately 7.31 GB. Please reserve at least 20 GB of disk space for dependencies, downloads, and background services. Service usage requires `127.0.0.1:8080`. Apple Intelligence, Speech, and Translation use separate system settings and language assets. Add `zh-CN` to the install command if you need Mandarin Speech.

1. Prepare the toolchain. When the Command Line Tools are not yet installed, run `xcode-select --install` first. After completing the system installation window, proceed. Use the following command to verify the environment.

   ```sh
   uname -m
   sw_vers -productVersion
   xcrun --sdk macosx --show-sdk-version
   uv --version
   ```

   `uname -m` should be `arm64`, and the SDK should be 26.4 or newer. When `uv` has not been installed, follow the official instructions to install it and restart the terminal. [uv install](https://docs.astral.sh/uv/getting-started/installation/)

2. Clone the project and enter the directory. Save the repository in a fixed location, and the client will start MCP from this path.

   ```sh
   git clone https://github.com/SiyiHuang/cairnkite-release.git Cairnkite
   cd Cairnkite
   ```

3. Check the ports and install the default scheme.

   ```sh
   lsof -nP -iTCP:8080 -sTCP:LISTEN
   bin/install default en-US
   bin/lfm status
   ```

   The first command returns an empty result when the port is idle. If a service already exists, confirm its purpose before proceeding. If Cairnkite already runs the LFM service, the installer checks its LaunchAgent and reuses weights that match the pinned SHA-256 hashes. The installation can be run again, and interrupted model downloads will be resumed. Fast runs continuously, and Vision is loaded when called. The first start-up requires waiting for the service to be ready. During this time, `bin/lfm status` can be run again. The normal model list includes at least `lfm-fast` and `lfm-vision`.

   Use `bin/install core` to install Apple frameworks only. Add Speech languages with commands such as `bin/install speech ja-JP`. Pass `--reuse-from` to reuse verified LFM downloads. [LFM maintenance](backends/lfm/README.md#maintenance)

4. Run default acceptance. Samples are from synthetic materials in the repository.

   ```sh
   python3 tests/planner.py
   .runtime/mcp/bin/python tests/codex_specialists.py
   .runtime/mcp/bin/python tests/smoke.py
   bin/lfm verify --profile default
   ```

   The native smoke test prints `Smoke test passed.` on success. The LFM check covers extraction, null fields, summaries, concurrency, long context, and image questions. It exits successfully and writes `backends/lfm/logs/verification.json`. After Apple Intelligence and language resources are ready, it can be run again with `.runtime/mcp/bin/python tests/smoke.py --apple`.

<a id="接入-codex-和-claude-code"></a>
## Connect Codex and Claude Code

Install the required client first, so `codex --version` or `claude --version` can be executed in the same terminal. Codex uses `codex login` for login, and Claude Code uses `claude auth login` for login. Calling the cloud main model requires the corresponding account permissions. [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) · [Claude Code installation](https://code.claude.com/docs/en/quickstart)

When both sets of clients are installed, run the following command in the project root directory.

```sh
bin/register
bin/register --check
codex mcp get local_specialists --json
codex mcp get local-lfm --json
claude mcp get local_specialists
claude mcp get local-lfm
```

When only one client is connected, use `bin/register codex` or `bin/register claude`, and run the corresponding `bin/register --check codex` or `bin/register --check claude`. Check to ensure both services point to `bin/serve` and `bin/lfm serve` of the current repository. The Claude Code check should also indicate that it is connected. The Codex-specific tool has a timeout of 360 seconds, and Claude Code uses user-level MCP configuration. If there is an old path conflict, handle it according to the [Client Migration Steps](docs/deployment.md#client-registration).

Start new `codex` and `claude` sessions respectively. If the client requires trust in the repository or approval of tools, verify the current path and follow the instructions provided. Paste the following synthetic checks in each session.

> Please actually call the status of local_specialists, then call plan_deployment with parameters feature="barcodes", execution="mcp", and verified_only=true. Then call extract_fields of local-lfm. The original text is “The telescope calibration is scheduled for July 21. Dana is the owner. The room is undecided.” The fields are owner (name of the responsible person), date (planned date), and room (determined room). Please report the tool’s results.

The selection result should be `barcodes`, and the field result should be `{"owner":"Dana","date":"July 21","room":null}`. Check the tool invocation records on the client to ensure both MCPs return successfully.

Prepare image acceptance samples in the project root directory.

```sh
cp tests/fixtures/observatory.png backends/lfm/inbox/observatory.png
```

Send the following prompt in each client.

> Please call the `inspect_image` function of local-lfm, with `filename="observatory.png"` and `question="What is the code for the left bench? Return only that code."`. Please report the number returned by the tool.

LFM Vision should return the left bench code `ORBIT-741`. You can remove the staged `backends/lfm/inbox/observatory.png` after the test. [Verification results](docs/verification.md)

## Optional backends

`bin/plan` and MCP’s `plan_deployment` return the candidate, permission, installation commands, and acceptance methods corresponding to the task. Select them and then run the corresponding installation commands.

```sh
bin/install paddle
bin/install moss
bin/install qwen
bin/install digup
bin/install omni
```

The `all` install target includes `core`, `paddle`, `moss`, and `omni`. Run offline redaction with `bin/redact`. [Full deployment guide](docs/deployment.md)

When using DigUp, run `bin/local index-digup <directory>` for the specified directory, and add `--code` to the code index. When using Omni, first run `bin/install omni`, start Omni, and create an index for the authorized directory. The following example adds the synthetic fixture directory prepared for default acceptance to Omni.

```sh
"$HOME/Applications/Omni.app/Contents/Helpers/omni" add_source "$HOME/LocalSpecialists/demo"
```

## Examples

Put the material to be processed into `~/LocalSpecialists`, and then specify the absolute path and task on the client. For example:

> Use `local_specialists` ’s `document` to read page 2 of the PDF I specified. First, use `auto` to extract it. If the relationship between table columns is unclear, use `paddle` to run it again. Indicate the source page number when answering, and keep the fields where there are discrepancies between the two results.

> Use the `transcribe` `moss` backend to transcribe the recording I specified. Summarize the respective positions of the two speakers, with the original words and time intervals for each.

> Use `search` to search for information in the Omni index directory I specified. First, list the 3 most relevant items and location details, then check the segments that support the conclusions.

`document` Process 1 page at a time. `transcribe` Receive single audio files that do not exceed 30 minutes. Long audio files for MOSS and Qwen may reach the generation limit. Check `may_be_truncated` and the last timestamp, and split the original file as needed. After segmentation, the speaker numbers for each segment need to be rechecked.

If the result exceeds `max_chars`, the service returns a preview and `result_id`. Use `read_evidence` and `next_offset` to continue reading the full JSON. The complete result is stored in `.runtime/results`.

<a id="文件和网络范围"></a>
## File and network scope

The file tool only accepts input within `~/LocalSpecialists` by default. Users can create `.runtime/config.json` and set `allowed_roots` as an absolute directory array that is allowed. The service resolves symbolic links and checks the target path. Both Omni and DigUp need to create an index for the selected directory.

```json
{
  "allowed_roots": ["~/LocalSpecialists", "/absolute/path/to/another/approved-folder"]
}
```

MCP uses stdio. Paddle starts a temporary page-recognition process on loopback and stops it when the task ends. Omni uses a local Unix socket. Installation downloads dependencies and weights. Hosted clients can receive tool arguments and results. For local-only work, run `bin/local <tool>`, use an upstream local command, or start an offline LFM-backed session. [Offline specialist tools](docs/deployment.md#offline-specialists)

Omni code is licensed under Apache 2.0, while Jina is licensed under CC BY-NC 4.0. The repository only distributes deployment code, dependency lists, and synthetic samples. The source of the licenses, permissions, and versions can be found in [Dependency Record](dependencies/README.md).

## Verification and Troubleshooting

1. Run the decision tree and native acceptance.

   ```sh
   python3 tests/planner.py
   .runtime/mcp/bin/python tests/codex_specialists.py
   .runtime/mcp/bin/python tests/smoke.py
   bin/lfm verify --profile default
   ```

2. Install the Apple Speech resources. When using Omni’s additional validation, wait for its synthesis directory to complete indexing.

   When Apple Intelligence is ready and the corresponding language resources are installed, `.runtime/mcp/bin/python tests/smoke.py --apple` can be used. Actual measurements show English transcription, English-to-Chinese translation, and Apple Foundation Models.
3. Run the corresponding acceptance test for the installed model.

   ```sh
   .runtime/mcp/bin/python tests/smoke.py --full
   .runtime/mcp/bin/python tests/smoke.py --expanded
   .runtime/mcp/bin/python tests/smoke.py --text-models
   .runtime/mcp/bin/python tests/smoke.py --digup
   ```

   Verified samples, clients, and current gaps are available in [Local Acceptance Record](docs/verification.md).

- When the client cannot find MCP, first run `bin/register --check` in the current repository. If it is an old path left by migration, use `mcp get` of the corresponding client to record startup parameters and custom settings, then only process entries with reported conflicts. After running `bin/register`, review the results. For detailed steps, see [Client Migration](docs/deployment.md#client-registration).
- `status` report `appleIntelligenceNotEnabled` when, `focus_text` cannot be generated. Vision, Speech, and Translation use separate system frameworks.
- When Apple Speech lacks language resources, run `bin/install speech <locale>`. If dealing with multi-person recordings where the original language is uncertain, you can try MOSS.
- When Omni shows no results, use `omni list_sources` to check the number of directories and indexes. macOS access restrictions may prevent Omni from reading the directories in 「Documents». The material to be indexed can be placed in `~/LocalSpecialists`.
- When Spotlight has no results, use `mdls` to check if the file has been added to the system metadata index. Omni uses a separate index.
- When the Paddle or MOSS call fails, check the local log path in the error message. Complex pages and long recordings take longer to process.

## Remove client registrations

```sh
codex mcp remove local_specialists
claude mcp remove local_specialists --scope user
codex mcp remove local-lfm
claude mcp remove local-lfm --scope user
```

To remove the managed LFM service, see the maintenance guide. [LFM maintenance](backends/lfm/README.md#maintenance)

## License

The project code and the original synthesized samples in this repository are licensed under the MIT License. The downloaded models, third-party components, and Apple system services are subject to their respective upstream terms. [MIT License](LICENSE) · [Dependencies and Model Licenses](dependencies/README.md)
