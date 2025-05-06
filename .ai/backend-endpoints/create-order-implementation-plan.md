# API Endpoint Implementation Plan: Create Order (Checkout Initiation)

## 1. Przegląd punktu końcowego
Endpoint `/orders` z metodą POST służy do inicjacji procesu zamówienia (checkout). Tworzy nowe zamówienie na podstawie przedmiotów z koszyka, waliduje dostępność ofert, ustawia status zamówienia na 'pending_payment', tworzy rekord transakcji w bazie danych oraz generuje i zwraca URL do systemu płatności. Endpoint wymaga uwierzytelnienia oraz roli Buyer.

## 2. Szczegóły żądania
- Metoda HTTP: `POST`
- Struktura URL: `/orders`
- Parametry Path: brak
- Format danych: `application/json`
- Request Body:
  ```json
  {
    "items": [
      { "offer_id": "uuid-offer-1", "quantity": 1 },
      { "offer_id": "uuid-offer-2", "quantity": 2 }
    ]
  }
  ```
- Nagłówki:
  - `Authorization`: Token sesji/Cookie, wymagany do uwierzytelnienia

## 3. Wykorzystywane typy
- **DTO Wejściowe**: 
  - `OrderItemRequest` (z types.py)
  - `CreateOrderRequest` (z types.py)
- **DTO Wyjściowe**: 
  - `CreateOrderResponse` (z types.py)
- **Typy Enum**:
  - `OrderStatus` (z types.py)
  - `TransactionStatus` (z types.py)
  - `LogEventType` (z types.py)
- **Modele bazy danych**:
  - `Order`
  - `OrderItem`
  - `Transaction`
  - `Offer`
  - `User`

## 4. Szczegóły odpowiedzi
- Kod sukcesu: `201 Created`
- Response Body (sukces):
  ```json
  {
    "order_id": "uuid-order-id",
    "payment_url": "http://mock-payment.local/pay?transaction_id=uuid-transaction-id&amount=123.45&callback_url=...",
    "status": "pending_payment",
    "created_at": "timestamp"
  }
  ```
- Kody błędów:
  - `400 Bad Request` z kodami błędów:
    - `INVALID_INPUT`: Nieprawidłowa struktura danych wejściowych
    - `EMPTY_CART`: Brak przedmiotów w koszyku
    - `OFFER_NOT_AVAILABLE`: Oferta nie jest dostępna (nieaktywna, sprzedana, zmoderowana)
    - `INSUFFICIENT_QUANTITY`: Niewystarczająca ilość produktu
  - `401 Unauthorized` z kodem błędu `NOT_AUTHENTICATED`
  - `403 Forbidden` z kodem błędu `INSUFFICIENT_PERMISSIONS`
  - `404 Not Found` z kodem błędu `OFFER_NOT_FOUND`
  - `500 Internal Server Error` z kodem błędu `ORDER_CREATION_FAILED`

## 5. Przepływ danych
1. Uwierzytelnienie i autoryzacja użytkownika
2. Walidacja danych wejściowych (struktura, niepusty koszyk)
3. Sprawdzenie istnienia każdej oferty w bazie danych
4. Weryfikacja statusu każdej oferty (musi być 'active')
5. Sprawdzenie dostępności ilości dla każdej oferty
6. Obliczenie łącznej kwoty zamówienia
7. Utworzenie rekordu zamówienia w tabeli 'orders'
8. Utworzenie rekordów dla elementów zamówienia w tabeli 'order_items'
9. Utworzenie rekordu transakcji w tabeli 'transactions' ze statusem 'pending'
10. Generowanie URL płatności zawierającego ID transakcji, kwotę oraz URL zwrotny
11. Zalogowanie zdarzenia w tabeli 'logs'
12. Zwrócenie odpowiedzi z ID zamówienia, URL płatności, statusem i datą utworzenia

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Wymagany ważny token sesji/cookie
- **Autoryzacja**: Sprawdzenie czy użytkownik ma rolę 'Buyer'
- **Walidacja danych**: 
  - Użycie Pydantic do walidacji struktury danych wejściowych
  - Walidacja istnienia ofert i ich dostępności
  - Walidacja ilości zamówionych przedmiotów
