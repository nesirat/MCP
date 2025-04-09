from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import time
from app.db.session import engine


class DatabaseHealth:
    @staticmethod
    def check_connection(session: Session) -> Dict[str, Any]:
        """
        Check database connection health.
        """
        start_time = time.time()
        try:
            # Execute a simple query to check connection
            session.execute(text("SELECT 1"))
            connection_time = time.time() - start_time

            # Get connection pool stats
            pool = engine.pool
            return {
                "status": "healthy",
                "connection_time_ms": round(connection_time * 1000, 2),
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @staticmethod
    def get_performance_metrics(session: Session) -> Dict[str, Any]:
        """
        Get database performance metrics.
        """
        try:
            # Get query execution time statistics
            result = session.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                ORDER BY total_time DESC
                LIMIT 10
            """))
            
            slow_queries = [
                {
                    "query": row[0],
                    "calls": row[1],
                    "total_time_ms": round(row[2], 2),
                    "mean_time_ms": round(row[3], 2),
                    "rows": row[4]
                }
                for row in result
            ]

            # Get table statistics
            result = session.execute(text("""
                SELECT 
                    schemaname,
                    relname,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """))
            
            table_stats = [
                {
                    "schema": row[0],
                    "table": row[1],
                    "live_rows": row[2],
                    "dead_rows": row[3],
                    "last_vacuum": row[4].isoformat() if row[4] else None,
                    "last_analyze": row[5].isoformat() if row[5] else None
                }
                for row in result
            ]

            return {
                "status": "healthy",
                "slow_queries": slow_queries,
                "table_stats": table_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @staticmethod
    def get_connection_pool_stats() -> Dict[str, Any]:
        """
        Get detailed connection pool statistics.
        """
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "timeout": pool.timeout(),
            "recycle": pool._recycle,
            "max_overflow": pool._max_overflow,
            "pool_size": pool._pool.size,
            "timestamp": datetime.utcnow().isoformat()
        } 