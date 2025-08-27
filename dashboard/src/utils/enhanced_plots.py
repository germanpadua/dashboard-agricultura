"""
===============================================================================
                  GRÁFICOS MEJORADOS PARA ANÁLISIS METEOROLÓGICO
===============================================================================

📈 DESCRIPCIÓN:
    Biblioteca especializada para visualización avanzada de datos meteorológicos
    con enfoque específico en identificación y resaltado de zonas de riesgo
    de repilo del olivo.

🌡️ FUNCIONALIDADES PRINCIPALES:
    - Gráficos de temperatura con zonas de riesgo resaltadas
    - Visualización de humedad con umbrales críticos
    - Análisis de precipitación y condiciones de mojado
    - Gráficos combinados multi-variable
    - Detección automática de períodos de riesgo
    - Esquemas de colores semáforo para alertas

🦠 CRITERIOS DE RIESGO DE REPILO:
    - Temperatura óptima: 15-20°C (riesgo alto)
    - Temperatura moderada: 12-15°C y 20-22°C
    - Humedad crítica: >95% (riesgo alto)
    - Humedad alerta: 90-95%
    - Condiciones de mojado: Lluvia + Humedad alta

🎨 CARACTERÍSTICAS VISUALES:
    - Interfaz moderna con Plotly
    - Zonas de riesgo con colores intuitivos
    - Tooltips informativos interactivos
    - Leyendas automáticas y contextuales
    - Responsive design para dashboard

👨‍💻 AUTOR: Sistema de Monitoreo Agrícola
📅 VERSION: 2024
🎯 PROPÓSITO: Visualización Avanzada - Dashboard Agrícola

===============================================================================
"""

# ==============================================================================
# IMPORTS Y DEPENDENCIAS
# ==============================================================================

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ==============================================================================
# GRÁFICOS DE TEMPERATURA CON ZONAS DE RIESGO
# ==============================================================================

