import logging
import urllib.request
import urllib.parse
import urllib.error
import json

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = '8755548017:AAEXUjVpwFWr_6qOPtYz_ZnZ_YvsozMbZjE'
N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/pelicula-guardrail'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def obtener_datos(titulo, comando='pelicula'):
    """
    Llama al workflow n8n que valida, scrapea (si es necesario) y devuelve
    los datos completos de la película incluyendo el análisis de la IA.
    Retorna el objeto 'datos' o {'error': '...'} si falla.
    """
    payload = {
        'titulo': titulo,
        'source': 'telegram',
        'command': comando,
    }
    body = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        },
        method='POST'
    )

    try:
        # Timeout generoso: 90s para peliculas nuevas que requieren scraping + LLM
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(response.read().decode('utf-8'))

        if result.get('status') == 'error' or result.get('decision') == 'REJECT':
            return {'error': result.get('message', 'Pelicula rechazada por el sistema')}

        datos = result.get('datos')
        if not datos:
            return {'error': 'Respuesta inesperada del servidor'}

        if result.get('reply'):
            datos['_reply'] = result.get('reply')

        return datos

    except urllib.error.HTTPError as e:
        try:
            body_err = json.loads(e.read().decode('utf-8'))
            return {'error': body_err.get('message', f'Error HTTP {e.code}')}
        except Exception:
            return {'error': f'Error HTTP {e.code}'}
    except urllib.error.URLError as e:
        return {'error': f'Error de conexion: {e.reason}. Comprueba que n8n y la API esten corriendo.'}
    except Exception as e:
        return {'error': f'Error inesperado: {e}'}


def extraer_titulo(args):
    return ' '.join(args)


async def responder_sin_titulo(update: Update, comando: str):
    await update.message.reply_text(f'Indica una pelicula. Ejemplo: /{comando} Interstellar')


async def responder_error(update: Update, titulo: str, motivo: str = ''):
    msg = f"No he podido encontrar informacion sobre '{titulo}'."
    if motivo:
        msg += f'\n{motivo}'
    await update.message.reply_text(msg)


async def responder_reply_si_existe(update: Update, datos):
    reply = datos.get('_reply')
    if reply:
        await update.message.reply_text(reply)
        return True
    return False


async def handle_error_or_reply(update: Update, titulo: str, datos: dict) -> bool:
    if datos.get('error'):
        await responder_error(update, titulo, datos['error'])
        return True
    if await responder_reply_si_existe(update, datos):
        return True
    return False


async def handle_errors_only(update: Update, titulo: str, datos: dict) -> bool:
    if datos.get('error'):
        await responder_error(update, titulo, datos['error'])
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🎬 *Bot de peliculas IMDb*\n\n'
        '/nota _pelicula_ — Nota en IMDb\n'
        '/director _pelicula_ — Director\n'
        '/sinopsis _pelicula_ — Sinopsis\n'
        '/duracion _pelicula_ — Duracion\n'
        '/votos _pelicula_ — Votos\n'
        '/pelicula _pelicula_ — Todo + analisis IA\n\n'
        'Ejemplo: /nota Interstellar',
        parse_mode='Markdown'
    )


async def nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'nota')
        return

    datos = obtener_datos(titulo, 'nota')
    if await handle_error_or_reply(update, titulo, datos):
        return

    url = datos.get('url', '')
    link = f' [IMDb]({url})' if url else ''
    await update.message.reply_text(
        f"⭐ *{datos.get('title', titulo)}*\n"
        f"Nota IMDb: *{datos.get('rating')}* / 10{link}",
        parse_mode='Markdown'
    )


async def director(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'director')
        return

    datos = obtener_datos(titulo, 'director')
    if await handle_error_or_reply(update, titulo, datos):
        return

    url = datos.get('url', '')
    link = f' [IMDb]({url})' if url else ''
    await update.message.reply_text(
        f"🎬 *{datos.get('title', titulo)}*\n"
        f"Director: {datos.get('director', 'Desconocido')}{link}",
        parse_mode='Markdown'
    )


