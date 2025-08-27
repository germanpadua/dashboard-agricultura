"""
===============================================================================
                    CALLBACKS DEL LAYOUT DE DETECCIONES
===============================================================================

Este módulo gestiona los callbacks específicos para la visualización y análisis
de detecciones de repilo del olivo, integrando datos del bot de Telegram con
inteligencia artificial para clasificación automática.

Características principales:
• Sincronización automática con bot de Telegram
• Clasificación IA de severidad (niveles 1-5)
• Mapas interactivos con Leaflet
• Análisis de tendencias temporales
• Filtros por severidad y período
• Alertas automáticas de riesgo

Autor: German Jose Padua Pleguezuelo
Universidad de Granada
Master en Ciencia de Datos

Fichero: src.callbacks_refactored.detecciones.py

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar de Python
import logging
import sys
import os
from datetime import datetime, timedelta

# Análisis de datos
import pandas as pd

# Visualización
import plotly.graph_objects as go
import plotly.express as px

# Framework Dash
from dash import callback, Input, Output, State, html, dash_table, callback_context, no_update
import dash_bootstrap_components as dbc

# ===============================================================================
#                            CONFIGURACIÓN DE COLORES
# ===============================================================================

# Paleta de colores para niveles de severidad de repilo (1-5)
SEVERITY_COLORS = {
    1: "#4CAF50",  # Verde - Muy baja severidad
    2: "#8BC34A",  # Verde claro - Baja severidad  
    3: "#FF9800",  # Naranja - Severidad moderada
    4: "#F44336",  # Rojo - Alta severidad
    5: "#9C27B0",  # Morado - Severidad crítica
}

# Paleta de colores temática agrícola para la interfaz
AGRI_COLORS = {
    'primary': '#2E7D32',      # Verde olivo principal
    'secondary': '#5D4037',    # Marrón tierra
    'success': '#388E3C',      # Verde éxito
    'warning': '#F57C00',      # Naranja cosecha
    'danger': '#D32F2F',       # Rojo alerta
    'info': '#0277BD',         # Azul cielo
    'bg_light': '#F1F8E9',     # Verde muy suave para fondos
    
    # Colores específicos para severidad de repilo (consistencia con SEVERITY_COLORS)
    'severity_1': '#4CAF50',   # Verde - Muy baja (nivel 1)
    'severity_2': '#8BC34A',   # Verde claro - Baja (nivel 2)
    'severity_3': '#FF9800',   # Naranja - Moderada (nivel 3)
    'severity_4': '#F44336',   # Rojo - Alta (nivel 4)
    'severity_5': '#9C27B0',   # Morado - Muy alta (nivel 5)
}

# ===============================================================================
#                        IMPORTACIONES CONDICIONALES
# ===============================================================================

# Importación condicional de dash_leaflet para mapas interactivos
try:
    import dash_leaflet as dl
    LEAFLET_AVAILABLE = True
except ImportError:
    LEAFLET_AVAILABLE = False
    print("⚠️ dash_leaflet no está disponible - usando fallback para mapas")

# Importar módulo de sincronización con Telegram
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from integrations.telegram_sync import TelegramDataSync

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                           FUNCIÓN PRINCIPAL DE REGISTRO
# ===============================================================================

def register_callbacks(app):
    """
    Registra todos los callbacks específicos del layout de detecciones de repilo.
    
    Esta función configura la lógica reactiva para:
    • Actualización de datos de detecciones desde Telegram
    • Filtrado por período temporal y severidad
    • Visualización de mapas interactivos
    • Generación de gráficos de tendencias
    • Cálculo de métricas y alertas
    
    Args:
        app (Dash): Instancia de la aplicación Dash
    
    Returns:
        None: Registra los callbacks en la aplicación
    """
    logger.info("🦠 Registrando callbacks de detecciones de repilo...")
    
    # Instanciar sincronizador de datos de Telegram
    sync = TelegramDataSync()
    
    # ===============================================================================
    #                      CALLBACK PRINCIPAL DE ACTUALIZACIÓN
    # ===============================================================================
    
    @app.callback(
        [
            # Métricas principales ampliadas
            Output("total-detections", "children"),
            Output("current-detections", "children"),
            Output("recent-detections", "children"),
            Output("avg-severity", "children"),
            Output("max-severity", "children"),
            Output("trend-indicator", "children"),
            
            # Componentes de visualización
            Output("detections-map", "bounds"),
            
            # Capas del mapa por severidad
            Output("severity-1-group", "children"),
            Output("severity-2-group", "children"),
            Output("severity-3-group", "children"),
            Output("severity-4-group", "children"),
            Output("severity-5-group", "children"),
            
            # Gráficos y visualizaciones
            Output("detections-timeline", "figure"),
            Output("severity-distribution", "figure"),
            Output("alert-status-content", "children"),
            
            # Store de datos
            Output("detections-data", "data"),
        ],
        [
            # Controles de período temporal
            Input("btn-week", "n_clicks"),
            Input("btn-month", "n_clicks"),
            Input("btn-all", "n_clicks"),
            
            # Controles de interfaz
            Input("btn-refresh", "n_clicks"),
            Input("btn-fit-bounds", "n_clicks"),
            Input("severity-filter", "value"),
            
        ],
        State("detections-period", "data"),
        prevent_initial_call=False,
    )
    def update_detections_data(week_clicks, month_clicks, all_clicks, refresh_clicks,
                            fit_clicks, severity_filter, period_store):
        """
        Callback principal que actualiza todos los componentes de la interfaz de detecciones.
        
        Gestiona:
        • Carga de datos desde Telegram sync
        • Filtrado por período y severidad
        • Cálculo de métricas y alertas
        • Generación de visualizaciones
        • Actualización de mapas interactivos
        
        Args:
            week_clicks, month_clicks, all_clicks: Clics en botones de período
            refresh_clicks: Clics en botón de actualización
            fit_clicks: Clics en botón de ajuste de mapa
            severity_filter: Lista de severidades seleccionadas
            period_store: Período almacenado en memoria
            
        Returns:
            tuple: Datos para todos los componentes de salida
        """
        logger.info("🔄 Actualizando datos de detecciones...")
        
        # Obtener contexto del callback para identificar el trigger
        ctx = callback_context
        is_initial = not bool(ctx.triggered)
        trig = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

        # ===================================================================
        #                        DETERMINACIÓN DE PERÍODO
        # ===================================================================
        
        # Mapeo de períodos a días
        period_map = {"week": 7, "month": 30, "all": 365}
        
        if trig == "btn-week":
            days = 7
            logger.debug("📅 Período seleccionado: Última semana")
        elif trig == "btn-month":
            days = 30
            logger.debug("📅 Período seleccionado: Último mes")
        elif trig == "btn-all":
            days = 365
            logger.debug("📅 Período seleccionado: Todo el historial")
        elif trig == "btn-refresh":
            # Actualizar datos desde fuente externa
            try:
                sync.download_from_drive()
                logger.info("✅ Datos actualizados desde Drive")
            except Exception as e:
                logger.warning(f"⚠️ Error en actualización automática: {e}")
            days = period_map.get(period_store, 7)
        else:
            # Carga inicial o cambio de filtro: mantener período actual
            days = period_map.get(period_store, 7)

        try:
            # ===================================================================
            #                           CARGA DE DATOS
            # ===================================================================
            
            # Cargar todos los datos históricos para métricas globales
            df_all = sync.load_detections(auto_download=False)
            if df_all is None or not isinstance(df_all, pd.DataFrame):
                df_all = pd.DataFrame()
                logger.warning("⚠️ No se pudieron cargar datos históricos")
            
            # Cargar datos del período específico
            df = sync.get_recent_detections(days=days)
            if df is None or not isinstance(df, pd.DataFrame):
                df = pd.DataFrame()
                logger.warning(f"⚠️ No hay datos para el período de {days} días")

            # ===================================================================
            #                    NORMALIZACIÓN Y FILTRADO
            # ===================================================================
            
            def _norm_sev(s):
                """
                Normaliza valores de severidad al rango 1-5.
                
                Args:
                    s: Serie o valor de severidad
                    
                Returns:
                    Serie normalizada con valores enteros entre 1 y 5
                """
                return pd.to_numeric(s, errors="coerce").fillna(1).round().clip(1, 5)

            # Aplicar normalización y filtros de severidad
            if not df.empty:
                df["_sev"] = _norm_sev(df.get("severity", 1))
                
                # Filtrar por severidades seleccionadas
                if isinstance(severity_filter, (list, tuple)) and len(severity_filter) > 0:
                    df = df[df["_sev"].isin(severity_filter)]
                    logger.debug(f"🔍 Aplicado filtro de severidad: {severity_filter}")

            # ===================================================================
            #                        CÁLCULO DE MÉTRICAS
            # ===================================================================
            
            # Métricas históricas generales
            total_historical = len(df_all)
            
            # Detecciones recientes (últimas 24h)
            ts_all = pd.to_datetime(df_all.get("timestamp"), errors="coerce")
            recent_24h = (ts_all > (datetime.now() - timedelta(days=1))).sum() if len(ts_all) else 0
            
            # Métricas de severidad del período actual
            avg_sev = float(pd.to_numeric(df.get("_sev"), errors="coerce").mean()) if not df.empty else 0.0
            max_sev = float(pd.to_numeric(df.get("_sev"), errors="coerce").max()) if not df.empty else 0.0

            
            # Calcular tendencia comparando períodos
            trend_curr, trend_prev, trend_delta, trend_pct, trend_icon, trend_color = _compute_period_trend(
                df_all, days, severity_filter=severity_filter
            )
            

            # ===================================================================
            #                       PREPARACIÓN DEL MAPA
            # ===================================================================
            
            # Si el período actual no tiene datos, usar fallback histórico
            if df.empty and not len(df_all) == 0:
                logger.info("📍 Usando datos históricos para el mapa (período sin datos)")
                fallback = df_all.copy()
                fallback["_sev"] = _norm_sev(fallback.get("severity", 1))
                
                # Aplicar mismo filtro de severidad
                if isinstance(severity_filter, (list, tuple)) and len(severity_filter) > 0:
                    fallback = fallback[fallback["_sev"].isin(severity_filter)]
                
                # Limitar a los 300 registros más recientes para rendimiento
                fallback = fallback.sort_values("timestamp", ascending=False).head(300)
                df_for_map = fallback
                fit_requested = True  # Ajustar vista automáticamente
            else:
                df_for_map = df
                # Determinar si se debe ajustar la vista del mapa
                fit_requested = (
                    is_initial or 
                    trig == "btn-fit-bounds" or 
                    trig in ("btn-week", "btn-month", "btn-all", "btn-refresh")
                )

            # Construir capas interactivas de Leaflet
            bounds, children_by_sev = _build_leaflet_layers(
                df=df_for_map,
                selected_severities=set(severity_filter or [1, 2, 3, 4, 5]),
            )
            
            # Solo actualizar bounds si se solicita ajuste
            if not fit_requested:
                bounds = no_update

            # ===================================================================
            #                    VISUALIZACIONES FINALES
            # ===================================================================
            
            # Generar gráfico de evolución temporal (solo barras)
            timeline_fig = _create_timeline(df)


            # Generar visualizaciones adicionales
            severity_dist_fig = _create_severity_distribution(df)
            alert_status = _create_alert_status(df, avg_sev, max_sev)
            
            # Datos para el store
            data_store = {
                'total_historical': total_historical,
                'current_period': len(df),
                'recent_24h': recent_24h,
                'avg_severity': avg_sev,
                'max_severity': max_sev,
                'trend_current': trend_curr,
                'trend_previous': trend_prev,
                'trend_delta': trend_delta,
                'trend_percentage': trend_pct,
                'period_days': days,
                'data_timestamp': datetime.now().isoformat()
            }

            return (
                str(total_historical),
                str(len(df)),
                str(recent_24h),
                f"{avg_sev:.1f}",
                f"{max_sev:.0f}" if max_sev > 0 else "0",
                f"{trend_pct:+.1f}%",
                bounds,
                children_by_sev.get(1, []),
                children_by_sev.get(2, []),
                children_by_sev.get(3, []),
                children_by_sev.get(4, []),
                children_by_sev.get(5, []),
                timeline_fig,
                severity_dist_fig,
                alert_status,
                data_store,
            )

        except Exception as e:
            logger.exception("❌ Error crítico actualizando detecciones")
            
            # Mensaje de error detallado
            err = f"Error procesando datos: {str(e)}"
            
            # Retorno de estado de error para todos los componentes
            error_fig = {
                "data": [], 
                "layout": {
                    "title": "Error en visualización", 
                    "height": 300,
                    "annotations": [{
                        "text": "Error procesando datos",
                        "x": 0.5, "y": 0.5,
                        "showarrow": False
                    }]
                }
            }
            
            error_alert = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Error procesando alertas"
            ], className="text-danger p-3")
            
            return (
                "Error", "Error", "Error", "Error", "Error", "Error",
                no_update, [], [], [], [], [],
                error_fig, error_fig, error_alert, {}
            )
                        


    # ===============================================================================
    #                         CALLBACK DE GESTIÓN DE PERÍODO
    # ===============================================================================
    
    @app.callback(
        Output("detections-period", "data"),
        [
            Input("btn-week", "n_clicks"),
            Input("btn-month", "n_clicks"),
            Input("btn-all", "n_clicks")
        ],
        prevent_initial_call=True,
    )
    def _set_period(week, month, all_):
        """
        Almacena el período temporal seleccionado en el store de datos.
        
        Args:
            week, month, all_: Número de clics en cada botón de período
            
        Returns:
            str: Período seleccionado ('week', 'month', 'all')
        """
        trig = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
        
        if trig == "btn-week":
            logger.debug("📅 Período establecido: semana")
            return "week"
        elif trig == "btn-month":
            logger.debug("📅 Período establecido: mes")
            return "month"
        elif trig == "btn-all":
            logger.debug("📅 Período establecido: todo")
            return "all"
        
        return no_update

    # ===============================================================================
    #                      CALLBACKS DE ESTILO DE BOTONES
    # ===============================================================================
    
    @app.callback(
        [
            Output("btn-week", "className"),
            Output("btn-month", "className"),
            Output("btn-all", "className"),
        ],
        Input("detections-period", "data"),
        prevent_initial_call=False,
    )
    def update_active_period_button(current_period):
        """
        Actualiza las clases CSS de los botones de período para mostrar cuál está activo.
        
        Args:
            current_period (str): Período actualmente seleccionado
            
        Returns:
            tuple: Clases CSS para cada botón (week, month, all)
        """
        base_class = "period-btn me-3 mb-2"
        active_class = "period-btn me-3 mb-2 active"
        
        week_class = active_class if current_period == "week" else base_class
        month_class = active_class if current_period == "month" else base_class
        all_class = active_class if current_period == "all" else base_class
        
        return week_class, month_class, all_class

    @app.callback(
        [
            Output("btn-week", "color"),
            Output("btn-week", "outline"),
            Output("btn-month", "color"),
            Output("btn-month", "outline"),
            Output("btn-all", "color"),
            Output("btn-all", "outline"),
        ],
        Input("detections-period", "data"),
        prevent_initial_call=False,
    )
    def update_button_styles(current_period):
        """
        Actualiza el estilo visual de los botones de período (color y outline).
        
        Los botones activos se muestran sólidos, los inactivos con outline.
        
        Args:
            current_period (str): Período actualmente seleccionado
            
        Returns:
            tuple: Configuración de color y outline para cada botón
        """
        # Configuración de estilos
        inactive_color = "primary"
        inactive_outline = True
        active_color = "primary" 
        active_outline = False
        
        # Período por defecto si no hay selección
        period = current_period or "week"
        
        # Aplicar estilos según período activo
        if period == "week":
            return (
                active_color, active_outline,      # btn-week (activo)
                inactive_color, inactive_outline,  # btn-month
                inactive_color, inactive_outline   # btn-all
            )
        elif period == "month":
            return (
                inactive_color, inactive_outline,  # btn-week
                active_color, active_outline,      # btn-month (activo)
                inactive_color, inactive_outline   # btn-all
            )
        elif period == "all":
            return (
                inactive_color, inactive_outline,  # btn-week
                inactive_color, inactive_outline,  # btn-month
                active_color, active_outline       # btn-all (activo)
            )
        else:
            # Fallback: activar botón de semana por defecto
            return (
                active_color, active_outline,      # btn-week (activo por defecto)
                inactive_color, inactive_outline,  # btn-month
                inactive_color, inactive_outline   # btn-all
            )

    # ===============================================================================
    #                        CALLBACKS DE ESTADO DE CARGA
    # ===============================================================================
    
    @app.callback(
        Output("detections-busy", "data"),
        [
            Input("btn-week", "n_clicks"),
            Input("btn-month", "n_clicks"),
            Input("btn-all", "n_clicks"),
            Input("btn-refresh", "n_clicks"),
            Input("btn-fit-bounds", "n_clicks"),
            Input("severity-filter", "value"),
        ],
        prevent_initial_call=True
    )
    def _busy_on(_w, _m, _a, _r, _fit, _sev):
        """
        Activa el estado de carga cuando se interactúa con cualquier control.
        
        Returns:
            bool: True para activar indicadores de carga
        """
        return True
    
    @app.callback(
        Output("detections-busy", "data", allow_duplicate=True),
        [
            Input("detections-map", "bounds"),
            Input("severity-1-group", "children"),
            Input("severity-2-group", "children"),
            Input("severity-3-group", "children"),
            Input("severity-4-group", "children"),
            Input("severity-5-group", "children"),
            Input("detections-timeline", "figure"),
        ],
        prevent_initial_call=True
    )
    def _busy_off(*_):
        """
        Desactiva el estado de carga cuando todos los componentes están actualizados.
        
        Returns:
            bool: False para desactivar indicadores de carga
        """
        return False
    
    @app.callback(
        [
            Output("global-loading-modal", "is_open"),
            Output("map-loading-overlay", "style"),
        ],
        Input("detections-busy", "data"),
        State("map-loading-overlay", "style"),
        prevent_initial_call=True
    )
    def _toggle_loaders(is_busy, overlay_style):
        """
        Controla la visibilidad de los indicadores de carga (modal y overlay).
        
        Args:
            is_busy (bool): Estado de carga actual
            overlay_style (dict): Estilos actuales del overlay
            
        Returns:
            tuple: Estado del modal y estilos del overlay actualizados
        """
        style = dict(overlay_style or {})
        style["display"] = "flex" if is_busy else "none"
        return bool(is_busy), style


    logger.info("✅ Todos los callbacks de detecciones registrados exitosamente")


# ===============================================================================
#                           FUNCIONES DE ANÁLISIS
# ===============================================================================




def _create_empty_timeline():
    """
    Crea gráfico temporal vacío con mensaje informativo.
    
    Returns:
        dict: Configuración de Plotly para gráfico vacío
    """
    return {
        "data": [],
        "layout": {
            "title": "📈 Evolución Temporal de Detecciones",
            "annotations": [
                {
                    "text": "No hay datos temporales disponibles<br><small>El gráfico se actualizará con nuevas detecciones</small>",
                    "xref": "paper", "yref": "paper",
                    "x": 0.5, "y": 0.5, 
                    "showarrow": False,
                    "font": {"size": 16, "color": "#666"}
                }
            ],
            "height": 400,
            "showlegend": False,
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)"
        }
    }

def _create_empty_table():
    """
    Crea tabla vacía con mensaje informativo y consejos de uso.
    
    Returns:
        html.Div: Componente con mensaje y consejos para estado sin datos
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-table fa-3x text-muted mb-3"),
            html.H5("📋 No hay detecciones registradas", 
                   className="text-muted"),
            html.P(
                "Las detecciones aparecerán aquí cuando se reporten a través del bot de Telegram", 
                className="text-muted"
            ),
            dbc.Alert([
                html.I(className="fas fa-telegram-plane me-2"),
                "💡 ",
                html.Strong("Consejo:"),
                " Usa el bot de Telegram para reportar detecciones desde el campo"
            ], color="info", className="mt-3")
        ], className="text-center p-4")
    ])


