from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401
from app.config.config import settings
from app.modules.announcements.router import router as announcements_router
from app.modules.calendar.router import router as calendar_router
from app.modules.notifications.router import router as notifications_router
from app.modules.users.router import admin_router, directory_router, router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Secure internal announcements, calendar, acknowledgement and notification API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for router in (auth_router, admin_router, directory_router, announcements_router, calendar_router, notifications_router):
    app.include_router(router, prefix="/api/v1")


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "environment": settings.environment}
