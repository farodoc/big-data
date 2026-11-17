# Sprawozdanie z projektu Big Data

## Analiza aktywności użytkowników GitHuba na podstawie GitHub Archive

## 1. Cel projektu

Celem projektu jest przygotowanie aplikacji, która pobiera duży zbiór danych,
zapisuje go w lokalnej bazie MongoDB, wykonuje podstawowe czyszczenie,
przeprowadza analizy statystyczne oraz przedstawia wyniki w postaci tabel
i wykresów.

W projekcie analizowana jest aktywność użytkowników GitHuba. Pojedynczy rekord
oznacza zdarzenie wykonane w serwisie, na przykład utworzenie commita,
otwarcie zgłoszenia albo zmianę w repozytorium.

## 2. Źródło danych

Źródłem danych jest **GitHub Archive**:

- strona projektu: https://www.gharchive.org/,
- adres pliku: `https://data.gharchive.org/YYYY-MM-DD-H.json.gz`,
- format: JSON Lines skompresowany gzipem,
- pojedynczy plik: jedna godzina aktywności GitHuba.

GitHub Archive jest publicznym i udokumentowanym źródłem danych. Nie jest to
żadne ze źródeł wykluczonych w wymaganiach projektu.

W analizie wykorzystano pierwsze trzy dni stycznia 2023 roku. Obejmuje to 72 pliki
godzinowe. Po rozpakowaniu dane zajmują około **7,2 GB**, czyli więcej niż
wymagane 5 GB.

Rozmiar pobranych plików można potwierdzić poleceniem:

```powershell
(Get-ChildItem data\raw\*.json.gz | Measure-Object -Property Length -Sum).Sum / 1GB
```

Liczbę plików można potwierdzić poleceniem:

```powershell
(Get-ChildItem data\raw\*.json.gz).Count
```

W raporcie należy wpisać wartości wyświetlone przez te polecenia. Nie należy
wpisywać liczby rekordów przed wykonaniem importu, ponieważ zależy ona od
rzeczywiście pobranych plików.

## 3. Przygotowanie środowiska

Projekt został wykonany w Pythonie. Do przechowywania danych używany jest
MongoDB uruchamiany lokalnie w Dockerze.

Utworzenie środowiska:

```powershell
py -m venv .venv
```

Aktywacja środowiska:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalacja bibliotek:

```powershell
python -m pip install -r requirements.txt
```

Uruchomienie MongoDB:

```powershell
docker compose up -d
```

Sprawdzenie kontenera:

```powershell
docker ps
```

MongoDB jest dostępny pod adresem `mongodb://localhost:27017`. Dane są
zapisywane w bazie `github_archive`, w kolekcji `events`.

## 4. Pobranie danych

Zakres pierwszych trzech dni stycznia można pobrać poleceniem:

```powershell
python -m app download --years 2023 --start-date 2023-01-01 --end-date 2023-01-03 --max-gb 8
```

Parametry oznaczają:

- `--years 2023` - rok danych,
- `--start-date 2023-01-01` - początek zakresu,
- `--end-date 2023-01-03` - koniec zakresu włącznie,
- `--max-gb 8` - maksymalny rozmiar pobierania w przybliżeniu.

Program pobiera pliki godzinowe i pomija pliki, które już istnieją. Dzięki temu
można przerwać pobieranie i uruchomić tę samą komendę ponownie.

## 5. Import danych do MongoDB

Import wykonuje się poleceniem:

```powershell
python -m app import --input-dir data\raw --batch-size 5000
```

Program wykonuje następujące czynności:

1. otwiera każdy plik `.json.gz`,
2. odczytuje dane wiersz po wierszu,
3. sprawdza poprawność JSON,
4. odrzuca rekordy niespełniające warunków jakości,
5. zapisuje poprawne rekordy do MongoDB partiami po 5000 dokumentów,
6. tworzy indeksy dla czasu, typu zdarzenia i repozytorium.

Wymagane pola wejściowe to:

