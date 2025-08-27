"""
Callbacks específicos del layout de datos satelitales
Maneja NDVI, anomalías, overlays PNG, análisis temporal y calidad de imagen

Autor: German Jose Padua Pleguezuelo
Universidad de Granada
Master en Ciencia de Datos

Fichero: src.callbacks_refactored.datos_satelitales.py
"""

import os
import logging
import time
import traceback
import hashlib
import json
import pickle
import io
import base64
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
from datetime import datetime, timedelta

# Configure matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid GUI issues


# Imports de terceros
try:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from dash import callback, Input, Output, State, html, dcc, no_update, callback_context
    import dash_bootstrap_components as dbc
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
except ImportError as e:
    logging.error(f"❌ Error importando dependencias: {e}")
    logging.warning("⚠️ Algunas librerías no disponibles, usando mocks para desarrollo")

# Imports locales
from src.utils.satellite_utils import (
    get_access_token,
    compute_ndvi_anomaly,
    compute_index_composite,
    build_evalscript,
    fetch_ndvi_stack_single
)

# Importar la configuración de los colormaps
import config_colormaps as cfg
from src.utils.finca_store import list_fincas

# Importar funciones helper
from src.callbacks_refactored.datos_satelitales_helpers import (
    _bounds_from_geometry,
    _outer_ring,
    _build_time_slices,
    _create_ndvi_legend,
    _create_anomaly_legend,
    _generate_kpi_cards_generic,
    _generate_charts_generic,
    _create_farmer_kpi_cards,
    _create_farmer_charts,
    create_farmer_historical_charts,
    _kpi_card,
    _array_to_png_bytes,
    _visual_params_for,
    _pixel_size_from_ring_mercator_strict,
    _fetch_window_resilient_generic,
    _create_cmap_from_def,
    _compute_inside_mask_from_ring,
    _array_to_data_uri_safe,
    _get_plotly_theme,
    _graph,
    _GRID,
    _slugify,
    _cache_key,
    _cache_path,
    cache_get,
    cache_set,
    CACHE_DIR
)

# Imports adicionales para nuevas funcionalidades
from src.components.ui_components_improved import create_metric_card
from src.utils.satellite_visualization import (
    create_professional_kpi_cards,
    create_enhanced_histogram_chart,
    create_comparative_analysis_chart,
    create_health_assessment_card,
    create_anomaly_analysis_chart
)
from src.utils.temporal_analysis import (
    create_temporal_trend_analysis,
    create_advanced_temporal_chart,
    create_trend_summary_card,
    detect_seasonal_patterns,
    create_seasonal_analysis_chart
)
from src.utils.temporal_comparison import (
    create_comparison_kpis,
    create_comparison_scatter_chart,
    create_comparison_summary_chart,
    create_health_classification_chart,
    create_change_analysis_chart,
    create_difference_chart,
    create_distribution_comparison_chart,
    create_comparison_stats_table
)

logger = logging.getLogger(__name__)



