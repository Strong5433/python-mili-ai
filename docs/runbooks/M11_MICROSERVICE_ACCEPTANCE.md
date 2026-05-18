# M11 微服务验收手册

## 1. 服务端口
- user-service: `8201`
- ai-service: `8202`
- app-service: `8203`
- screenshot-service: `8204`

## 2. 启动方式
```bash
cd deploy/docker
docker compose -f docker-compose.microservices.yml up -d --build
```

## 3. 验收链路（聚合入口：app-service）
1. 注册：`POST http://localhost:8203/api/user/register`
2. 登录：`POST http://localhost:8203/api/user/login`
3. 创建应用：`POST http://localhost:8203/api/app/add`
4. 生成代码：`GET http://localhost:8203/api/app/chat/gen/code?appId=xx&message=...`
5. 查询应用：`GET http://localhost:8203/api/app/get/vo?id=xx`
6. 截图：`POST http://localhost:8203/api/app/screenshot`

## 4. 自动化验证
```bash
cd backend/microservices
uv run pytest -q tests/test_m11_microservice_flow.py
```

## 5. 停止
```bash
cd deploy/docker
docker compose -f docker-compose.microservices.yml down
```
