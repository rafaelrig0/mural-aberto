from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.modules.admins.models import Admin
from app.modules.admins.service import get_active_admin

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


def get_current_admin(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Admin:
    """Exige um token válido e consulta o banco: admin desativado perde o acesso na hora."""
    if credentials is None:
        raise UnauthorizedError("Autenticação necessária.")
    admin_id = decode_access_token(credentials.credentials)
    admin = get_active_admin(db, admin_id) if admin_id is not None else None
    if admin is None:
        raise UnauthorizedError("Token inválido ou expirado.")
    return admin


CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]
