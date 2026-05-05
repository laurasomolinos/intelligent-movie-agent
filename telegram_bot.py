import logging
import urllib.request
import urllib.parse
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ── Configuración ─────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8702045865:AAH3RCl2TKHOHjuGC4A_djIc2PKiVGrwLqc"  # ← pega aquí tu token de BotFather
API_BASE_URL = "https://resigned-certify-shakiness.ngrok-free.dev"  # ← tu URL de ngrok

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ── Función para llamar a la API ──────────────────────────────────────────────

def obtener_datos(titulo):
    """Llama a la API Flask y devuelve los datos de la película o None si falla."""
    try:
        titulo_encoded = urllib.parse.quote(titulo)
        url = f"{API_BASE_URL}/pelicula?titulo={titulo_encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramBot/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            datos = json.loads(response.read().decode("utf-8"))
            if "error" in datos:
                return None
            return datos
    except Exception as e:
        logging.error(f"Error llamando a la API: {e}")
        return None

# ── Helpers ───────────────────────────────────────────────────────────────────

def extraer_titulo(args):
    """Une los argumentos del comando en un título de película."""
    if not args:
        return None
    return " ".join(args)

async def responder_sin_titulo(update: Update, comando: str):
    await update.message.reply_text(
        f"Debes indicar una película. Por ejemplo: /{comando} Interstellar"
    )

async def responder_error(update: Update, titulo: str):
    await update.message.reply_text(
        f"No he podido encontrar información sobre '{titulo}'. "
        f"Prueba con otro título."
    )

# ── Comandos ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bienvenido al bot de películas IMDb*\n\n"
        "Puedes preguntarme:\n"
        "/nota _película_ — Nota en IMDb\n"
        "/director _película_ — Director\n"
        "/sinopsis _película_ — Sinopsis\n"
        "/duracion _película_ — Duración\n"
        "/votos _película_ — Número de votos\n"
        "/pelicula _película_ — Todos los datos\n\n"
        "Ejemplo: /nota Interstellar",
        parse_mode="Markdown"
    )

async def nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "nota")
        return
    datos = obtener_datos(titulo)
    if datos and datos.get("rating"):
        await update.message.reply_text(
            f"⭐ *{datos['title']}*\nNota IMDb: *{datos['rating']}* / 10",
            parse_mode="Markdown"
        )
    else:
        await responder_error(update, titulo)

async def director(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "director")
        return
    datos = obtener_datos(titulo)
    if datos and datos.get("director"):
        await update.message.reply_text(
            f"🎬 *{datos['title']}*\nDirector: {datos['director']}",
            parse_mode="Markdown"
        )
    else:
        await responder_error(update, titulo)

async def sinopsis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "sinopsis")
        return
    datos = obtener_datos(titulo)
    if datos and datos.get("synopsis"):
        await update.message.reply_text(
            f"📖 *{datos['title']}*\n\n{datos['synopsis']}",
            parse_mode="Markdown"
        )
    else:
        await responder_error(update, titulo)

async def duracion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "duracion")
        return
    datos = obtener_datos(titulo)
    if datos and datos.get("duration"):
        await update.message.reply_text(
            f"⏱ *{datos['title']}*\nDuración: {datos['duration']}",
            parse_mode="Markdown"
        )
    else:
        await responder_error(update, titulo)

async def votos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "votos")
        return
    datos = obtener_datos(titulo)
    if datos and datos.get("votes"):
        votos_fmt = f"{int(datos['votes']):,}".replace(",", ".")
        await update.message.reply_text(
            f"🗳 *{datos['title']}*\nVotos en IMDb: {votos_fmt}",
            parse_mode="Markdown"
        )
    else:
        await responder_error(update, titulo)

async def pelicula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, "pelicula")
        return
    datos = obtener_datos(titulo)
    if datos:
        votos_fmt = f"{int(datos['votes']):,}".replace(",", ".") if datos.get("votes") else "N/A"
        generos = ", ".join(datos["genres"]) if datos.get("genres") else "N/A"
        texto = (
            f"🎬 *{datos.get('title', titulo)}*\n"
            f"⭐ Nota: {datos.get('rating', 'N/A')} / 10\n"
            f"🗳 Votos: {votos_fmt}\n"
            f"🎥 Director: {datos.get('director', 'N/A')}\n"
            f"⏱ Duración: {datos.get('duration', 'N/A')}\n"
            f"🎭 Géneros: {generos}\n\n"
            f"📖 {datos.get('synopsis', 'N/A')}"
        )
        await update.message.reply_text(texto, parse_mode="Markdown")
    else:
        await responder_error(update, titulo)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nota", nota))
    app.add_handler(CommandHandler("director", director))
    app.add_handler(CommandHandler("sinopsis", sinopsis))
    app.add_handler(CommandHandler("duracion", duracion))
    app.add_handler(CommandHandler("votos", votos))
    app.add_handler(CommandHandler("pelicula", pelicula))

    print("Bot arrancado. Pulsa Ctrl+C para parar.")
    app.run_polling()

if __name__ == "__main__":
    main()