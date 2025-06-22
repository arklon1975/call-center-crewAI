"""
Email routes for sending customer information via email
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr
from auth.dependencies import require_auth
from auth.models import User
from email_service import email_service
from config import config

router = APIRouter(prefix="/email", tags=["email"])

# Pydantic models
class EmailConfirmationRequest(BaseModel):
    call_id: str
    customer_email: EmailStr
    customer_name: str
    email_type: str  # "chat_summary", "information_request", "follow_up"
    confirmation_required: bool = True

class ChatSummaryEmailRequest(BaseModel):
    call_id: str
    customer_email: EmailStr
    customer_name: str
    chat_summary: Dict[str, Any]
    agent_name: Optional[str] = None

class InformationRequestEmailRequest(BaseModel):
    call_id: str
    customer_email: EmailStr
    customer_name: str
    requested_info: List[str]
    agent_name: Optional[str] = None

class FollowUpEmailRequest(BaseModel):
    call_id: str
    customer_email: EmailStr
    customer_name: str
    follow_up_notes: str
    agent_name: Optional[str] = None

class EmailConfirmationResponse(BaseModel):
    call_id: str
    customer_email: str
    email_type: str
    confirmed: bool
    message: str

@router.post("/confirm", response_model=EmailConfirmationResponse)
async def confirm_email_sending(
    request: EmailConfirmationRequest,
    current_user: User = Depends(require_auth)
) -> EmailConfirmationResponse:
    """
    Confirm if customer wants to receive email with chat information
    This endpoint should be called before sending the actual email
    """
    try:
        # In a real implementation, you might want to:
        # 1. Store the confirmation request in database
        # 2. Send a confirmation email to customer
        # 3. Wait for customer confirmation
        
        # For now, we'll simulate that customer confirmed
        # In production, you'd implement a proper confirmation flow
        
        return EmailConfirmationResponse(
            call_id=request.call_id,
            customer_email=request.customer_email,
            email_type=request.email_type,
            confirmed=True,
            message="Email confirmation request processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email confirmation: {str(e)}"
        )

@router.post("/send-chat-summary")
async def send_chat_summary_email(
    email_request: ChatSummaryEmailRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Send chat summary email to customer
    """
    try:
        success = await email_service.send_chat_summary_email(
            customer_email=email_request.customer_email,
            customer_name=email_request.customer_name,
            call_id=email_request.call_id,
            chat_summary=email_request.chat_summary,
            agent_name=email_request.agent_name or current_user.full_name
        )
        
        if success:
            return {
                "success": True,
                "message": "Chat summary email sent successfully",
                "call_id": email_request.call_id,
                "customer_email": email_request.customer_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send chat summary email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send chat summary email: {str(e)}"
        )

@router.post("/send-information-request")
async def send_information_request_email(
    email_request: InformationRequestEmailRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Send information request email to customer
    """
    try:
        success = await email_service.send_information_request_email(
            customer_email=email_request.customer_email,
            customer_name=email_request.customer_name,
            call_id=email_request.call_id,
            requested_info=email_request.requested_info,
            agent_name=email_request.agent_name or current_user.full_name
        )
        
        if success:
            return {
                "success": True,
                "message": "Information request email sent successfully",
                "call_id": email_request.call_id,
                "customer_email": email_request.customer_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send information request email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send information request email: {str(e)}"
        )

@router.post("/send-follow-up")
async def send_follow_up_email(
    email_request: FollowUpEmailRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Send follow-up email to customer
    """
    try:
        success = await email_service.send_follow_up_email(
            customer_email=email_request.customer_email,
            customer_name=email_request.customer_name,
            call_id=email_request.call_id,
            follow_up_notes=email_request.follow_up_notes,
            agent_name=email_request.agent_name or current_user.full_name
        )
        
        if success:
            return {
                "success": True,
                "message": "Follow-up email sent successfully",
                "call_id": email_request.call_id,
                "customer_email": email_request.customer_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send follow-up email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send follow-up email: {str(e)}"
        )

@router.get("/templates")
async def get_email_templates(current_user: User = Depends(require_auth)) -> Dict[str, Any]:
    """
    Get available email templates
    """
    return {
        "success": True,
        "templates": [
            {
                "id": "chat_summary",
                "name": "Resumen de Conversación",
                "description": "Envía un resumen completo de la conversación con el cliente",
                "fields": ["customer_email", "customer_name", "call_id", "chat_summary"]
            },
            {
                "id": "information_request",
                "name": "Información Solicitada",
                "description": "Envía información específica solicitada por el cliente",
                "fields": ["customer_email", "customer_name", "call_id", "requested_info"]
            },
            {
                "id": "follow_up",
                "name": "Seguimiento",
                "description": "Envía información de seguimiento o notas adicionales",
                "fields": ["customer_email", "customer_name", "call_id", "follow_up_notes"]
            }
        ]
    }

@router.get("/status")
async def get_email_status(current_user: User = Depends(require_auth)) -> Dict[str, Any]:
    """
    Get email service status
    """
    try:
        # Check if email configuration is valid
        config_valid = bool(
            config.MAIL_USERNAME and 
            config.MAIL_PASSWORD and 
            config.MAIL_SERVER
        )
        
        return {
            "success": True,
            "email_service_status": "configured" if config_valid else "not_configured",
            "mail_server": config.MAIL_SERVER,
            "mail_port": config.MAIL_PORT,
            "mail_from": config.MAIL_FROM,
            "support_email": config.SUPPORT_EMAIL
        }
        
    except Exception as e:
        return {
            "success": False,
            "email_service_status": "error",
            "error": str(e)
        } 