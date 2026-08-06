import structlog

from src.config import cfg, settings

log = structlog.get_logger()


def _normalize(value: str) -> str:
    return value.strip().lower()


def _resolved_app_env() -> str:
    env = settings.app_env or str(cfg.get("app", {}).get("env", "development"))
    return _normalize(env)


def _resolve_backend() -> str:
    requested = _normalize(settings.vector_backend)
    if requested in {"chroma", "qdrant"}:
        return requested
    if requested:
        log.warning("unknown_vector_backend", requested=requested)

    if _resolved_app_env() in {"prod", "production"}:
        return "qdrant"
    return "chroma"


def get_vector_store(collection: str = "knowledge_base"):
    backend = _resolve_backend()
    if backend == "qdrant":
        if _resolved_app_env() in {"prod", "production"} and not settings.qdrant_url:
            raise ValueError(
                "QDRANT_URL must be set when APP_ENV is production and backend is qdrant"
            )
        from src.vectordb.qdrant_store import get_qdrant_store

        log.info(
            "vector_store_selected",
            backend="qdrant",
            collection=collection,
            app_env=_resolved_app_env(),
        )
        return get_qdrant_store(collection)
    from src.vectordb.chroma_store import get_chroma_store

    log.info(
        "vector_store_selected",
        backend="chroma",
        collection=collection,
        app_env=_resolved_app_env(),
    )
    return get_chroma_store(collection)
