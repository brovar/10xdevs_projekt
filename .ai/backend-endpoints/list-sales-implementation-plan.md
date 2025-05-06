# API Endpoint Implementation Plan: List Sales (Seller)

## 1. Przegląd punktu końcowego
Endpoint umożliwia zalogowanym użytkownikom z rolą Seller przeglądanie historii sprzedaży w postaci paginowanej listy zamówień, które zawierają produkty sprzedane przez danego sprzedawcę. Zwraca podstawowe informacje o zamówieniach, podobne do tych z endpointu `GET /orders`, takie jak identyfikator, status, łączna kwota oraz daty utworzenia i aktualizacji.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/account/sales`
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
  - `UserRole`: Enum definiujący role użytkownika
- **Model bazy danych**:
  - `orders`: Tabela przechowująca zamówienia
  - `order_items`: Tabela przechowująca pozycje zamówienia
  - `offers`: Tabela przechowująca oferty (do powiązania z sellerem)

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
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie jest Sellerem
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do kontrolera, który weryfikuje autentykację użytkownika
2. Kontroler sprawdza, czy użytkownik ma rolę Seller
3. Kontroler waliduje parametry paginacji
4. Kontroler wywołuje odpowiednią metodę serwisu zamówień
5. Serwis wykonuje złożone zapytanie do bazy danych, które:
   - Pobiera zamówienia zawierające oferty danego sprzedawcy
   - Grupuje wyniki, aby uniknąć duplikatów zamówień (jeden seller może mieć kilka ofert w zamówieniu)
   - Oblicza łączną kwotę każdego zamówienia
6. Serwis przetwarza wyniki, tworząc odpowiedź paginowaną
7. Kontroler zwraca odpowiedź w formacie JSON

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint wymaga, aby użytkownik był zalogowany (sesja via HttpOnly cookie)
- **Autoryzacja**: 
  - Użytkownik musi mieć rolę Seller
  - Użytkownik może widzieć tylko zamówienia zawierające jego oferty
- **Walidacja danych**:
  - Parametry paginacji są walidowane pod kątem typów i wartości granicznych
  - Sprawdzenie, czy limit nie przekracza maksymalnej dozwolonej wartości (100)

## 7. Obsługa błędów
- **Błędy uwierzytelniania**: 
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "User not authenticated"
- **Błędy autoryzacji**: 
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "User must have Seller role to access sales history"
- **Błędy serwera**: 
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch sales data"
  - Logowanie szczegółów błędu do tabeli `logs` z event_type `SALES_LIST_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**: 
  - Upewnij się, że kolumna `order_id` w tabeli `order_items` jest indeksowana
  - Upewnij się, że kolumna `offer_id` w tabeli `order_items` jest indeksowana
  - Upewnij się, że kolumna `seller_id` w tabeli `offers` jest indeksowana
- **Złożone zapytanie**: 
  - Zapytanie wymaga złączenia trzech tabel (orders, order_items, offers)
  - Użyj odpowiednich JOINów i indeksów, aby zoptymalizować wykonanie
- **Paginacja**: 
  - Zaimplementuj paginację na poziomie bazy danych, nie aplikacji
  - Użyj OFFSET/LIMIT w zapytaniu SQL
- **Grupowanie**: 
  - Użyj GROUP BY, aby uniknąć duplikowania zamówień, które zawierają wiele produktów tego samego sprzedawcy

## 9. Etapy wdrożenia
1. **Rozszerzenie serwisu zamówień**:
   - Dodaj metodę `get_seller_sales(seller_id, page, limit)` do `OrderService`
   - Implementacja złożonego zapytania SQL
   - Uwzględnij obliczanie łącznej kwoty zamówienia

2. **Utworzenie zależności FastAPI**:
   - Zdefiniuj zależność `require_seller` do sprawdzania, czy użytkownik ma rolę Seller
   - Wykorzystaj istniejącą zależność `get_current_user` do uwierzytelniania

3. **Implementacja kontrolera**:
   ```python
   @router.get("/account/sales", response_model=OrderListResponse)
   async def list_seller_sales(
       current_user: UserDTO = Depends(get_current_user),
       _: None = Depends(require_seller),
       page: int = Query(1, ge=1),
       limit: int = Query(100, ge=1, le=100),
       order_service: OrderService = Depends(get_order_service)
   ):
       try:
           sales = await order_service.get_seller_sales(
               seller_id=current_user.id,
               page=page,
               limit=limit
           )
           return sales
       except Exception as e:
           # Log error
           logger.error(f"Error fetching sales data: {str(e)}")
           # Record in logs table
           await log_service.create_log(
               event_type=LogEventType.SALES_LIST_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch sales data: {str(e)}"
           )
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch sales data"
               }
           )
   ```

4. **Implementacja metody serwisu**:
   ```python
   async def get_seller_sales(self, seller_id: UUID, page: int = 1, limit: int = 100) -> OrderListResponse:
       # Calculate offset
       offset = (page - 1) * limit
       
       # Get total count of orders containing seller's offers
       query = """
       SELECT COUNT(DISTINCT o.id)
       FROM orders o
       JOIN order_items oi ON o.id = oi.order_id
       JOIN offers of ON oi.offer_id = of.id
       WHERE of.seller_id = :seller_id
       """
       total = await self.db.fetch_val(query, {"seller_id": seller_id})
       
       # Get orders containing seller's offers
       query = """
       SELECT o.id, o.status, o.created_at, o.updated_at,
              SUM(oi.price_at_purchase * oi.quantity) as total_amount
       FROM orders o
       JOIN order_items oi ON o.id = oi.order_id
       JOIN offers of ON oi.offer_id = of.id
       WHERE of.seller_id = :seller_id
       GROUP BY o.id, o.status, o.created_at, o.updated_at
       ORDER BY o.created_at DESC
       LIMIT :limit OFFSET :offset
       """
       
       records = await self.db.fetch_all(
           query, 
           {"seller_id": seller_id, "limit": limit, "offset": offset}
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
       pages = (total + limit - 1) // limit if total > 0 else 1
       
       return OrderListResponse(
           items=items,
           total=total,
           page=page,
           limit=limit,
           pages=pages
       )
   ```

5. **Dodanie definicji błędów**:
   - Zarejestruj nowy typ zdarzenia dziennika `SALES_LIST_FAIL` w enum `LogEventType` (jeśli jeszcze nie istnieje)

6. **Utworzenie zależności autoryzacyjnej**:
   ```python
   def require_seller(current_user: UserDTO = Depends(get_current_user)):
       if current_user.role != UserRole.SELLER:
           raise HTTPException(
               status_code=403,
               detail={
                   "error_code": "INSUFFICIENT_PERMISSIONS",
                   "message": "User must have Seller role to access sales history"
               }
           )
       return None
   ```

7. **Testy jednostkowe**:
   - Utwórz testy dla `OrderService.get_seller_sales`
   - Utwórz testy dla kontrolera `list_seller_sales`
   - Uwzględnij przypadki testowe dla różnych scenariuszy błędów i autoryzacji

8. **Testy integracyjne**:
   - Przetestuj pełny przepływ żądania-odpowiedzi
   - Sprawdź poprawność paginacji
   - Sprawdź poprawność filtrowania po seller_id
   - Sprawdź poprawność obliczania łącznej kwoty zamówienia

9. **Dokumentacja API**:
   - Zaktualizuj dokumentację Swagger za pomocą odpowiednich adnotacji FastAPI
   - Dodaj przykłady żądań i odpowiedzi 