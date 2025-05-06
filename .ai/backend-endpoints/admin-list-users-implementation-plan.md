# API Endpoint Implementation Plan: List Users (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania paginowanej listy wszystkich użytkowników w systemie. Dostęp do tego endpointu jest ograniczony wyłącznie do użytkowników z rolą Admin. Endpoint umożliwia filtrowanie listy użytkowników według roli, statusu oraz wyszukiwanie po adresie email lub imieniu i nazwisku.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/admin/users`
- **Parametry**:
  - **Opcjonalne**:
    - `page` (integer, domyślnie 1): Numer strony dla paginacji
    - `limit` (integer, domyślnie 100, max 100): Liczba elementów na stronę
    - `role` (string): Filtrowanie po roli użytkownika ('Buyer', 'Seller', 'Admin')
    - `status` (string): Filtrowanie po statusie użytkownika ('Active', 'Inactive', 'Deleted')
    - `search` (string): Wyszukiwanie po adresie email, imieniu lub nazwisku (case-insensitive, partial match)
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `UserDTO`: Model reprezentujący podstawowe dane użytkownika (bez hasła)
  - `UserListResponse`: Model paginowanej odpowiedzi zawierającej listę użytkowników
  - `UserRole` (enum): Enum definiujący dostępne role użytkowników
  - `UserStatus` (enum): Enum definiujący dostępne statusy użytkowników
- **Query Model**:
  - `UserListQueryParams`: Model walidujący parametry zapytania (page, limit, role, status, search)

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "items": [
      {
        "id": "uuid-user-id",
        "email": "user@example.com",
        "role": "Buyer",
        "status": "Active",
        "first_name": "John",
        "last_name": "Doe",
        "created_at": "timestamp",
        "updated_at": "timestamp"
      },
      // ... more users
    ],
    "total": 150,
    "page": 1,
    "limit": 100,
    "pages": 2
  }
  ```

- **Kody błędów**:
  - 400 Bad Request (`INVALID_QUERY_PARAM`): Nieprawidłowe parametry zapytania
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametrów zapytania za pomocą modelu Pydantic
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu użytkowników do pobrania paginowanej listy
5. Serwis generuje zapytanie SQL z odpowiednimi filtrami:
   - Zastosowanie warunków WHERE dla role i status, jeśli podano
   - Zastosowanie LIKE dla email, first_name lub last_name, jeśli podano search
   - Zastosowanie LIMIT i OFFSET na podstawie parametrów paginacji
6. Wykonanie zapytania SQL i pobranie danych
7. Obliczenie całkowitej liczby użytkowników spełniających kryteria (do paginacji)
8. Transformacja danych do modelu odpowiedzi
9. Zwrócenie odpowiedzi JSON z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja parametrów zapytania przez model Pydantic
  - Sprawdzenie, czy role i status są prawidłowymi wartościami enum
  - Ograniczenie wartości limit do maksymalnie 100
- **Ochrona danych**:
  - Niewysyłanie wrażliwych danych (np. haseł) w odpowiedzi
  - Logowanie dostępu do endpointu administracyjnego

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 400 Bad Request z kodem błędu `INVALID_QUERY_PARAM` i komunikatem "Invalid query parameter: [parameter_name]"
  - Szczegóły błędu wskazujące, który parametr jest nieprawidłowy i dlaczego
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy bazy danych**:
  - Przechwytywanie wyjątków DB i konwersja na 500 Internal Server Error
  - Kod błędu `FETCH_FAILED` z komunikatem "Failed to fetch users"
  - Logowanie szczegółów błędu do systemu logowania z ukryciem wrażliwych danych
- **Nieoczekiwane błędy**:
  - Ogólny handler wyjątków zwracający 500 z komunikatem "An unexpected error occurred"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumny używane do filtrowania są indeksowane (`role`, `status`)
  - Rozważ indeks dla kolumn używanych do wyszukiwania (`email`, `first_name`, `last_name`)
- **Paginacja**:
  - Ograniczenie maksymalnej liczby elementów na stronę do 100
  - Optymalizacja zapytania COUNT() przez zastosowanie oddzielnych zapytań dla danych i liczby rekordów
- **Optymalizacja zapytań**:
  - Używanie specyficznych warunków WHERE zamiast ogólnych LIKE, gdy to możliwe
  - Selektywne pobieranie tylko potrzebnych kolumn
- **Buforowanie**:
  - Rozważ implementację buforowania wyników zapytań dla często używanych filtrów
  - Zastosuj odpowiednią strategię unieważniania cache przy zmianach danych użytkowników
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych (np. aiomysql)

## 9. Etapy wdrożenia
1. **Utworzenie modelu parametrów zapytania**:
   ```python
   class UserListQueryParams(BaseModel):
       page: int = Field(1, gt=0, description="Numer strony")
       limit: int = Field(100, gt=0, le=100, description="Liczba elementów na stronę")
       role: Optional[UserRole] = None
       status: Optional[UserStatus] = None
       search: Optional[str] = None
       
       class Config:
           schema_extra = {
               "example": {
                   "page": 1,
                   "limit": 50,
                   "role": "Buyer",
                   "status": "Active",
                   "search": "john"
               }
           }
   ```

2. **Implementacja dependency dla wymagania roli Admin**:
   ```python
   async def require_admin(
       current_user: UserDTO = Depends(get_current_user),
   ) -> UserDTO:
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

