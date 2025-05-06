# API Endpoint Implementation Plan: Get Offer Image

## 1. Przegląd punktu końcowego
Endpoint `/media/offers/{offer_id}/{filename}` z metodą GET służy do pobierania plików obrazów przypisanych do ofert. Zapewnia dostęp do zasobów statycznych przechowywanych w systemie plików serwera. Dla ofert o statusie 'active' dostęp jest publiczny i nie wymaga uwierzytelnienia. Dla ofert o innym statusie (np. 'inactive', 'moderated') dostęp jest ograniczony do właściciela oferty (sprzedawcy) oraz administratorów. Endpoint zwraca plik obrazu w formacie PNG z odpowiednimi nagłówkami HTTP.

## 2. Szczegóły żądania
- Metoda HTTP: `GET`
- Struktura URL: `/media/offers/{offer_id}/{filename}`
- Parametry Path:
  - `offer_id` (UUID, wymagany): Identyfikator oferty, do której przypisany jest obraz
  - `filename` (string, wymagany): Nazwa pliku obrazu (np. "image.png")
- Format danych: Brak (żądanie nie zawiera treści)
- Nagłówki:
  - `Authorization` (opcjonalny): Token sesji/JWT, wymagany dla dostępu do obrazów ofert o statusie innym niż 'active'

## 3. Wykorzystywane typy
- **OfferStatus** (z types.py) - enum określający możliwe statusy oferty
- **UserRole** (z types.py) - enum określający role użytkowników
- Modele bazy danych:
  - **Offer** - reprezentacja tabeli `offers` w bazie danych dla weryfikacji istnienia oferty i jej statusu

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `200 OK`
- Response Body (sukces): Zawartość pliku obrazu w formacie binarnym
- Nagłówki odpowiedzi:
  - `Content-Type`: `image/png`
  - `Content-Disposition`: `inline; filename="[nazwa_pliku]"`
  - `Cache-Control`: `public, max-age=3600` (dla ofert aktywnych)
- Kody błędów:
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia, gdy jest wymagane
  - `403 Forbidden` z kodami błędów:
    - `ACCESS_DENIED` - użytkownik nie ma uprawnień do obrazu nieaktywnej oferty
  - `404 Not Found` z kodami błędów:
    - `OFFER_NOT_FOUND` - oferta nie istnieje
    - `IMAGE_NOT_FOUND` - obraz nie istnieje
  - `500 Internal Server Error` z kodem błędu `FILE_SERVE_FAILED` - błąd podczas serwowania pliku

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Walidacja parametrów ścieżki (offer_id jako UUID, sanityzacja nazwy pliku)
3. Pobranie informacji o ofercie z bazy danych
4. Sprawdzenie czy oferta istnieje
5. Sprawdzenie statusu oferty:
   - Jeśli status to 'active', kontynuuj bez sprawdzania uwierzytelnienia
   - W przeciwnym razie sprawdź uwierzytelnienie i autoryzację użytkownika:
     - Czy użytkownik jest zalogowany
     - Czy użytkownik jest właścicielem oferty lub administratorem
6. Budowa ścieżki do pliku obrazu na serwerze
7. Sprawdzenie czy plik istnieje
8. Ustawienie odpowiednich nagłówków HTTP
9. Zwrócenie zawartości pliku jako odpowiedzi HTTP

## 6. Względy bezpieczeństwa
- **Walidacja ścieżki**:
  - Sanityzacja nazwy pliku (usunięcie znaków specjalnych, zapobieganie path traversal)
  - Weryfikacja formatu UUID dla offer_id
- **Kontrola dostępu**:
  - Publiczny dostęp tylko do obrazów aktywnych ofert
  - Dostęp do obrazów nieaktywnych ofert tylko dla właściciela lub administratora
  - Implementacja uwierzytelniania dla zasobów wymagających autoryzacji
- **Serwowanie plików**:
  - Używanie bezpiecznych metod serwowania plików (np. `aiofiles`)
  - Ustawianie poprawnych typów MIME
  - Ograniczenie dostępu tylko do katalogu z obrazami ofert
