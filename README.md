# ODM

# 🎬 Disney+ OLAP – DuckDB
> Semestrální práce z předmětu **KI/ODM** – Organizace a správa dat  
> Univerzita Jana Evangelisty Purkyně v Ústí nad Labem  
> Autor: Karel Murgač | 2026

---

## 📋 Obsah projektu

Projekt implementuje **Data Warehouse (DWH)** nad datovou sadou Disney+ Shows pomocí **DuckDB**. Zahrnuje ETL pipeline, Star Schema, 7 analytických dotazů s vizualizacemi a statistické metody jako náhradu za data mining.

---

## 🗂️ Struktura repozitáře

```
📦 disney-olap-duckdb
├── 📄 etl_clean.py           # ETL – čištění surových dat (Python/pandas)
├── 📄 disney_dwh.sql         # DuckDB – Star Schema + 7 analytických dotazů
├── 📄 generate_charts.py     # Generování grafů pro dotazy 1–5 (matplotlib)
├── 📄 generate_charts_67.py  # Generování grafů pro dotazy 6–7 (matplotlib)
├── 📄 generate_pdf.py        # Generování seminární práce PDF (reportlab)
├── 📊 charts/
│   ├── dotaz1_hodnoceni_zanr.png
│   ├── dotaz2_pridane_tituly.png
│   ├── dotaz3_zeme.png
│   ├── dotaz4_dekady.png
│   ├── dotaz5_typy.png
│   ├── dotaz6_korelace.png
│   └── dotaz7_zscore.png
├── 📄 ODM26_MurgacKarel.pdf  # Finální seminární práce
└── 📄 README.md
```

> ⚠️ Soubory `disney_clean.csv` a `disney.db` nejsou součástí repozitáře – generují se automaticky (viz níže).

---

## 📦 Dataset

**Disney+ Shows** – 992 titulů (filmy, seriály, epizody) dostupných na platformě Disney+.

- Zdroj: [Kaggle – Disney+ Shows](https://www.kaggle.com/datasets)
- Klíčové atributy: `title`, `type`, `genre`, `country`, `year`, `added_at`, `imdb_rating`, `metascore`, `runtime`, `imdb_votes`

---

## 🏗️ Architektura – Star Schema (Snowflake)

```
                    ┌─────────────┐
                    │  dim_time   │
                    │  time_sk    │
                    │  year       │
                    │  month      │
                    │  quarter    │
                    └──────┬──────┘
                           │
┌─────────────┐    ┌───────┴───────┐    ┌───────────────┐
│  dim_type   │    │  fact_titles  │    │  dim_country  │
│  type_sk    ├────┤  imdb_id      ├────┤  country_sk   │
│  type_name  │    │  type_sk      │    │  country_name │
└─────────────┘    │  time_sk      │    └───────────────┘
                   │  country_sk   │
                   │  imdb_rating  │    ┌───────────────────────┐
                   │  metascore    │    │  bridge_title_genre   │
                   │  runtime_min  ├────┤  imdb_id              │
                   │  imdb_votes   │    │  genre_sk             │
                   └───────────────┘    └───────────┬───────────┘
                                                    │
                                        ┌───────────┴───────────┐
                                        │      dim_genre        │
                                        │      genre_sk         │
                                        │      genre_name       │
                                        └───────────────────────┘
```

---

## 🚀 Jak spustit

### 1. Požadavky

```bash
pip install pandas duckdb matplotlib reportlab
```

Stáhni [DuckDB CLI](https://duckdb.org/docs/installation/) (`duckdb.exe` pro Windows).

### 2. Dataset

Stáhni dataset z Kaggle a ulož jako `disney_plus_shows.csv` do složky projektu.

### 3. ETL – čištění dat

```bash
python etl_clean.py
```
Vytvoří soubor `disney_clean.csv`.

### 4. Vytvoření DWH a spuštění dotazů

```cmd
# CMD (Windows)
duckdb.exe disney.db < disney_dwh.sql

# PowerShell
Get-Content disney_dwh.sql | duckdb.exe disney.db
```
Vytvoří databázi `disney.db` se Star Schema a vypíše výsledky všech 7 dotazů.

### 5. Generování grafů

```bash
python generate_charts.py      # Grafy 1–5
python generate_charts_67.py   # Grafy 6–7
```

### 6. Generování PDF seminární práce

```bash
python generate_pdf.py
```
Vytvoří `ODM26_MurgacKarel.pdf`.

---

## 📊 Analytické dotazy

| # | Dotaz | Metoda |
|---|-------|--------|
| 1 | Průměrné IMDB hodnocení podle žánru (Top 10) | GROUP BY + AVG + JOIN bridge |
| 2 | Tituly přidané na Disney+ podle roku a kvartálu | GROUP BY + dim_time |
| 3 | Top 10 zemí podle počtu titulů a hodnocení | GROUP BY + AVG + dim_country |
| 4 | Průměrné hodnocení podle dekády vzniku | Integer division `// 10` |
| 5 | Srovnání typů obsahu (movie / series / episode) | GROUP BY + dim_type |
| 6 | Korelační analýza mezi metrikami | `CORR()` – Pearsonův koeficient |
| 7 | Z-score analýza – detekce outlierů | Window function `AVG() OVER()` + `STDDEV()` |

---

## 🔍 Statistické metody (náhrada data miningu)

DuckDB nepodporuje nativní data mining. Byly proto přidány 2 dotazy se složitějšími statistickými metodami:

- **Dotaz 6 – Korelační analýza:** Pearsonův koeficient mezi páry metrik (délka, hlasy, metascore vs. IMDB hodnocení). Nejsilnější korelace: Metascore ↔ IMDB (r = 0.72).
- **Dotaz 7 – Z-score / detekce outlierů:** Identifikace statisticky výjimečných titulů pomocí okénkových funkcí. Nejhorší: *Jonas Brothers Concert* (Z = -5.05), nejlepší: *Bluey* (Z = +2.98).

---

## 🛠️ Použité technologie

| Nástroj | Verze | Využití |
|---------|-------|---------|
| [DuckDB](https://duckdb.org/) | 1.x | OLAP databáze, Star Schema, SQL dotazy |
| Python | 3.x | ETL, generování grafů a PDF |
| pandas | latest | Čištění a transformace dat |
| matplotlib | latest | Vizualizace (7 grafů) |
| reportlab | latest | Generování PDF |

---

## 📚 Zdroje

1. DuckDB Documentation – https://duckdb.org/docs/
2. Kaggle – Disney+ Shows Dataset – https://www.kaggle.com/datasets
3. Wikipedia – Data warehouse – https://en.wikipedia.org/wiki/Data_warehouse
4. GoodData – DWH vs. Data Lake comparison – https://www.gooddata.com/blog/data-warehouse-data-lake-and-analytics-lake-a-detailed-comparison/
5. Wikiwand – Comparison of OLAP servers – https://www.wikiwand.com/en/Comparison_of_OLAP_servers