3. **Implementacja serwisu użytkowników lub rozszerzenie istniejącego**:
   ```python
   class UserService:
       def __init__(self, db: Database):
           self.db = db
       
       async def list_users(
           self,
           page: int = 1,
           limit: int = 100,
           role: Optional[UserRole] = None,
           status: Optional[UserStatus] = None,
           search: Optional[str] = None
       ) -> UserListResponse:
           # Oblicz offset dla paginacji
           offset = (page - 1) * limit
           
           # Zbuduj zapytanie bazowe
           query_conditions = []
           query_params = {}
           
           # Dodaj warunki filtrowania
           if role:
               query_conditions.append("role = :role")
               query_params["role"] = role
               
           if status:
               query_conditions.append("status = :status")
               query_params["status"] = status
               
           if search:
               search_condition = "(email LIKE :search OR first_name LIKE :search OR last_name LIKE :search)"
               query_conditions.append(search_condition)
               query_params["search"] = f"%{search}%"
           
           # Zbuduj klauzulę WHERE
           where_clause = " AND ".join(query_conditions)
           if where_clause:
               where_clause = f"WHERE {where_clause}"
           
           # Zapytanie liczące całkowitą ilość pasujących rekordów
           count_query = f"""
           SELECT COUNT(*) as total
           FROM users
           {where_clause}
           """
           
           # Zapytanie pobierające dane z paginacją
           data_query = f"""
           SELECT id, email, role, status, first_name, last_name, created_at, updated_at
           FROM users
           {where_clause}
           ORDER BY created_at DESC
           LIMIT :limit OFFSET :offset
           """
           
           # Dodaj parametry paginacji
           query_params["limit"] = limit
           query_params["offset"] = offset
           
           # Wykonaj zapytania
           async with self.db.transaction():
               total_result = await self.db.fetch_one(count_query, query_params)
               users_data = await self.db.fetch_all(data_query, query_params)
           
           # Przetwórz wyniki
           total = total_result["total"] if total_result else 0
           users = [UserDTO(**user) for user in users_data]
           
           # Oblicz całkowitą liczbę stron
           pages = (total + limit - 1) // limit if total > 0 else 0
           
           # Zwróć paginowaną odpowiedź
           return UserListResponse(
               items=users,
               total=total,
               page=page,
               limit=limit,
               pages=pages
           )
   ```

4. **Implementacja handlera endpointu**:
   ```python
   @router.get("/admin/users", response_model=UserListResponse)
   async def list_users(
       query_params: UserListQueryParams = Depends(),
       current_user: UserDTO = Depends(require_admin),
       user_service: UserService = Depends(get_user_service),
       log_service: LogService = Depends(get_log_service)
   ):
       try:
           # Loguj dostęp
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_USERS,
               user_id=current_user.id,
               message=f"Admin {current_user.email} accessed user list"
           )
           
           # Pobierz listę użytkowników
           result = await user_service.list_users(
               page=query_params.page,
               limit=query_params.limit,
               role=query_params.role,
               status=query_params.status,
               search=query_params.search
           )
           
           return result
           
       except ValueError as e:
           # Obsługa błędów walidacji
           raise HTTPException(
               status_code=400,
               detail={
                   "error_code": "INVALID_QUERY_PARAM",
                   "message": str(e)
               }
           )
       except Exception as e:
           # Loguj błąd
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_USERS_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch users: {str(e)}"
           )
           
           # Zwróć standardowy błąd
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch users"
               }
           )
   ```

5. **Dodanie endpointu do routera**:
   ```python
   # W pliku router konfiguracji routerów
   from fastapi import APIRouter, Depends
   from app.dependencies import require_admin
   from app.services import get_user_service, get_log_service
   
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodaj handler endpointu do routera
   admin_router.include_router(user_router)
   
   # Dodaj router do głównej aplikacji
   app.include_router(admin_router)
   ```

6. **Dodanie dokumentacji Swagger**:
   ```python
   @router.get(
       "/admin/users",
       response_model=UserListResponse,
       summary="List all users",
       description="Retrieves a paginated list of all users. Requires Admin role.",
       responses={
           200: {"description": "Successful response with paginated user list"},
           400: {"description": "Invalid query parameters"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           500: {"description": "Server error while fetching data"}
       }
   )
   ```

7. **Implementacja testów jednostkowych**:
   - Testy dla UserService.list_users
   - Testy dla dependency require_admin
   - Testy walidacji parametrów zapytania

8. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi parametrami filtrowania
   - Test scenariuszy błędów (nieprawidłowe parametry, brak uprawnień)
   - Test paginacji i jej limitów 