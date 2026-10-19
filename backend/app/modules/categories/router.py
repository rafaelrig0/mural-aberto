from fastapi import APIRouter, Depends, Response, status

from app.api.deps import DbSession, get_current_admin
from app.modules.categories import service
from app.modules.categories.schemas import CategoryRead, CategoryWrite

public_router = APIRouter(prefix="/categories", tags=["categories"])
admin_router = APIRouter(
    prefix="/admin/categories",
    tags=["admin: categories"],
    dependencies=[Depends(get_current_admin)],
)


@public_router.get("", response_model=list[CategoryRead])
def list_categories(db: DbSession) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in service.list_categories(db)]


@admin_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryWrite, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(db, payload.name))


@admin_router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryWrite, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.update_category(db, category_id, payload.name))


@admin_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession) -> Response:
    service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
