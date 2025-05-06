# API Endpoint Implementation Plan: Delete Offer

## 1. Przegląd punktu końcowego
Endpoint `/offers/{offer_id}` z metodą DELETE umożliwia usunięcie oferty z systemu. Dostęp do tego endpointu ma wyłącznie sprzedawca, który jest właścicielem oferty. Logika usuwania zależy od stanu oferty i jej powiązań - jeśli do oferty są przypisane zamówienia, zostanie wykonane tzw. "miękkie usunięcie" (soft delete) poprzez zmianę statusu na 'archived', w przeciwnym razie status zostanie zmieniony na 'deleted'. Endpoint nie wymaga ani nie zwraca żadnych danych, a pomyślne wykonanie operacji jest sygnalizowane kodem statusu 204 No Content.

## 2. Szczegóły żądania
- Metoda HTTP: `DELETE`
- Struktura URL: `/offers/{offer_id}`
- Parametry Path:
  - `offer_id` (UUID, wymagany): Identyfikator oferty, która ma zostać usunięta
- Format danych: Brak (żądanie nie zawiera treści)

## 3. Wykorzystywane typy
- **OfferStatus** (z types.py) - enum określający możliwe statusy oferty
- **UserRole** (z types.py) - enum określający role użytkowników
- **LogEventType** (z types.py) - enum określający typy zdarzeń w logach
- Modele bazy danych:
  - **Offer** - reprezentacja tabeli `offers` w bazie danych
  - **OrderItem** - reprezentacja tabeli `order_items` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `204 No Content`
- Response Body (sukces): Brak (pusta odpowiedź)
- Kody błędów:
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `403 Forbidden` z kodami błędów:
    - `INSUFFICIENT_PERMISSIONS` - użytkownik nie jest sprzedawcą
    - `NOT_OFFER_OWNER` - użytkownik nie jest właścicielem oferty
  - `404 Not Found` z kodem błędu `OFFER_NOT_FOUND` - oferta nie istnieje
  - `500 Internal Server Error` z kodem błędu `DELETE_FAILED` - błąd podczas usuwania oferty

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. System weryfikuje uwierzytelnienie użytkownika i sprawdza czy ma rolę Seller
3. Pobieranie oferty z bazy danych na podstawie offer_id
4. Sprawdzenie czy oferta istnieje
5. Sprawdzenie czy użytkownik jest właścicielem oferty
6. Sprawdzenie czy oferta ma powiązane zamówienia:
   - Jeśli tak: zmiana statusu oferty na 'archived'
   - Jeśli nie: zmiana statusu oferty na 'deleted'
7. Zapisanie zmian w bazie danych
8. Logowanie zdarzenia usunięcia oferty
9. Zwrócenie odpowiedzi z kodem statusu 204 No Content

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie dla wszystkich użytkowników
  - Weryfikacja tokenu sesji/JWT
- **Autoryzacja**:
  - Kontrola dostępu na podstawie roli (tylko sprzedawca może usuwać oferty)
  - Sprawdzanie własności zasobu (sprzedawca może usuwać tylko swoje oferty)
- **Bezpieczeństwo danych**:
  - Użycie "miękkiego usuwania" zamiast trwałego usunięcia danych z bazy
  - Zachowanie historii działań użytkownika
- **Ochrona przed atakami**:
  - Weryfikacja formatu UUID dla offer_id
  - Rate limiting dla zapobiegania nadużyciom
  - Logowanie prób nieautoryzowanego dostępu
  - Transakcje bazodanowe dla zapewnienia integralności danych

## 7. Obsługa błędów
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Brak wymaganej roli: `403 Forbidden` z kodem `INSUFFICIENT_PERMISSIONS`
  - Brak własności oferty: `403 Forbidden` z kodem `NOT_OFFER_OWNER`
- **Błędy biznesowe**:
  - Oferta nie istnieje: `404 Not Found` z kodem `OFFER_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `DELETE_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Operacje bazodanowe**:
  - Użycie transakcji dla zapewnienia atomowości operacji
  - Optymalizacja zapytań sprawdzających istnienie powiązanych zamówień
  - Indeksowanie odpowiednich kolumn w tabeli `offers` i `order_items`
- **Miękkie usuwanie**:
  - Zmiana statusu zamiast fizycznego usuwania rekordów z bazy danych
  - Unikanie kaskadowego usuwania powiązanych danych, co byłoby kosztowne dla ofert z dużą liczbą zamówień
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)
  - Wykorzystanie zadań w tle (background tasks) dla operacji niewymagających natychmiastowej odpowiedzi, np. logowanie

## 9. Etapy wdrożenia

