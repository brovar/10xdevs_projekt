# API Endpoint Implementation Plan: Get Offer Details

## 1. Przegląd punktu końcowego
Endpoint `/offers/{offer_id}` umożliwia pobieranie szczegółowych informacji o konkretnej ofercie na podstawie jej identyfikatora. Dostęp do danych oferty jest zróżnicowany w zależności od roli użytkownika: kupujący widzą tylko aktywne oferty, sprzedawcy widzą swoje własne oferty (niezależnie od statusu), a administratorzy mają dostęp do wszystkich ofert. Oprócz podstawowych danych oferty, endpoint zwraca również informacje o sprzedawcy i kategorii. Wymaga uwierzytelnienia.

## 2. Szczegóły żądania
- Metoda HTTP: `GET`
- Struktura URL: `/offers/{offer_id}`
- Parametry Path:
  - `offer_id` (UUID, wymagany): Identyfikator oferty, której szczegóły mają zostać pobrane
- Parametry Query: brak
- Request Body: brak

## 3. Wykorzystywane typy
- **OfferDetailDTO** (z types.py) - model szczegółów oferty w odpowiedzi
- **OfferSummaryDTO** (z types.py) - bazowy model dla OfferDetailDTO
- **SellerInfoDTO** (z types.py) - model informacji o sprzedawcy
- **CategoryDTO** (z types.py) - model informacji o kategorii
- **OfferStatus** (z types.py) - enum określający możliwe statusy oferty
- **UserRole** (z types.py) - enum określający role użytkowników
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
    "title": "Sample Product",
    "description": "Detailed description here.",
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
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `403 Forbidden` z kodem błędu `ACCESS_DENIED` - kupujący próbuje uzyskać dostęp do nieaktywnej/moderowanej oferty
  - `404 Not Found` z kodem błędu `OFFER_NOT_FOUND` - oferta o podanym ID nie istnieje
  - `500 Internal Server Error` z kodem błędu `FETCH_FAILED` - błąd pobierania danych

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. System weryfikuje uwierzytelnienie użytkownika i pobiera informacje o jego roli
3. Walidacja parametru `offer_id` (poprawny format UUID)
4. Pobranie danych oferty z bazy danych
5. Jeśli oferta nie istnieje, zwrócenie błędu 404
6. Sprawdzenie uprawnień do dostępu do oferty w zależności od roli użytkownika:
   - Kupujący: dostęp tylko do aktywnych ofert
   - Sprzedawcy: dostęp tylko do własnych ofert
   - Administratorzy: dostęp do wszystkich ofert
7. Jeśli użytkownik nie ma dostępu, zwrócenie błędu 403
8. Pobranie danych sprzedawcy i kategorii
9. Złączenie danych i zwrócenie odpowiedzi

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie dla wszystkich użytkowników
  - Weryfikacja tokenu sesji/JWT
- **Kontrola dostępu**:
  - Filtracja danych w zależności od roli użytkownika (RBAC)
  - Kupujący widzą tylko aktywne oferty
  - Sprzedawcy widzą tylko swoje własne oferty
  - Administratorzy widzą wszystkie oferty
- **Walidacja danych**:
  - Walidacja formatu UUID dla parametru `offer_id`
- **Ochrona danych**:
  - Udostępnianie tylko niezbędnych danych o sprzedawcy (bez ujawniania wrażliwych informacji)
- **Zapobieganie atakom**:
  - Ochrona przed manipulacją parametrami ścieżki
  - Logowanie prób nieautoryzowanego dostępu

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowy format UUID: `404 Not Found` z kodem `OFFER_NOT_FOUND`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Brak dostępu do oferty: `403 Forbidden` z kodem `ACCESS_DENIED`
- **Błędy biznesowe**:
  - Oferta nie istnieje: `404 Not Found` z kodem `OFFER_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `FETCH_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Optymalizacja zapytań**:
  - Użycie JOIN dla pobrania danych oferty, sprzedawcy i kategorii w jednym zapytaniu
  - Wykorzystanie indeksów dla `offers.id`, `offers.seller_id` i `offers.category_id`
- **Cachowanie**:
  - Możliwość cachowania odpowiedzi dla często oglądanych ofert (z uwzględnieniem roli użytkownika)
  - Ustawienie odpowiednich nagłówków cache-control
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)

## 9. Etapy wdrożenia

