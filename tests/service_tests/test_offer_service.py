import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from decimal import Decimal
from typing import Optional, Type, Any, Callable, Awaitable
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, AsyncResult
from sqlalchemy.engine.result import ScalarResult
from fastapi import HTTPException, UploadFile, BackgroundTasks
from logging import Logger

from src.services.offer_service import OfferService
from src.services.file_service import FileService
from src.services.log_service import LogService
from src.schemas import OfferStatus, LogEventType, OfferSummaryDTO, UserRole, OfferListResponse
from src.models import OfferModel, CategoryModel, UserModel
from src.exceptions.offer_exceptions import OfferNotFoundException, NotOfferOwnerException, InvalidStatusTransitionException, OfferAlreadyInactiveException, OfferModificationFailedException, OfferAlreadySoldException
from src.utils.pagination_utils import build_paginated_response
from sqlalchemy import or_

# Helper function for testing exceptions
async def assert_raises_exception(
    func: Callable[[], Awaitable[Any]],
    expected_exception: Type[Exception],
    check_exception_attributes: Optional[dict] = None
) -> None:
    """
    Helper function to assert that a coroutine raises a specific exception.
    
    Args:
        func: Async function to call
        expected_exception: The exception type expected to be raised
        check_exception_attributes: Optional dict of attribute names and expected values
    """
    try:
        await func()
        assert False, f"Expected {expected_exception.__name__} was not raised"
    except Exception as e:
        assert isinstance(e, expected_exception), f"Expected {expected_exception.__name__}, got {type(e).__name__}"
        
        if check_exception_attributes:
            for attr_name, expected_value in check_exception_attributes.items():
                if attr_name == 'message':
                    # Special case for checking the exception message
                    assert expected_value in str(e), f"Expected '{expected_value}' in exception message, got '{str(e)}'"
                else:
                    assert hasattr(e, attr_name), f"Exception does not have attribute '{attr_name}'"
                    actual_value = getattr(e, attr_name)
                    assert actual_value == expected_value, f"Expected {attr_name}='{expected_value}', got '{actual_value}'"

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    # Configure execute to return a mock that has a scalars method, which in turn has a first method.
    execute_result_mock = MagicMock() 
    scalars_result_mock = MagicMock()
    # Default for first() can be None or a specific object if most tests expect one.
    # Tests can override this per case.
    scalars_result_mock.first.return_value = None 
    execute_result_mock.scalars.return_value = scalars_result_mock
    session.execute.return_value = execute_result_mock

    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    # session.execute = AsyncMock() # Already configured above with more detail
    session.get = AsyncMock()
    return session

@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)

@pytest.fixture
def mock_file_service():
    service = MagicMock(spec=FileService)
    service.save_image = AsyncMock(return_value="test_image.jpg")
    return service

@pytest.fixture
def mock_log_service():
    service = MagicMock(spec=LogService)
    service.create_log = AsyncMock()
    return service

@pytest.fixture
@patch('src.services.offer_service.FileService', new_callable=MagicMock)
@patch('src.services.offer_service.LogService', new_callable=MagicMock)
def offer_service(MockLogService, MockFileService, mock_db_session, mock_logger):
    # Instance the mock services
    mock_fs_instance = MockFileService.return_value
    mock_ls_instance = MockLogService.return_value

    # Configure their async methods if any are called directly in OfferService init or methods
    mock_fs_instance.save_image = AsyncMock(return_value="test_image.jpg")
    mock_ls_instance.create_log = AsyncMock()

    service = OfferService(db_session=mock_db_session, logger=mock_logger)
    # Replace the auto-created instances with our specific mocks if needed,
    # or ensure OfferService uses the passed-in instances correctly.
    # For OfferService, it creates its own FileService and LogService instances.
    # So we need to patch where it looks for them.
    service.file_service = mock_fs_instance
    service.log_service = mock_ls_instance
    return service

@pytest.fixture
def mock_seller_user():
    user = UserModel(id=uuid4(), email="seller@example.com", role=UserRole.SELLER, status="ACTIVE")
    return user

