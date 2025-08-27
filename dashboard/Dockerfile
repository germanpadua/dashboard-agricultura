FROM python:3.12-slim

# Instalar dependencias del sistema para geopandas y proyecciones
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libgdal-dev \
    libproj-dev \
    libspatialindex-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash --user-group appuser

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY --chown=appuser:appuser . .

# Crear directorios necesarios
RUN mkdir -p data/raw data/fincas cache dynamic_map assets logs shared_data && \
    chown -R appuser:appuser data cache dynamic_map assets logs shared_data

# Cambiar al usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8050

# Comando para ejecutar la aplicación
CMD ["python", "src/app/main.py"]