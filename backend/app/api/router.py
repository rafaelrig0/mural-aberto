from fastapi import APIRouter

from app.modules.admins.router import router as auth_router
from app.modules.categories.router import admin_router as admin_categories_router
from app.modules.categories.router import public_router as categories_router
from app.modules.comments.router import admin_router as admin_comments_router
from app.modules.comments.router import public_router as comments_router
from app.modules.feedback.router import admin_router as admin_feedback_router
from app.modules.feedback.router import public_router as feedback_router
from app.modules.moderation.router import admin_router as admin_moderation_router
from app.modules.works.router import admin_router as admin_works_router
from app.modules.works.router import public_router as works_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(works_router)
api_router.include_router(comments_router)
api_router.include_router(feedback_router)
api_router.include_router(admin_categories_router)
api_router.include_router(admin_works_router)
api_router.include_router(admin_comments_router)
api_router.include_router(admin_feedback_router)
api_router.include_router(admin_moderation_router)