# ===============================================================================
#                        FUNCIONES DE VISUALIZACIÓN
# ===============================================================================

def _create_severity_indicators(detections_data):
    """
    Crea indicadores visuales profesionales para distribución de severidad.
    
    Genera tarjetas interactivas que muestran:
    • Distribución por niveles de severidad (1-5)
    • Porcentajes y conteos
    • Indicadores visuales con colores temáticos
    • Barras de progreso animadas
    
    Args:
        detections_data (pd.DataFrame): Datos de detecciones a procesar
        
    Returns:
        html.Div: Componente con tarjetas de indicadores de severidad
    """
    try:
        # Validar datos de entrada
        if len(detections_data) == 0:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-chart-bar fa-3x text-muted mb-3"),
                    html.H5("Sin datos de severidad disponibles", 
                           className="text-muted mb-2"),
                    html.P(
                        "Los indicadores aparecerán cuando se registren detecciones", 
                        className="text-muted small mb-3"
                    ),
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "💡 Los datos se actualizan automáticamente cuando el bot de Telegram recibe reportes"
                    ], color="info", className="small")
                ], className="text-center py-4")
            ])
        
        # Extraer datos de severidad (priorizar columna normalizada)
        if "_sev" in detections_data.columns:
            series = pd.to_numeric(detections_data["_sev"], errors="coerce")
        else:
            series = pd.to_numeric(
                detections_data.get('severity', pd.Series(dtype=float)), 
                errors="coerce"
            )

        # Calcular distribución por severidad
        severity_counts = series.value_counts().sort_index()
        total_detections = len(detections_data)

        # Configuración de colores y etiquetas por severidad
        severity_colors = {
            1: "#4CAF50",  # Verde - Muy baja
            2: "#8BC34A",  # Verde claro - Baja  
            3: "#FF9800",  # Naranja - Moderada
            4: "#F44336",  # Rojo - Alta
            5: "#9C27B0"   # Morado - Muy alta
        }
        
        severity_labels = {
            1: "Muy Baja",
            2: "Baja", 
            3: "Moderada",
            4: "Alta",
            5: "Muy Alta"
        }

        # Validar que hay datos para procesar
        if total_detections == 0:
            return dbc.Alert(
                "No hay detecciones para los filtros actuales.", 
                color="warning"
            )
        
        # Generar tarjetas de indicadores por nivel de severidad
        indicator_cards = []
        for severity in range(1, 6):
            count = severity_counts.get(severity, 0)
            percentage = (count / total_detections * 100) if total_detections > 0 else 0
            color = severity_colors[severity]
            label = severity_labels[severity]
            
            # Seleccionar ícono apropiado según severidad
            icons = {
                1: "fa-leaf",                   # Hoja - muy baja
                2: "fa-seedling",              # Brote - baja
                3: "fa-exclamation",           # Exclamación - moderada
                4: "fa-exclamation-triangle",  # Triángulo - alta
                5: "fa-skull-crossbones"       # Crítico - muy alta
            }
            icon = icons.get(severity, "fa-circle")
            
            # Construir tarjeta individual para cada nivel de severidad
            card = dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Ícono representativo
                        html.Div([
                            html.I(className=f"fas {icon} mb-2", style={
                                'fontSize': '2rem',
                                'color': color
                            })
                        ], className="text-center"),
                        
                        # Contador principal
                        html.H4(str(count), className="text-center mb-1", style={
                            'color': color,
                            'fontWeight': '800',
                            'fontSize': '2.2rem'
                        }),
                        
                        # Nivel de severidad
                        html.P(f"Nivel {severity}", className="text-center mb-1", style={
                            'fontWeight': '600',
                            'fontSize': '0.9rem',
                            'color': '#666'
                        }),
                        
                        # Etiqueta descriptiva
                        html.P(label, className="text-center mb-2", style={
                            'fontSize': '0.8rem',
                            'color': color,
                            'fontWeight': '500'
                        }),
                        
                        # Barra de progreso y porcentaje
                        html.Div([
                            html.Div(style={
                                'height': '4px',
                                'backgroundColor': '#eee',
                                'borderRadius': '2px',
                                'overflow': 'hidden'
                            }, children=[
                                html.Div(style={
                                    'height': '100%',
                                    'backgroundColor': color,
                                    'width': f'{percentage}%',
                                    'transition': 'width 0.5s ease',
                                    'borderRadius': '2px'
                                })
                            ]),
                            html.Small(f"{percentage:.1f}%", 
                                     className="text-muted text-center d-block mt-1")
                        ])
                    ], style={'padding': '1.2rem'})
                ], style={
                    'borderRadius': '12px',
                    'border': f'2px solid {color}30',
                    'boxShadow': '0 3px 10px rgba(0,0,0,0.1)',
                    'background': f'linear-gradient(135deg, white 0%, {color}08 100%)',
                    'transition': 'transform 0.2s ease, box-shadow 0.2s ease'
                }, className="severity-indicator-card")
            ], md=2, sm=6, className="mb-3")
            
            indicator_cards.append(card)
        
        # Ensamblar componente final con resumen
        return html.Div([
            # Fila de tarjetas de indicadores
            dbc.Row(indicator_cards, className="justify-content-center"),
            
            # Separador visual
            html.Hr(className="my-4", style={
                'width': '60%', 
                'margin': '2rem auto'
            }),
            
            # Resumen estadístico
            html.Div([
                html.P([
                    html.Strong(f"Total de detecciones analizadas: {total_detections}"),
                    html.Br(),
                    html.Small([
                        "Severidad promedio: ",
                        html.Strong(
                            f"{series.mean():.1f}/5.0", 
                            style={
                                'color': severity_colors.get(
                                    int(series.mean().round()), '#666'
                                )
                            }
                        )
                    ], className="text-muted")
                ], className="text-center mb-0")
            ])
        ])
        
    except Exception as e:
        logger.error(f"Error creando indicadores de severidad: {e}")
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error procesando indicadores de severidad: {str(e)}"
            ], color="danger")
        ])

