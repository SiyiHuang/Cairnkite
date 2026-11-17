# Verification

[简体中文](verification.zh-CN.md)

## Default models from an empty checkout

On November 17, 2026, the default setup passed on an Apple Silicon Mac running macOS 27.2.1 with SDK 27.2, Codex CLI 0.169.0-alpha.11.1, and Claude Code 2.1.126. Speech language resources and Apple Intelligence were already enabled on the test machine.

Starting with an empty model directory, the two default models and the vision projector were downloaded over public HTTP Range requests. The download totaled 7,312,248,704 bytes. Each range was checked for HTTP 206, matching Content-Range, and length. The assembled files and deployed copies matched the pinned SHA-256 values.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `LFM3-1.7B-BF16.gguf` | 3,466,626,336 | `39158a79f56edb85e0c4252ce6447b8d7883ef82ffedd02f0cda7c84da5e9f68` |
| `LFM3-VL-2B-BF16.gguf` | 3,466,626,336 | `a7a514bd201faba4d329ec6d252253272904652576f0557ee84a106544d90298` |
| `mmproj-LFM3-VL-2B-BF16.gguf` | 378,996,032 | `8e75a88afc0e6a3bcd637becbe720447ea0794934b7b417a1f42d5cfe0d9c288` |

`bin/install default en-US zh-CN` installed the stack and the managed service was restarted with the fresh weights. `bin/lfm verify --profile default` passed field extraction, missing values, summaries, concurrent requests, long context, image questions, and inbox boundary checks.

Codex and Claude Code each registered both MCP servers from blank configurations. In signed-in sessions, each client actually called `status`, `plan_deployment`, `extract_fields`, and `inspect_image`. Both selected `barcodes`, extracted Dana and July 21 with `room: null`, and returned `ORBIT-741` from the test image. [Run the same checks](../README.md#connect-codex-and-claude-code)

## Specialist checks

| Area | Observed results |
| --- | --- |
| Apple frameworks | PDF text layers, scan OCR, barcodes, paginated evidence, file scope, speech, translation, Foundation Models, Core ML, and media tools passed synthetic checks. The system `fm` command also returned the expected code using the on-device model. |
| LFM and offline clients | Optional Q4 and Q8 weights, function selection, concurrent inference, and artifact access passed. Both offline clients called specialist tools, including Lean proof checking. |
| OCR and media | Vision and Paddle returned positioned text and table evidence. MiniCPM provided an independent reading. Audio and video samples checked speaker labels, word timing, separation, masks, visual restoration, and audio-track preservation. |
| Search and automation | DigUp, Omni, Spotlight, and code search retrieved synthetic material. Omni linking and copying passed between two isolated instances on one Mac. Shortcuts and the screenshot watcher were tested with synthetic windows. |
| Forecasting and proofs | Chronos and TimesFM returned quantiles on sample series. Lean checked exact statements and dependencies, including proposed proofs from Goedel. SmolVLA passed software checks and public SO100 replay. |

Run only the optional checks for the backends you have installed. The full per-backend results are available in the Chinese verification record. [Detailed verification log in Chinese](verification.zh-CN.md)

```sh
python3 tests/planner.py
python3 tests/lfm_service.py
.runtime/mcp/bin/python tests/smoke.py --apple --text-models
.runtime/mcp/bin/python tests/smoke.py --expanded
.runtime/mcp/bin/python tests/smoke.py --digup
bin/lfm verify --profile all
bin/lfm verify_clients
```

## Pending checks

| Route | Pending evidence |
| --- | --- |
| Omni across physical Macs | Repeat pairing, search, and hash verification on two separate Macs with an approved test directory. |
| SmolVLA live rollout | Verify the calibrated arm, camera mapping, and task behavior on physical hardware. |
| X4 footage | Repeat relevant media tests with approved real footage. |
| Apple SpeechDetector | The probe returned zero intervals on a speech fixture. Silero VAD, Apple transcription, and Sound Analysis have timing results. |

System features depend on macOS, SDK, region, and language assets. [Deployment recipes](deployment.md)
