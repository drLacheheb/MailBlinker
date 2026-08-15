from fastapi import APIRouter

from .emails import router as emails_router
from .health import router as health_router
from .pixel import router as pixel_router
from .webhook import close_webhook_bot, setup_webhook
from .webhook import router as webhook_router

router = APIRouter()
router.include_router(health_router)
router.include_router(pixel_router)
router.include_router(emails_router)
router.include_router(webhook_router)

__all__ = ["router", "setup_webhook", "close_webhook_bot"]
