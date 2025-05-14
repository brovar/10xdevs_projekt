from datetime import datetime
from logging import Logger
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import LogModel, UserModel
from schemas import (ChangePasswordRequest, LogEventType, UpdateUserRequest,
                     UserDTO, UserListResponse, UserRole, UserStatus)
from utils.password_utils import get_password_hash, verify_password


class UserService:
    def __init__(self, db_session: AsyncSession, logger: Logger):
        self.db_session = db_session
        self.logger = logger

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
            # Ensure user_id is correctly handled as string when needed
            user_id_str = str(user_id)
            self.logger.info(f"Looking up user with ID: {user_id_str}")

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
                        "message": "User not found.",
                    },
                )

            # Convert to DTO and return - make sure to convert UUID to string
            return UserDTO(
                id=str(user.id),  # Explicitly convert UUID to string
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
                    "message": "An error occurred while retrieving user data.",
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
            # Ensure user_id is correctly handled as string when needed
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
                        "message": "User not found.",
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

            # Return updated user - make sure to convert UUID to string
            return UserDTO(
                id=str(user.id),  # Explicitly convert UUID to string
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
                    "message": "An error occurred while updating user profile.",
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
            # Ensure user_id is correctly handled as string when needed
            user_id_str = str(user_id)

            # Find user by ID
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()

            if not user:
                self.logger.warning(
                    f"User with ID {user_id_str} not found during password change"
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "User not found.",
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
                    message=f"Failed password change attempt for user {user_id_str}: invalid current password",
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
                message=f"Password changed successfully for user {user_id_str}",
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
                    "message": "An error occurred while updating password. Please try again later.",
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
        try:
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
            query = base_query
            if filters:
                query = query.where(*filters)
            query = query.order_by(UserModel.created_at.desc())
            
            count_query = select(func.count()).select_from(
                UserModel
            )
            if filters:
                count_query = count_query.where(*filters)

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
                    id=str(u.id),  # Ensure UUID is converted to string
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
        except Exception as e:
            self.logger.error(f"Error listing users: {str(e)}")
            raise ValueError(f"Failed to fetch user details: {str(e)}")

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
                id=str(user.id),  # Ensure UUID is converted to string
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
        Block a user by setting their status to 'Inactive'.
        """
        try:
            # Fetch the user
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            if user.status == UserStatus.INACTIVE:
                raise ValueError(f"User with ID {user_id} is already inactive")
            
            # Update user status to Inactive
            user.status = UserStatus.INACTIVE
            user.updated_at = datetime.utcnow()
            await self.db_session.commit()
            
            # Return updated user DTO
            return UserDTO(
                id=str(user.id),
                email=user.email,
                role=user.role,
                status=user.status,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        except ValueError:
            # Propagate known errors
            raise
        except Exception as e:
            await self.db_session.rollback()
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
            # Fetch the user
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            if user.status == UserStatus.ACTIVE:
                raise ValueError(f"User with ID {user_id} is already active")
            
            # Update user status to Active
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.utcnow()
            await self.db_session.commit()
            
            # Return updated user DTO
            return UserDTO(
                id=str(user.id),
                email=user.email,
                role=user.role,
                status=user.status,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        except ValueError:
            # Propagate known errors
            raise
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error unblocking user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "UNBLOCK_FAILED",
                    "message": "Failed to unblock user",
                },
            )
