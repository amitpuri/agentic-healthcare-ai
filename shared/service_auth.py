"""Shared bearer-token authentication for internal healthcare services.

Every service on the compose network authenticates callers against the same
INTERNAL_SERVICE_TOKEN. This is a service-to-service credential, not a user
identity: it gates PHI-bearing endpoints so they are not anonymously readable.
"""

import hmac
import os
from typing import Optional

TOKEN_ENV_VAR = "INTERNAL_SERVICE_TOKEN"


def get_expected_token() -> str:
    return os.getenv(TOKEN_ENV_VAR, "").strip()


def token_is_valid(authorization_header: Optional[str]) -> bool:
    """Constant-time check of an `Authorization: Bearer <token>` header.

    Fails closed: an unconfigured INTERNAL_SERVICE_TOKEN rejects every caller
    rather than silently disabling authentication.
    """
    expected = get_expected_token()
    if not expected or not authorization_header:
        return False

    scheme, _, presented = authorization_header.partition(" ")
    if scheme.lower() != "bearer":
        return False

    return hmac.compare_digest(presented.strip(), expected)


UNAUTHORIZED_DETAIL = "Invalid or missing service credentials"
UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}
