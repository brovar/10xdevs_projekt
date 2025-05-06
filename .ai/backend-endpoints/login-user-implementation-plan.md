# API Endpoint Implementation Plan: Login User

## 1. Przegląd punktu końcowego
Endpoint `/auth/login` umożliwia uwierzytelnianie użytkowników w systemie. Przyjmuje dane logowania (email i hasło), weryfikuje je i w przypadku poprawnej weryfikacji ustanawia sesję poprzez ustawienie HttpOnly Secure cookie. Sukces operacji jest potwierdzany komunikatem, a niepowodzenie odpowiednim kodem błędu.

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/auth/login`
- Parametry: brak
- Request Body:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!"
  }
  ```

## 3. Wykorzystywane typy
- **LoginUserRequest** (z types.py) - model walidacji danych wejściowych
- **LoginUserResponse** (z types.py) - model odpowiedzi (dziedziczący z MessageResponse)
- **MessageResponse** (z types.py) - prosty model zawierający pole message
- Enum types:
  - **UserStatus** - określa możliwe statusy użytkownika (do walidacji)
  - **LogEventType** - określa typ zdarzenia logowania
- Modele bazy danych:
  - **UserModel** - reprezentacja tabeli `users` w bazie danych
  - **LogModel** - reprezentacja tabeli `logs` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK` (wraz z ciasteczkiem sesji w nagłówkach odpowiedzi)
- Response Body (sukces):
  ```json
  {
    "message": "Login successful"
  }
  ```
- Kody błędów:
  - `400 Bad Request` z kodem błędu `INVALID_INPUT` - niepoprawny format danych wejściowych
  - `401 Unauthorized` z różnymi kodami błędów:
    - `INVALID_CREDENTIALS` - nieprawidłowy email lub hasło
    - `USER_INACTIVE` - konto użytkownika jest nieaktywne
  - `500 Internal Server Error` z kodem błędu `LOGIN_FAILED` - błąd wewnętrzny serwera

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Pydantic waliduje dane wejściowe używając modelu `LoginUserRequest`
3. Kontroler wywołuje serwis użytkownika, przekazując zwalidowane dane
4. Serwis weryfikuje dane logowania:
   - Sprawdza, czy użytkownik o podanym adresie email istnieje
   - Jeśli nie istnieje, zwraca błąd `401 Unauthorized` z kodem `INVALID_CREDENTIALS`
   - Jeśli istnieje, weryfikuje hasło używając bcrypt
   - Jeśli hasło jest nieprawidłowe, zwraca błąd `401 Unauthorized` z kodem `INVALID_CREDENTIALS`
   - Sprawdza status użytkownika; jeśli jest inny niż `Active`, zwraca błąd `401 Unauthorized` z kodem `USER_INACTIVE`
5. Serwis tworzy sesję użytkownika:
   - Generuje identyfikator sesji i zapisuje dane sesji
   - Ustawia ciasteczko sesji (HttpOnly, Secure, SameSite=Lax, czas wygaśnięcia 1 tydzień)
6. Serwis loguje zdarzenie logowania w tabeli `logs`
7. Kontroler zwraca odpowiedź sukcesu z kodem `200 OK` i ustawionym ciasteczkiem sesji

## 6. Względy bezpieczeństwa
- **Ochrona przed wyciekiem informacji**:
  - Unikanie ujawniania, czy użytkownik istnieje (ten sam komunikat dla nieistniejącego użytkownika i złego hasła)
  - Ograniczone informacje w logach (bez pełnych danych uwierzytelniających)
- **Ochrona haseł**:
  - Weryfikacja haseł za pomocą bezpiecznych funkcji porównujących hashe (time-safe)
  - Nigdy nie przechowywanie ani nie logowanie surowych haseł
- **Ochrona sesji**:
  - Używanie ciasteczek z flagami HttpOnly (ochrona przed XSS)
  - Używanie flag Secure (wymuszenie HTTPS)
  - Używanie flag SameSite=Lax (ochrona przed CSRF)
  - Krótki czas życia sesji (1 tydzień zgodnie ze specyfikacją)
- **Zapobieganie atakom**:
  - Implementacja rate-limitingu (np. maksymalnie 5 prób logowania na minutę na IP)
  - Opóźnienie odpowiedzi dla nieudanych prób logowania (ochrona przed atakami czasowymi)
  - Implementacja opóźnień wykładniczych przy kolejnych nieudanych próbach logowania

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Niepoprawny format email: `400 Bad Request` z kodem `INVALID_INPUT`
  - Brakujące wymagane pola: `400 Bad Request` z kodem `INVALID_INPUT`
- **Błędy uwierzytelniania**:
  - Nieistniejący użytkownik: `401 Unauthorized` z kodem `INVALID_CREDENTIALS`
  - Nieprawidłowe hasło: `401 Unauthorized` z kodem `INVALID_CREDENTIALS`
  - Konto nieaktywne: `401 Unauthorized` z kodem `USER_INACTIVE`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `LOGIN_FAILED`
  - Problemy z utworzeniem sesji: `500 Internal Server Error` z kodem `LOGIN_FAILED`

## 8. Rozważania dotyczące wydajności
- **Efektywne wyszukiwanie użytkownika**:
  - Indeks na kolumnie `email` przyspiesza wyszukiwanie
- **Zarządzanie sesjami**:
  - Efektywne przechowywanie sesji (rozważenie użycia Redis dla dużej skali)
- **Asynchroniczność**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
- **Optymalizacja walidacji**:
  - Sprawdzanie istnienia użytkownika przed kosztowną weryfikacją hasła

## 9. Etapy wdrożenia
1. **Uzupełnienie modeli bazy danych**:
   - Upewnienie się, że istniejące modele `UserModel` i `LogModel` są odpowiednio skonfigurowane

2. **Implementacja funkcji weryfikacji hasła**:
   ```python
   from passlib.context import CryptContext

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   def verify_password(plain_password: str, hashed_password: str) -> bool:
       return pwd_context.verify(plain_password, hashed_password)
   ```

3. **Rozszerzenie serwisu użytkownika**:
   - Dodanie metody `login_user` do klasy `UserService`
   ```python
   async def login_user(self, login_data: LoginUserRequest, request: Request) -> bool:
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
               message=f"{log_message}: user not found"
           )
           self.db_session.add(log_entry)
           await self.db_session.commit()
           
           raise HTTPException(
               status_code=401,
               detail={
                   "error_code": "INVALID_CREDENTIALS",
                   "message": "Nieprawidłowe dane logowania."
               }
           )
       
       # Add user_id to log now that we have it
       log_entry = LogModel(
           event_type=event_type,
           user_id=user.id,
           ip_address=request.client.host,
           message=log_message
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
                   "message": "Nieprawidłowe dane logowania."
               }
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
                   "message": "Konto użytkownika jest nieaktywne."
               }
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
                   "message": "Wystąpił błąd podczas logowania. Spróbuj ponownie później."
               }
           )
   ```

4. **Implementacja zarządzania sesją**:
   - Utworzenie klasy `SessionManager` do obsługi sesji
   ```python
   from fastapi import Request, Response
   from uuid import uuid4
   import time
   from datetime import datetime, timedelta

   class SessionManager:
       def __init__(self, cookie_name: str = "session", cookie_max_age: int = 604800):  # 7 days in seconds
           self.cookie_name = cookie_name
           self.cookie_max_age = cookie_max_age
       
       def create_session(self, response: Response, user_id: str, user_role: str):
           session_id = str(uuid4())
           expires = datetime.utcnow() + timedelta(seconds=self.cookie_max_age)
           
           # Set cookie - in a real app you'd encrypt/sign this or use a proper session backend
           response.set_cookie(
               key=self.cookie_name,
               value=session_id,
               httponly=True,
               secure=True,  # requires HTTPS in production
               samesite="lax",
               max_age=self.cookie_max_age,
               expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
           )
           
           # In a real implementation, you'd store session data in a database or cache
           # For simplicity, this example doesn't include that part
           
           return session_id
       
       def end_session(self, response: Response):
           response.delete_cookie(
               key=self.cookie_name,
               httponly=True,
               secure=True,
               samesite="lax"
           )
   ```

5. **Utworzenie kontrolera uwierzytelniania**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Request, Response
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger

   from dependencies import get_db_session, get_logger
   from services.user_service import UserService
   from services.session_manager import SessionManager
   from types import LoginUserRequest, LoginUserResponse

   router = APIRouter(prefix="/auth", tags=["auth"])

   session_manager = SessionManager()

   @router.post("/login", response_model=LoginUserResponse)
   async def login_user(
       login_data: LoginUserRequest,
       response: Response,
       request: Request,
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       user_service = UserService(db_session, logger)
       try:
           # Authenticate user
           login_successful = await user_service.login_user(login_data, request)
           
           if login_successful:
               # Here we would retrieve user details and create a session
               # For demonstration, creating a simplified version
               user_result = await db_session.execute(
                   select(UserModel).where(UserModel.email == login_data.email)
               )
               user = user_result.scalars().first()
               
               # Create session
               session_manager.create_session(response, str(user.id), user.role.value)
               
               return {"message": "Login successful"}
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error during login: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "LOGIN_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas logowania. Spróbuj ponownie później."
               }
           )
   ```

