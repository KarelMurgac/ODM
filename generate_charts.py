import duckdb
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
OUTPUT = 'charts'
os.makedirs(OUTPUT, exist_ok=True)

con = duckdb.connect('disney.db')

# ── Graf 1: Průměrné IMDB hodnocení podle žánru (top 10) ──────────────────────
df1 = con.execute("""
    SELECT dg.genre_name, round(avg(f.imdb_rating),2) AS avg_rating, count(*) AS pocet
    FROM fact_titles f
    JOIN bridge_title_genre btg ON btg.imdb_id = f.imdb_id
    JOIN dim_genre dg ON dg.genre_sk = btg.genre_sk
    WHERE f.imdb_rating IS NOT NULL
    GROUP BY dg.genre_name
    ORDER BY avg_rating DESC LIMIT 10
""").df()

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(df1['genre_name'][::-1], df1['avg_rating'][::-1], color='#1565C0')
ax.bar_label(bars, fmt='%.2f', padding=3)
ax.set_xlabel('Průměrné IMDB hodnocení')
ax.set_title('Dotaz 1: Průměrné IMDB hodnocení podle žánru (Top 10)')
ax.set_xlim(0, 9.5)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz1_hodnoceni_zanr.png', dpi=150)
plt.close()
print('Graf 1 hotov')

# ── Graf 2: Počet přidaných titulů podle roku a kvartálu ──────────────────────
df2 = con.execute("""
    SELECT tim.year, tim.quarter, count(*) AS pocet, dt.type_name
    FROM fact_titles f
    JOIN dim_time tim ON tim.time_sk = f.time_sk
    JOIN dim_type dt ON dt.type_sk = f.type_sk
    GROUP BY tim.year, tim.quarter, dt.type_name
    ORDER BY tim.year, tim.quarter
""").df()

df2['period'] = df2['year'].astype(str) + ' Q' + df2['quarter'].astype(str)
pivot = df2.pivot_table(index='period', columns='type_name', values='pocet', fill_value=0)

fig, ax = plt.subplots(figsize=(10, 5))
pivot.plot(kind='bar', ax=ax, color=['#1565C0', '#F57F17', '#2E7D32'])
ax.set_xlabel('Období')
ax.set_ylabel('Počet titulů')
ax.set_title('Dotaz 2: Tituly přidané na Disney+ podle roku a kvartálu')
ax.legend(title='Typ')
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz2_pridane_tituly.png', dpi=150)
plt.close()
print('Graf 2 hotov')

# ── Graf 3: Top 10 zemí podle počtu titulů ────────────────────────────────────
df3 = con.execute("""
    SELECT dc.country_name, count(*) AS pocet, round(avg(f.imdb_rating),2) AS avg_rating
    FROM fact_titles f
    JOIN dim_country dc ON dc.country_sk = f.country_sk
    WHERE f.imdb_rating IS NOT NULL
    GROUP BY dc.country_name
    ORDER BY pocet DESC LIMIT 10
""").df()

fig, ax1 = plt.subplots(figsize=(10, 5))
colors = ['#1565C0' if i == 0 else '#90CAF9' for i in range(len(df3))]
bars = ax1.bar(df3['country_name'], df3['pocet'], color=colors)
ax1.set_ylabel('Počet titulů', color='#1565C0')
ax1.set_xlabel('Země')
ax1.set_title('Dotaz 3: Top 10 zemí podle počtu titulů a průměrného hodnocení')

ax2 = ax1.twinx()
ax2.plot(df3['country_name'], df3['avg_rating'], color='#E53935', marker='o', linewidth=2, label='Avg IMDB')
ax2.set_ylabel('Průměrné IMDB hodnocení', color='#E53935')
ax2.set_ylim(0, 10)
ax2.legend(loc='upper right')
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz3_zeme.png', dpi=150)
plt.close()
print('Graf 3 hotov')

# ── Graf 4: Průměrné hodnocení podle dekády (po 10 letech) ────────────────────
df4 = con.execute("""
    SELECT (release_year // 10 * 10)::INT AS dekada,
           count(*) AS pocet,
           round(avg(imdb_rating),2) AS avg_imdb,
           round(avg(metascore),1) AS avg_metascore
    FROM fact_titles
    WHERE release_year IS NOT NULL AND imdb_rating IS NOT NULL
      AND release_year >= 1940
    GROUP BY dekada ORDER BY dekada
""").df()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df4['dekada'], df4['avg_imdb'], marker='o', color='#1565C0', label='IMDB rating', linewidth=2)
ax2 = ax.twinx()
ax2.bar(df4['dekada'], df4['pocet'], alpha=0.3, color='#90CAF9', width=7, label='Počet titulů')
ax.set_xlabel('Dekáda')
ax.set_ylabel('Průměrné IMDB hodnocení', color='#1565C0')
ax2.set_ylabel('Počet titulů', color='#90CAF9')
ax.set_title('Dotaz 4: Průměrné IMDB hodnocení podle dekády vzniku')
ax.set_ylim(5, 8.5)
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz4_dekady.png', dpi=150)
plt.close()
print('Graf 4 hotov')

# ── Graf 5: Srovnání typů obsahu ──────────────────────────────────────────────
df5 = con.execute("""
    SELECT dt.type_name, count(*) AS pocet,
           round(avg(f.runtime_min),0) AS avg_runtime,
           round(avg(f.imdb_rating),2) AS avg_rating
    FROM fact_titles f
    JOIN dim_type dt ON dt.type_sk = f.type_sk
    GROUP BY dt.type_name
""").df()

fig, axes = plt.subplots(1, 3, figsize=(12, 5))
colors = ['#1565C0', '#F57F17', '#2E7D32']

axes[0].bar(df5['type_name'], df5['pocet'], color=colors)
axes[0].set_title('Počet titulů')
axes[0].set_ylabel('Počet')
for bar, v in zip(axes[0].patches, df5['pocet']):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, str(int(v)), ha='center')

axes[1].bar(df5['type_name'], df5['avg_rating'], color=colors)
axes[1].set_title('Průměrné IMDB hodnocení')
axes[1].set_ylim(0, 8)
for bar, v in zip(axes[1].patches, df5['avg_rating']):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, str(v), ha='center')

axes[2].bar(df5['type_name'], df5['avg_runtime'], color=colors)
axes[2].set_title('Průměrná délka (min)')
for bar, v in zip(axes[2].patches, df5['avg_runtime']):
    axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(int(v)), ha='center')

fig.suptitle('Dotaz 5: Srovnání typů obsahu (movie / series / episode)', fontsize=13)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz5_typy.png', dpi=150)
plt.close()
print('Graf 5 hotov')

print('\nVšechny grafy uloženy do:', OUTPUT)
