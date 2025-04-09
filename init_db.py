import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base
from app.auth import get_password_hash
from app.models.user import User

def init_db():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.email == "admin@mcp.local").first()
        if not admin:
            # Create admin user
            admin = User(
                email="admin@mcp.local",
                hashed_password=get_password_hash("Admin@123"),
                full_name="Admin User",
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 