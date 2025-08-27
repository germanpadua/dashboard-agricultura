"""
Utilidades para comparación temporal de índices de vegetación.

Módulo especializado en análisis comparativo entre dos períodos temporales
para índices de vegetación con enfoque en aplicaciones agrícolas.

Funcionalidades:
- Comparación estadística entre períodos
- Visualización de cambios y tendencias
- KPIs agrícolas orientados a agricultores
- Clasificación de salud del cultivo

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import logging
from typing import Dict, List, Optional, Tuple

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# Librerías de Dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.app.app_config import AGRI_THEME

logger = logging.getLogger(__name__)


def create_agricultural_kpis(
    data1: dict, data2: dict, date1: str, date2: str, indices: List[str]
) -> html.Div:
    """
    Crea KPIs enfocados en información práctica para agricultores.
    
    Args:
        data1: Datos del primer período
        data2: Datos del segundo período
        date1: Fecha del primer período
        date2: Fecha del segundo período
        indices: Lista de índices a analizar
        
    Returns:
        Componente html.Div con tarjetas KPI agrícolas
    """
    try:
        cards = []
        
        for idx in indices:
            if idx not in data1 or idx not in data2:
                continue
                
            # Clasificar salud para ambos períodos
            health1 = classify_vegetation_health(data1[idx], idx)
            health2 = classify_vegetation_health(data2[idx], idx)
            
            total1 = sum(health1.values())
            total2 = sum(health2.values())
            
            if total1 == 0 or total2 == 0:
                continue
                
            # Calcular cambios en áreas de riesgo
            risk_area1 = (
                health1["Regular"] + health1["Deficiente"]
            ) / total1 * 100
            risk_area2 = (
                health2["Regular"] + health2["Deficiente"]
            ) / total2 * 100
            risk_change = risk_area2 - risk_area1
            
            # Área con salud excelente/buena
            healthy_area1 = (
                health1["Excelente"] + health1["Buena"]
            ) / total1 * 100
            healthy_area2 = (
                health2["Excelente"] + health2["Buena"]
            ) / total2 * 100
            health_change = healthy_area2 - healthy_area1
            
            # Determinar estado general del cultivo
            if health_change > 5:
                status = "Mejorando"
                status_color = AGRI_THEME["colors"]["success"]
                status_icon = "fas fa-trending-up"
            elif health_change < -5:
                status = "Deteriorando"
                status_color = AGRI_THEME["colors"]["danger"]
                status_icon = "fas fa-trending-down"
            else:
                status = "Estable"
                status_color = AGRI_THEME["colors"]["info"]
                status_icon = "fas fa-minus"
                
            # Interpretación para agricultores
            if idx == "NDVI":
                interpretation = _get_ndvi_interpretation(healthy_area2, risk_area2)
            elif idx == "OSAVI":
                interpretation = _get_osavi_interpretation(healthy_area2, risk_area2)
            elif idx == "NDRE":
                interpretation = _get_ndre_interpretation(healthy_area2, risk_area2)
            else:
                interpretation = "Monitorear evolución del cultivo"
            
            card = dbc.Card([
                dbc.CardBody([
                    # Header con índice
                    html.Div([
                        html.H5([
                            html.I(className=f"{_get_index_icon(idx)} me-2"),
                            f"{idx} - {_get_index_name(idx)}"
                        ], className="mb-0", style={"color": AGRI_THEME["colors"]["primary"]})
                    ], className="mb-3"),
                    
                    # Estado general
                    html.Div([
                        dbc.Badge([
                            html.I(className=f"{status_icon} me-1"),
                            status
                        ], color=_get_badge_color(status_color), pill=True, className="mb-2 fs-6")
                    ], className="text-center mb-3"),
                    
                    # Métricas principales
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H4(f"{healthy_area2:.0f}%", className="mb-1 text-success fw-bold"),
                                html.Small("Área Saludable", className="text-muted fw-bold")
                            ], className="text-center")
                        ], md=6),
                        dbc.Col([
                            html.Div([
                                html.H4(f"{risk_area2:.0f}%", className="mb-1 text-warning fw-bold"), 
                                html.Small("Área de Riesgo", className="text-muted fw-bold")
                            ], className="text-center")
                        ], md=6)
                    ], className="mb-3"),
                    
                    # Cambios
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Small("Cambio en Salud:", className="text-muted"),
                                html.P(f"{health_change:+.1f}%", 
                                      className=f"mb-0 fw-bold {'text-success' if health_change > 0 else 'text-danger' if health_change < 0 else 'text-info'}")
                            ], md=6),
                            dbc.Col([
                                html.Small("Cambio en Riesgo:", className="text-muted"),
                                html.P(f"{risk_change:+.1f}%",
                                      className=f"mb-0 fw-bold {'text-danger' if risk_change > 0 else 'text-success' if risk_change < 0 else 'text-info'}")
                            ], md=6)
                        ])
                    ], className="mb-3"),
                    
                    # Recomendación
                    html.Div([
                        html.Hr(className="my-2"),
                        html.P([
                            html.I(className="fas fa-lightbulb me-2", style={"color": AGRI_THEME["colors"]["warning"]}),
                            interpretation
                        ], className="small mb-0 fst-italic", style={"color": AGRI_THEME["colors"]["text_secondary"]})
                    ])
                ])
            ], style={
                "borderRadius": "12px",
                "border": f"2px solid {status_color}",
                "boxShadow": f"0 4px 12px {status_color}33",
                "background": f"linear-gradient(145deg, {AGRI_THEME['colors']['bg_card']} 0%, {status_color}05 100%)"
            })
            
            cards.append(dbc.Col(card, lg=4, md=6, className="mb-3"))
        
        if not cards:
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "No se pudieron generar análisis de salud del cultivo."
                ], color="warning")
            ])
        
        return html.Div([
            dbc.Row(cards, className="g-3")
        ])
        
    except Exception as e:
        logger.error(f"Error creando KPIs agrícolas: {e}")
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error en análisis: {str(e)}"
            ], color="danger")
        ])


def _get_index_name(idx: str) -> str:
    names = {
        "NDVI": "Vigor Vegetativo",
        "OSAVI": "Análisis de Suelo", 
        "NDRE": "Estrés Hídrico"
    }
    return names.get(idx, "Índice de Vegetación")


def _get_badge_color(status_color: str) -> str:
    color_map = {
        AGRI_THEME["colors"]["success"]: "success",
        AGRI_THEME["colors"]["danger"]: "danger",
        AGRI_THEME["colors"]["info"]: "info",
        AGRI_THEME["colors"]["warning"]: "warning"
    }
    return color_map.get(status_color, "secondary")


def _get_ndvi_interpretation(healthy_pct: float, risk_pct: float) -> str:
    """
    Genera interpretación agrícola para NDVI.
    
    Args:
        healthy_pct: Porcentaje de área saludable
        risk_pct: Porcentaje de área de riesgo
        
    Returns:
        Interpretación y recomendación para el agricultor
    """
    if healthy_pct > 70:
        return (
            "Cultivo en excelente estado. Mantener programa de manejo actual."
        )
    elif healthy_pct > 50:
        return (
            "Cultivo saludable. Monitorear áreas de riesgo para prevenir problemas."
        )
    elif risk_pct > 30:
        return (
            "Atención: Considerar riego adicional o tratamiento nutricional."
        )
    else:
        return (
            "Estado crítico. Inspección de campo y medidas correctivas urgentes."
        )


def _get_osavi_interpretation(healthy_pct: float, risk_pct: float) -> str:
    """
    Genera interpretación agrícola para OSAVI.
    
    Args:
        healthy_pct: Porcentaje de área saludable
        risk_pct: Porcentaje de área de riesgo
        
    Returns:
        Interpretación y recomendación para el agricultor
    """
    if healthy_pct > 70:
        return "Óptima cobertura vegetal. Suelo bien protegido."
    elif risk_pct > 25:
        return (
            "Cobertura insuficiente. Evaluar densidad de plantación o erosión."
        )
    else:
        return "Cobertura vegetal aceptable. Monitorear evolución."


def _get_ndre_interpretation(healthy_pct: float, risk_pct: float) -> str:
    """
    Genera interpretación agrícola para NDRE.
    
    Args:
        healthy_pct: Porcentaje de área saludable
        risk_pct: Porcentaje de área de riesgo
        
    Returns:
        Interpretación y recomendación para el agricultor
    """
    if risk_pct > 30:
        return (
            "Posible estrés hídrico o nutricional. "
            "Revisar riego y fertilización."
        )
    elif healthy_pct > 60:
        return "Sin indicios de estrés. Condiciones nutricionales adecuadas."
    else:
        return "Monitorear signos de estrés. Considerar análisis foliar."


def create_comparison_kpis(
    data1: dict, data2: dict, date1: str, date2: str, indices: List[str]
) -> html.Div:
    """
    Alias para mantener compatibilidad - usa la versión agrícola.
    
    Args:
        data1: Datos del primer período
        data2: Datos del segundo período
        date1: Fecha del primer período
        date2: Fecha del segundo período
        indices: Lista de índices a analizar
        
    Returns:
        Componente html.Div con KPIs comparativos
    """
    return create_agricultural_kpis(data1, data2, date1, date2, indices)


def create_comparison_scatter_chart(
    data1: dict, data2: dict, date1: str, date2: str, indices: List[str]
) -> go.Figure:
    """
    Gráfico simplificado de análisis de cambios.
    
    Enfocado en NDVI para claridad, muestra porcentajes de mejora,
    empeoramiento y estabilidad para agricultores.
    
    Args:
        data1: Datos del primer período
        data2: Datos del segundo período
        date1: Fecha del primer período
        date2: Fecha del segundo período
        indices: Lista de índices a analizar
        
    Returns:
        Figura de Plotly con análisis de cambios
    """
    try:
        # Usar NDVI como índice principal para simplicidad
        main_index = (
            'NDVI' if 'NDVI' in indices
            else indices[0] if indices
            else 'NDVI'
        )
        
        if main_index not in data1 or main_index not in data2:
            return go.Figure()
            
        arr1 = data1[main_index].flatten()
        arr2 = data2[main_index].flatten()
        
        # Asegurar mismas dimensiones
        min_len = min(len(arr1), len(arr2))
        arr1 = arr1[:min_len]
        arr2 = arr2[:min_len]
        
        # Filtrar valores válidos
        mask = np.isfinite(arr1) & np.isfinite(arr2)
        x_vals = arr1[mask]
        y_vals = arr2[mask]
        
        if len(x_vals) == 0:
            return go.Figure()
        
        # Calcular diferencias para clasificar cambios
        diff = y_vals - x_vals
        threshold = 0.05  # Umbral de cambio significativo
        
        improved = np.sum(diff > threshold)
        stable = np.sum(np.abs(diff) <= threshold) 
        worsened = np.sum(diff < -threshold)
        total = len(diff)
        
        # Crear gráfico de barras simple con porcentajes
        fig = go.Figure()
        
        categories = ['Ha Mejorado', 'Se Mantiene', 'Ha Empeorado']
        values = [improved/total*100, stable/total*100, worsened/total*100]
        colors = ['#27AE60', '#3498DB', '#E74C3C']
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=values,
                marker=dict(
                    color=colors,
                    opacity=0.8,
                    line=dict(color='white', width=2)
                ),
                text=[f"{v:.1f}%" for v in values],
                textposition='auto',
                name='Estado del Cultivo'
            )
        )
        
        # Agregar interpretación
        if worsened/total > 0.3:
            interpretation = "⚠️ Más del 30% del área ha empeorado. Revisa manejo."
        elif improved/total > 0.3:
            interpretation = "🎉 ¡Excelente! Más del 30% del área ha mejorado."
        else:
            interpretation = "📊 Cambios normales. El cultivo se mantiene estable."
        
        fig.add_annotation(
            text=f"<b>Análisis del Período:</b><br>{interpretation}",
            xref="paper", yref="paper",
            x=0.5, y=1.15,
            showarrow=False,
            align="center",
            font=dict(size=12, color="#2c3e50"),
            bgcolor="rgba(52, 152, 219, 0.1)",
            bordercolor="#3498DB",
            borderwidth=1
        )
        
        fig.update_layout(
            height=400,
            title_text=f"Análisis de Cambios en {main_index}",
            title_x=0.5,
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(title="Estado del Cambio"),
            yaxis=dict(title="Porcentaje del Área (%)"),
            margin=dict(t=100, b=60, l=60, r=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico scatter: {e}")
        return go.Figure()


def create_difference_chart(
    data1: dict, data2: dict, date1: str, date2: str, indices: List[str]
) -> go.Figure:
    """
    Crea gráfico de diferencias (período 2 - período 1).
    
    Optimizado con submuestreo para histogramas grandes para mejor rendimiento.
    
    Args:
        data1: Datos del primer período
        data2: Datos del segundo período
        date1: Fecha del primer período
        date2: Fecha del segundo período
        indices: Lista de índices a analizar
        
    Returns:
        Figura de Plotly con histograma de diferencias
    """
    try:
        fig = go.Figure()
        
        colors = [AGRI_THEME["colors"]["primary"], AGRI_THEME["colors"]["info"], AGRI_THEME["colors"]["success"]]
        
        for i, idx in enumerate(indices):
            if idx not in data1 or idx not in data2:
                continue
                
            arr1 = data1[idx].flatten()
            arr2 = data2[idx].flatten()
            
            # Asegurar mismas dimensiones
            min_len = min(len(arr1), len(arr2))
            arr1 = arr1[:min_len]
            arr2 = arr2[:min_len]
            
            # Calcular diferencia
            diff = arr2 - arr1
            valid_diff = diff[np.isfinite(diff)]
            
            if len(valid_diff) == 0:
                continue
            
            # Optimización: Submuestreo para histogramas grandes
            max_points = 20000  # Límite óptimo para rendimiento
            if len(valid_diff) > max_points:
                logger.info(
                    f"Submuestreando {len(valid_diff)} puntos a {max_points} "
                    "para histograma"
                )
                indices_sample = np.random.choice(
                    len(valid_diff), max_points, replace=False
                )
                valid_diff = valid_diff[indices_sample]
            
            # Histograma de diferencias optimizado
            fig.add_trace(
                go.Histogram(
                    x=valid_diff,
                    name=f'Δ {idx}',
                    nbinsx=30,  # Número óptimo de bins
                    opacity=0.7,
                    marker_color=colors[i % len(colors)],
                    hovertemplate=(
                        f'<b>Diferencia {idx}</b><br>'
                        'Rango: %{x}<br>'
                        'Frecuencia: %{y}<extra></extra>'
                    )
                )
            )
        
        # Línea de referencia en x=0 (sin cambio)
        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="gray",
            annotation_text="Sin cambio",
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Distribución de Diferencias (Período 2 - Período 1)",
            title_x=0.5,
            xaxis_title="Diferencia en índice",
            yaxis_title="Frecuencia",
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            barmode='overlay',
            # Optimizaciones de rendimiento
            dragmode=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico de diferencias: {e}")
        return go.Figure()


def create_distribution_comparison_chart(
    data1: dict, data2: dict, date1: str, date2: str, indices: List[str]
) -> go.Figure:
    """
    Crea gráfico comparativo de distribuciones.
    
    Optimizado con submuestreo y límite de subplots para mejor rendimiento.
    
    Args:
        data1: Datos del primer período
        data2: Datos del segundo período
        date1: Fecha del primer período
        date2: Fecha del segundo período
        indices: Lista de índices a analizar
        
    Returns:
        Figura de Plotly con comparación de distribuciones
    """
    try:
        # Limitar a máximo 3 índices para rendimiento óptimo
        indices_limited = indices[:3]
        if len(indices) > 3:
            logger.info(
                f"Limitando gráfico de distribuciones a primeros 3 índices "
                f"de {len(indices)}"
            )
        
        fig = make_subplots(
            rows=len(indices_limited), cols=1,
            subplot_titles=[f"Distribución {idx}" for idx in indices_limited],
            vertical_spacing=0.15
        )
        
        colors = [AGRI_THEME["colors"]["primary"], AGRI_THEME["colors"]["info"], AGRI_THEME["colors"]["success"]]
        
        for i, idx in enumerate(indices_limited):
            if idx not in data1 or idx not in data2:
                continue
                
            arr1 = data1[idx].flatten()
            arr2 = data2[idx].flatten()
            
            valid1 = arr1[np.isfinite(arr1)]
            valid2 = arr2[np.isfinite(arr2)]
            
            if len(valid1) == 0 or len(valid2) == 0:
                continue
            
            # Optimización: Submuestreo para distribuciones grandes
            max_points = 15000
            if len(valid1) > max_points:
                indices_sample = np.random.choice(
                    len(valid1), max_points, replace=False
                )
                valid1 = valid1[indices_sample]
            if len(valid2) > max_points:
                indices_sample = np.random.choice(
                    len(valid2), max_points, replace=False
                )
                valid2 = valid2[indices_sample]
            
            # Histogramas superpuestos optimizados
            fig.add_trace(
                go.Histogram(
                    x=valid1,
                    name=f'{date1}',
                    nbinsx=25,  # Número óptimo de bins
                    opacity=0.6,
                    marker_color=colors[i % len(colors)],
                    showlegend=(i == 0)
                ), 
                row=i+1, col=1
            )
            
            fig.add_trace(
                go.Histogram(
                    x=valid2,
                    name=f'{date2}',
                    nbinsx=25,  # Número óptimo de bins
                    opacity=0.6,
                    marker_color='orange',
                    showlegend=(i == 0)
                ), 
                row=i+1, col=1
            )
            
            # Líneas de estadísticas (medias)
            mean1, mean2 = np.mean(valid1), np.mean(valid2)
            
            fig.add_vline(
                x=mean1,
                line_dash="solid",
                line_color=colors[i % len(colors)],
                row=i+1, col=1,
                annotation_text=f"μ₁={mean1:.3f}"
            )
            fig.add_vline(
                x=mean2,
                line_dash="solid",
                line_color='orange',
                row=i+1, col=1,
                annotation_text=f"μ₂={mean2:.3f}"
            )
        
        fig.update_layout(
            height=250 * len(indices_limited),  # Altura proporcional
            title="Comparación de Distribuciones (muestra representativa)",
            title_x=0.5,
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            barmode='overlay',
            dragmode=False  # Optimización de rendimiento
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico de distribuciones: {e}")
        return go.Figure()


def create_comparison_stats_table(data1: dict, data2: dict, date1: str, date2: str, indices: List[str]) -> html.Div:
    """
    Crea tabla con estadísticas detalladas de la comparación
    """
    try:
        rows = []
        
        for idx in indices:
            if idx not in data1 or idx not in data2:
                continue
                
            arr1 = data1[idx].flatten()
            arr2 = data2[idx].flatten()
            
            valid1 = arr1[np.isfinite(arr1)]
            valid2 = arr2[np.isfinite(arr2)]
            
            if len(valid1) == 0 or len(valid2) == 0:
                continue
            
            # Estadísticas descriptivas
            stats1 = {
                'mean': np.mean(valid1),
                'median': np.median(valid1),
                'std': np.std(valid1),
                'min': np.min(valid1),
                'max': np.max(valid1),
                'count': len(valid1)
            }
            
            stats2 = {
                'mean': np.mean(valid2),
                'median': np.median(valid2),
                'std': np.std(valid2),
                'min': np.min(valid2),
                'max': np.max(valid2),
                'count': len(valid2)
            }
            
            # Test estadístico
            try:
                t_stat, p_value = stats.ttest_ind(valid1, valid2)
                significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
            except:
                t_stat, p_value, significance = 0, 1, "ns"
            
            # Correlación entre fechas (si tienen misma longitud)
            if len(valid1) == len(valid2):
                try:
                    correlation = np.corrcoef(valid1, valid2)[0, 1]
                except:
                    correlation = np.nan
            else:
                correlation = np.nan
            
            row = html.Tr([
                html.Td(html.Strong(idx), style={"color": AGRI_THEME["colors"]["primary"]}),
                html.Td(f"{stats1['mean']:.4f} ± {stats1['std']:.4f}"),
                html.Td(f"{stats2['mean']:.4f} ± {stats2['std']:.4f}"),
                html.Td(f"{((stats2['mean'] - stats1['mean']) / stats1['mean'] * 100):+.2f}%"),
                html.Td(f"{correlation:.3f}" if not np.isnan(correlation) else "N/A"),
                html.Td([
                    f"{p_value:.4f} ",
                    html.Small(significance, className="text-muted")
                ]),
                html.Td(f"{stats1['count']} / {stats2['count']}")
            ])
            
            rows.append(row)
        
        if not rows:
            return html.Div([
                dbc.Alert("No hay suficientes datos para generar la tabla estadística.", color="warning")
            ])
        
        table = dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Índice"),
                    html.Th(f"{date1} (Media ± SD)"),
                    html.Th(f"{date2} (Media ± SD)"),
                    html.Th("Cambio %"),
                    html.Th("Correlación"),
                    html.Th("p-valor"),
                    html.Th("N₁ / N₂")
                ])
            ]),
            html.Tbody(rows)
        ], striped=True, bordered=True, hover=True, responsive=True, size="sm")
        
        return html.Div([
            html.H6([
                html.I(className="fas fa-table me-2"),
                "Estadísticas Detalladas"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["primary"]}),
            table,
            html.Small([
                "Significancia: *** p<0.001, ** p<0.01, * p<0.05, ns = no significativo"
            ], className="text-muted mt-2")
        ])
        
    except Exception as e:
        logger.error(f"Error creando tabla de estadísticas: {e}")
        return html.Div([
            dbc.Alert(f"Error generando tabla: {str(e)}", color="danger")
        ])


def classify_vegetation_health(arr: np.ndarray, index_name: str) -> dict:
    """
    Clasifica píxeles según salud del cultivo para agricultores.
    
    Args:
        arr: Array con valores del índice de vegetación
        index_name: Nombre del índice (NDVI, OSAVI, NDRE)
        
    Returns:
        Diccionario con conteos por categoría de salud
    """
    valid_arr = arr[np.isfinite(arr)]
    if len(valid_arr) == 0:
        return {"Excelente": 0, "Buena": 0, "Regular": 0, "Deficiente": 0}
    
    if index_name == "NDVI":
        # Umbrales NDVI basados en literatura agrícola
        excellent = np.sum(valid_arr > 0.6)  # Vegetación muy densa/saludable
        good = np.sum(
            (valid_arr > 0.4) & (valid_arr <= 0.6)
        )  # Vegetación moderada
        regular = np.sum(
            (valid_arr > 0.2) & (valid_arr <= 0.4)
        )  # Vegetación escasa
        poor = np.sum(valid_arr <= 0.2)  # Suelo desnudo/estrés severo
        
    elif index_name == "OSAVI":
        # OSAVI optimizado para análisis de suelos
        excellent = np.sum(valid_arr > 0.5)
        good = np.sum((valid_arr > 0.3) & (valid_arr <= 0.5))
        regular = np.sum((valid_arr > 0.15) & (valid_arr <= 0.3))
        poor = np.sum(valid_arr <= 0.15)
        
    elif index_name == "NDRE":
        # NDRE para detección de estrés hídrico/nutricional
        excellent = np.sum(valid_arr > 0.2)
        good = np.sum((valid_arr > 0.1) & (valid_arr <= 0.2))
        regular = np.sum((valid_arr > 0.05) & (valid_arr <= 0.1))
        poor = np.sum(valid_arr <= 0.05)
    else:
        # Clasificación genérica basada en percentiles
        p25, p50, p75 = np.percentile(valid_arr, [25, 50, 75])
        excellent = np.sum(valid_arr > p75)
        good = np.sum((valid_arr > p50) & (valid_arr <= p75))
        regular = np.sum((valid_arr > p25) & (valid_arr <= p50))
        poor = np.sum(valid_arr <= p25)
    
    return {
        "Excelente": int(excellent),
        "Buena": int(good), 
        "Regular": int(regular),
        "Deficiente": int(poor)
    }


def create_health_classification_chart(data1: dict, data2: dict, date1: str, date2: str, indices: List[str]) -> go.Figure:
    """
    Gráfico de clasificación de salud del cultivo optimizado y comprensible para agricultores.
    Muestra la evolución de la salud entre dos períodos de forma clara y práctica.
    """
    try:
        # Usar solo NDVI para simplicidad y claridad
        main_index = "NDVI" if "NDVI" in indices else indices[0] if indices else "NDVI"
        
        if main_index not in data1 or main_index not in data2:
            return go.Figure()
        
        # Clasificar salud para ambos períodos
        health1 = classify_vegetation_health(data1[main_index], main_index)
        health2 = classify_vegetation_health(data2[main_index], main_index)
        
        categories = ["Excelente", "Buena", "Regular", "Deficiente"]
        values1 = [health1[cat] for cat in categories]
        values2 = [health2[cat] for cat in categories]
        
        # Convertir a porcentajes
        total1, total2 = sum(values1), sum(values2)
        if total1 > 0 and total2 > 0:
            pct1 = [v/total1*100 for v in values1]
            pct2 = [v/total2*100 for v in values2]
        else:
            return go.Figure()
        
        # Colores intuitivos para agricultores
        health_colors = ["#2E7D32", "#66BB6A", "#FF8A65", "#F44336"]
        
        # Calcular diferencias para mostrar cambios
        differences = [pct2[i] - pct1[i] for i in range(len(categories))]
        
        fig = go.Figure()
        
        # Período 1 (referencia)
        fig.add_trace(go.Bar(
            x=categories,
            y=pct1,
            name=f'📅 {date1}',
            marker_color=health_colors,
            opacity=0.6,
            hovertemplate='<b>%{x}</b><br>' +
                         f'{date1}: %{{y:.1f}}% del área<br>' +
                         '(%{customdata:,} píxeles)<extra></extra>',
            customdata=values1,
            offsetgroup=1
        ))
        
        # Período 2 (comparación)
        fig.add_trace(go.Bar(
            x=categories,
            y=pct2,
            name=f'📅 {date2}',
            marker_color=health_colors,
            opacity=1.0,
            hovertemplate='<b>%{x}</b><br>' +
                         f'{date2}: %{{y:.1f}}% del área<br>' +
                         '(%{customdata:,} píxeles)<br>' +
                         'Cambio: %{text}<extra></extra>',
            customdata=values2,
            text=[f"{diff:+.1f}%" for diff in differences],
            offsetgroup=2
        ))
        
        # Determinar el mensaje principal basado en cambios en salud
        excellent_change = differences[0]  # Cambio en área excelente
        good_change = differences[1]       # Cambio en área buena
        poor_change = differences[3]       # Cambio en área deficiente
        
        healthy_improvement = excellent_change + good_change
        
        if healthy_improvement > 5:
            main_message = f"¡Mejora notable! +{healthy_improvement:.1f}% más área saludable"
            message_color = "#2E7D32"
            recommendation = "Excelente evolución. Mantén las prácticas actuales de manejo"
        elif poor_change > 5:
            main_message = f"Atención: +{poor_change:.1f}% más área deficiente"
            message_color = "#F44336"
            recommendation = "Se requiere intervención. Revisa las condiciones de cultivo"
        elif abs(healthy_improvement) <= 3:
            main_message = "Estado estable entre períodos"
            message_color = "#1976D2"
            recommendation = "Sin cambios significativos. Continúa monitoreando"
        else:
            main_message = "Cambios mixtos en la salud del cultivo"
            message_color = "#FF8A65"
            recommendation = "Evalúa qué factores están afectando las diferentes zonas"
        
        fig.update_layout(
            title=dict(
                text=f"Evolución de la Salud de tu Cultivo<br>" +
                     f"<span style='font-size: 14px; color: {message_color};'>{main_message}</span>",
                x=0.5,
                font=dict(size=18)
            ),
            xaxis=dict(
                title="Clasificación de Salud",
                title_font=dict(size=14, family=AGRI_THEME["fonts"]["primary"]),
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="Porcentaje del Área Total (%)",
                title_font=dict(size=14, family=AGRI_THEME["fonts"]["primary"]),
                tickfont=dict(size=12),
                range=[0, max(max(pct1), max(pct2)) * 1.1]
            ),
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500,
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom", 
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=100, b=80, l=80, r=40)
        )
        
        # Añadir anotación con recomendación
        fig.add_annotation(
            text=f"🎯 <b>Recomendación:</b> {recommendation}",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=12, color=message_color),
            align="center",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=message_color,
            borderwidth=1,
            borderpad=10
        )
        
        # Añadir líneas de referencia para interpretación
        # Línea del 70% para área saludable objetivo
        fig.add_hline(
            y=70, 
            line_dash="dot", 
            line_color="#2E7D32", 
            line_width=1,
            annotation_text="Objetivo: 70% área saludable",
            annotation_position="right"
        )
        
        # Añadir etiquetas de cambio en las barras
        for i, (cat, diff) in enumerate(zip(categories, differences)):
            if abs(diff) > 1:  # Solo mostrar cambios significativos
                arrow = "↗️" if diff > 0 else "↘️"
                fig.add_annotation(
                    x=i,
                    y=max(pct1[i], pct2[i]) + 2,
                    text=f"{arrow} {abs(diff):.1f}%",
                    showarrow=False,
                    font=dict(size=11, color=health_colors[i])
                )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico de salud: {e}")
        return go.Figure()


def create_change_analysis_chart(data1: dict, data2: dict, date1: str, date2: str, indices: List[str]) -> go.Figure:
    """
    Análisis de cambios píxel por píxel comprensible para agricultores.
    Muestra qué porcentaje del cultivo ha mejorado, empeorado o se mantiene estable.
    """
    try:
        # Usar solo el índice principal (NDVI preferentemente) para simplicidad
        main_index = "NDVI" if "NDVI" in indices else indices[0] if indices else "NDVI"
        
        if main_index not in data1 or main_index not in data2:
            return go.Figure()
                
        arr1 = data1[main_index].flatten()
        arr2 = data2[main_index].flatten()
        
        # Asegurar mismas dimensiones
        min_len = min(len(arr1), len(arr2))
        arr1 = arr1[:min_len]
        arr2 = arr2[:min_len]
        
        # Filtrar valores válidos
        mask = np.isfinite(arr1) & np.isfinite(arr2)
        valid1 = arr1[mask]
        valid2 = arr2[mask]
        
        if len(valid1) == 0:
            return go.Figure()
        
        # Calcular cambios absolutos
        changes = valid2 - valid1
        total_pixels = len(changes)
        
        # Clasificación más práctica para agricultores
        # Usando umbrales más apropiados para decisiones agrícolas
        major_improvement = np.sum(changes > 0.1)        # Mejora considerable
        minor_improvement = np.sum((changes > 0.03) & (changes <= 0.1))  # Mejora leve
        stable = np.sum(np.abs(changes) <= 0.03)         # Sin cambios significativos
        minor_decline = np.sum((changes < -0.03) & (changes >= -0.1))    # Deterioro leve
        major_decline = np.sum(changes < -0.1)           # Deterioro considerable
        
        # Calcular porcentajes
        categories = ['Ha Mejorado\nMucho', 'Ha Mejorado\nPoco', 'Se Mantiene\nIgual', 'Ha Empeorado\nPoco', 'Ha Empeorado\nMucho']
        values = [major_improvement, minor_improvement, stable, minor_decline, major_decline]
        percentages = [v/total_pixels*100 if total_pixels > 0 else 0 for v in values]
        
        # Colores intuitivos para agricultores
        colors = ['#2E7D32', '#66BB6A', '#FDD835', '#FF8A65', '#F44336']
        
        # Iconos para mejor comprensión
        icons = ['📈', '↗️', '➡️', '↘️', '📉']
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=categories,
            y=percentages,
            marker=dict(
                color=colors,
                line=dict(color='white', width=1.5)
            ),
            text=[f"{p:.1f}%<br>{icons[i]}" for i, p in enumerate(percentages)],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' +
                         '%{y:.1f}% del área total<br>' +
                         '(%{customdata:,} píxeles)<br>' +
                         '<extra></extra>',
            customdata=values
        ))
        
        # Determinar mensaje principal basado en los resultados
        total_improvement = percentages[0] + percentages[1]  # Mejoras
        total_decline = percentages[3] + percentages[4]      # Deterioros
        stable_pct = percentages[2]                          # Estable
        
        if total_improvement > total_decline + 10:
            main_message = f"¡Excelente! {total_improvement:.1f}% de tu cultivo ha mejorado"
            message_color = "#2E7D32"
            recommendation = "Mantén las prácticas de manejo que has implementado"
        elif total_decline > total_improvement + 10:
            main_message = f"Atención: {total_decline:.1f}% de tu cultivo ha empeorado"
            message_color = "#F44336"
            recommendation = "Considera revisar riego, fertilización o control de plagas"
        elif stable_pct > 50:
            main_message = f"Cultivo estable: {stable_pct:.1f}% sin cambios significativos"
            message_color = "#1976D2"
            recommendation = "Comportamiento normal, continúa monitoreando"
        else:
            main_message = "Cambios mixtos en tu cultivo"
            message_color = "#FF8A65"
            recommendation = "Monitorea las áreas que han empeorado"
        
        fig.update_layout(
            title=dict(
                text=f"¿Cómo Ha Cambiado tu Cultivo?<br>" +
                     f"<span style='font-size: 14px; color: {message_color};'>{main_message}</span>",
                x=0.5,
                font=dict(size=18)
            ),
            xaxis=dict(
                title="Estado del Cambio",
                title_font=dict(size=14, family=AGRI_THEME["fonts"]["primary"]),
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="Porcentaje del Área Total (%)",
                title_font=dict(size=14, family=AGRI_THEME["fonts"]["primary"]),
                tickfont=dict(size=12)
            ),
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500,
            showlegend=False,
            margin=dict(t=100, b=80, l=80, r=40)
        )
        
        # Añadir anotación con recomendación
        fig.add_annotation(
            text=f"💡 <b>Recomendación:</b> {recommendation}",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=12, color=message_color),
            align="center",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=message_color,
            borderwidth=1,
            borderpad=10
        )
        
        # Línea de referencia para el balance 50%
        fig.add_hline(
            y=50, 
            line_dash="dash", 
            line_color="gray", 
            line_width=1,
            annotation_text="50% (línea de referencia)",
            annotation_position="right"
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando análisis de cambios: {e}")
        return go.Figure()


def create_comparison_summary_chart(data1: dict, data2: dict, date1: str, date2: str, indices: List[str]) -> go.Figure:
    """
    Crea un gráfico de barras simplificado con estadísticas agregadas
    SUPER OPTIMIZADO: Solo estadísticas, no datos individuales
    """
    try:
        fig = go.Figure()
        
        x_labels = []
        means1, means2 = [], []
        stds1, stds2 = [], []
        
        for idx in indices:
            if idx not in data1 or idx not in data2:
                continue
                
            arr1 = data1[idx].flatten()
            arr2 = data2[idx].flatten()
            
            valid1 = arr1[np.isfinite(arr1)]
            valid2 = arr2[np.isfinite(arr2)]
            
            if len(valid1) == 0 or len(valid2) == 0:
                continue
                
            x_labels.append(idx)
            means1.append(np.mean(valid1))
            means2.append(np.mean(valid2))
            stds1.append(np.std(valid1))
            stds2.append(np.std(valid2))
        
        if not x_labels:
            return go.Figure()
        
        # Barras agrupadas para medias
        fig.add_trace(go.Bar(
            x=x_labels,
            y=means1,
            name=f'Promedio {date1}',
            marker_color=AGRI_THEME["colors"]["primary"],
            error_y=dict(type='data', array=stds1, visible=True),
            hovertemplate='<b>%{x}</b><br>Promedio: %{y:.4f}<br>Desv. Est.: %{error_y.array:.4f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=x_labels,
            y=means2,
            name=f'Promedio {date2}',
            marker_color=AGRI_THEME["colors"]["info"],
            error_y=dict(type='data', array=stds2, visible=True),
            hovertemplate='<b>%{x}</b><br>Promedio: %{y:.4f}<br>Desv. Est.: %{error_y.array:.4f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Resumen Estadístico de la Comparación",
            title_x=0.5,
            xaxis_title="Índices de Vegetación",
            yaxis_title="Valor Promedio",
            font=dict(family=AGRI_THEME["fonts"]["primary"]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            barmode='group',
            # Máxima optimización
            dragmode=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando gráfico resumen: {e}")
        return go.Figure()


def _get_index_icon(index_name: str) -> str:
    """
    Retorna el icono FontAwesome apropiado para cada índice.
    
    Args:
        index_name: Nombre del índice de vegetación
        
    Returns:
        Clase CSS del icono FontAwesome
    """
    icons = {
        "NDVI": "fas fa-seedling",
        "OSAVI": "fas fa-leaf",
        "NDRE": "fas fa-spa"
    }
    return icons.get(index_name, "fas fa-chart-line")