1. **Utworzenie serwisu ofert z metodą pobierania szczegółów**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, join
   from typing import Optional
   from uuid import UUID
   from fastapi import HTTPException, status
   from logging import Logger
   
   from src.db.models import Offer, User, Category
   from src.types import OfferDetailDTO, SellerInfoDTO, CategoryDTO, OfferStatus, UserRole
   
   class OfferService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
           
       async def get_offer_details(
           self,
           offer_id: UUID,
           user_id: UUID,
           user_role: UserRole
       ) -> OfferDetailDTO:
           """
           Get detailed information about a specific offer
           
           Args:
               offer_id: UUID of the offer to retrieve
               user_id: UUID of the current user
               user_role: Role of the current user
               
           Returns:
               OfferDetailDTO with offer details
               
           Raises:
               HTTPException: If offer not found or user has no access
           """
           try:
               # Create query to fetch offer with related data
               query = (
                   select(Offer, User, Category)
                   .join(User, Offer.seller_id == User.id)
                   .join(Category, Offer.category_id == Category.id)
                   .where(Offer.id == offer_id)
               )
               
               # Execute query
               result = await self.db_session.execute(query)
               record = result.first()
               
               # Check if offer exists
               if not record:
                   raise HTTPException(
                       status_code=status.HTTP_404_NOT_FOUND,
                       detail={
                           "error_code": "OFFER_NOT_FOUND",
                           "message": "Offer not found"
                       }
                   )
                   
               offer, seller, category = record
               
               # Check access based on user role
               if user_role == UserRole.BUYER:
                   # Buyers can only see active offers
                   if offer.status != OfferStatus.ACTIVE:
                       raise HTTPException(
                           status_code=status.HTTP_403_FORBIDDEN,
                           detail={
                               "error_code": "ACCESS_DENIED",
                               "message": "This offer is not available"
                           }
                       )
               elif user_role == UserRole.SELLER:
                   # Sellers can only see their own offers
                   if offer.seller_id != user_id:
                       raise HTTPException(
                           status_code=status.HTTP_403_FORBIDDEN,
                           detail={
                               "error_code": "ACCESS_DENIED",
                               "message": "You don't have access to this offer"
                           }
                       )
               # Admins can see all offers
               
               # Prepare seller info
               seller_info = SellerInfoDTO(
                   id=seller.id,
                   first_name=seller.first_name,
                   last_name=seller.last_name
               )
               
               # Prepare category info
               category_info = CategoryDTO(
                   id=category.id,
                   name=category.name
               )
               
               # Return detailed DTO
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
               
           except HTTPException:
               # Re-raise HTTP exceptions
               raise
           except Exception as e:
               # Log the error
               self.logger.error(f"Error fetching offer details: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "FETCH_FAILED",
                       "message": "Failed to fetch offer details"
                   }
               )
   ```

2. **Utworzenie kontrolera (routera) z funkcją obsługi endpointu**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Path
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   from uuid import UUID
   
   from src.db.session import get_async_session
   from src.services.offer_service import OfferService
   from src.services.auth import get_current_user
   from src.types import OfferDetailDTO
   
   router = APIRouter(prefix="/offers", tags=["offers"])
   
   @router.get("/{offer_id}", response_model=OfferDetailDTO)
   async def get_offer_details(
       offer_id: UUID = Path(..., description="UUID of the offer to retrieve"),
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger)
   ):
       """
       Get detailed information about a specific offer.
       
       Access rules:
       - Buyers can only see active offers
       - Sellers can only see their own offers
       - Admins can see all offers
       
       The response includes seller and category information.
       """
       try:
           offer_service = OfferService(db, logger)
           result = await offer_service.get_offer_details(
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
           logger.error(f"Unexpected error in get_offer_details endpoint: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "FETCH_FAILED",
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
   from fastapi import HTTPException
   
   from src.services.offer_service import OfferService
   from src.types import UserRole, OfferStatus
   
   @pytest.fixture
   def db_session():
       mock_session = AsyncMock(spec=AsyncSession)
       mock_session.execute = AsyncMock()
       return mock_session
   
   @pytest.fixture
   def logger():
       return MagicMock()
   
   @pytest.mark.asyncio
   async def test_get_offer_details_success(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer record
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = user_id
       mock_offer.status = OfferStatus.ACTIVE
       mock_offer.title = "Test Offer"
       
       # Mock seller record
       mock_seller = MagicMock()
       mock_seller.id = user_id
       mock_seller.first_name = "Test"
       mock_seller.last_name = "Seller"
       
       # Mock category record
       mock_category = MagicMock()
       mock_category.id = 1
       mock_category.name = "Test Category"
       
       # Setup mock return value
       db_session.execute.return_value.first.return_value = (mock_offer, mock_seller, mock_category)
       
       # Test - Admin role
       result = await service.get_offer_details(offer_id, user_id, UserRole.ADMIN)
       
       # Verify
       assert result.id == offer_id
       assert result.title == "Test Offer"
       assert result.seller.id == user_id
       assert result.seller.first_name == "Test"
       assert result.category.id == 1
       assert result.category.name == "Test Category"
   
   @pytest.mark.asyncio
   async def test_get_offer_details_not_found(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock no result returned
       db_session.execute.return_value.first.return_value = None
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.get_offer_details(offer_id, user_id, UserRole.BUYER)
           
       assert exc_info.value.status_code == 404
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_FOUND"
   
   @pytest.mark.asyncio
   async def test_get_offer_details_buyer_access_denied(db_session, logger):
       # Setup - buyer trying to access inactive offer
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer with inactive status
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = UUID("99999999-9999-9999-9999-999999999999")  # Different seller
       mock_offer.status = OfferStatus.INACTIVE
       
       mock_seller = MagicMock()
       mock_category = MagicMock()
       
       # Setup mock return
       db_session.execute.return_value.first.return_value = (mock_offer, mock_seller, mock_category)
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.get_offer_details(offer_id, user_id, UserRole.BUYER)
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "ACCESS_DENIED"
   
   @pytest.mark.asyncio
   async def test_get_offer_details_seller_access_denied(db_session, logger):
       # Setup - seller trying to access another seller's offer
       service = OfferService(db_session, logger)
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       user_id = UUID("87654321-8765-4321-8765-432187654321")
       
       # Mock offer with different seller_id
       mock_offer = MagicMock()
       mock_offer.id = offer_id
       mock_offer.seller_id = UUID("99999999-9999-9999-9999-999999999999")  # Different seller
       mock_offer.status = OfferStatus.ACTIVE
       
       mock_seller = MagicMock()
       mock_category = MagicMock()
       
       # Setup mock return
       db_session.execute.return_value.first.return_value = (mock_offer, mock_seller, mock_category)
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await service.get_offer_details(offer_id, user_id, UserRole.SELLER)
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "ACCESS_DENIED"
   ```

