# Architektura UI dla Steambay MVP

## 1. Przegląd struktury UI

Architektura interfejsu użytkownika (UI) dla Steambay MVP została zaprojektowana z myślą o zapewnieniu intuicyjnej i efektywnej interakcji dla trzech głównych ról użytkowników: Kupującego (Buyer), Sprzedającego (Seller) oraz Administratora (Admin). Aplikacja będzie SPA (Single Page Application) zbudowaną w oparciu o React i Bootstrap 5, co zapewni responsywność i nowoczesny wygląd. Nawigacja jest dynamiczna, dostosowując dostępne opcje do roli zalogowanego użytkownika oraz jego statusu uwierzytelnienia. Stan aplikacji, w szczególności koszyk, będzie zarządzany z wykorzystaniem React Context API oraz localStorage, aby zapewnić trwałość danych po stronie klienta. Komunikacja z backendem odbywać się będzie poprzez zdefiniowane API RESTowe, z odpowiednią obsługą stanów ładowania, błędów oraz sukcesu operacji.

Podstawowa struktura katalogów projektu frontendowego będzie wyglądać następująco:

```
src/
├── assets/           # Statyczne zasoby (ikony, obrazy, fonty)
├── components/       # Komponenty UI wielokrotnego użytku
│   ├── common/       # Bardzo generyczne komponenty (np. Button, Input, Modal)
│   ├── layout/       # Komponenty struktury strony (np. Header, Footer, Sidebar)
│   └── shared/       # Komponenty specyficzne dla domeny, ale reużywalne (np. OfferCard, UserListItem)
├── contexts/         # Konteksty React (np. AuthContext, CartContext, NotificationContext)
├── hooks/            # Niestandardowe hooki React (np. useAuth, useCart, useApi)
├── pages/            # Komponenty reprezentujące poszczególne widoki/strony aplikacji
│   ├── auth/         # Strony związane z uwierzytelnianiem (Login, Register)
│   ├── account/      # Strony profilu użytkownika i zarządzania kontem
│   ├── offers/       # Strony listowania i szczegółów ofert
│   ├── cart/         # Strona koszyka i procesu finalizacji zakupu
│   ├── orders/       # Strony historii i szczegółów zamówień (dla Kupującego)
│   ├── sales/        # Strony zarządzania ofertami i historią sprzedaży (dla Sprzedającego)
│   ├── admin/        # Strony panelu administracyjnego
│   └── errors/       # Strony błędów (np. 404, 403)
├── routes/           # Konfiguracja routingu aplikacji (React Router)
├── services/         # Moduły odpowiedzialne za komunikację z API backendu
├── styles/           # Globalne style, zmienne CSS, konfiguracja Bootstrap
├── utils/            # Funkcje pomocnicze, walidatory, formatery
├── App.js            # Główny komponent aplikacji
└── index.js          # Punkt wejścia aplikacji
```

## 2. Lista widoków

Poniżej znajduje się lista kluczowych widoków aplikacji wraz z ich celami i elementami.

### Widoki wspólne (dostępne dla wszystkich lub wielu ról)

-   **Nazwa widoku:** HomePage (Strona Główna)
    -   **Ścieżka widoku:** `/`
    -   **Główny cel:** Umożliwienie użytkownikom przeglądania i wyszukiwania dostępnych ofert. Strona startowa aplikacji.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Pole wyszukiwania ofert.
        -   Lista aktywnych ofert (paginowana, domyślnie np. najnowsze lub losowe).
        -   Podstawowe informacje o ofertach: miniaturka zdjęcia, tytuł, cena.
    -   **Kluczowe komponenty widoku:** `SearchBar`, `OfferGrid`/`OfferList`, `OfferCard`, `Pagination`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Szybki dostęp do ofert, intuicyjne wyszukiwanie. Responsywność dla różnych urządzeń.
        -   Dostępność: Kontrast, nawigacja klawiaturą dla wyszukiwarki i listy ofert.
        -   Bezpieczeństwo: Wyświetlanie tylko aktywnych i nie moderowanych ofert dla niezalogowanych i Kupujących.

