# Agente Inteligente de Películas — n8n Workflow

Bot de Telegram que responde consultas sobre películas usando scraping de IMDb, caché persistente y enriquecimiento con IA, orquestado completamente en n8n.

---

## Stack

El proyecto corre en cuatro contenedores Docker: la API de scraping en Python con Flask y Playwright, Redis, ngrok para exponer n8n públicamente, y n8n como orquestador central. El bot de Telegram corre fuera de Docker y se conecta a n8n por HTTP. El LLM utilizado es LLaMA 3.3 70B a través de la API de Groq.

---

## Cómo funciona el flujo

El usuario escribe un comando en Telegram, por ejemplo `/pelicula Inception`. El bot hace una petición HTTP a n8n y espera la respuesta hasta 90 segundos.

n8n recibe la petición por un webhook, normaliza el título y comprueba primero si ya existe en caché. Si existe, responde en menos de un segundo con los datos guardados. Si no existe, continúa al proceso completo.

**Guardrail:** antes de lanzar el scraping, el sistema valida que el input sea un título de película real. Para ello hace una llamada rápida a Groq con el LLM, que responde únicamente true o false. Además, una capa de detección por keywords con normalización Unicode bloquea intentos de prompt injection como "ignora las instrucciones" o "olvídate de todo". Si el input no pasa el guardrail, el flujo termina ahí sin tocar el scraper.

**Scraping:** si el guardrail aprueba el input, n8n llama a la API Flask, que lanza un navegador Chromium real con Playwright. El navegador busca la película en IMDb, navega a su página y extrae los datos estructurados del bloque JSON-LD que IMDb incluye en todas sus páginas: título, director, puntuación, votos, sinopsis, duración y géneros. Este proceso tarda aproximadamente 60 segundos.

**Enriquecimiento con IA:** con los datos del scraping, se hace una segunda llamada a Groq para que el LLM genere una recomendación personalizada, un emoji representativo y una sugerencia de con quién ver la película.

**Respuesta final:** n8n monta el objeto de datos completo, responde la petición HTTP al bot, y guarda los datos en caché para que futuras consultas de la misma película sean instantáneas. El bot recibe el objeto y formatea el mensaje de Telegram con toda la información.

---

## Por qué existe el guardrail

Aunque el bot solo devuelve información de películas, internamente usa un LLM que recibe el input del usuario. Sin guardrail, un input malicioso podría manipular las instrucciones del LLM de enriquecimiento. Además, cada petición lanza un scraping de 60 segundos y una llamada de pago a la API de Groq, por lo que filtrar inputs inválidos antes tiene un impacto real en rendimiento y coste.

---

## Tiempos de respuesta

Una consulta con cache hit responde en menos de un segundo. Una consulta rechazada por el guardrail tarda entre uno y tres segundos. Una consulta nueva que requiere scraping tarda entre 60 y 70 segundos en total.

---

## Arranque

Levantar los servicios con `docker compose up -d` y arrancar el bot manualmente con `python telegram_bot.py`. Las credenciales necesarias van en el archivo `.env`: token de Groq, token de Telegram, ID del chat y token de ngrok.

---

## Comandos disponibles

El bot responde a `/pelicula`, `/nota`, `/director`, `/sinopsis`, `/duracion`, `/votos` y `/start`. Todos admiten el título de la película como argumento.

---

## Limitaciones

El scraping tarda cerca de un minuto en primeras consultas. La detección de inyecciones cubre patrones conocidos pero no es exhaustiva. Títulos homónimos sin año pueden colisionar en caché.
