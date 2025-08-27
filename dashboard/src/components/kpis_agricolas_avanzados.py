"""
Componentes avanzados de KPIs agrícolas específicos para olivar
Desarrollado para TFM - Ciencia de Datos - Universidad de Granada
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

def create_agricultural_kpis_card(ndvi_stats, finca_data=None):
    """
    Crea un card con KPIs agrícolas específicos para olivar
    """
    if not ndvi_stats:
        return dbc.Alert("No hay datos disponibles para calcular KPIs", color="warning")
    
    # Calcular KPIs específicos para olivar
    kpis = calculate_olive_specific_kpis(ndvi_stats, finca_data)
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-seedling me-2 text-success"),
                "KPIs Agrícolas - Olivar"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                # Vigor General del Cultivo
                dbc.Col([
                    _create_kpi_metric(
                        "Vigor General",
                        kpis["vigor_general"],
                        "fas fa-chart-line",
                        get_vigor_color(kpis["vigor_general"])
                    )
                ], width=6, lg=3),
                
                # Índice de Estrés Hídrico
                dbc.Col([
                    _create_kpi_metric(
                        "Estrés Hídrico",
                        kpis["estres_hidrico"],
                        "fas fa-tint",
                        get_stress_color(kpis["estres_hidrico"])
                    )
                ], width=6, lg=3),
                
                # Uniformidad del Cultivo
                dbc.Col([
                    _create_kpi_metric(
                        "Uniformidad",
                        kpis["uniformidad"],
                        "fas fa-equals",
                        get_uniformity_color(kpis["uniformidad"])
                    )
                ], width=6, lg=3),
                
                # Potencial Productivo
                dbc.Col([
                    _create_kpi_metric(
                        "Potencial Productivo",
                        kpis["potencial_productivo"],
                        "fas fa-chart-area",
                        get_potential_color(kpis["potencial_productivo"])
                    )
                ], width=6, lg=3)
            ], className="mb-3"),
            
            # Métricas adicionales
            dbc.Row([
                dbc.Col([
                    _create_detailed_metrics_table(kpis)
                ], width=12)
            ])
        ])
    ], className="mb-4")

def _create_kpi_metric(title, value, icon, color):
    """Crea una métrica KPI individual"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} fa-2x mb-2", style={"color": color}),
                html.H4(f"{value:.1f}%", className="mb-1", style={"color": color}),
                html.P(title, className="text-muted mb-0", style={"fontSize": "0.85rem"})
            ], className="text-center")
        ], className="py-3")
    ], className="h-100 border-0 shadow-sm")

def _create_detailed_metrics_table(kpis):
    """Crea tabla detallada con métricas adicionales"""
    return dbc.Card([
        dbc.CardHeader([
            html.H6([
                html.I(className="fas fa-table me-2"),
                "Métricas Detalladas"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Métrica"),
                        html.Th("Valor"),
                        html.Th("Interpretación"),
                        html.Th("Estado")
                    ])
                ]),
                html.Tbody([
                    _create_metric_row("NDVI Promedio", f"{kpis['ndvi_mean']:.3f}", 
                                     interpret_ndvi_value(kpis['ndvi_mean']),
                                     get_ndvi_status_badge(kpis['ndvi_mean'])),
                    _create_metric_row("Variabilidad (CV)", f"{kpis['coef_variacion']:.1f}%", 
                                     interpret_variability(kpis['coef_variacion']),
                                     get_variability_badge(kpis['coef_variacion'])),
                    _create_metric_row("Área Productiva", f"{kpis['area_productiva']:.1f}%", 
                                     "Porcentaje del área con NDVI > 0.3",
                                     get_area_badge(kpis['area_productiva'])),
                    _create_metric_row("Zonas de Alerta", f"{kpis['zonas_alerta']:.1f}%", 
                                     "Área con posibles problemas",
                                     get_alert_badge(kpis['zonas_alerta']))
                ])
            ], bordered=True, hover=True, size="sm")
        ])
    ], className="border-0 shadow-sm")

def _create_metric_row(metric, value, interpretation, badge):
    """Crea una fila de la tabla de métricas"""
    return html.Tr([
        html.Td(metric, className="fw-semibold"),
        html.Td(value),
        html.Td(interpretation, className="text-muted"),
        html.Td(badge)
    ])

