# API Endpoint Implementation Plan: Update Offer

## 1. Przegląd punktu końcowego
Endpoint `/offers/{offer_id}` z metodą PUT umożliwia aktualizację istniejącej oferty w systemie. Dostęp do tego endpointu ma wyłącznie sprzedawca, który jest właścicielem oferty. Aktualizować można tylko oferty w statusie 'active' lub 'inactive'. Endpoint przyjmuje dane w formacie multipart/form-data, co pozwala na aktualizację wszystkich pól oferty, włącznie z możliwością dodania, zmiany lub usunięcia obrazu produktu. Po pomyślnej aktualizacji, endpoint zwraca zaktualizowany obiekt oferty.

## 2. Szczegóły żądania
- Metoda HTTP: `PUT`
- Struktura URL: `/offers/{offer_id}`
- Parametry Path:
  - `offer_id` (UUID, wymagany): Identyfikator oferty, która ma zostać zaktualizowana
- Format danych: `multipart/form-data`
- Pola formularza:
  ```
  title: string (wymagane) - tytuł oferty
  description: string (opcjonalne) - opis oferty
  price: string (wymagane) - cena produktu (reprezentacja wartości dziesiętnej)
  quantity: integer (wymagane) - ilość dostępnych sztuk
  category_id: integer (wymagane) - identyfikator kategorii
  image: file (opcjonalne) - plik obrazu (PNG, max 1024x768)
  ```
- Uwaga: Wszystkie edytowalne pola muszą być przekazane, nawet jeśli nie ulegają zmianie

## 3. Wykorzystywane typy
- **UpdateOfferRequest** (z types.py) - model walidacji danych wejściowych
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
    "title": "Updated Product Title",
    "description": "Updated product description.",
    "price": "99.99",
    "image_filename": "image.png",
    "quantity": 10,
    "status": "active",
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
  - `400 Bad Request` z różnymi kodami błędów:
    - `INVALID_INPUT` - nieprawidłowe dane wejściowe
    - `INVALID_FILE_TYPE` - nieprawidłowy format pliku
    - `FILE_TOO_LARGE` - zbyt duży plik
    - `INVALID_STATUS_FOR_EDIT` - nieprawidłowy status oferty dla edycji
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `403 Forbidden` z kodami błędów:
    - `INSUFFICIENT_PERMISSIONS` - użytkownik nie jest sprzedawcą
    - `NOT_OFFER_OWNER` - użytkownik nie jest właścicielem oferty
  - `404 Not Found` z kodami błędów:
    - `OFFER_NOT_FOUND` - oferta nie istnieje
    - `CATEGORY_NOT_FOUND` - kategoria nie istnieje
  - `500 Internal Server Error` z kodami błędów:
    - `UPDATE_FAILED` - błąd podczas aktualizacji oferty
    - `FILE_UPLOAD_FAILED` - błąd podczas przesyłania pliku

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. System weryfikuje uwierzytelnienie użytkownika i sprawdza czy ma rolę Seller
3. Pobieranie istniejącej oferty z bazy danych na podstawie offer_id
4. Sprawdzenie czy oferta istnieje
5. Sprawdzenie czy użytkownik jest właścicielem oferty
6. Sprawdzenie czy status oferty pozwala na edycję (active lub inactive)
7. Walidacja danych z formularza (title, price, quantity, category_id)
8. Sprawdzenie czy kategoria istnieje
9. Jeśli przesłano nowy obraz:
   - Walidacja rozmiaru i typu pliku
   - Usunięcie starego obrazu (jeśli istnieje)
   - Generowanie unikalnej nazwy pliku
   - Zapisanie nowego obrazu
10. Aktualizacja rekordu oferty w bazie danych
11. Logowanie zdarzenia aktualizacji oferty
12. Pobranie zaktualizowanej oferty z dodatkowymi danymi (sprzedawca, kategoria)
13. Zwrócenie odpowiedzi z zaktualizowanymi danymi

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie dla wszystkich użytkowników
  - Weryfikacja tokenu sesji/JWT
- **Autoryzacja**:
  - Kontrola dostępu na podstawie roli (tylko sprzedawca może aktualizować oferty)
  - Sprawdzanie własności zasobu (sprzedawca może aktualizować tylko swoje oferty)
- **Walidacja danych**:
  - Walidacja wszystkich pól formularza
  - Walidacja plików (typ, rozmiar)
  - Sanityzacja danych wejściowych (zapobieganie XSS, SQL Injection)
