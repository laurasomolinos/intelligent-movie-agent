1)  scrapper en python que, dada una película, obtenga un diccionario con la
información de la misma + parametros por consola (imdb_scrapper.py, proceso con: debug_save_html.py, imdb_scrapper_base.py)

2) skill de Alexa que utilizará el scrapper anterior para, cuando el usuario le
pida algún dato de una película  + video (apy.py, lambda_function.py, imdb_scrapper.py)

3) scrapper que obtenga la cartelera de cine de Madrid, integre esta información con la proporcionada por el scrapper anterior. Este scrapper se ejecutará todos los lunes a las 9:00 (usar cron) y enviará el resultado por telegram o por mail.  (cartelera.py, api.py, imdb_scrapper.py, telegram_bot, siguiendo los pasos del scrpper de imdb)

4) Opcional: perfil del usuario que valore cada género, filtre la nota por
ese perfil (cartelera.py)

5) opcional: Creación de workflow en N8N
✱ Workflow con N8N para implementar un guardarraíl

6) opcional: Un agente que se ejecute todos los lunes y obtenga los conciertos de la
semana
✓ Que filtre por los artistas que interesan al usuario y ponga un mail o
telegram con el resultado (carpeta conciertos)

Archivos importantes:

- pruebas.ipynb:  explica el proceso de todo el trabajo
- debug_save_html.py:  (NO NECESARIO PARA FUNCIONAMIENTO) es el archivo con el que saque el html (debug_search.html) de la pagina para hacer el scrapping luego en imdb_scrapper_base.py (imdb_2001.html es el html concreto de una pelicula como prueba)
- imdb_scrapper_base.py:  (no se usa ya) script de pueba para sacar los datos de una pelicula concreta con su url para ver si funcionaba teniendo en cuenta el html que sacamos con debug_save_html.py
- imdb_scrapper.py:  script que hace todo el proceso de sacar la información de las peliculas de imdb, si se ejecuta por consola y se le pide una pelicula concreta la busca en la pagina de imdb y devuelve los datos que queremos (se pueden añadir parametros por consola)
- lambda_function.py:  El código de Alexa. Se sube a AWS Lambda y conecta Alexa con la API Flask a través de ngrok. (dentro de carpeta alexa con video de la prueba del funcionamiento de la skill)
- telegram_bot.py: El bot de Telegram. Si al bot le decimos: /nota Interstellar, consulta API Flask y nos devuelve los datos.

  
Para la API:
-  api.py:  La API Flask. Recibe peticiones HTTP con el título de una película, llama al scrapper, guarda en caché y devuelve el JSON.
- Dockerfile:  Instrucciones para construir el contenedor de la API Flask con Playwright y Chromium incluidos.
- docker-compose.yml: Orquesta dos contenedores: la API Flask y ngrok. Con un solo comando arranca los dos juntos. Necesario para ejecutarlo en docker
Para correr todo esto simplemente poner docker compose up en la consola de 
Para la cartelera:
debug_cartelera.html: html guardado de la web de carteleras de madrid (NO NECESARIO PARA FUNCIONAMIENTO)
cartelera.py:  Scrapper de ecartelera.com. Obtiene las películas en cartelera en Madrid, consulta IMDb por cada una, filtra por tu perfil y envía el resultado por Telegram. Se ejecuta con cron los lunes.


## Arranque para el funcionamiento de todas las tareas:

1. Crear .env con: NGROK_AUTHTOKEN=tu_token
2. docker compose up --build
3. Copiar URL de ngrok (localhost:4040) en lambda_function.py y subirla a AWS Lambda
4. python telegram_bot.py (en terminal separada)
5. Cron (WSL): 0 9 * * 1 python3 cartelera.py

## Conversaciones LLM
https://chatgpt.com/g/g-p-69e7414b231c81918742e99d463872d2-agente-peliculas-si/project
  
