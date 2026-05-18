from pathlib import Path

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException


def load_prompt(prompt_name: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / prompt_name
    if not prompt_path.exists():
        raise BusinessException(ErrorCode.SYSTEM_ERROR, f"Prompt not found: {prompt_name}")
    return prompt_path.read_text(encoding="utf-8")
