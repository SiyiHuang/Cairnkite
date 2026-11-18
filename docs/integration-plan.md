# Cairnkite integration plan

[简体中文](integration-plan.zh-CN.md)

Cairnkite brings installable, selectable, and verifiable local tools to Codex and Claude Code on Apple Silicon. Start with the default setup, then reproduce and verify client calls for optional routes. The Apple and LFM runtimes manage their dependencies separately and share one deployment catalog and planner.

## Project structure

`bin/` contains installation, planning, and client registration commands. `catalog/` describes capabilities, licenses, resource requirements, and verification status. `native/` wraps Apple frameworks, and `src/` implements the specialist MCP server and terminal tools. `backends/lfm/` contains the LFM runtime, model pins, and client entry points. Downloads, indexes, logs, credentials, and runtime state are kept on the Mac.

## Default installation

| Capability | Default path | Deployment and verification |
| --- | --- | --- |
| PDFs, scans, and screenshots | PDFKit reads text layers. Vision handles scans, boxes, simple tables, and barcodes. | Compile the Swift helper. Use a two-page PDF and a barcode to check page numbers, text, coordinates, tables, and identifiers. |
| Text | Natural Language identifies languages and entities. LFM Fast extracts source-grounded fields and summarizes. | Use the local Metal service and MCP. Check present and missing fields, verify facts in a summary, and test the terminal call. |
| Image questions | LFM Vision answers questions about visible content. Vision OCR returns the text and coordinates. | Use a synthetic screenshot to verify known values and check that the image tool only reads explicitly staged inputs. |
| Audio and translation | Apple Speech and Translation use the installed language assets. | Check the English and Chinese environment, then run separate transcription and translation checks. Record the locale, asset status, words, and timestamps. |
| File locations | `rg` searches literals and code symbols. Spotlight searches indexed metadata. | Check coverage with a synthetic directory. Verify relative locations in the results. Semantic search uses an optional route. |
| Client access | `local_specialists` selects routes and runs specialist tools. `local-lfm` handles LFM. | One repository handles install, status, verification, and removal. Keep both MCP names and verify real calls from both clients. |

LFM Fast stays loaded and other runtimes and weights load as needed. Rerunning the default install reuses verified tools, weights, language assets, and the service. Fast is the default field extractor. The Apple Swift route is available where Apple Intelligence is enabled. [Verification results](verification.md)

## Optional routes and acceptance criteria

| Task | Routes to verify | Evidence |
| --- | --- | --- |
| Complex documents | PaddleOCR-VL for layout, MiniCPM-OCR for a second reading, Jev for scoring | Compare errors on columns, formulas, and tables. Check boxes and structure against the page. Give Jev both correct and incorrect candidates. |
| Audio | MOSS 8-bit diarization, Qwen ASR 0.6B and 1.7B, ForcedAligner and streaming, Apple SpeechDetector | Test Chinese, English, overlapping speakers, long recordings, and edited transcripts. Check time ranges, final text, and speaker labels. |
| Content and code search | Omni/Jina for personal use, DigUp/EmbeddingGemma 2 as a commercial candidate, Omni pairing, Core Spotlight app index, jina-grep and Qwen3-VL-Reranker | Compare the same queries with known answers against `rg` and the first-stage ranking. Record pages, lines, timestamps, and latency. Verify licenses and index scope. |
| Text and general reasoning | Apple Foundation Models text and structured output, Hy-MT2 glossaries, GLiNER2.5 spans, Privacy Filter, Clef-Flash, LFM Tools and Reason quantizations | Compare source spans, nulls, terminology, and scores. Verify tool calls, concurrent model memory, and offline client fallback. Check redacted text for remaining sensitive data. |
| Meetings and media | TalkNet active speaker detection, SAM3 masks and tracking, SAM Audio separation, Kokoro, SwiftVR and SeedVR2, Apple media and sound tools | Compare synchronization, tracks, sound labels, artifacts, and peak memory. Repeat selected tests with approved X4 footage. |
| Forecasting, proofs, and device actions | Chronos-2 and TimesFM, Goedel and Lean, Depth Anything and Core ML, SmolVLA replay, Shortcuts | Compare forecasting baselines. Check the exact proposition in Lean. Verify depth ordering and recorded actions. Use Shortcuts or Computer Use for tasks that depend on UI state. |

Give each optional route install and invocation instructions for both clients when it provides a reproducible independent output or improves cost or privacy at similar quality. Verify the parts that can run on one Mac first and record which checks still require a second Mac, hardware, or system resources. Keep the trial result or upstream limitation for excluded routes.

## How the agent chooses a route

The catalog behind `bin/plan` and `plan_deployment` carries `default` and `optional` profiles, evidence, and invocation details. Filter by output, target hardware, memory, language assets, licensing, and execution requirements. Rank by observed performance, resource needs, and readiness. Return the main recommendation, distinctive capabilities, failure conditions, alternatives, install commands, call parameters, and checks. Planning is read-only. Users can install the default profile or individual routes.

- Use PDFKit for PDF text layers and Vision for scans. Use Paddle for formulas and difficult reading order. For uncertain reads, try MiniCPM or score a rendered candidate against the original crop with Jev.
- Use Apple Speech for typical audio, MOSS for speaker attribution, Qwen for word timestamps, and ForcedAligner when a corrected transcript exists.
- Use Spotlight or `rg` for known names and symbols. Build an index over the selected source for semantic search. Use visual reranking when candidates require finer discrimination.
- Use LFM Fast for concise summaries and grounded fields. Compare Swift structured generation for fixed schemas and GLiNER for spans. Use Reason for an independent review or an offline coding-agent trial.
- For private inputs, run a local command or an isolated offline client. Hosted sessions can receive tool parameters and results. File tools use approved roots, references, and paginated evidence. Prefer framework APIs, terminal tools, files, and local MCP. Use Computer Use when the task depends on the interface or tests show a measurable advantage. [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP](https://code.claude.com/docs/en/mcp) · [Apple Foundation Models CLI and SDK](https://developer.apple.com/videos/play/wwdc2026/334/)

## Delivery order and verification

1. Run planner tests, install the Apple core, and verify both clients on synthetic data. Check Foundation Models availability with the Swift helper. Record Swift results separately from system `fm` checks that require machine-wide terms.
2. Maintain the default stack from pinned versions, deployment code, and test results. Retain the running loopback address, service identity, and weights during migration. Keep private material and runtime files local. Test the new checkout with fixtures and record how to restore the previous paths.
3. Verify install reruns, unready options, denied access, invalid tool arguments, and an unavailable local service. Check the same tool from both clients with known results. Record hosted-client and isolated offline runs separately.
4. For each optional route, document the version, source, license, resources, CLI and MCP calls, fixture, expected output, and observed result. Keep verification pending when evidence is limited to a tool listing or downloaded weights.
5. Repeat default calls on the target Mac. Record the verification scope of optional routes and mark physical checks that still require another Mac, an arm, or real footage. After a rename, verify the remote URL and client registrations. [Verification results](verification.md)
