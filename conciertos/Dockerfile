FROM python:3.11-slim

WORKDIR /app

COPY conciertos.py .

RUN pip install --no-cache-dir flask requests

CMD ["python", "conciertos.py"]