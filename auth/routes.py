"""
Authentication routes for the call center system
"""

from datetime import timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from .auth_utils import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, validate_password_strength, refresh_access_token,
    create_user_session, invalidate_user_sessions
)
from .models import User, UserRole, UserSession
from .dependencies import (
    require_auth, require_admin, get_client_ip, get_user_agent,
    get_optional_current_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole = UserRole.AGENT

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: str = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    email: str

@router.post("/register", response_model=Dict[str, Any])
async def register(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_admin)
):
    """Register a new user (admin only)"""
    try:
        # Check if username already exists
        existing_user = User.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = User.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        password_validation = validate_password_strength(user_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet requirements", "errors": password_validation["errors"]}
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        new_user = User.create({
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "role": user_data.role.value,
            "is_active": True,
            "is_verified": True  # Admin-created users are auto-verified
        })
        
        return {
            "success": True,
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """User login"""
    try:
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)  # From config
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        # Create session
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        create_user_session(user, access_token, refresh_token, ip_address, user_agent)
        
        # Create response
        response_data = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes in seconds
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=str(user.created_at) if user.created_at else "",
                last_login=str(user.last_login) if user.last_login else None
            )
        )
        
        # Create response with cookie
        response = JSONResponse(content=response_data.dict())
        
        # Set access token as httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=1800,  # 30 minutes
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=7 * 24 * 3600,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: Request, token_request: RefreshTokenRequest = None):
    """Refresh access token"""
    try:
        # Get refresh token from request body or cookie
        refresh_token_value = None
        if token_request and token_request.refresh_token:
            refresh_token_value = token_request.refresh_token
        else:
            refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not provided"
            )
        
        tokens = refresh_access_token(refresh_token_value)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create response
        response_data = {
            "success": True,
            **tokens,
            "expires_in": 1800
        }
        
        # Create response with new cookie
        response = JSONResponse(content=response_data)
        
        # Set new access token as httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            max_age=1800,  # 30 minutes
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(require_auth)):
    """User logout"""
    try:
        # Invalidate all user sessions
        invalidate_user_sessions(current_user.id)
        
        # Create response
        response_data = {
            "success": True,
            "message": "Logged out successfully"
        }
        
        # Create response with cookie clearing
        response = JSONResponse(content=response_data)
        
        # Clear access token cookie
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=str(current_user.created_at) if current_user.created_at else "",
        last_login=str(current_user.last_login) if current_user.last_login else None
    )

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(require_auth)
):
    """Change user password"""
    try:
        # Verify current password
        from .auth_utils import verify_password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        password_validation = validate_password_strength(password_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "New password does not meet requirements", "errors": password_validation["errors"]}
            )
        
        # Update password
        new_hashed_password = get_password_hash(password_data.new_password)
        current_user.update_password(new_hashed_password)
        
        # Invalidate all sessions except current one
        invalidate_user_sessions(current_user.id)
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: User = Depends(require_admin)):
    """Get all users (admin only)"""
    try:
        users = User.get_all_users()
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=str(user.created_at) if user.created_at else "",
                last_login=str(user.last_login) if user.last_login else None
            )
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )

@router.put("/users/{user_id}/activate")
async def activate_user(user_id: int, current_user: User = Depends(require_admin)):
    """Activate user account (admin only)"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.activate()
        
        return {
            "success": True,
            "message": f"User {user.username} activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, current_user: User = Depends(require_admin)):
    """Deactivate user account (admin only)"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't allow deactivating yourself
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        user.deactivate()
        invalidate_user_sessions(user.id)
        
        return {
            "success": True,
            "message": f"User {user.username} deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )

@router.get("/sessions")
async def get_user_sessions(current_user: User = Depends(require_auth)):
    """Get current user's active sessions"""
    try:
        sessions = UserSession.get_by_user_id(current_user.id)
        return {
            "success": True,
            "sessions": [
                {
                    "id": session.id,
                    "created_at": str(session.created_at) if session.created_at else "",
                    "last_activity": str(session.last_activity) if session.last_activity else "",
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "is_active": session.is_active,
                    "expires_at": str(session.expires_at) if session.expires_at else ""
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        ) 