- **Ochrona przed atakami**:
  - Zabezpieczenie przed atakami path traversal
  - Weryfikacja, czy żądany plik jest rzeczywiście w dozwolonym katalogu
  - Weryfikacja, czy plik należy do wskazanej oferty (zgodność offer_id i nazwy pliku)
- **Cache**:
  - Ustawienie nagłówków cache dla optymalizacji pobierania często używanych obrazów
  - Różne polityki cache dla różnych statusów oferty

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowy format offer_id: `400 Bad Request` z kodem `INVALID_OFFER_ID`
  - Nieprawidłowa nazwa pliku: `400 Bad Request` z kodem `INVALID_FILENAME`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia gdy wymagane: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Brak uprawnień do zasobu: `403 Forbidden` z kodem `ACCESS_DENIED`
- **Błędy biznesowe**:
  - Oferta nie istnieje: `404 Not Found` z kodem `OFFER_NOT_FOUND`
  - Obraz nie istnieje: `404 Not Found` z kodem `IMAGE_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z odczytem pliku: `500 Internal Server Error` z kodem `FILE_SERVE_FAILED`
  - Logowanie szczegółów błędów wewnętrznie, bez ujawniania ich użytkownikowi

## 8. Rozważania dotyczące wydajności
- **Cachowanie**:
  - Ustawienie nagłówków HTTP Cache-Control dla przeglądarek i proxy
  - Rozważenie użycia CDN dla często pobieranych obrazów
- **Optymalizacja plików**:
  - Przechowywanie obrazów w zoptymalizowanym formacie
  - Możliwość generowania miniatur na żądanie (opcjonalny parametr `size`)
- **Serwowanie asynchroniczne**:
  - Użycie asynchronicznych operacji I/O dla odczytu plików
  - Buforowanie małych plików w pamięci (opcjonalnie)
- **Ograniczenia**:
  - Rate limiting dla zapobiegania nadużyciom (ograniczenie liczby żądań)
  - Limity rozmiaru plików

## 9. Etapy wdrożenia

1. **Utworzenie konfiguracji dla ścieżek przechowywania mediów**:
   ```python
   # config.py
   from pathlib import Path
   
   # Bazowa ścieżka dla mediów
   MEDIA_ROOT = Path("./media")
   
   # Ścieżka dla obrazów ofert
   OFFER_IMAGES_DIR = MEDIA_ROOT / "offers"
   
   # Upewnienie się, że katalogi istnieją
   MEDIA_ROOT.mkdir(exist_ok=True)
   OFFER_IMAGES_DIR.mkdir(exist_ok=True)
   ```

2. **Utworzenie serwisu do obsługi mediów**:
   ```python
   from fastapi import HTTPException, status
   from pathlib import Path
   import aiofiles
   import os
   import uuid
   from typing import Optional
   from logging import Logger
   
   from src.config import OFFER_IMAGES_DIR
   from src.db.models import Offer
   from src.types import OfferStatus, UserRole
   
   class MediaService:
       def __init__(self, logger: Logger):
           self.logger = logger
       
       async def get_offer_image_path(
           self,
           offer_id: uuid.UUID,
           filename: str,
           offer: Optional[Offer] = None
       ) -> Path:
           """
           Validate and return the path to an offer image file
           
           Args:
               offer_id: UUID of the offer
               filename: Name of the image file
               offer: Optional Offer object if already fetched
               
           Returns:
               Path object pointing to the image file
               
           Raises:
               HTTPException: If the path is invalid or file doesn't exist
           """
           # Sanitize filename to prevent path traversal
           safe_filename = os.path.basename(filename)
           
           # Ensure filename doesn't start with dots or contain suspicious patterns
           if safe_filename != filename or ".." in filename or filename.startswith("."):
               self.logger.warning(f"Attempted path traversal: {filename}")
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail={
                       "error_code": "INVALID_FILENAME",
                       "message": "Invalid filename"
                   }
               )
           
           # Construct file path
           file_path = OFFER_IMAGES_DIR / str(offer_id) / safe_filename
           
           # Check if file exists
           if not file_path.exists() or not file_path.is_file():
               self.logger.info(f"Image not found: {file_path}")
               raise HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail={
                       "error_code": "IMAGE_NOT_FOUND",
                       "message": "Image file not found"
                   }
               )
           
           return file_path
       
       async def check_offer_image_access(
           self,
           offer: Offer,
           current_user_id: Optional[uuid.UUID] = None,
           current_user_role: Optional[UserRole] = None
       ) -> bool:
           """
           Check if user has access to the offer image
           
           Args:
               offer: The offer object
               current_user_id: Optional UUID of the current user
               current_user_role: Optional role of the current user
               
           Returns:
               True if access is allowed, otherwise raises HTTPException
               
           Raises:
               HTTPException: If access is denied
           """
           # Public access for active offers
           if offer.status == OfferStatus.ACTIVE:
               return True
           
           # For non-active offers, user must be authenticated
           if current_user_id is None:
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail={
                       "error_code": "NOT_AUTHENTICATED",
                       "message": "Authentication required to access this image"
                   }
               )
           
           # Admin has access to all images
           if current_user_role == UserRole.ADMIN:
               return True
           
           # Seller has access to their own offers' images
           if offer.seller_id == current_user_id:
               return True
           
           # Access denied for all other cases
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail={
                   "error_code": "ACCESS_DENIED",
                   "message": "You don't have permission to access this image"
               }
           )
       
       async def read_image_file(self, file_path: Path) -> bytes:
           """
           Read image file asynchronously
           
           Args:
               file_path: Path to the image file
               
           Returns:
               File content as bytes
               
           Raises:
               HTTPException: If file reading fails
           """
           try:
               async with aiofiles.open(file_path, "rb") as file:
                   return await file.read()
           except Exception as e:
               self.logger.error(f"Error reading file {file_path}: {str(e)}")
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "FILE_SERVE_FAILED",
                       "message": "Failed to serve the image file"
                   }
               )
   ```

3. **Utworzenie kontrolera (routera) dla serwowania obrazów ofert**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
   from fastapi.responses import FileResponse
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from typing import Optional
   from logging import Logger
   
   from src.db.session import get_async_session
   from src.db.models import Offer
   from src.services.media_service import MediaService
   from src.services.auth import get_current_user_optional
   from src.types import UserRole
   
   router = APIRouter(prefix="/media", tags=["media"])
   
   @router.get("/offers/{offer_id}/{filename}")
   async def get_offer_image(
       offer_id: UUID = Path(..., description="UUID of the offer"),
       filename: str = Path(..., description="Filename of the image"),
       current_user = Depends(get_current_user_optional),
       db: AsyncSession = Depends(get_async_session),
       logger: Logger = Depends(get_logger),
       media_service: MediaService = Depends(lambda: MediaService(logger))
   ):
       """
       Get an image file associated with an offer.
       
       - Public access for 'active' offers
       - Restricted access for other offer statuses (owner, admin)
       - Returns the image file with appropriate headers
       """
       try:
           # Get offer from database
           offer = await db.get(Offer, offer_id)
           
           # Check if offer exists
           if not offer:
               raise HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail={
                       "error_code": "OFFER_NOT_FOUND",
                       "message": "Offer not found"
                   }
               )
           
           # Extract user information if authenticated
           current_user_id = current_user.id if current_user else None
           current_user_role = current_user.role if current_user else None
           
           # Check access permission
           await media_service.check_offer_image_access(
               offer,
               current_user_id,
               current_user_role
           )
           
           # Get validated file path
           file_path = await media_service.get_offer_image_path(
               offer_id,
               filename,
               offer
           )
           
           # Set cache control based on offer status
           cache_control = "public, max-age=3600" if offer.status == OfferStatus.ACTIVE else "no-store"
           
           # Return file response with appropriate headers
           return FileResponse(
               path=str(file_path),
               media_type="image/png",
               filename=filename,
               content_disposition_type="inline",
               headers={"Cache-Control": cache_control}
           )
           
       except HTTPException:
           # Re-raise HTTP exceptions (already handled in service)
           raise
       except Exception as e:
           # Log unexpected errors
           logger.error(f"Unexpected error in get_offer_image endpoint: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error_code": "FILE_SERVE_FAILED",
                   "message": "An unexpected error occurred"
               }
           )
   ```