@pytest.fixture
def mock_category():
    return CategoryModel(id=1, name="Test Category")

@pytest.fixture
def mock_upload_file():
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "test.jpg"
    upload_file.content_type = "image/jpeg"
    upload_file.read = AsyncMock(return_value=b"file_content")
    upload_file.seek = AsyncMock()
    return upload_file

@pytest.fixture
def mock_offer_model(mock_seller_user, mock_category):
    """Provides a mock OfferModel instance."""
    return OfferModel(
        id=uuid4(),
        seller_id=mock_seller_user.id,
        category_id=mock_category.id,
        title="Test Offer for Deactivation",
        description="A description",
        price=Decimal("99.99"),
        quantity=10,
        status=OfferStatus.ACTIVE,
        image_filename="test.jpg",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.mark.asyncio
async def test_offer_service_initialization(offer_service, mock_db_session, mock_logger):
    """Test OfferService initialization."""
    assert offer_service.db_session == mock_db_session
    assert offer_service.logger == mock_logger
    assert isinstance(offer_service.file_service, MagicMock) # Patched instance
    assert isinstance(offer_service.log_service, MagicMock)  # Patched instance

@pytest.mark.asyncio
async def test_create_offer_success_minimal(offer_service, mock_db_session, mock_seller_user, mock_category, mock_log_service, mock_file_service):
    """Test successful offer creation with minimal data."""
    seller_id = mock_seller_user.id
    title = "Minimal Test Offer"
    price = Decimal("10.99")
    category_id = mock_category.id
    quantity = 1
    description = None # Explicitly for clarity
    image_filename = None # Explicitly for clarity

    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_category

    def side_effect_add(instance_being_added: OfferModel):
        instance_being_added.id = uuid4()
        instance_being_added.created_at = datetime.now(timezone.utc)
        instance_being_added.updated_at = datetime.now(timezone.utc)
    mock_db_session.add.side_effect = side_effect_add
    mock_db_session.refresh = AsyncMock()

    result_dto = await offer_service.create_offer(
        seller_id=seller_id,
        title=title,
        price=price,
        category_id=category_id,
        quantity=quantity,
        description=description,
        image=None, # Corresponds to image_filename = None
        background_tasks=None
    )

    assert type(result_dto).__name__ == OfferSummaryDTO.__name__ # Check by class name
    assert result_dto.id is not None
    assert isinstance(result_dto.id, UUID)
    assert result_dto.created_at is not None
    assert isinstance(result_dto.created_at, datetime)
    assert result_dto.title == title
    assert result_dto.price == price
    assert result_dto.seller_id == seller_id
    assert result_dto.category_id == category_id
    assert result_dto.status == OfferStatus.INACTIVE
    assert result_dto.image_filename is None

    mock_db_session.commit.assert_awaited_once()
    offer_service.log_service.create_log.assert_awaited_once_with(
        event_type=LogEventType.OFFER_CREATE,
        user_id=seller_id,
        message=f"User {seller_id} created a new offer: {title}"
    )
    offer_service.file_service.save_image.assert_not_awaited()

    # Check that an OfferModel instance was added to the session
    mock_db_session.add.assert_called_once() # Assert it was called
    added_args, _ = mock_db_session.add.call_args
    added_instance = added_args[0]
    
    # Debugging isinstance issue for OfferModel
    # print(f"added_instance type: {type(added_instance)}, module: {getattr(type(added_instance), '__module__', 'N/A')}")
    # print(f"OfferModel type: {OfferModel}, module: {getattr(OfferModel, '__module__', 'N/A')}")

    # assert isinstance(added_instance, OfferModel) # Problematic
    assert type(added_instance).__name__ == OfferModel.__name__ # Check by class name
    assert added_instance.id == result_dto.id 
    assert added_instance.title == title
    assert added_instance.status == OfferStatus.INACTIVE

@pytest.mark.asyncio
async def test_create_offer_success_with_image(offer_service, mock_db_session, mock_seller_user, mock_category, mock_upload_file):
    """Test successful offer creation with an image."""
    seller_id = mock_seller_user.id
    title = "Image Test Offer"
    price = Decimal("25.50")
    category_id = mock_category.id
    quantity = 1 
    description = None
    expected_image_filename = "test_image.jpg"

    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_category
    offer_service.file_service.save_image.return_value = expected_image_filename

    def side_effect_add_img(instance_being_added: OfferModel):
        instance_being_added.id = uuid4()
        instance_being_added.created_at = datetime.now(timezone.utc)
        instance_being_added.updated_at = datetime.now(timezone.utc)
        # OfferService sets image_filename on OfferModel before add, 
        # so we don't need to set it here unless it's a DB-generated/modified name.
        # For this test, file_service.save_image mock handles the name.

    mock_db_session.add.side_effect = side_effect_add_img
    mock_db_session.refresh = AsyncMock()

    result_dto = await offer_service.create_offer(
        seller_id=seller_id,
        title=title,
        price=price,
        category_id=category_id,
        quantity=quantity,
        description=description,
        image=mock_upload_file
    )
    
    assert type(result_dto).__name__ == OfferSummaryDTO.__name__ # Check by class name
    assert result_dto.id is not None
    assert isinstance(result_dto.id, UUID)
    assert result_dto.created_at is not None
    assert isinstance(result_dto.created_at, datetime)
    assert result_dto.image_filename == expected_image_filename
    offer_service.file_service.save_image.assert_awaited_once_with(mock_upload_file)
    mock_db_session.commit.assert_awaited_once()
    offer_service.log_service.create_log.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_offer_invalid_price(offer_service, mock_seller_user, mock_category):
    """Test offer creation with invalid price (<=0)."""
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            seller_id=mock_seller_user.id,
            title="Invalid Price Offer",
            price=Decimal("0"),
            category_id=mock_category.id
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "INVALID_PRICE"
    offer_service.db_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_offer_invalid_quantity(offer_service, mock_seller_user, mock_category):
    """Test offer creation with invalid quantity (<0)."""
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            seller_id=mock_seller_user.id,
            title="Invalid Quantity Offer",
            price=Decimal("10"),
            category_id=mock_category.id,
            quantity=-1
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "INVALID_QUANTITY"
    offer_service.db_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_offer_category_not_found(offer_service, mock_db_session, mock_seller_user):
    """Test offer creation with a non-existent category ID."""
    # Simulate category not found
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            seller_id=mock_seller_user.id,
            title="Category Not Found Offer",
            price=Decimal("10"),
            category_id=999 # Non-existent
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["error_code"] == "CATEGORY_NOT_FOUND"
    offer_service.db_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_offer_db_commit_exception(offer_service, mock_db_session, mock_seller_user, mock_category):
    """Test offer creation when database commit fails."""
    # Mock DB calls for category fetch
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_category
    mock_db_session.commit.side_effect = Exception("DB commit error")

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            seller_id=mock_seller_user.id,
            title="DB Commit Fail Offer",
            price=Decimal("10"),
            category_id=mock_category.id
        )
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error_code"] == "CREATE_FAILED"
    offer_service.db_session.rollback.assert_awaited_once() # Should be called once for the main try-except