def calculate_olive_specific_kpis(ndvi_stats, finca_data=None):
    """
    Calcula KPIs específicos para cultivos de olivar
    """
    try:
        ndvi_mean = ndvi_stats.get("mean", 0.5)
        ndvi_std = ndvi_stats.get("std", 0.1)
        ndvi_min = ndvi_stats.get("min", 0.0)
        ndvi_max = ndvi_stats.get("max", 1.0)
        
        # Vigor general del cultivo (basado en NDVI medio para olivar)
        # Olivar saludable: NDVI 0.3-0.8
        if ndvi_mean >= 0.6:
            vigor_general = min(100, (ndvi_mean - 0.3) / 0.5 * 100)
        else:
            vigor_general = (ndvi_mean / 0.6) * 70
        
        # Estrés hídrico (inverso del vigor en zonas bajas)
        # Valores NDVI < 0.3 indican posible estrés
        area_estres = min(100, max(0, (0.4 - ndvi_mean) / 0.4 * 100))
        estres_hidrico = area_estres
        
        # Uniformidad del cultivo (basado en desviación estándar)
        # Menor variabilidad = mayor uniformidad
        coef_variacion = (ndvi_std / ndvi_mean) * 100 if ndvi_mean > 0 else 100
        uniformidad = max(0, 100 - coef_variacion * 2)
        
        # Potencial productivo (combinación de vigor y uniformidad)
        potencial_productivo = (vigor_general * 0.7 + uniformidad * 0.3)
        
        # Métricas adicionales
        area_productiva = min(100, max(0, (ndvi_mean - 0.2) / 0.6 * 100))
        zonas_alerta = max(0, (0.35 - ndvi_mean) / 0.35 * 100) if ndvi_mean < 0.35 else 0
        
        return {
            "vigor_general": vigor_general,
            "estres_hidrico": estres_hidrico,
            "uniformidad": uniformidad,
            "potencial_productivo": potencial_productivo,
            "ndvi_mean": ndvi_mean,
            "coef_variacion": coef_variacion,
            "area_productiva": area_productiva,
            "zonas_alerta": zonas_alerta
        }
        
    except Exception as e:
        print(f"Error calculando KPIs: {e}")
        return {
            "vigor_general": 0,
            "estres_hidrico": 100,
            "uniformidad": 0,
            "potencial_productivo": 0,
            "ndvi_mean": 0,
            "coef_variacion": 100,
            "area_productiva": 0,
            "zonas_alerta": 100
        }

# Funciones auxiliares para colores y badges
def get_vigor_color(valor):
    if valor >= 75: return "#28a745"  # Verde
    elif valor >= 50: return "#ffc107"  # Amarillo
    else: return "#dc3545"  # Rojo

def get_stress_color(valor):
    if valor <= 25: return "#28a745"  # Verde (poco estrés)
    elif valor <= 50: return "#ffc107"  # Amarillo
    else: return "#dc3545"  # Rojo (mucho estrés)

def get_uniformity_color(valor):
    if valor >= 75: return "#28a745"
    elif valor >= 50: return "#ffc107"
    else: return "#dc3545"

def get_potential_color(valor):
    if valor >= 80: return "#28a745"
    elif valor >= 60: return "#ffc107"
    else: return "#dc3545"

def interpret_ndvi_value(valor):
    if valor >= 0.6: return "Vigor excelente"
    elif valor >= 0.4: return "Vigor bueno"
    elif valor >= 0.3: return "Vigor moderado"
    else: return "Posible estrés"

def interpret_variability(valor):
    if valor <= 15: return "Muy uniforme"
    elif valor <= 25: return "Uniforme"
    elif valor <= 35: return "Moderadamente variable"
    else: return "Muy variable"

def get_ndvi_status_badge(valor):
    if valor >= 0.6:
        return dbc.Badge("Excelente", color="success")
    elif valor >= 0.4:
        return dbc.Badge("Bueno", color="warning")
    elif valor >= 0.3:
        return dbc.Badge("Moderado", color="info")
    else:
        return dbc.Badge("Alerta", color="danger")

def get_variability_badge(valor):
    if valor <= 15:
        return dbc.Badge("Muy Uniforme", color="success")
    elif valor <= 25:
        return dbc.Badge("Uniforme", color="info")
    elif valor <= 35:
        return dbc.Badge("Variable", color="warning")
    else:
        return dbc.Badge("Muy Variable", color="danger")

def get_area_badge(valor):
    if valor >= 80:
        return dbc.Badge("Excelente", color="success")
    elif valor >= 60:
        return dbc.Badge("Buena", color="info")
    elif valor >= 40:
        return dbc.Badge("Regular", color="warning")
    else:
        return dbc.Badge("Deficiente", color="danger")

def get_alert_badge(valor):
    if valor <= 10:
        return dbc.Badge("Sin problemas", color="success")
    elif valor <= 25:
        return dbc.Badge("Alerta menor", color="warning")
    else:
        return dbc.Badge("Alerta mayor", color="danger")

def create_temporal_analysis_chart(historical_data):
    """
    Crea gráfico de análisis temporal de KPIs
    """
    if not historical_data:
        return dcc.Graph(figure=go.Figure())
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Vigor General", "Estrés Hídrico", "Uniformidad", "Potencial Productivo"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Datos simulados para demostración
    dates = [datetime.now() - timedelta(days=x*7) for x in range(12, 0, -1)]
    
    # Vigor General
    vigor_data = np.random.normal(70, 10, 12)
    fig.add_trace(
        go.Scatter(x=dates, y=vigor_data, name="Vigor", line=dict(color="#28a745")),
        row=1, col=1
    )
    
    # Estrés Hídrico
    estres_data = np.random.normal(30, 8, 12)
    fig.add_trace(
        go.Scatter(x=dates, y=estres_data, name="Estrés", line=dict(color="#dc3545")),
        row=1, col=2
    )
    
    # Uniformidad
    uniformidad_data = np.random.normal(75, 5, 12)
    fig.add_trace(
        go.Scatter(x=dates, y=uniformidad_data, name="Uniformidad", line=dict(color="#007bff")),
        row=2, col=1
    )
    
    # Potencial Productivo
    potencial_data = np.random.normal(68, 12, 12)
    fig.add_trace(
        go.Scatter(x=dates, y=potencial_data, name="Potencial", line=dict(color="#6f42c1")),
        row=2, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text="Evolución Temporal de KPIs (Últimas 12 semanas)"
    )
    
    return dcc.Graph(figure=fig)
