"""
Funciones adicionales para el sistema de alertas histórico de repilo
Complemento del layout_historico.py con funcionalidades específicas
"""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def create_risk_evolution_chart(weather_data, period_type="7d"):
    """
    Crea gráfico de evolución del riesgo de repilo a lo largo del tiempo
    """
    if not weather_data or len(weather_data) == 0:
        return _create_empty_risk_chart()
    
    df = pd.DataFrame(weather_data)
    if df.empty or 'timestamp' not in df.columns:
        return _create_empty_risk_chart()
    
    # Convertir timestamp si es necesario
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df = df.sort_values('timestamp')
    
    # Calcular score de riesgo diario
    daily_risk_scores = []
    for _, row in df.iterrows():
        risk_score = _calculate_daily_risk_score(row)
        daily_risk_scores.append(risk_score)
    
    df['risk_score'] = daily_risk_scores
    
    # Crear el gráfico
    fig = go.Figure()
    
    # Línea principal de riesgo
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['risk_score'],
        mode='lines+markers',
        name='Score de Riesgo',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=6, color='#e74c3c', opacity=0.8),
        hovertemplate='<b>%{x}</b><br>Score de Riesgo: %{y:.1f}/100<extra></extra>'
    ))
    
    # Zonas de riesgo como bandas de color
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(40, 167, 69, 0.1)", 
                  layer="below", line_width=0)
    fig.add_hrect(y0=30, y1=50, fillcolor="rgba(23, 162, 184, 0.1)", 
                  layer="below", line_width=0)
    fig.add_hrect(y0=50, y1=70, fillcolor="rgba(255, 193, 7, 0.1)", 
                  layer="below", line_width=0)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(220, 53, 69, 0.1)", 
                  layer="below", line_width=0)
    
    # Líneas de referencia
    fig.add_hline(y=30, line_dash="dash", line_color="#28a745", 
                  annotation_text="Umbral Vigilancia", annotation_position="right")
    fig.add_hline(y=50, line_dash="dash", line_color="#ffc107", 
                  annotation_text="Umbral Alto", annotation_position="right")
    fig.add_hline(y=70, line_dash="dash", line_color="#dc3545", 
                  annotation_text="Umbral Crítico", annotation_position="right")
    
    # Configuración del layout
    fig.update_layout(
        title={
            'text': '📈 Evolución del Riesgo de Repilo - Análisis Histórico',
            'x': 0.5,
            'font': {'size': 16, 'family': 'Arial, sans-serif'}
        },
        xaxis={
            'title': 'Fecha',
            'showgrid': True,
            'gridcolor': 'rgba(128, 128, 128, 0.2)'
        },
        yaxis={
            'title': 'Score de Riesgo (0-100)',
            'range': [0, 100],
            'showgrid': True,
            'gridcolor': 'rgba(128, 128, 128, 0.2)'
        },
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig

def _calculate_daily_risk_score(row):
    """
    Calcula el score de riesgo para un día específico
    """
    risk_score = 0
    
    # Obtener valores con defaults seguros
    temp = row.get('temperature', 15)
    humidity = row.get('humidity', 70)
    precipitation = row.get('precipitation', 0)
    
    # Temperatura (peso: 30%)
    if 15 <= temp <= 20:  # Óptimo para repilo
        risk_score += 30
    elif 12 <= temp <= 22:  # Crítico pero no óptimo
        risk_score += 20
    elif 10 <= temp <= 25:  # Moderado
        risk_score += 10
    # Fuera del rango: 0 puntos
    
    # Humedad (peso: 40%)
    if humidity >= 95:  # Extrema
        risk_score += 40
    elif humidity >= 85:  # Crítica
        risk_score += 30
    elif humidity >= 75:  # Moderada
        risk_score += 15
    elif humidity >= 65:  # Baja
        risk_score += 5
    # Menor a 65%: 0 puntos
    
    # Precipitación (peso: 30%)
    if precipitation > 10:  # Lluvia intensa
        risk_score += 30
    elif precipitation > 5:  # Lluvia moderada
        risk_score += 20
    elif precipitation > 1:  # Lluvia ligera
        risk_score += 15
    elif precipitation > 0:  # Rocío/humedad
        risk_score += 10
    # Sin precipitación: 0 puntos
    
    return min(100, risk_score)  # Máximo 100

def _create_empty_risk_chart():
    """
    Crea un gráfico vacío cuando no hay datos
    """
    fig = go.Figure()
    
    fig.update_layout(
        title='📊 Evolución del Riesgo de Repilo',
        xaxis={'title': 'Fecha', 'showgrid': False},
        yaxis={'title': 'Score de Riesgo (0-100)', 'range': [0, 100], 'showgrid': False},
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        annotations=[
            dict(
                text="🔄 Seleccione un período con datos meteorológicos<br>para visualizar la evolución del riesgo de repilo",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="#6c757d"),
                align="center"
            )
        ]
    )
    
    return fig

def create_period_statistics_panel(weather_data, period_info):
    """
    Crea panel de estadísticas del período analizado
    """
    import dash_bootstrap_components as dbc
    from dash import html
    
    if not weather_data or len(weather_data) == 0:
        return dbc.Alert("No hay datos disponibles para el período seleccionado", color="warning")
    
    df = pd.DataFrame(weather_data)
    
    # Calcular estadísticas
    stats = {
        'total_days': len(df),
        'avg_temp': df['temperature'].mean() if 'temperature' in df.columns else 0,
        'avg_humidity': df['humidity'].mean() if 'humidity' in df.columns else 0,
        'total_precipitation': df['precipitation'].sum() if 'precipitation' in df.columns else 0,
        'rainy_days': (df['precipitation'] > 0).sum() if 'precipitation' in df.columns else 0
    }
    
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.H5(f"{stats['total_days']}", className="mb-1 fw-bold text-primary"),
                html.Small("Días analizados", className="text-muted")
            ], className="text-center")
        ], md=2),
        dbc.Col([
            html.Div([
                html.H5(f"{stats['avg_temp']:.1f}°C", className="mb-1 fw-bold text-warning"),
                html.Small("Temp. promedio", className="text-muted")
            ], className="text-center")
        ], md=2),
        dbc.Col([
            html.Div([
                html.H5(f"{stats['avg_humidity']:.1f}%", className="mb-1 fw-bold text-info"),
                html.Small("Humedad promedio", className="text-muted")
            ], className="text-center")
        ], md=2),
        dbc.Col([
            html.Div([
                html.H5(f"{stats['total_precipitation']:.1f}mm", className="mb-1 fw-bold text-success"),
                html.Small("Precipitación total", className="text-muted")
            ], className="text-center")
        ], md=3),
        dbc.Col([
            html.Div([
                html.H5(f"{stats['rainy_days']}", className="mb-1 fw-bold text-secondary"),
                html.Small("Días con lluvia", className="text-muted")
            ], className="text-center")
        ], md=3)
    ])