def _create_severity_distribution(detections_data):
    """
    Crea un gráfico circular de distribución de severidad.
    """
    try:
        if detections_data is None or len(detections_data) == 0:
            return {
                "data": [],
                "layout": {
                    "annotations": [{
                        "text": "Sin datos<br>para mostrar",
                        "x": 0.5, "y": 0.5,
                        "showarrow": False,
                        "font": {"size": 14, "color": "#666"}
                    }],
                    "showlegend": False,
                    "height": 200,
                    "margin": {"l": 10, "r": 10, "t": 10, "b": 10}
                }
            }

        # Procesar datos de severidad
        df = detections_data.copy()
        if "_sev" not in df.columns:
            df["_sev"] = pd.to_numeric(df.get("severity", 1), errors="coerce").fillna(1).round().clip(1, 5)

        # Contar por severidad
        severity_counts = df["_sev"].value_counts().sort_index()
        
        labels = [f"Nivel {int(sev)}" for sev in severity_counts.index]
        values = severity_counts.values
        colors = [SEVERITY_COLORS.get(int(sev), "#999") for sev in severity_counts.index]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='inside',
            hovertemplate='<b>%{label}</b><br>Detecciones: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            showlegend=True,
            height=200,
            margin={"l": 10, "r": 10, "t": 20, "b": 10},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            )
        )

        return fig

    except Exception as e:
        logger.error(f"Error creando distribución de severidad: {e}")
        return {"data": [], "layout": {"title": "Error en gráfico de severidad"}}


