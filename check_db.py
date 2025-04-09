from app.db.database import SessionLocal, engine
from app.db import models
from app.core.security import get_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    try:
        # Create database tables
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        
        # Create a new session
        db = SessionLocal()
        
        try:
            # Check if admin user exists
            logger.info("Checking for existing admin user...")
            admin = db.query(models.User).filter(models.User.email == "admin@mcp.local").first()
            
            if admin:
                logger.info(f"Admin user exists: {admin.email}")
                logger.info(f"Admin user ID: {admin.id}")
                logger.info(f"Admin user is_active: {admin.is_active}")
                logger.info(f"Admin user is_admin: {admin.is_admin}")
            else:
                logger.info("Admin user does not exist, creating...")
                admin_user = models.User(
                    email="admin@mcp.local",
                    hashed_password=get_password_hash("Admin@123"),
                    is_active=True,
                    is_admin=True,
                    name="Administrator"
                )
                db.add(admin_user)
                db.commit()
                logger.info("Admin user created successfully")
            
            # List all users
            logger.info("\nListing all users:")
            users = db.query(models.User).all()
            for user in users:
                logger.info(f"User: {user.email}, ID: {user.id}, Active: {user.is_active}, Admin: {user.is_admin}")
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    check_database() 