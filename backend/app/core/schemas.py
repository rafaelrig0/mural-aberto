from pydantic import BaseModel, ConfigDict


class AppSchema(BaseModel):
    """Base dos schemas: remove espaços nas pontas das strings."""

    model_config = ConfigDict(str_strip_whitespace=True)


class ORMSchema(AppSchema):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
