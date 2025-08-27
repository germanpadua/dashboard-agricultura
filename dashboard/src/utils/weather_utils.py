"""
===============================================================================
                    UTILIDADES PARA API METEOROLÓGICA AEMET
===============================================================================

🌡️ DESCRIPCIÓN:
    Biblioteca de utilidades para interacción robusta con la API de AEMET
    (Agencia Estatal de Meteorología). Proporciona funciones optimizadas
    para obtener predicciones meteorológicas con manejo avanzado de errores.

🔄 CARACTERÍSTICAS:
    - Sistema de reintentos exponenciales para mayor robustez
    - Manejo inteligente de timeouts y errores de conexión
    - Normalización de nombres de municipios (acentos, espacios)
    - Headers optimizados para mejor compatibilidad
    - Logging detallado para monitorización y debugging
    - Soporte para predicciones diarias y horarias

📊 DATOS DISPONIBLES:
    - Predicciones diarias: Temperaturas, precipitación, viento
    - Predicciones horarias: Datos detallados por hora
    - Cobertura: Todos los municipios de España
    - Formato: JSON estructurado

🔑 AUTENTICACIÓN:
    - API Key de AEMET requerida
    - Configuración por variable de entorno AEMET_API_KEY
    - Fallback a archivo .aemet_api_key

👨‍💻 AUTOR: Sistema de Monitoreo Agrícola
📅 VERSION: 2024
🎯 PROPÓSITO: Integración AEMET - Dashboard Agrícola

===============================================================================
"""

# ==============================================================================
# IMPORTS Y CONFIGURACIÓN
# ==============================================================================

# Librerías estándar
import logging
import os
import time
import unicodedata
from typing import Dict, List, Optional, Union

# Librerías de terceros
import pandas as pd
import requests

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de autenticación con AEMET
AEMET_API_KEY = os.getenv("AEMET_API_KEY")

# ==============================================================================
# FUNCIONES DE CONEXIÓN ROBUSTA
# ==============================================================================

def _make_request_with_retry(
    url: str, 
    headers: Optional[Dict[str, str]] = None, 
    max_retries: int = 5, 
    delay: int = 1
) -> requests.Response:
    """
    🔄 Realiza peticiones HTTP robustas con sistema de reintentos exponenciales
    
    Implementa una estrategia de reintentos sofisticada diseñada específicamente
    para la API de AEMET, manejando timeouts, errores de conexión y respuestas
    erróneas de forma inteligente.
    
    Args:
        url (str): URL de la API de AEMET a consultar
        headers (dict, optional): Headers HTTP adicionales
        max_retries (int): Número máximo de reintentos. Default 5.
        delay (int): Delay base en segundos para reintentos. Default 1.
    
    Returns:
        requests.Response: Respuesta HTTP exitosa
    
    Raises:
        requests.exceptions.RequestException: Si todos los reintentos fallan
    
    Note:
        - Backoff exponencial: 1s, 2s, 4s, 8s, 16s
        - Timeouts progresivos: aumentan con cada intento
        - Headers optimizados para AEMET
        - Cierre automático de sesiones
        - Logging detallado del progreso
    
    Example:
        >>> response = _make_request_with_retry(
        ...     "https://opendata.aemet.es/opendata/api/prediccion/...",
        ...     headers={"api_key": API_KEY}
        ... )
    """
    # Bucle de reintentos con backoff exponencial
    for attempt in range(max_retries):
        session = None
        try:
            logger.debug(f"🔄 Intento {attempt + 1}/{max_retries} para URL: {url}")
            
            # Configurar sesión HTTP optimizada para AEMET
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate'
            })
            if headers:
                session.headers.update(headers)
            
            # Timeouts progresivos: más tiempo en intentos posteriores
            connect_timeout = 5 + attempt * 2
            read_timeout = 15 + attempt * 5
            timeout = (connect_timeout, read_timeout)
            
            # Ejecutar petición con timeouts progresivos
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            
            logger.debug(f"✅ Petición exitosa en intento {attempt + 1}")
            return response
            
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException) as e:
            logger.warning(f"⚠️ Error en intento {attempt + 1}: {type(e).__name__}: {e}")
            
            if attempt < max_retries - 1:
                # Backoff exponencial: 1s, 2s, 4s, 8s, 16s
                wait_time = delay * (2 ** attempt)
                logger.info(f"⏱️ Esperando {wait_time}s antes del siguiente intento...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Todos los intentos fallaron para {url}")
                raise
        finally:
            # Garantizar cierre de sesión para evitar memory leaks
            if session:
                try:
                    session.close()
                except:
                    pass
                
    return None

