# API Endpoint Implementation Plan: Change Current User Password

## 1. Przegląd punktu końcowego
Endpoint `/account/password` z metodą PUT umożliwia zmianę hasła aktualnie zalogowanego użytkownika. Wymaga uwierzytelnienia poprzez istniejącą sesję oraz weryfikacji aktualnego hasła użytkownika przed ustawieniem nowego. Nowe hasło musi spełniać określoną politykę bezpieczeństwa (minimalna długość, wymagane znaki). Endpoint zapisuje zmiany w bazie danych, rejestruje zdarzenie w logach systemowych i zwraca komunikat o pomyślnej zmianie hasła.

## 2. Szczegóły żądania
- Metoda HTTP: `PUT`
- Struktura URL: `/account/password`
- Parametry: brak
- Request Body:
  ```json
  {
    "current_password": "OldPassword1!",
    "new_password": "NewPassword123!"
  }
  ```
  Oba pola są wymagane. Brak któregokolwiek spowoduje błąd walidacji.

## 3. Wykorzystywane typy
- **ChangePasswordRequest** (z types.py) - model walidacji danych wejściowych, zawierający pola `current_password` i `new_password`
- **ChangePasswordResponse** (z types.py) - model odpowiedzi (dziedziczący z MessageResponse)
- **MessageResponse** (z types.py) - prosty model zawierający pole message
- Enum types:
  - **LogEventType** - do logowania zdarzenia zmiany hasła (wartość PASSWORD_CHANGE)
- Modele bazy danych:
  - **UserModel** - reprezentacja tabeli `users` w bazie danych
  - **LogModel** - reprezentacja tabeli `logs` w bazie danych (do rejestrowania zdarzenia zmiany hasła)

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Response Body (sukces):
  ```json
  {
    "message": "Password updated successfully"
  }
  ```
- Kody błędów:
  - `400 Bad Request` z różnymi kodami błędów:
    - `INVALID_INPUT` - niepoprawny format danych wejściowych
    - `PASSWORD_POLICY_VIOLATED` - nowe hasło nie spełnia wymagań polityki
  - `401 Unauthorized` z różnymi kodami błędów:
    - `NOT_AUTHENTICATED` - użytkownik nie jest zalogowany
    - `INVALID_CURRENT_PASSWORD` - podane aktualne hasło jest nieprawidłowe
  - `500 Internal Server Error` z kodem błędu `PASSWORD_UPDATE_FAILED` - błąd wewnętrzny serwera

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Middleware sesji weryfikuje, czy użytkownik jest zalogowany (sprawdza sesję)
3. Jeśli użytkownik nie jest zalogowany, zwracany jest błąd `401 Unauthorized`
4. Jeśli użytkownik jest zalogowany:
   - Pydantic waliduje dane wejściowe zgodnie z modelem ChangePasswordRequest
   - Z sesji pobierany jest identyfikator użytkownika
   - Kontroler wywołuje serwis użytkownika, przekazując identyfikator i dane zmiany hasła
   - Serwis pobiera dane użytkownika z bazy danych
   - Serwis weryfikuje, czy podane aktualne hasło zgadza się z haszem w bazie danych
   - Jeśli aktualne hasło jest nieprawidłowe, zwracany jest błąd `401 Unauthorized` z kodem `INVALID_CURRENT_PASSWORD`
   - Serwis sprawdza, czy nowe hasło spełnia politykę bezpieczeństwa
   - Jeśli nowe hasło nie spełnia wymagań, zwracany jest błąd `400 Bad Request` z kodem `PASSWORD_POLICY_VIOLATED`
   - Serwis generuje nowy hasz dla nowego hasła
   - Serwis aktualizuje rekord użytkownika w bazie danych z nowym haszem hasła
   - Serwis rejestruje zdarzenie zmiany hasła w tabeli logs
5. Kontroler zwraca odpowiedź z komunikatem o pomyślnej zmianie hasła i kodem `200 OK`

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymaga ważnej sesji, implementowanej przez HttpOnly cookie
  - Weryfikacja aktualnego hasła przed zmianą na nowe
