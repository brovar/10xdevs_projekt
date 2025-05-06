# API Endpoint Implementation Plan: Create Offer

## 1. Przegląd punktu końcowego
Endpoint `/offers` umożliwia sprzedawcom tworzenie nowych ofert produktów na platformie. Obsługuje przesyłanie danych oferty w formacie multipart/form-data, co pozwala na dołączenie pliku obrazu. Endpoint wykonuje walidację wszystkich pól, sprawdza istnienie kategorii, przetwarza plik obrazu (jeśli został dodany) i tworzy nowy rekord oferty w bazie danych. Wymaga uwierzytelnienia oraz roli Seller.

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/offers`
- Format danych: `multipart/form-data`
- Parametry: brak
- Pola formularza:
  ```
  title: string (wymagane) - tytuł oferty
  description: string (opcjonalne) - opis oferty
  price: string (wymagane) - cena produktu (reprezentacja wartości dziesiętnej)
  quantity: integer (domyślnie 1) - ilość dostępnych sztuk
  category_id: integer (wymagane) - identyfikator kategorii
  image: file (opcjonalne) - plik obrazu (obsługiwane formaty: PNG, JPEG, WebP)
  ```

## 3. Wykorzystywane typy
- **OfferSummaryDTO** (z types.py) - model odpowiedzi
- **OfferStatus** (z types.py) - enum określający status oferty
- **UserRole** (z types.py) - enum określający role użytkowników
- **LogEventType** (z types.py) - enum określający typy zdarzeń w logach
- Modele bazy danych:
  - **Offer** - reprezentacja tabeli `offers` w bazie danych
  - **Category** - reprezentacja tabeli `categories` w bazie danych
  - **User** - reprezentacja tabeli `users` w bazie danych

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `201 Created`
- Response Body (sukces):
  ```json
  {
    "id": "uuid-offer-id",
    "seller_id": "uuid-seller-id",
    "category_id": 1,
    "title": "Sample Product",
    "price": "99.99",
    "image_filename": "image.png",
    "quantity": 10,
    "status": "inactive",
    "created_at": "timestamp"
  }
  ```
- Kody błędów:
  - `400 Bad Request` z różnymi kodami błędów:
    - `INVALID_INPUT` - brakujące lub nieprawidłowe pola
    - `INVALID_FILE_TYPE` - nieprawidłowy format pliku
    - `FILE_TOO_LARGE` - zbyt duży plik
    - `INVALID_PRICE` - nieprawidłowa cena (musi być większa od 0)
    - `INVALID_QUANTITY` - nieprawidłowa ilość (nie może być ujemna)
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED` - brak uwierzytelnienia
  - `403 Forbidden` z kodem błędu `INSUFFICIENT_PERMISSIONS` - użytkownik nie jest sprzedawcą
  - `404 Not Found` z kodem błędu `CATEGORY_NOT_FOUND` - kategoria nie istnieje
  - `500 Internal Server Error` z kodami błędów:
    - `CREATE_FAILED` - błąd podczas tworzenia oferty w bazie danych
    - `FILE_UPLOAD_FAILED` - błąd podczas przesyłania pliku

## 5. Przepływ danych
1. Żądanie HTTP trafia do kontrolera FastAPI
2. Kontroler weryfikuje uwierzytelnienie użytkownika i sprawdza czy ma rolę Seller
3. Dane z formularza są walidowane (tytuł, cena, ilość, kategoria)
4. Kontroler sprawdza czy kategoria istnieje w bazie danych
5. Jeśli przesłano obraz:
   - Walidacja rozmiaru i typu pliku
   - Generowanie unikalnej nazwy pliku
   - Asynchroniczne zapisanie pliku na dysku (jako zadanie w tle)
6. Utworzenie nowego rekordu w tabeli `offers` ze statusem "inactive"
7. Zapisanie zdarzenia w tabeli `logs` (jako zadanie w tle)
8. Zwrócenie danych utworzonej oferty z kodem `201 Created`

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**:
  - Wymagane uwierzytelnienie przez token JWT
  - Kontrola dostępu oparta na rolach (RBAC) - tylko sprzedawcy mogą tworzyć oferty
- **Walidacja wejścia**:
  - Walidacja wszystkich pól formularza
  - Walidacja plików (typ, rozmiar)
