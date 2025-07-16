# Dockerfile
FROM python:3.11-slim

# ‑‑ install JDK 11 for Gradle builds
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ‑‑ copy source
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ‑‑ EXPOSE is only documentation; Render injects $PORT1 AND $PORT2
EXPOSE 8000 8080
ENV PORT1=8000
ENV PORT2=8080

# Start FastAPI on the port Render provides
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "$PORT1", "&", "python", "-m", "http.server", "$PORT2", "--directory", "./"]