- **Polityka haseł**:
  - Wymaganie minimalnej długości hasła (10 znaków)
  - Wymaganie różnych typów znaków (wielkich liter, małych liter, cyfr/znaków specjalnych)
  - Weryfikacja, czy nowe hasło różni się od starego (opcjonalnie)
- **Bezpieczne przechowywanie haseł**:
  - Używanie silnego algorytmu haszowania (bcrypt)
  - Nigdy nie przechowywanie jawnych haseł w bazie danych
- **Ochrona przed atakami**:
  - Implementacja rate-limitingu dla zapobiegania atakom brute-force
  - Stosowanie stałego czasu odpowiedzi dla zapobiegania atakom czasowym
  - Niejawność informacji o tym, dlaczego konkretne hasło nie spełnia wymogów

## 7. Obsługa błędów
- **Błędy walidacji wejścia**:
  - Brakujące pola: `400 Bad Request` z kodem `INVALID_INPUT`
  - Niepoprawny format danych: `400 Bad Request` z kodem `INVALID_INPUT`
  - Nowe hasło nie spełnia polityki: `400 Bad Request` z kodem `PASSWORD_POLICY_VIOLATED`
- **Błędy uwierzytelniania**:
  - Użytkownik niezalogowany: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Niepoprawne aktualne hasło: `401 Unauthorized` z kodem `INVALID_CURRENT_PASSWORD`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `PASSWORD_UPDATE_FAILED`

## 8. Rozważania dotyczące wydajności
- **Kosztowne operacje haszowania**:
  - Haszowanie haseł jest procesem wymagającym obliczeniowo
  - Należy zrównoważyć bezpieczeństwo (liczba rund haszowania) z wydajnością
- **Walidacja**:
  - Efektywna walidacja danych wejściowych przez Pydantic
- **Asynchroniczność**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
- **Opóźnienie odpowiedzi**:
  - Implementacja stałego czasu odpowiedzi dla zapobiegania atakom czasowym

## 9. Etapy wdrożenia
1. **Rozszerzenie walidatorów i funkcji pomocniczych do obsługi haseł**:
   ```python
   from passlib.context import CryptContext

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   def get_password_hash(password: str) -> str:
       return pwd_context.hash(password)

   def verify_password(plain_password: str, hashed_password: str) -> bool:
       return pwd_context.verify(plain_password, hashed_password)
   ```

2. **Rozszerzenie serwisu użytkownika o metodę change_password**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update
   from logging import Logger
   from fastapi import HTTPException
   from uuid import UUID
   from datetime import datetime

   from models.user_model import UserModel
   from models.log_model import LogModel
   from types import ChangePasswordRequest, LogEventType

   class UserService:
       # Istniejące metody...
       
       async def change_password(self, user_id: UUID, password_data: ChangePasswordRequest, request_ip: str = None) -> bool:
           """
           Change user's password.
           Verifies current password, validates new password policy, updates password hash.
           Raises appropriate exceptions for validation errors.
           Returns True if successful.
           """
           try:
               # Find user by ID
               result = await self.db_session.execute(
                   select(UserModel).where(UserModel.id == user_id)
               )
               user = result.scalars().first()
               
               if not user:
                   self.logger.warning(f"User with ID {user_id} not found during password change")
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
                       message=f"Failed password change attempt for user {user_id}: invalid current password"
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
                   message=f"Password changed successfully for user {user_id}"
               )
               self.db_session.add(log_entry)
               
               # Commit all changes
               await self.db_session.commit()
               
               return True
               
           except HTTPException:
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
   ```

3. **Implementacja kontrolera zmiany hasła**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Request
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   from uuid import UUID

   from dependencies import get_db_session, get_logger, require_authenticated
   from services.user_service import UserService
   from types import ChangePasswordRequest, ChangePasswordResponse

   router = APIRouter(tags=["account"])

   # Existing endpoints...

   @router.put("/account/password", response_model=ChangePasswordResponse)
   async def change_current_user_password(
       password_data: ChangePasswordRequest,
       request: Request,
       session_data: dict = Depends(require_authenticated),
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       try:
           # Get user ID from session
           user_id = session_data["user_id"]
           
           # Get client IP for logging
           client_ip = request.client.host
           
           # Call service to change password
           user_service = UserService(db_session, logger)
           success = await user_service.change_password(
               UUID(user_id), 
               password_data, 
               client_ip
           )
           
           return {"message": "Password updated successfully"}
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error changing password: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "PASSWORD_UPDATE_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas aktualizacji hasła."
               }
           )
   ```