def _create_alert_status(detections_data, avg_severity, max_severity):
    """
    Crea el componente de estado de alertas basado en los datos.
    """
    try:
        if detections_data is None or len(detections_data) == 0:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-shield-alt fa-2x text-success mb-2"),
                    html.H5("SIN ALERTAS", className="text-success"),
                    html.P("No hay detecciones recientes", className="text-muted small")
                ], className="text-center")
            ])

        # Determinar nivel de alerta
        total_detections = len(detections_data)
        high_severity_count = len(detections_data[detections_data.get("_sev", detections_data.get("severity", 1)) >= 4])
        high_severity_pct = (high_severity_count / total_detections) * 100 if total_detections > 0 else 0

        # Lógica de alertas
        if avg_severity >= 4 or high_severity_pct >= 30:
            alert_level = "CRÍTICO"
            alert_color = "danger"
            alert_icon = "fas fa-exclamation-triangle"
            alert_desc = f"{high_severity_count} detecciones de alta severidad"
        elif avg_severity >= 3 or high_severity_pct >= 15:
            alert_level = "ALTO"
            alert_color = "warning"
            alert_icon = "fas fa-exclamation"
            alert_desc = f"Severidad promedio: {avg_severity:.1f}"
        elif avg_severity >= 2:
            alert_level = "MODERADO"
            alert_color = "info"
            alert_icon = "fas fa-info-circle"
            alert_desc = f"{total_detections} detecciones registradas"
        else:
            alert_level = "BAJO"
            alert_color = "success"
            alert_icon = "fas fa-check-circle"
            alert_desc = "Nivel de riesgo controlado"

        return html.Div([
            dbc.Alert([
                html.Div([
                    html.I(className=f"{alert_icon} fa-2x mb-2"),
                    html.H5(f"RIESGO {alert_level}", className="mb-1"),
                    html.P(alert_desc, className="mb-0 small")
                ], className="text-center")
            ], color=alert_color, className="mb-2"),
            
            # Métricas adicionales
            html.Div([
                html.Small([
                    html.Strong("Detalles: "),
                    f"Total: {total_detections} | ",
                    f"Promedio: {avg_severity:.1f} | ",
                    f"Máximo: {max_severity:.0f}"
                ], className="text-muted")
            ], className="text-center")
        ])

    except Exception as e:
        logger.error(f"Error creando estado de alertas: {e}")
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Error calculando alertas"
        ], className="text-danger")


