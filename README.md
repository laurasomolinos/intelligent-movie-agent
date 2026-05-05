Archivos importantes:

- pruebas.ipynb:  explica el proceso de todo el trabajo
- debug_save_html.py:  (NO NECESARIO PARA FUNCIONAMIENTO) es el archivo con el que saque el html (debug_search.html) de la pagina para hacer el scrapping luego en imdb_scrapper_base.py (imdb_2001.html es el html concreto de una pelicula como prueba)
- imdb_scrapper_base.py:  (no se usa ya) script de pueba para sacar los datos de una pelicula concreta con su url para ver si funcionaba teniendo en cuenta el html que sacamos con debug_save_html.py
- imdb_scrapper.py:  script que hace todo el proceso de sacar la información de las peliculas de imdb, si se ejecuta por consola y se le pide una pelicula concreta la busca en la pagina de imdb y devuelve los datos que queremos (se pueden añadir parametros por consola)
- lambda_function.py:  El código de Alexa. Se sube a AWS Lambda y conecta Alexa con la API Flask a través de ngrok. -> https://developer.amazon.com/alexa/console/ask/test/amzn1.ask.skill.e033956a-2500-4297-af2c-94a612f22f8c/development/es_ES/
- telegram_bot.py: El bot de Telegram. Si al bot le decimos: /nota Interstellar, consulta API Flask y nos devuelve los datos.
Para la API:
-  api.py:  La API Flask. Recibe peticiones HTTP con el título de una película, llama al scrapper, guarda en caché y devuelve el JSON.
- Dockerfile:  Instrucciones para construir el contenedor de la API Flask con Playwright y Chromium incluidos.
- docker-compose.yml: Orquesta dos contenedores: la API Flask y ngrok. Con un solo comando arranca los dos juntos. Necesario para ejecutarlo en docker
Para correr todo esto simplemente poner docker compose up en la consola de 
Para la cartelera:
debug_cartelera.html: html guardado de la web de carteleras de madrid (NO NECESARIO PARA FUNCIONAMIENTO)
cartelera.py:  Scrapper de ecartelera.com. Obtiene las películas en cartelera en Madrid, consulta IMDb por cada una, filtra por tu perfil y envía el resultado por Telegram. Se ejecuta con cron los lunes.


Se necesitaria un archivo .env para inicializar grok que contenga el token de la api

Para arrancarlo necesitamos: 
1. Docker — arranca la API Flask + ngrok. En la terminal de VS Code dentro de este proyecto:
   docker compose up --build
  
