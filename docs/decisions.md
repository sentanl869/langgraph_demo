# 决策记录

## M0-1 Milvus
- 版本：2.6.9（最新）
- SDK：pymilvus 最新版本
- 认证：用户名/密码，配置在 `.env`
- 部署形态：standalone/cluster 均需兼容，但 Agent 实现不依赖形态，仅依赖连接配置

## M0-2 mem0（HTTP 封装方式）
- base URL：通过 `MEM0_SERVER_URL` 配置，写入 `.env`
- 认证：使用 `Authorization: Token <API_KEY>`，调用方式完全参考 `example/mem0.py`
- 接口路径：暂定固定为 `/memories/` 与 `/search/`，需评估是否满足需求

## M0-3 LLM
- 供应商：自建或其他第三方
- API 兼容性：兼容 OpenAI API
- 模型 ID：从 `.env` 获取
- Endpoint：从 `.env` 获取

## M0-4 MCP
- Transport：需兼容 stdio/HTTP/SSE
- Server 地址：从 `.env` 获取
- 工具名：从 `.env` 获取
- 鉴权：暂无

## M0-5 Langfuse
- 部署方式：自建
- Host：从 `.env` 获取
- 环境标识：需要，作为 trace metadata 使用

## M0-6 输出格式
- 严格 JSON

## M0-7 langgraph checkpoint
- 方案：MemorySaver（内存），实现需支持后续切换为外部持久化存储

## M1-2 依赖与运行环境
- Python 版本：>=3.10
- 依赖：langgraph、langfuse、mcp、pymilvus、requests、python-dotenv、openai
- 开发依赖：pytest
- 依赖管理：不使用 `pyproject.toml`，改为 `requirements.txt` 与 `requirements-dev.txt`，通过 `uv pip install -r ...` 安装

## M1-3 配置项命名（.env.example）
- Milvus：MILVUS_HOST、MILVUS_PORT、MILVUS_USERNAME、MILVUS_PASSWORD、MILVUS_COLLECTION、MILVUS_PARTITION、MILVUS_DB_NAME
- mem0：MEM0_SERVER_URL、MEM0_API_KEY、MEM0_USER_ID
- LLM：LLM_API_KEY、LLM_ENDPOINT、LLM_MODEL、LLM_TIMEOUT、LLM_TEMPERATURE
- Langfuse：LANGFUSE_PUBLIC_KEY、LANGFUSE_SECRET_KEY、LANGFUSE_HOST、LANGFUSE_ENV
- MCP：MCP_TRANSPORT、MCP_SERVER_URL、MCP_TOOL_NAME、MCP_API_KEY、MCP_COMMAND、MCP_ARGS
- Checkpoint：CHECKPOINT_BACKEND、CHECKPOINT_PATH

## M1-4 运行说明位置
- 文档路径：`docs/run.md`

## M2-1 测试约定
- 使用 `pytest.ini` 统一配置 pytest
- 测试目录固定为 `tests/`

## M2-2 配置读取设计
- 提供 `load_config()` 返回结构化配置对象（分组为 milvus/mem0/llm/langfuse/mcp/checkpoint）
- 数值型字段进行类型转换（例如端口、超时、温度）
- 空字符串统一归一为 `None`，`MCP_ARGS` 使用 `shlex.split` 解析为列表

## M2-3 测试导入路径
- 使用 `tests/conftest.py` 将项目根目录加入 `sys.path`，保证 `app` 可被 pytest 导入

## M3-1 LLM 节点实现
- 使用 `openai.OpenAI` 客户端，`LLM_ENDPOINT` 映射为 `base_url`
- 消息结构为 `system`（可选）+ `user`
- 输出为 `{status, model, output_text}`，失败时补充 `error` 并返回 `status=failed`
- 节点日志包含开始/成功/失败（异常栈通过 logger.exception 输出）

## M3-2 LLM 单组件验证前置
- 需要提供真实的 `LLM_ENDPOINT` 与 `LLM_API_KEY`（写入 `.env`）后再执行单组件验证

## M3-3 LLM 单组件验证方式
- 使用 `load_config().llm` + `run_llm_node("ping")` 进行真实服务连通性验证

## M3-4 LLM e2e 测试触发方式
- e2e 测试放在 `e2e/`，默认 `pytest` 不执行
- 仅在执行 `pytest e2e` 时运行该目录下用例

## M4-1 mem0 节点实现约定
- HTTP 调用沿用 `example/mem0.py`：`/memories/` 写入、`/search/` 查询，Headers 含 `Content-Type` 与可选 `Authorization: Token <API_KEY>`
- `memory_id` 取写入响应的 `id` 字段，缺失则返回 `None`
- `query_result` 原样返回查询响应 JSON
- URL 通过 `server_url.rstrip("/")` 拼接，避免双斜杠

## M5-1 Milvus 节点实现约定
- 使用 `pymilvus.connections.connect` 建立连接，`alias=default`，`db_name` 由配置透传
- 默认向集合写入字段 `embedding`，实体为 `[{ "embedding": vector }]`，集合需预先具备同名向量字段
- 检索使用 `collection.search`，`anns_field=embedding`，`metric_type=L2`，`nprobe=10`
- 仅取 `insert_result.primary_keys` 的首个值作为 `write_id`
- 搜索结果优先调用 `to_dict()` 转为可 JSON 序列化结构

## M6-1 Langfuse trace/span 实现约定
- 通过 `Langfuse(public_key, secret_key, host)` 初始化客户端
- Trace metadata 默认包含 `env`（来自 `LANGFUSE_ENV`），允许额外 metadata 覆盖/扩展
- Span metadata 透传入参，不做合并处理
- 返回 `trace_id`/`span_id`（若对象无 id 则为 `None`），异常返回 `status=failed` 与 `error`

