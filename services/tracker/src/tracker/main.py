from contextlib import asynccontextmanager

from core import get_logger, init_db, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .security import SecurityHeadersMiddleware

logger = get_logger("tracker.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.success(f"Tracker API ready on {settings.BASE_URL}")
    yield
    logger.info("Tracker API shutting down...")


app = FastAPI(
    title="MailBlinker API",
    description="Self-hosted email tracking and HTML formatting API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "tracker.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
