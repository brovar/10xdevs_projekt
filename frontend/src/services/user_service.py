from datetime import datetime
from logging import Logger
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import LogModel, OfferModel, OrderItemModel, OrderModel, UserModel
from schemas import (ChangePasswordRequest, LogEventType, LoginUserRequest,
                     OfferStatus, OrderStatus, UpdateUserRequest, UserDTO,
                     UserListResponse, UserRole, UserStatus)
from utils.password_utils import get_password_hash, verify_password


class UserService:
    def __init__(self, db_session: AsyncSession, logger: Logger):
        self.db_session = db_session
        self.logger = logger

    async def login_user(
        self, login_data: LoginUserRequest, request: Request
    ) -> bool:
        """
        Authenticate a user based on email and password.

        Args:
            login_data: The login request data containing email and password
            request: The FastAPI request object (for getting IP address)

        Returns:
            bool: True if authentication is successful

        Raises:
            HTTPException: If authentication fails or user is inactive
        """
        # Find user by email
        user_result = await self.db_session.execute(
            select(UserModel).where(UserModel.email == login_data.email)
        )
        user = user_result.scalars().first()

        # Safety - always log attempt (but don't expose if user exists)
        log_message = f"Login attempt for email {login_data.email}"
        event_type = LogEventType.USER_LOGIN

        # Verify credentials and user status
        if not user:
            # Don't expose that user doesn't exist
            log_entry = LogModel(
                event_type=event_type,
                ip_address=request.client.host,
                message=f"{log_message}: user not found",
            )
            self.db_session.add(log_entry)
            await self.db_session.commit()

            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "INVALID_CREDENTIALS",
                    "message": "Nieprawidłowe dane logowania.",
                },
            )

        # Add user_id to log now that we have it
        log_entry = LogModel(
            event_type=event_type,
            user_id=user.id,
            ip_address=request.client.host,
            message=log_message,
        )

        # Check if password is correct
        if not verify_password(login_data.password, user.password_hash):
            log_entry.message += ": invalid password"
            self.db_session.add(log_entry)
            await self.db_session.commit()

            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "INVALID_CREDENTIALS",
                    "message": "Nieprawidłowe dane logowania.",
                },
            )

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            log_entry.message += f": user inactive (status={user.status})"
            self.db_session.add(log_entry)
            await self.db_session.commit()

            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "USER_INACTIVE",
                    "message": "Konto użytkownika jest nieaktywne.",
                },
            )

        try:
            # Update log message for successful login
            log_entry.message += ": successful"
            self.db_session.add(log_entry)
            await self.db_session.commit()

            return True
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Failed to process login: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "LOGIN_FAILED",
                    "message": "Wystąpił błąd podczas logowania. Spróbuj ponownie później.",
                },
            )

    async def get_current_user(self, user_id: UUID) -> UserDTO:
        """
        Retrieve current user's profile data from database.

        Args:
            user_id: UUID of the user to retrieve

        Returns:
            UserDTO: User data transfer object with profile information

        Raises:
            HTTPException: 404 if user doesn't exist, 500 for server errors
        """
        try:
            # Convert UUID to string if needed - fix for asyncpg.pgproto.UUID issue
            user_id_str = str(user_id)

            # Query database for user
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()

            # Check if user exists
            if not user:
                self.logger.warning(
                    f"User with ID {user_id_str} not found in database"
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika.",
                    },
                )

            # Convert to DTO and return
            return UserDTO(
                id=str(user.id),  # Ensure UUID is converted to string
                email=user.email,
                role=user.role,
                status=user.status,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving user data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Wystąpił błąd podczas pobierania danych użytkownika.",
                },
            )

    async def update_user_profile(
        self, user_id: UUID, update_data: UpdateUserRequest
    ) -> UserDTO:
        """
        Update current user's profile data.
        Only updates fields that are provided in update_data.

        Args:
            user_id: UUID of the user to update
            update_data: The data to update in the user's profile

        Returns:
            UserDTO: Updated user data transfer object with profile information

        Raises:
            HTTPException: 404 if user doesn't exist, 500 for server errors
        """
        try:
            # Convert UUID to string if needed
            user_id_str = str(user_id)

            # Check if user exists
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()

            if not user:
                self.logger.warning(
                    f"User with ID {user_id_str} not found in database"
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika.",
                    },
                )

            # Prepare update data (only non-None fields)
            update_values = {}
            if update_data.first_name is not None:
                update_values["first_name"] = update_data.first_name
            if update_data.last_name is not None:
                update_values["last_name"] = update_data.last_name

            # Add updated_at timestamp
            update_values["updated_at"] = datetime.utcnow()

            # Update user in database
            await self.db_session.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(**update_values)
            )

            # Log the action
            log_entry = LogModel(
                event_type=LogEventType.USER_PROFILE_UPDATE,
                user_id=user_id,
                message=f"User {user_id_str} updated profile information",
            )
            self.db_session.add(log_entry)

            # Commit changes
            await self.db_session.commit()

            # Refresh user object to get updated data
            await self.db_session.refresh(user)

            # Return updated user
            return UserDTO(
                id=str(user.id),  # Ensure UUID is converted to string
                email=user.email,
                role=user.role,
                status=user.status,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating user profile: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "PROFILE_UPDATE_FAILED",
                    "message": "Wystąpił błąd podczas aktualizacji profilu użytkownika.",
                },
            )

    async def change_password(
        self,
        user_id: UUID,
        password_data: ChangePasswordRequest,
        request_ip: str = None,
    ) -> bool:
        """
        Change user's password.
        Verifies current password, validates new password policy, updates password hash.

        Args:
            user_id: UUID of the user changing password
            password_data: Object containing current and new password
            request_ip: IP address of the request for logging purposes

        Returns:
            bool: True if password was successfully changed

        Raises:
            HTTPException: 401 if current password is invalid, 404 if user not found, 500 for server errors
        """
        try:
            # Find user by ID
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()

            if not user:
                self.logger.warning(
                    f"User with ID {user_id} not found during password change"
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika.",
                    },
                )

            # Verify current password
            if not verify_password(
                password_data.current_password, user.password_hash
            ):
                # Log failed attempt
                log_entry = LogModel(
                    event_type=LogEventType.PASSWORD_CHANGE,
                    user_id=user_id,
                    ip_address=request_ip,
                    message=f"Failed password change attempt for user {user_id}: invalid current password",
                )
                self.db_session.add(log_entry)
                await self.db_session.commit()

                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "INVALID_CURRENT_PASSWORD",
                        "message": "Aktualne hasło jest nieprawidłowe.",
                    },
                )

            # The validation for new password is already done by Pydantic model,
            # but we could add additional checks here if needed

            # Hash new password
            new_password_hash = get_password_hash(password_data.new_password)

            # Update user record with new password hash
            await self.db_session.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    password_hash=new_password_hash,
                    updated_at=datetime.utcnow(),
                )
            )

            # Log successful password change
            log_entry = LogModel(
                event_type=LogEventType.PASSWORD_CHANGE,
                user_id=user_id,
                ip_address=request_ip,
                message=f"Password changed successfully for user {user_id}",
            )
            self.db_session.add(log_entry)

            # Commit all changes
            await self.db_session.commit()

            return True

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error changing password: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "PASSWORD_UPDATE_FAILED",
                    "message": "Wystąpił błąd podczas aktualizacji hasła. Spróbuj ponownie później.",
                },
            )

    async def list_users(
        self,
        page: int = 1,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
    ) -> UserListResponse:
        """
        Retrieve a paginated list of users with optional filters.
        """
        offset = (page - 1) * limit

        # Base query
        base_query = select(UserModel)

        # Filter conditions
        filters = []
        if role:
            filters.append(UserModel.role == role)
        if status:
            filters.append(UserModel.status == status)
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    UserModel.email.ilike(search_term),
                    UserModel.first_name.ilike(search_term),
                    UserModel.last_name.ilike(search_term),
                )
            )

        # Apply filters
        query = base_query.where(*filters).order_by(
            UserModel.created_at.desc()
        )
        count_query = select(func.count()).select_from(
            base_query.where(*filters).subquery()
        )

        # Fetch total count
        total_count_result = await self.db_session.execute(count_query)
        total = total_count_result.scalar() or 0

        # Fetch paginated user data
        users_result = await self.db_session.execute(
            query.offset(offset).limit(limit)
        )
        users_db = users_result.scalars().all()

        # Transform to DTOs
        items = [
            UserDTO(
                id=u.id,
                email=u.email,
                role=u.role,
                status=u.status,
                first_name=u.first_name,
                last_name=u.last_name,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users_db
        ]

        # Calculate pages
        pages = (total + limit - 1) // limit if total > 0 else 0

        return UserListResponse(
            items=items, total=total, page=page, limit=limit, pages=pages
        )

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserDTO]:
        """
        Retrieve a single user's details by ID.
        Returns None if user not found.
        Raises ValueError on DB errors.
        """
        try:
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            # Map to DTO excluding password
            return UserDTO(
                id=user.id,
                email=user.email,
                role=user.role,
                status=user.status,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        except Exception as e:
            self.logger.error(f"Error fetching user by ID: {str(e)}")
            raise ValueError(f"Failed to fetch user details: {str(e)}")

    async def block_user(self, user_id: UUID) -> UserDTO:
        """
        Block a user by setting their status to 'Inactive'. If the user is a Seller,
        deactivate their active offers and cancel active orders.
        """
        try:
            # Start a database transaction
            async with self.db_session.begin():
                # Fetch the user
                result = await self.db_session.execute(
                    select(UserModel).where(UserModel.id == user_id)
                )
                user = result.scalars().first()
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                if user.status == UserStatus.INACTIVE:
                    raise ValueError(
                        f"User with ID {user_id} is already inactive"
                    )
                current_time = datetime.utcnow()

                # Update user status to Inactive
                update_query = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        status=UserStatus.INACTIVE, updated_at=current_time
                    )
                    .returning(
                        UserModel.id,
                        UserModel.email,
                        UserModel.role,
                        UserModel.status,
                        UserModel.first_name,
                        UserModel.last_name,
                        UserModel.created_at,
                        UserModel.updated_at,
                    )
                )
                res = await self.db_session.execute(update_query)
                updated_row = res.fetchone()
                # Map updated row to DTO
                updated_user = UserDTO(**dict(updated_row))

                # If the user is a Seller, deactivate their offers
                if user.role == UserRole.SELLER:
                    # Deactivate offers
                    offers_res = await self.db_session.execute(
                        select(OfferModel.id).where(
                            OfferModel.seller_id == user_id,
                            OfferModel.status.in_(
                                [OfferStatus.ACTIVE, OfferStatus.INACTIVE]
                            ),
                        )
                    )
                    offer_ids = offers_res.scalars().all()
                    if offer_ids:
                        await self.db_session.execute(
                            update(OfferModel)
                            .where(OfferModel.id.in_(offer_ids))
                            .values(
                                status=OfferStatus.INACTIVE,
                                updated_at=current_time,
                            )
                        )

                    # Cancel active orders
                    orders_res = await self.db_session.execute(
                        select(OrderModel.id)
                        .distinct()
                        .join(
                            OrderItemModel,
                            OrderModel.id == OrderItemModel.order_id,
                        )
                        .join(
                            OfferModel,
                            OrderItemModel.offer_id == OfferModel.id,
                        )
                        .where(
                            OfferModel.seller_id == user_id,
                            OrderModel.status.in_(
                                [
                                    OrderStatus.PENDING_PAYMENT,
                                    OrderStatus.PROCESSING,
                                    OrderStatus.SHIPPED,
                                ]
                            ),
                        )
                    )
                    order_ids = orders_res.scalars().all()
                    if order_ids:
                        await self.db_session.execute(
                            update(OrderModel)
                            .where(OrderModel.id.in_(order_ids))
                            .values(
                                status=OrderStatus.CANCELLED,
                                updated_at=current_time,
                            )
                        )
            return updated_user
        except ValueError:
            # Propagate known errors
            raise
        except Exception as e:
            self.logger.error(f"Error blocking user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "BLOCK_FAILED",
                    "message": "Failed to block user",
                },
            )

    async def unblock_user(self, user_id: UUID) -> UserDTO:
        """
        Unblock a user by setting their status to 'Active'.
        """
        try:
            # Start a database transaction
            async with self.db_session.begin():
                # Fetch the user
                result = await self.db_session.execute(
                    select(UserModel).where(UserModel.id == user_id)
                )
                user = result.scalars().first()
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                if user.status == UserStatus.ACTIVE:
                    raise ValueError(
                        f"User with ID {user_id} is already active"
                    )
                current_time = datetime.utcnow()

                # Update user status to 'Active'
                update_query = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(status=UserStatus.ACTIVE, updated_at=current_time)
                    .returning(
                        UserModel.id,
                        UserModel.email,
                        UserModel.role,
                        UserModel.status,
                        UserModel.first_name,
                        UserModel.last_name,
                        UserModel.created_at,
                        UserModel.updated_at,
                    )
                )
                res = await self.db_session.execute(update_query)
                updated_row = res.fetchone()
                # Map to DTO
                unblocked_user = UserDTO(**dict(updated_row))
            return unblocked_user
        except ValueError:
            # Propagate known errors for handler
            raise
        except Exception as e:
            self.logger.error(f"Error unblocking user {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "UNBLOCK_FAILED",
                    "message": "Failed to unblock user",
                },
            )
