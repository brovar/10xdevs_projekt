# API Endpoint Implementation Plan: List Offers

## 1. Przegląd punktu końcowego
Endpoint `/offers` umożliwia pobieranie paginowanej listy ofert dostępnych w systemie. Dostęp do danych jest zróżnicowany w zależności od roli użytkownika: kupujący widzą tylko aktywne oferty, sprzedawcy widzą swoje własne oferty (aktywne i nieaktywne), a administratorzy mają dostęp do wszystkich ofert. Endpoint oferuje zaawansowane opcje filtrowania, sortowania i paginacji wyników. Wymaga uwierzytelnienia.

## 2. Szczegóły żądania
- Metoda HTTP: `GET`
- Struktura URL: `/offers`
- Parametry Query:
  - `search` (string, opcjonalny): Wyszukiwana fraza (dla tytułu i opisu, bez rozróżniania wielkości liter, częściowe dopasowanie)
  - `category_id` (integer, opcjonalny): Filtrowanie według ID kategorii
  - `seller_id` (UUID, opcjonalny, tylko dla Admina): Filtrowanie według ID sprzedawcy
  - `status` (string, opcjonalny, tylko dla Admina/Sprzedawcy): Filtrowanie według statusu oferty (`active`, `inactive`, `sold`, `moderated`, `archived`)
  - `sort` (string, opcjonalny): Kryterium sortowania (`price_asc`, `price_desc`, `created_at_desc`, `relevance` gdy użyto search). Domyślnie: `created_at_desc`
  - `page` (integer, opcjonalny, domyślnie 1): Numer strony dla paginacji
  - `limit` (integer, opcjonalny, domyślnie 100, maksymalnie 100): Liczba elementów na stronę
- Request Body: Brak

## 3. Wykorzystywane typy
- **OfferSummaryDTO** (z types.py) - model pojedynczej oferty w odpowiedzi
- **OfferListResponse** (z types.py) - model odpowiedzi z paginowaną listą ofert
- **PaginatedResponse** (z types.py) - bazowy model dla paginowanych odpowiedzi
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
    "items": [
      {
        "id": "uuid-offer-id",
        "seller_id": "uuid-seller-id",
        "category_id": 1,
        "title": "Sample Product",
        "price": "99.99",
        "image_filename": "image.png",
        "quantity": 10,
        "status": "active",
        "created_at": "timestamp"
      }
      // ... inne oferty
    ],
    "total": 150,
    "page": 1,
    "limit": 100,
    "pages": 2
  }
  ```
- Kody błędów:
  - `400 Bad Request` z kodem błędu `INVALID_QUERY_PARAM` - nieprawidłowe parametry zapytania
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `500 Internal Server Error` z kodem błędu `FETCH_FAILED` - błąd pobierania danych

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. System weryfikuje uwierzytelnienie użytkownika i pobiera informacje o jego roli
3. Parametry zapytania są walidowane i przetwarzane
4. Budowane jest zapytanie bazodanowe z uwzględnieniem:
   - Roli użytkownika (filtrowanie dostępnych ofert)
   - Parametrów wyszukiwania i filtrowania
   - Sortowania i paginacji
5. Zapytanie jest wykonywane asynchronicznie na bazie danych
6. Wyniki są mapowane na DTO i zwracane w odpowiedzi z informacjami o paginacji
7. W przypadku błędów, zwracana jest odpowiednia odpowiedź błędu

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie dla wszystkich użytkowników
  - Weryfikacja tokenu sesji/JWT
- **Kontrola dostępu**:
  - Filtracja danych w zależności od roli użytkownika (RBAC)
  - Kupujący widzą tylko aktywne oferty
  - Sprzedawcy widzą tylko swoje oferty (aktywne i nieaktywne)
  - Tylko administratorzy mogą filtrować według seller_id
  - Tylko administratorzy i sprzedawcy (dla własnych ofert) mogą filtrować według statusu
- **Walidacja danych**:
  - Walidacja i sanityzacja wszystkich parametrów wejściowych
  - Kontrola limitów (np. maksymalnie 100 elementów na stronę)
- **Zapobieganie atakom**:
  - Ochrona przed SQL Injection przez użycie ORM i parametryzowanych zapytań
  - Rate limiting dla zapobiegania atakom DoS

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowe parametry zapytania: `400 Bad Request` z kodem `INVALID_QUERY_PARAM`
  - Szczegółowe komunikaty walidacyjne dla konkretnych pól
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Próba dostępu do niedozwolonych filtrów (np. seller_id dla nie-administratora): `400 Bad Request` z kodem `INVALID_QUERY_PARAM`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `FETCH_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Paginacja**:
  - Efektywna implementacja paginacji z wykorzystaniem SQL LIMIT i OFFSET
  - Ograniczenie maksymalnej wielkości strony do 100 elementów
