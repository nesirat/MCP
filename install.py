import os
import sys
import getpass
import re
from app.db.database import SessionLocal, engine
from app.db import models
from passlib.context import CryptContext
from pydantic import EmailStr

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_password(password: str) -> bool:
    """Validate password meets requirements"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@$!%*?&]", password):
        return False
    return True

def get_admin_credentials():
    """Get admin credentials from user input"""
    print("\n=== MCP Installation ===")
    print("Please provide admin credentials:")
    
    while True:
        email = input("Admin email: ").strip()
        try:
            EmailStr.validate(email)
            break
        except ValueError:
            print("Invalid email format. Please try again.")
    
    while True:
        password = getpass.getpass("Admin password: ")
        if validate_password(password):
            break
        print("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character")
    
    return email, password

def create_admin_user(email: str, password: str):
    """Create admin user in database"""
    # Create database tables
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(models.User).filter(models.User.is_admin == True).first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return

        # Create new admin user
        hashed_password = pwd_context.hash(password)
        admin_user = models.User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created successfully: {email}")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

def create_directories():
    """Create necessary directories"""
    directories = [
        "app/static",
        "app/static/css",
        "app/static/js",
        "app/static/img",
        "app/templates",
        "logs",
        "certs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Main installation function"""
    print("\n=== MCP Installation ===")
    
    # Create necessary directories
    create_directories()
    
    # Use default admin credentials
    email = "admin@mcp.local"
    password = "Admin@123"
    
    # Create admin user
    create_admin_user(email, password)
    
    print("\nInstallation completed successfully!")
    print(f"Admin email: {email}")
    print("Please keep these credentials safe!")

if __name__ == "__main__":
    main() 