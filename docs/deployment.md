# Deployment and tool selection

[简体中文](deployment.zh-CN.md)

Run `bin/plan` in the root directory of the repository to view the decision tree. Select the branch that is closest to the desired output, and then add hard requirements. The selection tool can be run using Python 3.10 or a newer version before installation. The built-in inference backend requires Apple Silicon and macOS 26 or later.

| Task | First, determine the output | Select example |
| --- | --- | --- |
| Document | Original text, regional coordinates, table structure, independent OCR or candidate scores | `bin/plan complex-layout --require formula_markup` |
| Audio | Segment times, speaker labels, word times, transcript alignment, streaming input, or separated audio | `bin/plan speaker-transcript --execution mcp` |
| Search | File name, semantic matching, code, cross-Mac or image-text optimization | `bin/plan semantic-search --use commercial` |
| Text | Translation, fixed terms, fields, privacy markers or routing | `bin/plan glossary-translation --execution local` |
| Images and videos | Active speaker, object masking, repair, relative depth or native action | `bin/plan restore-video --require upscale_video` |
| Other tasks | Numerical prediction, Lean proof, or robotic arm motion | `bin/plan forecast --use production` |

`--execution mcp` Requires MCP that has been integrated into the repository. `--execution local` Requires native commands with documented records. `--verified-only` Requires the route and specified capabilities to have been tested in practice. The output still lists the excluded candidates and reasons.

`--profile default` View the default route. `--profile optional` Query specific options. `plan_deployment` Using the same name `profile` parameter. You can combine profiles and output requirements, for example `bin/plan scan --profile optional --require table_structure`.

When preparing another Mac, use `--machine arm64 --macos 27.2 --disk-gib 100 --memory-gib 24` to set the target. MCP’s `plan_deployment` accepts the same set of `target` fields, `machine`, `macos`, `disk_gib`, and `memory_gib`. When the target is explicitly specified, the installed state of this machine is not involved in sorting.

The weight of LFM depends on the fixed version file list. Default deployment also counts towards the permanent Fast and applicable visual components. When planning `focused-review`, the 24 GiB target will be selected as Q4. There are no candidates for the 16 GiB target under the current standard configuration, and the 32 GiB target can be chosen as Q8. The weight is merely a minimum memory requirement. Actual operation also requires space for context, processes, and macOS.

