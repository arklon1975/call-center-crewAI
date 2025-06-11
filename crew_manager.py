"""
CrewAI Manager - Orchestrates multi-agent interactions for call center operations
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from crewai import Crew, Task

from agents.customer_service_agent import CustomerServiceAgent
from agents.call_routing_agent import CallRoutingAgent
from agents.supervisor_agent import SupervisorAgent
from database.models import Call, CallLog
from config import config

class CallCenterCrew:
    """Main crew manager for call center operations"""
    
    def __init__(self):
        # Initialize agents
        self.customer_service_agent = CustomerServiceAgent()
        self.call_routing_agent = CallRoutingAgent()
        self.supervisor_agent = SupervisorAgent()
        
        # Active calls tracking
        self.active_calls: Dict[str, Dict] = {}
    
    def initiate_call(self, customer_phone: str, customer_name: str = None, initial_message: str = "") -> Dict[str, Any]:
        """Initiate a new customer call"""
        try:
            # Generate unique call ID
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            
            # Create call record
            call_data = {
                "call_id": call_id,
                "customer_phone": customer_phone,
                "customer_name": customer_name,
                "status": "active"
            }
            
            # First, route the call to determine department
            if initial_message:
                routing_result = self.call_routing_agent.route_call(
                    call_id=call_id,
                    customer_message=initial_message,
                    customer_info={"phone": customer_phone, "name": customer_name}
                )
                
                if routing_result.get("success"):
                    call_data["department"] = routing_result["routing_decision"].get("department", "general")
                    call_data["priority"] = routing_result["routing_decision"].get("priority", 2)
            
            # Create the call in database
            call = Call.create(call_data)
            
            # Track active call
            self.active_calls[call_id] = {
                "call": call,
                "start_time": datetime.now(),
                "messages": [],
                "current_agent": "routing_agent" if not initial_message else "cs_agent",
                "escalated": False
            }
            
            # Log call initiation
            CallLog.create({
                "call_id": call_id,
                "agent_id": "system",
                "message_type": "system",
                "content": f"Call initiated - Customer: {customer_name or customer_phone}"
            })
            
            response = {
                "success": True,
                "call_id": call_id,
                "message": "Call initiated successfully",
                "routing_info": routing_result if initial_message else None
            }
            
            # If there's an initial message, handle it immediately
            if initial_message:
                customer_response = self.handle_customer_message(call_id, initial_message)
                response["initial_response"] = customer_response
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initiate call: {str(e)}"
            }
    
    def handle_customer_message(self, call_id: str, message: str) -> Dict[str, Any]:
        """Process customer message through appropriate agent"""
        try:
            if call_id not in self.active_calls:
                return {
                    "success": False,
                    "error": "Call not found or no longer active"
                }
            
            call_info = self.active_calls[call_id]
            current_agent = call_info["current_agent"]
            
            # Add message to call history
            call_info["messages"].append({
                "type": "customer",
                "content": message,
                "timestamp": datetime.now()
            })
            
            # Route to appropriate agent based on current state
            if current_agent == "cs_agent" or call_info.get("escalated") == False:
                # Handle through customer service agent
                response = self.customer_service_agent.handle_customer_inquiry(
                    call_id=call_id,
                    customer_message=message,
                    context={"call_history": call_info["messages"][-5:]}  # Last 5 messages
                )
                
                # Check if escalation is needed
                if response.get("escalation_required"):
                    escalation_response = self._handle_escalation(call_id, response.get("action_needed", "customer_request"))
                    response["escalation_info"] = escalation_response
                    call_info["escalated"] = True
                    call_info["current_agent"] = "supervisor_agent"
                
            elif current_agent == "supervisor_agent":
                # Handle through supervisor
                response = self.supervisor_agent.handle_escalation(
                    call_id=call_id,
                    escalation_reason="continued_interaction",
                    context={"customer_message": message, "call_history": call_info["messages"][-5:]}
                )
            
            else:
                # Default to customer service
                response = self.customer_service_agent.handle_customer_inquiry(call_id, message)
            
            # Add agent response to call history
            call_info["messages"].append({
                "type": "agent",
                "content": response.get("response", ""),
                "timestamp": datetime.now(),
                "agent": response.get("agent_id", current_agent)
            })
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process message: {str(e)}"
            }
    
    def _handle_escalation(self, call_id: str, escalation_reason: str) -> Dict[str, Any]:
        """Handle call escalation to supervisor"""
        try:
            escalation_response = self.supervisor_agent.handle_escalation(
                call_id=call_id,
                escalation_reason=escalation_reason,
                context={"call_info": self.active_calls.get(call_id, {})}
            )
            
            # Update call priority if needed
            if escalation_response.get("success"):
                call = Call.get_by_call_id(call_id)
                if call and call.priority < 3:
                    call.priority = 3  # Escalated calls get higher priority
            
            return escalation_response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Escalation failed: {str(e)}"
            }
    
    def end_call(self, call_id: str, resolution_status: str = "completed") -> Dict[str, Any]:
        """End an active call"""
        try:
            if call_id not in self.active_calls:
                return {
                    "success": False,
                    "error": "Call not found or already ended"
                }
            
            call_info = self.active_calls[call_id]
            end_time = datetime.now()
            duration = int((end_time - call_info["start_time"]).total_seconds())
            
            # Update call record
            call = Call.get_by_call_id(call_id)
            if call:
                call.update_status("completed")
                call.duration_seconds = duration
                call.ended_at = end_time
            
            # Log call completion
            CallLog.create({
                "call_id": call_id,
                "agent_id": "system",
                "message_type": "system",
                "content": f"Call ended - Duration: {duration}s, Status: {resolution_status}"
            })
            
            # Trigger quality monitoring
            quality_analysis = self.supervisor_agent.monitor_call_quality(call_id)
            
            # Remove from active calls
            del self.active_calls[call_id]
            
            return {
                "success": True,
                "call_id": call_id,
                "duration_seconds": duration,
                "resolution_status": resolution_status,
                "quality_analysis": quality_analysis.get("quality_analysis") if quality_analysis.get("success") else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to end call: {str(e)}"
            }
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current status of a call"""
        try:
            if call_id in self.active_calls:
                call_info = self.active_calls[call_id]
                return {
                    "success": True,
                    "call_id": call_id,
                    "status": "active",
                    "current_agent": call_info["current_agent"],
                    "escalated": call_info.get("escalated", False),
                    "message_count": len(call_info["messages"]),
                    "duration_seconds": int((datetime.now() - call_info["start_time"]).total_seconds())
                }
            else:
                # Check if it's a completed call
                call = Call.get_by_call_id(call_id)
                if call:
                    return {
                        "success": True,
                        "call_id": call_id,
                        "status": call.status,
                        "department": call.department,
                        "priority": call.priority,
                        "duration_seconds": call.duration_seconds
                    }
                else:
                    return {
                        "success": False,
                        "error": "Call not found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get call status: {str(e)}"
            }
    
    def get_active_calls_summary(self) -> Dict[str, Any]:
        """Get summary of all active calls"""
        try:
            summary = {
                "total_active_calls": len(self.active_calls),
                "calls_by_agent": {},
                "calls_by_department": {},
                "escalated_calls": 0,
                "average_duration": 0
            }
            
            total_duration = 0
            for call_id, call_info in self.active_calls.items():
                # Count by agent
                agent = call_info["current_agent"]
                summary["calls_by_agent"][agent] = summary["calls_by_agent"].get(agent, 0) + 1
                
                # Count by department
                call = call_info.get("call")
                if call and call.department:
                    dept = call.department
                    summary["calls_by_department"][dept] = summary["calls_by_department"].get(dept, 0) + 1
                
                # Count escalated calls
                if call_info.get("escalated"):
                    summary["escalated_calls"] += 1
                
                # Calculate duration
                duration = int((datetime.now() - call_info["start_time"]).total_seconds())
                total_duration += duration
            
            # Calculate average duration
            if self.active_calls:
                summary["average_duration"] = total_duration // len(self.active_calls)
            
            return {
                "success": True,
                "summary": summary,
                "active_calls": list(self.active_calls.keys())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get calls summary: {str(e)}"
            }
    
    def get_agent_performance(self, time_period: str = "today") -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        try:
            return self.supervisor_agent.generate_performance_report(time_period=time_period)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get performance metrics: {str(e)}"
            }

# Global crew manager instance
call_center_crew = CallCenterCrew()
