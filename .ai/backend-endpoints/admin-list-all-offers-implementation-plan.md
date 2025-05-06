# API Endpoint Implementation Plan: List All Offers (Admin)

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania paginowanej listy wszystkich ofert w systemie przez administratora. W przeciwieństwie do standardowego endpointu `/offers`, ten umożliwia dostęp do ofert o wszystkich statusach (w tym `inactive`, `moderated`, `archived`, `deleted`) i zapewnia możliwość filtrowania po sprzedawcy. Endpoint wymaga uprawnień administratora i oferuje rozszerzone możliwości filtrowania, sortowania i paginacji.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/admin/offers`
- **Parametry**:
  - **Opcjonalne**:
    - `search` (string): Wyszukiwanie po tytule i opisie oferty (case-insensitive, partial match)
    - `category_id` (integer): Filtrowanie po ID kategorii
    - `seller_id` (UUID): Filtrowanie po ID sprzedawcy
    - `status` (string): Filtrowanie po statusie oferty (`active`, `inactive`, `sold`, `moderated`, `archived`, `deleted`)
    - `sort` (string): Kryterium sortowania (`price_asc`, `price_desc`, `created_at_desc`, `relevance` jeśli używane jest wyszukiwanie), domyślnie `created_at_desc`
    - `page` (integer, domyślnie 1): Numer strony dla paginacji
    - `limit` (integer, domyślnie 100, max 100): Liczba elementów na stronę
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **DTO**:
  - `OfferSummaryDTO`: Model reprezentujący podstawowe dane oferty
  - `OfferListResponse`: Model paginowanej odpowiedzi zawierającej listę ofert
  - `OfferStatus` (enum): Enum definiujący statusy ofert
  - `LogEventType` (enum): Enum definiujący typy zdarzeń logowania
- **Query Model**:
  - `AdminOfferListQueryParams`: Model walidujący parametry zapytania (search, category_id, seller_id, status, sort, page, limit)

## 4. Szczegóły odpowiedzi
- **Kod statusu**: 200 OK (sukces)
- **Struktura odpowiedzi**:
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
        "status": "active", // Może być dowolny status
        "created_at": "timestamp"
      },
      // ... inne oferty
    ],
    "total": 150,
    "page": 1,
    "limit": 100,
    "pages": 2
  }
  ```