6. **Implementacja rate-limitingu**:
   ```python
   from fastapi import Request, HTTPException
   import time
   from collections import defaultdict
   
   # Simple in-memory rate limiter (in production, use Redis or similar)
   class RateLimiter:
       def __init__(self, max_requests: int = 5, window_seconds: int = 60):
           self.max_requests = max_requests
           self.window_seconds = window_seconds
           self.requests = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]
       
       def check_rate_limit(self, request: Request):
           ip = request.client.host
           now = time.time()
           
           # Remove requests outside of current window
           self.requests[ip] = [ts for ts in self.requests[ip] if now - ts < self.window_seconds]
           
           # Check if rate limit is exceeded
           if len(self.requests[ip]) >= self.max_requests:
               raise HTTPException(
                   status_code=429,
                   detail={
                       "error_code": "RATE_LIMIT_EXCEEDED",
                       "message": "Zbyt wiele prób logowania. Spróbuj ponownie później."
                   }
               )
           
           # Add current request timestamp
           self.requests[ip].append(now)
   
   # Create rate limiter instance
   login_rate_limiter = RateLimiter()
   
   # Add to login endpoint
   @router.post("/login", response_model=LoginUserResponse)
   async def login_user(
       login_data: LoginUserRequest,
       response: Response,
       request: Request,
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       # Check rate limit
       login_rate_limiter.check_rate_limit(request)
       
       # Rest of the function remains the same
       ...
   ```

7. **Rejestracja routera w aplikacji głównej**:
   ```python
   from fastapi import FastAPI
   from routers import auth_router

   app = FastAPI()
   app.include_router(auth_router)
   ```

8. **Konfiguracja middlewarów sesji**:
   ```python
   from fastapi.middleware.sessions import SessionMiddleware
   
   app = FastAPI()
   app.add_middleware(
       SessionMiddleware, 
       secret_key="your-secret-key"  # Use a secure random key in production
   )
   ```

9. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy walidacji danych w modelu LoginUserRequest
   - Testy weryfikacji hasła
   - Testy serwisu UserService.login_user
   - Testy kontrolera `/auth/login`
   - Testy rate-limitingu

10. **Aktualizacja dokumentacji API**:
    - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
    - Dodanie przykładów zapytań i odpowiedzi 