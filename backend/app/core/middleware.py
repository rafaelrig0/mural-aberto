import logging

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

TOO_LARGE_MESSAGE = "O conteúdo enviado excede o tamanho permitido."
INTERNAL_ERROR_MESSAGE = "Erro interno do servidor."


class UnhandledErrorMiddleware:
    """Converte erros não tratados em 500 JSON DENTRO da camada de CORS.

    O handler de Exception do Starlette roda no ServerErrorMiddleware, que fica por fora de
    todos os middlewares. Por isso as respostas 500 saíam sem os cabeçalhos CORS, e o navegador
    mostrava "erro de CORS" em vez da mensagem padrão. Este middleware fica logo abaixo do CORS.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, tracked_send)
        except Exception:
            if response_started:  # parte da resposta já saiu: não dá para trocar por um 500
                raise
            logger.exception("Erro não tratado em %s %s", scope["method"], scope["path"])
            response = JSONResponse(
                status_code=500,
                content={"error": {"code": "internal_error", "message": INTERNAL_ERROR_MESSAGE}},
            )
            await response(scope, receive, send)


class BodySizeLimitMiddleware:
    """Rejeita corpos de requisição grandes demais, antes de o framework processá-los.

    Verifica o Content-Length (rejeição imediata) e também conta os bytes recebidos, para
    cobrir requisições com transferência em partes (chunked), que não informam o tamanho.
    """

    def __init__(
        self, app: ASGIApp, *, default_limit: int, path_limits: dict[tuple[str, str], int]
    ) -> None:
        self.app = app
        self.default_limit = default_limit
        self.path_limits = path_limits

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        limit = self.path_limits.get((scope["method"], scope["path"]), self.default_limit)
        declared = Headers(scope=scope).get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            response = JSONResponse(
                status_code=413,
                content={"error": {"code": "payload_too_large", "message": TOO_LARGE_MESSAGE}},
            )
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise HTTPException(status_code=413, detail=TOO_LARGE_MESSAGE)
            return message

        await self.app(scope, limited_receive, send)
