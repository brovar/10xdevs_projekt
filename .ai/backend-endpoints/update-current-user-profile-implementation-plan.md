# API Endpoint Implementation Plan: Update Current User Profile

## 1. Przegląd punktu końcowego
Endpoint `/account` z metodą PATCH umożliwia aktualizację danych profilu aktualnie zalogowanego użytkownika. Pozwala na zmianę opcjonalnych pól osobowych, takich jak imię (first_name) i nazwisko (last_name). Endpoint wymaga uwierzytelnienia poprzez istniejącą sesję, weryfikuje poprawność danych wejściowych, zapisuje zmiany w bazie danych oraz zwraca zaktualizowane dane użytkownika.

## 2. Szczegóły żądania
- Metoda HTTP: `PATCH`
- Struktura URL: `/account`
- Parametry: brak
- Request Body:
  ```json
  {
    "first_name": "John",  // Opcjonalne
    "last_name": "Doe"     // Opcjonalne
  }
  ```
  Oba pola są opcjonalne, ale żądanie musi zawierać co najmniej jedno z nich.

## 3. Wykorzystywane typy
- **UpdateUserRequest** (z types.py) - model walidacji danych wejściowych, zawierający opcjonalne pola `first_name` i `last_name`
- **UserDTO** (z types.py) - model odpowiedzi zawierający zaktualizowane dane użytkownika
- Enum types:
  - **UserStatus** - określa możliwe statusy użytkownika (do walidacji aktywności konta)
  - **LogEventType** - do logowania zdarzenia aktualizacji profilu
- Modele bazy danych:
  - **UserModel** - reprezentacja tabeli `users` w bazie danych
  - **LogModel** - reprezentacja tabeli `logs` w bazie danych (do rejestrowania zdarzenia aktualizacji)

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Response Body (sukces): pełny obiekt użytkownika z aktualizacjami (model UserDTO)
  ```json
  {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "role": "Buyer",
    "status": "Active",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "timestamp",
    "updated_at": "timestamp" 
  }
  ```
- Kody błędów:
  - `400 Bad Request` z kodem błędu `INVALID_INPUT` - niepoprawny format danych wejściowych
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - użytkownik nie jest zalogowany
  - `404 Not Found` z kodem błędu `USER_NOT_FOUND` - konto użytkownika nie istnieje
  - `500 Internal Server Error` z kodem błędu `PROFILE_UPDATE_FAILED` - błąd wewnętrzny serwera podczas aktualizacji profilu

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Middleware sesji weryfikuje, czy użytkownik jest zalogowany (sprawdza sesję)
3. Jeśli użytkownik nie jest zalogowany, zwracany jest błąd `401 Unauthorized`
4. Jeśli użytkownik jest zalogowany:
   - Pydantic waliduje dane wejściowe zgodnie z modelem UpdateUserRequest
   - Z sesji pobierany jest identyfikator użytkownika
   - Kontroler wywołuje serwis użytkownika, przekazując identyfikator i dane aktualizacji
   - Serwis weryfikuje istnienie użytkownika w bazie danych
   - Jeśli użytkownik nie istnieje, zwracany jest błąd `404 Not Found`
   - Serwis aktualizuje tylko te pola, które zostały przekazane w żądaniu
   - Serwis zapisuje zmiany w bazie danych, ustawiając pole updated_at na aktualny czas
   - Serwis rejestruje zdarzenie aktualizacji profilu w tabeli logs
   - Serwis pobiera i zwraca zaktualizowane dane użytkownika
5. Kontroler zwraca odpowiedź z zaktualizowanymi danymi użytkownika i kodem `200 OK`

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymaga ważnej sesji, implementowanej przez HttpOnly cookie
  - Sesja powinna być weryfikowana przed dostępem do danych
- **Autoryzacja**:
  - Użytkownik może aktualizować tylko własne dane
  - Brak możliwości modyfikacji danych innych użytkowników
- **Walidacja danych**:
  - Walidacja typów danych i długości pól przez Pydantic
  - Sanityzacja danych wejściowych, aby zapobiec atakom XSS
- **Ochrona przed atakami**:
  - Zabezpieczenie przed atakami CSRF
  - Ochrona przed manipulacją sesji

## 7. Obsługa błędów
- **Błędy walidacji wejścia**:
  - Niepoprawny format danych: `400 Bad Request` z kodem `INVALID_INPUT`
  - Dane przekraczające dopuszczalną długość: `400 Bad Request` z kodem `INVALID_INPUT`
- **Błędy uwierzytelniania**:
  - Brak sesji/użytkownik niezalogowany: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Wygasła sesja: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
