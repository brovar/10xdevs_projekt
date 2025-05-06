# API Endpoint Implementation Plan: Activate Offer

## 1. Przegląd punktu końcowego
Endpoint `/offers/{offer_id}/activate` z metodą POST umożliwia zmianę statusu oferty z 'inactive' na 'active', co udostępnia ją dla potencjalnych kupujących. Dostęp do tego endpointu ma wyłącznie sprzedawca, który jest właścicielem oferty. Oferta musi być w statusie 'inactive' aby operacja aktywacji była możliwa. Po pomyślnym wykonaniu operacji, endpoint zwraca zaktualizowany obiekt oferty z nowym statusem i dodatkowymi informacjami o sprzedawcy i kategorii.

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/offers/{offer_id}/activate`
- Parametry Path:
  - `offer_id` (UUID, wymagany): Identyfikator oferty, która ma zostać aktywowana
- Format danych: Brak (żądanie nie zawiera treści)

## 3. Wykorzystywane typy
- **OfferDetailDTO** (z types.py) - model odpowiedzi z pełnymi szczegółami oferty
- **OfferStatus** (z types.py) - enum określający możliwe statusy oferty
- **UserRole** (z types.py) - enum określający role użytkowników
- **LogEventType** (z types.py) - enum określający typy zdarzeń w logach
- **CategoryDTO** (z types.py) - model informacji o kategorii
- **SellerInfoDTO** (z types.py) - model informacji o sprzedawcy
- Modele bazy danych:
  - **Offer** - reprezentacja tabeli `offers` w bazie danych
  - **Category** - reprezentacja tabeli `categories` w bazie danych
  - **User** - reprezentacja tabeli `users` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Response Body (sukces):
  ```json
  {
    "id": "uuid-offer-id",
    "seller_id": "uuid-seller-id",
    "category_id": 1,
    "title": "Product Title",
    "description": "Product description.",
    "price": "99.99",
    "image_filename": "image.png",
    "quantity": 10,
    "status": "active", // Zmieniony status
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
- Kody błędów:
  - `400 Bad Request` z kodem błędu `INVALID_STATUS_TRANSITION` - nieprawidłowa zmiana statusu (oferta nie jest w statusie 'inactive')
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `403 Forbidden` z kodami błędów:
    - `INSUFFICIENT_PERMISSIONS` - użytkownik nie jest sprzedawcą
    - `NOT_OFFER_OWNER` - użytkownik nie jest właścicielem oferty
  - `404 Not Found` z kodem błędu `OFFER_NOT_FOUND` - oferta nie istnieje
  - `409 Conflict` z kodem błędu `ALREADY_ACTIVE` - oferta jest już aktywna
  - `500 Internal Server Error` z kodem błędu `ACTIVATION_FAILED` - błąd podczas aktywacji oferty

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. System weryfikuje uwierzytelnienie użytkownika i sprawdza czy ma rolę Seller
3. Pobieranie oferty z bazy danych na podstawie offer_id
4. Sprawdzenie czy oferta istnieje
5. Sprawdzenie czy użytkownik jest właścicielem oferty
6. Sprawdzenie czy oferta jest w statusie 'inactive'
7. Zmiana statusu oferty na 'active'
8. Aktualizacja pola updated_at na aktualną datę i czas
9. Zapisanie zmian w bazie danych
10. Logowanie zdarzenia zmiany statusu oferty
11. Pobranie zaktualizowanej oferty z dodatkowymi danymi (sprzedawca, kategoria)
12. Zwrócenie odpowiedzi z zaktualizowanymi danymi

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie dla wszystkich użytkowników
  - Weryfikacja tokenu sesji/JWT
- **Autoryzacja**:
  - Kontrola dostępu na podstawie roli (tylko sprzedawca może aktywować oferty)
  - Sprawdzanie własności zasobu (sprzedawca może aktywować tylko swoje oferty)
- **Walidacja**:
  - Sprawdzanie stanu oferty przed zmianą statusu
  - Weryfikacja formatu UUID dla offer_id
- **Ochrona przed atakami**:
  - Rate limiting dla zapobiegania nadużyciom
  - Logowanie prób nieautoryzowanego dostępu
  - Transakcje bazodanowe dla zapewnienia integralności danych

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowy status oferty: `400 Bad Request` z kodem `INVALID_STATUS_TRANSITION`
  - Oferta już aktywna: `409 Conflict` z kodem `ALREADY_ACTIVE`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Brak wymaganej roli: `403 Forbidden` z kodem `INSUFFICIENT_PERMISSIONS`
  - Brak własności oferty: `403 Forbidden` z kodem `NOT_OFFER_OWNER`
- **Błędy biznesowe**:
  - Oferta nie istnieje: `404 Not Found` z kodem `OFFER_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `ACTIVATION_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Operacje bazodanowe**:
  - Użycie transakcji dla zapewnienia atomowości operacji zmiany statusu
  - Optymalizacja zapytań (minimalizacja liczby zapytań)
  - Indeksowanie kolumny status w tabeli `offers` dla szybszego wyszukiwania
- **Cachowanie**:
  - Możliwość cachowania często używanych kategorii
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
  - Wykorzystanie zadań w tle (background tasks) dla operacji niewymagających natychmiastowej odpowiedzi, np. logowanie

## 9. Etapy wdrożenia

1. **Dodanie metody aktywacji oferty do serwisu ofert**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from fastapi import HTTPException, status
   from uuid import UUID
   from datetime import datetime
   from logging import Logger
   
   from src.db.models import Offer, User, Category
   from src.types import OfferDetailDTO, OfferStatus, UserRole, LogEventType
   from src.services.logging import log_event
   
   class OfferService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
       
       async def activate_offer(
           self,
           offer_id: UUID,
           user_id: UUID,
           user_role: UserRole
       ) -> OfferDetailDTO:
           """
           Activate an offer by changing its status from 'inactive' to 'active'
           
           Args:
               offer_id: UUID of the offer to activate
               user_id: UUID of the current user
               user_role: Role of the current user
               
           Returns:
               OfferDetailDTO with the updated offer details
               
           Raises:
               HTTPException: Various exceptions based on validation and authorization
           """
           try:
               # Verify user is a seller
               if user_role != UserRole.SELLER:
                   raise HTTPException(
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail={
                           "error_code": "INSUFFICIENT_PERMISSIONS",
                           "message": "Only sellers can activate offers"
                       }
                   )
               
               # Get the offer
               offer = await self.db_session.get(Offer, offer_id)
               
               # Check if offer exists
               if not offer:
                   raise HTTPException(
                       status_code=status.HTTP_404_NOT_FOUND,
                       detail={
                           "error_code": "OFFER_NOT_FOUND",
                           "message": "Offer not found"
                       }
                   )
               
               # Check if user is the owner
               if offer.seller_id != user_id:
                   raise HTTPException(
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail={
                           "error_code": "NOT_OFFER_OWNER",
                           "message": "You can only activate your own offers"
                       }
                   )
               
               # Check if offer is already active
               if offer.status == OfferStatus.ACTIVE:
                   raise HTTPException(
                       status_code=status.HTTP_409_CONFLICT,
                       detail={
                           "error_code": "ALREADY_ACTIVE",
                           "message": "Offer is already active"
                       }
                   )
               
               # Check if offer status allows activation (must be 'inactive')
               if offer.status != OfferStatus.INACTIVE:
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail={
                           "error_code": "INVALID_STATUS_TRANSITION",
                           "message": f"Cannot activate offer with status '{offer.status}'"
                       }
                   )
               
               # Update offer status
               offer.status = OfferStatus.ACTIVE
               offer.updated_at = datetime.now()
               
               # Save to database
               await self.db_session.commit()
               await self.db_session.refresh(offer)
               
               # Log the status change event
               await log_event(
                   self.db_session,
                   LogEventType.OFFER_STATUS_CHANGE,
                   user_id,
                   f"Offer {offer_id} activated"
               )
               
               # Fetch seller and category for full response
               seller = await self.db_session.get(User, offer.seller_id)
               category = await self.db_session.get(Category, offer.category_id)
               
               # Return detailed DTO
               return self._map_to_offer_detail_dto(offer, seller, category)
               
           except HTTPException:
               # Re-raise HTTP exceptions
               raise
           except Exception as e:
               # Log the error
               self.logger.error(f"Error activating offer: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "ACTIVATION_FAILED",
                       "message": "Failed to activate offer"
                   }
               )
       
       def _map_to_offer_detail_dto(self, offer, seller, category):
           """Map database models to OfferDetailDTO"""
           from src.types import SellerInfoDTO, CategoryDTO
           
           seller_info = SellerInfoDTO(
               id=seller.id,
               first_name=seller.first_name,
               last_name=seller.last_name
           )
           
           category_info = CategoryDTO(
               id=category.id,
               name=category.name
           )
           
           return OfferDetailDTO(
               id=offer.id,
               seller_id=offer.seller_id,
               category_id=offer.category_id,
               title=offer.title,
               description=offer.description,
               price=offer.price,
               image_filename=offer.image_filename,
               quantity=offer.quantity,
               status=offer.status,
               created_at=offer.created_at,
               updated_at=offer.updated_at,
               seller=seller_info,
               category=category_info
           )
   ```

2. **Utworzenie kontrolera (routera) dla endpointu aktywacji oferty**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Path
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from logging import Logger
   
   from src.db.session import get_async_session
   from src.services.offer_service import OfferService
   from src.services.auth import get_current_user
   from src.types import OfferDetailDTO
   
   router = APIRouter(prefix="/offers", tags=["offers"])
   
   @router.post("/{offer_id}/activate", response_model=OfferDetailDTO)
   async def activate_offer(
       offer_id: UUID = Path(..., description="UUID of the offer to activate"),
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger)
   ):
       """
       Activate an offer by changing its status from 'inactive' to 'active'.
       
       - Requires Seller role and ownership of the offer
       - Offer must be in 'inactive' status
       - Returns the updated offer with seller and category information
       """
       try:
           # Call service method
           offer_service = OfferService(db, logger)
           result = await offer_service.activate_offer(
               offer_id=offer_id,
               user_id=current_user.id,
               user_role=current_user.role
           )
           
           return result
           
       except HTTPException:
           # Re-raise HTTP exceptions (already handled in service)
           raise
       except Exception as e:
           # Log unexpected errors
           logger.error(f"Unexpected error in activate_offer endpoint: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "ACTIVATION_FAILED",
                   "message": "An unexpected error occurred"
               }
           )
   ```