def create_temperature_risk_chart(df: pd.DataFrame, risk_zones: List[Dict] = None) -> go.Figure:
    """
    🌡️ Crea gráfico avanzado de temperatura con zonas de riesgo de repilo
    
    Genera visualización interactiva que resalta automáticamente las zonas
    de temperatura óptimas para el desarrollo de repilo del olivo, usando
    bandas de color y marcadores especiales para períodos críticos.
    
    Args:
        df (pd.DataFrame): DataFrame con datos meteorológicos que debe contener:
            - Dates: Timestamps de las mediciones
            - Air_Temp: Temperatura del aire en °C
        risk_zones (List[Dict], optional): Lista de zonas de riesgo identificadas
            previamente por el sistema de análisis. Cada zona debe contener:
            - type: Tipo de riesgo ('temperature_optimal', 'critical_combined')
            - data: DataFrame con datos de la zona
            - description: Descripción textual del riesgo
        
    Returns:
        go.Figure: Figura interactiva de Plotly con:
            - Línea principal de temperatura
            - Bandas de riesgo coloreadas
            - Marcadores especiales para períodos críticos
            - Tooltips informativos
            - Leyenda completa
    
    Note:
        - Zona rojo (15-20°C): Riesgo alto de repilo
        - Zona amarilla (12-15°C y 20-22°C): Riesgo moderado
        - Marcadores diamante rojos: Períodos de riesgo crítico
        - Altura fija de 400px para integración en dashboard
    
    Example:
        >>> df = pd.DataFrame({'Dates': dates, 'Air_Temp': temps})
        >>> fig = create_temperature_risk_chart(df)
        >>> fig.show()
    """
    # Validación de datos de entrada
    if df.empty:
        return _create_empty_chart("No hay datos de temperatura disponibles")
    
    # Crear figura base
    fig = go.Figure()
    
    # Banda de temperatura óptima para repilo (15-20°C) - RIESGO ALTO
    fig.add_hrect(
        y0=15, y1=20,
        fillcolor="rgba(220, 53, 69, 0.2)",  # Rojo translúcido
        line_width=0,
        annotation_text="⚠️ ZONA RIESGO ALTO REPILO (15-20°C)",
        annotation_position="top left",
        layer="below"
    )
    
    # Bandas de temperatura moderada para repilo - RIESGO MODERADO
    
    # Banda inferior (12-15°C)
    fig.add_hrect(
        y0=12, y1=15,
        fillcolor="rgba(255, 193, 7, 0.15)",  # Amarillo translucido
        line_width=0,
        annotation_text="🟡 Riesgo Moderado (12-15°C)",
        annotation_position="bottom left",
        layer="below"
    )
    
    # Banda superior (20-22°C)
    fig.add_hrect(
        y0=20, y1=22,
        fillcolor="rgba(255, 193, 7, 0.15)",  # Amarillo translucido
        line_width=0,
        annotation_text="🟡 Riesgo Moderado (20-22°C)",
        annotation_position="top right",
        layer="below"
    )
    
    # Línea de temperatura
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df['Air_Temp'],
            mode='lines+markers',
            name='Temperatura',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=4),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Fecha: %{x}<br>' +
                         'Temperatura: %{y:.1f}°C<br>' +
                         '<extra></extra>'
        )
    )
    
    # Resaltar períodos de riesgo crítico
    if risk_zones:
        for zone in risk_zones:
            if zone['type'] in ['temperature_optimal', 'critical_combined']:
                zone_data = zone['data']
                fig.add_trace(
                    go.Scatter(
                        x=zone_data['Dates'],
                        y=zone_data['Air_Temp'],
                        mode='markers',
                        name=zone['description'],
                        marker=dict(
                            color='red',
                            size=8,
                            symbol='diamond'
                        ),
                        hovertemplate='<b>⚠️ RIESGO CRÍTICO</b><br>' +
                                     'Fecha: %{x}<br>' +
                                     'Temperatura: %{y:.1f}°C<br>' +
                                     '<extra></extra>'
                    )
                )
    
    fig.update_layout(
        title={
            'text': '🌡️ Evolución de Temperatura con Zonas de Riesgo de Repilo',
            'x': 0.5,
            'font': {'size': 16, 'color': '#2E7D32'}
        },
        xaxis_title="Fecha y Hora",
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

# ==============================================================================
# GRÁFICOS DE HUMEDAD CON ZONAS CRÍTICAS
# ==============================================================================

def create_humidity_risk_chart(df: pd.DataFrame, risk_zones: List[Dict] = None) -> go.Figure:
    """
    💧 Crea gráfico especializado de humedad con zonas críticas de repilo
    
    Visualiza la evolución de la humedad relativa resaltando automáticamente
    los umbrales críticos para el desarrollo de repilo del olivo (>95%)
    y zonas de alerta (90-95%).
    
    Args:
        df (pd.DataFrame): DataFrame con datos meteorológicos que debe contener:
            - Dates: Timestamps de las mediciones
            - Air_Relat_Hum: Humedad relativa en porcentaje (0-100)
        risk_zones (List[Dict], optional): Zonas de riesgo adicionales
            identificadas por el sistema de análisis
    
    Returns:
        go.Figure: Figura interactiva con:
            - Línea principal de humedad relativa
            - Banda roja para riesgo crítico (>95%)
            - Banda amarilla para zona de alerta (90-95%)
            - Marcadores especiales para valores críticos
            - Tooltips con información de riesgo
    
    Note:
        - Zona roja (>95%): Riesgo alto de repilo
        - Zona amarilla (90-95%): Zona de alerta
        - Los puntos >95% se marcan con triángulos rojos
        - Escala fija 0-100% para contexto visual
    
    Example:
        >>> df = pd.DataFrame({'Dates': dates, 'Air_Relat_Hum': humidity})
        >>> fig = create_humidity_risk_chart(df)
        >>> fig.show()
    """
    # Validación de datos de entrada
    if df.empty:
        return _create_empty_chart("No hay datos de humedad disponibles")
    
    # Crear figura base para humedad
    fig = go.Figure()
    
    # Banda de riesgo crítico por humedad alta (>95%) - RIESGO ALTO
    fig.add_hrect(
        y0=95, y1=100,
        fillcolor="rgba(220, 53, 69, 0.3)",  # Rojo intenso
        line_width=0,
        annotation_text="🔴 ZONA RIESGO CRÍTICO (>95%)",
        annotation_position="top left",
        layer="below"
    )
    
    # Banda de alerta por humedad moderadamente alta (90-95%)
    fig.add_hrect(
        y0=90, y1=95,
        fillcolor="rgba(255, 193, 7, 0.2)",  # Amarillo translucido
        line_width=0,
        annotation_text="🟡 ZONA DE ALERTA (90-95%)",
        annotation_position="bottom left",
        layer="below"
    )
    
    # Línea de humedad
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df['Air_Relat_Hum'],
            mode='lines+markers',
            name='Humedad Relativa',
            line=dict(color='#1E88E5', width=2),
            marker=dict(size=4),
            fill='tonexty' if df['Air_Relat_Hum'].max() > 95 else None,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Fecha: %{x}<br>' +
                         'Humedad: %{y:.1f}%<br>' +
                         '<extra></extra>'
        )
    )
    
    # Resaltar períodos críticos de humedad
    high_humidity = df[df['Air_Relat_Hum'] > 95]
    if not high_humidity.empty:
        fig.add_trace(
            go.Scatter(
                x=high_humidity['Dates'],
                y=high_humidity['Air_Relat_Hum'],
                mode='markers',
                name='Humedad Crítica >95%',
                marker=dict(
                    color='red',
                    size=8,
                    symbol='triangle-up'
                ),
                hovertemplate='<b>🚨 HUMEDAD CRÍTICA</b><br>' +
                             'Fecha: %{x}<br>' +
                             'Humedad: %{y:.1f}%<br>' +
                             'RIESGO ALTO DE REPILO<br>' +
                             '<extra></extra>'
            )
        )
    
    fig.update_layout(
        title={
            'text': '💧 Evolución de Humedad Relativa y Riesgo de Repilo',
            'x': 0.5,
            'font': {'size': 16, 'color': '#2E7D32'}
        },
        xaxis_title="Fecha y Hora",
        yaxis_title="Humedad Relativa (%)",
        template="plotly_white",
        hovermode='x unified',
        height=400,
        showlegend=True,
        yaxis=dict(range=[0, 100])
    )
    
    return fig

