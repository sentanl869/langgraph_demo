# 运行说明

## 前置条件
- Python >= 3.10
- 已安装 `uv`

## 安装依赖
```bash
uv venv .venv
uv pip install -r requirements.txt -r requirements-dev.txt
```

## 配置环境变量
```bash
cp .env.example .env
# 按实际环境修改 .env
```

## 运行入口
```bash
python -m app.main
```

## LangGraph CLI 启动
> 需安装 `langgraph-cli`，并在项目根目录执行命令。

### 开发模式（dev）
```bash
.venv/bin/langgraph dev --config langgraph.json
```

### 部署模式（up）
> 需 Docker 可用，且设置许可证相关环境变量后才能启动。
```bash
.venv/bin/langgraph up --config langgraph.json
```

#### 许可证环境变量（二选一）
- `LANGSMITH_API_KEY`（具备 LangGraph Cloud 访问权限）
- `LANGGRAPH_CLOUD_LICENSE_KEY`

## 容器镜像构建与运行
> 基础镜像为 `ubuntu:24.04`，容器内使用 Python 3.12 运行。

### 构建镜像
```bash
docker build -t langgraph-demo:local .
```

### 运行默认入口（python -m app.main）
```bash
docker run --rm --env-file .env langgraph-demo:local
```

### 运行 LangGraph CLI（可选）
```bash
docker run --rm --env-file .env langgraph-demo:local \
  langgraph dev --config langgraph.json
```

## Kubernetes 部署（Job）
> 仅支持 `python -m app.main` 入口，不要求 `langgraph up`。

### 准备镜像
- 确保 `k8s/job.yaml` 中的 `image` 指向可被集群拉取的镜像。

### 创建 Secret（从 .env）
```bash
kubectl create secret generic langgraph-demo-env --from-env-file=.env
```

### 应用 ConfigMap 与 Job
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/job.yaml
```

### 查看运行结果
```bash
kubectl logs job/langgraph-demo
```

### 修改运行参数
- 编辑 `k8s/configmap.yaml` 中的 `AGENT_*` 字段后重新 `kubectl apply`。

## 测试
```bash
pytest
```

## e2e 测试
```bash
pytest e2e
```
