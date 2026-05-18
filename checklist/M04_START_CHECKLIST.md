# M04 开工清单（对话历史与会话增强）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m04-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M04 状态

## 2. M04 对标范围（对标第 6 期）
- [x] 对标提交 `092f62f`：对话历史模块（后端基础能力）
  - [x] 新增对话历史实体 / Schema / Service / API
  - [x] 按应用查询对话历史能力打通
- [x] 对标提交 `bc7aaac`：对话历史模块（前端）
  - [x] 前端对话页加载历史消息
  - [x] 管理端对话历史分页查询对接
- [x] 对标提交 `55a5613`：对话记忆持久化
  - [x] 生成链路中持久化 user/ai 消息
  - [x] 支持基于游标（lastCreateTime）加载更多历史
- [x] 对标提交 `3818b73`：增加 Redis Session
  - [x] 校验会话在 Redis 下稳定可用
  - [x] 历史接口鉴权与会话边界补齐
- [x] 对标提交 `94fdc9a`：前端文案修复
  - [x] 前端交互文案与提示优化
  - [x] 页面细节回归检查

## 3. 计划落地顺序
1. 先完成后端历史模型与查询接口
2. 再完成生成链路历史持久化与会话校验
3. 最后完成前端历史联调与文案修复

## 4. M04 DoD（验收门禁）
- [x] `GET /api/chatHistory/app/{appId}` 可用
- [x] `POST /api/chatHistory/admin/list/page/vo` 可用
- [x] 对话生成后可查询到 user/ai 历史消息
- [x] 刷新后历史可恢复并支持继续对话
- [x] `uv run pytest -q -p no:faulthandler` 通过
- [x] `npm run build` 通过
- [x] `CHANGELOGS.md` 已更新
- [x] 提交信息使用中文

## 5. 推荐提交拆分（中文）
1. `feat(m04): 增加对话历史模型与查询接口`
2. `feat(m04): 打通生成链路历史持久化`
3. `feat(m04): 完成对话历史前端对接与文案优化`
4. `test(m04): 增加对话历史模块集成测试`
5. `docs(m04): 更新验收清单与阶段日志`