## M6-2 Agent 运行 Langfuse 集成方式
- `run_agent` 外层创建一次 trace（配置齐全时启用），并将 trace 以闭包方式传入 `build_graph`
- 节点执行时在 wrapper 内创建 span（metadata 至少包含 `node`），避免在 state 中保存 trace 对象以保持 checkpoint 可序列化
- span 结束采用 `span.end()` 的可选调用（有该方法则调用，无则忽略），不依赖额外输出字段
- trace metadata 额外包含 `thread_id`，用于关联一次执行

## M7-1 MCP 节点实现约定
- transport 通过 `MCP_TRANSPORT` 选择：`stdio` 使用 `MCP_COMMAND` + `MCP_ARGS`；`http`/`sse` 使用 `MCP_SERVER_URL`
- 调用前初始化 MCP `ClientSession`，执行 `initialize()` 后再 `call_tool(tool_name, tool_args)`
- HTTP/SSE 传入 `Authorization: Bearer <API_KEY>`（如配置 `MCP_API_KEY`）
- 未提供 `tool_name` 或 transport 缺少必填配置时抛错并返回 `status=failed`

## M8-1 langgraph 状态与默认值
- `AgentState` 统一存放 `prompt`、`mem0_query`、`milvus_vector`、`milvus_query_vector`、`mcp_tool_args` 及四类节点结果与最终 `result`
- mem0 写入内容优先使用 LLM 输出 `output_text`，否则回退到 `prompt`
- `mem0_query` 缺省时使用固定问题文案；Milvus 向量缺省使用固定默认向量

## M8-2 checkpoint 与运行约定
- `build_checkpointer` 默认选择 `MemorySaver`；`sqlite` 后端需配置 `CHECKPOINT_PATH`
- `run_agent` 在启用 checkpointer 时必须传 `thread_id`，缺省回退为 `"default"`
- CLI 未指定 `--thread-id` 时生成随机 `uuid` 作为 thread id
- `sqlite` 后端依赖额外的 langgraph sqlite checkpoint 包，缺失时抛出运行时错误

## M8-3 CLI 入参约定
- CLI 支持 `--prompt`、`--mem0-query`、`--mcp-args`（JSON 对象字符串）
- `--mcp-args` 非 JSON 或非对象时视为错误

## M9-1 LangGraph CLI 版本与配置格式
- CLI 包：`langgraph-cli==0.4.11`（提供 `langgraph dev/up` 命令）
- 配置文件：仅支持 JSON（默认 `langgraph.json`），当前版本不支持 YAML
- 关键字段：`dependencies`（含 `"."` 本地依赖）、`graphs`（`module.py:graph`）、`env`（指向 `./.env`）

## M9-2 LangGraph CLI 配置与入口
- 配置文件：`langgraph.json`
- graph id：`validation_agent`
- graph 入口：`./app/langgraph_app.py:graph`（模块内预编译 graph）
- 依赖：`dependencies` 使用 `"."` 以加载当前项目与 `requirements.txt`
- 环境变量：`env` 指向 `./.env`，由 CLI 加载

## M9-3 LangGraph CLI dev 验证方式
- `langgraph dev --config langgraph.json` 已由用户本地验证通过
- 由于当前运行环境限制端口绑定，开发机验证结果作为准入记录

## M9-4 LangGraph CLI up 打包方式
- 新增 `setup.py`，将项目识别为可安装包，避免 langgraph CLI Docker 构建中 `uv pip install -e .` 失败
- 依赖仍以 `requirements.txt` 为唯一来源，`setup.py` 读取并作为 `install_requires`

## M9-4 LangGraph CLI up 启动失败原因
- `langgraph up` 默认使用 licensed 运行时，需要许可证校验
- 缺少 `LANGSMITH_API_KEY`（具备 LangGraph Cloud 访问权限）或 `LANGGRAPH_CLOUD_LICENSE_KEY`，导致容器启动失败

## M9-5 运行文档补充范围
- `docs/run.md` 增加 `langgraph dev`/`langgraph up` 启动方式与示例命令
- 标注 `langgraph.json` 配置使用与许可证环境变量要求

## M9-6 Langgraph dev 的 Langfuse trace 注入方式
- 使用 `contextvars` 保存当前运行的 trace，不写入 state，避免 checkpoint 序列化问题
- `build_graph` 的节点 wrapper 优先使用显式传入的 trace；未传入时在首个节点内惰性创建 trace 并写入上下文
- trace metadata 读取 `configurable.thread_id`（缺省为 `default`），并在 `final` 节点结束后清理上下文
- `app/langgraph_app.py` 仍导出编译后的 `Pregel` graph，避免 wrapper 导致类型校验失败

## M11-1 容器镜像构建方案
- 基础镜像：`ubuntu:24.04`
- Python：使用系统包 `python3`（Ubuntu 24.04 默认 3.12），满足 `langgraph.json` 的版本要求
- 依赖安装：容器内创建 `/opt/venv`，使用 `uv pip install -r requirements.txt` 安装运行依赖
- 默认入口：`python -m app.main`，需要时可覆盖为 `langgraph dev --config langgraph.json`
- 构建上下文：通过 `.dockerignore` 排除 `.env` 等敏感文件，避免密钥进入镜像

## M11-2 容器验证与一致性
- 本地完成 `docker build` 与 `docker run --env-file .env` 验证，镜像可启动
- 容器运行依赖 `.env` 与 `langgraph.json`，与本地 `langgraph dev/up` 使用同一份配置
- 运行时 mem0/Milvus 需外部服务可用；未启动时会返回连接失败（符合预期）
