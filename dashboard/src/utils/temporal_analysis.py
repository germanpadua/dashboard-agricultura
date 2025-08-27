"""
Utilidades de análisis temporal avanzado para datos satelitales.

Módulo especializado en análisis de series temporales, detección de tendencias
y patrones estacionales para índices de vegetación.

Funcionalidades:
- Análisis de tendencias con regresión lineal
- Detección de anomalías usando z-score
- Suavizado de series temporales
- Análisis estacional

Autor: Sistema de Monitoreo Agrícola
Fecha: 2024
"""

# Librerías estándar
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from scipy.signal import savgol_filter

# Suprimir warnings de scipy
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

def create_temporal_trend_analysis(
    temporal_data: List[Dict], index_name: str = "NDVI"
) -> Dict:
    """
    Realiza análisis temporal completo de tendencias.
    
    Args:
        temporal_data: Lista de diccionarios con datos temporales
        index_name: Nombre del índice a analizar (por defecto "NDVI")
        
    Returns:
        Diccionario con resultados del análisis temporal completo
    """
    if not temporal_data or len(temporal_data) < 3:
        return {"error": "Insufficient temporal data for analysis"}
    
    # Preparar datos para análisis
    dates = []
    values = []
    std_values = []
    
    # Deserializar datos temporales
    import base64
    import pickle
    
    for data_point in temporal_data:
        if 'date' in data_point and 'array' in data_point:
            try:
                dates.append(pd.to_datetime(data_point['date']))
                array = pickle.loads(base64.b64decode(data_point['array']))
                valid_array = array[np.isfinite(array)]
                
                if len(valid_array) > 0:
                    values.append(np.nanmean(valid_array))
                    std_values.append(np.nanstd(valid_array))
                else:
                    values.append(np.nan)
                    std_values.append(np.nan)
                    
            except Exception as e:
                logger.warning(f"Error procesando punto temporal: {e}")
                continue
    
    if len(values) < 3:
        return {"error": "Insufficient valid data points for analysis"}
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'std': std_values
    }).dropna()
    
    if len(df) < 3:
        return {"error": "Insufficient valid data after cleaning"}
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calcular tendencia usando regresión lineal
    x_numeric = np.arange(len(df))
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        x_numeric, df['value']
    )
    
    # Clasificación de tendencia basada en significancia estadística
    if p_value < 0.05:  # Estadísticamente significativo
        if slope > 0.001:
            trend_status = "Tendencia positiva significativa"
            trend_color = "#27AE60"
            trend_icon = "fas fa-arrow-up"
        elif slope < -0.001:
            trend_status = "Tendencia negativa significativa"
            trend_color = "#E74C3C"
            trend_icon = "fas fa-arrow-down"
        else:
            trend_status = "Estable"
            trend_color = "#3498DB"
            trend_icon = "fas fa-minus"
    else:
        trend_status = "Sin tendencia clara"
        trend_color = "#95A5A6"
        trend_icon = "fas fa-question"
    
    # Análisis estacional (si los datos abarcan múltiples meses)
    seasonal_analysis = None
    if len(df) > 12 and (df['date'].max() - df['date'].min()).days > 180:
        df['month'] = df['date'].dt.month
        monthly_stats = df.groupby('month')['value'].agg(
            ['mean', 'std', 'count']
        ).reset_index()
        seasonal_analysis = monthly_stats.to_dict('records')
    
    # Detección de anomalías usando z-score
    z_scores = np.abs(stats.zscore(df['value']))
    # Puntos con más de 2 desviaciones estándar
    anomalies = df[z_scores > 2].copy()
    
    # Suavizado usando filtro Savitzky-Golay
    if len(df) >= 5:
        window_length = min(
            len(df) if len(df) % 2 == 1 else len(df) - 1, 11
        )
        window_length = max(window_length, 5)  # Tamaño mínimo de ventana
        try:
            smoothed_values = savgol_filter(df['value'], window_length, 3)
        except Exception:
            # Fallback a media móvil si falla Savitzky-Golay
            smoothed_values = df['value'].rolling(
                window=3, center=True
            ).mean().values
    else:
        smoothed_values = df['value'].values
    
    # Detección de puntos de cambio (método simple)
    changes = []
    if len(df) > 6:
        for i in range(3, len(df) - 3):
            before = df['value'].iloc[:i].mean()
            after = df['value'].iloc[i:].mean()
            # Detectar cambios significativos
            if abs(before - after) > df['value'].std():
                changes.append({
                    'date': df['date'].iloc[i],
                    'value': df['value'].iloc[i],
                    'change': after - before
                })
    
    return {
        'dataframe': df,
        'trend': {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'status': trend_status,
            'color': trend_color,
            'icon': trend_icon
        },
        'seasonal': seasonal_analysis,
        'anomalies': anomalies,
        'smoothed_values': smoothed_values,
        'change_points': changes,
        'statistics': {
            'mean': float(df['value'].mean()),
            'std': float(df['value'].std()),
            'min': float(df['value'].min()),
            'max': float(df['value'].max()),
            'cv': float(df['value'].std() / df['value'].mean()) if df['value'].mean() != 0 else 0
        }
    }

