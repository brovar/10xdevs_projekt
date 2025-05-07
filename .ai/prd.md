# Dokument wymagań produktu (PRD) - Steambay MVP

## 1. Przegląd produktu

Steambay (MVP) to uproszczona aplikacja internetowa symulująca platformę e-commerce. Jej głównym celem jest dostarczenie rekruterom i zespołom technicznym automatycznie wdrażanego, izolowanego środowiska do oceny umiejętności kandydatów na pentesterów w zakresie identyfikacji podstawowych podatności i zrozumienia logiki biznesowej aplikacji webowych.

Aplikacja będzie dostarczana jako pojedynczy obraz Docker, zawierający backend (Python 3 + FastAPI), frontend (JavaScript + React) oraz lekką bazę danych SQL. Środowisko inicjalizuje się za pomocą skryptu startowego, który tworzy strukturę bazy danych oraz wstępne dane, w tym konta użytkowników (statyczne dla kandydatów i generowane) oraz kategorie produktów.

Kluczowym założeniem MVP jest skupienie się na podstawowej funkcjonalności e-commerce i zapewnienie stabilnego, powtarzalnego środowiska. MVP celowo nie będzie zawierać wbudowanych podatności bezpieczeństwa; mechanizmy flag podatności mogą zostać dodane w przyszłych iteracjach. Interfejs użytkownika będzie prosty, zgodny z podstawowymi wytycznymi WCAG i zoptymalizowany pod kątem przeglądarek Chrome, Firefox i Edge. Dane aplikacji są przechowywane w kontenerze i nie są trwałe po jego usunięciu.

## 2. Problem użytkownika

Obecnie rekruterzy i zespoły techniczne zajmujące się bezpieczeństwem aplikacji stają przed wyzwaniem szybkiego i efektywnego przygotowania realistycznych, ale kontrolowanych środowisk testowych dla kandydatów na pentesterów. Konfiguracja typowej aplikacji e-commerce z jej zależnościami (baza danych, serwer webowy, usługi zewnętrzne) jest czasochłonna i kosztowna. Ponadto, manualne wprowadzanie danych testowych (użytkownicy, produkty, zamówienia) jest monotonne i podatne na błędy, co opóźnia proces rekrutacji i utrudnia standaryzację oceny kandydatów. Gotowe do użycia rozwiązania tego typu posiadają stałą kombinację podatności, co negatywnie wpływa na wiarygodność wniosków wyciąganych z ocen kandydatów.

## 3. Wymagania funkcjonalne

### 3.1. Role użytkowników i zarządzanie kontami
-   Trzy role użytkowników: Kupujący (Buyer), Sprzedający (Seller), Administrator (Admin).
-   Rejestracja: Wymagany unikalny adres email (używany jako login) i hasło.
    -   Hasło: minimum 10 znaków, musi zawierać małą literę, dużą literę oraz cyfrę lub znak specjalny. Walidacja tylko po stronie backendu.
    -   Brak weryfikacji online adresu email.
-   Logowanie: Użycie adresu email i hasła.
-   Zarządzanie sesją: Sesje po stronie serwera z wykorzystaniem ciasteczek sesyjnych (HttpOnly, Secure), czas wygaśnięcia: 1 tydzień.
-   Edycja profilu (Kupujący, Sprzedający): Możliwość zmiany hasła.
-   Statusy użytkownika: Aktywny (Active), Nieaktywny (Inactive - blokowany przez Admina).
-   Zarządzanie użytkownikami (Admin):
    -   Przeglądanie listy użytkowników (z paginacją).
    -   Podgląd szczegółów użytkownika.
    -   Blokowanie (zmiana statusu na Inactive) i odblokowywanie (zmiana statusu na Active) kont użytkowników.
    -   Dezaktywacja konta sprzedawcy powoduje anulowanie jego aktywnych zamówień i ustawienie jego ofert jako 'inactive'.
    -   Ręczne tworzenie/usuwanie kont testowych (w ramach panelu admina lub skryptu inicjalizującego).

### 3.2. Zarządzanie ofertami
-   Tworzenie oferty (Sprzedający):
    -   Pola: Tytuł (tekst), Opis (tekst), Cena (Decimal/Numeric, wyświetlana z symbolem USD), Zdjęcie (plik PNG, max 1024x768px), Ilość (liczba całkowita, domyślnie 1), Kategoria (wybór z predefiniowanej listy 20 statycznych kategorii).
    -   Zdjęcia przechowywane w systemie plików kontenera (`/app/media/offers/<offer_id>/`). Serwowane przez backend.
    -   Domyślny status nowej oferty: 'inactive'.
-   Edycja oferty (Sprzedający):
    -   Możliwość edycji wszystkich pól oferty ze statusem 'active' lub 'inactive'.
    -   Nie można edytować oferty ze statusem 'sold' lub 'archived'.
