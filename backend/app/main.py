from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to AI Email Copilot API"}

from app.api.auth import router as auth_router
from app.api.emails import router as emails_router
from app.api.send import router as send_router
from app.api.gmail import router as gmail_router
from app.api.drafts import router as drafts_router
from app.api.settings import router as settings_router
from app.api.chat import router as chat_router

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(emails_router, prefix=f"{settings.API_V1_STR}/emails", tags=["emails"])
app.include_router(send_router, prefix=f"{settings.API_V1_STR}/emails", tags=["emails"])
app.include_router(gmail_router, prefix=f"{settings.API_V1_STR}/gmail", tags=["gmail"])
app.include_router(drafts_router, prefix=f"{settings.API_V1_STR}/drafts", tags=["drafts"])
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}", tags=["chat"])
