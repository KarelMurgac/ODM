import pandas as pd
import re

df = pd.read_csv('disney_plus_shows.csv')

# runtime: "97 min" -> 97 (int)
df['runtime_min'] = df['runtime'].str.extract(r'(\d+)').astype(float)

# added_at: "November 12, 2019" -> date
df['added_at'] = pd.to_datetime(df['added_at'], format='%B %d, %Y', errors='coerce')

# released_at: "31 Mar 1999" -> date
df['released_at'] = pd.to_datetime(df['released_at'], format='%d %b %Y', errors='coerce')

# year: "2018–" -> 2018 (vezme první 4 číslice)
df['year_start'] = df['year'].str.extract(r'(\d{4})').astype(float)

# imdb_votes: "283,945" -> 283945
df['imdb_votes_int'] = df['imdb_votes'].str.replace(',', '', regex=False).astype(float)

# Vyber a přejmenuj sloupce
clean = df[[
    'imdb_id', 'title', 'type', 'rated', 'year_start',
    'released_at', 'added_at', 'runtime_min',
    'genre', 'director', 'language', 'country',
    'metascore', 'imdb_rating', 'imdb_votes_int', 'awards'
]].copy()

clean.rename(columns={'year_start': 'year', 'imdb_votes_int': 'imdb_votes'}, inplace=True)

clean.to_csv('disney_clean.csv', index=False)
print(f"Uloženo: {len(clean)} řádků, {len(clean.columns)} sloupců")
print(clean.dtypes)
print(clean.head(3).to_string())
