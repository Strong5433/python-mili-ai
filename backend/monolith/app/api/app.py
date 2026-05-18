import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.codegen_routing_service import AiCodeGenTypeRoutingService
from app.core.ai_codegen_facade import AiCodeGeneratorFacade
from app.core.codegen_workflow import CodeGenWorkflowRunner
from app.core.config import Settings
from app.core.edit_modes import EDIT_MODE_FULL
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import BaseResponse, success_response
from app.core.sse import build_sse_data, build_sse_event
from app.dependencies import (
    get_ai_codegen_facade,
    get_ai_routing_service,
    get_app_service,
    get_app_settings,
    get_chat_history_service,
    get_codegen_workflow_runner,
    get_db_session,
    get_login_user,
    get_rate_limit_service,
    get_screenshot_service,
    require_role,
)
from app.models.user import User
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppDeployRequest,
    AppQueryRequest,
    AppRouteCodeGenRequest,
    AppRouteCodeGenResult,
    AppScreenshotRequest,
    AppUpdateRequest,
    AppVersionRollbackRequest,
    AppVersionSnapshotRequest,
    AppVersionVO,
    AppVO,
    PageAppVO,
)
from app.schemas.user import DeleteRequest
from app.services.app_service import AppService
from app.services.chat_history_service import (
    MESSAGE_TYPE_ASSISTANT,
    MESSAGE_TYPE_USER,
    ChatHistoryService,
)
from app.services.rate_limit_service import RateLimitService
from app.services.screenshot_service import ScreenshotService
from app.services.user_service import USER_ROLE_ADMIN

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/app", tags=["app"])


@router.post("/add", response_model=BaseResponse[int])
async def add_app(
    payload: AppAddRequest,
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
    ai_routing_service: AiCodeGenTypeRoutingService = Depends(get_ai_routing_service),
) -> BaseResponse[int]:
    app_id = await app_service.add_app(
        db=db,
        payload=payload,
        login_user=login_user,
        routing_service=ai_routing_service,
    )
    return success_response(app_id)


