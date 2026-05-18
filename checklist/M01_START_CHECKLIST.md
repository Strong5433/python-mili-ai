# M01 开工清单（用户模块）

## 1. 分支与流程检查
- [x] 当前分支为临时分支（非 `master`）
- [x] 分支命名符合：`temp/m01-yyyymmdd-主题`
- [x] `REFACTOR_PLAN.md` 与 `CHANGELOGS.md` 已切换到 M01 状态

## 2. M01 目标范围（对标第 3 期）
- [x] 用户注册：`POST /api/user/register`
- [x] 用户登录：`POST /api/user/login`
- [x] 登录态获取：`GET /api/user/get/login`
- [x] 用户登出：`POST /api/user/logout`
- [x] 基础权限：`user/admin`（`require_role` + 管理员接口鉴权）
- [x] Redis Session 落地与读取（Redis 优先 + 内存兜底）
- [x] 管理员用户管理：增删改查 + 分页
  - `POST /api/user/add`
  - `GET /api/user/get`
  - `GET /api/user/get/vo`
  - `POST /api/user/update`
  - `POST /api/user/delete`
  - `POST /api/user/list/page/vo`

## 3. 技术与目录实现
- [x] 新增用户领域目录：`models/schemas/services/api/dependencies`
- [x] 新增用户表实体与迁移脚本
- [x] 新增密码哈希工具（PBKDF2）
- [x] 新增会话读写封装（Cookie + SessionService）
- [x] 与前端 `userController` 契约保持兼容（字段与路径一致）

## 4. M01 DoD（验收门禁）
- [x] 四个用户核心接口可用
- [x] 未登录访问受限接口返回 `40100`
- [x] 登录后可获取当前用户
- [x] 登出后会话失效
- [x] 管理员 CRUD/分页接口可用
- [x] `uv run pytest -q` 通过（8 passed）
- [x] `npm run build` 通过
- [x] Postman 人工测试通过（用户链路 + 管理员链路）
- [x] `CHANGELOGS.md` 已归档到 M01 合并记录

## 5. 收尾结果
1. M01 功能、自动化测试、人工测试均通过
2. 对标 `c96ffa8`、`d52f335`、`55ab6c7` 已完成
3. 已满足进入 M02 的收尾条件
