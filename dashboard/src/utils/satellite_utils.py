# src/utils/satellite_utils.py

import os
import io
import base64
import logging
from io import BytesIO
from typing import List, Optional, Tuple, Union

import numpy as np
import requests
import rasterio
import rasterio.features
from shapely.geometry import Polygon, shape as shapely_shape, mapping as shapely_mapping
from shapely.geometry.base import BaseGeometry
from dotenv import load_dotenv
from datetime import datetime, timedelta

from pyproj import Geod, Transformer
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend

load_dotenv()

# ------------------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------------------
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# ------------------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ========================= EVALSCRIPTS =========================
# Índices soportados: NDVI, OSAVI, NDRE
# - "masked=True": usa mosaico temporal (TILE) + mediana por píxel y filtra con SCL+dataMask
# - "masked=False": versión simple (una sola muestra) sin filtrar

# ---- Versiones simples (sin máscara ni mosaico) ----
EVALSCRIPT_NDVI_SIMPLE = """\
//VERSION=3
function setup() {
  return {
    input: ["B08", "B04"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  var den = s.B08 + s.B04 + 1e-6;
  var ndvi = (s.B08 - s.B04) / den;
  return [ndvi];
}
"""

EVALSCRIPT_OSAVI_SIMPLE = """\
//VERSION=3
function setup() {
  return {
    input: ["B08", "B04"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  var den = s.B08 + s.B04 + 0.16 + 1e-6;
  var osavi = (s.B08 - s.B04) / den;
  return [osavi];
}
"""

# Nota: NDRE usa B05 (20 m) + B08 (10 m). Sentinel Hub remuestrea al grid de salida.
EVALSCRIPT_NDRE_SIMPLE = """\
//VERSION=3
function setup() {
  return {
    input: ["B08", "B05"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  var den = s.B08 + s.B05 + 1e-6;
  var ndre = (s.B08 - s.B05) / den;
  return [ndre];
}
"""

# ---- Helpers comunes (masked + mosaico temporal por mediana) ----
def _median_js():
    return """\
function median(vals) {
  if (!vals || vals.length === 0) return NaN;
  vals.sort(function(a,b){ return a-b; });
  var m = Math.floor(vals.length / 2);
  return (vals.length % 2) ? vals[m] : 0.5 * (vals[m-1] + vals[m]);
}
"""

def _masked_header_js(bands):
    # bands es algo como: ["B08","B04","SCL","dataMask"]
    # Usamos mosaicking TILE para disponer de múltiples muestras (samples[])
    bands_list = ",".join(f'"{b}"' for b in bands)
    return f"""\
//VERSION=3
function setup() {{
  return {{
    input: [{{ bands: [{bands_list}] }}],
    output: {{ bands: 1, sampleType: "FLOAT32" }},
    mosaicking: "TILE"
  }};
}}
"""

def _keep_classes_list(include_water: bool) -> str:
    # SCL a mantener: vegetación(4), no vegetado(5), sin clasificar(7); opcional agua(6)
    keep = [4, 5, 7] + ([6] if include_water else [])
    return ",".join(str(x) for x in keep)

# ---- NDVI masked + mediana temporal ----
def _ndvi_masked_evalscript(include_water: bool = False) -> str:
    keep = _keep_classes_list(include_water)
    return (
        _masked_header_js(["B08","B04","SCL","dataMask"])
        + _median_js()
        + f"""\
const KEEP = new Set([{keep}]);

function evaluatePixel(samples) {{
  var vals = [];
  for (var i = 0; i < samples.length; i++) {{
    var s = samples[i];
    if (s.dataMask === 0) continue;
    if (!KEEP.has(s.SCL)) continue;
    var den = s.B08 + s.B04 + 1e-6;
    if (den <= 0) continue;
    var ndvi = (s.B08 - s.B04) / den;
    if (isFinite(ndvi)) vals.push(ndvi);
  }}
  return [ median(vals) ];
}}
"""
    )