1. **Rozszerzenie serwisu ofert o metodę usuwania**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from fastapi import HTTPException, status
   from typing import Optional
   from uuid import UUID
   from datetime import datetime
   from logging import Logger
   
   from src.db.models import Offer, OrderItem
   from src.types import OfferStatus, UserRole, LogEventType
   from src.services.logging import log_event
   
   class OfferService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
       
       async def delete_offer(
           self,
           offer_id: UUID,
           user_id: UUID,
           user_role: UserRole
       ) -> None:
           """
           Delete an offer (soft delete via status change)
           
           Args:
               offer_id: UUID of the offer to delete
               user_id: UUID of the current user
               user_role: Role of the current user
               
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
                           "message": "Only sellers can delete offers"
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
                           "message": "You can only delete your own offers"
                       }
                   )
               
               # Check if offer has associated orders
               # Using a select query with exists to be more efficient
               stmt = select(OrderItem).where(OrderItem.offer_id == offer_id).limit(1)
               result = await self.db_session.execute(stmt)
               has_orders = result.scalars().first() is not None
               
               # Set appropriate status based on order existence
               if has_orders:
                   offer.status = OfferStatus.ARCHIVED
                   status_description = "archived"
               else:
                   offer.status = OfferStatus.DELETED
                   status_description = "deleted"
               
               # Update offer
               offer.updated_at = datetime.now()
               
               # Save to database
               await self.db_session.commit()
               
               # Log the delete event
               await log_event(
                   self.db_session,
                   LogEventType.OFFER_STATUS_CHANGE,
                   user_id,
                   f"Offer {offer_id} {status_description}"
               )
               
           except HTTPException:
               # Re-raise HTTP exceptions
               raise
           except Exception as e:
               # Log the error
               self.logger.error(f"Error deleting offer: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "DELETE_FAILED",
                       "message": "Failed to delete offer"
                   }
               )
   ```

2. **Dodanie metody kontrolera do obsługi endpointu DELETE**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Path
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from logging import Logger
   
   from src.db.session import get_async_session
   from src.services.offer_service import OfferService
   from src.services.auth import get_current_user
   
   router = APIRouter(prefix="/offers", tags=["offers"])
   
   @router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
   async def delete_offer(
       offer_id: UUID = Path(..., description="UUID of the offer to delete"),
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger)
   ):
       """
       Delete an offer.
       
       - Requires Seller role and ownership of the offer
       - If the offer has associated orders, it will be archived instead of deleted
       - Returns no content on success
       """
       try:
           # Call service method
           offer_service = OfferService(db, logger)
           await offer_service.delete_offer(
               offer_id=offer_id,
               user_id=current_user.id,
               user_role=current_user.role
           )
           
           # Return 204 No Content (done via status_code in the decorator)
           return None
           
       except HTTPException:
           # Re-raise HTTP exceptions (already handled in service)
           raise
       except Exception as e:
           # Log unexpected errors
           logger.error(f"Unexpected error in delete_offer endpoint: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "DELETE_FAILED",
                   "message": "An unexpected error occurred"
               }
           )
   ```

3. **Utworzenie testów jednostkowych dla metody usuwania oferty**:
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
       mock_session.execute = AsyncMock()
       mock_session.commit = AsyncMock()
       return mock_session
   
   @pytest.fixture
   def logger():
       return MagicMock()
   
   @pytest.mark.asyncio
   async def test_delete_offer_success_no_orders(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       
       # Mock no associated orders
       mock_result = AsyncMock()
       mock_result.scalars().first.return_value = None
       db_session.execute.return_value = mock_result
       
       # Setup mock returns
       db_session.get.return_value = mock_offer
       
       # Execute test
       await service.delete_offer(
           offer_id=offer_id,
           user_id=user_id,
           user_role=UserRole.SELLER
       )
       
       # Verify
       assert mock_offer.status == OfferStatus.DELETED
       assert db_session.commit.called
   
   @pytest.mark.asyncio
   async def test_delete_offer_success_with_orders(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       
       # Mock associated orders exist
       mock_order_item = MagicMock()
       mock_result = AsyncMock()
       mock_result.scalars().first.return_value = mock_order_item
       db_session.execute.return_value = mock_result
       
       # Setup mock returns
       db_session.get.return_value = mock_offer
       
       # Execute test
       await service.delete_offer(
           offer_id=offer_id,
           user_id=user_id,
           user_role=UserRole.SELLER
       )
       
       # Verify
       assert mock_offer.status == OfferStatus.ARCHIVED
       assert db_session.commit.called
   
   @pytest.mark.asyncio
   async def test_delete_offer_not_found(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer not found
       db_session.get.return_value = None
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.delete_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 404
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_FOUND"
   
   @pytest.mark.asyncio
   async def test_delete_offer_not_owner(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       other_user_id = UUID("99999999-9999-9999-9999-999999999999")
       
       # Mock offer with different owner
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = other_user_id
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.delete_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "NOT_OFFER_OWNER"
   
   @pytest.mark.asyncio
   async def test_delete_offer_not_seller(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.delete_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.BUYER
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "INSUFFICIENT_PERMISSIONS"
   ```

4. **Utworzenie testów integracyjnych dla endpointu DELETE**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch, MagicMock
   
   from main import app
   from src.types import UserRole
   
   client = TestClient(app)
   
   def test_delete_offer_unauthorized():
       # Test without authentication
       response = client.delete("/offers/12345678-1234-5678-1234-567812345678")
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.delete_offer")
   def test_delete_offer_success(mock_delete_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service (no return value needed for delete operation)
       mock_delete_offer.return_value = None
       
       # Test request
       response = client.delete("/offers/12345678-1234-5678-1234-567812345678")
       
       # Verify
       assert response.status_code == 204
       assert response.content == b''  # Empty content for 204
       assert mock_delete_offer.called
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.delete_offer")
   def test_delete_offer_not_found(mock_delete_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service raising not found error
       from fastapi import HTTPException, status
       mock_delete_offer.side_effect = HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail={"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}
       )
       
       # Test request
       response = client.delete("/offers/12345678-1234-5678-1234-567812345678")
       
       # Verify
       assert response.status_code == 404
       assert response.json()["error_code"] == "OFFER_NOT_FOUND"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.delete_offer")
   def test_delete_offer_forbidden(mock_delete_offer, mock_get_current_user):
       # Mock authenticated buyer (wrong role)
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.BUYER,
           "email": "buyer@example.com"
       }
       
       # Mock service raising forbidden error
       from fastapi import HTTPException, status
       mock_delete_offer.side_effect = HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only sellers can delete offers"}
       )
       
       # Test request
       response = client.delete("/offers/12345678-1234-5678-1234-567812345678")
       
       # Verify
       assert response.status_code == 403
       assert response.json()["error_code"] == "INSUFFICIENT_PERMISSIONS"
   ```