- **Zabezpieczenie przed wyścigami (race conditions)**: 
  - Użycie transakcji bazodanowych do atomowego zapisywania zamówienia i elementów
  - Implementacja blokady optymistycznej przy sprawdzaniu/aktualizacji ilości ofert
- **Ochrona przed duplikacją zamówień**: 
  - Implementacja idempotentności przez sprawdzanie istniejących zamówień w toku
- **Logowanie**: 
  - Rejestrowanie wszystkich prób zamówień (udanych i nieudanych) w tabeli 'logs'
  - Zapisywanie IP użytkownika, identyfikatora użytkownika i szczegółów zdarzenia

## 7. Obsługa błędów
- **Błędy walidacji**:
  - Nieprawidłowa struktura JSON: 422 Unprocessable Entity (obsługiwane przez FastAPI) lub 400 Bad Request
  - Puste koszyk (brak przedmiotów): 400 Bad Request z kodem `EMPTY_CART`
  - Nieprawidłowy typ danych: 400 Bad Request z kodem `INVALID_INPUT`
  - Nieprawidłowa ilość (mniejsza od 1): 400 Bad Request z kodem `INVALID_INPUT`
- **Błędy biznesowe**:
  - Oferta nie istnieje: 404 Not Found z kodem `OFFER_NOT_FOUND`
  - Oferta niedostępna (nieaktywna, sprzedana): 400 Bad Request z kodem `OFFER_NOT_AVAILABLE`
  - Niewystarczająca ilość: 400 Bad Request z kodem `INSUFFICIENT_QUANTITY`
- **Błędy autoryzacji**:
  - Brak uwierzytelnienia: 401 Unauthorized z kodem `NOT_AUTHENTICATED`
  - Niewystarczające uprawnienia: 403 Forbidden z kodem `INSUFFICIENT_PERMISSIONS`
- **Błędy systemowe**:
  - Problemy z bazą danych: 500 Internal Server Error z kodem `ORDER_CREATION_FAILED`
  - Nieobsłużone wyjątki: 500 Internal Server Error z kodem `ORDER_CREATION_FAILED`

## 8. Rozważania dotyczące wydajności
- **Transakcje bazodanowe**: 
  - Użycie transakcji do zapewnienia spójności danych
  - Minimalizacja czasu trwania transakcji poprzez wykonanie tylko niezbędnych operacji w jej obrębie
- **Asynchroniczne przetwarzanie**: 
  - Implementacja asynchronicznych endpointów dla operacji I/O-bound
  - Wykorzystanie FastAPI async/await dla obsługi równoległych żądań
- **Indeksowanie**: 
  - Upewnienie się, że tabele 'offers', 'orders', 'order_items', 'transactions' mają odpowiednie indeksy
- **Obsługa dużej liczby żądań**: 
  - Implementacja buforowania dla popularnych ofert
  - Rozważenie mechanizmu kolejkowania zamówień w przypadku dużego obciążenia
- **Monitorowanie wydajności**: 
  - Dodanie metryk czasu wykonania dla kluczowych operacji
  - Logowanie i monitorowanie opóźnień w przetwarzaniu zamówień

## 9. Etapy wdrożenia

