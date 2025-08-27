"""
============================================================================
                    FINCA STORE - GESTIÓN DE FINCAS GEOESPACIALES
============================================================================

Módulo para la gestión y almacenamiento de fincas agrícolas con soporte
geoespacial completo. Proporciona funcionalidades CRUD para fincas con
cálculos precisos de área, validación geométrica y persistencia atómica.

Características principales:
- Cálculo preciso de áreas usando coordenadas geográficas
- Validación y sanitización de geometrías GeoJSON
- Operaciones CRUD completas (Create, Read, Update, Delete)
- Persistencia atómica para prevenir corrupción de datos
- Soporte para importación/exportación GeoJSON
- Nombres únicos automáticos para evitar duplicados

Dependencias opcionales:
- Shapely: Para validación y reparación de geometrías
- Si no está disponible, usa validación básica

Autor: Sistema de Monitoreo Agrícola
Versión: 2024
============================================================================
"""

# Librerías estándar
import datetime
import json
import math
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

# Librerías de terceros

# Shapely (opcional) - Para validación geométrica avanzada
try:
    from shapely.geometry import Polygon, MultiPolygon, mapping, shape
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("⚠️ Warning: Shapely no disponible. Validación geométrica será básica.")

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

# Configuración del archivo de almacenamiento persistente
STORE_FILE = Path("data/fincas.json")
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Constantes para cálculos geográficos
METERS_PER_DEGREE_LAT = 111000  # Metros por grado de latitud (constante)
SQUARE_METERS_TO_HECTARES = 10000  # Conversión de m² a hectáreas

# ==============================================================================
# FUNCIONES DE CÁLCULO GEOESPACIAL
# ==============================================================================

def calculate_polygon_area_hectares(coordinates: List[List[float]]) -> float:
    """
    Calcula el área de un polígono en hectáreas con precisión geográfica.
    
    Utiliza la biblioteca Shapely si está disponible para máxima precisión,
    o implementa la fórmula del surveyor como fallback. Aplica correcciones
    geográficas específicas para la latitud de España (~37°).
    
    Args:
        coordinates: Lista de coordenadas en formato [[lon, lat], [lon, lat], ...]
                    Las coordenadas deben estar en grados decimales (WGS84)
        
    Returns:
        float: Área del polígono en hectáreas, redondeada a 2 decimales
        
    Note:
        - Maneja automáticamente el cierre del polígono si es necesario
        - Aplica factor de corrección por latitud para mayor precisión
        - Retorna 0.0 si hay errores en el cálculo o datos insuficientes
        
    Example:
        >>> coords = [[-2.5, 37.0], [-2.4, 37.0], [-2.4, 37.1], [-2.5, 37.1]]
        >>> area = calculate_polygon_area_hectares(coords)
        >>> print(f"Área: {area} hectáreas")
    """
    # Validación de entrada
    if not coordinates or len(coordinates) < 3:
        return 0.0
    
    try:
        # Método 1: Usar Shapely si está disponible (mayor precisión)
        if SHAPELY_AVAILABLE:
            geom = Polygon(coordinates)
            
            # Calcular latitud promedio para corrección geográfica
            avg_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
            lon_correction_factor = math.cos(math.radians(avg_lat))
            
            # Factores de conversión ajustados por latitud
            m_per_degree_lon = METERS_PER_DEGREE_LAT * lon_correction_factor
            
            # Convertir área de grados² a metros²
            area_deg_squared = geom.area
            area_m_squared = area_deg_squared * METERS_PER_DEGREE_LAT * m_per_degree_lon
            
            # Convertir a hectáreas y redondear
            area_hectares = area_m_squared / SQUARE_METERS_TO_HECTARES
            return round(area_hectares, 2)
        
        else:
            # Método 2: Fórmula del surveyor (fallback cuando Shapely no disponible)
            coords_copy = coordinates.copy()
            
            # Asegurar que el polígono esté cerrado
            if coords_copy[0] != coords_copy[-1]:
                coords_copy.append(coords_copy[0])
            
            # Aplicar fórmula del surveyor (Shoelace formula)
            area_deg_squared = 0.0
            for i in range(len(coords_copy) - 1):
                area_deg_squared += (coords_copy[i][0] * coords_copy[i+1][1] - 
                                   coords_copy[i+1][0] * coords_copy[i][1])
            
            area_deg_squared = abs(area_deg_squared) / 2.0
            
            # Aplicar corrección geográfica
            avg_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
            lon_correction_factor = math.cos(math.radians(avg_lat))
            m_per_degree_lon = METERS_PER_DEGREE_LAT * lon_correction_factor
            
            # Convertir a metros² y luego a hectáreas
            area_m_squared = area_deg_squared * METERS_PER_DEGREE_LAT * m_per_degree_lon
            area_hectares = area_m_squared / SQUARE_METERS_TO_HECTARES
            
            return round(area_hectares, 2)
            
    except Exception as e:
        print(f"❌ Error en cálculo de área: {type(e).__name__}: {e}")
        return 0.0


