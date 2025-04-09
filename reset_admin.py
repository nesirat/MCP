import logging
from app.db.database import SessionLocal, engine
from app.db import models
from app.core.security import get_password_hash, verify_password
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_admin():
    logger.info("\n=== Starting Admin Reset ===")
    
    try:
        # Create database tables
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        
        # Create a new session
        db = SessionLocal()
        
        try:
            # Drop all existing users
            logger.info("Dropping existing users...")
            db.execute(text("DELETE FROM users"))
            db.commit()
            
            # Create new admin user
            logger.info("\n=== Creating Admin User ===")
            password = "admin"
            logger.info(f"Using password: {password}")
            
            hashed = get_password_hash(password)
            logger.info(f"Generated hash: {hashed}")
            logger.info(f"Hash length: {len(hashed)}")
            
            # Verify the hash works before saving
            verify_result = verify_password(password, hashed)
            logger.info(f"Verification test result: {verify_result}")
            
            admin_user = models.User(
                email="admin@mcp.local",
                hashed_password=hashed,
                is_active=True,
                is_admin=True,
                name="Administrator"
            )
            db.add(admin_user)
            db.commit()
            
            # Verify admin user
            admin = db.query(models.User).filter(models.User.email == "admin@mcp.local").first()
            if admin:
                logger.info("\nAdmin user created successfully:")
                logger.info(f"Email: {admin.email}")
                logger.info(f"ID: {admin.id}")
                logger.info(f"Is active: {admin.is_active}")
                logger.info(f"Is admin: {admin.is_admin}")
                logger.info(f"Password hash: {admin.hashed_password}")
                logger.info(f"Password hash length: {len(admin.hashed_password)}")
                
                # Verify the saved hash
                verify_result = verify_password(password, admin.hashed_password)
                logger.info(f"Final verification test result: {verify_result}")
            else:
                logger.error("Failed to create admin user!")
            
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
    reset_admin() 