from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_app_settings, get_db_session, get_user_service, require_role
from app.models.user import User
from app.schemas.user import (
    DeleteRequest,
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
from app.services.user_service import USER_ROLE_ADMIN, UserService
from app.core.config import Settings
from app.core.response import BaseResponse, success_response

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", response_model=BaseResponse[int])
async def user_register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[int]:
    user_id = await user_service.register(db, payload)
    return success_response(user_id)


@router.post("/login", response_model=BaseResponse[LoginUserVO])
async def user_login(
    payload: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[LoginUserVO]:
    login_user, session_id = await user_service.login(db, payload)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return success_response(login_user)


@router.get("/get/login", response_model=BaseResponse[LoginUserVO])
async def get_login_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[LoginUserVO]:
    session_id = request.cookies.get(settings.session_cookie_name)
    login_user = await user_service.get_login_user(db, session_id)
    return success_response(login_user)


@router.post("/logout", response_model=BaseResponse[bool])
async def user_logout(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_app_settings),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[bool]:
    session_id = request.cookies.get(settings.session_cookie_name)
    result = await user_service.logout(session_id)
    response.delete_cookie(
        key=settings.session_cookie_name,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return success_response(result)


@router.post("/add", response_model=BaseResponse[int])
async def add_user(
    payload: UserAddRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[int]:
    user_id = await user_service.add_user(db, payload)
    return success_response(user_id)


@router.get("/get", response_model=BaseResponse[UserData])
async def get_user_by_id(
    id: int,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[UserData]:
    user_data = await user_service.get_user_by_id(db, id)
    return success_response(user_data)


@router.get("/get/vo", response_model=BaseResponse[UserVO])
async def get_user_vo_by_id(
    id: int,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[UserVO]:
    user_data = await user_service.get_user_vo_by_id(db, id)
    return success_response(user_data)


@router.post("/delete", response_model=BaseResponse[bool])
async def delete_user(
    payload: DeleteRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[bool]:
    result = await user_service.delete_user(db, payload.id or 0)
    return success_response(result)


@router.post("/update", response_model=BaseResponse[bool])
async def update_user(
    payload: UserUpdateRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[bool]:
    result = await user_service.update_user(db, payload)
    return success_response(result)


@router.post("/list/page/vo", response_model=BaseResponse[PageUserVO])
async def list_user_vo_by_page(
    payload: UserQueryRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse[PageUserVO]:
    page = await user_service.list_user_vo_by_page(db, payload)
    return success_response(page)


@router.get("/admin/ping", response_model=BaseResponse[bool])
async def admin_ping(_: User = Depends(require_role(USER_ROLE_ADMIN))) -> BaseResponse[bool]:
    return success_response(True)
