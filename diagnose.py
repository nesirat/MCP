import logging
from app.db.database import SessionLocal, engine
from app.db import models
from app.core.config import settings
from app.core.security import verify_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    logger.info("\n=== Database Check ===")
    try:
        # Check database connection
        db = SessionLocal()
        logger.info("Database connection successful")
        
        # Check tables
        tables = engine.table_names()
        logger.info(f"Available tables: {tables}")
        
        # Check users table
        users = db.query(models.User).all()
        logger.info(f"\nTotal users in database: {len(users)}")
        
        # Check admin user
        admin = db.query(models.User).filter(models.User.email == "admin@mcp.local").first()
        if admin:
            logger.info("\nAdmin user found:")
            logger.info(f"Email: {admin.email}")
            logger.info(f"ID: {admin.id}")
            logger.info(f"Is active: {admin.is_active}")
            logger.info(f"Is admin: {admin.is_admin}")
            logger.info(f"Last login: {admin.last_login}")
            
            # Test password verification
            test_password = "Admin@123"
            is_valid = verify_password(test_password, admin.hashed_password)
            logger.info(f"\nPassword verification test:")
            logger.info(f"Test password: {test_password}")
            logger.info(f"Password valid: {is_valid}")
        else:
            logger.error("Admin user not found!")
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

def check_config():
    logger.info("\n=== Configuration Check ===")
    logger.info(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
    logger.info(f"ALGORITHM: {settings.ALGORITHM}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    logger.info(f"DB_HOST: {settings.DB_HOST}")
    logger.info(f"DB_PORT: {settings.DB_PORT}")
    logger.info(f"DB_USER: {settings.DB_USER}")
    logger.info(f"DB_NAME: {settings.DB_NAME}")

if __name__ == "__main__":
    try:
        check_config()
        check_database()
        logger.info("\nDiagnostic check completed successfully")
    except Exception as e:
        logger.error(f"Diagnostic check failed: {str(e)}")
        raise 