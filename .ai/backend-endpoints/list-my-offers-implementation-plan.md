# API Endpoint Implementation Plan: List Seller's Own Offers

## 1. Przegląd punktu końcowego
Endpoint `/seller/offers` umożliwia zalogowanym sprzedawcom przeglądanie listy swoich ofert z opcjami filtrowania, wyszukiwania i stronicowania. Jest to kluczowy element zarządzania ofertami przez sprzedawców w systemie.

## 2. Szczegóły żądania
- **Metoda HTTP**: GET
- **Struktura URL**: `/seller/offers`
- **Parametry URL**:
  - Opcjonalne:
    - `search` (string): Wyszukiwanie po tytule i opisie oferty (niewrażliwe na wielkość liter, częściowe dopasowanie)
    - `category_id` (integer): Filtrowanie po ID kategorii
    - `status` (string): Filtrowanie po statusie oferty (`active`, `inactive`, `sold`, `moderated`, `archived`)
    - `sort` (string): Kryterium sortowania (`price_asc`, `price_desc`, `created_at_desc`)
    - `page` (integer): Numer strony (domyślnie 1)
    - `limit` (integer): Liczba elementów na stronę (domyślnie 100, maksymalnie 100)
- **Request Body**: Brak

## 3. Wykorzystywane typy
- **Parametry zapytania**:
  - Nowy model `SellerOfferListQueryParams` (wzorowany na `OfferListQueryParams`, ale z dodatkowym polem `status`)
- **Odpowiedź**:
  - `OfferSummaryDTO`: Reprezentuje pojedynczą ofertę w liście
  - `OfferListResponse` (extends `PaginatedResponse`): Zawiera listę ofert i metadane stronicowania
- **Enums**:
  - `OfferStatus`: Do walidacji parametru `status`
  - `UserRole`: Do sprawdzania roli użytkownika
  - `LogEventType`: Do logowania zdarzeń

## 4. Szczegóły odpowiedzi
- **Kod sukcesu**: 200 OK
- **Format odpowiedzi**: JSON
- **Struktura odpowiedzi**:
  ```json
  {
    "items": [
      {
        "id": "uuid-offer-id",
        "seller_id": "uuid-current-seller-id",
        "category_id": 1,
        "title": "My Product",
        "price": "49.99",
        "image_filename": "my_image.png",
        "quantity": 5,
        "status": "inactive",
        "created_at": "timestamp"
      }
    ],
    "total": 25,
    "page": 1,
    "limit": 100,
    "pages": 1
  }
  ```
- **Kody błędów**:
  - `400 Bad Request`: Nieprawidłowe parametry zapytania
  - `401 Unauthorized`: Brak uwierzytelnienia
  - `403 Forbidden`: Brak uprawnień (nie jest sprzedawcą)
  - `500 Internal Server Error`: Błąd serwera

## 5. Przepływ danych
1. Odbierz żądanie GET z parametrami zapytania
2. Zwaliduj parametry zapytania używając Pydantic
3. Sprawdź uwierzytelnienie użytkownika (sesja)
4. Sprawdź czy użytkownik ma rolę Seller
5. Utwórz zapytanie SQL do bazy danych z filtracją po:
   - seller_id (równe ID bieżącego użytkownika)
   - category_id (jeśli podano)
   - status (jeśli podano)
   - title/description zawierające szukany tekst (jeśli podano parametr `search`)
6. Zastosuj sortowanie zgodnie z parametrem `sort`
7. Zastosuj stronicowanie zgodnie z parametrami `page` i `limit`
8. Wykonaj zapytanie do bazy danych
9. Przekształć wyniki zapytania do listy obiektów `OfferSummaryDTO`
10. Utwórz odpowiedź `OfferListResponse` z listą ofert i metadanymi stronicowania
11. Zaloguj zdarzenie w systemie logów
12. Zwróć odpowiedź z kodem HTTP 200

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Wymaga ważnej sesji użytkownika (HttpOnly cookie)
- **Autoryzacja**: Wymaga roli `Seller`
- **Filtrowanie danych**: Zapewnij, że użytkownik widzi tylko swoje oferty
- **Ochrona przed atakami**:
  - Użyj parametryzowanych zapytań SQL dla parametrów wyszukiwania i filtrów
  - Ogranicz maksymalną liczbę zwracanych elementów (max 100)
  - Waliduj wszystkie parametry wejściowe za pomocą Pydantic
  - Sanityzuj parametr `search` przed użyciem w zapytaniach SQL