- **Zapobieganie atakom**:
  - Ochrona przed SQL Injection przez użycie ORM
  - Ochrona przed XSS przez sanityzację danych wejściowych
  - Limit rozmiaru przesyłanych plików
  - Kontrola typów przesyłanych plików
- **Rate limiting**:
  - Ograniczenie liczby żądań z jednego IP w celu zapobiegania nadużyciom

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowe pola formularza: `400 Bad Request` z odpowiednim kodem błędu
  - Nieprawidłowy typ pliku: `400 Bad Request` z kodem `INVALID_FILE_TYPE`
  - Zbyt duży plik: `400 Bad Request` z kodem `FILE_TOO_LARGE`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: `401 Unauthorized` z kodem `NOT_AUTHENTICATED`
  - Niewystarczające uprawnienia: `403 Forbidden` z kodem `INSUFFICIENT_PERMISSIONS`
- **Błędy biznesowe**:
  - Kategoria nie istnieje: `404 Not Found` z kodem `CATEGORY_NOT_FOUND`
- **Błędy systemowe**:
  - Problemy z bazą danych: `500 Internal Server Error` z kodem `CREATE_FAILED`
  - Problemy z przesyłaniem pliku: `500 Internal Server Error` z kodem `FILE_UPLOAD_FAILED`

## 8. Rozważania dotyczące wydajności
- **Asynchroniczne przetwarzanie**:
  - Użycie async/await dla operacji I/O (dostęp do bazy danych, operacje na plikach)
  - Wykorzystanie zadań w tle (background tasks) dla przetwarzania obrazów
- **Obsługa plików**:
  - Asynchroniczny zapis plików na dysku
  - Optymalizacja obrazów (kompresja, zmiana rozmiaru) jako zadanie w tle
- **Baza danych**:
  - Transakcje bazodanowe dla zapewnienia atomowości operacji
  - Indeksacja odpowiednich kolumn w tabeli `offers`
- **Skalowanie**:
  - Możliwość integracji z CDN dla przechowywania obrazów
  - Cachowanie informacji o kategoriach

## 9. Etapy wdrożenia