1. **Utworzenie OrderService**:
   ```python
   # src/services/order_service.py
   from fastapi import HTTPException, status, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   import logging
   from typing import List, Optional, Dict
   from decimal import Decimal
   import uuid
   from datetime import datetime
   
   from src.db.models import Order, OrderItem, Offer, Transaction, User
   from src.types import OrderStatus, TransactionStatus, LogEventType, CreateOrderRequest, OrderItemRequest
   from src.services.log_service import LogService
   from src.config import PAYMENT_GATEWAY_URL
   
   class OrderService:
       def __init__(self, db: AsyncSession, log_service: LogService, logger: logging.Logger):
           self.db = db
           self.log_service = log_service
           self.logger = logger
       
       async def create_order(
           self,
           current_user: User,
           order_data: CreateOrderRequest,
           ip_address: Optional[str] = None
       ) -> Dict:
           """
           Create a new order with the given items.
           
           Args:
               current_user: The authenticated user making the order
               order_data: CreateOrderRequest with items to order
               ip_address: Optional IP address for logging
               
           Returns:
               Dictionary containing order_id, payment_url, status, and created_at
               
           Raises:
               HTTPException: If validation fails or order creation fails
           """
           # Log order creation start
           await self.log_service.create_log(
               event_type=LogEventType.ORDER_PLACE_START,
               user_id=current_user.id,
               ip_address=ip_address,
               message=f"Order creation started for user {current_user.email} with {len(order_data.items)} items"
           )
           
           # Start transaction
           try:
               # Validate items - check if offers exist and are available
               offers_map = {}
               total_amount = Decimal("0.00")
               
               for item in order_data.items:
                   offer = await self.db.get(Offer, item.offer_id)
                   
                   # Check if offer exists
                   if not offer:
                       raise HTTPException(
                           status_code=status.HTTP_404_NOT_FOUND,
                           detail={
                               "error_code": "OFFER_NOT_FOUND",
                               "message": f"Offer with ID {item.offer_id} not found"
                           }
                       )
                   
                   # Check if offer is active
                   if offer.status != "active":
                       raise HTTPException(
                           status_code=status.HTTP_400_BAD_REQUEST,
                           detail={
                               "error_code": "OFFER_NOT_AVAILABLE",
                               "message": f"Offer with ID {item.offer_id} is not active"
                           }
                       )
                   
                   # Check if quantity is sufficient
                   if offer.quantity < item.quantity:
                       raise HTTPException(
                           status_code=status.HTTP_400_BAD_REQUEST,
                           detail={
                               "error_code": "INSUFFICIENT_QUANTITY",
                               "message": f"Insufficient quantity for offer {item.offer_id}. Available: {offer.quantity}, Requested: {item.quantity}"
                           }
                       )
                   
                   # Store offer in map for later use
                   offers_map[str(item.offer_id)] = offer
                   
                   # Calculate item total and add to order total
                   item_total = offer.price * Decimal(str(item.quantity))
                   total_amount += item_total
               
               # Create order record
               order_id = uuid.uuid4()
               order = Order(
                   id=order_id,
                   buyer_id=current_user.id,
                   status=OrderStatus.PENDING_PAYMENT,
                   created_at=datetime.utcnow()
               )
               self.db.add(order)
               await self.db.flush()  # Flush to get the order ID
               
               # Create order items
               for item in order_data.items:
                   offer = offers_map[str(item.offer_id)]
                   order_item = OrderItem(
                       order_id=order_id,
                       offer_id=item.offer_id,
                       quantity=item.quantity,
                       price_at_purchase=offer.price
                   )
                   self.db.add(order_item)
               
               # Create transaction record
               transaction_id = uuid.uuid4()
               transaction = Transaction(
                   id=transaction_id,
                   order_id=order_id,
                   status=TransactionStatus.FAIL,  # Default to fail until payment completes
                   amount=total_amount,
                   timestamp=datetime.utcnow()
               )
               self.db.add(transaction)
               
               # Construct payment URL with transaction ID and callback URL
               callback_url = f"{PAYMENT_GATEWAY_URL}/payments/callback"
               payment_url = f"{PAYMENT_GATEWAY_URL}/pay?transaction_id={transaction_id}&amount={total_amount}&callback_url={callback_url}"
               
               # Commit the transaction
               await self.db.commit()
               
               # Log successful order creation
               await self.log_service.create_log(
                   event_type=LogEventType.ORDER_PLACE_SUCCESS,
                   user_id=current_user.id,
                   ip_address=ip_address,
                   message=f"Order {order_id} created successfully for user {current_user.email} with total amount {total_amount}"
               )
               
               # Return the order details
               return {
                   "order_id": order_id,
                   "payment_url": payment_url,
                   "status": OrderStatus.PENDING_PAYMENT,
                   "created_at": order.created_at
               }
           
           except HTTPException:
               # Rollback transaction and re-raise HTTP exceptions
               await self.db.rollback()
               raise
           
           except Exception as e:
               # Rollback transaction and handle unexpected errors
               await self.db.rollback()
               error_message = f"Error creating order: {str(e)}"
               self.logger.error(error_message)
               
               # Log order creation failure
               await self.log_service.create_log(
                   event_type=LogEventType.ORDER_PLACE_FAIL,
                   user_id=current_user.id,
                   ip_address=ip_address,
                   message=error_message
               )
               
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail={
                       "error_code": "ORDER_CREATION_FAILED",
                       "message": "An error occurred while processing your order"
                   }
               )
   ```

