# syntax=docker/dockerfile:1
###############################################################################
#  Stage 1 – base image with Java 21, Python 3, and Maven 3.9.10
###############################################################################
FROM eclipse-temurin:21-jdk-jammy AS base

# --- OS packages (git is handy for Gradle plugins that use it) ---------------
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 python3-pip git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# --- Maven 3.9.10 ------------------------------------------------------------
ARG MAVEN_VERSION=3.9.11
RUN curl -fsSL https://dlcdn.apache.org/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
      | tar -xz -C /opt && \
    ln -s /opt/apache-maven-${MAVEN_VERSION}/bin/mvn /usr/local/bin/mvn

WORKDIR /app

###############################################################################
#  Stage 2 – install Python deps only once for better layer caching
###############################################################################
FROM base AS python-deps

# If you keep a requirements.txt, copy it; otherwise install directly.
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
# RUN pip3 list
# RUN pip3 install --no-cache-dir fastapi uvicorn[standard] python-multipart jinja2 aiofiles

###############################################################################
#  Stage 3 – application: copy source and prep Gradle wrapper
###############################################################################
FROM base AS app-src

WORKDIR /app
COPY --from=python-deps /usr/local/lib/python3.*/site-packages /usr/local/lib/python3.*/site-packages
COPY . .

# Ensure the Gradle wrapper is executable for Linux
RUN chmod +x ./gradlew

###############################################################################
#  Stage 4 – runtime: smallest possible final image ---------------------------
FROM eclipse-temurin:21-jdk-jammy AS runtime

WORKDIR /app

# Copy everything from the previous layer
COPY --from=app-src /app /app
COPY --from=python-deps /usr/local/lib/python3.*/site-packages /usr/local/lib/python3.*/site-packages
RUN pip list

# Default port for FastAPI; free tiers override $PORT
EXPOSE 8000

# When hosts set $PORT we respect it, otherwise fall back to 8000.
# Two workers handle concurrent /buildomlfile uploads without huge RAM use.
# CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
