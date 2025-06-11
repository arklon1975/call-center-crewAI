"""
Authentication models for the call center system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from database.database import execute_query

class UserRole(Enum):
    """User roles in the system"""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    AGENT = "agent"
    VIEWER = "viewer"

@dataclass
class User:
    """User model for authentication"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    full_name: str = ""
    hashed_password: str = ""
    role: UserRole = UserRole.AGENT
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    @staticmethod
    def create(user_data: dict) -> "User":
        """Create a new user"""
        query = """
            INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            user_data["username"],
            user_data["email"],
            user_data["full_name"],
            user_data["hashed_password"],
            user_data.get("role", UserRole.AGENT.value),
            user_data.get("is_active", True),
            user_data.get("is_verified", False)
        ))
        return User.get_by_username(user_data["username"])
    
    @staticmethod
    def get_by_username(username: str) -> Optional["User"]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = ?"
        results = execute_query(query, (username,))
        if results:
            row = results[0]
            return User(
                id=row[0], username=row[1], email=row[2], full_name=row[3],
                hashed_password=row[4], role=UserRole(row[5]), is_active=row[6],
                is_verified=row[7], created_at=row[8], last_login=row[9],
                failed_login_attempts=row[10], locked_until=row[11]
            )
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional["User"]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = ?"
        results = execute_query(query, (email,))
        if results:
            row = results[0]
            return User(
                id=row[0], username=row[1], email=row[2], full_name=row[3],
                hashed_password=row[4], role=UserRole(row[5]), is_active=row[6],
                is_verified=row[7], created_at=row[8], last_login=row[9],
                failed_login_attempts=row[10], locked_until=row[11]
            )
        return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional["User"]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        results = execute_query(query, (user_id,))
        if results:
            row = results[0]
            return User(
                id=row[0], username=row[1], email=row[2], full_name=row[3],
                hashed_password=row[4], role=UserRole(row[5]), is_active=row[6],
                is_verified=row[7], created_at=row[8], last_login=row[9],
                failed_login_attempts=row[10], locked_until=row[11]
            )
        return None
    
    @staticmethod
    def get_all_users() -> List["User"]:
        """Get all users"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        results = execute_query(query)
        users = []
        for row in results:
            users.append(User(
                id=row[0], username=row[1], email=row[2], full_name=row[3],
                hashed_password=row[4], role=UserRole(row[5]), is_active=row[6],
                is_verified=row[7], created_at=row[8], last_login=row[9],
                failed_login_attempts=row[10], locked_until=row[11]
            ))
        return users
    
    def update_last_login(self):
        """Update last login timestamp"""
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        execute_query(query, (self.id,))
        self.last_login = datetime.now()
    
    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        query = "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = ?"
        execute_query(query, (self.id,))
        self.failed_login_attempts += 1
    
    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        query = "UPDATE users SET failed_login_attempts = 0 WHERE id = ?"
        execute_query(query, (self.id,))
        self.failed_login_attempts = 0
    
    def lock_account(self, until: datetime):
        """Lock user account until specified time"""
        query = "UPDATE users SET locked_until = ? WHERE id = ?"
        execute_query(query, (until, self.id))
        self.locked_until = until
    
    def unlock_account(self):
        """Unlock user account"""
        query = "UPDATE users SET locked_until = NULL, failed_login_attempts = 0 WHERE id = ?"
        execute_query(query, (self.id,))
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def update_password(self, new_hashed_password: str):
        """Update user password"""
        query = "UPDATE users SET hashed_password = ? WHERE id = ?"
        execute_query(query, (new_hashed_password, self.id))
        self.hashed_password = new_hashed_password
    
    def deactivate(self):
        """Deactivate user account"""
        query = "UPDATE users SET is_active = FALSE WHERE id = ?"
        execute_query(query, (self.id,))
        self.is_active = False
    
    def activate(self):
        """Activate user account"""
        query = "UPDATE users SET is_active = TRUE WHERE id = ?"
        execute_query(query, (self.id,))
        self.is_active = True
    
    def verify_email(self):
        """Mark email as verified"""
        query = "UPDATE users SET is_verified = TRUE WHERE id = ?"
        execute_query(query, (self.id,))
        self.is_verified = True
    
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.AGENT: 2,
            UserRole.SUPERVISOR: 3,
            UserRole.ADMIN: 4
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

@dataclass
class UserSession:
    """User session model for tracking active sessions"""
    id: Optional[int] = None
    user_id: int = 0
    session_token: str = ""
    refresh_token: str = ""
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    @staticmethod
    def create(session_data: dict) -> "UserSession":
        """Create a new user session"""
        query = """
            INSERT INTO user_sessions (user_id, session_token, refresh_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            session_data["user_id"],
            session_data["session_token"],
            session_data["refresh_token"],
            session_data["expires_at"],
            session_data.get("ip_address"),
            session_data.get("user_agent")
        ))
        return UserSession.get_by_token(session_data["session_token"])
    
    @staticmethod
    def get_by_token(token: str) -> Optional["UserSession"]:
        """Get session by token"""
        query = "SELECT * FROM user_sessions WHERE session_token = ? AND is_active = TRUE"
        results = execute_query(query, (token,))
        if results:
            row = results[0]
            return UserSession(
                id=row[0], user_id=row[1], session_token=row[2], refresh_token=row[3],
                expires_at=row[4], created_at=row[5], last_activity=row[6],
                ip_address=row[7], user_agent=row[8], is_active=row[9]
            )
        return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List["UserSession"]:
        """Get all active sessions for a user"""
        query = "SELECT * FROM user_sessions WHERE user_id = ? AND is_active = TRUE ORDER BY created_at DESC"
        results = execute_query(query, (user_id,))
        sessions = []
        for row in results:
            sessions.append(UserSession(
                id=row[0], user_id=row[1], session_token=row[2], refresh_token=row[3],
                expires_at=row[4], created_at=row[5], last_activity=row[6],
                ip_address=row[7], user_agent=row[8], is_active=row[9]
            ))
        return sessions
    
    def update_activity(self):
        """Update last activity timestamp"""
        query = "UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?"
        execute_query(query, (self.id,))
        self.last_activity = datetime.now()
    
    def invalidate(self):
        """Invalidate the session"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE id = ?"
        execute_query(query, (self.id,))
        self.is_active = False
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at 