4. **Utworzenie testów integracyjnych dla endpointu**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch
   
   from main import app
   from src.types import UserRole
   
   client = TestClient(app)
   
   def test_get_offer_details_unauthorized():
       response = client.get("/offers/12345678-1234-5678-1234-567812345678")
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.get_offer_details")
   def test_get_offer_details_success(mock_get_offer_details, mock_get_current_user):
       # Mock authenticated user
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.BUYER,
           "email": "buyer@example.com"
       }
       
       # Mock service response
       mock_get_offer_details.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "seller_id": "87654321-8765-4321-8765-432187654321",
           "category_id": 1,
           "title": "Test Offer",
           "description": "Test Description",
           "price": "99.99",
           "image_filename": "test.png",
           "quantity": 10,
           "status": "active",
           "created_at": "2023-01-01T00:00:00Z",
           "updated_at": None,
           "seller": {
               "id": "87654321-8765-4321-8765-432187654321",
               "first_name": "Test",
               "last_name": "Seller"
           },
           "category": {
               "id": 1,
               "name": "Test Category"
           }
       }
       
       response = client.get("/offers/12345678-1234-5678-1234-567812345678")
       assert response.status_code == 200
       assert response.json()["id"] == "12345678-1234-5678-1234-567812345678"
       assert response.json()["title"] == "Test Offer"
       assert response.json()["seller"]["first_name"] == "Test"
       assert response.json()["category"]["name"] == "Test Category"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.offer_service.OfferService.get_offer_details")
   def test_get_offer_details_not_found(mock_get_offer_details, mock_get_current_user):
       # Mock authenticated user
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.BUYER,
           "email": "buyer@example.com"
       }
       
       # Mock service raising not found error
       from fastapi import HTTPException, status
       mock_get_offer_details.side_effect = HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail={"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}
       )
       
       response = client.get("/offers/12345678-1234-5678-1234-567812345678")
       assert response.status_code == 404
       assert response.json()["error_code"] == "OFFER_NOT_FOUND"
   ```

5. **Rejestracja routera w aplikacji głównej**:
   ```python
   from fastapi import FastAPI
   from src.routers import offers_router
   
   app = FastAPI()
   app.include_router(offers_router)
   ```

6. **Dodanie dokumentacji OpenAPI/Swagger**:
   ```python
   # W pliku głównym aplikacji lub w funkcji customizującej dokumentację API
   
   # Customize endpoint documentation
   for path in openapi_schema["paths"]:
       if path == "/offers/{offer_id}":
           operation = openapi_schema["paths"][path]["get"]
           operation["description"] = (
               "Get detailed information about a specific offer. "
               "Access depends on user role: Buyers see only active offers, "
               "Sellers see their own offers, Admins see all offers."
           )
           operation["security"] = [{"cookieAuth": []}]
   ```
