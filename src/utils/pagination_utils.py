from typing import List, TypeVar

from schemas import PaginatedResponse

T = TypeVar("T")


def build_paginated_response(
    items: List[T], total: int, page: int, limit: int
) -> PaginatedResponse:
    """
    Build a generic paginated response.

    Args:
        items: List of items in the current page
        total: Total number of items matching the query
        page: Current page number
        limit: Number of items per page

    Returns:
        PaginatedResponse with items, total, page, limit, pages
    """
    pages = (total + limit - 1) // limit if total > 0 else 0
    return PaginatedResponse(
        items=items, total=total, page=page, limit=limit, pages=pages
    )
