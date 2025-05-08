# REST API Plan

## 1. Resources

-   **Auth**: Handles user authentication (login, registration). Related to `users` table.
-   **Users**: Represents user accounts (`users` table). Includes profile management and admin actions.
-   **Categories**: Represents product categories (`categories` table). Read-only.
-   **Offers**: Represents products listed for sale (`offers` table). Includes creation, editing, status changes, search, and moderation.
-   **Media**: Represents static files, specifically offer images. Served from the filesystem.
-   **Orders**: Represents customer purchases (`orders`, `order_items` tables). Includes checkout process and status updates.
-   **Payments**: Handles the callback from the mock payment processor. Related to `transactions` and `orders` tables.
-   **Logs**: Represents application event logs (`logs` table). Read-only via Admin panel.

## 2. Endpoints

### 2.1 Auth

-   **Register User**
    -   **Method**: `POST`
    -   **Path**: `/auth/register`
    -   **Description**: Creates a new Buyer or Seller user account.
    -   **Request Body**:
        ```json
        {
          "email": "user@example.com",
          "password": "Password123!",
          "role": "Buyer" // or "Seller"
        }
        ```
    -   **Response Body (Success)**:
        ```json
        {
          "id": "uuid-user-id",
          "email": "user@example.com",
          "role": "Buyer",
          "status": "Active",
          "first_name": null,
          "last_name": null,
          "created_at": "timestamp"
        }
        ```
    -   **Success Code**: `201 Created`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`, `PASSWORD_POLICY_VIOLATED`, `INVALID_ROLE`)
        -   `409 Conflict` (`EMAIL_EXISTS`)
        -   `500 Internal Server Error` (`REGISTRATION_FAILED`)

-   **Login User**
    -   **Method**: `POST`
    -   **Path**: `/auth/login`
    -   **Description**: Authenticates a user and establishes a session via HttpOnly Secure cookie.
    -   **Request Body**:
        ```json
        {
          "email": "user@example.com",
          "password": "Password123!"
        }
        ```
    -   **Response Body (Success)**:
        ```json
        {
          "message": "Login successful"
        }
        ```
    -   **Success Code**: `200 OK` (Session cookie set in response headers)
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`)
        -   `401 Unauthorized` (`INVALID_CREDENTIALS`, `USER_INACTIVE`)
        -   `500 Internal Server Error` (`LOGIN_FAILED`)

-   **Logout User**
    -   **Method**: `POST`
    -   **Path**: `/auth/logout`
    -   **Description**: Clears the user's session cookie. Requires authentication.
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "message": "Logout successful"
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `500 Internal Server Error` (`LOGOUT_FAILED`)

### 2.2 Users

-   **Get Current User**
    -   **Method**: `GET`
    -   **Path**: `/account`
    -   **Description**: Retrieves the profile details of the currently authenticated user. Requires authentication.
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "id": "uuid-user-id",
          "email": "user@example.com",
          "role": "Buyer", // or "Seller", "Admin"
          "status": "Active",
          "first_name": "John",
          "last_name": "Doe",
          "created_at": "timestamp",
          "updated_at": "timestamp" // optional
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `404 Not Found` (`USER_NOT_FOUND`)

-   **Update Current User Profile** (Note: PRD only mentions password change, but allow basic info update)
    -   **Method**: `PATCH`
    -   **Path**: `/account`
    -   **Description**: Updates the first name and last name of the currently authenticated user. Requires authentication.
    -   **Request Body**:
        ```json
        {
          "first_name": "John", // Optional
          "last_name": "Doe"  // Optional
        }
        ```
    -   **Response Body (Success)**: Updated User object (see `GET /account`)
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `500 Internal Server Error` (`PROFILE_UPDATE_FAILED`)

