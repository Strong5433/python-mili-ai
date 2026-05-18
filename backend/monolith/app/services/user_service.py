import re
from math import ceil

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import (
    LoginUserVO,
    PageUserVO,
    UserAddRequest,
    UserData,
    UserLoginRequest,
    UserQueryRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVO,
)
from app.services.session_service import SessionService

USER_ROLE_USER = "user"
USER_ROLE_ADMIN = "admin"


class UserService:
    _account_pattern = re.compile(r"^[A-Za-z0-9_]{4,64}$")
    _valid_roles = {USER_ROLE_USER, USER_ROLE_ADMIN}
    _sortable_fields = {
        "id": User.id,
        "createTime": User.create_time,
        "updateTime": User.update_time,
        "userAccount": User.user_account,
        "userName": User.user_name,
        "userRole": User.user_role,
    }

    def __init__(self, settings: Settings, session_service: SessionService) -> None:
        self.settings = settings
        self.session_service = session_service

    async def register(self, db: AsyncSession, payload: UserRegisterRequest) -> int:
        user_account = (payload.user_account or "").strip()
        user_password = payload.user_password or ""
        check_password = payload.check_password or ""
        self._validate_register_fields(user_account, user_password, check_password)

        exists = await db.scalar(self._active_user_select().where(User.user_account == user_account).limit(1))
        if exists is not None:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Account already exists")

        new_user = User(
            user_account=user_account,
            user_password=hash_password(user_password, self.settings.password_salt),
            user_name=f"user_{user_account}",
            user_role=USER_ROLE_USER,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user.id

    async def login(self, db: AsyncSession, payload: UserLoginRequest) -> tuple[LoginUserVO, str]:
        user_account = (payload.user_account or "").strip()
        user_password = payload.user_password or ""
        if not user_account or not user_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Account or password is empty")

        user = await db.scalar(self._active_user_select().where(User.user_account == user_account).limit(1))
        if user is None:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid account or password")
        if not verify_password(user_password, user.user_password, self.settings.password_salt):
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid account or password")

        session_id = await self.session_service.create_session(user.id, user.user_role)
        return self._to_login_vo(user), session_id

    async def get_login_user(self, db: AsyncSession, session_id: str | None) -> LoginUserVO:
        user = await self.get_login_user_entity(db, session_id)
        return self._to_login_vo(user)

    async def get_login_user_entity(self, db: AsyncSession, session_id: str | None) -> User:
        if not session_id:
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR, "Not logged in")

        session_payload = await self.session_service.get_session(session_id)
        if session_payload is None:
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR, "Not logged in")

        user = await db.scalar(
            self._active_user_select().where(User.id == session_payload.user_id).limit(1)
        )
        if user is None:
            await self.session_service.delete_session(session_id)
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR, "Not logged in")
        return user

    async def logout(self, session_id: str | None) -> bool:
        if not session_id:
            return True
        await self.session_service.delete_session(session_id)
        return True

    async def add_user(self, db: AsyncSession, payload: UserAddRequest) -> int:
        user_account = (payload.user_account or "").strip()
        if not self._account_pattern.fullmatch(user_account):
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid account format")
        exists = await db.scalar(self._active_user_select().where(User.user_account == user_account).limit(1))
        if exists is not None:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Account already exists")

        user_role = self._normalize_role(payload.user_role)
        new_user = User(
            user_account=user_account,
            user_password=hash_password("12345678", self.settings.password_salt),
            user_name=(payload.user_name or "").strip() or f"user_{user_account}",
            user_avatar=payload.user_avatar,
            user_profile=payload.user_profile,
            user_role=user_role,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user.id

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> UserData:
        user = await self._must_get_active_user(db, user_id)
        return self._to_user_data(user)

    async def get_user_vo_by_id(self, db: AsyncSession, user_id: int) -> UserVO:
        user = await self._must_get_active_user(db, user_id)
        return self._to_user_vo(user)

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        if user_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid id")
        user = await db.scalar(self._active_user_select().where(User.id == user_id).limit(1))
        if user is None:
            return False
        user.is_delete = 1
        await db.commit()
        return True

    async def update_user(self, db: AsyncSession, payload: UserUpdateRequest) -> bool:
        user_id = payload.id or 0
        user = await self._must_get_active_user(db, user_id)
        if payload.user_name is not None:
            user.user_name = payload.user_name
        if payload.user_avatar is not None:
            user.user_avatar = payload.user_avatar
        if payload.user_profile is not None:
            user.user_profile = payload.user_profile
        if payload.user_role is not None:
            user.user_role = self._normalize_role(payload.user_role)
        await db.commit()
        return True

    async def list_user_vo_by_page(self, db: AsyncSession, payload: UserQueryRequest) -> PageUserVO:
        page_num = payload.page_num or 1
        page_size = payload.page_size or 10
        if page_num <= 0:
            page_num = 1
        if page_size <= 0:
            page_size = 10
        page_size = min(page_size, 100)

        filters = [User.is_delete == 0]
        if payload.id and payload.id > 0:
            filters.append(User.id == payload.id)
        if payload.user_name:
            filters.append(User.user_name.like(f"%{payload.user_name.strip()}%"))
        if payload.user_account:
            filters.append(User.user_account.like(f"%{payload.user_account.strip()}%"))
        if payload.user_profile:
            filters.append(User.user_profile.like(f"%{payload.user_profile.strip()}%"))
        if payload.user_role:
            filters.append(User.user_role == self._normalize_role(payload.user_role))

        query_stmt = select(User).where(*filters)
        count_stmt = select(func.count(User.id)).where(*filters)

        sort_column = self._sortable_fields.get(payload.sort_field or "")
        sort_order = (payload.sort_order or "").lower()
        if sort_column is not None:
            order_by = desc(sort_column) if "desc" in sort_order else asc(sort_column)
            query_stmt = query_stmt.order_by(order_by)
        else:
            query_stmt = query_stmt.order_by(desc(User.id))

        offset = (page_num - 1) * page_size
        users = (await db.scalars(query_stmt.offset(offset).limit(page_size))).all()
        total_row = int(await db.scalar(count_stmt) or 0)
        total_page = ceil(total_row / page_size) if total_row > 0 else 0

        return PageUserVO(
            records=[self._to_user_vo(item) for item in users],
            page_number=page_num,
            page_size=page_size,
            total_page=total_page,
            total_row=total_row,
            optimize_count_query=True,
        )

    def assert_role(self, user: User, required_role: str) -> None:
        if user.user_role != required_role:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

    def _validate_register_fields(self, user_account: str, user_password: str, check_password: str) -> None:
        if not user_account or not user_password or not check_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Account or password is empty")
        if len(user_password) < 8:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Password too short")
        if user_password != check_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Password and checkPassword do not match")
        if not self._account_pattern.fullmatch(user_account):
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid account format")

    @staticmethod
    def _to_login_vo(user: User) -> LoginUserVO:
        return LoginUserVO(
            id=user.id,
            user_account=user.user_account,
            user_name=user.user_name,
            user_avatar=user.user_avatar,
            user_profile=user.user_profile,
            user_role=user.user_role,
            create_time=user.create_time,
            update_time=user.update_time,
        )

    @staticmethod
    def _to_user_data(user: User) -> UserData:
        return UserData(
            id=user.id,
            user_account=user.user_account,
            user_password=user.user_password,
            user_name=user.user_name,
            user_avatar=user.user_avatar,
            user_profile=user.user_profile,
            user_role=user.user_role,
            edit_time=user.edit_time,
            create_time=user.create_time,
            update_time=user.update_time,
            is_delete=user.is_delete,
        )

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

    @classmethod
    def _normalize_role(cls, role: str | None) -> str:
        role_value = (role or USER_ROLE_USER).strip()
        if role_value not in cls._valid_roles:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid user role")
        return role_value

    async def _must_get_active_user(self, db: AsyncSession, user_id: int) -> User:
        if user_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid id")
        user = await db.scalar(self._active_user_select().where(User.id == user_id).limit(1))
        if user is None:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "User not found")
        return user

    @staticmethod
    def _active_user_select() -> Select[tuple[User]]:
        return select(User).where(User.is_delete == 0)
