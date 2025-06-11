#!/usr/bin/env python3
"""
Setup script for authentication system
Creates database tables and default admin user
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Setup environment variables"""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("""# Call Center System Environment Variables

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-use-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database
DATABASE_URL=sqlite:///call_center.db

# Redis (for rate limiting and caching)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000

# Environment
ENVIRONMENT=development

# Server
PORT=5000
""")
        print("✅ .env file created. Please update with your actual values.")
    else:
        print("✅ .env file already exists.")

def setup_database():
    """Initialize database with authentication tables"""
    try:
        from database.database import init_database
        print("Initializing database...")
        init_database()
        print("✅ Database initialized successfully.")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def create_admin_user():
    """Create default admin user"""
    try:
        from auth.models import User
        from auth.auth_utils import get_password_hash
        
        # Check if admin user already exists
        existing_admin = User.get_by_username("admin")
        if existing_admin:
            print("✅ Admin user already exists.")
            return True
        
        # Create admin user
        admin_data = {
            "username": "admin",
            "email": "admin@callcenter.com",
            "full_name": "System Administrator",
            "hashed_password": get_password_hash("Admin123!"),
            "role": "admin",
            "is_active": True,
            "is_verified": True
        }
        
        admin_user = User.create(admin_data)
        if admin_user:
            print("✅ Admin user created successfully!")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("   ⚠️  Please change the password after first login!")
            return True
        else:
            print("❌ Failed to create admin user.")
            return False
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def verify_setup():
    """Verify the setup is working"""
    try:
        from auth.models import User
        from auth.auth_utils import authenticate_user
        
        # Test authentication
        user = authenticate_user("admin", "Admin123!")
        if user:
            print("✅ Authentication system working correctly.")
            return True
        else:
            print("❌ Authentication test failed.")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Call Center Authentication System...")
    print("=" * 50)
    
    # Step 1: Setup environment
    print("\n1. Setting up environment...")
    setup_environment()
    
    # Step 2: Initialize database
    print("\n2. Initializing database...")
    if not setup_database():
        print("❌ Setup failed at database initialization.")
        return False
    
    # Step 3: Create admin user
    print("\n3. Creating admin user...")
    if not create_admin_user():
        print("❌ Setup failed at admin user creation.")
        return False
    
    # Step 4: Verify setup
    print("\n4. Verifying setup...")
    if not verify_setup():
        print("❌ Setup verification failed.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update the .env file with your actual OpenAI API key")
    print("2. Run the application: python main.py")
    print("3. Visit http://localhost:5000/login")
    print("4. Login with admin/Admin123! and change the password")
    print("\n🔒 Security reminders:")
    print("- Change the default admin password immediately")
    print("- Update the SECRET_KEY in .env file")
    print("- Use strong passwords for all users")
    print("- Enable HTTPS in production")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 