-   **Change Current User Password**
    -   **Method**: `PUT`
    -   **Path**: `/account/password`
    -   **Description**: Changes the password for the currently authenticated user. Requires authentication.
    -   **Request Body**:
        ```json
        {
          "current_password": "OldPassword1!",
          "new_password": "NewPassword123!"
        }
        ```
    -   **Response Body (Success)**:
        ```json
        {
          "message": "Password updated successfully"
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`, `PASSWORD_POLICY_VIOLATED`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`, `INVALID_CURRENT_PASSWORD`)
        -   `500 Internal Server Error` (`PASSWORD_UPDATE_FAILED`)

### 2.3 Categories

-   **List Categories**
    -   **Method**: `GET`
    -   **Path**: `/categories`
    -   **Description**: Retrieves the list of all available product categories. Requires authentication.
    -   **Query Parameters**: None
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "items": [
            { "id": 1, "name": "Electronics" },
            { "id": 2, "name": "Books" }
            // ... up to 20 categories
          ]
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `500 Internal Server Error` (`FETCH_FAILED`)

### 2.4 Offers

-   **List Offers**
    -   **Method**: `GET`
    -   **Path**: `/offers`
    -   **Description**: Retrieves a paginated list of offers. Buyers see 'active' offers. Sellers see their own offers ('active', 'inactive'). Admins see all offers. Requires authentication.
    -   **Query Parameters**:
        -   `search` (string, optional): Search term for title and description (case-insensitive, partial match).
        -   `category_id` (integer, optional): Filter by category ID.
        -   `seller_id` (uuid, optional, Admin only): Filter by seller ID.
        -   `status` (string, optional, Admin/Seller only): Filter by offer status (`active`, `inactive`, `sold`, `moderated`, `archived`).
        -   `sort` (string, optional): Sorting criteria (e.g., `price_asc`, `price_desc`, `created_at_desc`, `relevance` if search is used). Default `created_at_desc`.
        -   `page` (integer, optional, default 1): Page number for pagination.
        -   `limit` (integer, optional, default 100): Number of items per page. Max 100.
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "items": [
            {
              "id": "uuid-offer-id",
              "seller_id": "uuid-seller-id",
              "category_id": 1,
              "title": "Sample Product",
              "price": "99.99",
              "image_filename": "image.png", // Filename only
              "quantity": 10,
              "status": "active",
              "created_at": "timestamp"
              // Maybe include seller name/basic info? TBD
            }
            // ... other offers
          ],
          "total": 150,
          "page": 1,
          "limit": 100,
          "pages": 2
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_QUERY_PARAM`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **List Seller's Own Offers**
    -   **Method**: `GET`
    -   **Path**: `/seller/offers`
    -   **Description**: Retrieves a paginated list of offers owned by the currently authenticated Seller. This endpoint is specifically for sellers to manage their own offers. Requires Seller role.
    -   **Query Parameters**:
        -   `search` (string, optional): Search term for title and description within the seller's offers (case-insensitive, partial match).
        -   `category_id` (integer, optional): Filter by category ID.
        -   `status` (string, optional): Filter by offer status (e.g., `active`, `inactive`, `sold`, `moderated`, `archived`).
        -   `sort` (string, optional): Sorting criteria (e.g., `price_asc`, `price_desc`, `created_at_desc`). Default `created_at_desc`.
        -   `page` (integer, optional, default 1): Page number for pagination.
        -   `limit` (integer, optional, default 100): Number of items per page. Max 100.
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "items": [
            {
              "id": "uuid-offer-id",
              "seller_id": "uuid-current-seller-id", // Implicitly the authenticated seller's ID
              "category_id": 1,
              "title": "My Product",
              "price": "49.99",
              "image_filename": "my_image.png",
              "quantity": 5,
              "status": "inactive",
              "created_at": "timestamp"
            }
            // ... other offers by this seller
          ],
          "total": 25,
          "page": 1,
          "limit": 100,
          "pages": 1
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_QUERY_PARAM`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`) // Not a Seller
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **Create Offer**
    -   **Method**: `POST`
    -   **Path**: `/offers`
    -   **Description**: Creates a new offer. Requires Seller role. Uses `multipart/form-data`.
    -   **Request Body (`multipart/form-data`)**:
        -   `title` (string)
        -   `description` (string, optional)
        -   `price` (string representation of decimal)
        -   `quantity` (integer, default 1)
        -   `category_id` (integer)
        -   `image` (file, optional, PNG, max 1024x768)
    -   **Response Body (Success)**: The created offer object (similar to list item, including `id`, default `status='inactive'`)
    -   **Success Code**: `201 Created`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`, `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`, `INVALID_PRICE`, `INVALID_QUANTITY`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`) // Not a Seller
        -   `404 Not Found` (`CATEGORY_NOT_FOUND`)
        -   `500 Internal Server Error` (`CREATE_FAILED`, `FILE_UPLOAD_FAILED`)

