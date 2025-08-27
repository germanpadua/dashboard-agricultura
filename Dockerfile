# Dockerfile (en la raíz del repo)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Paquetes útiles (curl para healthcheck; build-essential si compilas ruedas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    libexpat1 \
    libgeos-c1v5 libgeos-dev \
    proj-bin proj-data \
    gdal-bin \
  && rm -rf /var/lib/apt/lists/*

# Copiamos requirements y luego el código (mejor para cache de capas)
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copia todo el proyecto
COPY . .

# Exponemos el puerto del dashboard (el bot no necesita puerto)
EXPOSE 8050
