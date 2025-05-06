# API Endpoint Implementation Plan: List Orders (Buyer)

## 1. Przegląd punktu końcowego
Endpoint ten umożliwia zalogowanym użytkownikom z rolą Buyer przeglądanie historii swoich zamówień w postaci paginowanej listy. Zwraca podstawowe informacje o zamówieniach, takie jak identyfikator, status, łączna kwota oraz daty utworzenia i aktualizacji.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/orders`
- **Parametry**:
  - **Opcjonalne**:
    - `page` (integer, domyślnie 1): Numer strony do pobrania
    - `limit` (integer, domyślnie 100, maksymalnie 100): Liczba elementów na stronę
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OrderSummaryDTO`: Model reprezentujący podstawowe informacje o zamówieniu
  - `OrderListResponse` (dziedziczy po `PaginatedResponse`): Model odpowiedzi zawierający paginowaną listę zamówień
- **Enum**:
  - `OrderStatus`: Enum definiujący możliwe statusy zamówienia
- **Model bazy danych**:
  - `orders`: Tabela przechowująca zamówienia
  - `order_items`: Tabela przechowująca pozycje zamówienia

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "items": [
      {
        "id": "uuid-order-id",
        "status": "processing",
        "total_amount": "123.45",
        "created_at": "timestamp",
        "updated_at": "timestamp" // opcjonalne
      }
    ],
    "total": 25, // całkowita liczba zamówień
    "page": 1, // aktualna strona
    "limit": 100, // elementy na stronę
    "pages": 1 // całkowita liczba stron
  }
  ```

- **Kody błędów**:
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest zalogowany
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie jest Buyerem
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do kontrolera, który weryfikuje autentykację użytkownika
2. Kontroler sprawdza, czy użytkownik ma rolę Buyer
3. Kontroler waliduje parametry paginacji
4. Kontroler wywołuje odpowiednią metodę serwisu zamówień
5. Serwis zamówień wykonuje zapytanie do bazy danych, pobierając zamówienia danego użytkownika
6. Serwis oblicza łączną kwotę każdego zamówienia na podstawie pozycji zamówienia
7. Serwis przetwarza wyniki, tworząc odpowiedź paginowaną
8. Kontroler zwraca odpowiedź w formacie JSON

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint wymaga, aby użytkownik był zalogowany (sesja via HttpOnly cookie)
- **Autoryzacja**: 
  - Użytkownik musi mieć rolę Buyer
  - Użytkownik może widzieć tylko swoje zamówienia (filtrowanie po buyer_id)
- **Walidacja danych**:
  - Parametry paginacji są walidowane pod kątem typów i wartości granicznych
  - Sprawdzenie, czy limit nie przekracza maksymalnej dozwolonej wartości (100)

## 7. Obsługa błędów
- **Błędy uwierzytelniania**: 
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "User not authenticated"
- **Błędy autoryzacji**: 
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "User must have Buyer role to access orders"
- **Błędy serwera**: 
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch orders"
  - Logowanie szczegółów błędu do tabeli `logs` z event_type `ORDER_LIST_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**: 
  - Upewnij się, że kolumna `buyer_id` w tabeli `orders` jest indeksowana
  - Upewnij się, że kolumna `order_id` w tabeli `order_items` jest indeksowana
- **Paginacja**: 
  - Zaimplementuj paginację na poziomie bazy danych, a nie aplikacji
  - Użyj OFFSET/LIMIT w zapytaniu SQL
- **Obliczanie łącznej kwoty**:
  - Rozważ obliczenie łącznej kwoty za pomocą agregacji w bazie danych, zamiast w aplikacji
  - Alternatywnie, używaj JOIN do pobierania powiązanych pozycji zamówienia w jednym zapytaniu

## 9. Etapy wdrożenia
1. **Utworzenie serwisu zamówień**:
   - Zaimplementuj klasę `OrderService` z metodą `get_buyer_orders`
   - Dodaj logikę paginacji i filtrowania po buyer_id
   - Uwzględnij obliczanie łącznej kwoty zamówienia

2. **Utworzenie zależności FastAPI**:
   - Zdefiniuj zależność `require_buyer` do sprawdzania, czy użytkownik ma rolę Buyer
   - Wykorzystaj istniejącą zależność `get_current_user` do uwierzytelniania

3. **Implementacja kontrolera**:
   ```python
   @router.get("/orders", response_model=OrderListResponse)
   async def list_buyer_orders(
       current_user: UserDTO = Depends(get_current_user),
       _: None = Depends(require_buyer),
       page: int = Query(1, ge=1),
       limit: int = Query(100, ge=1, le=100),
       order_service: OrderService = Depends(get_order_service)
   ):
       try:
           orders = await order_service.get_buyer_orders(
               buyer_id=current_user.id,
               page=page,
               limit=limit
           )
           return orders
       except Exception as e:
           # Log error
           logger.error(f"Error fetching orders: {str(e)}")
           # Record in logs table
           await log_service.create_log(
               event_type=LogEventType.ORDER_LIST_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch orders: {str(e)}"
           )
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch orders"
               }
           )
   ```

4. **Implementacja serwisu zamówień**:
   ```python
   class OrderService:
       def __init__(self, db: Database):
           self.db = db
       
       async def get_buyer_orders(self, buyer_id: UUID, page: int = 1, limit: int = 100) -> OrderListResponse:
           # Calculate offset
           offset = (page - 1) * limit
           
           # Get total count
           query = "SELECT COUNT(*) FROM orders WHERE buyer_id = :buyer_id"
           total = await self.db.fetch_val(query, {"buyer_id": buyer_id})
           
           # Get orders
           query = """
           SELECT o.id, o.status, o.created_at, o.updated_at,
                  SUM(oi.price_at_purchase * oi.quantity) as total_amount
           FROM orders o
           JOIN order_items oi ON o.id = oi.order_id
           WHERE o.buyer_id = :buyer_id
           GROUP BY o.id, o.status, o.created_at, o.updated_at
           ORDER BY o.created_at DESC
           LIMIT :limit OFFSET :offset
           """
           
           records = await self.db.fetch_all(
               query, 
               {"buyer_id": buyer_id, "limit": limit, "offset": offset}
           )
           
           # Transform to DTOs
           items = [
               OrderSummaryDTO(
                   id=record["id"],
                   status=record["status"],
                   total_amount=record["total_amount"],
                   created_at=record["created_at"],
                   updated_at=record["updated_at"]
               )
               for record in records
           ]
           
           # Calculate pages
           pages = (total + limit - 1) // limit
           
           return OrderListResponse(
               items=items,
               total=total,
               page=page,
               limit=limit,
               pages=pages
           )
   ```

5. **Dodanie definicji błędów**:
   - Zarejestruj nowy typ zdarzenia dziennika `ORDER_LIST_FAIL` w enum `LogEventType` (jeśli jeszcze nie istnieje)

6. **Testy jednostkowe**:
   - Utwórz testy dla `OrderService.get_buyer_orders`
   - Utwórz testy dla kontrolera `list_buyer_orders`
   - Uwzględnij przypadki testowe dla różnych scenariuszy błędów

7. **Testy integracyjne**:
   - Przetestuj pełny przepływ żądania-odpowiedzi
   - Sprawdź poprawność paginacji
   - Sprawdź obliczanie łącznej kwoty zamówienia

8. **Dokumentacja API**:
   - Zaktualizuj dokumentację Swagger za pomocą odpowiednich adnotacji FastAPI
   - Dodaj przykłady żądań i odpowiedzi 