from playwright.sync_api import sync_playwright
import json
import time


# ---------------------------------------------------------
# 1) TOPSELLER SCRAPEN (richtige Spiel-URLs + Limit)
# ---------------------------------------------------------

def scrape_itch_topsellers(limit=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

        print("Lade itch.io Topseller...")
        page.goto("https://itch.io/games/top-sellers", wait_until="domcontentloaded")
        page.wait_for_selector(".game_cell")

        last_count = 0

        # Infinite Scroll
        while True:
            page.mouse.wheel(0, 50000)
            time.sleep(1)

            items = page.query_selector_all(".game_cell")
            if len(items) == last_count:
                break
            last_count = len(items)

            if limit and last_count >= limit:
                break

        if limit:
            items = items[:limit]

        results = []

        for item in items:
            title_el = item.query_selector(".game_title")
            author_el = item.query_selector(".game_author")
            price_el = item.query_selector(".price_value")

            # Spiel-Link (nicht Dev-Profil)
            url_el = item.query_selector("a.title, a.game_link")
            game_url = url_el.get_attribute("href") if url_el else None

            results.append({
                "name": title_el.inner_text().strip() if title_el else None,
                "author": author_el.inner_text().strip() if author_el else None,
                "price": price_el.inner_text().strip() if price_el else "Free",
                "url": game_url
            })

        browser.close()
        return results


# ---------------------------------------------------------
# 2) DETAILSEITE SCRAPEN (HTML, inkl. GENRE)
# ---------------------------------------------------------

def scrape_itch_game_page_html(browser, url):
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    try:
        page.goto(url, timeout=60000, wait_until="networkidle")
    except:
        print("Fehler beim Laden:", url)
        page.close()
        return {
            "tags": [],
            "description": None,
            "platforms": [],
            "release_date": None,
            "genre": None
        }

    page.wait_for_timeout(800)

    # TAGS
    tag_elements = page.query_selector_all(".game_tags .tag, .game_tags_widget .tag")
    tags = [t.inner_text().strip() for t in tag_elements]

    # BESCHREIBUNG
    desc_el = page.query_selector(
        ".formatted_description, .game_description, .user_formatted, .markdown"
    )
    description = desc_el.inner_text().strip() if desc_el else None

    # PLATTFORMEN
    platform_elements = page.query_selector_all(".buy_row .icon")
    platforms = []
    for p in platform_elements:
        title = p.get_attribute("title")
        aria = p.get_attribute("aria-label")
        if title:
            platforms.append(title.lower())
        elif aria:
            platforms.append(aria.lower())

    # RELEASE DATE
    release_el = page.query_selector(
        ".game_info_panel_widget .date, .date_label, .info_row .date"
    )
    release_date = release_el.inner_text().strip() if release_el else None

    # GENRE (richtiger Block!)
    genre = None
    meta_rows = page.query_selector_all(".game_metadata .meta_row")
    for row in meta_rows:
        label = row.query_selector(".meta_label")
        value = row.query_selector(".meta_value")
        if label and value and label.inner_text().strip().lower() == "genre":
            genre = value.inner_text().strip()
            break

    page.close()

    return {
        "tags": tags,
        "description": description,
        "platforms": platforms,
        "release_date": release_date,
        "genre": genre
    }


# ---------------------------------------------------------
# 3) MAIN – ALLES KOMBINIEREN & SPEICHERN
# ---------------------------------------------------------

def run(limit=10):
    print(f"Starte Scrape mit Limit = {limit}")

    # 1. Topseller
    topseller_data = scrape_itch_topsellers(limit=limit)

    with open("itch_topsellers.json", "w", encoding="utf-8") as f:
        json.dump(topseller_data, f, indent=4, ensure_ascii=False)

    print("Itch Topseller gespeichert:", len(topseller_data))

    # 2. Detaildaten (HTML)
    final_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for entry in topseller_data:
            print("Scrape Details:", entry["name"], "->", entry["url"])
            details = scrape_itch_game_page_html(browser, entry["url"])
            combined = {**entry, **details}
            final_data.append(combined)

        browser.close()

    # 3. Finale Datei
    with open("itch_topsellers_full.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print("FERTIG – finale JSON erstellt.")
    print("Einträge:", len(final_data))


if __name__ == "__main__":
    run(limit=5)
