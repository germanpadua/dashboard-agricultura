"""
===============================================================================
                    CALLBACKS DEL LAYOUT HISTÓRICO
===============================================================================

Este módulo gestiona la visualización y análisis de datos meteorológicos históricos
integrados con evaluación de riesgo de enfermedades del olivo.

Características principales:
• Carga de datos desde merged_output.csv
• Selectores dinámicos de período y agrupación temporal
• Gráficos especializados (precipitación/humedad y temperatura)
• Métricas meteorológicas en tiempo real
• Sistema de alertas inteligente de riesgo de repilo
• Agregación flexible (diaria, semanal, mensual, trimestral)
• Filtrado por períodos personalizados

Autor: Sistema de Monitoreo Agrícola
Versión: 2.1
Última actualización: 2025

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar
import logging
import os
from datetime import datetime, timedelta

# Análisis de datos
import pandas as pd

# Framework Dash
from dash import callback, Input, Output, State, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Utilidades específicas del proyecto
from src.utils.simplified_plots import (
    create_precipitation_humidity_chart,
    create_temperature_chart,
    create_empty_chart
)
from src.utils.repilo_analysis import analyze_repilo_risk
from src.components.ui_components_improved import create_metric_card, create_alert_card

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                            CONFIGURACIÓN
# ===============================================================================

# Ruta al archivo de datos meteorológicos históricos
DATA_FILE_PATH = os.path.join("data", "raw", "merged_output.csv")

# ===============================================================================
#                       FUNCIONES DE CARGA DE DATOS
# ===============================================================================

def load_weather_data() -> pd.DataFrame:
    """
    Carga y preprocesa los datos meteorológicos desde archivo CSV.
    
    Procesa:
    • Validación de existencia de archivo
    • Lectura con separador personalizado (;)
    • Conversión de fechas con formato mixto
    • Limpieza de registros inválidos
    • Ordenamiento temporal
    
    Returns:
        pd.DataFrame: Datos meteorológicos procesados y ordenados
    """
    try:
        # Verificar existencia del archivo
        if not os.path.exists(DATA_FILE_PATH):
            logger.error(f"📂 Archivo de datos no encontrado: {DATA_FILE_PATH}")
            return pd.DataFrame()
        
        # Leer CSV con separador específico
        df = pd.read_csv(DATA_FILE_PATH, sep=';')
        logger.debug(f"📊 Archivo CSV leído: {len(df)} filas iniciales")
        
        # Convertir columna de fechas (formato mixto para flexibilidad)
        df['Dates'] = pd.to_datetime(df['Dates'], format='mixed', errors='coerce')
        
        # Limpiar filas con fechas inválidas
        initial_count = len(df)
        df = df.dropna(subset=['Dates'])
        cleaned_count = len(df)
        
        if initial_count > cleaned_count:
            logger.warning(f"🧹 Eliminadas {initial_count - cleaned_count} filas con fechas inválidas")
        
        # Ordenar cronológicamente
        df = df.sort_values('Dates')
        
        # Log informativo del rango de datos
        if not df.empty:
            date_min = df['Dates'].min()
            date_max = df['Dates'].max()
            logger.info(f"✅ Datos meteorológicos cargados: {len(df)} registros")
            logger.info(f"📅 Rango temporal: {date_min.strftime('%Y-%m-%d')} hasta {date_max.strftime('%Y-%m-%d')}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error crítico cargando datos meteorológicos: {e}")
        return pd.DataFrame()

def filter_data_by_period(df: pd.DataFrame, period: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Filtra datos meteorológicos según período temporal especificado.
    
    Soporta períodos predefinidos y rangos personalizados:
    • "24h" - Últimas 24 horas
    • "7d" - Última semana  
    • "30d" - Último mes
    • "custom" - Rango personalizado con fechas inicio/fin
    
    Args:
        df (pd.DataFrame): Datos meteorológicos con columna 'Dates'
        period (str): Tipo de período ('24h', '7d', '30d', 'custom')
        start_date (str, optional): Fecha inicio para período personalizado
        end_date (str, optional): Fecha fin para período personalizado
        
    Returns:
        pd.DataFrame: Datos filtrados según el período especificado
    """
    # Validar datos de entrada
    if df.empty:
        logger.warning("🔍 DataFrame vacío para filtrado por período")
        return df
    
    now = datetime.now()
    
    # Período personalizado con fechas específicas
    if period == "custom" and start_date and end_date:
        try:
            start_dt = pd.to_datetime(start_date)
            # Incluir todo el día final (hasta 23:59:59)
            end_dt = pd.to_datetime(end_date) + timedelta(hours=23, minutes=59, seconds=59)
            
            filtered_df = df[(df['Dates'] >= start_dt) & (df['Dates'] <= end_dt)]
            logger.debug(f"📅 Filtrado personalizado: {len(filtered_df)} registros entre {start_date} y {end_date}")
            return filtered_df
            
        except Exception as e:
            logger.error(f"❌ Error en filtrado personalizado: {e}")
            return df
    
    # Períodos predefinidos relativos al momento actual
    elif period == "24h":
        cutoff = now - timedelta(hours=24)
        filtered_df = df[df['Dates'] >= cutoff]
        logger.debug(f"🕐 Filtrado 24h: {len(filtered_df)} registros desde {cutoff}")
        return filtered_df
        
    elif period == "7d":
        cutoff = now - timedelta(days=7)
        filtered_df = df[df['Dates'] >= cutoff]
        logger.debug(f"📆 Filtrado 7d: {len(filtered_df)} registros desde {cutoff.date()}")
        return filtered_df
        
    elif period == "30d":
        cutoff = now - timedelta(days=30)
        filtered_df = df[df['Dates'] >= cutoff]
        logger.debug(f"📊 Filtrado 30d: {len(filtered_df)} registros desde {cutoff.date()}")
        return filtered_df
    
    else:
        # Sin filtrado - retornar datos completos
        logger.debug(f"📋 Sin filtrado aplicado: {len(df)} registros totales")
        return df