- **Błędy biznesowe**:
  - Użytkownik nie istnieje w bazie danych: `404 Not Found` z kodem `USER_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `PROFILE_UPDATE_FAILED`

## 8. Rozważania dotyczące wydajności
- **Optymalizacja zapytań do bazy danych**:
  - Aktualizacja tylko wymaganych pól (partial update)
  - Unikanie niepotrzebnych zapytań do bazy danych
- **Walidacja**:
  - Efektywna walidacja danych wejściowych przez Pydantic
- **Asynchroniczność**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
- **Indeksowanie**:
  - Wykorzystanie istniejącego indeksu na kolumnie ID użytkownika

## 9. Etapy wdrożenia
1. **Rozszerzenie serwisu użytkownika o metodę update_user_profile**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update
   from logging import Logger
   from fastapi import HTTPException
   from uuid import UUID
   from datetime import datetime

   from models.user_model import UserModel
   from models.log_model import LogModel
   from types import UpdateUserRequest, UserDTO, LogEventType

   class UserService:
       # Istniejące metody...
       
       async def update_user_profile(self, user_id: UUID, update_data: UpdateUserRequest) -> UserDTO:
           """
           Update current user's profile data.
           Only updates fields that are provided in update_data.
           Raises 404 if user doesn't exist.
           """
           try:
               # Check if user exists
               result = await self.db_session.execute(
                   select(UserModel).where(UserModel.id == user_id)
               )
               user = result.scalars().first()
               
               if not user:
                   self.logger.warning(f"User with ID {user_id} not found in database")
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
                   event_type=LogEventType.PASSWORD_CHANGE,  # Use an appropriate event type
                   user_id=user_id,
                   message=f"User {user_id} updated profile information"
               )
               self.db_session.add(log_entry)
               
               # Commit changes
               await self.db_session.commit()
               
               # Refresh user object to get updated data
               await self.db_session.refresh(user)
               
               # Return updated user
               return UserDTO(
                   id=user.id,
                   email=user.email,
                   role=user.role,
                   status=user.status,
                   first_name=user.first_name,
                   last_name=user.last_name,
                   created_at=user.created_at,
                   updated_at=user.updated_at
               )
               
           except HTTPException:
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
   ```

2. **Implementacja kontrolera aktualizacji profilu**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Request
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   from uuid import UUID

   from dependencies import get_db_session, get_logger, require_authenticated
   from services.user_service import UserService
   from types import UpdateUserRequest, UserDTO

   router = APIRouter(tags=["account"])

   # Existing GET /account endpoint...

   @router.patch("/account", response_model=UserDTO)
   async def update_current_user_profile(
       update_data: UpdateUserRequest,
       request: Request,
       session_data: dict = Depends(require_authenticated),
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       try:
           # Get user ID from session
           user_id = session_data["user_id"]
           
           # Validate that at least one field is provided
           if update_data.first_name is None and update_data.last_name is None:
               raise HTTPException(
                   status_code=400,
                   detail={
                       "error_code": "INVALID_INPUT",
                       "message": "Należy podać co najmniej jedno pole do aktualizacji."
                   }
               )
           
           # Call service to update user profile
           user_service = UserService(db_session, logger)
           updated_user = await user_service.update_user_profile(UUID(user_id), update_data)
           
           return updated_user
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error updating user profile: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "PROFILE_UPDATE_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas aktualizacji profilu użytkownika."
               }
           )
   ```

3. **Upewnienie się, że model UpdateUserRequest jest poprawnie zdefiniowany**:
   ```python
   # W types.py model już powinien istnieć, ale upewnijmy się, że ma poprawną definicję:
   
   class UpdateUserRequest(BaseModel):
       first_name: Optional[str] = None
       last_name: Optional[str] = None
       
       # Możemy dodać walidatory, np. dla długości pól
       @validator('first_name')
       def validate_first_name(cls, v):
           if v is not None and len(v) > 100:  # Zgodnie z definicją bazy danych
               raise ValueError('Imię nie może przekraczać 100 znaków')
           return v
           
       @validator('last_name')
       def validate_last_name(cls, v):
           if v is not None and len(v) > 100:  # Zgodnie z definicją bazy danych
               raise ValueError('Nazwisko nie może przekraczać 100 znaków')
           return v
   ```

4. **Dodanie nowego typu zdarzenia logów (jeśli nie istnieje)**:
   ```python
   # W types.py, w enum LogEventType dodać:
   USER_PROFILE_UPDATE = "USER_PROFILE_UPDATE"
   
   # I zaktualizować metodę w UserService:
   log_entry = LogModel(
       event_type=LogEventType.USER_PROFILE_UPDATE,
       user_id=user_id,
       message=f"User {user_id} updated profile information"
   )
   ```

5. **Aktualizacja routera w aplikacji głównej** (jeśli jeszcze nie istnieje):
   ```python
   from fastapi import FastAPI
   from routers import auth_router, account_router

   app = FastAPI()
   app.include_router(auth_router)
   app.include_router(account_router)
   ```

6. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy metody `update_user_profile` w `UserService`:
     - Test z poprawną aktualizacją tylko imienia
     - Test z poprawną aktualizacją tylko nazwiska
     - Test z poprawną aktualizacją obu pól
     - Test z nieistniejącym użytkownikiem (oczekiwane 404)
     - Test z błędem bazy danych (oczekiwane 500)
   - Testy endpointu `PATCH /account`:
     - Test z zalogowanym użytkownikiem i poprawnymi danymi
     - Test z niezalogowanym użytkownikiem (oczekiwane 401)
     - Test z zalogowanym użytkownikiem, ale nieprawidłowymi danymi (oczekiwane 400)
     - Test z brakiem pól do aktualizacji (oczekiwane 400)

7. **Aktualizacja dokumentacji API**:
   - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
   - Dodanie przykładów żądań i odpowiedzi
   - Opisanie ograniczeń dotyczących aktualizowanych pól 