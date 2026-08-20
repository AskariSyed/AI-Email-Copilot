import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import correlation_id_var, get_logger, setup_logging
from app.core.scheduler import start_scheduler, stop_scheduler

logger = get_logger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Application starting up...")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Application shutting down...")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_observability_context(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} completed in {process_time:.2f}ms", extra={"latency_ms": process_time, "status_code": response.status_code, "path": request.url.path})
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"{request.method} {request.url.path} failed after {process_time:.2f}ms: {e!s}", exc_info=True, extra={"latency_ms": process_time, "path": request.url.path})
        raise

@app.get("/")
def root():
    return {"message": "Welcome to AI Email Copilot API"}


from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.drafts import router as drafts_router
from app.api.emails import router as emails_router
from app.api.gmail import router as gmail_router
from app.api.send import router as send_router
from app.api.settings import router as settings_router

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(
    emails_router, prefix=f"{settings.API_V1_STR}/emails", tags=["emails"]
)
app.include_router(send_router, prefix=f"{settings.API_V1_STR}/emails", tags=["emails"])
app.include_router(gmail_router, prefix=f"{settings.API_V1_STR}/gmail", tags=["gmail"])
app.include_router(
    drafts_router, prefix=f"{settings.API_V1_STR}/drafts", tags=["drafts"]
)
app.include_router(
    settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"]
)
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}", tags=["chat"])
