# 变更日志（CHANGELOGS）

本文件记录项目的重要变更，统一使用中文维护。

## 维护规范
- 开发中变更先写入 `进行中`。
- 验收通过并合并到 `master` 后，将条目归档到对应日期。
- 每条记录建议附带提交哈希，便于追踪。

## 进行中
- 暂无（M00-M11 全部完成）。

## 2026-02-27

### M11 收尾归档
- M11 微服务改造完成，范围对齐 `9211e98` 到 `893918c`（按 Python 技术栈落地最小等价能力）。
- 已完成能力：
  - 新增 `backend/microservices` 目录结构：`common`、`model`、`client`、`user-service`、`ai-service`、`app-service`、`screenshot-service`。
  - 新增聚合服务 `app-service`，打通用户透传、应用创建、SSE 代码生成、截图主链路。
  - 新增微服务编排：`deploy/docker/docker-compose.microservices.yml`。
  - 新增 M11 运行与验收文档：`docs/runbooks/M11_MICROSERVICE_ACCEPTANCE.md`。
- 已完成验证：
  - `uv run pytest -q tests/test_m11_microservice_flow.py` 通过（`1 passed`）。
  - `uv run pytest -q -p no:faulthandler`（monolith）通过（`28 passed`）。
  - `npm run build` 通过。
  - `docker compose -f deploy/docker/docker-compose.microservices.yml config` 通过。
- 相关提交：
  - `3374b85` `feat(m11): 完成微服务拆分与跨服务主链路联调`
  - `af21834` `chore(m11): 清理测试产物并固定截图目录忽略规则`
- M11 已按流程合并到 `master`。
  - `6df934b` `merge(m11): 合并微服务改造阶段成果`

### M10 收尾归档
- M10 部署与可观测性完成，范围对齐 `ad303cc`、`18c86bc`。
- 已完成能力：
  - 新增容器化部署：`backend/monolith/Dockerfile`、`frontend/Dockerfile`、`deploy/docker/docker-compose.yml`。
  - 新增监控采集：后端 `/metrics` 指标端点、Prometheus 抓取配置、Grafana 数据源与默认仪表盘。
  - 新增部署文档：`deploy/docker/README.md`、`docs/runbooks/M10_DEPLOY_OBSERVABILITY.md`。
  - 新增指标测试：`test_metrics_endpoint`。
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`28 passed`）。
  - 前端构建：`npm run build` 通过。
  - 编排校验：`docker compose config` 通过。
  - 说明：当前执行环境未启动 Docker Desktop 引擎，`docker compose up -d` 需在本机复验。
- 相关提交：
  - `acc2f1f` `feat(m10): 完成容器化部署与可观测性基础能力`

### M09 收尾归档
- M09 系统优化完成，范围对齐 `08cb772`、`1939024`、`2d32bb4`、`566d530`、`3e71e72`、`5d45f3a`、`b99d502`。
- 已完成能力：
  - 并发与稳定性：`OpenAICompatibleService` 增加并发信号量控制和失败重试。
  - 安全与成本：Prompt 关键词审查 + 最大长度截断，避免高风险输入和过长提示词。
  - 限流：`/api/app/chat/gen/code`、`/api/app/chat/gen/workflow` 新增按用户限流保护。
  - 缓存：应用分页查询增加热点缓存，并在写操作后自动失效。
  - 配置：新增 `LLM_RETRY_COUNT`、`AI_CONCURRENCY_LIMIT`、`LLM_MAX_PROMPT_CHARS`、`PROMPT_BLOCK_KEYWORDS`、`APP_QUERY_CACHE_TTL_SECONDS`、`CHAT_RATE_LIMIT_*`。
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`27 passed`）。
  - 前端构建：`npm run build` 通过。
- 相关提交：
  - `e74a151` `feat(m09): 完成系统优化能力并补齐限流缓存测试`
- M09 已按流程合并到 `master`。
  - `d653f4a` `merge(m09): 合并系统优化阶段成果`

### M08 收尾归档
- M08 AI 工作流完成，范围对齐 `f69f244`、`c755246`、`cd25d72`、`1ac37d8`、`62b5655`、`5dd51f0`、`c55d713`。
- 已完成能力：
  - 新增工作流执行器：`CodeGenWorkflowRunner`，支持节点化编排。
  - 工作流中引入并行子节点（资源计划 + 质量策略），使用并发任务执行。
  - 新增工作流 SSE 接口：`GET /api/app/chat/gen/workflow`，可追踪 `workflow` 节点事件。
  - 前端新增“工作流 / 直连”切换开关，并统一在工具流面板展示节点轨迹。
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`25 passed`）。
  - 前端构建：`npm run build` 通过。
- 相关提交：
  - `40d82b3` `feat(m08): 打通工作流并发节点与追踪事件`
- M08 已按流程合并到 `master`。
  - `e23de81` `merge(m08): 合并AI工作流重构成果`

