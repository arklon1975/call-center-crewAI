"""
Multi-Agent Call Center System with CrewAI
Main application entry point with FastAPI server
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import time
import logging

from api.routes import router
from auth.routes import router as auth_router
from auth.dependencies import get_optional_current_user
from database.database import init_database
from crew_manager import CallCenterCrew
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Application shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Call Center System",
    description="CrewAI-powered call center with specialized agents and authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if config.DEBUG else ["localhost", "127.0.0.1"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not config.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(get_optional_current_user)):
    """Main dashboard page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user=Depends(get_optional_current_user)):
    """Agent monitoring dashboard"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, current_user=Depends(get_optional_current_user)):
    """Admin panel"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": current_user
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return templates.TemplateResponse("404.html", {
        "request": request
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse("500.html", {
        "request": request
    }, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    # Log startup information
    logger.info(f"Starting Call Center System on port {port}")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )
