from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.ticket_comment import TicketComment
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    Ticket,
    TicketCommentCreate,
    TicketComment,
    TicketList
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("", response_model=Ticket)
async def create_ticket(
    ticket: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ticket"""
    db_ticket = Ticket(
        user_id=current_user.id,
        subject=ticket.subject,
        description=ticket.description,
        priority=ticket.priority,
        status=TicketStatus.OPEN
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("", response_model=TicketList)
async def list_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tickets with optional filtering"""
    query = db.query(Ticket).filter(Ticket.user_id == current_user.id)
    
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return TicketList(
        tickets=tickets,
        total=total,
        page=page,
        size=size
    )

@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific ticket"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket

@router.put("/{ticket_id}", response_model=Ticket)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a ticket"""
    db_ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == current_user.id
    ).first()
    
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    for field, value in ticket_update.model_dump(exclude_unset=True).items():
        setattr(db_ticket, field, value)
    
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.post("/{ticket_id}/comments", response_model=TicketComment)
async def add_comment(
    ticket_id: int,
    comment: TicketCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a ticket"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    db_comment = TicketComment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=comment.message,
        is_admin=current_user.is_admin
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/{ticket_id}/comments", response_model=List[TicketComment])
async def list_comments(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List comments for a ticket"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket.comments 