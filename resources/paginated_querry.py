from typing import Optional, Type
from sqlalchemy.orm.session import Session
from sqlalchemy import select
from sqlalchemy.ext.declarative import DeclarativeMeta

def paginated_query(db: Session,model: Type[DeclarativeMeta], limit: int,cursor: Optional[int] = None,
    filters: Optional[list] = None, order_by_field = None):
    """Executes a generic paginated query on a SQLAlchemy model.
        db (Session): SQLAlchemy database session.
        model (Type[DeclarativeMeta]): SQLAlchemy model class to query.
        limit (int): Maximum number of items to return.
        cursor (Optional[int], optional): The value of the last seen item's ordering field (for pagination). Defaults to None.
        filters (Optional[list], optional): List of SQLAlchemy filter conditions to apply. Defaults to None.
        order_by_field (optional): SQLAlchemy field to order results by. Defaults to model.id.
        dict: {
            "results": List of model instances up to the specified limit,
            "next_cursor": The value of the ordering field for the next page, or None if no more results,
            "has_more": Boolean indicating if there are more results beyond the current page
    Notes:
        - Assumes the ordering field is unique and can be used as a cursor.
        - Fetches one extra record to determine if there are more results. """
    filters = filters or []
    order_by_field = order_by_field or model.id
    if cursor:
        filters.append(order_by_field > cursor)
    stmt = select(model).where(*filters).order_by(order_by_field).limit(limit + 1)
    results = db.scalar(stmt).all()
    has_more = len(results) > limit
    next_cursor = results[-1].id if has_more else None
    return {
        "results": results[:limit],
        "next_cursor": next_cursor,
        "has_more": has_more
    }

def paginate_live_search(results: list, limit: int,cursor: Optional[int] = None):
    """Paginates a list of search results using a cursor-based approach.
    Args:
        results (list): The complete list of search results.
        limit (int): Maximum number of items to return.
        cursor (Optional[int], optional): The index to start pagination from. Defaults to None.
    Returns:
        dict: {
            "results": List of items up to the specified limit,
            "next_cursor": The index for the next page, or None if no more results,
            "has_more": Boolean indicating if there are more results beyond the current page
    Notes:
        - Uses list slicing for pagination.
        - Calculates the next cursor based on the current position and limit. """
    start = cursor or 0
    end = start + limit
    paginated_results = results[start:end]
    has_more = end < len(results)
    next_cursor = end if has_more else None
    return {
        "results": paginated_results,
        "next_cursor": next_cursor,
        "has_more": has_more
    }