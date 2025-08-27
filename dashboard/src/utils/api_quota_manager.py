# src/utils/api_quota_manager.py
"""
Sistema inteligente de gestión de cuotas y caché para APIs satelitales.
Optimizado para reducir consumo de Copernicus API y mejorar performance.

Autor: Sistema de Optimización API
Fecha: 2025-08-26
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pickle
import time
import random

logger = logging.getLogger(__name__)

class IntelligentSatelliteCache:
    """
    Sistema de caché inteligente multinivel para datos satelitales.
    """
    
    def __init__(self, cache_dir: str = "./.sat_cache_intelligent"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Caché en memoria para la sesión actual
        self.memory_cache = {}
        
        # Archivo de metadatos del caché
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
        
    def _load_metadata(self):
        """Carga metadatos del caché desde disco."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    'entries': {},
                    'stats': {
                        'total_requests': 0,
                        'cache_hits': 0,
                        'cache_misses': 0,
                        'last_cleanup': None
                    }
                }
        except Exception as e:
            logger.warning(f"Error cargando metadatos del caché: {e}")
            self.metadata = {
                'entries': {},
                'stats': {'total_requests': 0, 'cache_hits': 0, 'cache_misses': 0, 'last_cleanup': None}
            }
    
    def _save_metadata(self):
        """Guarda metadatos del caché a disco."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando metadatos del caché: {e}")
    
    def _generate_cache_key(self, geometry: Any, date_range: Tuple[str, str], 
                           index_type: str, resolution: Tuple[int, int] = (384, 384)) -> str:
        """Genera clave única para el caché basada en los parámetros."""
        try:
            # Normalizar geometría para clave consistente
            if hasattr(geometry, '__geo_interface__'):
                geom_str = str(geometry.__geo_interface__)
            elif isinstance(geometry, (list, tuple)):
                geom_str = str([(round(float(x), 6), round(float(y), 6)) for x, y in geometry])
            else:
                geom_str = str(geometry)
            
            # Crear clave combinando todos los parámetros
            cache_input = f"{geom_str}_{date_range[0]}_{date_range[1]}_{index_type}_{resolution[0]}x{resolution[1]}"
            return hashlib.sha256(cache_input.encode('utf-8')).hexdigest()[:16]
            
        except Exception as e:
            logger.warning(f"Error generando clave de caché: {e}")
            return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    
    def get_cached_data(self, geometry: Any, date_range: Tuple[str, str], 
                       index_type: str, resolution: Tuple[int, int] = (384, 384)) -> Optional[Any]:
        """
        Busca datos en el caché (memoria + disco).
        
        Returns:
            Datos del caché si existen y son válidos, None en caso contrario
        """
        cache_key = self._generate_cache_key(geometry, date_range, index_type, resolution)
        
        # 1. Buscar en memoria primero
        if cache_key in self.memory_cache:
            logger.info("✅ Datos obtenidos desde caché en memoria")
            self.metadata['stats']['cache_hits'] += 1
            self._save_metadata()
            return self.memory_cache[cache_key]
        
        # 2. Buscar en disco
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                # Verificar si el caché sigue siendo válido
                if self._is_cache_valid(cache_key):
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    # Cargar en memoria para acceso rápido
                    self.memory_cache[cache_key] = data
                    
                    logger.info("✅ Datos obtenidos desde caché en disco")
                    self.metadata['stats']['cache_hits'] += 1
                    self._save_metadata()
                    return data
                else:
                    # Caché expirado, eliminarlo
                    cache_file.unlink()
                    if cache_key in self.metadata['entries']:
                        del self.metadata['entries'][cache_key]
                    logger.info("🗑️ Caché expirado eliminado")
                    
            except Exception as e:
                logger.warning(f"Error leyendo caché desde disco: {e}")
                # Eliminar archivo corrupto
                if cache_file.exists():
                    cache_file.unlink()
        
        # 3. No encontrado en caché
        self.metadata['stats']['cache_misses'] += 1
        self._save_metadata()
        return None
    
    def store_cached_data(self, geometry: Any, date_range: Tuple[str, str], 
                         index_type: str, data: Any, resolution: Tuple[int, int] = (384, 384)):
        """Almacena datos en el caché (memoria + disco)."""
        cache_key = self._generate_cache_key(geometry, date_range, index_type, resolution)
        
        try:
            # Almacenar en memoria
            self.memory_cache[cache_key] = data
            
            # Almacenar en disco
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Actualizar metadatos
            self.metadata['entries'][cache_key] = {
                'created_at': datetime.now().isoformat(),
                'date_range': date_range,
                'index_type': index_type,
                'resolution': resolution,
                'file_size': cache_file.stat().st_size
            }
            self._save_metadata()
            
            logger.info(f"💾 Datos almacenados en caché: {cache_key}")
            
            # Limpieza automática ocasional por tamaño (no por tiempo)
            if random.random() < 0.05:  # 5% de posibilidad cada vez que se almacena
                try:
                    # Limpieza de archivos corruptos
                    self.cleanup_corrupted_cache()
                    # Limpieza por tamaño si supera el límite configurado
                    max_cache_size = int(os.getenv("MAX_CACHE_SIZE_MB", 1000))  # 1GB por defecto
                    self.cleanup_by_size(max_cache_size)
                except Exception as cleanup_error:
                    logger.warning(f"Error en limpieza automática: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Error almacenando datos en caché: {e}")
    
    def _is_cache_valid(self, cache_key: str, check_integrity: bool = True) -> bool:
        """
        Verifica si una entrada de caché sigue siendo válida.
        Para datos satelitales NO expiramos por tiempo - las imágenes son inmutables.
        Solo verificamos integridad de archivos.
        """
        if cache_key not in self.metadata['entries']:
            return False
        
        if not check_integrity:
            return True
            
        try:
            # Solo verificar que el archivo existe y es legible
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            return cache_file.exists() and cache_file.stat().st_size > 0
        except:
            return False
    
    def cleanup_by_size(self, max_size_mb: int = 500):
        """
        Limpia caché por tamaño total, eliminando primero las entradas más antiguas.
        Para datos satelitales, solo limpiamos por espacio, NO por tiempo.
        """
        # Calcular tamaño actual
        total_size_bytes = 0
        cache_entries = []
        
        for cache_key, metadata in self.metadata['entries'].items():
            try:
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                if cache_file.exists():
                    size = cache_file.stat().st_size
                    total_size_bytes += size
                    cache_entries.append({
                        'key': cache_key,
                        'size': size,
                        'created_at': metadata.get('created_at', '1970-01-01T00:00:00'),
                        'file': cache_file
                    })
            except Exception as e:
                logger.warning(f"Error verificando tamaño de {cache_key}: {e}")
        
        current_size_mb = total_size_bytes / (1024 * 1024)
        logger.info(f"📊 Caché actual: {current_size_mb:.1f} MB")
        
        if current_size_mb <= max_size_mb:
            logger.info(f"✅ Caché dentro del límite ({max_size_mb} MB)")
            return
        
        # Ordenar por fecha (más antiguos primero) para eliminar
        cache_entries.sort(key=lambda x: x['created_at'])
        
        removed_count = 0
        freed_mb = 0
        
        for entry in cache_entries:
            if current_size_mb <= max_size_mb:
                break
                
            try:
                # Eliminar archivo
                entry['file'].unlink()
                size_mb = entry['size'] / (1024 * 1024)
                freed_mb += size_mb
                current_size_mb -= size_mb
                
                # Eliminar de metadatos y memoria
                del self.metadata['entries'][entry['key']]
                if entry['key'] in self.memory_cache:
                    del self.memory_cache[entry['key']]
                
                removed_count += 1
                logger.debug(f"🗑️ Eliminado caché: {entry['key']} ({size_mb:.1f} MB)")
                
            except Exception as e:
                logger.warning(f"Error eliminando caché {entry['key']}: {e}")
        
        self.metadata['stats']['last_cleanup'] = datetime.now().isoformat()
        self._save_metadata()
        
        if removed_count > 0:
            logger.info(f"🧹 Liberados {freed_mb:.1f} MB eliminando {removed_count} archivos antiguos")
    
    def cleanup_corrupted_cache(self):
        """Limpia archivos de caché corruptos o inaccesibles."""
        corrupted_keys = []
        
        for cache_key in list(self.metadata['entries'].keys()):
            if not self._is_cache_valid(cache_key, check_integrity=True):
                corrupted_keys.append(cache_key)
        
        for key in corrupted_keys:
            try:
                cache_file = self.cache_dir / f"{key}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                del self.metadata['entries'][key]
                if key in self.memory_cache:
                    del self.memory_cache[key]
            except Exception as e:
                logger.warning(f"Error eliminando caché corrupto {key}: {e}")
        
        if corrupted_keys:
            self.metadata['stats']['last_cleanup'] = datetime.now().isoformat()
            self._save_metadata()
            logger.info(f"🧹 Limpiados {len(corrupted_keys)} archivos de caché corruptos")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché."""
        total_requests = self.metadata['stats']['cache_hits'] + self.metadata['stats']['cache_misses']
        hit_rate = (self.metadata['stats']['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calcular tamaño total del caché
        total_size = 0
        for entry in self.metadata['entries'].values():
            total_size += entry.get('file_size', 0)
        
        return {
            'total_entries': len(self.metadata['entries']),
            'memory_entries': len(self.memory_cache),
            'cache_hits': self.metadata['stats']['cache_hits'],
            'cache_misses': self.metadata['stats']['cache_misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_size_mb': round(total_size / (1024*1024), 2),
            'last_cleanup': self.metadata['stats'].get('last_cleanup', 'Never')
        }


class ApiQuotaMonitor:
    """
    Monitor de consumo de API satelital (sin límites, solo informativo).
    """
    
    def __init__(self, tracking_file: str = "./.api_usage_tracking.json"):
        self.tracking_file = Path(tracking_file)
        # Límites configurables desde variables de entorno
        self.monthly_requests_limit = int(os.getenv("COPERNICUS_MONTHLY_REQUESTS_LIMIT", 30000))
        self.monthly_processing_units_limit = int(os.getenv("COPERNICUS_MONTHLY_PROCESSING_UNITS_LIMIT", 30000))
        self._load_usage_data()
    
    def _load_usage_data(self):
        """Carga datos de uso de la API."""
        try:
            if self.tracking_file.exists():
                with open(self.tracking_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = {
                    'daily_usage': {},
                    'total_requests': 0,
                    'session_requests': 0,
                    'last_reset': date.today().isoformat()
                }
        except Exception as e:
            logger.warning(f"Error cargando datos de uso API: {e}")
            self.usage_data = {
                'daily_usage': {},
                'total_requests': 0,
                'session_requests': 0,
                'last_reset': date.today().isoformat()
            }
    
    def _save_usage_data(self):
        """Guarda datos de uso a disco."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando datos de uso API: {e}")
    
    def log_api_request(self, endpoint: str = "copernicus", cost: float = 1.0):
        """
        Registra una llamada a la API.
        
        Args:
            endpoint: Nombre del endpoint usado
            cost: Costo relativo de la operación (1.0 = normal, 2.0 = alto, etc.)
        """
        today = date.today().isoformat()
        
        # Inicializar día si no existe
        if today not in self.usage_data['daily_usage']:
            self.usage_data['daily_usage'][today] = {
                'requests': 0,
                'total_cost': 0.0,
                'endpoints': {}
            }
        
        # Registrar request
        self.usage_data['daily_usage'][today]['requests'] += 1
        self.usage_data['daily_usage'][today]['total_cost'] += cost
        self.usage_data['total_requests'] += 1
        self.usage_data['session_requests'] += 1
        
        # Registrar por endpoint
        if endpoint not in self.usage_data['daily_usage'][today]['endpoints']:
            self.usage_data['daily_usage'][today]['endpoints'][endpoint] = 0
        self.usage_data['daily_usage'][today]['endpoints'][endpoint] += 1
        
        self._save_usage_data()
        
        # Log informativo
        daily_requests = self.usage_data['daily_usage'][today]['requests']
        logger.info(f"📊 API Request logged: {endpoint} (Daily: {daily_requests}, Session: {self.usage_data['session_requests']})")
        
        # Advertencias informativas (sin bloquear)
        if daily_requests >= 50:
            logger.warning(f"⚠️ Alto uso de API: {daily_requests} requests hoy. Considera optimizar.")
        elif daily_requests >= 30:
            logger.info(f"📈 Uso moderado de API: {daily_requests} requests hoy.")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de la API."""
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        today_data = self.usage_data['daily_usage'].get(today, {'requests': 0, 'total_cost': 0})
        yesterday_data = self.usage_data['daily_usage'].get(yesterday, {'requests': 0, 'total_cost': 0})
        
        # Calcular promedio semanal
        week_ago = date.today() - timedelta(days=7)
        weekly_requests = 0
        weekly_days = 0
        
        for day_str in self.usage_data['daily_usage']:
            day_date = datetime.fromisoformat(day_str).date()
            if day_date >= week_ago:
                weekly_requests += self.usage_data['daily_usage'][day_str]['requests']
                weekly_days += 1
        
        weekly_average = weekly_requests / weekly_days if weekly_days > 0 else 0
        
        # Calcular uso mensual actual
        current_month = date.today().replace(day=1).isoformat()
        monthly_requests = 0
        for day_str, day_data in self.usage_data['daily_usage'].items():
            try:
                day_date = datetime.fromisoformat(day_str).date()
                if day_date >= datetime.fromisoformat(current_month).date():
                    monthly_requests += day_data['requests']
            except:
                continue
        
        return {
            'requests_today': today_data['requests'],
            'requests_month': monthly_requests,
            'today_cost': today_data.get('total_cost', 0),
            'yesterday_requests': yesterday_data['requests'],
            'session_requests': self.usage_data['session_requests'],
            'total_requests': self.usage_data['total_requests'],
            'weekly_average': round(weekly_average, 1),
            'monthly_limit': self.monthly_requests_limit,
            'monthly_percentage': round((monthly_requests / self.monthly_requests_limit) * 100, 1) if self.monthly_requests_limit > 0 else 0,
            'status': self._get_usage_status(today_data['requests']),
            'cache_hits': getattr(self, 'cache_hits', 0),
            'recommendation': self._get_usage_recommendation(today_data['requests'])
        }
    
    def _get_usage_status(self, daily_requests: int) -> str:
        """Determina el estado del uso de API basado en límites reales."""
        daily_sustainable = self.monthly_requests_limit / 30  # ~1000 requests/día
        
        if daily_requests < daily_sustainable * 0.3:  # < 30% del límite diario
            return 'low'
        elif daily_requests < daily_sustainable * 0.7:  # < 70% del límite diario
            return 'moderate'
        elif daily_requests < daily_sustainable:  # < límite diario sostenible
            return 'high'
        else:
            return 'very_high'
    
    def _get_usage_recommendation(self, daily_requests: int) -> str:
        """Genera recomendación basada en el uso y límites reales."""
        daily_sustainable = self.monthly_requests_limit / 30
        
        if daily_requests < daily_sustainable * 0.3:
            return "Uso normal de API. Continúa con el desarrollo."
        elif daily_requests < daily_sustainable * 0.7:
            return "Uso moderado. El caché está funcionando bien."
        elif daily_requests < daily_sustainable:
            return "Uso alto pero sostenible. Monitorea el uso mensual."
        else:
            return f"Uso muy alto: {daily_requests}/{daily_sustainable:.0f} diarios. Considera optimizar consultas."
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Limpia datos de uso antiguos."""
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        old_keys = []
        
        for day_str in self.usage_data['daily_usage']:
            try:
                day_date = datetime.fromisoformat(day_str).date()
                if day_date < cutoff_date:
                    old_keys.append(day_str)
            except:
                old_keys.append(day_str)  # Eliminar entradas malformadas
        
        for key in old_keys:
            del self.usage_data['daily_usage'][key]
        
        if old_keys:
            logger.info(f"🧹 Eliminados {len(old_keys)} días de datos de uso antiguos")
            self._save_usage_data()


# Instancias globales
_cache_instance = None
_quota_monitor_instance = None

def get_intelligent_cache() -> IntelligentSatelliteCache:
    """Obtiene instancia singleton del caché inteligente."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentSatelliteCache()
    return _cache_instance

def get_quota_monitor() -> ApiQuotaMonitor:
    """Obtiene instancia singleton del monitor de cuotas."""
    global _quota_monitor_instance
    if _quota_monitor_instance is None:
        _quota_monitor_instance = ApiQuotaMonitor()
    return _quota_monitor_instance


def manual_cache_cleanup(max_size_mb: int = 500, clean_corrupted: bool = True):
    """
    Función utilitaria para limpieza manual del caché.
    
    Args:
        max_size_mb: Tamaño máximo del caché en MB
        clean_corrupted: Si limpiar archivos corruptos
        
    Returns:
        Dict con estadísticas de la limpieza realizada
    """
    try:
        cache_manager = get_intelligent_cache()
        
        # Obtener estadísticas antes
        stats_before = cache_manager.get_cache_stats()
        
        # Limpieza
        if clean_corrupted:
            cache_manager.cleanup_corrupted_cache()
            
        cache_manager.cleanup_by_size(max_size_mb)
        
        # Obtener estadísticas después
        stats_after = cache_manager.get_cache_stats()
        
        return {
            'success': True,
            'before': stats_before,
            'after': stats_after,
            'freed_mb': stats_before['total_size_mb'] - stats_after['total_size_mb'],
            'removed_entries': stats_before['total_entries'] - stats_after['total_entries']
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza manual del caché: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def create_quota_status_component():
    """
    Crea componente visual para mostrar estado de cuotas API.
    
    Returns:
        Componente Dash Bootstrap para mostrar en el dashboard
    """
    try:
        import dash_bootstrap_components as dbc
        from dash import html
        
        quota_monitor = get_quota_monitor()
        cache_instance = get_intelligent_cache()
        
        usage_stats = quota_monitor.get_usage_stats()
        cache_stats = cache_instance.get_cache_stats()
        
        # Determinar color según el estado
        status_colors = {
            'low': 'success',
            'moderate': 'info', 
            'high': 'warning',
            'very_high': 'danger'
        }
        
        color = status_colors.get(usage_stats['status'], 'secondary')
        
        return dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-satellite me-2"),
                    "Estado API Satelital"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                # Requests hoy
                html.Div([
                    html.Strong("Requests hoy: "),
                    html.Span(f"{usage_stats['today_requests']}", className=f"text-{color}"),
                    html.Small(f" (Sesión: {usage_stats['session_requests']})", className="text-muted ms-2")
                ], className="mb-2"),
                
                # Caché effectiveness
                html.Div([
                    html.Strong("Caché: "),
                    html.Span(f"{cache_stats['hit_rate_percent']}% hits ", className="text-success"),
                    html.Small(f"({cache_stats['total_entries']} entradas)", className="text-muted")
                ], className="mb-2"),
                
                # Recomendación
                dbc.Alert([
                    html.I(className="fas fa-lightbulb me-2"),
                    usage_stats['recommendation']
                ], color=color, className="mb-0 p-2 small")
            ])
        ], className="mb-3")
        
    except Exception as e:
        logger.error(f"Error creando componente de estado de cuotas: {e}")
        return None