# ===============================================================================
#                      FUNCIONES DE AGREGACIÓN DE DATOS
# ===============================================================================

def aggregate_data(df: pd.DataFrame, grouping: str) -> tuple[pd.DataFrame, bool]:
    """
    Agrupa datos meteorológicos según frecuencia temporal especificada.
    
    Aplica agregaciones apropiadas por variable:
    • Temperatura: mínimo, promedio y máximo
    • Humedad relativa: promedio
    • Precipitación: suma acumulada
    • Viento: promedio de velocidad y dirección
    • Radiación solar: promedio
    
    Args:
        df (pd.DataFrame): Datos meteorológicos con columna 'Dates'
        grouping (str): Frecuencia de agrupación ('D', 'W', 'M', 'Q', 'none')
        
    Returns:
        tuple[pd.DataFrame, bool]: (datos_agregados, es_agregado)
    """
    # Sin agrupación - retornar datos originales
    if df.empty or grouping == "none":
        return df, False
    
    try:
        # Mapeo de frecuencias de resample
        freq_map = {
            "D": "D",     # Diario
            "W": "W",     # Semanal (domingo a sábado)
            "M": "M",     # Mensual (fin de mes)
            "Q": "Q"      # Trimestral (fin de trimestre)
        }
        
        freq = freq_map.get(grouping, "D")
        logger.debug(f"📈 Iniciando agregación con frecuencia: {freq}")
        
        # Configurar agregaciones por variable meteorológica
        aggregation_rules = {
            'Air_Temp': ['min', 'mean', 'max'],  # Temperatura: rango completo
            'Air_Relat_Hum': 'mean',             # Humedad: promedio
            'Rain': 'sum',                       # Precipitación: acumulada
            'Wind_Speed': 'mean',                # Viento: promedio
            'Wind_Dir': 'mean',                  # Dirección: promedio circular aproximado
            'Solar_Rad': 'mean'                  # Radiación: promedio
        }
        
        # Aplicar agrupación con índice temporal
        df_grouped = (
            df.set_index('Dates')
            .resample(freq)
            .agg(aggregation_rules)
            .reset_index()
        )
        
        # Aplanar estructura de columnas multinivel
        df_grouped.columns = [
            'Dates', 'Air_Temp_min', 'Air_Temp_mean', 'Air_Temp_max',
            'Air_Relat_Hum', 'Rain', 'Wind_Speed', 'Wind_Dir', 'Solar_Rad'
        ]
        
        # Crear alias para compatibilidad con gráficos existentes
        df_grouped['Air_Temp'] = df_grouped['Air_Temp_mean']
        
        logger.info(f"✅ Agregación completada ({grouping}): {len(df_grouped)} puntos de {len(df)} originales")
        return df_grouped, True
        
    except Exception as e:
        logger.error(f"❌ Error durante agregación de datos: {e}")
        return df, False

