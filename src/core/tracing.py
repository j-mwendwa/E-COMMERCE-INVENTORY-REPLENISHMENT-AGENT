import structlog

from src.config import settings

logger = structlog.get_logger()

_langsmith_enabled = bool(settings.langsmith_api_key and settings.langsmith_tracing)

if _langsmith_enabled:
    try:
        from langsmith import traceable

        def is_traceable_enabled() -> bool:
            return True
    except ImportError:
        logger.warning("tracing_import_failed", msg="langsmith package not installed")

        def traceable(*_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def is_traceable_enabled() -> bool:
            return False
else:

    def traceable(*_args, **_kwargs):
        def decorator(fn):
            return fn

        return decorator

    def is_traceable_enabled() -> bool:
        return False


def setup_tracing() -> None:
    if _langsmith_enabled:
        try:
            import os

            os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGSMITH_TRACING"] = "true"
            logger.info("langsmith_tracing_enabled", project=settings.app_env)
        except Exception:
            logger.exception("langsmith_tracing_setup_failed")
    else:
        logger.info("langsmith_tracing_disabled")