1. **Utworzenie kontrolera ofert**:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
   from fastapi.security import OAuth2PasswordBearer
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID, uuid4
   from decimal import Decimal
   from typing import Optional
   import os
   import aiofiles
   from PIL import Image
   import io

   from src.types import OfferSummaryDTO, UserRole, LogEventType, OfferStatus
   from src.db.models import Offer, Category, User
   from src.db.session import get_async_session
   from src.services.auth import get_current_user
   from src.services.logging import log_event

   router = APIRouter(prefix="/offers", tags=["offers"])

   # Constants
   ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
   MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
   UPLOAD_DIR = "uploads/offers"

   # Ensure upload directory exists
   os.makedirs(UPLOAD_DIR, exist_ok=True)

   @router.post("/", status_code=status.HTTP_201_CREATED, response_model=OfferSummaryDTO)
   async def create_offer(
       background_tasks: BackgroundTasks,
       title: str = Form(...),
       price: Decimal = Form(...),
       quantity: int = Form(1),
       category_id: int = Form(...),
       description: Optional[str] = Form(None),
       image: Optional[UploadFile] = File(None),
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session)
   ):
       """
       Create a new offer (product listing).
       - Requires Seller role
       - Accepts multipart/form-data with optional image upload
       - Returns the created offer details
       """
       # Verify seller role
       if current_user.role != UserRole.SELLER:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only sellers can create offers"}
           )
       
       # Validate price
       if price <= 0:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail={"error_code": "INVALID_PRICE", "message": "Price must be greater than 0"}
           )
       
       # Validate quantity
       if quantity < 0:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail={"error_code": "INVALID_QUANTITY", "message": "Quantity cannot be negative"}
           )
       
       try:
           # Verify category exists
           category = await db.get(Category, category_id)
           if not category:
               raise HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail={"error_code": "CATEGORY_NOT_FOUND", "message": "Category not found"}
               )
           
           # Process image if provided
           image_filename = None
           if image:
               # Validate image size
               content = await image.read()
               if len(content) > MAX_IMAGE_SIZE:
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail={"error_code": "FILE_TOO_LARGE", "message": "Image size exceeds the 5MB limit"}
                   )
               
               # Validate image type
               if image.content_type not in ALLOWED_IMAGE_TYPES:
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail={"error_code": "INVALID_FILE_TYPE", "message": "Unsupported image format. Use JPG, PNG or WebP"}
                   )
               
               # Generate unique filename
               ext = image.filename.split('.')[-1]
               image_filename = f"{uuid4()}.{ext}"
               
               # Reset file cursor
               await image.seek(0)
               
               # Save image asynchronously using background task
               image_path = os.path.join(UPLOAD_DIR, image_filename)
               background_tasks.add_task(save_image, image_path, content)
           
           # Create offer in database
           new_offer = Offer(
               seller_id=current_user.id,
               category_id=category_id,
               title=title,
               description=description,
               price=price,
               quantity=quantity,
               image_filename=image_filename,
               status=OfferStatus.INACTIVE  # Default status is inactive
           )
           
           db.add(new_offer)
           await db.commit()
           await db.refresh(new_offer)
           
           # Log event using background task
           background_tasks.add_task(
               log_event,
               db,
               LogEventType.OFFER_CREATE,
               current_user.id,
               f"Offer created: {new_offer.id}"
           )
           
           return OfferSummaryDTO.from_orm(new_offer)
           
       except HTTPException:
           # Re-raise HTTP exceptions as they already have the proper format
           raise
       except Exception as e:
           # Log the error
           print(f"Error creating offer: {str(e)}")
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={"error_code": "CREATE_FAILED", "message": "Failed to create offer"}
           )
   ```

2. **Implementacja funkcji pomocniczej do zapisywania obrazów**:
   ```python
   async def save_image(path: str, contents: bytes):
       """Save image to file system asynchronously"""
       try:
           # Save original file
           async with aiofiles.open(path, 'wb') as f:
               await f.write(contents)
           
           # Optionally process/resize image
           try:
               img = Image.open(io.BytesIO(contents))
               # Resize logic here if needed
               # For example: img = img.resize((800, 600), Image.LANCZOS)
               img.save(path, optimize=True)
           except Exception as e:
               # Log error but don't fail the request
               print(f"Error processing image: {str(e)}")
       except Exception as e:
           # Log file save error
           print(f"Error saving image: {str(e)}")
   ```

3. **Implementacja usługi logowania zdarzeń** (jeśli jeszcze nie istnieje):
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   from src.db.models import Log
   from src.types import LogEventType

   async def log_event(
       db: AsyncSession,
       event_type: LogEventType,
       user_id: UUID = None,
       message: str = "",
       ip_address: str = None
   ):
       """Create a log entry for application events"""
       try:
           log_entry = Log(
               event_type=event_type,
               user_id=user_id,
               ip_address=ip_address,
               message=message
           )
           db.add(log_entry)
           await db.commit()
       except Exception as e:
           print(f"Error creating log entry: {str(e)}")
           # Don't propagate error as logging should not affect the main flow
           await db.rollback()
   ```

4. **Rejestracja routera w aplikacji głównej**:
   ```python
   from fastapi import FastAPI
   from routers import offers_router

   app = FastAPI()
   app.include_router(offers_router)
   ```

5. **Utworzenie zależności dla przechowywania plików** (jeśli potrzebne w przyszłości):
   ```python
   from fastapi import Depends, UploadFile
   from typing import Optional
   import aiofiles
   import os
   from uuid import uuid4

   from config import UPLOAD_DIR

   class FileStorage:
       def __init__(self, upload_dir: str = UPLOAD_DIR):
           self.upload_dir = upload_dir
           os.makedirs(self.upload_dir, exist_ok=True)
           
       async def save_file(self, file: UploadFile) -> Optional[str]:
           """Save file to storage and return filename"""
           if not file:
               return None
               
           try:
               # Generate unique filename
               ext = file.filename.split('.')[-1]
               filename = f"{uuid4()}.{ext}"
               
               # Save file
               file_path = os.path.join(self.upload_dir, filename)
               content = await file.read()
               
               async with aiofiles.open(file_path, 'wb') as f:
                   await f.write(content)
                   
               return filename
           except Exception as e:
               print(f"Error saving file: {str(e)}")
               return None

   def get_file_storage() -> FileStorage:
       return FileStorage()
   ```
