# Projekt easyAI

## Jak przygotowac dzialajace srodowisko (od zera)

### 1) Wymagania

- Python 3.12+
- uv (https://docs.astral.sh/uv/)
- MiKTeX (do budowy PDF)

### 2) Instalacja zaleznosci projektu przez uv

W katalogu projektu uruchom:

```powershell
uv sync
```

To tworzy/uzupelnia lokalne srodowisko `.venv` na podstawie `pyproject.toml` i `uv.lock`.

Opcjonalnie (narzedzia developerskie, np. testy):

```powershell
uv sync --extra dev
```

### 3) Aktywacja srodowiska (opcjonalna)

Nie jest wymagana przy `uv run`, ale moze byc wygodna.

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Git Bash:

```bash
source .venv/Scripts/activate
```

## Uruchamianie

### 1) Eksperymenty

```powershell
uv run python lab_01/nimby_experiments.py
```

Wersja modulowa (podzial na pliki):

```powershell
uv run python lab_01/nimby_experiments_split.py
```

Wyniki trafia do `lab_01/results.json`.

### 2) Wykresy

```powershell
uv run python lab_01/generate_plots.py
```

Wykresy trafia do `lab_01/figures/`.

### 3) PDF raportu

```powershell
powershell -ExecutionPolicy Bypass -File lab_01/build_report.ps1
```

Gotowy plik: `lab_01/report.pdf`.

## Jak aktualizowac zaleznosci i uv.lock

Przy dodaniu nowej biblioteki:

```powershell
uv add NAZWA_PAKIETU
```

Po zmianach recznych w `pyproject.toml` zaktualizuj lock:

```powershell
uv lock
uv sync
```

Dzieki temu instrukcja uruchomienia pozostaje odtwarzalna na nowej maszynie.
