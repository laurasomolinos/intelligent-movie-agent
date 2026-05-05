import requests
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
import logging

logging.basicConfig(level=logging.INFO)

# ── Configuración ─────────────────────────────────────────────────────────────

API_BASE_URL = "https://resigned-certify-shakiness.ngrok-free.dev"
TELEGRAM_TOKEN = "8702045865:AAH3RCl2TKHOHjuGC4A_djIc2PKiVGrwLqc"
TELEGRAM_CHAT_ID = "8679957224"  # ← pon aquí el número que te dio @userinfobot

PERFIL_USUARIO = {
    "nota_minima_general": 6.0,
    "generos": {
        "Ciencia ficción": 6.0,
        "Terror": 7.0,
        "Comedia": 5.0,
        "Drama": 6.5,
        "Acción": 6.0,
        "Animación": 5.0,
    },
    "directores_favoritos": [
        "Christopher Nolan",
        "Denis Villeneuve",
    ]
}

# ── Scrapper de ecartelera.com ────────────────────────────────────────────────

def obtener_cartelera_madrid():
    """Obtiene las películas en cartelera en Madrid desde ecartelera.com"""
    url = "https://www.ecartelera.com/cines/0,30,1.html"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error obteniendo cartelera: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    peliculas = []
    vistas = set()  # para no repetir películas

    todos_enlaces = soup.find_all('a', href=True)

    for a in todos_enlaces:
        href = a.get('href', '')
        texto = a.get_text(strip=True)

        # Solo enlaces a páginas de películas, no a cartelera ni videos
        if (
            '/peliculas/' in href
            and '/cartelera/' not in href
            and '/videos/' not in href
            and texto
            and texto not in ['Películas', 'Ver tráiler']
            and href not in vistas
        ):
            vistas.add(href)
            enlace_cartelera = href.replace('/peliculas/', '/peliculas/').rstrip('/') + '/cartelera/'
            peliculas.append({
                "titulo": texto,
                "enlace_ecartelera": href,
                "enlace_cartelera": enlace_cartelera
            })

    logging.info(f"Películas encontradas en cartelera: {len(peliculas)}")
    return peliculas


# ── Llamada a la API de IMDb ──────────────────────────────────────────────────

def obtener_datos_imdb(titulo):
    """Llama a tu API Flask para obtener los datos de IMDb."""
    try:
        titulo_encoded = urllib.parse.quote(titulo)
        url = f"{API_BASE_URL}/pelicula?titulo={titulo_encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Cartelera/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            datos = json.loads(response.read().decode("utf-8"))
            if "error" in datos:
                return None
            return datos
    except Exception as e:
        logging.error(f"Error obteniendo datos IMDb para '{titulo}': {e}")
        return None


# ── Filtrado por perfil de usuario ────────────────────────────────────────────

def pasa_filtro(datos_imdb):
    """Devuelve True si la película pasa el filtro del perfil de usuario."""
    if not datos_imdb:
        return False

    rating = datos_imdb.get("rating")
    if not rating:
        return False

    rating = float(rating)
    generos = datos_imdb.get("genres") or []
    director = datos_imdb.get("director") or ""

    # Si el director es favorito, siempre pasa sin importar la nota
    for dir_favorito in PERFIL_USUARIO["directores_favoritos"]:
        if dir_favorito.lower() in director.lower():
            logging.info(f"  → Pasa por director favorito: {director}")
            return True

    # Comprueba nota mínima por género específico
    for genero in generos:
        if genero in PERFIL_USUARIO["generos"]:
            nota_minima = PERFIL_USUARIO["generos"][genero]
            resultado = rating >= nota_minima
            logging.info(f"  → Género '{genero}': nota {rating} >= {nota_minima} → {resultado}")
            return resultado

    # Nota mínima general
    resultado = rating >= PERFIL_USUARIO["nota_minima_general"]
    logging.info(f"  → Nota general: {rating} >= {PERFIL_USUARIO['nota_minima_general']} → {resultado}")
    return resultado


# ── Envío por Telegram ────────────────────────────────────────────────────────

def enviar_telegram(mensaje):
    """Envía un mensaje por Telegram."""
    # Telegram tiene límite de 4096 caracteres por mensaje
    # Si es muy largo lo partimos
    max_len = 4000
    partes = [mensaje[i:i+max_len] for i in range(0, len(mensaje), max_len)]

    for parte in partes:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            datos = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": parte
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(datos).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                resultado = json.loads(response.read().decode("utf-8"))
                if not resultado.get("ok"):
                    logging.error(f"Error Telegram: {resultado}")
        except Exception as e:
            logging.error(f"Error enviando Telegram: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logging.info("Iniciando scrapper de cartelera...")

    peliculas_cartelera = obtener_cartelera_madrid()

    if not peliculas_cartelera:
        enviar_telegram("⚠️ No se pudo obtener la cartelera de Madrid esta semana.")
        return

    resultados = []
    no_encontradas = []

    for pelicula in peliculas_cartelera:
        titulo = pelicula["titulo"]
        logging.info(f"Consultando IMDb: {titulo}")

        datos_imdb = obtener_datos_imdb(titulo)

        if datos_imdb:
            if pasa_filtro(datos_imdb):
                resultados.append({
                    "titulo": datos_imdb.get("title", titulo),
                    "rating": datos_imdb.get("rating"),
                    "director": datos_imdb.get("director", "N/A"),
                    "duracion": datos_imdb.get("duration", "N/A"),
                    "generos": datos_imdb.get("genres", []),
                    "enlace_ecartelera": pelicula["enlace_ecartelera"],
                    "enlace_imdb": datos_imdb.get("url", "")
                })
        else:
            no_encontradas.append(titulo)

    # Construye el mensaje
    if resultados:
        mensaje = f"🎬 *Cartelera de Madrid — {len(resultados)} películas recomendadas*\n"
        mensaje += f"_(Filtro: nota mínima {PERFIL_USUARIO['nota_minima_general']})_\n\n"

        for p in resultados:
            generos_str = ", ".join(p["generos"]) if p["generos"] else "N/A"
            mensaje += (
                f"{p['titulo']}\n"
                f"⭐ {p['rating']} / 10\n"
                f"🎥 {p['director']}\n"
                f"⏱ {p['duracion']}\n"
                f"🎭 {generos_str}\n"
                f"🔗 {p['enlace_ecartelera']}\n\n"
            )
    else:
        mensaje = (
            "🎬 *Cartelera de Madrid esta semana*\n\n"
            "Ninguna película en cartelera pasa el filtro de tu perfil esta semana."
        )

    if no_encontradas:
        mensaje += f"\n_No encontradas en IMDb: {', '.join(no_encontradas[:5])}_"

    logging.info(f"Enviando resultado: {len(resultados)} películas pasan el filtro")
    enviar_telegram(mensaje)
    logging.info("¡Cartelera enviada por Telegram!")


if __name__ == "__main__":
    main()