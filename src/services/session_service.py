from fastapi import Response, Request, HTTPException
from uuid import UUID
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel
import os
import logging

# Configure logging
logger = logging.getLogger("steambay")

class SessionData(BaseModel):
    user_id: UUID
    user_role: str

class SessionService:
    def __init__(
        self, 
        cookie_name: str = "session", 
        cookie_max_age: int = 604800,  # 7 days in seconds
        secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    ):
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.secret_key = secret_key
        logger.info("Session service initialized")
        
    async def create_session(self, response: Response, user_id: UUID, user_role: str) -> str:
        """
        Create a new session for the user and set the session cookie.
        
        Args:
            response: FastAPI response object to set cookie
            user_id: User ID to store in session
            user_role: User role to store in session
            
        Returns:
            str: The session token
        """
        logger.debug(f"Creating session for user {user_id} with role {user_role}")
        
        # Create JWT payload
        payload = {
            "sub": str(user_id),
            "role": user_role,
            "exp": datetime.utcnow() + timedelta(seconds=self.cookie_max_age)
        }
        
        # Create JWT token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Set cookie in response
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.cookie_max_age,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        logger.debug("Session created successfully")
        return token
    
    async def end_session(self, response: Response, request: Request = None) -> bool:
        """
        End a user session and remove the session cookie.
        
        Args:
            response: FastAPI response object
            request: FastAPI request object (optional)
            
        Returns:
            bool: True if session was successfully ended, False if no session was found
        """
        # Simply delete the cookie
        response.delete_cookie(
            key=self.cookie_name,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        logger.debug("Session ended successfully")
        return True
            
    async def get_session(self, request: Request) -> SessionData:
        """
        Get the session data from a request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            SessionData: The session data
            
        Raises:
            HTTPException: If no valid session is found
        """
        try:
            # Get token from cookie
            token = request.cookies.get(self.cookie_name)
            if not token:
                logger.debug("No session token found in cookies")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany."
                    }
                )
            
            # Decode token
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                user_id = UUID(payload["sub"])
                user_role = payload["role"]
                
                logger.debug(f"Session found for user {user_id}")
                return SessionData(user_id=user_id, user_role=user_role)
            except jwt.ExpiredSignatureError:
                logger.debug("Session token expired")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "SESSION_EXPIRED",
                        "message": "Sesja wygasła. Zaloguj się ponownie."
                    }
                )
            except (jwt.InvalidTokenError, ValueError):
                logger.debug("Invalid session token")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "INVALID_TOKEN",
                        "message": "Nieprawidłowy token sesji."
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Użytkownik nie jest zalogowany."
                }
            ) 