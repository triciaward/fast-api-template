# Services package for optional features like Redis and WebSockets

# Try to import optional services
try:
    from .email import email_service
except ImportError:
    email_service = None  # type: ignore

try:
    from .oauth import oauth_service
except ImportError:
    oauth_service = None  # type: ignore

try:
    from .redis import redis_client
except ImportError:
    redis_client = None

# Note: websocket_manager doesn't exist in websocket.py, so we'll skip it for now

__all__ = [
    "email_service",
    "oauth_service",
    "redis_client",
]
