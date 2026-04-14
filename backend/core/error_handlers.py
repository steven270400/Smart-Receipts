import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymysql import MySQLError

from backend.core.exceptions import AppException, DatabaseException
from backend.core.response import error_response

logger = logging.getLogger("smartreceipts.api")


def _log_api_error(request: Request, message: str) -> None:
    logger.error(
        "api_error path=%s error=%s time=%s",
        request.url.path,
        message,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        _log_api_error(request, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=exc.code, message=exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        message = "; ".join(item.get("msg", "invalid") for item in exc.errors())
        _log_api_error(request, message)
        return JSONResponse(
            status_code=422,
            content=error_response(code=42201, message=message, data=exc.errors()),
        )

    @app.exception_handler(MySQLError)
    async def handle_db_error(request: Request, exc: MySQLError):
        _log_api_error(request, str(exc))
        db_exc = DatabaseException("database operation failed")
        return JSONResponse(
            status_code=db_exc.status_code,
            content=error_response(code=db_exc.code, message=db_exc.message),
        )

    @app.exception_handler(Exception)
    async def handle_unknown_error(request: Request, exc: Exception):
        _log_api_error(request, str(exc))
        return JSONResponse(
            status_code=500,
            content=error_response(code=50000, message="internal server error"),
        )
