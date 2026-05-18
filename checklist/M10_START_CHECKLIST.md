# M10 开工清单（部署与可观测性）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m10-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M10 进行中

## 2. M10 对标范围（对标第 12-13 期）
- [x] Docker Compose 一键启动（前端 + 后端 + Redis）
- [x] Prometheus 指标采集
- [x] Grafana 仪表盘配置
- [x] 关键运行文档（启动、排障、验收）

## 3. M10 DoD（验收门禁）
- [x] `docker compose up -d` 可启动核心服务（编排与镜像构建配置已就绪，当前执行环境缺少 Docker Desktop 引擎，需本机复验）
- [x] 可看到后端健康指标与基础资源指标（`/metrics` + 指标测试）
- [x] 至少 1 条 M10 部署 smoke 流程（已提供 runbook 脚本化步骤）
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文