- **Indeksowanie bazy danych**:
  - Wykorzystanie istniejących indeksów dla kolumn używanych do filtrowania i sortowania:
    - `idx_offers_status` dla filtrowania po statusie
    - `idx_offers_seller_id` dla filtrowania po sprzedawcy
    - `idx_offers_category_id` dla filtrowania po kategorii
    - `idx_offers_title` dla wyszukiwania w tytule
    - `idx_offers_description` dla wyszukiwania w opisie
- **Optymalizacja zapytań**:
  - Korzystanie z SELECT tylko na potrzebnych kolumnach
  - Wykorzystanie JOIN tylko gdy konieczne
  - Unikanie złożonych podkwerend
- **Cachowanie**:
  - Możliwość implementacji cachowania dla często używanych parametrów wyszukiwania
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych)

## 9. Etapy wdrożenia

1. **Utworzenie walidatorów parametrów zapytania**:
   ```python
   from typing import Optional, List
   from fastapi import Query
   from uuid import UUID
   from src.types import OfferStatus
   
   class OfferListParams:
       def __init__(
           self,
           search: Optional[str] = Query(None, description="Search term for title and description"),
           category_id: Optional[int] = Query(None, description="Filter by category ID"),
           seller_id: Optional[UUID] = Query(None, description="Filter by seller ID (Admin only)"),
           status: Optional[str] = Query(None, description="Filter by offer status (Admin/Seller only)"),
           sort: Optional[str] = Query("created_at_desc", description="Sorting criteria"),
           page: int = Query(1, ge=1, description="Page number"),
           limit: int = Query(100, ge=1, le=100, description="Items per page, max 100")
       ):
           self.search = search
           self.category_id = category_id
           self.seller_id = seller_id
           self.status = status
           self.sort = sort
           self.page = page
           self.limit = limit
           
       def validate_for_role(self, role: str, user_id: Optional[UUID] = None):
           """Validate parameters based on user role"""
           errors = []
           
           # Validate status parameter
           if self.status is not None:
               try:
                   status_enum = OfferStatus(self.status)
               except ValueError:
                   errors.append({"param": "status", "msg": f"Invalid status value: {self.status}"})
                   
               # Only Admin and Seller (for own offers) can filter by status
               if role not in [UserRole.ADMIN, UserRole.SELLER]:
                   errors.append({"param": "status", "msg": "Status filtering not allowed for this role"})
           
           # Validate seller_id parameter - only Admin can filter by seller_id
           if self.seller_id is not None and role != UserRole.ADMIN:
               errors.append({"param": "seller_id", "msg": "Seller ID filtering only allowed for Admin"})
               
           # Validate sort parameter
           valid_sort_options = ["price_asc", "price_desc", "created_at_desc", "relevance"]
           if self.sort not in valid_sort_options:
               errors.append({"param": "sort", "msg": f"Invalid sort value: {self.sort}"})
               
           # Relevance sorting only valid with search
           if self.sort == "relevance" and not self.search:
               errors.append({"param": "sort", "msg": "Relevance sorting only available with search parameter"})
               
           return errors
   ```

