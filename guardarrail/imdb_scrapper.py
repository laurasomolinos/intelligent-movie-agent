from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import re
import argparse
import sys


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
    """
    Extrae los datos de la película desde el bloque JSON-LD del HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
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


def find_imdb_movie_url(page, title, year=None):
    """
    Busca una película por título en IMDb y devuelve la URL del primer resultado razonable.
    """
    search_url = f"https://www.imdb.com/find/?q={title.replace(' ', '+')}&s=tt&ttype=ft"
    page.goto(search_url, wait_until="domcontentloaded")

    try:
        page.wait_for_selector('a[href*="/title/tt"]', timeout=8000)
    except:
        # si no aparecen, guardamos html para depurar
        html = page.content()
        with open("debug_search.html", "w", encoding="utf-8") as f:
            f.write(html)
        return None

    # Intentamos resultados modernos
    candidate_links = page.locator('a[href*="/title/tt"]')
    count = candidate_links.count()

    if count == 0:
        return None

    matches = []

    for i in range(min(count, 10)):  # revisamos solo los primeros
        try:
            link = candidate_links.nth(i)
            href = link.get_attribute("href")
            text = link.inner_text().strip()

            if not href or "/title/tt" not in href:
                continue

            # Normalizamos a URL absoluta
            if href.startswith("/"):
                href = "https://www.imdb.com" + href.split("?")[0]
            else:
                href = href.split("?")[0]

            matches.append({
                "text": text,
                "href": href
            })
        except Exception:
            continue

    if not matches:
        return None

    # Si el usuario dio año, intentamos encontrar una coincidencia mejor
    if year:
        for m in matches:
            if year in m["text"]:
                return m["href"]

    # Si no, cogemos el primer resultado
    return matches[0]["href"]


def fetch_imdb_html_from_title(title, year=None, headless=True):
    """
    Busca la película por título, entra en su página y devuelve el HTML renderizado.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        context = browser.new_context(
            locale="es-ES",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768}
        )

        page = context.new_page()

        movie_url = find_imdb_movie_url(page, title, year)

        if not movie_url:
            context.close()
            browser.close()
            raise ValueError(f"No se encontró una película para: {title}")

        page.goto(movie_url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector('script[type="application/ld+json"]', timeout=8000)
        except:
            pass

        html = page.content()
        context.close()
        browser.close()

        return html, movie_url


def get_movie_data_imdb(title, headless=True):
    """
    Busca una película por título y devuelve sus datos.
    """
    html, found_url = fetch_imdb_html_from_title(title, headless=headless)
    movie = extract_movie_data_from_html(html)

    if movie is None:
        raise ValueError("No se pudieron extraer los datos de la película.")

    # por si el JSON-LD no trajera la misma url exacta
    if not movie.get("url"):
        movie["url"] = found_url

    return movie


def main():
    parser = argparse.ArgumentParser(
        description="Consulta información de una película en IMDb."
    )
    parser.add_argument(
        "title",
        type=str,
        help="Título de la película a buscar"
    )
    parser.add_argument(
        "--field",
        type=str,
        choices=["title", "original_title", "rating", "votes", "synopsis", "director", "duration", "genres", "url"],
        default=None,
        help="Si se indica, devuelve solo ese campo"
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Muestra el navegador durante la ejecución"
    )

    args = parser.parse_args()

    try:
        movie = get_movie_data_imdb(
            title=args.title,
            headless=not args.show_browser
        )

        if args.field:
            value = movie.get(args.field)
            if isinstance(value, (list, dict)):
                print(json.dumps(value, ensure_ascii=False, indent=2))
            else:
                print(value)
        else:
            print(json.dumps(movie, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()