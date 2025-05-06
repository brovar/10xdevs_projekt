# API Endpoint Implementation Plan: List Categories

## 1. Przegląd punktu końcowego
Endpoint służy do pobierania listy wszystkich dostępnych kategorii produktów w systemie. Endpoint wymaga uwierzytelnienia i zwraca prostą listę kategorii zawierającą ich identyfikatory oraz nazwy. Kategorie są używane do klasyfikacji ofert w systemie.

## 2. Szczegóły żądania
- Metoda HTTP: `GET`
- Struktura URL: `/categories`
- Parametry: Brak parametrów
- Request Body: Brak ciała żądania

## 3. Wykorzystywane typy
- **CategoryDTO** (istniejący w `types.py`): Model reprezentujący kategorię z polami `id` (int) i `name` (str)
- **CategoriesListResponse** (istniejący w `types.py`): Model zawierający pole `items` - listę obiektów `CategoryDTO`

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Format odpowiedzi:
```json
{
  "items": [
    { "id": 1, "name": "Electronics" },
    { "id": 2, "name": "Books" },
    // ... do 20 kategorii
  ]
}
```
- Kody błędów:
  - `401 Unauthorized` (`NOT_AUTHENTICATED`): Użytkownik nie jest uwierzytelniony
  - `500 Internal Server Error` (`FETCH_FAILED`): Wystąpił błąd przy próbie pobrania danych

## 5. Przepływ danych
1. Otrzymanie żądania GET od uwierzytelnionego użytkownika
2. Walidacja sesji użytkownika (zależność FastAPI)
3. Wywołanie metody serwisu kategorii do pobrania wszystkich aktywnych kategorii
4. Transformacja wyników zapytania do modelu odpowiedzi
5. Zwrócenie poprawnie sformatowanej odpowiedzi

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint wymaga uwierzytelnienia poprzez sesję użytkownika
- **Autoryzacja**: Każdy uwierzytelniony użytkownik (Buyer, Seller, Admin) ma dostęp do listy kategorii
- **Walidacja danych**: Brak danych wejściowych do walidacji
- **Logowanie**: Każde wywołanie endpointu powinno być logowane dla celów audytowych

## 7. Obsługa błędów
- **NOT_AUTHENTICATED (401)**: Kiedy użytkownik nie jest uwierzytelniony
  ```json
  {
    "error_code": "NOT_AUTHENTICATED",
    "message": "Authentication required to access this resource"
  }
  ```

- **FETCH_FAILED (500)**: Kiedy wystąpi błąd podczas pobierania danych z bazy
  ```json
  {
    "error_code": "FETCH_FAILED",
    "message": "Failed to retrieve category data"
  }
  ```

## 8. Rozważania dotyczące wydajności
- Dane kategorii zmieniają się rzadko, więc można zastosować cachowanie:
  - Implementacja pamięci podręcznej na poziomie aplikacji (np. Redis)
  - Ustawienie nagłówków cache HTTP dla odpowiedzi
- Dane są niewielkie (do 20 kategorii), więc nie ma potrzeby implementacji paginacji
- Użycie odpowiednich indeksów w bazie danych (są już zdefiniowane w planie bazy danych)

## 9. Etapy wdrożenia

1. **Utworzenie serwisu kategorii**:
   ```python
   # services/category_service.py
   from typing import List
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   
   from database import get_db
   from models.category import Category
   from types import CategoryDTO
   
   class CategoryService:
       def __init__(self, db: AsyncSession = Depends(get_db)):
           self.db = db
       
       async def get_all_categories(self) -> List[CategoryDTO]:
           """Fetch all categories from the database"""
           query = select(Category).order_by(Category.id)
           result = await self.db.execute(query)
           categories = result.scalars().all()
           
           return [CategoryDTO(id=cat.id, name=cat.name) for cat in categories]
   ```

2. **Implementacja modelu bazodanowego** (jeśli jeszcze nie istnieje):
   ```python
   # models/category.py
   from sqlalchemy import Column, BigInteger, String
   from database import Base
   
   class Category(Base):
       __tablename__ = "categories"
       
       id = Column(BigInteger, primary_key=True)
       name = Column(String(100), unique=True, nullable=False)
   ```

