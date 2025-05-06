# API Endpoint Implementation Plan: List Logs (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania paginowanej listy logów zdarzeń aplikacji. Jest to część funkcjonalności administracyjnej systemu, pozwalającej administratorom na monitorowanie aktywności użytkowników, diagnozowanie problemów oraz audyt bezpieczeństwa. Endpoint umożliwia filtrowanie zdarzeń według różnych kryteriów, takich jak typ zdarzenia, użytkownik, adres IP oraz zakres dat. Dostęp do tego endpointu jest ograniczony wyłącznie do użytkowników z rolą Admin.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/admin/logs`
- **Parametry zapytania**:
  - **Opcjonalne**:
    - `page` (integer, domyślnie 1): Numer strony dla paginacji
    - `limit` (integer, domyślnie 100, maksymalnie 100): Liczba elementów na stronę
    - `event_type` (string): Filtrowanie po typie zdarzenia (np. "USER_LOGIN", "OFFER_CREATE")
    - `user_id` (UUID): Filtrowanie po ID użytkownika
    - `ip_address` (string): Filtrowanie po adresie IP
    - `start_date` (string, format ISO 8601): Data początkowa dla filtrowania
    - `end_date` (string, format ISO 8601): Data końcowa dla filtrowania
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `LogDTO`: Model reprezentujący pojedynczy wpis logu
  - `LogListResponse` (extends `PaginatedResponse`): Model reprezentujący paginowaną listę logów
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania
  - `UserRole` (enum): Enum definiujący role użytkowników, używany do weryfikacji roli Admin

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**: Obiekt `LogListResponse` zawierający paginowaną listę logów
  ```json
  {
    "items": [
      {
        "id": 12345,
        "event_type": "USER_LOGIN",
        "user_id": "uuid-user-id", // opcjonalne
        "ip_address": "192.168.1.100", // opcjonalne
        "message": "Login successful for user@example.com",
        "timestamp": "2023-04-15T12:00:00Z"
      },
      {
        "id": 12344,
        "event_type": "USER_REGISTER",
        "user_id": "uuid-user-id", // opcjonalne
        "ip_address": "192.168.1.101", // opcjonalne
        "message": "New user registered: user2@example.com",
        "timestamp": "2023-04-15T11:55:00Z"
      }
      // ... inne logi
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
2. Walidacja parametrów zapytania (page, limit, event_type, user_id, ip_address, start_date, end_date)
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu logów do pobierania paginowanej listy logów
5. Serwis wykonuje następujące operacje:
   - Przygotowanie zapytania SQL z odpowiednimi filtrami
   - Pobranie liczby wszystkich pasujących logów (dla paginacji)
   - Pobranie listy logów dla bieżącej strony
   - Przekształcenie danych do formatu DTO
6. Zapisuje zdarzenie pobrania listy logów w tabeli logów (meta-logging)
7. Zwraca paginowaną listę logów z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja parametrów zapytania (page, limit, start_date, end_date itp.)
  - Sprawdzenie, czy event_type jest prawidłową wartością z enum LogEventType
  - Sprawdzenie, czy user_id jest prawidłowym UUID
  - Walidacja formatu dat (ISO 8601)
- **Ochrona przed atakami**:
  - Ograniczenie liczby elementów na stronę do maksymalnie 100, aby zapobiec atakom DoS
  - Możliwość implementacji rate limitingu dla endpointów administracyjnych
  - Zapobieganie ujawnianiu wrażliwych informacji poprzez filtrowanie wiadomości logów
- **Audytowanie**:
  - Logowanie dostępu do listy logów w tabeli logów (meta-logging)
  - Rejestrowanie ID administratora wykonującego operację, zastosowanych filtrów i czasu wykonania

## 7. Obsługa błędów
- **Błędy walidacji parametrów**:
  - 400 Bad Request z kodem błędu `INVALID_QUERY_PARAM` i komunikatem opisującym problem:
    - "Page must be a positive integer"
    - "Limit must be a positive integer between 1 and 100"
    - "Invalid event_type value"
    - "Invalid user_id format"
    - "Invalid date format for start_date/end_date"
    - "End date must be after start date"
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch logs"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Paginacja**:
  - Implementacja paginacji po stronie bazy danych (LIMIT, OFFSET) dla efektywnego pobierania danych
  - Ograniczenie maksymalnej liczby elementów na stronę do 100
- **Optymalizacja zapytań**:
  - Wykorzystanie indeksów bazy danych dla kolumn używanych do filtrowania (event_type, user_id, ip_address, timestamp)
  - Minimalizacja liczby zapytań do bazy danych
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych
- **Zarządzanie zasobami**:
  - Zamykanie połączeń z bazą danych po zakończeniu operacji
  - Uwzględnienie potencjalnie dużego rozmiaru tabeli logów w projekcie indeksów i zapytań

## 9. Etapy wdrożenia
1. **Implementacja lub rozszerzenie LogService o metodę do pobierania listy logów**:
   ```python
   from datetime import datetime
   from typing import List, Optional, Tuple
   from uuid import UUID
   from fastapi import Depends
   from databases import Database
   from app.models.types import LogEventType, LogDTO, LogListResponse

   class LogService:
       def __init__(self, db: Database):
           self.db = db
       
       async def get_logs(
           self, 
           page: int = 1, 
           limit: int = 100, 
           event_type: Optional[LogEventType] = None,
           user_id: Optional[UUID] = None,
           ip_address: Optional[str] = None,
           start_date: Optional[datetime] = None,
           end_date: Optional[datetime] = None
       ) -> Tuple[List[LogDTO], int, int]:
           """
           Pobiera paginowaną listę logów z możliwością filtrowania.
           
           Args:
               page: Numer strony (domyślnie 1)
               limit: Liczba elementów na stronę (domyślnie 100, max 100)
               event_type: Opcjonalny filtr typu zdarzenia
               user_id: Opcjonalny filtr ID użytkownika
               ip_address: Opcjonalny filtr adresu IP
               start_date: Opcjonalna data początkowa (włącznie)
               end_date: Opcjonalna data końcowa (włącznie)
               
           Returns:
               Tuple zawierający:
               - Listę obiektów LogDTO
               - Całkowitą liczbę pasujących logów
               - Liczbę stron
           """
           # Walidacja parametrów
           if page < 1:
               raise ValueError("Page must be a positive integer")
           if limit < 1 or limit > 100:
               raise ValueError("Limit must be between 1 and 100")
           if start_date and end_date and end_date < start_date:
               raise ValueError("End date must be after start date")
           
           # Przygotowanie warunków WHERE dla zapytania
           where_conditions = []
           params = {}
           
           if event_type:
               where_conditions.append("event_type = :event_type")
               params["event_type"] = event_type
           
           if user_id:
               where_conditions.append("user_id = :user_id")
               params["user_id"] = user_id
           
           if ip_address:
               where_conditions.append("ip_address = :ip_address")
               params["ip_address"] = ip_address
           
           if start_date:
               where_conditions.append("timestamp >= :start_date")
               params["start_date"] = start_date
           
           if end_date:
               where_conditions.append("timestamp <= :end_date")
               params["end_date"] = end_date
           
           # Konstruowanie klauzuli WHERE
           where_clause = ""
           if where_conditions:
               where_clause = "WHERE " + " AND ".join(where_conditions)
           
           # Zapytanie o łączną liczbę logów (dla paginacji)
           count_query = f"""
           SELECT COUNT(*) as total
           FROM logs
           {where_clause}
           """
           
           result = await self.db.fetch_one(count_query, params)
           total_logs = result["total"]
           total_pages = (total_logs + limit - 1) // limit  # Ceiling division
           
           # Jeśli nie ma wyników, zwróć pustą listę
           if total_logs == 0:
               return [], 0, 0
           
           # Zapytanie o listę logów dla bieżącej strony
           offset = (page - 1) * limit
           
           logs_query = f"""
           SELECT id, event_type, user_id, ip_address, message, timestamp
           FROM logs
           {where_clause}
           ORDER BY timestamp DESC
           LIMIT :limit OFFSET :offset
           """
           
           params["limit"] = limit
           params["offset"] = offset
           
           logs_data = await self.db.fetch_all(logs_query, params)
           
           # Przekształć dane na obiekty DTO
           logs = [
               LogDTO(
                   id=log["id"],
                   event_type=LogEventType(log["event_type"]),
                   user_id=log["user_id"],
                   ip_address=log["ip_address"],
                   message=log["message"],
                   timestamp=log["timestamp"]
               )
               for log in logs_data
           ]
           
           return logs, total_logs, total_pages
       
       async def create_log(
           self, 
           event_type: LogEventType, 
           message: str, 
           user_id: Optional[UUID] = None, 
           ip_address: Optional[str] = None
       ) -> int:
           """
           Tworzy nowy wpis w logu.
           
           Args:
               event_type: Typ zdarzenia
               message: Wiadomość opisująca zdarzenie
               user_id: Opcjonalne ID użytkownika
               ip_address: Opcjonalny adres IP
               
           Returns:
               ID utworzonego logu
           """
           query = """
           INSERT INTO logs (event_type, user_id, ip_address, message, timestamp)
           VALUES (:event_type, :user_id, :ip_address, :message, :timestamp)
           RETURNING id
           """
           
           values = {
               "event_type": event_type,
               "user_id": user_id,
               "ip_address": ip_address,
               "message": message,
               "timestamp": datetime.now()
           }
           
           result = await self.db.fetch_one(query, values)
           return result["id"]
   ```

2. **Implementacja handlera endpointu**:
   ```python
   from datetime import datetime
   from typing import Optional
   from uuid import UUID
   from fastapi import APIRouter, Depends, HTTPException, Query
   from app.services.log_service import LogService
   from app.dependencies.auth import require_admin
   from app.models.types import UserDTO, LogEventType, LogListResponse

   router = APIRouter()

   def get_log_service():
       # Dependency dla serwisu logów
       # W rzeczywistej implementacji, należy użyć wstrzykiwania zależności
       # dla sesji bazy danych
       from app.dependencies.database import get_database
       return LogService(get_database())

   @router.get(
       "/admin/logs",
       response_model=LogListResponse,
       summary="List logs",
       description="Retrieves a paginated list of application logs. Allows filtering by various criteria. Requires Admin role.",
       responses={
           200: {"description": "List of logs retrieved successfully"},
           400: {"description": "Invalid query parameters"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           500: {"description": "Server error while fetching logs"}
       }
   )
   async def list_logs(
       page: int = Query(1, gt=0, description="Page number, starting from 1"),
       limit: int = Query(100, gt=0, le=100, description="Number of items per page (max 100)"),
       event_type: Optional[LogEventType] = Query(None, description="Filter by event type"),
       user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
       ip_address: Optional[str] = Query(None, description="Filter by IP address"),
       start_date: Optional[str] = Query(None, description="Filter by start date (ISO 8601 format)"),
       end_date: Optional[str] = Query(None, description="Filter by end date (ISO 8601 format)"),
       current_user: UserDTO = Depends(require_admin),
       log_service: LogService = Depends(get_log_service)
   ) -> LogListResponse:
       """
       Pobiera paginowaną listę logów zdarzeń aplikacji.
       Umożliwia filtrowanie według typu zdarzenia, użytkownika, adresu IP oraz zakresu dat.
       Dostęp tylko dla administratorów.
       """
       try:
           # Parsowanie dat, jeśli zostały podane
           parsed_start_date = None
           parsed_end_date = None
           
           if start_date:
               try:
                   parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
               except ValueError:
                   raise ValueError("Invalid date format for start_date. Use ISO 8601 format (e.g. 2023-04-15T12:00:00Z)")
           
           if end_date:
               try:
                   parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
               except ValueError:
                   raise ValueError("Invalid date format for end_date. Use ISO 8601 format (e.g. 2023-04-15T12:00:00Z)")
           
           # Logowanie próby pobrania listy logów
           filter_info = []
           if event_type:
               filter_info.append(f"event_type={event_type}")
           if user_id:
               filter_info.append(f"user_id={user_id}")
           if ip_address:
               filter_info.append(f"ip_address={ip_address}")
           if start_date:
               filter_info.append(f"start_date={start_date}")
           if end_date:
               filter_info.append(f"end_date={end_date}")
           
           filters = ", ".join(filter_info) if filter_info else "none"
           
           await log_service.create_log(
               event_type=LogEventType.ADMIN_ACTION,
               user_id=current_user.id,
               message=f"Admin {current_user.email} requested logs list. Filters: {filters}. Page: {page}, Limit: {limit}"
           )
           
           # Pobieranie listy logów
           logs, total_logs, total_pages = await log_service.get_logs(
               page=page,
               limit=limit,
               event_type=event_type,
               user_id=user_id,
               ip_address=ip_address,
               start_date=parsed_start_date,
               end_date=parsed_end_date
           )
           
           # Przygotowanie odpowiedzi
           response = LogListResponse(
               items=logs,
               total=total_logs,
               page=page,
               limit=limit,
               pages=total_pages
           )
           
           return response
           
       except ValueError as e:
           # Obsługa błędów walidacji parametrów
           error_message = str(e)
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.ADMIN_ACTION_FAIL,
               user_id=current_user.id,
               message=f"Failed to retrieve logs list: {error_message}"
           )
           
           # Zwróć odpowiedni błąd
           raise HTTPException(
               status_code=400,
               detail={
                   "error_code": "INVALID_QUERY_PARAM",
                   "message": error_message
               }
           )
       except Exception as e:
           # Logowanie nieoczekiwanego błędu
           await log_service.create_log(
               event_type=LogEventType.ADMIN_ACTION_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while retrieving logs list: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch logs"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       ADMIN_ACTION = "ADMIN_ACTION"
       ADMIN_ACTION_FAIL = "ADMIN_ACTION_FAIL"
   ```

4. **Upewnienie się, że endpoint jest dodany do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla LogService.get_logs:
     - Test pobierania listy logów bez filtrów
     - Test pobierania listy logów z filtrem event_type
     - Test pobierania listy logów z filtrem user_id
     - Test pobierania listy logów z filtrem ip_address
     - Test pobierania listy logów z filtrami dat
     - Test kombinacji wielu filtrów
     - Test paginacji (różne wartości page i limit)
     - Test obsługi błędów dla nieprawidłowych parametrów
   - Test dla handlera list_logs:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi
     - Test parsowania i walidacji parametrów dat
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi parametrami
   - Test wydajności dla dużej liczby logów
   - Test paginacji i filtrowania

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Wdrożenie i weryfikacja**:
   - Wdrożenie endpointu na środowisku deweloperskim
   - Weryfikacja poprawnego działania z różnymi parametrami
   - Sprawdzenie logów (meta-logging)
   - Analiza wydajności zapytań dla dużych zbiorów danych 