# ---- OSAVI masked + mediana temporal ----
def _osavi_masked_evalscript(include_water: bool = False) -> str:
    keep = _keep_classes_list(include_water)
    return (
        _masked_header_js(["B08","B04","SCL","dataMask"])
        + _median_js()
        + f"""\
const KEEP = new Set([{keep}]);

function evaluatePixel(samples) {{
  var vals = [];
  for (var i = 0; i < samples.length; i++) {{
    var s = samples[i];
    if (s.dataMask === 0) continue;
    if (!KEEP.has(s.SCL)) continue;
    var den = s.B08 + s.B04 + 0.16 + 1e-6;
    if (den <= 0) continue;
    var osavi = (s.B08 - s.B04) / den;
    if (isFinite(osavi)) vals.push(osavi);
  }}
  return [ median(vals) ];
}}
"""
    )

# ---- NDRE masked + mediana temporal ----
def _ndre_masked_evalscript(include_water: bool = False) -> str:
    keep = _keep_classes_list(include_water)
    return (
        _masked_header_js(["B08","B05","SCL","dataMask"])
        + _median_js()
        + f"""\
const KEEP = new Set([{keep}]);

function evaluatePixel(samples) {{
  var vals = [];
  for (var i = 0; i < samples.length; i++) {{
    var s = samples[i];
    if (s.dataMask === 0) continue;
    if (!KEEP.has(s.SCL)) continue;
    var den = s.B08 + s.B05 + 1e-6;
    if (den <= 0) continue;
    var ndre = (s.B08 - s.B05) / den;
    if (isFinite(ndre)) vals.push(ndre);
  }}
  return [ median(vals) ];
}}
"""
    )

# ---- Selector público (firma sin cambios) ----
def build_evalscript(index: str = "NDVI", masked: bool = True, include_water: bool = False) -> str:
    """
    Devuelve la evalscript para un índice dado.
    index: NDVI | OSAVI | NDRE
    masked: si True aplica SCL + dataMask y mosaico temporal (mediana por píxel)
    include_water: si True, mantiene SCL==6 (agua)
    """
    ix = (index or "NDVI").upper()
    if ix == "NDVI":
        return _ndvi_masked_evalscript(include_water) if masked else EVALSCRIPT_NDVI_SIMPLE
    if ix == "OSAVI":
        return _osavi_masked_evalscript(include_water) if masked else EVALSCRIPT_OSAVI_SIMPLE
    if ix == "NDRE":
        return _ndre_masked_evalscript(include_water) if masked else EVALSCRIPT_NDRE_SIMPLE
    raise ValueError(f"Índice no soportado: {index}")
# ======================= FIN EVALSCRIPTS ========================


# ------------------------------------------------------------------------------
# Autenticación
# ------------------------------------------------------------------------------
def get_access_token(client_id: str, client_secret: str, timeout: int = 30) -> str:
    """Solicita un token de acceso a Copernicus Data Space."""
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

# ------------------------------------------------------------------------------
# Geometrías y áreas
# ------------------------------------------------------------------------------
def _is_bbox(x) -> bool:
    return isinstance(x, (list, tuple, np.ndarray)) and len(x) == 4 and all(isinstance(v, (int, float, np.floating)) for v in x)

def _is_polygon_like(x) -> bool:
    # Lista de listas (ring) o [[[ring]]]
    if isinstance(x, (list, tuple)) and len(x) > 0:
        first = x[0]
        if isinstance(first, (list, tuple)) and len(first) > 0:
            # ring: [[x,y], ...]
            if isinstance(first[0], (list, tuple)) and len(first[0]) == 2:
                return True  # [[[x,y],...]]
            if len(first) == 2 and all(isinstance(v, (int, float, np.floating)) for v in first):
                return True  # [[x,y], ...]
    return False

