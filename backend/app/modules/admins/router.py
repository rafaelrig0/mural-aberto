from fastapi import APIRouter, Request

from app.api.deps import CurrentAdmin, DbSession
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token
from app.modules.admins import service
from app.modules.admins.schemas import AdminRead, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit(lambda: get_settings().rate_limit_login)
def login(request: Request, payload: LoginRequest, db: DbSession) -> TokenResponse:
    admin = service.authenticate(db, payload.email, payload.password)
    token, expires_in = create_access_token(admin.id)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=AdminRead)
def me(admin: CurrentAdmin) -> AdminRead:
    return AdminRead.model_validate(admin)
