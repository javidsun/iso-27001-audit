from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from iso_27001_audit.security.jwks import JWKSCache


class JWTValidator:
    def __init__(
        self,
        issuer: str,
        jwks_url: str,
        verify_aud: bool,
        expected_audience: str,
        ttl_seconds: int = 300,
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.verify_aud = verify_aud
        self.expected_audience = expected_audience
        self.jwks_cache = JWKSCache(jwks_url=jwks_url, ttl_seconds=ttl_seconds)

    @staticmethod
    def _extract_bearer_token(request: Request) -> str:
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        if not auth.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Invalid Authorization scheme (Bearer)")

        token = auth[7:].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Missing Bearer token")

        return token

    async def verify(self, request: Request) -> Dict[str, Any]:
        token = self._extract_bearer_token(request)

        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not isinstance(kid, str) or not kid:
                raise HTTPException(status_code=401, detail="Invalid token header (kid missing)")

            jwks = await self.jwks_cache.get()
            keys = jwks.get("keys")
            if not isinstance(keys, list):
                raise HTTPException(status_code=401, detail="Invalid JWKS format")

            key: Optional[Dict[str, Any]] = next(
                (k for k in keys if isinstance(k, dict) and k.get("kid") == kid),
                None,
            )
            if key is None:
                raise HTTPException(status_code=401, detail="Signing key not found (kid mismatch)")

            options = {"verify_aud": self.verify_aud}
            payload = jwt.decode(
                token=token,
                key=key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.expected_audience if self.verify_aud else None,
                options=options,
            )

            request.state.user = payload
            return payload

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except JWTError:
            raise HTTPException(status_code=401, detail="Token validation failed")