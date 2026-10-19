"""Registro central dos models.

O SQLAlchemy só resolve relacionamentos entre classes que já foram importadas. Qualquer ponto
de entrada que acesse o banco (API, scripts, migrações, testes) importa este módulo para ter
todos os models carregados, sem depender de quais routers por acaso foram importados.
"""

from app.modules.admins.models import Admin
from app.modules.categories.models import Category
from app.modules.comments.models import Comment
from app.modules.feedback.models import Feedback
from app.modules.media.models import WorkMedia
from app.modules.moderation.models import ModerationLog
from app.modules.works.models import Work

__all__ = ["Admin", "Category", "Comment", "Feedback", "ModerationLog", "Work", "WorkMedia"]
