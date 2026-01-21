# 任务拆解与进度跟踪

## 状态约定
- TODO：未开始
- DOING：进行中
- BLOCKED：阻塞
- DONE：已完成

## 任务清单（按里程碑）

### M0 需求澄清与前置（已完成）
- [x] T0-1 确认 Milvus 版本、认证方式、SDK（DONE）
- [x] T0-2 确认 mem0 服务地址、接口路径、认证方式与请求结构（按 `example/mem0.py`）（DONE）
- [x] T0-3 确认 LLM 供应商、模型名、API 兼容性（DONE）
- [x] T0-4 确认 MCP Server transport 类型、工具清单与鉴权方式（DONE）
- [x] T0-5 确认 Langfuse 版本/部署方式与项目配置（DONE）
- [x] T0-6 明确输出格式要求（严格 JSON）（DONE）
- [x] T0-7 明确 langgraph checkpoint 方案与存储位置（MemorySaver，可切换为持久化）（DONE）

### M1 项目初始化（uv + 结构）
- [x] T1-1 初始化项目结构：`app/`、`app/nodes/`、`docs/`（DONE）
- [x] T1-2 使用 uv 管理依赖（requirements.txt/requirements-dev.txt，包含 langgraph、langfuse、mcp、milvus SDK、requests、dotenv、pytest 等）（DONE）
- [x] T1-3 添加 `.env.example` 并列出完整配置项（含 MCP、Langfuse、checkpoint 配置）（DONE）
- [x] T1-4 编写运行说明文档（README 或 `docs/` 内）（DONE）

### M2 测试基础与配置闭环
- [x] T2-1 建立测试目录与约定（例如 `tests/`，pytest 配置）（DONE）
- [x] T2-2 为配置读取编写单元测试（先失败）（DONE）
- [x] T2-3 实现配置读取模块 `app/config.py`（使 T2-2 通过）（DONE）

### M3 LLM 接入闭环（先测后实现）
- [x] T3-1 为 LLM 节点编写最小可用单元测试（先失败）（DONE）
- [x] T3-2 实现 LLM 节点：调用模型并返回结果（使 T3-1 通过）（DONE）
- [x] T3-3 LLM 节点日志与异常处理完善（DONE）

### M4 mem0 接入闭环（先测后实现）
- [x] T4-1 为 mem0 节点编写最小可用单元测试（按 `example/mem0.py` 的 HTTP 调用方式，先失败）（DONE）
- [x] T4-2 实现 mem0 节点：写入记忆 + 检索（按 HTTP 方式，使 T4-1 通过）（DONE）
- [x] T4-3 mem0 节点日志与异常处理完善（DONE）

### M5 Milvus 接入闭环（先测后实现）
- [x] T5-1 为 Milvus 节点编写最小可用单元测试（先失败）（DONE）
- [x] T5-2 实现 Milvus 节点：写入向量 + 检索（使 T5-1 通过）（DONE）
- [x] T5-3 Milvus 节点日志与异常处理完善（DONE）

### M6 Langfuse 接入闭环（先测后实现）
- [x] T6-1 为 Langfuse trace/span 编写最小可用单元测试（先失败）（DONE）
- [x] T6-2 接入 Langfuse trace/span（使 T6-1 通过）（DONE）
- [x] T6-3 Agent 实际流程接入 Langfuse（外层创建 trace，节点内创建 span 并串联上下文）（DONE）
  - [x] T6-3-1 设计 Langfuse trace 上下文传递与节点 span 归属（DONE）
  - [x] T6-3-2 添加 run_agent + 节点 span 集成测试（先失败）（DONE）
  - [x] T6-3-3 实现外层 trace + 节点 span 逻辑（DONE）

### M7 MCP 接入闭环（先测后实现）
- [x] T7-1 为 MCP 节点编写最小可用单元测试（先失败）（DONE）
- [x] T7-2 实现 MCP 节点：调用 MCP 工具并返回结果（使 T7-1 通过）（DONE）
- [x] T7-3 MCP 节点日志与异常处理完善（DONE）

### M8 langgraph 编排与全流程闭环
- [x] T8-1 定义 langgraph 流程 `app/graph.py`（DONE）
- [x] T8-2 串联节点：LLM -> mem0 -> Milvus -> MCP（DONE）
- [x] T8-3 接入 langgraph 内置 checkpoint（MemorySaver）并预留切换为持久化的配置与实现接口（DONE）
- [x] T8-4 入口脚本 `app/main.py`，支持 CLI 执行（DONE）
- [x] T8-5 汇总返回结构化结果（含状态与关键返回值）（DONE）
- [x] T8-6 全流程集成测试（非 e2e，先失败，再通过）（DONE）

