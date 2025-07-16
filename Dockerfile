# Dockerfile
FROM maven:3.9.10-eclipse-temurin-21 AS runtime
#   • JDK 21.0.7 LTS & Maven 3.9.10 are already present
#     (see official tags list)  :contentReference[oaicite:2]{index=2}

# ---- Install Python 3 + pip ---------------------------------------------------
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Debian‑Slim packages are tiny yet compatible with Alpine‑size images  :contentReference[oaicite:3]{index=3}

# ---- Create working dir ------------------------------------------------------
WORKDIR /app

# ---- Python dependencies -----------------------------------------------------
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# ---- Copy project code & Gradle wrapper --------------------------------------
COPY . .

# Provide executable permissions to the Gradle wrapper script gradlew and gradlew.bat
# (if it exists) so that it can be executed in the container
# This is necessary for the Gradle wrapper to work correctly in the container environment
RUN chmod +x gradlew.bat || true
# The || true part ensures that if gradlew.bat does not exist, the command does not fail
RUN chmod +x gradlew


# ‑‑ EXPOSE is only documentation; Render injects $PORT1 AND $PORT2
ENV PORT=8000
EXPOSE 8000

# Start FastAPI on the port Render provides
RUN echo "$PORT"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
