from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError, UnprocessableError
from app.core.security import hash_password, verify_password
from app.modules.admins.models import Admin

MIN_PASSWORD_LENGTH = 12
_email_adapter: TypeAdapter[str] = TypeAdapter(EmailStr)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def authenticate(db: Session, email: str, password: str) -> Admin:
    """Mensagem genérica de propósito: não revela se o e-mail existe ou se a conta está inativa."""
    admin = db.scalar(select(Admin).where(Admin.email == normalize_email(email)))
    password_ok = verify_password(password, admin.password_hash if admin else None)
    if admin is None or not password_ok or not admin.is_active:
        raise UnauthorizedError("E-mail ou senha inválidos.")
    return admin


def get_active_admin(db: Session, admin_id: int) -> Admin | None:
    admin = db.get(Admin, admin_id)
    return admin if admin is not None and admin.is_active else None


def create_admin(db: Session, email: str, password: str) -> Admin:
    # O login exige um e-mail válido (LoginRequest usa EmailStr): sem esta checagem, o script
    # create_admin aceitava "admin" e criava uma conta que nunca conseguiria entrar.
    try:
        _email_adapter.validate_python(email.strip())
    except ValidationError as exc:
        raise UnprocessableError("Informe um e-mail válido para o administrador.") from exc
    if len(password) < MIN_PASSWORD_LENGTH:
        raise UnprocessableError(f"A senha deve ter ao menos {MIN_PASSWORD_LENGTH} caracteres.")
    admin = Admin(email=normalize_email(email), password_hash=hash_password(password))
    db.add(admin)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Já existe um administrador com este e-mail.") from exc
    return admin