@router.post("/update", response_model=BaseResponse[bool])
async def update_app(
    payload: AppUpdateRequest,
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[bool]:
    result = await app_service.update_app(db, payload, login_user)
    return success_response(result)


@router.post("/delete", response_model=BaseResponse[bool])
async def delete_app(
    payload: DeleteRequest,
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[bool]:
    result = await app_service.delete_app(db, payload.id or 0, login_user)
    return success_response(result)


@router.get("/get/vo", response_model=BaseResponse[AppVO])
async def get_app_vo_by_id(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[AppVO]:
    app_vo = await app_service.get_app_vo_by_id(db, id)
    return success_response(app_vo)


@router.post("/my/list/page/vo", response_model=BaseResponse[PageAppVO])
async def list_my_app_vo_by_page(
    payload: AppQueryRequest,
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[PageAppVO]:
    page = await app_service.list_my_app_vo_by_page(db, payload, login_user)
    return success_response(page)


@router.post("/good/list/page/vo", response_model=BaseResponse[PageAppVO])
async def list_good_app_vo_by_page(
    payload: AppQueryRequest,
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[PageAppVO]:
    page = await app_service.list_good_app_vo_by_page(db, payload)
    return success_response(page)


@router.post("/admin/delete", response_model=BaseResponse[bool])
async def delete_app_by_admin(
    payload: DeleteRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[bool]:
    result = await app_service.delete_app_by_admin(db, payload.id or 0)
    return success_response(result)


@router.post("/admin/update", response_model=BaseResponse[bool])
async def update_app_by_admin(
    payload: AppAdminUpdateRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[bool]:
    result = await app_service.update_app_by_admin(db, payload)
    return success_response(result)


@router.post("/admin/list/page/vo", response_model=BaseResponse[PageAppVO])
async def list_app_vo_by_page_by_admin(
    payload: AppQueryRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[PageAppVO]:
    page = await app_service.list_app_vo_by_page_by_admin(db, payload)
    return success_response(page)


@router.get("/admin/get/vo", response_model=BaseResponse[AppVO])
async def get_app_vo_by_id_by_admin(
    id: int,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[AppVO]:
    app_vo = await app_service.get_app_vo_by_id(db, id)
    return success_response(app_vo)


@router.post("/deploy", response_model=BaseResponse[str])
async def deploy_app(
    payload: AppDeployRequest,
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[str]:
    deploy_url = await app_service.deploy_app(
        db=db,
        payload=payload,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
        deploy_domain=settings.deploy_domain,
    )
    return success_response(deploy_url)


@router.get("/download/{app_id}")
async def download_app_code(
    app_id: int = Path(gt=0),
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> Response:
    zip_bytes = await app_service.build_download_zip_bytes(
        db=db,
        app_id=app_id,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
    )
    headers = {"Content-Disposition": f'attachment; filename="{app_id}.zip"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


@router.get("/download/project/{app_id}")
async def download_app_project(
    app_id: int = Path(gt=0),
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> Response:
    zip_bytes = await app_service.build_project_download_zip_bytes(
        db=db,
        app_id=app_id,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
    )
    headers = {"Content-Disposition": f'attachment; filename="project-{app_id}.zip"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


@router.post("/route/codegen", response_model=BaseResponse[AppRouteCodeGenResult])
async def route_code_gen_type(
    payload: AppRouteCodeGenRequest,
    ai_routing_service: AiCodeGenTypeRoutingService = Depends(get_ai_routing_service),
) -> BaseResponse[AppRouteCodeGenResult]:
    decision = await ai_routing_service.route(payload.prompt, payload.preferred_code_gen_type)
    return success_response(
        AppRouteCodeGenResult(
            code_gen_type=decision.code_gen_type,
            reason=decision.reason,
            source=decision.source,
        )
    )


@router.post("/screenshot", response_model=BaseResponse[str])
async def capture_app_screenshot(
    payload: AppScreenshotRequest,
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
    screenshot_service: ScreenshotService = Depends(get_screenshot_service),
) -> BaseResponse[str]:
    app_id = payload.app_id or 0
    screenshot_url = await screenshot_service.capture_app_screenshot(
        db=db,
        app_id=app_id,
        login_user=login_user,
        app_service=app_service,
        settings=settings,
    )
    return success_response(screenshot_url)


@router.post("/version/snapshot", response_model=BaseResponse[AppVersionVO])
async def create_app_version_snapshot(
    payload: AppVersionSnapshotRequest,
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[AppVersionVO]:
    app_id = payload.app_id or 0
    snapshot = await app_service.create_version_snapshot(
        db=db,
        app_id=app_id,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
        message=payload.message,
        edit_mode=payload.edit_mode,
    )
    return success_response(snapshot)


@router.get("/version/list", response_model=BaseResponse[list[AppVersionVO]])
async def list_app_versions(
    app_id: int = Query(alias="appId", gt=0),
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[list[AppVersionVO]]:
    versions = await app_service.list_version_snapshots(
        db=db,
        app_id=app_id,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
    )
    return success_response(versions)


@router.post("/version/rollback", response_model=BaseResponse[bool])
async def rollback_app_version(
    payload: AppVersionRollbackRequest,
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
) -> BaseResponse[bool]:
    app_id = payload.app_id or 0
    result = await app_service.rollback_to_version(
        db=db,
        app_id=app_id,
        version=payload.version,
        login_user=login_user,
        generated_root=settings.generated_code_path(),
    )
    return success_response(result)


@router.get("/chat/gen/code")
async def chat_to_gen_code(
    app_id: int = Query(alias="appId", gt=0),
    message: str = Query(min_length=1),
    edit_mode: str = Query(alias="editMode", default=EDIT_MODE_FULL),
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
    ai_facade: AiCodeGeneratorFacade = Depends(get_ai_codegen_facade),
) -> StreamingResponse:
    app_entity = await app_service.get_app_entity_by_id(db, app_id)
    if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
        raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")
    normalized_edit_mode = app_service.normalize_edit_mode(edit_mode)

    user_message = message.strip()
    user_prompt = user_message
    if app_entity.init_prompt:
        user_prompt = f"{app_entity.init_prompt}\n\n{user_prompt}"

    async def _stream() -> AsyncIterator[str]:
        try:
            await rate_limit_service.assert_chat_rate_limit(login_user.id, route="gen-code")
            await chat_history_service.add_chat_message(
                db,
                app_id=app_entity.id,
                user_id=login_user.id,
                message_type=MESSAGE_TYPE_USER,
                message=user_message,
            )
            ai_chunks: list[str] = []
            async for chunk in ai_facade.generate_and_save_code_stream(
                app_id=app_entity.id,
                user_message=user_prompt,
                code_gen_type=app_entity.code_gen_type,
                edit_mode=normalized_edit_mode,
            ):
                if isinstance(chunk, str):
                    ai_chunks.append(chunk)
                    yield build_sse_data({"d": chunk})
                else:
                    yield build_sse_data(chunk)
            assistant_message = "".join(ai_chunks).strip()
            if assistant_message:
                await chat_history_service.add_chat_message(
                    db,
                    app_id=app_entity.id,
                    user_id=login_user.id,
                    message_type=MESSAGE_TYPE_ASSISTANT,
                    message=assistant_message,
                )
            try:
                await app_service.create_version_snapshot(
                    db=db,
                    app_id=app_entity.id,
                    login_user=login_user,
                    generated_root=settings.generated_code_path(),
                    message=user_message,
                    edit_mode=normalized_edit_mode,
                )
            except BusinessException as snapshot_exc:
                logger.warning("Create version snapshot skipped: %s", snapshot_exc.message)
            yield build_sse_event("done", "done")
        except BusinessException as exc:
            yield build_sse_event(
                "business-error",
                {"code": int(exc.code), "message": exc.message},
            )
        except Exception as exc:
            logger.exception("Unexpected SSE error: %s", exc)
            yield build_sse_event(
                "business-error",
                {"code": int(ErrorCode.SYSTEM_ERROR), "message": "System error"},
            )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_stream(), media_type="text/event-stream", headers=headers)


@router.get("/chat/gen/workflow")
async def chat_to_gen_code_workflow(
    app_id: int = Query(alias="appId", gt=0),
    message: str = Query(min_length=1),
    edit_mode: str = Query(alias="editMode", default=EDIT_MODE_FULL),
    login_user: User = Depends(get_login_user),
    settings: Settings = Depends(get_app_settings),
    db: AsyncSession = Depends(get_db_session),
    app_service: AppService = Depends(get_app_service),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
    workflow_runner: CodeGenWorkflowRunner = Depends(get_codegen_workflow_runner),
) -> StreamingResponse:
    app_entity = await app_service.get_app_entity_by_id(db, app_id)
    if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
        raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")
    normalized_edit_mode = app_service.normalize_edit_mode(edit_mode)

    user_message = message.strip()
    user_prompt = user_message
    if app_entity.init_prompt:
        user_prompt = f"{app_entity.init_prompt}\n\n{user_prompt}"

    async def _stream() -> AsyncIterator[str]:
        try:
            await rate_limit_service.assert_chat_rate_limit(login_user.id, route="gen-workflow")
            await chat_history_service.add_chat_message(
                db,
                app_id=app_entity.id,
                user_id=login_user.id,
                message_type=MESSAGE_TYPE_USER,
                message=user_message,
            )
            ai_chunks: list[str] = []
            async for chunk in workflow_runner.run_stream(
                app_id=app_entity.id,
                user_message=user_prompt,
                code_gen_type=app_entity.code_gen_type,
                edit_mode=normalized_edit_mode,
            ):
                if isinstance(chunk, str):
                    ai_chunks.append(chunk)
                    yield build_sse_data({"d": chunk})
                else:
                    yield build_sse_data(chunk)
            assistant_message = "".join(ai_chunks).strip()
            if assistant_message:
                await chat_history_service.add_chat_message(
                    db,
                    app_id=app_entity.id,
                    user_id=login_user.id,
                    message_type=MESSAGE_TYPE_ASSISTANT,
                    message=assistant_message,
                )
            try:
                await app_service.create_version_snapshot(
                    db=db,
                    app_id=app_entity.id,
                    login_user=login_user,
                    generated_root=settings.generated_code_path(),
                    message=user_message,
                    edit_mode=normalized_edit_mode,
                )
            except BusinessException as snapshot_exc:
                logger.warning("Create version snapshot skipped: %s", snapshot_exc.message)
            yield build_sse_event("done", "done")
        except BusinessException as exc:
            yield build_sse_event(
                "business-error",
                {"code": int(exc.code), "message": exc.message},
            )
        except Exception as exc:
            logger.exception("Unexpected workflow SSE error: %s", exc)
            yield build_sse_event(
                "business-error",
                {"code": int(ErrorCode.SYSTEM_ERROR), "message": "System error"},
            )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_stream(), media_type="text/event-stream", headers=headers)
