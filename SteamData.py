from playwright.sync_api import sync_playwright
import json
import time

def scrape_steam_topsellers(limit=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://store.steampowered.com/search/?filter=topsellers")
        page.wait_for_selector(".search_result_row")

        last_count = 0

        while True:
            page.mouse.wheel(0, 50000)
            time.sleep(1)

            items = page.query_selector_all(".search_result_row")
            if len(items) == last_count:
                break
            last_count = len(items)

            if limit and last_count >= limit:
                break

        if limit:
            items = items[:limit]

        results = []

        for item in items:
            title_el = item.query_selector(".title")
            release_el = item.query_selector(".search_released")
            price_el = item.query_selector(".search_price")
            review_el = item.query_selector(".search_reviewscore span")

            results.append({
                "name": title_el.inner_text().strip() if title_el else None,
                "url": item.get_attribute("href"),
                "release": release_el.inner_text().strip() if release_el else None,
                "price": price_el.inner_text().strip() if price_el else None,
                "reviews": review_el.get_attribute("data-tooltip-html") if review_el else None
            })

        browser.close()
        return results


def scrape_steam_shop_page(browser, url):
    page = browser.new_page()

    # Robust laden
    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
    except:
        print("Fehler beim Laden:", url)
        page.close()
        return {
            "genres": [],
            "developer": [],
            "publisher": [],
            "tags": [],
            "features": [],
            "system_requirements": None
        }

    # Age Check umgehen
    if "agecheck" in page.url:
        try:
            page.select_option("#ageYear", "1990")
            page.click("input[type=submit]")
            page.wait_for_timeout(1000)
        except:
            pass

    # DETAILS BLOCK
    details_block = page.query_selector(".details_block")
    genres = []
    developer = []
    publisher = []

    if details_block:
        html = details_block.inner_html()

        def extract(label):
            if f"<b>{label}:</b>" in html:
                part = html.split(f"<b>{label}:</b>")[1].split("<br>")[0]
                return [x.strip() for x in part.split(",")]
            return []

        genres = extract("Genre")
        developer = extract("Entwickler")
        publisher = extract("Publisher")

    # TAGS
    tag_elements = page.query_selector_all(".app_tag")
    tags = [t.inner_text().strip() for t in tag_elements]

    # FEATURES
    feature_elements = page.query_selector_all(".game_area_details_specs a")
    features = [f.inner_text().strip() for f in feature_elements]

    # SYSTEM REQUIREMENTS
    sysreq_el = page.query_selector("#system_requirements")
    sysreq = sysreq_el.inner_text().strip() if sysreq_el else None

    page.close()

    return {
        "genres": genres,
        "developer": developer,
        "publisher": publisher,
        "tags": tags,
        "features": features,
        "system_requirements": sysreq
    }


# -----------------------------
#   HAUPTPROGRAMM
# -----------------------------

# 1. Topseller scrapen
topseller_data = scrape_steam_topsellers()

with open("steam_topsellers.json", "w", encoding="utf-8") as f:
    json.dump(topseller_data, f, indent=4, ensure_ascii=False)

print("Topseller gespeichert:", len(topseller_data))

# 2. Detaildaten scrapen
final_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for entry in topseller_data:
        print("Scrape:", entry["name"])
        details = scrape_steam_shop_page(browser, entry["url"])

        combined = {**entry, **details}
        final_data.append(combined)

    browser.close()

# 3. Finale Datei speichern
with open("steam_topsellers_full.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print("FERTIG – finale JSON erstellt.")
print("Einträge:", len(final_data))