- **Bezpieczeństwo plików**:
  - Generowanie losowych nazw plików
  - Sprawdzanie typu i rozmiaru pliku
  - Bezpieczne przechowywanie plików poza katalogiem publicznym
- **Ochrona przed atakami**:
  - Rate limiting dla zapobiegania nadużyciom
  - Logowanie prób nieautoryzowanego dostępu
  - Transakcje bazodanowe dla zapewnienia integralności danych

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowe dane formularza: `400 Bad Request` z kodem `INVALID_INPUT`
  - Nieprawidłowy typ pliku: `400 Bad Request` z kodem `INVALID_FILE_TYPE`
  - Zbyt duży plik: `400 Bad Request` z kodem `FILE_TOO_LARGE`
  - Nieprawidłowy status oferty: `400 Bad Request` z kodem `INVALID_STATUS_FOR_EDIT`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Brak wymaganej roli: `403 Forbidden` z kodem `INSUFFICIENT_PERMISSIONS`
  - Brak własności oferty: `403 Forbidden` z kodem `NOT_OFFER_OWNER`
- **Błędy biznesowe**:
  - Oferta nie istnieje: `404 Not Found` z kodem `OFFER_NOT_FOUND`
  - Kategoria nie istnieje: `404 Not Found` z kodem `CATEGORY_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `UPDATE_FAILED`
  - Problemy z przesyłaniem pliku: `500 Internal Server Error` z kodem `FILE_UPLOAD_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Obsługa plików**:
  - Asynchroniczne przetwarzanie plików
  - Efektywne zarządzanie pamięcią przy przesyłaniu dużych plików
  - Przetwarzanie obrazów w tle (np. zmiana rozmiaru, optymalizacja)
- **Operacje bazodanowe**:
  - Użycie transakcji dla zapewnienia atomowości operacji
  - Optymalizacja zapytań (minimalizacja liczby zapytań)
  - Indeksowanie odpowiednich kolumn w tabeli `offers`
- **Cachowanie**:
  - Możliwość cachowania często używanych kategorii
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych, operacje na plikach)
  - Wykorzystanie zadań w tle (background tasks) dla mniej krytycznych operacji

## 9. Etapy wdrożenia

