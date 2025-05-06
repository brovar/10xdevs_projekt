# API Endpoint Implementation Plan: Unmoderate Offer (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do cofnięcia moderacji oferty przez administratora poprzez zmianę jej statusu z "moderated" na "inactive". Jest to część funkcjonalności administracyjnej systemu, pozwalającej na przywrócenie dostępu do ofert, które wcześniej zostały zmoderowane (ukryte) jako nieodpowiednie. Wykonanie tej operacji wymaga uprawnień administratora. Po odmoderowaniu, oferta wraca do statusu "inactive" (aby sprzedawca mógł ją aktywować, gdy będzie gotowy) i ponownie jest widoczna dla wszystkich użytkowników.

## 2. Szczegóły żądania
- **Metoda HTTP**: POST
- **Struktura URL**: `/admin/offers/{offer_id}/unmoderate`
- **Parametry**:
  - **Wymagane**:
    - `offer_id` (UUID): identyfikator oferty, która ma zostać odmoderowana
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OfferDetailDTO`: Model reprezentujący szczegółowe dane oferty (zwracany po aktualizacji)
  - `OfferStatus` (enum): Enum definiujący statusy ofert, używany do zmiany statusu z "moderated" na "inactive"
  - `UserRole` (enum): Enum definiujący role użytkowników, używany do weryfikacji roli Admin
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**: Obiekt `OfferDetailDTO` ze zaktualizowanym statusem oferty
  ```json
  {
    "id": "uuid-offer-id",
    "seller_id": "uuid-seller-id",
    "category_id": 1,
    "title": "Sample Product",
    "description": "Detailed description here.",
    "price": "99.99",
    "image_filename": "image.png",
    "quantity": 10,
    "status": "inactive", // Zmieniono z "moderated" na "inactive"
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "seller": {
       "id": "uuid-seller-id",
       "first_name": "SellerFirstName",
       "last_name": "SellerLastName"
    },
    "category": {
        "id": 1,
        "name": "Electronics"
    }
  }
  ```

- **Kody błędów**:
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 404 Not Found (`OFFER_NOT_FOUND`): Oferta o podanym ID nie istnieje
  - 409 Conflict (`NOT_MODERATED`): Oferta nie jest w stanie "moderated"
  - 500 Internal Server Error (`UNMODERATION_FAILED`): Błąd serwera podczas odmoderowania oferty

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametru `offer_id` jako prawidłowego UUID
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu ofert do odmoderowania oferty
5. Serwis wykonuje następujące operacje w ramach transakcji bazodanowej:
   - Sprawdza, czy oferta o podanym ID istnieje
   - Sprawdza, czy oferta jest obecnie w stanie "moderated"
   - Aktualizuje status oferty na "inactive"
   - Aktualizuje pole `updated_at` oferty
6. Zapisuje zdarzenie odmoderowania oferty w tabeli logów
7. Pobiera pełne dane oferty wraz z danymi sprzedawcy i kategorii
8. Zwraca zaktualizowany obiekt oferty z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja `offer_id` jako prawidłowego UUID
  - Sprawdzenie, czy oferta istnieje przed odmoderowaniem
  - Sprawdzenie, czy oferta jest obecnie w stanie "moderated"
- **Transakcyjność**:
  - Użycie transakcji bazodanowej do zapewnienia spójności danych
  - W przypadku błędu wszystkie zmiany są wycofywane
- **Audytowanie**:
  - Logowanie operacji odmoderowania oferty w tabeli logów
  - Rejestrowanie ID administratora wykonującego operację, ID oferty i czasu wykonania

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 422 Unprocessable Entity: Nieprawidłowy format `offer_id` (automatycznie obsługiwane przez FastAPI)
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy zasobów**:
  - 404 Not Found z kodem błędu `OFFER_NOT_FOUND` i komunikatem "Offer not found"
- **Błędy stanu**:
  - 409 Conflict z kodem błędu `NOT_MODERATED` i komunikatem "Offer is not moderated"
- **Błędy serwera**:
  - 500 Internal Server Error z kodem błędu `UNMODERATION_FAILED` i komunikatem "Failed to unmoderate offer"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Transakcje bazodanowe**:
  - Wykonanie operacji odmoderowania w pojedynczej, lekkiej transakcji
  - Minimalna liczba zapytań do bazy danych
- **Indeksy bazy danych**:
  - Upewnienie się, że kolumna `id` w tabeli `offers` jest indeksowana (PK)
  - Indeks dla kolumny `status` w tabeli `offers` dla szybszego filtrowania
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych

## 9. Etapy wdrożenia
1. **Rozszerzenie OfferService o metodę do odmoderowania oferty**:
   ```python
   class OfferService:
       def __init__(self, db: Database):
           self.db = db
       
       async def unmoderate_offer(self, offer_id: UUID) -> OfferDetailDTO:
           """
           Odmoderuje ofertę poprzez zmianę jej statusu z 'moderated' na 'inactive'.
           
           Args:
               offer_id: UUID oferty do odmoderowania
               
           Returns:
               OfferDetailDTO zaktualizowanej oferty
               
           Raises:
               ValueError: Jeśli oferta nie istnieje lub nie jest zmoderowana
               Exception: Jeśli wystąpi błąd podczas odmoderowania
           """
           # Rozpocznij transakcję
           async with self.db.transaction():
               # Sprawdź, czy oferta istnieje i pobierz jej status
               query = """
               SELECT id, status
               FROM offers
               WHERE id = :offer_id
               """
               offer = await self.db.fetch_one(query, {"offer_id": offer_id})
               
               if not offer:
                   raise ValueError(f"Offer with ID {offer_id} not found")
               
               # Sprawdź, czy oferta jest zmoderowana
               if offer["status"] != OfferStatus.MODERATED:
                   raise ValueError(f"Offer with ID {offer_id} is not moderated")
               
               # Aktualizuj status oferty
               current_time = datetime.now()
               update_query = """
               UPDATE offers
               SET status = :status, updated_at = :updated_at
               WHERE id = :offer_id
               """
               await self.db.execute(
                   update_query,
                   {
                       "offer_id": offer_id,
                       "status": OfferStatus.INACTIVE,
                       "updated_at": current_time
                   }
               )
               
               # Pobierz pełne dane zaktualizowanej oferty
               offer_query = """
               SELECT o.id, o.seller_id, o.category_id, o.title, o.description,
                      o.price, o.image_filename, o.quantity, o.status,
                      o.created_at, o.updated_at,
                      u.first_name as seller_first_name, u.last_name as seller_last_name,
                      c.name as category_name
               FROM offers o
               JOIN users u ON o.seller_id = u.id
               JOIN categories c ON o.category_id = c.id
               WHERE o.id = :offer_id
               """
               offer_data = await self.db.fetch_one(offer_query, {"offer_id": offer_id})
               
               if not offer_data:
                   raise Exception(f"Failed to retrieve updated offer data for ID {offer_id}")
               
               # Przekształć dane do formatu DTO
               seller = {
                   "id": offer_data["seller_id"],
                   "first_name": offer_data["seller_first_name"],
                   "last_name": offer_data["seller_last_name"]
               }
               
               category = {
                   "id": offer_data["category_id"],
                   "name": offer_data["category_name"]
               }
               
               # Utwórz obiekt DTO
               offer_dto = OfferDetailDTO(
                   id=offer_data["id"],
                   seller_id=offer_data["seller_id"],
                   category_id=offer_data["category_id"],
                   title=offer_data["title"],
                   description=offer_data["description"],
                   price=offer_data["price"],
                   image_filename=offer_data["image_filename"],
                   quantity=offer_data["quantity"],
                   status=offer_data["status"],
                   created_at=offer_data["created_at"],
                   updated_at=offer_data["updated_at"],
                   seller=seller,
                   category=category
               )
               
               return offer_dto
   ```

2. **Implementacja handlera endpointu**:
   ```python
   @router.post(
       "/admin/offers/{offer_id}/unmoderate",
       response_model=OfferDetailDTO,
       summary="Unmoderate offer",
       description="Sets offer status from 'moderated' to 'inactive'. Requires Admin role.",
       responses={
           200: {"description": "Offer unmoderated successfully"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           404: {"description": "Offer not found"},
           409: {"description": "Offer is not moderated"},
           500: {"description": "Server error while unmoderating offer"}
       }
   )
   async def unmoderate_offer(
       offer_id: UUID = Path(..., description="The ID of the offer to unmoderate"),
       current_user: UserDTO = Depends(require_admin),
       offer_service: OfferService = Depends(get_offer_service),
       log_service: LogService = Depends(get_log_service)
   ) -> OfferDetailDTO:
       """
       Odmoderuje ofertę poprzez zmianę jej statusu z 'moderated' na 'inactive'.
       Odmoderowana oferta wraca do statusu nieaktywnego i będzie widoczna dla użytkowników
       po aktywacji przez sprzedawcę.
       Dostęp tylko dla administratorów.
       """
       try:
           # Logowanie próby odmoderowania
           await log_service.create_log(
               event_type=LogEventType.OFFER_UNMODERATION_ATTEMPT,
               user_id=current_user.id,
               message=f"Admin {current_user.email} attempted to unmoderate offer with ID {offer_id}"
           )
           
           # Odmoderowanie oferty
           unmoderated_offer = await offer_service.unmoderate_offer(offer_id)
           
           # Logowanie sukcesu
           await log_service.create_log(
               event_type=LogEventType.OFFER_UNMODERATED,
               user_id=current_user.id,
               message=f"Admin {current_user.email} successfully unmoderated offer with ID {offer_id}"
           )
           
           return unmoderated_offer
           
       except ValueError as e:
           error_message = str(e)
           
           # Określ kod błędu na podstawie treści komunikatu
           if "not found" in error_message.lower():
               error_code = "OFFER_NOT_FOUND"
               status_code = 404
           elif "not moderated" in error_message.lower():
               error_code = "NOT_MODERATED"
               status_code = 409
           else:
               error_code = "INVALID_REQUEST"
               status_code = 400
           
           # Logowanie błędu
           await log_service.create_log(
               event_type=LogEventType.OFFER_UNMODERATION_FAIL,
               user_id=current_user.id,
               message=f"Failed to unmoderate offer {offer_id}: {error_message}"
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
               event_type=LogEventType.OFFER_UNMODERATION_FAIL,
               user_id=current_user.id,
               message=f"Unexpected error while unmoderating offer {offer_id}: {str(e)}"
           )
           
           # Zwróć standardowy błąd serwera
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "UNMODERATION_FAILED",
                   "message": "Failed to unmoderate offer"
               }
           )
   ```

3. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       OFFER_UNMODERATION_ATTEMPT = "OFFER_UNMODERATION_ATTEMPT"
       OFFER_UNMODERATED = "OFFER_UNMODERATED"
       OFFER_UNMODERATION_FAIL = "OFFER_UNMODERATION_FAIL"
   ```