- `type`,
- `created_at`,
- `actor.login`,
- `repo.name`.

Dodatkowo `type` musi kończyć się tekstem `Event`. Z każdego poprawnego
rekordu zapisywane są: `event_id`, `event_type`, `created_at`, `actor_login`,
`repo_name` oraz `public`.

Na końcu importu program wypisuje podsumowanie, na przykład:

```text
Zaimportowano: [liczba], odrzucono: [liczba]
```

W miejsce `[liczba]` należy przepisać wartości z własnego uruchomienia.

## 6. Analizy statystyczne

Analizy uruchamia się poleceniem:

```powershell
python -m app analyze --output-dir output
```

Program wykonuje następujące agregacje MongoDB.

### 6.1. Statystyki opisowe zbioru

Obliczana jest liczba wszystkich zdarzeń, liczba unikalnych autorów oraz liczba
unikalnych repozytoriów. Wynik znajduje się w sekcji
`descriptive_statistics` pliku `output\results.json`.

### 6.2. Najczęstsze typy zdarzeń

Dokumenty są grupowane według pola `event_type`, sortowane malejąco według
liczby wystąpień, a następnie wybieranych jest 15 najczęstszych typów.
Wynik znajduje się w sekcji `most_common_event_types`.

### 6.3. Aktywność według godziny

Z pola `created_at` pobierana jest godzina UTC. Następnie liczona jest liczba
zdarzeń dla każdej godziny od 0 do 23. Wynik znajduje się w sekcji
`events_by_hour_utc`.

### 6.4. Najaktywniejsze repozytoria

Zdarzenia są grupowane według `repo_name`. Program zapisuje 10 repozytoriów
z największą liczbą zdarzeń. Wynik znajduje się w sekcji
`most_active_repositories`.

## 7. Wizualizacja wyników

Wizualizacje powstają razem z analizami po uruchomieniu:

```powershell
python -m app analyze --output-dir output
```

Program tworzy:

- `output\figures\event_types.png` - wykres 15 najczęstszych typów zdarzeń,
- `output\figures\events_by_hour.png` - wykres aktywności w kolejnych godzinach,
- `output\figures\most_active_repositories.png` - wykres 10 najaktywniejszych repozytoriów.

Statystyki zbioru, czyli liczba zdarzeń, autorów i repozytoriów, są dodatkowo
zapisane w czytelnej postaci w pliku:

```text
output\summary.txt
```

Wykresy można otworzyć bezpośrednio z Eksploratora plików. Są czytelniejszym
uzupełnieniem tabel zapisanych w `output\results.json`.

## 8. Wyniki i interpretacja

1. Najczęściej występującym typem zdarzenia jest `PushEvent`.
2. Największa aktywność występuje o godzinie `12` UTC, a najmniejsza
   o godzinie `2` UTC.
3. Najaktywniejszym repozytorium jest `Lombiq/Orchard`, z liczbą
   `94666` zdarzeń.

## 9. Spełnienie wymagań na ocenę 3,0

| Wymaganie | Sposób realizacji | Komenda |
|---|---|---|
| Udokumentowane źródło danych | GitHub Archive, opis formatu i adres plików w rozdziale 2 | `python -m app download ...` |
| Import do lokalnego MongoDB | MongoDB uruchamiany przez Docker Compose | `docker compose up -d` |
| Sprawdzanie i czyszczenie danych | Walidacja JSON, typu zdarzenia, czasu, autora i repozytorium | `python -m app import ...` |
| Co najmniej trzy analizy statystyczne | Statystyki zbioru, typy zdarzeń, godziny aktywności i repozytoria | `python -m app analyze ...` |
| Wizualizacja lub czytelne zestawienia | Trzy wykresy PNG i plik `results.json` | `python -m app analyze ...` |
| Kod, dane/instrukcja i sprawozdanie | Kod w `app`, instrukcja w `README.md`, sprawozdanie w tym pliku | Wszystkie powyższe |
