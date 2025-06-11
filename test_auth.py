#!/usr/bin/env python3
"""
Test script to verify authentication system is working
"""

import sys
import os
sys.path.insert(0, '.')

def test_database():
    """Test database connection and tables"""
    try:
        from database.database import execute_query
        
        # Test users table
        users = execute_query("SELECT COUNT(*) FROM users")
        print(f"✅ Users table exists with {users[0][0] if users else 0} users")
        
        # Test user_sessions table
        sessions = execute_query("SELECT COUNT(*) FROM user_sessions")
        print(f"✅ User sessions table exists with {sessions[0][0] if sessions else 0} sessions")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_auth_utils():
    """Test authentication utilities"""
    try:
        from auth.auth_utils import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        if verify_password(password, hashed):
            print("✅ Password hashing and verification working")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test token creation
        token = create_access_token({"sub": "test_user"})
        if token and len(token) > 50:
            print("✅ JWT token creation working")
        else:
            print("❌ JWT token creation failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Auth utils test failed: {e}")
        return False

def test_user_model():
    """Test user model operations"""
    try:
        from auth.models import User
        
        # Check if admin user exists
        admin = User.get_by_username("admin")
        if admin:
            print(f"✅ Admin user exists: {admin.username} ({admin.email})")
            print(f"   Role: {admin.role.value}")
            print(f"   Active: {admin.is_active}")
        else:
            print("❌ Admin user not found")
            return False
        
        return True
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_authentication():
    """Test full authentication flow"""
    try:
        from auth.auth_utils import authenticate_user
        
        # Test admin login
        user = authenticate_user("admin", "Admin123!")
        if user:
            print(f"✅ Authentication working for admin user")
            print(f"   User ID: {user.id}")
            print(f"   Role: {user.role.value}")
        else:
            print("❌ Authentication failed for admin user")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Call Center Authentication System")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database),
        ("Authentication Utils", test_auth_utils),
        ("User Model", test_user_model),
        ("Authentication Flow", test_authentication)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication system is working correctly.")
        print("\n🚀 You can now:")
        print("1. Run the application: python main.py")
        print("2. Visit: http://localhost:5000/login")
        print("3. Login with: admin / Admin123!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 