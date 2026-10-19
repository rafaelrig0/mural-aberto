import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import app.models as _registered_models  # noqa: F401  (registra todos os models)
from app.api.router import api_router
from app.core.config import BYTES_PER_MB, get_settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.middleware import BodySizeLimitMiddleware, UnhandledErrorMiddleware
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

DEFAULT_BODY_LIMIT_BYTES = BYTES_PER_MB  # 1 MB para tudo, exceto o envio de obras
MULTIPART_OVERHEAD_BYTES = BYTES_PER_MB  # campos de texto e cabeçalhos do formulário


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    app = FastAPI(
        title="API do Catálogo de Obras",
        version="1.0.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.state.limiter = limiter
    register_exception_handlers(app)

    # Os middlewares adicionados por último ficam por fora: o CORS precisa ser o mais externo
    # para que até as respostas 413 do limite de tamanho levem os cabeçalhos CORS.
    # Ordem final (de fora para dentro): CORS → UnhandledError → BodySizeLimit → rotas.
    work_upload_limit = (
        settings.max_image_size_bytes + settings.max_video_size_bytes + MULTIPART_OVERHEAD_BYTES
    )
    app.add_middleware(
        BodySizeLimitMiddleware,
        default_limit=DEFAULT_BODY_LIMIT_BYTES,
        path_limits={("POST", "/api/v1/works"): work_upload_limit},
    )
    # Logo abaixo do CORS: assim os erros 500 também levam os cabeçalhos CORS.
    app.add_middleware(UnhandledErrorMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(api_router)

    @app.get("/health", tags=["infra"])
    def health() -> JSONResponse:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("Health check: banco indisponível")
            return JSONResponse(status_code=503, content={"status": "database_unavailable"})
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()