def _to_ring_coords(geometry_or_bbox) -> list:
    """Devuelve un anillo [[lon,lat], ...] a partir de varias representaciones."""
    if isinstance(geometry_or_bbox, BaseGeometry):
        geom = geometry_or_bbox
    elif isinstance(geometry_or_bbox, dict) and geometry_or_bbox.get("type"):
        geom = shapely_shape(geometry_or_bbox)
    elif _is_polygon_like(geometry_or_bbox):
        # [[lon,lat], ...] o [[[lon,lat], ...]]
        ring = geometry_or_bbox[0] if (len(geometry_or_bbox) > 0 and isinstance(geometry_or_bbox[0][0], (list, tuple))) else geometry_or_bbox
        return ring
    elif _is_bbox(geometry_or_bbox):
        lon_min, lat_min, lon_max, lat_max = geometry_or_bbox
        ring = [
            [lon_min, lat_min],
            [lon_max, lat_min],
            [lon_max, lat_max],
            [lon_min, lat_max],
            [lon_min, lat_min],
        ]
        return ring
    else:
        raise ValueError("Geometría no reconocida.")

    if geom.geom_type == "Polygon":
        return list(np.array(geom.exterior.coords)[:, :2])
    elif geom.geom_type == "MultiPolygon":
        # usar el mayor polígono
        poly = max(list(geom.geoms), key=lambda g: g.area)
        return list(np.array(poly.exterior.coords)[:, :2])
    else:
        raise ValueError("Solo se admiten Polygon/MultiPolygon o bbox.")

def _utm_epsg_for_lonlat(lon: float, lat: float) -> str:
    zone = int((lon + 180) // 6) + 1
    if lat >= 0:
        return f"EPSG:{32600 + zone}"
    else:
        return f"EPSG:{32700 + zone}"

def _calculate_area_hectares(geometry_or_bbox) -> float:
    """Área aproximada en hectáreas usando proyección UTM dinámica."""
    try:
        ring = _to_ring_coords(geometry_or_bbox)
        # centroide aprox
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        lon_c = float(np.mean(lons))
        lat_c = float(np.mean(lats))
        epsg = _utm_epsg_for_lonlat(lon_c, lat_c)

        transformer = Transformer.from_crs("EPSG:4326", epsg, always_xy=True)
        coords_utm = [transformer.transform(x, y) for x, y in ring]
        poly_utm = Polygon(coords_utm)
        return abs(poly_utm.area) / 10000.0
    except Exception as e:
        logger.warning(f"⚠️ _calculate_area_hectares fallback por error: {e}")
        return 10.0

# ------------------------------------------------------------------------------
# Llamada al Process API
# ------------------------------------------------------------------------------
def _compute_dims_from_bbox(_bbox, target_m_per_px=10.0, min_dim=512, max_dim=2048) -> Tuple[int, int]:
    # _bbox = [lon_min, lat_min, lon_max, lat_max]
    lon_min, lat_min, lon_max, lat_max = _bbox
    lat_mid = (lat_min + lat_max) / 2.0
    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * max(0.1, abs(np.cos(np.radians(lat_mid))))
    width_m = (lon_max - lon_min) * m_per_deg_lon
    height_m = (lat_max - lat_min) * m_per_deg_lat
    w = int(np.clip(round(width_m / target_m_per_px), min_dim, max_dim))
    h = int(np.clip(round(height_m / target_m_per_px), min_dim, max_dim))
    return w, h

def get_image(
    token: str,
    bbox: list = None,
    polygon_coords: list = None,
    evalscript: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    start_date: str = "2025-06-01",
    end_date: str = "2025-06-01",
    auto_resolution: bool = True,
    target_m_per_px: float = 10.0,
    min_dim: int = 512,
    max_dim: int = 2048,
    max_cloud_coverage: float = 20.0,
    mosaic_order: str = "leastCC",
    timeout: int = 120,
    max_attempts: int = 5
) -> BytesIO:
    """
    Solicita imagen procesada (por defecto índice de vegetación) al Process API.

    Puedes pasar evalscript personalizada o usar los helpers build_evalscript(...).
    """
    bbox_is_empty = bbox is None or (hasattr(bbox, "size") and getattr(bbox, "size", 1) == 0)
    polygon_is_empty = not polygon_coords or len(polygon_coords) == 0

    if bbox_is_empty and polygon_is_empty:
        raise ValueError("Debes proporcionar bbox o polygon_coords.")

    if not bbox_is_empty:
        bounds = {
            "bbox": bbox.tolist() if hasattr(bbox, "tolist") else bbox,
            "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
        }
        _bbox_for_dims = bounds["bbox"]
    else:
        ring = polygon_coords[0] if (isinstance(polygon_coords[0][0], (list, tuple))) else polygon_coords
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        _bbox_for_dims = [min(lons), min(lats), max(lons), max(lats)]
        bounds = {
            "geometry": {"type": "Polygon", "coordinates": polygon_coords},
            "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
        }

    if auto_resolution and target_m_per_px is not None:
        try:
            width, height = _compute_dims_from_bbox(_bbox_for_dims, target_m_per_px, min_dim, max_dim)
        except Exception as e:
            logger.warning(f"⚠️ auto_resolution falló, usando {width}x{height}: {e}")
            logger.warning(f"Parámetros: {target_m_per_px}, {min_dim}, {max_dim}")

    # Evitar peticiones gigantes (límite conservador)
    max_pixels = 2300 * 2300
    if width * height > max_pixels:
        scale = (max_pixels / (width * height)) ** 0.5
        width = int(width * scale)
        height = int(height * scale)
        logger.info(f"ℹ️ Redimensionado a {width}x{height} para respetar límites de API")

    if evalscript is None:
        # Por compatibilidad: si no se pasa evalscript, usar NDVI enmascarado por defecto
        evalscript = build_evalscript("NDVI", masked=True)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "input": {
            "bounds": bounds,
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{start_date}T00:00:00Z",
                        "to":   f"{end_date}T23:59:59Z"
                    },
                    "maxCloudCoverage": max_cloud_coverage,
                    "mosaickingOrder": mosaic_order
                }
            }]
        },
        "output": {
            "width": int(width),
            "height": int(height),
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        },
        "processing": {
            "upsampling": "BILINEAR",
            "downsampling": "BILINEAR"
        },
        "evalscript": evalscript
    }

    attempt = 0
    while True:
        attempt += 1
        resp = requests.post(PROCESS_URL, json=payload, headers=headers, timeout=timeout)
        
        if resp.status_code == 429:
            # Usar Retry-After del header (en milisegundos según la documentación)
            ra = resp.headers.get("Retry-After")
            if ra and str(ra).isdigit():
                wait_s = float(ra) / 1000.0  # Convertir ms a segundos
                # Aplicar límite razonable pero respetar el servidor
                wait_s = min(wait_s, 60)  # Máximo 1 minuto
            else:
                # Exponential backoff como recomienda la documentación
                wait_s = min(2 ** attempt, 30)  # 2, 4, 8, 16, 30 segundos
            
            logger.warning(f"⏳ 429 rate-limited, retry {attempt}/{max_attempts} in {wait_s:.1f}s")
            if attempt >= max_attempts:
                logger.error(f"❌ Error Process API después de {max_attempts} intentos: {resp.text[:500]}")
                resp.raise_for_status()
            
            import time
            time.sleep(wait_s)  # Sin jitter, respetar el tiempo exacto
            continue
        
        try:
            resp.raise_for_status()
            break
        except Exception:
            if attempt >= max_attempts:
                logger.error(f"❌ Error Process API: {resp.text[:500]}")
                raise
            # Para otros errores, esperar antes del retry
            import time
            time.sleep(min(2 ** attempt, 10))
            continue

    return BytesIO(resp.content)

