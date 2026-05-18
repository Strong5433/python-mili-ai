from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.ai.openai_compatible_service import OpenAICompatibleService
from app.core.code_file_saver import CodeFileSaverExecutor
from app.core.code_gen_types import (
    CODE_GEN_TYPE_HTML,
    CODE_GEN_TYPE_MULTI_FILE,
    CODE_GEN_TYPE_VUE_PROJECT,
)
from app.core.code_parser import CodeParserExecutor
from app.core.config import Settings
from app.core.edit_modes import EDIT_MODE_INCREMENTAL
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.prompt_loader import load_prompt


class AiCodeGeneratorFacade:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ai_service = OpenAICompatibleService(settings)
        self.parser_executor = CodeParserExecutor()
        self.saver_executor = CodeFileSaverExecutor()

    async def generate_and_save_code_stream(
        self,
        app_id: int,
        user_message: str,
        code_gen_type: str,
        edit_mode: str,
    ) -> AsyncIterator[str | dict[str, Any]]:
        prompt_name = self._resolve_prompt_name(code_gen_type)
        system_prompt = load_prompt(prompt_name)
        guarded_message = self._guard_and_trim_prompt(user_message)
        final_user_message = self._build_edit_mode_message(guarded_message, edit_mode)

        yield self._tool_event("start", "llm.generate", "开始调用模型生成代码")
        chunks: list[str] = []
        async for chunk in self.ai_service.generate_stream(system_prompt=system_prompt, user_prompt=final_user_message):
            chunks.append(chunk)
            yield chunk
        yield self._tool_event("end", "llm.generate", f"模型输出完成，累计 {sum(len(item) for item in chunks)} 字符")

        final_text = "".join(chunks).strip()
        if not final_text:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "LLM empty response")

        yield self._tool_event("start", "parse.output", "开始解析生成内容")
        parsed_code = self.parser_executor.parse(code_gen_type=code_gen_type, raw_text=final_text)
        yield self._tool_event("end", "parse.output", f"解析完成，长度 {len(parsed_code)} 字符")

        yield self._tool_event("start", "write.files", "开始落盘生成文件")
        output_dir = self.saver_executor.save(
            code_gen_type=code_gen_type,
            app_id=app_id,
            parsed_code=parsed_code,
            settings=self.settings,
            edit_mode=edit_mode,
        )
        written_files = self._list_written_files(output_dir)
        for index, file_path in enumerate(written_files, start=1):
            yield self._tool_event(
                "delta",
                "write.files",
                f"[{index}/{len(written_files)}] 已写入 {file_path}",
            )
        yield self._tool_event(
            "end",
            "write.files",
            f"文件落盘完成，共 {len(written_files)} 个文件，目录 {output_dir.name}",
        )

    @staticmethod
    def _resolve_prompt_name(code_gen_type: str) -> str:
        if code_gen_type == CODE_GEN_TYPE_HTML:
            return "codegen-html-system-prompt.txt"
        if code_gen_type == CODE_GEN_TYPE_MULTI_FILE:
            return "codegen-multi-file-system-prompt.txt"
        if code_gen_type == CODE_GEN_TYPE_VUE_PROJECT:
            return "codegen-vue-project-system-prompt.txt"
        raise BusinessException(ErrorCode.PARAMS_ERROR, f"Unsupported code_gen_type: {code_gen_type}")

    @staticmethod
    def _tool_event(event: str, tool: str, message: str) -> dict[str, Any]:
        return {"type": "tool", "event": event, "tool": tool, "message": message}

    @staticmethod
    def _list_written_files(output_dir: Path) -> list[str]:
        if not output_dir.exists() or not output_dir.is_dir():
            return []
        return sorted(path.relative_to(output_dir).as_posix() for path in output_dir.rglob("*") if path.is_file())

    @staticmethod
    def _build_edit_mode_message(user_message: str, edit_mode: str) -> str:
        content = user_message.strip()
        if edit_mode == EDIT_MODE_INCREMENTAL:
            return (
                f"{content}\n\n"
                "请采用增量修改模式：仅输出需要变更的文件，使用 ```file:<相对路径> ... ``` 代码块格式。"
            )
        return (
            f"{content}\n\n"
            "请采用全量修改模式：输出完整结果（而不是只输出差异）。"
        )

    def _guard_and_trim_prompt(self, user_message: str) -> str:
        content = (user_message or "").strip()
        block_words = [item.strip().lower() for item in self.settings.prompt_block_keywords.split(",") if item.strip()]
        normalized = content.lower()
        for word in block_words:
            if word and word in normalized:
                raise BusinessException(ErrorCode.PARAMS_ERROR, f"Prompt blocked by safety rule: {word}")

        max_len = max(256, int(self.settings.llm_max_prompt_chars))
        if len(content) > max_len:
            content = content[:max_len]
        return content
