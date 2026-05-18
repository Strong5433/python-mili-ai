# backend/monolith

## 1. 环境准备（项目内虚拟环境）

```bash
uv venv .venv --python 3.11
uv pip sync requirements.lock.txt
```

## 2. 数据库迁移

```bash
uv run alembic upgrade head
uv run alembic current
```

## 3. 启动后端

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123
```

或使用脚本：

```powershell
./scripts/run_dev.ps1
```

## 4. 运行测试

```bash
uv run pytest -q -p no:faulthandler
```

或使用脚本：

```powershell
./scripts/run_test.ps1
```

## 5. M01 用户接口

- `POST /api/user/register`
- `POST /api/user/login`
- `GET /api/user/get/login`
- `POST /api/user/logout`
- `GET /api/user/admin/ping`（admin 权限示例）

统一响应格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

## 6. M02 应用生成接口

- `POST /api/app/add`
- `GET /api/app/get/vo?id={appId}`
- `GET /api/app/chat/gen/code?appId={appId}&message=...`（SSE）

## 7. M06 扩展接口

- `POST /api/app/route/codegen`
- `POST /api/app/screenshot`
- `GET /api/app/download/project/{appId}`

## 8. M07 版本管理接口

- `POST /api/app/version/snapshot`
- `GET /api/app/version/list?appId={appId}`
- `POST /api/app/version/rollback`
- `GET /api/app/chat/gen/code?...&editMode=full|incremental`

## 9. M08 工作流接口

- `GET /api/app/chat/gen/workflow?appId={appId}&message=...&editMode=...`（SSE）

## 10. 模型环境变量（仅运行时）

不要把真实密钥写入仓库文件（包括 `.env.example`、`README`、提交记录）。

```powershell
$env:LLM_BASE_URL="https://your-openai-compatible-endpoint/v1"
$env:LLM_API_KEY="<你的密钥>"
$env:LLM_MODEL_NAME="gpt-5.1-codex-mini"
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

## 11. M09 系统优化说明

- 并发：AI 调用链路增加并发信号量控制（`AI_CONCURRENCY_LIMIT`）
- 稳定性：模型请求支持重试（`LLM_RETRY_COUNT`）
- 安全：Prompt 违规关键词拦截 + 长度截断（`PROMPT_BLOCK_KEYWORDS`、`LLM_MAX_PROMPT_CHARS`）
- 限流：`/api/app/chat/gen/code`、`/api/app/chat/gen/workflow` 按用户限流（`CHAT_RATE_LIMIT_*`）
- 缓存：应用分页查询增加热点缓存（`APP_QUERY_CACHE_TTL_SECONDS`）

## 12. M10 监控指标

- 指标端点：`GET /metrics`
- 关键指标：
  - `python_ai_mother_http_requests_total`
  - `python_ai_mother_http_request_duration_seconds_*`