-   Usuwanie oferty (Sprzedający):
    -   Próba usunięcia oferty, która ma powiązane zamówienia, zmienia jej status na 'archived'. Oferta staje się niewidoczna w wyszukiwaniu.
    -   Usunięcie oferty bez zamówień usuwa ją fizycznie (lub oznacza jako usuniętą).
-   Statusy oferty:
    -   `active`: Widoczna dla kupujących, możliwa do zakupu. Ustawiany przez Sprzedającego.
    -   `inactive`: Niewidoczna dla kupujących, możliwa do edycji przez Sprzedającego. Ustawiany przez Sprzedającego.
    -   `sold`: Ustawiany automatycznie, gdy ilość osiągnie 0 lub ręcznie przez Sprzedającego (co zeruje ilość). Nieodwracalny. Oferta niewidoczna dla kupujących.
    -   `moderated`: Ustawiany przez Admina. Ukrywa ofertę, czyniąc ją niewidoczną dla Kupujących.
    -   `archived`: Ustawiany automatycznie przy próbie usunięcia oferty z zamówieniami. Niewidoczna w wyszukiwaniu.
-   Przeglądanie ofert (Wszyscy zalogowani):
    -   Lista ofert z paginacją (100 na stronę).
    -   Podgląd szczegółów oferty (tylko aktywne oferty dla Kupujących, chyba że moderowane).
-   Wyszukiwanie ofert (Wszyscy zalogowani):
    -   Proste wyszukiwanie tekstowe (case-insensitive, częściowe dopasowanie) w polach Tytuł i Opis.
    -   Sortowanie wyników wg trafności (prosty algorytm np. liczba wystąpień, malejąco).
    -   Paginacja wyników (100 na stronę).
-   Moderacja ofert (Admin):
    -   Możliwość zmiany statusu oferty na 'moderated', ukrywając ją przed Kupującymi.

### 3.3. Proces zakupowy
-   Koszyk:
    -   Implementowany po stronie przeglądarki klienta (np. Local Storage). Dostępny również dla niezalogowanych użytkowników.
    -   Dodawanie/usuwanie ofert do/z koszyka.
    -   Po zalogowaniu stan koszyka pozostaje bez zmian.
    -   Walidacja zawartości koszyka (dostępność oferty, ilość) przy przejściu do podsumowania (przed "płatnością").
-   Finalizacja zakupu ("Checkout"):
    -   Podsumowanie zamówienia.
    -   Backend inicjuje transakcję (status zamówienia np. 'pending_payment').
    -   Backend generuje URL do zewnętrznego mocka płatności (zawierający ID transakcji, kwotę, adresy URL callback).
    -   Frontend przekierowuje użytkownika do mocka płatności.
    -   Mock płatności symuluje proces (np. opóźnienie) i przekierowuje użytkownika z powrotem do aplikacji (na podany callback URL) ze statusem: `success`, `fail` lub `cancelled`.
    -   Backend obsługuje callback:
        -   Weryfikuje transakcję.
        -   Aktualizuje status zamówienia (`processing`, `failed`, `cancelled`).
        -   W przypadku sukcesu (`success`): aktualizuje ilość produktu w ofercie, aktualizuje licznik zakupów oferty (osobne pole). Loguje zdarzenie `PAYMENT_SUCCESS`.
        -   W przypadku porażki (`fail`): Loguje zdarzenie `PAYMENT_FAIL`.
        -   W przypadku anulowania (`cancelled`): Loguje zdarzenie `ORDER_PLACE_FAIL`.

### 3.4. Zamówienia i historia
-   Statusy zamówienia: `pending_payment`, `processing`, `shipped`, `delivered`, `cancelled`, `failed`.
    -   Sprzedający może zmieniać statusy `processing` -> `shipped` -> `delivered`.
    -   Admin może anulować zamówienie (`cancelled`).
    -   Statusy `pending_payment`, `failed`, `cancelled` (z płatności) ustawiane automatycznie.
-   Historia zamówień (Kupujący): Lista złożonych zamówień z ich statusami i szczegółami.
-   Historia sprzedaży (Sprzedający): Lista zamówień dotyczących ofert sprzedającego, z możliwością zmiany statusu zamówienia.
-   Przeglądanie zamówień (Admin): Dostęp do listy wszystkich zamówień i ich szczegółów (tylko do odczytu).

### 3.5. Panel administracyjny
-   Dostępny tylko dla roli Admin.
-   Sekcje: Zarządzanie użytkownikami, Przeglądanie ofert, Przeglądanie zamówień, Przeglądarka logów.
-   Funkcjonalności:
    -   Lista użytkowników z opcją blokowania/odblokowywania.
    -   Lista wszystkich ofert z opcją moderacji (zmiana statusu na 'moderated').
    -   Lista wszystkich zamówień (tylko podgląd).
    -   Przeglądarka logów aplikacji.

