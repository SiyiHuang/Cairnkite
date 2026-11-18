# Choosing tools with an agent

[简体中文](agents.zh-CN.md)

After cloning the repository, assign the following tasks to Codex or Claude Code. You can read the directory and run `bin/plan <feature> --json` directly before installation. If you are already registered for MCP, you can use `local_specialists.plan_deployment` instead, with the same parameters and logic.

> Read the docs/deployment.md and docs/agents.md in the repository, and call plan_deployment or bin/plan to view the decision tree. My task is to “fill in the expected output”, the device is “fill in macOS version, chip, memory, and available space”, the purpose is “personal, commercial, production, or research”, and the hard requirements are “fill in coordinates, word time, speaker, terminology, and other requirements such as keeping the material on this machine”.
>
> Provide reasons for the preferred, alternative, and excluded options, indicating whether they have existing measurements, require configuration, or need upstream testing. List the deployment instructions relevant to my task, installation commands, and a step for checking the results using synthetic data. If any answer changes the choice, ask me about it first. During deployment, follow the installation scope I have specified.

Also, use `profile=default` to prioritize checking the default installation, or specify `profile=optional` to check specific paths. For each candidate, `mcp` and `local_cli` provide actual calls. `mcp.server` distinguishes `local-lfm` from `local_specialists`. `status` contains `lfm_models`, which comes from the local loopback service and represents models that are visible to the service. Verification still uses examples from actual tasks.

When planning another machine, send `target` to `plan_deployment`, such as `{"machine":"arm64","macos":"27.2","disk_gib":100,"memory_gib":24}`. Explicit targets are marked with `unknown_on_target` to remind the Agent to review the actual installation and resources on that machine. When giving LFM the choice to review, also send `model` from the selected candidate `mcp.arguments` to the tool.

When querying the data directory specified by the user on the local machine, pass the approved absolute path to `plan_deployment.folder`. Only when selecting a type and returning requires index preparation, refer to the index formula. Once ready, use the returned `mcp.arguments` along with the user’s query term to call `search`.

## Two examples

**“The time required to generate words from the proofed version. The recording and text are kept on this device.”**

```sh
bin/plan align-transcript --execution local --require corrected_transcript --verified-only --json
```

The most suitable option is Qwen3-ForcedAligner. You need to provide the same recording, a revised version, and the language—up to 120 seconds per time slot. The execution phase is carried out directly on the local machine using `bin/local align_audio`.

**Company information needs to be searchable by meaning, and must be suitable for commercial use.**

```sh
bin/plan semantic-search --use commercial --execution mcp --verified-only --json
```

Choose DigUp. After installation, run `bin/local index-digup <directory>` on the authorized directory, then use `search` to query and verify page numbers or times. When checking codes, add `--code` to the index creation command, and pass `code=true` during querying. The Jina weight of Omni applies under non-commercial terms.

## From selection to deployment

1. Read the returned `recipe`, and check `evidence`, `readiness`, and `reasons`. If there are no recommendations, keep the hard conditions that caused the exclusion.
2. In relation to the goals and installation scope, describe the disk estimation, external apps, and required system resources. Check the index, pairing, microphone, or hardware according to the route. The upstream route is tested in a separate environment.
3. After the user requests deployment, install the specified route step by step. Verify the source and version, and first use a synthetic sample to obtain the expected format and positioning information.
4. For the MCP route, use `status` and a tool test to check client connections. For the CLI route, check the output on the local machine. Before processing the actual data, confirm the accessible paths and the scope of evidence that can be returned.

`plan_deployment` Only returns selection information. The cloud agent may receive parameters and returned content from the inference tool. For materials that require to be kept entirely on the local machine, you can run `bin/local`, upstream local commands, or start a local LFM session using `bin/lfm codex --with-specialists` or `bin/lfm claude --with-specialists`. [Special tool](deployment.md#offline-specialists) called by offline client]