### M9 LangGraph CLI 启动支持
- [x] T9-1 确认 langgraph CLI 版本与配置文件格式（langgraph.json/langgraph.yaml）（DONE）
- [x] T9-2 添加 langgraph CLI 配置文件，绑定 graph 入口并加载 `.env`（DONE）
- [x] T9-3 验证 `langgraph dev` 可启动并触发完整流程（DONE）
- [ ] T9-4 验证 `langgraph up` 可启动且配置与 dev 一致（BLOCKED）
- [x] T9-5 更新运行文档，补充 `langgraph dev`/`langgraph up` 使用说明（DONE）
- [x] T9-6 `langgraph dev` 启动时 Langfuse trace 生效（DONE）
  - [x] T9-6-1 设计 trace 上下文注入与 graph wrapper 方案（DONE）
  - [x] T9-6-2 添加 langgraph dev 入口的 Langfuse 集成测试（先失败）（DONE）
  - [x] T9-6-3 实现 trace 注入与 wrapper（DONE）
  - [x] T9-6-4 修复 langgraph dev 的 Graph 类型校验并改为节点内惰性创建 trace（DONE）

### M10 E2E 与收尾验证
- [x] T10-1 LLM 单组件 e2e 验证（真实服务）（DONE）
- [ ] T10-2 mem0 单组件 e2e 验证（真实服务）（TODO）
- [ ] T10-3 Milvus 单组件 e2e 验证（真实服务）（TODO）
- [ ] T10-4 MCP 单组件 e2e 验证（真实服务）（TODO）
- [ ] T10-5 Langfuse trace/span e2e 验证（可见 trace/span）（TODO）
- [ ] T10-6 全流程 e2e 验证（一次命令跑通）（TODO）
- [ ] T10-7 验证 checkpoint 生效（可恢复/可重放）（TODO）
- [ ] T10-8 验证结构化返回满足必含字段要求（TODO）
- [ ] T10-9 补充错误场景日志（服务不可用/鉴权失败）（TODO）
- [ ] T10-10 文档完善：使用说明、配置说明、排错说明（TODO）

### M11 容器镜像构建支持
- [x] T11-1 明确镜像构建方案（基础镜像为 `ubuntu:24.04`、依赖安装策略、默认入口命令）（DONE）
- [x] T11-2 添加 `Dockerfile` 与 `.dockerignore`（DONE）
- [x] T11-3 更新容器构建与运行说明（补充到 `docs/run.md`）（DONE）
- [x] T11-4 本地验证 `docker build` 与 `docker run --env-file .env`（DONE）
- [x] T11-5 验证容器运行配置与 `langgraph dev/up` 一致（DONE）

### M12 Kubernetes 部署支持
- [x] T12-1 明确 K8s 部署模式（Job/CronJob）与入口命令（`python -m app.main`）（DONE）
- [x] T12-2 添加 `k8s/` 清单（Job 或 CronJob、ConfigMap/Secret）（DONE）
- [x] T12-3 支持通过环境变量/参数配置运行参数（DONE）
- [x] T12-4 更新部署文档：Secret/ConfigMap 创建与 `kubectl apply` 流程（DONE）
- [ ] T12-5 本地或测试集群验证部署（kind/minikube/任意集群）（BLOCKED：当前无可用集群/权限）

## 依赖与阻塞项
- 未明确版本与认证方式或 mem0 HTTP 接口细节时，节点实现可能阻塞（T0-1/T0-2/T0-3/T0-4/T0-5）。
- 输出格式未确认时，汇总输出与日志格式可能需返工（T0-6）。
- checkpoint 方案未确定时，运行编排与持久化可能阻塞（T0-7）。
- langgraph CLI 配置格式与启动方式未确认时，CLI 支持任务可能阻塞（T9-1）。
- `langgraph up` 缺少许可证相关环境变量时无法启动（T9-4）。
- 容器镜像构建依赖 Docker/Podman 可用，且需确定基础镜像与入口策略（T11-1）。
- K8s 部署模式与入口命令未确认时，清单与验证会阻塞（T12-1）。
- 集群环境/镜像仓库不可用时，K8s 验证可能阻塞（T12-5）。

## 交付检查清单
- [ ] 单次命令可运行 Agent
- [ ] 可通过 `langgraph dev` 启动并完成一次流程
- [ ] 可通过 `langgraph up` 启动并与 dev 使用同一份配置
- [ ] 控制台日志能看到四类调用成功
- [ ] 结构化返回包含 `milvus`/`mem0`/`llm`/`mcp` 状态与关键返回值
- [ ] Langfuse 可看到该次运行及关键节点 span
- [ ] checkpoint 启用且可验证生效
- [ ] `.env` 修改后无需改代码即可切换配置
- [ ] 失败时能定位到具体节点与原因
- [ ] 可通过 `docker build` 构建容器镜像并运行 Agent
- [ ] 可通过 `k8s/` 清单在 Kubernetes 上部署并运行 Agent