### 3.6. Logowanie zdarzeń
-   Logi zapisywane do dedykowanej tabeli w bazie danych.
-   Brak rotacji logów w MVP.
-   Format logu: Tekstowy, zawierający: Data/godzina (timestamp), Typ zdarzenia (np. USER_LOGIN), Adres IP klienta, Komunikat (konkatenacja istotnych pól związanych ze zdarzeniem).
-   Logowane zdarzenia: `USER_LOGIN`, `USER_REGISTER`, `PASSWORD_CHANGE`, `OFFER_CREATE`, `OFFER_EDIT`, `OFFER_STATUS_CHANGE`, `ORDER_PLACE_START`, `ORDER_PLACE_SUCCESS`, `ORDER_PLACE_FAIL`, `PAYMENT_SUCCESS`, `PAYMENT_FAIL`, `OFFER_MODERATED`, `USER_ACTIVATED`, `USER_DEACTIVATED`.
-   Dostęp do logów: Panel administracyjny z możliwością filtrowania (po dacie, adresie IP, typie zdarzenia) i paginacją (100 wpisów na stronę).

### 3.7. Dane inicjalizacyjne
-   Skrypt startowy uruchamiany przy pierwszym starcie kontenera.
-   Tworzy strukturę bazy danych.
-   Tworzy 20 statycznych kategorii produktów.
-   Tworzy 6 statycznych kont użytkowników dla kandydatów (2x Buyer, 2x Seller, 2x Admin) ze stałymi, predefiniowanymi hasłami i pewną historią transakcji/ofert.
-   Opcjonalnie generuje dodatkowe dane (użytkownicy, oferty, zamówienia) przy użyciu biblioteki typu Faker dla zapewnienia realizmu i spójności relacyjnej.

### 3.8. Wymagania niefunkcjonalne (wybrane)
-   Interfejs: Webowy, responsywny (podstawowy poziom), działający poprawnie na aktualnych wersjach Chrome, Firefox, Edge.
-   Zgodność: Podstawowa zgodność z WCAG (np. kontrast, nawigacja klawiaturą).
-   Wydajność: Aplikacja powinna działać płynnie przy symulowanym obciążeniu generowanym przez pojedynczego użytkownika (kandydata). Czas startu kontenera < 2 min.
-   Bezpieczeństwo: Brak celowych podatności. Hasła hashowane. Użycie ciasteczek HttpOnly/Secure. Podstawowa walidacja danych wejściowych.
-   Wdrożenie: Pojedynczy kontener Docker. Zależności instalowane podczas budowania obrazu.
-   API: Komunikacja Frontend-Backend wyłącznie przez API RESTowe. Odpowiedzi błędów w formacie JSON: `{ "error_code": "KOD_BLEDU", "message": "Opis błędu.", "details": { ... } }`. API nie wersjonowane w MVP.

## 4. Granice produktu (Co NIE wchodzi w zakres MVP)

-   Integracja z rzeczywistymi systemami płatności (Stripe, PayPal itp.). Używany jest jedynie mock.
-   Rozbudowane wyszukiwanie i filtrowanie (np. po kategoriach, atrybutach, zaawansowane sortowanie).
-   System ocen i recenzji produktów.
-   Wewnętrzny system komunikacji (chat) między kupującymi a sprzedającymi.
-   Obsługa wielu walut, przeliczanie kursów, obsługa podatków czy prowizji.
-   Aplikacje mobilne (natywne lub PWA). Dostępny jest tylko interfejs webowy.
-   Architektura multitenant. Aplikacja działa jako pojedyncza instancja ze wspólną bazą danych.
-   Automatyczne procesy CI/CD.
-   Integracja z zewnętrznymi systemami ATS (Applicant Tracking Systems).
-   Zaawansowane mechanizmy analizy i raportowania (dashboardy BI, eksporty danych do PDF/CSV).
-   Mechanizmy Rate Limitingu.
-   Celowe wprowadzanie podatności bezpieczeństwa.
-   Edycja kategorii produktów przez UI.
-   Trwałe przechowywanie danych poza cyklem życia kontenera (brak trwałych wolumenów Docker).

## 5. Historyjki użytkowników

### 5.1. Rejestracja i Logowanie
-   ID: US-001
-   Tytuł: Rejestracja nowego użytkownika (Kupujący/Sprzedający)
-   Opis: Jako nowy użytkownik, chcę móc zarejestrować konto w systemie używając adresu email i hasła, abym mógł korzystać z funkcji aplikacji.
-   Kryteria akceptacji:
    -   Formularz rejestracji zawiera pola na adres email i hasło (oraz potwierdzenie hasła) oraz pole wyboru typu konta (Kupujący/Sprzedający)
    -   Walidacja po stronie backendu sprawdza unikalność adresu email.
    -   Walidacja po stronie backendu sprawdza zgodność hasła z polityką (min. 10 znaków, mała/duża litera, cyfra/znak specjalny).
    -   Po pomyślnej rejestracji użytkownik jest informowany o sukcesie i może się zalogować.
    -   W przypadku błędu (np. email zajęty, hasło niespełniające wymagań) wyświetlany jest odpowiedni komunikat.
    -   Nowe konto ma domyślnie status 'Active'.

