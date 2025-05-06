# API Endpoint Implementation Plan: Handle Payment Callback

## 1. Przegląd punktu końcowego
Endpoint służy do obsługi powiadomień z zewnętrznego systemu płatności o wyniku transakcji. Jest wywoływany przez dostawcę płatności (mock payment provider) po zakończeniu procesu płatności przez użytkownika. Na podstawie otrzymanych parametrów, aktualizuje status transakcji, status zamówienia oraz dostępną ilość produktów w przypadku pomyślnej płatności. Endpoint nie jest przeznaczony do bezpośredniego wywołania przez frontend, ale przez zewnętrzny system.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/payments/callback`
- **Parametry**:
  - **Wymagane**:
    - `transaction_id` (UUID): identyfikator transakcji w systemie
    - `status` (string): wynik transakcji - jedna z wartości: `success`, `fail`, `cancelled`
  - **Opcjonalne**:
    - Dodatkowe parametry od dostawcy płatności (np. external_id, checksum) - ignorowane w MVP, ale mogą być obsługiwane w przyszłości
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `PaymentCallbackResponse`: Model odpowiedzi zawierający komunikat i status zamówienia
- **Enum**:
  - `TransactionStatus`: Enum definiujący możliwe statusy transakcji (`SUCCESS`, `FAIL`, `CANCELLED`)
  - `OrderStatus`: Enum definiujący możliwe statusy zamówienia (`PENDING_PAYMENT`, `PROCESSING`, `CANCELLED`, `FAILED`)
  - `LogEventType`: Enum definiujący typy zdarzeń logowania
- **Model bazy danych**:
  - `transactions`: Tabela przechowująca transakcje
  - `orders`: Tabela przechowująca zamówienia
  - `order_items`: Tabela przechowująca pozycje zamówienia
  - `offers`: Tabela przechowująca oferty (do aktualizacji ilości w przypadku sukcesu)

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "message": "Callback processed",
    "order_status": "processing" // Lub "failed"/"cancelled" w zależności od status transakcji
  }
  ```

- **Kody błędów**:
  - 400 Bad Request (`MISSING_PARAM`, `INVALID_PARAM`, `INVALID_STATUS`): Brakujące lub nieprawidłowe parametry
  - 404 Not Found (`TRANSACTION_NOT_FOUND`, `ORDER_NOT_FOUND`): Transakcja lub zamówienie nie istnieje
  - 409 Conflict (`ORDER_ALREADY_PROCESSED`): Zamówienie zostało już przetworzone
  - 500 Internal Server Error (`CALLBACK_PROCESSING_FAILED`): Błąd serwera podczas przetwarzania

## 5. Przepływ danych
1. Żądanie trafia do kontrolera
2. Kontroler waliduje parametry (transaction_id jako UUID, status jako dopuszczalna wartość)
3. Kontroler wywołuje odpowiednią metodę serwisu płatności, przekazując transaction_id i status
4. Serwis płatności sprawdza, czy transakcja istnieje
5. Serwis płatności pobiera powiązane zamówienie
6. Serwis płatności sprawdza, czy zamówienie nie zostało już przetworzone (status inny niż PENDING_PAYMENT)
7. W zależności od statusu transakcji:
   - `success`: 
     - Aktualizuje status transakcji na SUCCESS
     - Aktualizuje status zamówienia na PROCESSING
     - Aktualizuje ilość dostępnych produktów dla każdej pozycji zamówienia
   - `fail` lub `cancelled`:
     - Aktualizuje status transakcji odpowiednio na FAIL lub CANCELLED
     - Aktualizuje status zamówienia odpowiednio na FAILED lub CANCELLED
8. Serwis tworzy wpis w logach o wyniku przetwarzania płatności
9. Kontroler zwraca odpowiedź z komunikatem i zaktualizowanym statusem zamówienia

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Endpoint nie wymaga standardowego uwierzytelniania, ponieważ jest wywoływany przez zewnętrzny system
  - W przyszłych wersjach można rozważyć dodatkową walidację (np. tokeny, podpisy cyfrowe) do weryfikacji autentyczności żądania
- **Walidacja danych**:
  - Ścisła walidacja transaction_id jako prawidłowego UUID
  - Walidacja statusu jako jednej z dozwolonych wartości
  - Sprawdzenie istnienia transakcji i powiązanego zamówienia
- **Atomowość operacji**:
  - Użycie transakcji bazodanowej do zapewnienia atomowości operacji aktualizacji statusów i ilości produktów
- **Idempotentność**:
  - Implementacja mechanizmu zapobiegającego wielokrotnemu przetworzeniu tego samego zdarzenia płatności

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 400 Bad Request z kodem błędu `MISSING_PARAM` i komunikatem "Missing required parameter: [parameter_name]"
  - 400 Bad Request z kodem błędu `INVALID_PARAM` i komunikatem "Invalid parameter format: [parameter_name]"
  - 400 Bad Request z kodem błędu `INVALID_STATUS` i komunikatem "Invalid status value. Allowed values: success, fail, cancelled"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `TRANSACTION_NOT_FOUND` i komunikatem "Transaction not found"
  - 404 Not Found z kodem błędu `ORDER_NOT_FOUND` i komunikatem "Order not found for transaction"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `ORDER_ALREADY_PROCESSED` i komunikatem "Order has already been processed"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `CALLBACK_PROCESSING_FAILED` i komunikatem "Failed to process payment callback"
  - Logowanie szczegółów błędu do tabeli `logs` z event_type `PAYMENT_CALLBACK_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumna `id` w tabeli `transactions` jest indeksowana (PK)
  - Upewnij się, że kolumna `order_id` w tabeli `transactions` jest indeksowana (FK)
  - Upewnij się, że kolumna `id` w tabeli `orders` jest indeksowana (PK)
- **Transakcje**:
  - Użyj transakcji bazodanowej do zapewnienia atomowości i izolacji operacji aktualizacji
- **Operacje asynchroniczne**:
  - Implementuj endpoint jako asynchroniczny w FastAPI dla lepszej wydajności
- **Obsługa równoczesnych żądań**:
  - Implementacja mechanizmu blokady optymistycznej do obsługi równoczesnych aktualizacji

## 9. Etapy wdrożenia
1. **Utworzenie serwisu płatności**:
   - Implementacja `PaymentService` z metodą `process_payment_callback(transaction_id, status)`
   - Dodanie logiki przetwarzania różnych statusów płatności
   - Implementacja aktualizacji ilości produktów

2. **Implementacja kontrolera**:
   ```python
   @router.get("/payments/callback", response_model=PaymentCallbackResponse)
   async def handle_payment_callback(
       transaction_id: UUID = Query(..., description="Transaction ID"),
       status: str = Query(..., description="Transaction status"),
       payment_service: PaymentService = Depends(get_payment_service),
       log_service: LogService = Depends(get_log_service)
   ):
       # Walidacja statusu
       if status not in ["success", "fail", "cancelled"]:
           await log_service.create_log(
               event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
               message=f"Invalid payment status: {status} for transaction {transaction_id}"
           )
           raise HTTPException(
               status_code=400,
               detail={
                   "error_code": "INVALID_STATUS",
                   "message": "Invalid status value. Allowed values: success, fail, cancelled"
               }
           )
       
       try:
           # Przekształcenie statusu string na enum
           transaction_status = TransactionStatus[status.upper()]
           
           # Przetworzenie callbacku
           result = await payment_service.process_payment_callback(
               transaction_id=transaction_id,
               status=transaction_status
           )
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.PAYMENT_CALLBACK_SUCCESS,
               message=f"Successfully processed payment callback for transaction {transaction_id} with status {status}"
           )
           
           return PaymentCallbackResponse(
               message="Callback processed",
               order_status=result.order_status
           )
       
       except ValueError as e:
           # Obsługa błędów walidacji lub nieistniejących zasobów
           error_message = str(e)
           error_code = "TRANSACTION_NOT_FOUND"
           status_code = 404
           
           if "Order not found" in error_message:
               error_code = "ORDER_NOT_FOUND"
           
           await log_service.create_log(
               event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
               message=f"Payment callback failed: {error_message}"
           )
           
           raise HTTPException(
               status_code=status_code,
               detail={
                   "error_code": error_code,
                   "message": error_message
               }
           )
       
       except ConflictError as e:
           # Obsługa błędów konfliktu stanu
           await log_service.create_log(
               event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
               message=f"Payment callback conflict: {str(e)}"
           )
           
           raise HTTPException(
               status_code=409,
               detail={
                   "error_code": "ORDER_ALREADY_PROCESSED",
                   "message": str(e)
               }
           )
       
       except Exception as e:
           # Obsługa nieoczekiwanych błędów
           logger.error(f"Error processing payment callback: {str(e)}")
           await log_service.create_log(
               event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
               message=f"Unexpected error processing payment callback: {str(e)}"
           )
           
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "CALLBACK_PROCESSING_FAILED",
                   "message": "Failed to process payment callback"
               }
           )
   ```

3. **Implementacja metody serwisu**:
   ```python
   class PaymentResult:
       def __init__(self, order_status: OrderStatus):
           self.order_status = order_status

   class PaymentService:
       def __init__(self, db: Database):
           self.db = db
       
       async def process_payment_callback(self, transaction_id: UUID, status: TransactionStatus) -> PaymentResult:
           # Sprawdź czy transakcja istnieje
           query = "SELECT * FROM transactions WHERE id = :transaction_id"
           transaction = await self.db.fetch_one(query, {"transaction_id": transaction_id})
           
           if transaction is None:
               raise ValueError(f"Transaction {transaction_id} not found")
           
           # Pobierz zamówienie
           query = "SELECT * FROM orders WHERE id = :order_id"
           order = await self.db.fetch_one(query, {"order_id": transaction["order_id"]})
           
           if order is None:
               raise ValueError(f"Order not found for transaction {transaction_id}")
           
           # Sprawdź, czy zamówienie nie zostało już przetworzone
           if order["status"] != OrderStatus.PENDING_PAYMENT:
               raise ConflictError(f"Order {order['id']} has already been processed")
           
           # Rozpocznij transakcję bazodanową
           async with self.db.transaction():
               # Aktualizuj status transakcji
               query = """
               UPDATE transactions 
               SET status = :status 
               WHERE id = :transaction_id
               """
               await self.db.execute(
                   query, 
                   {"transaction_id": transaction_id, "status": status}
               )
               
               # Określ nowy status zamówienia na podstawie statusu transakcji
               new_order_status = OrderStatus.PROCESSING
               if status == TransactionStatus.FAIL:
                   new_order_status = OrderStatus.FAILED
               elif status == TransactionStatus.CANCELLED:
                   new_order_status = OrderStatus.CANCELLED
               
               # Aktualizuj status zamówienia
               query = """
               UPDATE orders 
               SET status = :status, updated_at = :updated_at
               WHERE id = :order_id
               """
               await self.db.execute(
                   query, 
                   {
                       "order_id": transaction["order_id"], 
                       "status": new_order_status,
                       "updated_at": datetime.now()
                   }
               )
               
               # Jeśli płatność się powiodła, aktualizuj ilość produktów
               if status == TransactionStatus.SUCCESS:
                   # Pobierz wszystkie pozycje zamówienia
                   query = """
                   SELECT oi.offer_id, oi.quantity 
                   FROM order_items oi
                   WHERE oi.order_id = :order_id
                   """
                   order_items = await self.db.fetch_all(
                       query, 
                       {"order_id": transaction["order_id"]}
                   )
                   
                   # Aktualizuj ilość dla każdej oferty
                   for item in order_items:
                       query = """
                       UPDATE offers
                       SET quantity = quantity - :purchased_quantity
                       WHERE id = :offer_id AND quantity >= :purchased_quantity
                       """
                       result = await self.db.execute(
                           query,
                           {
                               "offer_id": item["offer_id"],
                               "purchased_quantity": item["quantity"]
                           }
                       )
                       
                       # Sprawdź, czy oferta ma teraz ilość 0 i ewentualnie zmień status na "sold"
                       query = """
                       UPDATE offers
                       SET status = 'sold'
                       WHERE id = :offer_id AND quantity = 0 AND status = 'active'
                       """
                       await self.db.execute(
                           query,
                           {"offer_id": item["offer_id"]}
                       )
           
           # Zwróć wynik z nowym statusem zamówienia
           return PaymentResult(order_status=new_order_status)
   ```

4. **Dodanie klas wyjątków**:
   ```python
   class ConflictError(Exception):
       """Raised when there is a conflict with the current state of the resource."""
       pass
   ```

5. **Dodanie typów zdarzeń logowania**:
   - Upewnij się, że w enum `LogEventType` istnieją zdarzenia `PAYMENT_CALLBACK_SUCCESS` i `PAYMENT_CALLBACK_FAIL`

6. **Testy jednostkowe**:
   - Utwórz testy dla `PaymentService.process_payment_callback`
   - Przetestuj scenariusze sukcesu i błędów dla każdego możliwego statusu płatności
   - Szczególnie przetestuj aktualizację ilości produktów i automatyczną zmianę statusu na "sold"
   - Przetestuj obsługę zamówień już przetworzonych (idempotentność)

7. **Testy integracyjne**:
   - Przetestuj cały przepływ żądania-odpowiedzi
   - Zweryfikuj poprawność aktualizacji statusów
   - Sprawdź, czy ilości produktów są prawidłowo aktualizowane
   - Sprawdź, czy logowanie działa poprawnie

8. **Dokumentacja API**:
   - Zaktualizuj dokumentację Swagger za pomocą odpowiednich adnotacji FastAPI
   - Dodaj przykładowe parametry i odpowiedzi
   - Wyjaśnij, że endpoint jest przeznaczony dla zewnętrznego systemu płatności 