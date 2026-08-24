"""API v1 router configuration.

This module defines the API v1 router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, knowledge

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth.router)
# Include chat endpoints
api_router.include_router(chat.router)
# Include knowledge endpoints
api_router.include_router(knowledge.router)