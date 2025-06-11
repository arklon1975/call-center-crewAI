"""
Supervisor Agent - Monitors call quality and handles escalations
"""

import json
from crewai import Agent
from openai import OpenAI
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import config
from knowledge_base import knowledge_base
from database.models import CallLog, Call, QualityMetric, Agent as AgentModel

class SupervisorAgent:
    """Supervisor Agent for quality monitoring and escalation handling"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.agent_config = config.AGENT_CONFIGS["supervisor"]
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            verbose=True,
            allow_delegation=True
        )
    
    def handle_escalation(self, call_id: str, escalation_reason: str, context: Dict = None) -> Dict[str, Any]:
        """Handle an escalated call"""
        
        # Log escalation
        CallLog.create({
            "call_id": call_id,
            "agent_id": "supervisor_agent",
            "message_type": "system",
            "content": f"Escalation received: {escalation_reason}"
        })
        
        try:
            # Get call history for context
            call_history = CallLog.get_by_call_id(call_id)
            conversation_context = "\n".join([
                f"{log.message_type}: {log.content}"
                for log in call_history[-10:]  # Last 10 messages
            ])
            
            # Use OpenAI to analyze the escalation and provide guidance
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an experienced call center supervisor handling an escalated customer service issue.
                        
                        Your responsibilities:
                        - Assess the escalation severity and appropriate response
                        - Provide specific guidance for resolution
                        - Determine if additional resources are needed
                        - Ensure customer satisfaction and issue resolution
                        - Maintain professional standards
                        
                        Escalation categories:
                        - billing_dispute: Billing or payment related issues
                        - service_failure: Service outages or technical failures  
                        - customer_dissatisfaction: Poor service experience
                        - policy_exception: Requests outside normal policy
                        - complex_technical: Advanced technical issues
                        - complaint_formal: Formal complaint requiring documentation
                        
                        Respond in JSON format with:
                        - escalation_category: category from above list
                        - severity_level: low/medium/high/critical
                        - recommended_action: specific action to take
                        - resolution_approach: step-by-step approach
                        - additional_resources: any additional help needed
                        - follow_up_required: true/false
                        - estimated_resolution_time: time estimate
                        - supervisor_response: what to tell the customer
                        """
                    },
                    {
                        "role": "user",
                        "content": f"""Escalation reason: {escalation_reason}
                        
                        Call context: {context or 'No additional context'}
                        
                        Recent conversation history:
                        {conversation_context}"""
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=self.agent_config["max_tokens"],
                temperature=self.agent_config["temperature"]
            )
            
            escalation_analysis = json.loads(response.choices[0].message.content)
            
            # Log supervisor's analysis
            CallLog.create({
                "call_id": call_id,
                "agent_id": "supervisor_agent",
                "message_type": "supervisor",
                "content": escalation_analysis.get("supervisor_response", "I'm reviewing your case and will provide a resolution.")
            })
            
            # Update call priority if needed
            call = Call.get_by_call_id(call_id)
            if call and escalation_analysis.get("severity_level") in ["high", "critical"]:
                call.priority = 4 if escalation_analysis.get("severity_level") == "critical" else 3
            
            return {
                "success": True,
                "escalation_handled": True,
                "analysis": escalation_analysis,
                "call_id": call_id,
                "supervisor_takeover": escalation_analysis.get("severity_level") in ["high", "critical"]
            }
            
        except Exception as e:
            # Fallback response for errors
            error_response = {
                "success": False,
                "error": str(e),
                "supervisor_response": "I apologize for the issue you're experiencing. I'm personally taking over your case to ensure it's resolved properly. Let me review the details and get back to you with a solution.",
                "escalation_handled": True,
                "supervisor_takeover": True
            }
            
            # Log error
            CallLog.create({
                "call_id": call_id,
                "agent_id": "supervisor_agent",
                "message_type": "system",
                "content": f"Error handling escalation: {str(e)}"
            })
            
            return error_response
    
    def monitor_call_quality(self, call_id: str) -> Dict[str, Any]:
        """Monitor and assess call quality"""
        try:
            call_history = CallLog.get_by_call_id(call_id)
            if not call_history:
                return {"error": "No call history found"}
            
            # Analyze conversation for quality metrics
            conversation_text = "\n".join([
                f"{log.message_type}: {log.content}"
                for log in call_history
                if log.message_type in ["customer", "agent"]
            ])
            
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this customer service conversation for quality metrics.
                        
                        Evaluate based on:
                        - Professional communication
                        - Problem resolution effectiveness
                        - Customer satisfaction indicators
                        - Response time and efficiency
                        - Adherence to procedures
                        - Empathy and rapport building
                        
                        Respond in JSON format with:
                        - overall_quality_score: 1-5 scale
                        - communication_score: 1-5 scale  
                        - resolution_effectiveness: 1-5 scale
                        - customer_satisfaction_indicators: positive/neutral/negative
                        - areas_for_improvement: list of specific areas
                        - positive_highlights: list of things done well
                        - recommendations: specific recommendations
                        - escalation_handled_properly: true/false if applicable
                        """
                    },
                    {
                        "role": "user",
                        "content": conversation_text
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.3
            )
            
            quality_analysis = json.loads(response.choices[0].message.content)
            
            # Store quality metrics
            QualityMetric.create({
                "call_id": call_id,
                "agent_id": "supervisor_agent",
                "quality_score": quality_analysis.get("overall_quality_score", 3),
                "resolution_status": "completed" if quality_analysis.get("resolution_effectiveness", 3) >= 3 else "needs_follow_up",
                "customer_satisfaction": self._convert_satisfaction_to_number(quality_analysis.get("customer_satisfaction_indicators", "neutral")),
                "notes": f"Quality review: {json.dumps(quality_analysis)}"
            })
            
            return {
                "success": True,
                "quality_analysis": quality_analysis,
                "call_id": call_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _convert_satisfaction_to_number(self, satisfaction_indicator: str) -> int:
        """Convert satisfaction indicator to numeric score"""
        mapping = {
            "positive": 5,
            "neutral": 3,
            "negative": 1
        }
        return mapping.get(satisfaction_indicator, 3)
    
    def generate_performance_report(self, agent_id: str = None, time_period: str = "today") -> Dict[str, Any]:
        """Generate performance report for agents"""
        try:
            # Calculate date range
            if time_period == "today":
                start_date = datetime.now().date()
            elif time_period == "week":
                start_date = datetime.now().date() - timedelta(days=7)
            elif time_period == "month":
                start_date = datetime.now().date() - timedelta(days=30)
            else:
                start_date = datetime.now().date()
            
            # Get performance data (simplified for demo)
            agents = AgentModel.get_all_agents() if not agent_id else [AgentModel.get_by_agent_id(agent_id)]
            
            performance_data = {}
            for agent in agents:
                if agent:
                    # Get call logs for the agent
                    agent_calls = self._get_agent_calls(agent.agent_id, start_date)
                    quality_metrics = self._get_agent_quality_metrics(agent.agent_id, start_date)
                    
                    performance_data[agent.agent_id] = {
                        "name": agent.name,
                        "role": agent.role,
                        "total_calls": len(agent_calls),
                        "average_quality_score": self._calculate_average_quality(quality_metrics),
                        "escalation_rate": self._calculate_escalation_rate(agent_calls),
                        "customer_satisfaction": self._calculate_satisfaction_score(quality_metrics),
                        "status": agent.status,
                        "recommendations": self._generate_agent_recommendations(agent.agent_id, quality_metrics)
                    }
            
            return {
                "success": True,
                "time_period": time_period,
                "report_date": datetime.now().isoformat(),
                "performance_data": performance_data,
                "summary": self._generate_summary(performance_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_agent_calls(self, agent_id: str, start_date) -> List:
        """Get calls handled by agent since start_date"""
        # Simplified implementation - would need proper date filtering in production
        return []
    
    def _get_agent_quality_metrics(self, agent_id: str, start_date) -> List:
        """Get quality metrics for agent since start_date"""
        # Simplified implementation
        return []
    
    def _calculate_average_quality(self, quality_metrics: List) -> float:
        """Calculate average quality score"""
        if not quality_metrics:
            return 0.0
        scores = [metric.get("quality_score", 0) for metric in quality_metrics]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_escalation_rate(self, agent_calls: List) -> float:
        """Calculate escalation rate for agent"""
        if not agent_calls:
            return 0.0
        escalated = sum(1 for call in agent_calls if "escalation" in str(call).lower())
        return (escalated / len(agent_calls)) * 100
    
    def _calculate_satisfaction_score(self, quality_metrics: List) -> float:
        """Calculate customer satisfaction score"""
        if not quality_metrics:
            return 0.0
        scores = [metric.get("customer_satisfaction", 3) for metric in quality_metrics]
        return sum(scores) / len(scores) if scores else 3.0
    
    def _generate_agent_recommendations(self, agent_id: str, quality_metrics: List) -> List[str]:
        """Generate recommendations for agent improvement"""
        recommendations = []
        
        avg_quality = self._calculate_average_quality(quality_metrics)
        if avg_quality < 3.5:
            recommendations.append("Focus on improving overall call quality and customer interaction")
        
        if len(quality_metrics) < 5:  # Low call volume
            recommendations.append("Increase call handling volume and engagement")
        
        return recommendations
    
    def _generate_summary(self, performance_data: Dict) -> Dict:
        """Generate summary statistics"""
        if not performance_data:
            return {}
        
        total_calls = sum(data["total_calls"] for data in performance_data.values())
        avg_quality = sum(data["average_quality_score"] for data in performance_data.values()) / len(performance_data)
        avg_satisfaction = sum(data["customer_satisfaction"] for data in performance_data.values()) / len(performance_data)
        
        return {
            "total_agents": len(performance_data),
            "total_calls_handled": total_calls,
            "average_quality_score": round(avg_quality, 2),
            "average_satisfaction": round(avg_satisfaction, 2),
            "top_performer": max(performance_data.keys(), key=lambda k: performance_data[k]["average_quality_score"])
        }
    
    def provide_coaching_feedback(self, agent_id: str, call_id: str) -> Dict[str, Any]:
        """Provide coaching feedback for specific call"""
        try:
            quality_analysis = self.monitor_call_quality(call_id)
            
            if not quality_analysis.get("success"):
                return {"success": False, "error": "Could not analyze call quality"}
            
            analysis = quality_analysis["quality_analysis"]
            
            # Generate coaching feedback
            coaching_response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an experienced call center supervisor providing coaching feedback.
                        Generate constructive, specific, and actionable feedback for the agent.
                        
                        Focus on:
                        - Specific behaviors to continue or change
                        - Practical tips for improvement
                        - Recognition of strengths
                        - Clear next steps for development
                        
                        Respond in JSON format with:
                        - strengths: list of specific strengths demonstrated
                        - improvement_areas: list of specific areas to improve
                        - actionable_tips: list of practical tips
                        - overall_feedback: summary feedback message
                        - development_goals: suggested goals for improvement
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Quality analysis results: {json.dumps(analysis)}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=600,
                temperature=0.7
            )
            
            coaching_feedback = json.loads(coaching_response.choices[0].message.content)
            
            # Log coaching session
            CallLog.create({
                "call_id": call_id,
                "agent_id": "supervisor_agent",
                "message_type": "system",
                "content": f"Coaching feedback provided for agent {agent_id}"
            })
            
            return {
                "success": True,
                "agent_id": agent_id,
                "call_id": call_id,
                "coaching_feedback": coaching_feedback
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
