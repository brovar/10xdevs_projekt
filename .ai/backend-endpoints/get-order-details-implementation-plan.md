# API Endpoint Implementation Plan: Get Order Details (Buyer/Seller/Admin)

## 1. Przegląd punktu końcowego
Endpoint umożliwia pobranie szczegółowych informacji o konkretnym zamówieniu. Dostęp do danych jest zróżnicowany w zależności od roli użytkownika:
- **Buyer** może zobaczyć tylko własne zamówienia
- **Seller** może zobaczyć zamówienia zawierające jego oferty
- **Admin** ma dostęp do wszystkich zamówień
Endpoint zwraca pełne informacje o zamówieniu, w tym listę pozycji zamówienia, cenę przy zakupie oraz obliczoną łączną wartość zamówienia.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/orders/{order_id}`
- **Parametry**:
  - **Wymagane**:
    - `order_id` (UUID): identyfikator zamówienia w ścieżce URL
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OrderDetailDTO`: Model reprezentujący szczegółowe informacje o zamówieniu
  - `OrderItemDTO`: Model reprezentujący pozycję zamówienia
  - `UserDTO`: Model użytkownika do autoryzacji
- **Enum**:
  - `OrderStatus`: Enum definiujący możliwe statusy zamówienia
  - `UserRole`: Enum definiujący role użytkowników
- **Model bazy danych**:
  - `orders`: Tabela przechowująca zamówienia
  - `order_items`: Tabela przechowująca pozycje zamówienia
  - `users`: Tabela z danymi użytkowników
  - `offers`: Tabela ofert (do sprawdzania czy Seller jest właścicielem oferty)

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "id": "uuid-order-id",
    "buyer_id": "uuid-buyer-id",
    "status": "processing",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "items": [
      {
        "id": 123,
        "offer_id": "uuid-offer-1",
        "quantity": 1,
        "price_at_purchase": "50.00",
        "offer_title": "Product Title 1"
      },
      {
        "id": 124,
        "offer_id": "uuid-offer-2",
        "quantity": 2,
        "price_at_purchase": "36.73",
        "offer_title": "Product Title 2"
      }
    ],
    "total_amount": "123.45"
  }
  ```

- **Kody błędów**:
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest zalogowany
  - 403 Forbidden (`ACCESS_DENIED`): Użytkownik nie ma uprawnień do przeglądania zamówienia
  - 404 Not Found (`ORDER_NOT_FOUND`): Zamówienie nie istnieje
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do kontrolera, który weryfikuje autentykację użytkownika
2. Kontroler validuje parametr `order_id` jako UUID
3. Kontroler wywołuje odpowiednią metodę serwisu zamówień, przekazując `order_id`, id użytkownika oraz jego rolę
4. Serwis zamówień sprawdza, czy użytkownik ma uprawnienia do przeglądania danego zamówienia:
   - Dla Buyera: czy jest właścicielem zamówienia
   - Dla Sellera: czy zamówienie zawiera jego oferty
   - Dla Admina: brak dodatkowych warunków
5. Serwis pobiera dane zamówienia z bazy danych, wraz z powiązanymi pozycjami zamówienia
6. Serwis oblicza łączną kwotę zamówienia na podstawie pozycji
7. Serwis przekształca dane do formatu DTO
8. Kontroler zwraca odpowiedź w formacie JSON

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint wymaga, aby użytkownik był zalogowany (sesja via HttpOnly cookie)
- **Autoryzacja**:
  - Buyer: może widzieć tylko swoje zamówienia (sprawdzanie `buyer_id`)
  - Seller: może widzieć tylko zamówienia zawierające jego oferty (sprawdzanie powiązania `offer_id` -> `seller_id`)
  - Admin: może widzieć wszystkie zamówienia
- **Walidacja danych**:
  - Validacja parametru `order_id` jako prawidłowego UUID
  - Sprawdzenie istnienia zamówienia przed próbą dostępu do danych

## 7. Obsługa błędów
- **Błędy uwierzytelniania**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "User not authenticated"
- **Błędy autoryzacji**:
  - 403 Forbidden z kodem błędu `ACCESS_DENIED` i komunikatem "User does not have permission to view this order"
- **Błędy zasobu**:
  - 404 Not Found z kodem błędu `ORDER_NOT_FOUND` i komunikatem "Order not found"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `FETCH_FAILED` i komunikatem "Failed to fetch order details"
  - Logowanie szczegółów błędu do tabeli `logs` z event_type `ORDER_DETAILS_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumna `id` w tabeli `orders` jest indeksowana (PK)
  - Upewnij się, że kolumna `order_id` w tabeli `order_items` jest indeksowana (FK)
  - Upewnij się, że kolumna `offer_id` w tabeli `order_items` jest indeksowana (FK)
- **Optymalizacja zapytań**:
  - Pobieraj zamówienie i jego pozycje w jednym zapytaniu, używając JOIN
  - Używaj JOIN do pobierania informacji o ofertach (np. tytuł)
- **Buforowanie**:
  - Rozważ buforowanie szczegółów zamówienia na poziomie serwisu dla częstych zapytań (opcjonalnie)

