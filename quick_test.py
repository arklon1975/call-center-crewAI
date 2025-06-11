import sys
sys.path.insert(0, '.')

try:
    from database.database import execute_query
    users = execute_query("SELECT username, email, role FROM users")
    print("Users in database:")
    for user in users:
        print(f"  - {user[0]} ({user[1]}) - Role: {user[2]}")
    
    from auth.models import User
    admin = User.get_by_username("admin")
    if admin:
        print(f"Admin user found: {admin.username}")
        print(f"Role: {admin.role.value}")
        print("Authentication system is working!")
    else:
        print("Admin user not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 