3. **Utworzenie testów jednostkowych dla metody aktywacji oferty**:
   ```python
   import pytest
   from unittest.mock import MagicMock, AsyncMock, patch
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from fastapi import HTTPException
   
   from src.services.offer_service import OfferService
   from src.types import UserRole, OfferStatus
   
   @pytest.fixture
   def db_session():
       mock_session = AsyncMock(spec=AsyncSession)
       mock_session.get = AsyncMock()
       mock_session.commit = AsyncMock()
       mock_session.refresh = AsyncMock()
       return mock_session
   
   @pytest.fixture
   def logger():
       return MagicMock()
   
   @pytest.mark.asyncio
   async def test_activate_offer_success(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.INACTIVE
       
       # Mock seller and category
       mock_seller = MagicMock()
       mock_seller.id = user_id
       mock_category = MagicMock()
       
       # Setup mock returns
       db_session.get.side_effect = [mock_offer, mock_seller, mock_category]
       
       # Mock DTO mapping
       service._map_to_offer_detail_dto = MagicMock()
       
       # Execute test
       await service.activate_offer(
           offer_id=offer_id,
           user_id=user_id,
           user_role=UserRole.SELLER
       )
       
       # Verify
       assert mock_offer.status == OfferStatus.ACTIVE
       assert db_session.commit.called
       assert db_session.refresh.called
       assert service._map_to_offer_detail_dto.called
   
   @pytest.mark.asyncio
   async def test_activate_offer_not_found(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer not found
       db_session.get.return_value = None
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.activate_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 404
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_FOUND"
   
   @pytest.mark.asyncio
   async def test_activate_offer_not_owner(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       other_user_id = UUID("99999999-9999-9999-9999-999999999999")
       
       # Mock offer with different owner
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = other_user_id
       mock_offer.status = OfferStatus.INACTIVE
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.activate_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "NOT_OFFER_OWNER"
   
   @pytest.mark.asyncio
   async def test_activate_offer_already_active(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer already active
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.ACTIVE
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.activate_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 409
       assert exc_info.value.detail["error_code"] == "ALREADY_ACTIVE"
   
   @pytest.mark.asyncio
   async def test_activate_offer_invalid_status(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer with invalid status (sold)
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.SOLD
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.activate_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 400
       assert exc_info.value.detail["error_code"] == "INVALID_STATUS_TRANSITION"
   
   @pytest.mark.asyncio
   async def test_activate_offer_not_seller(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.activate_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.BUYER
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "INSUFFICIENT_PERMISSIONS"
   ```