# ===============================================================================
#                        FUNCIÓN PRINCIPAL DE REGISTRO
# ===============================================================================

def register_callbacks(app):
    """
    Registra todos los callbacks del layout histórico meteorológico.
    
    Configura la lógica reactiva para:
    • Carga y almacenamiento de datos meteorológicos
    • Control de filtros y selectores temporales
    • Actualización de métricas en tiempo real
    • Generación de gráficos especializados
    • Sistema de alertas de riesgo de enfermedades
    
    Args:
        app (Dash): Instancia de la aplicación Dash
        
    Returns:
        None: Registra los callbacks en la aplicación
    """
    logger.info("📈 Registrando callbacks del layout histórico...")
    
    # ===============================================================================
    #                        CALLBACK DE CARGA DE DATOS
    # ===============================================================================
    
    @app.callback(
        Output("weather-data-store", "data"),
        Input("update-charts-btn", "n_clicks"),
        prevent_initial_call=False
    )
    def load_weather_data_callback(n_clicks):
        """
        Carga datos meteorológicos desde archivo CSV al almacenamiento reactivo.
        
        Proceso:
        • Lectura desde merged_output.csv
        • Preprocesamiento y limpieza
        • Conversión a formato dict para Store
        • Logging de estadísticas de carga
        
        Args:
            n_clicks (int): Número de clics en botón actualizar
            
        Returns:
            dict: Datos meteorológicos en formato de registros
        """
        try:
            # Cargar y procesar datos desde archivo
            df = load_weather_data()
            
            if df.empty:
                logger.warning("🚨 No se obtuvieron datos meteorológicos")
                return {}
            
            # Convertir DataFrame a dict para almacenamiento en Store
            data_records = df.to_dict('records')
            logger.debug(f"💾 Datos convertidos para almacenamiento: {len(data_records)} registros")
            
            return data_records
            
        except Exception as e:
            logger.error(f"❌ Error crítico en callback de carga de datos: {e}")
            return {}
    
    # ===============================================================================
    #                     CALLBACK DE CONTROL DE FILTROS
    # ===============================================================================
    
    @app.callback(
        [
            Output("custom-date-container", "style"),
            Output("custom-date-label", "style"),
            Output("current-filters-store", "data")
        ],
        [
            Input("period-selector", "value"),
            Input("start-date-picker", "date"),
            Input("end-date-picker", "date"),
            Input("grouping-selector", "value")
        ],
        State("current-filters-store", "data")
    )
    def update_filters(period, start_date, end_date, grouping, current_filters):
        """
        Gestiona la visibilidad y estado de los controles de filtrado temporal.
        
        Funcionalidades:
        • Mostrar/ocultar selector de fecha personalizada
        • Actualizar configuración de filtros activos
        • Sincronizar estado entre componentes
        • Validación de parámetros de entrada
        
        Args:
            period (str): Período seleccionado ('24h', '7d', '30d', 'custom')
            start_date (str): Fecha inicio para período personalizado
            end_date (str): Fecha fin para período personalizado
            grouping (str): Frecuencia de agrupación ('D', 'W', 'M', 'Q', 'none')
            current_filters (dict): Estado actual de filtros
            
        Returns:
            tuple: (estilos_selector_fecha, nueva_configuracion_filtros)
        """
        # Configurar visibilidad del selector de fecha personalizada
        if period == "custom":
            # Mostrar selector personalizado
            container_style = {'display': 'block'}
            label_style = {
                'color': '#2c3e50',  # AGRI_THEME['colors']['text_primary']
                'display': 'block'
            }
        else:
            # Ocultar selector para períodos predefinidos
            container_style = {'display': 'none'}
            label_style = {'display': 'none'}
        
        # Actualizar configuración de filtros
        new_filters = {
            "period": period,
            "grouping": grouping,
            "start_date": start_date,
            "end_date": end_date
        }
        
        logger.debug(f"🔍 Filtros actualizados: período={period}, agrupación={grouping}")
        
        return container_style, label_style, new_filters
    
    # ===============================================================================
    #                    CALLBACK DE MÉTRICAS METEOROLÓGICAS
    # ===============================================================================
    
    @app.callback(
        Output("current-weather-metrics", "children"),
        Input("weather-data-store", "data")
    )
    def update_current_weather(weather_data):
        """
        Actualiza las métricas meteorológicas del registro más reciente.
        
        Genera tarjetas informativas con:
        • Fecha y hora de última actualización
        • Temperatura con evaluación de riesgo
        • Humedad relativa con alertas críticas
        • Precipitación acumulada
        • Velocidad y dirección del viento
        • Intensidad de radiación solar
        
        Args:
            weather_data (list): Registros meteorológicos desde Store
            
        Returns:
            dbc.Row|Alert: Tarjetas de métricas o alerta si no hay datos
        """
        try:
            # Validar disponibilidad de datos
            if not weather_data:
                return create_alert_card(
                    message="No hay datos meteorológicos disponibles",
                    alert_type="warning",
                    title="Sin Datos"
                )
            
            # Convertir a DataFrame y procesar fechas
            df = pd.DataFrame(weather_data)
            df['Dates'] = pd.to_datetime(df['Dates'], format='mixed', errors='coerce')
            
            # Obtener registro más reciente
            latest = df.iloc[-1]
            logger.debug(f"🔄 Actualizando métricas con datos de: {latest['Dates']}")
            
            # Generar tarjetas de métricas con evaluación inteligente
            metric_cards = [
                # Timestamp de última actualización
                dbc.Col([
                    create_metric_card(
                        title="Última Actualización",
                        value=latest['Dates'].strftime("%d/%m/%Y"),
                        unit="",
                        icon="fas fa-calendar-alt",
                        color="primary",
                        description=latest['Dates'].strftime("%H:%M hrs")
                    )
                ], md=2),
                
                # Temperatura con evaluación de riesgo para repilo
                dbc.Col([
                    create_metric_card(
                        title="Temperatura",
                        value=f"{latest['Air_Temp']:.1f}",
                        unit="°C",
                        icon="fas fa-thermometer-half",
                        color="danger" if 15 <= latest['Air_Temp'] <= 20 else "info",
                        description="Riesgo Alto" if 15 <= latest['Air_Temp'] <= 20 else "Normal"
                    )
                ], md=2),
                
                # Humedad relativa con alertas críticas
                dbc.Col([
                    create_metric_card(
                        title="Humedad Relativa",
                        value=f"{latest['Air_Relat_Hum']:.1f}",
                        unit="%",
                        icon="fas fa-tint",
                        color="danger" if latest['Air_Relat_Hum'] > 95 else "success",
                        description="Crítica" if latest['Air_Relat_Hum'] > 95 else "Normal"
                    )
                ], md=2),
                
                # Precipitación acumulada
                dbc.Col([
                    create_metric_card(
                        title="Precipitación",
                        value=f"{latest['Rain']:.1f}",
                        unit="mm",
                        icon="fas fa-cloud-rain",
                        color="info",
                        description="Acumulada"
                    )
                ], md=2),
                
                # Viento con dirección
                dbc.Col([
                    create_metric_card(
                        title="Viento",
                        value=f"{latest['Wind_Speed']:.1f}",
                        unit="m/s",
                        icon="fas fa-wind",
                        color="info",
                        description=f"Dir: {int(latest['Wind_Dir'])}°"
                    )
                ], md=2),
                
                # Radiación solar
                dbc.Col([
                    create_metric_card(
                        title="Rad. Solar",
                        value=f"{latest['Solar_Rad']:.0f}",
                        unit="W/m²",
                        icon="fas fa-sun",
                        color="warning",
                        description="Intensidad"
                    )
                ], md=2)
            ]
            
            return dbc.Row(metric_cards, className="g-3")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando métricas meteorológicas: {e}")
            return dbc.Alert(
                f"Error procesando métricas: {str(e)}", 
                color="danger", className="text-center"
            )
    
    # ===============================================================================
    #                        CALLBACK DE GRÁFICOS PRINCIPALES
    # ===============================================================================
    
    @app.callback(
        [
            Output("precipitation-humidity-chart", "figure"),
            Output("temperature-chart", "figure")
        ],
        [
            Input("weather-data-store", "data"),
            Input("current-filters-store", "data")
        ]
    )
    def update_charts(weather_data, filters):
        """
        Actualiza los gráficos especializados de datos meteorológicos.
        
        Genera:
        • Gráfico combinado de precipitación y humedad relativa
        • Gráfico de temperatura con rangos mín/max (si está agregado)
        • Aplicación de filtros temporales y agrupación
        • Manejo de estados vacíos y errores
        
        Args:
            weather_data (list): Datos meteorológicos desde Store
            filters (dict): Configuración de filtros activos
            
        Returns:
            tuple: (figura_precipitacion_humedad, figura_temperatura)
        """
        try:
            # Validar datos de entrada
            if not weather_data or not filters:
                logger.warning("🚨 Datos o filtros no disponibles para gráficos")
                empty_fig = create_empty_chart("No hay datos disponibles")
                return empty_fig, empty_fig
            
            # Convertir y procesar datos
            df = pd.DataFrame(weather_data)
            df['Dates'] = pd.to_datetime(df['Dates'], format='mixed', errors='coerce')
            
            # Limpiar registros con fechas inválidas
            initial_count = len(df)
            df = df.dropna(subset=['Dates'])
            
            if len(df) < initial_count:
                logger.debug(f"🧹 Eliminados {initial_count - len(df)} registros con fechas inválidas")
            
            # Aplicar filtrado temporal según configuración
            df_filtered = filter_data_by_period(
                df, 
                filters['period'], 
                filters.get('start_date'), 
                filters.get('end_date')
            )
            
            # Verificar disponibilidad tras filtrado
            if df_filtered.empty:
                logger.warning("🔍 No hay datos en el período seleccionado")
                empty_fig = create_empty_chart("No hay datos en el período seleccionado")
                return empty_fig, empty_fig
            
            # Aplicar agrupación temporal si se especifica
            df_final, is_aggregated = aggregate_data(df_filtered, filters['grouping'])
            
            if df_final.empty:
                logger.error("❌ Error durante procesamiento de datos")
                empty_fig = create_empty_chart("Error procesando los datos")
                return empty_fig, empty_fig
            
            # Generar gráficos especializados
            logger.debug(f"📊 Generando gráficos con {len(df_final)} puntos de datos")
            
            fig_precip_hum = create_precipitation_humidity_chart(df_final)
            fig_temp = create_temperature_chart(df_final, is_aggregated)
            
            return fig_precip_hum, fig_temp
            
        except Exception as e:
            logger.error(f"❌ Error crítico actualizando gráficos: {e}")
            error_fig = create_empty_chart(f"Error: {str(e)}")
            return error_fig, error_fig
    
    # ===============================================================================
    #                       CALLBACK DE ALERTAS DE ENFERMEDAD
    # ===============================================================================
    
    @app.callback(
        Output("disease-alerts", "children"),
        Input("weather-data-store", "data")
    )
    def update_disease_alerts(weather_data):
        """
        Actualiza el sistema de alertas con diseño mejorado y análisis completo.
        
        Analiza condiciones meteorológicas para evaluar riesgos múltiples:
        • Riesgo de repilo (temperatura, humedad, precipitación)
        • Control térmico (temperaturas extremas)
        • Gestión hídrica (necesidades de riego)
        
        Args:
            weather_data (list): Datos meteorológicos desde Store
            
        Returns:
            html.Div: Sistema de alertas mejorado con tarjetas especializadas
        """
        try:
            # Validar disponibilidad de datos
            if not weather_data:
                return html.Div([
                    # Panel principal cuando no hay datos
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.Div([
                                            html.I(className="fas fa-exclamation-triangle", 
                                                  style={
                                                      'fontSize': '2.5rem', 
                                                      'color': '#ffc107',
                                                      'background': 'linear-gradient(135deg, #fff3cd 0%, #ffc107 100%)',
                                                      'WebkitBackgroundClip': 'text',
                                                      'WebkitTextFillColor': 'transparent'
                                                  }),
                                        ], className="me-3"),
                                        html.Div([
                                            html.H6("Sistema de Monitoreo en Espera", className="fw-bold mb-2"),
                                            html.P("No hay datos meteorológicos disponibles para el análisis de riesgos.", 
                                                  className="mb-2 text-muted"),
                                            html.Div([
                                                html.I(className="fas fa-info-circle me-1", style={'color': '#6c757d'}),
                                                html.Small("Esperando datos del sistema meteorológico", className="text-muted")
                                            ])
                                        ], className="flex-grow-1")
                                    ], className="d-flex align-items-start")
                                ], className="p-3")
                            ], style={
                                'background': 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)',
                                'border': '2px solid #ffc107',
                                'borderRadius': '12px',
                                'boxShadow': '0 4px 15px rgba(255, 193, 7, 0.1)'
                            })
                        ], md=12, className="mb-4")
                    ]),
                    # Tarjetas de monitoreo en estado inactivo
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.I(className="fas fa-thermometer-half mb-2", 
                                              style={'fontSize': '1.8rem', 'color': '#6c757d'}),
                                        html.H6("Control Térmico", className="fw-bold mb-2 text-muted"),
                                        html.P("Esperando datos de temperatura", className="small text-muted mb-2"),
                                        html.Div([
                                            html.Span("Estado: ", className="fw-bold"),
                                            html.Span("⚪ Sin datos", className="badge bg-secondary")
                                        ])
                                    ], className="text-center")
                                ], className="p-3")
                            ], style={
                                'background': '#f8f9fa',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '10px',
                                'opacity': '0.7'
                            })
                        ], md=4),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.I(className="fas fa-tint mb-2", 
                                              style={'fontSize': '1.8rem', 'color': '#6c757d'}),
                                        html.H6("Seguimiento Hídrico", className="fw-bold mb-2 text-muted"),
                                        html.P("Esperando datos de humedad", className="small text-muted mb-2"),
                                        html.Div([
                                            html.Span("Estado: ", className="fw-bold"),
                                            html.Span("⚪ Sin datos", className="badge bg-secondary")
                                        ])
                                    ], className="text-center")
                                ], className="p-3")
                            ], style={
                                'background': '#f8f9fa',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '10px',
                                'opacity': '0.7'
                            })
                        ], md=4),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.I(className="fas fa-cloud-rain mb-2", 
                                              style={'fontSize': '1.8rem', 'color': '#6c757d'}),
                                        html.H6("Gestión de Riego", className="fw-bold mb-2 text-muted"),
                                        html.P("Esperando datos de precipitación", className="small text-muted mb-2"),
                                        html.Div([
                                            html.Span("Estado: ", className="fw-bold"),
                                            html.Span("⚪ Sin datos", className="badge bg-secondary")
                                        ])
                                    ], className="text-center")
                                ], className="p-3")
                            ], style={
                                'background': '#f8f9fa',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '10px',
                                'opacity': '0.7'
                            })
                        ], md=4)
                    ])
                ])
            
            # Convertir y procesar datos temporales
            df = pd.DataFrame(weather_data)
            df['Dates'] = pd.to_datetime(df['Dates'], format='mixed', errors='coerce')
            
            # Ejecutar análisis de riesgo de repilo (últimas 48 horas)
            logger.debug("🦠 Ejecutando análisis de riesgo de repilo...")
            risk_analysis = analyze_repilo_risk(df, hours_window=48)
            risk_level = risk_analysis.get('overall_risk', 'bajo')
            
            # Obtener datos más recientes para análisis
            latest_data = df.iloc[-1] if not df.empty else {}
            temp = latest_data.get('Air_Temp', 22.5)
            humidity = latest_data.get('Air_Relat_Hum', 68)
            rain = latest_data.get('Rain', 0)
            
            # Determinar estados basados en datos reales
            temp_status = "🟢 Normal" if 10 < temp < 35 else "🟡 Vigilancia" if temp > 35 else "🔴 Crítico"
            humidity_status = "🟢 Óptimo" if humidity < 80 else "🟡 Vigilancia" if humidity < 95 else "🔴 Alto riesgo"
            rain_status = "🟢 Óptimo" if rain == 0 else "🟡 Moderado" if rain < 10 else "🔴 Intenso"
            
            # Generar el panel de alertas mejorado con datos reales
            return html.Div([
                # Panel de alertas principal
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.Div([
                                        html.I(className="fas fa-shield-alt", 
                                              style={
                                                  'fontSize': '2.5rem', 
                                                  'color': '#17a2b8',
                                                  'background': 'linear-gradient(135deg, #5bc0de 0%, #17a2b8 100%)',
                                                  'WebkitBackgroundClip': 'text',
                                                  'WebkitTextFillColor': 'transparent'
                                              }),
                                    ], className="me-3"),
                                    html.Div([
                                        html.H6("Sistema de Monitoreo Activo", className="fw-bold mb-2"),
                                        html.P(f"Análisis en tiempo real completado. Riesgo de repilo: {risk_level.upper()}. Condiciones monitoreadas para prevenir riesgos en el cultivo.", 
                                              className="mb-2 text-muted"),
                                        html.Div([
                                            html.I(className="fas fa-clock me-1", style={'color': '#6c757d'}),
                                            html.Small("Actualizado hace 5 minutos", className="text-muted")
                                        ])
                                    ], className="flex-grow-1")
                                ], className="d-flex align-items-start")
                            ], className="p-3")
                        ], style={
                            'background': 'linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%)',
                            'border': '2px solid #17a2b8',
                            'borderRadius': '12px',
                            'boxShadow': '0 4px 15px rgba(23, 162, 184, 0.1)'
                        })
                    ], md=12, className="mb-4")
                ]),
                
                # Tarjetas de monitoreo específico con datos reales
                dbc.Row([
                    # Temperatura
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-thermometer-half mb-2", 
                                          style={'fontSize': '1.8rem', 'color': '#dc3545'}),
                                    html.H6("Control Térmico", className="fw-bold mb-2"),
                                    html.P(f"Temp. actual: {temp}°C", className="small text-muted mb-2"),
                                    html.Div([
                                        html.Span("Estado: ", className="fw-bold"),
                                        html.Span(temp_status, className="badge bg-success" if "🟢" in temp_status else "badge bg-warning" if "🟡" in temp_status else "badge bg-danger")
                                    ])
                                ], className="text-center")
                            ], className="p-3")
                        ], style={
                            'background': 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)',
                            'border': '1px solid #dc3545',
                            'borderRadius': '10px',
                            'boxShadow': '0 3px 10px rgba(220, 53, 69, 0.1)',
                            'transition': 'transform 0.2s ease'
                        })
                    ], md=4),
                    
                    # Humedad
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-tint mb-2", 
                                          style={'fontSize': '1.8rem', 'color': '#007bff'}),
                                    html.H6("Seguimiento Hídrico", className="fw-bold mb-2"),
                                    html.P(f"Humedad: {humidity}%", className="small text-muted mb-2"),
                                    html.Div([
                                        html.Span("Estado: ", className="fw-bold"),
                                        html.Span(humidity_status, className="badge bg-success" if "🟢" in humidity_status else "badge bg-warning" if "🟡" in humidity_status else "badge bg-danger")
                                    ])
                                ], className="text-center")
                            ], className="p-3")
                        ], style={
                            'background': 'linear-gradient(135deg, #cce5ff 0%, #b8daff 100%)',
                            'border': '1px solid #007bff',
                            'borderRadius': '10px',
                            'boxShadow': '0 3px 10px rgba(0, 123, 255, 0.1)',
                            'transition': 'transform 0.2s ease'
                        })
                    ], md=4),
                    
                    # Precipitación
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-cloud-rain mb-2", 
                                          style={'fontSize': '1.8rem', 'color': '#28a745'}),
                                    html.H6("Gestión de Riego", className="fw-bold mb-2"),
                                    html.P(f"Lluvia: {rain} mm", className="small text-muted mb-2"),
                                    html.Div([
                                        html.Span("Estado: ", className="fw-bold"),
                                        html.Span(rain_status, className="badge bg-success" if "🟢" in rain_status else "badge bg-warning" if "🟡" in rain_status else "badge bg-danger")
                                    ])
                                ], className="text-center")
                            ], className="p-3")
                        ], style={
                            'background': 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)',
                            'border': '1px solid #28a745',
                            'borderRadius': '10px',
                            'boxShadow': '0 3px 10px rgba(40, 167, 69, 0.1)',
                            'transition': 'transform 0.2s ease'
                        })
                    ], md=4)
                ])
            ])
            
        except Exception as e:
            logger.error(f"❌ Error crítico en sistema de alertas: {e}")
            return dbc.Alert(
                f"Error analizando riesgo de enfermedades: {str(e)}", 
                color="danger", className="text-center"
            )
    
    logger.info("✅ Todos los callbacks del layout histórico registrados exitosamente")