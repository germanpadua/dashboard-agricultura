"""
Layout mejorado para Predicción Meteorológica
- Selección de municipio
- KPIs de temperaturas actuales
- Gráfico resumen semanal con riesgo de enfermedad  
- Gráfico predicción 48h con zonas de riesgo
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import unicodedata

from src.utils.weather_utils import get_lista_municipios
from src.app.app_config import AGRI_THEME, get_card_style, get_button_style
from src.components.ui_components_improved import (
    create_section_header,
    create_metric_card,
    create_alert_card,
    create_chart_container
)

from src.components.help_modals import (
    create_help_button,
    create_info_modal,
    MODAL_CONTENTS,
)

def normalizar(texto):
    """Normaliza texto para comparación sin acentos"""
    if not isinstance(texto, str):
        return ""
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower()

def create_municipality_selector(default_municipio="Benalua"):
    """Crea el selector de municipio profesional"""
    
    # Obtener lista de municipios
    try:
        municipios = get_lista_municipios()
        options = [{"label": str(m), "value": str(m)} for m in municipios]
        
        # Buscar municipio por defecto
        try:
            default_value = next(o["value"] for o in options if normalizar(o["value"]) == normalizar(default_municipio))
        except StopIteration:
            default_value = options[0]["value"] if options else None
    except Exception:
        options = [{"label": "Benalua", "value": "Benalua"}]
        default_value = "Benalua"
    
    return dbc.Card([
        dbc.CardHeader([

            html.Div([
                    html.I(className="fas fa-map-marker-alt me-2",
                          style={'color': AGRI_THEME['colors']['primary']}),
                    html.H5("Selección de Municipio", className="mb-0 d-inline"),
                ], className="d-flex align-items-center"),
                create_help_button("modal-selector", button_color="outline-primary"),
                create_info_modal(
                    modal_id="modal-selector",
                    title=MODAL_CONTENTS['municipio']['title'],
                    content_sections=MODAL_CONTENTS['municipio']['sections'],
                ),
            ], className="d-flex justify-content-between align-items-center", 
                style={'backgroundColor': AGRI_THEME['colors']['bg_light']}),
        dbc.CardBody([
            dcc.Dropdown(
                id="input-municipio",
                options=options,
                value=default_value,
                searchable=True,
                clearable=False,
                placeholder="Buscar municipio...",
                style={'fontFamily': AGRI_THEME['fonts']['primary']},
                className="mb-2"
            ),
            html.Small(
                "Escriba para buscar o seleccione de la lista desplegable",
                style={
                    'color': AGRI_THEME['colors']['text_secondary'],
                    'fontSize': AGRI_THEME['fonts']['sizes']['xs']
                }
            )
        ])
    ], style=get_card_style('default'))

def create_current_kpis_section():
    """KPIs de temperaturas y condiciones meteorológicas actuales/hoy"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.I(className="fas fa-thermometer-half me-2",
                          style={'color': AGRI_THEME['colors']['primary']}),
                    html.H4("📍 Condiciones Meteorológicas Actuales", className="mb-0 d-inline"),
                    html.Small(" • Datos en tiempo real", className="text-muted ms-2"),
                ], className="d-flex align-items-center"),
                create_help_button("modal-weather", button_color="outline-primary"),
                create_info_modal(
                    modal_id="modal-weather",
                    title=MODAL_CONTENTS['weather']['title'],
                    content_sections=MODAL_CONTENTS['weather']['sections'],
                ),
            ], className="d-flex justify-content-between align-items-center")
        ], style={'backgroundColor': AGRI_THEME['colors']['bg_light']}),
        dbc.CardBody([
            html.Div(id="current-weather-kpis", children=[
                dbc.Row([
                    dbc.Col([
                        create_alert_card(
                            message="🔄 Obteniendo datos meteorológicos más recientes del municipio seleccionado...",
                            alert_type="info",
                            title="Cargando Información"
                        )
                    ], md=12)
                ], className="g-2")
            ])
        ], className="p-3")
    ], style=get_card_style('highlight'))

