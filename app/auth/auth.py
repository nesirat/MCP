from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
import logging

from app.core.security.tokens import TokenManager
from app.models import User
from app.db.database import get_db
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
token_manager = TokenManager(settings.SECRET_KEY)

@router.post("/token")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember: str = "false",
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    logger.info("=== LOGIN ATTEMPT START ===")
    logger.info(f"Login attempt for user: {form_data.username}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request cookies: {request.cookies}")
    
    try:
        # Get user from database
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user:
            logger.info(f"User not found: {form_data.username}")
            logger.info("=== LOGIN ATTEMPT FAILED ===")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"User found: {user.email}")
        logger.info(f"User ID: {user.id}")
        logger.info(f"User is_active: {user.is_active}")
        logger.info(f"User is_admin: {user.is_admin}")
        logger.info(f"User hashed_password length: {len(user.hashed_password)}")
        
        # Verify password
        logger.info("\n=== PASSWORD VERIFICATION START ===")
        logger.info(f"Debug - Plain password length: {len(form_data.password)}")
        logger.info(f"Debug - Hashed password length: {len(user.hashed_password)}")
        
        if not user.verify_password(form_data.password):
            logger.info("Debug - Password verification result: False")
            logger.info("=== PASSWORD VERIFICATION COMPLETE ===")
            logger.info("\n=== LOGIN ATTEMPT FAILED ===")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info("Debug - Password verification result: True")
        logger.info("=== PASSWORD VERIFICATION COMPLETE ===\n")
        logger.info("Password verified successfully")
        
        # Convert remember string to boolean
        remember_bool = remember.lower() == "true"
        
        # Create access token
        access_token_expires = timedelta(days=30 if remember_bool else 1)
        access_token = token_manager.create_access_token(
            data={"sub": user.email},
            remember=remember_bool,
            expires_delta=access_token_expires
        )
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Set cookie
        max_age = 30 * 24 * 60 * 60 if remember_bool else 24 * 60 * 60  # 30 days or 1 day
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            max_age=max_age,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        logger.info("=== LOGIN ATTEMPT SUCCESSFUL ===")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.info("=== LOGIN ATTEMPT FAILED ===")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login process"
        )

@router.post("/logout")
async def logout(response: Response):
    """
    Logout the user by clearing the access token cookie
    """
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"} 