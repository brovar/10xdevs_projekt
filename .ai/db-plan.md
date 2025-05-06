```
-- Enable the UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUM Types and Tables

-- ENUM Types
CREATE TYPE user_role AS ENUM ('Buyer', 'Seller', 'Admin');
CREATE TYPE user_status AS ENUM ('Active', 'Inactive', 'Deleted');
CREATE TYPE offer_status AS ENUM ('active', 'inactive', 'sold', 'moderated', 'archived', 'deleted');
CREATE TYPE order_status AS ENUM ('pending_payment', 'processing', 'shipped', 'delivered', 'cancelled', 'failed');
CREATE TYPE transaction_status AS ENUM ('success', 'fail', 'cancelled');
CREATE TYPE log_event_type AS ENUM (
    'USER_LOGIN', 'USER_REGISTER', 'PASSWORD_CHANGE',
    'OFFER_CREATE', 'OFFER_EDIT', 'OFFER_STATUS_CHANGE',
    'ORDER_PLACE_START', 'ORDER_PLACE_SUCCESS', 'ORDER_PLACE_FAIL',
    'PAYMENT_SUCCESS', 'PAYMENT_FAIL',
    'OFFER_MODERATED',
    'USER_ACTIVATED', 'USER_DEACTIVATED', 'USER_DELETED'
);

-- Tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role user_role NOT NULL,
    status user_status NOT NULL DEFAULT 'Active',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID NOT NULL REFERENCES users(id),
    category_id BIGINT NOT NULL REFERENCES categories(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    image_filename VARCHAR(128),
    quantity INTEGER NOT NULL DEFAULT 1,
    status offer_status NOT NULL DEFAULT 'inactive',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID NOT NULL REFERENCES users(id),
    status order_status NOT NULL DEFAULT 'pending_payment',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id),
    offer_id UUID NOT NULL REFERENCES offers(id),
    quantity INTEGER NOT NULL,
    price_at_purchase NUMERIC(10, 2) NOT NULL
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id),
    external_transaction_id VARCHAR(255),
    status transaction_status NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    event_type log_event_type NOT NULL,
    user_id UUID REFERENCES users(id), -- Optional link to user
    ip_address INET,
    message TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Relacje między tabelami
-- Relacje są zdefiniowane przez ograniczenia FOREIGN KEY w definicjach tabel powyżej:
-- - users (1) -> offers (N) [seller_id]
-- - categories (1) -> offers (N) [category_id]
-- - users (1) -> orders (N) [buyer_id]
-- - orders (1) -> order_items (N) [order_id]
-- - offers (1) -> order_items (N) [offer_id]
-- - orders (1) -> transactions (N) [order_id]
-- - users (1) -> logs (N) [user_id, nullable]

-- 3. Indeksy
-- Indeksy dla kluczy głównych (PK) i ograniczeń UNIQUE są tworzone automatycznie.
-- Indeksy dla kluczy obcych (FK) są zalecane i często tworzone automatycznie przez PostgreSQL, ale jawne dodanie jest dobrą praktyką.

-- Indeksy dla FK
CREATE INDEX idx_offers_seller_id ON offers(seller_id);
CREATE INDEX idx_offers_category_id ON offers(category_id);
CREATE INDEX idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_offer_id ON order_items(offer_id);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_logs_user_id ON logs(user_id);

-- Indeksy dla często używanych kolumn w zapytaniach
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_offers_status ON offers(status);
CREATE INDEX idx_offers_title ON offers(title); -- B-tree for basic searches
CREATE INDEX idx_offers_description ON offers(description); -- B-tree (consider full-text search indexes later if needed)
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_event_type ON logs(event_type);
CREATE INDEX idx_logs_ip_address ON logs(ip_address);

-- 4. Zasady PostgreSQL (RLS)
-- Zgodnie z decyzjami z sesji planowania, Row Level Security (RLS) nie będzie implementowane w bazie danych na etapie MVP. Kontrola dostępu będzie realizowana w warstwie backendowej aplikacji.

-- 5. Dodatkowe uwagi
-- - **Strategia Soft Delete:** Usuwanie rekordów realizowane jest poprzez zmianę wartości w kolumnach `status` (np. na 'Deleted' w `users`, 'deleted'/'archived' w `offers`). Logika aplikacji musi odpowiednio filtrować te rekordy.
-- - **Walidacja Danych:** Zgodnie z decyzjami, nie użyto ograniczeń `CHECK` (np. `price > 0`). Integralność danych (poza `NOT NULL`, `UNIQUE`, FK) musi być zapewniona przez logikę backendu.
-- - **Klucze Obce:** Użyto domyślnego zachowania dla kluczy obcych (`ON DELETE RESTRICT`, `ON UPDATE CASCADE`). Przy strategii soft-delete, operacje te nie powinny być problemem, ale należy upewnić się, że logika aplikacji poprawnie zarządza powiązaniami.
-- - **Rozszerzenia:** Schemat wymaga aktywnego rozszerzenia `uuid-ossp` do generowania wartości domyślnych dla kluczy głównych UUID.
-- - **Timestampy:** Użyto `TIMESTAMPTZ` dla wszystkich znaczników czasu, aby zapewnić obsługę stref czasowych. Kolumny `updated_at` powinny być aktualizowane przez logikę aplikacji przy każdej modyfikacji rekordu.
```