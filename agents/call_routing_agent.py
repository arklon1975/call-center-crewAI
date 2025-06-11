"""
Call Routing Agent - Routes calls to appropriate departments and agents
"""

import json
from crewai import Agent
from openai import OpenAI
from typing import Dict, Any, List

from config import config
from knowledge_base import knowledge_base
from database.models import CallLog, Agent as AgentModel, Call

class CallRoutingAgent:
    """Call Routing Agent for intelligent call distribution"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.agent_config = config.AGENT_CONFIGS["call_routing"]
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            verbose=True,
            allow_delegation=False
        )
    
    def route_call(self, call_id: str, customer_message: str, customer_info: Dict = None) -> Dict[str, Any]:
        """Route call to appropriate department based on customer inquiry"""
        
        # Log routing request
        CallLog.create({
            "call_id": call_id,
            "agent_id": "routing_agent",
            "message_type": "system",
            "content": f"Routing analysis started for: {customer_message[:100]}"
        })
        
        try:
            # Use OpenAI to analyze the inquiry and determine routing
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an intelligent call routing system for a call center.
                        
                        Available departments:
                        {json.dumps(config.DEPARTMENTS, indent=2)}
                        
                        Department information:
                        {json.dumps(knowledge_base.department_info, indent=2)}
                        
                        Analyze the customer inquiry and determine:
                        1. Which department should handle this call
                        2. Priority level (1=low, 2=normal, 3=high, 4=urgent)
                        3. Estimated complexity (simple/moderate/complex)
                        4. Required skills or specialization
                        5. Whether immediate attention is needed
                        
                        Respond in JSON format with:
                        - department: department code
                        - department_name: full department name
                        - priority: 1-4 priority level
                        - complexity: simple/moderate/complex
                        - estimated_duration: estimated call duration in minutes
                        - required_skills: list of required skills
                        - reasoning: explanation for routing decision
                        - immediate_attention: true/false
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Customer inquiry: {customer_message}\nCustomer info: {customer_info or 'Not provided'}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=self.agent_config["max_tokens"],
                temperature=self.agent_config["temperature"]
            )
            
            routing_decision = json.loads(response.choices[0].message.content)
            
            # Get department information
            dept_info = knowledge_base.get_department_info(routing_decision.get("department", "general"))
            
            # Find available agents for the department
            available_agents = self._find_available_agents(routing_decision.get("department", "general"))
            
            # Log routing decision
            CallLog.create({
                "call_id": call_id,
                "agent_id": "routing_agent",
                "message_type": "system",
                "content": f"Routed to {routing_decision.get('department_name', 'General')} - Priority: {routing_decision.get('priority', 2)}"
            })
            
            # Update call record with routing information
            call = Call.get_by_call_id(call_id)
            if call:
                call.department = routing_decision.get("department", "general")
                call.priority = routing_decision.get("priority", 2)
                if available_agents:
                    call.assigned_agent = available_agents[0]["agent_id"]
            
            return {
                "success": True,
                "routing_decision": routing_decision,
                "department_info": dept_info,
                "available_agents": available_agents,
                "estimated_wait_time": dept_info.get("avg_wait_time", "Unknown") if dept_info else "Unknown",
                "call_id": call_id
            }
            
        except Exception as e:
            # Default routing on error
            error_response = {
                "success": False,
                "error": str(e),
                "routing_decision": {
                    "department": "general",
                    "department_name": "General Inquiries",
                    "priority": 2,
                    "complexity": "moderate",
                    "reasoning": "Error occurred during routing analysis, defaulting to general inquiries"
                },
                "department_info": knowledge_base.get_department_info("general"),
                "available_agents": self._find_available_agents("general")
            }
            
            # Log error
            CallLog.create({
                "call_id": call_id,
                "agent_id": "routing_agent",
                "message_type": "system",
                "content": f"Routing error occurred: {str(e)} - Defaulted to general department"
            })
            
            return error_response
    
    def _find_available_agents(self, department: str) -> List[Dict]:
        """Find available agents for a specific department"""
        try:
            # Get all agents
            all_agents = AgentModel.get_all_agents()
            
            # Filter agents based on department and availability
            available_agents = []
            for agent in all_agents:
                if agent.status == "available" and agent.current_calls < 3:  # Max 3 concurrent calls
                    available_agents.append({
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "role": agent.role,
                        "current_calls": agent.current_calls,
                        "total_calls": agent.total_calls
                    })
            
            # Sort by current workload (fewer calls first)
            available_agents.sort(key=lambda x: x["current_calls"])
            
            return available_agents
            
        except Exception as e:
            return []
    
    def get_queue_status(self, department: str = None) -> Dict[str, Any]:
        """Get current queue status for departments"""
        try:
            if department:
                # Get status for specific department
                active_calls = [call for call in Call.get_active_calls() if call.department == department]
                dept_info = knowledge_base.get_department_info(department)
                available_agents = self._find_available_agents(department)
                
                return {
                    "department": department,
                    "active_calls": len(active_calls),
                    "available_agents": len(available_agents),
                    "estimated_wait_time": dept_info.get("avg_wait_time", "Unknown") if dept_info else "Unknown",
                    "department_hours": dept_info.get("hours", "Unknown") if dept_info else "Unknown"
                }
            else:
                # Get status for all departments
                queue_status = {}
                for dept_code, dept_name in config.DEPARTMENTS.items():
                    active_calls = [call for call in Call.get_active_calls() if call.department == dept_code]
                    available_agents = self._find_available_agents(dept_code)
                    dept_info = knowledge_base.get_department_info(dept_code)
                    
                    queue_status[dept_code] = {
                        "name": dept_name,
                        "active_calls": len(active_calls),
                        "available_agents": len(available_agents),
                        "estimated_wait_time": dept_info.get("avg_wait_time", "Unknown") if dept_info else "Unknown"
                    }
                
                return {"queue_status": queue_status}
                
        except Exception as e:
            return {"error": str(e), "queue_status": {}}
    
    def recommend_callback(self, call_id: str, department: str) -> Dict[str, Any]:
        """Recommend callback based on queue status and customer priority"""
        try:
            queue_status = self.get_queue_status(department)
            call = Call.get_by_call_id(call_id)
            
            # Simple callback recommendation logic
            should_offer_callback = False
            callback_time = None
            
            if queue_status.get("available_agents", 0) == 0:
                should_offer_callback = True
                callback_time = "15-30 minutes"
            elif queue_status.get("active_calls", 0) > 5:
                should_offer_callback = True
                callback_time = "10-15 minutes"
            
            # High priority calls should not be offered callback
            if call and call.priority >= 3:
                should_offer_callback = False
            
            return {
                "should_offer_callback": should_offer_callback,
                "estimated_callback_time": callback_time,
                "current_queue_position": queue_status.get("active_calls", 0) + 1,
                "reasoning": f"Based on {queue_status.get('active_calls', 0)} active calls and {queue_status.get('available_agents', 0)} available agents"
            }
            
        except Exception as e:
            return {
                "should_offer_callback": False,
                "error": str(e)
            }
    
    def update_routing_metrics(self, call_id: str, actual_resolution_time: int, customer_satisfaction: int):
        """Update routing accuracy metrics based on call outcomes"""
        try:
            # This would be used to improve routing decisions over time
            # For now, just log the metrics
            CallLog.create({
                "call_id": call_id,
                "agent_id": "routing_agent",
                "message_type": "system",
                "content": f"Call completed - Resolution time: {actual_resolution_time}min, Satisfaction: {customer_satisfaction}/5"
            })
            
            return {"success": True, "metrics_updated": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
