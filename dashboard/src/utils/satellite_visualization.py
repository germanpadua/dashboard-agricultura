"""
Utilidades de visualización mejoradas para datos satelitales.

Módulo especializado en crear gráficos profesionales y visualizaciones
para análisis de índices de vegetación (NDVI, OSAVI, NDRE) con enfoque
en aplicaciones agrícolas.

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import logging
from typing import Dict, List, Optional, Tuple

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Librerías de Dash
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)

# Paleta de colores profesional para índices de vegetación
SATELLITE_COLORS = {
    'NDVI': {
        'primary': '#2ECC71',
        'secondary': '#27AE60',
        'gradient': ['#E8F5E8', '#2ECC71', '#1E8449']
    },
    'OSAVI': {
        'primary': '#3498DB',
        'secondary': '#2980B9',
        'gradient': ['#EBF3FD', '#3498DB', '#1F4E79']
    },
    'NDRE': {
        'primary': '#E74C3C',
        'secondary': '#C0392B',
        'gradient': ['#FDEDEC', '#E74C3C', '#922B21']
    },
    'anomaly': {
        'primary': '#F39C12',
        'secondary': '#E67E22',
        'gradient': ['#FDF2E9', '#F39C12', '#A6540D']
    }
}

def create_professional_kpi_cards(analysis_data: Dict) -> List[html.Div]:
    """
    Crea tarjetas KPI profesionales con estilo mejorado.
    
    Args:
        analysis_data: Diccionario con datos de análisis por índice
        
    Returns:
        Lista de componentes html.Div con las tarjetas KPI
    """
    cards = []
    
    for index_name, data in analysis_data.items():
        if 'array' not in data:
            continue
            
        # Deserializar datos del array
        import base64
        import pickle
        array = pickle.loads(base64.b64decode(data['array']))
        
        # Calcular estadísticas básicas
        valid_pixels = np.isfinite(array).sum()
        total_pixels = array.size
        mean_val = float(np.nanmean(array))
        std_val = float(np.nanstd(array))
        min_val = float(np.nanmin(array))
        max_val = float(np.nanmax(array))
        
        # Obtener esquema de colores
        colors = SATELLITE_COLORS.get(index_name, SATELLITE_COLORS['NDVI'])
        
        # Evaluación de salud del cultivo
        if index_name == 'NDVI':
            if mean_val > 0.6:
                health_status = "Excelente"
                health_color = "#27AE60"
                health_icon = "fas fa-leaf"
            elif mean_val > 0.4:
                health_status = "Buena"
                health_color = "#F39C12"
                health_icon = "fas fa-seedling"
            else:
                health_status = "Moderada"
                health_color = "#E74C3C"
                health_icon = "fas fa-exclamation-triangle"
        else:
            health_status = "Normal"
            health_color = colors['primary']
            health_icon = "fas fa-chart-line"
        
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-satellite me-2", style={"color": colors['primary']}),
                    html.H5(f"Índice {index_name}", className="mb-0", style={"color": "#2c3e50"})
                ], className="d-flex align-items-center")
            ], style={"background": f"linear-gradient(135deg, {colors['gradient'][0]}, {colors['gradient'][1]})", "border": "none"}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H3(f"{mean_val:.3f}", className="text-center mb-2", 
                               style={"color": colors['primary'], "fontWeight": "bold"}),
                        html.P("Valor Promedio", className="text-center text-muted mb-0")
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            html.I(className=health_icon, style={"color": health_color, "fontSize": "1.5rem"}),
                            html.Span(health_status, className="ms-2", style={"color": health_color, "fontWeight": "600"})
                        ], className="text-center")
                    ], md=6)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-arrow-up me-1", style={"color": "#27AE60"}),
                            f"Máx: {max_val:.3f}"
                        ], className="d-block text-muted"),
                        html.Small([
                            html.I(className="fas fa-arrow-down me-1", style={"color": "#E74C3C"}),
                            f"Mín: {min_val:.3f}"
                        ], className="d-block text-muted"),
                    ], md=6),
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-chart-bar me-1", style={"color": "#3498DB"}),
                            f"σ: {std_val:.3f}"
                        ], className="d-block text-muted"),
                        html.Small([
                            html.I(className="fas fa-eye me-1", style={"color": "#9B59B6"}),
                            f"Píxeles: {valid_pixels:,}"
                        ], className="d-block text-muted"),
                    ], md=6)
                ])
            ])
        ], className="satellite-kpi-card mb-3")
        
        cards.append(card)
    
    return cards

def create_enhanced_histogram_chart(analysis_data: Dict) -> go.Figure:
    """
    Crea gráfico de distribución simplificado.
    
    Genera histogramas de distribución para índices de vegetación
    con líneas de referencia para niveles de salud.
    
    Args:
        analysis_data: Diccionario con datos de análisis por índice
        
    Returns:
        Figura de Plotly con histograma de distribución
    """
    # Usar el primer índice disponible (típicamente NDVI) para simplificar
    main_index = list(analysis_data.keys())[0] if analysis_data else 'NDVI'
    
    if main_index not in analysis_data or 'array' not in analysis_data[main_index]:
        # Crear gráfico vacío si no hay datos
        return _create_empty_satellite_chart(
            "No hay datos disponibles para mostrar la distribución",
            "Distribución de Índices de Vegetación"
        )
    
    # Deserializar datos del array
    import base64
    import pickle
    array = pickle.loads(base64.b64decode(analysis_data[main_index]['array']))
    valid_data = array[np.isfinite(array)]
    
    colors = SATELLITE_COLORS.get(main_index, SATELLITE_COLORS['NDVI'])
    
    # Crear figura con histograma único
    fig = go.Figure()
    
    # Histograma principal de distribución
    fig.add_trace(
        go.Histogram(
            x=valid_data,
            nbinsx=20,  # Número óptimo de bins para claridad
            name=f"Distribución {main_index}",
            marker=dict(
                color=colors['primary'],
                line=dict(color=colors['secondary'], width=1)
            ),
            opacity=0.8
        )
    )
    
    # Agregar líneas de referencia para niveles de salud
    fig.add_vline(
        x=0.6, 
        line_dash="dash", 
        line_color="#27AE60", 
        annotation_text="Excelente",
        annotation_position="top"
    )
    fig.add_vline(
        x=0.4, 
        line_dash="dash", 
        line_color="#F39C12", 
        annotation_text="Buena",
        annotation_position="top"
    )
    fig.add_vline(
        x=0.2, 
        line_dash="dash", 
        line_color="#E67E22", 
        annotation_text="Moderada",
        annotation_position="top"
    )
    
    # Estadísticas básicas como texto
    mean_val = np.mean(valid_data)
    std_val = np.std(valid_data)
    
    fig.add_annotation(
        text=f"Promedio: {mean_val:.3f}<br>Desviación: {std_val:.3f}<br>Píxeles: {len(valid_data):,}",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        font=dict(size=10, color="#2c3e50")
    )
    
    fig.update_layout(
        height=350,
        showlegend=False,
        title=dict(
            text=f"📊 Distribución de Valores {main_index}",
            x=0.5,
            font=dict(size=16, color="#2c3e50")
        ),
        xaxis_title=f"Valor {main_index}",
        yaxis_title="Frecuencia (píxeles)",
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def _create_empty_satellite_chart(message: str, title: str) -> go.Figure:
    """
    Crea un gráfico vacío con mensaje personalizado.
    
    Args:
        message: Mensaje a mostrar en el gráfico vacío
        title: Título del gráfico
        
    Returns:
        Figura de Plotly vacía con mensaje
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#7f8c8d")
    )
    fig.update_layout(
        height=300,
        title=title,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_comparative_analysis_chart(
    current_data: Dict, historical_data: Optional[Dict] = None
) -> go.Figure:
    """
    Crea gráfico comparativo simplificado enfocado en promedios.
    
    Args:
        current_data: Datos del período actual
        historical_data: Datos históricos de referencia (opcional)
        
    Returns:
        Figura de Plotly con comparación temporal
    """
    fig = go.Figure()
    
    indices = list(current_data.keys())
    
    current_means = []
    current_stds = []
    historical_means = []
    historical_stds = []
    
    for idx in indices:
        # Datos actuales
        import base64
        import pickle
        array = pickle.loads(base64.b64decode(current_data[idx]['array']))
        current_means.append(np.nanmean(array))
        current_stds.append(np.nanstd(array))
        
        # Datos históricos (si están disponibles)
        if historical_data and idx in historical_data:
            hist_array = pickle.loads(base64.b64decode(historical_data[idx]['array']))
            historical_means.append(np.nanmean(hist_array))
            historical_stds.append(np.nanstd(hist_array))
        else:
            historical_means.append(None)
            historical_stds.append(None)
    
    # Current data bars
    fig.add_trace(
        go.Bar(
            x=indices,
            y=current_means,
            error_y=dict(type='data', array=current_stds, visible=True),
            name='Periodo Actual',
            marker=dict(
                color='#2ECC71',
                line=dict(color='#27AE60', width=2)
            ),
            opacity=0.8
        )
    )
    
    # Historical data bars (if available)
    if any(h is not None for h in historical_means):
        fig.add_trace(
            go.Bar(
                x=indices,
                y=[h for h in historical_means if h is not None],
                error_y=dict(type='data', array=[h for h in historical_stds if h is not None], visible=True),
                name='Referencia Histórica',
                marker=dict(
                    color='#3498DB',
                    line=dict(color='#2980B9', width=2)
                ),
                opacity=0.8
            )
        )
    
    fig.update_layout(
        title=dict(
            text="📈 Comparación Temporal de Índices",
            x=0.5,
            font=dict(size=16, color="#2c3e50")
        ),
        xaxis=dict(title="Índices de Vegetación"),
        yaxis=dict(title="Valor Promedio"),
        barmode='group',
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    
    return fig

def create_temporal_evolution_chart(temporal_data: List[Dict], index_name: str = "NDVI") -> go.Figure:
    """
    Create temporal evolution chart for time series analysis
    """
    if not temporal_data:
        return go.Figure()
    
    dates = []
    values = []
    std_values = []
    
    for data_point in temporal_data:
        if 'date' in data_point and 'array' in data_point:
            dates.append(pd.to_datetime(data_point['date']))
            
            # Deserialize array
            import pickle, base64
            array = pickle.loads(base64.b64decode(data_point['array']))
            values.append(np.nanmean(array))
            std_values.append(np.nanstd(array))
    
    colors = SATELLITE_COLORS.get(index_name, SATELLITE_COLORS['NDVI'])
    
    fig = go.Figure()
    
    # Main trend line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=f'{index_name} Promedio',
            line=dict(color=colors['primary'], width=3),
            marker=dict(size=8, color=colors['primary'])
        )
    )
    
    # Error bands (standard deviation)
    upper_bound = [v + s for v, s in zip(values, std_values)]
    lower_bound = [v - s for v, s in zip(values, std_values)]
    
    fig.add_trace(
        go.Scatter(
            x=dates + dates[::-1],
            y=upper_bound + lower_bound[::-1],
            fill='toself',
            fillcolor=colors['primary'].replace('1)', '0.2)'),
            line=dict(color='rgba(0,0,0,0)'),
            name='Desviación Estándar',
            showlegend=True
        )
    )
    
    fig.update_layout(
        title=dict(
            text=f"📈 Evolución Temporal del {index_name}",
            x=0.5,
            font=dict(size=16, color="#2c3e50")
        ),
        xaxis=dict(title="Fecha"),
        yaxis=dict(title=f"Valor {index_name}"),
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_anomaly_analysis_chart(anomaly_data: Dict) -> go.Figure:
    """
    Crear gráfico de anomalías simplificado y claro para agricultores
    """
    import pickle, base64
    array = pickle.loads(base64.b64decode(anomaly_data['array']))
    valid_data = array[np.isfinite(array)]
    
    if len(valid_data) == 0:
        return go.Figure()
    
    # Calcular estadísticas básicas
    mean_val = np.mean(valid_data)
    std_val = np.std(valid_data)
    
    # Clasificar anomalías de forma simple
    positive_anomalies = np.sum(valid_data > 0.1)  # Crecimiento inusual
    normal_range = np.sum((valid_data >= -0.1) & (valid_data <= 0.1))  # Rango normal
    negative_anomalies = np.sum(valid_data < -0.1)  # Decrecimiento preocupante
    
    total = len(valid_data)
    
    # Crear gráfico de barras simple en lugar de histograma complejo
    fig = go.Figure()
    
    categories = ['Crecimiento<br>Inusual', 'Rango<br>Normal', 'Posible<br>Problema']
    values = [positive_anomalies/total*100, normal_range/total*100, negative_anomalies/total*100]
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
            name='Distribución de Anomalías'
        )
    )
    
    # Agregar interpretación como anotación
    interpretation = ""
    if negative_anomalies/total > 0.3:
        interpretation = "⚠️ Áreas con posible estrés detectadas. Revisa riego y nutrición."
    elif positive_anomalies/total > 0.2:
        interpretation = "🌱 Crecimiento excepcional detectado. ¡Buen manejo!"
    else:
        interpretation = "😊 Desarrollo normal del cultivo. Sin anomalías significativas."
    
    fig.add_annotation(
        text=interpretation,
        xref="paper", yref="paper",
        x=0.5, y=1.15,
        showarrow=False,
        align="center",
        font=dict(size=12, color="#2c3e50", family="Inter"),
        bgcolor="rgba(241, 196, 15, 0.1)",
        bordercolor="#F1C40F",
        borderwidth=1
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title=dict(
            text="📊 Análisis de Anomalías en el Cultivo",
            x=0.5,
            font=dict(size=16, color="#2c3e50")
        ),
        xaxis=dict(
            title="Estado del Cultivo"),
        yaxis=dict(
            title="Porcentaje del Área (%)"
        ),
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=100, b=60, l=60, r=40)
    )
    
    return fig

