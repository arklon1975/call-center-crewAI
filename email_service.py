"""
Email service for sending customer information via email
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to customers"""
    
    def __init__(self):
        self.config = self._get_email_config()
        self.fastmail = FastMail(self.config)
        self.template_env = Environment(
            loader=FileSystemLoader('templates/emails')
        )
    
    def _get_email_config(self) -> ConnectionConfig:
        """Get email configuration from environment variables"""
        return ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", "noreply@callcenter.com"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
            MAIL_FROM=os.getenv("MAIL_FROM", "noreply@callcenter.com"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "true").lower() == "true",
            MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "false").lower() == "true",
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
    
    async def send_chat_summary_email(
        self,
        customer_email: str,
        customer_name: str,
        call_id: str,
        chat_summary: Dict[str, Any],
        agent_name: str = "Nuestro Agente"
    ) -> bool:
        """
        Send chat summary email to customer
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            call_id: Call ID for reference
            chat_summary: Summary of the chat conversation
            agent_name: Name of the agent who handled the call
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Prepare email content
            subject = f"Resumen de tu conversación - Call Center"
            
            # Create email template context
            context = {
                "customer_name": customer_name,
                "call_id": call_id,
                "agent_name": agent_name,
                "conversation_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "chat_summary": chat_summary,
                "company_name": "Call Center System",
                "support_email": "soporte@callcenter.com"
            }
            
            # Render email template
            template = self.template_env.get_template("chat_summary.html")
            html_content = template.render(**context)
            
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[customer_email],
                body=html_content,
                subtype="html"
            )
            
            # Send email
            await self.fastmail.send_message(message)
            
            logger.info(f"Chat summary email sent to {customer_email} for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send chat summary email to {customer_email}: {str(e)}")
            return False
    
    async def send_information_request_email(
        self,
        customer_email: str,
        customer_name: str,
        call_id: str,
        requested_info: List[str],
        agent_name: str = "Nuestro Agente"
    ) -> bool:
        """
        Send email with requested information to customer
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            call_id: Call ID for reference
            requested_info: List of requested information items
            agent_name: Name of the agent who handled the call
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = f"Información solicitada - Call Center"
            
            context = {
                "customer_name": customer_name,
                "call_id": call_id,
                "agent_name": agent_name,
                "conversation_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "requested_info": requested_info,
                "company_name": "Call Center System",
                "support_email": "soporte@callcenter.com"
            }
            
            template = self.template_env.get_template("information_request.html")
            html_content = template.render(**context)
            
            message = MessageSchema(
                subject=subject,
                recipients=[customer_email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            
            logger.info(f"Information request email sent to {customer_email} for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send information request email to {customer_email}: {str(e)}")
            return False
    
    async def send_follow_up_email(
        self,
        customer_email: str,
        customer_name: str,
        call_id: str,
        follow_up_notes: str,
        agent_name: str = "Nuestro Agente"
    ) -> bool:
        """
        Send follow-up email to customer
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            call_id: Call ID for reference
            follow_up_notes: Follow-up notes or additional information
            agent_name: Name of the agent who handled the call
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = f"Seguimiento de tu consulta - Call Center"
            
            context = {
                "customer_name": customer_name,
                "call_id": call_id,
                "agent_name": agent_name,
                "conversation_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "follow_up_notes": follow_up_notes,
                "company_name": "Call Center System",
                "support_email": "soporte@callcenter.com"
            }
            
            template = self.template_env.get_template("follow_up.html")
            html_content = template.render(**context)
            
            message = MessageSchema(
                subject=subject,
                recipients=[customer_email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            
            logger.info(f"Follow-up email sent to {customer_email} for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send follow-up email to {customer_email}: {str(e)}")
            return False

# Global email service instance
email_service = EmailService() 