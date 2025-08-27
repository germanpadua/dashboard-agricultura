
"""
Funciones auxiliares para análisis de datos satelitales.

Este módulo contiene todas las funciones helper utilizadas por los callbacks
de análisis satelital, organizadas por categorías funcionales:

1. GEOMETRÍA Y PROCESAMIENTO ESPACIAL
   - Extracción de bounds y anillos de geometrías
   - Cálculo de máscaras de polígono
   - Transformaciones de coordenadas

2. PROCESAMIENTO DE DATOS SATELITALES
   - Funciones de caché para fincas e índices
   - Obtención resiliente de datos con múltiples intentos
   - Generación de composites temporales

3. VISUALIZACIÓN Y COLORMAPS
   - Creación de mapas de color personalizados
   - Generación de overlays PNG para mapas web
   - Leyendas y escalas de color

4. ANÁLISIS ESTADÍSTICO Y KPIS
   - Cálculo de métricas de salud de cultivos
   - Generación de gráficas estadísticas
   - Tarjetas KPI responsivas

5. ANIMACIONES TEMPORALES
   - Procesamiento de series temporales
   - Generación de frames para animaciones
   - Codificación en formatos GIF/WebP

Autor: German Jose Padua Pleguezuelo
Universidad de Granada
Master en Ciencia de Datos

Fichero: src.callbacks_refactored.datos_satelitales_helpers.py
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
import math
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
from datetime import datetime, timedelta

import config_colormaps as cfg


# Configure matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid GUI issues
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

# Dashboard imports
try:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from dash import html, dcc, no_update
    import dash_bootstrap_components as dbc
    from matplotlib.colors import Normalize
    from utils.api_quota_manager import get_intelligent_cache, get_quota_monitor
except ImportError as e:
    logging.error(f"❌ Error importando dependencias: {e}")
    logging.warning("⚠️ Algunas librerías no disponibles, usando mocks para desarrollo")

# Configuración
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURACIÓN Y CONSTANTES GLOBALES
# =====================================================================

# Cache configuration
CACHE_DIR = Path("./.sat_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Plotting configuration
_GRID = dict(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)

# Color palettes
AGRI_COLORS = {
    "primary": "#2E7D32",   # verde olivo
    "secondary": "#5D4037",
    "success": "#388E3C",
    "warning": "#F57C00",
    "danger": "#D32F2F",
    "info": "#0277BD",
}

# =====================================================================
# SECCIÓN 1: GEOMETRÍA Y PROCESAMIENTO ESPACIAL
# =====================================================================


def _bounds_from_geometry(geom: dict) -> Optional[List[List[float]]]:
    """
    Extrae los límites geográficos (bounds) de una geometría GeoJSON.
    
    Args:
        geom: Diccionario con geometría GeoJSON (Polygon o MultiPolygon)
        
    Returns:
        Lista de coordenadas [[lat_min, lon_min], [lat_max, lon_max]] 
        con pequeño padding, o None si geometría inválida
    """
    if not geom: 
        return None
    
    geometry_type = geom.get("type")
    coordinates = geom.get("coordinates")
    
    if not geometry_type or coordinates is None: 
        return None
    
    # Inicializar límites extremos
    lat_min, lat_max = 90.0, -90.0
    lon_min, lon_max = 180.0, -180.0
    
    def update_bounds(lon: float, lat: float) -> None:
        """Actualiza los límites con nuevas coordenadas."""
        nonlocal lat_min, lat_max, lon_min, lon_max
        lat_min = min(lat_min, lat)
        lat_max = max(lat_max, lat)
        lon_min = min(lon_min, lon)
        lon_max = max(lon_max, lon)
    
    # Procesar según tipo de geometría
    if geometry_type == "Polygon":
        for ring in coordinates:
            for lon, lat in ring: 
                update_bounds(lon, lat)
    elif geometry_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                for lon, lat in ring: 
                    update_bounds(lon, lat)
    else:
        return None
    
    # Agregar pequeño padding para evitar bordes exactos
    padding = 1e-4
    return [
        [lat_min - padding, lon_min - padding], 
        [lat_max + padding, lon_max + padding]
    ]

def _outer_ring(geom: dict) -> Optional[List[List[float]]]:
    """
    Extrae el anillo exterior de una geometría GeoJSON.
    
    Args:
        geom: Diccionario con geometría GeoJSON (Polygon o MultiPolygon)
        
    Returns:
        Lista de coordenadas [[lon, lat], ...] del anillo exterior,
        o None si geometría inválida
    """
    if not geom: 
        return None
        
    geometry_type = geom.get("type")
    coordinates = geom.get("coordinates")
    
    if geometry_type == "Polygon": 
        return coordinates[0] if coordinates else None
    elif geometry_type == "MultiPolygon" and coordinates: 
        return coordinates[0][0]  # Primer polígono, primer anillo
    
    return None


def _build_time_slices(start_iso: str, end_iso: str, freq: str) -> List[tuple]:
    """
    Genera ventanas temporales para análisis histórico.
    
    Args:
        start_iso: Fecha de inicio en formato ISO (YYYY-MM-DD)
        end_iso: Fecha de fin en formato ISO (YYYY-MM-DD)
        freq: Frecuencia ('monthly' o 'fortnight')
        
    Returns:
        Lista de tuplas (fecha_inicio, fecha_fin) para cada ventana temporal
    """
    from datetime import timedelta
    import pandas as pd
    
    if not start_iso or not end_iso:
        return []
        
    start_date = pd.to_datetime(start_iso).date()
    end_date = pd.to_datetime(end_iso).date()
    
    # Asegurar orden correcto de fechas
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    windows = []
    
    if freq == "fortnight":
        # Ventanas quincenales (14 días)
        current = start_date
        while current <= end_date:
            window_end = min(current + timedelta(days=13), end_date)
            windows.append((current.isoformat(), window_end.isoformat()))
            current = window_end + timedelta(days=1)
    else:  # monthly (por defecto)
        # Ventanas mensuales
        current = start_date.replace(day=1)  # Inicio del mes
        
        while current <= end_date:
            # Calcular fin del mes actual
            if current.month == 12:
                month_end = current.replace(day=31)
            else:
                next_month = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
                month_end = next_month - timedelta(days=1)
            
            # Ajustar ventana a los límites solicitados
            window_start = max(current, start_date)
            window_end = min(month_end, end_date)
            
            windows.append((window_start.isoformat(), window_end.isoformat()))
            
            # Avanzar al siguiente mes
            current = (month_end + timedelta(days=1)).replace(day=1)
    
    return windows


# =====================================================================
# SECCIÓN 3: VISUALIZACIÓN Y COLORMAPS
# =====================================================================


def _create_ndvi_legend():
    """Crea leyenda científica para NDVI"""
    return dbc.Card([
        dbc.CardHeader(html.H6([html.I(className="fas fa-leaf me-2"), "Leyenda NDVI"], className="mb-0")),
        dbc.CardBody([
            html.Div([
                html.Div(style={
                    "background": "linear-gradient(to right, #704214, #FFFF00, #006400)",
                    "height": "20px", "width": "100%", "border-radius": "3px"
                }),
                dbc.Row([
                    dbc.Col(html.Small("-1.0", className="text-muted"), width="auto"),
                    dbc.Col(html.Small("0.0", className="text-center text-muted"), width=True),
                    dbc.Col(html.Small("1.0", className="text-muted text-end"), width="auto")
                ], className="mt-1")
            ], className="mb-2"),
            html.Small([
                "🟤 < 0.3: Suelo/agua | ",
                "🟡 0.3-0.6: Moderada | ",
                "🟢 > 0.6: Vigorosa"
            ], className="text-muted")
        ])
    ], className="shadow-sm")

def _create_anomaly_legend():
    """Crea leyenda científica para anomalías NDVI"""
    return dbc.Card([
        dbc.CardHeader(html.H6([html.I(className="fas fa-chart-line me-2"), "Leyenda Anomalía"], className="mb-0")),
        dbc.CardBody([
            html.Div([
                html.Div(style={
                    "background": "linear-gradient(to right, #d73027, #ffffff, #1a9850)",
                    "height": "20px", "width": "100%", "border-radius": "3px"
                }),
                dbc.Row([
                    dbc.Col(html.Small("-0.3", className="text-muted"), width="auto"),
                    dbc.Col(html.Small("0.0", className="text-center text-muted"), width=True),
                    dbc.Col(html.Small("+0.3", className="text-muted text-end"), width="auto")
                ], className="mt-1")
            ], className="mb-2"),
            html.Small([
                "🔴 Negativa: Estrés | ",
                "⚪ Normal | ",
                "🟢 Positiva: Mejora"
            ], className="text-muted")
        ])
    ], className="shadow-sm")


def _create_anomaly_colormap():
    """Crea colormap para anomalías NDVI"""
    try:
        anomaly_cmap_name = cfg.ANOMALY_COLORMAP
        anomaly_def = cfg.ANOMALY_COLORMAPS_DEF.get(anomaly_cmap_name)
        
        if not anomaly_def:
            # Fallback a colormap simple divergente
            colors = ['#d73027', '#ffffff', '#1a9850']
            return LinearSegmentedColormap.from_list('anomaly_fallback', colors, N=256)
        
        # Crear colormap desde definición
        values = [stop[0] for stop in anomaly_def]
        colors = [stop[1] for stop in anomaly_def]
        
        # Normalizar valores al rango [0, 1] para LinearSegmentedColormap
        min_val, max_val = min(values), max(values)
        val_range = max_val - min_val
        
        if val_range == 0:
            normalized_values = [0.5] * len(values)
        else:
            normalized_values = [(v - min_val) / val_range for v in values]
        
        # Crear colormap
        cmap = LinearSegmentedColormap.from_list(anomaly_cmap_name, list(zip(normalized_values, colors)), N=256)
        cmap.set_bad((0, 0, 0, 0))  # Transparente para NaN
        
        return cmap
        
    except Exception as e:
        logger.error(f"Error creando colormap de anomalías: {e}")
        # Fallback simple
        colors = ['#d73027', '#ffffff', '#1a9850']
        cmap = LinearSegmentedColormap.from_list('anomaly_simple', colors, N=256)
        cmap.set_bad((0, 0, 0, 0))
        return cmap


# =====================================================================
# SECCIÓN 4: ANÁLISIS ESTADÍSTICO Y KPIS
# =====================================================================

def _palette():
    return {
        "stress":   "#d84a3a",  # rojo
        "mid":      "#f0ad00",  # ámbar
        "healthy":  "#2ea44f",  # verde
        "anom_neg": "#c0392b",  # rojo oscuro
        "anom_neu": "#bdc3c7",  # gris claro
        "anom_pos": "#1e8449",  # verde oscuro
        "accent":   "#0d6efd"   # azul bootstrap para acentos
    }

def _get_plotly_theme():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, Roboto", size=13),
        margin=dict(l=24, r=16, t=42, b=28),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="white", bordercolor="rgba(0,0,0,0.15)", font_size=12),
        transition=dict(duration=250),
        autosize=False,   # 👈 importante
    )
_GRID = dict(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)

def _graph(fig, gid: str, height_px: int):
    fig.update_layout(height=height_px)
    return dcc.Graph(
        id=gid,
        figure=fig,
        className="mb-3",
        config={"displayModeBar": False, "responsive": True},
        style={"height": f"{height_px}px"}  # 👈 ancla definitiva
    )



# Helper functions inline para mejor rendimiento
def _finite(arr: np.ndarray) -> np.ndarray:
    """Extrae solo los valores finitos (no NaN, no infinitos) de un array."""
    return arr[np.isfinite(arr)]

def _percent(n: int, d: int) -> float:
    """Calcula porcentaje evitando división por cero."""
    return float(n) * 100.0 / float(d) if d > 0 else 0.0

def _fmt_pct(x: float, dec: int = 1) -> str:
    """Formatea un número como porcentaje con decimales especificados."""
    return f"{x:.{dec}f}%"


def _generate_kpi_cards_generic(arr: np.ndarray, anomaly: Optional[np.ndarray], lo: float, hi: float, label_idx: str):
    v = _finite(np.array(arr, dtype="float32"))
    if v.size == 0:
        return [dbc.Alert(f"No hay datos {label_idx} válidos", color="warning")]

    mean_v = float(np.mean(v))
    healthy_pct = _percent(int((v >= hi).sum()), int(v.size))
    stress_pct  = _percent(int((v <  lo).sum()), int(v.size))

    row1 = dbc.Row([
        _kpi_card(f"{label_idx} medio", f"{mean_v:.3f}", "", "fa-leaf", "success"),
        _kpi_card("Saludable", _fmt_pct(healthy_pct), f"≥ {hi:.2f}", "fa-seedling", "success"),
        _kpi_card("Estrés", _fmt_pct(stress_pct), f"< {lo:.2f}", "fa-triangle-exclamation", "danger"),
    ], className="g-3")

    cards = [row1]
    if anomaly is not None and np.isfinite(anomaly).any():
        a = _finite(np.array(anomaly, dtype="float32"))
        if a.size > 0:
            cards.append(dbc.Row([
                _kpi_card("ΔNDVI medio", f"{float(np.mean(a)):+.3f}", "vs años de referencia", "fa-chart-line", "primary"),
            ], className="g-3"))
    return cards


def _generate_charts_generic(arr: np.ndarray, anomaly: Optional[np.ndarray], label_idx: str):
    pal = _palette()
    theme = _get_plotly_theme()
    charts: List = []

    v = _finite(np.array(arr, dtype="float32"))
    if v.size == 0:
        return [dbc.Alert("No hay datos suficientes para generar gráficas", color="warning")]

    # ===== HISTOGRAMA MEJORADO CON DENSIDAD =====
    bins_ndvi = np.linspace(-0.2, 0.9, 50)  # Más bins para mejor resolución
    fig_hist = go.Figure()
    
    # Histograma principal con gradiente
    fig_hist.add_trace(go.Histogram(
        x=v,
        xbins=dict(start=bins_ndvi[0], end=bins_ndvi[-1], size=(bins_ndvi[-1]-bins_ndvi[0])/49),
        name=f"Distribución {label_idx}",
        marker=dict(
            color=v,
            colorscale=[[0, '#d84a3a'], [0.3, '#f0ad00'], [0.6, '#2ea44f'], [1, '#1e8449']],
            line=dict(color="white", width=0.5),
            cmin=-0.2,
            cmax=0.9
        ),
        opacity=0.8,
        hovertemplate=f"{label_idx}=%{{x:.3f}}<br>Frecuencia=%{{y}}<extra></extra>"
    ))

    # Agregar curva de densidad suavizada
    try:
        from scipy.stats import gaussian_kde
        if v.size > 10:
            kde = gaussian_kde(v)
            x_smooth = np.linspace(v.min(), v.max(), 200)
            y_smooth = kde(x_smooth) * len(v) * (bins_ndvi[1] - bins_ndvi[0])
            fig_hist.add_trace(go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode='lines',
                name='Tendencia',
                line=dict(color='#2c3e50', width=3, dash='dot'),
                yaxis='y2',
                hovertemplate='Densidad suavizada<extra></extra>'
            ))
    except ImportError:
        pass  # Sin scipy, continuar sin densidad

    fig_hist.update_layout(
        title=dict(
            text=f"📊 Distribución Detallada de {label_idx}",
            font=dict(size=16, color=pal["accent"])
        ),
        xaxis=dict(title=f"Valores {label_idx}", range=[-0.2, 0.9], gridcolor="rgba(0,0,0,0.1)"),
        yaxis=dict(title="Frecuencia de Píxeles", gridcolor="rgba(0,0,0,0.1)"),
        yaxis2=dict(title="Densidad", overlaying='y', side='right', showgrid=False),
        **theme,
        showlegend=True
    )

    # Líneas de referencia mejoradas
    fig_hist.add_vline(x=0.3, line_dash="dash", line_color=pal["mid"], line_width=2,
                       annotation_text="Umbral Estrés", annotation_position="top left", 
                       annotation_font_color=pal["mid"], annotation_font_size=12)
    fig_hist.add_vline(x=0.6, line_dash="dash", line_color=pal["healthy"], line_width=2,
                       annotation_text="Umbral Saludable", annotation_position="top right", 
                       annotation_font_color=pal["healthy"], annotation_font_size=12)
    
    charts.append(_graph(fig_hist, "kpi-ndvi-hist", 380))  


    # ===== GRÁFICO DE TARTA MEJORADO CON DETALLES =====
    stress = (v < 0.3).sum()
    mid    = ((v >= 0.3) & (v < 0.6)).sum()
    healthy= (v >= 0.6).sum()

    # Calcular porcentajes para el centro
    total_pixels = len(v)
    stress_pct = (stress / total_pixels) * 100
    healthy_pct = (healthy / total_pixels) * 100

    labels = ["🔴 Estrés (<0.3)", "🟡 Intermedio (0.3–0.6)", "🟢 Saludable (≥0.6)"]
    values = [int(stress), int(mid), int(healthy)]

    fig_pie_ndvi = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        sort=False,
        direction="clockwise",
        textinfo="label+percent",
        textposition="auto",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{label}</b><br>" +
                     "Píxeles: %{value:,}<br>" +
                     "Porcentaje: %{percent}<br>" +
                     "<extra></extra>",
        marker=dict(
            colors=[pal["stress"], pal["mid"], pal["healthy"]],
            line=dict(color='white', width=2)
        ),
        rotation=90
    ))
    
    # Determinar estado general para el centro
    if healthy_pct >= 60:
        center_text = "EXCELENTE"
        center_color = pal["healthy"]
    elif healthy_pct >= 40:
        center_text = "BUENO" 
        center_color = pal["mid"]
    else:
        center_text = "ALERTA"
        center_color = pal["stress"]

    fig_pie_ndvi.update_layout(
        title=dict(
            text=f"🎯 Clasificación de Salud del Cultivo",
            font=dict(size=16, color=pal["accent"])
        ),
        showlegend=False,  # Las etiquetas están en las porciones
        annotations=[
            dict(
                text=f"<b>{center_text}</b><br>{healthy_pct:.0f}% Saludable", 
                x=0.5, y=0.5, 
                font=dict(size=14, color=center_color, family="Arial Black"),
                showarrow=False
            )
        ],
        **theme
    )

    charts.append(_graph(fig_pie_ndvi, "kpi-ndvi-classes", 380))


    # ===== ANÁLISIS DE ANOMALÍAS MEJORADO =====
    if anomaly is not None and np.size(anomaly) > 0 and np.isfinite(anomaly).any():
        a = _finite(np.array(anomaly, dtype="float32"))
        if a.size > 0:
            bins_an = np.linspace(-0.3, 0.3, 60)
            
            # Separar valores negativos y positivos
            a_neg = a[a < -0.05]  # Deterioro significativo
            a_neu = a[(a >= -0.05) & (a <= 0.05)]  # Neutral
            a_pos = a[a > 0.05]   # Mejora significativa

            fig_ahist = go.Figure()
            
            # Deterioro significativo
            if len(a_neg) > 0:
                fig_ahist.add_trace(go.Histogram(
                    x=a_neg,
                    name="🔴 Deterioro",
                    marker=dict(color=pal["anom_neg"], line=dict(color="white", width=1)),
                    opacity=0.8,
                    hovertemplate="<b>Deterioro</b><br>ΔNDVI: %{x:.3f}<br>Píxeles: %{y}<extra></extra>"
                ))
            
            # Estable/neutral
            if len(a_neu) > 0:
                fig_ahist.add_trace(go.Histogram(
                    x=a_neu,
                    name="⚪ Estable", 
                    marker=dict(color=pal["anom_neu"], line=dict(color="white", width=1)),
                    opacity=0.8,
                    hovertemplate="<b>Estable</b><br>ΔNDVI: %{x:.3f}<br>Píxeles: %{y}<extra></extra>"
                ))
            
            # Mejora significativa
            if len(a_pos) > 0:
                fig_ahist.add_trace(go.Histogram(
                    x=a_pos,
                    name="🟢 Mejora",
                    marker=dict(color=pal["anom_pos"], line=dict(color="white", width=1)),
                    opacity=0.8,
                    hovertemplate="<b>Mejora</b><br>ΔNDVI: %{x:.3f}<br>Píxeles: %{y}<extra></extra>"
                ))

            # Calcular estadística principal
            mean_anomaly = np.mean(a)
            if mean_anomaly > 0.05:
                trend_text = "📈 Cultivo mejorando"
                trend_color = pal["anom_pos"]
            elif mean_anomaly < -0.05:
                trend_text = "📉 Cultivo deteriorando"  
                trend_color = pal["anom_neg"]
            else:
                trend_text = "➡️ Cultivo estable"
                trend_color = pal["anom_neu"]

            fig_ahist.update_layout(
                title=dict(
                    text=f"📊 Análisis de Cambios vs Años Anteriores<br><sub>{trend_text}</sub>",
                    font=dict(size=16, color=pal["accent"])
                ),
                xaxis=dict(title="Diferencia NDVI (ΔNDVI)", range=[-0.3, 0.3], gridcolor="rgba(0,0,0,0.1)"),
                yaxis=dict(title="Frecuencia de Píxeles", gridcolor="rgba(0,0,0,0.1)"),
                barmode="overlay",
                **theme,
                showlegend=True
            )

            # Líneas de referencia con mejor estilo
            fig_ahist.add_vline(x=-0.1, line_dash="dash", line_color=pal["anom_neg"], line_width=2,
                                annotation_text="Deterioro", annotation_position="top left", 
                                annotation_font_color=pal["anom_neg"])
            fig_ahist.add_vline(x=0.0, line_dash="solid", line_color=pal["anom_neu"], line_width=2,
                                annotation_text="Sin cambio", annotation_position="top", 
                                annotation_font_color=pal["anom_neu"])
            fig_ahist.add_vline(x=0.1, line_dash="dash", line_color=pal["anom_pos"], line_width=2,
                                annotation_text="Mejora", annotation_position="top right", 
                                annotation_font_color=pal["anom_pos"])

            charts.append(_graph(fig_ahist, "kpi-anom-hist", 380))


            # ===== ΔNDVI: TARTA POR CLASE =====
            neg = (a <= -0.1).sum()
            neu = ((a > -0.1) & (a < 0.1)).sum()
            pos = (a >= 0.1).sum()

            labels = ["Negativa (≤−0.1)", "Neutral (−0.1..0.1)", "Positiva (≥0.1)"]
            values = [int(neg), int(neu), int(pos)]

            fig_pie_an = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                sort=False,
                direction="clockwise",
                textinfo="percent",
                textposition="inside",
                marker=dict(colors=[pal["anom_neg"], pal["anom_neu"], pal["anom_pos"]])
            ))
            fig_pie_an.update_layout(
                title="Clases ΔNDVI (%)",
                showlegend=True,
                **theme
            )
            fig_pie_an.update_layout(annotations=[dict(text="ΔNDVI", x=0.5, y=0.5, font_size=12, showarrow=False)])

            charts.append(_graph(fig_pie_an, "kpi-anom-classes", 300))

    # Distribución responsiva: 2 gráficos por fila en ≥md (Bootstrap se encarga por ancho)
    return [dbc.Row([dbc.Col(c, md=6) for c in charts], className="g-3")]



# === Paleta y helper de tarjeta KPI con estilo agrícola (igual que Detecciones) ===
AGRI_COLORS = {
    "primary": "#2E7D32",   # verde olivo
    "secondary": "#5D4037",
    "success": "#388E3C",
    "warning": "#F57C00",
    "danger": "#D32F2F",
    "info": "#0277BD",
}

def _kpi_card(title: str, main_value: str, subtitle: str, icon: str, color_key: str = "primary"):
    color = AGRI_COLORS.get(color_key, AGRI_COLORS["primary"])
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                # Icono y título
                html.Div([
                    html.Div([
                        html.I(className=f"fas {icon}", style={
                            "fontSize": "2.0rem", "color": color,
                            "marginBottom": "0.4rem", "textShadow": "0 2px 4px rgba(0,0,0,0.08)"
                        })
                    ], className="text-center"),
                    html.P(title, style={
                        "fontSize": "0.8rem", "fontWeight": "700", "color": "#555",
                        "textTransform": "uppercase", "letterSpacing": "0.6px",
                        "marginBottom": "0.8rem", "textAlign": "center"
                    })
                ]),
                # Valor principal
                html.Div([
                    html.H1(main_value, className="text-center", style={
                        "fontSize": "2.6rem", "fontWeight": "800", "color": color,
                        "marginBottom": "0.2rem", "textShadow": "0 2px 4px rgba(0,0,0,0.08)"
                    })
                ]),
                # Subtítulo
                (html.P(subtitle, className="text-muted text-center mb-0", style={
                    "fontSize": "0.80rem", "fontStyle": "italic", "lineHeight": "1.25"
                }) if subtitle else html.Div())
            ], style={"padding": "1.4rem"}),
            style={
                "borderRadius": "16px",
                "boxShadow": "0 6px 18px rgba(0,0,0,0.12)",
                "border": "none",
                "background": f"linear-gradient(135deg, white 0%, {color}08 100%)",
                "borderTop": f"4px solid {color}",
                "height": "100%",
                "transition": "transform 0.2s ease, box-shadow 0.2s ease",
                "position": "relative",
            },
            className="metric-card card-animation",
        ),
        md=3, sm=6, xs=12, className="mb-3"
    )




# =====================================================================
# SECCIÓN 5: ANIMACIONES TEMPORALES
# =====================================================================
def _array_to_png_bytes(arr, vmin, vmax, cmap, target_w_px, target_h_px,
                        label_text=None, *, inside_mask=None, logger=None):

    import io
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from PIL import Image

    a = np.asarray(arr, dtype="float32")
    h_arr, w_arr = a.shape

    # aplicar cmap y alpha por píxel (NaN -> 0)
    norm = Normalize(vmin=vmin, vmax=vmax, clip=False)
    rgba = cmap(norm(a))  # respeta set_under y set_bad
    if inside_mask is not None and inside_mask.shape == a.shape:
        rgba[~inside_mask, 3] = 0.0  # exterior transparente

    dpi = 100.0
    fig_w = max(1.0, float(target_w_px) / dpi)
    fig_h = max(1.0, float(target_h_px) / dpi)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_axis_off()
    # límites de ejes para ocupar el lienzo completo (coordenadas de imagen)
    ax.set_xlim(0, w_arr)
    ax.set_ylim(h_arr, 0)
    plt.subplots_adjust(0, 0, 1, 1)

    im = ax.imshow(rgba, interpolation="bilinear", aspect="equal", origin="upper")
    im.set_alpha(1.0)

    if label_text:
        ax.text(8, 8, label_text, ha="left", va="top", fontsize=10, color="white",
                bbox=dict(facecolor=(0, 0, 0, 0.35), edgecolor="none", boxstyle="round,pad=0.3"))

    bio = io.BytesIO()
    fig.savefig(bio, format="png", transparent=True, bbox_inches=None, pad_inches=0, facecolor="none")
    plt.close(fig)
    bio.seek(0)

    # Verificar que el PNG final tiene el tamaño esperado
    try:
        im_for_size = Image.open(io.BytesIO(bio.getvalue()))
        png_w, png_h = im_for_size.size
        if logger is not None:
            logger.info(f"[anim] PNG saved size = {png_w}x{png_h} px (target {target_w_px}x{target_h_px})")
            if png_w != int(target_w_px) or png_h != int(target_h_px):
                logger.warning(f"[anim] ⚠️ PNG size mismatch (possible recrop elsewhere)")
    except Exception as _:
        pass

    return bio.getvalue()
def _visual_params_for(index_name: str, cmap_name: str):
    idx = (index_name or "").upper()
    if idx in {"NDVI", "OSAVI", "NDRE"}:
        # Puedes honrar NDVI_CUSTOM_RANGE si quieres un foco: (0.2, 0.85)
        vmin, vmax = (cfg.NDVI_CUSTOM_RANGE or (0.0, 1.0))
        cmap = _create_cmap_from_def(cmap_name)
        alpha = float(getattr(cfg, "NDVI_ALPHA", 0.85))
    elif idx in {"ANOMALY", "ANOMALÍA", "ANOMALIA"}:
        vmin, vmax = (-0.4, 0.4)  # o tu elección en config
        cmap = _create_anomaly_colormap()
        alpha = float(getattr(cfg, "ANOMALY_ALPHA", 0.8))
    else:
        vmin, vmax = (0.0, 1.0)
        cmap = _create_cmap_from_def(cmap_name)
        alpha = float(getattr(cfg, "NDVI_ALPHA", 0.85))
    return vmin, vmax, cmap, alpha





import numpy as np

def _pixel_size_from_ring_mercator_strict(ring, long_side_px=1024, max_side_px=4096):
    if not ring or len(ring) < 3:
        return long_side_px, long_side_px

    lats = [pt[1] for pt in ring]
    lons = [pt[0] for pt in ring]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    R = 6378137.0
    def _mx(lon_deg): return R * math.radians(lon_deg)
    def _my(lat_deg):
        lat = max(min(lat_deg, 89.5), -89.5)
        rad = math.radians(lat)
        return R * math.log(math.tan(math.pi/4.0 + rad/2.0))

    dx = abs(_mx(lon_max) - _mx(lon_min))
    dy = abs(_my(lat_max) - _my(lat_min))
    dy = dy if dy > 1e-12 else 1e-12

    aspect = dx / dy  # width / height

    if aspect >= 1.0:
        w = float(long_side_px)
        h = w / aspect
    else:
        h = float(long_side_px)
        w = h * aspect

    # límite superior opcional, preservando aspecto
    scale = 1.0
    if max(w, h) > max_side_px:
        scale = max_side_px / max(w, h)
    w = int(max(1, round(w * scale)))
    h = int(max(1, round(h * scale)))

    return w, h







# ===== Caché en disco para fincas =====
CACHE_DIR = Path("./.sat_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in (name or "anon")).strip("-")

def _ring_hash(ring: list) -> str:
    m = hashlib.sha256()
    m.update(json.dumps(ring, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    return m.hexdigest()[:16]

def _cache_key(farm_name: str, index: str, start_date: str, end_date: str, masked=True) -> str:
    base = f"{_slugify(farm_name)}__{index.upper()}__{start_date}_{end_date}__{'m' if masked else 'u'}"
    return base

def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.npy"

def cache_get(key: str) -> Optional[np.ndarray]:
    p = _cache_path(key)
    if p.exists():
        try:
            return np.load(p)
        except Exception:
            pass
    return None

def cache_set(key: str, arr: np.ndarray) -> None:
    try:
        np.save(_cache_path(key), np.array(arr, dtype="float32"))
    except Exception:
        pass



def _fetch_window_resilient_generic(
    token,
    ring,
    s0_iso: str,
    s1_iso: str,
    *,
    evalscript,
    width=384,
    height=384,
    index_type="NDVI",
):
    import os, json, hashlib, tempfile
    import numpy as np
    from datetime import date, timedelta
    from pathlib import Path
    from src.utils.satellite_utils import fetch_ndvi_stack_single

    def _to_date(iso: str) -> date:
        y, m, d = [int(x) for x in iso.split("-")]
        return date(y, m, d)

    def _normalize_ring(r):
        if not r or not isinstance(r, (list, tuple)):
            return r
        rr = [[round(float(x), 7), round(float(y), 7)] for x, y in r]
        if rr[0] != rr[-1]:
            rr.append(rr[0])
        return rr

    norm_ring = _normalize_ring(ring)

    try:
        geom_key = _ring_hash(norm_ring)
    except Exception:
        geom_key = hashlib.sha256(
            json.dumps(norm_ring, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]

    eval_hash = hashlib.sha256((evalscript or "").encode("utf-8")).hexdigest()[:8]

    tried = []
    def _try_dir(p):
        try:
            Path(p).mkdir(parents=True, exist_ok=True)
            testfile = Path(p) / ".write_test"
            with open(testfile, "wb") as f:
                f.write(b"ok")
            os.remove(testfile)
            return Path(p)
        except Exception:
            return None

    base_env = os.getenv("SAT_CACHE_DIR", "").strip()
    candidates = [c for c in [base_env,
                              os.path.join(os.path.expanduser("~"), ".sat_cache", "agridash"),
                              os.path.join(".", ".sat_cache")] if c]
    cache_base = None
    for c in candidates:
        tried.append(c)
        cache_base = _try_dir(c)
        if cache_base:
            break
    if not cache_base:
        logger.warning(f"[win-cache] No se pudo usar ninguna ruta de caché. Intentadas: {tried}")
        win_cache = None
    else:
        win_cache = cache_base / "win"
        win_cache.mkdir(parents=True, exist_ok=True)

    # SISTEMA DE CACHÉ INTELIGENTE
    cache_manager = get_intelligent_cache()
    quota_monitor = get_quota_monitor()
    
    # Generar clave de caché inteligente
    cache_key = f"{geom_key}_e{eval_hash}_{s0_iso}_{s1_iso}_{int(width)}x{int(height)}"
    
    # Intentar obtener datos desde caché inteligente
    try:
        cached_data = cache_manager.get_cached_data(
            geometry=norm_ring, 
            date_range=(s0_iso, s1_iso), 
            index_type=index_type,
            resolution=(width, height)
        )
        if cached_data:
            logger.info(f"✅ [intelligent-cache] HIT para {cache_key} ({index_type})")
            return cached_data["arr"], cached_data["dates"], cached_data["attempt"]
    except Exception as cache_error:
        logger.debug(f"⚠️ [intelligent-cache] Error accediendo caché: {cache_error}")
        # Continuar sin caché si hay error

    attempts = [
        dict(pad=0,  max_cloud=95.0, mosaic="leastCC"),
        dict(pad=7,  max_cloud=95.0, mosaic="leastCC"),
        dict(pad=14, max_cloud=95.0, mosaic="mostRecent"),
        dict(pad=21, max_cloud=95.0, mosaic="mostRecent"),
    ]

    s0 = _to_date(s0_iso)
    s1 = _to_date(s1_iso)

    for idx, att in enumerate(attempts, start=1):
        win0 = (s0 - timedelta(days=att["pad"])).isoformat()
        win1 = (s1 + timedelta(days=att["pad"])).isoformat()
        try:
            stack, _ = fetch_ndvi_stack_single(
                token=token,
                geometry_or_bbox=norm_ring,
                start_date=win0,
                end_date=win1,
                evalscript=evalscript,
                width=int(width),                 # << respeta tamaño
                height=int(height),               # << respeta tamaño
                adaptive_resolution=False,        # << clave para evitar cuadrado
                max_cloud_coverage=att["max_cloud"],
                mosaic_order=att["mosaic"],
                target_m_per_px=None,             # << sin forzar resolución
            )
            if stack:
                arr = np.array(stack[0], dtype="float32")
                if np.isfinite(arr).any():
                    # Guardar en caché inteligente
                    cache_data = {
                        "arr": arr,
                        "dates": (win0, win1),
                        "attempt": idx,
                        "metadata": {
                            "geom_key": geom_key,
                            "eval_hash": eval_hash,
                            "requested": {"s0": s0_iso, "s1": s1_iso, "w": int(width), "h": int(height)},
                            "used": {"s0": win0, "s1": win1, "attempt": idx},
                            "resolution": (width, height),
                            "geometry": norm_ring
                        }
                    }
                    
                    try:
                        cache_manager.store_cached_data(
                            geometry=norm_ring,
                            date_range=(s0_iso, s1_iso),
                            index_type=index_type,
                            data=cache_data,
                            resolution=(width, height)
                        )
                        logger.info(f"✅ [intelligent-cache] SAVE para {cache_key} ({index_type})")
                    except Exception as e:
                        logger.warning(f"⚠️ [intelligent-cache] Error guardando {cache_key}: {e}")
                    
                    # Registrar uso de API
                    try:
                        # Calcular costo estimado basado en resolución
                        estimated_cost = (width * height) / 100000  # Factor de escala
                        quota_monitor.log_api_request(
                            endpoint="copernicus_sentinel",
                            cost=max(1.0, estimated_cost)  # Mínimo 1.0
                        )
                        logger.info(f"📊 [api-monitor] Request registrado: {s0_iso} a {s1_iso} ({width}x{height})")
                    except Exception as e:
                        logger.warning(f"⚠️ [api-monitor] Error registrando uso: {e}")
                    
                    return arr, (win0, win1), idx
        except Exception as e:
            logger.debug(f"[hist] intento {idx} falló {win0}..{win1}: {e}")
            
            # Registrar fallo de API
            try:
                quota_monitor.log_api_request(
                    endpoint="copernicus_sentinel_failed",
                    cost=0.1  # Pequeño costo por intento fallido
                )
            except Exception as monitor_error:
                logger.warning(f"⚠️ [api-monitor] Error registrando fallo: {monitor_error}")
            
            continue

    return None, None, None


def _create_colormap_from_stops(color_stops: list):
    import matplotlib
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.colors as mcolors

    # Normaliza stops a [0,1]
    values = [stop[0] for stop in color_stops]
    colors = [stop[1] for stop in color_stops]
    min_val, max_val = min(values), max(values)
    rng = max(1e-9, max_val - min_val)
    normalized_values = [(v - min_val) / rng for v in values]
    normalized_values[0] = 0.0
    normalized_values[-1] = 1.0

    segments = list(zip(normalized_values, colors))
    cmap = LinearSegmentedColormap.from_list("custom_idx", segments, N=256)

    # UNDER => color de 0 (clamp)
    vmin_color = mcolors.to_rgba(colors[0], alpha=1.0)
    cmap.set_under(vmin_color)

    # BAD (NaN) => totalmente transparente
    cmap.set_bad((0, 0, 0, 0))

    return cmap



def _array_to_data_uri_safe(arr2d, vmin=0.0, vmax=1.0, cmap=None, alpha=None):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import io, base64

        if alpha is None:
            try:
                import config_colormaps as cfg
                alpha = float(getattr(cfg, "NDVI_ALPHA", 0.85))
            except Exception:
                alpha = 0.85

        a = np.array(arr2d, dtype="float32")
        h, w = a.shape

        fig, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=100, facecolor='none')
        ax.axis("off")
        plt.subplots_adjust(0, 0, 1, 1)

        im = ax.imshow(a, vmin=vmin, vmax=vmax, cmap=cmap,
                       interpolation="bilinear", aspect='equal', origin='upper')
        im.set_alpha(alpha)  # multiplicativo; respeta alpha=0 de BAD (NaN)

        bio = io.BytesIO()
        fig.savefig(bio, format="png", transparent=True, bbox_inches="tight",
                    pad_inches=0, facecolor='none')
        plt.close(fig); plt.clf()
        bio.seek(0)
        encoded = base64.b64encode(bio.getvalue()).decode("ascii")
        bio.close()
        return "data:image/png;base64," + encoded

    except Exception as e:
        logger.error(f"❌ _array_to_data_uri_safe: {e}")
        return ""
    

def _create_cmap_from_def(cmap_name: str) -> LinearSegmentedColormap:
    cmap_def = cfg.NDVI_COLORMAPS_DEF.get(cmap_name) or cfg.NDVI_COLORMAPS_DEF[cfg.NDVI_COLORMAP]
    # Reutiliza el helper que ya fija UNDER/BAD=gris (lo tienes en este módulo)
    return _create_colormap_from_stops(cmap_def)



def _compute_inside_mask_from_ring(ring_lonlat, width_px, height_px):

    import numpy as np
    from PIL import Image, ImageDraw

    if not ring_lonlat or len(ring_lonlat) < 3:
        return np.ones((height_px, width_px), dtype=bool)

    lons = [p[0] for p in ring_lonlat]
    lats = [p[1] for p in ring_lonlat]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    lon_span = max(1e-9, lon_max - lon_min)
    lat_span = max(1e-9, lat_max - lat_min)

    # a píxeles: col = (lon-lon_min)/span * (w-1), row = (lat_max-lat)/span * (h-1)
    poly_xy = []
    for lon, lat in ring_lonlat + ([ring_lonlat[0]] if ring_lonlat[0] != ring_lonlat[-1] else []):
        x = (lon - lon_min) / lon_span * (width_px - 1)
        y = (lat_max - lat) / lat_span * (height_px - 1)
        poly_xy.append((float(x), float(y)))

    img = Image.new("1", (width_px, height_px), 0)
    drw = ImageDraw.Draw(img)
    drw.polygon(poly_xy, outline=1, fill=1)
    return np.array(img, dtype=bool)


# =====================================================================
# =====================================================================
# SECCIÓN 6: VISUALIZACIONES ORIENTADAS A AGRICULTORES
# =====================================================================

def _create_farmer_kpi_cards(arr: np.ndarray, anomaly: Optional[np.ndarray] = None, index_name: str = "NDVI") -> List:
    """
    KPIs simples y claros para agricultores
    """
    v = _finite(np.array(arr, dtype="float32"))
    if v.size == 0:
        return [dbc.Alert("No hay datos válidos para analizar", color="warning")]
    
    # Solo lo más básico para agricultores
    valor_promedio = float(np.mean(v))
    zona_buena = (v >= 0.5).sum()
    zona_problema = (v < 0.3).sum()
    total_pixels = v.size
    
    pct_buena = _percent(zona_buena, total_pixels)
    pct_problema = _percent(zona_problema, total_pixels)
    
    # Estado simple
    if valor_promedio >= 0.6:
        estado, color, icono = "Saludable", "success", "fas fa-seedling"
    elif valor_promedio >= 0.4:
        estado, color, icono = "Regular", "warning", "fas fa-leaf"
    else:
        estado, color, icono = "Necesita atención", "danger", "fas fa-exclamation-triangle"
    
    # Solo 3 KPIs esenciales
    cards = [
        dbc.Row([
            dbc.Col([
                _farmer_kpi_card(
                    title="Estado del Cultivo",
                    main_value=estado,
                    subtitle=f"NDVI: {valor_promedio:.2f}",
                    icon=icono,
                    color_key=color
                )
            ], lg=4, md=12),
            
            dbc.Col([
                _farmer_kpi_card(
                    title="Área en Buen Estado",
                    main_value=f"{pct_buena:.0f}%",
                    subtitle="Verde y saludable",
                    icon="fas fa-check-circle",
                    color_key="success"
                )
            ], lg=4, md=12),
            
            dbc.Col([
                _farmer_kpi_card(
                    title="Área con Problemas",
                    main_value=f"{pct_problema:.0f}%",
                    subtitle="Requiere atención",
                    icon="fas fa-exclamation-triangle" if pct_problema > 15 else "fas fa-check-circle",
                    color_key="danger" if pct_problema > 15 else "success"
                )
            ], lg=4, md=12)
        ], className="g-3")
    ]
    
    return cards

def _farmer_kpi_card(title: str, main_value: str, subtitle: str, icon: str, color_key: str = "primary", size: str = "compact"):
    """
    Crea una tarjeta KPI compacta y profesional para agricultores.
    
    Args:
        title: Título de la métrica
        main_value: Valor principal a mostrar
        subtitle: Descripción adicional
        icon: Icono FontAwesome
        color_key: Color del tema (success, warning, danger, info, primary)
        size: Tamaño de la tarjeta (compact por defecto)
    """
    color = AGRI_COLORS.get(color_key, AGRI_COLORS["primary"])
    
    return dbc.Card([
        dbc.CardBody([
            # Header con icono y título en una línea
            html.Div([
                html.I(className=f"{icon} me-2", style={
                    "fontSize": "1.2rem",
                    "color": color
                }),
                html.Span(title, style={
                    "fontSize": "0.75rem",
                    "fontWeight": "600",
                    "color": "#666",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px"
                })
            ], className="d-flex align-items-center mb-2"),
            
            # Valor principal más compacto
            html.H3(main_value, className="mb-1", style={
                "fontSize": "1.8rem",
                "fontWeight": "700",
                "color": color,
                "lineHeight": "1"
            }),
            
            # Subtítulo más pequeño
            html.P(subtitle, className="text-muted mb-0", style={
                "fontSize": "0.7rem",
                "lineHeight": "1.2"
            })
        ], style={"padding": "1rem"})
    ], style={
        "borderRadius": "8px",
        "border": f"2px solid {color}20",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "background": "white",
        "borderLeft": f"4px solid {color}",
        "height": "100%",
        "transition": "all 0.2s ease"
    }, className="farmer-kpi-card h-100")

def _create_farmer_charts(arr: np.ndarray, anomaly: Optional[np.ndarray] = None, index_name: str = "NDVI") -> List:
    """
    Gráfico muy simple: solo barras con categorías básicas
    """
    v = _finite(np.array(arr, dtype="float32"))
    if v.size == 0:
        return [dbc.Alert("No hay datos", color="warning")]
    
    theme = _get_plotly_theme()
    
    # Clasificación simple en 3 categorías
    bueno = (v >= 0.5).sum()
    regular = ((v >= 0.3) & (v < 0.5)).sum()
    malo = (v < 0.3).sum()
    total = v.size
    
    # Porcentajes
    pct_bueno = (bueno / total) * 100
    pct_regular = (regular / total) * 100
    pct_malo = (malo / total) * 100
    
    # Gráfico de barras simple
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Bueno", "Regular", "Problemático"],
        y=[pct_bueno, pct_regular, pct_malo],
        marker_color=['#27AE60', '#F39C12', '#E74C3C'],
        text=[f"{p:.1f}%" for p in [pct_bueno, pct_regular, pct_malo]],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Estado de tu Cultivo",
        yaxis_title="Porcentaje del área",
        height=350,
        showlegend=False,
        **theme
    )
    
    return [_graph(fig, "farmer-simple-bars", 350)]




def create_farmer_historical_charts(temporal_data: pd.DataFrame, index_name: str = "NDVI") -> List:
    """
    Crea gráficos mejorados de evolución temporal con análisis de salud del cultivo
    y líneas apiladas por estado de salud (Excelente, Bueno, Moderado, Problemático)
    """
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime
        
        theme = _get_plotly_theme()
        
        if temporal_data.empty or 'ndvi_mean' not in temporal_data.columns:
            return [dbc.Alert("No hay datos históricos para análisis temporal", color="info")]
        
        df = temporal_data.dropna(subset=['ndvi_mean']).copy()
        if df.empty:
            return [dbc.Alert("No hay datos válidos para el análisis temporal", color="warning")]
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        # Umbrales de salud por índice
        THRESHOLDS = {
            "NDVI": {"excellent": 0.7, "good": 0.5, "moderate": 0.3},
            "OSAVI": {"excellent": 0.6, "good": 0.4, "moderate": 0.25},
            "NDRE": {"excellent": 0.5, "good": 0.3, "moderate": 0.2}
        }
        thresh = THRESHOLDS.get(index_name, THRESHOLDS["NDVI"])
        
        # Calcular porcentajes de salud para cada período
        df['excellent_pct'] = df.get('healthy_pct', 0) * 0.3  # Aproximación inicial
        df['good_pct'] = df.get('healthy_pct', 0) * 0.7      # Resto del área saludable
        df['moderate_pct'] = 100 - df.get('healthy_pct', 0) - df.get('stress_pct', 0)
        df['poor_pct'] = df.get('stress_pct', 0)
        
        # Si tenemos datos más detallados, recalcular
        if 'ndvi_mean' in df.columns:
            for idx, row in df.iterrows():
                mean_val = row['ndvi_mean']
                if mean_val >= thresh["excellent"]:
                    df.loc[idx, 'excellent_pct'] = 60
                    df.loc[idx, 'good_pct'] = 30
                    df.loc[idx, 'moderate_pct'] = 10
                    df.loc[idx, 'poor_pct'] = 0
                elif mean_val >= thresh["good"]:
                    df.loc[idx, 'excellent_pct'] = 20
                    df.loc[idx, 'good_pct'] = 50
                    df.loc[idx, 'moderate_pct'] = 25
                    df.loc[idx, 'poor_pct'] = 5
                elif mean_val >= thresh["moderate"]:
                    df.loc[idx, 'excellent_pct'] = 5
                    df.loc[idx, 'good_pct'] = 25
                    df.loc[idx, 'moderate_pct'] = 50
                    df.loc[idx, 'poor_pct'] = 20
                else:
                    df.loc[idx, 'excellent_pct'] = 0
                    df.loc[idx, 'good_pct'] = 10
                    df.loc[idx, 'moderate_pct'] = 40
                    df.loc[idx, 'poor_pct'] = 50

        charts = []
        
        # 1. GRÁFICO DE LÍNEAS APILADAS POR ESTADO DE SALUD
        fig_stacked = go.Figure()
        
        # Líneas apiladas para cada estado de salud
        fig_stacked.add_trace(go.Scatter(
            x=df['date'], y=df['excellent_pct'],
            mode='lines', name='Excelente (>0.7)',
            line=dict(width=0), fill='tozeroy', fillcolor='rgba(46, 125, 50, 0.8)',
            hovertemplate="<b>Excelente</b><br>%{y:.1f}% del área<br>%{x}<extra></extra>"
        ))
        
        fig_stacked.add_trace(go.Scatter(
            x=df['date'], y=df['excellent_pct'] + df['good_pct'],
            mode='lines', name='Bueno (0.5-0.7)',
            line=dict(width=0), fill='tonexty', fillcolor='rgba(102, 187, 106, 0.7)',
            hovertemplate="<b>Bueno</b><br>%{customdata:.1f}% del área<br>%{x}<extra></extra>",
            customdata=df['good_pct']
        ))
        
        fig_stacked.add_trace(go.Scatter(
            x=df['date'], y=df['excellent_pct'] + df['good_pct'] + df['moderate_pct'],
            mode='lines', name='Moderado (0.3-0.5)',
            line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 193, 7, 0.6)',
            hovertemplate="<b>Moderado</b><br>%{customdata:.1f}% del área<br>%{x}<extra></extra>",
            customdata=df['moderate_pct']
        ))
        
        fig_stacked.add_trace(go.Scatter(
            x=df['date'], y=[100] * len(df),
            mode='lines', name='Problemático (<0.3)',
            line=dict(width=0), fill='tonexty', fillcolor='rgba(244, 67, 54, 0.5)',
            hovertemplate="<b>Problemático</b><br>%{customdata:.1f}% del área<br>%{x}<extra></extra>",
            customdata=df['poor_pct']
        ))
        
        # Función helper para evitar conflictos con parámetros del theme
        def safe_update_layout(fig, **layout_params):
            """Actualiza layout evitando conflictos con el theme"""
            theme_layout = dict(theme) if theme else {}
            # Remover parámetros que se pasan directamente para evitar conflictos
            for param in layout_params.keys():
                theme_layout.pop(param, None)
            # Combinar parámetros directos con theme seguro
            final_params = {**theme_layout, **layout_params}
            fig.update_layout(**final_params)
        
        safe_update_layout(fig_stacked,
            title="Evolución de la Salud del Cultivo por Zonas",
            xaxis_title="Período", 
            yaxis_title="Porcentaje del Área (%)",
            height=450,
            hovermode='x unified',
            yaxis=dict(range=[0, 100]),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        
        stacked_card = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-chart-area me-2"),
                    "Distribución de Salud del Cultivo"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dcc.Graph(figure=fig_stacked, config={'displayModeBar': False}),
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Este gráfico muestra cómo se distribuye la salud de tu cultivo en el tiempo. ",
                    html.Strong("Verde = zonas más productivas, Amarillo = necesita atención, Rojo = problemas serios")
                ], color="info", className="mt-2")
            ])
        ], className="mb-4")
        
        charts.append(stacked_card)
        
        # 2. ANÁLISIS TEMPORAL DETALLADO
        if len(df) >= 3:  # Solo si tenemos suficientes datos
            # Preparar datos para análisis temporal
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            df['season'] = df['month'].map({
                12: 'Invierno', 1: 'Invierno', 2: 'Invierno',
                3: 'Primavera', 4: 'Primavera', 5: 'Primavera', 
                6: 'Verano', 7: 'Verano', 8: 'Verano',
                9: 'Otoño', 10: 'Otoño', 11: 'Otoño'
            })
            
            # Análisis mensual (si hay datos suficientes)
            monthly_analysis = df.groupby('month').agg({
                'ndvi_mean': ['mean', 'count'],
                'excellent_pct': 'mean',
                'good_pct': 'mean', 
                'moderate_pct': 'mean',
                'poor_pct': 'mean'
            }).round(2)
            
            if len(monthly_analysis) >= 3:
                fig_monthly = go.Figure()
                
                months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                
                for month_num in monthly_analysis.index:
                    month_data = monthly_analysis.loc[month_num]
                    month_name = months[month_num - 1]
                    
                    fig_monthly.add_trace(go.Bar(
                        x=[month_name],
                        y=[month_data[('ndvi_mean', 'mean')]],
                        name=f'{month_name}',
                        marker_color=_get_color_for_ndvi(month_data[('ndvi_mean', 'mean')]),
                        text=f"{month_data[('ndvi_mean', 'mean')]:.2f}",
                        textposition='outside',
                        hovertemplate=f"<b>{month_name}</b><br>NDVI: %{{y:.3f}}<br>Observaciones: {month_data[('ndvi_mean', 'count')]}<extra></extra>"
                    ))
                
                safe_update_layout(fig_monthly,
                    title="Patrón Mensual del Cultivo",
                    xaxis_title="Mes",
                    yaxis_title="NDVI Promedio",
                    height=400,
                    showlegend=False
                )
                
                monthly_card = dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className="fas fa-calendar me-2"),
                            "Análisis Mensual"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_monthly, config={'displayModeBar': False}),
                        _get_monthly_recommendations(monthly_analysis)
                    ])
                ], className="mb-4")
                
                charts.append(monthly_card)

        # 3. LÍNEA DE TENDENCIA SIMPLE (siempre incluir)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df['date'],
            y=df['ndvi_mean'],
            mode='lines+markers',
            name='NDVI',
            line=dict(color='#27AE60', width=3),
            marker=dict(size=8, color='#27AE60'),
            hovertemplate="<b>%{x}</b><br>NDVI: %{y:.3f}<extra></extra>"
        ))
        
        # Añadir línea de tendencia
        if len(df) >= 3:
            z = np.polyfit(range(len(df)), df['ndvi_mean'], 1)
            trend_line = np.poly1d(z)(range(len(df)))
            
            fig_trend.add_trace(go.Scatter(
                x=df['date'],
                y=trend_line,
                mode='lines',
                name='Tendencia',
                line=dict(color='#E74C3C', width=2, dash='dash'),
                hovertemplate="<b>Tendencia</b><br>%{y:.3f}<extra></extra>"
            ))
        
        # Añadir zonas de referencia
        fig_trend.add_hrect(y0=thresh["excellent"], y1=1, fillcolor="rgba(46, 125, 50, 0.1)", 
                           line_width=0, annotation_text="Excelente", annotation_position="right")
        fig_trend.add_hrect(y0=thresh["good"], y1=thresh["excellent"], fillcolor="rgba(102, 187, 106, 0.1)", 
                           line_width=0, annotation_text="Bueno", annotation_position="right")
        fig_trend.add_hrect(y0=thresh["moderate"], y1=thresh["good"], fillcolor="rgba(255, 193, 7, 0.1)", 
                           line_width=0, annotation_text="Moderado", annotation_position="right")
        fig_trend.add_hrect(y0=0, y1=thresh["moderate"], fillcolor="rgba(244, 67, 54, 0.1)", 
                           line_width=0, annotation_text="Problemático", annotation_position="right")
        
        safe_update_layout(fig_trend,
            title=f"Evolución del {index_name} con Tendencia",
            xaxis_title="Período",
            yaxis_title=f"Valor {index_name}",
            height=400,
            yaxis=dict(range=[0, 1])
        )
        
        trend_card = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-chart-line me-2"),
                    f"Tendencia General del {index_name}"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dcc.Graph(figure=fig_trend, config={'displayModeBar': False}),
                _get_trend_analysis(df, index_name)
            ])
        ], className="mb-4")
        
        charts.append(trend_card)
        
        return charts
    
    except Exception as e:
        logger.error(f"Error en gráficos históricos mejorados: {e}")
        import traceback
        traceback.print_exc()
        return [dbc.Alert("Error al generar gráficos históricos mejorados", color="danger")]


def _get_color_for_ndvi(ndvi_value):
    """Obtiene color basado en el valor NDVI"""
    if ndvi_value >= 0.7:
        return '#2E7D32'  # Verde oscuro - Excelente
    elif ndvi_value >= 0.5:
        return '#66BB6A'  # Verde - Bueno
    elif ndvi_value >= 0.3:
        return '#FFC107'  # Amarillo - Moderado
    else:
        return '#F44336'  # Rojo - Problemático


def _get_monthly_recommendations(monthly_analysis):
    """Genera recomendaciones basadas en el análisis mensual"""
    try:
        if monthly_analysis.empty:
            return html.Div()
        
        # Encontrar el mejor y peor mes
        best_month_idx = monthly_analysis[('ndvi_mean', 'mean')].idxmax()
        worst_month_idx = monthly_analysis[('ndvi_mean', 'mean')].idxmin()
        
        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        best_month = months[best_month_idx - 1]
        worst_month = months[worst_month_idx - 1]
        best_value = monthly_analysis.loc[best_month_idx, ('ndvi_mean', 'mean')]
        worst_value = monthly_analysis.loc[worst_month_idx, ('ndvi_mean', 'mean')]
        
        recommendations = []
        
        # Análisis de temporada alta
        if best_value >= 0.6:
            recommendations.append(f"🌟 **{best_month}** es tu mejor mes (NDVI: {best_value:.2f}). Aprovecha para:")
            if best_month_idx in [3, 4, 5]:  # Primavera
                recommendations.append("• Fertilización y siembra de cultivos estacionales")
            elif best_month_idx in [6, 7, 8]:  # Verano
                recommendations.append("• Cosecha en el momento óptimo de maduración")
            elif best_month_idx in [9, 10, 11]:  # Otoño
                recommendations.append("• Preparación del suelo para próxima temporada")
            else:  # Invierno
                recommendations.append("• Planificación y mantenimiento de infraestructura")
        
        # Análisis de temporada baja
        if worst_value < 0.4:
            recommendations.append(f"⚠️ **{worst_month}** requiere atención (NDVI: {worst_value:.2f}). Considera:")
            if worst_month_idx in [12, 1, 2]:  # Invierno
                recommendations.append("• Es normal la baja actividad, planifica la próxima temporada")
            elif worst_month_idx in [6, 7, 8]:  # Verano
                recommendations.append("• Revisar sistema de riego, posible estrés hídrico")
                recommendations.append("• Aplicar mulching para conservar humedad")
            else:
                recommendations.append("• Investigar causas: plagas, enfermedades o déficit nutricional")
                recommendations.append("• Considerar análisis de suelo y agua")
        
        return dbc.Alert([
            html.H6([html.I(className="fas fa-lightbulb me-2"), "Recomendaciones Mensuales"]),
            html.Ul([html.Li(rec) for rec in recommendations])
        ], color="info", className="mt-3")
        
    except Exception as e:
        logger.error(f"Error generando recomendaciones mensuales: {e}")
        return html.Div()



def _get_trend_analysis(df, index_name):
    """Analiza la tendencia general del índice"""
    try:
        if len(df) < 3:
            return html.Div()
        
        import numpy as np
        
        # Calcular tendencia linear
        x = np.arange(len(df))
        y = df['ndvi_mean'].values
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Análisis de la tendencia
        if abs(slope) < 0.001:  # Tendencia plana
            trend_desc = "estable"
            trend_color = "info"
            trend_icon = "fas fa-minus"
            advice = "El cultivo mantiene un rendimiento constante. Considera optimizaciones graduales."
        elif slope > 0.005:  # Tendencia muy positiva
            trend_desc = "en fuerte crecimiento"
            trend_color = "success" 
            trend_icon = "fas fa-arrow-trend-up"
            advice = "¡Excelente! El cultivo está mejorando. Mantén las prácticas actuales."
        elif slope > 0:  # Tendencia ligeramente positiva
            trend_desc = "en mejora gradual"
            trend_color = "success"
            trend_icon = "fas fa-arrow-up"
            advice = "Tendencia positiva. Identifica qué está funcionando bien y replícalo."
        elif slope < -0.005:  # Tendencia muy negativa
            trend_desc = "en declive"
            trend_color = "danger"
            trend_icon = "fas fa-arrow-trend-down"
            advice = "Atención urgente necesaria. Revisa riego, nutrición y posibles plagas."
        else:  # Tendencia ligeramente negativa
            trend_desc = "con ligero deterioro"
            trend_color = "warning"
            trend_icon = "fas fa-arrow-down"
            advice = "Monitoreo cercano recomendado. Considera ajustes en manejo."
        
        # Calcular variabilidad
        variability = np.std(y)
        if variability < 0.05:
            stability_desc = "muy estable"
        elif variability < 0.1:
            stability_desc = "moderadamente estable"
        else:
            stability_desc = "con alta variabilidad"
        
        return dbc.Alert([
            html.H6([
                html.I(className=f"{trend_icon} me-2"),
                f"Tendencia: {trend_desc}"
            ]),
            html.P([
                f"Tu cultivo está **{trend_desc}** y es **{stability_desc}**. ",
                advice
            ]),
            html.Small([
                f"Pendiente: {slope:+.4f} {index_name}/período • ",
                f"Variabilidad: {variability:.3f}"
            ], className="text-muted")
        ], color=trend_color, className="mt-3")
        
    except Exception as e:
        logger.error(f"Error en análisis de tendencia: {e}")
        return html.Div()


# =====================================================================
# SECCIÓN 6: FUNCIONES PARA AGRICULTORES MEJORADAS
# =====================================================================

def _create_farmer_kpi_cards(main_array, anomaly_array=None, main_index="NDVI"):
    """
    Crea tarjetas KPI mejoradas orientadas a agricultores con información práctica y accionable.
    
    Args:
        main_array: Array principal del índice (ej: NDVI)
        anomaly_array: Array de anomalías para comparación histórica
        main_index: Nombre del índice principal
        
    Returns:
        List de componentes Dash con KPIs informativos para agricultores
    """
    try:
        import numpy as np
        from dash import html
        import dash_bootstrap_components as dbc
        
        # Validar datos
        if main_array is None or len(main_array.flatten()) == 0:
            return [dbc.Alert("No hay datos válidos para análisis", color="warning")]
        
        # Obtener datos válidos (filtrar NaN e infinitos)
        valid_mask = np.isfinite(main_array)
        if not np.any(valid_mask):
            return [dbc.Alert("No hay datos válidos en el área seleccionada", color="warning")]
        
        valid_data = main_array[valid_mask]
        
        # Calcular estadísticas básicas
        mean_val = float(np.mean(valid_data))
        total_pixels = len(valid_data)
        
        # Umbrales optimizados por índice para cultivos mediterráneos
        THRESHOLDS = {
            "NDVI": {"excellent": 0.7, "good": 0.5, "moderate": 0.3, "poor": 0.1},
            "OSAVI": {"excellent": 0.6, "good": 0.4, "moderate": 0.25, "poor": 0.1},
            "NDRE": {"excellent": 0.5, "good": 0.3, "moderate": 0.2, "poor": 0.05}
        }
        
        thresh = THRESHOLDS.get(main_index, THRESHOLDS["NDVI"])
        
        # Calcular áreas por categoría (en hectáreas - asumiendo ~10m resolución)
        excellent_area = (np.sum(valid_data >= thresh["excellent"]) / total_pixels) * 100
        good_area = (np.sum((valid_data >= thresh["good"]) & (valid_data < thresh["excellent"])) / total_pixels) * 100
        moderate_area = (np.sum((valid_data >= thresh["moderate"]) & (valid_data < thresh["good"])) / total_pixels) * 100
        poor_area = (np.sum(valid_data < thresh["moderate"]) / total_pixels) * 100
        
        # Estado general del cultivo con recomendaciones específicas
        healthy_area = excellent_area + good_area
        problem_area = poor_area
        
        if healthy_area >= 80:
            status = "Cultivo Excelente"
            status_color = "#2E7D32"  # Verde oscuro
            status_icon = "fas fa-award"
            priority_action = "Mantener las prácticas actuales"
            recommendation = "Tu cultivo está en perfecto estado. Continúa con el programa de manejo actual."
        elif healthy_area >= 60:
            status = "Cultivo Saludable"
            status_color = "#388E3C"  # Verde medio
            status_icon = "fas fa-thumbs-up"
            priority_action = "Monitoreo regular"
            recommendation = "Buen estado general. Revisa las áreas moderadas para optimizar rendimiento."
        elif healthy_area >= 40:
            status = "Requiere Atención"
            status_color = "#F57C00"  # Naranja
            status_icon = "fas fa-exclamation-triangle"
            priority_action = "Evaluar riego y nutrición"
            recommendation = "Hay áreas que necesitan mejoras. Considera análisis de suelo y ajustes de fertilización."
        else:
            status = "Intervención Urgente"
            status_color = "#D32F2F"  # Rojo
            status_icon = "fas fa-warning"
            priority_action = "Inspección inmediata del campo"
            recommendation = "Estado crítico. Se requiere inspección de campo y medidas correctivas urgentes."
        
        # Calcular tendencia si hay datos de anomalía
        trend_info = None
        if anomaly_array is not None:
            try:
                valid_anomaly = anomaly_array[np.isfinite(anomaly_array)]
                if len(valid_anomaly) > 0:
                    anomaly_mean = float(np.mean(valid_anomaly))
                    if anomaly_mean > 0.05:
                        trend_info = {
                            "status": "Mejorando vs años anteriores",
                            "color": "#2E7D32",
                            "icon": "fas fa-trending-up",
                            "value": f"+{anomaly_mean:.3f}",
                            "interpretation": "Tu cultivo está mejor que en años anteriores"
                        }
                    elif anomaly_mean < -0.05:
                        trend_info = {
                            "status": "Deterioro vs años anteriores",
                            "color": "#D32F2F",
                            "icon": "fas fa-trending-down",
                            "value": f"{anomaly_mean:.3f}",
                            "interpretation": "Tu cultivo está peor que en años anteriores"
                        }
                    else:
                        trend_info = {
                            "status": "Similar a años anteriores",
                            "color": "#1976D2",
                            "icon": "fas fa-minus",
                            "value": f"{anomaly_mean:+.3f}",
                            "interpretation": "Comportamiento normal comparado con el histórico"
                        }
            except Exception as e:
                logger.warning(f"Error calculando comparación histórica: {e}")
        
        cards = []
        
        # Tarjeta 1: Estado general con acción prioritaria
        main_card = dbc.Card([
            dbc.CardBody([
                # Encabezado con estado general
                html.Div([
                    html.H3([
                        html.I(className=f"{status_icon} me-2", style={"color": status_color}),
                        status
                    ], className="mb-2", style={"color": status_color}),
                    html.P(f"Índice {main_index}: {mean_val:.3f}", 
                          className="text-muted mb-3", style={"fontSize": "1.1rem"})
                ]),
                
                # Métricas principales en columnas
                dbc.Row([
                    dbc.Col([
                        html.H4(f"{healthy_area:.0f}%", className="text-success fw-bold mb-1"),
                        html.P("Área Saludable", className="text-muted small mb-0")
                    ], md=4, className="text-center"),
                    dbc.Col([
                        html.H4(f"{moderate_area:.0f}%", className="text-warning fw-bold mb-1"),
                        html.P("Área Regular", className="text-muted small mb-0")
                    ], md=4, className="text-center"),
                    dbc.Col([
                        html.H4(f"{problem_area:.0f}%", className="text-danger fw-bold mb-1"),
                        html.P("Área Problemática", className="text-muted small mb-0")
                    ], md=4, className="text-center")
                ], className="mb-3"),
                
                # Acción prioritaria destacada
                dbc.Alert([
                    html.Div([
                        html.H6([
                            html.I(className="fas fa-clipboard-list me-2"),
                            "Acción Prioritaria"
                        ], className="mb-2 text-primary"),
                        html.P(priority_action, className="fw-bold mb-2", 
                              style={"fontSize": "1.1rem", "color": status_color}),
                        html.P(recommendation, className="mb-0 small")
                    ])
                ], color="light", className="mb-3"),
                
                # Comparación histórica si existe
                trend_info and html.Div([
                    html.Hr(),
                    html.Div([
                        html.H6([
                            html.I(className=f"{trend_info['icon']} me-2", 
                                  style={"color": trend_info["color"]}),
                            trend_info["status"]
                        ], className="mb-1"),
                        html.P([
                            "Cambio: ",
                            html.Span(trend_info["value"], 
                                     style={"color": trend_info["color"], "fontWeight": "bold"}),
                            " - ", trend_info["interpretation"]
                        ], className="small text-muted mb-0")
                    ])
                ]) or html.Div()
            ])
        ], style={
            "borderLeft": f"5px solid {status_color}",
            "backgroundColor": f"{status_color}0A",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.1)"
        }, className="mb-4")
        
        cards.append(main_card)
        
        # Tarjeta 2: Distribución visual del área
        distribution_card = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-chart-pie me-2"),
                    "Mapa de Salud del Cultivo"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                # Barras de progreso con iconos y colores
                html.Div([
                    html.Div([
                        html.P([
                            html.Span("🌟 ", style={"fontSize": "1.3rem"}),
                            f"Área Excelente: {excellent_area:.1f}%"
                        ], className="mb-1 fw-bold"),
                        dbc.Progress(value=excellent_area, color="success", 
                                   style={"height": "12px"}, className="mb-3")
                    ]),
                    
                    html.Div([
                        html.P([
                            html.Span("👍 ", style={"fontSize": "1.3rem"}),
                            f"Área Buena: {good_area:.1f}%"
                        ], className="mb-1 fw-bold"),
                        dbc.Progress(value=good_area, color="info", 
                                   style={"height": "12px"}, className="mb-3")
                    ]),
                    
                    html.Div([
                        html.P([
                            html.Span("⚠️ ", style={"fontSize": "1.3rem"}),
                            f"Área Regular: {moderate_area:.1f}%"
                        ], className="mb-1 fw-bold"),
                        dbc.Progress(value=moderate_area, color="warning", 
                                   style={"height": "12px"}, className="mb-3")
                    ]),
                    
                    html.Div([
                        html.P([
                            html.Span("🚨 ", style={"fontSize": "1.3rem"}),
                            f"Área con Problemas: {poor_area:.1f}%"
                        ], className="mb-1 fw-bold"),
                        dbc.Progress(value=poor_area, color="danger", 
                                   style={"height": "12px"}, className="mb-3")
                    ])
                ]),
                
                # Interpretación práctica
                html.Div([
                    html.Hr(),
                    html.P([
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        _get_area_interpretation(healthy_area, problem_area, main_index)
                    ], className="small text-muted mb-0", style={"fontStyle": "italic"})
                ])
            ])
        ], className="mb-3", style={"borderRadius": "12px"})
        
        cards.append(distribution_card)
        
        return cards
        
    except Exception as e:
        logger.error(f"Error creando KPIs para agricultores: {e}")
        return [dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error generando KPIs: {str(e)}"
        ], color="danger")]


def _get_area_interpretation(healthy_area, problem_area, index_name):
    """
    Proporciona interpretación práctica para agricultores basada en el porcentaje de áreas.
    
    Args:
        healthy_area: Porcentaje de área saludable
        problem_area: Porcentaje de área problemática
        index_name: Nombre del índice analizado
        
    Returns:
        str: Interpretación práctica para el agricultor
    """
    if healthy_area >= 85:
        return f"Excelente homogeneidad del cultivo. El {index_name} muestra una distribución muy uniforme y saludable."
    elif healthy_area >= 70:
        return f"Buen estado general. Las áreas problemáticas ({problem_area:.0f}%) pueden necesitar atención específica."
    elif healthy_area >= 50:
        return f"Estado mixto. Considera un manejo diferenciado por zonas para optimizar las áreas regulares."
    elif problem_area >= 30:
        return f"Atención: {problem_area:.0f}% del área muestra problemas. Revisa riego, nutrición o presencia de plagas."
    else:
        return f"Se requiere intervención. Considera análisis de suelo y evaluación de factores limitantes."


def _create_farmer_charts(main_array, anomaly_array=None, main_index="NDVI"):
    """
    Crea gráficos informativos y prácticos orientados a agricultores.
    
    Args:
        main_array: Array principal del índice
        anomaly_array: Array de anomalías para comparación histórica
        main_index: Nombre del índice
        
    Returns:
        List de componentes Dash con gráficos informativos para agricultores
    """
    try:
        import numpy as np
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        from dash import html, dcc
        import dash_bootstrap_components as dbc
        
        # Validar datos
        if main_array is None or len(main_array.flatten()) == 0:
            return [dbc.Alert("No hay datos válidos para gráficos", color="warning")]
        
        valid_mask = np.isfinite(main_array)
        if not np.any(valid_mask):
            return [dbc.Alert("No hay datos válidos para gráficos", color="warning")]
        
        valid_data = main_array[valid_mask]
        charts = []
        
        # Umbrales para cada índice
        THRESHOLDS = {
            "NDVI": {"excellent": 0.7, "good": 0.5, "moderate": 0.3, "poor": 0.1},
            "OSAVI": {"excellent": 0.6, "good": 0.4, "moderate": 0.25, "poor": 0.1},
            "NDRE": {"excellent": 0.5, "good": 0.3, "moderate": 0.2, "poor": 0.05}
        }
        thresh = THRESHOLDS.get(main_index, THRESHOLDS["NDVI"])
        
        # ===== GRÁFICO 1: MAPA DE CALOR DE ZONAS DE CULTIVO =====
        fig1 = go.Figure()
        
        # Clasificar datos en categorías para agricultores
        excellent_data = valid_data[valid_data >= thresh["excellent"]]
        good_data = valid_data[(valid_data >= thresh["good"]) & (valid_data < thresh["excellent"])]
        moderate_data = valid_data[(valid_data >= thresh["moderate"]) & (valid_data < thresh["good"])]
        poor_data = valid_data[valid_data < thresh["moderate"]]
        
        # Crear histograma apilado por categorías de salud
        if len(excellent_data) > 0:
            fig1.add_trace(go.Histogram(
                x=excellent_data, name="🌟 Zona Excelente", 
                marker_color="#2E7D32", opacity=0.8,
                hovertemplate=f"<b>Zona Excelente</b><br>{main_index}: %{{x:.3f}}<br>Píxeles: %{{y}}<extra></extra>"
            ))
        if len(good_data) > 0:
            fig1.add_trace(go.Histogram(
                x=good_data, name="👍 Zona Buena", 
                marker_color="#388E3C", opacity=0.8,
                hovertemplate=f"<b>Zona Buena</b><br>{main_index}: %{{x:.3f}}<br>Píxeles: %{{y}}<extra></extra>"
            ))
        if len(moderate_data) > 0:
            fig1.add_trace(go.Histogram(
                x=moderate_data, name="⚠️ Zona Regular", 
                marker_color="#F57C00", opacity=0.8,
                hovertemplate=f"<b>Zona Regular</b><br>{main_index}: %{{x:.3f}}<br>Píxeles: %{{y}}<extra></extra>"
            ))
        if len(poor_data) > 0:
            fig1.add_trace(go.Histogram(
                x=poor_data, name="🚨 Zona Problemática", 
                marker_color="#D32F2F", opacity=0.8,
                hovertemplate=f"<b>Zona Problemática</b><br>{main_index}: %{{x:.3f}}<br>Píxeles: %{{y}}<extra></extra>"
            ))
        
        # Líneas de referencia con etiquetas claras
        mean_val = float(np.mean(valid_data))
        fig1.add_vline(x=thresh["excellent"], line_dash="dash", line_color="#2E7D32", line_width=2,
                      annotation_text=f"Umbral Excelente ({thresh['excellent']})", 
                      annotation_position="top")
        fig1.add_vline(x=thresh["good"], line_dash="dash", line_color="#388E3C", line_width=2,
                      annotation_text=f"Umbral Bueno ({thresh['good']})", 
                      annotation_position="top")
        fig1.add_vline(x=thresh["moderate"], line_dash="dash", line_color="#F57C00", line_width=2,
                      annotation_text=f"Umbral Regular ({thresh['moderate']})", 
                      annotation_position="top")
        fig1.add_vline(x=mean_val, line_dash="solid", line_color="#1976D2", line_width=3,
                      annotation_text=f"Tu Promedio: {mean_val:.3f}", 
                      annotation_position="bottom")
        
        # Interpretación del promedio
        if mean_val >= thresh["excellent"]:
            interpretation = f"¡Excelente! Tu cultivo supera el umbral de calidad superior."
        elif mean_val >= thresh["good"]:
            interpretation = f"Buen estado. Tu cultivo está en el rango saludable."
        elif mean_val >= thresh["moderate"]:
            interpretation = f"Estado regular. Hay potencial de mejora con manejo específico."
        else:
            interpretation = f"Atención requerida. Tu cultivo necesita intervención."
        
        fig1.update_layout(
            title=f"Distribución de Zonas del Cultivo - {main_index}",
            xaxis_title=f"Valores del Índice {main_index}",
            yaxis_title="Cantidad de Área (píxeles)",
            template="plotly_white",
            height=450,
            barmode="overlay",
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="center", x=0.5
            )
        )
        
        chart1 = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-map me-2"),
                    f"Mapa de Zonas del Cultivo - {main_index}"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dcc.Graph(figure=fig1, config={'displayModeBar': False}),
                dbc.Alert([
                    html.I(className="fas fa-search me-2"),
                    html.Strong("Tu Análisis: "),
                    interpretation
                ], color="info", className="mt-3")
            ])
        ], className="mb-4")
        
        charts.append(chart1)
        
        
        # ===== GRÁFICO 3: COMPARACIÓN HISTÓRICA (si hay datos) =====
        if anomaly_array is not None:
            try:
                valid_anomaly = anomaly_array[np.isfinite(anomaly_array)]
                if len(valid_anomaly) > 0:
                    anomaly_mean = float(np.mean(valid_anomaly))
                    
                    # Clasificar cambios
                    improvement = valid_anomaly[valid_anomaly > 0.05]
                    stable = valid_anomaly[(valid_anomaly >= -0.05) & (valid_anomaly <= 0.05)]
                    decline = valid_anomaly[valid_anomaly < -0.05]
                    
                    improvement_pct = (len(improvement) / len(valid_anomaly)) * 100
                    stable_pct = (len(stable) / len(valid_anomaly)) * 100
                    decline_pct = (len(decline) / len(valid_anomaly)) * 100
                    
                    fig3 = go.Figure(data=[
                        go.Bar(
                            x=["Ha Mejorado", "Se Mantiene", "Ha Empeorado"],
                            y=[improvement_pct, stable_pct, decline_pct],
                            marker_color=["#2E7D32", "#1976D2", "#D32F2F"],
                            text=[f"{p:.1f}%" for p in [improvement_pct, stable_pct, decline_pct]],
                            textposition='outside',
                            hovertemplate="<b>%{x}</b><br>%{y:.1f}% del área<extra></extra>"
                        )
                    ])
                    
                    fig3.update_layout(
                        title="Cambios vs Años Anteriores",
                        yaxis_title="Porcentaje del Área (%)",
                        template="plotly_white",
                        height=400,
                        showlegend=False
                    )
                    
                    # Mensaje de tendencia
                    if improvement_pct > decline_pct:
                        trend_message = f"📈 Tendencia positiva: {improvement_pct:.1f}% del área ha mejorado vs años anteriores."
                        trend_color = "success"
                    elif decline_pct > improvement_pct:
                        trend_message = f"📉 Atención: {decline_pct:.1f}% del área ha empeorado vs años anteriores."
                        trend_color = "warning"
                    else:
                        trend_message = f"➡️ Cultivo estable: Sin cambios significativos vs años anteriores."
                        trend_color = "info"
                    
                    chart3 = dbc.Card([
                        dbc.CardHeader([
                            html.H6([
                                html.I(className="fas fa-chart-line me-2"),
                                "Evolución vs Temporadas Anteriores"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=fig3, config={'displayModeBar': False}),
                            dbc.Alert([
                                html.I(className="fas fa-calendar-alt me-2"),
                                html.Strong("Tendencia: "),
                                trend_message
                            ], color=trend_color, className="mt-3")
                        ])
                    ], className="mb-4")
                    
                    charts.append(chart3)
                    
            except Exception as e:
                logger.warning(f"Error creando gráfico de comparación histórica: {e}")
        
        return charts
        
    except Exception as e:
        logger.error(f"Error creando gráficos para agricultores: {e}")
        return [dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error generando gráficos: {str(e)}"
        ], color="danger")]


def _generate_kpi_cards_generic(arr, anomaly=None, lo=0.3, hi=0.6, label_idx="NDVI"):
    """Función genérica de respaldo para KPIs."""
    try:
        # Usar las funciones mejoradas como respaldo también
        return _create_farmer_kpi_cards(arr, anomaly, label_idx)
    except:
        return [dbc.Alert("Error generando KPIs genéricos", color="warning")]


def _generate_charts_generic(arr, anomaly=None, label_idx="NDVI"):
    """Función genérica de respaldo para gráficos.""" 
    try:
        # Usar las funciones mejoradas como respaldo también
        return _create_farmer_charts(arr, anomaly, label_idx)
    except:
        return [dbc.Alert("Error generando gráficos genéricos", color="warning")]


# ELIMINADA FUNCION DUPLICADA - SE USA LA VERSION MEJORADA CON ANALISIS TEMPORAL DETALLADO


def _create_trend_summary_card_improved(df, change, change_pct, index_type):
        if 'healthy_pct' in df_valid.columns and 'stress_pct' in df_valid.columns:
            fig2 = make_subplots(
                rows=1, cols=2,
                subplot_titles=["Porcentaje de Área Saludable", "Porcentaje de Área con Estrés"],
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Área saludable
            fig2.add_trace(
                go.Scatter(
                    x=df_valid['date'],
                    y=df_valid['healthy_pct'],
                    mode='lines+markers',
                    name='Área Saludable (%)',
                    line=dict(color="#2ECC71", width=3),
                    marker=dict(size=6),
                    fill='tonexty' if len(df_valid) > 1 else None,
                    fillcolor="rgba(46, 204, 113, 0.1)"
                ),
                row=1, col=1
            )
            
            # Área con estrés
            fig2.add_trace(
                go.Scatter(
                    x=df_valid['date'],
                    y=df_valid['stress_pct'],
                    mode='lines+markers',
                    name='Área con Estrés (%)',
                    line=dict(color="#E74C3C", width=3),
                    marker=dict(size=6),
                    fill='tonexty' if len(df_valid) > 1 else None,
                    fillcolor="rgba(231, 76, 60, 0.1)"
                ),
                row=1, col=2
            )
            
            fig2.update_layout(
                title="Distribución de Salud del Cultivo",
                template="plotly_white",
                height=400,
                showlegend=False
            )
            
            fig2.update_xaxes(title_text="Período", row=1, col=1)
            fig2.update_xaxes(title_text="Período", row=1, col=2)
            fig2.update_yaxes(title_text="Porcentaje (%)", range=[0, 100], row=1, col=1)
            fig2.update_yaxes(title_text="Porcentaje (%)", range=[0, 100], row=1, col=2)
            
            # Calcular promedios para recomendaciones
            avg_healthy = df_valid['healthy_pct'].mean()
            avg_stress = df_valid['stress_pct'].mean()
            
            if avg_healthy > 70:
                health_status = "¡Excelente! Tu cultivo mantiene un buen porcentaje de área saludable."
                health_color = "success"
            elif avg_healthy > 50:
                health_status = "Bueno. La mayoría de tu cultivo está en buen estado."
                health_color = "info"
            else:
                health_status = "Atención necesaria. Considera revisar las prácticas de manejo."
                health_color = "warning"
            
            chart2 = dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-chart-area me-2"),
                        "Análisis de Salud del Cultivo"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Graph(figure=fig2, config={'displayModeBar': False}),
                    dbc.Alert([
                        html.I(className="fas fa-stethoscope me-2"),
                        html.Strong(f"Estado general: "),
                        health_status,
                        html.Br(),
                        html.Small(f"Promedio área saludable: {avg_healthy:.1f}% | Promedio área con estrés: {avg_stress:.1f}%")
                    ], color=health_color, className="mt-3")
                ])
            ], className="mb-4")
            
            charts.append(chart2)
        
        # Tarjeta de resumen con tendencia
        if len(df_valid) >= 2:
            first_val = df_valid['ndvi_mean'].iloc[0]
            last_val = df_valid['ndvi_mean'].iloc[-1]
            change = last_val - first_val
            change_pct = (change / first_val) * 100 if first_val != 0 else 0
            
def _create_trend_summary_card_improved(df, change, change_pct, index_type):
    """Crea tarjeta de resumen de tendencia mejorada."""
    try:
        import numpy as np
        from dash import html
        import dash_bootstrap_components as dbc
        
        # Determinar tendencia
        if change > 0.05:
            trend_status = "Mejorando 📈"
            trend_color = "#27AE60"
            icon = "fas fa-arrow-up"
            advice = f"¡Tu cultivo está mejorando! Valores {index_type} superiores a {change:.3f} indican un crecimiento vigoroso."
        elif change < -0.05:
            trend_status = "Empeorando 📉"
            trend_color = "#E74C3C"
            icon = "fas fa-arrow-down"
            advice = f"Tu cultivo muestra signos de deterioro. Considera revisar riego, plagas o fertilización."
        else:
            trend_status = "Estable ➡️"
            trend_color = "#3498DB"
            icon = "fas fa-minus"
            advice = f"Tu cultivo se mantiene estable. Monitorea regularmente para detectar cambios."
        
        # Mejor y peor período
        best_idx = df['ndvi_mean'].idxmax()
        worst_idx = df['ndvi_mean'].idxmin()
        best_date = pd.to_datetime(df.loc[best_idx, 'date']).strftime('%B %Y')
        worst_date = pd.to_datetime(df.loc[worst_idx, 'date']).strftime('%B %Y')
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className=f"{icon} me-2", style={"color": trend_color}),
                    "Resumen de tu Cultivo"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4(trend_status, style={"color": trend_color}),
                        html.P("Tendencia general", className="text-muted small"),
                        html.P([
                            html.Strong("Cambio: "),
                            f"{change:+.3f} ({change_pct:+.1f}%)"
                        ], className="small")
                    ], md=4),
                    dbc.Col([
                        html.H6(f"🏆 Mejor época:", className="text-success"),
                        html.P(best_date, className="mb-0")
                    ], md=4),
                    dbc.Col([
                        html.H6(f"⚠️ Época más difícil:", className="text-warning"),
                        html.P(worst_date, className="mb-0")
                    ], md=4)
                ], className="mb-3"),
                html.Hr(),
                html.Div([
                    html.I(className="fas fa-lightbulb me-2", style={"color": "#F39C12"}),
                    html.Strong("Consejo: "),
                    advice
                ], className="text-muted")
            ])
        ], className="mb-3", style={
            "borderLeft": f"4px solid {trend_color}",
            "backgroundColor": f"{trend_color}08"
        })
        
    except Exception as e:
        logger.error(f"Error creando resumen de tendencia: {e}")
        return dbc.Alert("Error procesando tendencias", color="warning")


# FIN DEL MÓDULO
# =====================================================================
