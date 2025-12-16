"""Rate limiting configuration for Gateway."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.config import cfg

# Initialize Limiter with Redis storage
# Falls back to in-memory if no Redis URL is configured (though env should enforce it)
redis_url = cfg.settings().redis.url
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url if redis_url else "memory://",
    enabled=True
)
