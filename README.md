# 米粒 AI 应用生成平台

## 项目概述

本项目是一个基于 Python 的 AI 应用生成平台后端单体架构，采用 FastAPI 框架构建，支持用户通过自然语言描述生成完整的 Web 应用。项目采用模块化设计，具备完整的业务逻辑、自动化测试和监控体系。

## 项目结构分析

### 整体目录结构
```
backend/monolith/app/
├── ai/                          # AI 服务层
│   ├── codegen_routing_service.py    # 代码生成路由服务
│   └── openai_compatible_service.py  # OpenAI 兼容服务
├── api/                         # API 接口层
│   ├── app.py                   # 应用相关接口
│   ├── chat_history.py          # 聊天历史接口
│   ├── health.py                # 健康检查接口
│   ├── router.py                # 路由聚合器
│   └── user.py                  # 用户相关接口
├── core/                        # 核心业务逻辑层
│   ├── ai_codegen_facade.py     # AI 代码生成门面
│   ├── code_file_saver.py       # 代码文件保存器
│   ├── code_gen_types.py        # 代码生成类型定义
│   ├── code_parser.py           # 代码解析器
│   ├── codegen_workflow.py      # 代码生成工作流
│   ├── config.py                # 配置管理
│   ├── edit_modes.py            # 编辑模式定义
│   ├── error_codes.py           # 错误码定义
│   ├── exception_handlers.py    # 异常处理器
│   ├── exceptions.py            # 自定义异常
│   ├── logging_config.py        # 日志配置
│   ├── metrics.py               # 指标监控
│   ├── middleware.py            # 中间件
│   ├── prompt_loader.py         # 提示词加载器
│   ├── resources.py             # 资源管理器
│   ├── response.py              # 响应格式
│   ├── security.py              # 安全相关
│   └── sse.py                   # Server-Sent Events
├── db/                          # 数据库层
│   └── base.py                  # 数据库基类
├── models/                      # 数据模型层
│   ├── app.py                   # 应用模型
│   ├── chat_history.py          # 聊天历史模型
│   └── user.py                  # 用户模型
├── prompts/                     # AI 提示词文件
│   ├── codegen-html-system-prompt.txt
│   ├── codegen-multi-file-system-prompt.txt
│   ├── codegen-routing-system-prompt.txt
│   └── codegen-vue-project-system-prompt.txt
├── schemas/                     # 数据模式层
│   ├── app.py                   # 应用模式
│   ├── chat_history.py          # 聊天历史模式
│   └── user.py                  # 用户模式
├── services/                    # 业务服务层
│   ├── app_service.py           # 应用服务
│   ├── chat_history_service.py  # 聊天历史服务
│   ├── rate_limit_service.py    # 限流服务
│   ├── screenshot_service.py    # 截图服务
│   ├── session_service.py       # 会话服务
│   └── user_service.py          # 用户服务
├── dependencies.py              # 依赖注入定义
└── main.py                      # 应用入口
```

## 业务逻辑框架

### 1. 分层架构设计

#### API 层 (api/)
- **职责**: 接收 HTTP 请求，参数验证，响应格式化
- **特点**: 使用 FastAPI 的路由器和依赖注入系统
- **示例**: 
```python
@router.post("/add", response_model=BaseResponse[int])
async def add_app(
    payload: AppAddRequest,
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[int]:
    app_id = await app_service.add_app(
        db=db, payload=payload, login_user=login_user
    )
    return success_response(app_id)
```

#### 服务层 (services/)
- **职责**: 实现核心业务逻辑，数据持久化操作
- **特点**: 每个服务类对应一个业务领域
- **示例**: 
```python
class AppService:
    async def add_app(self, db: AsyncSession, payload: AppAddRequest, login_user: User) -> int:
        # 业务逻辑实现
        app_name = self._build_app_name(payload.init_prompt)
        new_app = App(app_name=app_name, user_id=login_user.id)
        db.add(new_app)
        await db.commit()
        return new_app.id
```

#### 核心业务层 (core/)
- **职责**: 实现复杂的业务逻辑，如 AI 代码生成、文件处理等
- **特点**: 采用门面模式、策略模式等设计模式
- **示例**: 
```python
class AiCodeGeneratorFacade:
    async def generate_and_save_code_stream(self, app_id: int, user_message: str) -> AsyncIterator:
        # AI 代码生成流程
        system_prompt = load_prompt("codegen-html-system-prompt.txt")
        async for chunk in self.ai_service.generate_stream(system_prompt, user_message):
            yield chunk
        # 解析和保存代码
        parsed_code = self.parser_executor.parse(raw_text)
        self.saver_executor.save(app_id, parsed_code)
```

