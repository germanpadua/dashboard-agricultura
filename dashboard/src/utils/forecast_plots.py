# -*- coding: utf-8 -*-
"""
Utilidades de visualización para predicciones meteorológicas con análisis de riesgo de repilo.

Este módulo proporciona funciones especializadas para crear visualizaciones interactivas
de predicciones meteorológicas con énfasis en el análisis de riesgo de repilo del olivo.

Funcionalidades principales:
- Gráficos de resumen semanal con indicadores de riesgo diario
- Visualizaciones de predicción 48h con lluvia, temperatura y humedad
- Zonas de riesgo científicas resaltadas según parámetros agronómicos
- Análisis automático de condiciones favorables para el desarrollo de la enfermedad

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES DE CONFIGURACIÓN PARA ANÁLISIS DE REPILO
# ============================================================================

# Colores para diferentes niveles de riesgo de repilo basados en Bootstrap
RISK_COLORS = {
    'alto': '#DC3545',      # Rojo - Alto riesgo de repilo
    'moderado': '#FFC107',  # Amarillo - Riesgo moderado
    'bajo': '#28A745',      # Verde - Bajo riesgo
    'sin_datos': '#6C757D'  # Gris - Sin datos disponibles
}

# Rangos de temperatura críticos para el desarrollo de repilo (Venturia oleaginea)
# Basado en literatura científica sobre condiciones óptimas del hongo
CRITICAL_TEMP_RANGE = (15, 20)  # Rango óptimo para desarrollo del hongo (°C)
MODERATE_TEMP_RANGES = [(12, 15), (20, 22)]  # Rangos subóptimos pero de riesgo (°C)

# Umbral crítico de humedad relativa para infección
CRITICAL_HUMIDITY_THRESHOLD = 95  # Porcentaje mínimo para condiciones favorables (%)


# ============================================================================
# FUNCIONES AUXILIARES PARA ZONAS DE RIESGO
# ============================================================================

def _add_risk_zones(fig: go.Figure, x_range: List, row: int = None, col: int = None) -> None:
    """
    Añade zonas de riesgo de temperatura para repilo al gráfico.
    
    Esta función dibuja rectángulos horizontales que representan los rangos de temperatura
    donde el hongo Venturia oleaginea (repilo) tiene condiciones favorables para desarrollarse.
    
    Args:
        fig: Figura de Plotly donde añadir las zonas de riesgo
        x_range: Rango de fechas [fecha_inicio, fecha_fin] para delimitar la zona
        row: Fila del subplot donde añadir la zona (opcional)
        col: Columna del subplot donde añadir la zona (opcional)
    
    Note:
        - Zona crítica: 15-20°C (condiciones óptimas para infección)
        - Zonas moderadas: 12-15°C y 20-22°C (condiciones subóptimas)
    """
    # Zona crítica de temperatura (15-20°C)
    fig.add_hrect(
        y0=CRITICAL_TEMP_RANGE[0],
        y1=CRITICAL_TEMP_RANGE[1],
        fillcolor="rgba(220, 53, 69, 0.4)",
        line_width=3,
        line_color="rgba(220, 53, 69, 1.0)",
        annotation_text="🚨 ZONA CRÍTICA REPILO (15-20°C) 🚨",
        annotation_position="top left",
        annotation=dict(
            font=dict(color="#ffffff", size=14, family="Arial Black"),
            bgcolor="rgba(220, 53, 69, 0.95)",
            bordercolor="#c0392b",
            borderwidth=2,
            borderpad=4
        ),
        layer="below",
        row=row, col=col
    )
    
    # Zonas de riesgo moderado
    for temp_range in MODERATE_TEMP_RANGES:
        position = "bottom left" if temp_range[0] < CRITICAL_TEMP_RANGE[0] else "top right"
        fig.add_hrect(
            y0=temp_range[0], 
            y1=temp_range[1], 
            fillcolor="rgba(255, 193, 7, 0.35)", 
            line_width=2, 
            line_color="rgba(255, 193, 7, 0.9)",
            annotation_text=f"⚠️ Riesgo Moderado ({temp_range[0]}-{temp_range[1]}°C)",
            annotation_position=position,
            annotation=dict(
                font=dict(color="#f39c12", size=12, family="Arial"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#f39c12",
                borderwidth=1
            ),
            layer="below",
            row=row, col=col
        )


def _add_critical_temperature_markers(
    fig: go.Figure,
    data: pd.DataFrame,
    temp_col: str,
    marker_name: str,
    marker_symbol: str = 'star',
    marker_size: int = 12
) -> None:
    """
    Añade marcadores especiales para temperaturas en rango crítico de repilo.
    
    Esta función identifica los puntos de datos donde la temperatura se encuentra
    en el rango crítico (15-20°C) y los marca con símbolos especiales para alertar
    sobre condiciones favorables para el desarrollo de repilo.
    
    Args:
        fig: Figura de Plotly donde añadir los marcadores
        data: DataFrame con datos meteorológicos
        temp_col: Nombre de la columna que contiene la temperatura
        marker_name: Nombre descriptivo para mostrar en la leyenda
        marker_symbol: Símbolo del marcador (por defecto 'star')
        marker_size: Tamaño del marcador en píxeles (por defecto 12)
    
    Example:
        >>> _add_critical_temperature_markers(
        ...     fig, weather_data, 'temperature', 'Temp. Crítica'
        ... )
    """
    # Filtrar temperaturas en rango crítico
    critical_temps = data[
        (data[temp_col] >= CRITICAL_TEMP_RANGE[0]) &
        (data[temp_col] <= CRITICAL_TEMP_RANGE[1])
    ]
    
    if not critical_temps.empty:
        fig.add_trace(
            go.Scatter(
                x=critical_temps['date'],
                y=critical_temps[temp_col],
                mode='markers',
                name=marker_name,
                marker=dict(
                    color='#ff4757',
                    size=marker_size,
                    symbol=marker_symbol,
                    line=dict(color='white', width=3)
                ),
                hovertemplate=f"<b>🚨 TEMPERATURA CRÍTICA</b><br>" +
                             "%{x|%A, %d %b}<br>" +
                             f"🌡️ {temp_col.replace('_', ' ').title()}: %{{y:.1f}}°C<br>" +
                             "⚠️ ZONA DE MÁXIMO RIESGO REPILO<br>" +
                             "<extra></extra>",
                showlegend=True
            )
        )


# ============================================================================
# FUNCIONES PRINCIPALES DE VISUALIZACIÓN
# ============================================================================

def create_weekly_forecast_chart(forecast_data: pd.DataFrame) -> go.Figure:
    """
    Crea un gráfico de resumen semanal con análisis de riesgo de repilo.
    
    Genera una visualización que combina temperaturas máximas/mínimas con zonas de riesgo
    científicamente validadas para el desarrollo del hongo Venturia oleaginea (repilo).
    
    Args:
        forecast_data (pd.DataFrame): DataFrame con predicciones meteorológicas diarias.
            Columnas esperadas:
            - 'date': Fecha de la predicción
            - 'temp_max': Temperatura máxima diaria (°C)
            - 'temp_min': Temperatura mínima diaria (°C)
            - 'humidity': Humedad relativa promedio (%)
            - 'rain': Precipitación diaria (mm)
            - 'risk_level': Nivel de riesgo calculado ('alto', 'moderado', 'bajo')
    
    Returns:
        go.Figure: Figura de Plotly con el gráfico interactivo del resumen semanal.
        
    Raises:
        ValueError: Si el DataFrame está vacío o no contiene las columnas necesarias.
        
    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=7),
        ...     'temp_max': [18, 19, 16, 22, 20, 17, 15],
        ...     'temp_min': [12, 14, 10, 16, 15, 13, 11],
        ...     'humidity': [85, 92, 96, 78, 88, 94, 97],
        ...     'rain': [0, 2.5, 5.0, 0, 1.2, 0, 3.8],
        ...     'risk_level': ['moderado', 'alto', 'alto', 'bajo', 'moderado', 'alto', 'alto']
        ... })
        >>> fig = create_weekly_forecast_chart(df)
        >>> fig.show()
    """
    if forecast_data.empty:
        logger.warning("DataFrame de predicción vacío")
        return create_empty_forecast_chart("No hay datos de predicción semanal disponibles")
    
    # Validar que existan las columnas requeridas para el análisis
    required_columns = ['date', 'temp_max', 'temp_min', 'humidity', 'rain']
    missing_columns = [col for col in required_columns if col not in forecast_data.columns]
    
    if missing_columns:
        error_msg = f"Columnas faltantes en forecast_data: {missing_columns}"
        logger.error(error_msg)
        return create_empty_forecast_chart(f"Datos incompletos: faltan columnas {missing_columns}")
    
    fig = go.Figure()
    
    # Preparar datos de riesgo con valores por defecto
    risk_levels = forecast_data.get('risk_level', ['sin_datos'] * len(forecast_data))
    colors_max = [RISK_COLORS.get(risk, RISK_COLORS['sin_datos']) for risk in risk_levels]
    
    # Barras de temperatura máxima coloreadas por nivel de riesgo
    fig.add_trace(
        go.Bar(
            x=forecast_data['date'],
            y=forecast_data['temp_max'],
            name='Temp. Máxima',
            marker=dict(
                color=colors_max,
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            hovertemplate="<b>%{x|%A, %d %b}</b><br>" +
                         "Temp. Máxima: %{y}°C<br>" +
                         "Riesgo: %{customdata}<br>" +
                         "<extra></extra>",
            customdata=risk_levels
        )
    )
    
    # Línea de temperatura mínima
    fig.add_trace(
        go.Scatter(
            x=forecast_data['date'],
            y=forecast_data['temp_min'],
            mode='lines+markers',
            name='Temp. Mínima',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x|%A, %d %b}</b><br>" +
                         "Temp. Mínima: %{y}°C<br>" +
                         "<extra></extra>"
        )
    )
    
    # ========================================================================
    # ZONAS DE RIESGO DE REPILO (ESTILO HISTÓRICO)
    # ========================================================================
    
    # Obtener rango de fechas para las zonas
    x_min, x_max = forecast_data['date'].min(), forecast_data['date'].max()
    
    # Zona óptima 15-20°C (riesgo alto) - Estilo histórico
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[15, 15, 20, 20, 15],
            fill="toself",
            fillcolor="rgba(220, 53, 69, 0.3)",
            line=dict(color="rgba(220, 53, 69, 0)", width=0),
            name="🔥 RIESGO ALTO (15-20°C)",
            hovertemplate="<b>ZONA RIESGO ALTO</b><br>Temperatura óptima para repilo<extra></extra>",
            showlegend=True
        )
    )
    
    # Zona moderada 12-15°C - Estilo histórico
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[12, 12, 15, 15, 12],
            fill="toself",
            fillcolor="rgba(255, 193, 7, 0.2)",  # Amarillo
            line=dict(color="rgba(255, 193, 7, 0)", width=0),
            name="⚠️ Riesgo Moderado (12-15°C)",
            hovertemplate="<b>ZONA RIESGO MODERADO</b><br>Temperatura subóptima<extra></extra>",
            showlegend=True
        )
    )
    
    # Zona moderada 20-22°C - Estilo histórico
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[20, 20, 22, 22, 20],
            fill="toself",
            fillcolor="rgba(255, 193, 7, 0.2)",  # Amarillo
            line=dict(color="rgba(255, 193, 7, 0)", width=0),
            name="⚠️ Riesgo Moderado (20-22°C)",
            hovertemplate="<b>ZONA RIESGO MODERADO</b><br>Temperatura subóptima<extra></extra>",
            showlegend=True
        )
    )
    
    # Añadir indicadores de precipitación
    rain_days = forecast_data[forecast_data['rain'] > 0]
    if not rain_days.empty:
        fig.add_trace(
            go.Scatter(
                x=rain_days['date'],
                y=rain_days['temp_max'] + 2,  # Colocar encima de las barras
                mode='markers',
                name='Precipitación',
                marker=dict(
                    symbol='circle',
                    size=15,
                    color='#17a2b8',
                    line=dict(color='white', width=2)
                ),
                hovertemplate="<b>%{x|%A, %d %b}</b><br>" +
                             "Lluvia prevista: %{customdata:.1f}mm<br>" +
                             "<extra></extra>",
                customdata=rain_days['rain']
            )
        )
    
    # ========================================================================
    # MARCADORES ESPECIALES PARA ALERTAS DE TEMPERATURA (ESTILO HISTÓRICO)
    # ========================================================================
    
    # Temperaturas máximas en zona crítica (15-20°C) - Estilo histórico
    critical_temps = forecast_data[
        (forecast_data['temp_max'] >= 15) & (forecast_data['temp_max'] <= 20)
    ]
    if not critical_temps.empty:
        fig.add_trace(
            go.Scatter(
                x=critical_temps['date'],
                y=critical_temps['temp_max'],
                mode='markers',
                name='🚨 Temp. Crítica',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='diamond'
                ),
                hovertemplate="<b>🚨 ALERTA REPILO</b><br>" +
                             "Fecha: %{x}<br>" +
                             "Temperatura: %{y:.1f}°C<br>" +
                             "RIESGO ALTO<br>" +
                             "<extra></extra>"
            )
        )
    
    # Configuración del layout (estilo histórico)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Temperatura (°C)",
        template="plotly_white",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_48h_forecast_chart(hourly_data: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico avanzado de predicción meteorológica 48 horas con análisis de repilo.
    
    Esta función genera una visualización completa de las condiciones meteorológicas
    esperadas en las próximas 48 horas, con énfasis especial en la identificación
    de condiciones favorables para el desarrollo de repilo en olivos.
    
    Características principales:
    - Zonas de riesgo de temperatura resaltadas (15-20°C) siguiendo el estilo histórico
    - Indicadores visuales de períodos nocturnos (20:00-06:00)
    - Alertas por humedad crítica (>95%) con marcadores especiales
    - Barras de precipitación con escala secundaria
    - Marcadores especiales para condiciones críticas combinadas
    
    Args:
        hourly_data (pd.DataFrame): DataFrame con predicciones horarias que debe contener:
            - 'datetime': Timestamp de cada observación
            - 'temperature': Temperatura en grados Celsius
            - 'humidity': Humedad relativa en porcentaje (0-100)
            - 'rain': Precipitación en mm
    
    Returns:
        go.Figure: Figura de Plotly con gráfico interactivo de predicción 48h
        
    Raises:
        None: Retorna un gráfico vacío si no hay datos válidos
        
    Example:
        >>> import pandas as pd
        >>> from datetime import datetime, timedelta
        >>> 
        >>> # Crear datos de ejemplo
        >>> dates = pd.date_range(start=datetime.now(), periods=48, freq='H')
        >>> data = pd.DataFrame({
        ...     'datetime': dates,
        ...     'temperature': np.random.normal(18, 3, 48),
        ...     'humidity': np.random.normal(85, 10, 48),
        ...     'rain': np.random.exponential(0.5, 48)
        ... })
        >>> 
        >>> # Generar gráfico
        >>> fig = create_48h_forecast_chart(data)
        >>> fig.show()
    """
    if hourly_data.empty:
        return create_empty_forecast_chart("No hay datos de predicción horaria disponibles")
    
    # Crear subplot con múltiples ejes - Estilo visual mejorado
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=[
            "<b>🌡️ Evolución de Temperatura - Análisis de Riesgo de Repilo</b>",
            "<b>💧 Condiciones de Humedad y Precipitación</b>"
        ],
        vertical_spacing=0.15,
        row_heights=[0.55, 0.45],
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )
    
    
    # === SUBPLOT 1: TEMPERATURA CON ZONAS DE RIESGO ELEGANTES ===
    
    # Zona crítica 15-20°C (riesgo alto) - Diseño premium
    fig.add_trace(
        go.Scatter(
            x=[hourly_data['datetime'].min(), hourly_data['datetime'].max(), 
               hourly_data['datetime'].max(), hourly_data['datetime'].min(), 
               hourly_data['datetime'].min()],
            y=[15, 15, 20, 20, 15],
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.15)",  # Rojo moderno más sutil
            line=dict(color="rgba(239, 68, 68, 0.4)", width=1),  # Borde sutil
            name="🔴 Riesgo Alto",
            hovertemplate="<b>🔴 ZONA DE RIESGO ALTO</b><br>" +
                         "Temperatura: 15-20°C<br>" +
                         "Condiciones óptimas para repilo<br>" +
                         "<extra></extra>",
            showlegend=True,
            legendgroup="risk_zones"
        ),
        row=1, col=1
    )
    
    # Zona moderada 12-15°C - Diseño premium
    fig.add_trace(
        go.Scatter(
            x=[hourly_data['datetime'].min(), hourly_data['datetime'].max(), 
               hourly_data['datetime'].max(), hourly_data['datetime'].min(), 
               hourly_data['datetime'].min()],
            y=[12, 12, 15, 15, 12],
            fill="toself",
            fillcolor="rgba(245, 158, 11, 0.12)",  # Amarillo moderno más sutil
            line=dict(color="rgba(245, 158, 11, 0.3)", width=1),
            name="🟡 Riesgo Moderado",
            hovertemplate="<b>🟡 ZONA DE RIESGO MODERADO</b><br>" +
                         "Temperatura: 12-15°C<br>" +
                         "Condiciones subóptimas<br>" +
                         "<extra></extra>",
            showlegend=True,
            legendgroup="risk_zones"
        ),
        row=1, col=1
    )
    
    # Zona moderada 20-22°C - Diseño premium
    fig.add_trace(
        go.Scatter(
            x=[hourly_data['datetime'].min(), hourly_data['datetime'].max(), 
               hourly_data['datetime'].max(), hourly_data['datetime'].min(), 
               hourly_data['datetime'].min()],
            y=[20, 20, 22, 22, 20],
            fill="toself",
            fillcolor="rgba(245, 158, 11, 0.12)",
            line=dict(color="rgba(245, 158, 11, 0.3)", width=1),
            name="🟡 Riesgo Moderado (Alta)",
            hovertemplate="<b>🟡 ZONA DE RIESGO MODERADO</b><br>" +
                         "Temperatura: 20-22°C<br>" +
                         "Condiciones subóptimas<br>" +
                         "<extra></extra>",
            showlegend=False,  # No mostrar duplicado en leyenda
            legendgroup="risk_zones"
        ),
        row=1, col=1
    )
    
    # Línea de temperatura - Diseño elegante y moderno
    fig.add_trace(
        go.Scatter(
            x=hourly_data['datetime'],
            y=hourly_data['temperature'],
            mode='lines+markers',
            name='🌡️ Temperatura',
            line=dict(
                color='#dc2626',  # Rojo moderno
                width=3,
                shape='spline',  # Línea suave
                smoothing=0.8
            ),
            marker=dict(
                size=5,
                color='#dc2626',
                line=dict(color='white', width=1),
                symbol='circle'
            ),
            hovertemplate="<b>🌡️ Temperatura</b><br>" +
                         "%{x|%a %d/%m %H:%M}<br>" +
                         "<b>%{y:.1f}°C</b><br>" +
                         "<extra></extra>",
            showlegend=True
        ),
        row=1, col=1
    )
    
    # Resaltar períodos críticos con marcadores MÁS DESTACADOS
    critical_temp = hourly_data[(hourly_data['temperature'] >= 15) & (hourly_data['temperature'] <= 20)]
    if not critical_temp.empty:
        fig.add_trace(
            go.Scatter(
                x=critical_temp['datetime'],
                y=critical_temp['temperature'],
                mode='markers',
                name='🔥 Temperatura Crítica',
                marker=dict(
                    color='#dc2626',
                    size=12,  # Más grande
                    symbol='diamond-wide',
                    line=dict(color='white', width=3),  # Borde más grueso
                    opacity=1  # Totalmente opaco
                ),
                hovertemplate="<b>🔥 TEMPERATURA CRÍTICA</b><br>" +
                             "%{x|%a %d/%m %H:%M}<br>" +
                             "<b>%{y:.1f}°C</b><br>" +
                             "🦠 <b>ALTO RIESGO DE REPILO</b><br>" +
                             "<extra></extra>",
                showlegend=True
            ),
            row=1, col=1
        )
    
    # === SUBPLOT 2: HUMEDAD Y PRECIPITACIÓN (DISEÑO ELEGANTE) ===
    
    # Zona de riesgo repilo: Humedad > 95% - Diseño premium
    fig.add_trace(
        go.Scatter(
            x=[hourly_data['datetime'].min(), hourly_data['datetime'].max(), 
               hourly_data['datetime'].max(), hourly_data['datetime'].min(), 
               hourly_data['datetime'].min()],
            y=[95, 95, 105, 105, 95],
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.08)",  # Más sutil
            line=dict(color="rgba(239, 68, 68, 0.3)", width=1),
            name="🔴 Zona Crítica Humedad",
            hovertemplate="<b>🔴 ZONA CRÍTICA</b><br>" +
                         "Humedad > 95%<br>" +
                         "Alto riesgo de repilo<br>" +
                         "<extra></extra>",
            showlegend=True,
            legendgroup="humidity_zones"
        ),
        row=2, col=1
    )
    
    # Precipitación como barras elegantes - EJE SECUNDARIO  
    fig.add_trace(
        go.Bar(
            x=hourly_data['datetime'],
            y=hourly_data['rain'],
            name="☔ Precipitación",
            marker=dict(
                color=hourly_data['rain'],
                colorscale=[
                    [0, 'rgba(59, 130, 246, 0.3)'],
                    [0.5, 'rgba(59, 130, 246, 0.6)'],
                    [1, 'rgba(37, 99, 235, 0.9)']
                ],
                line=dict(color='rgba(59, 130, 246, 0.5)', width=0.5),
                opacity=0.8
            ),
            width=1800000,  # Ancho de barras en milisegundos
            hovertemplate="<b>☔ Precipitación</b><br>" +
                         "%{x|%a %d/%m %H:%M}<br>" +
                         "<b>%{y:.1f} mm</b><br>" +
                         "<extra></extra>",
            showlegend=True
        ),
        row=2, col=1, secondary_y=True
    )
    
    # Humedad como línea suave - EJE PRINCIPAL
    fig.add_trace(
        go.Scatter(
            x=hourly_data['datetime'],
            y=hourly_data['humidity'],
            mode='lines+markers',
            name='💧 Humedad Relativa',
            line=dict(
                color='#0ea5e9',  # Azul moderno
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
                         "%{x|%a %d/%m %H:%M}<br>" +
                         "<b>%{y:.1f}%</b><br>" +
                         "<extra></extra>",
            showlegend=True
        ),
        row=2, col=1
    )
    
    # Resaltar períodos críticos de humedad con marcadores MÁS DESTACADOS
    critical_humidity = hourly_data[hourly_data['humidity'] > 95]
    if not critical_humidity.empty:
        fig.add_trace(
            go.Scatter(
                x=critical_humidity['datetime'],
                y=critical_humidity['humidity'],
                mode='markers',
                name='💧 Humedad Crítica',
                marker=dict(
                    color='#dc2626',
                    size=10,  # Más grande
                    symbol='triangle-up',
                    line=dict(color='white', width=3),  # Borde más grueso
                    opacity=1  # Totalmente opaco
                ),
                hovertemplate="<b>💧 HUMEDAD CRÍTICA</b><br>" +
                             "%{x|%a %d/%m %H:%M}<br>" +
                             "<b>%{y:.1f}%</b><br>" +
                             "🦠 <b>ALTO RIESGO DE REPILO</b><br>" +
                             "<extra></extra>",
                showlegend=True
            ),
            row=2, col=1
        )
    
    # === CONFIGURACIÓN DE EJES (DISEÑO MODERNO) ===
    
    # Subplot 1: Temperatura - Estilo elegante
    fig.update_yaxes(
        title_text="<b>Temperatura (°C)</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=12, color='#6b7280'),
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        zeroline=False,
        row=1, col=1
    )
    
    # Subplot 2: Humedad - Eje principal
    fig.update_yaxes(
        title_text="<b>Humedad (%)</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=12, color='#6b7280'),
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        range=[40, 105],
        zeroline=False,
        row=2, col=1
    )
    
    max_rain = hourly_data['rain'].max() if not hourly_data['rain'].empty else 0

    upper_rain = np.ceil(max_rain) + 5 if max_rain > 0 else 10

    # Subplot 2: Precipitación - Eje secundario
    fig.update_yaxes(
        title_text="<b>Precipitación (mm)</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=12, color='#6b7280'),
        secondary_y=True,
        row=2, col=1,
        rangemode="tozero",
        range=[0, upper_rain],
        showgrid=False
    )
    
    # Ejes X - Diseño consistente
    fig.update_xaxes(
        title_text="",
        tickfont=dict(size=11, color='#6b7280'),
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        zeroline=False,
        row=1, col=1
    )
    
    fig.update_xaxes(
        title_text="<b>Fecha y Hora</b>",
        title_font=dict(size=14, color='#374151', family='Inter, sans-serif'),
        tickfont=dict(size=11, color='#6b7280'),
        tickangle=0,
        gridcolor='rgba(107, 114, 128, 0.1)',
        gridwidth=1,
        showgrid=True,
        zeroline=False,
        row=2, col=1
    )
    
    # === LAYOUT PREMIUM ===
    fig.update_layout(
        template="plotly_white",
        hovermode='x unified',
        height=650,
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
        margin=dict(l=80, r=80, t=100, b=70),
        annotations=[
            # Información científica del repilo
            dict(
                x=0.5, y=1.12,
                xref='paper', yref='paper',
                text="🦠 <b>Condiciones críticas para repilo:</b> Temperatura 15-20°C + Humedad >95%",
                showarrow=False,
                font=dict(size=12, color='#dc2626', family='Inter, sans-serif'),
                bgcolor="rgba(254, 242, 242, 0.95)",
                bordercolor="rgba(239, 68, 68, 0.3)",
                borderwidth=1,
                borderpad=6,
                xanchor='center'
            )
        ]
    )
    
    return fig

def analyze_disease_risk_forecast(forecast_data: pd.DataFrame) -> Dict:
    """
    Analiza el riesgo de repilo en las predicciones
    
    Args:
        forecast_data: DataFrame con predicciones
        
    Returns:
        Dict con análisis de riesgo
    """
    if forecast_data.empty:
        return {'overall_risk': 'sin_datos', 'risk_days': []}
    
    risk_analysis = {
        'overall_risk': 'bajo',
        'risk_days': [],
        'high_risk_periods': [],
        'recommendations': []
    }
    
    for idx, row in forecast_data.iterrows():
        daily_risk = 'bajo'
        risk_factors = []
        
        # Analizar temperatura
        if 15 <= row.get('temp_max', 0) <= 20 or 15 <= row.get('temp_min', 0) <= 20:
            daily_risk = 'alto'
            risk_factors.append('Temperatura en zona crítica (15-20°C)')
        elif 12 <= row.get('temp_max', 0) <= 15 or 20 <= row.get('temp_max', 0) <= 22:
            if daily_risk == 'bajo':
                daily_risk = 'moderado'
            risk_factors.append('Temperatura en zona de alerta')
        
        # Analizar humedad
        if row.get('humidity', 0) > 95:
            if daily_risk != 'alto':
                daily_risk = 'alto'
            risk_factors.append('Humedad crítica >95%')
        elif row.get('humidity', 0) > 90:
            if daily_risk == 'bajo':
                daily_risk = 'moderado'
            risk_factors.append('Humedad alta >90%')
        
        # Analizar precipitación
        if row.get('rain', 0) > 0:
            risk_factors.append(f"Precipitación prevista: {row.get('rain', 0):.1f}mm")
        
        risk_analysis['risk_days'].append({
            'date': row.get('date'),
            'risk_level': daily_risk,
            'factors': risk_factors
        })
        
        # Actualizar riesgo general
        if daily_risk == 'alto' and risk_analysis['overall_risk'] != 'alto':
            risk_analysis['overall_risk'] = 'alto'
        elif daily_risk == 'moderado' and risk_analysis['overall_risk'] == 'bajo':
            risk_analysis['overall_risk'] = 'moderado'
    
    # Generar recomendaciones
    if risk_analysis['overall_risk'] == 'alto':
        risk_analysis['recommendations'].append(
            'Se prevén condiciones de alto riesgo para repilo. Considere tratamientos preventivos.'
        )
    elif risk_analysis['overall_risk'] == 'moderado':
        risk_analysis['recommendations'].append(
            'Condiciones de riesgo moderado. Mantenga vigilancia y prepare tratamientos si es necesario.'
        )
    else:
        risk_analysis['recommendations'].append(
            'Condiciones favorables con bajo riesgo de repilo.'
        )
    
    return risk_analysis

def create_empty_forecast_chart(message: str) -> go.Figure:
    """Crea gráfico vacío con mensaje"""
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
        height=450,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig