"""FastAPI entrypoint for the Contract Analysis Engine."""

import argparse
import logging

import uvicorn
from fastapi import FastAPI

from database import Base, engine
from routers import extraction, upload, vehicle

# Configure app-wide logging so errors are visible in console and deployment logs.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Create all SQLAlchemy tables on startup for quick local setup.
# In production, use migrations (Alembic) for schema versioning.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contract Analysis Engine",
    description="Uploads contracts, extracts OCR text, parses SLA fields with LLM, and decodes VINs.",
    version="1.0.0",
)


@app.get("/")
async def health_check():
    """Simple health endpoint to confirm the API server is running."""
    return {"status": "ok", "message": "Contract Analysis Engine is running."}


# Include feature routers in main application.
app.include_router(upload.router)
app.include_router(extraction.router)
app.include_router(vehicle.router)


def run_server() -> None:
    """Run the FastAPI application with optional host/port CLI flags."""
    parser = argparse.ArgumentParser(
        description="Run the Contract Analysis Engine API server.",
    )
    parser.add_argument("file", nargs="?", help="Optional file path (not used directly).")
    parser.add_argument("--host", default="127.0.0.1", help="Host for Uvicorn server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for Uvicorn server.")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")
    args = parser.parse_args()

    # If a file path is provided, explain the correct API flow for beginners.
    if args.file:
        logging.getLogger(__name__).info(
            "Received file argument '%s'. Start server first, then upload via POST /upload-contract.",
            args.file,
        )

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    """Allow `python main.py` to start the API server directly."""
    run_server()