2. **Utworzenie serwisu ofert z metodą pobierania listy**:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func, or_, desc, asc
   from typing import List, Optional, Dict, Any
   from uuid import UUID
   import math
   from logging import Logger
   
   from src.db.models import Offer, User, Category
   from src.types import OfferSummaryDTO, OfferListResponse, OfferStatus, UserRole
   
   class OfferService:
       def __init__(self, db_session: AsyncSession, logger: Logger):
           self.db_session = db_session
           self.logger = logger
           
       async def list_offers(
           self,
           user_id: UUID,
           user_role: UserRole,
           params: OfferListParams
       ) -> OfferListResponse:
           """
           Get paginated list of offers based on user role and query parameters
           """
           try:
               # Base query
               query = select(Offer)
               count_query = select(func.count(Offer.id))
               
               # Apply role-based filtering
               if user_role == UserRole.BUYER:
                   # Buyers see only active offers
                   query = query.where(Offer.status == OfferStatus.ACTIVE)
                   count_query = count_query.where(Offer.status == OfferStatus.ACTIVE)
               elif user_role == UserRole.SELLER:
                   # Sellers see their own offers (all statuses except those set by admin)
                   query = query.where(Offer.seller_id == user_id)
                   count_query = count_query.where(Offer.seller_id == user_id)
                   
                   # If status filter provided, apply it
                   if params.status:
                       query = query.where(Offer.status == OfferStatus(params.status))
                       count_query = count_query.where(Offer.status == OfferStatus(params.status))
               # Admin sees all offers with optional filters
               
               # Apply search filter if provided
               if params.search:
                   search_term = f"%{params.search.lower()}%"
                   query = query.where(
                       or_(
                           func.lower(Offer.title).like(search_term),
                           func.lower(Offer.description).like(search_term)
                       )
                   )
                   count_query = count_query.where(
                       or_(
                           func.lower(Offer.title).like(search_term),
                           func.lower(Offer.description).like(search_term)
                       )
                   )
               
               # Apply category filter if provided
               if params.category_id:
                   query = query.where(Offer.category_id == params.category_id)
                   count_query = count_query.where(Offer.category_id == params.category_id)
               
               # Apply seller filter if provided (Admin only)
               if params.seller_id and user_role == UserRole.ADMIN:
                   query = query.where(Offer.seller_id == params.seller_id)
                   count_query = count_query.where(Offer.seller_id == params.seller_id)
               
               # Apply status filter if provided (Admin only)
               if params.status and user_role == UserRole.ADMIN:
                   query = query.where(Offer.status == OfferStatus(params.status))
                   count_query = count_query.where(Offer.status == OfferStatus(params.status))
               
               # Apply sorting
               if params.sort == "price_asc":
                   query = query.order_by(asc(Offer.price))
               elif params.sort == "price_desc":
                   query = query.order_by(desc(Offer.price))
               elif params.sort == "relevance" and params.search:
                   # Basic relevance sorting - could be improved with full-text search
                   # This is a placeholder implementation
                   query = query.order_by(desc(Offer.created_at))
               else:  # Default sort by created_at_desc
                   query = query.order_by(desc(Offer.created_at))
               
               # Get total count for pagination
               total_count_result = await self.db_session.execute(count_query)
               total_count = total_count_result.scalar() or 0
               
               # Calculate pagination values
               total_pages = math.ceil(total_count / params.limit)
               offset = (params.page - 1) * params.limit
               
               # Apply pagination
               query = query.offset(offset).limit(params.limit)
               
               # Execute query
               result = await self.db_session.execute(query)
               offers = result.scalars().all()
               
               # Map to DTOs
               offer_dtos = [
                   OfferSummaryDTO(
                       id=offer.id,
                       seller_id=offer.seller_id,
                       category_id=offer.category_id,
                       title=offer.title,
                       price=offer.price,
                       image_filename=offer.image_filename,
                       quantity=offer.quantity,
                       status=offer.status,
                       created_at=offer.created_at
                   )
                   for offer in offers
               ]
               
               # Return paginated response
               return OfferListResponse(
                   items=offer_dtos,
                   total=total_count,
                   page=params.page,
                   limit=params.limit,
                   pages=total_pages
               )
           except Exception as e:
               self.logger.error(f"Error fetching offers list: {str(e)}")
               raise
   ```

3. **Utworzenie kontrolera (routera) z funkcją obsługi endpointu**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status
   from sqlalchemy.ext.asyncio import AsyncSession
   from logging import Logger
   
   from src.db.session import get_async_session
   from src.services.offer_service import OfferService
   from src.services.auth import get_current_user
   from src.types import OfferListResponse, UserRole
   
   router = APIRouter(prefix="/offers", tags=["offers"])
   
   @router.get("/", response_model=OfferListResponse)
   async def list_offers(
       params: OfferListParams = Depends(),
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger)
   ):
       """
       Get a paginated list of offers.
       
       The visible offers depend on the user's role:
       - Buyers see only active offers
       - Sellers see their own offers
       - Admins see all offers
       
       Various filters can be applied based on the query parameters.
       """
       # Validate parameters based on user role
       validation_errors = params.validate_for_role(current_user.role, current_user.id)
       if validation_errors:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail={
                   "error_code": "INVALID_QUERY_PARAM",
                   "message": "Invalid query parameters",
                   "details": validation_errors
               }
           )
       
       try:
           offer_service = OfferService(db, logger)
           result = await offer_service.list_offers(
               user_id=current_user.id,
               user_role=current_user.role,
               params=params
           )
           return result
       except Exception as e:
           logger.error(f"Failed to fetch offers: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch offers. Please try again later."
               }
           )
   ```