-   **Nazwa widoku:** OfferListPage (Lista Ofert / Wyniki Wyszukiwania)
    -   **Ścieżka widoku:** `/offers` (może zawierać parametry query dla wyszukiwania/filtrowania)
    -   **Główny cel:** Wyświetlanie listy ofert spełniających kryteria wyszukiwania lub filtrowania, z paginacją.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Lista ofert pasujących do kryteriów.
        -   Informacje o każdej ofercie: miniaturka zdjęcia (256x192px), tytuł, pierwsze 150 znaków opisu, kategoria, cena, nazwa sprzedającego (imię i nazwisko), ilość dostępnych sztuk, status oferty.
        -   Elementy sterujące paginacją (przyciski "Back", "Next", wskaźnik "Strona X z Y").
    -   **Kluczowe komponenty widoku:** `OfferGrid`/`OfferList`, `OfferCard`, `Pagination`, `SearchFilters` (jeśli dotyczy).
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Czytelne przedstawienie wyników, łatwa nawigacja między stronami.
        -   Dostępność: Zapewnienie dostępności dla elementów paginacji i kart ofert.
        -   Bezpieczeństwo: Widoczność ofert zgodna z rolą użytkownika i statusem oferty.

-   **Nazwa widoku:** OfferDetailPage (Szczegóły Oferty)
    -   **Ścieżka widoku:** `/offers/:offerId`
    -   **Główny cel:** Prezentacja pełnych informacji o wybranej ofercie, umożliwienie dodania do koszyka.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Wyeksponowane: Duże zdjęcie produktu, tytuł oferty.
        -   Mniej eksponowane: Pełny opis, cena (wyróżniona), kategoria, informacje o sprzedającym (imię i nazwisko), ilość dostępnych sztuk.
        -   Status oferty (kolorowy badge z ikoną).
        -   Przycisk "Dodaj do koszyka" (dla Kupujących, jeśli oferta jest aktywna i dostępna).
    -   **Kluczowe komponenty widoku:** `ImageGallery` (dla zdjęcia), `OfferInfoPanel`, `AddToCartButton`, `StatusBadge`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Przejrzysty układ, łatwy dostęp do kluczowych informacji i akcji.
        -   Dostępność: Odpowiednie tagi dla obrazów (alt), kontrast.
        -   Bezpieczeństwo: Przycisk "Dodaj do koszyka" widoczny i aktywny tylko dla uprawnionych użytkowników i dostępnych ofert.

-   **Nazwa widoku:** LoginPage (Logowanie)
    -   **Ścieżka widoku:** `/login`
    -   **Główny cel:** Umożliwienie zarejestrowanym użytkownikom zalogowania się do systemu.
    -   **Kluczowe informacje do wyświetlenia:** Formularz logowania (email, hasło). Link do strony rejestracji.
    -   **Kluczowe komponenty widoku:** `LoginForm`, `TextInput`, `Button`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Prosty i szybki proces logowania. Komunikaty o błędach (np. złe dane, konto nieaktywne).
        -   Dostępność: Etykiety dla pól, obsługa błędów walidacji.
        -   Bezpieczeństwo: Przesyłanie danych po HTTPS (konfiguracja serwera). Walidacja po stronie serwera.

-   **Nazwa widoku:** RegisterPage (Rejestracja)
    -   **Ścieżka widoku:** `/register`
    -   **Główny cel:** Umożliwienie nowym użytkownikom utworzenia konta (Kupujący lub Sprzedający).
    -   **Kluczowe informacje do wyświetlenia:** Formularz rejestracji (email, hasło, potwierdzenie hasła, wybór roli: Kupujący/Sprzedający). Link do strony logowania.
    -   **Kluczowe komponenty widoku:** `RegistrationForm`, `TextInput`, `SelectInput` (dla roli), `Button`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Jasne instrukcje, walidacja pól (np. polityka haseł po prawej stronie pola, czerwonym tekstem), informacja o sukcesie rejestracji.
        -   Dostępność: Etykiety, komunikaty walidacyjne.
        -   Bezpieczeństwo: Walidacja unikalności emaila i polityki haseł po stronie serwera.

