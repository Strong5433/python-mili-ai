# Python AI Mother 重构计划（强对标 yu-ai Git 历史）

## 1. 重构目标
- 在 `python-ai-mother` 中重建与 `yu-ai-code-mother` 功能等价的系统。
- 前端保持原技术栈：Vue3 + TypeScript + Vite + Ant Design Vue。
- 后端全部替换为 Python 技术栈。
- 实施顺序严格对标原仓库 Git 历史：先单体，后微服务。

## 1.1 执行状态
- M00：已完成并合并 `master`（合并提交：`202d2ce`）。
- M01：已完成并合并 `master`（合并提交：`7cacc86`）。
- M02：已完成并合并 `master`（合并提交：`d8dc16c`）。
- M03：已完成并合并 `master`（合并提交：`4454c50`）。
- M04：已完成并合并 `master`（合并提交：`74e635d`）。
- M05：已完成并合并 `master`（合并提交：`304551c`）。
- M06：已完成并合并 `master`（合并提交：`7a16af3`）。
- M07：已完成并合并 `master`（合并提交：`a3a2229`）。
- M08：已完成并合并 `master`（合并提交：`e23de81`）。
- M09：已完成并合并 `master`（合并提交：`d653f4a`）。
- M10：已完成并合并 `master`（合并提交：`1600eeb`）。
- M11：已完成并合并 `master`（合并提交：`6df934b`）。

## 2. 强制开发流程规范

### 2.1 分支规范（强制）
- 所有开发必须在临时分支进行，禁止直接在 `master` 开发。
- 临时分支命名统一：
  - `temp/m{里程碑编号}-{yyyyMMdd}-{简短主题}`
  - 示例：`temp/m01-20260226-user-auth`
- 每个里程碑固定只使用一个临时分支（开发 + 测试 + 收尾文档都在同一分支完成）。
- 禁止为同一里程碑再拆分 `doc-sync` / `post-merge-docs` 等附加分支。

### 2.2 合并规范（强制）
- 只有验收通过后，才允许合并到 `master`。
- 验收未通过，禁止合并，必须继续在临时分支修复。
- 合并前必须完成：
  - 代码自测通过
  - 关键接口联调通过
  - 变更日志已更新
  - 重构计划状态已更新

### 2.3 提交信息规范（强制）
- 提交说明必须使用中文描述（`commit desc` 中文）。
- 建议格式：
  - `feat(m01): 完成用户注册登录与会话管理`
  - `fix(m03): 修复应用分页查询越界问题`
  - `docs(m00): 补充重构计划与接口映射`
  - `test(m05): 增加SSE流式输出集成测试`

### 2.4 变更日志规范（强制）
- `CHANGELOGS.md` 必须使用中文维护。
- 每个临时分支在合并前必须更新 `进行中` 区块。
- 合并到 `master` 后，将对应条目归档到当天日期区块。

## 3. 环境规范（强制）
- Python 虚拟环境必须在项目内，路径固定 `.venv/`。
- Python 包管理统一使用 `uv`，禁止全局 `pip install`。
- 统一命令：
  - `uv venv .venv`
  - `uv pip install -r requirements.txt`
  - `uv run python xxx.py`
  - `uv run pytest`
- Node 版本用 `nvm` 固定，依赖仅在项目目录安装。

## 4. 后端替换技术栈（Java -> Python）
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

## 5. 目标目录结构
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

## 6. 对标总览（按 yu-ai 提交顺序）
| 里程碑 | 对标提交 | 核心主题 |
|---|---|---|
| M00 | `67a0407` `93a80d4` `33d879a` `ba30735` `aadf53e` | 初始化与基础依赖 |
| M01 | `c96ffa8` `d52f335` `55ab6c7` | 用户模块 |
| M02 | `2f783b3` `6c38f1d` | AI 应用生成初版 |
| M03 | `868c65b` `9112c1f` `e05b173` `44f81d6` `fc48d1e` `81eeda3` | 应用模块 + 部署 |
| M04 | `092f62f` `bc7aaac` `55a5613` `3818b73` `94fdc9a` | 对话历史 + Redis Session |
| M05 | `19b1bcd` `1695a3a` `845a82c` `76df070` | 工程项目生成 |
| M06 | `6519021` `499312b` `695d809` | 截图 + 打包 + AI 路由 |
| M07 | `cce4ad1` `e05c04c` `89c7725` | 可视化修改 |
| M08 | `f69f244` `c755246` `cd25d72` `1ac37d8` `62b5655` `5dd51f0` `c55d713` | AI 工作流 |
| M09 | `08cb772` `1939024` `2d32bb4` `566d530` `3e71e72` `5d45f3a` `b99d502` | 系统优化 |
| M10 | `ad303cc` `18c86bc` | 部署上线 + 可观测性 |
| M11 | `9211e98` 到 `893918c` | 微服务改造完成 |

