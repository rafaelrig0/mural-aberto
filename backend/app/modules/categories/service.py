import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.modules.categories.models import Category
from app.modules.works.models import Work


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada.")
    return category


def _apply_name(category: Category, name: str) -> None:
    slug = slugify(name)
    if not slug:
        raise UnprocessableError("O nome da categoria deve conter letras ou números.")
    category.name = name
    category.slug = slug


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Já existe uma categoria com este nome.") from exc


def create_category(db: Session, name: str) -> Category:
    category = Category()
    _apply_name(category, name)
    db.add(category)
    _commit_or_conflict(db)
    return category


def update_category(db: Session, category_id: int, name: str) -> Category:
    category = get_category(db, category_id)
    _apply_name(category, name)
    _commit_or_conflict(db)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    works_count = db.scalar(
        select(func.count()).select_from(Work).where(Work.category_id == category_id)
    )
    if works_count:
        raise ConflictError("A categoria possui obras e não pode ser excluída.")
    db.delete(category)
    db.commit()