-   **Nazwa widoku:** CartPage (Koszyk)
    -   **Ścieżka widoku:** `/cart`
    -   **Główny cel:** Umożliwienie użytkownikom przeglądania zawartości koszyka, modyfikacji ilości produktów i przejścia do finalizacji zakupu.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Lista produktów w koszyku (tytuł, cena jednostkowa, ilość, suma dla pozycji).
        -   Możliwość zmiany ilości (w granicach dostępności i limitu 20 produktów na cały koszyk).
        -   Możliwość usunięcia produktu z koszyka.
        -   Łączna suma do zapłaty.
        -   Przycisk "Przejdź do finalizacji".
    -   **Kluczowe komponenty widoku:** `CartItemsList`, `CartItem`, `QuantityInput`, `Button`, `OrderSummary`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Czytelne podsumowanie, łatwa modyfikacja koszyka. Informacja o pustym koszyku.
        -   Dostępność: Nawigacja klawiaturą po elementach koszyka.
        -   Bezpieczeństwo: Stan koszyka przechowywany w localStorage, walidacja dostępności i ilości przed finalizacją.

-   **Nazwa widoku:** ErrorPage (Strona Błędu)
    -   **Ścieżka widoku:** `/error` (lub dynamicznie w zależności od błędu np. `/404`, `/403`)
    -   **Główny cel:** Informowanie użytkownika o wystąpieniu błędu (np. strona nie znaleziona, brak uprawnień).
    -   **Kluczowe informacje do wyświetlenia:** Kod błędu, krótki opis problemu, link do strony głównej.
    -   **Kluczowe komponenty widoku:** `ErrorMessageDisplay`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Jasny komunikat, unikanie technicznego żargonu.
        -   Dostępność: Odpowiedni kontrast i czytelność.

### Widoki dla roli: Kupujący (Buyer)

-   **Nazwa widoku:** AccountPage (Moje Konto)
    -   **Ścieżka widoku:** `/account`
    -   **Główny cel:** Umożliwienie zalogowanemu użytkownikowi (Kupujący/Sprzedający/Admin) przeglądania danych swojego konta oraz zarządzania profilem (zmiana hasła, aktualizacja imienia/nazwiska).
    -   **Kluczowe informacje do wyświetlenia:**
        -   Aktualne dane profilu (email, rola, status, imię, nazwisko, data utworzenia) - pobierane z `GET /account`.
        -   Formularz zmiany hasła (stare hasło, nowe hasło, potwierdzenie nowego hasła).
        -   Formularz edycji imienia i nazwiska.
    -   **Kluczowe komponenty widoku:** `UserProfileInfo`, `ChangePasswordForm`, `UpdateProfileForm`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Prosty interfejs do przeglądania i aktualizacji danych.
        -   Dostępność: Etykiety dla pól, komunikaty walidacyjne.
        -   Bezpieczeństwo: Wymaganie starego hasła do zmiany.

-   **Nazwa widoku:** CheckoutPage (Finalizacja Zakupu)
    -   **Ścieżka widoku:** `/checkout`
    -   **Główny cel:** Przedstawienie podsumowania zamówienia przed przekierowaniem do mocka płatności.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Podsumowanie zamówienia: lista produktów, ilości, łączna kwota.
        -   Przycisk "Zapłać" (lub podobny, inicjujący transakcję backendową i przekierowanie).
    -   **Kluczowe komponenty widoku:** `OrderSummary`, `Button`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Ostatni krok przed "płatnością", jasne podsumowanie.
        -   Bezpieczeństwo: Walidacja koszyka po stronie serwera przed inicjacją transakcji.

