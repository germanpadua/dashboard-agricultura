"""
===============================================================================
                    SISTEMA DE SINCRONIZACIÓN TELEGRAM BOT
===============================================================================

🤖 DESCRIPCIÓN:
    Sistema completo para sincronización de datos del bot de Telegram con
    Google Drive. Gestiona descarga, procesamiento y cacheo de detecciones
    de enfermedades enviadas por usuarios del bot de campo.

📋 FUNCIONALIDADES PRINCIPALES:
    - Sincronización automática con Google Drive
    - Procesamiento de datos de detecciones (CSV)
    - Descarga y cacheo inteligente de imágenes
    - Conversión a formatos de visualización (GeoJSON, MapBox)
    - Estadísticas y análisis de severidad
    - Integración completa con dashboard Dash

🔗 INTEGRACIONES:
    - Google Drive API (descarga de datos y imágenes)
    - Telegram Bot (origen de datos)
    - Dashboard Dash (consumidor de datos)
    - Sistema de assets estático

⚠️  REQUISITOS:
    - Credenciales de Google Drive en service_account.json
    - Carpeta configurada en Google Drive
    - Estructura de datos CSV con columnas específicas

👨‍💻 AUTOR: Sistema de Monitoreo Agrícola
📅 VERSION: 2024
🎯 PROPÓSITO: Integración Telegram Bot - Dashboard Agrícola

===============================================================================
"""

# ==============================================================================
# IMPORTS Y DEPENDENCIAS
# ==============================================================================

import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import io
import time
import ssl
from http.client import IncompleteRead
from pathlib import Path
import mimetypes

# Google Drive API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


# ==============================================================================
# CLASE PRINCIPAL DE SINCRONIZACIÓN
# ==============================================================================

class TelegramDataSync:
    """
    🤖 Sincronizador de Datos del Bot de Telegram
    
    Gestiona la descarga, procesamiento y cacheo de datos enviados por el bot
    de Telegram desde Google Drive. Proporciona una interfaz completa para
    integrar las detecciones de campo en el dashboard agrícola.
    
    Características principales:
    - Descarga automática de archivos CSV desde Google Drive
    - Procesamiento inteligente de coordenadas y timestamps
    - Cacheo local de datos para rendimiento optimizado
    - Descarga bajo demanda de imágenes de campo
    - Conversión a múltiples formatos de visualización
    - Estadísticas automáticas de severidad y distribución
    
    Flujo de datos:
    1. Bot Telegram → Google Drive (CSV + imágenes)
    2. TelegramDataSync → Descarga y procesa
    3. Dashboard → Consume datos formateados
    
    Example:
        >>> sync = TelegramDataSync()
        >>> detecciones = sync.load_detections()
        >>> stats = sync.get_detection_stats(days=30)
        >>> mapa_data = sync.get_map_data(days=7)
    """
    
    def __init__(self, credentials_path: str = None, folder_id: str = None):
        """
        🔧 Inicializa el sincronizador de datos de Telegram
        
        Configura las rutas de trabajo, credenciales de Google Drive y
        estructura de directorios necesaria para el funcionamiento del sistema.
        
        Args:
            credentials_path (str, optional): Ruta personalizada al archivo de 
                credenciales service_account.json. Si no se proporciona, usa
                la ruta por defecto del proyecto.
            folder_id (str, optional): ID específico de carpeta en Google Drive.
                Si no se proporciona, usa el ID configurado por defecto.
        
        Raises:
            Exception: Si no se pueden crear los directorios necesarios
            
        Note:
            - Crea automáticamente los directorios de cache y assets
            - Inicializa conexión con Google Drive si las credenciales existen
            - Configura rutas tanto para datos como para imágenes estáticas
        """
        # Configuración de rutas por defecto del proyecto
        bot_path = r"C:\Users\germa\OneDrive - UNIVERSIDAD DE GRANADA\Escritorio\GERMAN\TFM\Telegram Bot"
        
        # Rutas de configuración
        self.credentials_path = credentials_path or os.path.join(bot_path, "service_account.json")
        self.folder_id = folder_id or "1N7DHpYhhoqVgLD-rgsuUP9Q_5vyHC07W"  # Carpeta en Google Drive
        
        # Configuración de sistema de cache local
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Archivo local de detecciones cacheadas
        self.local_csv = os.path.join(self.cache_dir, "telegram_detections.csv")

        # Sistema de assets para servir imágenes estáticas en el dashboard
        try:
            from src.app.app_config import ASSETS_PATH
        except Exception:
            # Fallback a estructura de proyecto estándar
            ASSETS_PATH = Path(__file__).resolve().parents[2] / "assets"

        self.assets_detections_dir = Path(ASSETS_PATH) / "detections"
        self.assets_detections_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicialización del servicio de Google Drive
        self.drive_service = None
        self._init_drive_service()
    
