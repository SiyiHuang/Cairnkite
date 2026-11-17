# Local LFM service

[简体中文](README.zh-CN.md)

This backend runs Liquid AI GGUF models with llama.cpp and Metal on Apple Silicon. The user LaunchAgent serves `127.0.0.1:8080`. The lock files pin upstream versions and SHA-256 hashes. [Model lock](config/models.lock.json) · [Runtime lock](config/runtime.lock.json)

| Model ID | Weights | Use |
| --- | --- | --- |
| `lfm-fast` | LFM3-1.7B BF16 | Field extraction and summaries, loaded at service startup |
| `lfm-vision` | LFM3-VL-2B BF16 and BF16 projector | Screenshot and image questions |
| `lfm-tools` | LFM2.5-8B-A1B Q8_0 | Tool selection and arguments |
| `lfm-reason` | LFM2.5-24B-A2B Q8_0 | Review and offline primary model |
| `lfm-fast-q4` / `lfm-reason-q4` | Q4_K_M | Quantization comparison |

Run `bin/register` from the project root to add `local-lfm` to Codex and Claude Code. Use `extract_fields` for verbatim spans or `null`, `summarize` for text, and `review` for a focused second opinion. Review defaults to Reason and accepts `model="lfm-reason-q4"` when installed. For `inspect_image`, stage a PNG or JPEG under `backends/lfm/inbox/` and pass its filename and your question. Images are limited to 8 MiB and 16 million pixels.

## Offline clients

```sh
bin/install lfm-reason
bin/lfm codex
bin/lfm claude
```

The launchers use isolated client configurations and restrict outbound connections to the local service. The Codex configuration is designed for read-only tasks with writes to its state directory. Claude Code retains its tool permission prompts. Add `--with-specialists` after installing `core` to load specialist tools. Start Omni and add `--with-omni` when an approved Omni socket is needed. [Offline tool calls](../../docs/deployment.md#offline-specialists) · [Omni](../../docs/deployment.md#omni)

## Local API

```sh
curl -fsS http://127.0.0.1:8080/v1/models
curl -fsS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"lfm-fast","messages":[{"role":"user","content":"Summarize: delivery moved to Thursday and Dana is still the owner."}],"max_tokens":160}'
```

Local clients can use `/v1/chat/completions`, `/v1/responses`, or the Anthropic-style `/v1/messages`. Supply a placeholder key if your SDK requires one. When executing function calls, validate the tool and arguments, then return each result using its original call ID. For the final answer, set `tool_choice: "none"`. The 8B model can otherwise issue repeated calls after receiving results.

<a id="维护"></a>
## Maintenance

```sh
bin/lfm setup default
bin/lfm start --available
bin/lfm status
bin/lfm verify --profile default
```

`default` installs Fast and Vision. Use `all` for all weights or pass an individual model ID. Setup verifies complete downloads and resumes incomplete ones. From a new checkout use `bin/lfm setup default --reuse-from /path/to/previous/lfm` to verify and reuse files. Run `bin/register --check` and update obsolete entries. [Registration migration](../../docs/deployment.md#client-registration)

The LaunchAgent runs from `~/Library/Application Support/Local LFM`, which contains staged configuration and APFS-cloned weights. It also holds server logs. The checkout contains verification logs at `backends/lfm/logs/`. The `--available` flag keeps optional weights that pass the current lock. Run `bin/lfm stop` to stop the service and disable login startup, or `bin/lfm uninstall` to remove the managed LaunchAgent. Remove MCP registrations with `codex mcp remove local-lfm` and `claude mcp remove local-lfm --scope user`.
