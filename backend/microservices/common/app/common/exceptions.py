from app.common.error_codes import ErrorCode


class BusinessException(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