-   **Nazwa widoku:** OrderConfirmationPage (Potwierdzenie Zamówienia)
    -   **Ścieżka widoku:** `/order/confirmation/:orderId` (lub podobna, np. po callbacku)
    -   **Główny cel:** Informowanie użytkownika o pomyślnym złożeniu zamówienia.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Komunikat o sukcesie (np. "Zamówienie złożone pomyślnie!").
        -   Ikona sukcesu.
        -   Podstawowe informacje o zamówieniu: lista zakupionych tytułów, ich ceny, ilość, cena łączna, nazwa sprzedającego dla każdej pozycji.
        -   Numer zamówienia.
        -   Link do historii zamówień.
    -   **Kluczowe komponenty widoku:** `SuccessMessage`, `OrderSummaryLite`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Pozytywne wzmocnienie, jasne informacje o zamówieniu.

-   **Nazwa widoku:** OrderHistoryPage (Historia Zamówień)
    -   **Ścieżka widoku:** `/orders`
    -   **Główny cel:** Umożliwienie Kupującemu przeglądania historii swoich zamówień.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Lista złożonych zamówień (ID zamówienia, data, status, łączna kwota).
        -   Paginacja.
        -   Link do szczegółów każdego zamówienia.
    -   **Kluczowe komponenty widoku:** `OrdersList`, `OrderItem`, `Pagination`, `StatusBadge`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Łatwy dostęp do poprzednich transakcji.

-   **Nazwa widoku:** OrderDetailPage (Szczegóły Zamówienia - dla Kupującego)
    -   **Ścieżka widoku:** `/orders/:orderId`
    -   **Główny cel:** Wyświetlenie szczegółowych informacji o konkretnym zamówieniu Kupującego.
    -   **Kluczowe informacje do wyświetlenia:**
        -   ID zamówienia, data, status (kolorowany).
        -   Lista zakupionych produktów (tytuł, ilość, cena jednostkowa w momencie zakupu, suma pozycji).
        -   Łączna kwota zamówienia.
        -   Informacje o sprzedawcy/sprzedawcach dla poszczególnych produktów.
    -   **Kluczowe komponenty widoku:** `OrderDetailsPanel`, `ItemsListInOrder`, `StatusBadge`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Pełny wgląd w szczegóły transakcji.

### Widoki dla roli: Sprzedający (Seller)

-   **Nazwa widoku:** MyOffersPage (Moje Oferty)
    -   **Ścieżka widoku:** `/seller/offers`
    -   **Główny cel:** Umożliwienie Sprzedającemu zarządzania swoimi ofertami.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Lista ofert Sprzedającego (tytuł, miniaturka zdjęcia 256x192px, cena, ilość sprzedanych sztuk, aktualny status).
        -   Opcje dla każdej oferty: Edytuj, Zmień status (active/inactive), Oznacz jako sprzedana, Usuń/Archiwizuj.
        -   Przycisk "Dodaj nową ofertę".
        -   Paginacja.
    -   **Kluczowe komponenty widoku:** `SellerOfferList`, `SellerOfferCard`, `Button`, `Pagination`, `StatusBadge`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Centralne miejsce do zarządzania asortymentem. Wymagane potwierdzenie dla krytycznych operacji (np. usunięcie).
        -   Bezpieczeństwo: Tylko właściciel oferty może nią zarządzać.

-   **Nazwa widoku:** CreateOfferPage (Tworzenie Oferty)
    -   **Ścieżka widoku:** `/offers/new`
    -   **Główny cel:** Umożliwienie Sprzedającemu dodania nowej oferty.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Formularz tworzenia oferty: Tytuł, Opis, Cena, Ilość (domyślnie 1), Kategoria (wybór z listy), Zdjęcie (pole na obrazek + przycisk "Upload", max 1024x768px PNG).
        -   Walidacja pól (po prawej stronie, czerwony tekst).
    -   **Kluczowe komponenty widoku:** `OfferForm`, `TextInput`, `TextArea`, `NumberInput`, `SelectInput` (dla kategorii), `FileUploadInput`, `Button`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Prowadzenie użytkownika przez proces tworzenia, jasne wymagania dotyczące pól.
        -   Dostępność: Etykiety, obsługa błędów walidacji.
        -   Bezpieczeństwo: Walidacja typów plików i rozmiarów po stronie klienta (wstępna) i serwera.

