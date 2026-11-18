# Local LFM Service

[简体中文](README.zh-CN.md)

Run the GGUF weights of Liquid AI using llama.cpp and Metal on Apple Silicon Macs. The service only listens on `127.0.0.1:8080`. After login, it is started by the user-level LaunchAgent. The source, version, and SHA-256 of the model and runtime download are recorded in [models.lock.json](config/models.lock.json) and [runtime.lock.json](config/runtime.lock.json) respectively.

| Model ID | Weight | Purpose |
| --- | --- | --- |
| `lfm-fast` | LFM3-1.7B BF16 | Text extraction, summary. Loaded when the service starts. |
| `lfm-tools` | LFM2.5-8B-A1B Q8_0 | Tool selection and parameter generation. |
| `lfm-reason` | LFM2.5-24B-A2B Q8_0 | Reasoning, review, and local Agent. |
| `lfm-vision` | LFM3-VL-2B BF16 and BF16 Visual Components | Screenshots and document pages. |
| `lfm-fast-q4` / `lfm-reason-q4` | Same model Q4_K_M | Same aircraft, comparison. |

## Use the existing Agent for delegation

Run ` `bin/register` ` in the root directory of the project. After completing the client registration, say “use local-lfm’s ` `extract_fields` ` to find the responsible person and date from this text” in a new Codex or Claude Code session. For a regular Claude Code session, use your own Claude login.

- `extract_fields` Pass the field descriptions and text to LFM, and it returns a short string that can be found in the original text. If not found, it returns `null`.
- `summarize` Receive text and optional focus points.
- `review` Receives a text or code snippet, along with a question that needs review. By default, `lfm-reason` is used. If Q4 is installed, `model="lfm-reason-q4"` can be specified.
- `inspect_image` Receives the PNG/JPEG file names and issues you provide. `inbox/` Supports static images up to 8 MiB in size and 16 million pixels. The file can be removed after analysis.

When delegating through the cloud-based main Agent, it can see tool parameters and return results. If you need to keep the images and answers on the local machine, run `backends/lfm/.venv/bin/python backends/lfm/scripts/lfm_mcp.py --image /path/to/image.png --question 'What status does the image show?'` in the project root directory.

## Full local test run

Start the program after installing the optional Reason weight in the project root directory.

```bash
bin/install lfm-reason
bin/lfm codex
bin/lfm claude
```

It can also be started from other directories using the absolute paths of the above two scripts. They use `lfm-reason` as the main model and employ isolated client configurations. macOS restricts the outbound network of two clients and child processes to local service ports. The Codex trial configuration is for read-only tasks, and only the state directory under the `.state/` project is writable. Claude Code retains its own tool license prompts. Daily cloud sessions can still use the original `codex` or `claude` commands.

After installing `core`, `bin/lfm codex --with-specialists` or `bin/lfm claude --with-specialists` can be used to temporarily access `local_specialists`. The offline Codex converts the MCP namespace into function names available to  llama.cpp via the adapter on the loopback address, and the generated files are saved in `.state/codex-local/specialists/artifacts/`. [Call examples and permission scope](../../docs/deployment.md#offline-specialists)

When using Omni, start the App first, and add `--with-omni` before `--with-specialists`. The client only exposes the selected Omni Unix socket. The query of paired devices and file retrieval are handled by Omni. [Omni Installation and Retrieval](../../docs/deployment.md#omni)

## Local API

This local process can directly use the OpenAI SDK, with the Base URL being `http://127.0.0.1:8080/v1`. If the SDK requires an API key, any placeholder string can be used. The deployment of the application and model routing are controlled by the caller.

```bash
curl -fsS http://127.0.0.1:8080/v1/models
curl -fsS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"lfm-fast","messages":[{"role":"user","content":"Summarize in one sentence: delivery moved to Thursday and Dana remains responsible."}],"max_tokens":160}'
```

The program can call `/v1/chat/completions`, `/v1/responses`, or `/v1/messages` in an Anthropic style as needed. Weight loading is done on-demand for the first call. External devices and cloud Bots cannot access this service from a reverse URL.

The function executor first checks the tools and parameters selected for the model, and after execution, fills in the results using the original call ID. When all results are collected, the model is explicitly instructed to answer based on those results, and in the final round, the value `tool_choice: "none"` is transmitted. The program can use JSON Schema constraint format when reading the answers. The 8B automatic mode may still initiate repeated calls after receiving the results. The acceptance covers both 8B and 24B models and two different inventory results.

<a id="维护"></a>
## Maintenance

Run the following command in the project root directory. Running the installation script repeatedly will verify the downloaded files and continue to download incomplete files. `default`: Select Fast and Vision. The model ID is downloaded separately to install the corresponding weights and enable persistent Fast. When the files are already fully downloaded, use `--reuse-from` to specify the old LFM root directory, re-verify, and reuse the existing weights.

```bash
bin/lfm setup default
bin/lfm start --available
bin/lfm status
bin/lfm verify --profile default
bin/lfm verify_clients
```

`bin/lfm setup all` Install all model types in the table. `bin/lfm start` Refresh the service when all models are ready. The default mode enables the installed models via `--available`. When migrating from an old deployment, first run `bin/lfm setup default --reuse-from <previous-root>` and `bin/lfm verify --profile default`. If all models are already available, use `all` to verify and reuse them. Run `bin/register --check` to find registrations pointing to old paths. Save existing commands and parameters for rollback, and follow [Client Migration Steps](../../docs/deployment.md#client-registration) to update to this project `bin/lfm serve`. The images are temporarily stored in this project `backends/lfm/inbox/`.

LaunchAgent reads the weight files for runtime, configuration, and APFS clone from `~/Library/Application Support/Local LFM`. This allows the service to start after login, without being restricted by macOS’s backend access to `Documents`. Within the project, `config/` is the source of deployment configuration. After modifying model parameters, `scripts/service.py start` can be run again to refresh the model configuration. `stop` will disable startup during login, and `uninstall` will remove the LaunchAgent created by this project. The operation logs are stored in `Application Support/Local LFM/logs/`, and verification results are recorded in the project’s `logs/`.

When running from the new work tree with `bin/lfm start --available`, the service can continue to use optional weights in the shared directory that match the current SHA-256 hash. This check also applies to the projection files of visual models. Two activations use the same local lock to avoid simultaneously modifying the service list.

To remove the delegation tools of a regular Agent, run `codex mcp remove local-lfm` and `claude mcp remove --scope user local-lfm`.
