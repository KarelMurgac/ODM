-- ============================================================
-- Disney+ DWH v DuckDB
-- Star Schema: 4 dimenze + 1 tabulka faktů + bridge tabulka
-- ============================================================

-- Načti vyčištěná data do staging tabulky
CREATE OR REPLACE TABLE staging AS
SELECT * FROM read_csv_auto('disney_clean.csv', timestampformat='%Y-%m-%d');

-- ============================================================
-- DIMENZE
-- ============================================================

-- dim_type: typ obsahu (movie / series / episode)
CREATE OR REPLACE TABLE dim_type AS
SELECT
    row_number() OVER () AS type_sk,
    type AS type_name
FROM (SELECT DISTINCT type FROM staging WHERE type IS NOT NULL);

-- dim_time: časová dimenze podle added_at
CREATE OR REPLACE TABLE dim_time AS
SELECT
    row_number() OVER () AS time_sk,
    added_date,
    year(added_date)    AS year,
    month(added_date)   AS month,
    day(added_date)     AS day,
    quarter(added_date) AS quarter,
    monthname(added_date) AS month_name
FROM (SELECT DISTINCT CAST(added_at AS DATE) AS added_date FROM staging WHERE added_at IS NOT NULL);

-- dim_country: primární země (první v seznamu)
CREATE OR REPLACE TABLE dim_country AS
SELECT
    row_number() OVER () AS country_sk,
    country_name
FROM (
    SELECT DISTINCT trim(split_part(country, ',', 1)) AS country_name
    FROM staging
    WHERE country IS NOT NULL
);

-- dim_genre: normalizované žánry (každý žánr jako samostatný řádek)
CREATE OR REPLACE TABLE dim_genre AS
SELECT
    row_number() OVER () AS genre_sk,
    genre_name
FROM (
    SELECT DISTINCT trim(g) AS genre_name
    FROM staging, unnest(string_split(genre, ',')) AS t(g)
    WHERE genre IS NOT NULL
);

-- bridge: titul <-> žánr (many-to-many)
CREATE OR REPLACE TABLE bridge_title_genre AS
SELECT
    s.imdb_id,
    dg.genre_sk
FROM staging s,
     unnest(string_split(s.genre, ',')) AS t(g)
JOIN dim_genre dg ON dg.genre_name = trim(g)
WHERE s.genre IS NOT NULL;

-- ============================================================
-- TABULKA FAKTŮ
-- ============================================================
CREATE OR REPLACE TABLE fact_titles AS
SELECT
    s.imdb_id,
    s.title,
    dt.type_sk,
    tim.time_sk,
    dc.country_sk,
    s.year                              AS release_year,
    s.runtime_min,
    s.imdb_rating,
    s.metascore,
    s.imdb_votes,
    s.rated
FROM staging s
LEFT JOIN dim_type dt       ON dt.type_name  = s.type
LEFT JOIN dim_time tim      ON tim.added_date = CAST(s.added_at AS DATE)
LEFT JOIN dim_country dc    ON dc.country_name = trim(split_part(s.country, ',', 1));

-- ============================================================
-- DOTAZY (řezy nad datovou strukturou)
-- ============================================================

-- DOTAZ 1: Průměrné IMDB hodnocení podle žánru (top 10)
SELECT 'DOTAZ 1: Průměrné IMDB hodnocení podle žánru (top 10)' AS popis;
SELECT
    dg.genre_name,
    round(avg(f.imdb_rating), 2) AS avg_rating,
    count(*)                     AS pocet_titulov
FROM fact_titles f
JOIN bridge_title_genre btg ON btg.imdb_id = f.imdb_id
JOIN dim_genre dg           ON dg.genre_sk  = btg.genre_sk
WHERE f.imdb_rating IS NOT NULL
GROUP BY dg.genre_name
ORDER BY avg_rating DESC
LIMIT 10;

-- DOTAZ 2: Počet přidaných titulů na Disney+ podle roku a kvartálu
SELECT 'DOTAZ 2: Tituly přidané na Disney+ podle roku a kvartálu' AS popis;
SELECT
    tim.year,
    tim.quarter,
    count(*)  AS pocet_pridanych,
    dt.type_name
FROM fact_titles f
JOIN dim_time tim  ON tim.time_sk  = f.time_sk
JOIN dim_type dt   ON dt.type_sk   = f.type_sk
GROUP BY tim.year, tim.quarter, dt.type_name
ORDER BY tim.year, tim.quarter;

-- DOTAZ 3: Top 10 zemí podle počtu titulů a průměrného hodnocení
SELECT 'DOTAZ 3: Top 10 zemí podle počtu titulů' AS popis;
SELECT
    dc.country_name,
    count(*)                     AS pocet_titulov,
    round(avg(f.imdb_rating), 2) AS avg_rating,
    round(avg(f.runtime_min), 0) AS avg_runtime_min