-   ID: US-002
-   Tytuł: Logowanie do systemu
-   Opis: Jako zarejestrowany użytkownik (Kupujący, Sprzedający, Admin), chcę móc zalogować się do aplikacji używając mojego adresu email i hasła, aby uzyskać dostęp do spersonalizowanych funkcji.
-   Kryteria akceptacji:
    -   Formularz logowania zawiera pola na adres email i hasło.
    -   Po podaniu poprawnych danych użytkownik jest zalogowany i przekierowany do odpowiedniego widoku (np. dashboardu, strony głównej).
    -   W przypadku podania błędnych danych wyświetlany jest komunikat o nieprawidłowym loginie lub haśle.
    -   Po pomyślnym logowaniu ustawiane jest ciasteczko sesyjne (HttpOnly, Secure).
    -   Logowane jest zdarzenie `USER_LOGIN`.

-   ID: US-003
-   Tytuł: Zmiana hasła
-   Opis: Jako zalogowany użytkownik (Kupujący, Sprzedający), chcę móc zmienić swoje hasło w ustawieniach profilu, aby zwiększyć bezpieczeństwo konta.
-   Kryteria akceptacji:
    -   Użytkownik musi podać swoje stare hasło oraz nowe hasło (zgodne z polityką) i jego potwierdzenie.
    -   Walidacja sprawdza poprawność starego hasła.
    -   Walidacja sprawdza zgodność nowego hasła z polityką.
    -   Po pomyślnej zmianie hasło zostaje zaktualizowane w bazie danych.
    -   Logowane jest zdarzenie `PASSWORD_CHANGE`.

-   ID: US-024
-   Tytuł: Wylogowanie z systemu
-   Opis: Jako zalogowany użytkownik (Kupujący, Sprzedający, Admin), chcę móc się wylogować z aplikacji, aby bezpiecznie zakończyć moją sesję.
-   Kryteria akceptacji:
    -   W interfejsie użytkownika dostępny jest przycisk lub link \\"Wyloguj\\".
    -   Kliknięcie \\"Wyloguj\\" wysyła żądanie do endpointu `POST /auth/logout`.
    -   Po pomyślnym wylogowaniu sesja użytkownika (ciasteczko) jest usuwana lub unieważniana.
    -   Użytkownik jest przekierowywany na stronę główną (`/`) lub stronę logowania (`/login`).
    -   Po wylogowaniu użytkownik traci dostęp do sekcji wymagających uwierzytelnienia.
    -   Endpoint wylogowania jest chroniony przed atakami CSRF.

-   ID: US-025
-   Tytuł: Przeglądanie danych swojego konta
-   Opis: Jako zalogowany użytkownik (Kupujący, Sprzedający, Admin), chcę móc zobaczyć informacje o moim koncie, aby zweryfikować swoje dane.
-   Kryteria akceptacji:
    -   W aplikacji dostępna jest sekcja \\"Moje Konto\\" (dostępna pod ścieżką `/account`).
    -   Widok pobiera dane z endpointu `GET /account`.
    -   Wyświetlane są informacje: adres email, rola (Buyer/Seller/Admin), status (Active/Inactive), imię i nazwisko (jeśli podane), data utworzenia konta.
    -   Widoczne są opcje umożliwiające edycję profilu (np. zmiana hasła).

-   ID: US-026
-   Tytuł: Aktualizacja danych profilu (imię, nazwisko)
-   Opis: Jako zalogowany użytkownik (Kupujący, Sprzedający), chcę móc zaktualizować swoje imię i nazwisko w ustawieniach profilu, aby moje dane były aktualne.
-   Kryteria akceptacji:
    -   W widoku \\"Moje Konto\\" (`/account`) znajduje się formularz umożliwiający edycję imienia i nazwiska.
    -   Po wprowadzeniu zmian i zapisaniu, wysyłane jest żądanie `PATCH /account` z nowymi danymi.
    -   Backend waliduje długość imienia i nazwiska (np. max 100 znaków).
    -   Po pomyślnej aktualizacji, zmiany są zapisywane w bazie danych i widoczne w profilu użytkownika.
    -   Wyświetlane jest powiadomienie o sukcesie aktualizacji.
    -   Logowane jest zdarzenie `USER_PROFILE_UPDATE`.

### 5.2. Zarządzanie Ofertami (Sprzedający)
-   ID: US-004
-   Tytuł: Tworzenie nowej oferty
-   Opis: Jako Sprzedający, chcę móc dodać nową ofertę produktu, podając tytuł, opis, cenę, ilość, kategorię i opcjonalnie zdjęcie, aby móc sprzedawać produkty.
-   Kryteria akceptacji:
    -   Formularz tworzenia oferty zawiera wymagane pola: Tytuł, Opis, Cena (Decimal, >0), Ilość (Integer, >0), Kategoria (lista rozwijana z 20 statycznych kategorii).
    -   Opcjonalne pole do uploadu zdjęcia (PNG, walidacja rozmiaru max 1024x768px).
    -   Po pomyślnym dodaniu oferta jest zapisywana w bazie danych ze statusem 'inactive'.
    -   Zdjęcie (jeśli dodane) jest zapisywane w systemie plików i powiązane z ofertą.
    -   Sprzedający widzi nowo dodaną ofertę na liście swoich ofert.
    -   Logowane jest zdarzenie `OFFER_CREATE`.

