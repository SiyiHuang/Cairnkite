# 本地 LFM 服务

[English](README.md)

在 Apple Silicon Mac 上用 llama.cpp 和 Metal 运行 Liquid AI 的 GGUF 权重。服务只监听 `127.0.0.1:8080`。登录后由用户级 LaunchAgent 启动，模型和运行时的下载来源、版本及 SHA-256 分别记录在 [models.lock.json](config/models.lock.json) 和 [runtime.lock.json](config/runtime.lock.json)。

| 模型 ID | 权重 | 用途 |
| --- | --- | --- |
| `lfm-fast` | LFM3-1.7B BF16 | 文本抽取、摘要。服务启动时加载。 |
| `lfm-tools` | LFM2.5-8B-A1B Q8_0 | 工具选择和参数生成。 |
| `lfm-reason` | LFM2.5-24B-A2B Q8_0 | 推理、复核和本地 Agent。 |
| `lfm-vision` | LFM3-VL-2B BF16 与 BF16 视觉组件 | 截图和文档页面。 |
| `lfm-fast-q4` / `lfm-reason-q4` | 同款模型 Q4_K_M | 同机对照。 |

## 用现有 Agent 委派

在项目根目录运行 `bin/register` 完成客户端注册后，在新开的 Codex 或 Claude Code 会话中说「用 local-lfm 的 `extract_fields` 从这段文字找负责人和日期」。Claude Code 的普通会话使用你自己的 Claude 登录。

- `extract_fields` 将字段说明和文本交给 LFM，返回可在原文中找到的短字符串。找不到时返回 `null`。
- `summarize` 接收文本和可选关注点。
- `review` 接收文本或代码片段，以及一个需要复核的问题。默认使用 `lfm-reason`，已安装 Q4 时可指定 `model="lfm-reason-q4"`。
- `inspect_image` 接收你主动放进 `inbox/` 的 PNG/JPEG 文件名和问题。支持至多 8 MiB、1600 万像素的静态图。可在分析后移走该文件。

通过云端主 Agent 委派时，它能看到工具参数和返回结果。需要把图片和答案都保留在本机时，可在项目根目录运行 `backends/lfm/.venv/bin/python backends/lfm/scripts/lfm_mcp.py --image /path/to/image.png --question '图里的状态是什么？'`。

## 全本地试跑

在项目根目录安装可选的 Reason 权重后启动。

```bash
bin/install lfm-reason
bin/lfm codex
bin/lfm claude
```

也可从其他目录用上面两个脚本的绝对路径启动。它们以 `lfm-reason` 为主模型，使用隔离的客户端配置。macOS 限制两个客户端及子进程的出站网络到本机服务端口。Codex 的试跑配置用于只读任务，只有它在项目 `.state/` 下的状态目录可写。Claude Code 保留自身的工具许可提示。日常云端会话仍可用原来的 `codex` 或 `claude` 命令。

安装 `core` 后，可用 `bin/lfm codex --with-specialists` 或 `bin/lfm claude --with-specialists` 临时接入 `local_specialists`。离线 Codex 通过回环地址上的适配器把 MCP 命名空间转换为本机 llama.cpp 可用的函数名，生成文件保存在 `.state/codex-local/specialists/artifacts/`。 [调用示例与权限范围](../../docs/deployment.zh-CN.md#offline-specialists)

使用 Omni 时先启动 App，在 `--with-specialists` 前加 `--with-omni`。客户端仅开放所选 Omni Unix socket。已配对设备的查询和文件取回由 Omni 处理。 [Omni 安装与检索](../../docs/deployment.zh-CN.md#omni)

## 本机 API

本机进程可以直接用 OpenAI SDK，Base URL 为 `http://127.0.0.1:8080/v1`。如果 SDK 要求填写 API key，可以传任意占位字符串。应用的部署和模型路由由调用方控制。

```bash
curl -fsS http://127.0.0.1:8080/v1/models
curl -fsS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"lfm-fast","messages":[{"role":"user","content":"用一句话概括：交付改到周四，负责人仍是周林。"}],"max_tokens":160}'
```

程序可按需调用 `/v1/chat/completions`、`/v1/responses`，或 Anthropic 风格的 `/v1/messages`。首次调用按需加载权重。外部设备和云端 Bot 无法从回环地址访问此服务。

函数执行器先核对模型选择的工具及参数，执行后按原调用 ID 回填结果。收齐结果时，明确让模型根据结果作答，并在最后一轮传 `tool_choice: "none"`。程序读取答案时可用 JSON Schema 约束格式。8B 的自动模式在收到结果后仍可能发起重复调用。验收覆盖 8B 与 24B 两种模型和两个不同的库存结果。

## 维护

在项目根目录执行以下命令。重复运行安装脚本会校验已下载的文件，并续传未完成的文件。`default` 选择 Fast 和 Vision。单独传模型 ID 安装对应权重及常驻 Fast。已有完整下载时可用 `--reuse-from` 指定旧的 LFM 根目录，重新校验并复用现有权重。

```bash
bin/lfm setup default
bin/lfm start --available
bin/lfm status
bin/lfm verify --profile default
bin/lfm verify_clients
```

`bin/lfm setup all` 安装表中全部型号。`bin/lfm start` 在全部型号就绪时刷新服务。默认档位通过 `--available` 启用已安装的型号。从旧部署迁移时，先运行 `bin/lfm setup default --reuse-from <旧根目录>` 和 `bin/lfm verify --profile default`。如果已有全部型号，可用 `all` 校验并复用。运行 `bin/register --check` 查找指向旧路径的注册。保存现有命令和参数以备回退，按[客户端迁移步骤](../../docs/deployment.zh-CN.md#client-registration)更新为本项目 `bin/lfm serve`。图像暂存到本项目的 `backends/lfm/inbox/`。

LaunchAgent 从 `~/Library/Application Support/Local LFM` 读取运行时、配置和 APFS 克隆的权重文件。这让登录后的服务可以启动，不受 macOS 对 `Documents` 的后台访问限制。项目内 `config/` 是部署配置的来源；修改模型参数后可重新运行 `scripts/service.py start` 刷新模型配置。`stop` 会同时禁用登录时启动，`uninstall` 会移除本项目创建的 LaunchAgent。运行日志在 `Application Support/Local LFM/logs/`，验证结果在项目的 `logs/`。

从新工作树运行 `bin/lfm start --available` 时，服务可继续使用共享目录中符合当前 SHA-256 的可选权重。这个检查也适用于视觉模型的投影文件。两次激活走同一个本机锁，避免同时改写服务清单。

要移除普通 Agent 的委派工具，运行 `codex mcp remove local-lfm` 和 `claude mcp remove --scope user local-lfm`。
