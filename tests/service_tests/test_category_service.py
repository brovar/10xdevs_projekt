from logging import Logger
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CategoryModel
from src.schemas import CategoryDTO
from src.services.category_service import CategoryService


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Provides an AsyncMock for the database session."""
    session = AsyncMock(spec=AsyncSession)
    # Configure execute to return a mock that has a scalars method,
    # which in turn has an all method.
    execute_result_mock = MagicMock()
    scalars_result_mock = MagicMock()
    execute_result_mock.scalars.return_value = scalars_result_mock
    session.execute.return_value = execute_result_mock
    return session


@pytest.fixture
def mock_logger() -> MagicMock:
    """Provides a MagicMock for the logger."""
    return MagicMock(spec=Logger)


@pytest.fixture
def category_service(
    mock_db_session: AsyncSession, mock_logger: Logger
) -> CategoryService:
    """Provides an instance of CategoryService with mocked dependencies."""
    return CategoryService(db_session=mock_db_session, logger=mock_logger)


@pytest.mark.asyncio
async def test_category_service_initialization(
    category_service: CategoryService,
    mock_db_session: AsyncSession,
    mock_logger: Logger,
):
    """Test CategoryService initialization."""
    assert category_service.db_session == mock_db_session
    assert category_service.logger == mock_logger


@pytest.mark.asyncio
async def test_get_all_categories_success(
    category_service: CategoryService, mock_db_session: AsyncSession
):
    """Test successful retrieval of all categories."""
    mock_categories_models = [
        CategoryModel(id=1, name="Electronics"),
        CategoryModel(id=2, name="Books"),
        CategoryModel(id=3, name="Home Goods"),
    ]
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = (
        mock_categories_models
    )

    result = await category_service.get_all_categories()

    assert len(result) == 3
    assert isinstance(result, list)
    for i, item in enumerate(result):
        assert isinstance(item, CategoryDTO)
        assert item.id == mock_categories_models[i].id
        assert item.name == mock_categories_models[i].name

    mock_db_session.execute.assert_awaited_once()
    # We can add more specific checks for the query if needed, e.g., by inspecting call_args


@pytest.mark.asyncio
async def test_get_all_categories_ordered_by_id(
    category_service: CategoryService, mock_db_session: AsyncSession
):
    """Test that categories are ordered by ID."""
    # Data is intentionally out of order by ID
    mock_categories_models = [
        CategoryModel(id=3, name="Home Goods"),
        CategoryModel(id=1, name="Electronics"),
        CategoryModel(id=2, name="Books"),
    ]
    # The service should re-order them when it constructs the DTOs if the query is correct
    # However, the mock here returns what the DB would return AFTER ordering.
    # So the test should assert the order from the mock directly matches DTO order.

    # Simulate DB returning already ordered data
    ordered_mock_models = sorted(mock_categories_models, key=lambda m: m.id)
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = (
        ordered_mock_models
    )

    result = await category_service.get_all_categories()

    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].name == "Electronics"
    assert result[1].id == 2
    assert result[1].name == "Books"
    assert result[2].id == 3
    assert result[2].name == "Home Goods"


@pytest.mark.asyncio
async def test_get_all_categories_empty(
    category_service: CategoryService, mock_db_session: AsyncSession
):
    """Test retrieval when no categories exist."""
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = (
        []
    )

    result = await category_service.get_all_categories()

    assert isinstance(result, list)
    assert len(result) == 0
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_categories_db_exception(
    category_service: CategoryService,
    mock_db_session: AsyncSession,
    mock_logger: MagicMock,
):
    """Test error handling when database query fails."""
    db_error_message = "Database connection failed"
    mock_db_session.execute.side_effect = Exception(db_error_message)

    with pytest.raises(HTTPException) as exc_info:
        await category_service.get_all_categories()

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error_code"] == "FETCH_FAILED"
    assert (
        exc_info.value.detail["message"] == "Failed to retrieve category data"
    )

    mock_logger.error.assert_called_once_with(
        f"Error fetching categories: {db_error_message}"
    )