-   **Nazwa widoku:** EditOfferPage (Edycja Oferty)
    -   **Ścieżka widoku:** `/offers/:offerId/edit`
    -   **Główny cel:** Umożliwienie Sprzedającemu edycji istniejącej oferty (tylko status 'active' lub 'inactive').
    -   **Kluczowe informacje do wyświetlenia:** Formularz edycji oferty (jak w CreateOfferPage, wypełniony danymi oferty).
    -   **Kluczowe komponenty widoku:** `OfferForm` (zainicjalizowany danymi).
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Podobny do tworzenia, ale z istniejącymi danymi. Ograniczenie edycji dla ofert sprzedanych/archiwizowanych.

-   **Nazwa widoku:** SalesHistoryPage (Historia Sprzedaży)
    -   **Ścieżka widoku:** `/seller/sales`
    -   **Główny cel:** Umożliwienie Sprzedającemu przeglądania historii sprzedaży swoich produktów i zarządzania statusami zamówień.
    -   **Kluczowe informacje do wyświetlenia:**
        -   Lista zamówień zawierających produkty Sprzedającego (ID zamówienia, data, produkt, kupujący, status zamówienia, kwota).
        -   Możliwość zmiany statusu zamówienia (processing -> shipped -> delivered).
        -   Paginacja.
        -   Sortowanie (po dacie transakcji, łącznej cenie, nazwie kupującego).
    -   **Kluczowe komponenty widoku:** `SalesList`, `SaleItem`, `OrderStatusDropdown`, `Pagination`, `SortControls`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Przejrzysty wgląd w sprzedaż, łatwa zmiana statusów.

### Widoki dla roli: Administrator (Admin)

-   **Nazwa widoku:** AdminDashboardPage (Panel Administratora)
    -   **Ścieżka widoku:** `/admin`
    -   **Główny cel:** Centralny panel dla Administratora do zarządzania systemem.
    -   **Kluczowe informacje do wyświetlenia:** System zakładek prowadzący do poszczególnych sekcji zarządzania.
    -   **Kluczowe komponenty widoku:** `Tabs` (Users, Offers, Orders, Logs).

    -   **Nazwa pod-widoku/zakładki:** UsersManagementTab (Zarządzanie Użytkownikami)
        -   **Cel:** Przeglądanie listy użytkowników, blokowanie/odblokowywanie kont, nawigacja do szczegółów użytkownika.
        -   **Info:** Lista wszystkich użytkowników (ID, email, rola, status), opcje "Blokuj"/"Odblokuj". Możliwość przejścia do widoku `AdminUserDetailPage` dla wybranego użytkownika. Paginacja. Wymagane potwierdzenie dla akcji blokowania/odblokowywania.
        -   **Komponenty:** `UserListTable`, `UserActions`, `Pagination`, `ConfirmationModal`.

    -   **Nazwa pod-widoku/zakładki:** OffersManagementTab (Zarządzanie Ofertami)
        -   **Cel:** Przeglądanie wszystkich ofert i ich moderacja.
        -   **Info:** Lista wszystkich ofert (ID, tytuł, sprzedający, status, cena, ilość), opcja "Moderuj" (zmiana statusu na 'moderated') / "Odmoderuj". Paginacja.
        -   **Komponenty:** `AdminOfferListTable`, `OfferModerationActions`, `Pagination`, `StatusBadge`.

    -   **Nazwa pod-widoku/zakładki:** OrdersManagementTab (Zarządzanie Zamówieniami)
        -   **Cel:** Przeglądanie wszystkich zamówień w systemie, nawigacja do szczegółów zamówienia, możliwość anulowania zamówienia.
        -   **Info:** Lista wszystkich zamówień (ID, data, kupujący, sprzedający (info o produktach), status, kwota). Możliwość przejścia do widoku `AdminOrderDetailPage` dla wybranego zamówienia. Opcja "Anuluj zamówienie" (może być w tabeli lub w widoku szczegółów). Paginacja. Wymagane potwierdzenie anulowania.
        -   **Komponenty:** `AdminOrderListTable`, `OrderCancelAction`, `Pagination`, `StatusBadge`, `ConfirmationModal`.

    -   **Nazwa pod-widoku/zakładki:** LogsViewerTab (Przeglądarka Logów)
        -   **Cel:** Monitorowanie działania aplikacji i diagnozowanie problemów.
        -   **Info:** Tabela logów (data/godzina, typ zdarzenia, IP klienta, komunikat). Filtrowanie (po typie akcji, adresie IP, przedziale dat). Paginacja (100/strona).
        -   **Komponenty:** `LogsTable`, `LogFilters`, `Pagination`.

    -   **UX, dostępność i względy bezpieczeństwa (dla całego Panelu Admina):**
        -   UX: Przejrzysty i funkcjonalny interfejs dla zaawansowanych operacji. Konsekwentne rozmieszczenie akcji.
        -   Dostępność: Tabele z odpowiednimi nagłówkami, możliwość nawigacji klawiaturą.
        -   Bezpieczeństwo: Dostęp wyłącznie dla roli Admin. Potwierdzenia dla operacji modyfikujących dane.

