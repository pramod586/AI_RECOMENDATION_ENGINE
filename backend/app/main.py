import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.api.documents import router as document_router
import app.models
from app.api.database import router as database_router
from app.api.conversations import router as conversation_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.config import settings
from app.logging_config import setup_logging


# --------------------------------------------------
# Logging setup
# --------------------------------------------------

setup_logging()

logger = logging.getLogger(__name__)

logger.info("AI Knowledge Assistant API started successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI Knowledge Assistant API",
    description="Backend API for an AI-powered RAG chatbot",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Request / Response Logging Middleware
# --------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):

    start_time = time.time()

    logger.info(
        "Request: %s %s",
        request.method,
        request.url.path,
    )

    try:

        response = await call_next(request)

        process_time = time.time() - start_time

        logger.info(
            "Response: %s %s | Status: %s | Time: %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        return response

    except Exception:

        process_time = time.time() - start_time

        logger.exception(
            "Request failed: %s %s | Time: %.3fs",
            request.method,
            request.url.path,
            process_time,
        )

        raise


# --------------------------------------------------
# Global exception handler
# --------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):

    logger.exception(
        "Unhandled exception: %s %s",
        request.method,
        request.url,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
        },
    )


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Register API routers
# --------------------------------------------------

app.include_router(database_router)
app.include_router(document_router)
app.include_router(conversation_router)
app.include_router(chat_router)
app.include_router(auth_router)


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "AI Knowledge Assistant API is running",
        "status": "success",
    }


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
    }