2. **Utworzenie LogService (jeśli nie istnieje)**:
   ```python
   # src/services/log_service.py
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import Optional
   from uuid import UUID
   
   from src.db.models import Log
   from src.types import LogEventType
   
   class LogService:
       def __init__(self, db: AsyncSession):
           self.db = db
       
       async def create_log(
           self,
           event_type: LogEventType,
           message: str,
           user_id: Optional[UUID] = None,
           ip_address: Optional[str] = None
       ) -> Log:
           """
           Create a new log entry
           
           Args:
               event_type: Type of event from LogEventType enum
               message: Log message
               user_id: Optional UUID of the user
               ip_address: Optional IP address
               
           Returns:
               Created Log record
           """
           log = Log(
               event_type=event_type,
               user_id=user_id,
               ip_address=ip_address,
               message=message
           )
           self.db.add(log)
           
           # Don't commit here, let the caller handle transaction
           return log
   ```

3. **Utworzenie konfiguracji dla systemu płatności**:
   ```python
   # src/config.py
   from pathlib import Path
   
   # Base URL for the payment gateway
   PAYMENT_GATEWAY_URL = "http://mock-payment.local"
   
   # Callback URL for payment notifications (to be registered with payment gateway)
   PAYMENT_CALLBACK_URL = "http://api.steambay.local/payments/callback"
   ```

4. **Utworzenie kontrolera OrderController**:
   ```python
   # src/controllers/order_controller.py
   from fastapi import APIRouter, Depends, Request, status
   from sqlalchemy.ext.asyncio import AsyncSession
   import logging
   
   from src.db.session import get_async_session
   from src.services.auth import get_current_user, require_role
   from src.services.order_service import OrderService
   from src.services.log_service import LogService
   from src.types import UserRole, CreateOrderRequest, CreateOrderResponse
   
   # Setup logger
   logger = logging.getLogger(__name__)
   
   # Create router
   router = APIRouter(prefix="/orders", tags=["orders"])
   
   @router.post(
       "",
       response_model=CreateOrderResponse,
       status_code=status.HTTP_201_CREATED,
       dependencies=[Depends(require_role([UserRole.BUYER]))]
   )
   async def create_order(
       request: Request,
       order_data: CreateOrderRequest,
       current_user = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_session),
       log_service: LogService = Depends(lambda db=Depends(get_async_session): LogService(db))
   ):
       """
       Create a new order from cart items, set status to 'pending_payment',
       validate items, create transaction record, and return URL for mock payment.
       Requires Buyer role.
       """
       # Get client IP for logging
       client_ip = request.client.host if request.client else None
       
       # Create order service
       order_service = OrderService(db, log_service, logger)
       
       # Create order and get response
       result = await order_service.create_order(
           current_user=current_user,
           order_data=order_data,
           ip_address=client_ip
       )
       
       # Return the result
       return CreateOrderResponse(**result)
   ```

5. **Dodanie wymaganych zabezpieczeń dostępu**:
   ```python
   # src/services/auth.py (uzupełnienie istniejącego pliku)
   from fastapi import Depends, HTTPException, status
   from typing import List, Callable
   
   from src.types import UserRole
   
   def require_role(allowed_roles: List[UserRole]) -> Callable:
       """
       Dependency function that ensures the current user has one of the allowed roles
       
       Args:
           allowed_roles: List of UserRole enums that are allowed access
           
       Returns:
           A dependency function that checks if user has required role
       """
       async def role_checker(current_user = Depends(get_current_user)):
           if current_user.role not in allowed_roles:
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail={
                       "error_code": "INSUFFICIENT_PERMISSIONS",
                       "message": "You don't have permission to perform this action"
                   }
               )
           return current_user
       
       return role_checker
   ```