1. **Utworzenie serwisu ofert z metodą aktualizacji**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from fastapi import HTTPException, status, UploadFile
   from typing import Optional
   from uuid import UUID
   import os
   import aiofiles
   from datetime import datetime
   from logging import Logger
   
   from src.db.models import Offer, User, Category
   from src.types import UpdateOfferRequest, OfferDetailDTO, OfferStatus, UserRole, LogEventType
   from src.services.logging import log_event
   
   class OfferService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
           self.UPLOAD_DIR = "uploads/offers"
           self.ALLOWED_IMAGE_TYPES = ["image/png"]
           self.MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
           
           # Ensure upload directory exists
           os.makedirs(self.UPLOAD_DIR, exist_ok=True)
           
       async def update_offer(
           self,
           offer_id: UUID,
           user_id: UUID,
           user_role: UserRole,
           update_data: UpdateOfferRequest,
           image: Optional[UploadFile] = None
       ) -> OfferDetailDTO:
           """
           Update an existing offer
           
           Args:
               offer_id: UUID of the offer to update
               user_id: UUID of the current user
               user_role: Role of the current user
               update_data: Data with updated offer fields
               image: Optional new image file
               
           Returns:
               OfferDetailDTO with updated offer details
               
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
                           "message": "Only sellers can update offers"
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
                           "message": "You can only update your own offers"
                       }
                   )
               
               # Check if offer is in an editable state
               if offer.status not in [OfferStatus.ACTIVE, OfferStatus.INACTIVE]:
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail={
                           "error_code": "INVALID_STATUS_FOR_EDIT",
                           "message": f"Cannot edit offer with status {offer.status}"
                       }
                   )
               
               # Verify category exists
               category = await self.db_session.get(Category, update_data.category_id)
               if not category:
                   raise HTTPException(
                       status_code=status.HTTP_404_NOT_FOUND,
                       detail={
                           "error_code": "CATEGORY_NOT_FOUND",
                           "message": "Category not found"
                       }
                   )
               
               # Process image if provided
               image_filename = offer.image_filename
               if image:
                   # Validate image size
                   content = await image.read()
                   if len(content) > self.MAX_IMAGE_SIZE:
                       raise HTTPException(
                           status_code=status.HTTP_400_BAD_REQUEST,
                           detail={
                               "error_code": "FILE_TOO_LARGE",
                               "message": "Image size exceeds the limit"
                           }
                       )
                   
                   # Validate image type
                   if image.content_type not in self.ALLOWED_IMAGE_TYPES:
                       raise HTTPException(
                           status_code=status.HTTP_400_BAD_REQUEST,
                           detail={
                               "error_code": "INVALID_FILE_TYPE",
                               "message": "Only PNG images are supported"
                           }
                       )
                   
                   # Generate unique filename
                   from uuid import uuid4
                   ext = image.filename.split('.')[-1]
                   image_filename = f"{uuid4()}.{ext}"
                   
                   # Reset file cursor
                   await image.seek(0)
                   
                   # Save new image
                   image_path = os.path.join(self.UPLOAD_DIR, image_filename)
                   await self._save_image(image_path, content)
                   
                   # Delete old image if exists
                   if offer.image_filename:
                       old_image_path = os.path.join(self.UPLOAD_DIR, offer.image_filename)
                       await self._delete_file_if_exists(old_image_path)
               
               # Update offer fields
               offer.title = update_data.title
               offer.description = update_data.description
               offer.price = update_data.price
               offer.quantity = update_data.quantity
               offer.category_id = update_data.category_id
               offer.image_filename = image_filename
               offer.updated_at = datetime.now()
               
               # Save to database
               await self.db_session.commit()
               await self.db_session.refresh(offer)
               
               # Log the update event
               await log_event(
                   self.db_session,
                   LogEventType.OFFER_EDIT,
                   user_id,
                   f"Offer updated: {offer.id}"
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
               self.logger.error(f"Error updating offer: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "UPDATE_FAILED",
                       "message": "Failed to update offer"
                   }
               )
       
       async def _save_image(self, path: str, content: bytes):
           """Save image file asynchronously"""
           try:
               async with aiofiles.open(path, 'wb') as f:
                   await f.write(content)
           except Exception as e:
               self.logger.error(f"Error saving image file: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "FILE_UPLOAD_FAILED",
                       "message": "Failed to save image file"
                   }
               )
       
       async def _delete_file_if_exists(self, path: str):
           """Delete file if it exists"""
           try:
               if os.path.exists(path):
                   os.remove(path)
           except Exception as e:
               # Log but don't fail if delete fails
               self.logger.error(f"Error deleting file {path}: {str(e)}")
       
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

2. **Utworzenie kontrolera (routera) z funkcją obsługi endpointu**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Path, BackgroundTasks
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import Optional
   from uuid import UUID
   from logging import Logger
   
   from src.db.session import get_async_session
   from src.services.offer_service import OfferService
   from src.services.auth import get_current_user
   from src.types import UpdateOfferRequest, OfferDetailDTO
   
   router = APIRouter(prefix="/offers", tags=["offers"])
   
   @router.put("/{offer_id}", response_model=OfferDetailDTO)
   async def update_offer(
       offer_id: UUID = Path(..., description="UUID of the offer to update"),
       title: str = Form(...),
       description: Optional[str] = Form(None),
       price: float = Form(...),
       quantity: int = Form(...),
       category_id: int = Form(...),
       image: Optional[UploadFile] = File(None),
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger),
       background_tasks: BackgroundTasks = BackgroundTasks()
   ):
       """
       Update an existing offer.
       
       - Requires Seller role and ownership of the offer
       - Offer must be in 'active' or 'inactive' status
       - All editable fields must be provided
       - Returns the updated offer with seller and category information
       """
       try:
           # Create update data from form fields
           update_data = UpdateOfferRequest(
               title=title,
               description=description,
               price=price,
               quantity=quantity,
               category_id=category_id
           )
           
           # Call service method
           offer_service = OfferService(db, logger)
           result = await offer_service.update_offer(
               offer_id=offer_id,
               user_id=current_user.id,
               user_role=current_user.role,
               update_data=update_data,
               image=image
           )
           
           return result
           
       except HTTPException:
           # Re-raise HTTP exceptions (already handled in service)
           raise
       except Exception as e:
           # Log unexpected errors
           logger.error(f"Unexpected error in update_offer endpoint: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "UPDATE_FAILED",
                   "message": "An unexpected error occurred"
               }
           )
   ```

3. **Utworzenie testów jednostkowych dla serwisu ofert**:
   ```python
   import pytest
   from unittest.mock import MagicMock, AsyncMock, patch
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from fastapi import HTTPException, UploadFile
   
   from src.services.offer_service import OfferService
   from src.types import UserRole, OfferStatus, UpdateOfferRequest
   
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
   
   @pytest.fixture
   def update_data():
       return UpdateOfferRequest(
           title="Updated Title",
           description="Updated Description",
           price=99.99,
           quantity=5,
           category_id=1
       )
   
   @pytest.mark.asyncio
   async def test_update_offer_success(db_session, logger, update_data):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.ACTIVE
       
       # Mock category
       mock_category = MagicMock()
       mock_category.id = 1
       
       # Mock seller
       mock_seller = MagicMock()
       mock_seller.id = user_id
       
       # Setup mock returns
       db_session.get.side_effect = [mock_offer, mock_category, mock_seller, mock_category]
       
       # Mock image handling methods
       service._save_image = AsyncMock()
       service._delete_file_if_exists = AsyncMock()
       service._map_to_offer_detail_dto = MagicMock()
       
       # Test without image
       result = await service.update_offer(
           offer_id=offer_id,
           user_id=user_id,
           user_role=UserRole.SELLER,
           update_data=update_data
       )
       
       # Verify
       assert db_session.commit.called
       assert db_session.refresh.called
       assert mock_offer.title == update_data.title
       assert mock_offer.description == update_data.description
   
   @pytest.mark.asyncio
   async def test_update_offer_not_found(db_session, logger, update_data):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer not found
       db_session.get.return_value = None
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.update_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER,
               update_data=update_data
           )
           
       assert exc_info.value.status_code == 404
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_FOUND"
   
   @pytest.mark.asyncio
   async def test_update_offer_not_owner(db_session, logger, update_data):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       other_user_id = UUID("99999999-9999-9999-9999-999999999999")
       
       # Mock offer with different owner
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = other_user_id
       mock_offer.status = OfferStatus.ACTIVE
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.update_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER,
               update_data=update_data
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "NOT_OFFER_OWNER"
   
   @pytest.mark.asyncio
   async def test_update_offer_invalid_status(db_session, logger, update_data):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer with sold status
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.SOLD
       
       db_session.get.return_value = mock_offer
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.update_offer(
               offer_id=offer_id,
               user_id=user_id,
               user_role=UserRole.SELLER,
               update_data=update_data
           )
           
       assert exc_info.value.status_code == 400
       assert exc_info.value.detail["error_code"] == "INVALID_STATUS_FOR_EDIT"
   ```

4. **Utworzenie testów integracyjnych dla endpointu**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch, MagicMock
   from io import BytesIO
   
   from main import app
   from src.types import UserRole, OfferStatus
   
   client = TestClient(app)
   
   def test_update_offer_unauthorized():
       # Test without authentication
       files = {"image": ("test.png", BytesIO(b"test"), "image/png")}
       data = {
           "title": "Updated Title",
           "description": "Updated Description",
           "price": "99.99",
           "quantity": "5",
           "category_id": "1"
       }
       
       response = client.put("/offers/12345678-1234-5678-1234-567812345678", data=data, files=files)
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.update_offer")
   def test_update_offer_success(mock_update_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service response
       mock_update_offer.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "seller_id": "12345678-1234-5678-1234-567812345678",
           "category_id": 1,
           "title": "Updated Title",
           "description": "Updated Description",
           "price": "99.99",
           "image_filename": "updated.png",
           "quantity": 5,
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
       
       # Test data
       files = {"image": ("test.png", BytesIO(b"test"), "image/png")}
       data = {
           "title": "Updated Title",
           "description": "Updated Description",
           "price": "99.99",
           "quantity": "5",
           "category_id": "1"
       }
       
       response = client.put("/offers/12345678-1234-5678-1234-567812345678", data=data, files=files)
       assert response.status_code == 200
       assert response.json()["title"] == "Updated Title"
       assert response.json()["seller"]["first_name"] == "Test"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.update_offer")
   def test_update_offer_not_found(mock_update_offer, mock_get_current_user):
       # Mock authenticated seller
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.SELLER,
           "email": "seller@example.com"
       }
       
       # Mock service raising not found error
       from fastapi import HTTPException, status
       mock_update_offer.side_effect = HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail={"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}
       )
       
       # Test data
       data = {
           "title": "Updated Title",
           "description": "Updated Description",
           "price": "99.99",
           "quantity": "5",
           "category_id": "1"
       }
       
       response = client.put("/offers/12345678-1234-5678-1234-567812345678", data=data)
       assert response.status_code == 404
       assert response.json()["error_code"] == "OFFER_NOT_FOUND"
   ```