def _log_json_shape(tag: str, payload: Union[Dict, List]) -> None:
    """
    Registra información sobre la estructura de datos JSON recibidos.
    
    Utilidad de debugging para registrar el formato y tamaño de las respuestas
    de la API de AEMET sin exponer datos sensibles.
    
    Args:
        tag: Etiqueta identificativa para el log
        payload: Datos JSON a analizar (dict o list)
    """
    try:
        if isinstance(payload, list):
            first_keys = list(payload[0].keys()) if payload else []
            logger.info("%s: list(len=%s) keys0=%s", tag, len(payload), first_keys)
        elif isinstance(payload, dict):
            logger.info("%s: dict keys=%s", tag, list(payload.keys()))
        else:
            logger.info("%s: %s", tag, type(payload).__name__)
    except Exception as e:
        logger.info("%s: (introspección fallida) %s", tag, e)

# Si no hay variable de entorno, intentar leer de un archivo oculto
if not AEMET_API_KEY:
    try:
        with open(".aemet_api_key", "r") as f:
            AEMET_API_KEY = f.read().strip()
    except FileNotFoundError:
        AEMET_API_KEY = None

def normalizar(texto: str) -> str:
    """
    Normaliza texto removiendo acentos y convirtiéndolo a minúsculas.
    
    Utilizada para comparaciones de nombres de municipios que deben ser
    insensibles a acentos y mayúsculas/minúsculas.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        str: Texto normalizado sin acentos y en minúsculas
    
    Example:
        >>> normalizar("Málaga")
        'malaga'
    """
    if not isinstance(texto, str):
        return ""
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower()

# ==============================================================================
# FUNCIONES DE GESTIÓN DE MUNICIPIOS
# ==============================================================================

def get_municipio_code(
    nombre_municipio: str, 
    diccionario_path: str = "notebooks/data/diccionario24.xlsx"
) -> str:
    """
    Obtiene el código INE de un municipio a partir de su nombre.
    
    Busca en el diccionario oficial de municipios españoles para encontrar
    el código INE correspondiente. Implementa búsqueda exacta y parcial.
    
    Args:
        nombre_municipio: Nombre del municipio a buscar
        diccionario_path: Ruta al archivo Excel con el diccionario de municipios
        
    Returns:
        str: Código INE del municipio (formato PPPNN)
        
    Raises:
        ValueError: Si el municipio no se encuentra en el diccionario
        
    Example:
        >>> codigo = get_municipio_code("Granada")
        >>> print(codigo)  # "18087"
    """
    df = pd.read_excel(diccionario_path, header=1, usecols=["CPRO","CMUN","NOMBRE"])
    nombre_norm = normalizar(nombre_municipio)
    df["NORM"] = df["NOMBRE"].apply(normalizar)
    # Coincidencia exacta
    match = df[df["NORM"] == nombre_norm]
    if match.empty:
        # Coincidencia parcial
        match = df[df["NORM"].str.contains(nombre_norm)]
    if match.empty:
        raise ValueError(f"No se encontró el municipio '{nombre_municipio}' en el diccionario.")
    row = match.iloc[0]
    cod_prov = row["CPRO"]
    cod_muni = row["CMUN"]
    return f"{cod_prov:02d}{cod_muni:03d}"

# ==============================================================================
# FUNCIONES DE PREDICCIONES METEOROLÓGICAS
# ==============================================================================

