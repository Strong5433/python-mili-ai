import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.core.code_gen_types import (
    CODE_GEN_TYPE_HTML,
    CODE_GEN_TYPE_MULTI_FILE,
    CODE_GEN_TYPE_VUE_PROJECT,
)
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException


class CodeParser(ABC):
    code_gen_type: str

    @abstractmethod
    def parse(self, raw_text: str) -> str:
        raise NotImplementedError


class HtmlCodeParser(CodeParser):
    code_gen_type = CODE_GEN_TYPE_HTML

    def parse(self, raw_text: str) -> str:
        html_code_block = re.search(r"```html\s*(.*?)```", raw_text, re.IGNORECASE | re.DOTALL)
        if html_code_block:
            return html_code_block.group(1).strip()

        generic_code_block = re.search(r"```[a-zA-Z0-9_-]*\s*(.*?)```", raw_text, re.DOTALL)
        if generic_code_block:
            return generic_code_block.group(1).strip()

        return raw_text.strip()


class MultiFileCodeParser(CodeParser):
    code_gen_type = CODE_GEN_TYPE_MULTI_FILE

    def parse(self, raw_text: str) -> str:
        return raw_text.strip()


class VueProjectCodeParser(CodeParser):
    code_gen_type = CODE_GEN_TYPE_VUE_PROJECT

    def parse(self, raw_text: str) -> str:
        return raw_text.strip()


class CodeParserExecutor:
    def __init__(self, parsers: Sequence[CodeParser] | None = None) -> None:
        parser_list = (
            list(parsers)
            if parsers is not None
            else [HtmlCodeParser(), MultiFileCodeParser(), VueProjectCodeParser()]
        )
        self._parsers = {parser.code_gen_type: parser for parser in parser_list}

    def parse(self, code_gen_type: str, raw_text: str) -> str:
        parser = self._parsers.get(code_gen_type)
        if parser is None:
            raise BusinessException(ErrorCode.PARAMS_ERROR, f"Unsupported code_gen_type: {code_gen_type}")
        parsed = parser.parse(raw_text)
        if not parsed:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "Parsed code is empty")
        return parsed


def parse_html_code(raw_text: str) -> str:
    return HtmlCodeParser().parse(raw_text)
