#!/usr/bin/env python3
"""
Simple database initialization script
"""

import sys
import os
sys.path.insert(0, '.')

def init_system():
    """Initialize the system"""
    try:
        # Initialize database
        from database.database import init_database
        print("Initializing database...")
        init_database()
        print("✅ Database initialized")
        
        # Check if admin user exists
        from auth.models import User
        admin = User.get_by_username("admin")
        
        if not admin:
            # Create admin user
            from auth.auth_utils import get_password_hash
            admin_data = {
                "username": "admin",
                "email": "admin@callcenter.com", 
                "full_name": "System Administrator",
                "hashed_password": get_password_hash("Admin123!"),
                "role": "admin",
                "is_active": True,
                "is_verified": True
            }
            
            admin = User.create(admin_data)
            print("✅ Admin user created")
            print("   Username: admin")
            print("   Password: Admin123!")
        else:
            print("✅ Admin user already exists")
        
        print("\n🎉 System ready!")
        print("Run: python main.py")
        print("Visit: http://localhost:5000/login")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_system() 