def create_health_assessment_card(analysis_data: Dict) -> html.Div:
    """
    Crear tarjeta simplificada de evaluación de salud vegetal para agricultores
    """
    if 'NDVI' not in analysis_data:
        return html.Div("No hay datos de NDVI para evaluación de salud")
    
    # Deserialize NDVI data
    import pickle, base64
    ndvi_array = pickle.loads(base64.b64decode(analysis_data['NDVI']['array']))
    
    # Health calculations
    valid_pixels = np.isfinite(ndvi_array)
    total_pixels = ndvi_array.size
    valid_data = ndvi_array[valid_pixels]
    
    if len(valid_data) == 0:
        return html.Div("No hay datos válidos para evaluación")
    
    mean_ndvi = np.mean(valid_data)
    
    # Classification zones (rangos más claros para agricultores)
    excellent = np.sum(valid_data > 0.6)  # NDVI > 0.6: Vegetación muy densa y saludable
    good = np.sum((valid_data > 0.4) & (valid_data <= 0.6))  # 0.4-0.6: Vegetación saludable
    moderate = np.sum((valid_data > 0.2) & (valid_data <= 0.4))  # 0.2-0.4: Vegetación moderada
    poor = np.sum(valid_data <= 0.2)  # ≤ 0.2: Vegetación débil o suelo desnudo
    
    total_valid = len(valid_data)
    
    # Overall health score (ponderado)
    health_score = (excellent * 4 + good * 3 + moderate * 2 + poor * 1) / (total_valid * 4) * 100
    
    # Determine overall status
    if health_score >= 75:
        overall_status = "Excelente"
        status_color = "#27AE60"
        status_icon = "fas fa-leaf"
        advice = "Tu cultivo está en óptimas condiciones. Mantén el programa actual."
    elif health_score >= 50:
        overall_status = "Buena"
        status_color = "#F39C12"
        status_icon = "fas fa-seedling"
        advice = "Salud vegetal buena. Considera optimizar riego o nutrientes."
    elif health_score >= 25:
        overall_status = "Moderada"
        status_color = "#E67E22"
        status_icon = "fas fa-exclamation-triangle"
        advice = "Requiere atención. Revisa riego, plagas y nutrición."
    else:
        overall_status = "Crítica"
        status_color = "#E74C3C"
        status_icon = "fas fa-exclamation-circle"
        advice = "Situación crítica. Intervención inmediata necesaria."
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className=status_icon, style={"color": status_color}),
                " Estado General del Cultivo"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            # Puntuación principal más destacada
            html.Div([
                html.H1(f"{health_score:.0f}", 
                        className="display-4 text-center mb-0",
                        style={"color": status_color, "fontWeight": "900"}),
                html.P("PUNTOS DE SALUD", 
                      className="text-center text-muted small mb-2",
                      style={"letterSpacing": "1px"}),
                html.H4(overall_status, 
                       className="text-center mb-3",
                       style={"color": status_color, "fontWeight": "600"}),
            ], className="mb-4"),
            
            # Explicación clara del porcentaje
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Strong("¿Qué significa esta puntuación? "),
                f"De cada 100 píxeles analizados en tu parcela, {health_score:.0f} muestran condiciones óptimas de vegetación."
            ], color="info", className="mb-3"),
            
            # Distribución simplificada
            html.H6("Distribución por Estado:", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5(f"{excellent/total_valid*100:.0f}%", 
                               style={"color": "#27AE60", "fontWeight": "bold"}),
                        html.Small("Excelente", className="text-muted")
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H5(f"{good/total_valid*100:.0f}%", 
                               style={"color": "#F39C12", "fontWeight": "bold"}),
                        html.Small("Buena", className="text-muted")
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H5(f"{moderate/total_valid*100:.0f}%", 
                               style={"color": "#E67E22", "fontWeight": "bold"}),
                        html.Small("Moderada", className="text-muted")
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H5(f"{poor/total_valid*100:.0f}%", 
                               style={"color": "#E74C3C", "fontWeight": "bold"}),
                        html.Small("Crítica", className="text-muted")
                    ], className="text-center")
                ], md=3)
            ], className="mb-3"),
            
            # Consejo práctico
            dbc.Alert([
                html.I(className="fas fa-lightbulb me-2"),
                html.Strong("Recomendación: "),
                advice
            ], color="light", className="border-0", style={"backgroundColor": "#f8f9fa"})
        ])
    ], className="satellite-kpi-card")