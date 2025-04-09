from typing import List, Optional, Union, Any
from sqlalchemy.orm import Query, Session
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta


class QueryOptimizer:
    @staticmethod
    def apply_pagination(
        query: Query,
        skip: int = 0,
        limit: int = 100,
        max_limit: int = 1000
    ) -> Query:
        """
        Apply pagination to a query with safety limits.
        """
        if limit > max_limit:
            limit = max_limit
        return query.offset(skip).limit(limit)

    @staticmethod
    def apply_ordering(
        query: Query,
        order_by: Optional[str] = None,
        order_direction: str = "desc"
    ) -> Query:
        """
        Apply ordering to a query.
        """
        if not order_by:
            return query

        column = getattr(query.column_descriptions[0]["entity"], order_by, None)
        if not column:
            return query

        if order_direction.lower() == "desc":
            return query.order_by(desc(column))
        return query.order_by(asc(column))

    @staticmethod
    def apply_filters(
        query: Query,
        filters: dict,
        model: Any
    ) -> Query:
        """
        Apply filters to a query.
        """
        for field, value in filters.items():
            if value is not None:
                column = getattr(model, field, None)
                if column is not None:
                    if isinstance(value, (list, tuple)):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        return query

    @staticmethod
    def apply_date_range(
        query: Query,
        date_field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Query:
        """
        Apply date range filtering to a query.
        """
        if start_date:
            query = query.filter(getattr(query.column_descriptions[0]["entity"], date_field) >= start_date)
        if end_date:
            query = query.filter(getattr(query.column_descriptions[0]["entity"], date_field) <= end_date)
        return query

    @staticmethod
    def apply_search(
        query: Query,
        search_fields: List[str],
        search_term: Optional[str] = None
    ) -> Query:
        """
        Apply search filtering to a query.
        """
        if not search_term:
            return query

        search_conditions = []
        for field in search_fields:
            column = getattr(query.column_descriptions[0]["entity"], field, None)
            if column is not None:
                search_conditions.append(column.ilike(f"%{search_term}%"))

        if search_conditions:
            query = query.filter(func.or_(*search_conditions))
        return query

    @staticmethod
    def get_count(query: Query) -> int:
        """
        Get the count of records efficiently.
        """
        return query.with_entities(func.count()).scalar()

    @staticmethod
    def get_stats(
        query: Query,
        group_by: str,
        count_field: str = "id"
    ) -> List[dict]:
        """
        Get statistics grouped by a field.
        """
        return query.with_entities(
            getattr(query.column_descriptions[0]["entity"], group_by),
            func.count(getattr(query.column_descriptions[0]["entity"], count_field))
        ).group_by(group_by).all()

    @staticmethod
    def bulk_insert(
        session: Session,
        model: Any,
        data: List[dict],
        batch_size: int = 1000
    ) -> None:
        """
        Perform efficient bulk insert operations.
        """
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            session.bulk_insert_mappings(model, batch)
            session.commit() 