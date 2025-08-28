"""
Gráficos simplificados para datos históricos.

Módulo que proporciona visualizaciones simplificadas para datos meteorológicos
históricos con énfasis en zonas de riesgo para cultivos.

Funcionalidades:
- Precipitación (histograma) + Humedad (líneas) con zonas de riesgo
- Temperatura (min, media, máx) con zonas de riesgo

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
from datetime import datetime, timedelta

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_precipitation_humidity_chart(df: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico combinado de precipitación y humedad con zonas de riesgo - Estilo Premium.
    
    Args:
        df: DataFrame con datos meteorológicos que debe contener:
            - 'Dates': Fechas de las observaciones
            - 'Rain': Precipitación en mm
            - 'Air_Relat_Hum': Humedad relativa en %
            
    Returns:
        Figura de Plotly con gráfico de doble eje mejorado visualmente
    """
    if df.empty:
        return create_empty_chart("No hay datos de precipitación/humedad disponibles")
    
    # Crear subplot con doble eje Y - Diseño elegante
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["<b>💧 Humedad y Precipitación - Análisis de Riesgo de Repilo</b>"]
    )
    
    # Zona de riesgo repilo: Humedad > 95% - Diseño premium
    if not df.empty:
        x_min, x_max = df['Dates'].min(), df['Dates'].max()
        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[95, 95, 105, 105, 95],
                fill="toself",
                fillcolor="rgba(239, 68, 68, 0.08)",
                line=dict(color="rgba(239, 68, 68, 0.3)", width=1),
                name="🔴 Zona Crítica Humedad",
                hovertemplate="<b>🔴 ZONA CRÍTICA</b><br>" +
                             "Humedad > 95%<br>" +
                             "Alto riesgo de repilo<br>" +
                             "<extra></extra>",
                showlegend=True
            ),
            secondary_y=True
        )
    
    # Precipitación como barras elegantes
    fig.add_trace(
        go.Bar(
            x=df['Dates'],
            y=df['Rain'],
            name="☔ Precipitación",
            marker=dict(
                color=df['Rain'],
                colorscale=[
                    [0, 'rgba(59, 130, 246, 0.3)'],
                    [0.5, 'rgba(59, 130, 246, 0.6)'],
                    [1, 'rgba(37, 99, 235, 0.9)']
                ],
                line=dict(color='rgba(59, 130, 246, 0.5)', width=0.5),
                opacity=0.8
            ),
            hovertemplate="<b>☔ Precipitación</b><br>" +
                         "%{x|%d/%m/%Y %H:%M}<br>" +
                         "<b>%{y:.1f} mm</b><br>" +
                         "<extra></extra>"
        ),
        secondary_y=False
    )
    
    # Humedad como línea suave
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df['Air_Relat_Hum'],
            mode='lines+markers',
            name='💧 Humedad Relativa',
            line=dict(
                color='#0ea5e9',
                width=3,
                shape='spline',
                smoothing=0.8
            ),
            marker=dict(
                size=4,
                color='#0ea5e9',
                line=dict(color='white', width=1),
                symbol='circle'
            ),
            hovertemplate="<b>💧 Humedad Relativa</b><br>" +
                         "%{x|%d/%m/%Y %H:%M}<br>" +
                         "<b>%{y:.1f}%</b><br>" +
                         "<extra></extra>"
        ),
        secondary_y=True
    )
    
    # Resaltar períodos críticos de humedad con marcadores destacados
    critical_humidity = df[df['Air_Relat_Hum'] > 95]
    if not critical_humidity.empty:
        fig.add_trace(
            go.Scatter(
                x=critical_humidity['Dates'],
                y=critical_humidity['Air_Relat_Hum'],
                mode='markers',
                name='💧 Humedad Crítica',
                marker=dict(
                    color='#dc2626',
                    size=10,
                    symbol='triangle-up',
                    line=dict(color='white', width=3),
                    opacity=1
                ),
                hovertemplate="<b>💧 HUMEDAD CRÍTICA</b><br>" +
                             "%{x|%d/%m/%Y %H:%M}<br>" +
                             "<b>%{y:.1f}%</b><br>" +
                             "🦠 <b>ALTO RIESGO DE REPILO</b><br>" +
                             "<extra></extra>"
            ),
            secondary_y=True
        )
    
    # Configurar ejes - Diseño moderno
    fig.update_yaxes(
        title_text="<b>Precipitación (mm)</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=12, color='#6b7280'),
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        zeroline=False,
        secondary_y=False,
        rangemode="tozero"
    )
    
    fig.update_yaxes(
        title_text="<b>Humedad (%)</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=12, color='#6b7280'),
        secondary_y=True,
        range=[40, 105],
        showgrid=False
    )
    
    fig.update_xaxes(
        title_text="<b>Fecha y Hora</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=11, color='#6b7280'),
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        zeroline=False
    )
    
    # Layout premium
    fig.update_layout(
        template="plotly_white",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="rgba(209, 213, 219, 0.8)",
            borderwidth=1,
            font=dict(size=11, family='Inter, sans-serif'),
            itemsizing="constant"
        ),
        plot_bgcolor='rgba(249, 250, 251, 0.3)',
        paper_bgcolor='#ffffff',
        margin=dict(l=80, r=80, t=80, b=60),
        annotations=[
            dict(
                x=0.5, y=1.15,
                xref='paper', yref='paper',
                text="🦠 <b>Humedad crítica:</b> >95% favorece desarrollo de repilo",
                showarrow=False,
                font=dict(size=11, color='#dc2626', family='Inter, sans-serif'),
                bgcolor="rgba(254, 242, 242, 0.95)",
                bordercolor="rgba(239, 68, 68, 0.3)",
                borderwidth=1,
                borderpad=4,
                xanchor='center'
            )
        ]
    )
    
    return fig