-   ID: US-005
-   Tytuł: Edycja istniejącej oferty
-   Opis: Jako Sprzedający, chcę móc edytować szczegóły moich ofert (tytuł, opis, cena, ilość, kategoria, zdjęcie), które mają status 'active' lub 'inactive', aby zaktualizować informacje o produkcie.
-   Kryteria akceptacji:
    -   Sprzedający może wybrać ofertę do edycji ze swojej listy.
    -   Formularz edycji pozwala na zmianę wszystkich pól (w tym podmianę/usunięcie zdjęcia).
    -   Edycja jest możliwa tylko dla ofert ze statusem 'active' lub 'inactive'.
    -   Po zapisaniu zmian zaktualizowane dane są widoczne w szczegółach oferty i na listach.
    -   Logowane jest zdarzenie `OFFER_EDIT`.

-   ID: US-006
-   Tytuł: Zmiana statusu oferty (Aktywna/Nieaktywna)
-   Opis: Jako Sprzedający, chcę móc zmieniać status moich ofert między 'active' a 'inactive', aby kontrolować ich widoczność dla kupujących.
-   Kryteria akceptacji:
    -   Na liście ofert Sprzedającego jest opcja zmiany statusu dla ofert 'active' i 'inactive'.
    -   Zmiana statusu na 'active' czyni ofertę widoczną w wyszukiwarce i na listach dla Kupujących.
    -   Zmiana statusu na 'inactive' ukrywa ofertę przed Kupującymi.
    -   Logowane jest zdarzenie `OFFER_STATUS_CHANGE` ze starym i nowym statusem.

-   ID: US-007
-   Tytuł: Oznaczenie oferty jako 'sold'
-   Opis: Jako Sprzedający, chcę móc ręcznie oznaczyć ofertę jako 'sold', aby wycofać ją ze sprzedaży, nawet jeśli ilość nie jest zerowa.
-   Kryteria akceptacji:
    -   Sprzedający ma opcję oznaczenia oferty jako 'sold'.
    -   Akcja ustawia status oferty na 'sold' i zeruje jej ilość.
    -   Oferta ze statusem 'sold' nie jest widoczna dla kupujących i nie można jej edytować.
    -   Status 'sold' jest nieodwracalny.
    -   Logowane jest zdarzenie `OFFER_STATUS_CHANGE`.

-   ID: US-008
-   Tytuł: Usuwanie/Archiwizacja oferty
-   Opis: Jako Sprzedający, chcę móc usunąć ofertę, której już nie oferuję, aby utrzymać porządek na liście moich produktów.
-   Kryteria akceptacji:
    -   Sprzedający ma opcję usunięcia oferty.
    -   Jeśli oferta nie ma powiązanych zamówień, jest usuwana z systemu.
    -   Jeśli oferta ma powiązane zamówienia, jej status jest zmieniany na 'archived', staje się niewidoczna w wyszukiwaniu i nie można jej edytować.
    -   Logowane jest zdarzenie `OFFER_STATUS_CHANGE` (jeśli archiwizowana) lub inne zdarzenie usunięcia.

-   ID: US-009
-   Tytuł: Przeglądanie historii sprzedaży
-   Opis: Jako Sprzedający, chcę móc przeglądać listę zamówień dotyczących moich ofert, wraz z ich statusami, aby śledzić sprzedaż.
-   Kryteria akceptacji:
    -   Dostępna jest sekcja "Historia Sprzedaży" lub podobna.
    -   Wyświetlana jest lista zamówień powiązanych z ofertami Sprzedającego.
    -   Lista zawiera kluczowe informacje: ID zamówienia, data, produkt, kupujący (nazwa/email), status, kwota.
    -   Lista jest paginowana.

-   ID: US-010
-   Tytuł: Zmiana statusu zamówienia przez Sprzedającego
-   Opis: Jako Sprzedający, chcę móc zmieniać statusy zamówień dla moich produktów (z 'processing' na 'shipped', z 'shipped' na 'delivered'), aby informować kupującego o postępie realizacji.
-   Kryteria akceptacji:
    -   W widoku historii sprzedaży/szczegółów zamówienia jest opcja zmiany statusu.
    -   Możliwe przejścia statusów: `processing` -> `shipped`, `shipped` -> `delivered`.
    -   Zmiana statusu jest odzwierciedlana w systemie i widoczna dla Kupującego.
    -   Logowane jest zdarzenie zmiany statusu zamówienia.

