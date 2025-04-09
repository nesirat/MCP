from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(f"\n=== PASSWORD VERIFICATION START ===")
    print(f"Debug - Plain password length: {len(plain_password)}")
    print(f"Debug - Hashed password length: {len(hashed_password)}")
    
    try:
        # Convert plain password to bytes and verify
        password_bytes = plain_password.encode()
        hashed_bytes = hashed_password.encode()
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
        print(f"Debug - Password verification result: {result}")
        print("=== PASSWORD VERIFICATION COMPLETE ===\n")
        return result
    except Exception as e:
        print(f"Debug - Error during password verification: {str(e)}")
        print("=== PASSWORD VERIFICATION FAILED ===\n")
        return False

def get_password_hash(password: str) -> str:
    print(f"\n=== PASSWORD HASHING START ===")
    print(f"Debug - Input password length: {len(password)}")
    
    try:
        # Generate salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        hashed_str = hashed.decode()
        print(f"Debug - Generated hash length: {len(hashed_str)}")
        print("=== PASSWORD HASHING COMPLETE ===\n")
        return hashed_str
    except Exception as e:
        print(f"Debug - Error during password hashing: {str(e)}")
        print("=== PASSWORD HASHING FAILED ===\n")
        raise

def create_access_token(data: dict, remember_me: bool = False):
    print(f"\n=== TOKEN CREATION START ===")
    print(f"Debug - Creating token with data: {data}")
    print(f"Debug - Remember me: {remember_me}")
    
    to_encode = data.copy()
    if remember_me:
        expire = datetime.utcnow() + timedelta(days=30)  # 30 days for remember me
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    print(f"Debug - Token payload: {to_encode}")
    
    try:
        # Ensure SECRET_KEY is properly set
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY is not set")
        
        print(f"Debug - Using SECRET_KEY length: {len(settings.SECRET_KEY)}")
        print(f"Debug - Using ALGORITHM: {settings.ALGORITHM}")
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        print(f"Debug - Token created successfully")
        print(f"Debug - Token length: {len(encoded_jwt)}")
        print("=== TOKEN CREATION COMPLETE ===\n")
        return encoded_jwt
    except Exception as e:
        print(f"Debug - Error creating token: {str(e)}")
        print(f"Debug - Error type: {type(e)}")
        print("=== TOKEN CREATION FAILED ===\n")
        raise 