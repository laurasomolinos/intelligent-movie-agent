from flask import Flask, jsonify, request
from imdb_scrapper import get_movie_data_imdb
import os
import json

app = Flask(__name__)

# Archivo para caché persistente
CACHE_FILE = "movies_cache.json"

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

# Carga el caché al iniciar
cache = load_cache()


@app.route('/pelicula', methods=['GET'])
def get_pelicula():
    global cache
    
    titulo = request.args.get('titulo', '').strip()
    
    if not titulo:
        return jsonify({"error": "Falta el parámetro 'titulo'"}), 400

    # Clave de cache en minúsculas para no repetir búsquedas
    cache_key = titulo.lower()

    if cache_key in cache:
        print(f"[CACHE HIT] {titulo}")
        return jsonify(cache[cache_key])

    try:
        print(f"[SCRAPING] {titulo}")
        datos = get_movie_data_imdb(titulo)
        cache[cache_key] = datos
        save_cache(cache)  # Guarda en archivo
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)