# ==============================================================================
# MÉTODOS DE INICIALIZACIÓN Y CONFIGURACIÓN
# ==============================================================================

    def _init_drive_service(self):
        """
        🔑 Inicializa el cliente de Google Drive API
        
        Configura la autenticación y crea la instancia del servicio Drive
        usando las credenciales de cuenta de servicio. El servicio se utiliza
        para todas las operaciones de descarga de archivos.
        
        Note:
            - Requiere permisos de solo lectura (drive.readonly)
            - Si las credenciales no existen, el servicio queda como None
            - Los errores se registran pero no interrumpen la ejecución
        """
        try:
            if os.path.exists(self.credentials_path):
                # Configurar credenciales con scope de solo lectura
                credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                # Crear cliente del servicio
                self.drive_service = build('drive', 'v3', credentials=credentials)
                print("✅ Servicio de Google Drive inicializado correctamente")
            else:
                print(f"⚠️ Archivo de credenciales no encontrado: {self.credentials_path}")
        except Exception as e:
            print(f"❌ Error inicializando Google Drive: {e}")
            self.drive_service = None
    
# ==============================================================================
# MÉTODOS DE DESCARGA Y SINCRONIZACIÓN
# ==============================================================================

    def download_from_drive(self) -> bool:
        """
        📥 Descarga el archivo CSV de detecciones más reciente desde Google Drive
        
        Busca archivos que contengan 'infecciones.csv' en la carpeta configurada,
        selecciona el más reciente por fecha de modificación y lo descarga al
        cache local para su procesamiento.
        
        Returns:
            bool: True si la descarga fue exitosa, False en caso contrario
            
        Note:
            - Solo descarga archivos con 'infecciones.csv' en el nombre
            - Ordena por fecha de modificación (más reciente primero)
            - Sobrescribe el archivo local existente
            - Registra el progreso y errores en consola
        
        Example:
            >>> sync = TelegramDataSync()
            >>> if sync.download_from_drive():
            ...     print("Datos actualizados desde Google Drive")
        """
        # Verificar disponibilidad del servicio
        if not self.drive_service:
            print("❌ Servicio de Google Drive no disponible")
            return False
        
        try:
            # Construir consulta para archivos CSV de infecciones
            query = f"'{self.folder_id}' in parents and name contains 'infecciones.csv' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                orderBy='modifiedTime desc',  # Más reciente primero
                fields="files(id, name, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                print("⚠️ No se encontraron archivos CSV de infecciones en Google Drive")
                return False
            
            # Seleccionar el archivo más reciente
            latest_file = files[0]
            file_id = latest_file['id']
            file_name = latest_file['name']
            
            print(f"📥 Descargando archivo: {file_name}")
            
            # Descargar contenido del archivo
            file_content = self.drive_service.files().get_media(fileId=file_id).execute()
            
            # Guardar en cache local
            with open(self.local_csv, 'wb') as f:
                f.write(file_content)
            
            print(f"✅ Archivo descargado y guardado en: {self.local_csv}")
            return True
            
        except HttpError as e:
            print(f"❌ Error de API de Google Drive: {e}")
            return False
        except Exception as e:
            print(f"❌ Error general descargando archivo: {e}")
            return False
    
    def load_detections(self, auto_download: bool = True) -> pd.DataFrame:
        """
        📈 Carga y procesa las detecciones de Telegram
        
        Gestiona la carga completa de datos de detecciones incluyendo descarga
        automática, validación de estructura, normalización de coordenadas,
        procesamiento de timestamps y enriquecimiento con descripciones.
        
        Args:
            auto_download (bool): Si es True, intenta descargar datos frescos
                desde Google Drive antes de cargar. Default True.
            
        Returns:
            pd.DataFrame: DataFrame procesado con columnas normalizadas:
                - latitude, longitude: Coordenadas numéricas validadas
                - timestamp: Fechas en formato datetime sin zona horaria
                - severity: Nivel de severidad (1-5)
                - severity_description: Descripción textual del nivel
                - photo_name: Nombre del archivo de imagen
                - photo_web_path: Ruta web para servir la imagen
                - location_name: Nombre de la ubicación (si disponible)
        
        Note:
            - Elimina filas con coordenadas inválidas
            - Normaliza coordenadas con comas decimales y caracteres unicode
            - Añade descripciones de severidad automáticamente
            - Cachea imágenes en el directorio de assets
            
        Example:
            >>> sync = TelegramDataSync()
            >>> df = sync.load_detections()
            >>> print(f"Cargadas {len(df)} detecciones")
        """
        # Paso 1: Descarga automática si está habilitada
        if auto_download:
            self.download_from_drive()
        
        try:
            # Verificar si existe archivo local
            if not os.path.exists(self.local_csv):
                print("WARNING  No hay datos locales, intentando descarga...")
                if not self.download_from_drive():
                    return pd.DataFrame()
            
            # Leer CSV
            df = pd.read_csv(self.local_csv)
            
            # Verificar columnas esperadas
            expected_cols = ['image_name', 'lat', 'lon', 'timestamp', 'severity_level']
            missing_cols = [col for col in expected_cols if col not in df.columns]
            
            if missing_cols:
                print(f"WARNING  Columnas faltantes en CSV: {missing_cols}")
                return pd.DataFrame()
            
            # Convertir timestamp a datetime y manejar zonas horarias
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Si tiene zona horaria, convertir a naive
                if df['timestamp'].dt.tz is not None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            except Exception as e:
                print(f"WARNING  Error procesando timestamps: {e}")
                # Intentar con formato específico
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                except:
                    print("ERROR No se pudieron procesar los timestamps")
                    return pd.DataFrame()
            
            # Renombrar columnas para consistencia
            column_mapping = {
                'lat': 'latitude',
                'lon': 'longitude', 
                'severity_level': 'severity',
                'image_name': 'photo_name',
                'kml_name': 'location_name'
            }
            
            df = df.rename(columns=column_mapping)

            # Asegurar numérico en lat/lon (coma decimal, espacios, ‘−’ unicode)
            for c in ("latitude", "longitude"):
                if c in df.columns:
                    s = df[c].astype(str).str.strip().str.replace("−", "-", regex=False).str.replace(",", ".", regex=False)
                    df[c] = pd.to_numeric(s, errors="coerce")

            # Elimina filas sin coordenadas válidas (el mapa las ignoraría)
            before = len(df)
            df = df.dropna(subset=["latitude", "longitude"])
            after = len(df)
            if after < before:
                print(f"INFO  Filas descartadas por coordenadas inválidas: {before-after}")
            
            # Paso 9: Enriquecimiento con descripciones de severidad
            severity_descriptions = {
                1: "Muy baja - Síntomas iniciales",
                2: "Baja - Pocas manchas visibles", 
                3: "Moderada - Manchas evidentes",
                4: "Alta - Defoliación notable",
                5: "Muy alta - Defoliación severa"
            }
            
            df['severity_description'] = df['severity'].map(severity_descriptions)
            
            print(f"✅ Cargadas {len(df)} detecciones válidas")

            # Paso 10: Cacheo inteligente de imágenes
            try:
                df = self._ensure_images_cached(df, max_downloads=40)
            except Exception as e:
                print(f"⚠️ Error en cacheo de imágenes: {e}")

            # Mostrar muestra de datos cargados
            print(f"📋 Vista previa de los datos:\n{df.head()}")
            return df
            
        except Exception as e:
            print(f"❌ Error crítico cargando detecciones: {e}")
            return pd.DataFrame()
    
