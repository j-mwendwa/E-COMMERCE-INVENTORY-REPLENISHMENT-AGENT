import hashlib
import hmac

import structlog
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings

log = structlog.get_logger()
_security = HTTPBearer(auto_error=False)


def _key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:12]


async def require_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> str:
    api_key = request.headers.get("X-API-Key")
    if not api_key and credentials:
        api_key = credentials.credentials
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    allowed = settings.allowed_api_keys_list
    for key in allowed:
        if hmac.compare_digest(api_key, key):
            log.info("api_key_authorized", key_hash=_key_hash(api_key))
            return api_key

    log.warning("api_key_denied", key_hash=_key_hash(api_key))
    raise HTTPException(status_code=403, detail="Invalid API key")
