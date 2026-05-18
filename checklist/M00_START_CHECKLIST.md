# M00 开工清单（FastAPI 单体骨架）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m00-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已同步最新规则

## 2. 环境检查（项目内虚拟环境）
- [x] `.venv/` 已存在（`uv venv .venv`）
- [x] 统一使用 `uv run` 执行命令
- [x] 前端 Node 版本已固定（`frontend/.nvmrc`）

## 3. M00 目录初始化
- [x] 创建 `backend/monolith/app/main.py`
- [x] 创建 `backend/monolith/app/core/`（配置、日志、错误码、统一响应）
- [x] 创建 `backend/monolith/tests/`（smoke test + 异常处理测试）
- [x] 创建 `backend/monolith/requirements.txt`
- [x] 创建 `.env.example` 与后端运行说明
- [x] 引入 `frontend/` 原技术栈工程

## 4. M00 功能目标
- [x] 提供 `GET /api/health/` 健康接口
- [x] 统一错误码与统一响应结构
- [x] 全局异常处理可用
- [x] 请求日志中间件与 CORS 配置已接入
- [x] 数据库与 Redis 资源管理器骨架已接入（初始化/释放）
- [x] 前端 baseURL 适配完成（`/api` + Vite 代理 `8123`）

## 5. M00 验收门禁（通过后才可申请合并）
- [x] `uv run pytest` 通过（当前 3 passed）
- [x] `uv run alembic current` 可执行
- [x] `npm run build` 通过（前端构建门禁）
- [x] `GET /api/health/` 返回成功
- [x] `CHANGELOGS.md` 的 `进行中` 已更新
- [x] 提交信息使用中文

## 6. M00 收尾结果
- [x] 新增 Alembic 初始化配置与迁移目录骨架
- [x] 增加统一启动脚本（本地开发/测试）
- [x] 补充 API 统一返回格式文档到 `docs/`
- [x] 完成 M00 验收记录并准备提合并申请

