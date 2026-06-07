from playwright.sync_api import sync_playwright
import json
import time


# ---------------------------------------------------------
# 1) TOPSELLER SCRAPEN
# ---------------------------------------------------------

def scrape_itch_topsellers(limit=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Lade itch.io Topseller...")
        page.goto("https://itch.io/games/top-sellers")
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
            url_el = item.query_selector("a")

            results.append({
                "name": title_el.inner_text().strip() if title_el else None,
                "author": author_el.inner_text().strip() if author_el else None,
                "price": price_el.inner_text().strip() if price_el else "Free",
                "url": url_el.get_attribute("href") if url_el else None
            })

        browser.close()
        return results


# ---------------------------------------------------------
# 2) DETAILSEITE SCRAPEN
# ---------------------------------------------------------

def scrape_itch_game_page(browser, url):
    page = browser.new_page()

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
    except:
        print("Fehler beim Laden:", url)
        page.close()
        return {
            "tags": [],
            "description": None,
            "platforms": [],
            "release_date": None
        }

    # Tags
    tag_elements = page.query_selector_all(".game_tags a")
    tags = [t.inner_text().strip() for t in tag_elements]

    # Beschreibung
    desc_el = page.query_selector(".formatted_description")
    description = desc_el.inner_text().strip() if desc_el else None

    # Plattformen
    platform_elements = page.query_selector_all(".game_platform")
    platforms = [p.inner_text().strip() for p in platform_elements]

    # Release Date
    release_el = page.query_selector(".game_info_panel_widget .date")
    release_date = release_el.inner_text().strip() if release_el else None

    page.close()

    return {
        "tags": tags,
        "description": description,
        "platforms": platforms,
        "release_date": release_date
    }


# ---------------------------------------------------------
# 3) HAUPTPROGRAMM
# ---------------------------------------------------------

if __name__ == "__main__":

    # 1. Topseller scrapen
    topseller_data = scrape_itch_topsellers()

    with open("itch_topsellers.json", "w", encoding="utf-8") as f:
        json.dump(topseller_data, f, indent=4, ensure_ascii=False)

    print("Itch Topseller gespeichert:", len(topseller_data))

    # 2. Detaildaten scrapen
    final_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for entry in topseller_data:
            print("Scrape:", entry["name"])
            details = scrape_itch_game_page(browser, entry["url"])

            combined = {**entry, **details}
            final_data.append(combined)

        browser.close()

    # 3. Finale Datei speichern
    with open("itch_topsellers_full.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print("FERTIG – finale JSON erstellt.")
    print("Einträge:", len(final_data))