4. **Utworzenie funkcji pomocniczej do autoryzacji opcjonalnej**:
   ```python
   # Dodać do src/services/auth.py
   
   async def get_current_user_optional(
       request: Request,
       db: AsyncSession = Depends(get_async_session)
   ):
       """
       Similar to get_current_user but returns None instead of raising an exception
       if no user is authenticated
       """
       try:
           return await get_current_user(request, db)
       except HTTPException:
           return None
   ```

5. **Utworzenie testów jednostkowych dla MediaService**:
   ```python
   import pytest
   from unittest.mock import MagicMock, AsyncMock, patch, mock_open
   from pathlib import Path
   from uuid import UUID
   from fastapi import HTTPException
   
   from src.services.media_service import MediaService
   from src.types import OfferStatus, UserRole
   
   @pytest.fixture
   def logger():
       return MagicMock()
   
   @pytest.fixture
   def media_service(logger):
       return MediaService(logger)
   
   @pytest.fixture
   def sample_offer():
       mock_offer = MagicMock()
       mock_offer.id = UUID("12345678-1234-5678-1234-567812345678")
       mock_offer.seller_id = UUID("87654321-8765-4321-8765-432187654321")
       mock_offer.status = OfferStatus.ACTIVE
       return mock_offer
   
   @pytest.mark.asyncio
   async def test_get_offer_image_path_success(media_service):
       # Setup
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       filename = "image.png"
       
       # Mock Path.exists and Path.is_file to return True
       with patch.object(Path, 'exists', return_value=True), \
            patch.object(Path, 'is_file', return_value=True):
           
           # Execute test
           result = await media_service.get_offer_image_path(offer_id, filename)
           
           # Verify
           assert isinstance(result, Path)
           assert str(offer_id) in str(result)
           assert filename in str(result)
   
   @pytest.mark.asyncio
   async def test_get_offer_image_path_not_found(media_service):
       # Setup
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       filename = "missing.png"
       
       # Mock Path.exists to return False
       with patch.object(Path, 'exists', return_value=False):
           
           # Test and verify
           with pytest.raises(HTTPException) as exc_info:
               await media_service.get_offer_image_path(offer_id, filename)
               
           assert exc_info.value.status_code == 404
           assert exc_info.value.detail["error_code"] == "IMAGE_NOT_FOUND"
   
   @pytest.mark.asyncio
   async def test_get_offer_image_path_invalid_filename(media_service):
       # Setup
       offer_id = UUID("12345678-1234-5678-1234-567812345678")
       filename = "../../../etc/passwd"  # Path traversal attempt
       
       # Test and verify
       with pytest.raises(HTTPException) as exc_info:
           await media_service.get_offer_image_path(offer_id, filename)
           
       assert exc_info.value.status_code == 400
       assert exc_info.value.detail["error_code"] == "INVALID_FILENAME"
   
   @pytest.mark.asyncio
   async def test_check_offer_image_access_active_offer(media_service, sample_offer):
       # Active offers are accessible without authentication
       sample_offer.status = OfferStatus.ACTIVE
       result = await media_service.check_offer_image_access(sample_offer)
       assert result is True
   
   @pytest.mark.asyncio
   async def test_check_offer_image_access_inactive_offer_no_auth(media_service, sample_offer):
       # Inactive offers require authentication
       sample_offer.status = OfferStatus.INACTIVE
       with pytest.raises(HTTPException) as exc_info:
           await media_service.check_offer_image_access(sample_offer)
           
       assert exc_info.value.status_code == 401
       assert exc_info.value.detail["error_code"] == "NOT_AUTHENTICATED"
   
   @pytest.mark.asyncio
   async def test_check_offer_image_access_inactive_offer_owner(media_service, sample_offer):
       # Owner has access to inactive offers
       sample_offer.status = OfferStatus.INACTIVE
       seller_id = sample_offer.seller_id
       
       result = await media_service.check_offer_image_access(
           sample_offer, 
           current_user_id=seller_id, 
           current_user_role=UserRole.SELLER
       )
       
       assert result is True
   
   @pytest.mark.asyncio
   async def test_check_offer_image_access_inactive_offer_admin(media_service, sample_offer):
       # Admin has access to all offers
       sample_offer.status = OfferStatus.INACTIVE
       admin_id = UUID("11111111-1111-1111-1111-111111111111")  # Different from seller_id
       
       result = await media_service.check_offer_image_access(
           sample_offer, 
           current_user_id=admin_id, 
           current_user_role=UserRole.ADMIN
       )
       
       assert result is True
   
   @pytest.mark.asyncio
   async def test_check_offer_image_access_inactive_offer_not_owner(media_service, sample_offer):
       # Non-owners cannot access inactive offers
       sample_offer.status = OfferStatus.INACTIVE
       other_user_id = UUID("99999999-9999-9999-9999-999999999999")  # Different from seller_id
       
       with pytest.raises(HTTPException) as exc_info:
           await media_service.check_offer_image_access(
               sample_offer, 
               current_user_id=other_user_id, 
               current_user_role=UserRole.SELLER
           )
           
       assert exc_info.value.status_code == 403
       assert exc_info.value.detail["error_code"] == "ACCESS_DENIED"
   
   @pytest.mark.asyncio
   async def test_read_image_file_success(media_service):
       # Setup
       file_path = Path("test/path/image.png")
       file_content = b"binary image data"
       
       # Mock aiofiles.open
       mock_file = AsyncMock()
       mock_file.__aenter__.return_value.read = AsyncMock(return_value=file_content)
       
       with patch('aiofiles.open', return_value=mock_file):
           # Execute test
           result = await media_service.read_image_file(file_path)
           
           # Verify
           assert result == file_content
   
   @pytest.mark.asyncio
   async def test_read_image_file_error(media_service):
       # Setup
       file_path = Path("test/path/image.png")
       
       # Mock aiofiles.open to raise an exception
       with patch('aiofiles.open', side_effect=Exception("File read error")):
           # Test and verify
           with pytest.raises(HTTPException) as exc_info:
               await media_service.read_image_file(file_path)
               
           assert exc_info.value.status_code == 500
           assert exc_info.value.detail["error_code"] == "FILE_SERVE_FAILED"
   ```