FROM fact_titles f
JOIN dim_country dc ON dc.country_sk = f.country_sk
WHERE f.imdb_rating IS NOT NULL
GROUP BY dc.country_name
ORDER BY pocet_titulov DESC
LIMIT 10;

-- DOTAZ 4: Trendy průměrného hodnocení filmů v čase (podle dekády)
SELECT 'DOTAZ 4: Průměrné hodnocení podle dekády vzniku' AS popis;
SELECT
    (release_year // 10 * 10)::INT AS dekada,
    count(*)                        AS pocet,
    round(avg(imdb_rating), 2)      AS avg_imdb,
    round(avg(metascore), 1)        AS avg_metascore
FROM fact_titles
WHERE release_year IS NOT NULL AND imdb_rating IS NOT NULL
GROUP BY dekada
ORDER BY dekada;

-- DOTAZ 5: Srovnání movies vs series – délka, hodnocení, hlasy
SELECT 'DOTAZ 5: Srovnání typů obsahu' AS popis;
SELECT
    dt.type_name,
    count(*)                       AS pocet,
    round(avg(f.runtime_min), 0)   AS avg_runtime_min,
    round(avg(f.imdb_rating), 2)   AS avg_rating,
    round(avg(f.imdb_votes), 0)    AS avg_hlasy,
    round(avg(f.metascore), 1)     AS avg_metascore
FROM fact_titles f
JOIN dim_type dt ON dt.type_sk = f.type_sk
GROUP BY dt.type_name;

-- ============================================================
-- DATA MINING: Klasifikace hodnocení (bucketing)
-- ============================================================
SELECT 'DATA MINING: Klasifikace titulů podle hodnocení' AS popis;
SELECT
    CASE
        WHEN imdb_rating >= 8.0 THEN 'Výborné (8+)'
        WHEN imdb_rating >= 6.5 THEN 'Dobré (6.5–8)'
        WHEN imdb_rating >= 5.0 THEN 'Průměrné (5–6.5)'
        ELSE 'Podprůměrné (<5)'
    END AS kategorie_hodnoceni,
    dt.type_name,
    count(*) AS pocet,
    round(avg(imdb_votes), 0) AS avg_hlasy
FROM fact_titles f
JOIN dim_type dt ON dt.type_sk = f.type_sk
WHERE imdb_rating IS NOT NULL
GROUP BY kategorie_hodnoceni, dt.type_name
ORDER BY kategorie_hodnoceni, dt.type_name;

-- ============================================================
-- DOTAZ 6: Korelační analýza mezi metrikami
-- (složitější statistická metoda místo data miningu)
-- ============================================================
SELECT 'DOTAZ 6: Korelační analýza mezi metrikami' AS popis;
SELECT
    round(corr(runtime_min, imdb_rating), 4)  AS korelace_delka_hodnoceni,
    round(corr(imdb_votes,  imdb_rating), 4)  AS korelace_hlasy_hodnoceni,
    round(corr(metascore,   imdb_rating), 4)  AS korelace_metascore_imdb,
    count(*) AS pocet_zaznamu
FROM fact_titles
WHERE runtime_min IS NOT NULL
  AND imdb_rating IS NOT NULL
  AND metascore   IS NOT NULL;

-- ============================================================
-- DOTAZ 7: Z-score analýza – detekce outlierů v hodnocení
-- (identifikace statisticky výjimečných titulů)
-- ============================================================
SELECT 'DOTAZ 7: Z-score analýza – outlieři v IMDB hodnocení' AS popis;
SELECT
    f.title,
    dt.type_name,
    f.imdb_rating,
    round((f.imdb_rating - avg(f.imdb_rating) OVER ()) 
          / stddev(f.imdb_rating) OVER (), 2)          AS z_score,
    CASE
        WHEN (f.imdb_rating - avg(f.imdb_rating) OVER ())
             / stddev(f.imdb_rating) OVER () >  2 THEN 'Výjimečně dobré'
        WHEN (f.imdb_rating - avg(f.imdb_rating) OVER ())
             / stddev(f.imdb_rating) OVER () < -2 THEN 'Výjimečně špatné'
        ELSE 'Běžné'
    END AS kategorie
FROM fact_titles f
JOIN dim_type dt ON dt.type_sk = f.type_sk
WHERE f.imdb_rating IS NOT NULL
ORDER BY abs((f.imdb_rating - avg(f.imdb_rating) OVER ())
             / stddev(f.imdb_rating) OVER ()) DESC
LIMIT 15;