async def sinopsis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'sinopsis')
        return

    datos = obtener_datos(titulo, 'sinopsis')
    if await handle_error_or_reply(update, titulo, datos):
        return

    url = datos.get('url', '')
    link = f'\n\n[Ver en IMDb]({url})' if url else ''
    await update.message.reply_text(
        f"📖 *{datos.get('title', titulo)}*\n\n"
        f"{datos.get('synopsis', 'Sinopsis no disponible.')}{link}",
        parse_mode='Markdown'
    )


async def duracion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'duracion')
        return

    datos = obtener_datos(titulo, 'duracion')
    if await handle_error_or_reply(update, titulo, datos):
        return

    url = datos.get('url', '')
    link = f' [IMDb]({url})' if url else ''
    await update.message.reply_text(
        f"⏱ *{datos.get('title', titulo)}*\n"
        f"Duracion: {datos.get('duration', 'No disponible')}{link}",
        parse_mode='Markdown'
    )


async def votos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'votos')
        return

    datos = obtener_datos(titulo, 'votos')
    if await handle_error_or_reply(update, titulo, datos):
        return

    votos_raw = datos.get('votes', 0)
    try:
        votos_num = int(votos_raw)
        votos_fmt = f"{votos_num:,}".replace(',', '.')
    except (ValueError, TypeError):
        votos_fmt = str(votos_raw)

    url = datos.get('url', '')
    link = f' [IMDb]({url})' if url else ''
    await update.message.reply_text(
        f"🗳 *{datos.get('title', titulo)}*\n"
        f"Votos en IMDb: {votos_fmt}{link}",
        parse_mode='Markdown'
    )


async def pelicula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titulo = extraer_titulo(context.args)
    if not titulo:
        await responder_sin_titulo(update, 'pelicula')
        return

    datos = obtener_datos(titulo, 'pelicula')
    if await handle_errors_only(update, titulo, datos):
        return

    votos_raw = datos.get('votes', 0)
    try:
        votos_num = int(votos_raw)
        votos_fmt = f"{votos_num:,}".replace(',', '.')
    except (ValueError, TypeError):
        votos_fmt = str(votos_raw)

    generos = ', '.join(datos.get('genres', [])) or 'No disponible'
    url = datos.get('url', '')
    link = f'\n\n[Ver en IMDb]({url})' if url else ''

    # Campos de IA (solo si estan disponibles)
    ai_vibra = datos.get('ai_vibra', '')
    ai_rec = datos.get('ai_recomendacion', '')
    ai_con = datos.get('ai_para_ver_con', '')

    ai_block = ''
    if ai_rec:
        vibra = f' {ai_vibra}' if ai_vibra else ''
        ai_block = f'\n\n─────────────────\n🤖 _{ai_rec}{vibra}_'
        if ai_con:
            ai_block += f'\n👥 *Para ver con:* {ai_con}'

    titulo_display = datos.get('title', titulo)
    texto = (
        f"🎬 *{titulo_display}*\n"
        f"─────────────────\n"
        f"⭐ *Nota:* {datos.get('rating')} / 10   🗳 *Votos:* {votos_fmt}\n"
        f"🎥 *Director:* {datos.get('director', 'Desconocido')}\n"
        f"⏱ *Duracion:* {datos.get('duration', 'N/D')}\n"
        f"🎭 *Generos:* {generos}\n\n"
        f"📖 _{datos.get('synopsis', 'Sinopsis no disponible.')}_"
        f"{ai_block}"
        f"{link}"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('nota', nota))
    app.add_handler(CommandHandler('notas', nota))
    app.add_handler(CommandHandler('director', director))
    app.add_handler(CommandHandler('sinopsis', sinopsis))
    app.add_handler(CommandHandler('duracion', duracion))
    app.add_handler(CommandHandler('votos', votos))
    app.add_handler(CommandHandler('pelicula', pelicula))

    print('Bot arrancado. Pulsa Ctrl+C para parar.')
    app.run_polling()


if __name__ == '__main__':
    main()