@pytest.mark.asyncio
async def test_create_offer_file_service_exception(offer_service, mock_db_session, mock_seller_user, mock_category, mock_upload_file):
    """Test offer creation when FileService.save_image fails."""
    # Mock DB calls for category fetch
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_category
    offer_service.file_service.save_image.side_effect = Exception("File save error")

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            seller_id=mock_seller_user.id,
            title="File Save Fail Offer",
            price=Decimal("10"),
            category_id=mock_category.id,
            image=mock_upload_file
        )
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error_code"] == "CREATE_FAILED"
    # Ensure rollback is called because the exception is caught by the generic Exception handler
    offer_service.db_session.rollback.assert_awaited_once() 

# --- Tests for deactivate_offer ---

@pytest.mark.asyncio
async def test_deactivate_offer_success(offer_service, mock_db_session, mock_seller_user, mock_offer_model, mock_category):
    """Test successful deactivation of an offer by its owner."""
    offer_to_deactivate = mock_offer_model
    offer_to_deactivate.status = OfferStatus.ACTIVE # Ensure it's active
    offer_to_deactivate.seller_id = mock_seller_user.id

    # Simplified side_effect for db.get
    mock_db_session.get.side_effect = [
        offer_to_deactivate, # For OfferModel
        mock_seller_user,    # For UserModel (seller)
        mock_category        # For CategoryModel
    ]

    result_dto = await offer_service.deactivate_offer(
        offer_id=offer_to_deactivate.id,
        user_id=mock_seller_user.id,
        user_role=UserRole.SELLER
    )

    assert result_dto.status == OfferStatus.INACTIVE
    assert offer_to_deactivate.status == OfferStatus.INACTIVE # Check model was updated
    assert result_dto.id == offer_to_deactivate.id
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_with(offer_to_deactivate)
    offer_service.log_service.create_log.assert_awaited_once_with(
        event_type=LogEventType.OFFER_STATUS_CHANGE,
        user_id=mock_seller_user.id,
        message=f"Offer {offer_to_deactivate.id} deactivated"
    )

