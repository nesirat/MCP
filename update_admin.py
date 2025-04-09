import logging
from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_admin_password():
    logger.info("\n=== Updating Admin Password ===")
    
    try:
        # Create a new session
        db = SessionLocal()
        
        try:
            # Find admin user
            admin = db.query(models.User).filter(models.User.email == "admin@mcp.local").first()
            if admin:
                # Update password
                admin.hashed_password = get_password_hash("admin123")
                db.commit()
                
                logger.info("\nAdmin password updated successfully:")
                logger.info(f"Email: {admin.email}")
                logger.info(f"ID: {admin.id}")
                logger.info(f"Is active: {admin.is_active}")
                logger.info(f"Is admin: {admin.is_admin}")
                logger.info(f"Password hash length: {len(admin.hashed_password)}")
            else:
                logger.error("Admin user not found!")
            
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
    update_admin_password() 