# ------------------------------------------------------------------------------
# Stacks / Composites
# ------------------------------------------------------------------------------
def _is_polygon_any(g) -> bool:
    return _is_polygon_like(g) or isinstance(g, dict) or isinstance(g, BaseGeometry)

def _apply_polygon_mask(array: np.ndarray, geometry_or_bbox, transform) -> np.ndarray:
    ring = _to_ring_coords(geometry_or_bbox)
    mask = rasterio.features.geometry_mask(
        [Polygon(ring).__geo_interface__],
        transform=transform, invert=True, out_shape=array.shape
    )
    arr = array.copy()
    arr[~mask] = np.nan
    return arr

def _apply_quality_filters(array: np.ndarray) -> np.ndarray:
    # Recorta a rango permitido y elimina outliers
    arr = np.array(array, dtype="float32")
    arr = np.where((arr < -1) | (arr > 1), np.nan, arr)
    return arr

def fetch_ndvi_stack_time_sliced(
    token: str,
    geometry_or_bbox,
    start_date: str,
    end_date: str,
    evalscript: str = None,
    step_days: int = 10,
    width: int = 1024,
    height: int = 1024,
    min_valid_pixels: int = 50
):
    """
    Versión time-sliced del stack (más robusta con escenas nubladas).
    """
    if evalscript is None:
        evalscript = build_evalscript("NDVI", masked=True)

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        cur = start
        arrays, transform_ref = [], None

        area_ha = _calculate_area_hectares(geometry_or_bbox)
        if area_ha < 10:
            width, height = min(2048, width * 2), min(2048, height * 2)

        while cur <= end:
            sub_start = cur.strftime("%Y-%m-%d")
            sub_end = min(cur + timedelta(days=step_days - 1), end).strftime("%Y-%m-%d")

            img = get_image(
                token=token,
                bbox=None if _is_polygon_any(geometry_or_bbox) else geometry_or_bbox,
                polygon_coords=[_to_ring_coords(geometry_or_bbox)] if _is_polygon_any(geometry_or_bbox) else None,
                evalscript=evalscript,
                width=width, height=height,
                start_date=sub_start, end_date=sub_end,
                max_cloud_coverage=70,
                mosaic_order="leastCC",
                target_m_per_px=10.0
            )

            with rasterio.open(img) as src:
                arr = src.read(1).astype("float32")
                transform_ref = transform_ref or src.transform

                if _is_polygon_any(geometry_or_bbox):
                    arr = _apply_polygon_mask(arr, geometry_or_bbox, src.transform)

                arr = _apply_quality_filters(arr)
                if np.isfinite(arr).sum() >= min_valid_pixels:
                    arrays.append(arr)

            cur += timedelta(days=step_days)

        return arrays, transform_ref

    except Exception as e:
        logger.error(f"❌ Error en fetch_ndvi_stack_time_sliced: {e}")
        return [], None

