FROM python:3.12-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash --user-group botuser

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY --chown=botuser:botuser . .

# Crear directorios necesarios
RUN mkdir -p data shared_data && \
    chown -R botuser:botuser data shared_data

# Cambiar al usuario no-root
USER botuser

# Comando para ejecutar el bot
CMD ["python", "main.py"]