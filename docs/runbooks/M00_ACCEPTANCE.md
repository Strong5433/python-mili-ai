# M00 验收记录

## 验收范围
- FastAPI 单体骨架初始化
- 统一响应结构与错误码
- 全局异常处理
- 健康检查接口
- 中间件（请求日志 + CORS）
- 资源管理骨架（SQLAlchemy + Redis）
- Alembic 迁移骨架
- 前端引入与 baseURL 适配
- 开发脚本与基础文档

## 验收环境
- 分支：`temp/m00-20260226-bootstrap`
- Python 虚拟环境：项目内 `.venv`
- 包管理器：`uv`
- 前端目录：`frontend`

## 验收命令与结果
1. 安装后端依赖  
   命令：`uv pip install -r backend/monolith/requirements.txt`  
   结果：通过
2. 后端测试  
   命令：`uv run pytest -q`（目录：`backend/monolith`）  
   结果：`3 passed`
3. Alembic 执行检查  
   命令：`uv run alembic current`（目录：`backend/monolith`）  
   结果：通过（SQLite context 初始化成功）
4. 前端构建门禁  
   命令：`npm run build`（目录：`frontend`）  
   结果：通过

## 前端 baseURL 适配核对
- `frontend/.env.development`：`VITE_API_BASE_URL=/api`
- `frontend/src/config/env.ts`：默认回退 `http://localhost:8123/api`
- `frontend/vite.config.ts`：`/api` 代理到 `http://localhost:8123`

## 核对结论
- [x] `GET /api/health/` 已实现
- [x] 统一响应结构已实现
- [x] 全局异常处理已实现
- [x] 后端测试门禁通过
- [x] 前端构建门禁通过
- [x] 前端 baseURL 适配已完成
- [x] 变更日志已更新（中文）
- [x] 提交信息已使用中文

## 合并建议
- 当前分支已满足 M00 验收条件，可发起合并申请至 `master`。
- 按流程执行：人工复核通过后再合并。