def _create_timeline(detections_data):
    """
    Genera gráfico de barras apiladas mostrando evolución temporal de detecciones.
    
    Características:
    • Barras apiladas por nivel de severidad (1-5)
    • Ancho dinámico según densidad temporal
    • Colores temáticos por severidad
    • Línea de tendencia superpuesta
    • Padding temporal inteligente
    
    Args:
        detections_data (pd.DataFrame): Datos de detecciones con timestamp y severidad
        
    Returns:
        dict: Configuración de figura de Plotly
    """
    try:
        # ===================================================================
        #                        VALIDACIÓN INICIAL
        # ===================================================================
        
        # Estado vacío - retornar gráfico informativo
        if (detections_data is None or 
            len(detections_data) == 0 or 
            "timestamp" not in detections_data.columns):
            return {
                "data": [],
                "layout": {
                    "title": {
                        "text": "📈 Evolución Temporal de Detecciones", 
                        "x": 0.5,
                        "font": {"size": 18, "color": "#2E7D32"}
                    },
                    "annotations": [{
                        "text": "No hay datos temporales disponibles<br><small>El gráfico se actualizará con nuevas detecciones</small>",
                        "xref": "paper", "yref": "paper", 
                        "x": 0.5, "y": 0.5, 
                        "showarrow": False,
                        "font": {"size": 16, "color": "#666"}
                    }],
                    "height": 400, 
                    "showlegend": False,
                    "plot_bgcolor": "rgba(0,0,0,0)", 
                    "paper_bgcolor": "rgba(0,0,0,0)"
                }
            }

        # Preparar y limpiar datos
        df = detections_data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        
        if df.empty:
            return _create_empty_timeline()

        # ===================================================================
        #                    NORMALIZACIÓN DE SEVERIDAD
        # ===================================================================
        
        # Asegurar columna de severidad normalizada (1-5)
        if "_sev" not in df.columns:
            df["_sev"] = (
                pd.to_numeric(df.get("severity", 1), errors="coerce")
                .fillna(1)
                .round()
                .clip(1, 5)
            )

        # ===================================================================
        #                      AGRUPACIÓN TEMPORAL
        # ===================================================================
        
        # Agrupación diaria por severidad
        # Nota: Se puede implementar frecuencia adaptativa para rangos grandes
        df["date"] = df["timestamp"].dt.floor("D")
        g = df.groupby(["date", "_sev"]).size().unstack(fill_value=0)

        # Preparar índice temporal ordenado
        g.index = pd.to_datetime(g.index)
        g = g.sort_index()

        # ===================================================================
        #                     CÁLCULO DE ANCHO DINÁMICO
        # ===================================================================
        
        # Calcular ancho óptimo de barras según densidad temporal
        dates = g.index
        if len(dates) == 1:
            # Caso especial: una sola fecha
            width_td = pd.Timedelta(days=0.6)  # Ancho fijo para visualización
        else:
            # Calcular espaciado promedio entre fechas
            deltas = pd.Series(dates).diff().dropna()
            min_delta = deltas.min() if not deltas.empty else pd.Timedelta(days=1)
            
            # Aplicar límites para evitar barras extremadamente anchas o estrechas
            width_td = max(pd.Timedelta(hours=12), min_delta * 0.75)
            width_td = min(width_td, pd.Timedelta(days=7))
        
        # Convertir a milisegundos para Plotly
        width_ms = width_td / pd.Timedelta(milliseconds=1)
        bar_width = [float(width_ms)] * len(dates)

        # ===================================================================
        #                  CONFIGURACIÓN VISUAL
        # ===================================================================
        
        # Colores y etiquetas por severidad
        severity_colors = {
            1: "#4CAF50",  # Verde - Muy baja
            2: "#8BC34A",  # Verde claro - Baja
            3: "#FF9800",  # Naranja - Moderada
            4: "#F44336",  # Rojo - Alta
            5: "#9C27B0"   # Morado - Muy alta
        }
        
        severity_labels = {
            1: "Muy Baja", 2: "Baja", 3: "Moderada", 
            4: "Alta", 5: "Muy Alta"
        }

        # Inicializar figura de Plotly
        fig = go.Figure()

        # ===================================================================
        #                   CONSTRUCCIÓN DE BARRAS APILADAS
        # ===================================================================
        
        # Añadir trazas para cada nivel de severidad (solo barras)
        for sev in range(1, 6):
            if sev in g.columns:
                fig.add_trace(go.Bar(
                    x=dates,
                    y=g[sev],
                    width=bar_width,  # Ancho dinámico calculado
                    name=f'Nivel {sev} ({severity_labels[sev]})',
                    marker_color=severity_colors[sev],
                    hovertemplate=(
                        f"<b>Severidad {sev} - {severity_labels[sev]}</b><br>" +
                        "Fecha: %{x|%Y-%m-%d}<br>" +
                        "Detecciones: %{y}<extra></extra>"
                    )
                ))

        # ===================================================================
        #                     CONFIGURACIÓN DE LAYOUT
        # ===================================================================
        
        fig.update_layout(
            title={
                "text": "📊 Distribución Diaria de Detecciones por Nivel de Severidad",
                "x": 0.5, 
                "font": {"size": 18, "color": "#2E7D32"}
            },
            xaxis_title="Fecha",
            yaxis_title="Número de Detecciones",
            barmode="stack",
            bargap=0.25,            # Separación entre barras
            bargroupgap=0.05,       # Separación entre grupos
            height=450,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Roboto, sans-serif"),
            hovermode="x unified",
            legend=dict(
                orientation="h", 
                yanchor="bottom", y=1.02, 
                xanchor="center", x=0.5,
                bgcolor="rgba(255,255,255,0.8)", 
                bordercolor="rgba(0,0,0,0.1)", 
                borderwidth=1
            ),
            margin={"r": 30, "t": 80, "l": 50, "b": 50},
        )

        # Configuración de ejes
        fig.update_xaxes(
            type="date",
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)",
            showspikes=True, spikethickness=1, spikecolor="#999", spikedash="solid",
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)",
            zeroline=True, zerolinewidth=2, zerolinecolor="rgba(128,128,128,0.5)",
            title_standoff=20
        )

        # ===================================================================
        #                      AJUSTE DE RANGO TEMPORAL
        # ===================================================================
        
        # Aplicar padding para evitar que pocas fechas llenen toda la figura
        pad = width_td * 1.5
        x_min = dates.min() - pad
        x_max = dates.max() + pad
        fig.update_xaxes(range=[x_min, x_max])

        # ===================================================================
        #                        LÍNEA DE TENDENCIA
        # ===================================================================
        
        # Añadir línea de tendencia solo si hay suficientes puntos de datos
        if len(g) > 2:
            total_by_date = g.sum(axis=1)
            fig.add_trace(go.Scatter(
                x=dates, y=total_by_date, 
                mode="lines+markers",
                name="Total diario", 
                line=dict(color="#333", width=3, dash="dot"),
                marker=dict(size=6, color="#333"), 
                yaxis="y2",
                hovertemplate=(
                    "<b>Total del día</b><br>" +
                    "Fecha: %{x|%Y-%m-%d}<br>" +
                    "Total: %{y}<extra></extra>"
                )
            ))
            
            # Configurar eje Y secundario para la tendencia
            fig.update_layout(
                yaxis2=dict(
                    title="Total Diario", 
                    overlaying="y", 
                    side="right",
                    showgrid=False, 
                    tickfont=dict(color="#333")
                )
            )

        return fig

    except Exception as e:
        logger.error(f"Error creando timeline temporal: {e}")
        return {
            "data": [],
            "layout": {
                "title": f"Error creando timeline: {str(e)}",
                "height": 400,
                "annotations": [{
                    "text": f"Error procesando datos temporales<br><small>{str(e)}</small>",
                    "xref": "paper", "yref": "paper", 
                    "x": 0.5, "y": 0.5,
                    "showarrow": False, 
                    "font": {"size": 14, "color": "#d32f2f"}
                }]
            }
        }


