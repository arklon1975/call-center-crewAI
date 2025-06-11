#!/usr/bin/env python3
"""
Simplified Call Center App with Authentication
"""

import os
import sys
sys.path.insert(0, '.')

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

# Initialize database first
try:
    from database.database import init_database
    init_database()
    print("✅ Database initialized")
except Exception as e:
    print(f"Database init error: {e}")

# Import auth components
try:
    from auth.models import User
    from auth.auth_utils import authenticate_user, create_access_token, get_password_hash
    from auth.dependencies import get_optional_current_user
    print("✅ Auth modules loaded")
except Exception as e:
    print(f"Auth import error: {e}")

# Create admin user if doesn't exist
try:
    admin = User.get_by_username("admin")
    if not admin:
        admin_data = {
            "username": "admin",
            "email": "admin@callcenter.com",
            "full_name": "System Administrator", 
            "hashed_password": get_password_hash("Admin123!"),
            "role": "admin",
            "is_active": True,
            "is_verified": True
        }
        User.create(admin_data)
        print("✅ Admin user created: admin/Admin123!")
    else:
        print("✅ Admin user exists")
except Exception as e:
    print(f"Admin creation error: {e}")

# Initialize FastAPI app
app = FastAPI(title="Call Center System", version="1.0.0")

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    print("✅ Static files and templates mounted")
except Exception as e:
    print(f"Static files error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Call Center System is running",
        "version": "1.0.0"
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(get_optional_current_user)):
    """Main page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"""
        <html>
        <head><title>Login - Call Center</title></head>
        <body>
            <h1>Call Center System - Login</h1>
            <form method="post" action="/api/auth/login">
                <div>
                    <label>Username:</label>
                    <input type="text" name="username" value="admin" required>
                </div>
                <div>
                    <label>Password:</label>
                    <input type="password" name="password" value="Admin123!" required>
                </div>
                <button type="submit">Login</button>
            </form>
            <p>Default credentials: admin / Admin123!</p>
        </body>
        </html>
        """)

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint"""
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "role": user.role.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def dashboard(current_user=Depends(get_optional_current_user)):
    """Dashboard endpoint"""
    if not current_user:
        return {"error": "Authentication required"}
    
    return {
        "message": "Welcome to the dashboard!",
        "user": current_user.username,
        "role": current_user.role.value
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Call Center System on port {port}")
    print(f"📱 Visit: http://localhost:{port}/login")
    print("🔑 Credentials: admin / Admin123!")
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=port,
        reload=False
    ) 