# 需求细化：基于 langgraph 的验证型 Agent

## 背景与目标
- 目标：使用 Python + langgraph 开发一个验证型 Agent，用于证明可分别调用并串联 milvus、mem0、LLM、MCP 工具与 langgraph，同时接入 langfuse 完成全流程 trace。
- 启动方式：除 `python -m app.main` 外，必须支持 langgraph CLI 的 `langgraph dev` 与 `langgraph up` 启动方式。
- 约束：环境管理工具使用 uv；所有连接配置与 LLM API Key/Endpoint、Langfuse Key/Host、MCP 连接信息必须写在 `.env` 中，且可配置。
- 容器化：必须支持构建容器镜像，用于部署或与 `langgraph up` 配套使用。
- 交付物：可运行的最小可验证流程（MVP），具备清晰的结构化返回与可追踪的 trace，并可构建镜像。

## 术语
- Agent：基于 langgraph 构建的编排流程。
- Milvus：向量数据库，用于存取向量化数据。
- mem0：记忆/上下文存储服务，用于保存与检索上下文。
- LLM：大模型服务，使用可配置 API Key 与 Endpoint 调用。
- MCP：Model Context Protocol，用于通过标准化工具调用访问外部能力。

## 功能需求
### 1) Agent 总体流程（核心验证链路）
- 必须包含可独立验证的节点：
  - Milvus 节点：完成一次向量写入 + 向量检索或按 id 查询。
  - mem0 节点：完成一次记忆写入 + 记忆检索，且必须使用 `example/mem0.py` 中的封装方式调用（HTTP 请求方式），禁止直接使用 mem0 SDK。
  - LLM 节点：完成一次模型调用，输出可解析文本。
- 必须包含 MCP 工具调用节点：至少调用一个 MCP 工具并获取返回结果。
- 必须使用 langgraph 编排上述节点，并形成可重复执行的完整流程。
- 允许通过 CLI 或简单的入口函数触发 Agent 执行（例如 `python -m app.main`）。
- Agent 必须返回结构化结果（建议 JSON 字典），用返回内容直接体现各组件调用成功与关键返回值。
- Agent 需要接入 langfuse，能够对整条流程进行 trace，并覆盖各节点执行。
- Agent 运行过程必须使用 langgraph 内置的 checkpoint 机制，用于保存与恢复执行状态。

### 1.5) LangGraph CLI 启动支持（新增）
- 必须支持使用 langgraph CLI 启动：`langgraph dev` 与 `langgraph up`。
- 需提供 langgraph CLI 所需的配置文件（如 `langgraph.json` 或 `langgraph.yaml`），并明确以下内容：
  - graph 映射与入口（指向 `app/graph.py` 中可导出的 graph 对象）。
  - 依赖/本地路径配置，确保 CLI 能加载当前项目代码。
  - 默认使用 `.env` 作为环境变量来源，不在配置文件中硬编码密钥。
  - 可选运行参数（端口、服务名、热更新等）需可配置且不影响代码。
- CLI 启动方式需与现有 `python -m app.main` 并存，且两种方式可独立验证完整流程。
- `langgraph dev` 应能在本地启动并触发一次完整流程；`langgraph up` 应能以与 dev 一致的配置启动（用于部署/容器化场景）。

### 1.6) 容器镜像构建支持（新增）
- 必须提供容器镜像构建方式（推荐 Dockerfile），在项目根目录可直接执行 `docker build` 生成镜像。
- 容器基础镜像必须使用 `ubuntu:24.04`。
- 镜像内需包含运行 Agent 所需的依赖与入口，必须明确默认启动命令（`python -m app.main` 或 langgraph CLI 入口）。
- 运行时配置必须通过环境变量注入（支持 `--env-file .env`），镜像中不得写入真实密钥。
- 需确保镜像中 Python 版本与 `langgraph.json` 中的 `python_version` 保持一致。
- 镜像运行配置应与本地 `langgraph dev/up` 一致，避免环境差异导致行为不一致。

### 2) 配置管理
- 所有连接信息必须放在 `.env` 中，代码通过环境变量读取：
  - Milvus：地址、端口、用户名/密码（若有）、集合名/分区名等。
  - mem0：Endpoint、API Key（若有）、工作空间/项目 id 等。
  - LLM：API Key、Endpoint、模型名、超时等。
  - Langfuse：Public Key、Secret Key、Host（或 Endpoint）、项目/环境标识（若需）。
  - MCP：Server Endpoint、Transport 类型（stdio/HTTP/SSE）、鉴权信息（若需）、默认工具名等。
- 不得在代码中硬编码任何连接密钥或 Endpoint。

