from logging import Logger
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import CategoryModel
from src.schemas import CategoryDTO


class CategoryService:
    def __init__(self, db_session: AsyncSession, logger: Optional[Logger] = None):
        self.db_session = db_session
        self.logger = logger

    async def list_categories(self) -> List[CategoryDTO]:
        """
        Fetch all categories from the database.

        Returns:
            List[CategoryDTO]: List of category objects with id and name

        Raises:
            Exception: If there's an error fetching categories
        """
        # Query all categories ordered by id
        result = await self.db_session.execute(
            select(CategoryModel).order_by(CategoryModel.id)
        )
        categories = result.scalars().all()

        # Convert to DTOs
        return [
            CategoryDTO(id=category.id, name=category.name)
            for category in categories
        ]

    async def get_all_categories(self) -> List[CategoryDTO]:
        """
        Fetch all categories from the database. (Kept for backward compatibility)

        Returns:
            List[CategoryDTO]: List of category objects with id and name

        Raises:
            HTTPException: 500 if there's an error fetching categories
        """
        try:
            return await self.list_categories()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching categories: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to retrieve category data",
                },
            )