def create_temperature_chart(df: pd.DataFrame, is_aggregated: bool = False) -> go.Figure:
    if df.empty:
        return create_empty_chart("No hay datos de temperatura disponibles")
    
    fig = go.Figure()
    
    # Zona de riesgo repilo: Temperatura óptima 15-20°C - Diseño premium
    if not df.empty:
        x_min, x_max = df['Dates'].min(), df['Dates'].max()
        
        # Zona óptima 15-20°C (riesgo alto)
        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[15, 15, 20, 20, 15],
                fill="toself",
                fillcolor="rgba(239, 68, 68, 0.15)",
                line=dict(color="rgba(239, 68, 68, 0.4)", width=1),
                name="🔴 Riesgo Alto",
                hovertemplate="<b>🔴 ZONA DE RIESGO ALTO</b><br>Temperatura: 15-20°C<br>Condiciones óptimas para repilo<br><extra></extra>",
                showlegend=True
            )
        )
        # Zona moderada 12-15°C
        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[12, 12, 15, 15, 12],
                fill="toself",
                fillcolor="rgba(245, 158, 11, 0.12)",
                line=dict(color="rgba(245, 158, 11, 0.3)", width=1),
                name="🟡 Riesgo Moderado",
                hovertemplate="<b>🟡 ZONA DE RIESGO MODERADO</b><br>Temperatura: 12-15°C<br>Condiciones subóptimas<br><extra></extra>",
                showlegend=True
            )
        )
        # Zona moderada 20-22°C
        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[20, 20, 22, 22, 20],
                fill="toself",
                fillcolor="rgba(245, 158, 11, 0.12)",
                line=dict(color="rgba(245, 158, 11, 0.3)", width=1),
                name="🟡 Riesgo Moderado (Alta)",
                hovertemplate="<b>🟡 ZONA DE RIESGO MODERADO</b><br>Temperatura: 20-22°C<br>Condiciones subóptimas<br><extra></extra>",
                showlegend=False
            )
        )
    
    if is_aggregated and 'Air_Temp_min' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['Dates'], y=df['Air_Temp_min'],
                mode='lines+markers', name='🌡️ Temp. Mínima',
                line=dict(color='#3b82f6', width=2, dash='dash', shape='spline', smoothing=0.8),
                marker=dict(size=4, color='#3b82f6', line=dict(color='white', width=1), symbol='circle'),
                hovertemplate="<b>🌡️ Temperatura Mínima</b><br>%{x|%d/%m/%Y}<br><b>%{y:.1f}°C</b><br><extra></extra>"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df['Dates'], y=df['Air_Temp_mean'],
                mode='lines+markers', name='🌡️ Temp. Media',
                line=dict(color='#dc2626', width=3, shape='spline', smoothing=0.8),
                marker=dict(size=6, color='#dc2626', line=dict(color='white', width=1), symbol='circle'),
                hovertemplate="<b>🌡️ Temperatura Media</b><br>%{x|%d/%m/%Y}<br><b>%{y:.1f}°C</b><br><extra></extra>"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df['Dates'], y=df['Air_Temp_max'],
                mode='lines+markers', name='🌡️ Temp. Máxima',
                line=dict(color='#f59e0b', width=2, dash='dash', shape='spline', smoothing=0.8),
                marker=dict(size=4, color='#f59e0b', line=dict(color='white', width=1), symbol='circle'),
                hovertemplate="<b>🌡️ Temperatura Máxima</b><br>%{x|%d/%m/%Y}<br><b>%{y:.1f}°C</b><br><extra></extra>"
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df['Dates'], y=df['Air_Temp'],
                mode='lines+markers', name='🌡️ Temperatura',
                line=dict(color='#dc2626', width=3, shape='spline', smoothing=0.8),
                marker=dict(size=5, color='#dc2626', line=dict(color='white', width=1), symbol='circle'),
                hovertemplate="<b>🌡️ Temperatura</b><br>%{x|%d/%m/%Y %H:%M}<br><b>%{y:.1f}°C</b><br><extra></extra>"
            )
        )
    
    # Marcadores críticos
    temp_col = 'Air_Temp_mean' if is_aggregated else 'Air_Temp'
    if temp_col in df.columns:
        critical_temp = df[(df[temp_col] >= 15) & (df[temp_col] <= 20)]
        if not critical_temp.empty:
            fig.add_trace(
                go.Scatter(
                    x=critical_temp['Dates'], y=critical_temp[temp_col],
                    mode='markers', name='🔥 Temperatura Crítica',
                    marker=dict(color='#dc2626', size=12, symbol='diamond-wide',
                                line=dict(color='white', width=3), opacity=1),
                    hovertemplate="<b>🔥 TEMPERATURA CRÍTICA</b><br>%{x}<br><b>%{y:.1f}°C</b><br>🦠 <b>ALTO RIESGO DE REPILO</b><br><extra></extra>"
                )
            )
    
    # Layout premium
    fig.update_layout(
        template="plotly_white",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="rgba(209, 213, 219, 0.8)", borderwidth=1,
            font=dict(size=11, family='Inter, sans-serif'), itemsizing="constant"
        ),
        plot_bgcolor='rgba(249, 250, 251, 0.3)',
        paper_bgcolor='#ffffff',
        margin=dict(l=80, r=80, t=110, b=60),  # ↑ margen superior
        xaxis=dict(
            title="<b>Fecha y Hora</b>",
            title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
            tickfont=dict(size=11, color='#6b7280'),
            gridcolor='rgba(107, 114, 128, 0.1)', gridwidth=1,
            showgrid=True, zeroline=False
        ),
        yaxis=dict(
            title="<b>Temperatura (°C)</b>",
            title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
            tickfont=dict(size=12, color='#6b7280'),
            gridcolor='rgba(107, 114, 128, 0.1)', gridwidth=1,
            showgrid=True, zeroline=False
        ),
        annotations=[
            dict(
                x=0.5, y=1.15,
                xref='paper', yref='paper',
                text="🦠 <b>Temperatura crítica:</b> 15-20°C favorece desarrollo de repilo",
                showarrow=False,
                font=dict(size=11, color='#dc2626', family='Inter, sans-serif'),
                bgcolor="rgba(254, 242, 242, 0.95)",
                bordercolor="rgba(239, 68, 68, 0.3)",
                borderwidth=1, borderpad=4,
                xanchor='center',
                yanchor='bottom'  # ← clave para que no tape la leyenda
            )
        ]
    )
    return fig

def create_empty_chart(message: str) -> go.Figure:
    """
    Crea gráfico vacío con mensaje personalizado.
    
    Args:
        message: Mensaje a mostrar en el gráfico vacío
        
    Returns:
        Figura de Plotly vacía con mensaje
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig