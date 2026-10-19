"""Cria as categorias iniciais (idempotente). Uso: python -m app.scripts.seed_categories"""

from sqlalchemy import select

import app.models  # noqa: F401  (registra todos os models)
from app.core.database import SessionLocal
from app.modules.categories import service
from app.modules.categories.models import Category

DEFAULT_CATEGORIES = ["Fotografia", "Pintura", "Grafite", "Desenho", "Poema", "Crônica", "Conto"]


def main() -> None:
    with SessionLocal() as db:
        existing = set(db.scalars(select(Category.name)))
        created = [name for name in DEFAULT_CATEGORIES if name not in existing]
        for name in created:
            service.create_category(db, name)
    print(f"Categorias criadas: {', '.join(created) if created else 'nenhuma (já existiam)'}")


if __name__ == "__main__":
    main()
