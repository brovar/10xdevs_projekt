# API Endpoint Implementation Plan: Register User

## 1. Przegląd punktu końcowego
Endpoint `/auth/register` umożliwia rejestrację nowych użytkowników w systemie z rolą Buyer (Kupujący) lub Seller (Sprzedający). Waliduje dane wejściowe, haszuje hasło i tworzy nowy rekord użytkownika w bazie danych. Endpoint zwraca szczegóły utworzonego użytkownika wraz z wygenerowanym identyfikatorem.

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/auth/register`
- Parametry: brak
- Request Body:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!",
    "role": "Buyer" // lub "Seller"
  }
  ```

## 3. Wykorzystywane typy
- **RegisterUserRequest** (z types.py) - model walidacji danych wejściowych
- **RegisterUserResponse** (z types.py) - model odpowiedzi
- **UserBase** (z types.py) - bazowy model użytkownika
- Enum types:
  - **UserRole** - określa możliwe role użytkownika
  - **UserStatus** - określa możliwe statusy użytkownika
- Modele bazy danych:
  - **UserModel** - reprezentacja tabeli `users` w bazie danych (do utworzenia)

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `201 Created`
- Response Body (sukces):
  ```json
  {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "role": "Buyer",
    "status": "Active",
    "first_name": null,
    "last_name": null,
    "created_at": "timestamp"
  }
  ```
- Kody błędów:
  - `400 Bad Request` z różnymi kodami błędów:
    - `INVALID_INPUT` - niepoprawny format danych wejściowych
    - `PASSWORD_POLICY_VIOLATED` - hasło nie spełnia wymagań polityki
    - `INVALID_ROLE` - nieprawidłowa rola użytkownika
  - `409 Conflict` z kodem błędu `EMAIL_EXISTS` - podany adres email już istnieje
  - `500 Internal Server Error` z kodem błędu `REGISTRATION_FAILED` - błąd wewnętrzny serwera

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Pydantic waliduje dane wejściowe używając modelu `RegisterUserRequest`
3. Kontroler wywołuje serwis użytkownika, przekazując zwalidowane dane
4. Serwis sprawdza, czy użytkownik o podanym adresie email już istnieje
5. Jeśli użytkownik istnieje, zwracany jest błąd `409 Conflict`
6. Jeśli użytkownik nie istnieje:
   - Serwis haszuje hasło użytkownika
   - Tworzy nowy rekord w tabeli `users`
   - Zapisuje zdarzenie w tabeli `logs`
   - Zwraca dane nowo utworzonego użytkownika
7. Kontroler formatuje odpowiedź zgodnie z modelem `RegisterUserResponse` i zwraca ją z kodem `201 Created`

## 6. Względy bezpieczeństwa
- **Walidacja wejścia**:
  - Walidacja formatu email przez Pydantic `EmailStr`
  - Walidacja siły hasła przez własny walidator
  - Walidacja roli użytkownika (tylko Buyer lub Seller)
- **Haszowanie haseł**:
  - Użycie biblioteki `passlib` z algorytmem bcrypt
  - Przechowywanie tylko hasza, nigdy surowego hasła
- **Zapobieganie atakom**:
  - Ochrona przed SQL Injection przez użycie ORM
  - Ochrona przed XSS przez walidację Pydantic
  - Rate-limiting na poziomie API dla zapobiegania atakom brute-force

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Niepoprawny format email: `400 Bad Request` z kodem `INVALID_INPUT`
  - Hasło nie spełnia wymagań: `400 Bad Request` z kodem `PASSWORD_POLICY_VIOLATED`
  - Nieprawidłowa rola: `400 Bad Request` z kodem `INVALID_ROLE`
- **Błędy biznesowe**:
  - Email już istnieje: `409 Conflict` z kodem `EMAIL_EXISTS`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `REGISTRATION_FAILED`

## 8. Rozważania dotyczące wydajności
- **Indeksacja bazy danych**:
  - Kolumna `email` posiada indeks UNIQUE, co przyspiesza wyszukiwanie
- **Async**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
- **Optymalizacja walidacji**:
  - Weryfikacja istnienia emaila przed kosztownym haszowaniem hasła

