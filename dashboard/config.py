# config.py - Configuración centralizada
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Configuración de la aplicación
class AppConfig:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8050"))
    
    # Datos
    CSV_PATH = DATA_DIR / "raw" / "merged_output.csv"
    KML_PATH = ASSETS_DIR / "Prueba Bot.kml"
    FINCAS_JSON = DATA_DIR / "fincas.json"
    
    # API Keys
    COPERNICUS_CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID")
    COPERNICUS_CLIENT_SECRET = os.getenv("COPERNICUS_CLIENT_SECRET")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    # Telegram Bot
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # Configuración de mapas
    DEFAULT_CENTER = [37.2387, -3.6712]
    DEFAULT_ZOOM = 12

# Configuración de logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
