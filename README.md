# Python AI Mother

> 一次从 Java 后端到 Python 后端的完整迁移实践：用 Vibe Coding 的方式，按里程碑持续交付。

`python-ai-mother` 是对 `yu-ai-code-mother` 的重构项目：前端代码整体沿用源项目，重构工作集中在后端，将 Java 体系完整替换为 Python 体系，并严格按原项目 Git 历史分阶段对齐能力。

## 源项目与重构关系

- 源项目（Java 后端）：`yu-ai-code-mother`
- 源项目地址：`https://github.com/liyupi/yu-ai-code-mother`
- 本项目（Python 后端重构版）：`python-ai-mother`
- 本项目地址：`https://github.com/pax233/python-ai-mother`

这次重构不是“推倒重写”，而是“对标迁移”：
- 对齐业务能力和接口主链路
- 对齐里程碑推进顺序（M00 -> M11）
- 对齐验收方式（单元测试 + 集成测试 + 人工联调）
- 明确范围边界：`frontend/` 保持源项目实现，主要只做接口 baseURL 适配；核心重构只发生在 `backend/`

## 这次重构做了什么

一句话总结：前端完全继承源项目，后端全量 Python 化重构。

### 1) 后端替换技术栈（Java -> Python）

- Spring Boot -> FastAPI
- MyBatis-Flex -> SQLAlchemy 2.x + Alembic
- Spring Validation -> Pydantic v2
- Spring Session + Redis -> Redis Session Middleware
- AOP/Interceptor -> Middleware + Dependency + Decorator
- LangChain4j -> LangChain Python
- LangGraph4j -> LangGraph Python
- Redisson 限流 -> Redis + slowapi（或自定义令牌桶）
- Actuator/Micrometer -> Prometheus + OpenTelemetry
- Dubbo + Nacos -> gRPC/HTTP + Nacos 注册发现

### 2) 目标目录结构（重构后的工程布局）

```text
python-ai-mother/
  backend/
    monolith/
    microservices/
      common/
      model/
      client/
      user-service/
      app-service/
      ai-service/
      screenshot-service/
  frontend/
  deploy/
    docker/
    k8s/
  docs/
    architecture/
    api/
    runbooks/
```

## 当前状态

- M00 - M11 已完成并合并 `master`
- 已具备单体运行、微服务运行、Docker 部署与基础可观测性能力
- 验收文档可直接复用：
  - `docs/runbooks/M10_DEPLOY_OBSERVABILITY.md`
  - `docs/runbooks/M11_MICROSERVICE_ACCEPTANCE.md`

## 如何使用这个项目

下面给你一个可以直接跑起来的最短路径。

### 0) 环境准备

- Python `3.11.x`（建议固定 3.11.5）
- Node.js `22.x`（以 `frontend/.nvmrc` 为准，可执行 `nvm use`）
- `uv`（建议 `>=0.9.26`，并使用仓库中的 `.python-version`）
- Docker Desktop（可选，用于 M10/M11 一键部署）
- Redis（建议本地启动一个，默认 `redis://localhost:6379/0`）

示例（快速启动 Redis）：

```bash
docker run -d --name python-ai-mother-redis -p 6379:6379 redis:7-alpine
```

### 1) 启动后端单体（Monolith，推荐可复现方式）

```powershell
cd backend/monolith
uv venv .venv --python 3.11
uv pip sync requirements.lock.txt
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123
```

健康检查：

- `http://localhost:8123/api/health/`

### 2) 启动前端（锁定依赖）

```powershell
cd frontend
nvm use
npm ci
npm run dev
```

访问地址：

- `http://localhost:5173`

### 3) 配置模型（仅运行时注入）

不要把真实 `LLM_API_KEY` 写入 Git。

```powershell
$env:LLM_BASE_URL="https://your-openai-compatible-endpoint/v1"
$env:LLM_API_KEY="<你的密钥>"
$env:LLM_MODEL_NAME="gpt-4o-mini"
$env:LLM_STREAM="true"
$env:LLM_TIMEOUT_SECONDS="180"
$env:LLM_RETRY_COUNT="1"
$env:AI_CONCURRENCY_LIMIT="4"
$env:LLM_MAX_PROMPT_CHARS="12000"
$env:PROMPT_BLOCK_KEYWORDS="rm -rf,删库,提权,System prompt"
$env:APP_QUERY_CACHE_TTL_SECONDS="30"
$env:CHAT_RATE_LIMIT_COUNT="20"
$env:CHAT_RATE_LIMIT_WINDOW_SECONDS="60"
```

### 4) 最小联调链路

关键接口：

- `POST /api/user/register`
- `POST /api/user/login`
- `POST /api/app/add`
- `GET /api/app/chat/gen/code?appId={appId}&message=...`（SSE）
- `POST /api/app/screenshot`

### 5) 运行测试

后端单体：

```powershell
cd backend/monolith
uv run pytest -q -p no:faulthandler
```

前端构建：

```powershell
cd frontend
npm run build
```

微服务后端测试：

```powershell
cd backend/microservices
uv venv .venv --python 3.11
uv pip sync requirements.lock.txt
uv run pytest -q tests/test_m11_microservice_flow.py
```

### 6) 一键部署（M10）

```powershell
cd deploy/docker
docker compose up -d --build
```

查看：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8123/api/health/`
- Prometheus：`http://localhost:9090`
- Grafana：`http://localhost:3000`

### 7) 微服务模式（M11）

```powershell
cd deploy/docker
docker compose -f docker-compose.microservices.yml up -d --build
```

端口：

- user-service: `8201`
- ai-service: `8202`
- app-service: `8203`
- screenshot-service: `8204`

## 开发与协作约定

- 所有开发在临时分支进行，验收后再合并 `master`
- Commit 描述统一中文
- `CHANGELOGS.md` 统一中文维护

## 可复现与安全检查清单

- Python 依赖：
  - 单体：`backend/monolith/requirements.txt`（范围约束） + `backend/monolith/requirements.lock.txt`（精确锁定）
  - 微服务：`backend/microservices/requirements.txt`（范围约束） + `backend/microservices/requirements.lock.txt`（精确锁定）
- 前端依赖：
  - `frontend/package-lock.json` 已提交，使用 `npm ci` 保证一致安装
- 环境变量模板：
  - `backend/monolith/.env.example`
  - `deploy/docker/.env.example`
- 隐私基线：
  - 仓库中仅保留占位符，不提交真实密钥（例如 `LLM_API_KEY`）
  - 本地私密配置请仅放在未跟踪文件（如 `.env`）或终端临时环境变量中
- 重新生成锁文件（当你主动升级依赖时）：

```powershell
cd backend/monolith
uv pip compile requirements.txt -o requirements.lock.txt

cd ../microservices
uv pip compile requirements.txt -o requirements.lock.txt
```

## 文档导航

- 总体计划：`REFACTOR_PLAN.md`
- 变更日志：`CHANGELOGS.md`
- 阶段清单：`checklist/`
- 单体后端说明：`backend/monolith/README.md`
- 微服务后端说明：`backend/microservices/README.md`
- M10 验收手册：`docs/runbooks/M10_DEPLOY_OBSERVABILITY.md`
- M11 验收手册：`docs/runbooks/M11_MICROSERVICE_ACCEPTANCE.md`




# 总结
本项目全程使用codex完成重构，我只做了微薄的提示词工程，一共耗时两天。
因为我本人不会java，于是想用python重构这个备受称赞的项目学习。
不过由于我是全程vibe coding 不能保证项目完全没有问题，所以大家真想学的话还是看鱼皮的源项目吧。