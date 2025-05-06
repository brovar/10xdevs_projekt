# API Endpoint Implementation Plan: Get Current User

## 1. Przegląd punktu końcowego
Endpoint `/account` umożliwia pobranie szczegółowych informacji o profilu aktualnie zalogowanego użytkownika. Wymaga uwierzytelnienia poprzez istniejącą sesję (HttpOnly cookie). Zwraca pełne dane profilowe użytkownika, takie jak identyfikator, email, rola, status, imię, nazwisko oraz daty utworzenia i ostatniej aktualizacji.

## 2. Szczegóły żądania
- Metoda HTTP: `GET`
- Struktura URL: `/account`
- Parametry: brak
- Request Body: brak
- Nagłówki: Automatycznie zawiera cookie sesji

## 3. Wykorzystywane typy
- **UserDTO** (z types.py) - model odpowiedzi zawierający dane użytkownika
- **UserBase** (z types.py) - bazowy model użytkownika (jeśli jest używany jako klasa bazowa dla UserDTO)
- Enum types:
  - **UserRole** - określa możliwe role użytkownika (Buyer, Seller, Admin)
  - **UserStatus** - określa możliwe statusy użytkownika (Active, Inactive, Deleted)
- Modele bazy danych:
  - **UserModel** - reprezentacja tabeli `users` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Response Body (sukces):
  ```json
  {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "role": "Buyer",
    "status": "Active",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "timestamp",
    "updated_at": "timestamp" // opcjonalnie
  }
  ```
- Kody błędów:
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - użytkownik nie jest zalogowany
  - `404 Not Found` z kodem błędu `USER_NOT_FOUND` - konto użytkownika nie istnieje (mogło zostać usunięte)
  - `500 Internal Server Error` - błąd wewnętrzny serwera

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Middleware sesji weryfikuje, czy użytkownik jest zalogowany (sprawdza sesję)
3. Jeśli użytkownik nie jest zalogowany, zwracany jest błąd `401 Unauthorized`
4. Jeśli użytkownik jest zalogowany:
   - Z sesji pobierany jest identyfikator użytkownika
   - Kontroler wywołuje serwis użytkownika, przekazując identyfikator
   - Serwis pobiera dane użytkownika z bazy danych
   - Jeśli użytkownik nie istnieje w bazie, zwracany jest błąd `404 Not Found`
   - Jeśli użytkownik istnieje, jego dane są formatowane zgodnie z modelem UserDTO
5. Kontroler zwraca odpowiedź z danymi użytkownika i kodem `200 OK`

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymaga ważnej sesji, implementowanej przez HttpOnly cookie
  - Sesja powinna być weryfikowana przed dostępem do danych
- **Autoryzacja**:
  - Użytkownik może uzyskać dostęp tylko do własnych danych
  - Brak możliwości dostępu do danych innych użytkowników przez manipulację parametrami
- **Ochrona danych wrażliwych**:
  - Hasło nigdy nie powinno być zwracane, nawet w formie haszowanej
  - Dane osobowe są chronione przez uwierzytelnianie
- **Obsługa wygasłych sesji**:
  - Poprawna obsługa wygasłych sesji oraz informowanie użytkownika o konieczności ponownego logowania

## 7. Obsługa błędów
- **Błędy uwierzytelniania**:
  - Brak sesji/użytkownik niezalogowany: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Wygasła sesja: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
- **Błędy biznesowe**:
  - Użytkownik nie istnieje w bazie danych: `404 Not Found` z kodem `USER_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z odpowiednim komunikatem

## 8. Rozważania dotyczące wydajności
- **Efektywne zapytania do bazy danych**:
  - Użycie indeksu na kolumnie ID użytkownika dla szybkiego wyszukiwania
  - Pobieranie tylko potrzebnych pól
- **Cachowanie**:
  - Rozważenie cachowania profilu użytkownika na czas sesji, jeśli profil jest często odczytywany
  - Invalidacja cache przy aktualizacji profilu
- **Asynchroniczność**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)

## 9. Etapy wdrożenia
1. **Sprawdzenie/rozszerzenie istniejącej zależności do sprawdzania uwierzytelnienia**:
   ```python
   from fastapi import Request, HTTPException

   async def require_authenticated(request: Request) -> dict:
       """
       Dependency that checks if user is authenticated.
       Returns user data from session if authenticated, otherwise raises 401.
       """
       user_id = request.session.get("user_id")
       if not user_id:
           raise HTTPException(
               status_code=401,
               detail={
                   "error_code": "NOT_AUTHENTICATED",
                   "message": "Użytkownik nie jest zalogowany."
               }
           )
       
       return {
           "user_id": user_id,
           "role": request.session.get("role")
       }
   ```

2. **Implementacja metody w serwisie użytkownika**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from logging import Logger
   from fastapi import HTTPException
   from uuid import UUID

   from models.user_model import UserModel
   from types import UserDTO

   class UserService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
           
       async def get_current_user(self, user_id: UUID) -> UserDTO:
           """
           Retrieve current user's profile data from database.
           Raises 404 if user doesn't exist.
           """
           try:
               # Query database for user
               result = await self.db_session.execute(
                   select(UserModel).where(UserModel.id == user_id)
               )
               user = result.scalars().first()
               
               # Check if user exists
               if not user:
                   self.logger.warning(f"User with ID {user_id} not found in database")
                   raise HTTPException(
                       status_code=404,
                       detail={
                           "error_code": "USER_NOT_FOUND",
                           "message": "Nie znaleziono użytkownika."
                       }
                   )
               
               # Convert to DTO and return
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
               self.logger.error(f"Error retrieving user data: {str(e)}")
               raise HTTPException(
                   status_code=500,
                   detail={
                       "error_code": "FETCH_FAILED",
                       "message": "Wystąpił błąd podczas pobierania danych użytkownika."
                   }
               )
   ```

3. **Implementacja kontrolera**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Request
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   from uuid import UUID

   from dependencies import get_db_session, get_logger, require_authenticated
   from services.user_service import UserService
   from types import UserDTO

   router = APIRouter(tags=["account"])

   @router.get("/account", response_model=UserDTO)
   async def get_current_user(
       request: Request,
       session_data: dict = Depends(require_authenticated),
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       try:
           # Get user ID from session
           user_id = session_data["user_id"]
           
           # Call service to get user data
           user_service = UserService(db_session, logger)
           user_data = await user_service.get_current_user(UUID(user_id))
           
           return user_data
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error retrieving user profile: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas pobierania profilu użytkownika."
               }
           )
   ```

4. **Integracja z istniejącą konfiguracją routerów**:
   ```python
   from fastapi import FastAPI
   from routers import auth_router, account_router

   app = FastAPI()
   app.include_router(auth_router)
   app.include_router(account_router)
   ```

5. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy metody `get_current_user` w `UserService`:
     - Test z istniejącym użytkownikiem
     - Test z nieistniejącym użytkownikiem (oczekiwane 404)
     - Test z błędem bazy danych (oczekiwane 500)
   - Testy endpointu `/account`:
     - Test z zalogowanym użytkownikiem
     - Test z niezalogowanym użytkownikiem (oczekiwane 401)
     - Test gdy sesja istnieje, ale użytkownik nie istnieje (oczekiwane 404)

6. **Aktualizacja dokumentacji API**:
   - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
   - Dodanie przykładów odpowiedzi
   - Wyjaśnienie, że endpoint wymaga zalogowanego użytkownika 