### 5.3. Przeglądanie i Wyszukiwanie Ofert (Wszyscy Zalogowani)
-   ID: US-011
-   Tytuł: Przeglądanie listy dostępnych ofert
-   Opis: Jako zalogowany użytkownik (Kupujący, Sprzedający, Admin), chcę móc przeglądać listę ofert, aby znaleźć interesujące produkty.
-   Kryteria akceptacji:
    -   Domyślny widok po zalogowaniu (lub dedykowana strona) pokazuje listę ofert.
    -   Kupujący widzą tylko oferty ze statusem 'active'.
    -   Sprzedający widzą swoje oferty. Admin widzi wszystkie oferty (wszystkie statusy).
    -   Lista zawiera podstawowe informacje: zdjęcie (miniaturka), tytuł, cena.
    -   Lista jest paginowana (100 ofert na stronę).

-   ID: US-012
-   Tytuł: Wyszukiwanie ofert
-   Opis: Jako zalogowany użytkownik, chcę móc wyszukiwać oferty po słowach kluczowych w tytule lub opisie, aby szybko znaleźć konkretne produkty.
-   Kryteria akceptacji:
    -   Pole wyszukiwania jest dostępne na stronie z listą ofert.
    -   Wyszukiwanie działa case-insensitive i dopasowuje częściowe ciągi znaków w tytule i opisie.
    -   Wyniki wyszukiwania (tylko oferty 'active' dla Kupujących) są wyświetlane w formie listy.
    -   Wyniki są sortowane wg trafności (malejąco).
    -   Wyniki są paginowane (100 na stronę).

-   ID: US-013
-   Tytuł: Przeglądanie szczegółów oferty
-   Opis: Jako zalogowany użytkownik, chcę móc zobaczyć szczegółowe informacje o ofercie, klikając na nią na liście, aby dowiedzieć się więcej o produkcie.
-   Kryteria akceptacji:
    -   Kliknięcie na ofertę na liście przenosi do widoku szczegółów.
    -   Widok szczegółów pokazuje: Tytuł, Opis, Cenę, Zdjęcie (większe), Ilość dostępną (jeśli dotyczy), Kategorię, Sprzedającego (nazwa).
    -   Kupujący widzą tylko szczegóły ofert 'active'.
    -   Kupujący widzą przycisk "Dodaj do koszyka" (jeśli ilość > 0).

### 5.4. Koszyk i Zakup (Kupujący)
-   ID: US-014
-   Tytuł: Dodawanie oferty do koszyka
-   Opis: Jako Kupujący, chcę móc dodać aktywną ofertę do mojego koszyka, aby móc ją później zakupić.
-   Kryteria akceptacji:
    -   Przycisk "Dodaj do koszyka" jest widoczny na stronie szczegółów aktywnej oferty (z ilością > 0).
    -   Kliknięcie przycisku dodaje ofertę (ID, ilość=1) do koszyka przechowywanego w Local Storage.
    -   Użytkownik otrzymuje wizualne potwierdzenie dodania do koszyka (np. zmiana ikony koszyka, komunikat).
    -   Można dodać ten sam produkt wielokrotnie (zwiększając ilość) do momentu osiągnięcia dostępnej ilości.

-   ID: US-015
-   Tytuł: Przeglądanie zawartości koszyka
-   Opis: Jako Kupujący, chcę móc zobaczyć zawartość mojego koszyka, aby sprawdzić wybrane produkty i ich łączną wartość przed zakupem.
-   Kryteria akceptacji:
    -   Dostępny jest link/przycisk do widoku koszyka.
    -   Widok koszyka pokazuje listę dodanych ofert (nazwa, cena jednostkowa, ilość, łączna cena dla pozycji).
    -   Możliwość zmiany ilości produktu w koszyku (w granicach dostępności).
    -   Możliwość usunięcia produktu z koszyka.
    -   Wyświetlana jest łączna suma do zapłaty za wszystkie produkty w koszyku.
    -   Widoczny jest przycisk "Przejdź do finalizacji" lub podobny.

-   ID: US-016
-   Tytuł: Finalizacja zakupu (Checkout)
-   Opis: Jako Kupujący, chcę móc sfinalizować zakup produktów z mojego koszyka, przechodząc przez proces "płatności" (mock), aby złożyć zamówienie.
-   Kryteria akceptacji:
    -   Kliknięcie "Przejdź do finalizacji" w koszyku inicjuje proces checkout.
    -   System waliduje zawartość koszyka (dostępność ofert, ilości). W razie problemów wyświetla błąd.
    -   Wyświetlane jest podsumowanie zamówienia (produkty, ilości, łączna kwota).
    -   Kliknięcie przycisku "Zapłać" (lub podobnego) wysyła żądanie do backendu w celu zainicjowania transakcji. Logowane jest zdarzenie `ORDER_PLACE_START`.
    -   Backend tworzy zamówienie w statusie 'pending_payment'.
    -   Backend zwraca URL do mocka płatności.
    -   Frontend przekierowuje użytkownika do mocka płatności.

