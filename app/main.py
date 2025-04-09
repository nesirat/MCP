from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, Response, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse, HTMLResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, case
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import json
import secrets
from pydantic import BaseModel, EmailStr, constr
import re
from pydantic import field_validator
import logging
import os
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.compression import CompressionMiddleware
from fastapi.middleware.http2 import HTTP2Middleware
import uvicorn

from .core.config import settings
from .db.database import SessionLocal, engine, get_db, init_db
from .db import models
from .collectors.bsi_collector import BSICollector
from .collectors.nvd_collector import NVDCollector
from .collectors.mitre_collector import MITRECollector
from .core.security import verify_password, get_password_hash, get_current_user
from .auth.auth import router as auth_router
from .core.security.tokens import TokenManager
from .core.logging import logger
from .routers import dashboard, tickets, auth, api_keys, alerts, notifications, analytics, versioning
from .core.middleware import APIUsageMiddleware, SecurityMiddleware, RateLimitHeadersMiddleware
from .core.middleware.versioning import VersioningMiddleware
from .services.notification import NotificationService
from .middleware.cache import CacheMiddleware
from .core.tasks import celery
from .api.v1.api import api_router
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.api_key import APIKeyMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
init_db()

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=settings.API_DOCS_URL,
    redoc_url=settings.API_REDOC_URL,
    openapi_url=settings.API_OPENAPI_URL,
    contact=settings.API_CONTACT,
    license_info=settings.API_LICENSE,
    terms_of_service=settings.API_TERMS_OF_SERVICE
)

# Add middleware
versioning_middleware = VersioningMiddleware(app)
app.add_middleware(APIUsageMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="/app/app/templates")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Add cache middleware
app.add_middleware(CacheMiddleware)

# Add compression middleware
app.add_middleware(CompressionMiddleware)

# Add HTTP/2 middleware
app.add_middleware(HTTP2Middleware)

# Add rate limit middleware
app.add_middleware(RateLimitMiddleware)

# Add API key middleware
app.add_middleware(APIKeyMiddleware)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

# Password validation regex
PASSWORD_REGEX = re.compile(r'^.{4,}$')  # Just require 4 or more characters for testing

# Initialize token manager
token_manager = TokenManager(settings.SECRET_KEY)

# Store versioning middleware in app state for access in routes
app.state.versioning_middleware = versioning_middleware

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(tickets.router, prefix="/api/v1", tags=["tickets"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(api_keys.router, prefix="/api/api-keys", tags=["api-keys"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(versioning.router, prefix="/api/versioning", tags=["versioning"])

# Initialize notification service
notification_service = NotificationService()

# Add notification service to app state
app.state.notification_service = notification_service

def create_access_token(data: dict, remember_me: bool = False):
    print(f"\n=== TOKEN CREATION START ===")
    print(f"Debug - Creating token with data: {data}")
    
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
        return encoded_jwt  # Return without Bearer prefix
    except Exception as e:
        print(f"Debug - Error creating token: {str(e)}")
        print("=== TOKEN CREATION FAILED ===\n")
        raise

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "settings": settings}
    )

@app.get("/login")
async def login_page(request: Request):
    """Login page"""
    logger.info("Login page accessed")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "settings": settings}
    )

