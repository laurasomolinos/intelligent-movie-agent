# Parte Opcional II

Agente que se ejecute todos los lunes y obtenga los conciertos de la semana, y que filtre por los artistas que interesan al usuario y ponga un mail o telegram con el resultado.

Para esta parte vamos a combinar los conceptos aprendidos en esta práctica. La idea es crear un docker compose que levante dos servicios: uno será el servicio de n8n, que se encargará de activarse todos los lunes a las 9 de la mañana, y el otro es un agente que se ejecuta al recibir una petición HTTP request desde el workflow.

---

## Agente de conciertos

Este agente tiene como funciones:

1. Consultar la API de Ticketmaster para buscar conciertos en Madrid durante los próximos 7 días, filtrando por géneros musicales configurables.
2. Limpiar y deduplicar los resultados (Ticketmaster suele devolver entradas duplicadas: versión normal + VIP).
3. Enviar el resultado por Telegram al chat configurado.
4. Exponerse como un servidor HTTP Flask con endpoints para lanzarlo desde un scheduler.

En resumen, es el equivalente del `cartelera.py` de películas, pero para conciertos: en vez de scrapear eCartelera y consultar IMDb, llama a la API oficial de Ticketmaster y manda el resultado por Telegram.

---

## Workflow de n8n

Compuesto por tres nodos:

1. **Schedule Trigger** — se dispara automáticamente cada lunes a las 9:00. Es el equivalente al cron que usábamos en `cartelera.py`.
2. **Manual Trigger** — permite ejecutar el workflow a mano desde la UI de n8n, sin esperar al lunes. Útil para pruebas.
3. **HTTP Request** — el único nodo de acción. Hace un `POST http://conciertos:5001/ejecutar`, que llama al endpoint Flask del script. Ahí es donde entra el nombre de servicio Docker: `conciertos` se resuelve automáticamente dentro de la red `red_conciertos`.

A diferencia de antes que usábamos cron, en este caso para aprender otro enfoque distinto, n8n actúa como cron con UI visual, y el script Flask queda siempre encendido esperando peticiones HTTP. La ventaja es que puedes ver el historial de ejecuciones, relanzar manualmente, y añadir más nodos (reintentos, alertas de error, etc.) sin tocar código.

Por otra parte, las desventajas de hacerlo con n8n son:

1. **Complejidad innecesaria** — dos contenedores corriendo 24/7 para una tarea que ocurre una vez a la semana. Cron solo existe los segundos que tarda en ejecutarse.
2. **Más puntos de fallo** — Flask, n8n, la red Docker, el volumen y el workflow importado tienen que estar sanos a la vez. Con cron solo puede fallar el script.

Por ello, tras observar ambos enfoques, para el caso más simple la mejor solución es usar cron. Sin embargo, la opción del workflow podría empezar a tener cabida si nuestra idea es hacer que este crezca, por ejemplo con un número mayor de servicios y funcionalidades.