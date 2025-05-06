# Aplikacja - Steambay (MVP)

## Główny problem
Rekruterzy i zespoły techniczne potrzebują prostego, szybko wdrażalnego środowiska symulującego aplikację e-commerce, w której kandydaci na pentesterów mogą ćwiczyć podstawowe scenariusze ataku. Obecnie przygotowanie takiego środowiska wymaga czasochłonnej konfiguracji wielu usług i manualnego wprowadzania danych, co opóźnia proces rekrutacji i podnosi koszty przygotowania.

## Najmniejszy zestaw funkcjonalności
- **Role i konta użytkowników**  
  - Kupujący: rejestracja, logowanie, przeglądanie i wyszukiwanie ofert, dodawanie do koszyka, składanie zamówienia.  
  - Sprzedający: rejestracja, logowanie, tworzenie/editowanie/usuwanie własnych ofert produktowych, przeglądanie statusu zamówień.  
  - Administrator: zarządzanie użytkownikami (blokowanie/odblokowywanie kont), przeglądanie wszystkich ofert i zamówień, prosta inspekcja logów aplikacji.  
- **Podstawowe ścieżki e-commerce**  
  - CRUD ofert: tytuł, opis, cena, zdjęcie (upload pliku).  
  - Koszyk i “checkout”: podsumowanie zamówienia, fikcyjne potwierdzenie zakupu (bez realnych płatności).  
  - Historia zamówień: dla kupujących i sprzedających.  
- **Panel administracyjny**  
  - Lista i szczegóły użytkowników, ofert, zamówień.  
  - Ręczne tworzenie/usuwanie kont testowych.  
- **Jednokontenerowy deploy**  
  - Aplikacja, baza danych (np. SQLite lub lekki silnik SQL) i panel admina w jednym obrazie Docker.  
  - Skrypt startowy inicjalizujący bazę i domyślne konta (admin, seller1, buyer1).  

## Co NIE wchodzi w zakres MVP
- Integracja z systemami płatności (Stripe, PayPal itp.).  
- Rozbudowane wyszukiwanie (filtrowanie po kategoriach, sortowanie zaawansowane).  
- System ocen i recenzji produktów ani wewnętrzny chat między kupującym a sprzedającym.  
- Obsługa wielu walut, podatków czy prowizji.  
- Aplikacje mobilne – tylko interfejs webowy.  
- Wiele instancji multitenant – jedna wspólna baza i kontener.  
- Automatyczne wdrożenia CI/CD ani integracja z zewnętrznymi ATS.  
- Mechanizmy zaawansowanej analizy czy raportowania (dashboardy BI, eksport do PDF/CSV).  

## Kryteria sukcesu
1. **Szybki start**  
   - Czas uruchomienia kontenera i dostępności aplikacji ≤ 2 min.  
   - Poziom błędów deployu < 5 % w 20 kolejnych próbach.  
2. **Kompletność podstawowych ścieżek**  
   - Każda z trzech ról może w pełni wykonać przynajmniej jedną transakcję (np. kupujący zakup, sprzedający sprzedaż, admin zarządzanie) bez błędów krytycznych.  
3. **Stabilność działania**  
   - Aplikacja nie powinna generować błędów 500 ani awarii w 95 % scenariuszy testowych (min. 50 testów end-to-end).  
4. **Użyteczność dla rekrutacji**  
   - Rekruterzy/zespoły techniczne potrafią samodzielnie spróbować wszystkich podstawowych funkcji w ≤ 5 min od startu środowiska.  
   - Ankieta wśród pierwszych 10 rekruterów ocenia aplikację na min. 4/5 pod względem „łatwości użycia” i „kompletności funkcji MVP”.  