-   ID: US-017
-   Tytuł: Obsługa powrotu z mocka płatności
-   Opis: Jako Kupujący, po zakończeniu interakcji z mockiem płatności, chcę zostać przekierowany z powrotem do aplikacji i zobaczyć status mojej transakcji/zamówienia.
-   Kryteria akceptacji:
    -   Mock płatności przekierowuje na callback URL aplikacji ze statusem (success/fail/cancelled) i ID transakcji.
    -   Backend obsługuje callback, weryfikuje transakcję i aktualizuje status zamówienia.
    -   W przypadku sukcesu (`success`):
        -   Status zamówienia zmieniany na 'processing'.
        -   Ilość produktu w ofercie jest zmniejszana.
        -   Licznik zakupów oferty jest zwiększany.
        -   Logowane jest zdarzenie `PAYMENT_SUCCESS`.
        -   Użytkownik widzi potwierdzenie złożenia zamówienia. Koszyk jest czyszczony.
    -   W przypadku porażki (`fail`):
        -   Status zamówienia zmieniany na 'failed'.
        -   Logowane jest zdarzenie `PAYMENT_FAIL`.
        -   Użytkownik widzi informację o nieudanej płatności. Koszyk nie jest czyszczony.
    -   W przypadku anulowania (`cancelled`):
        -   Status zamówienia zmieniany na 'cancelled'.
        -   Logowane jest zdarzenie `ORDER_PLACE_FAIL`.
        -   Użytkownik widzi informację o anulowaniu płatności. Koszyk nie jest czyszczony.

-   ID: US-018
-   Tytuł: Przeglądanie historii zamówień
-   Opis: Jako Kupujący, chcę móc przeglądać historię moich złożonych zamówień wraz z ich statusami, aby śledzić zakupy.
-   Kryteria akceptacji:
    -   Dostępna jest sekcja "Historia Zamówień".
    -   Wyświetlana jest lista zamówień złożonych przez Kupującego.
    -   Lista zawiera kluczowe informacje: ID zamówienia, data, status, łączna kwota.
    -   Możliwość zobaczenia szczegółów zamówienia (lista produktów, adres - jeśli byłby w przyszłości).
    -   Lista jest paginowana.

### 5.5. Funkcje Administracyjne (Admin)
-   ID: US-019
-   Tytuł: Zarządzanie użytkownikami (Blokowanie/Odblokowywanie)
-   Opis: Jako Administrator, chcę móc blokować i odblokowywać konta użytkowników, aby zarządzać dostępem do platformy.
-   Kryteria akceptacji:
    -   W panelu admina dostępna jest lista wszystkich użytkowników (włącznie z innymi administratorami) z ich statusami ('Active'/'Inactive').
    -   Lista jest paginowana.
    -   Przy każdym użytkowniku jest opcja zmiany statusu (przycisk "Blokuj" dla aktywnych, "Odblokuj" dla nieaktywnych).
    -   Zablokowanie użytkownika (zmiana statusu na 'Inactive') uniemożliwia mu zalogowanie się.
    -   Odblokowanie użytkownika (zmiana statusu na 'Active') przywraca mu możliwość logowania.
    -   Jeśli blokowany jest Sprzedający, jego aktywne zamówienia są anulowane, a oferty stają się 'inactive'.
    -   Logowane są zdarzenia `USER_DEACTIVATED` i `USER_ACTIVATED`.

-   ID: US-020
-   Tytuł: Przeglądanie wszystkich ofert
-   Opis: Jako Administrator, chcę móc przeglądać wszystkie oferty w systemie, niezależnie od ich statusu, aby monitorować zawartość platformy.
-   Kryteria akceptacji:
    -   W panelu admina dostępna jest lista wszystkich ofert.
    -   Lista pokazuje oferty we wszystkich statusach ('active', 'inactive', 'sold', 'moderated', 'archived').
    -   Lista zawiera kluczowe informacje: ID, Tytuł, Sprzedający, Status, Cena, Ilość.
    -   Lista jest paginowana.
    -   Możliwość przejścia do widoku szczegółów oferty.

-   ID: US-021
-   Tytuł: Moderacja oferty (Ukrywanie)
-   Opis: Jako Administrator, chcę móc ukryć ofertę (zmienić jej status na 'moderated'), która narusza zasady, aby nie była widoczna dla kupujących.
-   Kryteria akceptacji:
    -   Na liście ofert w panelu admina (lub w szczegółach oferty) jest opcja "Moderuj" dla ofert nie będących już w stanie 'moderated'.
    -   Akcja zmienia status oferty na 'moderated'.
    -   Oferta ze statusem 'moderated' jest niewidoczna dla Kupujących (na listach, w wyszukiwarce, w szczegółach).
    -   Logowane jest zdarzenie `OFFER_MODERATED`.
    -   Opcjonalnie: możliwość cofnięcia moderacji (zmiana statusu z 'moderated' np. na 'inactive').

