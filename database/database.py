"""
Database configuration and session management
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import os
from datetime import datetime

DATABASE_PATH = "call_center.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'agent',
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)
    
    # Create user_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            refresh_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create calls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE NOT NULL,
            customer_phone TEXT,
            customer_name TEXT,
            department TEXT,
            status TEXT DEFAULT 'active',
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds INTEGER,
            assigned_agent TEXT
        )
    """)
    
    # Create agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            current_calls INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create call_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES calls (call_id),
            FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
        )
    """)
    
    # Create quality_metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            quality_score REAL,
            resolution_status TEXT,
            customer_satisfaction INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES calls (call_id),
            FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions (session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls (call_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_status ON calls (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_call_id ON call_logs (call_id)")
    
    conn.commit()
    conn.close()
    
    # Initialize default data
    initialize_default_agents()
    initialize_default_admin()

def initialize_default_agents():
    """Initialize default agents in the database"""
    default_agents = [
        ("cs_agent", "Customer Service Agent", "customer_service"),
        ("routing_agent", "Call Routing Agent", "call_routing"),
        ("supervisor_agent", "Supervisor Agent", "supervisor")
    ]
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    for agent_id, name, role in default_agents:
        cursor.execute("""
            INSERT OR IGNORE INTO agents (agent_id, name, role)
            VALUES (?, ?, ?)
        """, (agent_id, name, role))
    
    conn.commit()
    conn.close()

def initialize_default_admin():
    """Initialize default admin user"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        conn.close()
        return
    
    # Create default admin user
    # Password: Admin123! (should be changed on first login)
    from auth.auth_utils import get_password_hash
    hashed_password = get_password_hash("Admin123!")
    
    cursor.execute("""
        INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "admin",
        "admin@callcenter.com",
        "System Administrator",
        hashed_password,
        "admin",
        True,
        True
    ))
    
    conn.commit()
    conn.close()
    
    print("Default admin user created:")
    print("Username: admin")
    print("Password: Admin123!")
    print("Please change the password after first login!")

@contextmanager
def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """Get database session with automatic cleanup"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query: str, params: tuple = ()):
    """Execute a single query and return results"""
    with get_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall()

def execute_many(query: str, params_list: list):
    """Execute multiple queries with different parameters"""
    with get_db_session() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()

def backup_database(backup_path: str = None):
    """Create a backup of the database"""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"call_center_backup_{timestamp}.db"
    
    source = sqlite3.connect(DATABASE_PATH)
    backup = sqlite3.connect(backup_path)
    source.backup(backup)
    backup.close()
    source.close()
    
    return backup_path

def restore_database(backup_path: str):
    """Restore database from backup"""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Create backup of current database
    current_backup = backup_database()
    
    try:
        # Replace current database with backup
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
        
        source = sqlite3.connect(backup_path)
        target = sqlite3.connect(DATABASE_PATH)
        source.backup(target)
        target.close()
        source.close()
        
        return True
    except Exception as e:
        # Restore original database if restore fails
        if os.path.exists(current_backup):
            source = sqlite3.connect(current_backup)
            target = sqlite3.connect(DATABASE_PATH)
            source.backup(target)
            target.close()
            source.close()
        raise e