### M07 收尾归档
- M07 可视化修改完成，范围对齐 `cce4ad1`、`e05c04c`、`89c7725`。
- 已完成能力：
  - 新增编辑模式：`full`（全量）和 `incremental`（增量），并接入 `GET /api/app/chat/gen/code` 的 `editMode` 参数。
  - 生成落盘器支持两种模式：全量模式覆盖输出目录；增量模式仅更新涉及文件。
  - 新增版本快照与回滚接口：
    - `POST /api/app/version/snapshot`
    - `GET /api/app/version/list`
    - `POST /api/app/version/rollback`
  - 前端对话页新增“编辑模式切换 + 版本回滚弹窗”交互。
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`24 passed`）。
  - 前端构建：`npm run build` 通过。
- 相关提交：
  - `9ff6869` `feat(m07): 完成可视化修改双模式与版本回滚`
- M07 已按流程合并到 `master`。
  - `a3a2229` `merge(m07): 合并可视化修改与回滚重构成果`

### M06 收尾归档
- M06 功能扩展完成，范围对齐 `6519021`、`499312b`、`695d809`。
- 已完成能力：
  - 新增 AI 路由能力：`POST /api/app/route/codegen`，支持启发式 + LLM 可选策略。
  - 创建应用链路接入自动路由：未显式传 `codeGenType` 时自动推荐生成模式。
  - 新增截图能力：`POST /api/app/screenshot`，生成图片并静态可访问，同时回写应用封面。
  - 新增增强打包下载：`GET /api/app/download/project/{appId}`，zip 包含项目目录和 `python-ai-mother-manifest.json`。
  - 前端对话页新增“截图”按钮，并将下载链路切换为增强打包接口。
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`22 passed`）。
  - 前端构建：`npm run build` 通过。
- 相关提交：
  - `544f958` `feat(m06): 完成截图打包增强与AI路由能力`
- M06 已按流程合并到 `master`。
  - `7a16af3` `merge(m06): 合并截图打包与AI路由重构成果`

### 新增
- 引入前端工程到 `frontend/`，保持原技术栈。
  - `7909720` `feat(m00): 引入前端工程并完成baseURL适配`
- 新增仓库根 README，补齐项目入口说明。
  - `68150ce` `docs(m00): 补充仓库根README说明`
- 新增 M00 验收记录与前端 baseURL 适配记录。
  - `c90553b` `docs(m00): 完成验收记录并准备提合并`
  - `d8dd299` `docs(m00): 更新前端联通验收与清单状态`

### 变更
- M00 阶段已完成并合并到 `master`。
  - `202d2ce` `feat(m00): 完成初始化与基础依赖阶段`

### M05 收尾归档
- M05 工程项目生成完成，范围对齐 `19b1bcd`、`1695a3a`、`845a82c`、`76df070`。
- 已完成能力：
  - 新增 `vue_project` 生成模式，支持创建应用时选择 `codeGenType`
  - 多文件解析与落盘增强：支持 `file:<path>` 块格式、目录安全校验、`{code_gen_type}_{app_id}` 目录约定
  - 新增 Vue 工程提示词：`codegen-vue-project-system-prompt.txt`
  - `chat/gen/code` 增加工具事件流（start / delta / end）并保持文本流兼容
  - 前端对话页新增“工具调用流”展示，首页新增生成模式选择
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`20 passed`）
  - 前端构建：`npm run build` 通过
- 相关提交：
  - `90b4811` `docs(m05): 完成开工准备与清单初始化`
  - `7ff0283` `feat(m05): 打通工程项目生成与工具流展示`
- M05 已按流程合并到 `master`。
  - `304551c` `merge(m05): 合并工程项目生成重构成果`

### M04 收尾归档
- M04 对话历史与会话增强完成，范围对齐 `092f62f`、`bc7aaac`、`55a5613`、`3818b73`、`94fdc9a`。
- 已完成能力：
  - 新增 `chat_history` 模型、迁移、服务和接口，支持按应用查询历史与管理员分页检索
  - 打通 `GET /api/chatHistory/app/{appId}` 与 `POST /api/chatHistory/admin/list/page/vo`
  - `GET /api/app/chat/gen/code` 生成链路接入 user / assistant 消息持久化
  - 前端对话页支持历史加载、游标分页与只读模式文案优化
- 已完成验证：
  - 数据迁移：`uv run alembic upgrade head` 通过
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`18 passed`）
  - 前端构建：`npm run build` 通过
- 相关提交：
  - `648364b` `docs(m04): 完成开工准备与清单初始化`
  - `132d70d` `feat(m04): 完成对话历史模块与生成链路持久化`
  - `33ca8a9` `docs(m04): 完成清单收尾并优化只读文案`
- M04 已按流程合并到 `master`。
  - `74e635d` `merge(m04): 合并对话历史与会话增强重构成果`