## 7. Obsługa błędów
- Nieprawidłowe parametry zapytania:
  - Kod: 400 Bad Request
  - Kod błędu: `INVALID_QUERY_PARAM`
  - Komunikat: Szczegółowy opis błędu walidacji
  - Logowanie: `LogEventType.OFFER_LIST_FAIL`

- Użytkownik niezalogowany:
  - Kod: 401 Unauthorized
  - Kod błędu: `NOT_AUTHENTICATED`
  - Komunikat: "Authentication required"
  - Logowanie: `LogEventType.OFFER_LIST_FAIL`

- Brak uprawnień (nie jest sprzedawcą):
  - Kod: 403 Forbidden
  - Kod błędu: `INSUFFICIENT_PERMISSIONS`
  - Komunikat: "Seller role required"
  - Logowanie: `LogEventType.OFFER_LIST_FAIL`

- Błąd bazy danych lub inny wewnętrzny:
  - Kod: 500 Internal Server Error
  - Kod błędu: `FETCH_FAILED`
  - Komunikat: "Failed to fetch offers"
  - Logowanie: `LogEventType.OFFER_LIST_FAIL`

## 8. Rozważania dotyczące wydajności
- **Indeksy bazy danych**:
  - Upewnij się, że istnieją indeksy na `offers.seller_id`, `offers.category_id`, `offers.status`
  - Rozważ indeks dla wyszukiwania pełnotekstowego na `offers.title` i `offers.description`
- **Stronicowanie**: Ograniczenie liczby wyników do 100 na stronę
- **Optymalizacja zapytań**:
  - Użyj JOIN zamiast osobnych zapytań dla powiązanych danych
  - Używaj aliasów dla złożonych wyrażeń SQL
- **Buforowanie**:
  - Rozważ buforowanie częstych zapytań (np. aktywne oferty bez filtrów)

## 9. Etapy wdrożenia

1. **Utworzenie schematu zapytania**
   - Dodaj klasę `SellerOfferListQueryParams` w `schemas.py` opartą na `OfferListQueryParams`
   - Dodaj pole `status` opcjonalne typu `OfferStatus`
   - Dodaj walidację dla parametrów sortowania i limitów

2. **Utworzenie zależności autoryzacyjnej**
   - Utwórz funkcję `require_seller` jako zależność FastAPI
   - Sprawdza czy użytkownik jest zalogowany i ma rolę Seller
   - Zwraca użytkownika lub rzuca wyjątek HTTPException

3. **Implementacja serwisu ofert**
   - Dodaj metodę `get_seller_offers` w serwisie `OfferService`
   - Parametry: seller_id, search, category_id, status, sort, page, limit
   - Implementuj logikę filtrowania i sortowania
   - Obsłuż stronicowanie i obliczanie metadanych

4. **Implementacja endpointu**
   - Dodaj endpoint `/seller/offers` w `routes/offers.py`
   - Użyj zależności `require_seller`
   - Użyj `SellerOfferListQueryParams` do walidacji parametrów
   - Wywołaj serwis `OfferService.get_seller_offers`
   - Obsłuż potencjalne wyjątki i zwróć odpowiednie odpowiedzi błędów

5. **Implementacja logowania**
   - Dodaj wpisy logowania dla sukcesu i błędów
   - Używaj odpowiednich typów zdarzeń z `LogEventType`
   - Loguj istotne informacje: ID użytkownika, parametry zapytania (bez danych wrażliwych)

6. **Obsługa błędów**
   - Implementuj obsługę wyjątków dla wszystkich zidentyfikowanych scenariuszy błędów
   - Zwracaj standardowy format odpowiedzi błędu z kodem błędu i komunikatem

7. **Testowanie jednostkowe**
   - Przetestuj walidację parametrów zapytania
   - Przetestuj logikę autoryzacji
   - Przetestuj logikę filtrowania i sortowania
   - Przetestuj stronicowanie i obliczanie metadanych

8. **Testowanie integracyjne**
   - Przetestuj endpoint z różnymi kombinacjami parametrów
   - Przetestuj scenariusze błędów (np. nieprawidłowe parametry, brak uwierzytelnienia)
   - Przetestuj wydajność z dużymi zestawami danych

9. **Dokumentacja**
   - Zaktualizuj dokumentację API (np. Swagger)
   - Dodaj przykłady zapytań i odpowiedzi 