-   **Nazwa widoku:** AdminUserDetailPage (Szczegóły Użytkownika - Admin)
    -   **Ścieżka widoku:** `/admin/users/:userId`
    -   **Główny cel:** Wyświetlenie szczegółowych informacji o konkretnym użytkowniku przez Administratora.
    -   **Kluczowe informacje do wyświetlenia:** ID, email, rola, status, imię, nazwisko, data utworzenia, data ostatniej modyfikacji. Hasło ani jego hash nie są wyświetlane.
    -   **Kluczowe komponenty widoku:** `UserDetailsPanel`, `UserInfoItem`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Czytelna prezentacja danych użytkownika.
        -   Dostępność: Odpowiednie nagłówki i struktura semantyczna.
        -   Bezpieczeństwo: Dostęp tylko dla roli Admin.

-   **Nazwa widoku:** AdminOrderDetailPage (Szczegóły Zamówienia - Admin)
    -   **Ścieżka widoku:** `/admin/orders/:orderId`
    -   **Główny cel:** Wyświetlenie szczegółowych informacji o konkretnym zamówieniu przez Administratora oraz umożliwienie jego anulowania.
    -   **Kluczowe informacje do wyświetlenia:** ID zamówienia, data, status (kolorowany), dane Kupującego, lista produktów (tytuł, ilość, cena), łączna kwota. Przycisk "Anuluj zamówienie" (jeśli status pozwala).
    -   **Kluczowe komponenty widoku:** `OrderDetailsPanel`, `ItemsListInOrder`, `StatusBadge`, `CancelOrderButton`, `ConfirmationModal`.
    -   **UX, dostępność i względy bezpieczeństwa:**
        -   UX: Pełny wgląd w zamówienie, jasna prezentacja statusu. Wymagane potwierdzenie przed anulowaniem.
        -   Dostępność: Przejrzysta struktura informacji.
        -   Bezpieczeństwo: Dostęp tylko dla roli Admin. Opcja anulowania dostępna tylko dla odpowiednich statusów zamówienia.

## 3. Mapa podróży użytkownika

### Główny przypadek użycia: Zakup produktu przez Kupującego

1.  **Wejście:** Użytkownik ląduje na `HomePage` (`/`).
2.  **Odkrywanie:**
    *   Przegląda listę ofert na `HomePage`.
    *   Lub używa `SearchBar` do wyszukania konkretnego produktu. Wyniki wyświetlane są na `OfferListPage` (`/offers?search=...`).
