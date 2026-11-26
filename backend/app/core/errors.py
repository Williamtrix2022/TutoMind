"""Maps every failure to the contract's `ErrorResponse`: `{code, message, details?}`."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_CODE_BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "file_too_large",
    415: "unsupported_media_type",
    422: "invalid_request",
    429: "too_many_requests",
}


class ApiError(Exception):
    """Domain error raised by endpoints; rendered as an `ErrorResponse`."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def _response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
    return _response(exc.status_code, exc.code, exc.message, exc.details, exc.headers)


async def _http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _CODE_BY_STATUS.get(exc.status_code, "error")
    message = exc.detail if isinstance(exc.detail, str) else code
    return _response(exc.status_code, code, message, headers=getattr(exc, "headers", None))


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Only location and message: `input` and `ctx` could echo secrets (e.g. a password).
    errors = [
        {
            "loc": [str(part) for part in error["loc"]],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _response(422, "invalid_request", "La solicitud no es válida.", {"errors": errors})


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return _response(500, "internal_error", "Error interno del servidor.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled)
