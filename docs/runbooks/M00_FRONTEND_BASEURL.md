# M00 前端 baseURL 适配记录

## 目标
- 保持前端使用原技术栈。
- 将前端 API 请求适配到 Python 后端（`http://localhost:8123/api`）。

## 适配策略
- 前端请求基地址使用相对路径：`/api`
- Vite 开发代理将 `/api` 转发到 Python 后端：`http://localhost:8123`

## 关键配置
- `frontend/.env.development`
  - `VITE_API_BASE_URL=/api`
- `frontend/src/config/env.ts`
  - `API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8123/api'`
- `frontend/vite.config.ts`
  - `server.proxy['/api'].target = 'http://localhost:8123'`

## 联通验证
1. 启动后端：`uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123`（目录：`backend/monolith`）
2. 启动前端：`npm run dev`（目录：`frontend`）
3. 通过前端请求 `/api/health/`，由 Vite 代理转发到 Python 后端。

## 结果
- baseURL 适配完成。
- 前后端联通路径明确，可用于 M00 验收。

