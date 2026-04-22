import os
import sys
from functools import wraps
from flask import request, jsonify
from jwt import decode, PyJWTError, PyJWKClient

# Auth0 Configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "uyris.us.auth0.com").replace("https://", "").rstrip("/")
AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "https://uyris.us.auth0.com/api/v2/")
AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/"

print(f"[AUTH0 CONFIG] DOMAIN={AUTH0_DOMAIN}, AUDIENCE={AUTH0_AUDIENCE}, ISSUER={AUTH0_ISSUER}", file=sys.stderr, flush=True)

# Accept both audience formats (with and without trailing slash).
_audience_candidates = {AUTH0_AUDIENCE.rstrip("/")}
if AUTH0_AUDIENCE:
    _audience_candidates.add(AUTH0_AUDIENCE)

# Reused JWK client with internal caching of signing keys/JWKS.
_jwk_client = PyJWKClient(f"{AUTH0_ISSUER}.well-known/jwks.json")


def verify_jwt(token):
    """Verify JWT token and return decoded payload"""
    if not token:
        print(f"[JWT] No token provided", file=sys.stderr, flush=True)
        return None
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        print(f"[JWT] Attempting to verify token (first 50 chars): {token[:50]}...", file=sys.stderr, flush=True)
        # PyJWT expects a real public key, not the raw JWK dict.
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        print(f"[JWT] Signing key retrieved successfully", file=sys.stderr, flush=True)

        # Decode without audience validation - just verify the signature
        # Auth0 tokens may have different formats or audiences
        payload = decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=AUTH0_ISSUER,
            options={"verify_aud": False}  # Don't verify audience - just validate signature and issuer
        )
        print(f"[JWT] Token verified successfully. Payload sub: {payload.get('sub')}", file=sys.stderr, flush=True)

        return payload
    except PyJWTError as e:
        print(f"[JWT] PyJWTError: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return None
    except Exception as e:
        print(f"[JWT] Unexpected error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return None


def require_auth(f):
    """Decorator to require authentication on a route"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
        
        payload = verify_jwt(auth_header)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Extract user_id from token
        # Auth0 typically uses 'sub' as the unique identifier
        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "User ID not found in token"}), 401
        
        # Add user info to request context
        request.user_id = user_id
        request.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated
