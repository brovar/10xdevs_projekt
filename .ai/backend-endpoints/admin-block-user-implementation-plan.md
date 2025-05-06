# API Endpoint Implementation Plan: Block User (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do blokowania użytkownika przez administratora poprzez zmianę jego statusu na "Inactive". Gdy blokowany jest użytkownik z rolą Seller, dodatkowo anulowane są jego aktywne zamówienia i wszystkie jego oferty zostają oznaczone jako "inactive". Operacja wymaga uprawnień administratora i jest nieodwracalna (choć użytkownika można później odblokować osobnym endpointem).

## 2. Szczegóły żądania
- **Metoda HTTP**: POST
- **Struktura URL**: `/admin/users/{user_id}/block`
- **Parametry**:
  - **Wymagane**:
    - `user_id` (UUID): identyfikator użytkownika, który ma zostać zablokowany
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `UserDTO`: Model reprezentujący dane użytkownika (zwracany po aktualizacji)
  - `UserRole` (enum): Enum definiujący role użytkowników, używany do sprawdzenia czy blokowany użytkownik jest sprzedawcą
  - `UserStatus` (enum): Enum definiujący statusy użytkowników, używany do zmiany statusu na "Inactive"
  - `OrderStatus` (enum): Enum definiujący statusy zamówień, używany do anulowania aktywnych zamówień
  - `OfferStatus` (enum): Enum definiujący statusy ofert, używany do dezaktywacji ofert sprzedawcy
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
  ```json
  {
    "id": "uuid-user-id",
    "email": "user@example.com",
    "role": "Buyer", // lub "Seller", "Admin"
    "status": "Inactive", // Zmieniono na Inactive
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
  - 409 Conflict (`ALREADY_INACTIVE`): Użytkownik jest już nieaktywny
  - 500 Internal Server Error (`BLOCK_FAILED`): Błąd serwera podczas blokowania użytkownika

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametru `user_id` jako prawidłowego UUID
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu użytkowników do blokowania użytkownika
5. Serwis wykonuje następujące operacje w ramach jednej transakcji bazodanowej:
   - Sprawdza, czy użytkownik o podanym ID istnieje
   - Sprawdza, czy użytkownik nie jest już zablokowany (status "Inactive")
   - Aktualizuje status użytkownika na "Inactive"
   - Jeśli użytkownik ma rolę "Seller":
     - Pobiera listę aktywnych zamówień zawierających produkty sprzedawcy
     - Ustawia status tych zamówień na "cancelled"
     - Pobiera listę aktywnych ofert sprzedawcy
     - Ustawia status tych ofert na "inactive"
   - Aktualizuje pole `updated_at` użytkownika
6. Zapisuje zdarzenie blokowania użytkownika w tabeli logów
7. Zwraca zaktualizowany obiekt użytkownika z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja `user_id` jako prawidłowego UUID
  - Sprawdzenie, czy użytkownik istnieje przed blokowaniem
  - Sprawdzenie, czy użytkownik nie jest już zablokowany
- **Transakcyjność**:
  - Użycie transakcji bazodanowej do zapewnienia spójności danych
  - W przypadku błędu podczas którejkolwiek operacji, wszystkie zmiany są wycofywane
- **Audytowanie**:
  - Logowanie operacji blokowania użytkownika w tabeli logów
  - Rejestrowanie ID administratora wykonującego operację

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 422 Unprocessable Entity: Nieprawidłowy format `user_id` (automatycznie obsługiwane przez FastAPI)
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `USER_NOT_FOUND` i komunikatem "User not found"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `ALREADY_INACTIVE` i komunikatem "User is already inactive"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `BLOCK_FAILED` i komunikatem "Failed to block user"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Transakcje bazodanowe**:
  - Optymalizacja transakcji przez wykonanie wszystkich operacji w jednej transakcji
  - Zminimalizowanie ilości zapytań do bazy danych
- **Indeksy bazy danych**:
  - Upewnienie się, że kolumna `id` w tabeli `users` jest indeksowana (PK)
  - Indeksy dla kolumn `status` i `role` w tabeli `users`
  - Indeksy dla kluczy obcych w tabelach `orders` i `offers` odnoszących się do użytkowników
- **Selektywne aktualizacje**:
  - Aktualizacja tylko ofert o statusie "active" lub "inactive"
  - Anulowanie tylko zamówień w statusie "pending_payment", "processing" lub "shipped"
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych

## 9. Etapy wdrożenia
1. **Rozszerzenie UserService o metodę do blokowania użytkownika**:
   ```python
   class UserService:
       def __init__(self, db: Database):
           self.db = db
       
       async def block_user(self, user_id: UUID) -> UserDTO:
           """
           Blokuje użytkownika poprzez zmianę jego statusu na Inactive.
           Jeśli użytkownik jest sprzedawcą, anuluje aktywne zamówienia i dezaktywuje oferty.
           
           Args:
               user_id: UUID użytkownika do zablokowania
               
           Returns:
               UserDTO zaktualizowanego użytkownika
               
           Raises:
               ValueError: Jeśli użytkownik nie istnieje lub jest już nieaktywny
               Exception: Jeśli wystąpi błąd podczas blokowania
           """
           # Rozpocznij transakcję
           async with self.db.transaction():
               # Sprawdź, czy użytkownik istnieje i pobierz jego dane
               query = """
               SELECT id, email, role, status, first_name, last_name, created_at, updated_at
               FROM users
               WHERE id = :user_id
               """
               user = await self.db.fetch_one(query, {"user_id": user_id})
               
               if not user:
                   raise ValueError(f"User with ID {user_id} not found")
               
               # Sprawdź, czy użytkownik nie jest już zablokowany
               if user["status"] == UserStatus.INACTIVE:
                   raise ValueError(f"User with ID {user_id} is already inactive")
               
               # Aktualizuj status użytkownika
               current_time = datetime.now()
               update_query = """
               UPDATE users
               SET status = :status, updated_at = :updated_at
               WHERE id = :user_id
               RETURNING id, email, role, status, first_name, last_name, created_at, updated_at
               """
               updated_user = await self.db.fetch_one(
                   update_query,
                   {
                       "user_id": user_id,
                       "status": UserStatus.INACTIVE,
                       "updated_at": current_time
                   }
               )
               
               # Jeśli użytkownik jest sprzedawcą, anuluj zamówienia i dezaktywuj oferty
               if user["role"] == UserRole.SELLER:
                   # Pobierz aktywne oferty sprzedawcy
                   offers_query = """
                   SELECT id FROM offers
                   WHERE seller_id = :seller_id AND status IN ('active', 'inactive')
                   """
                   offers = await self.db.fetch_all(offers_query, {"seller_id": user_id})
                   
                   # Dezaktywuj oferty
                   if offers:
                       offer_ids = [offer["id"] for offer in offers]
                       deactivate_offers_query = """
                       UPDATE offers
                       SET status = :status, updated_at = :updated_at
                       WHERE id = ANY(:offer_ids)
                       """
                       await self.db.execute(
                           deactivate_offers_query,
                           {
                               "offer_ids": offer_ids,
                               "status": OfferStatus.INACTIVE,
                               "updated_at": current_time
                           }
                       )
                   
                   # Pobierz aktywne zamówienia zawierające produkty sprzedawcy
                   # Zwróć uwagę, że zapytanie używa połączenia orders-order_items-offers
                   orders_query = """
                   SELECT DISTINCT o.id
                   FROM orders o
                   JOIN order_items oi ON o.id = oi.order_id
                   JOIN offers of ON oi.offer_id = of.id
                   WHERE of.seller_id = :seller_id
                   AND o.status IN ('pending_payment', 'processing', 'shipped')
                   """
                   orders = await self.db.fetch_all(orders_query, {"seller_id": user_id})
                   
                   # Anuluj zamówienia
                   if orders:
                       order_ids = [order["id"] for order in orders]
                       cancel_orders_query = """
                       UPDATE orders
                       SET status = :status, updated_at = :updated_at
                       WHERE id = ANY(:order_ids)
                       """
                       await self.db.execute(
                           cancel_orders_query,
                           {
                               "order_ids": order_ids,
                               "status": OrderStatus.CANCELLED,
                               "updated_at": current_time
                           }
                       )
               
               return UserDTO(**updated_user)
   ```

2. **Implementacja handlera endpointu**:
   ```python
   @router.post(
       "/admin/users/{user_id}/block",
       response_model=UserDTO,
       summary="Block user",
       description="Sets user status to 'Inactive'. If Seller, cancels active orders and sets offers to 'inactive'.",
       responses={
           200: {"description": "User blocked successfully"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           404: {"description": "User not found"},
           409: {"description": "User is already inactive"},
           500: {"description": "Server error while blocking user"}
       }
   )
   async def block_user(
       user_id: UUID = Path(..., description="The ID of the user to block"),
       current_user: UserDTO = Depends(require_admin),
       user_service: UserService = Depends(get_user_service),
       log_service: LogService = Depends(get_log_service)
   ) -> UserDTO:
       """
       Blokuje użytkownika poprzez zmianę jego statusu na 'Inactive'.
       Jeśli blokowany jest sprzedawca, anuluje aktywne zamówienia i dezaktywuje oferty.
       Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie próby blokowania
           await log_service.create_log(
               event_type=LogEventType.USER_BLOCK_ATTEMPT,
               user_id=current_user.id,
               message=f"Admin {current_user.email} attempted to block user with ID {user_id}"
           )
           
           # Blokowanie użytkownika
           blocked_user = await user_service.block_user(user_id)
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.USER_DEACTIVATED,
               user_id=current_user.id,
               message=f"Admin {current_user.email} successfully blocked user {blocked_user.email} (ID: {user_id})"
           )
           
           return blocked_user
           
       except ValueError as e:
           error_message = str(e)
           
           # Określ kod błędu na podstawie treści komunikatu
           if "not found" in error_message.lower():
               error_code = "USER_NOT_FOUND"
               status_code = 404
           elif "already inactive" in error_message.lower():
               error_code = "ALREADY_INACTIVE"
               status_code = 409
           else:
               error_code = "INVALID_REQUEST"
               status_code = 400
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.USER_BLOCK_FAIL,
               user_id=current_user.id,
               message=f"Failed to block user {user_id}: {error_message}"
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
               event_type=LogEventType.USER_BLOCK_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while blocking user {user_id}: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "BLOCK_FAILED",
                   "message": "Failed to block user"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       USER_BLOCK_ATTEMPT = "USER_BLOCK_ATTEMPT"
       USER_BLOCK_FAIL = "USER_BLOCK_FAIL"
       # USER_DEACTIVATED już istnieje w specyfikacji
   ```

4. **Dodanie endpointu do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(user_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla UserService.block_user:
     - Test blokowania zwykłego użytkownika (Buyer)
     - Test blokowania sprzedawcy (Seller) - sprawdzenie anulowania zamówień i dezaktywacji ofert
     - Test blokowania już zablokowanego użytkownika (oczekiwany wyjątek)
     - Test blokowania nieistniejącego użytkownika (oczekiwany wyjątek)
   - Test dla handlera block_user:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi typami użytkowników (Buyer, Seller)
   - Test scenariuszy błędów (nieistniejący użytkownik, już zablokowany)
   - Test konsekwencji blokowania sprzedawcy (sprawdzenie statusu zamówień i ofert)

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Weryfikacja wydajności**:
   - Przeprowadzenie testów wydajnościowych dla scenariusza blokowania sprzedawcy z dużą liczbą ofert i zamówień
   - Optymalizacja zapytań SQL jeśli potrzebne 