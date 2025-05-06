# API Endpoint Implementation Plan: List All Orders (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania paginowanej listy wszystkich zamówień w systemie. Jest dostępny wyłącznie dla administratorów i umożliwia filtrowanie zamówień według statusu, identyfikatora kupującego lub identyfikatora sprzedającego. Dzięki temu administratorzy mogą monitorować i zarządzać wszystkimi zamówieniami w systemie, niezależnie od ich statusu czy powiązanych użytkowników.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/admin/orders`
- **Parametry zapytania**:
  - **Opcjonalne**:
    - `page` (integer, domyślnie 1): Numer strony dla paginacji
    - `limit` (integer, domyślnie 100, maksymalnie 100): Liczba elementów na stronę
    - `status` (string): Filtrowanie według statusu zamówienia (np. "processing", "shipped", "delivered")
    - `buyer_id` (UUID): Filtrowanie zamówień według ID kupującego
    - `seller_id` (UUID): Filtrowanie zamówień zawierających przedmioty od konkretnego sprzedawcy
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OrderSummaryDTO`: Model reprezentujący podstawowe informacje o zamówieniu
  - `OrderListResponse` (extends `PaginatedResponse`): Model reprezentujący paginowaną listę zamówień
  - `OrderStatus` (enum): Enum definiujący możliwe statusy zamówień
  - `UserRole` (enum): Enum definiujący role użytkowników, używany do weryfikacji roli Admin
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**: Obiekt `OrderListResponse` zawierający paginowaną listę zamówień
  ```json
  {
    "items": [
      {
        "id": "uuid-order-id-1",
        "status": "processing",
        "total_amount": "123.45",
        "created_at": "timestamp",
        "updated_at": "timestamp"
      },
      {
        "id": "uuid-order-id-2",
        "status": "shipped",
        "total_amount": "67.89",
        "created_at": "timestamp",
        "updated_at": "timestamp"
      }
      // ... inne zamówienia
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
2. Walidacja parametrów zapytania (page, limit, status, buyer_id, seller_id)
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu zamówień do pobierania paginowanej listy zamówień
5. Serwis wykonuje następujące operacje:
   - Przygotowanie zapytania SQL z odpowiednimi filtrami
   - Pobranie liczby wszystkich pasujących zamówień (dla paginacji)
   - Pobranie listy zamówień dla bieżącej strony
   - Dla każdego zamówienia obliczenie łącznej kwoty (suma price_at_purchase * quantity dla wszystkich elementów zamówienia)
   - Przekształcenie danych do formatu DTO
6. Zapisuje zdarzenie pobrania listy zamówień w tabeli logów
7. Zwraca paginowaną listę zamówień z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja parametrów zapytania (page, limit, status, buyer_id, seller_id)
  - Sprawdzenie, czy status jest prawidłową wartością z enum OrderStatus
  - Sprawdzenie, czy buyer_id i seller_id są prawidłowymi UUID
- **Ochrona przed atakami**:
  - Ograniczenie liczby elementów na stronę do maksymalnie 100, aby zapobiec atakom DoS
  - Możliwość implementacji rate limitingu dla endpointów administracyjnych
- **Audytowanie**:
  - Logowanie dostępu do listy zamówień w tabeli logów
  - Rejestrowanie ID administratora wykonującego operację, zastosowanych filtrów i czasu wykonania

## 7. Obsługa błędów
- **Błędy walidacji parametrów**:
  - 400 Bad Request z kodem błędu `INVALID_QUERY_PARAM` i komunikatem opisującym problem:
    - "Page must be a positive integer"
    - "Limit must be a positive integer between 1 and 100"
    - "Invalid status value"
    - "Invalid buyer_id format"
    - "Invalid seller_id format"
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch orders"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Paginacja**:
  - Implementacja paginacji po stronie bazy danych (LIMIT, OFFSET) dla efektywnego pobierania danych
  - Ograniczenie maksymalnej liczby elementów na stronę do 100
- **Optymalizacja zapytań**:
  - Minimalizacja liczby zapytań do bazy danych
  - Efektywne wykorzystanie JOIN dla filtrowania po seller_id
  - Użycie odpowiednich indeksów bazy danych (orders.id, orders.buyer_id, orders.status, order_items.order_id, order_items.offer_id)
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych
- **Buforowanie**:
  - Rozważenie implementacji mechanizmu buforowania dla często używanych filtrów (np. ostatnie zamówienia)

## 9. Etapy wdrożenia
1. **Implementacja lub rozszerzenie OrderService o metodę do pobierania listy zamówień**:
   ```python
   class OrderService:
       def __init__(self, db: Database):
           self.db = db
       
       async def get_admin_orders(
           self, 
           page: int = 1, 
           limit: int = 100, 
           status: Optional[OrderStatus] = None,
           buyer_id: Optional[UUID] = None,
           seller_id: Optional[UUID] = None
       ) -> Tuple[List[OrderSummaryDTO], int, int]:
           """
           Pobiera paginowaną listę zamówień dla administratora z możliwością filtrowania.
           
           Args:
               page: Numer strony (domyślnie 1)
               limit: Liczba elementów na stronę (domyślnie 100, max 100)
               status: Opcjonalny filtr statusu zamówienia
               buyer_id: Opcjonalny filtr ID kupującego
               seller_id: Opcjonalny filtr ID sprzedawcy (filtruje zamówienia zawierające produkty tego sprzedawcy)
               
           Returns:
               Tuple zawierający:
               - Listę obiektów OrderSummaryDTO
               - Całkowitą liczbę pasujących zamówień
               - Liczbę stron
           """
           # Walidacja parametrów
           if page < 1:
               raise ValueError("Page must be a positive integer")
           if limit < 1 or limit > 100:
               raise ValueError("Limit must be between 1 and 100")
           
           # Przygotowanie warunków WHERE dla zapytania
           where_conditions = []
           params = {}
           
           if status:
               where_conditions.append("o.status = :status")
               params["status"] = status
           
           if buyer_id:
               where_conditions.append("o.buyer_id = :buyer_id")
               params["buyer_id"] = buyer_id
           
           # Przygotowanie warunku JOIN dla seller_id
           join_condition = ""
           if seller_id:
               join_condition = """
               JOIN order_items oi ON o.id = oi.order_id
               JOIN offers of ON oi.offer_id = of.id AND of.seller_id = :seller_id
               """
               params["seller_id"] = seller_id
           
           # Konstruowanie klauzuli WHERE
           where_clause = ""
           if where_conditions:
               where_clause = "WHERE " + " AND ".join(where_conditions)
           
           # Zapytanie o łączną liczbę zamówień (dla paginacji)
           count_query = f"""
           SELECT COUNT(DISTINCT o.id) as total
           FROM orders o
           {join_condition}
           {where_clause}
           """
           
           result = await self.db.fetch_one(count_query, params)
           total_orders = result["total"]
           total_pages = (total_orders + limit - 1) // limit  # Ceiling division
           
           # Jeśli nie ma wyników, zwróć pustą listę
           if total_orders == 0:
               return [], 0, 0
           
           # Zapytanie o listę zamówień dla bieżącej strony
           offset = (page - 1) * limit
           
           orders_query = f"""
           SELECT DISTINCT o.id, o.status, o.buyer_id, o.created_at, o.updated_at
           FROM orders o
           {join_condition}
           {where_clause}
           ORDER BY o.created_at DESC
           LIMIT :limit OFFSET :offset
           """
           
           params["limit"] = limit
           params["offset"] = offset
           
           orders_data = await self.db.fetch_all(orders_query, params)
           
           # Pobieranie łącznej kwoty dla każdego zamówienia
           order_summaries = []
           for order in orders_data:
               # Zapytanie o elementy zamówienia
               items_query = """
               SELECT oi.quantity, oi.price_at_purchase
               FROM order_items oi
               WHERE oi.order_id = :order_id
               """
               
               items_data = await self.db.fetch_all(items_query, {"order_id": order["id"]})
               
               # Obliczenie łącznej kwoty
               total_amount = sum(item["quantity"] * item["price_at_purchase"] for item in items_data)
               
               # Utworzenie DTO
               order_summary = OrderSummaryDTO(
                   id=order["id"],
                   status=order["status"],
                   total_amount=total_amount,
                   created_at=order["created_at"],
                   updated_at=order["updated_at"]
               )
               
               order_summaries.append(order_summary)
           
           return order_summaries, total_orders, total_pages
   ```

2. **Implementacja handlera endpointu**:
   ```python
   @router.get(
       "/admin/orders",
       response_model=OrderListResponse,
       summary="List all orders",
       description="Retrieves a paginated list of all orders. Allows filtering by status, buyer_id, and seller_id. Requires Admin role.",
       responses={
           200: {"description": "List of orders retrieved successfully"},
           400: {"description": "Invalid query parameters"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           500: {"description": "Server error while fetching orders"}
       }
   )
   async def list_all_orders(
       page: int = Query(1, gt=0, description="Page number, starting from 1"),
       limit: int = Query(100, gt=0, le=100, description="Number of items per page (max 100)"),
       status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
       buyer_id: Optional[UUID] = Query(None, description="Filter by buyer ID"),
       seller_id: Optional[UUID] = Query(None, description="Filter by seller ID (orders containing items from this seller)"),
       current_user: UserDTO = Depends(require_admin),
       order_service: OrderService = Depends(get_order_service),
       log_service: LogService = Depends(get_log_service)
   ) -> OrderListResponse:
       """
       Pobiera paginowaną listę wszystkich zamówień w systemie.
       Umożliwia filtrowanie według statusu, ID kupującego i ID sprzedawcy.
       Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie próby pobrania listy zamówień
           filter_info = []
           if status:
               filter_info.append(f"status={status}")
           if buyer_id:
               filter_info.append(f"buyer_id={buyer_id}")
           if seller_id:
               filter_info.append(f"seller_id={seller_id}")
           
           filters = ", ".join(filter_info) if filter_info else "none"
           
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_ORDERS,
               user_id=current_user.id,
               message=f"Admin {current_user.email} requested orders list. Filters: {filters}. Page: {page}, Limit: {limit}"
           )
           
           # Pobieranie listy zamówień
           orders, total_orders, total_pages = await order_service.get_admin_orders(
               page=page,
               limit=limit,
               status=status,
               buyer_id=buyer_id,
               seller_id=seller_id
           )
           
           # Przygotowanie odpowiedzi
           response = OrderListResponse(
               items=orders,
               total=total_orders,
               page=page,
               limit=limit,
               pages=total_pages
           )
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_ORDERS_SUCCESS,
               user_id=current_user.id,
               message=f"Successfully retrieved orders list. Total: {total_orders}"
           )
           
           return response
           
       except ValueError as e:
           # Obsługa błędów walidacji parametrów
           error_message = str(e)
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_ORDERS_FAIL,
               user_id=current_user.id,
               message=f"Failed to retrieve orders list: {error_message}"
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
               event_type=LogEventType.ADMIN_LIST_ORDERS_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while retrieving orders list: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch orders"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       ADMIN_LIST_ORDERS = "ADMIN_LIST_ORDERS"
       ADMIN_LIST_ORDERS_SUCCESS = "ADMIN_LIST_ORDERS_SUCCESS"
       ADMIN_LIST_ORDERS_FAIL = "ADMIN_LIST_ORDERS_FAIL"
   ```

4. **Upewnienie się, że endpoint jest dodany do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(order_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla OrderService.get_admin_orders:
     - Test pobierania listy zamówień bez filtrów
     - Test pobierania listy zamówień z filtrem statusu
     - Test pobierania listy zamówień z filtrem buyer_id
     - Test pobierania listy zamówień z filtrem seller_id
     - Test pobierania listy zamówień z kombinacją filtrów
     - Test paginacji (różne wartości page i limit)
     - Test obsługi błędów dla nieprawidłowych parametrów
   - Test dla handlera list_all_orders:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi parametrami
   - Test wydajności dla dużej liczby zamówień
   - Test paginacji i filtrowania

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Wdrożenie i weryfikacja**:
   - Wdrożenie endpointu na środowisku deweloperskim
   - Weryfikacja poprawnego działania z różnymi parametrami
   - Sprawdzenie logów i rekordów audytu
   - Analiza wydajności zapytań dla dużych zbiorów danych 