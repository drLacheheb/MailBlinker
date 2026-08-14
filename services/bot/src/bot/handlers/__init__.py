from aiogram import Router

from .base import router as base_router
from .format import router as format_router
from .new import router as new_router
from .stats import router as stats_router

router = Router()
router.include_router(base_router)
router.include_router(new_router)
router.include_router(format_router)
router.include_router(stats_router)

__all__ = ["router"]
