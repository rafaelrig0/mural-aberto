from pydantic import Field

from app.core.schemas import AppSchema, ORMSchema


class CategoryWrite(AppSchema):
    name: str = Field(min_length=2, max_length=80)


class CategoryRead(ORMSchema):
    id: int
    name: str
    slug: str
