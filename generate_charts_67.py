import duckdb
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

con = duckdb.connect('disney.db')
OUTPUT = 'charts'

# ── Graf 6: Korelační matice (bar chart korelačních koeficientů) ───────────────
df6 = con.execute("""
    SELECT
        round(corr(runtime_min, imdb_rating), 4) AS korelace_delka_hodnoceni,
        round(corr(imdb_votes,  imdb_rating), 4) AS korelace_hlasy_hodnoceni,
        round(corr(metascore,   imdb_rating), 4) AS korelace_metascore_imdb
    FROM fact_titles
    WHERE runtime_min IS NOT NULL AND imdb_rating IS NOT NULL AND metascore IS NOT NULL
""").df()

labels = ['Délka filmu\nvs. IMDB', 'Počet hlasů\nvs. IMDB', 'Metascore\nvs. IMDB']
values = [df6['korelace_delka_hodnoceni'][0],
          df6['korelace_hlasy_hodnoceni'][0],
          df6['korelace_metascore_imdb'][0]]
colors = ['#1565C0' if v >= 0 else '#E53935' for v in values]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(labels, values, color=colors, width=0.4)
ax.bar_label(bars, fmt='%.4f', padding=3, fontsize=11)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_ylim(-0.1, 1.0)
ax.set_ylabel('Pearsonův korelační koeficient')
ax.set_title('Dotaz 6: Korelační analýza mezi metrikami Disney+ titulů')
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz6_korelace.png', dpi=150)
plt.close()
print('Graf 6 hotov')

# ── Graf 7: Z-score scatter plot ───────────────────────────────────────────────
df7 = con.execute("""
    SELECT
        f.title,
        f.imdb_rating,
        round((f.imdb_rating - avg(f.imdb_rating) OVER ())
              / stddev(f.imdb_rating) OVER (), 2) AS z_score,
        CASE
            WHEN (f.imdb_rating - avg(f.imdb_rating) OVER ())
                 / stddev(f.imdb_rating) OVER () >  2 THEN 'Výjimečně dobré'
            WHEN (f.imdb_rating - avg(f.imdb_rating) OVER ())
                 / stddev(f.imdb_rating) OVER () < -2 THEN 'Výjimečně špatné'
            ELSE 'Běžné'
        END AS kategorie
    FROM fact_titles f
    WHERE f.imdb_rating IS NOT NULL
    ORDER BY z_score
""").df()

color_map = {'Výjimečně dobré': '#2E7D32', 'Běžné': '#90CAF9', 'Výjimečně špatné': '#E53935'}
colors_scatter = df7['kategorie'].map(color_map)

fig, ax = plt.subplots(figsize=(11, 5))
ax.scatter(range(len(df7)), df7['z_score'], c=colors_scatter, s=15, alpha=0.7)
ax.axhline(2,  color='#2E7D32', linestyle='--', linewidth=1, label='Z = +2')
ax.axhline(-2, color='#E53935', linestyle='--', linewidth=1, label='Z = -2')
ax.axhline(0,  color='gray',    linestyle='-',  linewidth=0.5)
ax.set_xlabel('Tituly (seřazeny podle Z-score)')
ax.set_ylabel('Z-score')
ax.set_title('Dotaz 7: Z-score analýza – detekce outlierů v IMDB hodnocení')

# Popisky extrémních titulů
for _, row in df7[df7['kategorie'] != 'Běžné'].iterrows():
    idx = df7.index.get_loc(_)
    short = row['title'][:20] + '…' if len(row['title']) > 20 else row['title']
    ax.annotate(short, (idx, row['z_score']), fontsize=6.5,
                xytext=(5, 3), textcoords='offset points')

patches = [mpatches.Patch(color=c, label=l) for l, c in color_map.items()]
ax.legend(handles=patches + [
    plt.Line2D([0],[0], color='#2E7D32', linestyle='--', label='Z = +2'),
    plt.Line2D([0],[0], color='#E53935', linestyle='--', label='Z = -2'),
], fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUTPUT}/dotaz7_zscore.png', dpi=150)
plt.close()
print('Graf 7 hotov')
