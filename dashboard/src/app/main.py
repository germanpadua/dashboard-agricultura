"""
Autor: German Jose Padua Pleguezuelo
Universidad de Granada
Master en Ciencia de Datos

Fichero: main.py
"""

# Imports
import os
import sys
import logging
from pathlib import Path
from flask import send_from_directory
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


# Añadir directorio raíz al path para imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,  # Cambiar de DEBUG a INFO para reducir verbosidad
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# Configurar niveles específicos para diferentes módulos
logging.getLogger('src.callbacks_refactored.prediccion').setLevel(logging.INFO)
logging.getLogger('src.utils.weather_utils').setLevel(logging.INFO)
logging.getLogger('src.callbacks_refactored.main').setLevel(logging.INFO)

# Reducir verbosidad de módulos externos
logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logging.getLogger('numexpr').setLevel(logging.WARNING)
logging.getLogger('dash.dash').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

from src.callbacks_refactored import register

from src.app.data_loader import load_data, load_kml
from src.integrations.telegram_sync import TelegramDataSync

from src.layouts.app_layout import create_main_layout


def initialize_data():
    """
    Inicializa y carga todos los datos necesarios para el dashboard
    """
    logger.info("Cargando Datos para el Dashboard")
        
    # Paths de datos
    CSV_PATH = "data/raw/merged_output.csv"
    KML_PATH = "assets/Prueba Bot.kml"
    
    try:
        # Cargar datos meteorológicos
        df = load_data(CSV_PATH)
        if df is not None and not df.empty:
            logger.info(f"   - Datos meteorológicos: {len(df)} registros")
        else:
            logger.warning("   - Datos meteorológicos vacíos o no encontrados")
            df = None
        
        # Cargar datos geoespaciales
        kml_geojson = load_kml(KML_PATH)
        if kml_geojson:
            logger.info("   - Datos geoespaciales cargados")
        else:
            logger.warning("   - Datos geoespaciales no encontrados")
            kml_geojson = {}
        
        return df, kml_geojson
        
    except Exception as e:
        logger.error(f"❌ Error cargando datos: {e}")
        return None, {}

def create_dashboard():
    """
    Crea y configura completamente el dashboard refactorizado
    
    Returns:
        dash.Dash: Aplicación lista para ejecutar
    """
    # Cargar datos
    df, kml_geojson = initialize_data()
    
    # Configurar paths
    ASSETS_PATH = ROOT_DIR / "assets"
    
    # Crear aplicación Dash
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        suppress_callback_exceptions=True,
        assets_folder=str(ASSETS_PATH)
    )
    
    app.title = "Dashboard Agricultura - Conde de Benalua"
    
    # Configurar servido estático para overlays satelitales
    dynamic_map_dir = os.path.abspath("dynamic_map")
    os.makedirs(dynamic_map_dir, exist_ok=True)
    
    @app.server.route("/dynamic_map/<path:filename>")
    def dynamic_map_static(filename):
        return send_from_directory(dynamic_map_dir, filename)
    
    logger.info(f"✅ Servido estático configurado para /dynamic_map/ -> {dynamic_map_dir}")
    
    # Layout principal usando create_main_layout
    app.layout = lambda: create_main_layout(df, kml_geojson)
    logger.info("✅ Layout principal configurado usando create_main_layout")

    # Registrar callbacks de forma explícita y forzando reload (evita imports rancios)
    import importlib, inspect

    modules = [
        "src.callbacks_refactored.main",            # router de tabs
        "src.callbacks_refactored.detecciones",
        "src.callbacks_refactored.historico",
        "src.callbacks_refactored.prediccion",
        "src.callbacks_refactored.datos_satelitales",
        "src.callbacks_refactored.fincas",
    ]

    for modname in modules:
        try:
            m = importlib.import_module(modname)
            m = importlib.reload(m)
            print(f"[CB] {modname} -> {inspect.getfile(m)}")
            if hasattr(m, "register_callbacks"):
                m.register_callbacks(app)
                print(f"[CB] Registrados callbacks de {modname}")
            else:
                print(f"[CB] {modname} no expone register_callbacks")
        except Exception as e:
            print(f"[CB][ERROR] {modname}: {e}")

    logger.info("   ✅ Callbacks registrados (explicítamente)")
    logger.info("   ✅ Todos los callbacks registrados correctamente")
    
    logger.info("============================================================")
    logger.info("🎉 Dashboard refactorizado listo!")
    logger.info("📱 Funcionalidades incluidas:")
    logger.info("   • Callbacks modulares por layout")
    logger.info("   • Detecciones de repilo en tiempo real")
    logger.info("   • Análisis satelital NDVI/anomalías")
    logger.info("   • Sistema de fincas con zoom automático")
    logger.info("   • Prevención de duplicados de outputs")
    logger.info("   • Validación de ImageOverlay bounds/url/opacity")
    logger.info("   • Sistema de warmup para APIs externas")
    logger.info("============================================================")
    logger.info("🌐 Accede al dashboard en: http://127.0.0.1:8050")
    logger.info("============================================================")
    
    # Iniciar sistema de warmup para APIs
    try:
        from src.utils.api_warmup import warmup_all_apis
        import threading
        
        # Ejecutar warmup en hilo separado después de 3 segundos
        def delayed_warmup():
            import time
            time.sleep(3)
            warmup_all_apis()
        
        warmup_thread = threading.Thread(target=delayed_warmup, daemon=True)
        warmup_thread.start()
        logger.info("🔥 Sistema de warmup iniciado")
    except Exception as warmup_error:
        logger.warning(f"⚠️ No se pudo iniciar sistema de warmup: {warmup_error}")
    
    return app

# Crear la aplicación
app = create_dashboard()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")   # <- 0.0.0.0 por defecto
    port = int(os.getenv("PORT", "8050"))
    debug = os.getenv("DEBUG", "1") == "1"
    logger.info("🌐 Iniciando servidor...")
    logger.info(f"📍 URL: http://{host}:{port}/")
    logger.info("🔄 Presiona Ctrl+C para detener")
    app.enable_dev_tools(dev_tools_hot_reload=True)
    app.run(
        debug=debug,
        host=host,
        port=port
    )


