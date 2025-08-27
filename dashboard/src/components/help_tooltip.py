"""
Componente de tooltips de ayuda para el dashboard
Proporciona información contextual sobre datos y gráficos
"""

import dash_bootstrap_components as dbc
from dash import html


def create_help_tooltip(tooltip_id: str, help_text: str, icon_color: str = "info") -> dbc.Tooltip:
    """
    Crea un tooltip de ayuda con icono
    
    Args:
        tooltip_id: ID único para el tooltip
        help_text: Texto explicativo a mostrar
        icon_color: Color del icono (info, success, warning, danger)
    
    Returns:
        Componente Tooltip de Dash Bootstrap
    """
    return dbc.Tooltip(
        help_text,
        target=tooltip_id,
        placement="top",
        style={
            'backgroundColor': '#f8f9fa',
            'color': '#495057',
            'border': '1px solid #dee2e6',
            'fontSize': '14px',
            'maxWidth': '300px',
            'textAlign': 'left'
        }
    )


def help_icon(icon_id: str, color: str = "info", size: str = "sm") -> html.I:
    """
    Crea un icono de ayuda (ℹ️)
    
    Args:
        icon_id: ID único para el icono
        color: Color del icono Bootstrap
        size: Tamaño del icono
    
    Returns:
        Componente HTML del icono
    """
    return html.I(
        className=f"fas fa-info-circle text-{color} ms-2",
        id=icon_id,
        style={
            'cursor': 'pointer',
            'fontSize': '16px' if size == 'sm' else '20px'
        }
    )


def help_section(title: str, help_text: str, tooltip_id: str = None) -> html.Div:
    """
    Crea una sección completa con título e icono de ayuda
    
    Args:
        title: Título de la sección
        help_text: Texto explicativo
        tooltip_id: ID para el tooltip (se genera automáticamente si no se proporciona)
    
    Returns:
        Div con título e icono de ayuda
    """
    if not tooltip_id:
        tooltip_id = f"help-{title.lower().replace(' ', '-')}"
    
    return html.Div([
        html.H5([
            title,
            help_icon(tooltip_id)
        ], className="mb-3"),
        create_help_tooltip(tooltip_id, help_text)
    ])


# Diccionario de textos de ayuda específicos para agricultura/Repilo
HELP_TEXTS = {
    'temperatura': """
    📊 Datos de Temperatura
    • Fuente: Estación meteorológica AEMET
    • Actualización: Cada 6 horas
    • Importancia: Las temperaturas entre 15-25°C y alta humedad favorecen el desarrollo del Repilo
    • Alerta: Temperaturas prolongadas >30°C pueden estresar los olivos
    """,
    
    'humedad': """
    💧 Humedad Relativa
    • Fuente: Sensores meteorológicos locales
    • Rango óptimo: 60-80% para crecimiento del olivo
    • Riesgo Repilo: >85% durante >48h aumenta significativamente el riesgo de infección
    • Prevención: Monitorizar especialmente en primavera y otoño
    """,
    
    'precipitacion': """
    🌧️ Precipitación Acumulada
    • Fuente: Pluviómetro automático AEMET
    • Medida: mm acumulados por período
    • Riesgo Repilo: >20mm en 48h con temperaturas 15-25°C = Alto riesgo
    • Gestión: Aplicar tratamientos preventivos tras lluvias intensas
    """,
    
    'ndvi': """
    🛰️ Índice de Vegetación (NDVI)
    • Fuente: Imágenes satelitales Sentinel-2 (ESA)
    • Resolución: 10m por píxel
    • Rango: -1 a 1 (valores >0.3 indican vegetación saludable)
    • Detección: Descensos bruscos pueden indicar estrés o enfermedad
    • Frecuencia: Actualización cada 5 días (condiciones atmosféricas permitan)
    """,
    
    'repilo_deteccion': """
    🔍 Detección de Repilo
    • Método: Análisis espectral + Machine Learning
    • Precisión: >85% en condiciones óptimas
    • Indicadores: Manchas oscuras en hojas, defoliación prematura
    • Integración: Combina datos satelitales + registros de campo (Bot Telegram)
    • Validación: Confirmación manual recomendada para tratamientos
    """,
    
    'condiciones_favorables': """
    ⚠️ Condiciones Favorables para Repilo
    • Temperatura: 15-25°C (óptimo 20°C)
    • Humedad: >85% durante >48 horas
    • Precipitación: Hojas mojadas >10 horas
    • Época: Especialmente crítico en primavera (marzo-mayo) y otoño (septiembre-noviembre)
    • Prevención: Tratamientos cúpricos preventivos en períodos de riesgo
    """,
    
    'alertas_sistema': """
    🚨 Sistema de Alertas Inteligente
    • Análisis continuo de condiciones meteorológicas
    • Predicción de riesgo basada en modelos validados
    • Notificaciones automáticas por email/SMS
    • Integración con calendario de tratamientos
    • Personalizable por finca y variedad de olivo
    """,
    
    'datos_historicos': """
    📈 Análisis Histórico
    • Período: Datos desde 2020 hasta la actualidad
    • Fuentes: AEMET + Copernicus (Sentinel)
    • Correlaciones: Identificación de patrones estacionales
    • Predicción: Modelos basados en series temporales
    • Comparativa: Años similares para toma de decisiones
    """
}


def get_chart_help_component(chart_type: str, title: str = None) -> html.Div:
    """
    Retorna un componente completo de ayuda para un tipo de gráfico específico
    
    Args:
        chart_type: Tipo de gráfico ('temperatura', 'humedad', 'precipitacion', etc.)
        title: Título personalizado (opcional)
    
    Returns:
        Componente HTML con título e icono de ayuda
    """
    help_text = HELP_TEXTS.get(chart_type, "Información no disponible para este gráfico")
    display_title = title or chart_type.replace('_', ' ').title()
    tooltip_id = f"help-{chart_type}"
    
    return html.Div([
        html.Div([
            html.H6(display_title, className="mb-0"),
            help_icon(tooltip_id, color="primary", size="sm")
        ], className="d-flex align-items-center justify-content-between"),
        create_help_tooltip(tooltip_id, help_text)
    ], className="mb-2")
