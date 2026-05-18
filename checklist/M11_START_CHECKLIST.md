# M11 开工清单（微服务改造）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m11-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M11 进行中

## 2. M11 对标范围（对标第 14 期）
- [x] `common` 包
- [x] `model` 包
- [x] `client` 包
- [x] `user-service`
- [x] `ai-service`
- [x] `app-service`
- [x] `screenshot-service`
- [x] 跨服务调用联通

## 3. M11 DoD（验收门禁）
- [x] 服务可独立启动（已提供独立启动命令与微服务 Compose）
- [x] 跨服务调用稳定
- [x] 与单体核心功能等价（覆盖用户登录、应用创建、代码生成、截图主链路）
- [x] 至少 1 条 M11 集成 smoke test 通过
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文
