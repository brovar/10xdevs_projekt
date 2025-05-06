# API Endpoint Implementation Plan: Logout User

## 1. Przegląd punktu końcowego
Endpoint `/auth/logout` służy do wylogowania bieżącego użytkownika poprzez usunięcie jego sesji. Endpoint czyści ciasteczko sesji użytkownika, rejestruje zdarzenie w dzienniku systemowym i zwraca komunikat potwierdzający pomyślne wylogowanie. Endpoint wymaga, aby użytkownik był uwierzytelniony (zalogowany).

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/auth/logout`
- Parametry: brak
- Request Body: brak (puste)

## 3. Wykorzystywane typy
- **LogoutUserResponse** (z types.py) - model odpowiedzi dziedziczący z MessageResponse
- **MessageResponse** (z types.py) - prosty model zawierający pole message
- Enum types:
  - **LogEventType** - określa typ zdarzenia logowania (USER_LOGIN wartość do wykorzystania)
- Modele bazy danych:
  - **LogModel** - reprezentacja tabeli `logs` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK` (sesja została wyczyszczona)
- Response Body (sukces):
  ```json
  {
    "message": "Logout successful"
  }
  ```
- Kody błędów:
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - użytkownik nie jest zalogowany
  - `500 Internal Server Error` z kodem błędu `LOGOUT_FAILED` - błąd wewnętrzny serwera

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Kontroler sprawdza za pomocą middleware sesji lub innego mechanizmu, czy użytkownik jest zalogowany
3. Jeśli użytkownik nie jest zalogowany, zwracany jest błąd `401 Unauthorized`
4. Jeśli użytkownik jest zalogowany:
   - Pobierane są dane sesji (identyfikator użytkownika, rola)
   - Wywołany zostaje serwis sesji lub uwierzytelniania w celu zakończenia sesji
   - Sesja jest usuwana z pamięci/bazy danych (zależnie od implementacji)
   - Ciasteczko sesji jest usuwane z odpowiedzi HTTP
   - Zdarzenie wylogowania jest rejestrowane w tabeli `logs`
5. Kontroler zwraca odpowiedź sukcesu z kodem `200 OK` i wiadomością o pomyślnym wylogowaniu

## 6. Względy bezpieczeństwa
- **Ochrona przed CSRF**:
  - Implementacja tokenu CSRF dla endpointu wylogowania
  - Weryfikacja, czy żądanie wylogowania pochodzi z zaufanego źródła
- **Zabezpieczenie ciasteczek**:
  - Upewnienie się, że ciasteczka są prawidłowo usuwane ze wszystkich domen i ścieżek
  - Używanie flagi HttpOnly przy usuwaniu ciasteczek
  - Używanie flag Secure i SameSite przy usuwaniu ciasteczek
- **Obsługa sesji**:
  - Właściwe czyszczenie danych sesji z pamięci/bazy danych
  - Zapewnienie, że wszystkie zasoby związane z sesją są zwalniane
- **Obsługa wielu urządzeń**:
  - Rozważenie czy wylogowanie powinno dotyczyć wszystkich sesji użytkownika czy tylko bieżącej
  - Implementacja opcjonalnego parametru dla "wylogowania ze wszystkich urządzeń"

## 7. Obsługa błędów
- **Brak sesji**:
  - Użytkownik nie jest zalogowany: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
- **Problemy z ciasteczkami**:
  - Niepowodzenie usunięcia ciasteczka: `500 Internal Server Error` z kodem `LOGOUT_FAILED`
- **Problemy z bazą danych**:
  - Błąd podczas logowania zdarzenia: zapisać błąd w logach systemowych, ale zwrócić sukces użytkownikowi, ponieważ sesja została zakończona

## 8. Rozważania dotyczące wydajności
- **Lekka operacja**:
  - Wylogowanie jest zazwyczaj lekką operacją, która nie powinna powodować problemów z wydajnością
- **Asynchroniczność**:
  - Użycie async/await dla operacji I/O (operacje na bazie danych)
- **Zarządzanie sesjami**:
  - Efektywne usuwanie danych sesji, aby nie zaśmiecać pamięci/bazy danych

## 9. Etapy wdrożenia
1. **Aktualizacja lub wykorzystanie istniejącego managera sesji**:
   ```python
   # Zakładając, że klasa SessionManager już istnieje z poprzedniej implementacji login
   class SessionManager:
       # ... istniejące metody
       
       async def end_session(self, response: Response, request: Request) -> bool:
           # Pobierz identyfikator sesji z ciasteczka
           session_id = request.cookies.get(self.cookie_name)
           
           if not session_id:
               return False
               
           # W rzeczywistej implementacji, usunąłbyś dane sesji z bazy danych/cache
           # Przykład: await redis.delete(f"session:{session_id}")
           
           # Usuń ciasteczko
           response.delete_cookie(
               key=self.cookie_name,
               httponly=True,
               secure=True,
               samesite="lax"
           )
           
           return True
   ```