# ==============================================================================
# GRÁFICOS DE PRECIPITACIÓN Y CONDICIONES DE MOJADO
# ==============================================================================

def create_rain_wet_conditions_chart(df: pd.DataFrame, risk_zones: List[Dict] = None) -> go.Figure:
    """
    🌧️ Crea gráfico avanzado de precipitación con análisis de condiciones de mojado
    
    Combina datos de precipitación con condiciones de humedad alta para
    identificar períodos de mojado continuo que favorecen el desarrollo
    del repilo del olivo.
    
    Args:
        df (pd.DataFrame): DataFrame con datos meteorológicos:
            - Dates: Timestamps de las mediciones
            - Rain: Precipitación en mm
            - Air_Relat_Hum: Humedad relativa en %
        risk_zones (List[Dict], optional): Zonas de riesgo identificadas
    
    Returns:
        go.Figure: Gráfico con doble eje Y que muestra:
            - Barras de precipitación (eje izquierdo)
            - Línea de condiciones de mojado (eje derecho)
            - Bandas verticales para períodos de mojado prolongado
            - Anotaciones con duración de períodos críticos
    
    Note:
        - Condiciones de mojado: Lluvia > 0 O Humedad ≥ 95%
        - Períodos significativos: ≥ 8 horas continuas
        - Bandas rojas marcan períodos de riesgo prolongado
        - Integra precipitación y humedad en una sola vista
    
    Example:
        >>> df = pd.DataFrame({
        ...     'Dates': dates, 'Rain': rain, 'Air_Relat_Hum': humidity
        ... })
        >>> fig = create_rain_wet_conditions_chart(df)
        >>> fig.show()
    """
    # Validación de datos de entrada
    if df.empty:
        return _create_empty_chart("No hay datos de precipitación disponibles")
    
    # Crear subplot con doble eje Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=['🌧️ Precipitación y Condiciones de Mojado']
    )
    
    # Precipitación como barras
    fig.add_trace(
        go.Bar(
            x=df['Dates'],
            y=df['Rain'],
            name='Precipitación',
            marker_color='lightblue',
            opacity=0.7,
            hovertemplate='<b>Precipitación</b><br>' +
                         'Fecha: %{x}<br>' +
                         'Lluvia: %{y:.1f}mm<br>' +
                         '<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Condiciones de mojado (combinación humedad + lluvia)
    df_wet = df.copy()
    df_wet['wet_conditions'] = ((df_wet['Air_Relat_Hum'] >= 95) | (df_wet['Rain'] > 0)).astype(int) * 100
    
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df_wet['wet_conditions'],
            mode='lines',
            name='Condiciones de Mojado',
            line=dict(color='orange', width=3),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.3)',
            hovertemplate='<b>Condiciones Mojado</b><br>' +
                         'Fecha: %{x}<br>' +
                         'Estado: %{text}<br>' +
                         '<extra></extra>',
            text=['Mojado' if x > 0 else 'Seco' for x in df_wet['wet_conditions']]
        ),
        secondary_y=True
    )
    
    # Identificar períodos continuos de mojado
    wet_periods = _identify_wet_periods(df)
    for period in wet_periods:
        if period['duration_hours'] >= 8:  # Períodos significativos
            fig.add_vrect(
                x0=period['start'],
                x1=period['end'],
                fillcolor="rgba(255, 0, 0, 0.1)",
                layer="below",
                line_width=0,
                annotation_text=f"Mojado {period['duration_hours']}h" if period['duration_hours'] < 24 else f"Mojado {period['duration_hours']//24}d",
                annotation_position="top"
            )
    
    # Configurar ejes
    fig.update_yaxes(title_text="Precipitación (mm)", secondary_y=False)
    fig.update_yaxes(
        title_text="Condiciones de Mojado (%)",
        secondary_y=True,
        range=[0, 110]
    )
    
    fig.update_layout(
        xaxis_title="Fecha y Hora",
        template="plotly_white",
        hovermode='x unified',
        height=400,
        showlegend=True
    )
    
    return fig

