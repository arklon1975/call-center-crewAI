"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_utils import get_current_user, get_current_active_user
from .models import User, UserRole

# Security scheme
security = HTTPBearer()

async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header"""
    return credentials.credentials

async def get_current_user_dependency(token: str = Depends(get_token_from_header)) -> User:
    """Get current user from token"""
    return get_current_user(token)

async def get_current_active_user_dependency(
    current_user: User = Depends(get_current_user_dependency)
) -> User:
    """Get current active user"""
    return get_current_active_user(current_user)

def require_auth(current_user: User = Depends(get_current_active_user_dependency)) -> User:
    """Require authentication"""
    return current_user

def require_role(required_role: UserRole):
    """Require specific role or higher"""
    def role_checker(current_user: User = Depends(get_current_active_user_dependency)) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    """Require admin role"""
    return current_user

def require_supervisor(current_user: User = Depends(require_role(UserRole.SUPERVISOR))) -> User:
    """Require supervisor role or higher"""
    return current_user

def require_agent(current_user: User = Depends(require_role(UserRole.AGENT))) -> User:
    """Require agent role or higher"""
    return current_user

async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials.credentials)
    except HTTPException:
        return None

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    """Get user agent string"""
    return request.headers.get("User-Agent", "unknown") 