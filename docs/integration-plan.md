# Cairnkite integration plan

[简体中文](integration-plan.zh-CN.md)

Cairnkite combines Apple frameworks, LFM, and specialist backends with one deployment planner. The default profile provides a small set of general tools. Optional routes add features that require separate models, apps, or hardware.

| Directory | Purpose |
| --- | --- |
| `bin/` | Install, plan, register, and run tools |
| `catalog/` | Capabilities, licenses, requirements, and evidence |
| `native/` | Apple framework helpers |
| `src/` | Specialist MCP server and workers |
| `backends/lfm/` | LFM runtime, model pins, and client launchers |

## Default profile

Use PDFKit for PDF text layers and Apple Vision for scans, boxes, tables, and barcodes. Use LFM Fast for short summaries and source-grounded field extraction, and LFM Vision for image questions. Apple Speech and Translation use installed language assets. Spotlight searches file metadata, while `rg` can search filenames and code directly. The clients use `local_specialists` for routing and specialist tools, and `local-lfm` for LFM inference.

## Optional routes

| Task | Candidates | Acceptance check |
| --- | --- | --- |
| Complex documents | PaddleOCR-VL, MiniCPM-OCR, Jev | Compare reading order, formulas, tables, and boxes |
| Audio | MOSS, Qwen3-ASR and ForcedAligner, Silero VAD | Check speaker labels, vocabulary, timestamps, overlap, and truncation |
| Search | Omni, DigUp, Spotlight, Jina Code, Qwen reranker | Verify the license, index scope, source location, and ranking |
| Text | Foundation Models, Hy-MT2, GLiNER, Privacy Filter, Clef, LFM Tools and Reason | Check grounding, missing fields, terms, and resource usage |
| Media | TalkNet, SAM3, SAM Audio, Kokoro, SwiftVR, SeedVR2, Apple tools | Check tracks, timing, fidelity, and peak memory |
| Specialist tasks | Chronos, TimesFM, Lean, Goedel, Core ML, SmolVLA, Shortcuts | Compare baselines, prove the exact Lean statement, and validate device inputs separately |

The planner filters by output, hardware, language assets, licensing, and execution mode, then ranks usable candidates by readiness and task fit. A cloud client can receive tool inputs and outputs. Use local commands or offline clients for local-only processing.

For each route, record the pinned version, source, required resources, license, client or CLI entry point, test input, and observed output. Use synthetic fixtures to check MCP calls, reruns, missing resources, invalid inputs, and inaccessible files. Record physical hardware checks separately from tests with recorded data. [Deployment](deployment.md) · [Verification](verification.md)