def fetch_ndvi_stack_single(
    token: str,
    geometry_or_bbox,
    start_date: str,
    end_date: str,
    evalscript: str,
    width: int = 1024,
    height: int = 1024,
    adaptive_resolution: bool = True,
    **get_kwargs
):
    """
    Composite único para el rango [start_date, end_date].
    Compatible con cualquier evalscript (NDVI/OSAVI/NDRE).
    """
    try:
        if adaptive_resolution:
            area_ha = _calculate_area_hectares(geometry_or_bbox)
            if area_ha < 5:
                width, height = 2048, 2048
            elif area_ha < 50:
                width, height = 1536, 1536
            else:
                width, height = 1024, 1024

        polygon_param, bbox_param = None, None
        if _is_polygon_any(geometry_or_bbox):
            polygon_param = [_to_ring_coords(geometry_or_bbox)]
        else:
            bbox_param = geometry_or_bbox

        image = get_image(
            token=token,
            polygon_coords=polygon_param,
            bbox=bbox_param,
            evalscript=evalscript,
            start_date=start_date,
            end_date=end_date,
            width=width,
            height=height,
            target_m_per_px=get_kwargs.pop("target_m_per_px", 10.0),
            max_cloud_coverage=get_kwargs.pop("max_cloud_coverage", 60.0),
            mosaic_order=get_kwargs.pop("mosaic_order", "leastCC"),
            **get_kwargs
        )

        with rasterio.open(image) as src:
            array = src.read(1).astype("float32")
            transform = src.transform

        array = _apply_quality_filters(array)
        if array is None or array.size == 0:
            logger.error("❌ Array vacío")
            return [], None

        logger.info(f"✅ Array válido: shape={array.shape}, válidos={np.isfinite(array).sum()}")
        return [array], transform

    except Exception as e:
        logger.error(f"❌ Error en fetch_ndvi_stack_single: {e}")
        return [], None

def compute_index_composite(
    token: str,
    geometry_or_bbox,
    start_date: str,
    end_date: str,
    index: str = "NDVI",
    masked: bool = True,
    include_water: bool = False,
    **kwargs
) -> Tuple[Optional[np.ndarray], Optional[object]]:
    """
    Wrapper práctico para obtener un composite 2D de NDVI/OSAVI/NDRE.
    Devuelve (array, transform).
    """
    evalscript = build_evalscript(index=index, masked=masked, include_water=include_water)
    stack, transform = fetch_ndvi_stack_single(
        token=token,
        geometry_or_bbox=geometry_or_bbox,
        start_date=start_date,
        end_date=end_date,
        evalscript=evalscript,
        **kwargs
    )
    if not stack:
        return None, None
    return stack[0], transform