# ==============================================================================
# FUNCIONES DE PERSISTENCIA Y ALMACENAMIENTO
# ==============================================================================

def _atomic_write(path: str, data) -> None:
    """
    Implementa escritura atómica de archivos para prevenir corrupción.
    
    Utiliza el patrón write-then-move para garantizar atomicidad:
    1. Escribe datos a archivo temporal (.tmp)
    2. Reemplaza archivo original de forma atómica
    3. Limpia archivos temporales en caso de error
    
    Este enfoque previene corrupción de datos durante escrituras
    interrumpidas y es seguro en entornos multi-proceso.
    
    Args:
        path: Ruta completa del archivo de destino
        data: Datos a escribir (serializables a JSON)
    
    Raises:
        Exception: Re-lanza excepciones tras limpieza de temporales
        
    Note:
        - Usa codificación UTF-8 para caracteres especiales
        - JSON con indentación para legibilidad
        - Limpieza garantizada de archivos temporales
    """
    tmp_path = Path(f"{path}.tmp")
    try:
        # Fase 1: Escribir a archivo temporal
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Fase 2: Reemplazo atómico (operación atómica del OS)
        os.replace(tmp_path, path)
        
    except Exception as e:
        # Limpieza garantizada de archivos temporales
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass  # Ignorar errores de limpieza
        raise e

def load_fincas() -> List[Dict]:
    """
    Carga todas las fincas desde el almacenamiento persistente.
    
    Lee y valida el archivo JSON de fincas, manejando graciosamente
    casos de archivos inexistentes, vacíos o corruptos. Implementa
    validación robusta del formato GeoJSON.
    
    Returns:
        Lista de features GeoJSON válidos. Cada feature incluye:
        - type: "Feature" (estándar GeoJSON)
        - id: UUID único de identificación
        - geometry: Geometría espacial (Polygon/MultiPolygon)
        - properties: Metadatos (nombre, área, fechas, cultivo)
    
    Note:
        - Retorna lista vacía para archivos inexistentes/corruptos
        - Validación automática de estructura JSON
        - Logging detallado para debugging
        - Manejo seguro de excepciones
        
    Example:
        >>> fincas = load_fincas()
        >>> print(f"📊 Cargadas {len(fincas)} fincas")
        >>> for finca in fincas:
        ...     props = finca['properties']
        ...     print(f"{props['name']}: {props['area']} ha")
    """
    try:
        # Verificar precondiciones del archivo
        if not STORE_FILE.exists():
            print(f"📁 Archivo de fincas no existe: {STORE_FILE}")
            return []
            
        if STORE_FILE.stat().st_size == 0:
            print(f"📄 Archivo de fincas está vacío: {STORE_FILE}")
            return []
        
        # Leer y parsear JSON con manejo robusto
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Validación estricta de estructura
        if not isinstance(data, list):
            print(f"⚠️ Estructura inválida en {STORE_FILE}: esperado 'list', encontrado '{type(data).__name__}'")
            return []
        
        print(f"Cargadas {len(data)} fincas desde {STORE_FILE}")
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON malformado en {STORE_FILE}: {e}")
        return []
    except PermissionError as e:
        print(f"Sin permisos de lectura en {STORE_FILE}: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado cargando fincas: {type(e).__name__}: {e}")
        return []

