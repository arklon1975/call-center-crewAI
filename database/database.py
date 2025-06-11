"""
Database configuration and session management
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import os

DATABASE_PATH = "call_center.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    
    # Initialize default agents
    initialize_default_agents()

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