-   **Get Offer Details**
    -   **Method**: `GET`
    -   **Path**: `/offers/{offer_id}`
    -   **Description**: Retrieves details for a specific offer. Access rules depend on role and offer status (Buyers see 'active', Seller sees own, Admin sees all). Requires authentication.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "id": "uuid-offer-id",
          "seller_id": "uuid-seller-id",
          "category_id": 1,
          "title": "Sample Product",
          "description": "Detailed description here.",
          "price": "99.99",
          "image_filename": "image.png", // Filename only
          "quantity": 10,
          "status": "active",
          "created_at": "timestamp",
          "updated_at": "timestamp", // optional
          "seller": { // Include basic seller info
             "id": "uuid-seller-id",
             "first_name": "SellerFirstName", // If available
             "last_name": "SellerLastName"  // If available
          },
          "category": { // Include category name
              "id": 1,
              "name": "Electronics"
          }
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`ACCESS_DENIED`) // Buyer trying to access inactive/moderated offer
        -   `404 Not Found` (`OFFER_NOT_FOUND`)
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **Update Offer**
    -   **Method**: `PUT`
    -   **Path**: `/offers/{offer_id}`
    -   **Description**: Updates an existing offer. Requires Seller role and ownership, only for 'active' or 'inactive' offers. Uses `multipart/form-data`. Replaces allowed fields.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body (`multipart/form-data`)**: Same fields as Create Offer (`title`, `description`, `price`, `quantity`, `category_id`, optional `image`). Provide all editable fields.
    -   **Response Body (Success)**: Updated offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`, `INVALID_STATUS_FOR_EDIT`, ...)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`, `NOT_OFFER_OWNER`)
        -   `404 Not Found` (`OFFER_NOT_FOUND`, `CATEGORY_NOT_FOUND`)
        -   `500 Internal Server Error` (`UPDATE_FAILED`, `FILE_UPLOAD_FAILED`)

-   **Delete Offer**
    -   **Method**: `DELETE`
    -   **Path**: `/offers/{offer_id}`
    -   **Description**: Deletes an offer (soft delete/archive if orders exist). Requires Seller role and ownership.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: None
    -   **Success Code**: `204 No Content`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`, `NOT_OFFER_OWNER`)
        -   `404 Not Found` (`OFFER_NOT_FOUND`)
        -   `500 Internal Server Error` (`DELETE_FAILED`)

-   **Activate Offer**
    -   **Method**: `POST`
    -   **Path**: `/offers/{offer_id}/activate`
    -   **Description**: Sets offer status to 'active'. Requires Seller role and ownership. Offer must be 'inactive'.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `404`, `409` (Invalid current status), `500`

-   **Deactivate Offer**
    -   **Method**: `POST`
    -   **Path**: `/offers/{offer_id}/deactivate`
    -   **Description**: Sets offer status to 'inactive'. Requires Seller role and ownership. Offer must be 'active'.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `404`, `409` (Invalid current status), `500`

-   **Mark Offer as Sold**
    -   **Method**: `POST`
    -   **Path**: `/offers/{offer_id}/mark-sold`
    -   **Description**: Sets offer status to 'sold' and quantity to 0. Requires Seller role and ownership. Irreversible.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `404`, `409` (Already sold/archived), `500`

### 2.5 Media

-   **Get Offer Image**
    -   **Method**: `GET`
    -   **Path**: `/media/offers/{offer_id}/{filename}`
    -   **Description**: Serves the image file associated with an offer. No authentication needed if offer is 'active'. May require checks for other statuses based on final security decisions.
    -   **Path Parameters**: `offer_id` (UUID), `filename` (string)
    -   **Request Body**: None
    -   **Response Body (Success)**: Image file content (`image/png`)
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `404 Not Found` (`OFFER_NOT_FOUND`, `IMAGE_NOT_FOUND`)
        -   `403 Forbidden` (If access control is added based on offer status/user role)
        -   `500 Internal Server Error` (`FILE_SERVE_FAILED`)

### 2.6 Orders

-   **Create Order (Checkout Initiation)**
    -   **Method**: `POST`
    -   **Path**: `/orders`
    -   **Description**: Creates a new order from cart items, sets status to 'pending_payment', validates items, creates transaction record, and returns URL for mock payment. Requires Buyer role.
    -   **Request Body**:
        ```json
        {
          "items": [
            { "offer_id": "uuid-offer-1", "quantity": 1 },
            { "offer_id": "uuid-offer-2", "quantity": 2 }
          ]
        }
        ```
    -   **Response Body (Success)**:
        ```json
        {
          "order_id": "uuid-order-id",
          "payment_url": "http://mock-payment.local/pay?transaction_id=uuid-transaction-id&amount=123.45&callback_url=...",
          "status": "pending_payment",
          "created_at": "timestamp"
        }
        ```
    -   **Success Code**: `201 Created`
    -   **Error Codes**:
        -   `400 Bad Request` (`INVALID_INPUT`, `EMPTY_CART`, `OFFER_NOT_AVAILABLE`, `INSUFFICIENT_QUANTITY`)
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`) // Not a Buyer
        -   `404 Not Found` (`OFFER_NOT_FOUND`)
        -   `500 Internal Server Error` (`ORDER_CREATION_FAILED`)