# ------------------------------------------------------------------------------
# Anomalías
# ------------------------------------------------------------------------------
def compute_ndvi_anomaly(
    token: str,
    geometry_or_bbox,
    start_date: str,
    end_date: str,
    past_years: List[int],
    evalscript: str = None,
    max_retries: int = 2
) -> np.ndarray:
    """
    Calcula anomalías del índice actual vs mediana de años de referencia.
    Por defecto usa NDVI enmascarado; puedes pasar evalscript de OSAVI/NDRE.
    """
    if evalscript is None:
        evalscript = build_evalscript("NDVI", masked=True)

    # Cache simple para evitar recálculos innecesarios
    import hashlib
    cache_key = hashlib.md5(f"{geometry_or_bbox}{start_date}{end_date}{past_years}{evalscript}".encode()).hexdigest()
    
    # Variable global para cache simple
    if not hasattr(compute_ndvi_anomaly, '_cache'):
        compute_ndvi_anomaly._cache = {}
    
    # Verificar cache (máximo 10 elementos para no consumir memoria)
    if cache_key in compute_ndvi_anomaly._cache:
        logger.info(f"✅ Anomalía encontrada en caché para {past_years}")
        return compute_ndvi_anomaly._cache[cache_key]
    
    # Limpiar cache si está lleno
    if len(compute_ndvi_anomaly._cache) > 10:
        compute_ndvi_anomaly._cache.clear()

    logger.info(f"🔄 Calculando anomalías vs {past_years}")

    def _shift_interval_to_year(s: str, e: str, year: int):
        from datetime import datetime as _dt
        import calendar
        ds, de = _dt.fromisoformat(s), _dt.fromisoformat(e)
        def _safe(d, y):
            mm, dd = d.month, d.day
            try:
                return _dt(y, mm, dd)
            except ValueError:
                last = calendar.monthrange(y, mm)[1]
                return _dt(y, mm, min(dd, last))
        return _safe(ds, year).date().isoformat(), _safe(de, year).date().isoformat()

    # 1) Composite actual
    current_array = None
    for attempt in range(max_retries):
        stack, _ = fetch_ndvi_stack_single(
            token=token,
            geometry_or_bbox=geometry_or_bbox,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=1024, height=1024,
            adaptive_resolution=True,
            max_cloud_coverage=60.0,
            mosaic_order="leastCC",
            target_m_per_px=10.0
        )
        if stack:
            current_array = stack[0].astype("float32")
            break
        # Fallback
        stack, _ = fetch_ndvi_stack_single(
            token=token,
            geometry_or_bbox=geometry_or_bbox,
            start_date=start_date,
            end_date=end_date,
            evalscript=evalscript,
            width=768, height=768,
            adaptive_resolution=True,
            max_cloud_coverage=80.0,
            mosaic_order="mostRecent",
            target_m_per_px=12.0
        )
        if stack:
            current_array = stack[0].astype("float32")
            break
    if current_array is None:
        raise ValueError("No se pudo obtener composite actual.")

    # 2) Referencia (mediana de años)
    ref_arrays = []
    for y in past_years:
        ys, ye = _shift_interval_to_year(start_date, end_date, int(y))
        ok = False
        for attempt in range(max_retries):
            st, _ = fetch_ndvi_stack_single(
                token=token,
                geometry_or_bbox=geometry_or_bbox,
                start_date=ys, end_date=ye,
                evalscript=evalscript,
                width=1024, height=1024,
                adaptive_resolution=True,
                max_cloud_coverage=60.0,
                mosaic_order="leastCC",
                target_m_per_px=10.0
            )
            if st:
                ref_arrays.append(st[0].astype("float32")); ok = True; break
            # Fallback
            st, _ = fetch_ndvi_stack_single(
                token=token,
                geometry_or_bbox=geometry_or_bbox,
                start_date=ys, end_date=ye,
                evalscript=evalscript,
                width=768, height=768,
                adaptive_resolution=True,
                max_cloud_coverage=80.0,
                mosaic_order="mostRecent",
                target_m_per_px=12.0
            )
            if st:
                ref_arrays.append(st[0].astype("float32")); ok = True; break
        if not ok:
            logger.warning(f"⚠️ Año {y} sin datos; se omite")

    if len(ref_arrays) == 0:
        raise ValueError("No se obtuvieron composites de referencia.")

    reference_median = np.nanmedian(np.stack(ref_arrays, axis=0), axis=0).astype("float32")

    # Asegurar shapes iguales
    h = min(reference_median.shape[0], current_array.shape[0])
    w = min(reference_median.shape[1], current_array.shape[1])
    reference_median = reference_median[:h, :w]
    current_array = current_array[:h, :w]

    anomaly_array = current_array - reference_median

    valid_mask = np.isfinite(anomaly_array)
    logger.info(f"📊 Anomalías válidas: {int(valid_mask.sum())}/{anomaly_array.size}")
    logger.info(f"📈 min={np.nanmin(anomaly_array):.3f}, max={np.nanmax(anomaly_array):.3f}, mean={np.nanmean(anomaly_array):.3f}")
    
    # Guardar en cache
    compute_ndvi_anomaly._cache[cache_key] = anomaly_array
    logger.info(f"💾 Anomalía guardada en caché para futuras consultas")
    
    return anomaly_array