def create_weekly_forecast_section():
    """Tarjetas de predicción semanal (weather cards) con riesgo de enfermedad"""
    return create_chart_container(
        title="📊 Predicción Diaria - Próximos 7 Días",
        chart_component=html.Div([
            # Contenedor de las tarjetas
            dcc.Loading([
                html.Div(
                    id="pred-semanal-cards",
                    children=html.Div([
                        dbc.Alert(
                            [html.I(className="fas fa-spinner fa-spin me-2"), "Cargando predicción semanal..."],
                            color="info",
                            className="text-center"
                        )
                    ])
                )
            ], type="default"),
        ]),
        subtitle="🦠 Las tarjetas incluyen: temperaturas máx/mín, probabilidad de lluvia, humedad, viento y nivel de riesgo de repilo",
        actions=[
            create_help_button("modal-pred-semanal", button_color="outline-primary"),
            create_info_modal(
                modal_id="modal-pred-semanal",
                title=MODAL_CONTENTS['pred_semanal']['title'],
                content_sections=MODAL_CONTENTS['pred_semanal']['sections'],
            ),
        ],
        
    )

def create_unified_alerts_section():
    """Alertas unificadas: condiciones actuales, 48h y 7 días (estilo alineado con KPIs actuales)."""
    return dbc.Card([
        # Header (mismo estilo que create_current_kpis_section)
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.I(className="fas fa-shield-alt me-2",
                           style={'color': AGRI_THEME['colors']['primary']}),
                    html.H4("🛡️ Alertas", className="mb-0 d-inline"),
                    html.Small(" • Análisis actual, 48h y 7 días", className="text-muted ms-2"),
                ], className="d-flex align-items-center"),
                # Botón + modal de ayuda
                create_help_button("modal-alertas", button_color="outline-warning"),
                create_info_modal(
                    modal_id="modal-alertas",
                    title=MODAL_CONTENTS['alertas']['title'],
                    content_sections=MODAL_CONTENTS['alertas']['sections'],
                ),
            ], className="d-flex justify-content-between align-items-center")
        ], style={'backgroundColor': AGRI_THEME['colors']['bg_light']}),

        # Body
        dbc.CardBody([
            # Tarjetas de estado (3 columnas, responsive)
            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-clock me-2",
                                   style={'color': '#17a2b8'}),
                            html.H6("Condiciones actuales", className="mb-0 fw-bold text-primary"),
                        ], className="d-flex align-items-center mb-2"),
                        html.Div(
                            id="current-risk-status",
                            children=html.Span("Evaluando...", className="text-info small"),
                            role="status", **{"aria-live": "polite"}
                        ),
                    ]), className="h-100", outline=True)
                ], xs=12, md=4, className="mb-3"),

                dbc.Col([
                    dbc.Card(dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-hourglass-half me-2",
                                   style={'color': '#fd7e14'}),
                            html.H6("Próximas 48 horas", className="mb-0 fw-bold text-warning"),
                        ], className="d-flex align-items-center mb-2"),
                        html.Div(
                            id="48h-risk-status",
                            children=html.Span("Evaluando...", className="text-info small"),
                            role="status", **{"aria-live": "polite"}
                        ),
                    ]), className="h-100", outline=True)
                ], xs=12, md=4, className="mb-3"),

                dbc.Col([
                    dbc.Card(dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-calendar-week me-2",
                                   style={'color': '#6f42c1'}),
                            html.H6("Próximos 7 días", className="mb-0 fw-bold", style={'color': '#6f42c1'}),
                        ], className="d-flex align-items-center mb-2"),
                        html.Div(
                            id="weekly-risk-status",
                            children=html.Span("Evaluando...", className="text-info small"),
                            role="status", **{"aria-live": "polite"}
                        ),
                    ]), className="h-100", outline=True, style={'borderColor': '#6f42c1'})
                ], xs=12, md=4, className="mb-3"),
            ], className="g-2 mb-2"),

            # Contenedor de alertas detalladas (placeholder de carga)
            html.Div(id="disease-risk-alerts", children=[
                create_alert_card(
                    message="🔄 Analizando condiciones y evaluando riesgos en todos los períodos...",
                    alert_type="info",
                    title="Cargando evaluación"
                )
            ])
        ], className="p-3")
    ], style=get_card_style('highlight'))




        
        

