# 🌾 Dashboard de Agricultura Inteligente

> **Proyecto de Trabajo Final de Máster (TFM)**  
> **Universidad de Granada | Máster en Ciencia de Datos**  
> **Autor**: Germán José Padua Pleguezuelo


Dashboard interactivo de para el monitoreo y análisis integral de fincas agrícolas, especialmente olivares. Integra datos satelitales (Sentinel-2), meteorológicos (AEMET) y análisis temporal avanzado.

![Dashboard Principal](assets/screenshots/dashboard-main.png)
*📷  Captura del dashboard principal *

---

## 🚀 Características Principales

### 📊 **Análisis Satelital Avanzado**
- **Datos Sentinel-2** con resolución de 10m/píxel
- **Índices de vegetación**: NDVI, OSAVI, NDRE especializados para olivar
- **Detección de anomalías** comparando con años históricos
- **Análisis temporal** con series de datos automáticas
- **Visualización orientada a agricultores** con métricas simplificadas

![Análisis Satelital](assets/screenshots/satellite-analysis.png)
*📷 Captura mostrando el mapa satelital con overlay NDVI, gráficos de evolución y KPIs para agricultores*

### 🌤️ **Predicciones Meteorológicas Inteligentes**
- **Datos AEMET** en tiempo real con predicciones a 7 días
- **Análisis de riesgo de repilo** basado en condiciones científicas
- **Alertas automáticas** por umbrales críticos de temperatura y humedad
- **Gráficos interactivos** con zonas de riesgo visualmente destacadas
- **Sistema de caché inteligente** para optimizar consultas

![Predicciones Meteorológicas](assets/screenshots/weather-forecast.png)
*📷 Captura del módulo meteorológico mostrando las weather cards, gráfico 48h con zonas de riesgo y sistema de alertas*

### 🏡 **Gestión Integral de Fincas**
- **Registro georreferenciado** dibujando perímetros en mapas interactivos
- **Base de datos espacial** con información de cultivos, superficies y propietarios
- **Integración automática** con módulos de análisis satelital
- **Mapas duales**: vista satelital (ArcGIS) y calles (OpenStreetMap)
- **Sistema de métricas** dinámicas por explotación

![Gestión de Fincas](assets/screenshots/farm-management.png)
*📷 Captura mostrando el mapa con fincas registradas, formulario de nueva finca y tarjetas de fincas existentes*

### 📈 **Análisis Histórico Temporal**
- **Series temporales** de variables meteorológicas y satelitales
- **Análisis comparativo** entre temporadas
- **Detección de patrones estacionales** específicos del olivar mediterráneo
- **Predicciones estadísticas** basadas en datos históricos
- **Reportes automáticos** de tendencias y anomalías

![Análisis Histórico](assets/screenshots/historical-analysis.png)
*📷 Captura de gráficos de evolución temporal, análisis de tendencias y comparaciones interanuales*

### 📱 **Sistema de Detección de Enfermedades**
- **Bot de Telegram** independiente para registro desde campo
- **Georreferenciación automática** con fotos y coordenadas GPS
- **Extracción de metadatos EXIF** de fotografías
- **Integración con Google Drive** para almacenamiento en la nube
- **Sincronización automática** con dashboard web
- **Dashboard web** con galería interactiva y mapas de calor
- **Sistema KML** para exportar detecciones a Google Earth

![Sistema de Detecciones](assets/screenshots/disease-detection.png)
*📷  Captura del dashboard de detecciones mostrando el mapa con incidencias, galería de fotos y estadísticas*

---

## 🛠️ Tecnologías y Arquitectura

### **Stack Tecnológico**
```
Frontend: Dash 3.2.0 + Plotly + Bootstrap + Leaflet
Backend: Python 3.8+ + Flask 3.1.1 + Pandas 2.3.1
APIs: Copernicus Dataspace + AEMET + OpenWeather + Telegram
Base de Datos: JSON + Sistema de caché inteligente
Mapas: Leaflet.js + ArcGIS + OpenStreetMap
Análisis Geoespacial: GeoPandas 1.1.1 + Rasterio 1.4.3
Procesamiento: NumPy 2.2.6 + OpenCV 4.12.0 + Scikit-image
Containerización: Docker + Docker Compose
```

### **Arquitectura Modular**
```
dashboard-agricultura/
├── 📱 dashboard/                  # Aplicación Web Principal
│   ├── 📁 src/
│   │   ├── 🎯 app/               # Configuración y entry point
│   │   ├── 🎨 layouts/           # Interfaces por módulo (5 pestañas)
│   │   ├── ⚡ callbacks_refactored/ # Lógica de negocio modular
│   │   ├── 🔧 components/        # Componentes UI reutilizables
│   │   ├── 🛠️ utils/             # APIs y utilidades especializadas
│   │   └── 🔗 integrations/      # Telegram sync y APIs externas
│   ├── 📊 data/                  # Datos estructurados (fincas, análisis)
│   ├── 🎨 assets/                # CSS, imágenes, detecciones
│   ├── 💾 cache/                 # Sistema de caché inteligente
│   ├── 🗺️ dynamic_map/           # Overlays satelitales generados
│   └── 📓 notebooks/             # Jupyter notebooks para EDA
├── 🤖 telegram_bot/              # Bot de Telegram Independiente
│   ├── 🎯 main.py               # Entry point del bot
│   ├── 🤖 bot.py                # Lógica del bot y handlers
│   ├── 📊 kml_utils.py          # Procesamiento geoespacial
│   ├── 📷 exif_utils.py         # Extracción de metadatos de fotos
│   ├── ☁️ drive_utils.py        # Integración con Google Drive
│   └── 🔐 auth_drive.py         # Autenticación Google
├── 🐳 docker-compose.yml         # Orquestación de servicios
└── 📋 requirements.txt           # Dependencias base
```

