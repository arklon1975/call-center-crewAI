"""
Customer Service Agent - Handles customer inquiries and provides support
"""

import json
import os
from crewai import Agent, Task, Tool
from crewai_tools import BaseTool
from openai import OpenAI
from typing import Dict, Any, Optional

from config import config
from knowledge_base import knowledge_base
from database.models import CallLog

class CustomerServiceAgent:
    """Customer Service Agent for handling customer inquiries"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.agent_config = config.AGENT_CONFIGS["customer_service"]
        self.agent = self._create_agent()
        self.tools = self._create_tools()
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[]  # Tools will be added after creation
        )
    
    def _create_tools(self) -> list:
        """Create tools for the agent"""
        
        class KnowledgeBaseTool(BaseTool):
            name: str = "knowledge_base_search"
            description: str = "Search the knowledge base for relevant information and standard responses"
            
            def _run(self, query: str) -> str:
                # Search for relevant FAQ responses
                for key, response in knowledge_base.faq.items():
                    if any(word in query.lower() for word in key.split('_')):
                        return f"Standard response: {response}"
                
                return "No specific knowledge base entry found for this query."
        
        class EscalationCheckTool(BaseTool):
            name: str = "check_escalation"
            description: str = "Check if a situation requires escalation to supervisor"
            
            def _run(self, situation: str, call_duration: str = "0") -> str:
                duration = int(call_duration) if call_duration.isdigit() else 0
                escalation_info = knowledge_base.should_escalate(situation, duration)
                return json.dumps(escalation_info)
        
        class CallLogTool(BaseTool):
            name: str = "log_interaction"
            description: str = "Log customer interaction for record keeping"
            
            def _run(self, call_id: str, interaction: str) -> str:
                try:
                    CallLog.create({
                        "call_id": call_id,
                        "agent_id": "cs_agent",
                        "message_type": "agent",
                        "content": interaction
                    })
                    return "Interaction logged successfully"
                except Exception as e:
                    return f"Failed to log interaction: {str(e)}"
        
        return [KnowledgeBaseTool(), EscalationCheckTool(), CallLogTool()]
    
    def handle_customer_inquiry(self, call_id: str, customer_message: str, context: Dict = None) -> Dict[str, Any]:
        """Handle a customer inquiry and generate appropriate response"""
        
        # Log customer message
        CallLog.create({
            "call_id": call_id,
            "agent_id": "cs_agent",
            "message_type": "customer",
            "content": customer_message
        })
        
        try:
            # Use OpenAI to generate intelligent response
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a professional customer service representative. 
                        Your role: {self.agent_config['role']}
                        Your goal: {self.agent_config['goal']}
                        Background: {self.agent_config['backstory']}
                        
                        Guidelines:
                        - Be helpful, professional, and empathetic
                        - Provide clear and concise responses
                        - Ask clarifying questions when needed
                        - Offer solutions and next steps
                        - Use knowledge base information when available
                        
                        Respond in JSON format with these fields:
                        - response: Your response to the customer
                        - action_needed: Any action that needs to be taken
                        - escalation_required: true/false if escalation is needed
                        - sentiment_detected: positive/neutral/negative
                        - next_steps: Suggested next steps
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Customer message: {customer_message}\nCall context: {context or 'New call'}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=self.agent_config["max_tokens"],
                temperature=self.agent_config["temperature"]
            )
            
            response_data = json.loads(response.choices[0].message.content)
            
            # Log agent response
            CallLog.create({
                "call_id": call_id,
                "agent_id": "cs_agent",
                "message_type": "agent",
                "content": response_data.get("response", "")
            })
            
            return {
                "agent_id": "cs_agent",
                "response": response_data.get("response", "I apologize, but I'm having trouble processing your request. Let me connect you with a supervisor."),
                "action_needed": response_data.get("action_needed"),
                "escalation_required": response_data.get("escalation_required", False),
                "sentiment_detected": response_data.get("sentiment_detected", "neutral"),
                "next_steps": response_data.get("next_steps"),
                "success": True
            }
            
        except Exception as e:
            error_response = "I apologize for the technical difficulty. Let me connect you with a supervisor who can better assist you."
            
            # Log error
            CallLog.create({
                "call_id": call_id,
                "agent_id": "cs_agent",
                "message_type": "system",
                "content": f"Error occurred: {str(e)}"
            })
            
            return {
                "agent_id": "cs_agent",
                "response": error_response,
                "action_needed": "escalate_to_supervisor",
                "escalation_required": True,
                "error": str(e),
                "success": False
            }
    
    def get_suggested_responses(self, inquiry_type: str) -> list:
        """Get suggested responses for common inquiry types"""
        suggestions = []
        
        # Check knowledge base for relevant responses
        kb_response = knowledge_base.get_response(inquiry_type)
        if kb_response:
            suggestions.append(kb_response)
        
        # Get procedure steps if applicable
        if inquiry_type in ["issue_resolution", "call_opening", "call_closing"]:
            procedure = knowledge_base.get_procedure(inquiry_type)
            if procedure:
                suggestions.extend(procedure)
        
        return suggestions
    
    def analyze_customer_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze customer sentiment from their message"""
        try:
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment and emotion in the customer message. Respond with JSON containing: sentiment (positive/negative/neutral), emotion (frustrated/happy/confused/angry/neutral), confidence (0-1), and urgency_level (low/medium/high)."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "sentiment": "neutral",
                "emotion": "neutral", 
                "confidence": 0.5,
                "urgency_level": "medium",
                "error": str(e)
            }
