from enum import IntEnum


class ErrorCode(IntEnum):
    SUCCESS = 0
    PARAMS_ERROR = 40000
    NOT_LOGIN_ERROR = 40100
    NO_AUTH_ERROR = 40101
    NOT_FOUND_ERROR = 40400
    SYSTEM_ERROR = 50000