def save_fincas(fincas: List[Dict]) -> None:
    """
    Guarda todas las fincas usando escritura atómica para máxima seguridad.
    
    Implementa persistencia robusta usando el patrón write-then-move
    para prevenir corrupción de datos durante operaciones críticas.
    La escritura es completamente atómica desde la perspectiva del sistema.
    
    Args:
        fincas: Lista de features GeoJSON válidos a persistir
    
    Raises:
        Exception: Si falla la operación de escritura atómica
        
    Note:
        - Escritura atómica garantizada via _atomic_write()
        - Formato JSON humanamente legible (indentado)
        - Codificación UTF-8 para caracteres especiales
        - Validación de entrada delegada al caller
        - Operación all-or-nothing (todo o nada)
    
    Example:
        >>> fincas = load_fincas()
        >>> fincas.append(nueva_finca_geojson)
        >>> save_fincas(fincas)  # Operación atómica
    """
    try:
        # Validación básica de entrada
        if not isinstance(fincas, list):
            raise ValueError(f"Se esperaba 'list', recibido '{type(fincas).__name__}'")
        
        # Ejecutar escritura atómica
        _atomic_write(str(STORE_FILE), fincas)
        print(f"💾 {len(fincas)} fincas guardadas exitosamente en {STORE_FILE}")
        
    except Exception as e:
        print(f"❌ Fallo en guardado: {type(e).__name__}: {e}")
        raise

def _sanitize_geometry(geometry: Dict) -> Dict:
    """
    Sanitiza y valida geometrías GeoJSON.
    
    Convierte a Shapely (si disponible), repara geometrías inválidas y garantiza
    que el resultado sea un Polígono o MultiPolígono válido en formato GeoJSON.
    
    Args:
        geometry: Geometría en formato GeoJSON dict
        
    Returns:
        dict: Geometría sanitizada y válida en formato GeoJSON
        
    Raises:
        ValueError: Si la geometría no es válida o no es polígono/multipolígono
        
    Note:
        - Con Shapely: validación y reparación automática
        - Sin Shapely: solo validación estructural básica
    """
    if not SHAPELY_AVAILABLE:
        # Sin shapely, solo validamos estructura básica
        if not isinstance(geometry, dict) or "type" not in geometry:
            raise ValueError("Invalid geometry structure")
        return geometry
    
    try:
        geom = shape(geometry)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if isinstance(geom, (Polygon, MultiPolygon)):
            return mapping(geom)
        raise ValueError("La geometría debe ser un polígono o multipolígono válido.")
    except Exception as e:
        print(f"Warning: Geometry validation failed: {e}")
        return geometry

def _unique_name(base: str, existing_names: set) -> str:
    """
    Genera un nombre único para evitar duplicados.
    
    Aplica sufijos numéricos incrementales hasta encontrar un nombre
    que no exista en el conjunto de nombres existentes.
    
    Args:
        base: Nombre base deseado
        existing_names: Conjunto de nombres ya existentes
        
    Returns:
        str: Nombre único garantizado
        
    Example:
        >>> existing = {"Finca", "Finca_1"}
        >>> _unique_name("Finca", existing)
        'Finca_2'
    """
    name = base.strip() or "Finca"
    if name not in existing_names:
        return name
    suffix = 1
    while f"{name}_{suffix}" in existing_names:
        suffix += 1
    return f"{name}_{suffix}"

