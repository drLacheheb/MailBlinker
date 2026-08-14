from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root_health():
    return {
        "service": "MailBlinker API",
        "status": "online",
        "version": "1.0.0",
    }
