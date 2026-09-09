"""FastAPI Application Entry Point for Municipal FAQ Chatbot."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.chat import router as chat_router

# Load environment configuration from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Municipal Service FAQ Chatbot",
    description="Conversational public-service assistant for municipal queries with grounded RAG retrieval and live weather integration.",
    version="1.0.0",
)

# CORS middleware for local web browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints under root (/health, /chat, /clear)
app.include_router(chat_router)

# Mount frontend directory for browser UI
current_dir = Path(__file__).resolve().parent
frontend_dir = current_dir.parent / "frontend"

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info("Mounted frontend directory from %s", frontend_dir)
else:
    logger.warning("Frontend directory %s does not exist yet.", frontend_dir)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