### M03 收尾归档
- M03 应用模块与部署完成，范围对齐 `868c65b`、`9112c1f`、`e05b173`、`44f81d6`、`fc48d1e`、`81eeda3`。
- 已完成能力：
  - 应用 CRUD、分页查询、管理员应用接口
  - 应用部署（`deployKey` / `deployedTime`）、静态访问、下载
  - 前端默认部署地址适配，作品可直接访问
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过（`16 passed`）
  - 前端构建：`npm run build` 通过
  - 端到端 smoke：注册登录 -> 创建应用 -> AI 生成 -> 部署 -> 静态访问 -> 下载
- 相关提交：
  - `cb6f90f` `docs(m03): 完成开工准备与清单初始化`
  - `79d85d0` `feat(m03): 补齐应用模块CRUD分页与部署下载接口`
  - `7d8adb0` `test(m03): 增加应用模块接口集成测试`
  - `03bb2ab` `docs(m03): 更新阶段进展与验收清单`
  - `0535307` `feat(m03): 适配前端默认部署地址到静态资源`
  - `4c52baf` `test(m03): 修复测试配置污染并增加静态访问断言`
  - `9eff615` `docs(m03): 更新对标进度与端到端演示记录`
- M03 已按流程合并到 `master`。
  - `4454c50` `merge(m03): 合并应用模块与部署重构成果`

### M02 收尾归档
- M02 AI 应用生成初版完成，范围对齐 `2f783b3`、`6c38f1d`。
- 已完成能力：
  - 模型接入、Prompt 加载、最小生成链路
  - `POST /api/app/add`、`GET /api/app/get/vo`、`GET /api/app/chat/gen/code`（SSE）
  - 解析器执行器化、保存器执行器化、通用 SSE 事件构建
- 已完成验证：
  - 自动化测试：`uv run pytest -q -p no:faulthandler` 通过
  - 前端构建：`npm run build` 通过
  - 非 mock 联调：真实模型请求可返回并成功落盘生成文件
- 相关提交：
  - `b626004` `docs(m02): 完成开工准备与清单初始化`
  - `c25a3b7` `feat(m02): 打通应用生成主链路并完成执行器化重构`
  - `cac41e8` `test(m02): 增加应用生成链路与SSE测试`
  - `48a4d39` `docs(m02): 更新清单日志与模型配置说明`
  - `50a25e6` `chore(test): 兼容Windows测试输出并禁用faulthandler`
- M02 已按流程合并到 `master`。
  - `d8dc16c` `merge(m02): 合并AI应用生成初版重构成果`

### M01 收尾归档
- M01 用户模块与管理员能力已完成，并通过自动化与人工验收。
  - `31dd5c1` `feat(m01): 完成用户注册登录与会话鉴权`
  - `390b1b2` `test(m01): 增加用户模块接口集成测试`
  - `b158be0` `docs(m01): 更新验收清单与阶段文档`
  - `11f54d3` `feat(m01): 补齐管理员用户CRUD与分页接口`
  - `6bcc799` `test(m01): 增加管理员接口权限与分页测试`
  - `291b1a1` `docs(m01): 更新管理员模块对标与验收记录`
- M01 对标结论：`c96ffa8`、`d52f335`、`55ab6c7` 已全部对齐。
- M01 人工测试状态：Postman 全链路通过（用户 + 管理员 + 权限负例）。
- M01 已按流程合并到 `master`。
  - `7cacc86` `merge(m01): 合并用户模块重构成果`

## 2026-02-26

### 新增
- 初始化仓库，新增基础文档与重构计划初版。
  - `aaa357a` `docs: initialize python-ai-mother with refactor plan`
- 新增变更日志文件并写入初始历史。
  - `a3ad0e5` `docs: add CHANGELOGS.md with initial history`
- 新增 M00 开工清单。
  - `4d26bab` `docs(m00): 完成计划终检并新增开工清单`
- 初始化 FastAPI 单体骨架与健康检查。
  - `858063e` `feat(m00): 初始化FastAPI单体骨架与健康检查`
- 增加中间件、资源管理器、Alembic 骨架和开发脚本。
  - `00488ad` `feat(m00): 补充中间件与资源管理骨架`
  - `898b17b` `feat(m00): 增加迁移骨架与开发脚本`

### 变更
- 强制项目内 Python 虚拟环境策略，统一使用 `uv`。
  - `83fb120` `docs: enforce project-local env policy with uv`
- 优化重构路线，按 `yu-ai-code-mother` 历史里程碑对齐。
  - `8f9bded` `docs: optimize refactor roadmap aligned to yu-ai git milestones`
- 固化分支流程规范，并将重构计划与日志改为中文维护。
  - `62a9cc7` `docs: 规范分支流程并改为中文提交与日志`
- 补充统一响应文档、验收清单与日志。
  - `72b9c1e` `docs(m00): 更新进行中日志与开工清单`
  - `e4d0ea5` `docs(m00): 补充统一响应文档与验收清单`

