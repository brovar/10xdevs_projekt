# API Endpoint Implementation Plan: Deliver Order

## 1. Przegląd punktu końcowego
Endpoint umożliwia sprzedawcom oznaczenie zamówienia jako dostarczone, zmieniając jego status z "shipped" na "delivered". Sprzedawca musi być właścicielem przynajmniej jednego przedmiotu w zamówieniu, aby móc wykonać tę operację. Endpoint zwraca zaktualizowane szczegóły zamówienia po pomyślnej zmianie statusu.

## 2. Szczegóły żądania
- **Metoda HTTP**: POST
- **Struktura URL**: `/orders/{order_id}/deliver`
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
  - `LogEventType`: Enum definiujący typy zdarzeń logowania
- **Model bazy danych**:
  - `orders`: Tabela przechowująca zamówienia
  - `order_items`: Tabela przechowująca pozycje zamówienia
  - `offers`: Tabela przechowująca oferty (do powiązania z sellerem)

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**: Zaktualizowany obiekt OrderDetailDTO, taki sam jak z endpointu `GET /orders/{order_id}`:
  ```json
  {
    "id": "uuid-order-id",
    "buyer_id": "uuid-buyer-id",
    "status": "delivered", // Nowy status zamówienia
    "created_at": "timestamp",
    "updated_at": "timestamp", // Zaktualizowany timestamp
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
  - 400 Bad Request (`INVALID_ORDER_ID`): Nieprawidłowy format identyfikatora zamówienia
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest zalogowany
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie jest Sellerem lub nie jest właścicielem żadnego przedmiotu w zamówieniu
  - 404 Not Found (`ORDER_NOT_FOUND`): Zamówienie nie istnieje
  - 409 Conflict (`INVALID_ORDER_STATUS`): Zamówienie nie jest w statusie "shipped"
  - 500 Internal Server Error (`DELIVER_FAILED`): Błąd serwera podczas zmiany statusu

## 5. Przepływ danych
1. Żądanie trafia do kontrolera, który weryfikuje autentykację użytkownika
2. Kontroler validuje parametr `order_id` jako UUID
3. Kontroler sprawdza, czy użytkownik ma rolę Seller
4. Kontroler wywołuje odpowiednią metodę serwisu zamówień, przekazując `order_id` i id sprzedawcy
5. Serwis zamówień sprawdza, czy zamówienie istnieje
6. Serwis zamówień sprawdza, czy sprzedawca jest właścicielem przynajmniej jednego przedmiotu w zamówieniu
7. Serwis zamówień sprawdza, czy zamówienie jest w statusie "shipped"
8. Serwis zamówień aktualizuje status zamówienia na "delivered" i ustawia `updated_at` na aktualny czas
9. Serwis zamówień pobiera zaktualizowane dane zamówienia
10. Serwis tworzy wpis w logach o zmianie statusu zamówienia
11. Kontroler zwraca zaktualizowane szczegóły zamówienia

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint wymaga, aby użytkownik był zalogowany (sesja via HttpOnly cookie)
- **Autoryzacja**:
  - Użytkownik musi mieć rolę Seller
  - Sprzedawca może oznaczać jako dostarczone tylko zamówienia zawierające jego oferty (sprawdzanie powiązania `offer_id` -> `seller_id`)
- **Walidacja danych**:
  - Validacja parametru `order_id` jako prawidłowego UUID
  - Sprawdzenie istnienia zamówienia przed próbą aktualizacji
  - Sprawdzenie, czy aktualny status zamówienia to "shipped"
- **Konsystencja danych**:
  - Używanie transakcji do zapewnienia atomowości operacji zmiany statusu

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 400 Bad Request z kodem błędu `INVALID_ORDER_ID` i komunikatem "Invalid order ID format"
- **Błędy uwierzytelniania**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "User not authenticated"
- **Błędy autoryzacji**:
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "User must be a seller and own items in this order"
- **Błędy zasobu**:
  - 404 Not Found z kodem błędu `ORDER_NOT_FOUND` i komunikatem "Order not found"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `INVALID_ORDER_STATUS` i komunikatem "Order must be in 'shipped' status to be delivered"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `DELIVER_FAILED` i komunikatem "Failed to deliver order"
  - Logowanie szczegółów błędu do tabeli `logs` z event_type `ORDER_DELIVER_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumna `id` w tabeli `orders` jest indeksowana (PK)
  - Upewnij się, że kolumna `order_id` w tabeli `order_items` jest indeksowana (FK)
  - Upewnij się, że kolumna `offer_id` w tabeli `order_items` jest indeksowana (FK)
  - Upewnij się, że kolumna `seller_id` w tabeli `offers` jest indeksowana
- **Transakcje**:
  - Użyj transakcji bazodanowej do zapewnienia atomowości operacji aktualizacji statusu
- **Operacje asynchroniczne**:
  - Implementuj endpoint jako asynchroniczny w FastAPI dla lepszej wydajności przy operacjach I/O-bound

## 9. Etapy wdrożenia
1. **Rozszerzenie serwisu zamówień**:
   - Dodaj metodę `deliver_order(order_id, seller_id)` do `OrderService`
   - Implementuj wszystkie niezbędne kroki walidacji i przetwarzania
   - Zapewnij odpowiednią obsługę błędów na poziomie serwisu