@pytest.mark.asyncio
async def test_deactivate_offer_user_not_seller(offer_service, mock_offer_model):
    """Test deactivation attempt by a user who is not a seller."""
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.deactivate_offer(
            offer_id=mock_offer_model.id,
            user_id=uuid4(), # Some other user
            user_role=UserRole.BUYER # Non-seller role
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_code"] == "INSUFFICIENT_PERMISSIONS"

@pytest.mark.asyncio
async def test_deactivate_offer_not_found(offer_service, mock_db_session, mock_seller_user):
    """Test deactivation attempt for a non-existent offer."""
    # Re-define get to ensure it's a fresh mock
    mock_db_session.get = AsyncMock(return_value=None)

    # Use the helper function
    await assert_raises_exception(
        func=lambda: offer_service.deactivate_offer(
            offer_id=uuid4(),
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferNotFoundException
    )

@pytest.mark.asyncio
async def test_deactivate_offer_not_owner(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test deactivation attempt by a seller who is not the owner."""
    other_seller_id = uuid4()
    mock_offer_model.seller_id = other_seller_id
    mock_db_session.get.return_value = mock_offer_model

    await assert_raises_exception(
        func=lambda: offer_service.deactivate_offer(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=NotOfferOwnerException
    )

@pytest.mark.asyncio
async def test_deactivate_offer_already_inactive(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test deactivation attempt on an offer that is already inactive."""
    mock_offer_model.status = OfferStatus.INACTIVE
    mock_offer_model.seller_id = mock_seller_user.id
    mock_db_session.get.return_value = mock_offer_model

    await assert_raises_exception(
        func=lambda: offer_service.deactivate_offer(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferAlreadyInactiveException
    )

@pytest.mark.asyncio
async def test_deactivate_offer_invalid_status(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test deactivation attempt on an offer with a status that doesn't allow deactivation (e.g., SOLD)."""
    mock_offer_model.status = OfferStatus.SOLD
    mock_offer_model.seller_id = mock_seller_user.id
    mock_db_session.get.return_value = mock_offer_model

    await assert_raises_exception(
        func=lambda: offer_service.deactivate_offer(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=InvalidStatusTransitionException
    )

@pytest.mark.asyncio
async def test_deactivate_offer_db_commit_exception(offer_service, mock_db_session, mock_seller_user, mock_offer_model):
    """Test deactivation when database commit fails."""
    offer_to_deactivate = mock_offer_model
    offer_to_deactivate.status = OfferStatus.ACTIVE
    offer_to_deactivate.seller_id = mock_seller_user.id
    
    mock_db_session.get.return_value = offer_to_deactivate
    mock_db_session.commit.side_effect = Exception("DB commit error")

    await assert_raises_exception(
        func=lambda: offer_service.deactivate_offer(
            offer_id=offer_to_deactivate.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferModificationFailedException,
        check_exception_attributes={
            "operation": "deactivate",
            "message": "DB commit error"
        }
    )

# --- Tests for mark_offer_as_sold ---

@pytest.mark.asyncio
async def test_mark_offer_as_sold_success(offer_service, mock_db_session, mock_seller_user, mock_offer_model, mock_category):
    """Test successful marking of an offer as sold by its owner."""
    offer_to_sell = mock_offer_model
    offer_to_sell.status = OfferStatus.ACTIVE
    offer_to_sell.seller_id = mock_seller_user.id
    # initial_quantity = offer_to_sell.quantity # Not strictly needed for this simplified mock

    mock_db_session.get.side_effect = [
        offer_to_sell,
        mock_seller_user,
        mock_category
    ]

    result_dto = await offer_service.mark_offer_as_sold(
        offer_id=offer_to_sell.id,
        user_id=mock_seller_user.id,
        user_role=UserRole.SELLER
    )

    assert result_dto.status == OfferStatus.SOLD
    assert offer_to_sell.status == OfferStatus.SOLD
    assert offer_to_sell.quantity == 0
    assert result_dto.id == offer_to_sell.id
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_with(offer_to_sell)
    offer_service.log_service.create_log.assert_awaited_once_with(
        event_type=LogEventType.OFFER_STATUS_CHANGE,
        user_id=mock_seller_user.id,
        message=f"Offer {offer_to_sell.id} marked as sold"
    )

@pytest.mark.asyncio
async def test_mark_offer_as_sold_user_not_seller(offer_service, mock_offer_model):
    """Test marking as sold attempt by a user who is not a seller."""
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.mark_offer_as_sold(
            offer_id=mock_offer_model.id,
            user_id=uuid4(),
            user_role=UserRole.BUYER
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_code"] == "INSUFFICIENT_PERMISSIONS"

@pytest.mark.asyncio
async def test_mark_offer_as_sold_not_found(offer_service, mock_db_session, mock_seller_user):
    """Test marking a non-existent offer as sold."""
    # Re-define get to ensure it's a fresh mock
    mock_db_session.get = AsyncMock(return_value=None)
    
    await assert_raises_exception(
        func=lambda: offer_service.mark_offer_as_sold(
            offer_id=uuid4(),
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferNotFoundException
    )

@pytest.mark.asyncio
async def test_mark_offer_as_sold_not_owner(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test marking as sold by a seller who is not the owner."""
    other_seller_id = uuid4()
    mock_offer_model.seller_id = other_seller_id
    mock_db_session.get.return_value = mock_offer_model
    
    await assert_raises_exception(
        func=lambda: offer_service.mark_offer_as_sold(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=NotOfferOwnerException
    )

@pytest.mark.asyncio
async def test_mark_offer_as_sold_already_sold(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test marking as sold an offer that is already sold."""
    mock_offer_model.status = OfferStatus.SOLD
    mock_offer_model.seller_id = mock_seller_user.id
    mock_db_session.get.return_value = mock_offer_model
    
    await assert_raises_exception(
        func=lambda: offer_service.mark_offer_as_sold(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferAlreadySoldException
    )

@pytest.mark.asyncio
async def test_mark_offer_as_sold_invalid_status_archived(offer_service, mock_db_session, mock_offer_model, mock_seller_user):
    """Test marking as sold an offer that is archived (invalid transition)."""
    mock_offer_model.status = OfferStatus.ARCHIVED
    mock_offer_model.seller_id = mock_seller_user.id
    mock_db_session.get.return_value = mock_offer_model
    
    await assert_raises_exception(
        func=lambda: offer_service.mark_offer_as_sold(
            offer_id=mock_offer_model.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=InvalidStatusTransitionException
    )

@pytest.mark.asyncio
async def test_mark_offer_as_sold_db_commit_exception(offer_service, mock_db_session, mock_seller_user, mock_offer_model):
    """Test marking as sold when database commit fails."""
    offer_to_sell = mock_offer_model
    offer_to_sell.status = OfferStatus.ACTIVE
    offer_to_sell.seller_id = mock_seller_user.id
    
    mock_db_session.get.return_value = offer_to_sell
    mock_db_session.commit.side_effect = Exception("DB commit error")

    await assert_raises_exception(
        func=lambda: offer_service.mark_offer_as_sold(
            offer_id=offer_to_sell.id,
            user_id=mock_seller_user.id,
            user_role=UserRole.SELLER
        ),
        expected_exception=OfferModificationFailedException,
        check_exception_attributes={
            "operation": "mark_sold",
            "message": "DB commit error"
        }
    )

# --- Tests for list_all_offers ---

@pytest.mark.asyncio
async def test_list_all_offers_no_filters_default_sort(offer_service, mock_db_session, mock_offer_model):
    """Test listing all offers with no filters and default sorting."""
    offer1_id = uuid4()
    offer2_id = uuid4()
    # Make sure created_at are distinct for reliable sort assertion
    now = datetime.now(timezone.utc)
    offers_data = [
        OfferModel(id=offer1_id, title="Offer Alpha", created_at=now, seller_id=uuid4(), category_id=1, price=Decimal(10), quantity=1, status=OfferStatus.ACTIVE),
        OfferModel(id=offer2_id, title="Offer Beta", created_at=now - timedelta(hours=1), seller_id=uuid4(), category_id=2, price=Decimal(20), quantity=1, status=OfferStatus.INACTIVE)
    ]

    # Mock for count query
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = len(offers_data)

    # Mock for data query (scalars is now awaited)
    scalar_result = MagicMock()
    scalar_result.all.return_value = offers_data

    # Setup the mocks with the new flow
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=len(offers_data))),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]

    response = await offer_service.list_all_offers(page=1, limit=10)

    # Use direct attribute checks instead of isinstance
    assert hasattr(response, 'items')
    assert hasattr(response, 'total')
    assert hasattr(response, 'page')
    assert hasattr(response, 'limit')
    assert hasattr(response, 'pages')
    assert response.total == len(offers_data)
    assert len(response.items) == len(offers_data)
    assert str(response.items[0].id) == str(offer1_id) # Default sort is created_at_desc
    assert str(response.items[1].id) == str(offer2_id)
    assert response.page == 1
    assert response.limit == 10
    assert response.pages == 1

    # Check that execute was called twice (once for count, once for data)
    assert mock_db_session.execute.call_count == 2

@pytest.mark.asyncio
async def test_list_all_offers_with_search_filter(offer_service, mock_db_session):
    """Test listing offers with a search term."""
    search_term = "Alpha"
    # Mocking execute to simulate filtering
    filtered_offer = OfferModel(id=uuid4(), title="Offer Alpha", seller_id=uuid4(), category_id=1, price=Decimal(10), quantity=1, status=OfferStatus.ACTIVE, created_at=datetime.now(timezone.utc))
    
    # Setup scalar_result mock
    scalar_result = MagicMock()
    scalar_result.all.return_value = [filtered_offer]
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]

    response = await offer_service.list_all_offers(search=search_term)
    assert response.total == 1
    assert len(response.items) == 1
    assert search_term in response.items[0].title

@pytest.mark.asyncio
async def test_list_all_offers_with_category_filter(offer_service, mock_db_session):
    """Test listing offers filtered by category_id."""
    category_id_to_filter = 1
    filtered_offer_cat = OfferModel(id=uuid4(), title="Offer Cat1", seller_id=uuid4(), category_id=category_id_to_filter, price=Decimal(10), quantity=1, status=OfferStatus.ACTIVE, created_at=datetime.now(timezone.utc))

    # Setup scalar_result mock
    scalar_result = MagicMock()
    scalar_result.all.return_value = [filtered_offer_cat]
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]
    
    response = await offer_service.list_all_offers(category_id=category_id_to_filter)
    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].category_id == category_id_to_filter

@pytest.mark.asyncio
async def test_list_all_offers_with_status_filter(offer_service, mock_db_session):
    """Test listing offers filtered by status."""
    status_to_filter = OfferStatus.INACTIVE
    filtered_offer_status = OfferModel(id=uuid4(), title="Offer Inactive", seller_id=uuid4(), category_id=1, price=Decimal(10), quantity=1, status=status_to_filter, created_at=datetime.now(timezone.utc))

    # Setup scalar_result mock
    scalar_result = MagicMock()
    scalar_result.all.return_value = [filtered_offer_status]
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]
    
    response = await offer_service.list_all_offers(status_filter=status_to_filter)
    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].status == status_to_filter

@pytest.mark.asyncio
async def test_list_all_offers_sort_price_asc(offer_service, mock_db_session):
    """Test listing offers sorted by price ascending."""
    offer_cheaper = OfferModel(id=uuid4(), title="Cheap Offer", price=Decimal("5"), seller_id=uuid4(), category_id=1, quantity=1, status=OfferStatus.ACTIVE, created_at=datetime.now(timezone.utc))
    offer_expensive = OfferModel(id=uuid4(), title="Expensive Offer", price=Decimal("50"), seller_id=uuid4(), category_id=1, quantity=1, status=OfferStatus.ACTIVE, created_at=datetime.now(timezone.utc))
    
    # Setup scalar_result mock with price-ordered data
    scalar_result = MagicMock()
    scalar_result.all.return_value = [offer_cheaper, offer_expensive]
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=2)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]

    response = await offer_service.list_all_offers(sort="price_asc")
    assert response.total == 2
    assert response.items[0].price < response.items[1].price

@pytest.mark.asyncio
async def test_list_all_offers_pagination(offer_service, mock_db_session):
    """Test pagination for listing offers."""
    # Simulate 15 offers in total, page 2, limit 5
    all_offers = [OfferModel(id=uuid4(), title=f"Offer {i}", seller_id=uuid4(), category_id=1, price=Decimal(10), quantity=1, status=OfferStatus.ACTIVE, created_at=datetime.now(timezone.utc)) for i in range(15)]
    page = 2
    limit = 5
    expected_items_on_page = all_offers[(page-1)*limit : page*limit]

    # Setup scalar_result mock with paginated data
    scalar_result = MagicMock()
    scalar_result.all.return_value = expected_items_on_page
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=15)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]

    response = await offer_service.list_all_offers(page=page, limit=limit)
    assert response.total == 15
    assert len(response.items) == limit
    assert response.page == page
    assert response.limit == limit
    assert response.pages == (15 + limit - 1) // limit

