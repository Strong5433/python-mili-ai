# backend/microservices

## 1. Service layout (M11)
- `common`: shared response and error contracts
- `model`: cross-service schemas
- `client`: internal service clients
- `user-service`: register, login, session validation
- `ai-service`: code generation service
- `app-service`: aggregation entry service
- `screenshot-service`: screenshot service

## 2. Local setup (project-local uv env)
```bash
cd backend/microservices
uv venv .venv --python 3.11
uv pip sync requirements.lock.txt
```

Start services separately:
```bash
uv run uvicorn user-service.app.main:app --host 0.0.0.0 --port 8201
uv run uvicorn ai-service.app.main:app --host 0.0.0.0 --port 8202
uv run uvicorn app-service.app.main:app --host 0.0.0.0 --port 8203
uv run uvicorn screenshot-service.app.main:app --host 0.0.0.0 --port 8204
```

## 3. Docker compose
- File: `deploy/docker/docker-compose.microservices.yml`
- Gateway entry: `app-service` at `http://localhost:8203`

## 4. Smoke test
```bash
cd backend/microservices
uv run pytest -q tests/test_m11_microservice_flow.py
```