-   **List Orders (Buyer)**
    -   **Method**: `GET`
    -   **Path**: `/orders`
    -   **Description**: Retrieves a paginated list of orders placed by the currently authenticated Buyer.
    -   **Query Parameters**: `page`, `limit` (as in List Offers)
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list structure (like List Offers) containing Order summary objects:
        ```json
        // Item structure within "items" array:
        {
          "id": "uuid-order-id",
          "status": "processing",
          "total_amount": "123.45", // Calculated sum
          "created_at": "timestamp",
          "updated_at": "timestamp" // optional
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`) // Not a Buyer
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **Get Order Details (Buyer/Seller/Admin)**
    -   **Method**: `GET`
    -   **Path**: `/orders/{order_id}`
    -   **Description**: Retrieves details for a specific order. Buyer can see own orders. Seller can see orders containing their offers. Admin can see all orders. Requires authentication.
    -   **Path Parameters**: `order_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**:
        ```json
        {
          "id": "uuid-order-id",
          "buyer_id": "uuid-buyer-id",
          "status": "processing",
          "created_at": "timestamp",
          "updated_at": "timestamp",
          "items": [
            {
              "id": 123, // order_items.id
              "offer_id": "uuid-offer-1",
              "quantity": 1,
              "price_at_purchase": "50.00",
              "offer_title": "Product Title 1" // Denormalized for convenience
            },
            {
              "id": 124,
              "offer_id": "uuid-offer-2",
              "quantity": 2,
              "price_at_purchase": "36.73",
              "offer_title": "Product Title 2"
            }
          ],
          "total_amount": "123.45" // Calculated sum
          // Maybe add Buyer/Seller details depending on who is viewing?
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`ACCESS_DENIED`) // User doesn't have permission to view this order
        -   `404 Not Found` (`ORDER_NOT_FOUND`)
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **List Sales (Seller)**
    -   **Method**: `GET`
    -   **Path**: `/account/sales`
    -   **Description**: Retrieves a paginated list of orders containing items sold by the currently authenticated Seller. Requires Seller role.
    -   **Query Parameters**: `page`, `limit`
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list structure (like List Offers) containing Order summary objects (similar to `GET /orders` list items).
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `401 Unauthorized` (`NOT_AUTHENTICATED`)
        -   `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`) // Not a Seller
        -   `500 Internal Server Error` (`FETCH_FAILED`)

