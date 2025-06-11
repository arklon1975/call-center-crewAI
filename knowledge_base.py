"""
Knowledge base for call center agents
Contains common responses, procedures, and information
"""

from typing import Dict, List, Optional

class KnowledgeBase:
    """Centralized knowledge base for call center operations"""
    
    def __init__(self):
        self.faq = self._load_faq()
        self.procedures = self._load_procedures()
        self.escalation_rules = self._load_escalation_rules()
        self.department_info = self._load_department_info()
    
    def _load_faq(self) -> Dict[str, str]:
        """Load frequently asked questions and answers"""
        return {
            "billing_question": "For billing inquiries, I can help you with account balances, payment methods, and billing history. What specific billing question do you have?",
            "technical_support": "I can assist with technical issues including connectivity problems, software installation, and troubleshooting. Please describe the technical issue you're experiencing.",
            "account_access": "If you're having trouble accessing your account, I can help with password resets, account verification, and login issues. Can you provide your account email or phone number?",
            "service_cancellation": "I understand you want to cancel your service. Let me connect you with our retention specialist who can review your account and discuss available options.",
            "refund_request": "For refund requests, I'll need to review your account and recent transactions. Can you provide details about the charge you'd like to dispute?",
            "product_information": "I'd be happy to provide information about our products and services. What specific product are you interested in learning about?",
            "complaint_resolution": "I apologize for any inconvenience you've experienced. I want to make sure we resolve this properly. Can you please explain the issue in detail?"
        }
    
    def _load_procedures(self) -> Dict[str, List[str]]:
        """Load standard operating procedures"""
        return {
            "call_opening": [
                "Greet the customer warmly",
                "Identify yourself and the company",
                "Ask how you can help today",
                "Listen actively to the customer's concern"
            ],
            "issue_resolution": [
                "Gather all relevant information",
                "Verify customer identity if needed",
                "Research the issue thoroughly",
                "Provide clear solution steps",
                "Confirm customer understanding",
                "Follow up if necessary"
            ],
            "escalation": [
                "Identify when escalation is needed",
                "Inform customer about escalation",
                "Prepare comprehensive case summary",
                "Transfer to appropriate supervisor",
                "Follow up on resolution"
            ],
            "call_closing": [
                "Summarize what was accomplished",
                "Ask if there are any other questions",
                "Provide reference number if applicable",
                "Thank the customer for their call",
                "End the call professionally"
            ]
        }
    
    def _load_escalation_rules(self) -> Dict[str, Dict]:
        """Load escalation rules and triggers"""
        return {
            "high_priority": {
                "conditions": ["service_outage", "security_issue", "billing_dispute_over_500"],
                "escalate_to": "supervisor",
                "time_limit": 5  # minutes
            },
            "technical_complex": {
                "conditions": ["multiple_failed_attempts", "advanced_configuration"],
                "escalate_to": "technical_specialist",
                "time_limit": 15
            },
            "customer_dissatisfaction": {
                "conditions": ["complaint", "multiple_transfers", "request_supervisor"],
                "escalate_to": "supervisor",
                "time_limit": 2
            }
        }
    
    def _load_department_info(self) -> Dict[str, Dict]:
        """Load department information and routing rules"""
        return {
            "technical_support": {
                "description": "Hardware, software, and connectivity issues",
                "keywords": ["not working", "error", "connection", "setup", "install"],
                "hours": "24/7",
                "avg_wait_time": "3 minutes"
            },
            "billing": {
                "description": "Account billing, payments, and charges",
                "keywords": ["bill", "payment", "charge", "refund", "account"],
                "hours": "8 AM - 8 PM",
                "avg_wait_time": "2 minutes"
            },
            "sales": {
                "description": "New services, upgrades, and product information",
                "keywords": ["buy", "purchase", "upgrade", "new service", "pricing"],
                "hours": "9 AM - 6 PM",
                "avg_wait_time": "1 minute"
            },
            "general": {
                "description": "General inquiries and information",
                "keywords": ["information", "hours", "location", "general"],
                "hours": "24/7",
                "avg_wait_time": "2 minutes"
            }
        }
    
    def get_response(self, query_type: str) -> Optional[str]:
        """Get a standard response for a query type"""
        return self.faq.get(query_type)
    
    def get_procedure(self, procedure_name: str) -> Optional[List[str]]:
        """Get procedure steps"""
        return self.procedures.get(procedure_name)
    
    def should_escalate(self, situation: str, call_duration: int = 0) -> Dict:
        """Determine if a situation should be escalated"""
        for rule_name, rule in self.escalation_rules.items():
            if situation in rule["conditions"]:
                return {
                    "should_escalate": True,
                    "escalate_to": rule["escalate_to"],
                    "reason": rule_name,
                    "time_exceeded": call_duration > rule["time_limit"]
                }
        
        return {"should_escalate": False}
    
    def route_to_department(self, customer_message: str) -> str:
        """Determine which department should handle the inquiry"""
        message_lower = customer_message.lower()
        
        for dept, info in self.department_info.items():
            for keyword in info["keywords"]:
                if keyword in message_lower:
                    return dept
        
        return "general"  # Default department
    
    def get_department_info(self, department: str) -> Optional[Dict]:
        """Get information about a department"""
        return self.department_info.get(department)

# Global knowledge base instance
knowledge_base = KnowledgeBase()