### 2. 数据流架构

#### 请求处理流程
```
HTTP 请求 → API 路由 → 参数验证 → 依赖注入 → 服务层 → 核心业务 → 数据持久化 → 响应返回
```

#### AI 代码生成流程
```
用户输入 → 提示词组装 → AI 模型调用 → 代码解析 → 文件保存 → 版本管理 → 实时预览
```

### 3. 关键业务模块

#### 用户管理模块
- 用户注册、登录、权限验证
- 会话管理和安全控制
- 管理员权限控制

#### 应用管理模块
- 应用创建、编辑、删除
- 应用版本管理和回滚
- 应用部署和预览

#### AI 代码生成模块
- 多模式代码生成（HTML、多文件、Vue项目）
- 实时流式生成和进度反馈
- 代码解析和文件保存

#### 聊天历史模块
- 对话记录存储和管理
- 消息类型分类（用户、助手）
- 分页查询和搜索

## 代码编写框架

### 1. 配置管理框架

#### 配置类设计
```python
class Settings(BaseSettings):
    app_name: str = "python-ai-mother-backend"
    database_url: str = "sqlite+aiosqlite:///./python_ai_mother.db"
    redis_url: str = "redis://localhost:6379/0"
    
    @lru_cache(maxsize=1)
    def get_settings() -> Settings:
        return Settings()
```

#### 环境配置支持
- 支持 .env 文件配置
- 环境变量优先级最高
- 类型安全的配置验证

### 2. 依赖注入框架

#### 依赖定义
```python
# dependencies.py
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_app_service(
    settings: Settings = Depends(get_settings),
    redis_client: Redis = Depends(get_redis_client),
) -> AppService:
    return AppService(settings, redis_client)
```

#### 资源管理
```python
class ResourceManager:
    async def start(self):
        self.redis_client = await Redis.from_url(self.settings.redis_url)
        
    async def stop(self):
        await self.redis_client.aclose()
```

### 3. 异常处理框架

#### 自定义异常体系
```python
class BusinessException(Exception):
    def __init__(self, error_code: ErrorCode, message: str = ""):
        self.error_code = error_code
        self.message = message or error_code.description

class ErrorCode(Enum):
    SUCCESS = (0, "成功")
    PARAMS_ERROR = (40000, "请求参数错误")
    NO_AUTH_ERROR = (40100, "无权限")
    NOT_FOUND_ERROR = (40400, "请求数据不存在")
    SYSTEM_ERROR = (50000, "系统内部异常")
```

#### 全局异常处理器
```python
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content=error_response(exc.error_code, exc.message)
    )
```

### 4. 中间件框架

#### 中间件链设计
```python
def register_middlewares(app: FastAPI, settings: Settings):
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 请求日志中间件
    app.add_middleware(LoggingMiddleware)
    
    # 限流中间件
    app.add_middleware(RateLimitMiddleware)
```

### 5. 数据访问框架

#### SQLAlchemy 2.0 配置
```python
# db/base.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass
```

#### 异步数据操作
```python
# models/user.py
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_account: Mapped[str] = mapped_column(String(256), unique=True)
    user_password: Mapped[str] = mapped_column(String(512))
    user_name: Mapped[str] = mapped_column(String(256))
    user_role: Mapped[str] = mapped_column(String(64), default="user")
```

### 6. AI 集成框架

#### OpenAI 兼容服务
```python
class OpenAICompatibleService:
    async def generate_stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", self.settings.llm_base_url, 
                                   json={"messages": messages}) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line[6:]
```

#### 代码生成工作流
```python
class CodeGenWorkflowRunner:
    async def run_workflow(self, app_id: int, user_message: str) -> AsyncIterator:
        # 1. 验证应用状态
        await self._validate_app_state(app_id)
        
        # 2. 保存用户消息
        await self._save_user_message(app_id, user_message)
        
        # 3. 执行 AI 代码生成
        async for event in self.ai_facade.generate_and_save_code_stream(app_id, user_message):
            yield event
            
        # 4. 保存助手回复
        await self._save_assistant_message(app_id, "代码生成完成")
```

### 7. 实时通信框架

