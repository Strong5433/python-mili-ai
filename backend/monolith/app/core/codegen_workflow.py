import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.core.ai_codegen_facade import AiCodeGeneratorFacade
from app.core.config import Settings


class CodeGenWorkflowRunner:
    """M08 minimal workflow runner with node trace and concurrent sub tasks."""

    def __init__(self, settings: Settings) -> None:
        self.facade = AiCodeGeneratorFacade(settings)

    async def run_stream(
        self,
        app_id: int,
        user_message: str,
        code_gen_type: str,
        edit_mode: str,
    ) -> AsyncIterator[str | dict[str, Any]]:
        yield self._event("router", "start", "开始路由生成策略")
        route = "simple"
        if code_gen_type in {"multi_file", "vue_project"}:
            route = "project"
        yield self._event("router", "end", f"路由完成：{route}")

        yield self._event("parallel", "start", "并行执行资源计划与质量检查")
        assets_task = asyncio.create_task(self._collect_assets(user_message))
        quality_task = asyncio.create_task(self._quality_plan(user_message))
        assets, quality = await asyncio.gather(assets_task, quality_task)
        yield self._event("asset_collector", "end", assets)
        yield self._event("quality_checker", "end", quality)
        yield self._event("parallel", "end", "并行节点完成")

        yield self._event("code_generator", "start", "开始执行代码生成节点")
        async for chunk in self.facade.generate_and_save_code_stream(
            app_id=app_id,
            user_message=user_message,
            code_gen_type=code_gen_type,
            edit_mode=edit_mode,
        ):
            yield chunk
        yield self._event("code_generator", "end", "代码生成节点完成")

    @staticmethod
    async def _collect_assets(user_message: str) -> str:
        await asyncio.sleep(0)
        if "图片" in user_message or "图标" in user_message:
            return "检测到图片需求，已规划素材位"
        return "未检测到额外素材需求"

    @staticmethod
    async def _quality_plan(user_message: str) -> str:
        await asyncio.sleep(0)
        if len(user_message) > 120:
            return "提示词较长，启用结构化输出约束"
        return "启用默认质量检查策略"

    @staticmethod
    def _event(node: str, event: str, message: str) -> dict[str, Any]:
        return {
            "type": "workflow",
            "node": node,
            "event": event,
            "message": message,
        }