-   ID: US-022
-   Tytuł: Przeglądanie wszystkich zamówień
-   Opis: Jako Administrator, chcę móc przeglądać wszystkie zamówienia w systemie, aby mieć wgląd w aktywność transakcyjną.
-   Kryteria akceptacji:
    -   W panelu admina dostępna jest lista wszystkich zamówień.
    -   Lista zawiera kluczowe informacje: ID zamówienia, Data, Kupujący, Sprzedający, Status, Kwota.
    -   Lista jest paginowana.
    -   Możliwość wyświetlenia szczegółów zamówienia (lista produktów).
    -   Admin ma tylko uprawnienia do odczytu zamówień (poza potencjalnym anulowaniem).

-   ID: US-023
-   Tytuł: Przeglądanie logów aplikacji
-   Opis: Jako Administrator, chcę móc przeglądać logi systemowe, aby monitorować działanie aplikacji i diagnozować potencjalne problemy.
-   Kryteria akceptacji:
    -   W panelu admina dostępna jest przeglądarka logów.
    -   Logi są wyświetlane w tabeli z kolumnami: Data/godzina, Typ zdarzenia, IP klienta, Komunikat.
    -   Logi są paginowane (100 wpisów na stronę), posortowane malejąco wg daty.
    -   Dostępne są opcje filtrowania logów po zakresie dat, adresie IP i typie zdarzenia.

-   ID: US-027
-   Tytuł: Anulowanie zamówienia przez Administratora
-   Opis: Jako Administrator, chcę móc anulować zamówienie użytkownika, aby zarządzać problematycznymi lub błędnymi transakcjami.
-   Kryteria akceptacji:
    -   W panelu administracyjnym, na liście zamówień lub w widoku szczegółów zamówienia, dostępna jest opcja \\"Anuluj zamówienie\\".
    -   Opcja jest dostępna tylko dla zamówień w statusach umożliwiających anulowanie (np. `pending_payment`, `processing`, `shipped` - do ustalenia wg logiki biznesowej).
    -   Przed anulowaniem wyświetlany jest dialog potwierdzenia.
    -   Po potwierdzeniu, wysyłane jest żądanie `POST /admin/orders/{order_id}/cancel`.
    -   Po pomyślnym anulowaniu, status zamówienia zmienia się na `cancelled`.
    -   Zmiana statusu jest widoczna dla Administratora, Kupującego i Sprzedającego (w odpowiednich widokach).
    -   Logowane jest zdarzenie `ORDER_CANCELLED`. W przypadku błędu logowane jest `ORDER_CANCEL_FAIL`.

-   ID: US-028
-   Tytuł: Przeglądanie szczegółów użytkownika przez Administratora
-   Opis: Jako Administrator, chcę móc zobaczyć szczegółowe informacje o konkretnym użytkowniku, aby uzyskać więcej kontekstu na jego temat.
-   Kryteria akceptacji:
    -   Na liście użytkowników w panelu admina (`/admin`, zakładka Użytkownicy) istnieje możliwość kliknięcia na użytkownika, aby zobaczyć jego szczegóły.
    -   Akcja pobiera dane z endpointu `GET /admin/users/{user_id}`.
    -   Wyświetlany jest dedykowany widok lub modal ze szczegółami: ID, email, rola, status, imię, nazwisko, data utworzenia, data ostatniej modyfikacji.
    -   Hasło ani jego hash nie są wyświetlane.
    -   Logowane jest zdarzenie `ADMIN_GET_USER_DETAILS`.

## 6. Metryki sukcesu

1.  Szybki start:
    -   Cel: Czas od uruchomienia polecenia `docker run` do momentu dostępności interfejsu webowego aplikacji nie przekracza 2 minut.
    -   Miernik: Czas startu mierzony w sekundach.
    -   Cel: Poziom błędów podczas wdrażania (uruchamiania kontenera) jest mniejszy niż 5% w serii 20 kolejnych prób.
    -   Miernik: Procent nieudanych uruchomień kontenera.
2.  Kompletność podstawowych ścieżek:
    -   Cel: Każda z trzech ról (Kupujący, Sprzedający, Admin) może w pełni wykonać co najmniej jedną kluczową transakcję/akcję (np. Kupujący: od znalezienia produktu do złożenia zamówienia; Sprzedający: od stworzenia oferty do zobaczenia jej sprzedaży; Admin: zablokowanie użytkownika i znalezienie logu tej akcji) bez napotykania błędów krytycznych (np. błędy serwera 500, niemożność ukończenia przepływu).
    -   Miernik: Zaliczone/Niezaliczone scenariusze testowe dla kluczowych przepływów per rola.
3.  Stabilność działania:
    -   Cel: Aplikacja nie generuje błędów serwera (HTTP 5xx) ani nie ulega awarii w ramach zdefiniowanego zestawu scenariuszy testowych (minimum 50 testów end-to-end obejmujących główne funkcjonalności).
    -   Miernik: Procent scenariuszy testowych zakończonych bez błędów 5xx lub awarii aplikacji.
