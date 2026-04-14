from dataclasses import dataclass


@dataclass
class AppException(Exception):
    message: str
    code: int
    status_code: int = 400


class ParamException(AppException):
    def __init__(self, message: str = "invalid parameters", code: int = 40001):
        super().__init__(message=message, code=code, status_code=400)


class DatabaseException(AppException):
    def __init__(self, message: str = "database error", code: int = 50001):
        super().__init__(message=message, code=code, status_code=500)


class OCRException(AppException):
    def __init__(self, message: str = "ocr error", code: int = 50002):
        super().__init__(message=message, code=code, status_code=500)


class LLMException(AppException):
    def __init__(self, message: str = "llm error", code: int = 50003):
        super().__init__(message=message, code=code, status_code=500)


class NotFoundException(AppException):
    def __init__(self, message: str = "not found", code: int = 40401):
        super().__init__(message=message, code=code, status_code=404)
