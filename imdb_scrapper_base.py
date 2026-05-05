from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re


def parse_iso_duration(duration_str):
    """
    Convierte duraciones tipo PT2H29M a '2h 29min'
    """
    if not duration_str:
        return None

    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return duration_str

    hours, minutes, seconds = match.groups()
    parts = []

    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}min")
    if seconds and not hours and not minutes:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else duration_str


def extract_movie_data_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1) Intentamos con JSON-LD
    jsonld_scripts = soup.find_all("script", type="application/ld+json")

    for script in jsonld_scripts:
        try:
            if not script.string:
                continue

            data = json.loads(script.string)

            if isinstance(data, dict) and data.get("@type") == "Movie":
                director = None
                director_data = data.get("director")

                if isinstance(director_data, list):
                    director = ", ".join(
                        d.get("name", "") for d in director_data if isinstance(d, dict)
                    )
                elif isinstance(director_data, dict):
                    director = director_data.get("name")

                rating = None
                votes = None
                if isinstance(data.get("aggregateRating"), dict):
                    rating = data["aggregateRating"].get("ratingValue")
                    votes = data["aggregateRating"].get("ratingCount")

                duration = parse_iso_duration(data.get("duration"))

                return {
                    "title": data.get("alternateName") or data.get("name"),
                    "original_title": data.get("name"),
                    "rating": rating,
                    "votes": votes,
                    "synopsis": data.get("description"),
                    "director": director,
                    "duration": duration,
                    "genres": data.get("genre"),
                    "url": data.get("url")
                }

        except Exception:
            continue

    return None


def fetch_imdb_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()
        return html


def get_movie_data_imdb(url):
    html = fetch_imdb_html(url)
    movie = extract_movie_data_from_html(html)
    return movie


if __name__ == "__main__":
    url = "https://www.imdb.com/es-es/title/tt0816692/?ref_=nv_sr_srsg_0_tt_6_nm_2_in_0_q_INTER"
    movie = get_movie_data_imdb(url)
    print(json.dumps(movie, ensure_ascii=False, indent=2))