@pytest.mark.asyncio
async def test_list_all_offers_empty_result(offer_service, mock_db_session):
    """Test listing offers when no offers match criteria."""
    # Setup scalar_result mock with empty list
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    
    # Reset execute mock
    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=0)),
        MagicMock(scalars=AsyncMock(return_value=scalar_result))
    ]

    response = await offer_service.list_all_offers(search="NonExistentTerm")
    assert response.total == 0
    assert len(response.items) == 0
    assert response.pages == 0

@pytest.mark.asyncio
async def test_list_all_offers_db_exception(offer_service, mock_db_session):
    """Test listing offers when a database exception occurs."""
    mock_db_session.execute.side_effect = Exception("DB query error")

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.list_all_offers()
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error_code"] == "FETCH_FAILED"

# --- Tests for moderate_offer ---

@pytest.mark.asyncio
async def test_moderate_offer_success(offer_service, mock_db_session, mock_offer_model, mock_seller_user, mock_category):
    """Test successful moderation of an offer."""
    offer_to_moderate = mock_offer_model
    offer_to_moderate.status = OfferStatus.ACTIVE # Can be any non-moderated status

    mock_db_session.get.side_effect = [
        offer_to_moderate,
        mock_seller_user, # Corresponds to offer.seller_id from mock_offer_model
        mock_category     # Corresponds to offer.category_id from mock_offer_model
    ]

    result_dto = await offer_service.moderate_offer(offer_id=offer_to_moderate.id)

    assert result_dto.status == OfferStatus.MODERATED
    assert offer_to_moderate.status == OfferStatus.MODERATED
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_with(offer_to_moderate)
    # No log event for moderation in current service implementation