4. **Upewnienie się, że model ChangePasswordRequest jest poprawnie zdefiniowany**:
   ```python
   # W types.py model już powinien istnieć, ale upewnijmy się, że ma poprawną definicję:
   
   class ChangePasswordRequest(BaseModel):
       current_password: str
       new_password: str
       
       @validator('new_password')
       def password_strength(cls, v):
           if len(v) < 10:
               raise ValueError('Password must be at least 10 characters long')
           if not re.search(r'[A-Z]', v):
               raise ValueError('Password must contain an uppercase letter')
           if not re.search(r'[a-z]', v):
               raise ValueError('Password must contain a lowercase letter')
           if not re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', v):
               raise ValueError('Password must contain a digit or special character')
           return v
   
   class ChangePasswordResponse(MessageResponse):
       pass
   ```

5. **Implementacja rate-limitingu dla endpointu zmiany hasła**:
   ```python
   from fastapi import Request, HTTPException
   import time
   from collections import defaultdict
   
   # Simple in-memory rate limiter for password changes
   class PasswordChangeRateLimiter:
       def __init__(self, max_attempts: int = 5, window_seconds: int = 300):  # 5 attempts per 5 minutes
           self.max_attempts = max_attempts
           self.window_seconds = window_seconds
           self.attempts = defaultdict(list)  # user_id -> [timestamp1, timestamp2, ...]
       
       def check_rate_limit(self, user_id: str):
           now = time.time()
           
           # Remove attempts outside of current window
           self.attempts[user_id] = [ts for ts in self.attempts[user_id] if now - ts < self.window_seconds]
           
           # Check if rate limit is exceeded
           if len(self.attempts[user_id]) >= self.max_attempts:
               raise HTTPException(
                   status_code=429,
                   detail={
                       "error_code": "RATE_LIMIT_EXCEEDED",
                       "message": "Zbyt wiele prób zmiany hasła. Spróbuj ponownie później."
                   }
               )
           
           # Add current attempt timestamp
           self.attempts[user_id].append(now)
   
   # Create rate limiter instance
   password_rate_limiter = PasswordChangeRateLimiter()
   
   # Add to controller
   @router.put("/account/password", response_model=ChangePasswordResponse)
   async def change_current_user_password(
       # ... existing parameters
   ):
       # Get user ID from session
       user_id = session_data["user_id"]
       
       # Check rate limit
       password_rate_limiter.check_rate_limit(user_id)
       
       # ... rest of the function
   ```

6. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy funkcji `verify_password` i `get_password_hash`
   - Testy metody `change_password` w `UserService`:
     - Test z poprawnymi danymi
     - Test z nieprawidłowym aktualnym hasłem
     - Test z nowym hasłem niespełniającym polityki bezpieczeństwa
     - Test z nieistniejącym użytkownikiem
     - Test z błędem bazy danych
   - Testy endpointu `PUT /account/password`:
     - Test z poprawnymi danymi
     - Test z nieprawidłowym aktualnym hasłem
     - Test z nowym hasłem niespełniającym polityki
     - Test z niezalogowanym użytkownikiem
     - Test rate-limitingu

7. **Aktualizacja dokumentacji API**:
   - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
   - Dodanie przykładów żądań i odpowiedzi
   - Opisanie polityki bezpieczeństwa haseł 