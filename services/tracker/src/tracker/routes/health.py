from fastapi import APIRouter

router = APIRouter()


@router.get("/")
@router.get("/health")
@router.get("/healthz")
async def root_health():
    return {
        "service": "MailBlinker API",
        "status": "healthy",
        "version": "1.0.0",
    }
