import io
import json
import shutil
import time
import zipfile
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from math import ceil
from pathlib import Path
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.code_gen_types import CODE_GEN_TYPE_HTML, SUPPORTED_CODE_GEN_TYPES
from app.core.config import Settings
from app.core.edit_modes import EDIT_MODE_FULL, SUPPORTED_EDIT_MODES
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.models.app import App
from app.models.user import User
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppDeployRequest,
    AppQueryRequest,
    AppUpdateRequest,
    AppVersionVO,
    AppVO,
    PageAppVO,
)
from app.schemas.user import UserVO
from app.services.user_service import USER_ROLE_ADMIN

GOOD_APP_PRIORITY = 99


class AppService:
    _memory_cache: dict[str, tuple[str, float]] = {}
    _sortable_fields = {
        "id": App.id,
        "createTime": App.create_time,
        "updateTime": App.update_time,
        "appName": App.app_name,
        "priority": App.priority,
        "deployedTime": App.deployed_time,
    }

    def __init__(self, settings: Settings | None = None, redis_client: Redis | None = None) -> None:
        self.settings = settings
        self.redis_client = redis_client

    async def add_app(
        self,
        db: AsyncSession,
        payload: AppAddRequest,
        login_user: User,
        routing_service: object | None = None,
    ) -> int:
        app_name = self._build_app_name(payload.init_prompt)
        code_gen_type = await self._resolve_code_gen_type(payload, routing_service)
        new_app = App(
            app_name=app_name,
            init_prompt=(payload.init_prompt or "").strip() or None,
            code_gen_type=code_gen_type,
            user_id=login_user.id,
        )
        db.add(new_app)
        await db.commit()
        await db.refresh(new_app)
        await self._invalidate_query_cache()
        return new_app.id

    async def update_app(self, db: AsyncSession, payload: AppUpdateRequest, login_user: User) -> bool:
        app_id = payload.id or 0
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")
        app_name = (payload.app_name or "").strip()
        if app_name:
            app_entity.app_name = app_name[:128]
        await db.commit()
        await self._invalidate_query_cache()
        return True

    async def delete_app(self, db: AsyncSession, app_id: int, login_user: User) -> bool:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")
        app_entity.is_delete = 1
        await db.commit()
        await self._invalidate_query_cache()
        return True

    async def delete_app_by_admin(self, db: AsyncSession, app_id: int) -> bool:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        app_entity.is_delete = 1
        await db.commit()
        await self._invalidate_query_cache()
        return True

    async def update_app_by_admin(self, db: AsyncSession, payload: AppAdminUpdateRequest) -> bool:
        app_id = payload.id or 0
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if payload.app_name is not None:
            app_name = payload.app_name.strip()
            app_entity.app_name = app_name[:128] if app_name else app_entity.app_name
        if payload.cover is not None:
            app_entity.cover = payload.cover
        if payload.priority is not None:
            app_entity.priority = payload.priority
        if payload.code_gen_type is not None:
            app_entity.code_gen_type = self._normalize_code_gen_type(payload.code_gen_type)
        await db.commit()
        await self._invalidate_query_cache()
        return True

    async def get_app_vo_by_id(self, db: AsyncSession, app_id: int) -> AppVO:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        user_map = await self._load_user_vo_map(db, [app_entity.user_id])
        return self._to_app_vo(app_entity, user_map.get(app_entity.user_id))

    async def list_my_app_vo_by_page(
        self, db: AsyncSession, payload: AppQueryRequest, login_user: User
    ) -> PageAppVO:
        payload.user_id = login_user.id
        return await self._get_or_set_page_cache(
            cache_scope="my",
            payload=payload,
            loader=lambda: self._list_app_vo_by_page(db, payload, max_page_size=20),
        )

    async def list_good_app_vo_by_page(self, db: AsyncSession, payload: AppQueryRequest) -> PageAppVO:
        payload.priority = GOOD_APP_PRIORITY
        return await self._get_or_set_page_cache(
            cache_scope="good",
            payload=payload,
            loader=lambda: self._list_app_vo_by_page(db, payload, max_page_size=20),
        )

    async def list_app_vo_by_page_by_admin(self, db: AsyncSession, payload: AppQueryRequest) -> PageAppVO:
        return await self._get_or_set_page_cache(
            cache_scope="admin",
            payload=payload,
            loader=lambda: self._list_app_vo_by_page(db, payload, max_page_size=100),
        )

    async def deploy_app(
        self,
        db: AsyncSession,
        payload: AppDeployRequest,
        login_user: User,
        generated_root: Path,
        deploy_domain: str,
    ) -> str:
        app_id = payload.app_id or 0
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

        source_dir_name = f"{app_entity.code_gen_type}_{app_entity.id}"
        source_dir = generated_root / source_dir_name
        if not source_dir.exists() or not source_dir.is_dir():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Generated code not found, please generate first")

        deploy_key = source_dir_name
        app_entity.deploy_key = deploy_key
        app_entity.deployed_time = datetime.now(UTC)
        await db.commit()
        await self._invalidate_query_cache()
        return f"{deploy_domain.rstrip('/')}/{deploy_key}/"

    async def build_download_zip_bytes(self, db: AsyncSession, app_id: int, login_user: User, generated_root: Path) -> bytes:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

        source_dir = generated_root / f"{app_entity.code_gen_type}_{app_entity.id}"
        if not source_dir.exists() or not source_dir.is_dir():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Generated code not found, please generate first")
        return self._zip_directory_to_bytes(source_dir)

    async def build_project_download_zip_bytes(
        self,
        db: AsyncSession,
        app_id: int,
        login_user: User,
        generated_root: Path,
    ) -> bytes:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

        source_dir = generated_root / f"{app_entity.code_gen_type}_{app_entity.id}"
        if not source_dir.exists() or not source_dir.is_dir():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Generated code not found, please generate first")

        file_list = [path.relative_to(source_dir).as_posix() for path in source_dir.rglob("*") if path.is_file()]
        manifest = {
            "appId": app_entity.id,
            "appName": app_entity.app_name,
            "codeGenType": app_entity.code_gen_type,
            "deployKey": app_entity.deploy_key,
            "deployedTime": app_entity.deployed_time.isoformat() if app_entity.deployed_time else None,
            "exportedAt": datetime.now(UTC).isoformat(),
            "files": sorted(file_list),
        }
        return self._zip_directory_to_bytes_with_manifest(
            source_dir=source_dir,
            root_dir=source_dir.name,
            manifest=manifest,
        )

    async def create_version_snapshot(
        self,
        db: AsyncSession,
        app_id: int,
        login_user: User,
        generated_root: Path,
        message: str | None,
        edit_mode: str,
    ) -> AppVersionVO:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        self._assert_access(app_entity, login_user)

        normalized_mode = self.normalize_edit_mode(edit_mode)
        source_dir = self._resolve_source_dir(app_entity, generated_root)
        versions_dir = source_dir / ".versions"
        versions_dir.mkdir(parents=True, exist_ok=True)
        index_path = versions_dir / "index.json"

        entries = self._load_version_index(index_path)
        latest = int(entries[-1]["version"]) if entries else 0
        next_version = latest + 1
        file_name = f"v{next_version:04d}_{normalized_mode}.zip"
        snapshot_path = versions_dir / file_name

        self._zip_snapshot(source_dir=source_dir, snapshot_path=snapshot_path)

        entry = {
            "version": next_version,
            "fileName": file_name,
            "message": (message or "").strip() or None,
            "editMode": normalized_mode,
            "createdTime": datetime.now(UTC).isoformat(),
        }
        entries.append(entry)
        self._save_version_index(index_path, entries)
        return self._to_app_version_vo(entry)

    async def list_version_snapshots(
        self,
        db: AsyncSession,
        app_id: int,
        login_user: User,
        generated_root: Path,
    ) -> list[AppVersionVO]:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        self._assert_access(app_entity, login_user)

        source_dir = self._resolve_source_dir(app_entity, generated_root)
        index_path = source_dir / ".versions" / "index.json"
        entries = self._load_version_index(index_path)
        return [self._to_app_version_vo(item) for item in reversed(entries)]

    async def rollback_to_version(
        self,
        db: AsyncSession,
        app_id: int,
        version: int,
        login_user: User,
        generated_root: Path,
    ) -> bool:
        app_entity = await self.get_app_entity_by_id(db, app_id)
        self._assert_access(app_entity, login_user)

        source_dir = self._resolve_source_dir(app_entity, generated_root)
        versions_dir = source_dir / ".versions"
        index_path = versions_dir / "index.json"
        entries = self._load_version_index(index_path)
        target = next((item for item in entries if int(item.get("version", 0)) == version), None)
        if target is None:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Version not found")

        file_name = str(target.get("fileName") or "").strip()
        if not file_name:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Snapshot file missing")
        snapshot_path = versions_dir / file_name
        if not snapshot_path.exists():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Snapshot file not found")

        self._clear_source_dir_for_restore(source_dir)
        self._restore_snapshot(snapshot_path=snapshot_path, source_dir=source_dir)
        return True

    async def get_app_entity_by_id(self, db: AsyncSession, app_id: int) -> App:
        if app_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid app id")
        app_entity = await db.scalar(select(App).where(App.id == app_id, App.is_delete == 0).limit(1))
        if app_entity is None:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "App not found")
        return app_entity

    @staticmethod
    def _query_cache_prefix() -> str:
        return "cache:app:list:"

    def _query_cache_ttl_seconds(self) -> int:
        if self.settings is None:
            return 30
        return max(1, int(self.settings.app_query_cache_ttl_seconds))

    def _build_page_cache_key(self, cache_scope: str, payload: AppQueryRequest) -> str:
        cache_payload = payload.model_dump(by_alias=True, mode="json")
        cache_json = json.dumps(cache_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"{self._query_cache_prefix()}{cache_scope}:{cache_json}"

    async def _get_or_set_page_cache(
        self,
        cache_scope: str,
        payload: AppQueryRequest,
        loader: Callable[[], Awaitable[PageAppVO]],
    ) -> PageAppVO:
        cache_key = self._build_page_cache_key(cache_scope, payload)
        cached_text = await self._cache_get(cache_key)
        if cached_text:
            try:
                cached_obj = json.loads(cached_text)
                return PageAppVO.model_validate(cached_obj)
            except json.JSONDecodeError:
                pass

        page = await loader()
        payload_text = json.dumps(page.model_dump(by_alias=True, mode="json"), ensure_ascii=False)
        await self._cache_set(cache_key, payload_text, self._query_cache_ttl_seconds())
        return page

    async def _cache_get(self, key: str) -> str | None:
        if self.redis_client is not None:
            try:
                redis_value = await self.redis_client.get(key)
                if isinstance(redis_value, str):
                    return redis_value
            except RedisError:
                pass

        cached = self._memory_cache.get(key)
        if cached is None:
            return None
        value, expire_at = cached
        if time.monotonic() >= expire_at:
            self._memory_cache.pop(key, None)
            return None
        return value

    async def _cache_set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._memory_cache[key] = (value, time.monotonic() + ttl_seconds)
        if self.redis_client is None:
            return
        try:
            await self.redis_client.setex(key, ttl_seconds, value)
        except RedisError:
            return

    async def _invalidate_query_cache(self) -> None:
        prefix = self._query_cache_prefix()
        stale_keys = [item for item in self._memory_cache if item.startswith(prefix)]
        for key in stale_keys:
            self._memory_cache.pop(key, None)

        if self.redis_client is None:
            return
        scan_iter = getattr(self.redis_client, "scan_iter", None)
        if not callable(scan_iter):
            return

        delete_keys: list[str] = []
        try:
            async for key in scan_iter(match=f"{prefix}*"):
                if isinstance(key, str):
                    delete_keys.append(key)
                elif isinstance(key, bytes):
                    delete_keys.append(key.decode("utf-8", errors="ignore"))
            if delete_keys:
                await self.redis_client.delete(*delete_keys)
        except RedisError:
            return

    async def _list_app_vo_by_page(
        self,
        db: AsyncSession,
        payload: AppQueryRequest,
        max_page_size: int,
    ) -> PageAppVO:
        page_num = payload.page_num or 1
        page_size = payload.page_size or 10
        if page_num <= 0:
            page_num = 1
        if page_size <= 0:
            page_size = 10
        page_size = min(page_size, max_page_size)

        filters = [App.is_delete == 0]
        if payload.id and payload.id > 0:
            filters.append(App.id == payload.id)
        if payload.app_name:
            filters.append(App.app_name.like(f"%{payload.app_name.strip()}%"))
        if payload.cover:
            filters.append(App.cover.like(f"%{payload.cover.strip()}%"))
        if payload.init_prompt:
            filters.append(App.init_prompt.like(f"%{payload.init_prompt.strip()}%"))
        if payload.code_gen_type:
            filters.append(App.code_gen_type == payload.code_gen_type.strip())
        if payload.deploy_key:
            filters.append(App.deploy_key == payload.deploy_key.strip())
        if payload.priority is not None:
            filters.append(App.priority == payload.priority)
        if payload.user_id and payload.user_id > 0:
            filters.append(App.user_id == payload.user_id)

        query_stmt = select(App).where(*filters)
        count_stmt = select(func.count(App.id)).where(*filters)

        sort_column = self._sortable_fields.get(payload.sort_field or "")
        sort_order = (payload.sort_order or "").lower()
        if sort_column is not None:
            order_by = desc(sort_column) if "desc" in sort_order else asc(sort_column)
            query_stmt = query_stmt.order_by(order_by)
        else:
            query_stmt = query_stmt.order_by(desc(App.id))

        offset = (page_num - 1) * page_size
        apps = (await db.scalars(query_stmt.offset(offset).limit(page_size))).all()
        total_row = int(await db.scalar(count_stmt) or 0)
        total_page = ceil(total_row / page_size) if total_row > 0 else 0

        user_ids = [app.user_id for app in apps]
        user_map = await self._load_user_vo_map(db, user_ids)
        records = [self._to_app_vo(item, user_map.get(item.user_id)) for item in apps]

        return PageAppVO(
            records=records,
            page_number=page_num,
            page_size=page_size,
            total_page=total_page,
            total_row=total_row,
            optimize_count_query=True,
        )

    async def _load_user_vo_map(self, db: AsyncSession, user_ids: list[int]) -> dict[int, UserVO]:
        clean_user_ids = sorted({item for item in user_ids if item > 0})
        if not clean_user_ids:
            return {}
        users = (
            await db.scalars(select(User).where(User.id.in_(clean_user_ids), User.is_delete == 0))
        ).all()
        return {item.id: self._to_user_vo(item) for item in users}

    @staticmethod
    def _to_user_vo(user: User) -> UserVO:
        return UserVO(
            id=user.id,
            user_account=user.user_account,
            user_name=user.user_name,
            user_avatar=user.user_avatar,
            user_profile=user.user_profile,
            user_role=user.user_role,
            create_time=user.create_time,
        )

    @staticmethod
    def _to_app_vo(app_entity: App, user_vo: UserVO | None) -> AppVO:
        return AppVO(
            id=app_entity.id,
            app_name=app_entity.app_name,
            cover=app_entity.cover,
            init_prompt=app_entity.init_prompt,
            code_gen_type=app_entity.code_gen_type,
            deploy_key=app_entity.deploy_key,
            deployed_time=app_entity.deployed_time,
            priority=app_entity.priority,
            user_id=app_entity.user_id,
            create_time=app_entity.create_time,
            update_time=app_entity.update_time,
            user=user_vo,
        )

    @staticmethod
    def _build_app_name(init_prompt: str | None) -> str:
        if not init_prompt:
            return "My App"
        name = init_prompt.strip().replace("\n", " ")
        if not name:
            return "My App"
        return name[:32]

    @staticmethod
    def _normalize_code_gen_type(code_gen_type: str | None) -> str:
        value = (code_gen_type or CODE_GEN_TYPE_HTML).strip()
        if value not in SUPPORTED_CODE_GEN_TYPES:
            raise BusinessException(ErrorCode.PARAMS_ERROR, f"Unsupported code_gen_type: {value}")
        return value

    @staticmethod
    def normalize_edit_mode(edit_mode: str | None) -> str:
        value = (edit_mode or EDIT_MODE_FULL).strip().lower()
        if value not in SUPPORTED_EDIT_MODES:
            raise BusinessException(ErrorCode.PARAMS_ERROR, f"Unsupported edit_mode: {value}")
        return value

    async def _resolve_code_gen_type(self, payload: AppAddRequest, routing_service: object | None) -> str:
        specified = (payload.code_gen_type or "").strip()
        if specified:
            return self._normalize_code_gen_type(specified)

        if payload.enable_auto_route and routing_service is not None:
            route_method = getattr(routing_service, "route", None)
            if callable(route_method):
                decision = await route_method(payload.init_prompt or "", None)
                code_gen_type = getattr(decision, "code_gen_type", None)
                if isinstance(code_gen_type, str) and code_gen_type in SUPPORTED_CODE_GEN_TYPES:
                    return code_gen_type
        return CODE_GEN_TYPE_HTML

    @staticmethod
    def _zip_directory_to_bytes(source_dir: Path) -> bytes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for path in source_dir.rglob("*"):
                if path.is_file():
                    arc_name = path.relative_to(source_dir).as_posix()
                    zip_file.write(path, arcname=arc_name)
        return zip_buffer.getvalue()

    @staticmethod
    def _zip_directory_to_bytes_with_manifest(source_dir: Path, root_dir: str, manifest: dict) -> bytes:
        zip_buffer = io.BytesIO()
        prefix = root_dir.strip().strip("/") or "project"
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for path in source_dir.rglob("*"):
                if path.is_file():
                    arc_name = f"{prefix}/{path.relative_to(source_dir).as_posix()}"
                    zip_file.write(path, arcname=arc_name)
            zip_file.writestr(
                f"{prefix}/python-ai-mother-manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )
        return zip_buffer.getvalue()

    @staticmethod
    def _assert_access(app_entity: App, login_user: User) -> None:
        if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

    @staticmethod
    def _resolve_source_dir(app_entity: App, generated_root: Path) -> Path:
        source_dir = generated_root / f"{app_entity.code_gen_type}_{app_entity.id}"
        if not source_dir.exists() or not source_dir.is_dir():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Generated code not found, please generate first")
        return source_dir

    @staticmethod
    def _load_version_index(index_path: Path) -> list[dict[str, Any]]:
        if not index_path.exists():
            return []
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return [item for item in raw if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
        return []

    @staticmethod
    def _save_version_index(index_path: Path, entries: list[dict[str, Any]]) -> None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _zip_snapshot(source_dir: Path, snapshot_path: Path) -> None:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(snapshot_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for path in source_dir.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(source_dir).as_posix()
                if rel.startswith(".versions/"):
                    continue
                zip_file.write(path, arcname=rel)

    @staticmethod
    def _clear_source_dir_for_restore(source_dir: Path) -> None:
        keep_roots = {".versions", ".screenshots"}
        for path in source_dir.iterdir():
            if path.name in keep_roots:
                continue
            if path.is_file():
                path.unlink(missing_ok=True)
            else:
                shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def _restore_snapshot(snapshot_path: Path, source_dir: Path) -> None:
        with zipfile.ZipFile(snapshot_path, mode="r") as zip_file:
            for name in zip_file.namelist():
                clean = name.replace("\\", "/").strip("/")
                if not clean or clean.startswith("../") or "/../" in clean:
                    continue
                target = (source_dir / clean).resolve()
                try:
                    target.relative_to(source_dir.resolve())
                except ValueError as exc:
                    raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid snapshot file path") from exc
                target.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(name, "r") as src, target.open("wb") as dst:
                    dst.write(src.read())

    @staticmethod
    def _to_app_version_vo(entry: dict[str, Any]) -> AppVersionVO:
        return AppVersionVO(
            version=int(entry.get("version") or 0),
            file_name=str(entry.get("fileName") or ""),
            message=(str(entry.get("message")) if entry.get("message") is not None else None),
            edit_mode=str(entry.get("editMode") or EDIT_MODE_FULL),
            created_time=str(entry.get("createdTime") or datetime.now(UTC).isoformat()),
        )