2. **Implementacja kontrolera**:
   ```python
   @router.post("/orders/{order_id}/deliver", response_model=OrderDetailDTO)
   async def deliver_order(
       order_id: UUID,
       current_user: UserDTO = Depends(get_current_user),
       order_service: OrderService = Depends(get_order_service),
       log_service: LogService = Depends(get_log_service)
   ):
       # Sprawdź czy użytkownik jest sprzedawcą
       if current_user.role != UserRole.SELLER:
           await log_service.create_log(
               event_type=LogEventType.ORDER_DELIVER_FAIL,
               user_id=current_user.id,
               message=f"Unauthorized attempt to deliver order {order_id} by non-seller user"
           )
           raise HTTPException(
               status_code=403,
               detail={
                   "error_code": "INSUFFICIENT_PERMISSIONS",
                   "message": "User must be a seller to deliver orders"
               }
           )
       
       try:
           updated_order = await order_service.deliver_order(
               order_id=order_id,
               seller_id=current_user.id
           )
           
           # Log successful order delivery
           await log_service.create_log(
               event_type=LogEventType.ORDER_STATUS_CHANGE,
               user_id=current_user.id,
               message=f"Order {order_id} delivered by seller {current_user.id}"
           )
           
           return updated_order
       
       except ValueError as e:
           # Obsługa błędów walidacji lub nieistniejącego zamówienia
           error_message = str(e)
           error_code = "ORDER_NOT_FOUND"
           status_code = 404
           
           if "Invalid order ID" in error_message:
               error_code = "INVALID_ORDER_ID"
               status_code = 400
           
           await log_service.create_log(
               event_type=LogEventType.ORDER_DELIVER_FAIL,
               user_id=current_user.id,
               message=f"Failed to deliver order: {error_message}"
           )
           
           raise HTTPException(
               status_code=status_code,
               detail={
                   "error_code": error_code,
                   "message": error_message
               }
           )
       
       except PermissionError:
           # Obsługa błędów autoryzacji
           await log_service.create_log(
               event_type=LogEventType.ORDER_DELIVER_FAIL,
               user_id=current_user.id,
               message=f"Seller {current_user.id} not authorized to deliver order {order_id}"
           )
           
           raise HTTPException(
               status_code=403,
               detail={
                   "error_code": "INSUFFICIENT_PERMISSIONS",
                   "message": "User must own items in this order to deliver it"
               }
           )
       
       except ConflictError:
           # Obsługa błędów stanu zamówienia
           await log_service.create_log(
               event_type=LogEventType.ORDER_DELIVER_FAIL,
               user_id=current_user.id,
               message=f"Cannot deliver order {order_id}: invalid order status"
           )
           
           raise HTTPException(
               status_code=409,
               detail={
                   "error_code": "INVALID_ORDER_STATUS",
                   "message": "Order must be in 'shipped' status to be delivered"
               }
           )
       
       except Exception as e:
           # Obsługa nieoczekiwanych błędów
           logger.error(f"Error delivering order: {str(e)}")
           await log_service.create_log(
               event_type=LogEventType.ORDER_DELIVER_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error delivering order {order_id}: {str(e)}"
           )
           
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "DELIVER_FAILED",
                   "message": "Failed to deliver order"
               }
           )
   ```

3. **Implementacja metody serwisu**:
   ```python
   async def deliver_order(self, order_id: UUID, seller_id: UUID) -> OrderDetailDTO:
       # Check if order exists
       query = "SELECT * FROM orders WHERE id = :order_id"
       order_record = await self.db.fetch_one(query, {"order_id": order_id})
       
       if order_record is None:
           raise ValueError(f"Order {order_id} not found")
       
       # Check if order is in 'shipped' status
       if order_record["status"] != OrderStatus.SHIPPED:
           raise ConflictError(f"Order must be in 'shipped' status to be delivered")
       
       # Check if seller owns any items in this order
       query = """
       SELECT COUNT(*) FROM order_items oi
       JOIN offers o ON oi.offer_id = o.id
       WHERE oi.order_id = :order_id AND o.seller_id = :seller_id
       """
       seller_items_count = await self.db.fetch_val(
           query, {"order_id": order_id, "seller_id": seller_id}
       )
       
       if seller_items_count == 0:
           raise PermissionError("Seller does not own any items in this order")
       
       # Update order status to 'delivered'
       async with self.db.transaction():
           query = """
           UPDATE orders 
           SET status = :new_status, updated_at = :updated_at
           WHERE id = :order_id
           """
           await self.db.execute(
               query, 
               {
                   "order_id": order_id, 
                   "new_status": OrderStatus.DELIVERED,
                   "updated_at": datetime.now()
               }
           )
       
       # Get updated order details using existing method
       return await self.get_order_details(order_id, seller_id, UserRole.SELLER)
   ```

4. **Dodanie typów zdarzeń logowania** (jeśli nie istnieją):
   - Upewnij się, że w enum `LogEventType` istnieją zdarzenia `ORDER_STATUS_CHANGE` i `ORDER_DELIVER_FAIL`

5. **Testy jednostkowe**:
   - Utwórz testy dla `OrderService.deliver_order`
   - Przetestuj wszystkie scenariusze błędów:
     - Zamówienie nie istnieje
     - Zamówienie nie jest w statusie "shipped"
     - Sprzedawca nie jest właścicielem żadnego przedmiotu w zamówieniu
   - Przetestuj pomyślny przypadek zmiany statusu

6. **Testy integracyjne**:
   - Przetestuj cały przepływ żądania-odpowiedzi
   - Sprawdź, czy status zamówienia jest rzeczywiście aktualizowany w bazie danych
   - Sprawdź, czy zwracany obiekt OrderDetailDTO ma prawidłowo zaktualizowany status
   - Sprawdź, czy zdarzenie jest prawidłowo logowane

7. **Dokumentacja API**:
   - Zaktualizuj dokumentację Swagger za pomocą odpowiednich adnotacji FastAPI
   - Dodaj przykładowe odpowiedzi dla powodzenia i różnych scenariuszy błędów 