## 9. Etapy wdrożenia
1. **Przygotowanie modelu bazy danych**:
   - Utworzenie klasy `UserModel` dla SQLAlchemy odpowiadającej tabeli `users`
   ```python
   class UserModel(Base):
       __tablename__ = "users"
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       email = Column(String(255), unique=True, nullable=False)
       password_hash = Column(Text, nullable=False)
       role = Column(Enum(UserRole), nullable=False)
       status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
       first_name = Column(String(100), nullable=True)
       last_name = Column(String(100), nullable=True)
       created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
       updated_at = Column(DateTime(timezone=True), nullable=True)
   ```

2. **Utworzenie serwisu użytkownika**:
   - Implementacja klasy `UserService` z metodą `register_user`
   ```python
   class UserService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
           
       async def register_user(self, user_data: RegisterUserRequest) -> UserBase:
           # Check if email exists
           existing_user = await self.db_session.execute(
               select(UserModel).where(UserModel.email == user_data.email)
           )
           if existing_user.scalars().first():
               raise HTTPException(
                   status_code=409,
                   detail={
                       "error_code": "EMAIL_EXISTS",
                       "message": "Użytkownik o podanym adresie email już istnieje."
                   }
               )
           
           # Hash password
           password_hash = get_password_hash(user_data.password)
           
           # Create new user
           new_user = UserModel(
               email=user_data.email,
               password_hash=password_hash,
               role=user_data.role,
               status=UserStatus.ACTIVE
           )
           
           try:
               self.db_session.add(new_user)
               await self.db_session.commit()
               await self.db_session.refresh(new_user)
               
               # Log event
               log_entry = LogModel(
                   event_type=LogEventType.USER_REGISTER,
                   user_id=new_user.id,
                   message=f"Registered new user with email {user_data.email} and role {user_data.role}"
               )
               self.db_session.add(log_entry)
               await self.db_session.commit()
               
               return UserBase(
                   id=new_user.id,
                   email=new_user.email,
                   role=new_user.role,
                   status=new_user.status,
                   first_name=new_user.first_name,
                   last_name=new_user.last_name,
                   created_at=new_user.created_at
               )
           except Exception as e:
               await self.db_session.rollback()
               self.logger.error(f"Failed to register user: {str(e)}")
               raise HTTPException(
                   status_code=500,
                   detail={
                       "error_code": "REGISTRATION_FAILED",
                       "message": "Wystąpił błąd podczas rejestracji. Spróbuj ponownie później."
                   }
               )
   ```

3. **Implementacja funkcji pomocniczych do haszowania hasła**:
   ```python
   from passlib.context import CryptContext

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   def get_password_hash(password: str) -> str:
       return pwd_context.hash(password)
   ```

4. **Utworzenie kontrolera**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger

   from dependencies import get_db_session, get_logger
   from services.user_service import UserService
   from types import RegisterUserRequest, RegisterUserResponse

   router = APIRouter(prefix="/auth", tags=["auth"])

   @router.post("/register", response_model=RegisterUserResponse, status_code=201)
   async def register_user(
       user_data: RegisterUserRequest,
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger)
   ):
       user_service = UserService(db_session, logger)
       try:
           new_user = await user_service.register_user(user_data)
           return new_user
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error during user registration: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "REGISTRATION_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas rejestracji. Spróbuj ponownie później."
               }
           )
   ```

5. **Implementacja zależności (dependencies)**:
   ```python
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   import logging

   from database import get_session

   async def get_db_session() -> AsyncSession:
       async with get_session() as session:
           yield session

   def get_logger() -> Logger:
       return logging.getLogger("app")
   ```

6. **Rejestracja routera w aplikacji głównej**:
   ```python
   from fastapi import FastAPI
   from routers import auth_router

   app = FastAPI()
   app.include_router(auth_router)
   ```

7. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy walidacji danych w modelu RegisterUserRequest
   - Testy serwisu UserService
   - Testy kontrolera `/auth/register`

8. **Aktualizacja dokumentacji API**:
   - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
   - Dodanie przykładów zapytań i odpowiedzi 