### 3) 运行与环境
- 使用 `uv` 作为依赖管理与运行工具。
- 提供最小可运行的 `pyproject.toml` 与启动说明（在 README 或 docs 中）。
- 代码需在本地环境可运行，默认使用 `.env` 中的配置。
- 需提供 langgraph CLI 配置与说明，确保 `langgraph dev`/`langgraph up` 可在本地运行。
- 需选定并配置 langgraph 内置的 checkpoint 实现（如内存或持久化方案），并确保可运行；实现需支持后续可切换到外部持久化存储。
- 如需容器构建与运行，要求 Docker/Podman 可用，且构建流程可复现。

### 4) 可观测性与验证
- 每个节点必须输出基本日志（开始、成功、失败），便于排错。
- Agent 的最终返回内容必须包含每个组件的调用状态与关键结果，用于明确验证调用成功。
- 发生异常时应捕获并输出错误信息，确保流程可诊断。
- Langfuse trace 必须可用：执行一次流程后，可在 Langfuse 中看到该次运行及关键节点 span。

## 非功能需求
- 可维护性：模块化结构，节点功能清晰。
- 可复用性：核心逻辑与配置读取解耦。
- 最小化实现：避免过度封装，优先完成验证链路。
- 开发方式：采用测试驱动开发（TDD）。实现流程必须为“先写测试，再写功能”；测试初次执行应失败，功能实现后测试应通过。
- 可部署性：容器镜像构建过程可追溯、可复现，且不引入配置泄露风险。

## 目录与代码结构建议
- `app/`：应用代码
  - `main.py`：入口
  - `graph.py`：langgraph 流程定义
  - `nodes/`：各节点逻辑（milvus、mem0、llm、mcp）
  - `config.py`：读取 `.env` 并解析配置
- `docs/`：需求与说明文档
- `.env.example`：示例配置文件（不含真实密钥）
- `langgraph.json` 或 `langgraph.yaml`：langgraph CLI 配置文件

## 关键流程示意
1. 读取 `.env` -> 初始化客户端（Milvus、mem0、LLM、MCP、Langfuse）。
2. langgraph 运行：
   - 节点 A（Milvus）：写入向量 -> 检索验证。
   - 节点 B（mem0）：写入记忆 -> 检索验证。
   - 节点 C（LLM）：调用模型 -> 返回结果。
   - 节点 D（MCP）：调用 MCP 工具 -> 返回结果。
   - 运行中启用 langgraph checkpoint，保存执行状态以便恢复。
   - 关键节点需形成 Langfuse trace/span。
3. 汇总并输出验证结果（结构化返回，含各节点状态与关键返回值）。

## 返回结果要求（用于明确验证成功）
- 返回格式：结构化对象（推荐 JSON 字典）。
- 必含字段：
  - `milvus`: `{ status, write_id, query_result }`
  - `mem0`: `{ status, memory_id, query_result }`
  - `llm`: `{ status, model, output_text }`
  - `mcp`: `{ status, tool_name, tool_result }`
- 成功判定：四个 `status` 均为 `success` 且关键字段非空。

## 验收标准
- 可通过一次命令运行 Agent，并在控制台看到四类调用均成功的日志。
- 可通过 `langgraph dev` 启动并触发一次完整流程。
- 可通过 `langgraph up` 启动并与 dev 使用同一份配置。
- `.env` 中修改配置后，无需改代码即可切换连接。
- 任一服务不可用时，日志可明确指出失败节点与原因。
- 可通过 `docker build` 构建出镜像，并能以 `--env-file .env` 的方式启动 Agent。

## 开放问题
- Milvus 与 mem0 的具体版本、认证方式与 SDK 版本要求。
- LLM 使用的具体供应商与模型名称。
- MCP Server 的 transport 类型、工具清单与鉴权方式。
- 期望的输出格式（JSON、文本、或两者）。
- langgraph CLI 的目标部署方式（本地、容器、或远端）与配置文件格式偏好（JSON/YAML）。
- 容器镜像的构建策略（uv/pip）与默认入口命令的偏好。
- 是否要求镜像支持 `langgraph up` 的构建流程或独立 `docker build` 即可。

## 里程碑建议
- M1：完成项目初始化（uv + pyproject + 目录结构）。
- M2：完成各节点最小调用与本地运行（含 MCP）。
- M3：接入 langgraph 并形成完整流程。
- M4：完善日志、文档与示例配置。
- M5：补齐 langgraph CLI 启动支持（dev/up 配置与文档）。
- M6：补齐容器镜像构建支持（Dockerfile、构建与运行文档、验证）。