def register_callbacks(app):
    """
    Registra todos los callbacks relacionados con análisis de datos satelitales.
    
    Esta función configura los siguientes grupos de callbacks:
    1. Control de interfaz (botones avanzados, años de referencia)
    2. Análisis satelital principal (NDVI, OSAVI, NDRE con caché)
    3. Generación y actualización de overlays PNG para mapas
    4. Visualización de KPIs y gráficas
    5. Análisis temporal histórico
    6. Generación de animaciones temporales
    7. Comparación temporal entre períodos
    
    Args:
        app: Instancia de la aplicación Dash donde registrar los callbacks
    """
    logger.info("🔄 Registrando callbacks de análisis satelital...")

    from dash import callback_context
    
    # =====================================================================
    # SECCIÓN 1: CALLBACKS DE CONTROL DE INTERFAZ
    # =====================================================================
    
    # Callback para mostrar/ocultar opciones avanzadas
    @app.callback(
        [Output("advanced-controls-collapse", "is_open"),
         Output("toggle-advanced-btn", "children")],
        Input("toggle-advanced-btn", "n_clicks"),
        State("advanced-controls-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_advanced_controls(n_clicks, is_open):
        if is_open:
            return False, [html.I(className="fas fa-chevron-down me-2"), "Mostrar Opciones Avanzadas"]
        else:
            return True, [html.I(className="fas fa-chevron-up me-2"), "Ocultar Opciones Avanzadas"]

    # Gestión de años de referencia - Paso 1: Renderizar opciones desde el store
    @app.callback(
        Output("reference-years-list", "options"),
        Input("reference-years-store", "data")
    )
    def render_reference_years_options(years):
        years = sorted({int(y) for y in (years or [])}, reverse=True)
        return [{"label": str(y), "value": y} for y in years]


    # Gestión de años de referencia - Paso 2: Actualizar store con años seleccionados
    @app.callback(
        [Output("reference-years-store", "data"),
        Output("reference-years-list", "value")],
        [Input("add-reference-year-btn", "n_clicks"),
        Input("reference-years-list", "value")],
        [State("reference-year-input", "value"),
        State("reference-years-store", "data"),
        State("reference-years-list", "value")],
        prevent_initial_call=True
    )
    def update_reference_years(n_add, checklist_value, year_input, current_years, current_checked):
        from dash import no_update
        from datetime import datetime

        # Fuente de verdad por defecto (por si el store viene vacío)
        default_years = [2024, 2023, 2022]
        current_years = list(current_years or default_years)
        current_checked = list(current_checked or default_years)

        trig = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None

        # Caso A: pulsado "Añadir" → validamos y añadimos al Store y lo marcamos en la checklist
        if trig == "add-reference-year-btn":
            if year_input is None:
                return no_update, no_update
            try:
                y = int(year_input)
            except:
                return no_update, no_update
            y_min, y_max = 2015, datetime.now().year
            if y < y_min or y > y_max:
                return no_update, no_update

            new_store   = sorted({*current_years, y}, reverse=True)
            new_checked = sorted({*current_checked, y}, reverse=True)
            return new_store, new_checked

        # Caso B: el usuario marca/desmarca en la checklist → el Store pasa a ser EXACTAMENTE lo seleccionado
        if trig == "reference-years-list":
            years = sorted({int(v) for v in (checklist_value or [])}, reverse=True)
            # devolvemos también el mismo 'value' para no modificar la selección del usuario
            return years, checklist_value

        return no_update, no_update
    
    # =====================================================================
    # SECCIÓN 2: ANÁLISIS SATELITAL PRINCIPAL
    # =====================================================================
    # Callback principal: ejecuta análisis de índices satelitales con caché optimizado
    @app.callback(
        [
            Output("raw-ndvi-data-store", "data"),
            Output("overlay-bounds", "data"),
        ],
        Input("run-analysis-btn", "n_clicks"),
        [
            State("analysis-mode-selector", "value"),
            State("selected-geometry", "data"),
            State("ndvi-date-range", "start_date"),
            State("ndvi-date-range", "end_date"),
            State("reference-years-store", "data"),
            State("index-checklist", "value"),
        ],
        prevent_initial_call=True
    )
    def run_analysis(n_clicks, selected_mode, drawn_feature, start_date, end_date, reference_years, index_list):
        """
        Análisis unificado:
        - Calcula uno o varios índices (NDVI/OSAVI/NDRE) según checklist.
        - Usa caché por finca (npy) y, si no hay HIT, usa _fetch_window_resilient_generic
            (que a su vez cachea por ventana .npz). Así evitamos consultas repetidas.
        - Si hay años de referencia, calcula anomalía NDVI.
        """
        if not n_clicks:
            return no_update, no_update

        import os, base64, pickle, hashlib, json, traceback
        from pathlib import Path
        import numpy as np

        # ===== Configuración de caché =====

        # ===== Log de cabecera =====
        logger.info("=" * 72)
        logger.info("🚀 ANÁLISIS SATELITAL AVANZADO (con caché de finca y de ventana)")
        logger.info(f"   🎯 Modo: {selected_mode} | 📅 {start_date} → {end_date} | 🧮 Índices: {index_list}")
        logger.info(f"   📊 Años referencia: {reference_years}")
        logger.info("=" * 72)

        # ===== 1) Geometría objetivo =====
        geom, farm_name = None, "Área dibujada"
        try:
            if selected_mode and selected_mode != "temporal":
                selected_farm = next((f for f in (list_fincas() or []) if str(f.get("id")) == str(selected_mode)), None)
                if selected_farm:
                    geom = selected_farm.get("geometry")
                    farm_name = selected_farm.get("properties", {}).get("name", f"finca-{selected_mode}")
                    logger.info(f"Usando geometría de la finca: '{farm_name}'")
            elif drawn_feature and drawn_feature.get("geometry"):
                geom = drawn_feature["geometry"]
                logger.info("Usando geometría dibujada en el mapa (store)")
        except Exception as e:
            logger.error(f"Error obteniendo geometría seleccionada: {e}")
            return no_update, no_update

        if not geom:
            logger.warning("No hay geometría válida. Selecciona una finca o dibuja un polígono.")
            return no_update, no_update

        # ===== 2) Bounds / ring =====
        try:
            bounds = _bounds_from_geometry(geom)
            ring = _outer_ring(geom)
            if not ring or not bounds:
                logger.error("Geometría inválida (sin anillo o sin bounds).")
                return no_update, no_update
        except Exception as e:
            logger.error(f"Error procesando geometría: {e}")
            return no_update, no_update

        # ===== 3) Token =====
        cid, csec = os.getenv("COPERNICUS_CLIENT_ID"), os.getenv("COPERNICUS_CLIENT_SECRET")
        if not cid or not csec:
            logger.error("Credenciales de Copernicus no configuradas en .env")
            return no_update, no_update
        try:
            token = get_access_token(cid, csec)
        except Exception as e:
            logger.error(f"Error autenticando contra Copernicus: {e}")
            return no_update, no_update

        # ===== 4) Índices solicitados =====
        masked = True
        include_water = False
        indices = [i.upper() for i in (index_list or ["NDVI"])]

        # Resolución/size base (se puede refinar por área; aquí mantenemos fijo y dejamos a la función resiliente ajustar si hace falta)
        base_w, base_h = 1024, 1024

        # ===== AQUÍ ES DONDE REALMENTE SE INICIA EL PROCESAMIENTO =====
        # Todas las validaciones han pasado, ahora sí activamos el estado busy
        logger.info("🔄 Iniciando procesamiento satelital...")

        arrays_by_index = {}
        try:
            for idx in indices:
                arr = None
                used_win = None
                attempt_id = None

                # 4.a) Probar caché por FINCA (solo si no es "temporal")
                cache_key = None
                if selected_mode and selected_mode != "temporal":
                    cache_key = _cache_key(farm_name, idx, start_date, end_date, masked=True)
                    arr = cache_get(cache_key)
                    if arr is not None and np.isfinite(arr).any():
                        logger.info(f"[farm-cache] HIT {cache_key}.npy")
                        used_win = (start_date, end_date)  # semánticamente el rango pedido
                        attempt_id = 0  # marca de HIT desde caché de finca

                # 4.b) Si no hay HIT, usar la función resiliente con CACHÉ POR VENTANA
                if arr is None:
                    evalscript = build_evalscript(idx, masked=masked, include_water=include_water)
                    arr, used_win, attempt_id = _fetch_window_resilient_generic(
                        token=token,
                        ring=ring,
                        s0_iso=start_date,
                        s1_iso=end_date,
                        evalscript=evalscript,
                        index_type=idx,
                        width=base_w,
                        height=base_h,
                    )

                    # Si obtuvimos array y es finca → guardamos también en caché de FINCA (composite del intervalo)
                    if arr is not None and cache_key:
                        cache_set(cache_key, arr)

                # 4.c) Serializar si hay datos
                if arr is not None and np.isfinite(arr).any():
                    arrays_by_index[idx] = {
                        "array": base64.b64encode(
                            pickle.dumps(np.array(arr, dtype="float32"), protocol=pickle.HIGHEST_PROTOCOL)
                        ).decode("ascii"),
                        "shape": list(np.array(arr).shape),
                        "range": [float(np.nanmin(arr)), float(np.nanmax(arr))],
                        # metadatos útiles para UI/inspección:
                        "used_window": list(used_win) if used_win else [start_date, end_date],
                        "attempt": int(attempt_id) if attempt_id is not None else None,
                    }
                else:
                    logger.info(f"Índice {idx}: sin datos válidos en el periodo solicitado")

        except Exception as e:
            logger.error(f"Fallo calculando índices: {e}\n{traceback.format_exc()}")
            return no_update, no_update

        if len(arrays_by_index) == 0:
            logger.info("No hay ningún índice con datos válidos → nada que mostrar.")
            return no_update, no_update

        # ===== 5) Anomalía NDVI (solo si hay años de referencia) =====
        anomaly_b64 = None
        years_list = [int(y) for y in (reference_years or []) if str(y).isdigit()]
        if len(years_list) > 0 and "NDVI" in arrays_by_index:
            try:
                anomaly_array = compute_ndvi_anomaly(
                    token=token,
                    geometry_or_bbox=ring,
                    start_date=start_date,
                    end_date=end_date,
                    past_years=years_list,
                    evalscript=build_evalscript("NDVI", masked=True),
                    max_retries=2
                )
                if anomaly_array is not None and np.isfinite(anomaly_array).any():
                    anomaly_b64 = base64.b64encode(
                        pickle.dumps(np.array(anomaly_array, dtype="float32"), protocol=pickle.HIGHEST_PROTOCOL)
                    ).decode("ascii")
            except ValueError as ve:
                logger.warning(f"Anomalía NDVI omitida (sin referencia suficiente): {ve}")
            except Exception as e:
                logger.error(f"Error calculando anomalía NDVI: {e}")

        # ===== 6) Store =====
        try:
            store_data = {"indices": arrays_by_index}
            if anomaly_b64 is not None:
                store_data["anomaly"] = anomaly_b64
            logger.info("✅ Datos preparados (store) + bounds para overlays")
            return store_data, bounds
        except Exception as e:
            logger.error(f"Error serializando resultados: {e}")
            return no_update, no_update


    # =====================================================================
    # SECCIÓN 3: GENERACIÓN Y ACTUALIZACIÓN DE OVERLAYS PARA MAPAS
    # =====================================================================
    
    # Callback para generar overlays PNG de índices satelitales
    @app.callback(
        [
            Output("dynamic-ndvi-overlay", "url"),
            Output("dynamic-osavi-overlay", "url"),
            Output("dynamic-ndre-overlay", "url"),
            Output("anomaly-ndvi-overlay", "url"),
        ],
        [
            Input("raw-ndvi-data-store", "data"),
            Input("ndvi-colormap-selector", "value"),
        ],
        prevent_initial_call=True
    )
    def update_overlays(stored_data, cmap_name):
        if not stored_data or not cmap_name:
            logger.warning("⚠️ update_overlays: No stored_data o cmap_name")
            return no_update, no_update, no_update, no_update

        decode = lambda b64: pickle.loads(base64.b64decode(b64))
        indices = stored_data.get("indices", {})
        logger.info(f"🎨 Generando overlays con colormap '{cmap_name}' para índices: {list(indices.keys())}")

        ndvi_url = osavi_url = ndre_url = anomaly_url = ""

        if "NDVI" in indices:
            try:
                arr = decode(indices["NDVI"]["array"])
                vmin, vmax, cmap, alpha = _visual_params_for("NDVI", cmap_name)
                logger.info(f"📊 NDVI: array shape={arr.shape}, vmin={vmin}, vmax={vmax}, alpha={alpha}")
                ndvi_url = _array_to_data_uri_safe(arr, vmin=vmin, vmax=vmax, cmap=cmap, alpha=alpha)
                if ndvi_url:
                    logger.info(f"✅ NDVI overlay generado exitosamente (URL len: {len(ndvi_url)})")
                else:
                    logger.error("❌ NDVI overlay vacío")
            except Exception as e:
                logger.error(f"❌ Error generando overlay NDVI: {e}")

        if "OSAVI" in indices:
            try:
                arr = decode(indices["OSAVI"]["array"])
                vmin, vmax, cmap, alpha = _visual_params_for("OSAVI", cmap_name)
                logger.info(f"📊 OSAVI: array shape={arr.shape}, vmin={vmin}, vmax={vmax}, alpha={alpha}")
                osavi_url = _array_to_data_uri_safe(arr, vmin=vmin, vmax=vmax, cmap=cmap, alpha=alpha)
                if osavi_url:
                    logger.info(f"✅ OSAVI overlay generado exitosamente (URL len: {len(osavi_url)})")
                else:
                    logger.error("❌ OSAVI overlay vacío")
            except Exception as e:
                logger.error(f"❌ Error generando overlay OSAVI: {e}")

        if "NDRE" in indices:
            try:
                arr = decode(indices["NDRE"]["array"])
                vmin, vmax, cmap, alpha = _visual_params_for("NDRE", cmap_name)
                logger.info(f"📊 NDRE: array shape={arr.shape}, vmin={vmin}, vmax={vmax}, alpha={alpha}")
                ndre_url = _array_to_data_uri_safe(arr, vmin=vmin, vmax=vmax, cmap=cmap, alpha=alpha)
                if ndre_url:
                    logger.info(f"✅ NDRE overlay generado exitosamente (URL len: {len(ndre_url)})")
                else:
                    logger.error("❌ NDRE overlay vacío")
            except Exception as e:
                logger.error(f"❌ Error generando overlay NDRE: {e}")

        if "anomaly" in stored_data:
            try:
                arr = decode(stored_data["anomaly"])
                vmin, vmax, cmap, alpha = _visual_params_for("ANOMALY", cmap_name)
                logger.info(f"📊 ANOMALY: array shape={arr.shape}, vmin={vmin}, vmax={vmax}, alpha={alpha}")
                anomaly_url = _array_to_data_uri_safe(arr, vmin=vmin, vmax=vmax, cmap=cmap, alpha=alpha)
                if anomaly_url:
                    logger.info(f"✅ Anomaly overlay generado exitosamente (URL len: {len(anomaly_url)})")
                else:
                    logger.error("❌ Anomaly overlay vacío")
            except Exception as e:
                logger.error(f"❌ Error generando overlay anomaly: {e}")

        logger.info(f"🎨 Overlays finalizados - URLs generadas: NDVI={len(ndvi_url)>0}, OSAVI={len(osavi_url)>0}, NDRE={len(ndre_url)>0}, Anomaly={len(anomaly_url)>0}")
        return ndvi_url, osavi_url, ndre_url, anomaly_url
        
    # Callback para actualizar los bounds de los overlays
    @app.callback(
        [
            Output("dynamic-ndvi-overlay", "bounds"),
            Output("dynamic-osavi-overlay", "bounds"),
            Output("dynamic-ndre-overlay", "bounds"),
            Output("anomaly-ndvi-overlay", "bounds"),
        ],
        Input("overlay-bounds", "data"),
        prevent_initial_call=True
    )
    def update_overlay_bounds(bounds_data):
        if not bounds_data:
            return no_update, no_update, no_update, no_update
        return bounds_data, bounds_data, bounds_data, bounds_data

    # Callback para controlar la opacidad de los overlays según disponibilidad de datos
    @app.callback(
        [
            Output("dynamic-ndvi-overlay", "opacity"),
            Output("dynamic-osavi-overlay", "opacity"),
            Output("dynamic-ndre-overlay", "opacity"),
            Output("anomaly-ndvi-overlay", "opacity"),
        ],
        [
            Input("dynamic-ndvi-overlay", "url"),
            Input("dynamic-osavi-overlay", "url"),
            Input("dynamic-ndre-overlay", "url"),
            Input("anomaly-ndvi-overlay", "url"),
        ],
        prevent_initial_call=True
    )
    def update_overlay_opacity(ndvi_url, osavi_url, ndre_url, anomaly_url):
        """Actualiza la opacidad de los overlays: visible si tiene URL, invisible si no"""
        ndvi_opacity = 0.7 if ndvi_url and ndvi_url != "" else 0
        osavi_opacity = 0.7 if osavi_url and osavi_url != "" else 0
        ndre_opacity = 0.7 if ndre_url and ndre_url != "" else 0
        anomaly_opacity = 0.7 if anomaly_url and anomaly_url != "" else 0
        
        logger.info(f"🎨 Opacidades actualizadas - NDVI: {ndvi_opacity}, OSAVI: {osavi_opacity}, NDRE: {ndre_opacity}, Anomalía: {anomaly_opacity}")
        return ndvi_opacity, osavi_opacity, ndre_opacity, anomaly_opacity


    @app.callback(
        [Output("ndvi-legend", "children"),
        Output("anomaly-legend", "children")],
        [Input("raw-ndvi-data-store", "data"),
        Input("analysis-index-selector", "value")],
        prevent_initial_call=True
    )
    def update_legends(stored_data, idx_selected):
        """
        Muestra la leyenda del índice visualizado (NDVI/OSAVI/NDRE usa la misma escala base)
        y la leyenda de anomalía sólo si hay anomalía y NDVI está disponible.
        """
        if not stored_data:
            return None, None

        indices = stored_data.get("indices", {})
        # índice elegido o fallback a NDVI si existe
        idx = (idx_selected or "NDVI").upper()
        if idx not in indices:
            idx = "NDVI" if "NDVI" in indices else None

        ndvi_legend = _create_ndvi_legend() if idx else None
        anomaly_legend = _create_anomaly_legend() if ("anomaly" in stored_data and "NDVI" in indices) else None
        return ndvi_legend, anomaly_legend

    # Callback simplificado - ya no necesitamos control manual de visibilidad
    # La visibilidad se controla desde los overlays del mapa

    @app.callback(
        Output("selected-geometry", "data"),
        Input("bbox-draw-control", "geojson"),
        prevent_initial_call=True
    )
    def capture_drawn_geometry(geojson_data):
        """Captura geometrías dibujadas en el mapa para análisis temporal"""
        if not geojson_data or not geojson_data.get("features"):
            return None
            
        try:
            # Tomar la última feature dibujada
            features = geojson_data["features"]
            if features:
                last_feature = features[-1]
                logger.info(f"Geometría capturada: {last_feature.get('geometry', {}).get('type')}")
                return last_feature
        except Exception as e:
            logger.error(f"Error capturando geometría: {e}")
            
        return None

    # =====================================================================
    # SECCIÓN 4: VISUALIZACIÓN DE KPIS Y GRÁFICAS
    # =====================================================================
    
    # Callback para generar KPIs y gráficas a partir de datos satelitales
    @app.callback(
        [
            Output("kpi-cards-container", "children"),
            Output("kpi-charts-container", "children"), 
            Output("kpi-section", "style"),
            Output("charts-section", "style")
        ],
        [
            Input("raw-ndvi-data-store", "data"),
            Input("analysis-index-selector", "value"),   
        ],
        prevent_initial_call=True
    )
    def render_kpis_and_charts(stored_data, analysis_idx):
        """
        Genera KPIs y gráficas orientados a agricultores a partir de los datos satelitales.
        
        Prioriza las visualizaciones especializadas para agricultores con lenguaje simple
        y consejos prácticos sobre el estado del cultivo.
        """
        if not stored_data:
            return [], [], {"display": "none"}, {"display": "none"}

        indices = stored_data.get("indices", {})
        
        if not indices:
            return [], [], {"display": "none"}, {"display": "none"}

        try:
            logger.info("🎨 Generando visualizaciones orientadas a agricultores...")
            
            # Determinar índice principal para análisis
            main_index = analysis_idx if analysis_idx and analysis_idx in indices else "NDVI"
            if main_index not in indices and indices:
                main_index = list(indices.keys())[0]  # Tomar el primer índice disponible
            
            # Decodificar datos del índice principal
            decode = lambda b: pickle.loads(base64.b64decode(b))
            main_array = decode(indices[main_index]["array"])
            
            # Decodificar anomalía si está disponible
            anomaly_array = None
            if "anomaly" in stored_data and main_index == "NDVI":
                try:
                    anomaly_array = decode(stored_data["anomaly"])
                    logger.info("✅ Datos de anomalía disponibles para análisis")
                except Exception as e:
                    logger.warning(f"⚠️ Error decodificando anomalía: {e}")
            
            # Usar funciones especializadas para agricultores
            logger.info(f"🌱 Generando KPIs para agricultores usando {main_index}")
            farmer_kpi_cards = _create_farmer_kpi_cards(main_array, anomaly_array, main_index)
            
            logger.info(f"📊 Generando gráficos para agricultores usando {main_index}")
            farmer_charts = _create_farmer_charts(main_array, anomaly_array, main_index)
            
            logger.info("✅ Visualizaciones para agricultores generadas exitosamente")
            return farmer_kpi_cards, farmer_charts, {"display":"block"}, {"display":"block"}
            
        except Exception as e:
            logger.error(f"❌ Error generando visualizaciones para agricultores: {e}")
            logger.info("🔄 Usando visualizaciones de respaldo...")
            
            # Fallback a funciones genéricas originales
            try:
                decode = lambda b: pickle.loads(base64.b64decode(b))
                arr = None
                if analysis_idx and analysis_idx in indices:
                    arr = decode(indices[analysis_idx]["array"])
                elif "NDVI" in indices:
                    analysis_idx = "NDVI"
                    arr = decode(indices["NDVI"]["array"])

                anomaly = pickle.loads(base64.b64decode(stored_data["anomaly"])) if "anomaly" in stored_data and analysis_idx=="NDVI" else None
                if arr is None:
                    logger.warning("⚠️ No hay datos válidos para visualización de respaldo")
                    return [], [], {"display": "none"}, {"display": "none"}

                # Umbrales por índice optimizados para cultivos mediterráneos
                THRESH = {
                    "NDVI": {"lo": 0.30, "hi": 0.60},
                    "OSAVI": {"lo": 0.25, "hi": 0.55},
                    "NDRE": {"lo": 0.20, "hi": 0.40},
                }.get(analysis_idx, {"lo": 0.30, "hi": 0.60})

                logger.info(f"🔄 Usando visualización genérica para {analysis_idx}")
                kpi_cards = _generate_kpi_cards_generic(arr, anomaly, lo=THRESH["lo"], hi=THRESH["hi"], label_idx=analysis_idx)
                charts = _generate_charts_generic(arr, anomaly, label_idx=analysis_idx)
                return kpi_cards, charts, {"display":"block"}, {"display":"block"}
                
            except Exception as fallback_e:
                logger.error(f"❌ Error crítico en visualización de respaldo: {fallback_e}")
                error_msg = dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error generando análisis: {str(e)}"
                ], color="danger")
                return [error_msg], [], {"display":"block"}, {"display":"none"}


    # =====================================================================
    # SECCIÓN 5: ANÁLISIS TEMPORAL HISTÓRICO
    # =====================================================================
    


    # Callback principal para cálculo de datos históricos temporales
    @app.callback(
        [
            Output("historical-data-store", "data"),
            Output("historical-kpi-cards", "children"),
            Output("historical-charts-container", "children"),
            Output("historical-controls-help", "children"),
        ],
        Input("compute-historical-btn", "n_clicks"),
        [
            State("analysis-mode-selector", "value"),
            State("selected-geometry", "data"),
            State("historical-frequency", "value"),
            State("historical-date-range", "start_date"),
            State("historical-date-range", "end_date"),
            State("reference-years-store", "data"),
            State("analysis-index-selector", "value")
        ],
        prevent_initial_call=True
    )
    def compute_historical(n_clicks, selected_mode, drawn_feature,
                           freq, start_date, end_date, ref_years, analysis_idx):
        if not n_clicks:
            return no_update, no_update, no_update, no_update

        idx = (analysis_idx or "NDVI").upper()
        evalscript = build_evalscript(idx, masked=True)

        # --- Geometría objetivo (igual que en run_analysis) ---
        geom, farm_name = None, "Área dibujada"
        if selected_mode and selected_mode != "temporal":
            selected_farm = next((f for f in (list_fincas() or []) if str(f.get("id")) == str(selected_mode)), None)
            if selected_farm:
                geom = selected_farm.get("geometry")
                farm_name = selected_farm.get("properties", {}).get("name", "Finca sin nombre")
        elif drawn_feature and drawn_feature.get("geometry"):
            geom = drawn_feature["geometry"]

        if not geom:
            msg = dbc.Alert("Selecciona una finca o dibuja un polígono en el mapa.", color="warning")
            return None, msg, [], "Sin geometría."

        try:
            bounds = _bounds_from_geometry(geom)
            ring = _outer_ring(geom)
            if not ring or not bounds:
                return None, dbc.Alert("Error: Geometría inválida.", color="danger"), [], "Geometría inválida"
        except Exception as e:
            return None, dbc.Alert(f"Error en geometría: {e}", color="danger"), [], "Error en geometría"

        # --- Credenciales Copernicus ---
        cid, csec = os.getenv("COPERNICUS_CLIENT_ID"), os.getenv("COPERNICUS_CLIENT_SECRET")
        if not cid or not csec:
            msg = dbc.Alert("Credenciales de Copernicus no configuradas en .env.", color="danger")
            return None, msg, [], "Faltan credenciales"
        try:
            token = get_access_token(cid, csec)
        except Exception as e:
            return None, dbc.Alert(f"Error de autenticación: {e}", color="danger"), [], "Auth error"

        # --- Slices temporales ---
        slices = _build_time_slices(start_date, end_date, freq or "monthly")
        if not slices:
            return None, dbc.Alert("Rango de fechas no válido.", color="warning"), [], "Rango vacío"

        # --- Ajustes / umbrales KPIs ---
        lo, hi = 0.3, 0.6

        rows = []
        ok_windows = 0
        for s0, s1 in slices:
            try:
                # NDVI del intervalo (mosaico); resol. menor para agilidad
                arr, used_window, attempt_id = _fetch_window_resilient_generic(
                    token, ring, s0, s1, evalscript=evalscript, width=384, height=384, index_type="NDVI"
                )

                if arr is None:
                    # sin datos incluso tras expandir: marcamos ventana no válida
                    rows.append({"start": s0, "end": s1})
                    continue

                v = arr[np.isfinite(arr)]
                if v.size == 0:
                    rows.append({"start": s0, "end": s1})
                    continue

                used_s0, used_s1 = used_window

                ndvi_mean = float(np.mean(v))
                healthy_pct = float((v >= hi).sum()) * 100.0 / float(v.size)
                stress_pct  = float((v <  lo).sum()) * 100.0 / float(v.size)

                item = {
                    "start": s0, "end": s1,
                    "ndvi_mean": ndvi_mean,
                    "healthy_pct": healthy_pct,
                    "stress_pct":  stress_pct,
                    "used_start": used_s0,
                    "used_end": used_s1,
                    "attempt": attempt_id,
                }

                rows.append(item)
                ok_windows += 1

            except Exception as e:
                logger.warning(f"[Histórico] ventana {s0}..{s1} sin datos o con error: {e}")
                rows.append({"start": s0, "end": s1})

        # --- DataFrame con resultados ---
        df = pd.DataFrame(rows)
        if df.empty or df["ndvi_mean"].dropna().empty:
            msg = dbc.Alert("No se obtuvieron datos suficientes para el histórico.", color="info")
            help_txt = f"Ventanas: {len(slices)} · Válidas: 0"
            return None, msg, [], help_txt

        # fecha representativa (centro de la ventana) para el eje X
        df["t0"] = pd.to_datetime(df["start"])
        df["t1"] = pd.to_datetime(df["end"])
        df["date"] = df["t0"] + (df["t1"] - df["t0"]) / 2

        # --- KPIs históricos (última ventana válida) ---
        last = df.dropna(subset=["ndvi_mean"]).sort_values("date").iloc[-1]
        kpi_cards = dbc.Row([
            _kpi_card("NDVI medio (último)", f"{last['ndvi_mean']:.3f}", f"{last['start']} → {last['end']}", "fa-leaf", "success"),
            _kpi_card("Saludable (último)", f"{last.get('healthy_pct', 0):.1f}%", "por superficie", "fa-seedling", "success"),
            _kpi_card("Estrés (último)", f"{last.get('stress_pct', 0):.1f}%", "por superficie", "fa-triangle-exclamation", "danger"),
        ], className="g-3")

        if "anom_mean" in df.columns and df["anom_mean"].notna().any():
            last_an = df.dropna(subset=["anom_mean"]).sort_values("date").iloc[-1]
            kpi_cards = html.Div([
                kpi_cards,
                dbc.Row([
                    _kpi_card("ΔNDVI medio (último)", f"{last_an['anom_mean']:+.3f}", f"{last_an['start']} → {last_an['end']}", "fa-chart-line", "primary"),
                ], className="g-3"),
            ])

        # --- Análisis simplificado para agricultores ---
        try:
            logger.info("🌱 Generando análisis histórico simplificado para agricultores")
            # Usar df que ya tiene los datos válidos
            df_valid = df.dropna(subset=["ndvi_mean"])
            charts = create_farmer_historical_charts(df_valid, idx)
            
        except Exception as e:
            logger.error(f"❌ Error creando gráficos para agricultores: {e}")
            # Fallback mínimo
            charts = [dbc.Alert("No se pudieron generar gráficos de evolución", color="warning")]

        # --- Store serializado ---
        hist_payload = {
            "freq": freq,
            "start": start_date, "end": end_date,
            "rows": df[["start","end","date","ndvi_mean","healthy_pct","stress_pct"]] \
                        .assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d")) \
                        .to_dict(orient="records")
        }
        store_data = base64.b64encode(pickle.dumps(hist_payload, protocol=pickle.HIGHEST_PROTOCOL)).decode("ascii")

        expanded = sum(int(r.get("attempt", 1) > 1) for r in rows if "attempt" in r)
        help_txt = f"Ventanas: {len(slices)} · Válidas: {ok_windows} · Expandidas: {expanded} · Frecuencia: {'Mensual' if freq=='monthly' else 'Quincenal'}"
        return store_data, kpi_cards, charts, help_txt

    # =====================================================================
    # SECCIÓN 6: GENERACIÓN DE ANIMACIONES TEMPORALES
    # =====================================================================
    
    # Callback para generar animación temporal de índices satelitales
    @app.callback(
        [
            Output("historical-ndvi-animation", "children"),
            Output("anim-helper-text", "children"),
            Output("anim-frames-store", "data"),
            Output("anim-slider", "max"),
            Output("anim-slider", "marks"),
        ],
        Input("generate-ndvi-animation-btn", "n_clicks"),
        [
            State("analysis-mode-selector", "value"),
            State("selected-geometry", "data"),
            State("historical-frequency", "value"),
            State("historical-date-range", "start_date"),
            State("historical-date-range", "end_date"),
            State("ndvi-colormap-selector", "value"),
            State("analysis-index-selector", "value"),
        ],
        prevent_initial_call=True
    )
    def generate_ndvi_animation(n_clicks, selected_mode, drawn_feature,
                                freq, start_date, end_date, cmap_name, analysis_index):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update

        import os, base64
        import numpy as np
        import pandas as pd
        import dash_bootstrap_components as dbc
        from matplotlib.colors import Normalize
        import math

        idx = (analysis_index or "NDVI").upper()
        evalscript = build_evalscript(idx, masked=True)

        # --- Geometría ---
        geom = None
        if selected_mode and selected_mode != "temporal":
            selected_farm = next((f for f in (list_fincas() or []) if str(f.get("id")) == str(selected_mode)), None)
            if selected_farm:
                geom = selected_farm.get("geometry")
        elif drawn_feature and drawn_feature.get("geometry"):
            geom = drawn_feature["geometry"]

        if not geom:
            warn = dbc.Alert("Selecciona una finca o dibuja un polígono.", color="warning")
            return warn, "Sin geometría.", None, 0, {}

        try:
            ring = _outer_ring(geom)
            if not ring:
                err = dbc.Alert("Geometría inválida.", color="danger")
                return err, "Geometría inválida.", None, 0, {}
        except Exception as e:
            err = dbc.Alert(f"Error en geometría: {e}", color="danger")
            return err, "Error en geometría.", None, 0, {}

        # --- Token ---
        cid, csec = os.getenv("COPERNICUS_CLIENT_ID"), os.getenv("COPERNICUS_CLIENT_SECRET")
        if not cid or not csec:
            err = dbc.Alert("Faltan credenciales Copernicus en .env.", color="danger")
            return err, "Faltan credenciales.", None, 0, {}
        try:
            token = get_access_token(cid, csec)
        except Exception as e:
            err = dbc.Alert(f"Error de autenticación: {e}", color="danger")
            return err, "Auth error.", None, 0, {}

        # --- Ventanas temporales ---
        slices = _build_time_slices(start_date, end_date, freq or "monthly")
        if not slices:
            warn = dbc.Alert("Rango histórico vacío.", color="warning")
            return warn, "Rango vacío.", None, 0, {}

        # === TAMAÑO DEL LIENZO (Mercator estricto) ===
        width_px, height_px = _pixel_size_from_ring_mercator_strict(ring, long_side_px=512, max_side_px=2048)
        canvas_ratio = float(width_px) / float(height_px)
        logger.info(f"[anim] canvas size = {width_px}x{height_px} (ratio {canvas_ratio:.6f})")

        # Log del ratio Mercator calculado “a mano” (por si quieres comparar)
        R = 6378137.0
        def _mx(lon_deg): return R * math.radians(lon_deg)
        def _my(lat_deg):
            lat = max(min(lat_deg, 89.5), -89.5)
            rad = math.radians(lat)
            return R * math.log(math.tan(math.pi/4.0 + rad/2.0))
        lats = [p[1] for p in ring]; lons = [p[0] for p in ring]
        dx = abs(_mx(max(lons)) - _mx(min(lons)))
        dy = abs(_my(max(lats)) - _my(min(lats))) or 1e-12
        merc_ratio = dx / dy
        logger.info(f"[anim] mercator ratio from ring = {merc_ratio:.6f}")

        # --- Máscara del polígono (opcional) ---
        inside_mask = _compute_inside_mask_from_ring(ring, width_px, height_px)

        # --- Petición de frames (con caché por ventana) ---
        frames, labels = [], []
        for s0, s1 in slices:
            arr, used_window, _att = _fetch_window_resilient_generic(
                token=token,
                ring=ring,
                s0_iso=s0,
                s1_iso=s1,
                evalscript=evalscript,
                index_type="NDVI",
                width=width_px,
                height=height_px,
            )
            if arr is None or not np.isfinite(arr).any():
                logger.info(f"[anim] ventana {s0}..{s1}: sin datos")
                continue

            h_arr, w_arr = arr.shape
            arr_ratio = float(w_arr) / float(h_arr)
            logger.info(f"[anim] frame array shape = {w_arr}x{h_arr} (ratio {arr_ratio:.6f})")
            if abs(arr_ratio - canvas_ratio) > 1e-3:
                logger.warning(f"[anim] ⚠️ array/canvas ratio mismatch: arr {arr_ratio:.6f} vs canvas {canvas_ratio:.6f}")

            frames.append(np.array(arr, dtype="float32"))
            t0 = pd.to_datetime(used_window[0]); t1 = pd.to_datetime(used_window[1])
            labels.append(f"{t0:%d %b %Y} – {t1:%d %b %Y}")

        if len(frames) < 2:
            info = dbc.Alert("No hay suficientes ventanas válidas para animar.", color="info")
            return info, "0–1 ventana válida.", None, 0, {}

        # === Colorimetría [0,1], UNDER=0, BAD=transparent ===
        vmin, vmax = (getattr(cfg, "NDVI_CUSTOM_RANGE", None) or (0.0, 1.0))
        cmap = _create_cmap_from_def(cmap_name)
        try:
            # set_under como color de 0; set_bad transparente
            c0 = cmap(Normalize(vmin=vmin, vmax=vmax, clip=False)(vmin))
            c0 = (c0[0], c0[1], c0[2], 1.0)
            cmap.set_under(c0)
            cmap.set_bad((0, 0, 0, 0))
        except Exception:
            pass

        # --- Generar PNGs (sin recorte 'tight') ---
        png_uris = []
        for arr, label in zip(frames, labels):
            b = _array_to_png_bytes(
                arr, vmin=vmin, vmax=vmax, cmap=cmap,
                target_w_px=width_px, target_h_px=height_px,
                label_text=label,
                inside_mask=inside_mask,
                logger=logger
            )
            png_uris.append("data:image/png;base64," + base64.b64encode(b).decode("ascii"))

        helper = f"{idx}: {len(png_uris)} frames · {width_px}×{height_px} · ratio={canvas_ratio:.6f} · vmin={vmin:.2f} · vmax={vmax:.2f}"
        N = len(png_uris)
        marks = {0: labels[0], (N-1): labels[-1]} if N >= 2 else {}
        store_data = {"frames": png_uris, "labels": labels}
        return "", helper, store_data, (N - 1), marks





    @app.callback(
        Output("manual-anim-container", "style"),
        Input("anim-mode", "value"),
        prevent_initial_call=True
    )
    def _toggle_manual_container(mode):
        return {"display": "block"} if mode == "manual" else {"display": "none"}


    @app.callback(
    [
        Output("manual-animation-view", "children"),
        Output("anim-current-label", "children"),
        Output("anim-slider", "value"),
    ],
    [
        Input("anim-slider", "value"),
        Input("anim-interval", "n_intervals"),
        Input("anim-frames-store", "data"),  # 👈 nuevo: dispara al generar frames
    ],
    [
        State("anim-interval", "disabled"),
    ],
    prevent_initial_call=True
    )
    def _update_manual_frame(slider_val, n_intervals, store, interval_disabled):
        if not store or not store.get("frames"):
            return no_update, no_update, no_update

        frames = store["frames"]
        labels = store.get("labels", [""] * len(frames))

        trig = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None

        # Caso 1: se acaban de generar nuevos frames -> empieza en el 0
        if trig == "anim-frames-store":
            idx = 0
        else:
            # Caso 2: slider manual o avance por intervalo
            if not isinstance(slider_val, int):
                idx = 0
            else:
                idx = max(0, min(slider_val, len(frames) - 1))
            if trig == "anim-interval" and not interval_disabled:
                idx = (idx + 1) % len(frames)

        img = html.Img(
            src=frames[idx],
            style={"maxWidth": "100%", "borderRadius": "8px", "boxShadow": "0 4px 14px rgba(0,0,0,.12)"}
        )
        return img, labels[idx], idx


    @app.callback(
    [Output("anim-interval", "disabled"),
        Output("anim-play-btn", "children")],
    Input("anim-play-btn", "n_clicks"),
    State("anim-interval", "disabled"),
    prevent_initial_call=True
    )
    def _toggle_play(n, disabled):
        # alterna entre reproducir y pausar
        new_disabled = not disabled
        btn = [html.I(className="fas fa-pause me-1"), "Pausar"] if not new_disabled else [html.I(className="fas fa-play me-1"), "Reproducir"]
        return new_disabled, btn

    @app.callback(
        Output("anim-interval", "interval"),
        Input("anim-frame-ms", "value"),
        prevent_initial_call=True
    )

    # =====================================================================
    # SECCIÓN 7: COMPARACIÓN TEMPORAL ENTRE PERÍODOS
    # =====================================================================
    
    # Callback para ejecutar comparación entre dos rangos temporales
    @app.callback(
        [
            Output("comparison-results-section", "style"),
            Output("comparison-kpis", "children"),
            Output("comparison-scatter-chart", "children"),
            Output("comparison-difference-chart", "children"),
            Output("comparison-data-store", "data")
        ],
        Input("run-comparison-btn", "n_clicks"),
        [
            State("comparison-range1", "start_date"),
            State("comparison-range1", "end_date"), 
            State("comparison-range2", "start_date"),
            State("comparison-range2", "end_date"),
            State("comparison-indices", "value"),
            State("analysis-mode-selector", "value"),
            State("selected-geometry", "data")
        ],
        prevent_initial_call=True
    )
    def run_temporal_comparison(n_clicks, start_date1, end_date1, start_date2, end_date2, indices, selected_mode, drawn_feature):
        """Ejecuta comparación temporal entre dos rangos de fechas"""
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update
            
        try:
            import base64, pickle
            
            # Validar inputs
            if not start_date1 or not end_date1 or not start_date2 or not end_date2 or not indices:
                return {"display": "none"}, "Faltan parámetros", "", "", {}
            
            if start_date1 >= end_date1 or start_date2 >= end_date2:
                error_msg = dbc.Alert("Las fechas de inicio deben ser anteriores a las de fin", color="warning")
                return {"display": "block"}, error_msg, "", "", {}
            
            logger.info("=" * 60)
            logger.info("🔄 COMPARACIÓN TEMPORAL ENTRE PERÍODOS")
            logger.info(f"   📅 Período 1: {start_date1} → {end_date1}")
            logger.info(f"   📅 Período 2: {start_date2} → {end_date2}")
            logger.info(f"   🧮 Índices: {indices}")
            logger.info("=" * 60)
            
            # ===== Obtener geometría (mismo método que run_analysis) =====
            geom, farm_name = None, "Área dibujada"
            try:
                if selected_mode and selected_mode != "temporal":
                    selected_farm = next((f for f in (list_fincas() or []) if str(f.get("id")) == str(selected_mode)), None)
                    if selected_farm:
                        geom = selected_farm.get("geometry")
                        farm_name = selected_farm.get("properties", {}).get("name", f"finca-{selected_mode}")
                        logger.info(f"Usando geometría de la finca: '{farm_name}'")
                elif drawn_feature and drawn_feature.get("geometry"):
                    geom = drawn_feature["geometry"]
                    logger.info("Usando geometría dibujada en el mapa")
            except Exception as e:
                logger.error(f"Error obteniendo geometría: {e}")
                error_msg = dbc.Alert(f"Error en geometría: {str(e)}", color="danger")
                return {"display": "block"}, error_msg, "", "", {}
            
            if not geom:
                error_msg = dbc.Alert("Selecciona una finca o dibuja un polígono en el mapa", color="warning")
                return {"display": "block"}, error_msg, "", "", {}
            
            # ===== Procesar geometría (mismo método que run_analysis) =====
            try:
                bounds = _bounds_from_geometry(geom)
                ring = _outer_ring(geom)
                if not ring or not bounds:
                    error_msg = dbc.Alert("Geometría inválida", color="danger")
                    return {"display": "block"}, error_msg, "", "", {}
            except Exception as e:
                logger.error(f"Error procesando geometría: {e}")
                error_msg = dbc.Alert(f"Error en geometría: {str(e)}", color="danger")
                return {"display": "block"}, error_msg, "", "", {}
            
            # ===== Token (mismo método que run_analysis) =====
            cid, csec = os.getenv("COPERNICUS_CLIENT_ID"), os.getenv("COPERNICUS_CLIENT_SECRET")
            if not cid or not csec:
                error_msg = dbc.Alert("Faltan credenciales de Copernicus", color="danger")
                return {"display": "block"}, error_msg, "", "", {}
            try:
                token = get_access_token(cid, csec)
            except Exception as e:
                logger.error(f"Error autenticando: {e}")
                error_msg = dbc.Alert(f"Error autenticando: {str(e)}", color="danger")
                return {"display": "block"}, error_msg, "", "", {}
            
            # ===== Obtener datos usando la misma lógica resiliente que run_analysis =====
            masked = True
            include_water = False
            indices = [i.upper() for i in (indices or ["NDVI"])]
            base_w, base_h = 1024, 1024
            
            data1, data2 = {}, {}
            
            for idx in indices:
                try:
                    logger.info(f"Obteniendo {idx} para período 1: {start_date1} → {end_date1}")
                    evalscript = build_evalscript(idx, masked=masked, include_water=include_water)
                    
                    # Período 1
                    arr1, used_win1, attempt_id1 = _fetch_window_resilient_generic(
                        token=token,
                        ring=ring,
                        s0_iso=start_date1,
                        s1_iso=end_date1,
                        evalscript=evalscript,
                        index_type=idx,
                        width=base_w,
                        height=base_h,
                    )
                    
                    logger.info(f"Obteniendo {idx} para período 2: {start_date2} → {end_date2}")
                    
                    # Período 2
                    arr2, used_win2, attempt_id2 = _fetch_window_resilient_generic(
                        token=token,
                        ring=ring,
                        s0_iso=start_date2,
                        s1_iso=end_date2,
                        evalscript=evalscript,
                        index_type=idx,
                        width=base_w,
                        height=base_h,
                    )
                    
                    if arr1 is not None and arr2 is not None and np.isfinite(arr1).any() and np.isfinite(arr2).any():
                        data1[idx] = np.array(arr1, dtype="float32")
                        data2[idx] = np.array(arr2, dtype="float32")
                        logger.info(f"✅ {idx}: shapes {arr1.shape} y {arr2.shape}")
                        logger.info(f"   📊 Período 1: {np.isfinite(arr1).sum()} píxeles válidos")
                        logger.info(f"   📊 Período 2: {np.isfinite(arr2).sum()} píxeles válidos")
                    else:
                        logger.warning(f"⚠️ Datos incompletos para {idx}")
                        
                except Exception as e:
                    logger.error(f"Error obteniendo datos {idx}: {e}")
                    continue
            
            if not data1 or not data2:
                error_msg = dbc.Alert("No se pudieron obtener datos satelitales para los períodos seleccionados", color="danger")
                return {"display": "block"}, error_msg, "", "", {}
            
            # Formatear períodos para mostrar
            period1_str = f"{pd.to_datetime(start_date1).strftime('%d/%m/%Y')} - {pd.to_datetime(end_date1).strftime('%d/%m/%Y')}"
            period2_str = f"{pd.to_datetime(start_date2).strftime('%d/%m/%Y')} - {pd.to_datetime(end_date2).strftime('%d/%m/%Y')}"
            
            # Generar componentes visuales ORIENTADOS A AGRICULTORES
            logger.info("🎨 Generando análisis para agricultores...")
            
            # KPIs con información práctica
            kpis = create_comparison_kpis(data1, data2, period1_str, period2_str, indices)
            
            # Análisis de cambios píxel por píxel comprensible
            change_fig = create_change_analysis_chart(data1, data2, period1_str, period2_str, indices)
            change_chart = dcc.Graph(
                figure=change_fig, 
                config={
                    'displayModeBar': False,
                    'scrollZoom': False,
                    'doubleClick': False,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                    'staticPlot': False
                }
            ) if change_fig.data else "Sin datos para análisis de cambios"
            
            # Clasificación de salud del cultivo
            health_fig = create_health_classification_chart(data1, data2, period1_str, period2_str, indices) 
            health_chart = dcc.Graph(
                figure=health_fig,
                config={
                    'displayModeBar': False,
                    'scrollZoom': False,
                    'doubleClick': False,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                    'staticPlot': False
                }
            ) if health_fig.data else "Sin datos para clasificación de salud"
            
            # Tabla estadística simplificada (opcional)
            stats_table = create_comparison_stats_table(data1, data2, period1_str, period2_str, indices)
            
            # Almacenar datos de forma segura (evitando serialización de arrays grandes)
            comparison_data = {
                "period1": f"{start_date1}_{end_date1}",
                "period2": f"{start_date2}_{end_date2}", 
                "indices": indices,
                "farm_name": farm_name,
                # Solo metadatos, no arrays completos
                "summary": {
                    idx: {
                        "period1_stats": {"mean": float(np.nanmean(data1[idx])), "std": float(np.nanstd(data1[idx])), "count": int(np.isfinite(data1[idx]).sum())},
                        "period2_stats": {"mean": float(np.nanmean(data2[idx])), "std": float(np.nanstd(data2[idx])), "count": int(np.isfinite(data2[idx]).sum())}
                    } for idx in indices if idx in data1 and idx in data2
                }
            }
            
            logger.info("✅ Comparación temporal completada exitosamente")
            
            logger.info("✅ Visualizaciones generadas exitosamente")
            
            return (
                {"display": "block"},
                kpis,                    # KPIs agrícolas con interpretaciones
                change_chart,            # Análisis de cambios píxel por píxel
                health_chart,            # Clasificación de salud del cultivo
                comparison_data
            )
            
        except Exception as e:
            logger.error(f"❌ Error en comparación temporal: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error en el análisis: {str(e)}"
            ], color="danger")
            
            return {"display": "block"}, error_msg, "", "", {}


    # Callback para mostrar la sección de animación después del análisis histórico
    @app.callback(
        Output("animation-section", "style"),
        [Input("historical-kpi-cards", "children"),
         Input("historical-charts-container", "children")],
        prevent_initial_call=True
    )
    def show_animation_section(kpi_cards, charts):
        # Mostrar la sección de animación cuando hay resultados históricos
        if kpi_cards or charts:
            return {"display": "block"}
        return {"display": "none"}

    # ===============================================================================
    #                    CALLBACK PARA MONITOR DE CUOTA API
    # ===============================================================================
    @app.callback(
        Output("api-quota-monitor-container", "children"),
        [Input("run-analysis-btn", "n_clicks"),
         Input("run-comparison-btn", "n_clicks"),
         Input("compute-historical-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_api_quota_monitor(n1, n2, n3):
        """
        Actualiza el monitor de cuota API después de cualquier operación.
        Se ejecuta también al cargar la página para mostrar estado inicial.
        """
        try:
            from utils.api_quota_manager import get_quota_monitor
            from src.app.app_config import AGRI_THEME
            
            quota_monitor = get_quota_monitor()
            usage_stats = quota_monitor.get_usage_stats()
            
            # Determinar color del progreso basado en límites reales de Copernicus
            requests_today = usage_stats.get('requests_today', 0)
            requests_month = usage_stats.get('requests_month', 0)
            cache_hits = usage_stats.get('cache_hits', 0)
            daily_sustainable = 30000 / 30  # ~1000 requests/día sostenible
            
            if requests_today < daily_sustainable * 0.3:  # < 300/día
                progress_color = "success"
                status_text = "Uso bajo"
                icon_class = "fas fa-satellite"
            elif requests_today < daily_sustainable * 0.7:  # < 700/día
                progress_color = "warning"
                status_text = "Uso moderado"
                icon_class = "fas fa-exclamation-triangle"
            else:
                progress_color = "danger"
                status_text = "Uso intensivo"
                icon_class = "fas fa-exclamation-circle"
            
            return dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6([
                            html.I(className=f"{icon_class} me-2"),
                            "Monitor API Satelital"
                        ], className="mb-2", style={"color": AGRI_THEME["colors"]["primary"]}),
                        html.P([
                            f"Requests hoy: {requests_today} ",
                            html.Small(f"({status_text})", className="text-muted")
                        ], className="mb-1"),
                        html.P([
                            f"Este mes: {requests_month:,}/30,000 ",
                            html.Small(f"({(requests_month/30000*100):.1f}%)", className="text-info")
                        ], className="mb-2 small"),
                        dbc.Progress(
                            value=min(100, (requests_today / daily_sustainable) * 100),
                            color=progress_color,
                            className="mb-2",
                            style={"height": "8px"}
                        ),
                        html.Div([
                            html.P([
                                html.I(className="fas fa-database me-1"),
                                "Caché activo: ", 
                                html.Span(f"{cache_hits} hits", className="text-success")
                            ], className="mb-1 small text-muted"),
                            html.P([
                                html.I(className="fas fa-clock me-1"),
                                f"Actualizado: {datetime.now().strftime('%H:%M:%S')}"
                            ], className="mb-0 small text-muted")
                        ])
                    ])
                ])
            ], color="light", outline=True, className="mb-3", style={"borderRadius": "10px"})
            
        except Exception as e:
            logger.warning(f"Error actualizando monitor de cuota API: {e}")
            return dbc.Card([
                dbc.CardBody([
                    html.P([
                        html.I(className="fas fa-satellite me-2"),
                        "Monitor API no disponible"
                    ], className="mb-0 text-muted")
                ])
            ], color="light", outline=True, className="mb-3")

    # ===============================================================================
    #                    CALLBACKS DE ESTADO DE CARGA
    # ===============================================================================
    
    @app.callback(
        Output("satellite-busy", "data", allow_duplicate=True),
        Input("run-analysis-btn", "n_clicks"),
        [State("analysis-mode-selector", "value"), State("selected-geometry", "data")],
        prevent_initial_call=True
    )
    def _check_analysis_validity(n_clicks, selected_mode, drawn_feature):
        """Solo activa busy si hay datos válidos para procesar."""
        if not n_clicks:
            return False
            
        # Validar que hay geometría válida
        has_geometry = False
        if selected_mode and selected_mode != "temporal":
            # Verificar si la finca seleccionada existe
            from src.utils.finca_store import list_fincas
            selected_farm = next((f for f in (list_fincas() or []) if str(f.get("id")) == str(selected_mode)), None)
            has_geometry = bool(selected_farm and selected_farm.get("geometry"))
        elif drawn_feature and drawn_feature.get("geometry"):
            has_geometry = True
            
        # Solo activar busy si hay geometría válida
        return has_geometry
    
    @app.callback(
        Output("satellite-busy", "data", allow_duplicate=True),
        [
            # Se desactiva cuando se actualizan los componentes principales
            Input("kpi-cards-container", "children"),
            Input("dynamic-ndvi-overlay", "url"),
            Input("dynamic-osavi-overlay", "url"),
            Input("dynamic-ndre-overlay", "url"),
            Input("historical-charts-container", "children"),
            Input("comparison-results-section", "style"),
        ],
        prevent_initial_call=True
    )
    def _unset_satellite_busy(*_):
        """Desactiva el estado de carga cuando los componentes están actualizados."""
        return False
    
    @app.callback(
        [
            Output("satellite-loading-modal", "is_open"),
            Output("satellite-map-loading-overlay", "style"),
        ],
        Input("satellite-busy", "data"),
        State("satellite-map-loading-overlay", "style"),
        prevent_initial_call=True
    )
    def _toggle_satellite_loaders(is_busy, overlay_style):
        """
        Controla la visibilidad de los indicadores de carga satelital.
        
        Args:
            is_busy (bool): Estado de carga actual
            overlay_style (dict): Estilos actuales del overlay
            
        Returns:
            tuple: Estado del modal y estilos del overlay actualizados
        """
        style = dict(overlay_style or {})
        if is_busy:
            style["display"] = "flex"
        else:
            style["display"] = "none"
        
        return bool(is_busy), style

    logger.info("✅ Todos los callbacks de análisis satelital registrados correctamente")
    logger.info(f"📊 Total de callbacks registrados: {len([func for func in locals().values() if hasattr(func, '_callback')])}")


