# M10 部署与可观测性验收手册

## 1. 前置条件
- Docker Desktop 已启动（Windows 需确保 `dockerDesktopLinuxEngine` 可用）
- 当前目录：`python-ai-mother/`

## 2. 启动方式
```bash
cd deploy/docker
cp .env.example .env
docker compose up -d --build
```

## 3. 服务检查
- 前端：`http://localhost:5173`
- 后端健康：`http://localhost:8123/api/health/`
- 指标端点：`http://localhost:8123/metrics`
- Prometheus：`http://localhost:9090`
- Grafana：`http://localhost:3000`（默认账号/密码：`admin/admin`）

## 4. Prometheus 验证
在 Prometheus 页面执行查询：
- `python_ai_mother_http_requests_total`
- `python_ai_mother_http_request_duration_seconds_count`

## 5. Grafana 验证
- 打开默认首页仪表盘：`Python AI Mother 概览`
- 确认能看到：
  - HTTP 请求速率（按路由）
  - HTTP 延迟 p95（按路由）
  - 最近 1 小时请求总量

## 6. 烟雾测试链路
1. 访问 `http://localhost:5173`
2. 登录后访问一次 `GET /api/health/`
3. 刷新 Grafana，看请求总量是否增长

## 7. 停止与清理
```bash
cd deploy/docker
docker compose down
```

如需删除卷：
```bash
docker compose down -v
```