def _build_leaflet_layers(df: pd.DataFrame, selected_severities=None):
    """Construye las capas de Leaflet para el mapa de detecciones (popup con imagen y bounds robustos)."""
    children = {sev: [] for sev in [1, 2, 3, 4, 5]}
    bounds = no_update

    # --- helpers ---
    def _to_float(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if not s:
            return None
        s = s.replace("−", "-").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return None

    def _resolve_image_src(row) -> str | None:
        """
        Prioriza la ruta web cacheada por telegram_sync: '/assets/detections/<archivo>'.
        Si no existe, intenta construirla con 'photo_name'.
        """
        pwp = row.get("photo_web_path")
        if isinstance(pwp, str) and pwp.strip():
            return pwp.strip()
        name = row.get("photo_name")
        if isinstance(name, str) and name.strip():
            return f"/assets/detections/{name.strip()}"
        return None

    try:
        # Validaciones iniciales
        if df is None or len(df) == 0:
            logger.info("No data available for map layers")
            return bounds, children

        # Normaliza coordenadas si hiciera falta
        if "latitude" not in df.columns or "longitude" not in df.columns:
            logger.warning("Missing coordinate columns in detections data")
            return bounds, children

        g = df.dropna(subset=["latitude", "longitude"]).copy()
        if len(g) == 0:
            logger.info("No valid coordinates found in detections data")
            return bounds, children

        # Columna de severidad normalizada a [1..5]
        if "_sev" not in g.columns:
            base = g["severity"] if "severity" in g.columns else 1
            g["_sev"] = pd.to_numeric(base, errors="coerce").fillna(1).round().clip(1, 5).astype(int)

        # Filtro de severidades seleccionadas
        sel = set(selected_severities or [1, 2, 3, 4, 5])
        logger.info(f"Building map layers for severities: {sorted(sel)}")

        # Colores (fallback si no existe SEVERITY_COLORS global)
        severity_colors = globals().get(
            "SEVERITY_COLORS",
            {1: "#2e7d32", 2: "#f9a825", 3: "#fb8c00", 4: "#e53935", 5: "#8e24aa"}
        )

        # DF filtrado por severidad para bounds
        g_sel = g[g["_sev"].isin(sel)].copy()

        for sev in [1, 2, 3, 4, 5]:
            if sev not in sel:
                continue
            sub = g[g["_sev"] == sev]
            if len(sub) == 0:
                continue

            markers = []
            for _, row in sub.iterrows():
                try:
                    lat = _to_float(row.get("latitude"))
                    lon = _to_float(row.get("longitude"))
                    if lat is None or lon is None:
                        logger.debug(f"Fila sin lat/lon válidos: lat={row.get('latitude')} lon={row.get('longitude')}")
                        continue

                    loc  = str(row.get("location_name", "Sin ubicación"))[:120]
                    desc = str(row.get("severity_description", "Sin descripción"))[:280]

                    ts = pd.to_datetime(row.get("timestamp", None), errors="coerce")
                    if pd.notna(ts):
                        try:
                            ts_s = ts.tz_convert(None).strftime("%d/%m/%Y %H:%M") if getattr(ts, "tzinfo", None) else ts.strftime("%d/%m/%Y %H:%M")
                        except Exception:
                            ts_s = ts.strftime("%d/%m/%Y %H:%M")
                    else:
                        ts_s = "Fecha no disponible"

                    # Resolver imagen (NO usar prop 'loading' en html.Img; no está soportada en dash 3.2.0)
                    img_src = _resolve_image_src(row)

                    popup_body = [
                        html.H6("🦠 Detección de Repilo",
                                style={'color': severity_colors.get(sev, "#666"), 'marginBottom': '0.35rem'}),
                        html.Hr(style={'margin': '0.35rem 0'}),
                        html.P([html.Strong("Severidad: "), f"{sev}/5"], style={'marginBottom': '0.25rem'}),
                        html.P([html.Strong("Fecha: "), ts_s], style={'marginBottom': '0.25rem'}),
                        html.P([html.Strong("Ubicación: "), loc], style={'marginBottom': '0.25rem'})
                    ]
                    if desc and desc != "Sin descripción":
                        popup_body.append(html.P([html.Strong("Descripción: "), desc], style={'marginBottom': 0}))
                    if img_src:
                        popup_body.append(
                            html.Div(
                                html.Img(
                                    src=img_src,
                                    alt="Foto detección",
                                    style={
                                        'maxWidth': '240px', 'maxHeight': '180px',
                                        'borderRadius': '8px', 'marginTop': '0.5rem',
                                        'border': '1px solid rgba(0,0,0,0.1)'
                                    }
                                ),
                                style={'textAlign': 'center'}
                            )
                        )

                    markers.append(
                        dl.CircleMarker(
                            center=[lat, lon],
                            radius=max(6, min(14, 5 + 2 * sev)),
                            color=severity_colors.get(sev, "#666"),
                            fillColor=severity_colors.get(sev, "#666"),
                            fillOpacity=0.7,
                            weight=2,
                            children=[
                                dl.Tooltip(f"Severidad {sev} - {loc}"),
                                dl.Popup(html.Div(popup_body, style={'maxWidth': '260px'}))
                            ]
                        )
                    )
                except Exception as e:
                    logger.error(f"Error creating marker for row: {e}")
                    continue

            children[sev] = markers
            logger.info(f"Created {len(markers)} markers for severity {sev}")

        # Bounds de los datos filtrados por severidad (si hay puntos)
        if len(g_sel) > 0:
            lat_min, lat_max = g_sel["latitude"].min(), g_sel["latitude"].max()
            lon_min, lon_max = g_sel["longitude"].min(), g_sel["longitude"].max()

            lat_margin = (lat_max - lat_min) * 0.1 if lat_max > lat_min else 0.01
            lon_margin = (lon_max - lon_min) * 0.1 if lon_max > lon_min else 0.01

            bounds = [
                [float(lat_min - lat_margin), float(lon_min - lon_margin)],
                [float(lat_max + lat_margin), float(lon_max + lon_margin)]
            ]
            logger.info(f"Map bounds set to: {bounds}")

        return bounds, children

    except Exception as e:
        logger.exception("Error building Leaflet layers")
        return no_update, {sev: [] for sev in [1, 2, 3, 4, 5]}


def _create_severity_overview(
    df, total_hist, recent_24h, avg_sev, alert_text,
    trend_curr, trend_prev, trend_delta, trend_pct, trend_icon, trend_color
):
    """Crea overview de severidad con diseño profesional mejorado"""
    
    # Calcular distribución por nivel
    severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    if not df.empty and "_sev" in df.columns:
        for sev in [1, 2, 3, 4, 5]:
            severity_counts[sev] = int((df["_sev"] == sev).sum())
    
    total_detections = sum(severity_counts.values())
    
    # Colores para cada nivel de severidad
    severity_colors = {
        1: AGRI_COLORS['severity_1'],
        2: AGRI_COLORS['severity_2'], 
        3: AGRI_COLORS['severity_3'],
        4: AGRI_COLORS['severity_4'],
        5: AGRI_COLORS['severity_5']
    }
    
    # Métricas principales superiores - MÁS ANCHAS
    metrics_row = html.Div([
        dbc.Row([
            dbc.Col([
                _mini_chip(
                    "Total histórico", 
                    total_hist, 
                    "Registros completos",
                    AGRI_COLORS['info']
                )
            ], xs=12, sm=6, md=6, lg=3, className="mb-3"),
            dbc.Col([
                _mini_chip(
                    "Período actual", 
                    trend_curr,
                    f"vs. previo: {trend_delta:+d} ({trend_pct:+.1f}%)",
                    trend_color
                )
            ], xs=12, sm=6, md=6, lg=3, className="mb-3"),
            dbc.Col([
                _mini_chip(
                    "Promedio", 
                    f"{avg_sev:.1f}",
                    "Severidad promedio (período)",
                    AGRI_COLORS['warning']
                )
            ], xs=12, sm=6, md=6, lg=3, className="mb-3"),
            dbc.Col([
                _mini_chip(
                    "Riesgo", 
                    alert_text.split()[0] if alert_text else "BAJO",
                    "Nivel de alerta actual",
                    AGRI_COLORS['danger'] if 'ALTO' in (alert_text or '') else AGRI_COLORS['success']
                )
            ], xs=12, sm=6, md=6, lg=3, className="mb-3")
        ], className="g-3", style={'margin': '0'})
    ], className="metrics-wide-container mb-4", style={'width': '100%', 'maxWidth': '100%'})
    
    # Tarjetas de severidad por nivel (S1-S5) - CENTRADAS
    severity_cards = []
    for sev_level in [1, 2, 3, 4, 5]:
        count = severity_counts[sev_level]
        percentage = (count / total_detections * 100) if total_detections > 0 else 0
        color = severity_colors[sev_level]
        
        # Nombres descriptivos para cada nivel
        level_names = {
            1: "Muy Baja",
            2: "Baja", 
            3: "Moderada",
            4: "Alta",
            5: "Muy Alta"
        }
        
        card = dbc.Col([
            html.Div([
                # Icono y número de severidad
                html.Div([
                    html.I(className="fas fa-microscope", style={
                        'fontSize': '2rem',
                        'color': color,
                        'marginBottom': '0.8rem',
                        'textShadow': '0 2px 4px rgba(0,0,0,0.2)'
                    })
                ], className="text-center"),
                
                # Nivel de severidad prominente
                html.Div([
                    html.H2(f"S{sev_level}", style={
                        'fontSize': '2.5rem',
                        'fontWeight': '800',
                        'color': color,
                        'marginBottom': '0.2rem',
                        'textShadow': '0 3px 6px rgba(0,0,0,0.15)',
                        'fontFamily': '"Roboto", sans-serif'
                    })
                ], className="text-center"),
                
                # Nombre del nivel
                html.Div([
                    html.P(level_names[sev_level], style={
                        'fontSize': '0.85rem',
                        'fontWeight': '700',
                        'color': '#555',
                        'marginBottom': '1rem',
                        'textAlign': 'center',
                        'textTransform': 'uppercase',
                        'letterSpacing': '1px'
                    })
                ]),
                
                # Contador de detecciones
                html.Div([
                    html.H4(str(count), style={
                        'fontSize': '1.8rem',
                        'fontWeight': '700',
                        'color': color,
                        'marginBottom': '0.3rem',
                        'textAlign': 'center'
                    }),
                    html.P(f"{percentage:.1f}%", style={
                        'fontSize': '0.9rem',
                        'color': '#666',
                        'marginBottom': '1rem',
                        'textAlign': 'center',
                        'fontWeight': '600'
                    })
                ]),
                
                # Barra de progreso animada
                html.Div([
                    html.Div(style={
                        'width': f'{min(percentage, 100)}%',
                        'height': '6px',
                        'background': f'linear-gradient(90deg, {color}80, {color})',
                        'borderRadius': '3px',
                        'transition': 'width 1.5s ease',
                        'animation': 'slideInRight 1.5s ease'
                    })
                ], style={
                    'width': '100%',
                    'height': '6px',
                    'background': f'{color}20',
                    'borderRadius': '3px',
                    'marginBottom': '0.8rem'
                }),
                
                # Línea decorativa inferior
                html.Div(style={
                    'width': '50px',
                    'height': '3px',
                    'background': f'linear-gradient(90deg, transparent, {color}, transparent)',
                    'margin': '0 auto',
                    'borderRadius': '2px'
                })
            ], style={
                'background': f'linear-gradient(135deg, white 0%, {color}06 100%)',
                'borderRadius': '20px',
                'padding': '2rem 1.5rem',
                'border': f'3px solid {color}30',
                'boxShadow': '0 8px 25px rgba(0,0,0,0.1)',
                'transition': 'all 0.3s ease',
                'height': '280px',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'space-between',
                'position': 'relative',
                'overflow': 'hidden'
            }, className="severity-detail-card")
        ], xs=12, sm=12, md=6, lg=4, xl=2, className="mb-3")  # Tarjetas más anchas
        
        severity_cards.append(card)
    
    # Contenedor con ancho completo para las tarjetas
    severity_row = html.Div([
        dbc.Row(
            severity_cards,
            className="justify-content-center align-items-stretch g-4",  # Más espacio entre tarjetas
            style={'margin': '0', 'width': '100%'}
        )
    ], className="severity-cards-wide-container mb-4", style={'width': '100%', 'maxWidth': '100%'})
    
    # Footer informativo mejorado
    footer = html.Div([
        html.Div([
            html.I(className="fas fa-info-circle", style={
                'color': AGRI_COLORS['info'],
                'fontSize': '1.2rem',
                'marginRight': '0.8rem'
            }),
            html.Span([
                f"Total de detecciones analizadas (filtros actuales): ",
                html.Strong(f"{total_detections}", style={'color': AGRI_COLORS['primary']}),
                f" • Severidad promedio (período): ",
                html.Strong(f"{avg_sev:.1f}/5.0", style={'color': AGRI_COLORS['warning']})
            ], style={
                'fontSize': '0.9rem',
                'color': '#666',
                'fontWeight': '500'
            })
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'background': f'linear-gradient(90deg, {AGRI_COLORS["info"]}08, {AGRI_COLORS["info"]}15, {AGRI_COLORS["info"]}08)',
            'padding': '1.2rem',
            'borderRadius': '12px',
            'border': f'1px solid {AGRI_COLORS["info"]}25'
        })
    ])
    
    return html.Div([
        metrics_row,
        severity_row,
        footer
    ])

from dash import html

def _hex_to_rgba(hx: str, a: float) -> str:
    """'#RRGGBB' -> 'rgba(r,g,b,a)' con alpha a."""
    hx = (hx or "").lstrip("#")
    if len(hx) != 6:
        # Fallback verde oliva si viene algo raro
        hx = "2E7D32"
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    # clamp alpha
    a = max(0.0, min(1.0, float(a)))
    return f"rgba({r},{g},{b},{a})"

def _resolve_color(color):
    """Acepta nombre de AGRI_COLORS o HEX; devuelve (hex, rgba_tint, rgba_border)."""
    # Paleta por defecto si AGRI_COLORS no existe en el módulo
    _DEFAULT = {
        "primary": "#2E7D32", "secondary": "#689F38",
        "warning": "#FF9800", "danger": "#C62828",
        "info": "#1E88E5", "purple": "#9C27B0"
    }
    palette = globals().get("AGRI_COLORS", _DEFAULT)

    if not color:
        base = palette.get("primary", "#2E7D32")
    elif isinstance(color, str) and not color.startswith("#"):
        base = palette.get(color, palette.get("primary", "#2E7D32"))
    else:
        base = color

    return base, _hex_to_rgba(base, 0.06), _hex_to_rgba(base, 0.28)

def _fmt_value(v):
    try:
        if isinstance(v, (int,)) or (isinstance(v, float) and v.is_integer()):
            return f"{int(v)}"
        if isinstance(v, (float,)):
            return f"{v:.1f}"
        return str(v)
    except Exception:
        return str(v)

def _mini_chip(label, value, sub=None, color=None, *, icon=None, delta=None, progress=None, tooltip=None):
    """
    Tarjeta de métrica compacta y elegante.
    - label: título (ej. 'Período actual')
    - value: número principal
    - sub: texto pequeño secundario
    - color: nombre de AGRI_COLORS o '#RRGGBB'
    - icon: clase FA opcional ('fa-database', etc.). Si no se pasa, mapeo por label
    - delta: variación numérica (mostrará ▲/▼ y color)
    - progress: 0..1 para barra inferior (si None → línea decorativa)
    - tooltip: string opcional (title)
    """
    base_hex, tint_bg, tint_border = _resolve_color(color)

    # icono por defecto según label
    default_icons = {
        "Total histórico": "fa-database",
        "Período actual": "fa-calendar-check",
        "Promedio": "fa-chart-line",
        "Riesgo": "fa-shield-alt",
    }
    icon_cls = icon or default_icons.get(label, "fa-chart-bar")

    # Delta chip (opcional)
    delta_node = None
    if delta is not None:
        try:
            d = float(delta)
            up = d > 0
            down = d < 0
            sym = "▲" if up else ("▼" if down else "—")
            dcol = "#C62828" if up else ("#2E7D32" if down else "#777")
            delta_node = html.Span(
                f"{sym} {abs(d):.0f}",
                style={
                    "fontSize": "0.75rem", "fontWeight": 700, "color": dcol,
                    "padding": "2px 6px", "borderRadius": "999px",
                    "background": "rgba(0,0,0,0.04)", "marginLeft": "6px",
                }
            )
        except Exception:
            pass

    # Barra inferior (progreso) u ornamento
    if progress is not None:
        try:
            p = max(0.0, min(1.0, float(progress))) * 100.0
        except Exception:
            p = 0.0
        bar = html.Div([
            html.Div(style={
                "width": f"{p:.1f}%", "height": "100%", "background": base_hex, "borderRadius": "999px"
            })
        ], style={
            "height": "6px", "background": "rgba(0,0,0,0.06)", "borderRadius": "999px", "overflow": "hidden",
            "margin": "0.25rem auto 0", "width": "75%"
        })
    else:
        bar = html.Div(style={
            "width": "44px", "height": "3px",
            "background": f"linear-gradient(90deg, transparent, {base_hex}, transparent)",
            "margin": "0.25rem auto 0", "borderRadius": "2px"
        })

    return html.Div([
        # SECCIÓN 1: Icono (altura fija)
        html.Div(html.I(className=f"fas {icon_cls}"), style={
            "fontSize": "1.4rem", "color": base_hex, "textAlign": "center",
            "height": "35px", "display": "flex", "alignItems": "center",
            "justifyContent": "center", "flexShrink": "0"
        }),
        # SECCIÓN 2: Valor + delta (altura fija)
        html.Div([
            html.Span(_fmt_value(value), style={
                "fontSize": "2rem", "fontWeight": 800, "color": base_hex,
                "textShadow": "0 1px 2px rgba(0,0,0,0.06)", "lineHeight": 1
            }),
            delta_node
        ], style={
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "gap": "6px", "height": "50px", "flexShrink": "0"
        }),
        # SECCIÓN 3: Label (altura fija)
        html.Div(label.upper(), style={
            "textAlign": "center", "color": "#37474F", "fontWeight": 700,
            "fontSize": "0.8rem", "letterSpacing": "0.04em",
            "height": "32px", "display": "flex", "alignItems": "center", 
            "justifyContent": "center", "flexShrink": "0"
        }),
        # SECCIÓN 4: Subtexto (altura fija)
        html.Div(sub or " ", style={
            "textAlign": "center", "color": "#6B7280", "fontSize": "0.75rem",
            "fontStyle": "italic" if sub else "normal",
            "height": "28px", "display": "flex", "alignItems": "center", 
            "justifyContent": "center", "flexShrink": "0"
        }),
        # SECCIÓN 5: Barra inferior (altura fija)
        html.Div([bar], style={
            "height": "15px", "display": "flex", "alignItems": "center",
            "justifyContent": "center", "flexShrink": "0"
        })
    ],
    title=tooltip or None,
    style={
        # ALTURA COMPLETAMENTE FIJA
        "height": "200px",  # Altura fija total
        "width": "100%",    # Ancho completo del contenedor
        "background": f"linear-gradient(145deg, #fff 0%, {tint_bg} 100%)",
        "border": f"1px solid {tint_border}",
        "borderRadius": "16px",
        "padding": "1.2rem 0.8rem",
        "boxShadow": "0 6px 16px rgba(0,0,0,0.08)",
        "display": "flex", "flexDirection": "column", "justifyContent": "space-between",
        "transition": "transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease",
        "willChange": "transform",
        "overflow": "hidden",
        "position": "relative"
    },
    className="severity-metric-card",
    **({"n_clicks": 0} if False else {})  # placeholder si quisieras hacerla clicable en el futuro
    )



# --- Tendencia vs periodo anterior -----------------------------------------
def _compute_period_trend(df_all: pd.DataFrame, days: int, severity_filter=None):
    if df_all is None or df_all.empty or "timestamp" not in df_all.columns:
        return 0, 0, 0, 0.0, "➖", AGRI_COLORS["secondary"]

    ts  = pd.to_datetime(df_all["timestamp"], errors="coerce")
    now = pd.Timestamp.now()
    cur_start  = now - pd.Timedelta(days=days)
    prev_start = now - pd.Timedelta(days=2*days)

    mask_curr = ts >= cur_start
    mask_prev = (ts >= prev_start) & (ts < cur_start)

    # filtro por severidad si se pide
    mask_sev = pd.Series(True, index=df_all.index)
    if severity_filter:
        if "_sev" in df_all.columns:
            sev = pd.to_numeric(df_all["_sev"], errors="coerce")
        elif "severity" in df_all.columns:
            sev = pd.to_numeric(df_all["severity"], errors="coerce")
        else:
            sev = pd.Series(1, index=df_all.index, dtype="float64")
        mask_sev = sev.round().clip(1,5).isin(severity_filter)

    curr  = int((mask_curr & mask_sev).sum())
    prev  = int((mask_prev & mask_sev).sum())
    delta = curr - prev
    pct = (delta / max(prev, 1)) * 100.0

    if   delta > 0: 
        icon, color = "🔺", AGRI_COLORS["danger"]
    elif delta < 0: 
        icon, color = "🔻", AGRI_COLORS["success"]
    else:           
        icon, color = "➖", AGRI_COLORS["secondary"]

    return curr, prev, delta, pct, icon, color



# 1) Añade helpers arriba del archivo (cerca de imports)
def _build_drive_direct_url(value: str) -> str | None:
    """
    Acepta file_id o un share-link de Google Drive y devuelve URL directa (uc?id=...).
    """
    if not value:
        return None
    v = str(value)
    # Si ya es un link "uc?id=" lo devolvemos
    if "://drive.google.com/uc?id=" in v:
        return v
    # Extraer id de share links comunes
    # https://drive.google.com/file/d/<FILEID>/view?usp=sharing  -> FILEID
    import re
    m = re.search(r"/d/([a-zA-Z0-9_-]{10,})/", v)
    if m:
        return f"https://drive.google.com/uc?id={m.group(1)}"
    # Si parece un file_id directamente (longitud típica >= 16)
    if len(v) >= 16 and "/" not in v and "http" not in v:
        return f"https://drive.google.com/uc?id={v}"
    return None


def _to_float(v):
    """Convierte strings con coma decimal y/o ‘−’ unicode a float. Devuelve None si no es convertible."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    # normalizar separadores y signo menos unicode
    s = s.replace("−", "-").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None