def create_48h_forecast_section():
    """Gráfico predicción 48h con temperatura, humedad y precipitaciones con indicadores de riesgo"""
    return create_chart_container(
        title="🌡️ Evolución Detallada - Temperatura, Humedad y Precipitaciones",
        chart_component=dcc.Loading([
            dcc.Graph(
                id="forecast-48h-chart",
                style={'height': '650px'},
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'prediccion_48h_repilo',
                        'height': 800,
                        'width': 1200,
                        'scale': 1
                    }
                }
            )
        ], type="default"),
        actions=[
            create_help_button("modal-pred-horaria", button_color="outline-primary"),
            create_info_modal(
                modal_id="modal-pred-horaria",
                title=MODAL_CONTENTS['pred_horaria']['title'],
                content_sections=MODAL_CONTENTS['pred_horaria']['sections'],
            ),
        ],
    )

# ===============================================================================
#                        FUNCIÓN PRINCIPAL DE CONSTRUCCIÓN
# ===============================================================================

def build_layout_prediccion_improved(default_municipio="Benalua"):
    """
    Construye layout completo para predicción meteorológica avanzada con análisis de riesgo.
    
    Genera interfaz profesional y comprehensiva que permite a agricultores
    y técnicos agrícolas acceder a predicciones meteorológicas precisas
    con análisis integrado de riesgo de enfermedades.
    
    Args:
        default_municipio (str): Municipio por defecto para inicializar
                                el sistema ("Benalua" optimizado para caché)
                                
    Returns:
        html.Div: Layout completo del módulo de predicción con todos
                 los componentes necesarios para análisis profesional
                 
    Architecture:
        • Header informativo con contexto del módulo
        • Selector inteligente de municipios
        • Panel de métricas meteorológicas actuales
        • Sección de predicción semanal con tarjetas
        • Sistema de alertas consolidado de riesgo
        • Gráfico detallado de evolución 48h
        • Stores para manejo de estado
        • Modales informativos y de configuración
        • Sistema de notificaciones
        
    Features:
        • Predicciones meteorológicas de alta precisión
        • Análisis científico de riesgo de repilo
        • Recomendaciones contextuales de tratamiento
        • Exportación de datos y reportes
        • Sistema de alertas proactivo
        • Optimización de caché para máxima velocidad
        
    Note:
        Diseñado para trabajar estrechamente con callbacks en
        prediccion.py para funcionalidad completa de predicción.
    """
    
    return html.Div([
        
        # HEADER PRINCIPAL
        create_section_header(
            title="Pronóstico Meteorológico Avanzado",
            subtitle="Predicciones precisas con análisis de riesgo de enfermedades para la planificación agrícola óptima",
            icon="fas fa-cloud-sun",
            actions=[
                create_help_button("modal-prediccion", button_color="outline-primary"),
                create_info_modal(
                    modal_id="modal-prediccion",
                    title=MODAL_CONTENTS['prediccion']['title'],
                    content_sections=MODAL_CONTENTS['prediccion']['sections'],
                ),
            ],
        ),
        
        # FILA 1: CONFIGURACIÓN INICIAL - SELECTOR DE MUNICIPIO
        dbc.Row([
            dbc.Col([
                create_municipality_selector(default_municipio)
            ], md=6),
            dbc.Col([
                # Panel de estado del sistema
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-satellite me-2", style={'color': '#28a745'}),
                            html.Strong("Sistema Activo", className="text-success")
                        ], className="d-flex align-items-center justify-content-center")
                    ], className="py-2")
                ], color="light", outline=True, className="h-100")
            ], md=6)
        ], className="mb-4"),
        
        # FILA 2: CONDICIONES METEOROLÓGICAS ACTUALES
        dbc.Row([
            dbc.Col([
                create_current_kpis_section()
            ], md=12)
        ], className="mb-4"),
        
        # FILA 3: SISTEMA UNIFICADO DE ALERTAS
        create_unified_alerts_section(),
        
        # FILA 4: ANÁLISIS TEMPORAL - PREDICCIONES DETALLADAS
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-line me-2", style={'color': '#007bff'}),
                        "Análisis Temporal Detallado"
                    ], className="text-primary mb-3"),
                    
                    # Tabs para navegar entre vistas (sin contenido interno)
                    dbc.Tabs([
                        dbc.Tab(
                            label="📅 Predicción 7 Días", 
                            tab_id="weekly-tab",
                            active_tab_style={"backgroundColor": "#007bff", "color": "white"}
                        ),
                        dbc.Tab(
                            label="⏰ Evolución 48 Horas", 
                            tab_id="hourly-tab",
                            active_tab_style={"backgroundColor": "#007bff", "color": "white"}
                        )
                    ], id="forecast-tabs", active_tab="weekly-tab", className="mb-3"),
                    
                    # Contenedores persistentes que se muestran/ocultan según tab activa
                    html.Div([
                        create_weekly_forecast_section()
                    ], id="weekly-content", style={'display': 'block'}),
                    
                    html.Div([
                        create_48h_forecast_section()
                    ], id="hourly-content", style={'display': 'none'})
                ])
            ], md=12)
        ], className="mb-4"),
        
        # STORES PARA DATOS
        dcc.Store(id="forecast-data-store"),
        dcc.Store(id="selected-municipality-store"),
        dcc.Store(id="disease-risk-analysis-store"),
        
        # MODALES INFORMATIVOS
        create_risk_guide_modal(),
        create_cache_status_modal(),
        
        # SISTEMA DE NOTIFICACIONES
        html.Div(id="forecast-notifications"),
        
    ], 
    style={
        'fontFamily': AGRI_THEME['fonts']['primary'],
        'backgroundColor': AGRI_THEME['colors']['bg_light'],
        'minHeight': '100vh',
        'padding': '1.5rem'
    })

