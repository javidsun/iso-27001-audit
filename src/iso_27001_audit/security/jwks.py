import time
import httpx
from typing import  Optional,Dict,Any



class JWKSCache:
    def __init__(self, jwks_url: str, ttl_seconds: int = 300) -> None:
        self.jwks_url = jwks_url
        self.ttl_seconds = ttl_seconds
        self._cached_at: float = 0.0
        self._jwks: Optional[Dict[str, Any]] = None

    async def get(self) -> Dict[str, Any]:
        now = time.time()
        if self._jwks is not None and (now - self._cached_at) < self.ttl_seconds:
            return self._jwks

        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(self.jwks_url)
            r.raise_for_status()
            self._jwks = r.json()
            self._cached_at = now
            return self._jwks