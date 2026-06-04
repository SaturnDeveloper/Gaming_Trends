import json
import re
from collections import defaultdict, Counter

# HTML entfernen
def strip_html(text):
    return re.sub(r"<.*?>", "", text)

# Alle Genre-Felder, die Steam-Dumps typischerweise enthalten
GENRE_FIELDS = [
    "genres",
    "genre",
    "genre_raw",
]

# Genres pro Spiel extrahieren (einmalig pro Spiel)
def extract_unique_genres(game):
    genres = set()

    for field in GENRE_FIELDS:
        if field not in game:
            continue

        value = game[field]

        # Fall: "Action, Indie"
        if isinstance(value, str):
            parts = [strip_html(v).strip() for v in value.split(",")]
            genres.update(parts)

        # Fall: ["Action", "Indie"]
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, str):
                    genres.add(strip_html(v).strip())
                elif isinstance(v, dict) and "description" in v:
                    genres.add(strip_html(v["description"]).strip())

    # Leere Einträge entfernen
    return {g for g in genres if g}


# Release-Jahr extrahieren
def extract_year(game):
    for key in ["release_date", "release_date_raw", "release", "date", "releaseDate"]:
        if key in game and isinstance(game[key], str):
            match = re.search(r"(19|20)\d{2}", game[key])
            if match:
                return int(match.group())
    return None


# JSON laden
with open("steam_topsellers_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Counter
genre_total = Counter()                 # Spiele pro Genre
genre_by_year = defaultdict(Counter)    # Spiele pro Genre pro Jahr
missing_years = 0

# Hauptschleife
for game in data:
    genres = extract_unique_genres(game)
    year = extract_year(game)

    # Spiele pro Genre (gesamt)
    for g in genres:
        genre_total[g] += 1

    # Spiele pro Genre pro Jahr
    if year:
        for g in genres:
            genre_by_year[year][g] += 1
    else:
        missing_years += 1


# ============================
# AUSGABE
# ============================

print("\n=== Anzahl Spiele pro Genre (GESAMT) ===")
for genre, count in genre_total.most_common():
    print(f"{genre}: {count}")

print("\n=== Anzahl Spiele pro Genre pro Jahr ===")
for year in sorted(genre_by_year):
    print(f"\n--- {year} ---")
    for genre, count in genre_by_year[year].most_common():
        print(f"{genre}: {count}")

print(f"\nSpiele ohne Release-Jahr: {missing_years}")