# ------------------------------------------------------------------------------
# Overlays PNG (si usas tus colormaps)
# ------------------------------------------------------------------------------
def _create_colormap_from_stops(color_stops: list) -> matplotlib.colors.LinearSegmentedColormap:
    from matplotlib.colors import LinearSegmentedColormap
    values = [stop[0] for stop in color_stops]
    colors = [stop[1] for stop in color_stops]
    min_val, max_val = min(values), max(values)
    val_range = max_val - min_val
    if val_range == 0:
        normalized_values = [0.5] * len(values)
    else:
        normalized_values = [(v - min_val) / val_range for v in values]
    normalized_values[0] = 0.0
    normalized_values[-1] = 1.0
    segments = list(zip(normalized_values, colors))
    cmap = LinearSegmentedColormap.from_list('custom_ndvi', segments, N=256)
    cmap.set_bad((0, 0, 0, 0))
    return cmap

def _array_to_data_uri_safe(arr2d, vmin, vmax, cmap):
    try:
        import matplotlib.pyplot as plt
        plt.ioff()
        a = np.array(arr2d, dtype="float32")
        h, w = a.shape
        fig, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=100, facecolor='none')
        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        im = ax.imshow(a, vmin=vmin, vmax=vmax, cmap=cmap, interpolation="bilinear", aspect='equal')
        alpha_mask = np.where(np.isfinite(a), 0.9, 0.0)
        im.set_alpha(alpha_mask)
        bio = io.BytesIO()
        fig.savefig(bio, format="png", transparent=True, bbox_inches="tight", pad_inches=0, facecolor='none')
        plt.close(fig); plt.clf()
        bio.seek(0)
        encoded = base64.b64encode(bio.getvalue()).decode("ascii")
        bio.close()
        return "data:image/png;base64," + encoded
    except Exception as e:
        logger.error(f"❌ _array_to_data_uri_safe: {e}")
        return ""

def generate_ndvi_overlays_all_scales(
    ndvi_array: np.ndarray,
    bounds: list,
    vmin: float = -0.2,
    vmax: float = 0.9
) -> dict:
    """
    Genera overlays NDVI para todas las escalas de colores definidas en config_colormaps.
    """
    try:
        import config_colormaps as cfg
        overlays = {}
        for scale_name in cfg.NDVI_COLORMAPS_DEF.keys():
            try:
                if not cfg.validate_colormap_definition(scale_name):
                    logger.warning(f"⚠️ Escala inválida: {scale_name}")
                    continue
                cmap = _create_colormap_from_stops(cfg.NDVI_COLORMAPS_DEF[scale_name])
                data_uri = _array_to_data_uri_safe(ndvi_array, vmin, vmax, cmap)
                overlays[scale_name] = data_uri
                logger.info(f"✅ Overlay generado: {scale_name}")
            except Exception as e:
                logger.error(f"❌ Error overlay {scale_name}: {e}")
                overlays[scale_name] = None
        return overlays
    except Exception as e:
        logger.error(f"❌ generate_ndvi_overlays_all_scales: {e}")
        return {}