- **Kody błędów**:
  - 400 Bad Request (`INVALID_QUERY_PARAM`): Nieprawidłowe parametry zapytania
  - 401 Unauthorized (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - 403 Forbidden (`INSUFFICIENT_PERMISSIONS`): Użytkownik nie ma uprawnień administratora
  - 500 Internal Server Error (`FETCH_FAILED`): Błąd serwera podczas pobierania danych

## 5. Przepływ danych
1. Żądanie trafia do routera API
2. Walidacja parametrów zapytania za pomocą modelu Pydantic
3. Sprawdzenie, czy użytkownik jest uwierzytelniony i ma rolę Admin
4. Wywołanie metody serwisu ofert do pobrania paginowanej listy
5. Serwis generuje zapytanie SQL z odpowiednimi filtrami:
   - Zastosowanie warunków WHERE dla category_id, seller_id i status, jeśli podano
   - Zastosowanie LIKE dla title i description, jeśli podano search
   - Zastosowanie ORDER BY na podstawie parametru sort
   - Zastosowanie LIMIT i OFFSET na podstawie parametrów paginacji
6. Wykonanie zapytania SQL i pobranie danych
7. Obliczenie całkowitej liczby ofert spełniających kryteria (do paginacji)
8. Transformacja danych do modelu odpowiedzi
9. Zwrócenie odpowiedzi JSON z kodem statusu 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: 
  - Wymagane uwierzytelnienie przez middleware sesji FastAPI
  - Sprawdzenie ważności sesji użytkownika przed wykonaniem operacji
- **Autoryzacja**:
  - Sprawdzenie, czy użytkownik ma rolę Admin przez dependency FastAPI
  - Użycie dekoratora `@Depends(require_admin)`
- **Walidacja danych**:
  - Walidacja parametrów zapytania przez model Pydantic
  - Sprawdzenie, czy status jest prawidłową wartością enum
  - Sprawdzenie, czy seller_id jest prawidłowym UUID
  - Ograniczenie wartości limit do maksymalnie 100
- **Ochrona danych**:
  - Logowanie dostępu administratora do listy ofert
  - Unikanie przekazywania zbyt szczegółowych danych w przypadku błędów

## 7. Obsługa błędów
- **Błędy walidacji**:
  - 400 Bad Request z kodem błędu `INVALID_QUERY_PARAM` i komunikatem "Invalid query parameter: [parameter_name]"
  - Szczegóły błędu wskazujące, który parametr jest nieprawidłowy i dlaczego
- **Błędy uwierzytelniania/autoryzacji**:
  - 401 Unauthorized z kodem błędu `NOT_AUTHENTICATED` i komunikatem "Authentication required"
  - 403 Forbidden z kodem błędu `INSUFFICIENT_PERMISSIONS` i komunikatem "Admin role required"
- **Błędy bazy danych**:
  - Przechwytywanie wyjątków DB i konwersja na 500 Internal Server Error
  - Kod błędu `FETCH_FAILED` z komunikatem "Failed to fetch offers"
  - Logowanie szczegółów błędu do systemu logowania z ukryciem wrażliwych danych
- **Nieoczekiwane błędy**:
  - Ogólny handler wyjątków zwracający 500 z komunikatem "An unexpected error occurred"
  - Logowanie szczegółów błędu do systemu logowania

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że kolumny używane do filtrowania są indeksowane (seller_id, category_id, status)
  - Indeksy dla kolumn używanych do wyszukiwania (title, description)
  - Indeksy dla kolumn używanych do sortowania (price, created_at)
- **Paginacja**:
  - Ograniczenie maksymalnej liczby elementów na stronę do 100
  - Optymalizacja zapytania COUNT() przez zastosowanie oddzielnych zapytań dla danych i liczby rekordów
- **Optymalizacja zapytań**:
  - Używanie specyficznych warunków WHERE zamiast ogólnych LIKE, gdy to możliwe
  - Selektywne pobieranie tylko potrzebnych kolumn
- **Buforowanie**:
  - Rozważ implementację buforowania wyników zapytań dla często używanych filtrów
  - Zastosuj odpowiednią strategię unieważniania cache przy zmianach danych ofert
- **Asynchroniczność**:
  - Implementacja endpointu jako async dla lepszej wydajności operacji I/O-bound
  - Użycie asynchronicznych klientów bazy danych

## 9. Etapy wdrożenia
1. **Utworzenie modelu parametrów zapytania**:
   ```python
   class AdminOfferListQueryParams(BaseModel):
       search: Optional[str] = None
       category_id: Optional[int] = None
       seller_id: Optional[UUID] = None
       status: Optional[OfferStatus] = None
       sort: str = Field("created_at_desc", description="Sorting criteria")
       page: int = Field(1, gt=0, description="Page number")
       limit: int = Field(100, gt=0, le=100, description="Items per page")
       
       @validator('sort')
       def validate_sort(cls, v):
           allowed_values = ['price_asc', 'price_desc', 'created_at_desc', 'relevance']
           if v not in allowed_values:
               raise ValueError(f"Sort must be one of: {', '.join(allowed_values)}")
           return v
       
       class Config:
           schema_extra = {
               "example": {
                   "search": "laptop",
                   "category_id": 1,
                   "seller_id": "123e4567-e89b-12d3-a456-426614174000",
                   "status": "active",
                   "sort": "price_asc",
                   "page": 1,
                   "limit": 50
               }
           }
   ```

2. **Rozszerzenie OfferService o metodę do pobierania wszystkich ofert**:
   ```python
   class OfferService:
       def __init__(self, db: Database):
           self.db = db
       
       async def list_all_offers(
           self,
           search: Optional[str] = None,
           category_id: Optional[int] = None,
           seller_id: Optional[UUID] = None,
           status: Optional[OfferStatus] = None,
           sort: str = "created_at_desc",
           page: int = 1,
           limit: int = 100
       ) -> OfferListResponse:
           # Oblicz offset dla paginacji
           offset = (page - 1) * limit
           
           # Zbuduj zapytanie bazowe
           query_conditions = []
           query_params = {}
           
           # Dodaj warunki filtrowania
           if category_id:
               query_conditions.append("category_id = :category_id")
               query_params["category_id"] = category_id
               
           if seller_id:
               query_conditions.append("seller_id = :seller_id")
               query_params["seller_id"] = seller_id
               
           if status:
               query_conditions.append("status = :status")
               query_params["status"] = status
               
           if search:
               search_condition = "(title ILIKE :search OR description ILIKE :search)"
               query_conditions.append(search_condition)
               query_params["search"] = f"%{search}%"
           
           # Zbuduj klauzulę WHERE
           where_clause = " AND ".join(query_conditions)
           if where_clause:
               where_clause = f"WHERE {where_clause}"
           
           # Określ sortowanie
           order_clause = ""
           if sort == "price_asc":
               order_clause = "ORDER BY price ASC"
           elif sort == "price_desc":
               order_clause = "ORDER BY price DESC"
           elif sort == "created_at_desc":
               order_clause = "ORDER BY created_at DESC"
           elif sort == "relevance" and search:
               # Prosta implementacja sortowania według trafności dla wyszukiwania
               # W rzeczywistości można użyć bardziej zaawansowanych technik pełnotekstowego wyszukiwania
               order_clause = "ORDER BY CASE WHEN title ILIKE :exact_title THEN 1 WHEN title ILIKE :start_title THEN 2 ELSE 3 END"
               query_params["exact_title"] = f"{search}"
               query_params["start_title"] = f"{search}%"
           else:
               # Domyślne sortowanie
               order_clause = "ORDER BY created_at DESC"
           
           # Zapytanie liczące całkowitą ilość pasujących rekordów
           count_query = f"""
           SELECT COUNT(*) as total
           FROM offers
           {where_clause}
           """
           
           # Zapytanie pobierające dane z paginacją
           data_query = f"""
           SELECT id, seller_id, category_id, title, price, image_filename, 
                  quantity, status, created_at
           FROM offers
           {where_clause}
           {order_clause}
           LIMIT :limit OFFSET :offset
           """
           
           # Dodaj parametry paginacji
           query_params["limit"] = limit
           query_params["offset"] = offset
           
           # Wykonaj zapytania
           async with self.db.transaction():
               total_result = await self.db.fetch_one(count_query, query_params)
               offers_data = await self.db.fetch_all(data_query, query_params)
           
           # Przetwórz wyniki
           total = total_result["total"] if total_result else 0
           offers = [OfferSummaryDTO(**offer) for offer in offers_data]
           
           # Oblicz całkowitą liczbę stron
           pages = (total + limit - 1) // limit if total > 0 else 0
           
           # Zwróć paginowaną odpowiedź
           return OfferListResponse(
               items=offers,
               total=total,
               page=page,
               limit=limit,
               pages=pages
           )
   ```

3. **Implementacja handlera endpointu**:
   ```python
   @router.get("/admin/offers", response_model=OfferListResponse)
   async def list_all_offers(
       query_params: AdminOfferListQueryParams = Depends(),
       current_user: UserDTO = Depends(require_admin),
       offer_service: OfferService = Depends(get_offer_service),
       log_service: LogService = Depends(get_log_service)
   ):
       try:
           # Loguj dostęp
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_OFFERS,
               user_id=current_user.id,
               message=f"Admin {current_user.email} accessed offer list"
           )
           
           # Pobierz listę ofert
           result = await offer_service.list_all_offers(
               search=query_params.search,
               category_id=query_params.category_id,
               seller_id=query_params.seller_id,
               status=query_params.status,
               sort=query_params.sort,
               page=query_params.page,
               limit=query_params.limit
           )
           
           return result
           
       except ValueError as e:
           # Obsługa błędów walidacji
           raise HTTPException(
               status_code=400,
               detail={
                   "error_code": "INVALID_QUERY_PARAM",
                   "message": str(e)
               }
           )
       except Exception as e:
           # Loguj błąd
           await log_service.create_log(
               event_type=LogEventType.ADMIN_LIST_OFFERS_FAIL,
               user_id=current_user.id,
               message=f"Failed to fetch offers: {str(e)}"
           )
           
           # Zwróć standardowy błąd
           raise HTTPException(
               status_code=500,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to fetch offers"
               }
           )
   ```

4. **Dodanie typów zdarzeń logowania (jeśli nie istnieją)**:
   ```python
   class LogEventType(str, Enum):
       # ... istniejące typy zdarzeń ...
       ADMIN_LIST_OFFERS = "ADMIN_LIST_OFFERS"
       ADMIN_LIST_OFFERS_FAIL = "ADMIN_LIST_OFFERS_FAIL"
   ```

5. **Dodanie endpointu do routera admin**:
   ```python
   # Upewnij się, że router admin jest poprawnie skonfigurowany
   admin_router = APIRouter(prefix="/admin", tags=["admin"])
   
   # Dodanie endpointu do routera
   admin_router.include_router(offer_router)
   
   # Dodanie routera do głównej aplikacji
   app.include_router(admin_router)
   ```

6. **Dodanie dokumentacji Swagger**:
   ```python
   @router.get(
       "/admin/offers",
       response_model=OfferListResponse,
       summary="List all offers",
       description="Retrieves a paginated list of all offers regardless of status. Requires Admin role.",
       responses={
           200: {"description": "Successful response with paginated offer list"},
           400: {"description": "Invalid query parameters"},
           401: {"description": "User not authenticated"},
           403: {"description": "User does not have Admin role"},
           500: {"description": "Server error while fetching data"}
       }
   )
   ```

7. **Implementacja testów jednostkowych**:
   - Testy dla OfferService.list_all_offers:
     - Test filtrowania po różnych parametrach
     - Test sortowania
     - Test paginacji
   - Testy dla AdminOfferListQueryParams:
     - Test walidacji parametrów
     - Test wartości domyślnych
   - Testy dla handlera list_all_offers:
     - Test autoryzacji (tylko Admin)
     - Test poprawnego zwracania odpowiedzi

8. **Implementacja testów integracyjnych**:
   - Test całego flow endpointu z różnymi parametrami filtrowania
   - Test scenariuszy błędów (nieprawidłowe parametry, brak uprawnień)
   - Test paginacji i jej limitów 