4. **Utworzenie testów jednostkowych dla serwisu ofert**:
   ```python
   import pytest
   from unittest.mock import MagicMock, AsyncMock, patch
   from sqlalchemy.ext.asyncio import AsyncSession
   
   from src.services.offer_service import OfferService
   from src.types import UserRole, OfferStatus, OfferListParams
   
   @pytest.fixture
   def db_session():
       mock_session = AsyncMock(spec=AsyncSession)
       mock_session.execute = AsyncMock()
       mock_session.commit = AsyncMock()
       return mock_session
   
   @pytest.fixture
   def logger():
       return MagicMock()
   
   @pytest.mark.asyncio
   async def test_list_offers_buyer_role(db_session, logger):
       # Setup
       service = OfferService(db_session, logger)
       user_id = "12345678-1234-5678-1234-567812345678"
       params = OfferListParams()
       
       # Mock query results
       db_session.execute.return_value.scalar.return_value = 10  # Total count
       db_session.execute.return_value.scalars.return_value.all.return_value = []  # Empty list of offers
       
       # Test
       result = await service.list_offers(user_id, UserRole.BUYER, params)
       
       # Verify
       assert result.total == 10
       assert result.page == 1
       assert result.limit == 100
       assert result.pages == 1
       assert len(result.items) == 0
       
       # Check that the query included status filter for ACTIVE
       # This would require more complex mocking of the SQLAlchemy query
   
   @pytest.mark.asyncio
   async def test_list_offers_seller_role(db_session, logger):
       # Similar to above but test seller-specific logic
       pass
   
   @pytest.mark.asyncio
   async def test_list_offers_admin_role(db_session, logger):
       # Similar to above but test admin-specific logic
       pass
   
   @pytest.mark.asyncio
   async def test_list_offers_with_search(db_session, logger):
       # Test search functionality
       pass
   
   @pytest.mark.asyncio
   async def test_list_offers_with_filters(db_session, logger):
       # Test various filters
       pass
   ```

5. **Utworzenie testów integracyjnych dla endpointu**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch
   
   from main import app
   from src.types import UserRole
   
   client = TestClient(app)
   
   def test_list_offers_unauthorized():
       response = client.get("/offers")
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   def test_list_offers_buyer(mock_get_current_user):
       # Mock authenticated buyer
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.BUYER,
           "email": "buyer@example.com"
       }
       
       response = client.get("/offers")
       assert response.status_code == 200
       assert "items" in response.json()
       assert "total" in response.json()
       
       # More assertions based on expected response format
   
   @patch("src.services.auth.get_current_user")
   def test_list_offers_invalid_params(mock_get_current_user):
       # Mock authenticated user
       mock_get_current_user.return_value = {
           "id": "12345678-1234-5678-1234-567812345678",
           "role": UserRole.BUYER,
           "email": "buyer@example.com"
       }
       
       # Test invalid status for buyer
       response = client.get("/offers?status=inactive")
       assert response.status_code == 400
       assert response.json()["error_code"] == "INVALID_QUERY_PARAM"
       
       # Test invalid sort option
       response = client.get("/offers?sort=unknown")
       assert response.status_code == 400
       assert response.json()["error_code"] == "INVALID_QUERY_PARAM"
   ```

6. **Rejestracja routera w aplikacji głównej**:
   ```python
   from fastapi import FastAPI
   from src.routers import offers_router
   
   app = FastAPI()
   app.include_router(offers_router)
   ```

7. **Dokumentacja OpenAPI/Swagger**:
   ```python
   # W pliku głównym aplikacji
   from fastapi import FastAPI
   from fastapi.openapi.utils import get_openapi
   
   app = FastAPI()
   
   def custom_openapi():
       if app.openapi_schema:
           return app.openapi_schema
       
       openapi_schema = get_openapi(
           title="SteamBay API",
           version="1.0.0",
           description="API for SteamBay e-commerce platform",
           routes=app.routes,
       )
       
       # Customize endpoint documentation
       for path in openapi_schema["paths"]:
           if path == "/offers":
               for method in openapi_schema["paths"][path]:
                   if method == "get":
                       operation = openapi_schema["paths"][path][method]
                       operation["description"] = "Retrieve a paginated list of offers with filtering options. Access is role-based."
                       operation["security"] = [{"cookieAuth": []}]
       
       app.openapi_schema = openapi_schema
       return app.openapi_schema
   
   app.openapi = custom_openapi
   ```