## 9. Etapy wdrożenia
1. **Rozszerzenie serwisu zamówień**:
   - Dodaj metodę `get_order_details(order_id, user_id, user_role)` do `OrderService`
   - Zaimplementuj logikę autoryzacji w zależności od roli użytkownika
   - Dodaj operacje pobierania danych z bazy i tworzenia DTO

2. **Implementacja kontrolera**:
   ```python
   @router.get("/orders/{order_id}", response_model=OrderDetailDTO)
   async def get_order_details(
       order_id: UUID,
       current_user: UserDTO = Depends(get_current_user),
       order_service: OrderService = Depends(get_order_service)
   ):
       try:
           order = await order_service.get_order_details(
               order_id=order_id,
               user_id=current_user.id,
               user_role=current_user.role
           )
           return order
       except PermissionError:
           # Record unauthorized access attempt
           await log_service.create_log(
               event_type=LogEventType.ORDER_DETAILS_FAIL,
               user_id=current_user.id,
               message=f"Unauthorized access attempt to order {order_id}"
           )
           raise HTTPException(
               status_code=403,
               detail={
                   "error_code": "ACCESS_DENIED",
                   "message": "User does not have permission to view this order"
               }
           )
       except ValueError:
           # Record not found
           await log_service.create_log(
               event_type=LogEventType.ORDER_DETAILS_FAIL,
               user_id=current_user.id,
               message=f"Order not found: {order_id}"
           )
           raise HTTPException(
               status_code=404,
               detail={
                   "error_code": "ORDER_NOT_FOUND",
                   "message": "Order not found"
               }
           )
       except Exception as e:
           # Log error
           logger.error(f"Error fetching order details: {str(e)}")
           # Record in logs table
           await log_service.create_log(
               event_type=LogEventType.ORDER_DETAILS_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch order details: {str(e)}"
           )
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch order details"
               }
           )
   ```

3. **Implementacja metody serwisu**:
   ```python
   async def get_order_details(self, order_id: UUID, user_id: UUID, user_role: UserRole) -> OrderDetailDTO:
       # Check if order exists
       query = "SELECT * FROM orders WHERE id = :order_id"
       order_record = await self.db.fetch_one(query, {"order_id": order_id})
       
       if order_record is None:
           raise ValueError(f"Order {order_id} not found")
       
       # Authorization logic based on user role
       if user_role == UserRole.BUYER:
           # Buyer can only view own orders
           if order_record["buyer_id"] != user_id:
               raise PermissionError("User does not have permission to view this order")
       
       elif user_role == UserRole.SELLER:
           # Seller can view orders containing their offers
           query = """
           SELECT COUNT(*) FROM order_items oi
           JOIN offers o ON oi.offer_id = o.id
           WHERE oi.order_id = :order_id AND o.seller_id = :seller_id
           """
           seller_items_count = await self.db.fetch_val(
               query, {"order_id": order_id, "seller_id": user_id}
           )
           
           if seller_items_count == 0:
               raise PermissionError("User does not have permission to view this order")
       
       # Admin can view all orders, no additional checks needed
       
       # Fetch order items
       query = """
       SELECT oi.id, oi.offer_id, oi.quantity, oi.price_at_purchase, o.title as offer_title
       FROM order_items oi
       LEFT JOIN offers o ON oi.offer_id = o.id
       WHERE oi.order_id = :order_id
       """
       item_records = await self.db.fetch_all(query, {"order_id": order_id})
       
       # Calculate total amount
       total_amount = sum(
           item["price_at_purchase"] * item["quantity"] for item in item_records
       )
       
       # Transform to DTOs
       items = [
           OrderItemDTO(
               id=item["id"],
               offer_id=item["offer_id"],
               quantity=item["quantity"],
               price_at_purchase=item["price_at_purchase"],
               offer_title=item["offer_title"]
           )
           for item in item_records
       ]
       
       # Create order detail DTO
       return OrderDetailDTO(
           id=order_record["id"],
           buyer_id=order_record["buyer_id"],
           status=order_record["status"],
           created_at=order_record["created_at"],
           updated_at=order_record["updated_at"],
           items=items,
           total_amount=total_amount
       )
   ```

4. **Dodanie definicji błędów** (jeśli potrzebne):
   - Zarejestruj nowy typ zdarzenia dziennika `ORDER_DETAILS_FAIL` w enum `LogEventType` (jeśli jeszcze nie istnieje)

5. **Testy jednostkowe**:
   - Utwórz testy dla różnych scenariuszy autoryzacji w `OrderService.get_order_details`
   - Utwórz testy dla kontrolera `get_order_details`
   - Uwzględnij przypadki testowe dla różnych ról użytkowników i scenariuszy błędów

6. **Testy integracyjne**:
   - Przetestuj całe przepływy dla różnych ról:
     - Buyer próbujący uzyskać dostęp do własnego zamówienia
     - Buyer próbujący uzyskać dostęp do cudzego zamówienia
     - Seller próbujący uzyskać dostęp do zamówienia zawierającego jego ofertę
     - Seller próbujący uzyskać dostęp do zamówienia bez jego ofert
     - Admin uzyskujący dostęp do dowolnego zamówienia

7. **Dokumentacja API**:
   - Zaktualizuj dokumentację Swagger za pomocą odpowiednich adnotacji FastAPI
   - Dodaj przykłady odpowiedzi dla różnych ról użytkowników 