3.  **Wybór produktu:** Klika na interesującą go ofertę (`OfferCard`) na `HomePage` lub `OfferListPage`.
4.  **Szczegóły produktu:** Przechodzi na `OfferDetailPage` (`/offers/:offerId`), gdzie zapoznaje się ze szczegółami.
5.  **Dodanie do koszyka:** Klika `AddToCartButton`. Produkt jest dodawany do koszyka (stan w `localStorage`), a licznik na ikonie koszyka w `Header` jest aktualizowany.
6.  **Przegląd koszyka:** Klika ikonę koszyka w `Header`, przechodząc na `CartPage` (`/cart`).
7.  **Modyfikacja koszyka:** Na `CartPage` może zmienić ilość produktów (`QuantityInput`) lub usunąć pozycje. Widzi `OrderSummary`.
8.  **Finalizacja (Krok 1):** Klika przycisk "Przejdź do finalizacji".
9.  **Logowanie/Rejestracja (jeśli konieczne):** Jeśli użytkownik nie jest zalogowany, jest przekierowywany na `LoginPage` (`/login`). Po zalogowaniu (lub rejestracji na `RegisterPage` i zalogowaniu) wraca do procesu finalizacji.
10. **Finalizacja (Krok 2 - Podsumowanie):** Przechodzi na `CheckoutPage` (`/checkout`), gdzie widzi ostateczne podsumowanie zamówienia.
11. **Inicjacja Płatności:** Klika przycisk "Zapłać". Aplikacja komunikuje się z backendem (`POST /orders`), który inicjuje transakcję i zwraca URL do mocka płatności.
12. **Przekierowanie do Mocka Płatności:** Frontend przekierowuje użytkownika na zewnętrzny URL mocka płatności. (Stan aplikacji może wskazywać na oczekiwanie na powrót).
13. **Powrót z Mocka Płatności:** Po symulacji płatności, mock przekierowuje użytkownika z powrotem do aplikacji na zdefiniowany callback URL (`GET /payments/callback` obsługiwany przez backend).
14. **Potwierdzenie Zamówienia:**
    *   **Sukces:** Jeśli płatność się powiodła, backend aktualizuje status zamówienia. Frontend przekierowuje użytkownika na `OrderConfirmationPage` (`/order/confirmation/:orderId`), gdzie widzi potwierdzenie i podsumowanie zakupu. Koszyk jest czyszczony.
    *   **Porażka/Anulowanie:** Jeśli płatność nie powiodła się lub została anulowana, użytkownik widzi odpowiedni komunikat (np. `ToastNotification`) i może zostać na `CartPage` lub `CheckoutPage`. Koszyk nie jest czyszczony.
15. **Sprawdzenie Historii:** Użytkownik może później przejrzeć swoje zamówienie na `OrderHistoryPage` (`/orders`) i `OrderDetailPage` (`/orders/:orderId`).

## 4. Układ i struktura nawigacji

### Główny układ strony
Aplikacja będzie miała standardowy układ z trzema głównymi sekcjami:
1.  **Header (Nagłówek):** Umieszczony na górze każdej strony. Zawiera logo/nazwę aplikacji, główne linki nawigacyjne (dynamiczne w zależności od roli i statusu logowania), wyszukiwarkę (na stronie głównej lub globalnie dostępna) oraz ikonę koszyka.
2.  **Main Content (Główna Zawartość):** Centralna część strony, gdzie renderowane są widoki (komponenty z katalogu `pages/`).
3.  **Footer (Stopka):** Umieszczona na dole strony, zawierająca np. informacje o prawach autorskich.

### Pasek Nawigacyjny (Header)
-   **Logo/Nazwa aplikacji:** Zawsze widoczne, linkuje do `HomePage` (`/`).
-   **Nawigacja dla niezalogowanych:**
    -   "Strona Główna" (`/`)
    -   "Login" (`/login`)
    -   "Register" (`/register`)
-   **Nawigacja dla zalogowanego Kupującego (Buyer):**
    -   "Strona Główna" (`/`)
    -   "Moje Konto" (`/account`)
    -   "Moje Zamówienia" (`/orders`)
    -   "Logout" (akcja wylogowania)