def create_advanced_temporal_chart(
    analysis_results: Dict, index_name: str = "NDVI"
) -> go.Figure:
    """
    Crea visualización temporal avanzada con múltiples componentes.
    
    Args:
        analysis_results: Resultados del análisis temporal
        index_name: Nombre del índice a visualizar
        
    Returns:
        Figura de Plotly con análisis temporal completo
    """
    df = analysis_results['dataframe']
    trend = analysis_results['trend']
    anomalies = analysis_results['anomalies']
    smoothed = analysis_results['smoothed_values']
    
    # Crear subplots con ejes secundarios
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            f'📈 Serie Temporal {index_name}',
            '📊 Distribución Mensual',
            '🎯 Análisis de Anomalías',
            '📋 Estadísticas Clave'
        ],
        specs=[
            [{"secondary_y": True}, {"secondary_y": False}],
            [{"secondary_y": False}, {"type": "table"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Serie temporal principal con bandas de confianza
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='markers+lines',
            name=f'{index_name} Observado',
            line=dict(color='#2ECC71', width=2),
            marker=dict(size=6),
            error_y=dict(
                type='data',
                array=df['std'],
                visible=True,
                color='rgba(46, 204, 113, 0.3)'
            )
        ),
        row=1, col=1
    )
    
    # Línea de tendencia suavizada
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=smoothed,
            mode='lines',
            name='Tendencia Suavizada',
            line=dict(color='#E74C3C', width=3, dash='dash')
        ),
        row=1, col=1
    )
    
    # Línea de tendencia lineal
    x_numeric = np.arange(len(df))
    trend_line = trend['slope'] * x_numeric + trend['intercept']
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=trend_line,
            mode='lines',
            name=f'Tendencia Lineal (R² = {trend["r_squared"]:.3f})',
            line=dict(color=trend['color'], width=2, dash='dot')
        ),
        row=1, col=1
    )
    
    # Anomalies
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies['date'],
                y=anomalies['value'],
                mode='markers',
                name='Anomalías',
                marker=dict(
                    size=12,
                    color='#F39C12',
                    symbol='diamond',
                    line=dict(color='#E67E22', width=2)
                )
            ),
            row=1, col=1
        )
    
    # Monthly distribution (if seasonal data available)
    if analysis_results['seasonal']:
        seasonal_df = pd.DataFrame(analysis_results['seasonal'])
        fig.add_trace(
            go.Bar(
                x=seasonal_df['month'],
                y=seasonal_df['mean'],
                name='Promedio Mensual',
                marker=dict(color='#3498DB'),
                error_y=dict(type='data', array=seasonal_df['std'])
            ),
            row=1, col=2
        )
    
    # Anomaly analysis histogram
    fig.add_trace(
        go.Histogram(
            x=df['value'],
            nbinsx=20,
            name='Distribución',
            marker=dict(color='#9B59B6', opacity=0.7)
        ),
        row=2, col=1
    )
    
    # Add normal curve overlay
    x_range = np.linspace(df['value'].min(), df['value'].max(), 100)
    normal_curve = stats.norm.pdf(x_range, df['value'].mean(), df['value'].std())
    normal_curve = normal_curve * len(df) * (df['value'].max() - df['value'].min()) / 20  # Scale to histogram
    
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=normal_curve,
            mode='lines',
            name='Distribución Normal',
            line=dict(color='#E74C3C', width=2)
        ),
        row=2, col=1
    )
    
    # Statistics table
    stats_data = analysis_results['statistics']
    fig.add_trace(
        go.Table(
            header=dict(
                values=['Estadística', 'Valor'],
                fill_color='#ECF0F1',
                font=dict(color='#2C3E50', size=12)
            ),
            cells=dict(
                values=[
                    ['Media', 'Desv. Est.', 'Mínimo', 'Máximo', 'Coef. Variación'],
                    [f"{stats_data['mean']:.4f}",
                     f"{stats_data['std']:.4f}",
                     f"{stats_data['min']:.4f}",
                     f"{stats_data['max']:.4f}",
                     f"{stats_data['cv']:.3f}"]
                ],
                fill_color='#FFFFFF',
                font=dict(size=11)
            )
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title=dict(
            text=f"📊 Análisis Temporal Avanzado - {index_name}",
            x=0.5,
            font=dict(size=18, color="#2c3e50")
        ),
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Fecha", row=1, col=1)
    fig.update_yaxes(title_text=f"Valor {index_name}", row=1, col=1)
    fig.update_xaxes(title_text="Mes", row=1, col=2)
    fig.update_yaxes(title_text=f"Promedio {index_name}", row=1, col=2)
    fig.update_xaxes(title_text=f"Valor {index_name}", row=2, col=1)
    fig.update_yaxes(title_text="Frecuencia", row=2, col=1)
    
    return fig

def create_trend_summary_card(
    analysis_results: Dict, index_name: str = "NDVI"
) -> Dict:
    """
    Crea tarjeta resumen con hallazgos clave del análisis temporal.
    
    Args:
        analysis_results: Resultados del análisis temporal
        index_name: Nombre del índice analizado
        
    Returns:
        Diccionario con resumen de tendencias y recomendaciones
    """
    trend = analysis_results['trend']
    stats = analysis_results['statistics']
    
    # Calcular significancia de la tendencia
    annual_change = trend['slope'] * 365  # Asumiendo datos diarios
    relative_change = (
        (annual_change / stats['mean']) * 100 if stats['mean'] != 0 else 0
    )
    
    # Generar recomendaciones basadas en tendencias
    recommendations = []
    if trend['p_value'] < 0.05:
        if trend['slope'] > 0.001:
            recommendations.append(
                "📈 Tendencia positiva: Mantener prácticas actuales"
            )
            recommendations.append(
                "🌱 Considerar optimización de recursos"
            )
        elif trend['slope'] < -0.001:
            recommendations.append(
                "📉 Tendencia negativa: Requiere atención"
            )
            recommendations.append(
                "🔍 Investigar causas del deterioro"
            )
            recommendations.append(
                "💧 Evaluar riego y nutrición"
            )
    else:
        recommendations.append("📊 Comportamiento estable")
        recommendations.append("🔄 Monitoreo continuo recomendado")
    
    # Evaluación de variabilidad
    if stats['cv'] < 0.1:
        variability_status = "Baja variabilidad"
        variability_color = "#27AE60"
    elif stats['cv'] < 0.2:
        variability_status = "Variabilidad moderada"
        variability_color = "#F39C12"
    else:
        variability_status = "Alta variabilidad"
        variability_color = "#E74C3C"
    
    return {
        'trend_status': trend['status'],
        'trend_color': trend['color'],
        'trend_icon': trend['icon'],
        'annual_change': annual_change,
        'relative_change': relative_change,
        'variability_status': variability_status,
        'variability_color': variability_color,
        'recommendations': recommendations,
        'r_squared': trend['r_squared'],
        'p_value': trend['p_value']
    }

def detect_seasonal_patterns(
    temporal_data: List[Dict], index_name: str = "NDVI"
) -> Dict:
    """
    Detecta patrones estacionales en los datos.
    
    Args:
        temporal_data: Lista de diccionarios con datos temporales
        index_name: Nombre del índice a analizar
        
    Returns:
        Diccionario con análisis estacional completo
    """
    if not temporal_data or len(temporal_data) < 12:
        return {"error": "Insufficient data for seasonal analysis"}
    
    # Preparar datos para análisis estacional
    dates = []
    values = []
    
    # Deserializar datos temporales
    import base64
    import pickle
    
    for data_point in temporal_data:
        if 'date' in data_point and 'array' in data_point:
            try:
                dates.append(pd.to_datetime(data_point['date']))
                array = pickle.loads(base64.b64decode(data_point['array']))
                valid_array = array[np.isfinite(array)]
                
                if len(valid_array) > 0:
                    values.append(np.nanmean(valid_array))
                else:
                    values.append(np.nan)
                    
            except Exception:
                continue
    
    df = pd.DataFrame({'date': dates, 'value': values}).dropna()
    
    if len(df) < 12:
        return {"error": "Insufficient data points for seasonal analysis"}
    
    # Añadir componentes temporales
    df['month'] = df['date'].dt.month
    df['season'] = df['date'].dt.month.map({
        12: 'Invierno', 1: 'Invierno', 2: 'Invierno',
        3: 'Primavera', 4: 'Primavera', 5: 'Primavera',
        6: 'Verano', 7: 'Verano', 8: 'Verano',
        9: 'Otoño', 10: 'Otoño', 11: 'Otoño'
    })
    
    # Análisis mensual
    monthly_stats = df.groupby('month')['value'].agg(
        ['mean', 'std', 'count']
    ).reset_index()
    
    # Análisis estacional
    seasonal_stats = df.groupby('season')['value'].agg(
        ['mean', 'std', 'count']
    ).reset_index()
    
    # Identificar estaciones pico
    max_season = seasonal_stats.loc[
        seasonal_stats['mean'].idxmax(), 'season'
    ]
    min_season = seasonal_stats.loc[
        seasonal_stats['mean'].idxmin(), 'season'
    ]
    
    return {
        'monthly_stats': monthly_stats.to_dict('records'),
        'seasonal_stats': seasonal_stats.to_dict('records'),
        'peak_season': max_season,
        'low_season': min_season,
        'seasonal_amplitude': float(
            seasonal_stats['mean'].max() - seasonal_stats['mean'].min()
        )
    }

def create_seasonal_analysis_chart(
    seasonal_results: Dict, index_name: str = "NDVI"
) -> go.Figure:
    """
    Crea visualización de análisis estacional.
    
    Args:
        seasonal_results: Resultados del análisis estacional
        index_name: Nombre del índice a visualizar
        
    Returns:
        Figura de Plotly con análisis estacional
    """
    if 'error' in seasonal_results:
        fig = go.Figure()
        fig.add_annotation(
            text=seasonal_results['error'],
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#E74C3C")
        )
        return fig
    
    monthly_df = pd.DataFrame(seasonal_results['monthly_stats'])
    seasonal_df = pd.DataFrame(seasonal_results['seasonal_stats'])
    
    # Crear subplots para análisis estacional
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            '📅 Variación Mensual',
            '🌱 Análisis Estacional'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Gráfico de variación mensual
    fig.add_trace(
        go.Scatter(
            x=monthly_df['month'],
            y=monthly_df['mean'],
            mode='lines+markers',
            name='Promedio Mensual',
            line=dict(color='#2ECC71', width=3),
            marker=dict(size=8),
            error_y=dict(
                type='data',
                array=monthly_df['std'],
                visible=True
            )
        ),
        row=1, col=1
    )
    
    # Barras estacionales con colores temáticos
    season_colors = {
        'Primavera': '#2ECC71',
        'Verano': '#F39C12',
        'Otoño': '#E67E22',
        'Invierno': '#3498DB'
    }
    
    fig.add_trace(
        go.Bar(
            x=seasonal_df['season'],
            y=seasonal_df['mean'],
            name='Promedio Estacional',
            marker=dict(
                color=[
                    season_colors.get(season, '#95A5A6')
                    for season in seasonal_df['season']
                ]
            ),
            error_y=dict(
                type='data',
                array=seasonal_df['std'],
                visible=True
            )
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        title=dict(
            text=f"🌿 Análisis Estacional - {index_name}",
            x=0.5,
            font=dict(size=16, color="#2c3e50")
        ),
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(title_text="Mes", row=1, col=1)
    fig.update_yaxes(title_text=f"Valor {index_name}", row=1, col=1)
    fig.update_xaxes(title_text="Estación", row=1, col=2)
    fig.update_yaxes(title_text=f"Valor {index_name}", row=1, col=2)
    
    return fig