-   **Ship Order Item(s)** (Assuming Seller ships items individually or marks whole order) Let's assume whole order for simplicity.
    -   **Method**: `POST`
    -   **Path**: `/orders/{order_id}/ship`
    -   **Description**: Sets order status to 'shipped'. Requires Seller role and ownership of at least one item in the order. Order must be 'processing'.
    -   **Path Parameters**: `order_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated Order details object (like `GET /orders/{order_id}`).
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403` (Not Seller or doesn't own items), `404`, `409` (Invalid current status), `500`

-   **Deliver Order**
    -   **Method**: `POST`
    -   **Path**: `/orders/{order_id}/deliver`
    -   **Description**: Sets order status to 'delivered'. Requires Seller role and ownership. Order must be 'shipped'.
    -   **Path Parameters**: `order_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated Order details object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `404`, `409` (Invalid current status), `500`

### 2.7 Payments (Callback)

-   **Handle Payment Callback**
    -   **Method**: `GET`
    -   **Path**: `/payments/callback`
    -   **Description**: Endpoint called by the mock payment provider to notify application of transaction outcome. NOT called by frontend. Updates order status, transaction status, and offer quantity on success.
    -   **Query Parameters**:
        -   `transaction_id` (UUID)
        -   `status` (string: `success`, `fail`, `cancelled`)
        -   (Other params from mock provider might exist, e.g., external ID, checksum - ignore for MVP unless specified)
    -   **Request Body**: None
    -   **Response Body (Success)**: Redirect to frontend confirmation/failure page (e.g., `302 Found` with `Location` header). Details TBD. Or just `200 OK` if frontend polls order status. Let's return `200 OK`.
        ```json
        { "message": "Callback processed", "order_status": "processing" } // Or failed/cancelled
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**:
        -   `400 Bad Request` (`MISSING_PARAM`, `INVALID_PARAM`, `INVALID_STATUS`)
        -   `404 Not Found` (`TRANSACTION_NOT_FOUND`, `ORDER_NOT_FOUND`)
        -   `409 Conflict` (`ORDER_ALREADY_PROCESSED`)
        -   `500 Internal Server Error` (`CALLBACK_PROCESSING_FAILED`)

### 2.8 Admin Endpoints

Prefix: `/admin` (Requires Admin role for all endpoints below)

-   **List Users**
    -   **Method**: `GET`
    -   **Path**: `/admin/users`
    -   **Description**: Retrieves a paginated list of all users.
    -   **Query Parameters**: `page`, `limit`, `role` (optional filter), `status` (optional filter), `search` (optional, for email/name)
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list structure containing User objects (excluding password hash).
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `500`

-   **Get User Details (Admin)**
    -   **Method**: `GET`
    -   **Path**: `/admin/users/{user_id}`
    -   **Description**: Retrieves details for a specific user.
    -   **Path Parameters**: `user_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: User object (excluding password hash).
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `500`

-   **Block User**
    -   **Method**: `POST`
    -   **Path**: `/admin/users/{user_id}/block`
    -   **Description**: Sets user status to 'Inactive'. If Seller, cancels active orders and sets offers to 'inactive'.
    -   **Path Parameters**: `user_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated User object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `409` (Already inactive), `500`

-   **Unblock User**
    -   **Method**: `POST`
    -   **Path**: `/admin/users/{user_id}/unblock`
    -   **Description**: Sets user status to 'Active'.
    -   **Path Parameters**: `user_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated User object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `409` (Already active), `500`

-   **List All Offers (Admin)**
    -   **Method**: `GET`
    -   **Path**: `/admin/offers`
    -   **Description**: Retrieves a paginated list of all offers, regardless of status. (Equivalent to `GET /offers` but guaranteed to show all statuses).
    -   **Query Parameters**: See `GET /offers`. Allows filtering by any status.
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list of Offer objects.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `500`

-   **Moderate Offer**
    -   **Method**: `POST`
    -   **Path**: `/admin/offers/{offer_id}/moderate`
    -   **Description**: Sets offer status to 'moderated'.
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated Offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `409` (Already moderated), `500`

-   **Unmoderate Offer**
    -   **Method**: `POST`
    -   **Path**: `/admin/offers/{offer_id}/unmoderate`
    -   **Description**: Sets offer status back to 'inactive' (or original status before moderation? PRD unclear, let's assume 'inactive').
    -   **Path Parameters**: `offer_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated Offer object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `409` (Not moderated), `500`

-   **List All Orders (Admin)**
    -   **Method**: `GET`
    -   **Path**: `/admin/orders`
    -   **Description**: Retrieves a paginated list of all orders.
    -   **Query Parameters**: `page`, `limit`, `status` (optional filter), `buyer_id` (optional filter), `seller_id` (optional filter, based on items)
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list of Order summary objects.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400`, `401`, `403`, `500`

-   **Cancel Order (Admin)**
    -   **Method**: `POST`
    -   **Path**: `/admin/orders/{order_id}/cancel`
    -   **Description**: Sets order status to 'cancelled'.
    -   **Path Parameters**: `order_id` (UUID)
    -   **Request Body**: None
    -   **Response Body (Success)**: Updated Order details object.
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `401`, `403`, `404`, `409` (Cannot cancel, e.g., already delivered/cancelled), `500`

-   **List Logs**
    -   **Method**: `GET`
    -   **Path**: `/admin/logs`
    -   **Description**: Retrieves a paginated list of application logs.
    -   **Query Parameters**:
        -   `page`, `limit`
        -   `event_type` (string, optional)
        -   `user_id` (uuid, optional)
        -   `ip_address` (string, optional)
        -   `start_date` (string, optional, ISO 8601 format)
        -   `end_date` (string, optional, ISO 8601 format)
    -   **Request Body**: None
    -   **Response Body (Success)**: Paginated list structure containing Log objects:
        ```json
        // Item structure within "items" array:
        {
          "id": 12345,
          "event_type": "USER_LOGIN",
          "user_id": "uuid-user-id", // optional
          "ip_address": "192.168.1.100", // optional
          "message": "Login successful for user@example.com",
          "timestamp": "timestamp"
        }
        ```
    -   **Success Code**: `200 OK`
    -   **Error Codes**: `400` (Invalid filter), `401`, `403`, `500`

## 3. Uwierzytelnianie i autoryzacja

-   **Mechanism**: Session-based authentication using secure, HttpOnly cookies.
    -   FastAPI's `SessionMiddleware` or a similar library (e.g., `fastapi-sessions`) will be used.
    -   Login endpoint (`/auth/login`) verifies credentials and sets the session cookie upon success.
    -   Logout endpoint (`/auth/logout`) clears the session cookie.
    -   Cookie attributes: `HttpOnly=True`, `Secure=True` (requires HTTPS in production), `SameSite=Lax` (or `Strict`). Session expiration: 1 week (as per PRD).
-   **Authorization**: Role-based access control (RBAC) implemented using FastAPI dependencies.
    -   A dependency checks for a valid session and retrieves the user's role.
    -   Endpoint decorators or dependencies enforce required roles (e.g., `@Depends(require_role('Admin'))`).
    -   Specific ownership checks (e.g., Seller can only edit own offers) are implemented within endpoint logic.
    -   Access to resources like offers and orders depends on the user's role and the resource's status (e.g., Buyers only see active offers).

## 4. Walidacja i logika biznesowa

-   **Input Validation**: Pydantic models are used for request body validation in FastAPI.
    -   **Users**: Email format, password policy (min 10 chars, upper, lower, digit/special - checked in backend logic), role must be 'Buyer' or 'Seller' on registration.
    -   **Offers**: Title required, price > 0, quantity >= 0, valid category ID, image size/type validation (PNG, <= 1024x768).
    -   **Orders**: `items` array not empty, each item has valid `offer_id` and `quantity > 0`. Backend checks offer availability and quantity during creation.
    -   **General**: Type checking, required fields enforced by Pydantic. Custom validators for specific rules.
-   **Error Handling**: Custom exception handlers in FastAPI capture specific exceptions (validation errors, DB errors, permission errors) and return standardized JSON error responses as per PRD:
    ```json
    {
      "error_code": "UNIQUE_CONSTRAINT_VIOLATED", // Example code
      "message": "An account with this email already exists.", // User-friendly message
      "details": { // Optional, for more context
        "field": "email"
      }
    }
    ```
-   **Business Logic Implementation**:
    -   **Password Hashing**: Passwords hashed using a strong algorithm (e.g., bcrypt) before storing (`users.password_hash`). Verified during login.
    -   **Status Transitions**: Implemented in specific endpoints (e.g., `/offers/{id}/activate`, `/admin/users/{id}/block`). Logic checks current status before allowing transition.
    -   **Soft Deletes/Archiving**: `DELETE /offers/{id}` checks for associated orders. If found, status is set to `archived`; otherwise, potentially deleted or marked `deleted` (TBD - plan uses soft delete via status change).
    -   **Offer Quantity Management**: Decremented during successful payment callback (`GET /payments/callback`). Checked during order creation (`POST /orders`). Offer status potentially set to `sold` if quantity reaches 0 after purchase.
    -   **User Blocking Consequences**: Blocking a Seller (`POST /admin/users/{id}/block`) triggers logic to cancel their active orders and set their offers to `inactive`.
    -   **Logging**: Application events (login, offer creation, payment success/fail, etc.) are logged to the `logs` table via dedicated service calls within relevant endpoint logic. Log entries include timestamp, event type, user ID (if applicable), IP address, and a descriptive message.
    -   **Search**: `GET /offers?search=...` uses case-insensitive partial matching on `title` and `description` fields (e.g., using `ILIKE` or `LOWER()` in SQL). Relevance sorting TBD (simple count or basic full-text search feature if DB supports).
    -   **Pagination**: Default limit 100, max 100 enforced on all list endpoints.
    -   **Mock Payment Integration**: `POST /orders` generates the payment URL. `GET /payments/callback` handles the result, updating related entities.
