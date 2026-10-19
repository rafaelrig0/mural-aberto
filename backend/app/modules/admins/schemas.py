from pydantic import EmailStr, Field

from app.core.schemas import AppSchema, ORMSchema


class LoginRequest(AppSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(AppSchema):
    access_token: str
    token_type: str = "bearer"  # noqa: S105  (nome do tipo de token, não é um segredo)
    expires_in: int


class AdminRead(ORMSchema):
    id: int
    email: EmailStr
