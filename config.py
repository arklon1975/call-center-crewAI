"""
Configuration settings for the call center system
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CallCenterConfig:
    """Configuration class for call center settings"""
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    OPENAI_MODEL = "gpt-4o"
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///call_center.db")
    
    # Redis Configuration (for rate limiting and sessions)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    
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
