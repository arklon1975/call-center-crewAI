"""
Database models for the call center system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from database.database import execute_query, get_db_session

@dataclass
class Call:
    """Call model"""
    id: Optional[int] = None
    call_id: str = ""
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    department: Optional[str] = None
    status: str = "active"
    priority: int = 1
    created_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    assigned_agent: Optional[str] = None
    
    @staticmethod
    def create(call_data: dict) -> "Call":
        """Create a new call record"""
        query = """
            INSERT INTO calls (call_id, customer_phone, customer_name, department, priority, assigned_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            call_data.get("call_id"),
            call_data.get("customer_phone"),
            call_data.get("customer_name"),
            call_data.get("department", "general"),
            call_data.get("priority", 1),
            call_data.get("assigned_agent")
        ))
        return Call.get_by_call_id(call_data["call_id"])
    
    @staticmethod
    def get_by_call_id(call_id: str) -> Optional["Call"]:
        """Get call by call_id"""
        query = "SELECT * FROM calls WHERE call_id = ?"
        results = execute_query(query, (call_id,))
        if results:
            row = results[0]
            return Call(
                id=row[0], call_id=row[1], customer_phone=row[2],
                customer_name=row[3], department=row[4], status=row[5],
                priority=row[6], created_at=row[7], ended_at=row[8],
                duration_seconds=row[9], assigned_agent=row[10]
            )
        return None
    
    @staticmethod
    def get_active_calls() -> List["Call"]:
        """Get all active calls"""
        query = "SELECT * FROM calls WHERE status = 'active' ORDER BY created_at DESC"
        results = execute_query(query)
        calls = []
        for row in results:
            calls.append(Call(
                id=row[0], call_id=row[1], customer_phone=row[2],
                customer_name=row[3], department=row[4], status=row[5],
                priority=row[6], created_at=row[7], ended_at=row[8],
                duration_seconds=row[9], assigned_agent=row[10]
            ))
        return calls
    
    def update_status(self, status: str):
        """Update call status"""
        query = "UPDATE calls SET status = ? WHERE call_id = ?"
        execute_query(query, (status, self.call_id))
        self.status = status

@dataclass
class Agent:
    """Agent model"""
    id: Optional[int] = None
    agent_id: str = ""
    name: str = ""
    role: str = ""
    status: str = "available"
    current_calls: int = 0
    total_calls: int = 0
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    
    @staticmethod
    def get_by_agent_id(agent_id: str) -> Optional["Agent"]:
        """Get agent by agent_id"""
        query = "SELECT * FROM agents WHERE agent_id = ?"
        results = execute_query(query, (agent_id,))
        if results:
            row = results[0]
            return Agent(
                id=row[0], agent_id=row[1], name=row[2], role=row[3],
                status=row[4], current_calls=row[5], total_calls=row[6],
                created_at=row[7], last_active=row[8]
            )
        return None
    
    @staticmethod
    def get_all_agents() -> List["Agent"]:
        """Get all agents"""
        query = "SELECT * FROM agents ORDER BY name"
        results = execute_query(query)
        agents = []
        for row in results:
            agents.append(Agent(
                id=row[0], agent_id=row[1], name=row[2], role=row[3],
                status=row[4], current_calls=row[5], total_calls=row[6],
                created_at=row[7], last_active=row[8]
            ))
        return agents
    
    def update_status(self, status: str):
        """Update agent status"""
        query = "UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP WHERE agent_id = ?"
        execute_query(query, (status, self.agent_id))
        self.status = status

@dataclass
class CallLog:
    """Call log model for tracking conversation history"""
    id: Optional[int] = None
    call_id: str = ""
    agent_id: str = ""
    message_type: str = ""  # 'customer', 'agent', 'system'
    content: str = ""
    timestamp: Optional[datetime] = None
    
    @staticmethod
    def create(log_data: dict) -> "CallLog":
        """Create a new call log entry"""
        query = """
            INSERT INTO call_logs (call_id, agent_id, message_type, content)
            VALUES (?, ?, ?, ?)
        """
        execute_query(query, (
            log_data["call_id"],
            log_data["agent_id"],
            log_data["message_type"],
            log_data["content"]
        ))
        return CallLog(**log_data)
    
    @staticmethod
    def get_by_call_id(call_id: str) -> List["CallLog"]:
        """Get all logs for a specific call"""
        query = "SELECT * FROM call_logs WHERE call_id = ? ORDER BY timestamp"
        results = execute_query(query, (call_id,))
        logs = []
        for row in results:
            logs.append(CallLog(
                id=row[0], call_id=row[1], agent_id=row[2],
                message_type=row[3], content=row[4], timestamp=row[5]
            ))
        return logs

@dataclass
class QualityMetric:
    """Quality metrics model"""
    id: Optional[int] = None
    call_id: str = ""
    agent_id: str = ""
    quality_score: Optional[float] = None
    resolution_status: Optional[str] = None
    customer_satisfaction: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @staticmethod
    def create(metric_data: dict) -> "QualityMetric":
        """Create a new quality metric record"""
        query = """
            INSERT INTO quality_metrics (call_id, agent_id, quality_score, resolution_status, customer_satisfaction, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            metric_data["call_id"],
            metric_data["agent_id"],
            metric_data.get("quality_score"),
            metric_data.get("resolution_status"),
            metric_data.get("customer_satisfaction"),
            metric_data.get("notes")
        ))
        return QualityMetric(**metric_data)
    
    @staticmethod
    def get_by_call_id(call_id: str) -> Optional["QualityMetric"]:
        """Get quality metrics for a specific call"""
        query = "SELECT * FROM quality_metrics WHERE call_id = ?"
        results = execute_query(query, (call_id,))
        if results:
            row = results[0]
            return QualityMetric(
                id=row[0], call_id=row[1], agent_id=row[2],
                quality_score=row[3], resolution_status=row[4],
                customer_satisfaction=row[5], notes=row[6], created_at=row[7]
            )
        return None
