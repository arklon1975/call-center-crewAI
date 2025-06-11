"""
Configuration settings for the call center system
"""

import os
from typing import Dict, Any

class CallCenterConfig:
    """Configuration class for call center settings"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    OPENAI_MODEL = "gpt-4o"
    
    # Database Configuration
    DATABASE_URL = "sqlite:///call_center.db"
    
    # Agent Configuration
    AGENT_CONFIGS = {
        "customer_service": {
            "name": "Customer Service Agent",
            "role": "Customer Support Specialist",
            "goal": "Provide excellent customer service and resolve inquiries efficiently",
            "backstory": "You are an experienced customer service representative with deep knowledge of company policies and procedures.",
            "max_tokens": 1000,
            "temperature": 0.7
        },
        "call_routing": {
            "name": "Call Routing Agent",
            "role": "Call Distribution Specialist",
            "goal": "Route calls to the most appropriate department or agent based on customer needs",
            "backstory": "You are an intelligent call routing system that understands customer inquiries and directs them efficiently.",
            "max_tokens": 500,
            "temperature": 0.3
        },
        "supervisor": {
            "name": "Supervisor Agent",
            "role": "Quality Assurance Supervisor",
            "goal": "Monitor call quality, provide guidance, and handle escalations",
            "backstory": "You are a seasoned call center supervisor focused on maintaining high service standards and resolving complex issues.",
            "max_tokens": 1200,
            "temperature": 0.5
        }
    }
    
    # Call Center Departments
    DEPARTMENTS = {
        "technical_support": "Technical Support",
        "billing": "Billing and Accounts",
        "sales": "Sales Department", 
        "general": "General Inquiries",
        "complaints": "Complaints and Escalations"
    }
    
    # System Settings
    MAX_CONVERSATION_TURNS = 10
    CALL_TIMEOUT_MINUTES = 30
    QUALITY_SCORE_THRESHOLD = 3.5

config = CallCenterConfig()