# ==============================================================================
# MÉTODOS DE CONSULTA Y FILTRADO DE DATOS
# ==============================================================================

    def get_recent_detections(self, days: int = 7) -> pd.DataFrame:
        """
        📅 Obtiene detecciones recientes filtradas por tiempo
        
        Carga todas las detecciones y filtra las que estén dentro del rango
        de tiempo especificado. Normaliza los timestamps para comparación
        consistente sin zonas horarias.
        
        Args:
            days (int): Número de días hacia atrás para incluir detecciones.
                Default es 7 días.
            
        Returns:
            pd.DataFrame: DataFrame con detecciones recientes ordenadas por
                timestamp descendente (más recientes primero).
                
        Note:
            - Usa load_detections() internamente, beneficiándose del cache
            - Maneja automáticamente la normalización de timestamps
            - Retorna DataFrame vacío si no hay datos o hay errores
            
        Example:
            >>> sync = TelegramDataSync()
            >>> recientes = sync.get_recent_detections(days=3)
            >>> print(f"Detecciones últimas 72h: {len(recientes)}")
        """
        try:
            # Cargar todas las detecciones
            df = self.load_detections()
            
            if df.empty:
                return df
            
            # Verificar y normalizar formato de timestamp
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Normalizar a timestamps sin zona horaria para comparación
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            
            # Aplicar filtro temporal
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_df = df[df['timestamp'] >= cutoff_time]
            
            # Ordenar por timestamp descendente (más recientes primero)
            return recent_df.sort_values('timestamp', ascending=False)
            
        except Exception as e:
            print(f"❌ Error obteniendo detecciones recientes: {e}")
            return pd.DataFrame()
    
    def get_detection_stats(self, days: int = 30) -> Dict:
        """
        📊 Genera estadísticas completas de las detecciones
        
        Calcula métricas importantes sobre las detecciones incluyendo
        totales, distribución de severidad, promedios y última detección.
        
        Args:
            days (int): Período de tiempo en días para calcular detecciones
                recientes. Default 30 días.
            
        Returns:
            Dict: Diccionario con estadísticas completas:
                - total_detections: Número total de detecciones
                - recent_detections: Detecciones en el período especificado
                - severity_distribution: Conteo por nivel de severidad
                - avg_severity: Severidad promedio
                - last_detection: Timestamp de la última detección
                - time_period_days: Período utilizado para recientes
                
        Note:
            - Retorna estructura válida incluso con datos vacíos
            - La distribución de severidad se basa en todos los datos históricos
            - Las detecciones recientes usan el filtro temporal especificado
            
        Example:
            >>> stats = sync.get_detection_stats(days=7)
            >>> print(f"Severidad promedio: {stats['avg_severity']:.1f}")
        """
        # Cargar todas las detecciones disponibles
        df = self.load_detections()
        
        # Manejar caso sin datos
        if df.empty:
            return {
                'total_detections': 0,
                'recent_detections': 0,
                'severity_distribution': {},
                'avg_severity': 0,
                'last_detection': None,
                'time_period_days': days
            }
        
        # Calcular detecciones recientes usando filtro temporal
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_df = df[df['timestamp'] >= cutoff_time]
        
        # Distribución de severidad basada en todos los datos históricos
        severity_dist = df['severity'].value_counts().to_dict()
        
        # Timestamp de la última detección registrada
        last_detection = df['timestamp'].max() if len(df) > 0 else None
        
        return {
            'total_detections': len(df),
            'recent_detections': len(recent_df),
            'severity_distribution': severity_dist,
            'avg_severity': float(df['severity'].mean()) if len(df) > 0 else 0,
            'last_detection': last_detection,
            'time_period_days': days
        }
    
