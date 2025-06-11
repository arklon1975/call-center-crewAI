"""
Authentication utilities for the call center system
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from config import config
from .models import User, UserSession

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except JWTError:
        return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = User.get_by_username(username)
    if not user:
        # Try to find by email
        user = User.get_by_email(username)
    
    if not user:
        return None
    
    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        # Increment failed attempts
        user.increment_failed_attempts()
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            lock_until = datetime.now() + timedelta(minutes=30)
            user.lock_account(lock_until)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed login attempts. Try again in 30 minutes."
            )
        
        return None
    
    # Reset failed attempts on successful login
    user.reset_failed_attempts()
    user.update_last_login()
    
    return user

def get_current_user(token: str) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = User.get_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(user: User) -> User:
    """Ensure user is active"""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked"
        )
    
    return user

def create_user_session(user: User, access_token: str, refresh_token: str, 
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> UserSession:
    """Create a new user session"""
    expires_at = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    session_data = {
        "user_id": user.id,
        "session_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "ip_address": ip_address,
        "user_agent": user_agent
    }
    
    return UserSession.create(session_data)

def invalidate_user_sessions(user_id: int):
    """Invalidate all sessions for a user"""
    sessions = UserSession.get_by_user_id(user_id)
    for session in sessions:
        session.invalidate()

def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, "refresh")
    if payload is None:
        return None
    
    username = payload.get("sub")
    if username is None:
        return None
    
    user = User.get_by_username(username)
    if user is None or not user.is_active:
        return None
    
    # Create new tokens
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    } 