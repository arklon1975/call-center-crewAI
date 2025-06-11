"""
Authentication module for the call center system
"""

from .auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_active_user
)

from .models import User, UserRole, UserSession
from .dependencies import require_auth, require_role

__all__ = [
    "verify_password",
    "get_password_hash", 
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    "User",
    "UserRole", 
    "UserSession",
    "require_auth",
    "require_role"
] 