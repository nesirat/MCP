from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.db.health import DatabaseHealth
from typing import Dict, Any

router = APIRouter()


@router.get("/database/connection", response_model=Dict[str, Any])
async def check_database_connection(db: Session = Depends(get_db_session)):
    """
    Check database connection health.
    """
    return DatabaseHealth.check_connection(db)


@router.get("/database/performance", response_model=Dict[str, Any])
async def get_database_performance(db: Session = Depends(get_db_session)):
    """
    Get database performance metrics.
    """
    return DatabaseHealth.get_performance_metrics(db)


@router.get("/database/pool", response_model=Dict[str, Any])
async def get_connection_pool_stats():
    """
    Get connection pool statistics.
    """
    return DatabaseHealth.get_connection_pool_stats() 