import json
import re
from collections import defaultdict, Counter
import os

def strip_html(text):
    return re.sub(r"<.*?>", "", text)

GENRE_FIELDS = ["genres", "genre", "genre_raw"]

def extract_unique_genres(game):
    genres = set()
    for field in GENRE_FIELDS:
        if field not in game:
            continue
        value = game[field]
        if isinstance(value, str):
            parts = [strip_html(v).strip() for v in value.split(",")]
            genres.update(parts)
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, str):
                    genres.add(strip_html(v).strip())
                elif isinstance(v, dict) and "description" in v:
                    genres.add(strip_html(v["description"]).strip())
    return {g for g in genres if g}

def extract_year(game):
    for key in ["release_date", "release_date_raw", "release", "date", "releaseDate"]:
        if key in game and isinstance(game[key], str):
            match = re.search(r"(19|20)\d{2}", game[key])
            if match:
                return int(match.group())
    return None

def extract_review_percent(game):
    if "reviews" not in game or not isinstance(game["reviews"], str):
        return None
    match = re.search(r"(\d+)%", game["reviews"])
    return int(match.group(1)) if match else None

def extract_review_count(game):
    if "reviews" not in game or not isinstance(game["reviews"], str):
        return None
    match = re.search(r"([\d,\.]+) user reviews", game["reviews"])
    if match:
        return int(match.group(1).replace(",", "").replace(".", ""))
    return None


# JSON laden
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "steam_topsellers_full.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)


genre_total = Counter()
genre_by_year = defaultdict(Counter)
review_percent_by_year = defaultdict(list)
review_count_by_year = defaultdict(list)
genre_count_per_year = defaultdict(list)
tag_counter = Counter()
missing_years = 0

# NEW: Cooccurrence
tag_cooccurrence = Counter()
genre_cooccurrence = Counter()

for game in data:
    genres = extract_unique_genres(game)
    year = extract_year(game)
    review_percent = extract_review_percent(game)
    review_count = extract_review_count(game)

    # Tags
    if "tags" in game and isinstance(game["tags"], list):
        tag_list = [t for t in game["tags"] if isinstance(t, str)]
        for t in tag_list:
            tag_counter[t] += 1

        # Tag-Cooccurrence
        for i in range(len(tag_list)):
            for j in range(i + 1, len(tag_list)):
                a, b = sorted([tag_list[i], tag_list[j]])
                tag_cooccurrence[(a, b)] += 1

    # Genre total
    for g in genres:
        genre_total[g] += 1

    # Genre-Cooccurrence
    genre_list = list(genres)
    for i in range(len(genre_list)):
        for j in range(i + 1, len(genre_list)):
            a, b = sorted([genre_list[i], genre_list[j]])
            genre_cooccurrence[(a, b)] += 1

    # Genre per year
    if year:
        for g in genres:
            genre_by_year[year][g] += 1
        genre_count_per_year[year].append(len(genres))
    else:
        missing_years += 1

    # Review trends
    if year and review_percent:
        review_percent_by_year[year].append(review_percent)
    if year and review_count:
        review_count_by_year[year].append(review_count)


# GRAPH STRUCTURES
tag_nodes = [{"id": tag, "value": count} for tag, count in tag_counter.items()]
tag_links = [
    {"source": a, "target": b, "value": count}
    for (a, b), count in tag_cooccurrence.items()
]

genre_nodes = [{"id": genre, "value": count} for genre, count in genre_total.items()]
genre_links = [
    {"source": a, "target": b, "value": count}
    for (a, b), count in genre_cooccurrence.items()
]


# JSON-Struktur vorbereiten
output = {
    "genre_total": dict(genre_total),
    "genre_by_year": {year: dict(cnt) for year, cnt in genre_by_year.items()},
    "review_percent_by_year": {
        year: sum(vals) / len(vals) for year, vals in review_percent_by_year.items()
    },
    "review_count_by_year": {
        year: sum(vals) / len(vals) for year, vals in review_count_by_year.items()
    },
    "top_tags": dict(tag_counter.most_common(50)),
    "avg_genres_per_year": {
        year: sum(vals) / len(vals) for year, vals in genre_count_per_year.items()
    },
    "missing_years": missing_years,

    # NEW: Graphs
    "tag_graph": {
        "nodes": tag_nodes,
        "links": tag_links
    },
    "genre_graph": {
        "nodes": genre_nodes,
        "links": genre_links
    }
}

# JSON speichern
with open("steam_trends.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print("steam_trends.json wurde erzeugt.")
