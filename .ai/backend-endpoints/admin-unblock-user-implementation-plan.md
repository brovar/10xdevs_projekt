# API Endpoint Implementation Plan: Unblock User (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do odblokowywania użytkownika przez administratora poprzez zmianę jego statusu z "Inactive" na "Active". Jest to operacja odwrotna do blokowania użytkownika. Endpoint nie przywraca automatycznie statusu ofert sprzedawcy ani anulowanych zamówień - te muszą być zarządzane osobno. Operacja wymaga uprawnień administratora i może być wykonana tylko dla użytkowników, którzy są obecnie zablokowani.

## 2. Szczegóły żądania
- **Metoda HTTP**: POST
- **Struktura URL**: `/admin/users/{user_id}/unblock`
- **Parametry**:
  - **Wymagane**:
    - `user_id` (UUID): identyfikator użytkownika, który ma zostać odblokowany
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `UserDTO`: Model reprezentujący dane użytkownika (zwracany po aktualizacji)
  - `UserStatus` (enum): Enum definiujący statusy użytkowników, używany do zmiany statusu na "Active"
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "role": "Buyer", // lub "Seller", "Admin"
    "status": "Active", // Zmieniono na Active
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
  ```

- **Kody błędów**:
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 404 Not Found (`USER_NOT_FOUND`): Użytkownik o podanym ID nie istnieje
  - 409 Conflict (`ALREADY_ACTIVE`): Użytkownik jest już aktywny
  - 500 Internal Server Error (`UNBLOCK_FAILED`): Błąd serwera podczas odblokowywania użytkownika

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametru `user_id` jako prawidłowego UUID
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu użytkowników do odblokowywania użytkownika
5. Serwis wykonuje następujące operacje w ramach transakcji bazodanowej:
   - Sprawdza, czy użytkownik o podanym ID istnieje
   - Sprawdza, czy użytkownik jest zablokowany (status "Inactive")
   - Aktualizuje status użytkownika na "Active"
   - Aktualizuje pole `updated_at` użytkownika
6. Zapisuje zdarzenie odblokowywania użytkownika w tabeli logów
7. Zwraca zaktualizowany obiekt użytkownika z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja `user_id` jako prawidłowego UUID
  - Sprawdzenie, czy użytkownik istnieje przed odblokowywaniem
  - Sprawdzenie, czy użytkownik jest obecnie zablokowany
- **Transakcyjność**:
  - Użycie transakcji bazodanowej do zapewnienia spójności danych
  - W przypadku błędu wszystkie zmiany są wycofywane
- **Audytowanie**:
  - Logowanie operacji odblokowywania użytkownika w tabeli logów
  - Rejestrowanie ID administratora wykonującego operację

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 422 Unprocessable Entity: Nieprawidłowy format `user_id` (automatycznie obsługiwane przez FastAPI)
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `USER_NOT_FOUND` i komunikatem "User not found"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `ALREADY_ACTIVE` i komunikatem "User is already active"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `UNBLOCK_FAILED` i komunikatem "Failed to unblock user"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Transakcje bazodanowe**:
  - Wykonanie operacji w pojedynczej, lekkiej transakcji
  - Tylko jedna operacja aktualizacji na bazie danych
- **Indeksy bazy danych**:
  - Upewnienie się, że kolumna `id` w tabeli `users` jest indeksowana (PK)
  - Indeksy dla kolumny `status` w tabeli `users` pomagają w szybkim wyszukiwaniu
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych

## 9. Etapy wdrożenia
1. **Rozszerzenie UserService o metodę do odblokowywania użytkownika**:
   ```python
   class UserService:
       def __init__(self, db: Database):
           self.db = db
       
       async def unblock_user(self, user_id: UUID) -> UserDTO:
           """
           Odblokowuje użytkownika poprzez zmianę jego statusu na Active.
           
           Args:
               user_id: UUID użytkownika do odblokowania
               
           Returns:
               UserDTO zaktualizowanego użytkownika
               
           Raises:
               ValueError: Jeśli użytkownik nie istnieje lub jest już aktywny
               Exception: Jeśli wystąpi błąd podczas odblokowywania
           """
           # Rozpocznij transakcję
           async with self.db.transaction():
               # Sprawdź, czy użytkownik istnieje i pobierz jego dane
               query = """
               SELECT id, email, role, status, first_name, last_name, created_at, updated_at
               FROM users
               WHERE id = :user_id
               """
               user = await self.db.fetch_one(query, {"user_id": user_id})
               
               if not user:
                   raise ValueError(f"User with ID {user_id} not found")
               
               # Sprawdź, czy użytkownik jest obecnie zablokowany
               if user["status"] == UserStatus.ACTIVE:
                   raise ValueError(f"User with ID {user_id} is already active")
               
               # Aktualizuj status użytkownika
               current_time = datetime.now()
               update_query = """
               UPDATE users
               SET status = :status, updated_at = :updated_at
               WHERE id = :user_id
               RETURNING id, email, role, status, first_name, last_name, created_at, updated_at
               """
               updated_user = await self.db.fetch_one(
                   update_query,
                   {
                       "user_id": user_id,
                       "status": UserStatus.ACTIVE,
                       "updated_at": current_time
                   }
               )
               
               return UserDTO(**updated_user)
   ```

2. **Implementacja handlera endpointu**:
   ```python
   @router.post(
       "/admin/users/{user_id}/unblock",
       response_model=UserDTO,
       summary="Unblock user",
       description="Sets user status to 'Active'. Requires Admin role.",
       responses={
           200: {"description": "User unblocked successfully"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           404: {"description": "User not found"},
           409: {"description": "User is already active"},
           500: {"description": "Server error while unblocking user"}
       }
   )
   async def unblock_user(
       user_id: UUID = Path(..., description="The ID of the user to unblock"),
       current_user: UserDTO = Depends(require_admin),
       user_service: UserService = Depends(get_user_service),
       log_service: LogService = Depends(get_log_service)
   ) -> UserDTO:
       """
       Odblokowuje użytkownika poprzez zmianę jego statusu na 'Active'.
       Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie próby odblokowania
           await log_service.create_log(
               event_type=LogEventType.USER_UNBLOCK_ATTEMPT,
               user_id=current_user.id,
               message=f"Admin {current_user.email} attempted to unblock user with ID {user_id}"
           )
           
           # Odblokowanie użytkownika
           unblocked_user = await user_service.unblock_user(user_id)
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.USER_ACTIVATED,
               user_id=current_user.id,
               message=f"Admin {current_user.email} successfully unblocked user {unblocked_user.email} (ID: {user_id})"
           )
           
           return unblocked_user
           
       except ValueError as e:
           error_message = str(e)
           
           # Określ kod błędu na podstawie treści komunikatu
           if "not found" in error_message.lower():
               error_code = "USER_NOT_FOUND"
               status_code = 404
           elif "already active" in error_message.lower():
               error_code = "ALREADY_ACTIVE"
               status_code = 409
           else:
               error_code = "INVALID_REQUEST"
               status_code = 400
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.USER_UNBLOCK_FAIL,
               user_id=current_user.id,
               message=f"Failed to unblock user {user_id}: {error_message}"
           )
           
           # Zwróć odpowiedni błąd
           raise HTTPException(
               status_code=status_code,
               detail={
                   "error_code": error_code,
                   "message": error_message
               }
           )
       except Exception as e:
           # Logowanie nieoczekiwanego błędu
           await log_service.create_log(
               event_type=LogEventType.USER_UNBLOCK_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while unblocking user {user_id}: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "UNBLOCK_FAILED",
                   "message": "Failed to unblock user"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       USER_UNBLOCK_ATTEMPT = "USER_UNBLOCK_ATTEMPT"
       USER_UNBLOCK_FAIL = "USER_UNBLOCK_FAIL"
       # USER_ACTIVATED już istnieje w specyfikacji
   ```

4. **Dodanie endpointu do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(user_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla UserService.unblock_user:
     - Test odblokowywania zwykłego użytkownika (Buyer lub Seller)
     - Test odblokowywania już aktywnego użytkownika (oczekiwany wyjątek)
     - Test odblokowywania nieistniejącego użytkownika (oczekiwany wyjątek)
   - Test dla handlera unblock_user:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi typami użytkowników (Buyer, Seller)
   - Test scenariuszy błędów (nieistniejący użytkownik, już aktywny)
   - Test pełnego cyklu: blokowanie i następnie odblokowywanie użytkownika

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Wdrożenie i weryfikacja**:
   - Wdrożenie endpointu na środowisku deweloperskim
   - Ręczne testy weryfikacyjne
   - Sprawdzenie poprawności logowania zdarzeń 