# ==============================================================================
# MÉTODOS DE FORMATO Y VISUALIZACIÓN
# ==============================================================================

    def get_map_data(self, days: int = 7, include_colors: bool = True) -> Dict:
        """
        🗺️ Formatea datos para visualización en mapas interactivos
        
        Convierte las detecciones en un formato optimizado para mapas con
        características geográficas, colores por severidad y metadatos completos.
        
        Args:
            days (int): Número de días hacia atrás para incluir detecciones.
                Default 7 días.
            include_colors (bool): Si incluir esquema de colores basado en
                severidad. Default True.
            
        Returns:
            Dict: Diccionario estructurado para mapas:
                - features: Lista de features geográficas con coordenadas y metadata
                - center: Coordenadas del centro del mapa
                - bounds: Límites geográficos (norte, sur, este, oeste)
                - severity_legend: Leyenda con colores y niveles de severidad
                
        Note:
            - Usa esquema de colores semáforo (verde a rojo) para severidad
            - Calcula automáticamente el centro y bounds del mapa
            - Incluye fallback a coordenadas de Benaluá si no hay datos
            - Cada feature incluye popup con información detallada
            
        Example:
            >>> map_data = sync.get_map_data(days=14, include_colors=True)
            >>> center = map_data['center']
            >>> features = map_data['features']
        """
        # Obtener detecciones recientes para el período especificado
        df = self.get_recent_detections(days=days)
        
        # Manejar caso sin datos con valores por defecto
        if df.empty:
            return {
                'features': [],
                'center': [36.8396, -2.3091],  # Centro aproximado Benaluá
                'bounds': None,
                'severity_legend': self._get_severity_legend()
            }
        
        # Esquema de colores semáforo por nivel de severidad
        severity_colors = {
            1: '#90EE90',  # Verde claro - Muy baja
            2: '#FFD700',  # Amarillo - Baja  
            3: '#FFA500',  # Naranja - Moderada
            4: '#FF6347',  # Rojo tomate - Alta
            5: '#8B0000'   # Rojo oscuro - Muy alta
        }
        
        features = []
        
        for _, row in df.iterrows():
            feature = {
                'id': f"detection_{row.name}",
                'type': 'circle',
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'radius': 50,  # Radio en metros
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'severity': int(row['severity']),
                'severity_description': row['severity_description'],
                'photo_name': row.get('photo_name', 'Sin foto'),
                'location_name': row.get('location_name', 'Sin nombre')
            }
            
            if include_colors:
                feature['color'] = severity_colors.get(int(row['severity']), '#808080')
                feature['fillColor'] = severity_colors.get(int(row['severity']), '#808080')
                feature['opacity'] = 0.8
                feature['fillOpacity'] = 0.6
            
            features.append(feature)
        
        # Calcular bounds
        if len(features) > 0:
            lats = [f['latitude'] for f in features]
            lons = [f['longitude'] for f in features]
            bounds = {
                'north': max(lats),
                'south': min(lats),
                'east': max(lons),
                'west': min(lons)
            }
        else:
            bounds = None
        
        # Centro del mapa
        if bounds:
            center = [
                (bounds['north'] + bounds['south']) / 2,
                (bounds['east'] + bounds['west']) / 2
            ]
        else:
            center = [36.8396, -2.3091]  # Centro por defecto
        
        return {
            'features': features,
            'center': center,
            'bounds': bounds,
            'severity_legend': {
                'title': 'Grado de Infección',
                'items': [
                    {'severity': 1, 'color': severity_colors[1], 'label': 'Muy baja'},
                    {'severity': 2, 'color': severity_colors[2], 'label': 'Baja'},
                    {'severity': 3, 'color': severity_colors[3], 'label': 'Moderada'},
                    {'severity': 4, 'color': severity_colors[4], 'label': 'Alta'},
                    {'severity': 5, 'color': severity_colors[5], 'label': 'Muy alta'},
                ]
            }
        }
    
    def export_dashboard_format(self, days: int = 7) -> str:
        """
        Exporta datos en formato JSON para el dashboard
        
        Args:
            days: Días de antigüedad máxima
            
        Returns:
            JSON string con los datos
        """
        map_data = self.get_map_data(days=days)
        stats = self.get_detection_stats(days=days)
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'telegram_bot',
            'time_period_days': days,
            'statistics': stats,
            'map_data': map_data,
            'metadata': {
                'total_features': len(map_data['features']),
                'has_recent_data': len(map_data['features']) > 0,
                'data_freshness': 'auto_sync' if self.drive_service else 'manual_sync'
            }
        }
        
        return json.dumps(export_data, default=str, indent=2)
    
    def get_severity_summary(self, days: int = 7) -> Dict:
        """
        Obtiene un resumen de severidad para mostrar en el dashboard
        
        Args:
            days: Días para el resumen
            
        Returns:
            Diccionario con resumen de severidad
        """
        df = self.get_recent_detections(days=days)
        
        if df.empty:
            return {
                'total': 0,
                'severity_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'max_severity': 0,
                'avg_severity': 0,
                'alert_level': 'none'
            }
        
        severity_counts = df['severity'].value_counts().reindex(range(1, 6), fill_value=0).to_dict()
        max_severity = int(df['severity'].max())
        avg_severity = float(df['severity'].mean())
        
        # Determinar nivel de alerta
        if max_severity >= 5 or avg_severity >= 4:
            alert_level = 'critical'
        elif max_severity >= 4 or avg_severity >= 3:
            alert_level = 'high'
        elif max_severity >= 3 or avg_severity >= 2:
            alert_level = 'medium'
        else:
            alert_level = 'low'
        
        return {
            'total': len(df),
            'severity_counts': severity_counts,
            'max_severity': max_severity,
            'avg_severity': round(avg_severity, 2),
            'alert_level': alert_level,
            'period_days': days
        }
    
    def get_geojson_data(self) -> Dict:
        """
        Convierte las detecciones a formato GeoJSON para mapas
        
        Returns:
            Diccionario en formato GeoJSON
        """
        df = self.load_detections()
        
        if df.empty:
            return {
                "type": "FeatureCollection",
                "features": []
            }
        
        features = []
        
        for _, row in df.iterrows():
            # Color según severidad
            color_map = {
                1: "#28a745",  # Verde - Muy baja
                2: "#ffc107",  # Amarillo - Baja  
                3: "#fd7e14",  # Naranja - Moderada
                4: "#dc3545",  # Rojo - Alta
                5: "#6f1e51"   # Morado - Muy alta
            }
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                },
                "properties": {
                    "name": row.get('location_name', 'Detección'),
                    "severity": row['severity'],
                    "severity_description": row.get('severity_description', ''),
                    "timestamp": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    "photo_name": row.get('photo_name', ''),
                    "color": color_map.get(row['severity'], "#666666"),
                    "popup": f"""
                    <b>Detección de Repilo</b><br>
                    <b>Severidad:</b> {row['severity']}/5 - {row.get('severity_description', '')}<br>
                    <b>Fecha:</b> {row['timestamp'].strftime('%d/%m/%Y %H:%M')}<br>
                    <b>Coordenadas:</b> {row['latitude']:.6f}, {row['longitude']:.6f}
                    """
                }
            }
            
            features.append(feature)
        
        return {
            "type": "FeatureCollection", 
            "features": features
        }
    
    def export_to_dashboard_format(self, output_path: str = None) -> str:
        """
        Exporta los datos en formato compatible con el dashboard
        
        Args:
            output_path: Ruta donde guardar el archivo
            
        Returns:
            Ruta del archivo exportado
        """
        if output_path is None:
            output_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "data", "telegram_detections.json"
            )
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generar datos completos
        export_data = {
            "detections": self.load_detections().to_dict('records'),
            "stats": self.get_detection_stats(),
            "geojson": self.get_geojson_data(),
            "last_sync": datetime.now().isoformat()
        }
        
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        return output_path