6. **Zarejestrowanie routera w aplikacji głównej**:
   ```python
   # main.py (uzupełnienie istniejącego pliku)
   
   # Import nowego routera
   from src.controllers.order_controller import router as order_router
   
   # Dodanie routera do aplikacji
   app.include_router(order_router)
   ```

7. **Utworzenie testów jednostkowych**:
   ```python
   # tests/services/test_order_service.py
   import pytest
   from unittest.mock import AsyncMock, MagicMock, patch
   from fastapi import HTTPException
   from decimal import Decimal
   import uuid
   
   from src.services.order_service import OrderService
   from src.types import OrderStatus, TransactionStatus, CreateOrderRequest, OrderItemRequest
   
   @pytest.fixture
   def mock_db():
       db = AsyncMock()
       db.commit = AsyncMock()
       db.rollback = AsyncMock()
       db.flush = AsyncMock()
       db.get = AsyncMock()
       return db
   
   @pytest.fixture
   def mock_log_service():
       service = AsyncMock()
       service.create_log = AsyncMock()
       return service
   
   @pytest.fixture
   def mock_logger():
       return MagicMock()
   
   @pytest.fixture
   def order_service(mock_db, mock_log_service, mock_logger):
       return OrderService(mock_db, mock_log_service, mock_logger)
   
   @pytest.fixture
   def sample_user():
       user = MagicMock()
       user.id = uuid.uuid4()
       user.email = "buyer@example.com"
       user.role = "Buyer"
       return user
   
   @pytest.fixture
   def sample_order_data():
       return CreateOrderRequest(
           items=[
               OrderItemRequest(offer_id=uuid.uuid4(), quantity=2),
               OrderItemRequest(offer_id=uuid.uuid4(), quantity=1)
           ]
       )
   
   @pytest.fixture
   def sample_offers():
       offer1 = MagicMock()
       offer1.id = uuid.uuid4()
       offer1.status = "active"
       offer1.quantity = 5
       offer1.price = Decimal("10.00")
       
       offer2 = MagicMock()
       offer2.id = uuid.uuid4()
       offer2.status = "active"
       offer2.quantity = 3
       offer2.price = Decimal("20.00")
       
       return [offer1, offer2]
   
   @pytest.mark.asyncio
   async def test_create_order_success(order_service, sample_user, sample_order_data, sample_offers, mock_db):
       # Setup mock DB to return sample offers
       mock_db.get.side_effect = sample_offers
       
       # Call create_order
       result = await order_service.create_order(sample_user, sample_order_data)
       
       # Assertions
       assert "order_id" in result
       assert "payment_url" in result
       assert result["status"] == OrderStatus.PENDING_PAYMENT
       assert "created_at" in result
       
       # Check that DB operations were called
       assert mock_db.add.call_count == 3  # Order, 2 OrderItems
       assert mock_db.commit.called
   
   @pytest.mark.asyncio
   async def test_create_order_offer_not_found(order_service, sample_user, sample_order_data, mock_db):
       # Setup mock DB to return None (offer not found)
       mock_db.get.return_value = None
       
       # Test
       with pytest.raises(HTTPException) as exc_info:
           await order_service.create_order(sample_user, sample_order_data)
       
       # Assertions
       assert exc_info.value.status_code == 404
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_FOUND"
       assert mock_db.rollback.called
   
   @pytest.mark.asyncio
   async def test_create_order_offer_not_active(order_service, sample_user, sample_order_data, mock_db):
       # Setup mock DB to return inactive offer
       offer = MagicMock()
       offer.status = "inactive"
       mock_db.get.return_value = offer
       
       # Test
       with pytest.raises(HTTPException) as exc_info:
           await order_service.create_order(sample_user, sample_order_data)
       
       # Assertions
       assert exc_info.value.status_code == 400
       assert exc_info.value.detail["error_code"] == "OFFER_NOT_AVAILABLE"
       assert mock_db.rollback.called
   
   @pytest.mark.asyncio
   async def test_create_order_insufficient_quantity(order_service, sample_user, sample_order_data, mock_db):
       # Setup mock DB to return offer with insufficient quantity
       offer = MagicMock()
       offer.status = "active"
       offer.quantity = 0
       mock_db.get.return_value = offer
       
       # Test
       with pytest.raises(HTTPException) as exc_info:
           await order_service.create_order(sample_user, sample_order_data)
       
       # Assertions
       assert exc_info.value.status_code == 400
       assert exc_info.value.detail["error_code"] == "INSUFFICIENT_QUANTITY"
       assert mock_db.rollback.called
   ```

