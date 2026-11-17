# Cairnkite

[简体中文](README.zh-CN.md)

Cairnkite is a local AI toolkit for macOS. It lets Codex and Claude Code choose and call Liquid AI models, Apple frameworks, and specialist models through MCP. You can also run the tools directly from your terminal.

The name combines *cairn*, a trail marker that points to the right tool, and *kite*, the bird. In Chinese, the project is called 石鸢.

<a id="安装"></a>
## Quick start

You need an Apple Silicon Mac, macOS 26 or later, the macOS 26.4 SDK or later from Xcode or Command Line Tools, and `uv`. Allow at least 20 GB of disk space. The three files for the default LFM Fast and Vision models total about 7.31 GB. Apple Intelligence, Speech, and Translation have their own system settings and language assets. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

If you need Command Line Tools, run `xcode-select --install` and finish installation. Check the selected SDK with `xcrun --sdk macosx --show-sdk-version`.

```sh
git clone https://github.com/SiyiHuang/cairnkite-release.git Cairnkite
cd Cairnkite
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

The LFM service uses `127.0.0.1:8080`. If the port is occupied, identify the existing service before installing. Cairnkite can reuse its own managed LFM service. Keep the checkout at a stable path because MCP registrations use absolute paths.

```sh
bin/install default en-US zh-CN
bin/lfm status
.runtime/mcp/bin/python tests/smoke.py
bin/lfm verify --profile default
```

Once the service is ready, its model list includes `lfm-fast` and `lfm-vision`. The native smoke test prints `Smoke test passed.` and the LFM check writes `backends/lfm/logs/verification.json`. The installer verifies downloaded files and resumes interrupted model transfers. Use `bin/install core` for Apple frameworks only or `bin/install speech ja-JP` to add a speech language. [Reuse existing LFM downloads](backends/lfm/README.md#maintenance)

## Connect Codex and Claude Code

Install the client CLIs and sign in with `codex login` or `claude auth login` if you use a hosted primary model. [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) · [Claude Code quickstart](https://code.claude.com/docs/en/quickstart)

```sh
bin/register
bin/register --check
```

Use `bin/register codex` or `bin/register claude` to register one client. Append the same client name to `bin/register --check` to check it independently. The two entries should point to this checkout's `bin/serve` and `bin/lfm serve`. Inspect them with `codex mcp get local_specialists --json`, `claude mcp get local_specialists`, and the matching commands for `local-lfm`. Claude Code should report that the entries are connected. [Move an existing registration](docs/deployment.md#client-registration)

Start a new session in each client and paste this prompt.

> Call local_specialists status, then call local_specialists plan_deployment with feature="barcodes", execution="mcp", and verified_only=true. Call local-lfm extract_fields on "The telescope calibration is scheduled for July 21. Dana is the owner. The room is undecided." Extract owner (responsible person's name), date (scheduled date), and room (confirmed room). Report the tool results.

Check the tool trace for the recommendation `barcodes` and the result `{"owner":"Dana","date":"July 21","room":null}`.

```sh
cp tests/fixtures/observatory.png backends/lfm/inbox/observatory.png
```

> Call local-lfm inspect_image with filename="observatory.png" and question="What is the code for the left bench? Return only that code." Report the tool result.

Both clients should return `ORBIT-741` using LFM Vision. [Verification results](docs/verification.md)

<a id="工作流"></a>
## Choose a tool

| Task | Start with | Options |
| --- | --- | --- |
| PDF, scans, and barcodes | PDFKit and Apple Vision | PaddleOCR-VL for complex layouts, MiniCPM-OCR for a second pass, and Jev for scoring |
| Text and images | LFM Fast and Vision | LFM Reason, Apple Foundation Models, GLiNER, and Privacy Filter |
| Audio | Apple Speech and Sound Analysis | Silero VAD, MOSS, Qwen3-ASR and alignment, SAM Audio, and Kokoro |
| Search and translation | Spotlight and Apple Translation | DigUp, Omni, Jina Code, Qwen reranking, and Hy-MT2 |
| Images and video | Apple Vision and VideoToolbox | Core ML depth, SAM3, TalkNet, SwiftVR, and SeedVR2 |
| Forecasts, proofs, and robot recordings | Run the planner | Chronos-2, TimesFM, Lean, Goedel, and SmolVLA |

```sh
bin/plan scan --profile default
bin/plan complex-layout --require formula_markup --execution mcp
bin/plan semantic-search --use commercial --json
```

The planner works before installation. It returns the reason for each recommendation, requirements, installation commands, and an acceptance check. The planner catalog includes Chinese labels and explanations. Agents can use stable feature IDs and the linked English recipes. [Deployment guide](docs/deployment.md) · [Agent guide](docs/agents.md) · [Project plan](docs/integration-plan.md)

<a id="文件和网络范围"></a>
## Files, privacy, and licensing

Place input files under `~/LocalSpecialists` or configure approved directories with `allowed_roots` in `.runtime/config.json`. LFM Vision reads images staged in `backends/lfm/inbox/`. Large specialist results can be paged with `read_evidence` and are stored in `.runtime/results/`.

The tools run locally. Hosted Codex and Claude Code sessions can receive inputs and outputs from their tools. For material that must stay on the Mac, run `bin/local`, use `bin/lfm local`, or start an offline LFM-backed client. [Offline client setup](docs/deployment.md#offline-specialists)

Cairnkite's source code and original fixtures are MIT licensed. Downloaded models, dependencies, and Apple services use their own terms. [MIT license](LICENSE) · [Dependency versions and licenses](dependencies/README.md)


## Troubleshooting and removal

Run `bin/register --check` for stale paths and `bin/lfm status` for the model list. If Apple Intelligence is unavailable, `status` reports its reason. Language assets and search indexes have separate setup steps. [Deployment guide](docs/deployment.md)

Run the matching commands for the clients you registered.

```sh
codex mcp remove local_specialists
codex mcp remove local-lfm
claude mcp remove local_specialists --scope user
claude mcp remove local-lfm --scope user
```

To manage the LFM background service, see the maintenance guide. [LFM maintenance](backends/lfm/README.md#maintenance)
