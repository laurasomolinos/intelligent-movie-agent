import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)

# ── Configuración (desde variables de entorno) ────────────────────────────────

TELEGRAM_TOKEN        = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")
TICKETMASTER_API_KEY  = os.environ.get("TICKETMASTER_API_KEY", "")

# Géneros de interés separados por comas. Por defecto: rock
GENEROS_FAVORITOS = [
    g.strip().lower()
    for g in os.environ.get("GENEROS_FAVORITOS", "rock").split(",")
    if g.strip()
]

# ── Llamada a Ticketmaster ────────────────────────────────────────────────────

def obtener_conciertos_madrid():
    """Consulta la API de Ticketmaster y devuelve conciertos de la semana en Madrid."""
    conciertos = []

    hoy       = datetime.now()
    en_7_dias = hoy + timedelta(days=7)
    fecha_ini = hoy.strftime("%Y-%m-%dT00:00:00Z")
    fecha_fin = en_7_dias.strftime("%Y-%m-%dT23:59:59Z")

    for genero in GENEROS_FAVORITOS:
        params = urllib.parse.urlencode({
            "apikey":             TICKETMASTER_API_KEY,
            "classificationName": genero,
            "city":               "Madrid",
            "countryCode":        "ES",
            "startDateTime":      fecha_ini,
            "endDateTime":        fecha_fin,
            "size":               20,
        })
        url = f"https://app.ticketmaster.com/discovery/v2/events.json?{params}"

        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            datos = resp.json()

            eventos = datos.get("_embedded", {}).get("events", [])
            logging.info(f"Ticketmaster devolvió {len(eventos)} eventos para género '{genero}'")

            for e in eventos:
                artista = e.get("name", "Desconocido")
                fecha   = e.get("dates", {}).get("start", {}).get("localDate", "N/A")
                venue   = (
                    e.get("_embedded", {})
                     .get("venues", [{}])[0]
                     .get("name", "N/A")
                )
                enlace = e.get("url", "")

                conciertos.append({
                    "artista": artista,
                    "fecha":   fecha,
                    "venue":   venue,
                    "enlace":  enlace,
                    "genero":  genero,
                })

        except Exception as ex:
            logging.error(f"Error consultando Ticketmaster para '{genero}': {ex}")

    return conciertos


# ── Envío por Telegram ────────────────────────────────────────────────────────

def enviar_telegram(mensaje):
    """Envía un mensaje por Telegram partiéndolo si supera 4096 chars."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no configurados")
        return

    max_len = 4000
    partes  = [mensaje[i:i+max_len] for i in range(0, len(mensaje), max_len)]

    for parte in partes:
        try:
            url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": parte}).encode("utf-8")
            req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resultado = json.loads(resp.read().decode("utf-8"))
                if not resultado.get("ok"):
                    logging.error(f"Error Telegram: {resultado}")
        except Exception as e:
            logging.error(f"Error enviando Telegram: {e}")


# ── Lógica principal ──────────────────────────────────────────────────────────

def ejecutar():
    """Obtiene conciertos de Ticketmaster y envía el resultado por Telegram."""
    logging.info(f"Iniciando agente de conciertos (géneros: {GENEROS_FAVORITOS})...")

    if not TICKETMASTER_API_KEY:
        msg = "⚠️ TICKETMASTER_API_KEY no configurada."
        logging.error(msg)
        return {"ok": False, "mensaje": msg}

    conciertos = obtener_conciertos_madrid()

    # Priorizar eventos normales sobre VIP antes de deduplicar
    conciertos.sort(key=lambda c: 1 if "vip" in c["artista"].lower() else 0)

    # Deduplicar por artista+fecha (Ticketmaster devuelve versión normal y VIP por separado)
    vistos = set()
    unicos = []
    for c in conciertos:
        clave = f"{c['artista'].split('|')[0].strip().lower()}_{c['fecha']}"
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(c)
    conciertos = unicos

    generos_str = ", ".join(GENEROS_FAVORITOS)

    if conciertos:
        mensaje = f"🎸 *Conciertos de {generos_str} en Madrid esta semana*\n\n"
        logging.info(f"── Recomendaciones de la semana ({len(conciertos)}) ──────────────")
        for c in conciertos:
            mensaje += (
                f"🎤 {c['artista']}\n"
                f"📅 {c['fecha']}\n"
                f"📍 {c['venue']}\n"
                f"🔗 {c['enlace']}\n\n"
            )
            logging.info(f"  🎤 {c['artista']} | 📅 {c['fecha']} | 📍 {c['venue']}")
        logging.info("────────────────────────────────────────────────────────────")
    else:
        mensaje = f"🎸 No hay conciertos de {generos_str} en Madrid esta semana."
        logging.info("No hay conciertos que mostrar esta semana.")

    enviar_telegram(mensaje)
    logging.info("Resultado enviado por Telegram.")
    return {"ok": True, "total": len(conciertos), "conciertos": conciertos}


# ── Endpoints HTTP ────────────────────────────────────────────────────────────

@app.route("/ejecutar", methods=["POST", "GET"])
def endpoint_ejecutar():
    resultado = ejecutar()
    return jsonify(resultado)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "generos": GENEROS_FAVORITOS})


# ── Arranque ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)