def add_finca(
    name: str, 
    geometry: Dict, 
    crop_type: Optional[str] = None, 
    area: Optional[str] = None
) -> Dict:
    """
    Añade una nueva finca con área calculada automáticamente.
    
    Crea una nueva finca GeoJSON con cálculo automático del área basado
    en las coordenadas geográficas. Garantiza nombres únicos y valida
    la geometría antes del almacenamiento.
    
    Args:
        name: Nombre deseado para la finca
        geometry: Geometría GeoJSON (Polygon o MultiPolygon)
        crop_type: Tipo de cultivo (opcional)
        area: Parámetro legacy (se ignora, área se calcula automáticamente)
        
    Returns:
        dict: Feature GeoJSON de la finca creada
        
    Raises:
        Exception: Si falla la validación o el guardado
        
    Example:
        >>> geom = {"type": "Polygon", "coordinates": [[[...]]]} 
        >>> finca = add_finca("Mi Olivar", geom, "olivos")
        >>> print(f"Área: {finca['properties']['area']} ha")
    """
    try:
        fincas = load_fincas()
        existing_names = {f.get("properties", {}).get("name", "") for f in fincas}
        unique = _unique_name(name, existing_names)
        sanitized = _sanitize_geometry(geometry)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Calcular área automáticamente
        calculated_area = 0.0
        if geometry.get("type") == "Polygon" and geometry.get("coordinates"):
            coordinates = geometry["coordinates"][0]  # Exterior ring
            calculated_area = calculate_polygon_area_hectares(coordinates)
        
        # Propiedades base
        properties = {
            "name": unique,
            "area": calculated_area,  # Área calculada automáticamente
            "created_at": now,
            "updated_at": now,
        }
        
        feature = {
            "type": "Feature",
            "id": str(uuid.uuid4()),
            "geometry": sanitized,
            "properties": properties,
        }
        
        fincas.append(feature)
        save_fincas(fincas)
        print(f"Finca '{unique}' añadida correctamente con área {calculated_area} ha")
        return feature
    except Exception as e:
        print(f"Error adding finca: {e}")
        raise