def get_prediccion_diaria(cod_muni: str) -> Union[Dict, List]:
    """
    🌡️ Obtiene predicción meteorológica diaria de AEMET
    
    Descarga los datos de predicción diaria para un municipio específico
    usando la API oficial de AEMET. Incluye temperaturas, precipitación,
    viento y otros parámetros meteorológicos.
    
    Args:
        cod_muni (str): Código INE del municipio (formato PPPNN)
    
    Returns:
        dict/list: Datos de predicción en formato JSON
    
    Raises:
        ValueError: Si no está configurada la API key
        requests.exceptions.RequestException: En caso de error de conexión
    
    Example:
        >>> data = get_prediccion_diaria("18015")  # Benaluá
        >>> print(len(data))  # Número de días de predicción
    """
    logger.info(f"🌡️ Solicitando predicción diaria para municipio: {cod_muni}")
    if not AEMET_API_KEY:
        logger.error("ERROR No se ha configurado la API key de AEMET")
        raise ValueError("No se ha configurado la API key de AEMET.")
    
    url_pred = f"https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/{cod_muni}/"
    headers = {"api_key": AEMET_API_KEY}
    
    try:
        logger.info(f"REQUEST Haciendo request a AEMET: {url_pred}")
        r_pred = _make_request_with_retry(url_pred, headers=headers)
        resp = r_pred.json()
        logger.info(f"DATA Respuesta inicial AEMET: {resp}")
        
        data_url = resp.get("datos")
        if data_url:
            logger.info(f"REQUEST Descargando datos desde: {data_url}")
            r_data = _make_request_with_retry(data_url, headers=headers)
            data = r_data.json()
            logger.info(f"OK Datos diarios obtenidos: {len(data) if isinstance(data, list) else 'N/A'} elementos")
            _log_json_shape("DIARIA", data)
            return data
        
        logger.warning("WARNING No se encontró URL de datos en la respuesta")
        return resp
        
    except Exception as e:
        logger.error(f"ERROR Error obteniendo predicción diaria: {e}")
        raise

def get_prediccion_horaria(cod_muni: str) -> Union[Dict, List]:
    """
    ⏰ Obtiene predicción meteorológica horaria de AEMET
    
    Descarga los datos de predicción horaria detallada para un municipio
    específico. Proporciona información meteorológica con resolución horaria.
    
    Args:
        cod_muni (str): Código INE del municipio (formato PPPNN)
    
    Returns:
        dict/list: Datos de predicción horaria en formato JSON
    
    Raises:
        ValueError: Si no está configurada la API key
        requests.exceptions.RequestException: En caso de error de conexión
    
    Example:
        >>> data = get_prediccion_horaria("18015")  # Benaluá
        >>> print(f"Horas de predicción: {len(data)}")
    """
    logger.info(f"⏰ Solicitando predicción horaria para municipio: {cod_muni}")
    if not AEMET_API_KEY:
        logger.error("ERROR No se ha configurado la API key de AEMET")
        raise ValueError("No se ha configurado la API key de AEMET.")
    
    url_pred = f"https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/horaria/{cod_muni}/"
    headers = {"api_key": AEMET_API_KEY}
    
    try:
        logger.info(f"REQUEST Haciendo request a AEMET: {url_pred}")
        r_pred = _make_request_with_retry(url_pred, headers=headers)
        resp = r_pred.json()
        logger.info(f"DATA Respuesta inicial AEMET: {resp}")
        
        data_url = resp.get("datos")
        if data_url:
            logger.info(f"REQUEST Descargando datos desde: {data_url}")
            r_data = _make_request_with_retry(data_url, headers=headers)
            data = r_data.json()
            logger.info(f"OK Datos horarios obtenidos: {len(data) if isinstance(data, list) else 'N/A'} elementos")
            _log_json_shape("HORARIA", data)
            return data
        
        logger.warning("WARNING No se encontró URL de datos en la respuesta")
        return resp
        
    except Exception as e:
        logger.error(f"ERROR Error obteniendo predicción horaria: {e}")
        raise

def get_lista_municipios(
    diccionario_path: str = "notebooks/data/diccionario24.xlsx"
) -> List[str]:
    """
    🏢 Obtiene lista completa de municipios disponibles
    
    Carga y procesa el diccionario de municipios españoles para obtener
    una lista alfabetizada de todos los nombres disponibles.
    
    Args:
        diccionario_path (str): Ruta al archivo Excel con el diccionario
    
    Returns:
        List[str]: Lista ordenada de nombres de municipios
    
    Example:
        >>> municipios = get_lista_municipios()
        >>> print(f"Municipios disponibles: {len(municipios)}")
        >>> print(municipios[:5])  # Primeros 5
    """
    df = pd.read_excel(diccionario_path, header=1, usecols=["NOMBRE"])
    return sorted(df["NOMBRE"].dropna().astype(str).unique().tolist())