-   **Nawigacja dla zalogowanego Sprzedającego (Seller):**
    -   "Strona Główna" (`/`)
    -   "Moje Konto" (`/account`)
    -   "Moje Oferty" (`/seller/offers`)
    -   "Historia Sprzedaży" (`/seller/sales`)
    -   "Logout" (akcja wylogowania)
-   **Nawigacja dla zalogowanego Administratora (Admin):**
    -   "Strona Główna" (`/`)
    -   "Moje Konto" (`/account`)
    -   "Admin Panel" (`/admin`)
    -   "Logout" (akcja wylogowania)
-   **Ikona Koszyka:** Zawsze widoczna, z licznikiem produktów. Linkuje do `CartPage` (`/cart`).

### Nawigacja w Panelu Administracyjnym (`/admin`)
-   Realizowana za pomocą komponentu zakładek (`Tabs`) w ramach `AdminDashboardPage`.
-   Zakładki: "Zarządzanie Użytkownikami", "Zarządzanie Ofertami", "Przeglądanie Zamówień", "Przeglądarka Logów".

### Ochrona Tras
-   Trasy wymagające uwierzytelnienia (np. `/account`, `/checkout`, `/orders`) będą chronione. Niezalogowany użytkownik próbujący uzyskać do nich dostęp zostanie przekierowany na `LoginPage`.
-   Trasy wymagające specyficznej roli (np. `/seller/*`, `/admin/*`) będą dodatkowo chronione. Użytkownik bez odpowiednich uprawnień zostanie przekierowany na `ErrorPage` (np. 403 Forbidden) lub `HomePage`.

## 5. Kluczowe komponenty

-   **`Button`:** Standardowy komponent przycisku z różnymi wariantami (primary, secondary, danger), obsługujący stany (disabled, loading).
-   **`TextInput`, `NumberInput`, `TextArea`, `SelectInput`, `FileUploadInput`:** Komponenty formularzy z walidacją i obsługą błędów.
-   **`OfferCard`:** Komponent wyświetlający pojedynczą ofertę na listach. Zawiera miniaturkę, tytuł, cenę, podstawowe info.
-   **`Pagination`:** Komponent do nawigacji po stronach list. (Przyciski "Back", "Next", wskaźnik "Strona X z Y").
-   **`StatusBadge`:** Komponent do wyświetlania statusów ofert i zamówień za pomocą kolorowych etykiet i opcjonalnych ikon.
    -   Statusy ofert: Active (zielony ✓), Inactive (szary ⏸), Sold (niebieski 💰), Moderated (czerwony ⚠), Archived (ciemnoszary 🗄).
    -   Statusy zamówień: Shipped/Delivered (zielone), Pending_payment/Processing (żółte), Cancelled/Failed (czerwone).
-   **`Modal` / `ConfirmationDialog`:** Do wyświetlania dialogów potwierdzenia dla krytycznych akcji (np. usunięcie, blokowanie).
-   **`ToastNotification`:** Do wyświetlania krótkich komunikatów o sukcesie lub błędzie.
-   **`SearchBar`:** Komponent pola wyszukiwania.
-   **`Table`:** Generyczny komponent tabeli do wyświetlania danych listowych, np. w panelu admina, z możliwością sortowania.
-   **`Tabs`:** Komponent zakładek do organizacji treści, np. w panelu admina.
-   **`Spinner` / `SkeletonLoader`:** Do wskazywania stanu ładowania danych.
-   **`Header`:** Główny pasek nawigacyjny aplikacji.
-   **`Footer`:** Stopka aplikacji.
-   **`ProtectedRoute` / `RoleRoute`:** Komponenty wyższego rzędu (HOC) lub dedykowane komponenty routingu do ochrony tras.
-   **`Form`:** Komponent opakowujący formularze, integrujący się z React Hook Form.
-   **`ImageUploader`:** Komponent do obsługi uploadu zdjęć w formularzach ofert, z podglądem i walidacją.

Architektura ta ma na celu stworzenie solidnych podstaw pod dalszy rozwój interfejsu użytkownika Steambay MVP, z uwzględnieniem wszystkich kluczowych wymagań funkcjonalnych i niefunkcjonalnych. 