#### Server-Sent Events (SSE)
```python
@router.get("/chat/gen/code")
async def generate_code_sse(
    app_id: int = Query(..., alias="appId"),
    message: str = Query(...),
    workflow_runner: CodeGenWorkflowRunner = Depends(get_codegen_workflow_runner),
):
    async def event_generator():
        async for event in workflow_runner.run_workflow(app_id, message):
            if isinstance(event, str):
                yield build_sse_event("message", {"content": event})
            else:
                yield build_sse_event("tool", event)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 8. 缓存和性能优化

#### Redis 缓存集成
```python
class AppService:
    async def _get_from_cache(self, key: str) -> str | None:
        try:
            if self.redis_client:
                return await self.redis_client.get(key)
        except RedisError:
            pass
        return self._memory_cache.get(key)
    
    async def _set_to_cache(self, key: str, value: str, ttl: int = 30):
        try:
            if self.redis_client:
                await self.redis_client.setex(key, ttl, value)
        except RedisError:
            pass
        self._memory_cache[key] = (value, time.time() + ttl)
```

### 9. 监控和指标框架

#### Prometheus 指标收集
```python
# core/metrics.py
from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    'python_ai_mother_http_requests_total',
    'Total HTTP requests',
    ['method', 'route']
)

http_request_duration_seconds = Histogram(
    'python_ai_mother_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'route']
)
```

#### 中间件指标收集
```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    http_requests_total.labels(
        method=request.method,
        route=request.url.path
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        route=request.url.path
    ).observe(duration)
    
    return response
```

## 测试框架

### 1. 单元测试架构

#### 测试文件组织
```
backend/monolith/tests/
├── test_user_auth.py           # 用户认证测试
├── test_health.py              # 健康检查测试
├── test_chat_history_m04.py    # 聊天历史测试
├── test_app_m02.py             # M02 应用功能测试
├── test_app_m03.py             # M03 应用功能测试
└── ...
```

#### 测试夹具设计
```python
# tests/conftest.py
@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        # 注入 Mock 依赖
        app.state.resources.redis_client = FakeRedis()
        yield test_client

class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
    
    async def setex(self, key: str, _: int, value: str) -> bool:
        self.store[key] = value
        return True
```

### 2. 集成测试策略

#### API 端点测试
```python
def test_user_register_login_logout_flow(client: TestClient) -> None:
    # 注册用户
    register_response = client.post("/api/user/register", json=register_payload)
    assert register_response.status_code == 200
    
    # 登录验证
    login_response = client.post("/api/user/login", json=login_payload)
    assert login_response.status_code == 200
    
    # 业务逻辑验证
    login_body = login_response.json()
    assert login_body["code"] == int(ErrorCode.SUCCESS)
```

#### 业务逻辑测试
```python
def test_ai_code_generation_flow():
    # 测试完整的 AI 代码生成流程
    facade = AiCodeGeneratorFacade(settings)
    
    # 模拟 AI 响应
    with patch.object(facade.ai_service, 'generate_stream') as mock_stream:
        mock_stream.return_value = async_iterator(["生成的代码内容"])
        
        # 执行代码生成
        result = await facade.generate_and_save_code_stream(1, "创建一个登录页面")
        
        # 验证结果
        assert "生成的代码内容" in result
```

## 部署和运维框架

### 1. 容器化部署

#### Docker 配置
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8123

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
```

### 2. 环境配置管理

#### 多环境支持
```python
# 开发环境
DATABASE_URL=sqlite+aiosqlite:///./python_ai_mother.db
REDIS_URL=redis://localhost:6379/0

# 生产环境  
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app
REDIS_URL=redis://redis:6379/0
```

## 总结

本后端单体架构采用现代 Python 技术栈，具备以下特点：

1. **清晰的层次架构**: API层、服务层、核心业务层分离明确
2. **完善的依赖注入**: 基于 FastAPI 的依赖注入系统，代码解耦良好
3. **强大的异常处理**: 自定义异常体系和全局异常处理器
4. **完整的测试覆盖**: 单元测试和集成测试覆盖核心功能
5. **实时通信支持**: SSE 技术实现实时进度反馈
6. **性能优化**: Redis 缓存和多级缓存策略
7. **监控可观测性**: Prometheus 指标收集和 Grafana 可视化
8. **容器化部署**: Docker 支持，易于部署和扩展

该架构为 AI 应用生成平台提供了稳定、可扩展、易维护的技术基础。

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
