# Wahl des offizielles Python-Basis-Image.
FROM python:3.12-slim

# Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# Kopie die Abhängigkeiten-Datei und Installation dieser.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kopie den gesamten restlichen Quellcodes wird in das Arbeitsverzeichnis gelegt.
COPY . .

# Port auf den die Anwendung im Container lauscht.
EXPOSE 5000

# Der Befehl, der beim Start des Containers ausgeführt wird.
CMD ["python", "app.py"]