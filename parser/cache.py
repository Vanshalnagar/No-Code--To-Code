# parser/cache.py
from typing import Dict, Any, Optional

# A simple in-memory dictionary cache for demonstration.
# For production, this could be replaced with Redis, Memcached, etc.
_CACHE: Dict[str, Any] = {}

def get(key: str) -> Optional[Any]:
    """Get a value from the cache."""
    return _CACHE.get(key)

def set(key: str, value: Any) -> None:
    """Set a value in the cache."""
    _CACHE[key] = value
