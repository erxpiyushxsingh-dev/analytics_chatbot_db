"""
FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router
from services.db_service import db_service
from config import config

logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("Starting Analytics Chatbot API…")
    await db_service.connect()
    logger.info("Database connected")
    yield
    logger.info("Shutting down…")
    await db_service.disconnect()
    logger.info("Database disconnected")


app = FastAPI(
    title="Business Analytics Chatbot API",
    description=(
        "Natural language → SQL → Result → Chart pipeline. "
        "Accepts natural language questions, converts them to SQL via LLM, "
        "validates for safety, executes on the database, and returns "
        "JSON results with chart-ready data."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["analytics"])

# Global exception handler to ensure JSON responses for all errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all uncaught exceptions and return JSON."""
    import traceback
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": str(exc), "detail": "Internal server error"}
    )

# Serve frontend UI
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_ui():
    """Serve the chatbot UI."""
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Analytics Chatbot API. Visit /docs for Swagger UI."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