8. **Utworzenie testów integracyjnych**:
   ```python
   # tests/controllers/test_order_controller.py
   import pytest
   from fastapi.testclient import TestClient
   from unittest.mock import AsyncMock, patch, MagicMock
   import uuid
   from decimal import Decimal
   
   from main import app
   from src.types import UserRole, OrderStatus
   
   client = TestClient(app)
   
   @pytest.fixture
   def mock_user():
       user = MagicMock()
       user.id = uuid.uuid4()
       user.email = "test@example.com"
       user.role = UserRole.BUYER
       return user
   
   def test_create_order_unauthorized():
       # Setup
       payload = {
           "items": [
               {"offer_id": str(uuid.uuid4()), "quantity": 1}
           ]
       }
       
       # Call API without authentication
       response = client.post("/orders", json=payload)
       
       # Assertions
       assert response.status_code == 401
       assert response.json()["error_code"] == "NOT_AUTHENTICATED"
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.auth.require_role")
   @patch("src.services.order_service.OrderService.create_order")
   def test_create_order_success(mock_create_order, mock_require_role, mock_get_current_user, mock_user):
       # Setup
       mock_get_current_user.return_value = mock_user
       mock_require_role.return_value = lambda: True
       
       order_id = uuid.uuid4()
       mock_create_order.return_value = {
           "order_id": order_id,
           "payment_url": "http://mock-payment.local/pay?transaction_id=123&amount=30.00",
           "status": OrderStatus.PENDING_PAYMENT,
           "created_at": "2023-01-01T12:00:00"
       }
       
       payload = {
           "items": [
               {"offer_id": str(uuid.uuid4()), "quantity": 1}
           ]
       }
       
       # Call API
       response = client.post("/orders", json=payload)
       
       # Assertions
       assert response.status_code == 201
       result = response.json()
       assert result["order_id"] == str(order_id)
       assert "payment_url" in result
       assert result["status"] == OrderStatus.PENDING_PAYMENT
       assert "created_at" in result
   
   @patch("src.services.auth.get_current_user")
   @patch("src.services.auth.require_role")
   @patch("src.db.session.get_async_session")
   def test_create_order_empty_cart(mock_db, mock_require_role, mock_get_current_user, mock_user):
       # Setup
       mock_get_current_user.return_value = mock_user
       mock_require_role.return_value = lambda: True
       
       payload = {
           "items": []
       }
       
       # Call API
       response = client.post("/orders", json=payload)
       
       # Assertions
       assert response.status_code == 400
       assert response.json()["detail"][0]["type"] == "value_error"
   ```

9. **Aktualizacja modeli bazy danych**:
   Upewnij się, że w pliku `src/db/models.py` zdefiniowane są odpowiednie modele bazy danych, zgodne ze schematem z `db-plan.md`.

10. **Dokumentacja API z OpenAPI**:
    ```python
    # Dodaj do definicji endpointu w order_controller.py
    
    @router.post(
        "",
        response_model=CreateOrderResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_role([UserRole.BUYER]))],
        summary="Create Order (Checkout Initiation)",
        description="""
        Creates a new order from cart items, sets status to 'pending_payment',
        validates items, creates transaction record, and returns URL for mock payment.
        Requires Buyer role.
        
        Error codes:
        - INVALID_INPUT: Invalid input structure or data
        - EMPTY_CART: No items in the cart
        - OFFER_NOT_FOUND: One of the offers doesn't exist
        - OFFER_NOT_AVAILABLE: One of the offers is not active
        - INSUFFICIENT_QUANTITY: Not enough quantity available for an offer
        - NOT_AUTHENTICATED: User is not authenticated
        - INSUFFICIENT_PERMISSIONS: User is not a Buyer
        - ORDER_CREATION_FAILED: Internal server error
        """
    )
    ```