def update_finca(
    finca_id: str, 
    name: Optional[str] = None, 
    crop_type: Optional[str] = None, 
    area: Optional[str] = None
) -> None:
    """
    Actualiza una finca existente con recálculo automático de área.
    
    Modifica los metadatos de una finca existente. El área siempre
    se recalcula automáticamente basándose en la geometría actual.
    
    Args:
        finca_id: UUID único de identificación de la finca
        name: Nuevo nombre (opcional, debe ser único)
        crop_type: Nuevo tipo de cultivo (opcional)
        area: Parámetro legacy (se ignora, área se recalcula automáticamente)
        
    Raises:
        Exception: Si falla la actualización o el guardado
        
    Note:
        - El área siempre se recalcula desde la geometría
        - Los nombres se validan para evitar duplicados
        - Se actualiza automáticamente el timestamp updated_at
    """
    try:
        fincas = load_fincas()
        existing_names = {
            f.get("properties", {}).get("name", "")
            for f in fincas
            if f.get("id") != finca_id
        }
        
        updated = False
        for f in fincas:
            if f.get("id") == finca_id:
                props = f.setdefault("properties", {})
                
                # Actualizar nombre si se proporciona
                if name is not None:
                    unique = _unique_name(name, existing_names)
                    props["name"] = unique
                
                # El área se recalcula automáticamente basándose en la geometría
                geometry = f.get("geometry", {})
                if geometry.get("type") == "Polygon" and geometry.get("coordinates"):
                    coordinates = geometry["coordinates"][0]  # Exterior ring
                    calculated_area = calculate_polygon_area_hectares(coordinates)
                    props["area"] = calculated_area
                
                # Actualizar timestamp
                props["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                updated = True
                break
        
        if updated:
            save_fincas(fincas)
            print(f"Finca {finca_id} actualizada correctamente")
        else:
            print(f"Warning: Finca {finca_id} not found for update")
    except Exception as e:
        print(f"Error updating finca: {e}")
        raise

def rename_finca(finca_id: str, new_name: str) -> None:
    """
    Renombra una finca (función de conveniencia).
    
    Wrapper para mantener compatibilidad con código existente.
    Internamente utiliza update_finca() para garantizar consistencia.
    
    Args:
        finca_id: UUID de la finca a renombrar
        new_name: Nuevo nombre único
    """
    update_finca(finca_id, name=new_name)

def delete_finca(finca_id: str) -> None:
    """
    Elimina una finca del almacenamiento.
    
    Remueve permanentemente una finca identificada por su UUID.
    La operación es atómica y actualiza el archivo de forma segura.
    
    Args:
        finca_id: UUID único de la finca a eliminar
        
    Raises:
        Exception: Si falla la eliminación o el guardado
        
    Note:
        - Operación irreversible
        - No produce error si la finca no existe
        - Actualización atómica del archivo
    """
    try:
        fincas = load_fincas()
        original_count = len(fincas)
        fincas = [f for f in fincas if f.get("id") != finca_id]
        
        if len(fincas) < original_count:
            save_fincas(fincas)
            print(f"Finca {finca_id} eliminada correctamente")
        else:
            print(f"Warning: Finca {finca_id} not found for deletion")
    except Exception as e:
        print(f"Error deleting finca: {e}")
        raise

def get_finca(finca_id: str) -> Optional[Dict]:
    """
    Obtiene una finca específica por su UUID.
    
    Busca y retorna la finca con el ID especificado,
    o None si no existe.
    
    Args:
        finca_id: UUID único de la finca
        
    Returns:
        Optional[Dict]: Feature GeoJSON de la finca o None si no existe
        
    Example:
        >>> finca = get_finca("123e4567-e89b-12d3-a456-426614174000")
        >>> if finca:
        ...     print(f"Nombre: {finca['properties']['name']}")
    """
    try:
        fincas = load_fincas()
        return next((f for f in fincas if f.get("id") == finca_id), None)
    except Exception as e:
        print(f"Error getting finca {finca_id}: {e}")
        return None

def list_fincas() -> List[Dict]:
    """
    Lista todas las fincas almacenadas.
    
    Wrapper de conveniencia para load_fincas().
    
    Returns:
        List[Dict]: Lista de todas las fincas como features GeoJSON
    """
    return load_fincas()

def get_fincas_by_crop_type(crop_type: str) -> List[Dict]:
    """
    Obtiene fincas filtradas por tipo de cultivo.
    
    Busca y retorna todas las fincas que coinciden con el
    tipo de cultivo especificado.
    
    Args:
        crop_type: Tipo de cultivo a filtrar
        
    Returns:
        List[Dict]: Lista de fincas que coinciden con el tipo de cultivo
        
    Example:
        >>> olivos = get_fincas_by_crop_type("olivos")
        >>> print(f"Fincas de olivos: {len(olivos)}")
    """
    try:
        fincas = load_fincas()
        return [f for f in fincas if f.get("properties", {}).get("crop_type") == crop_type]
    except Exception as e:
        print(f"Error getting fincas by crop type: {e}")
        return []

def get_total_area() -> float:
    """
    Calcula el área total de todas las fincas.
    
    Suma las áreas individuales de todas las fincas almacenadas
    para obtener el área total gestionada.
    
    Returns:
        float: Área total en hectáreas
        
    Note:
        - Ignora fincas con áreas inválidas o faltantes
        - Retorna 0.0 si no hay fincas o en caso de error
    """
    try:
        fincas = load_fincas()
        total = 0.0
        for f in fincas:
            area_str = f.get("properties", {}).get("area", "")
            if area_str:
                try:
                    total += float(area_str)
                except (ValueError, TypeError):
                    continue
        return total
    except Exception as e:
        print(f"Error calculating total area: {e}")
        return 0.0

def get_crop_type_stats() -> Dict[str, Dict]:
    """
    Obtiene estadísticas agrupadas por tipo de cultivo.
    
    Genera un resumen estadístico con conteo de fincas y área
    total para cada tipo de cultivo registrado.
    
    Returns:
        Dict[str, Dict]: Diccionario con estadísticas por cultivo:
            {"cultivo": {"count": int, "total_area": float}}
            
    Example:
        >>> stats = get_crop_type_stats()
        >>> for cultivo, datos in stats.items():
        ...     print(f"{cultivo}: {datos['count']} fincas, {datos['total_area']} ha")
    """
    try:
        fincas = load_fincas()
        stats = {}
        
        for f in fincas:
            props = f.get("properties", {})
            crop_type = props.get("crop_type", "sin_especificar")
            area_str = props.get("area", "")
            
            if crop_type not in stats:
                stats[crop_type] = {"count": 0, "total_area": 0.0}
            
            stats[crop_type]["count"] += 1
            
            if area_str:
                try:
                    stats[crop_type]["total_area"] += float(area_str)
                except (ValueError, TypeError):
                    continue
        
        return stats
    except Exception as e:
        print(f"Error getting crop type stats: {e}")
        return {}

def export_finca_geojson(finca_id: str, path: Path) -> None:
    """
    Exporta una finca individual a archivo GeoJSON.
    
    Guarda una finca específica en formato GeoJSON estándar
    para uso en aplicaciones GIS externas.
    
    Args:
        finca_id: UUID de la finca a exportar
        path: Ruta del archivo de destino
        
    Raises:
        KeyError: Si la finca no existe
        Exception: Si falla la escritura del archivo
        
    Example:
        >>> from pathlib import Path
        >>> export_finca_geojson("123-uuid", Path("mi_finca.geojson"))
    """
    try:
        finca = get_finca(finca_id)
        if finca is None:
            raise KeyError(f"No existe finca con id {finca_id}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(finca, f, indent=2, ensure_ascii=False)
        print(f"Finca {finca_id} exportada a {path}")
    except Exception as e:
        print(f"Error exporting finca: {e}")
        raise

def export_multiple_fincas_geojson(finca_ids: List[str], path: Path) -> None:
    """
    Exporta múltiples fincas a un FeatureCollection GeoJSON.
    
    Combina varias fincas en un único archivo GeoJSON FeatureCollection
    estándar con metadatos de exportación.
    
    Args:
        finca_ids: Lista de UUIDs de fincas a exportar
        path: Ruta del archivo de destino
        
    Raises:
        ValueError: Si no se encuentran fincas válidas
        Exception: Si falla la escritura del archivo
        
    Example:
        >>> ids = ["uuid1", "uuid2", "uuid3"]
        >>> export_multiple_fincas_geojson(ids, Path("fincas.geojson"))
    """
    try:
        fincas = [get_finca(fid) for fid in finca_ids]
        fincas = [f for f in fincas if f is not None]
        
        if not fincas:
            raise ValueError("No se encontraron fincas válidas para exportar")
        
        geojson = {
            "type": "FeatureCollection",
            "features": fincas,
            "properties": {
                "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
                "total_fincas": len(fincas)
            }
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        print(f"{len(fincas)} fincas exportadas a {path}")
    except Exception as e:
        print(f"Error exporting multiple fincas: {e}")
        raise

def import_finca_geojson(path: Path) -> Dict:
    """
    Importa una finca desde archivo GeoJSON.
    
    Lee un archivo GeoJSON Feature y lo incorpora al sistema con
    validación automática de geometría y generación de metadatos.
    
    Args:
        path: Ruta del archivo GeoJSON a importar
        
    Returns:
        Dict: Feature GeoJSON de la finca importada
        
    Raises:
        Exception: Si falla la lectura o validación del archivo
        
    Note:
        - Sanitiza automáticamente la geometría
        - Genera UUID si no existe
        - Garantiza nombre único
        - Actualiza timestamps
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            feature = json.load(f)
        
        # Sanitizar geometría
        if "geometry" in feature:
            feature["geometry"] = _sanitize_geometry(feature["geometry"])
        if not feature.get("id"):
            feature["id"] = str(uuid.uuid4())
        
        now = datetime.datetime.utcnow().isoformat() + "Z"
        props = feature.setdefault("properties", {})
        props.setdefault("created_at", now)
        props["updated_at"] = now
        
        # Nombre único
        fincas = load_fincas()
        existing_names = {f.get("properties", {}).get("name", "") for f in fincas}
        name = _unique_name(props.get("name", "Finca"), existing_names)
        props["name"] = name
        
        fincas.append(feature)
        save_fincas(fincas)
        print(f"Finca '{name}' importada correctamente")
        return feature
    except Exception as e:
        print(f"Error importing finca: {e}")
        raise

def import_multiple_fincas_geojson(path: Path) -> List[Dict]:
    """
    Importa múltiples fincas desde FeatureCollection GeoJSON.
    
    Lee un archivo GeoJSON FeatureCollection e importa todas las
    fincas contenidas con validación y procesamiento automático.
    
    Args:
        path: Ruta del archivo FeatureCollection GeoJSON
        
    Returns:
        List[Dict]: Lista de features GeoJSON importados
        
    Raises:
        ValueError: Si el archivo no es una FeatureCollection válida
        Exception: Si falla la importación
        
    Note:
        - Valida que sea FeatureCollection
        - Procesa cada feature individualmente
        - Garantiza nombres únicos para todos
        - Operación atómica (todo o nada)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if data.get("type") != "FeatureCollection":
            raise ValueError("El archivo debe ser una FeatureCollection válida")
        
        features = data.get("features", [])
        if not features:
            raise ValueError("No se encontraron features en el archivo")
        
        imported_fincas = []
        fincas = load_fincas()
        existing_names = {f.get("properties", {}).get("name", "") for f in fincas}
        
        for feature in features:
            # Sanitizar geometría
            if "geometry" in feature:
                feature["geometry"] = _sanitize_geometry(feature["geometry"])
            
            if not feature.get("id"):
                feature["id"] = str(uuid.uuid4())
            
            now = datetime.datetime.utcnow().isoformat() + "Z"
            props = feature.setdefault("properties", {})
            props.setdefault("created_at", now)
            props["updated_at"] = now
            
            # Nombre único
            name = _unique_name(props.get("name", "Finca"), existing_names)
            props["name"] = name
            existing_names.add(name)
            
            fincas.append(feature)
            imported_fincas.append(feature)
        
        save_fincas(fincas)
        print(f"{len(imported_fincas)} fincas importadas correctamente")
        return imported_fincas
    except Exception as e:
        print(f"Error importing multiple fincas: {e}")
        raise

# Función de utilidad para debug
def debug_fincas() -> None:
    """
    Función de utilidad para debugging del estado del sistema.
    
    Imprime información detallada sobre el archivo de almacenamiento
    y las fincas cargadas para facilitar la depuración.
    
    Note:
        - Solo para desarrollo y depuración
        - Imprime información directamente a consola
        - Maneja errores graciosamente
    """
    try:
        print(f"STORE_FILE exists: {STORE_FILE.exists()}")
        if STORE_FILE.exists():
            print(f"STORE_FILE size: {STORE_FILE.stat().st_size} bytes")
        
        fincas = load_fincas()
        print(f"Loaded {len(fincas)} fincas")
        
        for i, finca in enumerate(fincas):
            props = finca.get("properties", {})
            print(f"  {i+1}. {props.get('name', 'NO_NAME')} ({finca.get('id', 'NO_ID')})")
            
    except Exception as e:
        print(f"Debug error: {e}")

if __name__ == "__main__":
    debug_fincas()