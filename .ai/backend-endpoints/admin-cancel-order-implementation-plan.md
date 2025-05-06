# API Endpoint Implementation Plan: Cancel Order (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do anulowania zamówienia przez administratora poprzez zmianę jego statusu na "cancelled". Jest to część funkcjonalności administracyjnej systemu, pozwalającej na interwencję w nieprawidłowe, problematyczne lub sporne zamówienia. Anulowane zamówienie nie może być dalej przetwarzane, a jego status jest ostateczny. Wykonanie tej operacji wymaga uprawnień administratora. Anulowanie jest możliwe tylko dla zamówień, które nie zostały jeszcze zrealizowane (dostarczone) lub wcześniej anulowane.

## 2. Szczegóły żądania
- **Metoda HTTP**: POST
- **Struktura URL**: `/admin/orders/{order_id}/cancel`
- **Parametry**:
  - **Wymagane**:
    - `order_id` (UUID): identyfikator zamówienia, które ma zostać anulowane
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OrderDetailDTO`: Model reprezentujący szczegółowe dane zamówienia (zwracany po aktualizacji)
  - `OrderStatus` (enum): Enum definiujący statusy zamówień, używany do zmiany statusu na "cancelled"
  - `UserRole` (enum): Enum definiujący role użytkowników, używany do weryfikacji roli Admin
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania
  - `OrderItemDTO`: Model reprezentujący elementy zamówienia

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**: Obiekt `OrderDetailDTO` ze zaktualizowanym statusem zamówienia
  ```json
  {
    "id": "uuid-order-id",
    "buyer_id": "uuid-buyer-id",
    "status": "cancelled", // Zmieniono na cancelled
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
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 404 Not Found (`ORDER_NOT_FOUND`): Zamówienie o podanym ID nie istnieje
  - 409 Conflict (`CANNOT_CANCEL`): Zamówienia nie można anulować (np. już dostarczone, już anulowane)
  - 500 Internal Server Error (`CANCELLATION_FAILED`): Błąd serwera podczas anulowania zamówienia

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametru `order_id` jako prawidłowego UUID
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu zamówień do anulowania zamówienia
5. Serwis wykonuje następujące operacje w ramach transakcji bazodanowej:
   - Sprawdza, czy zamówienie o podanym ID istnieje
   - Sprawdza, czy zamówienie nie jest już anulowane lub dostarczone (sprawdzenie aktualnego statusu)
   - Aktualizuje status zamówienia na "cancelled"
   - Aktualizuje pole `updated_at` zamówienia
6. Zapisuje zdarzenie anulowania zamówienia w tabeli logów
7. Pobiera pełne dane zamówienia wraz z elementami
8. Zwraca zaktualizowany obiekt zamówienia z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja `order_id` jako prawidłowego UUID
  - Sprawdzenie, czy zamówienie istnieje przed anulowaniem
  - Sprawdzenie, czy zamówienie można anulować (weryfikacja aktualnego statusu)
- **Transakcyjność**:
  - Użycie transakcji bazodanowej do zapewnienia spójności danych
  - W przypadku błędu wszystkie zmiany są wycofywane
- **Audytowanie**:
  - Logowanie operacji anulowania zamówienia w tabeli logów
  - Rejestrowanie ID administratora wykonującego operację, ID zamówienia i czasu wykonania

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 422 Unprocessable Entity: Nieprawidłowy format `order_id` (automatycznie obsługiwane przez FastAPI)
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `ORDER_NOT_FOUND` i komunikatem "Order not found"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `CANNOT_CANCEL` i komunikatem opisującym przyczynę, np. "Order is already cancelled" lub "Order is already delivered and cannot be cancelled"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `CANCELLATION_FAILED` i komunikatem "Failed to cancel order"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Transakcje bazodanowe**:
  - Wykonanie operacji anulowania w pojedynczej, lekkiej transakcji
  - Minimalna liczba zapytań do bazy danych
- **Indeksy bazy danych**:
  - Upewnienie się, że kolumna `id` w tabeli `orders` jest indeksowana (PK)
  - Indeks dla kolumny `status` w tabeli `orders` dla szybszego filtrowania
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych

## 9. Etapy wdrożenia
1. **Rozszerzenie OrderService o metodę do anulowania zamówienia**:
   ```python
   class OrderService:
       def __init__(self, db: Database):
           self.db = db
       
       async def cancel_order(self, order_id: UUID) -> OrderDetailDTO:
           """
           Anuluje zamówienie poprzez zmianę jego statusu na 'cancelled'.
           
           Args:
               order_id: UUID zamówienia do anulowania
               
           Returns:
               OrderDetailDTO zaktualizowanego zamówienia
               
           Raises:
               ValueError: Jeśli zamówienie nie istnieje lub nie może być anulowane
               Exception: Jeśli wystąpi błąd podczas anulowania
           """
           # Rozpocznij transakcję
           async with self.db.transaction():
               # Sprawdź, czy zamówienie istnieje i pobierz jego status
               query = """
               SELECT id, status
               FROM orders
               WHERE id = :order_id
               """
               order = await self.db.fetch_one(query, {"order_id": order_id})
               
               if not order:
                   raise ValueError(f"Order with ID {order_id} not found")
               
               # Sprawdź, czy zamówienie może być anulowane
               current_status = OrderStatus(order["status"])
               
               if current_status == OrderStatus.CANCELLED:
                   raise ValueError(f"Order with ID {order_id} is already cancelled")
               
               if current_status == OrderStatus.DELIVERED:
                   raise ValueError(f"Order with ID {order_id} is already delivered and cannot be cancelled")
               
               # Aktualizuj status zamówienia
               current_time = datetime.now()
               update_query = """
               UPDATE orders
               SET status = :status, updated_at = :updated_at
               WHERE id = :order_id
               """
               await self.db.execute(
                   update_query,
                   {
                       "order_id": order_id,
                       "status": OrderStatus.CANCELLED,
                       "updated_at": current_time
                   }
               )
               
               # Pobierz pełne dane zaktualizowanego zamówienia
               order_query = """
               SELECT o.id, o.buyer_id, o.status, o.created_at, o.updated_at
               FROM orders o
               WHERE o.id = :order_id
               """
               order_data = await self.db.fetch_one(order_query, {"order_id": order_id})
               
               if not order_data:
                   raise Exception(f"Failed to retrieve updated order data for ID {order_id}")
               
               # Pobierz elementy zamówienia
               items_query = """
               SELECT oi.id, oi.offer_id, oi.quantity, oi.price_at_purchase, o.title as offer_title
               FROM order_items oi
               JOIN offers o ON oi.offer_id = o.id
               WHERE oi.order_id = :order_id
               """
               items_data = await self.db.fetch_all(items_query, {"order_id": order_id})
               
               # Przekształć dane elementów do formatu DTO
               order_items = [
                   OrderItemDTO(
                       id=item["id"],
                       offer_id=item["offer_id"],
                       quantity=item["quantity"],
                       price_at_purchase=item["price_at_purchase"],
                       offer_title=item["offer_title"]
                   )
                   for item in items_data
               ]
               
               # Oblicz łączną kwotę zamówienia
               total_amount = sum(item.quantity * item.price_at_purchase for item in order_items)
               
               # Utwórz obiekt DTO
               order_dto = OrderDetailDTO(
                   id=order_data["id"],
                   buyer_id=order_data["buyer_id"],
                   status=order_data["status"],
                   created_at=order_data["created_at"],
                   updated_at=order_data["updated_at"],
                   items=order_items,
                   total_amount=total_amount
               )
               
               return order_dto
   ```

2. **Implementacja handlera endpointu**:
   ```python
   @router.post(
       "/admin/orders/{order_id}/cancel",
       response_model=OrderDetailDTO,
       summary="Cancel order",
       description="Sets order status to 'cancelled'. Requires Admin role.",
       responses={
           200: {"description": "Order cancelled successfully"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           404: {"description": "Order not found"},
           409: {"description": "Order cannot be cancelled"},
           500: {"description": "Server error while cancelling order"}
       }
   )
   async def cancel_order(
       order_id: UUID = Path(..., description="The ID of the order to cancel"),
       current_user: UserDTO = Depends(require_admin),
       order_service: OrderService = Depends(get_order_service),
       log_service: LogService = Depends(get_log_service)
   ) -> OrderDetailDTO:
       """
       Anuluje zamówienie poprzez zmianę jego statusu na 'cancelled'.
       Anulowanie jest możliwe tylko dla zamówień, które nie zostały jeszcze zrealizowane
       (dostarczone) lub wcześniej anulowane.
       Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie próby anulowania
           await log_service.create_log(
               event_type=LogEventType.ORDER_CANCEL_ATTEMPT,
               user_id=current_user.id,
               message=f"Admin {current_user.email} attempted to cancel order with ID {order_id}"
           )
           
           # Anulowanie zamówienia
           cancelled_order = await order_service.cancel_order(order_id)
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.ORDER_CANCELLED,
               user_id=current_user.id,
               message=f"Admin {current_user.email} successfully cancelled order with ID {order_id}"
           )
           
           return cancelled_order
           
       except ValueError as e:
           error_message = str(e)
           
           # Określ kod błędu na podstawie treści komunikatu
           if "not found" in error_message.lower():
               error_code = "ORDER_NOT_FOUND"
               status_code = 404
           elif "already cancelled" in error_message.lower() or "cannot be cancelled" in error_message.lower():
               error_code = "CANNOT_CANCEL"
               status_code = 409
           else:
               error_code = "INVALID_REQUEST"
               status_code = 400
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.ORDER_CANCEL_FAIL,
               user_id=current_user.id,
               message=f"Failed to cancel order {order_id}: {error_message}"
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
               event_type=LogEventType.ORDER_CANCEL_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while cancelling order {order_id}: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "CANCELLATION_FAILED",
                   "message": "Failed to cancel order"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       ORDER_CANCEL_ATTEMPT = "ORDER_CANCEL_ATTEMPT"
       ORDER_CANCELLED = "ORDER_CANCELLED"
       ORDER_CANCEL_FAIL = "ORDER_CANCEL_FAIL"
   ```

4. **Upewnienie się, że endpoint jest dodany do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera (powinien być już dodany w ramach order_router)
   admin_router.include_router(order_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla OrderService.cancel_order:
     - Test anulowania zamówienia z prawidłowym ID i statusem umożliwiającym anulowanie
     - Test anulowania nieistniejącego zamówienia (oczekiwany wyjątek)
     - Test anulowania zamówienia, które jest już anulowane (oczekiwany wyjątek)
     - Test anulowania zamówienia, które zostało dostarczone (oczekiwany wyjątek)
   - Test dla handlera cancel_order:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi z zaktualizowanym zamówieniem
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow: utworzenie → opłacenie → przetwarzanie → anulowanie zamówienia
   - Test scenariuszy błędów (nieistniejące zamówienie, zamówienie już anulowane, zamówienie dostarczone)
   - Test wpływu anulowania na powiązane encje (np. czy status ofert się zmienia)

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Wdrożenie i weryfikacja**:
   - Wdrożenie endpointu na środowisku deweloperskim
   - Weryfikacja poprawnego działania w różnych scenariuszach
   - Sprawdzenie logów i rekordów audytu 