"""
Admin router for HTML-based administration.

This module provides HTML routes for admin interfaces using Jinja2 templates.
All endpoints require superuser privileges.
"""

from fastapi import APIRouter

from app.api.admin_views import (
    admin_api_keys_view,
    admin_create_api_key,
    admin_revoke_api_key,
    admin_rotate_api_key,
)

router = APIRouter()

# API Key management routes
router.add_api_route(
    "/api-keys",
    admin_api_keys_view,
    methods=["GET"],
    include_in_schema=False,  # Exclude from OpenAPI schema
    tags=["admin-html"],
    summary="Admin API Key Management Dashboard",
    description="HTML dashboard for managing API keys",
)

router.add_api_route(
    "/api-keys",
    admin_create_api_key,
    methods=["POST"],
    include_in_schema=False,  # Exclude from OpenAPI schema
    tags=["admin-html"],
    summary="Create API Key via Admin Interface",
    description="Create a new API key via the admin HTML interface",
)

router.add_api_route(
    "/api-keys/{key_id}/rotate",
    admin_rotate_api_key,
    methods=["POST"],
    include_in_schema=False,  # Exclude from OpenAPI schema
    tags=["admin-html"],
    summary="Rotate API Key via Admin Interface",
    description="Rotate an API key via the admin HTML interface",
)

router.add_api_route(
    "/api-keys/{key_id}/revoke",
    admin_revoke_api_key,
    methods=["POST"],
    include_in_schema=False,  # Exclude from OpenAPI schema
    tags=["admin-html"],
    summary="Revoke API Key via Admin Interface",
    description="Revoke an API key via the admin HTML interface",
)
