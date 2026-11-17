# Choosing tools with an agent

[简体中文](agents.zh-CN.md)

Before installation, ask Codex or Claude Code to read this guide and run `bin/plan <feature> --json`. A registered client can use `local_specialists.plan_deployment` with the same feature IDs.

> Read docs/deployment.md and docs/agents.md. Use plan_deployment or bin/plan to recommend a tool for [expected output]. The target Mac is [macOS, chip, memory and available storage]. The intended use is [personal, commercial, production or research]. My hard requirements are [coordinates, word timing, speaker identity, glossary terms, local-only processing, or other constraints].
>
> Report the best match and alternatives, evidence and setup requirements, and any exclusions. Give the corresponding recipe, install command, and one check using synthetic data. Ask about a missing requirement if the answer would change the recommendation.

Use `profile=default` or `profile=optional` to narrow the selection. Read `recipe`, `evidence`, `readiness`, and `reasons`. The `mcp` and `local_cli` fields describe how to call each candidate. For LFM review, pass the recommended `model` in `mcp.arguments`.

To plan for another Mac, pass a `target` such as `{"machine":"arm64","macos":"27.2","disk_gib":100,"memory_gib":24}`. The planner marks installed state on that target as `unknown_on_target`. For an existing index, pass the approved absolute `folder` and use the returned search arguments.

## Examples

```sh
bin/plan align-transcript --execution local --require corrected_transcript --verified-only --json
bin/plan semantic-search --use commercial --execution mcp --verified-only --json
```

For local word timing from an edited transcript, use Qwen3-ForcedAligner with the matching audio, transcript, and language. Each call to `bin/local align_audio` accepts up to 120 seconds. For commercial semantic search, try DigUp. Run `bin/local index-digup <directory>`, then verify the pages or timestamps in the results. For code, build the index with `--code` and query with `code=true`. Omni's Jina weights have noncommercial terms.

Install the selected route, check its source and version, and run the recipe with synthetic data. Test an actual tool call in the chosen client before processing production material. For local-only tasks, use the terminal or an offline LFM-backed session. [Offline clients](deployment.md#offline-specialists)