# ==============================================================================
# GRÁFICOS COMBINADOS Y ANÁLISIS INTEGRAL
# ==============================================================================

def create_combined_risk_overview(df: pd.DataFrame, risk_analysis: Dict) -> go.Figure:
    """
    🔍 Crea vista general combinada de todas las variables meteorológicas
    
    Genera un gráfico multi-panel que muestra temperatura, humedad y
    precipitación en subplots sincronizados, resaltando períodos de
    riesgo crítico identificados por el sistema de análisis.
    
    Args:
        df (pd.DataFrame): DataFrame completo con datos meteorológicos:
            - Dates: Timestamps
            - Air_Temp: Temperatura en °C  
            - Air_Relat_Hum: Humedad relativa en %
            - Rain: Precipitación en mm
        risk_analysis (Dict): Resultados del análisis de riesgo:
            - overall_risk: Nivel general ('alto', 'moderado', 'bajo')
            - risk_zones: Lista de períodos críticos identificados
    
    Returns:
        go.Figure: Panel combinado con 3 subplots sincronizados:
            - Panel superior: Temperatura con bandas de riesgo
            - Panel medio: Humedad con umbrales críticos
            - Panel inferior: Precipitación como barras
            - Líneas verticales rojas en períodos críticos
    
    Note:
        - Los ejes X están sincronizados para fácil comparación
        - El título muestra el nivel de riesgo general
        - Color del título según nivel de riesgo
        - Altura total de 600px para vista completa
    
    Example:
        >>> risk_analysis = {'overall_risk': 'alto', 'risk_zones': zones}
        >>> fig = create_combined_risk_overview(df, risk_analysis)
        >>> fig.show()
    """
    # Validación de datos de entrada
    if df.empty:
        return _create_empty_chart("No hay datos para análisis combinado")
    
    # Crear subplot con múltiples ejes Y
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=['Temperatura (°C)', 'Humedad Relativa (%)', 'Precipitación (mm)'],
        vertical_spacing=0.05
    )
    
    # Temperatura
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df['Air_Temp'],
            mode='lines',
            name='Temperatura',
            line=dict(color='red', width=2),
        ),
        row=1, col=1
    )
    
    # Zona de riesgo temperatura
    fig.add_hrect(
        y0=15, y1=20,
        fillcolor="rgba(220, 53, 69, 0.2)",
        line_width=0,
        row=1, col=1
    )
    
    # Humedad
    fig.add_trace(
        go.Scatter(
            x=df['Dates'],
            y=df['Air_Relat_Hum'],
            mode='lines',
            name='Humedad',
            line=dict(color='blue', width=2),
        ),
        row=2, col=1
    )
    
    # Zona de riesgo humedad
    fig.add_hrect(
        y0=95, y1=100,
        fillcolor="rgba(220, 53, 69, 0.2)",
        line_width=0,
        row=2, col=1
    )
    
    # Precipitación
    fig.add_trace(
        go.Bar(
            x=df['Dates'],
            y=df['Rain'],
            name='Precipitación',
            marker_color='lightblue'
        ),
        row=3, col=1
    )
    
    # Destacar períodos de riesgo crítico
    if risk_analysis.get('risk_zones'):
        for zone in risk_analysis['risk_zones']:
            if zone['type'] == 'critical_combined':
                zone_data = zone['data']
                for _, row in zone_data.iterrows():
                    fig.add_vline(
                        x=row['Dates'],
                        line_color="red",
                        line_width=2,
                        opacity=0.7
                    )
    
    fig.update_layout(
        title={
            'text': f"🔍 Análisis Combinado - Riesgo: {risk_analysis.get('overall_risk', 'N/A').upper()}",
            'x': 0.5,
            'font': {'size': 18, 'color': _get_risk_color(risk_analysis.get('overall_risk', 'bajo'))}
        },
        height=600,
        template="plotly_white",
        showlegend=True
    )
    
    return fig

# ==============================================================================
# FUNCIONES AUXILIARES Y UTILIDADES
# ==============================================================================

