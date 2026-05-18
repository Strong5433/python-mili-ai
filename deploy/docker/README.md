# Docker 部署入口（M10）

## 1. 启动
```bash
cp .env.example .env
docker compose up -d --build
```

## 2. 核心地址
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8123`
- 后端健康：`http://localhost:8123/api/health/`
- 指标端点：`http://localhost:8123/metrics`
- Prometheus：`http://localhost:9090`
- Grafana：`http://localhost:3000`

## 3. 停止
```bash
docker compose down
```

删除卷：
```bash
docker compose down -v
```
