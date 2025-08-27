"""
Sistema de caché para predicciones meteorológicas.

Mantiene datos de predicción durante 6 horas para reducir llamadas a la API de AEMET
y mejorar el rendimiento del sistema. Implementa persistencia en disco con metadatos
y limpieza automática de archivos expirados.

Características:
- Caché persistente en disco
- Validación automática de expiración
- Metadatos de control
- Limpieza automática

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

class WeatherCache:
    """
    Gestor de caché para predicciones meteorológicas.
    
    Almacena datos de predicción durante 6 horas para:
    - Reducir llamadas a la API de AEMET
    - Mejorar tiempos de respuesta
    - Evitar límites de rate limiting
    - Optimizar el uso de recursos
    """
    
    def __init__(self, cache_dir: str = "cache") -> None:
        """
        Inicializa el gestor de caché.
        
        Args:
            cache_dir: Directorio base para almacenar archivos de caché
        """
        # Configuración del sistema de caché
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=6)  # Duración de validez
        
        # Crear estructura de directorios
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Subdirectorio para predicciones meteorológicas
        self.weather_cache_dir = os.path.join(self.cache_dir, "weather")
        os.makedirs(self.weather_cache_dir, exist_ok=True)
        
        logger.info(
            f"💾 WeatherCache inicializado en: {self.weather_cache_dir}"
        )
        logger.debug(
            f"Duración de validez: {self.cache_duration.total_seconds()/3600:.1f}h"
        )
    
    def _get_cache_path(self, municipio: str, prediction_type: str) -> str:
        """
        Genera la ruta del archivo de caché.
        
        Args:
            municipio: Nombre del municipio
            prediction_type: Tipo de predicción ('diaria' o 'horaria')
            
        Returns:
            Ruta completa del archivo de caché
        """
        # Normalizar nombre para uso como archivo
        safe_municipio = (
            municipio.lower()
            .replace(" ", "_")
            .replace("ú", "u")
            .replace("á", "a")
        )
        filename = f"{safe_municipio}_{prediction_type}.pkl"
        return os.path.join(self.weather_cache_dir, filename)
    
    def _get_metadata_path(self, municipio: str, prediction_type: str) -> str:
        """
        Genera la ruta del archivo de metadatos.
        
        Args:
            municipio: Nombre del municipio
            prediction_type: Tipo de predicción ('diaria' o 'horaria')
            
        Returns:
            Ruta completa del archivo de metadatos
        """
        safe_municipio = (
            municipio.lower()
            .replace(" ", "_")
            .replace("ú", "u")
            .replace("á", "a")
        )
        filename = f"{safe_municipio}_{prediction_type}_meta.json"
        return os.path.join(self.weather_cache_dir, filename)
    
    def is_cache_valid(self, municipio: str, prediction_type: str) -> bool:
        """
        Verifica si el caché es válido (no ha expirado).
        
        Args:
            municipio: Nombre del municipio
            prediction_type: Tipo de predicción
            
        Returns:
            True si el caché es válido, False en caso contrario
        """
        try:
            meta_path = self._get_metadata_path(municipio, prediction_type)
            cache_path = self._get_cache_path(municipio, prediction_type)
            
            # Verificar existencia de archivos
            if not (os.path.exists(meta_path) and os.path.exists(cache_path)):
                logger.debug(
                    f"🚫 Caché no existe para {municipio} ({prediction_type})"
                )
                return False
            
            # Cargar metadatos
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Verificar expiración
            cached_time = datetime.fromisoformat(metadata['timestamp'])
            now = datetime.now()
            is_valid = (now - cached_time) < self.cache_duration
            
            if is_valid:
                time_left = self.cache_duration - (now - cached_time)
                logger.info(
                    f"✅ Caché válido para {municipio} ({prediction_type}) - "
                    f"Expira en {time_left}"
                )
            else:
                logger.info(
                    f"⏰ Caché expirado para {municipio} ({prediction_type})"
                )
            
            return is_valid
            
        except Exception as e:
            logger.warning(
                f"❌ Error verificando caché para {municipio} "
                f"({prediction_type}): {e}"
            )
            return False
    
    def get_cached_data(
        self, municipio: str, prediction_type: str
    ) -> Optional[Any]:
        """
        Recupera datos del caché si son válidos.
        
        Args:
            municipio: Nombre del municipio
            prediction_type: Tipo de predicción
            
        Returns:
            Datos de predicción si están en caché y son válidos
        """
        try:
            if not self.is_cache_valid(municipio, prediction_type):
                return None
            
            cache_path = self._get_cache_path(municipio, prediction_type)
            
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            logger.info(
                f"📂 Datos recuperados del caché para {municipio} "
                f"({prediction_type})"
            )
            return data
            
        except Exception as e:
            logger.error(
                f"❌ Error recuperando caché para {municipio} "
                f"({prediction_type}): {e}"
            )
            return None
    
    def save_to_cache(
        self, municipio: str, prediction_type: str, data: Any
    ) -> bool:
        """
        Guarda datos en el caché.
        
        Args:
            municipio: Nombre del municipio
            prediction_type: Tipo de predicción
            data: Datos de predicción a guardar
            
        Returns:
            True si se guardó correctamente
        """
        try:
            cache_path = self._get_cache_path(municipio, prediction_type)
            meta_path = self._get_metadata_path(municipio, prediction_type)
            
            # Guardar datos
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Guardar metadatos de control
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'municipio': municipio,
                'prediction_type': prediction_type,
                'data_size': (
                    len(data) if isinstance(data, (list, dict)) else 1
                )
            )
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(
                f"💾 Datos guardados en caché para {municipio} "
                f"({prediction_type})"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"❌ Error guardando en caché para {municipio} "
                f"({prediction_type}): {e}"
            )
            return False
    
    def clear_expired_cache(self) -> int:
        """
        Limpia archivos de caché expirados del sistema.
        
        Elimina automáticamente todos los archivos de caché que han superado
        el tiempo de validez configurado (6 horas por defecto).
        
        Returns:
            int: Número de archivos eliminados durante la limpieza
        """
        deleted_count = 0
        
        try:
            if not os.path.exists(self.weather_cache_dir):
                return 0
            
            now = datetime.now()
            
            for filename in os.listdir(self.weather_cache_dir):
                if filename.endswith('_meta.json'):
                    meta_path = os.path.join(self.weather_cache_dir, filename)
                    
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        cached_time = datetime.fromisoformat(metadata['timestamp'])
                        
                        # Si ha expirado, eliminar archivos
                        if (now - cached_time) >= self.cache_duration:
                            # Eliminar archivo de metadatos
                            os.remove(meta_path)
                            
                            # Eliminar archivo de datos correspondiente
                            cache_filename = filename.replace('_meta.json', '.pkl')
                            cache_path = os.path.join(self.weather_cache_dir, cache_filename)
                            
                            if os.path.exists(cache_path):
                                os.remove(cache_path)
                            
                            deleted_count += 1
                            logger.info(f"🗑️ Eliminado caché expirado: {metadata['municipio']} ({metadata['prediction_type']})")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando archivo de caché {filename}: {e}")
                        continue
            
            if deleted_count > 0:
                logger.info(f"🧹 Limpieza de caché completada: {deleted_count} archivos eliminados")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error durante limpieza de caché: {e}")
            return 0
    
    def get_cache_info(self) -> dict:
        """
        Obtiene información detallada sobre el estado actual del caché.
        
        Recopila estadísticas sobre las predicciones almacenadas, incluyendo
        información de validez, antigüedad y tamaño de datos.
        
        Returns:
            dict: Diccionario con información completa del caché:
                - cache_dir: Directorio del caché
                - cache_duration_hours: Duración de validez en horas
                - cached_predictions: Lista de predicciones con metadatos
        """
        info = {
            'cache_dir': self.weather_cache_dir,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
            'cached_predictions': []
        }
        
        try:
            if not os.path.exists(self.weather_cache_dir):
                return info
            
            for filename in os.listdir(self.weather_cache_dir):
                if filename.endswith('_meta.json'):
                    meta_path = os.path.join(self.weather_cache_dir, filename)
                    
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        cached_time = datetime.fromisoformat(metadata['timestamp'])
                        now = datetime.now()
                        age_hours = (now - cached_time).total_seconds() / 3600
                        is_valid = age_hours < self.cache_duration.total_seconds() / 3600
                        
                        info['cached_predictions'].append({
                            'municipio': metadata['municipio'],
                            'type': metadata['prediction_type'],
                            'cached_at': metadata['timestamp'],
                            'age_hours': round(age_hours, 2),
                            'is_valid': is_valid,
                            'data_size': metadata.get('data_size', 'unknown')
                        })
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo metadatos de {filename}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo información de caché: {e}")
        
        return info


# Instancia global del caché
weather_cache = WeatherCache()


def get_cached_or_fetch_prediction(
    municipio: str, 
    prediction_type: str, 
    fetch_function, 
    *args, 
    **kwargs
) -> Tuple[Any, bool]:
    """
    Función de conveniencia para obtener predicciones con caché automático.
    
    Implementa el patrón cache-aside: primero intenta obtener datos del caché,
    y si no están disponibles o han expirado, llama a la función de fetch
    y guarda el resultado en caché para futuras consultas.
    
    Args:
        municipio: Nombre del municipio para la predicción
        prediction_type: Tipo de predicción ('diaria' o 'horaria')
        fetch_function: Función callable que obtiene datos frescos
        *args: Argumentos posicionales para la función de fetch
        **kwargs: Argumentos de palabra clave para la función de fetch
        
    Returns:
        Tuple[Any, bool]: Tupla con (datos_prediccion, fue_desde_cache)
            - datos_prediccion: Los datos meteorológicos obtenidos
            - fue_desde_cache: True si los datos vinieron del caché, False si fueron obtenidos frescos
    """
    logger.info(f"🔍 Buscando predicción {prediction_type} para {municipio}")
    
    # Limpiar caché expirado antes de verificar
    weather_cache.clear_expired_cache()
    
    # Intentar obtener del caché
    cached_data = weather_cache.get_cached_data(municipio, prediction_type)
    
    if cached_data is not None:
        logger.info(f"✅ Usando datos en caché para {municipio} ({prediction_type})")
        return cached_data, True
    
    # Si no hay caché válido, hacer fetch
    logger.info(f"🌐 Obteniendo datos frescos para {municipio} ({prediction_type})")
    
    try:
        fresh_data = fetch_function(*args, **kwargs)
        
        # Guardar en caché si los datos son válidos
        if fresh_data:
            weather_cache.save_to_cache(municipio, prediction_type, fresh_data)
            logger.info(f"💾 Datos guardados en caché para {municipio} ({prediction_type})")
        
        return fresh_data, False
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos frescos para {municipio} ({prediction_type}): {e}")
        return None, False