3. **Implementacja zależności autoryzacyjnej**:
   ```python
   # dependencies.py
   from fastapi import Depends, HTTPException, status
   from fastapi.security import SessionCookie
   
   from services.auth_service import AuthService
   
   session_cookie = SessionCookie(name="session")
   
   async def require_authenticated_user(
       session_id: str = Depends(session_cookie),
       auth_service: AuthService = Depends()
   ):
       if not session_id:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail={
                   "error_code": "NOT_AUTHENTICATED",
                   "message": "Authentication required to access this resource"
               }
           )
       
       user = await auth_service.get_user_by_session(session_id)
       if not user:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail={
                   "error_code": "NOT_AUTHENTICATED",
                   "message": "Authentication required to access this resource"
               }
           )
       
       return user
   ```

4. **Implementacja routera kategorii**:
   ```python
   # routers/category_router.py
   from fastapi import APIRouter, Depends, HTTPException, status
   from typing import List
   
   from dependencies import require_authenticated_user
   from services.category_service import CategoryService
   from types import CategoryDTO, CategoriesListResponse
   from services.log_service import LogService
   
   router = APIRouter(
       prefix="/categories",
       tags=["categories"],
       dependencies=[Depends(require_authenticated_user)]
   )
   
   @router.get(
       "",
       response_model=CategoriesListResponse,
       status_code=status.HTTP_200_OK
   )
   async def list_categories(
       category_service: CategoryService = Depends(),
       log_service: LogService = Depends(),
       user = Depends(require_authenticated_user)
   ):
       try:
           categories = await category_service.get_all_categories()
           await log_service.log_event(
               user_id=user.id,
               event_type="CATEGORY_LIST_VIEWED",
               message=f"User {user.email} viewed categories list"
           )
           return CategoriesListResponse(items=categories)
       except Exception as e:
           await log_service.log_error(
               user_id=user.id,
               error_message=str(e),
               endpoint="/categories"
           )
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "FETCH_FAILED",
                   "message": "Failed to retrieve category data"
               }
           )
   ```

5. **Rejestracja routera w głównej aplikacji**:
   ```python
   # main.py (dołącz poniższe do istniejącej konfiguracji)
   from routers import category_router
   
   app.include_router(category_router.router)
   ```

6. **Implementacja mechanizmu cachowania** (opcjonalnie):
   ```python
   # middleware.py
   from fastapi import Request, Response
   from datetime import datetime, timedelta
   
   async def add_cache_headers(request: Request, call_next):
       response = await call_next(request)
       
       # Apply caching only to the categories endpoint
       if request.url.path == "/categories" and request.method == "GET":
           # Cache for 1 hour
           expires = datetime.utcnow() + timedelta(hours=1)
           response.headers["Cache-Control"] = "public, max-age=3600"
           response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
       
       return response
   
   # W main.py dodaj:
   from middleware import add_cache_headers
   
   app.middleware("http")(add_cache_headers)
   ```

7. **Testy jednostkowe**:
   ```python
   # tests/test_category_endpoint.py
   import pytest
   from fastapi.testclient import TestClient
   from unittest.mock import patch, MagicMock
   
   from main import app
   
   client = TestClient(app)
   
   @pytest.fixture
   def mock_auth():
       with patch("dependencies.require_authenticated_user") as mock:
           mock.return_value = MagicMock(id="user-id", email="test@example.com")
           yield mock
   
   @pytest.fixture
   def mock_category_service():
       with patch("services.category_service.CategoryService.get_all_categories") as mock:
           mock.return_value = [
               {"id": 1, "name": "Electronics"},
               {"id": 2, "name": "Books"}
           ]
           yield mock
   
   def test_list_categories_success(mock_auth, mock_category_service):
       response = client.get("/categories")
       assert response.status_code == 200
       assert "items" in response.json()
       assert len(response.json()["items"]) == 2
   
   def test_list_categories_unauthorized():
       response = client.get("/categories")  # Bez mockowania autoryzacji
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   def test_list_categories_error(mock_auth):
       with patch("services.category_service.CategoryService.get_all_categories") as mock:
           mock.side_effect = Exception("Database error")
           response = client.get("/categories")
           assert response.status_code == 500
           assert response.json()["error_code"] == "FETCH_FAILED"
   ```

8. **Dokumentacja API**:
   - Dodaj do głównej dokumentacji Swagger/OpenAPI opis endpointu i wymagań autoryzacyjnych
   - Upewnij się, że przykładowa odpowiedź jest zawarta w dokumentacji 