When selecting a semantic or code index from existing data for this machine, run `bin/plan semantic-search --use personal --folder "$HOME/LocalSpecialists/demo"`, or pass the absolute `folder` of the approved directory to `plan_deployment`. The index selection will prioritize the indices already ready in the directory, and `folder` will be placed in the returned `search` parameter. The document index and code index of DigUp are checked separately. Omni is only marked as ready when the App is running and reports that the directory has a completed non-empty index. The check only reads the index status, and after the directory content changes, it is refreshed according to the appropriate formula. [DigUp CLI](https://github.com/ARahim3/DigUp) · [Omni CLI](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

| Marking | Meaning |
| --- | --- |
| `verified` | The project has passed the sample acceptance at the local machine with the specified output. It is subject to the acceptance criteria of each candidate. |
| `integrated` | There is already a call entry in this repository, but there are still material, system resources, or feature acceptance conditions to be met. |
| `upstream` | Upstream provides the route. Follow the fixed version, trial run, and record results according to the corresponding chapters. |
| `installed` | Local files or known system resources are ready. The actual path and input still need verification. |
| `needs_setup` | Need to download system assets, prepare indexes, or confirm software configuration. |
| `trial_required` | Suitable for entry into the upstream trial run. |

Within the task, the selection tool prioritizes routes that meet the criteria and are ready on the local machine, and then suggests candidates in the order of the decision tree. The result `question` indicates that permissions or hardware information will affect the next step. In commercial or production scenarios, known restricted weights and items to be verified are filtered out. `permissive` means that no such restrictions are recorded for that route, and the system framework still applies the Apple software terms. When data must be kept strictly on the local machine, `bin/local` or a command from the upstream local machine is used, and the output is reviewed on the local machine.

## Install and register

```sh
bin/install default
bin/register
bin/register --check
.runtime/mcp/bin/python tests/smoke.py
```

`bin/install default` requires `uv`, Swift 6, and macOS 26.4 or later SDKs. Xcode or Command Line Tools can provide the compilation environment. The country code following `default` will install the corresponding Apple Speech language resources. When using only the CLI, client registration can be skipped. The parameters of the specialized tool’s JSON can be passed to `bin/local <tool>` via standard input. The LFM tool uses `bin/lfm local <tool>`. Files are stored in `~/LocalSpecialists` or the directory explicitly selected in the configuration. The examples use synthetic materials prepared from test scripts.

<a id="client-registration"></a>
### Moving a checkout

Run `bin/register --check` in the new repository path. It will check the startup commands and parameters for the installed backend configurations of both clients. The parameter-free `bin/register` will check all existing entries with the same name before adding a new one. In case of conflicts, use `codex mcp get <name> --json` or `claude mcp get <name>` to understand the existing paths, parameters, and scopes, and then retain the required custom timeout, environment, and permission configurations. [Codex MCP Configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP Scope](https://code.claude.com/docs/en/mcp#mcp-installation-scopes)

If it is confirmed that the entry belongs to an old work tree, the startup path can be changed directly within the original configuration scope. You can also use `codex mcp remove <name>` or `claude mcp remove <name> --scope <scope>` to remove the entry, then run `bin/register` from the new path to restore the required custom settings. In the new session, try `local_specialists.status` and `local-lfm.extract_fields` separately to confirm the selected server and on-site results. [Codex MCP CLI](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP CLI](https://code.claude.com/docs/en/mcp)

## Liquid AI LFM

Default configuration installs Fast and Vision. llama.cpp uses Apple Silicon via Metal, listens to `127.0.0.1:8080`. `bin/lfm status` to view models, `bin/lfm verify --profile default` to verify the default configuration. `bin/register` registers when the LFM environment is established as well, `local-lfm`. [Runtime and commands](../backends/lfm/README.md) · [LFM Open License](https://www.liquid.ai/lfm-license)

<a id="lfm-fast"></a>
### LFM Fast Summary and Fields

`bin/install default` or `bin/install lfm-fast`. Two clients call `local-lfm.extract_fields` or `local-lfm.summarize`. The local command receives JSON parameters from the same tool.

```sh
printf '%s\n' '{"text":"Marina inspected the prism.","fields":{"owner":"Name of the person who inspected it"}}' | bin/lfm local extract_fields
```

Check that `owner` is `Marina`. Run `bin/lfm verify --profile default` to test missing fields, rescheduling, and instructions embedded in the source text.

<a id="lfm-vision"></a>
### LFM Vision Static Image Q&A

`bin/install default` or `bin/install lfm-vision`. Actively store the PNG or JPEG into `inbox/` used by LFM MCP. Two clients call `local-lfm.inspect_image`, with the parameter being the file name and issue. The acceptance script reads values from the combined screenshots containing system status numbers, while checking for directory overflow errors. OCR, tables, and original image positioning can be done using Apple Vision document tools.

<a id="lfm-tools"></a>
### LFM Tools Function Call

`bin/install lfm-tools`. In the shell tool of any client, pass the JSON requests for `messages` and `tools` via stdin to `bin/lfm chat lfm-tools`. Extract the name and parameters from `choices[].message.tool_calls`, verify them by the executor, invoke them, and then return the results. After the tool call ends, explicitly instruct the model to respond based on the results, and send `tool_choice="none"`. `bin/lfm verify --profile all` uses the inventory tool with interference options to verify the selections, parameters, and finalization.

<a id="lfm-reason"></a>
### LFM Reason Review & Local Agent

`bin/install lfm-reason`. Two common clients can pass the text and review questions to `local-lfm.review`. For full-native client testing, use `bin/lfm codex` and `bin/lfm claude`, and use `bin/lfm verify_clients` for verification. The review samples include the excess resources after addition. Tool invocation is based on isolated client logs and correct results.

<a id="offline-specialists"></a>
#### Offline Codex and Claude Code dedicated tools

Run `bin/install core` first. When using optional backends such as Lean and PaddleOCR, install them according to their respective sections. `--with-specialists` should be placed after `codex` or `claude`, and it loads `local_specialists` for the current session.

```sh
bin/lfm codex --with-specialists
bin/lfm claude --with-specialists
```

For example, let any client use the `barcodes` backend with `local_specialists.document` to read the QR codes under `~/LocalSpecialists`. It is also possible for Codex to limit the MCP of this session to a single tool.

```sh
bin/lfm codex --with-specialists exec --strict-config --ephemeral \
  -c 'mcp_servers.local_specialists.enabled_tools=["extract_apple_fields"]' \
  'Use extract_apple_fields to extract the name and date from: Remi booked the lab for October 31.'
```

Codex connects existing LFM services via temporary loopback ports. Lean and PaddleOCR are delegated to their respective worker processes via session-specific Unix sockets. The offline Codex writes tool outputs to `backends/lfm/.state/codex-local/specialists/artifacts/`. The next tool can directly use the returned file path. For example, use `synthesize_speech` to generate a WAV, and then have `classify_sound` read that WAV. When the result is truncated, use `read_evidence` and the returned `result_id` to continue reading. The regular video repair of MLX-Gen shares a running lock within the same project. [Codex MCP configuration](https://learn.chatgpt.com/docs/config-file/config-reference)

The self-provided Core ML model is used in offline Codex with the compiled and approved `.mlmodelc`. Apple’s compilation API requires writing to the system temporary directory, and `native/.build/release/apple-specialists compile-coreml <absolute-model-path> <absolute-output.mlmodelc-path>` can run outside of offline sessions. Then, the compiled output can be handed over to `predict_coreml`. Tasks that need to be written to other directories can directly use `bin/local`.

<a id="lfm-quantization"></a>
### LFM Q4 Comparison

Install `lfm-fast-q4` or `lfm-reason-q4`, and send the same JSON request via stdin to `bin/lfm chat <model-id>`. Reason Q4 can also be used with standard MCP `local-lfm.review` or `bin/lfm local review`, with parameters being `text`, `question`, and `model="lfm-reason-q4"`. `model` is omitted, and Reason Q8 will be used instead. Compare the accuracy, first-load latency, hot-running time, and memory for the same input set, and then decide whether to choose Q4.

## Document

<a id="pdfkit"></a>
### Apple PDFKit

Install `core`. Call `document`, specify the PDF and `backend="auto"`. Check the model, number, and page number on the first page with the text layer. Return `pdfkit` to indicate that the text layer has been obtained. For the image page, `auto` will switch to Vision. [PDFPage document](https://developer.apple.com/documentation/pdfkit/pdfpage/string)

<a id="vision"></a>
### Apple Vision OCR and Document Recognition

Install `core`. Call `document`, and use `backend="vision"` to force page-by-page OCR. Check `ORBIT-741`, tables, and normalized coordinates using the combined PDF of page 2. Verify multi-column order and cells using a real sample page. [Vision Document Recognition](https://developer.apple.com/documentation/vision/recognizedocumentsrequest)

<a id="paddle"></a>
### PaddleOCR-VL 1.6 and PP-DocLayoutV3

Run `bin/install paddle`. Call `document`, and use `backend="paddle"` to process single-page content that requires formatting. Check the category, box, and text in `blocks`. The `latex` of formula blocks provides expressions without the outer mathematical delimiters, while `text` preserves the original output. The formula numbers are in separate blocks. In some composite examples, one side of the delimiters may be missing, and `latex` can be used during rendering to add delimiters manually. The offline client starts with `--with-specialists`, and is delegated to the Paddle worker process via the local Unix socket. Use `tests/fixtures/formula-page.png` to verify the limits, denominators, integral square roots, and coordinates. [Paddle Apple Silicon Installation Documentation](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-Apple-Silicon.html)

<a id="minicpm"></a>
### MiniCPM-OCR 1.0

Run `bin/install minicpm`. Use `document` ’s `backend="minicpm"` to generate a second set of text for the same page. Verify `ORBIT-741`, `FILTER-193`, and table times using the synthetic scan page. The formula page can simultaneously check expressions and numbers. The tool returns the entire page text and the generation limit markers. If block coordinates are required, select Vision or Paddle. [OpenBMB model card](https://huggingface.co/openbmb/MiniCPM-OCR-1.0)

<a id="jev"></a>
### MiniCPM-OCR Jev

Run `bin/install jev`. Send the original cropping, candidate text, and the rendering image of the text to `score_ocr`, along with `original_path`, `text`, and `rendered_path`. Verify the scores using the upstream text, formulas, and table examples, and then compare the correct and incorrect candidates with the similar samples marked by oneself. The project uses upstream text error examples for reasoning. Before batch filtering, calibrate according to font and rendering methods. No threshold is set in the repository. [OpenBMB Input and Acceptance Instructions](https://github.com/OpenBMB/MiniCPM-OCR/blob/main/docs/minicpm_ocr_jev_tutorial_en.md)

<a id="barcodes"></a>
### Apple Vision barcode detection

Install `core`. Use `document` ’s `backend="barcodes"` to read known QR codes or regular barcodes. Verify `codes[].payload` and `bbox`. The encoding value is processed according to the input data. [Vision barcode interface](https://developer.apple.com/documentation/vision/detectbarcodesrequest)

## Audio

<a id="apple-speech"></a>
### Apple SpeechTranscriber

Run `bin/install speech en-US` or `bin/install speech zh-CN`. Use `status` to confirm the `speech_asset` of the required region code as `installed`. Use `transcribe` ’s `backend="apple"` to check the `copper prism`, segments, and time of the synthetic recording. It is also possible to approximate the speaking segment to locate the relevant sections. [SpeechTranscriber](https://developer.apple.com/documentation/speech/speechtranscriber)

<a id="whisper"></a>
### Offline transcription with Whisper

Install FFmpeg and make it available on PATH. From the project root, run `bin/install core` if needed, then `bin/install whisper`. The installer builds whisper.cpp v1.9.5 with Metal and downloads the pinned Whisper large-v3-turbo Q8_0 and Silero VAD v6.2.0 weights, about 835 MiB in total. It verifies the source archive and both weights with SHA-256. If you already have both exact GGML files, run `bin/install whisper --reuse-from /path/to/models` to verify and copy them into Cairnkite.

After `bin/register`, Codex and Claude Code can use `local_specialists.transcribe` with `backend="whisper"`. Provide an approved absolute audio `path`. Omit `language` for automatic detection or pass a Whisper code such as `en` or `zh`. The result contains text and segment timestamps in seconds. Each request accepts up to 30 minutes of audio. Split longer material into clips before calling the tool and add each clip's start offset when combining timestamps. For speaker labels, use MOSS. For word alignment against an edited transcript, use ForcedAligner.

Run the smoke test to copy the synthetic meeting into the approved demo folder, then try the same JSON used by both MCP clients.

```sh
.runtime/mcp/bin/python tests/smoke.py
printf '{"path":"%s","backend":"whisper","language":"en"}\n' "$HOME/LocalSpecialists/demo/meeting.wav" | bin/local transcribe
bin/plan whisper-transcript --verified-only
```

Expect four segments containing `copper prism` and the telescope and spectrometer times. Check a pure-silence clip for an empty segment list. Decoding and inference run with network access denied. [whisper.cpp v1.9.5](https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.5) · [Pinned Whisper weights](https://huggingface.co/ggerganov/whisper.cpp/tree/5359861c739e955e79d9a303bcbc70fb988958b1) · [Pinned Silero VAD weights](https://huggingface.co/ggml-org/whisper-vad/tree/9ffd54a1e1ee413ddf265af9913beaf518d1639b)

<a id="moss"></a>
### MOSS-Transcribe-Diarize

Run `bin/install moss`. Use `transcribe` ’s `backend="moss"` to check the two-person synthesis sample, and return `S01` and `S02`. Check `may_be_truncated`, speaking end times, and overlapping speeches on the actual long recording. The IDs of the same person may vary across files. [MLX adapts to](https://github.com/vanch007/mlx-MOSS-Transcribe-Diarize)

<a id="qwen-asr"></a>
### Qwen3-ASR 0.6B and word-level time

Run `bin/install qwen`, and install the 0.6B recognizer and aligner simultaneously. Use `backend="qwen"` with `transcribe` to process the synthetic recording. Check `text`, `segment_unit`, and the corresponding times. Alignment may normalize numbers or punctuation.

Start with 16 kHz WAV. Other formats require `ffmpeg`. If an anonymous speaker is needed, try [MOSS](#moss). [MLX transcription and timestamp instructions](https://github.com/moona3k/mlx-qwen3-asr#word-level-timestamps)

<a id="qwen-large"></a>
### Qwen3-ASR 1.7B and word-level time

Run `bin/install qwen-large`. Use `transcribe` ’s `backend="qwen-large"` to process the same audio segment. It shares the aligner with 0.6B. 1.7B has a larger weight, allowing comparison of transcriptions and processing time using the same set of terms and accent samples. [1.7B 8-bit weight](https://huggingface.co/moona3k/mlx-qwen3-asr-1.7b-8bit)

<a id="qwen-align"></a>
### Qwen3-ForcedAligner 0.6B

Run `bin/install qwen-align`. Call `align_audio`, and use `path` and `text` to provide the original audio and proofed version. `language` should be filled with `English` or the language supported by the upstream team. The maximum length of a single audio file is 120 seconds. Determine the start and end positions of the trial audio, then combine it with longer subtitles. This method uses known text. If there are discrepancies, first check whether the language and recording match. [Qwen Official Aligner](https://github.com/QwenLM/Qwen3-ASR)

<a id="speech-detector"></a>
### Apple SpeechDetector

Currently, Apple uses this module to reduce power consumption during transcription. Use `bin/plan speech-detector-probe` to view interface diagnostics. `transcribe` ’s `backend="activity"` retains the native probe, but no results are returned for the audio samples. Apple’s documentation states that the result stream currently only reports errors. When a time range is required, use Silero VAD, Apple transcription, or Sound Analysis. [SpeechDetector result stream](https://developer.apple.com/documentation/speech/speechdetector/results)

<a id="silero-vad"></a>
### Silero VAD

Preparation: `ffmpeg`, then run `bin/install silero` and `bin/register`. Codex, Claude Code, or `bin/local transcribe` use `backend="silero"` and absolute audio path `path`. The model processes the first track as a 16 kHz mono signal, up to 30 minutes long, and returns the number of seconds in the audible range. The current parameters are for general speech. Speech shorter than 250 milliseconds will not be returned. Use the transcription method when needed for speakers, text, or word-by-word timing. [Silero sequence ONNX release](https://github.com/snakers4/silero-vad/releases/tag/v6.2.2)

<a id="qwen-stream"></a>
### Qwen3-ASR Streaming CLI

Run `bin/install qwen`. `bin/stream-asr` reads 16 kHz mono, 16-bit little-endian PCM from stdin, and outputs one line of NDJSON per round. `text` is the current entire text, and `stable_text` is the stable prefix. When the display is updated, the old version is replaced with a new one using `text`. After input ends, `final` and the revision count are returned. The following command can be used to replay the synthetic recording based on the real-time clock.

```sh
ffmpeg -hide_banner -loglevel error -re -i tests/fixtures/meeting.wav \
  -ac 1 -ar 16000 -f s16le - | bin/stream-asr --language English
```

The Codex and Claude Code can replay files up to 30 minutes long in the `transcribe` `backend="qwen-stream"` playback approval directory. After completion, one `partials`, `metrics`, and final version can be obtained. To receive real-time transcriptions item by item, use the local PCM pipeline. The following command collects data from the specified microphone via AVFoundation, and the final version is provided after completion. First, initiate the capture in an app authorized by macOS. Fill in the device name with the actual name on the local machine.

```sh
ffmpeg -nostdin -hide_banner -f avfoundation -i ':MacBook Pro Microphone' \
  -t 5 -vn -ac 1 -ar 16000 -f s16le - | bin/stream-asr --chunk-seconds 1 --language English
```

The local device hears the synthesized sentences played by the speaker via its built-in microphone. The first set of results recognizes the target name, the second set includes a number, and the final version also contains a number. [Streaming interface](https://github.com/moona3k/mlx-qwen3-asr#streaming)

<a id="sam-audio"></a>
### SAM Audio small

Run `bin/install sam-audio` to install fixed MLX weights and T5 encoder. Two clients and `bin/local separate_audio` receive authorized local audio paths and `description`, such as `"human speech and spoken conversation"`. Each segment is up to 30 seconds long, producing two 48 kHz WAV files. Use samples from known two sound sources to verify the target track, residual track, crosstalk, and distortion. [MLX model card](https://huggingface.co/mlx-community/sam-audio-small) · [Meta weights and parameters](https://huggingface.co/facebook/sam-audio-small)

<a id="kokoro"></a>
### Kokoro 82M

Run `bin/install kokoro` to install the pinned MLX weights, language frontend, and two voices. Call `synthesize_speech` with `backend="kokoro"` and use `voice="af_heart"` for English or `voice="zf_xiaobei"` for Mandarin. The baseline speed is `words_per_minute=175`. Other values scale proportionally. Check the voice, content, and 24 kHz WAV output. Test long and mixed-language text separately. [Kokoro MLX guide](https://github.com/Neywa-Labs/mlx-audio/blob/main/docs/models/tts/kokoro.md) · [Original model and license](https://huggingface.co/hexgrad/Kokoro-82M)

<a id="apple-tts"></a>
### macOS Speech Synthesis

Run `bin/install core` and `bin/register`. The Codex and Claude Code call `local_specialists.synthesize_speech`, and the terminal can pass the same JSON parameters to `bin/local synthesize_speech`. For example `{"text":"A technician in Shanghai checks the instruments.","voice":"Tingting"}`. Use `say -v '?'` to check the system sound profile, and adjust `words_per_minute` to control the speed. The result provides the local 22.05 kHz WAV path and duration, which is saved in `.runtime/artifacts/`. [Apple system sound profile](https://support.apple.com/guide/mac-help/mchlp2290/mac)

<a id="sound-analysis"></a>
### Apple Sound Analysis

Run `bin/install core` and `bin/register`. Call `local_specialists.classify_sound` in either client, or pipe the same JSON to `bin/local classify_sound`. Supply `path`, with optional `threshold` and per-window `limit`. Results include labels, confidence scores, and potentially overlapping windows. The synthetic fixture returned `speech`. Calibrate thresholds with representative background audio. [Apple sound classification](https://developer.apple.com/documentation/soundanalysis/classifying-sounds-in-an-audio-file)

## Search

<a id="omni"></a>
### Omni and Jina v5 Omni Small

Run `bin/install omni` to download and verify the App and fixed Small weights. Use `add_source` via Omni CLI to add to the specified directory, and use `list_sources` to check the progress. Use `search` and `backend="omni"` to search for telescope calibration, and verify the results against the synthesis guide. The actual results include text lines and PDF pages, and short audio/video return file paths. Use DigUp if a media timecode is required. The weights are used under CC BY-NC 4.0. Regular Agent sessions are connected via MCP to Omni’s local Unix socket. [Omni usage and index:](https://github.com/hanxiao/omni-macos)

Start Omni for the offline session first, then run one of the following commands. `--with-omni` opens the selected Omni Unix socket. By default, the standard socket of Omni is used. An isolated instance can be used by specifying a absolute path with `LFM_OMNI_SOCKET`.

```sh
bin/lfm codex --with-omni --with-specialists
bin/lfm claude --with-omni --with-specialists
```

<a id="digup"></a>
### DigUp and EmbeddingGemma 2

Run `bin/install digup` to install the signature command-line components and the verified EmbeddingGemma 2 weights. No App needs to be launched. When building the index, only the authorized directory should be provided. It is recommended to use project-synthesized samples first.

```sh
.runtime/mcp/bin/python tests/smoke.py
bin/local index-digup "$HOME/LocalSpecialists/demo"
jq -nc --arg folder "$HOME/LocalSpecialists/demo" \
  '{folder:$folder,backend:"digup",query:"ORBIT-741 11:40"}' | bin/local search
.runtime/mcp/bin/python tests/smoke.py --digup
```

The result should point to `calibration.pdf`, page 2. Codex and Claude Code use the same `search` parameter. To query the code, run `bin/local index-digup --code <directory>` and pass `code=true` in the query. Re-run the corresponding index creation command after the directory content changes. The default semantic threshold is 2 standard deviations. If a rewrite query for a small index returns no candidates, use `min_semantic_z=1` to query again and check item by item. [DigUp Installation and Usage](https://github.com/ARahim3/DigUp) · [Google model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)

<a id="omni-pairing"></a>
### Omni across Macs

Two Macs are installed with Omni, and the index directories that each are willing to share are prepared. In the “File” menu of the application, select “Link a Mac”, compare the pairing codes between devices, and enable search and file reading as needed. First, use a composite file to verify the associated device, and determine the return and sharing scope when one end is turned off.

Merge the `omni_linked_macs` field into `.runtime/config.json`. Use a unique paired name or ID, and fill in the absolute directory of the other Mac. Calling `search_linked_mac` will send the query to the specified device, and results are returned based on these paths. The original index range for the peer search is determined by the shared settings of the peer Omni.

```json
{"omni_linked_macs":{"Studio":["/Users/me/LocalSpecialists/shared"]}}
```

```sh
printf '%s\n' '{"peer":"Studio","query":"Violet Sextant"}' | bin/local search_linked_mac
```

Codex and Claude Code can accept the same parameters. Offline sessions open the local socket in the same way as Omni above, and queries are sent from Omni to the selected paired device. The local version has been tested through pairing, querying, and file reading across two isolated application instances. Local area network discovery and behavior across two hardware devices are still under evaluation. [Omni CLI](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

<a id="omni-linked-copy"></a>
### Retrieve the original copy of the paired Mac

In the previous step, configure the two Macs and allow reading of files on the device where the files are located. `search_linked_mac` returns the permitted hits and their size. For the hits to be retained, call `fetch_linked_mac`, passing the same `peer`, `query`, and the full `path` of the hit. Omitting `output_folder` will create a separate subdirectory in the tool output directory for this copy, which is suitable for offline Codex. When specifying manually, choose a directory that is writable by the client, already exists, and within the allowed range on the local machine. The terminal can pass the same JSON to `bin/local fetch_linked_mac`, and both clients can call the same MCP tool. [Omni file retrieval](https://github.com/hanxiao/omni-macos/blob/v0.20.5/docs/CLI.md)

The tool checks the file read permissions for this hit and the other party. The file size reported by the index is up to 16 MiB, and it must match the actual number of bytes read from the Omni cache. Files with the same name in the directory will be retained. The tool returns the local path `path`, the original `remote_path`, the byte count, and `sha256`, allowing subsequent tools to read the local path. Omni also retains its own pull cache. When starting Omni with an independent data directory, the absolute cache path for this instance can be entered in `omni_link_cache_root` under `.runtime/config.json`. The physical dual-machine acceptance is pending. [Omni local cache implementation](https://github.com/hanxiao/omni-macos/blob/v0.20.5/App/Link/RemoteFiles.swift)

<a id="spotlight"></a>
### Spotlight File Name Search

Install `core`, and create a unique file name in the indexed directory of the system. Use `mdls` to verify the indexing, and then compare with `mdfind -onlyin "$PWD" -name <filename>` and MCP’s `search(backend="spotlight")`. If there is no match in the test directory of this project, use `rg --files` to locate the path. [Apple Spotlight Guide](https://support.apple.com/guide/mac-help/search-with-spotlight-mchlp1008/mac)

<a id="core-spotlight"></a>
### SpotlightSearchTool Owned App Index

Run `bin/install apple-spotlight` with macOS 27 and 27 SDK, and enable Apple Intelligence. This installation compiles a native assistant app with an independent identity. Use `search_apple_notes` or `bin/local search_apple_notes` to query JSON in the authorized directory, and pass in `path` and `question`. JSON is an array of short notes containing `id`, `title`, and `text`, with a maximum of 24 entries and 32 KiB.

Each query records this set of notes in the auxiliary app’s index, returns the original text in `matches`, and removes the index after completion. By default, `mode="answer"` is searched using the device model with `SpotlightSearchTool`. Descriptive issues will be tried to be rewritten into short keywords. Samples of seaside walking paths are matched using `ocean`. Check `matches` to verify the model response. If there is no match, the empty result is used. [Apple Natural Language Query Example](https://developer.apple.com/documentation/corespotlight/searching-indexed-content-with-natural-language)

<a id="core-spotlight-semantic"></a>
### Core Spotlight Semantic Retrieval

Use the same `bin/install apple-spotlight` XZ to install the auxiliary app, and in `search_apple_notes` or `bin/local search_apple_notes`, input `mode="semantic"`. `question` input the phrase to search for. `CSUserQuery` enable system lexical and semantic sorting, returning up to five `matches` original entries, `text` as `null`. If no matches are found on the first attempt of a new batch, try up to two more times to complete the index update. This mode directly calls Core Spotlight without starting a Foundation Model session. [Apple Core Spotlight Search API](https://developer.apple.com/documentation/corespotlight/building-a-search-interface-for-your-app)

Available to run `tests/fixtures/spotlight-notes.json` or `tests/smoke.py --apple` multiple times. `pastries made with tree nuts` found a note titled `Almond Nutmeg Cookies` on the local machine. The same query returns nothing when the semantics are disabled. `marine mammals` did not retrieve any seal notes. If missed recalls occur, try `mode="answer"` to have the device model rewrite the keywords. [Apple Core Spotlight Semantic Switch](https://developer.apple.com/documentation/corespotlight/csuserquerycontext/disablesemanticsearch)

<a id="jina-grep"></a>
### Jina Code Embeddings and jina-grep

Run `bin/install jina-grep`. In Codex or Claude Code, call `search_code`, provide the behavior description `query`, and the array of absolute paths of the identified UTF-8 source files `files`. The same request can be handed over to `bin/local search_code`. A maximum of 64 files, totaling 128 KiB, are returned, including segments, line numbers, and similarity scores. For repeated searches across the entire warehouse, a DigUp index can be created first. Known symbols can be used with `rg` or a language server. A weight of 0.5B is limited for non-commercial use. [Jina’s semantic code retrieval](https://github.com/jina-ai/jina-grep-cli#code-search) · [0.5B MLX weight](https://huggingface.co/jinaai/jina-code-embeddings-0.5b-mlx)

<a id="qwen-reranker"></a>
### Qwen3-VL-Reranker-2B

Run `bin/install qwen-reranker`, then pass `query` and up to 12 `candidates` to `rerank_visual`. PDF candidates use `path` and `page`, images use `path`, and candidates can also carry `text`. The output is sorted by relevance, and the `input_index` of candidates is retained. The local command is `bin/local rerank_visual`. [Official models and scoring method:](https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B)

First, use Omni, DigUp, or keyword recall to retrieve candidates, and then compare the rankings of the correct pages before and after fine-ranking using the same query. The MLX route uses an official template and the difference between yes/no logits to calculate the relevance score. The long edge of the image is limited to 1,344 pixels, and small text areas can be extracted separately.

Run `bin/install qwen-reranker-4bit` when space is limited, and set `precision="4bit"` when calling. The weight is approximately 1.78 GB, and BF16 is about 4.26 GB. The preferred option is the same in both samples, and the 4-bit score is lower. Re-set the score threshold based on your own materials. [MLX 4-bit weight](https://huggingface.co/mlx-community/Qwen3-VL-Reranker-2B-4bit)

## Text

<a id="apple-translation"></a>
### Apple Translation

Install `core`. In “System Settings → General → Language and Region → Translation Language”, download the two target languages. Use `native/.build/release/apple-specialists translation-status en zh-Hans` to confirm that `asset` is equal to `installed`. Call up `translate`, use `texts` for a set of short texts, `source_language="en"`, `target_language="zh-Hans"`. Check the number of output items and their meanings. This device uses English to simplified Chinese for verification. [Apple Offline Translation Settings](https://support.apple.com/guide/mac-help/mchldd8b3c15/mac) · [TranslationSession](https://developer.apple.com/documentation/translation/translationsession)

<a id="hy-mt"></a>
### Hy-MT2

Run `bin/install hy-mt`. Call `translate` via `backend="hy-mt"`. Use `glossary` when referring to terms. The key is the original word, and the value is the expected translation. Check the number of translated texts, `truncated`, and term matches. Batch output returns in the order of input. Long texts or subtitles are split into smaller batches, preserving the original ID, time axis, and term checks. 7B can be deployed separately according to official instructions and compared with 1.8B using the same corpus. [Example of Tencent model cards and terms:](https://huggingface.co/tencent/Hy-MT2-1.8B#hy-mt2-translation-task-instruction-examples-chinese-english-comparison)

<a id="natural-language"></a>
### Apple Natural Language

Install `core`, call `text_analysis`. Use text containing place names, person names, and emojis to check the language, part of speech, and built-in entities, and retrieve the positions using UTF-16 units. The availability of language or entity tags varies depending on the text and the system. [Natural Language](https://developer.apple.com/documentation/naturallanguage)

<a id="foundation-models"></a>
### Apple Foundation Models Short Text Q&A

Install `core`. Enable Apple Intelligence on compatible devices and wait for resources to become available. Use `status` to check `foundation_models` as `available`. Call `focus_text`, providing a short text with known facts and a location query, and check each sentence individually. The Swift approach for macOS 27.2.1 has been addressed using synthetic samples for the responsible person and date. [Apple Foundation Models](https://developer.apple.com/documentation/foundationmodels)

<a id="foundation-structured"></a>
### Apple Foundation Models Structured Generation

Run `bin/install core`, use `status` to confirm `foundation_models` as `available`. Codex and Claude Code can call `local_specialists.extract_apple_fields`, with parameters identical to the local CLI. Swift dynamic schema constraints fields. Fields that are omitted or left blank in the model are `null`. The tool checks that each non-empty value matches the continuous string in the original text. For values that require “confirmed”, context verification is still needed. Testing shows that Apple fills in “tentative” as a delivery method. LFM Fast is more stable for the project samples, so it remains the default. [Apple Swift Guided Generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation)

```sh
printf '%s\n' '{"text":"Marina owns the inspection. The budget is pending.","fields":{"owner":"Name of the person responsible","budget":"Confirmed budget amount"}}' | bin/local extract_apple_fields
```

Acceptance: `owner` corresponds to `Marina`, and `budget` corresponds to `null`. The system’s `fm` CLI and Apple Python SDK also provide structured paths. [Apple CLI and SDK](https://developer.apple.com/videos/play/wwdc2026/334/) · [Apple Python SDK](https://github.com/apple/python-apple-fm-sdk)

The structured extraction in this section uses Swift. After the machine-level clause process is completed in macOS 27 with `fm`, the device model can also be called using the terminal or the shell of the Agent. Use `fm respond --model system --no-stream --greedy 'Return only the code BASALT-814.'` to check local calls on this machine. When using Python callbacks, the local binding in the next section can be selected. [Apple CLI and SDK](https://developer.apple.com/videos/play/wwdc2026/334/)

<a id="apple-fm-python"></a>
### Apple Foundation Models Python Tool Callback

Run `bin/install apple-fm-python` to enable Apple Intelligence. The project uses the official 0.2.2 source package. It compiles the Swift-C binding directly using the current SDK to generate Python interfaces. This installation requires the native 26.5 and 27.2 Command Line Tools. The official `pip` build process requires a full Xcode.

Run the script of `import apple_fm_sdk` using `bin/apple-fm-python your_script.py`. Actual calls can utilize `LanguageModelSession` of the SDK, custom `Tool`, and `@generable`. The `lookup_apple_record` provided for the two Agents enables the system model to select a key from the JSON object in the configuration directory, and then Python returns the original value. The JSON file has a maximum size of 32 KiB and up to 32 keys. When knowing which records can be returned, pass `keys` to limit the range. `lookups` provides the actual call keys, hit status, and original values, while `text` is the explanation given by the model.

```sh
bin/plan apple-record-lookup --execution mcp --verified-only --json
printf '%s\n' '{"path":"/Users/me/LocalSpecialists/calibration.json","question":"Use read_record to get the service code for beacon_amber."}' |
  bin/local lookup_apple_record
```

Use `{"beacon_amber":{"service_code":762},"beacon_blue":{"service_code":481}}` as the acceptance content. Verify that `lookups` contains only the true values of required keys, and then compare with the model’s instructions. Codex and Claude Code pass the same parameters via registered MCP. [Apple Python SDK](https://github.com/apple/python-apple-fm-sdk) · [Apple Image Input API](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting)

<a id="apple-fm-image"></a>
### Apple Foundation Models Native Image Q&A

On macOS 27, use `xcrun --sdk macosx --show-sdk-version` to confirm that the 27 SDK is enabled, then run `bin/install apple-fm-python`. Check `status.apple_fm_attachments`, and then send `path` and `question` of the images from the authorized directory to `inspect_apple_attachment`. This process passes the images directly to the local system model as `ImageAttachment`. Use two images with only graphics and no text to verify colors and positions. When precise text and coordinates are required, use `document` and `backend="vision"`. [Apple’s native image input](https://developer.apple.com/documentation/FoundationModels/analyzing-images-with-multimodal-prompting)

<a id="gliner"></a>
### GLiNER2.5 multi-v1

Run `bin/install core`, `bin/install gliner`, and `bin/register`. Both clients call `local_specialists.extract_entities`. Pipe the same JSON to `bin/local extract_entities` in the terminal. Try `{"texts":["Dana inspects instruments in Seattle."],"labels":{"person":"person name","city":"city name"}}`. Each batch supports up to eight passages. Results include confidence scores and half-open Unicode code-point ranges. Use `[start:end]` to recover the original text. Check thresholds, spans, and misses on labeled data. [Fastino model card](https://huggingface.co/fastino/gliner2.5-multi-v1)

<a id="privacy-filter"></a>
### OpenAI Privacy Filter

Run `bin/install privacy`. The installer prepares model weights and the verified `o200k_base` vocabulary simultaneously. The terminal, offline Codex, and offline Claude Code can all use `bin/redact < input.txt > redacted.txt` to process files on the local CPU. The command first verifies the local vocabulary, and offline sessions continue to use network isolation on the client. The output path of offline Codex should be in its own state directory. One synthetic sample replaces names, dates, emails, and phone numbers, while another sample omits names. After checking the remaining sensitive information, decide which content can be output. When a span and category are required, set `TIKTOKEN_CACHE_DIR` on the local machine as the `.runtime/models/privacy/tiktoken` for the project, and then use `opf redact --checkpoint.runtime/models/privacy/original --device cpu --format json` to call the upstream entry point. [OpenAI OPF installation and command](https://github.com/openai/privacy-filter#how-to-use) · [Vocabulary and verification values](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py)

<a id="clef"></a>
### Cloudflare Clef-Flash

Run `bin/install clef` and `bin/register`. Codex, Claude Code, or `bin/local decide` receive `state`, `questions`, and optional `image_path`. Each question provides `instructions`. Binary questions use `type="binary"` to return scores for true or false propositions. Multiple-choice questions use `type="choice"` and a mapping from candidate names to descriptions. Scoring questions use `type="score"` and a list of descriptions from low to high, returning scores for each level and the expected score level starting from 0.

Fix the problem order and candidate definitions, compare the misclassification rates using annotated samples, and determine the review threshold on the holdout set. The publisher recommends 16 GB or more memory. [Clef original model](https://huggingface.co/Cloudflare/clef-flash) · [MLX 4-bit weights and running code](https://huggingface.co/mlx-community/clef-flash-4bit)

## Images and videos

<a id="talknet"></a>
### TalkNet-ASD

Preparation: `ffmpeg`, then run `bin/install talknet`. Input `path` via Codex, Claude Code, or `bin/local active_video_speakers`, followed by the segment duration `start` and segment seconds `duration`. Optionally use `device="mps"` or `"cpu"`. The result includes active tracks, source video time, pixel frames, and AVI files with audio annotations. The 360° material is converted to standard perspectives first. Off-screen speech, occlusions, and audio-video offsets require review of the footage segments. The code is MIT. The licensing of pre-trained weights for TalkSet and S3FD is not clear. [Mac compatibility and weight source:](https://github.com/nawta/TalkNet-ASD-py312) · [original project:](https://github.com/TaoRuijie/TalkNet-ASD)

<a id="sam3"></a>
### Segment Anything 3

Run `bin/install sam3` to install fixed BF16 weights and a tokenizer released along with the weights. Two clients and `bin/local segment_objects` use `path` and short object names, such as `prompt="a cat"`. `task="segment"` returns the PNG masks and pixel boxes for each object. `task="track"` processes videos up to 1080p pixels, lasting up to 30 seconds, and returns the annotated MP4 file along with boxes and numbers listed by sampling time. Time is converted from frame numbers and nominal frame rate. Numbers are associated based on box overlap. Occlusion and cutout require review. [MLX Model Card](https://huggingface.co/mlx-community/sam3-bf16) · [Meta Source Code and Licenses](https://github.com/facebookresearch/sam3)

<a id="apple-video-upscale"></a>
### Apple VideoToolbox Video Upscaling

Run `bin/install core` on macOS 26 or later, and prepare for `ffmpeg` and `ffprobe`. First, query the magnification supported by the system based on the input pixel width and height, such as `native/.build/release/apple-specialists video-scale-status 320 192`. The magnification is determined by the device and input size. The 320 × 192 resolution on this device supports 2x and 4x, while 1920 × 1080 returns an empty list. [Apple’s magnification interface is](https://developer.apple.com/documentation/videotoolbox/vtlowlatencysuperresolutionscalerconfiguration)

In Codex, Claude Code, or `bin/local restore_video`, enter `path`, `backend="apple"`, and `scale="2x"` or `"4x"`. The input processes SDR short videos. You can use `start_seconds` and `max_frames` to specify segments, and it returns the actual first-frame time, width, height, number of frames, frame rate, and number of audio tracks. The output is H.264 MP4. If there are audio tracks, the corresponding segments are encoded as AAC. `bin/plan upscale-video-4x` returns a 4x call parameter and size check prompt. [Apple video processing example](https://developer.apple.com/documentation/videotoolbox/enhancing-your-app-with-machine-learning-based-video-effects)

<a id="swiftvr"></a>
### SwiftVR

Preparation: `ffmpeg` and `ffprobe`. Run `bin/install swiftvr` and `bin/register`. Pass `path`, optional `start_seconds`, `max_frames`, and `seed` to Codex, Claude Code, or `bin/local restore_video`. The tool processes short clips up to 1080p pixels, returning MP4 files at the original resolution, frame count, frame rate, and number of audio tracks. SwiftVR processes frames according to `4n + 1`, and may cut off the tail. Higher resolutions or long videos can be tested directly using upstream commands. [SwiftVR parameters and actual measured](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md#swiftvr-one-step-restoration)

First, use reference short videos to compare motion, local details, frames, and audio tracks. After processing with SwiftVR, the SSIM values of the two degradation samples decreased compared to the references. The current fixed weight applies under the SwiftVR Research License. When making a selection, use `bin/plan restore-video --use research`. [Fixed weight license:](https://huggingface.co/H-oliday/SwiftVR/blob/a0b09461bd89847712dd91dbb4c63541b4693936/LICENSE)

<a id="seedvr2"></a>
### SeedVR2

Run `bin/install seedvr2` and `bin/register`. For static images, use `restore_image`, and pass in `path` and `scale="2x"`. For videos, require `ffmpeg` and `ffprobe`, using `restore_video` and `backend="seedvr2"`. First, use `scale="1x"` to check the number of frames, image, and audio tracks. The terminal can pass the same parameters to `bin/local restore_image` or `bin/local restore_video`.

The video enables the upstream zoom mode only when `scale="2x"` and `allow_high_memory=true` are explicitly provided. For the 320 × 192, 9-frame sample of the project, a peak MLX of approximately 52.7 GB was measured. First, run a short video test, and compare the detail reconstruction under the same reference. [MLX-Gen runtime parameters](https://github.com/lpalbou/mlx-gen/blob/main/docs/upscaling.md) · [fixed weights](https://huggingface.co/AbstractFramework/seedvr2-3b-8bit/tree/6e6b162d1e96c873ad93645508bbc4636814c0c7)

<a id="apple-foreground"></a>
### Apple Vision Foreground Segmentation

Run `bin/install core`. Provide `extract_apple_foreground` with the absolute path of the image, `path`, and extract `instances` and `foreground_png` from the result. The MCP at both ends shares the same interface with `bin/local extract_apple_foreground`. First, check the exported size and alpha channel, then check the contour of the actual sample. Use SAM3 when specifying objects by text. [Apple Vision instance mask](https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest)

<a id="vision-media"></a>
### Apple Vision Media Preprocessing

Run `bin/install core` and `bin/register`. The Codex and Claude Code call `local_specialists.inspect_apple_image`, and the terminal can pass the same JSON parameters to `bin/local inspect_apple_image`. When passing `path`, the category and appearance scores can be used; `comparison` returns the feature distance between two images, and the smaller the value, the more similar they are. Use the same and different images to check the distance, and then use business materials to find the appropriate threshold. Video frames can be extracted first, and then the same entry can be called. There are separate Vision APIs for image extraction, optical flow, and pose. [Apple Vision Request Directory](https://developer.apple.com/documentation/vision) · [Apple Thumbnail Example](https://developer.apple.com/documentation/Vision/generating-thumbnails-from-videos)

<a id="depth-anything"></a>
### Depth Anything V2 Small Core ML

Run `bin/install depth-anything` and `bin/register`. The installer verifies Apple’s FP16 `.mlpackage`, and uses system Core ML for compilation. Codex and Claude Code call `local_specialists.estimate_depth`, and the terminal can pass the same JSON parameters to `bin/local estimate_depth`. When inputting images, `path`, `compute` optional `all`, `cpu`, `cpu-gpu`. The result is a local relative depth PNG that aligns with the decoded input image, with the longest side up to 4000 pixels. First, use clear foreground and background outlines to verify the depth order. Physical distances need to be calibrated additionally. [Apple Core ML model cards and Swift integration](https://huggingface.co/apple/coreml-depth-anything-v2-small)

<a id="core-ml"></a>
### Apple Core ML

Run `bin/install core` and `bin/register`. Place the provided `.mlmodel`, `.mlpackage`, or `.mlmodelc` in a directory accessible for reading. Codex and Claude Code call `predict_coreml`, and the terminal can use `bin/local predict_coreml`. Only the `model` path allows viewing the input name, type, and shape. During prediction, pass the `inputs` by name to the `image` path, `number`, `integer`, `text`, or `values`, and the tensor can be attached with `shape`. The image results are saved as PNGs of the original output size of the model. The tensor returns its shape, total length, and the first 1,024 values. The sequence and model state must be processed during a specialized adaptation.

`compute` Optional: `all`, `cpu`, or `cpu-gpu`. Actual operator scheduling can be verified using the Xcode model report or Instruments. Licensing is determined based on the specific model. [Apple Core ML Development Documentation](https://developer.apple.com/documentation/coreml)

<a id="shortcuts"></a>
### Apple Shortcuts

Run `bin/install core` and `bin/register`. Create a separate text shortcut in the Quick Commands App. Add **Use Model**, select **On-Device**, and use **Shortcut Input** as the prompt. Then add **Stop and Output**, select the **Response** of the previous action. Use `shortcuts list --show-identifiers` to find the UUID, and enter it into the `allowed_shortcut_ids` array of project `.runtime/config.json`. The configured ID can be obtained from `status`. [Apple Device Model Action](https://support.apple.com/guide/shortcuts-mac/use-apple-intelligence-in-shortcuts-mchl91750563/mac)

Verify directly with synthetic text `shortcuts run "<UUID>" -i input.txt --output-type public.plain-text`. Codex and Claude Code call `run_apple_shortcut`, passing in `shortcut_id` ,  `text`, or sending the same JSON to `bin/local run_apple_shortcut` via terminal. The calls from Codex are executed according to the tool approval configuration. Only the shortcut command IDs ready to be run by the agent are added to the array. The shortcut command itself decides whether to access system applications, networks, or user profiles. [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac) · [Reference to Codex configuration](https://developers.openai.com/codex/config-reference)

In the image workflow, add **Extract Text from Image**, select **Shortcut Input** for the image, and then use **Stop and Output** to get **Extracted Text**. Register a separate UUID, and use `path` from `run_apple_shortcut` to access the approved directory of images. Perform `path` or `text` each time. The local machine successfully tested the command line and two clients using screenshots from a real synthesis App window. [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)

<a id="screenshot-folder"></a>
### The specified directory automatically performs OCR upon receiving screenshots

Run `bin/install core`. Use `bin/local watch-screenshots "$HOME/LocalSpecialists/screenshots"` to continuously wait for new files and output NDJSON. You can also call `wait_for_screenshot` from any client, use `folder` to specify the allowed directory, and set `wait_seconds` to 1–45 seconds. MCP returns the Vision OCR and coordinates of the new files. Empty wait returns `timed_out`.

First, complete writing the screenshot, then move it to the final file name in the monitor directory, using PNG, JPEG, or HEIC. The monitor range is the direct file in that directory. During acceptance, `SCShareableContent.currentProcess` captures the test application and opens its own window. After being moved into the directory, both clients receive `NATIVE-482`. [Apple ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit)

<a id="shortcuts-folder"></a>
### Shortcuts Folder Automation

In Shortcuts’ **Automation**, create a **Folder** trigger, select a directory specifically for storing screenshots, enable **Added Files** and **Ignore Subfolders**, and choose **Run Immediately**. Use **Extract Text from Image** to receive **Shortcut Input**, pass the **Extracted Text** to **Save File**, and save it in another directory. Codex and Claude Code can read and output text from the approved output directory. The local Claude Code can add this directory to the current session using `bin/lfm claude --with-specialists --add-dir <output-directory>`. Any registered image shortcut command can also be invoked using `run_apple_shortcut`.

Use two new test screenshots to verify the output. Both triggers during local testing succeeded. The first trigger to text generation took about 53 seconds. The project’s directory monitoring tool can directly return text and coordinates, and can be called via MCP. [Apple Shortcuts automation for](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac)

<a id="shortcuts-screenshot"></a>
### System Screenshot Triggered

In the Shortcuts editor, search for **Screenshot**, add the **When a screenshot is saved** trigger, then select **Files**. Add **Text** and **Save File**, and confirm the trigger with a fixed test marker. Press `Shift⌘4` followed by a space, select the composite test window, and save the file. During local acceptance, the system log records `WFScreenshotTrigger`, and the background workflow writes `SCREEN-EVENT-571`. After moving this screenshot to the approved directory, it can be accessed via Codex or Claude Code using `document(backend="vision")`. Both ends receive `WINDOW-EVENT-684`. [Apple Shortcuts Automation](https://support.apple.com/guide/shortcuts-mac/add-automations-apdfbdbd7123/mac) · [Apple Screenshot Shortcut](https://support.apple.com/en-au/guide/mac-help/mh26782/27/mac/27)

In macOS 27.2.1, the screenshot trigger offers three destination categories: Files, Photos, and Clipboard. If you need to listen only to a specified directory and generate OCR automatically, use the project’s directory monitoring tool or the Folder trigger in Shortcuts.

## Special Task

<a id="timesfm"></a>
### TimesFM 3.0

Run `bin/install timesfm` to install Google’s MLX backend and fixed weights. Codex, Claude Code, and `bin/local forecast_series` all use `backend="timesfm"`, adopting Chronos’ fields and three-level quantiles. Keep a set of time-ordering data and a simple baseline comparison to examine prediction errors, interval coverage, and whether future covariates are available in advance. The local weights are non-commercial and non-production. For production scenarios, Chronos-2 from this project can be used. [Google TimesFM source code and license](https://github.com/google-research/timesfm) · [3.0 model card](https://huggingface.co/google/timesfm-3.0-pytorch)

<a id="chronos"></a>
### Chronos-2

Run `bin/install core` ,  `bin/install chronos` and `bin/register`. Codex and Claude Code call `local_specialists.forecast_series`, and the terminal can pass the same JSON parameters to `bin/local forecast_series`. For example `{"targets":{"count":[11,12,12,14,15,16,18,19]},"horizon":2}`. Multiple targets and historical covariates share the same inter-interval grid. It is known that each future numerical covariance must have a historical sequence with the same name, and the future length equals `horizon`. The prediction rows are in order of 0.1, 0.5, 0.9 quartiles. Leave a segment with known true values to compare the error and interval coverage with the recent value or seasonal baseline. [Amazon Chronos-2 model card](https://huggingface.co/amazon/chronos-2)

<a id="lean-kernel"></a>
### Lean Kernel Verification Existing Proofs

Run `bin/install lean`. Pass the Lean code `source`, theorem name `declaration`, and expected proposition type `statement` to `check_lean_proof`. The terminal can pass the same set of JSON parameters to `bin/local check_lean_proof`. Review the compilation statement again and audit the axiom dependencies of the specified theorem. When `statement` is provided, independently compile the target proposition and verify the theorem type. Dependencies on `sorryAx` or custom axioms, as well as mismatched propositions, all return `accepted=false`. If Lean 4.9.0 is used and Mathlib is required, run `bin/install lean-mathlib` and pass `library="mathlib"`. [Lean’s proof review instructions](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

Both offline Codex and Claude Code can use `--with-specialists`. The MCP for the current session connects to a separately isolated Lean process via a temporary Unix socket, and the socket is cleaned up after exit. Regularly registered Codex and Claude Code directly use the entry configured with `bin/register`.

<a id="goedel"></a>
### Goedel-Prover-V2 and Lean

Run `bin/install goedel` and `bin/register`. Provide formalized Lean propositions `statement` to Codex, Claude Code, or `bin/local generate_lean_proof`. The output includes candidate Lean code and `verification`. Check `accepted`, `statement_checked`, and `axioms` before use. For example, `∀ p q: Prop, p ∧ q → q ∧ p` can be used to check the standard library path.

Run `bin/install lean-mathlib` separately when Mathlib is required, and pass in `library="mathlib"`. This installation uses Lean 4.9.0 official version and the accompanying Mathlib. The Goedel official Linux batch experiment has its own fixed dependencies. The relationship between propositions and natural language problems still needs verification. [Goedel official environment and examples:](https://github.com/Goedel-LM/Goedel-Prover-V2#5-environment-setup) · [Fixed 8B GGUF:](https://huggingface.co/mradermacher/Goedel-Prover-V2-8B-GGUF/tree/43fab68ec71738a75b0a84738e18b222d2d4e249)

<a id="smolvla"></a>
### SmolVLA and LeRobot Offline Preview

Run `bin/install smolvla` and `bin/register`. Codex, Claude Code, or `bin/local preview_robot_actions` are inputted into `camera_images`, six-dimensional `state`, and `instruction`. The images are mapped according to the camera name during training. For the public SO100 samples, `camera1` is used for `top`, and `camera2` is used for `wrist`. When using `statistics_path` to provide LeRobot `stats.json` from the same dataset, the input state and output action use the units of that dataset. If omitted, normalized states are provided, and normalized actions are returned.

`device` Optional: `mps` or `cpu`. `seed` can be used for repeated sampling, and `steps` controls the retrieval of the first few steps in 50 steps of action. Verify the shape, scale, and deviation by comparing the state aligned with the camera frame with the corresponding action space. The tool reads the recorded data and returns a preview. [Model Card](https://huggingface.co/lerobot/smolvla_base) · [SO100 Sample Set](https://huggingface.co/datasets/lerobot/svla_so100_pickplace)

<a id="smolvla-preflight"></a>
### LeRobot Pre-Operation Inspection

Run `bin/install core` and `bin/install smolvla`, then call `bin/local check_smolvla_rollout`. Both clients can use the same-name tool of MCP. When parameters are omitted, check `lerobot-rollout` and native motor drivers, and enumerate the USB serial ports reported by the system. It is also possible to pass `port`, local `policy_path` and `calibration_path` from the authorized directory, and check the matching ports, model files, and SO-100/SO-101 six-axis metadata. [LeRobot hardware configuration](https://huggingface.co/docs/lerobot/main/en/so100)

`matching_metadata` indicates that the file structure matches. Camera mapping, real robotic arm calibration, and task performance need to be confirmed on-site. The preliminary inspection only enumerates serial ports and reads files; `hardware_verified` remains as `false`.

<a id="smolvla-rollout"></a>
### LeRobot On-Site Operation

`bin/install smolvla` Install fixed LeRobot 0.7.0, dataset dependencies, and Feetech drivers. The on-site entry is `.runtime/smolvla/bin/lerobot-rollout`. Use calibration and teaching data corresponding to the robotic arm, motion space, camera layout, and tasks, and input them via `--policy.path`, `--robot.type`, `--robot.port`, `--robot.id`, and `--robot.cameras` according to the official documentation. First, perform a pre-check for the same configuration, and verify the strategy actions through playback or simulation. This project has tested local CLI loading, pre-check, and public recording playback. Real-machine tasks, cameras, and motion quality are still pending acceptance. [LeRobot SmolVLA Deployment](https://huggingface.co/docs/lerobot/main/en/smolvla#evaluate-the-finetuned-model-and-run-it-in-real-time) · [On-site CLI](https://huggingface.co/docs/lerobot/main/en/inference)
