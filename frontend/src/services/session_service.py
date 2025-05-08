from fastapi import Response, Request, HTTPException
from uuid import UUID
from datetime import datetime, timedelta
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from pydantic import BaseModel
import uuid


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
        self.cookie_params = CookieParameters(
            max_age=cookie_max_age,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # Create the session cookie frontend
        self.cookie = SessionCookie(
            cookie_name=cookie_name,
            identifier="general_verifier",
            auto_error=True,
            secret_key=secret_key,
            cookie_params=self.cookie_params,
        )
        
        # Create in-memory backend
        self.backend = InMemoryBackend[UUID, SessionData]()
        
    async def create_session(self, response: Response, user_id: UUID, user_role: str) -> UUID:
        """
        Create a new session for the user and set the session cookie.
        
        Args:
            response: FastAPI response object to set cookie
            user_id: User ID to store in session
            user_role: User role to store in session
            
        Returns:
            UUID: The session ID
        """
        session_id = uuid.uuid4()
        session_data = SessionData(user_id=user_id, user_role=user_role)
        
        # Store session in backend
        await self.backend.create(session_id, session_data)
        
        # Set cookie in response
        await self.cookie.attach_to_response(response, session_id)
        
        return session_id
    
    async def end_session(self, response: Response, session_id: UUID = None, request: Request = None) -> bool:
        """
        End a user session and remove the session cookie.
        
        Can be called either with a specific session_id or with a request to extract the session from cookies.
        
        Args:
            response: FastAPI response object
            session_id: Session ID to end (optional if request is provided)
            request: FastAPI request object to extract session from cookies (optional if session_id is provided)
            
        Returns:
            bool: True if session was successfully ended, False if no session was found
            
        Raises:
            ValueError: If neither session_id nor request is provided
        """
        if session_id is None and request is None:
            raise ValueError("Either session_id or request must be provided")
            
        # If session_id not provided, try to get it from request cookies
        if session_id is None and request is not None:
            try:
                session_id = await self.cookie.load(request)
            except Exception:
                return False
                
        if not session_id:
            return False
            
        try:
            # Delete session from backend
            await self.backend.delete(session_id)
            # Remove cookie from response
            await self.cookie.delete_from_response(response)
            return True
        except Exception:
            return False
            
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
            session_id = await self.cookie.load(request)
            session = await self.backend.read(session_id)
            if session is None:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany."
                    }
                )
            return session
        except Exception:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Użytkownik nie jest zalogowany."
                }
            )


# Create session verifier for dependency injection
class CustomVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: Exception,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True 