2. **Rozszerzenie serwisu użytkownika/uwierzytelniania**:
   ```python
   class AuthService:
       def __init__(self, db_session: AsyncSession, logger: Logger, session_manager: SessionManager):
           self.db_session = db_session
           self.logger = logger
           self.session_manager = session_manager
           
       async def logout_user(self, request: Request, response: Response) -> bool:
           try:
               # Pobierz identyfikator użytkownika z sesji (zakładamy, że jest dostępny)
               user_id = request.session.get("user_id")
               
               if not user_id:
                   raise HTTPException(
                       status_code=401,
                       detail={
                           "error_code": "NOT_AUTHENTICATED",
                           "message": "Użytkownik nie jest zalogowany."
                       }
                   )
                   
               # Zakończ sesję
               session_ended = await self.session_manager.end_session(response, request)
               
               if not session_ended:
                   raise HTTPException(
                       status_code=500,
                       detail={
                           "error_code": "LOGOUT_FAILED",
                           "message": "Wystąpił błąd podczas wylogowania. Spróbuj ponownie później."
                       }
                   )
               
               # Zapisz zdarzenie w logach
               log_entry = LogModel(
                   event_type=LogEventType.USER_LOGIN,  # Używamy tego samego typu co dla logowania
                   user_id=user_id,
                   ip_address=request.client.host,
                   message=f"User {user_id} logged out successfully"
               )
               
               self.db_session.add(log_entry)
               await self.db_session.commit()
               
               return True
           except HTTPException as e:
               raise e
           except Exception as e:
               await self.db_session.rollback()
               self.logger.error(f"Failed to process logout: {str(e)}")
               raise HTTPException(
                   status_code=500,
                   detail={
                       "error_code": "LOGOUT_FAILED",
                       "message": "Wystąpił błąd podczas wylogowania. Spróbuj ponownie później."
                   }
               )
   ```

3. **Implementacja kontrolera uwierzytelniania**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Request, Response
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger

   from dependencies import get_db_session, get_logger, require_authenticated
   from services.auth_service import AuthService
   from services.session_manager import SessionManager
   from types import LogoutUserResponse

   router = APIRouter(prefix="/auth", tags=["auth"])
   session_manager = SessionManager()

   @router.post("/logout", response_model=LogoutUserResponse)
   async def logout_user(
       request: Request,
       response: Response,
       db_session: AsyncSession = Depends(get_db_session),
       logger: Logger = Depends(get_logger),
       _: dict = Depends(require_authenticated)  # Dependency that checks if user is authenticated
   ):
       auth_service = AuthService(db_session, logger, session_manager)
       try:
           await auth_service.logout_user(request, response)
           return {"message": "Logout successful"}
       except HTTPException as e:
           raise e
       except Exception as e:
           logger.error(f"Unexpected error during logout: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "LOGOUT_FAILED",
                   "message": "Wystąpił nieoczekiwany błąd podczas wylogowania. Spróbuj ponownie później."
               }
           )
   ```

4. **Implementacja zależności do sprawdzania uwierzytelnienia**:
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
       
       # Możesz zwrócić więcej danych z sesji jeśli są potrzebne
       return {
           "user_id": user_id,
           "role": request.session.get("role")
       }
   ```

5. **Integracja z istniejącą konfiguracją routerów**:
   ```python
   from fastapi import FastAPI
   from routers import auth_router

   app = FastAPI()
   app.include_router(auth_router)
   ```

6. **Aktualizacja konfiguracji middleware sesji** (jeśli jeszcze nie zrobiono):
   ```python
   from fastapi.middleware.sessions import SessionMiddleware
   
   app = FastAPI()
   app.add_middleware(
       SessionMiddleware, 
       secret_key="your-secret-key"  # Użyj bezpiecznego losowego klucza w środowisku produkcyjnym
   )
   ```

7. **Utworzenie testów jednostkowych i integracyjnych**:
   - Testy funkcji `end_session` w `SessionManager`
   - Testy metody `logout_user` w `AuthService`
   - Testy endpointu `/auth/logout` z uwzględnieniem różnych scenariuszy:
     - Użytkownik zalogowany
     - Użytkownik niezalogowany
     - Błędy podczas zapisywania do bazy danych

8. **Aktualizacja dokumentacji API**:
   - Dodanie opisu endpointu w dokumentacji Swagger/OpenAPI
   - Dodanie przykładów zapytań i odpowiedzi
   - Opisanie możliwych kodów odpowiedzi i ich znaczenia 