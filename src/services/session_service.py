from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel


class SessionData(BaseModel):
    user_id: str  # Store UUID as string to avoid UUID conversion issues
    user_role: str


class SessionService:
    """A simpler session service implementation using JWT-signed cookies"""

    def __init__(
        self,
        cookie_name: str = "session",
        cookie_max_age: int = 604800,  # 7 days in seconds
        secret_key: str = "CHANGE_ME_IN_PRODUCTION",
    ):
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.secret_key = secret_key
        self.sessions: Dict[str, SessionData] = {}

    async def create_session(
        self, response: Response, user_id: UUID, user_role: str
    ) -> str:
        """
        Create a new session for the user and set the session cookie.

        Args:
            response: FastAPI response object to set cookie
            user_id: User ID to store in session
            user_role: User role to store in session

        Returns:
            str: The session ID
        """
        try:
            # Generate a session ID
            session_id = str(uuid4())

            # Store session data in memory - convert UUID to string
            user_id_str = str(user_id)
            session_data = SessionData(
                user_id=user_id_str, user_role=user_role
            )
            self.sessions[session_id] = session_data

            # Create a JWT token with the session ID
            payload = {
                "session_id": session_id,
                "exp": datetime.utcnow()
                + timedelta(seconds=self.cookie_max_age),
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")

            # Set the cookie
            response.set_cookie(
                key=self.cookie_name,
                value=token,
                max_age=self.cookie_max_age,
                httponly=True,
                secure=True,
                samesite="lax",
            )

            return session_id
        except Exception as e:
            # Log the error with detailed information
            print(f"Error creating session: {str(e)}")
            print(f"Error type: {type(e)}")
            raise

    async def end_session(
        self,
        response: Response,
        session_id: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> bool:
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
                token = request.cookies.get(self.cookie_name)
                if token:
                    payload = jwt.decode(
                        token, self.secret_key, algorithms=["HS256"]
                    )
                    session_id = payload.get("session_id")
            except Exception:
                # Invalid token or other error
                pass

        if not session_id:
            # No valid session to end
            response.delete_cookie(key=self.cookie_name)
            return False

        # Delete session from memory if it exists
        if session_id in self.sessions:
            del self.sessions[session_id]

        # Clear the cookie
        response.delete_cookie(key=self.cookie_name)
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
            # Get session ID from cookie
            token = request.cookies.get(self.cookie_name)
            if not token:
                raise ValueError("No session cookie found")

            # Decode the JWT token
            try:
                payload = jwt.decode(
                    token, self.secret_key, algorithms=["HS256"]
                )
            except jwt.ExpiredSignatureError:
                raise ValueError("Session expired")
            except jwt.InvalidTokenError:
                raise ValueError("Invalid session token")

            session_id = payload.get("session_id")
            if not session_id:
                raise ValueError("Invalid session token format")

            # Get session data from memory
            session_data = self.sessions.get(session_id)
            if not session_data:
                raise ValueError("Session not found in server memory")

            return session_data
        except Exception as e:
            print(f"Session error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Użytkownik nie jest zalogowany.",
                },
            )
