import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import DataError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

IGNORED_LOC_PARTS = {"body", "query", "path", "form", "header"}
VALUE_ERROR_PREFIX = "Value error, "


class AppError(Exception):
    """Erro de domínio com status HTTP e código estável para o frontend."""

    status_code = 400
    code = "bad_request"
    default_message = "Requisição inválida."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Credenciais inválidas ou ausentes."


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Recurso não encontrado."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "A operação conflita com o estado atual do recurso."


class InvalidTransitionError(ConflictError):
    code = "invalid_transition"
    default_message = "Transição de estado não permitida."


class UnprocessableError(AppError):
    status_code = 422
    code = "invalid_submission"
    default_message = "Os dados enviados são inválidos."


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"
    default_message = "O conteúdo enviado excede o tamanho permitido."


class UnsupportedMediaError(AppError):
    status_code = 415
    code = "unsupported_media_type"
    default_message = "Formato de arquivo não permitido."


class StorageError(AppError):
    status_code = 502
    code = "storage_unavailable"
    default_message = "O serviço de armazenamento está indisponível. Tente novamente."


def error_response(
    status_code: int, code: str, message: str, details: list[dict[str, str]] | None = None
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def _format_validation_errors(errors: Any) -> list[dict[str, str]]:
    """Mantém só campo e mensagem: nunca devolve o valor enviado nem objetos internos."""
    details = []
    for err in errors:
        field = ".".join(str(part) for part in err["loc"] if part not in IGNORED_LOC_PARTS)
        message = str(err["msg"]).removeprefix(VALUE_ERROR_PREFIX)
        details.append({"field": field, "message": message})
    return details


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            422,
            "validation_error",
            "Dados inválidos.",
            _format_validation_errors(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large"}
        code = codes.get(exc.status_code, f"http_{exc.status_code}")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit(_: Request, __: RateLimitExceeded) -> JSONResponse:
        return error_response(
            429, "rate_limited", "Muitas requisições. Tente novamente mais tarde."
        )

    @app.exception_handler(DataError)
    async def handle_data_error(request: Request, exc: DataError) -> JSONResponse:
        """Valor que o banco não aceita (ex.: id acima do limite de INTEGER): é erro do cliente,
        não do servidor. Sem isto, /works/99999999999 respondia 500."""
        logger.warning(
            "Valor rejeitado pelo banco em %s %s: %s",
            request.method,
            request.url.path,
            type(exc.orig).__name__,
        )
        return error_response(
            422, "invalid_parameter", "Um dos valores informados está fora do intervalo permitido."
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Erro não tratado em %s %s", request.method, request.url.path, exc_info=exc
        )
        return error_response(500, "internal_error", "Erro interno do servidor.")
