# M09 开工清单（系统优化）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m09-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M09 进行中

## 2. M09 对标范围（对标第 11 期）
- [x] 并发优化（AI 调用并发控制）
- [x] 缓存优化（热点接口缓存）
- [x] 安全优化（限流 + Prompt 审查）
- [x] 稳定性优化（重试）
- [x] 成本优化（提示词截断）

## 3. M09 DoD（验收门禁）
- [x] 核心链路具备并发/限流/安全保护
- [x] 至少 1 条 M09 端到端 smoke test 通过
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文
