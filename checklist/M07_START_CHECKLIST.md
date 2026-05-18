# M07 开工清单（可视化修改）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m07-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M07 进行中

## 2. M07 对标范围（对标第 9 期）
- [x] 对标提交 `cce4ad1`：前端可视化编辑交互
- [x] 对标提交 `e05c04c`：原生模式全量修改
- [x] 对标提交 `89c7725`：工程模式增量修改

## 3. M07 DoD（验收门禁）
- [x] 同一应用支持全量修改 + 增量修改两种模式
- [x] 支持版本快照与回滚
- [x] 至少 1 条 M07 端到端 smoke test 通过
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文
