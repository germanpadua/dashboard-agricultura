"""
===============================================================================
                       CALLBACKS PRINCIPALES DEL DASHBOARD
===============================================================================

Este módulo contiene los callbacks transversales que coordinan la funcionalidad
global del dashboard agrícola, incluyendo navegación entre pestañas y renderizado
dinámico de layouts.

Características principales:
• Router inteligente con anti-rebote
• Navegación fluida entre pestañas
• Carga dinámica de layouts especializados
• Validación de pestañas permitidas
• Manejo robusto de errores con fallbacks
• Preprocesamiento de datos para layouts
• Sistema de logging detallado

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
import time

# Framework Dash
from dash import callback, Input, Output, State, html, no_update, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# Análisis de datos
import pandas as pd

# Utilidades del proyecto (mantenidas para compatibilidad)
from src.utils.plots import make_soil_figure, make_temp_figure
from src.utils.weather_utils import get_municipio_code, get_prediccion_diaria, get_prediccion_horaria

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                           FUNCIONES AUXILIARES
# ===============================================================================

def render_weather(tab: str, df: pd.DataFrame) -> html.Div:
    """
    Genera contenido contextual del panel meteorológico según pestaña.
    
    Implementa dos modos de visualización:
    • 'hoy': Datos actuales del último registro disponible
    • 'semana': Resumen agregado de los últimos 7 días
    
    Args:
        tab (str): Modo de visualización ('hoy', 'semana')
        df (pd.DataFrame): Datos meteorológicos con columnas estándar
                          ['Dates', 'Air_Temp', 'Rain', 'Wind_Speed', 
                           'Wind_Dir', 'Air_Relat_Hum']
                           
    Returns:
        html.Div: Componente con tarjetas meteorológicas estilizadas
    """
    # Mapeo de días de la semana a español
    dias_es = {
        'Mon': 'lun', 'Tue': 'mar', 'Wed': 'mié', 'Thu': 'jue',
        'Fri': 'vie', 'Sat': 'sáb', 'Sun': 'dom'
    }

    # ===================================================================
    #                        MODO 'HOY' - DATOS ACTUALES
    # ===================================================================
    
    if tab == 'hoy':
        # Obtener último registro disponible
        latest_record = df.iloc[-1]
        fecha_actual = latest_record['Dates'].strftime("%d/%m/%Y %H:%M")
        
        # Estructurar información meteorológica actual
        current_weather_info = [
            ("📅 Fecha", fecha_actual),
            ("🌡️ Temperatura", f"{latest_record['Air_Temp']:.1f} °C"),
            ("🌧️ Precipitación", f"{latest_record['Rain']:.1f} mm"),
            ("💨 Viento", f"{latest_record['Wind_Speed']:.1f} m/s, {int(latest_record['Wind_Dir'])}°"),
            ("🌬️ Humedad", f"{latest_record['Air_Relat_Hum']:.0f} %"),
        ]
        
        # Generar tarjetas informativas
        weather_cards = []
        for title, value in current_weather_info:
            card = dbc.Card([
                dbc.CardHeader(
                    title, 
                    className="fw-bold text-center",
                    style={'backgroundColor': '#f8f9fa', 'border': 'none'}
                ),
                dbc.CardBody(
                    html.H4(
                        value, 
                        className="card-title text-center mb-0",
                        style={'color': '#2E7D32', 'fontWeight': '700'}
                    )
                )
            ], className="shadow-sm border-0", 
               style={"minWidth": "10rem", "borderRadius": "12px"})
            
            weather_cards.append(card)
        
        return html.Div([
            dbc.Row(
                [dbc.Col(card, width="auto") for card in weather_cards], 
                className="g-4 justify-content-center"
            )
        ])

    # ===================================================================
    #                     MODO 'SEMANA' - RESUMEN SEMANAL
    # ===================================================================
    
    # Determinar ventana temporal para semana actual
    now = pd.Timestamp.now().normalize()
    monday_current_week = now - pd.Timedelta(days=now.weekday())
    
    # Filtrar datos de la semana actual
    week_data = df[
        (df['Dates'] >= monday_current_week) & 
        (df['Dates'] < monday_current_week + pd.Timedelta(days=7))
    ]
    
    # Fallback: si no hay datos de semana actual, usar últimos 7 días
    if week_data.empty:
        last_date = df['Dates'].max()
        week_data = df[
            (df['Dates'] >= last_date - pd.Timedelta(days=6)) & 
            (df['Dates'] <= last_date)
        ]
        logger.debug("🔄 Usando últimos 7 días como fallback para vista semanal")

    # Agregación diaria de datos meteorológicos
    aggregation_rules = {
        'Air_Temp': ['min', 'max'],  # Temperaturas mín/máx
        'Rain': 'sum'                # Precipitación acumulada
    }
    
    daily_summary = (
        week_data.set_index('Dates')
        .resample('D')
        .agg(aggregation_rules)
    )
    
    # Aplanar columnas multinivel
    daily_summary.columns = ['_'.join(col) for col in daily_summary.columns]

    # Generar tarjetas para cada día
    daily_cards = []
    for timestamp, daily_data in daily_summary.iterrows():
        # Información del día
        dia_abrev = dias_es.get(timestamp.strftime('%a'), timestamp.strftime('%a'))
        numero_dia = timestamp.day
        
        # Temperaturas
        temp_max = f"{daily_data['Air_Temp_max']:.0f}°"
        temp_min = f"{daily_data['Air_Temp_min']:.0f}°"
        
        # Precipitación con icono contextual
        lluvia_total = daily_data['Rain_sum']
        precipitacion_text = f"{lluvia_total:.1f} mm"
        
        # Selección inteligente de icono meteorológico
        if lluvia_total >= 5:
            weather_icon = '🌧️'  # Lluvia fuerte
        elif lluvia_total > 0:
            weather_icon = '⛅'       # Parcialmente nublado
        else:
            weather_icon = '☀️'     # Soleado
        
        # Construir tarjeta individual
        daily_card = html.Div([
            # Header con día
            html.Div(
                f"{dia_abrev} {numero_dia}", 
                className="fw-bold mb-1",
                style={'fontSize': '0.85rem', 'color': '#2c3e50'}
            ),
            
            # Icono meteorológico
            html.Div(
                weather_icon, 
                style={
                    "fontSize": "1.6rem", 
                    "lineHeight": "1", 
                    "marginBottom": "8px"
                }
            ),
            
            # Temperatura máxima
            html.Div(
                temp_max, 
                className="fw-semibold",
                style={'fontSize': '0.9rem', 'color': '#e74c3c'}
            ),
            
            # Temperatura mínima
            html.Div(
                temp_min, 
                className="text-muted",
                style={'fontSize': '0.8rem'}
            ),
            
            # Precipitación
            html.Div(
                precipitacion_text, 
                style={'fontSize': '0.75rem', 'color': '#3498db'}
            )
        ], className="text-center p-2", style={
            "minWidth": "70px",
            "borderRadius": "0.75rem",
            "backgroundColor": "#f8f9fa",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            "transition": "transform 0.2s ease",
            "cursor": "default"
        })
        
        daily_cards.append(daily_card)

    return html.Div(
        daily_cards, 
        style={
            "display": "flex", 
            "gap": "8px", 
            "overflowX": "auto", 
            "padding": "4px",
            "scrollbarWidth": "thin"
        }
    )


# ===============================================================================
#                           FUNCIÓN DE REGISTRO PRINCIPAL
# ===============================================================================

def register_callbacks(app):
    """
    Registra callbacks principales y transversales del dashboard agrícola.
    
    Configura el sistema de navegación inteligente que gestiona la transición
    entre pestañas del dashboard con las siguientes características avanzadas:
    
    • Router con anti-rebote y validación de entrada
    • Navegación fluida entre módulos especializados
    • Carga dinámica de layouts con manejo de errores
    • Sistema de estado interno para prevenir cambios involuntarios
    • Fallback robusto en caso de errores de importación
    
    Args:
        app: Instancia de la aplicación Dash
        
    Note:
        Esta función debe llamarse una sola vez durante la inicialización
        de la aplicación para registrar correctamente todos los callbacks
        del sistema de navegación.
    """
    logger.info("🔧 Iniciando registro de callbacks principales...")

    # ===================================================================
    #                    CONFIGURACIÓN DE NAVEGACIÓN
    # ===================================================================
    
    # Pestañas válidas del sistema - conjunto inmutable para seguridad
    ALLOWED_TABS = {
        "detecciones",      # Análisis de enfermedades detectadas
        "historico",        # Datos meteorológicos históricos  
        "prediccion",       # Pronósticos y modelos predictivos
        "datos-satelitales", # Análisis de imágenes satelitales
        "fincas"           # Gestión de propiedades agrícolas
    }

    # Estado interno del módulo para control de anti-rebote
    _navigation_state = {
        "last_tab": None,           # Última pestaña válida seleccionada
        "last_change_ts": 0.0,      # Timestamp del último cambio exitoso
        "debounce_threshold": 0.5   # Umbral mínimo entre cambios (segundos)
    }

    # ===================================================================
    #                    CALLBACK PRINCIPAL DE NAVEGACIÓN
    # ===================================================================

    @app.callback(
        # Salidas duales: contenido dinámico y confirmación de pestaña activa
        Output("main-content", "children"),     # Contenido principal del dashboard
        Output("main-tabs", "value"),          # Pestaña activa (con autocorrección)
        
        # Entradas: pestaña seleccionada y datos de contexto
        Input("main-tabs", "value"),           # Pestaña solicitada por el usuario
        State('weather-data', 'data'),         # Datos meteorológicos en memoria
        State('kml-data', 'data'),            # Datos geoespaciales cargados
        
        # Configuración del callback
        prevent_initial_call=False,            # Permitir carga inicial
        allow_duplicate=True                   # Permitir actualizaciones duplicadas
    )
    def intelligent_layout_router(selected_tab, weather_data, kml_data):
        """
        Router inteligente de layouts con sistema anti-rebote y validación.
        
        Gestiona la navegación entre diferentes módulos del dashboard con
        validación robusta y recuperación de errores. Implementa un sistema
        de anti-rebote para evitar cambios involuntarios muy rápidos.
        
        Args:
            selected_tab (str): Pestaña seleccionada por el usuario
            weather_data (list): Datos meteorológicos en formato JSON
            kml_data (dict): Datos geoespaciales en formato GeoJSON
            
        Returns:
            tuple: (layout_content, confirmed_tab)
                - layout_content: Componente Dash con el layout renderizado
                - confirmed_tab: Pestaña efectivamente activa (puede diferir 
                  de selected_tab en caso de rebote o error)
                  
        Raises:
            PreventUpdate: Cuando se detecta entrada inválida o rebote
        """
        current_timestamp = time.time()
        
        logger.info(f"🧭 Solicitud de navegación a pestaña: '{selected_tab}'")

        # ===============================================================
        #                    VALIDACIÓN DE ENTRADA
        # ===============================================================
        
        # Filtro primario: rechazar valores None o pestañas inválidas
        if selected_tab is None or selected_tab not in ALLOWED_TABS:
            logger.warning(f"⚠️ Pestaña inválida rechazada: '{selected_tab}'")
            logger.debug(f"Pestañas válidas: {ALLOWED_TABS}")
            raise PreventUpdate  # No realizar ningún cambio

        # ===============================================================
        #                    SISTEMA ANTI-REBOTE
        # ===============================================================
        
        # Detectar cambios muy rápidos que podrían ser rebotes involuntarios
        last_tab = _navigation_state["last_tab"]
        last_timestamp = _navigation_state["last_change_ts"]
        debounce_threshold = _navigation_state["debounce_threshold"]
        
        if (last_tab is not None 
            and last_tab != selected_tab
            and (current_timestamp - last_timestamp) < debounce_threshold):
            
            logger.warning(
                f"🚫 Cambio demasiado rápido detectado: "
                f"'{last_tab}' → '{selected_tab}' "
                f"(Δt: {current_timestamp - last_timestamp:.3f}s)"
            )
            
            # Devolver al estado anterior sin cambios
            return no_update, last_tab

        # ===============================================================
        #                PREPARACIÓN DE DATOS AUXILIARES
        # ===============================================================
        
        # Reconstruir DataFrame meteorológico desde datos serializados
        weather_df = pd.DataFrame(weather_data) if weather_data else pd.DataFrame()
        
        # Conversión segura de fechas si existen datos
        if not weather_df.empty and 'Dates' in weather_df.columns:
            try:
                weather_df['Dates'] = pd.to_datetime(
                    weather_df['Dates'], 
                    format='mixed', 
                    errors='coerce'
                )
                logger.debug(f"📅 Datos meteorológicos procesados: {len(weather_df)} registros")
            except Exception as e:
                logger.error(f"⚠️ Error procesando fechas meteorológicas: {e}")
        
        # Preparar datos geoespaciales
        kml_geojson = kml_data if kml_data else {}
        
        if kml_geojson:
            logger.debug("🗺️ Datos geoespaciales disponibles para el layout")

        # ===============================================================
        #                    RENDERIZADO DINÁMICO DE LAYOUTS
        # ===============================================================
        
        layout_content = None
        
        try:
            # Enrutamiento basado en pestaña seleccionada
            if selected_tab == "detecciones":
                logger.info("🦠 Construyendo layout de detecciones de enfermedades...")
                from src.layouts.layout_detecciones_enhanced import build_layout_detecciones_enhanced
                layout_content = build_layout_detecciones_enhanced()
                
            elif selected_tab == "historico":
                logger.info("📊 Construyendo layout de análisis histórico...")
                from src.layouts.layout_historico import build_layout_historico_improved
                layout_content = build_layout_historico_improved(weather_df, kml_geojson)
                
            elif selected_tab == "prediccion":
                logger.info("🔮 Construyendo layout de predicciones meteorológicas...")
                from src.layouts.layout_prediccion_improved import build_layout_prediccion_improved
                layout_content = build_layout_prediccion_improved()
                
            elif selected_tab == "datos-satelitales":
                logger.info("🛰️ Construyendo layout de análisis satelital...")
                
                # Sistema de importación con recarga forzada para desarrollo
                import importlib
                import inspect
                
                try:
                    import src.layouts.layout_datos_satelitales_improved as satellite_layout
                    
                    # Forzar recarga del módulo (útil durante desarrollo)
                    satellite_layout = importlib.reload(satellite_layout)
                    
                    logger.debug(f"✅ Módulo satelital cargado desde: {inspect.getfile(satellite_layout)}")
                    
                    # Verificar que la función principal existe
                    if hasattr(satellite_layout, 'build_scientific_satellite_layout'):
                        layout_content = satellite_layout.build_scientific_satellite_layout()
                        logger.info("✅ Layout satelital construido exitosamente")
                    else:
                        raise AttributeError("Función 'build_scientific_satellite_layout' no encontrada")
                        
                except ImportError as ie:
                    logger.error(f"❌ Error de importación en módulo satelital: {ie}")
                    raise
                except Exception as e:
                    logger.error(f"❌ Error general en construcción satelital: {e}")
                    raise
                
            elif selected_tab == "fincas":
                logger.info("🏞️ Construyendo layout de gestión de fincas...")
                from src.layouts.layout_fincas_improved import build_layout_fincas_improved
                layout_content = build_layout_fincas_improved()
                
            else:
                # Este caso nunca debería ejecutarse debido a ALLOWED_TABS
                logger.error(f"❌ Pestaña no implementada: '{selected_tab}'")
                raise PreventUpdate
                
        except Exception as construction_error:
            logger.error(
                f"💥 Error crítico construyendo layout '{selected_tab}': "
                f"{construction_error}"
            )
            
            # Layout de emergencia con información de error
            layout_content = html.Div([
                dbc.Alert([
                    html.H4("⚠️ Error de Construcción", className="alert-heading"),
                    html.P(f"No se pudo cargar la pestaña '{selected_tab}'"),
                    html.Hr(),
                    html.P(f"Error técnico: {str(construction_error)}", className="mb-0")
                ], color="danger", className="mx-3 mt-3"),
                
                html.Div([
                    html.H5("🔧 Modo de Emergencia Activado"),
                    html.P("El sistema ha activado un layout de emergencia. "
                           "Por favor, intente navegar a otra pestaña o "
                           "contacte al administrador si el problema persiste.")
                ], className="text-center text-muted p-4")
            ])

        # ===============================================================
        #                    ACTUALIZACIÓN DE ESTADO
        # ===============================================================
        
        # Registrar cambio exitoso en el estado interno
        _navigation_state["last_tab"] = selected_tab
        _navigation_state["last_change_ts"] = current_timestamp
        
        logger.info(f"✅ Navegación completada exitosamente a '{selected_tab}'")
        
        # Retornar layout construido y confirmar pestaña activa
        return layout_content, selected_tab

    # ===================================================================
    #                    CONFIRMACIÓN DE REGISTRO
    # ===================================================================
    
    logger.info("✅ Callbacks principales registrados correctamente")
    logger.debug(f"Sistema de navegación configurado para {len(ALLOWED_TABS)} pestañas")

