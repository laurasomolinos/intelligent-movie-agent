from flask import Flask, jsonify, request
from imdb_scrapper import get_movie_data_imdb
import os
import json
import re

app = Flask(__name__)

# Archivo para caché persistente
CACHE_FILE = os.environ.get("CACHE_FILE", "movies_cache.json")
os.makedirs(os.path.dirname(CACHE_FILE) if os.path.dirname(CACHE_FILE) else ".", exist_ok=True)

def load_cache():
    """Carga el caché desde el archivo JSON"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Guarda el caché en el archivo JSON"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando caché: {e}")


def normalizar_titulo(titulo):
    """Genera una clave estable para cache a partir del título."""
    return re.sub(r'\s+', ' ', (titulo or '')).strip().lower()

# Carga el caché al iniciar
cache = load_cache()


@app.route('/pelicula', methods=['GET'])
def get_pelicula():
    global cache
    
    titulo = request.args.get('titulo', '').strip()
    
    if not titulo:
        return jsonify({"error": "Falta el parámetro 'titulo'"}), 400

    # Clave estable para no repetir búsquedas por diferencias de espacios o mayúsculas
    cache_key = normalizar_titulo(titulo)
    legacy_key = titulo.lower()

    if cache_key in cache:
        print(f"[CACHE HIT] {titulo}")
        return jsonify(cache[cache_key])

    if legacy_key in cache:
        print(f"[CACHE HIT LEGACY] {titulo}")
        datos = cache[legacy_key]
        cache[cache_key] = datos
        save_cache(cache)
        return jsonify(datos)

    print(f"[CACHE MISS] {titulo}")
    return jsonify({"cached": False}), 404


@app.route('/pelicula/scrape', methods=['GET'])
def scrape_pelicula():
    titulo = request.args.get('titulo', '').strip()
    if not titulo:
        return jsonify({"error": "Falta el parámetro 'titulo'"}), 400
    try:
        print(f"[SCRAPING FORZADO] {titulo}")
        datos = get_movie_data_imdb(titulo)
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/pelicula/cache', methods=['POST'])
def save_pelicula_cache():
    global cache
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"error": "body vacío"}), 400

    # n8n specifyBody:"string" may double-encode: body arrives as a JSON string instead of dict
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            return jsonify({"error": "body string invalido"}), 400

    # n8n a veces envía el JSON completo como KEY del objeto: {"<json_string>": null}
    if isinstance(body, dict) and not body.get('title') and not body.get('for_cache'):
        first_key = next(iter(body), '')
        try:
            parsed = json.loads(first_key)
            if isinstance(parsed, dict):
                body = parsed
        except Exception:
            pass

    datos = body.get('for_cache') or body.get('datos') or body
    if not datos or not datos.get('title'):
        return jsonify({"error": "Datos inválidos"}), 400

    cache_key = normalizar_titulo(datos.get('_cache_key') or datos.get('title', ''))
    cache[cache_key] = datos
    save_cache(cache)
    return jsonify({"ok": True})


@app.route('/audit', methods=['GET'])
@app.route('/audit/cache-hit', methods=['GET'])
@app.route('/audit/dead-letter', methods=['GET'])
def audit_event():
    return jsonify({
        "ok": True,
        "route": request.path,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)