6. **Utworzenie testów integracyjnych dla endpointu GET /media/offers/{offer_id}/{filename}**:
   ```python
   from fastapi.testclient import TestClient
   import pytest
   from unittest.mock import patch, MagicMock
   from pathlib import Path
   
   from main import app
   from src.types import UserRole, OfferStatus
   
   client = TestClient(app)
   
   @patch("src.db.session.get_async_session")
   @patch("src.services.media_service.MediaService.get_offer_image_path")
   def test_get_offer_image_active_offer_success(mock_get_path, mock_session):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       filename = "image.png"
       file_path = Path(f"/tmp/media/offers/{offer_id}/{filename}")
       
       # Mock offer (active status)
       mock_offer = MagicMock()
       mock_offer.status = OfferStatus.ACTIVE
       
       # Mock session to return the offer
       mock_session.return_value.__aenter__.return_value.get.return_value = mock_offer
       
       # Mock get_offer_image_path
       mock_get_path.return_value = file_path
       
       # Mock FileResponse to avoid actual file handling
       with patch("fastapi.responses.FileResponse", return_value=MagicMock()) as mock_file_response:
           # Test request
           response = client.get(f"/media/offers/{offer_id}/{filename}")
           
           # Verify
           assert response.status_code == 200
           mock_file_response.assert_called_once()
           assert "Cache-Control" in mock_file_response.call_args[1]["headers"]
           assert "max-age=3600" in mock_file_response.call_args[1]["headers"]["Cache-Control"]
   
   @patch("src.db.session.get_async_session")
   def test_get_offer_image_not_found(mock_session):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       filename = "image.png"
       
       # Mock session to return None (offer not found)
       mock_session.return_value.__aenter__.return_value.get.return_value = None
       
       # Test request
       response = client.get(f"/media/offers/{offer_id}/{filename}")
       
       # Verify
       assert response.status_code == 404
       assert response.json()["error_code"] == "OFFER_NOT_FOUND"
   
   @patch("src.db.session.get_async_session")
   @patch("src.services.auth.get_current_user_optional")
   def test_get_offer_image_inactive_offer_unauthorized(mock_get_user, mock_session):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       filename = "image.png"
       
       # Mock offer (inactive status)
       mock_offer = MagicMock()
       mock_offer.status = OfferStatus.INACTIVE
       
       # Mock session to return the offer
       mock_session.return_value.__aenter__.return_value.get.return_value = mock_offer
       
       # Mock no user authenticated
       mock_get_user.return_value = None
       
       # Test request
       response = client.get(f"/media/offers/{offer_id}/{filename}")
       
       # Verify
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.db.session.get_async_session")
   @patch("src.services.auth.get_current_user_optional")
   @patch("src.services.media_service.MediaService.get_offer_image_path")
   def test_get_offer_image_inactive_offer_authorized_owner(mock_get_path, mock_get_user, mock_session):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       seller_id = "87654321-8765-4321-8765-432187654321"
       filename = "image.png"
       file_path = Path(f"/tmp/media/offers/{offer_id}/{filename}")
       
       # Mock offer (inactive status)
       mock_offer = MagicMock()
       mock_offer.status = OfferStatus.INACTIVE
       mock_offer.seller_id = seller_id
       
       # Mock session to return the offer
       mock_session.return_value.__aenter__.return_value.get.return_value = mock_offer
       
       # Mock authenticated seller (owner)
       mock_get_user.return_value = MagicMock(id=seller_id, role=UserRole.SELLER)
       
       # Mock get_offer_image_path
       mock_get_path.return_value = file_path
       
       # Mock FileResponse
       with patch("fastapi.responses.FileResponse", return_value=MagicMock()) as mock_file_response:
           # Test request
           response = client.get(f"/media/offers/{offer_id}/{filename}")
           
           # Verify
           assert response.status_code == 200
           mock_file_response.assert_called_once()
           assert "Cache-Control" in mock_file_response.call_args[1]["headers"]
           assert "no-store" in mock_file_response.call_args[1]["headers"]["Cache-Control"]
   
   @patch("src.db.session.get_async_session")
   @patch("src.services.auth.get_current_user_optional")
   def test_get_offer_image_inactive_offer_other_user(mock_get_user, mock_session):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       seller_id = "87654321-8765-4321-8765-432187654321"
       other_user_id = "99999999-9999-9999-9999-999999999999"
       filename = "image.png"
       
       # Mock offer (inactive status)
       mock_offer = MagicMock()
       mock_offer.status = OfferStatus.INACTIVE
       mock_offer.seller_id = seller_id
       
       # Mock session to return the offer
       mock_session.return_value.__aenter__.return_value.get.return_value = mock_offer
       
       # Mock authenticated user (not the owner)
       mock_get_user.return_value = MagicMock(id=other_user_id, role=UserRole.BUYER)
       
       # Test request
       response = client.get(f"/media/offers/{offer_id}/{filename}")
       
       # Verify
       assert response.status_code == 403
       assert response.json()["error_code"] == "ACCESS_DENIED"
   
   @patch("src.services.media_service.MediaService.get_offer_image_path")
   def test_image_not_found(mock_get_path):
       # Setup
       offer_id = "12345678-1234-5678-1234-567812345678"
       filename = "missing.png"
       
       # Mock get_offer_image_path to raise IMAGE_NOT_FOUND exception
       from fastapi import HTTPException
       mock_get_path.side_effect = HTTPException(
           status_code=404,
           detail={"error_code": "IMAGE_NOT_FOUND", "message": "Image file not found"}
       )
       
       # Test request
       response = client.get(f"/media/offers/{offer_id}/{filename}")
       
       # Verify
       assert response.status_code == 404
       assert response.json()["error_code"] == "IMAGE_NOT_FOUND"
   ```