def create_risk_guide_modal():
    """Modal con guía práctica de manejo de repilo para agricultores"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className="fas fa-leaf me-2", style={'color': '#28a745'}),
            "Guía de Manejo del Repilo - Para Agricultores"
        ])),
        dbc.ModalBody([
            # Tabs para organizar la información
            dbc.Tabs([
                # Tab 1: Identificación
                dbc.Tab(label="🔍 Identificar", tab_id="identify-tab", children=[
                    html.Div([
                        html.H5("¿Cómo reconocer el repilo?", className="text-primary mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.H6("Síntomas iniciales:", className="fw-bold mb-2"),
                                html.Ul([
                                    html.Li("Manchas circulares amarillentas en hojas"),
                                    html.Li("Manchas de 2-10mm de diámetro"),
                                    html.Li("Color que pasa de amarillo a marrón"),
                                    html.Li("Hojas que se vuelven amarillas y caen")
                                ])
                            ], md=6),
                            dbc.Col([
                                html.H6("Síntomas avanzados:", className="fw-bold mb-2"),
                                html.Ul([
                                    html.Li("Defoliación intensa"),
                                    html.Li("Pérdida de hasta 70% de las hojas"),
                                    html.Li("Debilitamiento del árbol"),
                                    html.Li("Reducción de la cosecha")
                                ])
                            ], md=6)
                        ])
                    ], className="mt-3")
                ]),
                
                # Tab 2: Condiciones de riesgo
                dbc.Tab(label="⚠️ Cuándo Actuar", tab_id="risk-tab", children=[
                    html.Div([
                        html.H5("Condiciones que favorecen el repilo", className="text-danger mb-3"),
                        
                        # Alertas por nivel de riesgo
                        dbc.Alert([
                            html.H6([html.I(className="fas fa-thermometer-three-quarters me-2"), "RIESGO EXTREMO"], className="alert-heading text-white mb-2"),
                            html.P("• Temperatura entre 15-20°C", className="mb-1"),
                            html.P("• Humedad superior al 95%", className="mb-1"),
                            html.P("• Presencia de lluvia o rocío", className="mb-1"),
                            html.Strong("🚨 ACCIÓN INMEDIATA: Aplicar tratamiento preventivo")
                        ], color="danger", className="mb-3"),
                        
                        dbc.Alert([
                            html.H6([html.I(className="fas fa-thermometer-half me-2"), "RIESGO ALTO"], className="alert-heading mb-2"),
                            html.P("• Temperatura entre 12-15°C o 20-22°C", className="mb-1"),
                            html.P("• Humedad entre 85-95%", className="mb-1"),
                            html.P("• Varios días consecutivos húmedos", className="mb-1"),
                            html.Strong("⚠️ VIGILANCIA: Preparar tratamiento si persisten condiciones")
                        ], color="warning", className="mb-3")
                    ], className="mt-3")
                ]),
                
                # Tab 3: Tratamientos
                dbc.Tab(label="💊 Tratamientos", tab_id="treatment-tab", children=[
                    html.Div([
                        html.H5("Estrategias de control", className="text-success mb-3"),
                        
                        html.H6("🛡️ Tratamientos Preventivos:", className="fw-bold mb-2"),
                        html.Ul([
                            html.Li([html.Strong("Cobre (oxicloruro/sulfato): "), "2-3 g/L - aplicar antes de períodos lluviosos"]),
                            html.Li([html.Strong("Mezclas cúpricas: "), "Alternar formulaciones para evitar resistencias"]),
                            html.Li([html.Strong("Momento clave: "), "Otoño (octubre-noviembre) e invierno"]),
                            html.Li([html.Strong("Frecuencia: "), "Cada 15-20 días en períodos de riesgo"])
                        ], className="mb-3"),
                        
                        html.H6("🎯 Tratamientos Curativos:", className="fw-bold mb-2"),
                        html.Ul([
                            html.Li([html.Strong("Triazoles: "), "En primeras fases de infección"]),
                            html.Li([html.Strong("Strobirulinas: "), "Sistémicos para casos establecidos"]),
                            html.Li([html.Strong("Importante: "), "Alternar materias activas"])
                        ], className="mb-3"),
                        
                        html.H6("🌿 Medidas Culturales:", className="fw-bold mb-2"),
                        html.Ul([
                            html.Li("Poda para mejorar ventilación"),
                            html.Li("Evitar riego por aspersión"),
                            html.Li("Eliminación de hojas infectadas"),
                            html.Li("Control de malas hierbas")
                        ])
                    ], className="mt-3")
                ]),
                
                # Tab 4: Calendario
                dbc.Tab(label="📅 Calendario", tab_id="calendar-tab", children=[
                    html.Div([
                        html.H5("Calendario de actuaciones", className="text-info mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([html.H6("🍂 OTOÑO", className="mb-0 text-warning")]),
                                    dbc.CardBody([
                                        html.P("• Tratamiento preventivo principal", className="mb-1"),
                                        html.P("• 2-3 aplicaciones con cobre", className="mb-1"),
                                        html.P("• Poda de aireación", className="mb-1")
                                    ])
                                ])
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([html.H6("❄️ INVIERNO", className="mb-0 text-primary")]),
                                    dbc.CardBody([
                                        html.P("• Mantener protección cúprica", className="mb-1"),
                                        html.P("• Limpieza de hojas caídas", className="mb-1"),
                                        html.P("• Evaluación de daños", className="mb-1")
                                    ])
                                ])
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([html.H6("🌸 PRIMAVERA", className="mb-0 text-success")]),
                                    dbc.CardBody([
                                        html.P("• Evaluación de brotación", className="mb-1"),
                                        html.P("• Tratamientos según síntomas", className="mb-1"),
                                        html.P("• Vigilancia intensiva", className="mb-1")
                                    ])
                                ])
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([html.H6("☀️ VERANO", className="mb-0 text-info")]),
                                    dbc.CardBody([
                                        html.P("• Riesgo menor por calor", className="mb-1"),
                                        html.P("• Preparación campaña", className="mb-1"),
                                        html.P("• Mantenimiento general", className="mb-1")
                                    ])
                                ])
                            ], md=3)
                        ])
                    ], className="mt-3")
                ])
            ], id="risk-guide-tabs", active_tab="identify-tab")
        ], style={'maxHeight': '70vh', 'overflowY': 'auto'}),
        dbc.ModalFooter([
            html.Small("Consulte siempre con su técnico de confianza antes de aplicar tratamientos", 
                      className="text-muted me-auto"),
            dbc.Button("Cerrar", id="close-risk-guide", color="primary", n_clicks=0)
        ])
    ], id="risk-guide-modal", size="xl", is_open=False)

def create_cache_status_modal():
    """Modal con información del estado del caché"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className="fas fa-database me-2", style={'color': '#3498db'}),
            "Estado del Sistema de Caché"
        ])),
        dbc.ModalBody([
            html.Div(id="cache-status-content", children=[
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "El sistema de caché optimiza la carga de datos para Benalúa"
                ], color="info")
            ])
        ]),
        dbc.ModalFooter(
            dbc.Button("Cerrar", id="close-cache-modal", className="ms-auto", n_clicks=0)
        )
    ], id="cache-status-modal", size="md", is_open=False)

# Función para backward compatibility
def build_layout_prediccion(default_municipio="Benalua"):
    """Mantiene compatibilidad con el código existente"""
    return build_layout_prediccion_improved(default_municipio)