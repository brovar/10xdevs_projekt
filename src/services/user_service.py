from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from logging import Logger
from schemas import LoginUserRequest, UserStatus, LogEventType, UserDTO, UpdateUserRequest, ChangePasswordRequest, UserRole
from models import UserModel, LogModel
from utils.password_utils import verify_password, get_password_hash
from uuid import UUID
from datetime import datetime
from sqlalchemy import func, or_
from typing import Optional

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
                self.logger.warning(f"User with ID {user_id_str} not found in database")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika."
                    }
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
                updated_at=user.updated_at
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
                    "message": "Wystąpił błąd podczas pobierania danych użytkownika."
                }
            )
    
    async def update_user_profile(self, user_id: UUID, update_data: UpdateUserRequest) -> UserDTO:
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
                self.logger.warning(f"User with ID {user_id_str} not found in database")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika."
                    }
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
                message=f"User {user_id_str} updated profile information"
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
                updated_at=user.updated_at
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
                    "message": "Wystąpił błąd podczas aktualizacji profilu użytkownika."
                }
            )
    
    async def change_password(self, user_id: UUID, password_data: ChangePasswordRequest, request_ip: str = None) -> bool:
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
                self.logger.warning(f"User with ID {user_id_str} not found during password change")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "USER_NOT_FOUND",
                        "message": "Nie znaleziono użytkownika."
                    }
                )
            
            # Verify current password
            if not verify_password(password_data.current_password, user.password_hash):
                # Log failed attempt
                log_entry = LogModel(
                    event_type=LogEventType.PASSWORD_CHANGE,
                    user_id=user_id,
                    ip_address=request_ip,
                    message=f"Failed password change attempt for user {user_id_str}: invalid current password"
                )
                self.db_session.add(log_entry)
                await self.db_session.commit()
                
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "INVALID_CURRENT_PASSWORD",
                        "message": "Aktualne hasło jest nieprawidłowe."
                    }
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
                    updated_at=datetime.utcnow()
                )
            )
            
            # Log successful password change
            log_entry = LogModel(
                event_type=LogEventType.PASSWORD_CHANGE,
                user_id=user_id,
                ip_address=request_ip,
                message=f"Password changed successfully for user {user_id_str}"
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
                    "message": "Wystąpił błąd podczas aktualizacji hasła. Spróbuj ponownie później."
                }
            ) 