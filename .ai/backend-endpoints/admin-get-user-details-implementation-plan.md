# API Endpoint Implementation Plan: Get User Details (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania szczegółowych informacji o konkretnym użytkowniku przez administratora systemu. Dostęp do tego endpointu jest ograniczony wyłącznie do użytkowników z rolą Admin. Endpoint zwraca pełne informacje o użytkowniku, z wyłączeniem hasła.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/admin/users/{user_id}`
- **Parametry**:
  - **Wymagane**:
    - `user_id` (UUID): identyfikator użytkownika, którego szczegóły mają zostać pobrane
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `UserDTO`: Model reprezentujący pełne dane użytkownika (bez hasła)
  - `UserRole` (enum): Enum definiujący dostępne role użytkowników
  - `UserStatus` (enum): Enum definiujący dostępne statusy użytkowników
- **Path Parameters**:
  - `user_id` (UUID): Identyfikator użytkownika

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
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

- **Kody błędów**:
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 404 Not Found (`USER_NOT_FOUND`): Użytkownik o podanym ID nie istnieje
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametru `user_id` jako prawidłowego UUID
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu użytkowników do pobrania szczegółów użytkownika
5. Serwis wykonuje zapytanie SQL do bazy danych:
   - SELECT wszystkich potrzebnych pól z tabeli `users` dla podanego `user_id`
   - Wykluczenie pola `password_hash` z wyników
6. Sprawdzenie, czy użytkownik o podanym ID istnieje, jeśli nie - zwrócenie błędu 404
7. Transformacja danych do modelu UserDTO
8. Zwrócenie odpowiedzi JSON z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja `user_id` jako prawidłowego UUID
  - Sprawdzenie, czy użytkownik o podanym ID istnieje
- **Ochrona danych**:
  - Niewysyłanie hasła ani innych wrażliwych danych użytkownika
  - Zabezpieczenie przed atakami typu IDOR (Insecure Direct Object References)
  - Logowanie dostępu do danych użytkownika

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 422 Unprocessable Entity: Nieprawidłowy format `user_id` (automatycznie obsługiwane przez FastAPI)
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `USER_NOT_FOUND` i komunikatem "User not found"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch user details"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumna `id` w tabeli `users` jest indeksowana (to jest już PK)
- **Zapytania**:
  - Selektywne pobieranie tylko potrzebnych kolumn
  - Wykluczenie pola `password_hash` z zapytania dla optymalnej wydajności
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych
- **Cachowanie**:
  - Dane użytkowników mogą być cachowane przez krótki okres czasu, jeśli są często odczytywane
  - Implementacja strategii invalidacji cache przy modyfikacji danych użytkownika

## 9. Etapy wdrożenia
1. **Rozszerzenie UserService o metodę do pobierania szczegółów użytkownika**:
   ```python
   class UserService:
       def __init__(self, db: Database):
           self.db = db
       
       async def get_user_by_id(self, user_id: UUID) -> Optional[UserDTO]:
           """
           Pobiera szczegóły użytkownika na podstawie ID.
           
           Args:
               user_id: UUID użytkownika
               
           Returns:
               UserDTO jeśli użytkownik istnieje, None w przeciwnym przypadku
               
           Raises:
               ValueError: Jeśli wystąpi błąd podczas pobierania danych
           """
           query = """
           SELECT id, email, role, status, first_name, last_name, created_at, updated_at
           FROM users
           WHERE id = :user_id
           """
           
           try:
               result = await self.db.fetch_one(query, {"user_id": user_id})
               
               if result is None:
                   return None
                   
               return UserDTO(**result)
           except Exception as e:
               # Logowanie błędu
               logger.error(f"Error fetching user details: {str(e)}")
               raise ValueError(f"Failed to fetch user details: {str(e)}")
   ```

2. **Implementacja dependency require_admin (jeśli nie istnieje)**:
   ```python
   async def require_admin(
       current_user: UserDTO = Depends(get_current_user),
   ) -> UserDTO:
       """
       Sprawdza, czy bieżący użytkownik ma rolę Admin.
       
       Args:
           current_user: Obiekt UserDTO bieżącego użytkownika
           
       Returns:
           UserDTO jeśli użytkownik ma rolę Admin
           
       Raises:
           HTTPException: Jeśli użytkownik nie ma roli Admin
       """
       if not current_user or current_user.role != UserRole.ADMIN:
           raise HTTPException(
               status_code=403,
               detail={
                   "error_code": "INSUFFICIENT_PERMISSIONS",
                   "message": "Admin role required"
               }
           )
       return current_user
   ```

3. **Implementacja handlera endpointu**:
   ```python
   @router.get(
       "/admin/users/{user_id}",
       response_model=UserDTO,
       summary="Get user details",
       description="Retrieves details for a specific user. Requires Admin role.",
       responses={
           200: {"description": "User details retrieved successfully"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           404: {"description": "User not found"},
           500: {"description": "Server error while fetching data"}
       }
   )
   async def get_user_details(
       user_id: UUID = Path(..., description="The ID of the user to retrieve"),
       current_user: UserDTO = Depends(require_admin),
       user_service: UserService = Depends(get_user_service),
       log_service: LogService = Depends(get_log_service)
   ) -> UserDTO:
       """
       Pobiera szczegóły użytkownika o podanym ID. Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie dostępu administratora
           await log_service.create_log(
               event_type=LogEventType.ADMIN_GET_USER_DETAILS,
               user_id=current_user.id,
               message=f"Admin {current_user.email} accessed user details for user ID {user_id}"
           )
           
           # Pobieranie szczegółów użytkownika
           user = await user_service.get_user_by_id(user_id)
           
           # Sprawdzenie, czy użytkownik istnieje
           if user is None:
               await log_service.create_log(
                   event_type=LogEventType.ADMIN_GET_USER_DETAILS_FAIL,
                   user_id=current_user.id,
                   message=f"User with ID {user_id} not found"
               )
               raise HTTPException(
                   status_code=404,
                   detail={
                       "error_code": "USER_NOT_FOUND",
                       "message": "User not found"
                   }
               )
           
           return user
           
       except ValueError as e:
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.ADMIN_GET_USER_DETAILS_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch user details: {str(e)}"
           )
           
           # Zwracanie standardowego błędu
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch user details"
               }
           )
   ```

4. **Dodanie typu zdarzenia w LogEventType (jeśli nie istnieje)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       ADMIN_GET_USER_DETAILS = "ADMIN_GET_USER_DETAILS"
       ADMIN_GET_USER_DETAILS_FAIL = "ADMIN_GET_USER_DETAILS_FAIL"
   ```

5. **Dodanie endpointu do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(user_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

6. **Implementacja testów jednostkowych**:
   - Test dla UserService.get_user_by_id
   - Test dla dependency require_admin
   - Test walidacji parametru path user_id

7. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z prawidłowym ID użytkownika
   - Test scenariuszy błędów (nieistniejący użytkownik, nieprawidłowe UUID)
   - Test przypadków związanych z autoryzacją (różne role użytkowników)

8. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje) 