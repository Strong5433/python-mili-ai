# M08 开工清单（AI 工作流）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m08-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M08 进行中

## 2. M08 对标范围（对标第 10 期）
- [x] 工作流执行器（节点化）
- [x] 并发子图/并行节点（最小可用）
- [x] 节点追踪事件（SSE 可观测）

## 3. M08 DoD（验收门禁）
- [x] 工作流可运行并返回生成结果
- [x] 工作流节点事件可追踪
- [x] 至少 1 条 M08 端到端 smoke test 通过
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文
