"""
FastAPI routes for the call center system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from crew_manager import call_center_crew
from database.models import Call, Agent, CallLog
from agents.call_routing_agent import CallRoutingAgent
from auth.dependencies import require_auth, require_supervisor, require_admin
from auth.models import User

router = APIRouter()

# Include email routes
from api.email_routes import router as email_router
router.include_router(email_router)

# Pydantic models for request/response
class InitiateCallRequest(BaseModel):
    customer_phone: str
    customer_name: Optional[str] = None
    initial_message: Optional[str] = ""

class CustomerMessageRequest(BaseModel):
    call_id: str
    message: str

class EndCallRequest(BaseModel):
    call_id: str
    resolution_status: Optional[str] = "completed"

# Call Management Endpoints
@router.post("/calls/initiate")
async def initiate_call(
    request: InitiateCallRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Initiate a new customer call (requires authentication)"""
    try:
        result = call_center_crew.initiate_call(
            customer_phone=request.customer_phone,
            customer_name=request.customer_name,
            initial_message=request.initial_message
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to initiate call"))
        
        # Log the action
        result["initiated_by"] = current_user.username
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/calls/message")
async def send_customer_message(
    request: CustomerMessageRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Send a customer message and get agent response (requires authentication)"""
    try:
        result = call_center_crew.handle_customer_message(
            call_id=request.call_id,
            message=request.message
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process message"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/calls/end")
async def end_call(
    request: EndCallRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """End an active call (requires authentication)"""
    try:
        result = call_center_crew.end_call(
            call_id=request.call_id,
            resolution_status=request.resolution_status
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to end call"))
        
        # Log the action
        result["ended_by"] = current_user.username
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/calls/{call_id}/status")
async def get_call_status(
    call_id: str,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get status of a specific call (requires authentication)"""
    try:
        result = call_center_crew.get_call_status(call_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Call not found"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/calls/{call_id}/history")
async def get_call_history(
    call_id: str,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get conversation history for a call (requires authentication)"""
    try:
        call_logs = CallLog.get_by_call_id(call_id)
        
        history = []
        for log in call_logs:
            history.append({
                "id": log.id,
                "agent_id": log.agent_id,
                "message_type": log.message_type,
                "content": log.content,
                "timestamp": log.timestamp
            })
        
        return {
            "success": True,
            "call_id": call_id,
            "history": history,
            "message_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Dashboard and Monitoring Endpoints
@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get dashboard summary with key metrics (requires authentication)"""
    try:
        # Get active calls summary
        active_calls = call_center_crew.get_active_calls_summary()
        
        # Get agent status
        agents = Agent.get_all_agents()
        agent_status = {}
        for agent in agents:
            agent_status[agent.agent_id] = {
                "name": agent.name,
                "role": agent.role,
                "status": agent.status,
                "current_calls": agent.current_calls,
                "total_calls": agent.total_calls
            }
        
        # Get queue status
        routing_agent = CallRoutingAgent()
        queue_status = routing_agent.get_queue_status()
        
        return {
            "success": True,
            "timestamp": call_center_crew.active_calls,
            "active_calls": active_calls.get("summary", {}) if active_calls.get("success") else {},
            "agent_status": agent_status,
            "queue_status": queue_status.get("queue_status", {}),
            "system_status": "operational",
            "user_role": current_user.role.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/dashboard/calls/active")
async def get_active_calls(
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get list of all active calls (requires authentication)"""
    try:
        result = call_center_crew.get_active_calls_summary()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get active calls"))
        
        # Get detailed info for each active call
        active_calls_detail = []
        for call_id in result.get("active_calls", []):
            call_status = call_center_crew.get_call_status(call_id)
            if call_status.get("success"):
                # Get call record for additional details
                call_record = Call.get_by_call_id(call_id)
                if call_record:
                    active_calls_detail.append({
                        "call_id": call_id,
                        "customer_phone": call_record.customer_phone,
                        "customer_name": call_record.customer_name,
                        "department": call_record.department,
                        "priority": call_record.priority,
                        "current_agent": call_status.get("current_agent"),
                        "escalated": call_status.get("escalated", False),
                        "duration_seconds": call_status.get("duration_seconds", 0)
                    })
        
        return {
            "success": True,
            "active_calls": active_calls_detail,
            "summary": result.get("summary", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/dashboard/agents")
async def get_agents_status(
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get status of all agents (requires authentication)"""
    try:
        agents = Agent.get_all_agents()
        
        agents_list = []
        for agent in agents:
            agents_list.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "status": agent.status,
                "current_calls": agent.current_calls,
                "total_calls": agent.total_calls,
                "last_active": str(agent.last_active) if agent.last_active else None
            })
        
        return {
            "success": True,
            "agents": agents_list,
            "available_agents": len([a for a in agents if a.status == "available"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/dashboard/performance")
async def get_performance_metrics(
    time_period: str = "today",
    current_user: User = Depends(require_supervisor)
) -> Dict[str, Any]:
    """Get performance metrics for specified time period (requires supervisor role)"""
    try:
        result = call_center_crew.get_agent_performance(time_period=time_period)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get performance metrics"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    time_period: str = "today",
    current_user: User = Depends(require_supervisor)
) -> Dict[str, Any]:
    """Get performance metrics for a specific agent (requires supervisor role)"""
    try:
        # This would need to be implemented in crew_manager
        return {
            "success": True,
            "agent_id": agent_id,
            "time_period": time_period,
            "message": "Agent performance metrics not yet implemented"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/agents/{agent_id}/coaching")
async def provide_coaching(
    agent_id: str,
    call_id: str,
    current_user: User = Depends(require_supervisor)
) -> Dict[str, Any]:
    """Provide coaching feedback for an agent (requires supervisor role)"""
    try:
        # This would need to be implemented in crew_manager
        return {
            "success": True,
            "agent_id": agent_id,
            "call_id": call_id,
            "coached_by": current_user.username,
            "message": "Coaching functionality not yet implemented"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/routing/queue-status")
async def get_queue_status(
    department: Optional[str] = None,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get queue status for departments (requires authentication)"""
    try:
        routing_agent = CallRoutingAgent()
        result = routing_agent.get_queue_status()
        
        if department:
            # Filter by specific department
            queue_status = result.get("queue_status", {})
            filtered_status = {dept: status for dept, status in queue_status.items() if dept == department}
            result["queue_status"] = filtered_status
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/routing/callback-recommendation")
async def get_callback_recommendation(
    call_id: str,
    department: str,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """Get callback recommendation for a call (requires authentication)"""
    try:
        # This would need to be implemented in call_routing_agent
        return {
            "success": True,
            "call_id": call_id,
            "department": department,
            "recommendation": "Callback functionality not yet implemented"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# System Health and Configuration
@router.get("/system/health")
async def system_health() -> Dict[str, Any]:
    """Get system health status (public endpoint)"""
    try:
        # Check database connection
        agents = Agent.get_all_agents()
        db_status = "healthy" if agents is not None else "error"
        
        # Check active calls
        active_calls_summary = call_center_crew.get_active_calls_summary()
        crew_status = "healthy" if active_calls_summary.get("success") else "error"
        
        return {
            "success": True,
            "status": "healthy" if db_status == "healthy" and crew_status == "healthy" else "degraded",
            "components": {
                "database": db_status,
                "crew_manager": crew_status,
                "agents": {
                    "customer_service": "healthy",
                    "call_routing": "healthy",
                    "supervisor": "healthy"
                }
            },
            "uptime": "System operational",
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

# Admin-only endpoints
@router.get("/admin/system-info")
async def get_system_info(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get detailed system information (admin only)"""
    try:
        import psutil
        import platform
        
        return {
            "success": True,
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "database": {
                "type": "SQLite",
                "path": "call_center.db"
            },
            "environment": {
                "debug": current_user.role.value == "admin"  # Only show to admin
            }
        }
        
    except ImportError:
        return {
            "success": True,
            "message": "System monitoring not available (psutil not installed)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