4. **Upewnienie się, że endpoint jest dodany do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera (powinien być już dodany w ramach offer_router)
   admin_router.include_router(offer_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

5. **Implementacja testów jednostkowych**:
   - Test dla OfferService.unmoderate_offer:
     - Test odmoderowania oferty z prawidłowym ID i statusem "moderated"
     - Test odmoderowania nieistniejącej oferty (oczekiwany wyjątek)
     - Test odmoderowania oferty, która nie jest zmoderowana (oczekiwany wyjątek)
   - Test dla handlera unmoderate_offer:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi z zaktualizowaną ofertą
     - Test obsługi błędów

6. **Implementacja testów integracyjnych**:
   - Test całego flow moderacji i odmoderowania oferty
   - Test scenariuszy błędów (nieistniejąca oferta, oferta nie jest zmoderowana)
   - Test widoczności oferty dla różnych ról użytkowników przed moderacją, po moderacji i po odmoderowaniu

7. **Aktualizacja dokumentacji API**:
   - Dodanie dokumentacji do Swagger dla endpointu
   - Zaktualizowanie dokumentacji projektowej (jeśli istnieje)

8. **Wdrożenie i weryfikacja**:
   - Wdrożenie endpointu na środowisku deweloperskim
   - Weryfikacja poprawnego działania w różnych scenariuszach
   - Sprawdzenie logów i rekordów audytu 