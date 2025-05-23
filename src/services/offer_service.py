from datetime import datetime
from decimal import Decimal
from logging import Logger
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import case, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import CategoryModel, OfferModel, UserModel
from schemas import (CategoryDTO, LogEventType, OfferDetailDTO,
                     OfferListResponse, OfferStatus, OfferSummaryDTO,
                     SellerInfoDTO, UserRole)
from src.exceptions.offer_exceptions import (InvalidStatusTransitionException,
                                             NotOfferOwnerException,
                                             OfferAlreadyInactiveException,
                                             OfferAlreadySoldException,
                                             OfferModificationFailedException,
                                             OfferNotFoundException)
from utils.pagination_utils import build_paginated_response

from .file_service import FileService
from .log_service import LogService


class OfferService:
    def __init__(self, db_session: AsyncSession, logger: Logger):
        self.db_session = db_session
        self.logger = logger
        self.file_service = FileService(logger)
        self.log_service = LogService(db_session)

    async def create_offer(
        self,
        seller_id: UUID,
        title: str,
        price: Decimal,
        category_id: int,
        quantity: int = 1,
        description: Optional[str] = None,
        image: Optional[UploadFile] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> OfferSummaryDTO:
        """
        Creates a new offer in the database.

        Args:
            seller_id: ID of the seller creating the offer
            title: Title of the offer
            price: Price of the product
            category_id: ID of the product category
            quantity: Quantity available (default 1)
            description: Optional product description
            image: Optional product image
            background_tasks: Optional background tasks for async operations

        Returns:
            OfferSummaryDTO: The created offer details

        Raises:
            HTTPException: If validation fails or database operation fails
        """
        try:
            # Validate price
            if price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_PRICE",
                        "message": "Price must be greater than 0",
                    },
                )

            # Validate quantity
            if quantity < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_QUANTITY",
                        "message": "Quantity cannot be negative",
                    },
                )

            # Verify category exists
            result = await self.db_session.execute(
                select(CategoryModel).where(CategoryModel.id == category_id)
            )
            category = result.scalars().first()

            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "CATEGORY_NOT_FOUND",
                        "message": "Category not found",
                    },
                )

            # Process image if provided
            image_filename = None
            if image:
                image_filename = await self.file_service.save_image(image)

            # Create offer in database
            new_offer = OfferModel(
                seller_id=seller_id,
                category_id=category_id,
                title=title,
                description=description,
                price=price,
                quantity=quantity,
                image_filename=image_filename,
                status=OfferStatus.INACTIVE,  # Default status is inactive
            )

            self.db_session.add(new_offer)

            # Log event using LogService
            await self.log_service.create_log(
                event_type=LogEventType.OFFER_CREATE,
                user_id=seller_id,
                message=f"User {seller_id} created a new offer: {title}",
            )

            await self.db_session.commit()
            await self.db_session.refresh(new_offer)

            # Convert to DTO and return
            return OfferSummaryDTO(
                id=new_offer.id,
                seller_id=new_offer.seller_id,
                category_id=new_offer.category_id,
                title=new_offer.title,
                price=new_offer.price,
                image_filename=new_offer.image_filename,
                quantity=new_offer.quantity,
                status=new_offer.status,
                created_at=new_offer.created_at,
            )

        except HTTPException:
            await self.db_session.rollback()
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating offer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "CREATE_FAILED",
                    "message": "Failed to create the offer",
                },
            )

    async def deactivate_offer(
        self, offer_id: UUID, user_id: UUID, user_role: UserRole
    ) -> OfferDetailDTO:
        """
        Deactivate an offer by changing its status from 'active' to 'inactive'

        Args:
            offer_id: UUID of the offer to deactivate
            user_id: UUID of the current user
            user_role: Role of the current user

        Returns:
            OfferDetailDTO with the updated offer details

        Raises:
            HTTPException: Various exceptions based on validation and authorization
        """
        try:
            # Verify user is a seller
            if user_role != UserRole.SELLER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "message": "Only sellers can deactivate offers",
                    },
                )

            # Get the offer
            offer = await self.db_session.get(OfferModel, offer_id)

            # Check if offer exists
            if not offer:
                raise OfferNotFoundException(offer_id)

            # Check if user is the owner
            if offer.seller_id != user_id:
                raise NotOfferOwnerException(offer_id)

            # Check if offer is already inactive
            if offer.status == OfferStatus.INACTIVE:
                raise OfferAlreadyInactiveException(offer_id)

            # Check if offer status allows deactivation (must be 'active')
            if offer.status != OfferStatus.ACTIVE:
                raise InvalidStatusTransitionException(
                    current_status=offer.status,
                    target_status=OfferStatus.INACTIVE,
                )

            # Update offer status
            offer.status = OfferStatus.INACTIVE
            offer.updated_at = datetime.now()

            # Save to database
            await self.db_session.commit()
            await self.db_session.refresh(offer)

            # Log the status change event
            await self.log_service.create_log(
                event_type=LogEventType.OFFER_STATUS_CHANGE,
                user_id=user_id,
                message=f"Offer {offer_id} deactivated",
            )

            # Fetch seller and category for full response
            seller = await self.db_session.get(UserModel, offer.seller_id)
            category = await self.db_session.get(
                CategoryModel, offer.category_id
            )

            # Return detailed DTO
            return self._map_to_offer_detail_dto(offer, seller, category)

        except (
            OfferNotFoundException,
            NotOfferOwnerException,
            InvalidStatusTransitionException,
            OfferAlreadyInactiveException,
        ):
            # Re-raise custom exceptions
            raise
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log the error
            self.logger.error(f"Error deactivating offer: {str(e)}")
            raise OfferModificationFailedException(
                operation="deactivate", details=str(e)
            )

    def _map_to_offer_detail_dto(self, offer, seller, category):
        """
        Maps database models to OfferDetailDTO

        Args:
            offer: OfferModel instance
            seller: UserModel instance
            category: CategoryModel instance

        Returns:
            OfferDetailDTO with offer details, seller and category information
        """
        seller_info = SellerInfoDTO(
            id=seller.id,
            first_name=seller.first_name,
            last_name=seller.last_name,
        )

        category_info = CategoryDTO(id=category.id, name=category.name)

        return OfferDetailDTO(
            id=offer.id,
            seller_id=offer.seller_id,
            category_id=offer.category_id,
            title=offer.title,
            description=offer.description,
            price=offer.price,
            image_filename=offer.image_filename,
            quantity=offer.quantity,
            status=offer.status,
            created_at=offer.created_at,
            updated_at=offer.updated_at,
            seller=seller_info,
            category=category_info,
        )

    async def mark_offer_as_sold(
        self, offer_id: UUID, user_id: UUID, user_role: UserRole
    ) -> OfferDetailDTO:
        """
        Mark an offer as sold by changing its status to 'sold' and setting quantity to 0

        Args:
            offer_id: UUID of the offer to mark as sold
            user_id: UUID of the current user
            user_role: Role of the current user

        Returns:
            OfferDetailDTO with the updated offer details

        Raises:
            HTTPException: Various exceptions based on validation and authorization
        """
        try:
            # Verify user is a seller
            if user_role != UserRole.SELLER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "message": "Only sellers can mark offers as sold",
                    },
                )

            # Get the offer
            offer = await self.db_session.get(OfferModel, offer_id)

            # Check if offer exists
            if not offer:
                raise OfferNotFoundException(offer_id)

            # Check if user is the owner
            if offer.seller_id != user_id:
                raise NotOfferOwnerException(offer_id)

            # Check if offer is already sold
            if offer.status == OfferStatus.SOLD:
                raise OfferAlreadySoldException(offer_id)

            # Check if offer status allows marking as sold (cannot be archived or deleted)
            if offer.status in [OfferStatus.ARCHIVED, OfferStatus.DELETED]:
                raise InvalidStatusTransitionException(
                    current_status=offer.status, target_status=OfferStatus.SOLD
                )

            # Update offer status and quantity
            offer.status = OfferStatus.SOLD
            offer.quantity = 0
            offer.updated_at = datetime.now()

            # Save to database
            await self.db_session.commit()
            await self.db_session.refresh(offer)

            # Log the status change event
            await self.log_service.create_log(
                event_type=LogEventType.OFFER_STATUS_CHANGE,
                user_id=user_id,
                message=f"Offer {offer_id} marked as sold",
            )

            # Fetch seller and category for full response
            seller = await self.db_session.get(UserModel, offer.seller_id)
            category = await self.db_session.get(
                CategoryModel, offer.category_id
            )

            # Return detailed DTO
            return self._map_to_offer_detail_dto(offer, seller, category)

        except (
            OfferNotFoundException,
            NotOfferOwnerException,
            InvalidStatusTransitionException,
            OfferAlreadySoldException,
        ):
            # Re-raise custom exceptions
            raise
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log the error
            self.logger.error(f"Error marking offer as sold: {str(e)}")
            raise OfferModificationFailedException(
                operation="mark_sold", details=str(e)
            )

    async def list_all_offers(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        seller_id: Optional[UUID] = None,
        status_filter: Optional[OfferStatus] = None,
        sort: str = "created_at_desc",
        page: int = 1,
        limit: int = 100,
    ) -> OfferListResponse:
        """
        Retrieve a paginated list of all offers for admin, with filtering, sorting, and pagination.
        """
        try:
            # Calculate offset
            offset = (page - 1) * limit

            # Base query
            base_query = select(OfferModel)
            filters = []
            if search:
                term = f"%{search}%"
                filters.append(
                    or_(
                        OfferModel.title.ilike(term),
                        OfferModel.description.ilike(term),
                    )
                )
            if category_id is not None:
                filters.append(OfferModel.category_id == category_id)
            if seller_id is not None:
                filters.append(OfferModel.seller_id == seller_id)
            if status_filter is not None:
                filters.append(OfferModel.status == status_filter)

            # Apply filters
            query = base_query.where(*filters) if filters else base_query

            # Sorting
            if sort == "price_asc":
                query = query.order_by(OfferModel.price.asc())
            elif sort == "price_desc":
                query = query.order_by(OfferModel.price.desc())
            elif sort == "relevance" and search:
                # Simple relevance: exact match first, prefix match next, then others
                # Using term for ILIKE conditions
                # term is defined above as f"%{search}%"
                query = query.order_by(
                    case(
                        [
                            (OfferModel.title.ilike(term), 1),
                            (OfferModel.title.ilike(f"{search}%"), 2),
                        ],
                        else_=3,
                    )
                )
            else:
                # default sort by creation date descending
                query = query.order_by(OfferModel.created_at.desc())

            # Count total
            count_q = select(func.count()).select_from(query.subquery())
            total = (await self.db_session.execute(count_q)).scalar() or 0

            # Fetch paginated data
            result = await self.db_session.execute(
                query.offset(offset).limit(limit)
            )
            scalar_result = await result.scalars()
            offers = scalar_result.all()

            # Map to DTOs
            items = [
                OfferSummaryDTO(
                    id=o.id,
                    seller_id=o.seller_id,
                    category_id=o.category_id,
                    title=o.title,
                    price=o.price,
                    image_filename=o.image_filename,
                    quantity=o.quantity,
                    status=o.status,
                    created_at=o.created_at,
                )
                for o in offers
            ]

            # Build and return paginated response
            paginated = build_paginated_response(items, total, page, limit)
            # Convert to OfferListResponse
            return OfferListResponse(**paginated.model_dump())
        except Exception as e:
            self.logger.error(f"Error fetching all offers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch offers",
                },
            )

    async def moderate_offer(self, offer_id: UUID) -> OfferDetailDTO:
        """
        Moderates an offer by changing its status to 'moderated'.
        """
        # Retrieve the offer
        offer = await self.db_session.get(OfferModel, offer_id)
        if not offer:
            raise OfferNotFoundException(offer_id)
        if offer.status == OfferStatus.MODERATED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "ALREADY_MODERATED",
                    "message": "Offer is already moderated",
                },
            )
        # Update status and timestamp
        offer.status = OfferStatus.MODERATED
        offer.updated_at = datetime.now()
        try:
            await self.db_session.commit()
            await self.db_session.refresh(offer)
        except HTTPException:
            await self.db_session.rollback()
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error moderating offer {offer_id}: {str(e)}")
            raise OfferModificationFailedException(
                operation="moderation", details=str(e)
            )
        # Fetch related entities for full DTO
        seller = await self.db_session.get(UserModel, offer.seller_id)
        category = await self.db_session.get(CategoryModel, offer.category_id)
        return self._map_to_offer_detail_dto(offer, seller, category)

    async def unmoderate_offer(self, offer_id: UUID) -> OfferDetailDTO:
        """
        Unmoderates an offer by changing its status from 'moderated' to 'inactive'.
        """
        # Retrieve the offer
        offer = await self.db_session.get(OfferModel, offer_id)
        if not offer:
            raise OfferNotFoundException(offer_id)
        # Ensure the offer is currently moderated
        if offer.status != OfferStatus.MODERATED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "NOT_MODERATED",
                    "message": "Offer is not moderated",
                },
            )
        # Update status and timestamp
        offer.status = OfferStatus.INACTIVE
        offer.updated_at = datetime.now()
        try:
            await self.db_session.commit()
            await self.db_session.refresh(offer)
        except HTTPException:
            await self.db_session.rollback()
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error unmoderating offer {offer_id}: {str(e)}")
            raise OfferModificationFailedException(
                operation="unmoderation", details=str(e)
            )
        # Fetch related entities for full DTO
        seller = await self.db_session.get(UserModel, offer.seller_id)
        category = await self.db_session.get(CategoryModel, offer.category_id)
        return self._map_to_offer_detail_dto(offer, seller, category)
        
    async def search_offers(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
        sort: str = "created_at_desc",
    ) -> OfferListResponse:
        """
        Search and filter public offers with pagination.
        Only returns active offers for public consumption.

        Args:
            search: Optional search term for title/description
            category_id: Optional category ID to filter by
            page: Page number (default: 1)
            limit: Number of items per page (default: 20)
            sort: Sort order (price_asc, price_desc, created_at_desc, relevance)

        Returns:
            OfferListResponse: Paginated list of offers
        """
        try:
            # Calculate offset
            offset = (page - 1) * limit

            # Base query - only include ACTIVE offers
            base_query = select(OfferModel).where(OfferModel.status == OfferStatus.ACTIVE)
            filters = []
            
            if search:
                term = f"%{search}%"
                filters.append(
                    or_(
                        OfferModel.title.ilike(term),
                        OfferModel.description.ilike(term),
                    )
                )
            if category_id is not None:
                filters.append(OfferModel.category_id == category_id)

            # Apply filters
            query = base_query.where(*filters) if filters else base_query

            # Sorting
            if sort == "price_asc":
                query = query.order_by(OfferModel.price.asc())
            elif sort == "price_desc":
                query = query.order_by(OfferModel.price.desc())
            elif sort == "relevance" and search:
                # Simple relevance: exact match first, prefix match next, then others
                query = query.order_by(
                    case(
                        [
                            (OfferModel.title.ilike(search), 1),
                            (OfferModel.title.ilike(f"{search}%"), 2),
                        ],
                        else_=3,
                    )
                )
            else:
                # default sort by creation date descending
                query = query.order_by(OfferModel.created_at.desc())

            # Count total
            count_q = select(func.count()).select_from(query.subquery())
            total = (await self.db_session.execute(count_q)).scalar() or 0

            # Fetch paginated data
            result = await self.db_session.execute(
                query.offset(offset).limit(limit)
            )
            offers = result.scalars().all()

            # Map to DTOs
            items = [
                OfferSummaryDTO(
                    id=o.id,
                    seller_id=o.seller_id,
                    category_id=o.category_id,
                    title=o.title,
                    price=o.price,
                    image_filename=o.image_filename,
                    quantity=o.quantity,
                    status=o.status,
                    created_at=o.created_at,
                )
                for o in offers
            ]

            # Build and return paginated response
            return OfferListResponse(
                items=items,
                total=total,
                page=page,
                limit=limit,
                pages=(total + limit - 1) // limit if limit > 0 else 0
            )
        except Exception as e:
            self.logger.error(f"Error searching offers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch offers",
                },
            )
