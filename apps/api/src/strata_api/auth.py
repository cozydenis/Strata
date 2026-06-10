"""Supabase JWT verification — resolves the authenticated user for protected endpoints.

Supabase Auth signs access tokens with the project's JWT secret (HS256, the
"legacy" shared secret available in the dashboard). The frontend sends them as
Authorization: Bearer <token>; we verify locally without calling Supabase.
"""
from __future__ import annotations

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from strata_api.config import settings

_bearer = HTTPBearer(auto_error=False)
_credentials_dep = Security(_bearer)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = _credentials_dep,
) -> str:
    """Return the Supabase user id (JWT `sub`) or raise 401/503."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=503, detail="Auth is not configured on this server.")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from err

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token has no subject.")
    return user_id