4. **Utworzenie testów integracyjnych dla endpointu aktywacji oferty**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch, MagicMock
   
   from main import app
   from src.types import UserRole, OfferStatus
   
   client = TestClient(app)
   
   def test_activate_offer_unauthorized():
       # Test without authentication
       response = client.post("/offers/12345678-1234-5678-1234-567812345678/activate")
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.activate_offer")
   def test_activate_offer_success(mock_activate_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service response
       mock_activate_offer.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "seller_id": "12345678-1234-5678-1234-567812345678",
           "category_id": 1,
           "title": "Test Product",
           "description": "Test Description",
           "price": "99.99",
           "image_filename": "test.png",
           "quantity": 10,
           "status": "active",
           "created_at": "2023-01-01T00:00:00Z",
           "updated_at": "2023-01-02T00:00:00Z",
           "seller": {
               "id": "12345678-1234-5678-1234-567812345678",
               "first_name": "Test",
               "last_name": "Seller"
           },
           "category": {
               "id": 1,
               "name": "Test Category"
           }
       }
       
       # Test request
       response = client.post("/offers/12345678-1234-5678-1234-567812345678/activate")
       
       # Verify
       assert response.status_code == 200
       assert response.json()["status"] == "active"
       assert mock_activate_offer.called
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.activate_offer")
   def test_activate_offer_not_found(mock_activate_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service raising not found error
       from fastapi import HTTPException, status
       mock_activate_offer.side_effect = HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail={"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}
       )
       
       # Test request
       response = client.post("/offers/12345678-1234-5678-1234-567812345678/activate")
       
       # Verify
       assert response.status_code == 404
       assert response.json()["error_code"] == "OFFER_NOT_FOUND"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.activate_offer")
   def test_activate_offer_already_active(mock_activate_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service raising conflict error
       from fastapi import HTTPException, status
       mock_activate_offer.side_effect = HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail={"error_code": "ALREADY_ACTIVE", "message": "Offer is already active"}
       )
       
       # Test request
       response = client.post("/offers/12345678-1234-5678-1234-567812345678/activate")
       
       # Verify
       assert response.status_code == 409
       assert response.json()["error_code"] == "ALREADY_ACTIVE"
   ```

## 10. Plan testów

1. **Testy jednostkowe**:
   - Testowanie pomyślnej aktywacji oferty
   - Testowanie scenariuszy uprawnień (różne role, właściciel vs inny użytkownik)
   - Testowanie scenariuszy dla różnych stanów oferty (już aktywna, sprzedana, moderowana itp.)
   - Testowanie scenariusza gdy oferta nie istnieje

2. **Testy integracyjne**:
   - Testowanie pełnego przepływu aktywacji oferty
   - Testowanie autoryzacji i uwierzytelniania
   - Testowanie obsługi błędów

3. **Testy wydajnościowe**:
   - Testowanie wydajności przy dużej liczbie równoczesnych żądań aktywacji
   - Testowanie wydajności logowania zdarzeń 