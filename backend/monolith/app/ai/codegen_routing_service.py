import json
import re
from dataclasses import dataclass

from app.ai.openai_compatible_service import OpenAICompatibleService
from app.core.code_gen_types import (
    CODE_GEN_TYPE_HTML,
    CODE_GEN_TYPE_MULTI_FILE,
    CODE_GEN_TYPE_VUE_PROJECT,
    SUPPORTED_CODE_GEN_TYPES,
)
from app.core.config import Settings
from app.core.prompt_loader import load_prompt

_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


@dataclass(slots=True)
class CodeGenRouteDecision:
    code_gen_type: str
    reason: str
    source: str


class AiCodeGenTypeRoutingService:
    """Route prompt to a suitable code generation type."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ai_service = OpenAICompatibleService(settings)

    async def route(self, prompt: str, preferred_code_gen_type: str | None = None) -> CodeGenRouteDecision:
        preferred = (preferred_code_gen_type or "").strip()
        if preferred in SUPPORTED_CODE_GEN_TYPES:
            return CodeGenRouteDecision(
                code_gen_type=preferred,
                reason="用户已显式指定生成模式",
                source="user",
            )

        heuristic = self._heuristic_route(prompt)
        if not self.settings.llm_base_url or not self.settings.llm_api_key:
            return heuristic

        llm_decision = await self._llm_route(prompt)
        if llm_decision is not None:
            return llm_decision
        return heuristic

    async def _llm_route(self, prompt: str) -> CodeGenRouteDecision | None:
        try:
            system_prompt = load_prompt("codegen-routing-system-prompt.txt")
            text = await self.ai_service.generate_text(system_prompt=system_prompt, user_prompt=prompt)
            if not text:
                return None
            decision = self._parse_llm_response(text)
            if decision is None:
                return None
            return CodeGenRouteDecision(
                code_gen_type=decision.code_gen_type,
                reason=decision.reason,
                source="llm",
            )
        except Exception:
            return None

    @staticmethod
    def _heuristic_route(prompt: str) -> CodeGenRouteDecision:
        normalized = (prompt or "").lower()
        vue_keywords = {
            "vue",
            "vite",
            "pinia",
            "router",
            "组件",
            "工程",
            "项目",
            "typescript",
            "ts",
            "npm",
        }
        multi_file_keywords = {
            "多文件",
            "多页面",
            "拆分",
            "目录结构",
            "模块化",
            "component",
            "css",
            "javascript",
            "js",
        }

        if any(token in normalized for token in vue_keywords):
            return CodeGenRouteDecision(
                code_gen_type=CODE_GEN_TYPE_VUE_PROJECT,
                reason="命中 Vue 工程关键词",
                source="heuristic",
            )

        if any(token in normalized for token in multi_file_keywords):
            return CodeGenRouteDecision(
                code_gen_type=CODE_GEN_TYPE_MULTI_FILE,
                reason="命中多文件关键词",
                source="heuristic",
            )

        return CodeGenRouteDecision(
            code_gen_type=CODE_GEN_TYPE_HTML,
            reason="默认回退到 HTML 模式",
            source="heuristic",
        )

    @staticmethod
    def _parse_llm_response(text: str) -> CodeGenRouteDecision | None:
        data = AiCodeGenTypeRoutingService._extract_json_obj(text)
        if data is None:
            return None

        code_gen_type = str(data.get("codeGenType") or data.get("code_gen_type") or "").strip()
        reason = str(data.get("reason") or "").strip() or "LLM 路由"
        if code_gen_type not in SUPPORTED_CODE_GEN_TYPES:
            return None

        return CodeGenRouteDecision(code_gen_type=code_gen_type, reason=reason, source="llm")

    @staticmethod
    def _extract_json_obj(text: str) -> dict | None:
        raw = (text or "").strip()
        if not raw:
            return None

        matched = _JSON_FENCE_PATTERN.search(raw)
        if matched:
            raw = matched.group(1).strip()

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(raw[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
        return None
