from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.api.routes import router
from src.config import cfg
from src.core.logging import setup_logging
from src.core.tracing import setup_tracing, traceable

log = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    setup_tracing()
    log.info("app_starting", env=cfg.get("app", {}).get("env", "development"))
    mcp_enabled = cfg.get("mcp", {}).get("enabled", False)
    if mcp_enabled:
        try:
            from src.tools.mcp_client import load_mcp_tools

            count = await load_mcp_tools()
            log.info("mcp_loaded", tool_count=count)
        except Exception:
            log.exception("mcp_load_failed")
    else:
        log.info("mcp_disabled")

    yield

    log.info("app_shutting_down")


@traceable(name="create_app")
def create_app() -> FastAPI:
    app = FastAPI(
        title=cfg.get("app", {}).get("name", "Inventory Replenishment Agent"),
        version=cfg.get("app", {}).get("version", "0.1.0"),
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", error=str(exc), path=str(request.url))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(router)

    return app


app = create_app()