def _identify_wet_periods(df: pd.DataFrame) -> List[Dict]:
    """
    💧 Identifica períodos continuos de mojado en los datos meteorológicos
    
    Analiza las condiciones de humedad y precipitación para detectar
    períodos continuos donde las plantas permanecen mojadas, condición
    favorable para el desarrollo de enfermedades fúngicas como el repilo.
    
    Args:
        df (pd.DataFrame): DataFrame con datos meteorológicos:
            - Dates: Timestamps de las mediciones
            - Air_Relat_Hum: Humedad relativa en %
            - Rain: Precipitación en mm
    
    Returns:
        List[Dict]: Lista de períodos de mojado, cada uno con:
            - start: Timestamp de inicio del período
            - end: Timestamp de fin del período  
            - duration_hours: Duración en horas (int)
    
    Note:
        - Condición de mojado: Humedad ≥ 95% O Precipitación > 0
        - Detecta períodos continuos sin interrupciones
        - Maneja correctamente períodos que continúan hasta el final
        - Retorna duración en horas enteras para facilidad de uso
    
    Example:
        >>> periods = _identify_wet_periods(df)
        >>> for period in periods:
        ...     print(f"Mojado {period['duration_hours']}h")
    """
    # Validación de datos
    if df.empty:
        return []
    
    # Preparar datos para análisis
    df_wet = df.copy()
    # Definir condiciones de mojado: Humedad alta O Precipitación
    df_wet['is_wet'] = (df_wet['Air_Relat_Hum'] >= 95) | (df_wet['Rain'] > 0)
    
    # Detectar períodos continuos de mojado
    periods = []
    start_period = None
    
    for idx, row in df_wet.iterrows():
        # Inicio de período de mojado
        if row['is_wet'] and start_period is None:
            start_period = row['Dates']
        # Fin de período de mojado    
        elif not row['is_wet'] and start_period is not None:
            end_period = row['Dates']
            duration = (end_period - start_period).total_seconds() / 3600
            periods.append({
                'start': start_period,
                'end': end_period,
                'duration_hours': int(duration)
            })
            start_period = None
    
    # Manejar período que continúa hasta el final de los datos
    if start_period is not None:
        end_period = df_wet['Dates'].iloc[-1]
        duration = (end_period - start_period).total_seconds() / 3600
        periods.append({
            'start': start_period,
            'end': end_period,
            'duration_hours': int(duration)
        })
    
    return periods

def _create_empty_chart(message: str) -> go.Figure:
    """
    📋 Crea gráfico placeholder cuando no hay datos disponibles
    
    Genera una figura vacía con un mensaje centrado para casos donde
    no hay datos suficientes para crear la visualización solicitada.
    
    Args:
        message (str): Mensaje a mostrar en el gráfico vacío
    
    Returns:
        go.Figure: Figura con mensaje centrado y sin ejes visibles
    
    Note:
        - Usa template 'plotly_white' para consistencia
        - Altura estándar de 400px
        - Texto en gris para indicar estado inactivo
        - Sin ejes ni controles para evitar confusión
    
    Example:
        >>> fig = _create_empty_chart("No hay datos disponibles")
        >>> fig.show()
    """
    # Crear figura vacía
    fig = go.Figure()
    
    # Añadir mensaje centrado
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,  # Centro del gráfico
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

def _get_risk_color(risk_level: str) -> str:
    """
    🎨 Obtiene color estándar según nivel de riesgo de repilo
    
    Mapea los niveles de riesgo del sistema a colores consistentes
    usando el esquema semáforo estándar para interfaces de usuario.
    
    Args:
        risk_level (str): Nivel de riesgo ('alto', 'moderado', 'bajo', etc.)
    
    Returns:
        str: Código de color hexadecimal correspondiente
    
    Note:
        - Usa esquema semáforo: rojo (alto), amarillo (moderado), verde (bajo)
        - Color gris por defecto para casos no reconocidos
        - Case-insensitive para flexibilidad
    
    Example:
        >>> color = _get_risk_color('alto')
        >>> print(color)  # '#DC3545'
    """
    # Mapeo estándar de niveles de riesgo a colores
    colors = {
        'alto': '#DC3545',        # Rojo Bootstrap (danger)
        'moderado': '#FFC107',    # Amarillo Bootstrap (warning) 
        'bajo': '#28A745',        # Verde Bootstrap (success)
        'desconocido': '#6C757D', # Gris Bootstrap (secondary)
        'error': '#DC3545'        # Rojo para errores
    }
    return colors.get(risk_level.lower(), '#6C757D')  # Fallback a gris