## 7. 里程碑实施与验收（DoD）

### M00 初始化与基础依赖（对标第2期）
- 范围：
  - FastAPI 单体骨架
  - SQLAlchemy/Alembic/Redis 接入
  - 统一错误码、统一响应、全局异常
  - 前端 baseURL 适配
- DoD：
  - `/health` 可用
  - 前后端可联通
  - 至少 1 个 smoke test 通过

### M01 用户模块（对标第3期）
- 范围：
  - 注册/登录/登出/登录态
  - user/admin 权限
  - Redis Session
- DoD：
  - `POST /api/user/register` 可用
  - `POST /api/user/login` 可用
  - `GET /api/user/get/login` 可用
  - `POST /api/user/logout` 可用

### M02 AI 应用生成初版（对标第4期）
- 范围：模型接入、Prompt 加载、最小生成链路
- DoD：输入提示词可返回可用生成结果

### M03 应用模块与部署（对标第5期）
- 范围：应用 CRUD、部署、下载、静态访问
- DoD：应用主流程可完整演示

### M04 对话历史与会话增强（对标第6期）
- 范围：对话持久化、历史查询、会话恢复
- DoD：刷新后历史可恢复

### M05 工程项目生成（对标第7期）
- 范围：多文件工程生成、工具调用、SSE 输出
- DoD：`/app/chat/gen/code` 流式生成稳定

### M06 功能扩展（对标第8期）
- 范围：截图、打包下载、AI 路由
- DoD：截图与打包流程可用

### M07 可视化修改（对标第9期）
- 范围：全量修改、增量修改、回滚
- DoD：同一应用支持两种修改模式

### M08 AI 工作流（对标第10期）
- 范围：LangGraph 工作流、并发子图
- DoD：工作流可运行并可追踪节点

### M09 系统优化（对标第11期）
- 范围：并发、缓存、限流、安全、稳定性、成本
- DoD：核心性能指标优于优化前基线

### M10 部署与可观测性（对标第12-13期）
- 范围：Docker Compose、Prometheus、Grafana
- DoD：可一键部署并看到核心监控指标

### M11 微服务改造（对标第14期）
- 顺序（强制）：
  - `common` -> `model` -> `client` -> `user-service` -> `ai-service` -> `app-service` -> `screenshot-service` -> 跨服务调用 -> 收敛
- DoD：
  - 服务可独立启动
  - 跨服务调用稳定
  - 与单体功能等价

## 8. 测试门禁（每个里程碑强制执行）
- 后端：`uv run pytest`
- 前端：`npm run build`（有 lint 则执行 `npm run lint`）
- 联调：至少 1 条端到端核心链路通过
- 不满足门禁：不得合并 `master`

## 9. 风险与回滚
- 后端替换导致联调中断：
  - 先保证单体可运行，再拆微服务
- 工作流迁移复杂：
  - 先简化工作流可用，再补高级节点
- 跨服务协议不稳定：
  - 先 HTTP 内部调用，稳定后升级 gRPC
- 前端改动膨胀：
  - 前端只做 API 适配，不做无关重构

## 10. 立即执行项
- [x] 创建 M09 临时分支（命名：`temp/m09-yyyymmdd-optimize`）
- [x] 增加并发控制与热点缓存（优先 AI 链路和查询链路）
- [x] 增加限流与 Prompt 安全校验
- [x] 增加重试与稳定性增强策略
- [x] 增加至少 1 条 M09 端到端 smoke test
- [x] 更新 `CHANGELOGS.md` 的 `进行中` 区块并进入 M09
- [x] 准备 M10 临时分支（部署与可观测性）
- [x] 输出 M10 开工清单并补齐 Docker Compose 目标清单
- [x] 完成 M10 收尾并合并 `master`
- [x] 创建 M11 临时分支并输出开工清单
- [x] 完成 M11 微服务目录与服务骨架迁移
- [x] 完成跨服务联调与验收