@pytest.mark.asyncio
async def test_moderate_offer_not_found(offer_service, mock_db_session):
    """Test moderating a non-existent offer."""
    # Re-define get to ensure it's a fresh mock
    mock_db_session.get = AsyncMock(return_value=None)
    
    await assert_raises_exception(
        func=lambda: offer_service.moderate_offer(offer_id=uuid4()),
        expected_exception=OfferNotFoundException
    )

@pytest.mark.asyncio
async def test_moderate_offer_already_moderated(offer_service, mock_db_session, mock_offer_model):
    """Test moderating an offer that is already moderated."""
    mock_offer_model.status = OfferStatus.MODERATED
    mock_db_session.get.return_value = mock_offer_model
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.moderate_offer(offer_id=mock_offer_model.id)
    assert exc_info.value.status_code == 409 # Conflict
    assert exc_info.value.detail["error_code"] == "ALREADY_MODERATED"

@pytest.mark.asyncio
async def test_moderate_offer_db_commit_exception(offer_service, mock_db_session, mock_offer_model):
    """Test moderating an offer when database commit fails."""
    mock_offer_model.status = OfferStatus.ACTIVE
    mock_db_session.get.return_value = mock_offer_model
    mock_db_session.commit.side_effect = Exception("DB commit error")

    await assert_raises_exception(
        func=lambda: offer_service.moderate_offer(offer_id=mock_offer_model.id),
        expected_exception=OfferModificationFailedException,
        check_exception_attributes={
            "operation": "moderation",
            "message": "DB commit error"
        }
    )