---

## ⚡ Instalación y Configuración

### **Requisitos del Sistema**

- **Conexión estable** a Internet para descarga de datos

### **1. Instalación Base**
```bash
# Clonar el repositorio
git clone https://github.com/germanpadua/dashboard-agricultura.git
cd dashboard-agricultura

# Crear entorno virtual
python -m venv envTFM
envTFM\Scripts\activate        # Windows
# source envTFM/bin/activate   # Linux/Mac

# Instalar dependencias del dashboard
pip install -r requirements.txt

```

### **2. Configuración de APIs**
Crea archivos de configuración según tus necesidades:

**Para el Dashboard (`.env` en /dashboard/)**:
```env
# ===== REQUERIDO: Copernicus Data Space =====
COPERNICUS_CLIENT_ID=tu_client_id_aqui
COPERNICUS_CLIENT_SECRET=tu_client_secret_aqui

# ===== OPCIONAL: APIs adicionales =====
AEMET_API_KEY=tu_api_key_aemet

# ===== CONFIGURACIÓN SERVIDOR =====
HOST=0.0.0.0
PORT=8050
DEBUG=False
CACHE_DURATION=1800  # 30 minutos
```

**Para el Bot de Telegram (`.env.bot` en /telegram_bot/)**:
```env
# ===== TELEGRAM BOT =====
TELEGRAM_BOT_TOKEN=tu_token_bot_telegram
CHAT_ID=tu_chat_id

# ===== GOOGLE DRIVE (opcional) =====
GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
```

**🔑 Obtener credenciales**:
- **Copernicus**: [dataspace.copernicus.eu](https://dataspace.copernicus.eu/) (gratuito)
- **AEMET**: [opendata.aemet.es](https://opendata.aemet.es/) (gratuito)
- **Telegram Bot**: [@BotFather](https://t.me/botfather) en Telegram

### **3. Ejecución**

## 🐳 Despliegue con Docker

```bash
# Clonar repositorio
git clone https://github.com/germanpadua/dashboard-agricultura.git
cd dashboard-agricultura

# Configurar variables de entorno
cp dashboard/.env.example dashboard/.env
cp telegram_bot/.env.bot.example telegram_bot/.env.bot
# Editar archivos .env con tus credenciales

# Ejecutar servicios
docker-compose up --build

# Acceder:
# Dashboard: http://localhost:8050
# Bot de Telegram: activo automáticamente
```

### **Servicios Incluidos**
- **web**: Dashboard Dash
- **bot**: Bot de Telegram con sincronización automática
- **Volúmenes persistentes**: Para cache, datos y configuración

### **Comandos Útiles**
```bash
# Ver logs en tiempo real
docker-compose logs -f

# Solo dashboard
docker-compose up web

# Solo bot
docker-compose up bot

# Reiniciar servicios
docker-compose restart

# Parar y limpiar
docker-compose down
docker system prune -f
```

---

## 🎯 Guía de Uso

### **🗺️ Gestión de Fincas**
1. **Registro**: Accede a "Gestión de Fincas" → Dibuja perímetro en el mapa
2. **Guardado**: Las fincas se integran automáticamente en otros módulos

### **🛰️ Análisis Satelital**
1. **Selección**: Elige finca registrada o dibuja área temporal
2. **Configuración**: Define fechas de análisis y años de referencia
3. **Índices**: Selecciona NDVI, OSAVI o NDRE según necesidad
4. **Interpretación**: Los resultados se presentan con métricas para agricultores

### **🌤️ Predicciones Meteorológicas**  
1. **Municipio**: Selecciona ubicación (predeterminado: Benalúa, Almería)
2. **Monitoreo**: Revisa KPIs actuales y predicción semanal
3. **Alertas**: El sistema detecta automáticamente condiciones de riesgo para repilo
4. **Análisis**: Usa el gráfico 48h para planificar tratamientos preventivos

### **📈 Datos Históricos**
1. **Variables**: Selecciona temperatura, humedad, NDVI u otros índices
2. **Período**: Define rango temporal (recomendado: mínimo 1 año)
3. **Comparación**: Analiza tendencias y detecta patrones estacionales
4. **Exportación**: Descarga reportes en PDF o CSV

### **📱 Sistema de Detecciones**
1. **Configuración**: Configura el bot de Telegram con tu token
2. **Registro en Campo**: Envía foto con ubicación desde cualquier dispositivo
3. **Procesamiento**: El bot extrae coordenadas GPS y metadatos automáticamente
4. **Almacenamiento**: Las detecciones se sincronizan con Google Drive
5. **Visualización**: Monitorea incidencias desde el dashboard web
6. **Análisis**: Utiliza mapas de calor y estadísticas temporales
7. **Exportación**: Descarga datos KML para análisis en GIS


---

## 📚 Referencias Científicas

1. 

---

## 👨‍💻 Autor

**Germán José Padua Pleguezuelo**  
📧 german.padua@ugr.es  
🎓 Máster en Ciencia de Datos - Universidad de Granada  
🔗 LinkedIn: [linkedin.com/in/german-jose-padua-pleguezuelo/](https://www.linkedin.com/in/german-jose-padua-pleguezuelo/)  
🐙 GitHub: [github.com/germanpadua](https://github.com/germanpadua)

---

## 📝 Licencia



---

## 🏆 Reconocimientos

- **Universidad de Granada** - Máster en Ciencia de Datos  
- **Copernicus Programme** - Datos satelitales Sentinel-2
- **AEMET** - Datos meteorológicos oficiales
- **Comunidad open-source** - Librerías Dash, Plotly, Leaflet