@app.post("/token")
async def login_for_access_token(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    remember: str = Form(default="false"),  # Handle remember separately
    db: Session = Depends(get_db)
):
    print("\n=== DETAILED LOGIN ATTEMPT LOG ===")
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    print(f"Request Headers: {dict(request.headers)}")
    print(f"Request Cookies: {request.cookies}")
    print(f"Form Data: username={username}, password=***, remember={remember}")
    
    # Convert remember string to boolean
    remember_bool = remember.lower() == "true"
    
    try:
        # Get user from database
        user = db.query(models.User).filter(models.User.email == username).first()
        print(f"User found: {user is not None}")
        if not user:
            print("User not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        print("Verifying password...")
        if not verify_password(password, user.hashed_password):
            print("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print("Password verified successfully")
        
        # Create access token
        print(f"Creating access token with remember={remember_bool}")
        access_token = create_access_token(
            data={"sub": user.email},
            remember_me=remember_bool
        )
        print(f"Access token created successfully, length: {len(access_token)}")
        
        # Update last login
        print("Updating last login time")
        user.last_login = datetime.utcnow()
        db.commit()
        print("Last login time updated")
        
        # Set cookie
        print(f"Setting cookie with remember={remember_bool}")
        max_age = 30 * 24 * 60 * 60 if remember_bool else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        print(f"Cookie max_age: {max_age} seconds")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=max_age
        )
        print("Cookie set successfully")
        
        print("=== LOGIN SUCCESSFUL ===")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error during login: {str(e)}")
        print(f"Error type: {type(e)}")
        raise

@app.get("/vulnerabilities/", response_model=List[dict])
async def get_vulnerabilities(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    query = db.query(models.Vulnerability)
    
    if severity:
        query = query.filter(models.Vulnerability.severity == severity)
    if source:
        query = query.filter(models.Vulnerability.source == source)
    if search:
        search_filter = or_(
            models.Vulnerability.title.ilike(f"%{search}%"),
            models.Vulnerability.description.ilike(f"%{search}%"),
            models.Vulnerability.cve_id.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    vulnerabilities = query.offset(skip).limit(limit).all()
    return [
        {
            "id": v.id,
            "cve_id": v.cve_id,
            "title": v.title,
            "description": v.description,
            "severity": v.severity,
            "cvss_score": v.cvss_score,
            "published_date": v.published_date,
            "last_modified_date": v.last_modified_date,
            "source": v.source,
            "references": v.references
        }
        for v in vulnerabilities
    ]

@app.get("/vulnerabilities/{cve_id}", response_model=dict)
async def get_vulnerability(
    cve_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    vulnerability = db.query(models.Vulnerability).filter(models.Vulnerability.cve_id == cve_id).first()
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return {
        "id": vulnerability.id,
        "cve_id": vulnerability.cve_id,
        "title": vulnerability.title,
        "description": vulnerability.description,
        "severity": vulnerability.severity,
        "cvss_score": vulnerability.cvss_score,
        "published_date": vulnerability.published_date,
        "last_modified_date": vulnerability.last_modified_date,
        "source": vulnerability.source,
        "references": vulnerability.references
    }

@app.post("/collect/bsi")
async def collect_bsi_data(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    collector = BSICollector()
    vulnerabilities = await collector.collect_vulnerabilities()
    
    for vuln_data in vulnerabilities:
        db_vuln = models.Vulnerability(**vuln_data)
        db.add(db_vuln)
    
    try:
        db.commit()
        return {"message": f"Successfully collected {len(vulnerabilities)} vulnerabilities"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collect/nvd")
async def collect_nvd_data(
    days_back: int = Query(7, ge=1, le=120),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    collector = NVDCollector()
    vulnerabilities = await collector.collect_vulnerabilities(days_back)
    
    for vuln_data in vulnerabilities:
        db_vuln = models.Vulnerability(**vuln_data)
        db.add(db_vuln)
    
    try:
        db.commit()
        return {"message": f"Successfully collected {len(vulnerabilities)} vulnerabilities"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collect/mitre")
async def collect_mitre_data(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    collector = MITRECollector()
    vulnerabilities = await collector.collect_vulnerabilities(limit)
    
    for vuln_data in vulnerabilities:
        db_vuln = models.Vulnerability(**vuln_data)
        db.add(db_vuln)
    
    try:
        db.commit()
        return {"message": f"Successfully collected {len(vulnerabilities)} vulnerabilities"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_vulnerability_stats(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Basic vulnerability stats
    total_vulns = db.query(models.Vulnerability).count()
    severity_counts = db.query(
        models.Vulnerability.severity,
        func.count(models.Vulnerability.id)
    ).group_by(models.Vulnerability.severity).all()
    
    source_counts = db.query(
        models.Vulnerability.source,
        func.count(models.Vulnerability.id)
    ).group_by(models.Vulnerability.source).all()
    
    # Monthly trends
    monthly_trends = db.query(
        func.date_trunc('month', models.Vulnerability.last_modified_date).label('month'),
        func.count(models.Vulnerability.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # API usage stats
    api_usage = db.query(
        models.APIKeyUsage.key_id,
        func.count(models.APIKeyUsage.id).label('total_requests'),
        func.avg(models.APIKeyUsage.response_time).label('avg_response_time'),
        func.count(case((models.APIKeyUsage.status_code >= 400, 1))).label('error_count')
    ).group_by(models.APIKeyUsage.key_id).all()
    
    # User activity stats
    user_activity = db.query(
        models.User.id,
        models.User.email,
        func.count(models.Ticket.id).label('ticket_count'),
        func.count(models.APIKey.id).label('api_key_count'),
        func.max(models.User.last_login).label('last_login')
    ).outerjoin(models.Ticket).outerjoin(models.APIKey).group_by(models.User.id, models.User.email).all()
    
    return {
        "total_vulnerabilities": total_vulns,
        "severity_distribution": dict(severity_counts),
        "source_distribution": dict(source_counts),
        "monthly_trends": [
            {
                "month": trend.month.strftime("%Y-%m"),
                "count": trend.count
            }
            for trend in monthly_trends
        ],
        "api_usage": [
            {
                "key_id": usage.key_id,
                "total_requests": usage.total_requests,
                "avg_response_time": float(usage.avg_response_time) if usage.avg_response_time else 0,
                "error_count": usage.error_count
            }
            for usage in api_usage
        ],
        "user_activity": [
            {
                "user_id": activity.id,
                "email": activity.email,
                "ticket_count": activity.ticket_count,
                "api_key_count": activity.api_key_count,
                "last_login": activity.last_login.isoformat() if activity.last_login else None
            }
            for activity in user_activity
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "cache_enabled": settings.CACHE_ENABLED,
        "compression_enabled": settings.COMPRESSION_ENABLED,
        "celery_connected": celery.connection().connected
    }

@app.get("/events")
async def events(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Server-Sent Events endpoint for real-time updates
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            # Get latest vulnerabilities
            db = next(SessionLocal())
            vulnerabilities = db.query(models.Vulnerability).order_by(models.Vulnerability.last_modified_date.desc()).limit(10).all()
            
            # Convert to list of dictionaries
            vuln_list = [
                {
                    "id": v.id,
                    "cve_id": v.cve_id,
                    "title": v.title,
                    "description": v.description,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                    "published_date": v.published_date,
                    "last_modified_date": v.last_modified_date,
                    "source": v.source,
                    "references": v.references
                }
                for v in vulnerabilities
            ]
            
            yield f"data: {json.dumps(vuln_list)}\n\n"
            await asyncio.sleep(30)  # Update every 30 seconds
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/v1/messages")
async def post_message(
    message: dict,
    token: str = Depends(oauth2_scheme)
):
    """
    Endpoint for receiving messages from the client
    """
    # Here you can process the message and trigger appropriate actions
    # For example, you could trigger a vulnerability collection
    if message.get("type") == "collect":
        collector = NVDCollector()
        vulnerabilities = await collector.collect_vulnerabilities(days_back=7)
        
        db = next(SessionLocal())
        for vuln_data in vulnerabilities:
            db_vuln = models.Vulnerability(**vuln_data)
            db.add(db_vuln)
        
        try:
            db.commit()
            return {"message": f"Successfully collected {len(vulnerabilities)} vulnerabilities"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": "Message received"}

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', v):
            raise ValueError('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character')
        return v

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    key: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True

class APIKeyUsage(BaseModel):
    key_id: int
    endpoint: str
    timestamp: datetime
    status_code: int
    response_time: float

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/dashboard")
async def dashboard_page(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "settings": settings,
            "user": current_user
        }
    )

@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Admin routes
@app.get("/admin/users", response_model=List[dict])
async def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    users = db.query(models.User).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "api_key_count": len(user.api_keys),
            "ticket_count": len(user.tickets)
        }
        for user in users
    ]

@app.get("/admin/api-keys", response_model=List[dict])
async def get_all_api_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    api_keys = db.query(models.APIKey).all()
    return [
        {
            "id": key.id,
            "user_email": key.user.email,
            "name": key.name,
            "description": key.description,
            "is_active": key.is_active,
            "created_at": key.created_at,
            "last_used": key.last_used,
            "usage_count": key.usage_count
        }
        for key in api_keys
    ]

@app.get("/admin/tickets", response_model=List[dict])
async def get_all_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    
    tickets = query.order_by(models.Ticket.created_at.desc()).all()
    return [
        {
            "id": ticket.id,
            "user_email": ticket.user.email,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "response_count": len(ticket.responses)
        }
        for ticket in tickets
    ]

@app.get("/admin/tickets/{ticket_id}", response_model=dict)
async def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {
        "id": ticket.id,
        "user_email": ticket.user.email,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "responses": [
            {
                "id": response.id,
                "message": response.message,
                "created_at": response.created_at,
                "is_admin": response.is_admin,
                "user_email": response.user.email
            }
            for response in ticket.responses
        ]
    }

@app.post("/admin/tickets/{ticket_id}/respond")
async def respond_to_ticket(
    ticket_id: int,
    message: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    response = models.TicketResponse(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=message,
        is_admin=True
    )
    db.add(response)
    db.commit()
    
    return {"message": "Response added successfully"}

@app.put("/admin/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    status: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin features"
        )
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = status
    db.commit()
    
    return {"message": "Ticket status updated successfully"}

# Customer ticket routes
@app.post("/tickets", response_model=dict)
async def create_ticket(
    subject: str = Body(...),
    description: str = Body(...),
    priority: str = Body("medium"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = models.Ticket(
        user_id=current_user.id,
        subject=subject,
        description=description,
        priority=priority
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "created_at": ticket.created_at
    }

@app.get("/tickets", response_model=List[dict])
async def get_user_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tickets = db.query(models.Ticket).filter(
        models.Ticket.user_id == current_user.id
    ).order_by(models.Ticket.created_at.desc()).all()
    
    return [
        {
            "id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "response_count": len(ticket.responses)
        }
        for ticket in tickets
    ]

@app.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "responses": [
            {
                "id": response.id,
                "message": response.message,
                "created_at": response.created_at,
                "is_admin": response.is_admin
            }
            for response in ticket.responses
        ]
    }

@app.post("/tickets/{ticket_id}/respond")
async def respond_to_ticket_user(
    ticket_id: int,
    message: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    response = models.TicketResponse(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=message,
        is_admin=False
    )
    db.add(response)
    db.commit()
    
    return {"message": "Response added successfully"}

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    newsletter_subscribed: Optional[bool] = None
    email_frequency: Optional[str] = None

@app.post("/profile", response_model=dict)
async def update_profile(
    profile: UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        # Update only provided fields
        for field, value in profile.model_dump(exclude_unset=True).items():
            setattr(current_user, field, value)
        
        db.commit()
        return {"message": "Profile updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/profile")
async def profile_page(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """Display user profile page"""
    context = {
        "request": request,
        "user": current_user
    }
    return templates.TemplateResponse("profile.html", context)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login-page", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@app.get("/tickets")
async def tickets_page(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """Display the tickets list page"""
    return templates.TemplateResponse(
        "tickets/list.html",
        {"request": request, "user": current_user}
    )

@app.get("/tickets/{ticket_id}")
async def ticket_detail_page(
    request: Request,
    ticket_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Display the ticket detail page"""
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return templates.TemplateResponse(
        "tickets/detail.html",
        {
            "request": request,
            "user": current_user,
            "ticket": ticket,
            "get_status_color": lambda status: {
                "open": "primary",
                "in_progress": "warning",
                "resolved": "success",
                "closed": "secondary"
            }.get(status, "secondary"),
            "get_priority_color": lambda priority: {
                "low": "info",
                "medium": "primary",
                "high": "warning",
                "critical": "danger"
            }.get(priority, "secondary"),
            "format_date": lambda date: date.strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
        contact=settings.API_CONTACT,
        license_info=settings.API_LICENSE,
        terms_of_service=settings.API_TERMS_OF_SERVICE,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add security requirements
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add API version information
    openapi_schema["info"]["x-api-version"] = settings.CURRENT_API_VERSION
    openapi_schema["info"]["x-supported-versions"] = settings.SUPPORTED_API_VERSIONS
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Custom docs endpoints
@app.get(settings.API_DOCS_URL, include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=settings.API_OPENAPI_URL,
        title=f"{settings.API_TITLE} - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Welcome to MCP API",
        "docs_url": settings.API_DOCS_URL,
        "redoc_url": settings.API_REDOC_URL,
        "openapi_url": settings.API_OPENAPI_URL,
        "current_version": settings.CURRENT_API_VERSION,
        "supported_versions": settings.SUPPORTED_API_VERSIONS,
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        http="h11",  # Use h11 for HTTP/1.1
        # For HTTP/2 support, use:
        # http="h2",
        # ssl_keyfile="path/to/key.pem",
        # ssl_certfile="path/to/cert.pem"
    ) 