# --- Tests for unmoderate_offer ---

@pytest.mark.asyncio
async def test_unmoderate_offer_success(offer_service, mock_db_session, mock_offer_model, mock_seller_user, mock_category):
    """Test successful unmoderation of an offer."""
    offer_to_unmoderate = mock_offer_model
    offer_to_unmoderate.status = OfferStatus.MODERATED

    mock_db_session.get.side_effect = [
        offer_to_unmoderate,
        mock_seller_user,
        mock_category
    ]

    result_dto = await offer_service.unmoderate_offer(offer_id=offer_to_unmoderate.id)

    assert result_dto.status == OfferStatus.INACTIVE # Unmoderation sets to INACTIVE
    assert offer_to_unmoderate.status == OfferStatus.INACTIVE
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_with(offer_to_unmoderate)
    # No log event for unmoderation in current service implementation

@pytest.mark.asyncio
async def test_unmoderate_offer_not_found(offer_service, mock_db_session):
    """Test unmoderating a non-existent offer."""
    # Re-define get to ensure it's a fresh mock
    mock_db_session.get = AsyncMock(return_value=None)
    
    await assert_raises_exception(
        func=lambda: offer_service.unmoderate_offer(offer_id=uuid4()),
        expected_exception=OfferNotFoundException
    )

@pytest.mark.asyncio
async def test_unmoderate_offer_not_moderated(offer_service, mock_db_session, mock_offer_model):
    """Test unmoderating an offer that is not currently moderated."""
    mock_offer_model.status = OfferStatus.ACTIVE # Any non-moderated status
    mock_db_session.get.return_value = mock_offer_model
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.unmoderate_offer(offer_id=mock_offer_model.id)
    assert exc_info.value.status_code == 409 # Conflict
    assert exc_info.value.detail["error_code"] == "NOT_MODERATED"

@pytest.mark.asyncio
async def test_unmoderate_offer_db_commit_exception(offer_service, mock_db_session, mock_offer_model):
    """Test unmoderating an offer when database commit fails."""
    mock_offer_model.status = OfferStatus.MODERATED
    mock_db_session.get.return_value = mock_offer_model
    mock_db_session.commit.side_effect = Exception("DB commit error")

    await assert_raises_exception(
        func=lambda: offer_service.unmoderate_offer(offer_id=mock_offer_model.id),
        expected_exception=OfferModificationFailedException,
        check_exception_attributes={
            "operation": "unmoderation",
            "message": "DB commit error"
        }
    )
    assert mock_db_session.rollback.await_count > 0