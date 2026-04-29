"""Application entrypoint for Green Synth AI.

This file intentionally stays thin:
- Wires FastAPI routes
- Exposes `API_APP` for ASGI servers
- Boots Streamlit UI when executed directly
"""

from __future__ import annotations

import logging

from frontend.app_ui import render_main_page

try:
    from fastapi import FastAPI
    from routes.api import api_router
except Exception:  # pragma: no cover - optional dependency path
    FastAPI = None
    api_router = None

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_api_app():
    """Create and configure FastAPI app for HTTP endpoints."""
    if FastAPI is None or api_router is None:
        logger.warning("FastAPI or API routes unavailable. `API_APP` is disabled.")
        return None

    app = FastAPI(title="Green Synth AI API", version="1.0.0")
    app.include_router(api_router, prefix="/api")
    logger.info("FastAPI app initialized with /api routes.")
    return app


API_APP = create_api_app()
# Backward-compatible ASGI symbol for commands like: uvicorn app:app
app = API_APP


if __name__ == "__main__":
    logger.info("Launching Streamlit frontend page renderer.")
    render_main_page()