# ==============================================================================
# MÉTODOS AUXILIARES INTERNOS
# ==============================================================================

    def _find_drive_file_by_name(self, name: str):
        """
        🔍 Busca un archivo específico en Google Drive por nombre
        
        Realiza búsqueda exacta primero, si no encuentra nada intenta
        búsqueda parcial usando el stem del nombre del archivo.
        
        Args:
            name (str): Nombre del archivo a buscar
            
        Returns:
            dict: Metadatos del archivo encontrado o None si no existe
        
        Note:
            - Busca primero con nombre exacto
            - Si no encuentra y no tiene extensión, busca por 'contains'
            - Retorna el archivo más reciente si hay múltiples coincidencias
        """
        try:
            q = f"'{self.folder_id}' in parents and name = '{name}' and trashed=false"
            res = self.drive_service.files().list(
                q=q, fields="files(id,name,mimeType,size,modifiedTime)", pageSize=1
            ).execute()
            files = res.get("files", [])
            if files:
                return files[0]

            stem = Path(name).stem
            if stem and "." not in name:
                q2 = f"'{self.folder_id}' in parents and name contains '{stem}' and trashed=false"
                res = self.drive_service.files().list(
                    q=q2, fields="files(id,name,mimeType,size,modifiedTime)",
                    pageSize=10, orderBy="modifiedTime desc"
                ).execute()
                files = res.get("files", [])
                if files:
                    return files[0]
        except Exception as e:
            print(f"WARNING  _find_drive_file_by_name error: {e}")
        return None

    
    def _download_drive_file(self, file_id: str, out_path: Path, chunk_size: int = 256 * 1024,
                         max_retries: int = 6) -> None:
        """
        Descarga un fichero de Drive en chunks con reintentos exponenciales.
        Lanza excepción si no se consigue tras los reintentos.
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        # 'wb' crea de cero; si quieres reanudar, usa 'r+b' y conserva tamaño. Para simplicidad: restart.
        with open(out_path, "wb") as fh:
            downloader = MediaIoBaseDownload(io.BufferedWriter(fh), request, chunksize=chunk_size)
            done = False
            retries = 0
            while not done:
                try:
                    status, done = downloader.next_chunk()
                    # opcional: print(f"descarga {int(status.progress()*100)}%") si status
                except (ssl.SSLError, IncompleteRead, HttpError, OSError, ConnectionError) as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    sleep = min(2 ** retries, 10)
                    time.sleep(sleep)
                    # Reintenta el mismo next_chunk(); MediaIoBaseDownload maneja el rango internamente
                    continue


    def _ensure_images_cached(self, df: pd.DataFrame, max_downloads: int = 40) -> pd.DataFrame:
        """
        Para cada fila con 'photo_name':
        - Si ya existe en /assets/detections, usa esa ruta.
        - Si no existe, lo busca en Drive por nombre y lo descarga de forma robusta.
        Añade la columna 'photo_web_path' con '/assets/detections/<archivo>' si está disponible.
        """
        if df is None or df.empty:
            if df is not None:
                df["photo_web_path"] = None
            return df

        if "photo_name" not in df.columns:
            df["photo_web_path"] = None
            return df

        names = (
            df["photo_name"].dropna().astype(str).str.strip().unique().tolist()
        )
        web_paths = {}
        downloads = 0

        for name in names:
            # 1) ¿Ya está cacheado?
            local_path = self.assets_detections_dir / name
            if local_path.exists():
                web_paths[name] = f"/assets/detections/{local_path.name}"
                continue

            if not self.drive_service or downloads >= max_downloads:
                continue

            meta = self._find_drive_file_by_name(name)
            if not meta:
                continue

            try:
                # Asegurar extensión apropiada si hiciera falta
                fname = meta.get("name") or name
                if "." not in fname:
                    ext = mimetypes.guess_extension(meta.get("mimeType") or "") or ".jpg"
                    fname = f"{Path(fname).stem}{ext}"

                save_path = self.assets_detections_dir / fname
                # Evitar colisión trivial
                i = 1
                while save_path.exists() and save_path.name != name:
                    save_path = self.assets_detections_dir / f"{Path(fname).stem}_{i}{Path(fname).suffix}"
                    i += 1

                self._download_drive_file(meta["id"], save_path)
                downloads += 1
                web_paths[name] = f"/assets/detections/{save_path.name}"
            except Exception as e:
                print(f"WARNING  No se pudo descargar imagen '{name}': {e}")
                continue

        df = df.copy()
        df["photo_web_path"] = df["photo_name"].map(web_paths)
        return df


# ==============================================================================
# INSTANCIACIÓN GLOBAL Y TESTING
# ==============================================================================

# Instancia global del sincronizador para uso en el dashboard
# Se inicializa con configuración por defecto y puede ser usada
# directamente por los callbacks del dashboard
telegram_sync = TelegramDataSync()


def _get_severity_legend():
    """
    🎨 Genera leyenda estándar de colores por severidad
    
    Returns:
        Dict: Estructura de leyenda con colores y etiquetas
    """
    return {
        'title': 'Grado de Infección',
        'items': [
            {'severity': 1, 'color': '#90EE90', 'label': 'Muy baja'},
            {'severity': 2, 'color': '#FFD700', 'label': 'Baja'},
            {'severity': 3, 'color': '#FFA500', 'label': 'Moderada'},
            {'severity': 4, 'color': '#FF6347', 'label': 'Alta'},
            {'severity': 5, 'color': '#8B0000', 'label': 'Muy alta'},
        ]
    }


if __name__ == "__main__":
    """
    🧪 Modo de testing y demostración del módulo
    
    Ejecuta un conjunto de pruebas básicas para verificar el correcto
    funcionamiento del sistema de sincronización con Telegram.
    """
    print("⚙️  === TEST DEL SISTEMA DE SINCRONIZACIÓN TELEGRAM ===")
    print()
    
    # Crear instancia de prueba
    sync = TelegramDataSync()
    
    try:
        # Test 1: Cargar detecciones
        detections = sync.load_detections()
        print(f"✅ Detecciones totales cargadas: {len(detections)}")
        
        # Test 2: Detecciones recientes
        recent = sync.get_recent_detections(days=1)
        print(f"🗺️ Detecciones últimas 24h: {len(recent)}")
        
        # Test 3: Estadísticas
        stats = sync.get_detection_stats(days=7)
        print(f"📊 Severidad promedio (7d): {stats.get('avg_severity', 0):.1f}")
        
        # Test 4: Datos para mapa
        map_data = sync.get_map_data(days=7)
        print(f"🗺️ Features para mapa: {len(map_data.get('features', []))}")
        
        # Test 5: Exportación
        export_path = sync.export_to_dashboard_format()
        print(f"📦 Archivo exportado: {export_path}")
        
        print()
        print("✅ Todos los tests completados exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante testing: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        
    print("⚙️  === FIN DE TESTS ===")
