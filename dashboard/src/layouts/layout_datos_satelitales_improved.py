"""
===============================================================================
                    LAYOUT MEJORADO PARA ANÁLISIS SATELITAL
===============================================================================

Layout profesional optimizado para el análisis de datos satelitales agrícolas.
Diseñado específicamente para trabajar en conjunto con los callbacks del módulo
datos_satelitales.py, proporcionando una interfaz completa y user-friendly.

Características principales:
• Base cartográfica satelital (Esri World Imagery) de alta resolución
• Sistema de controles intuitivos para configuración de análisis
• Mapeo 1:1 de IDs con callbacks para sincronización perfecta
• Visualización avanzada de índices de vegetación (NDVI, OSAVI, NDRE)
• Panel de análisis histórico con animaciones temporales
• Comparación temporal inteligente entre períodos
• Detección automática de anomalías y alertas de cultivo
• Sistema de overlays dinámicos con leyendas interactivas
• Integración completa con datos de fincas registradas

Componentes técnicos:
• Controles de período y selección de área avanzados
• Mapas interactivos con capas especializadas por índice
• KPIs automáticos y métricas de salud de cultivo
• Análisis comparativo entre fechas con visualizaciones
• Sistema de animación temporal para evolución de índices
• Herramientas de exportación y análisis de datos

Integración con callbacks:
• Sincronización perfecta con datos_satelitales.py
• IDs de componentes alineados para callbacks específicos
• Stores compartidos para intercambio de datos eficiente

Autor: Sistema de Monitoreo Agrícola
Versión: 2.1 Enhanced
Última actualización: 2025

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar
import datetime
import logging

# Framework Dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl

# Utilidades del proyecto
from src.utils.finca_store import list_fincas
from src.app.app_config import AGRI_THEME
import config_colormaps as cfg
from utils.api_quota_manager import get_quota_monitor

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                           FUNCIONES AUXILIARES
# ===============================================================================

def _saved_fincas_layer():
    """
    Construye capa GeoJSON con las fincas registradas en el sistema.
    
    Genera una capa de visualización que muestra todas las propiedades
    agrícolas previamente registradas por el usuario, permitiendo su
    selección para análisis satelital específico.
    
    Returns:
        dl.GeoJSON: Componente Dash Leaflet con geometrías de fincas
                   estilizadas según el tema de la aplicación
                   
    Features:
        • Carga automática de fincas desde el sistema de almacenamiento
        • Estilizado consistente con el tema de la aplicación
        • Efectos hover para mejor interacción usuario
        • Manejo robusto de errores en datos malformados
        • Preparación de propiedades para callbacks
    """
    # Obtener lista de fincas del sistema de almacenamiento
    fincas = list_fincas() or []
    features = []
    
    # Procesar cada finca registrada
    for finca in fincas:
        try:
            # Validar estructura de datos básica
            if isinstance(finca, dict) and finca.get("geometry"):
                # Construir feature GeoJSON válido
                feature = {
                    "type": "Feature",
                    "geometry": finca["geometry"],
                    "properties": {
                        **finca.get("properties", {}),
                        "id": finca.get("id")
                    }
                }
                features.append(feature)
                
        except Exception as e:
            # Continuar con siguiente finca si hay error en una específica
            logger.debug(f"Error procesando finca: {e}")
            continue

    # Retornar capa GeoJSON configurada
    return dl.GeoJSON(
        id="saved-fincas-layer",
        data={
            "type": "FeatureCollection", 
            "features": features
        },
        options={
            "style": {
                "color": AGRI_THEME["colors"]["primary"], 
                "weight": 2, 
                "fillOpacity": 0.05
            }
        },
        hoverStyle={
            "weight": 3, 
            "color": AGRI_THEME["colors"]["success"], 
            "fillOpacity": 0.10
        },
        zoomToBounds=False,
    )

def _create_api_quota_monitor():
    """
    Crea componente dinámico de monitoreo de cuota API satelital.
    
    Proporciona información visual sobre el uso de la API de Copernicus,
    mostrando estadísticas de consumo que se actualizan automáticamente.
    
    Returns:
        dbc.Card: Componente visual con información de uso de API
    """
    return html.Div(id="api-quota-monitor-container")

# ===============================================================================
#                        FUNCIÓN PRINCIPAL DE CONSTRUCCIÓN
# ===============================================================================

def build_scientific_satellite_layout():
    """
    Construye el layout científico completo para análisis satelital avanzado.
    
    Genera una interfaz profesional y comprehensiva diseñada específicamente
    para el análisis de datos satelitales agrícolas. La función coordina la
    creación de todos los componentes necesarios para un sistema completo
    de monitoreo satelital.
    
    Architecture:
        • Sistema de controles en dos niveles (básicos y avanzados)
        • Mapas interactivos con múltiples capas especializadas
        • Paneles de análisis temporal y comparativo
        • Sistema de stores para manejo de estado
        • Componentes de animación y visualización histórica
        
    Returns:
        html.Div: Layout completo del módulo satelital con todos los
                 componentes necesarios para análisis profesional
                 
    Note:
        Esta función debe mantenerse sincronizada con los callbacks
        en datos_satelitales.py para garantizar funcionalidad completa.
    """

    # ===================================================================
    #                    PREPARACIÓN DE DATOS BASE
    # ===================================================================
    fincas = list_fincas() or []
    fincas_options = [{"label": "🎯 Análisis temporal (dibujar área)", "value": "temporal"}]
    for f in fincas:
        name = f.get("properties", {}).get("name", "Sin nombre")
        crop = f.get("properties", {}).get("crop_type", "")
        area = f.get("properties", {}).get("area", "")
        label = " ".join([p for p in [f"🌿 " + name, f"({crop})" if crop else "", f"- {area} ha" if area else ""] if p])
        fincas_options.append({"label": label, "value": f.get("id")})

    today = datetime.date.today()
    hist_start = today - datetime.timedelta(days=180)

    colormap_options = [{"label": k.replace("_", " ").title(), "value": k} for k in getattr(cfg, "NDVI_COLORMAPS_DEF", {}).keys()]
    default_cmap = getattr(cfg, "NDVI_COLORMAP", (colormap_options[0]["value"] if colormap_options else "viridis"))

    # ===================================================================
    #                    STORES DE ESTADO COMPARTIDO
    # ===================================================================
    # Configuración de almacenes de estado para intercambio de datos
    # entre componentes y callbacks del sistema satelital
    stores = html.Div([
        # Geometría seleccionada por el usuario (área de análisis)
        dcc.Store(id="selected-geometry", storage_type="memory"),
        
        # Límites geoespaciales para overlays de mapas
        dcc.Store(id="overlay-bounds", storage_type="memory"),
        
        # Resumen estadístico del análisis actual
        dcc.Store(id="analysis-summary", storage_type="memory"),
        
        # Datos NDVI raw para procesamiento
        dcc.Store(id="raw-ndvi-data-store", storage_type="memory"),
        
        # Años de referencia para análisis de anomalías
        dcc.Store(id="reference-years-store", data=[2024, 2023, 2022]),
        
        # Datos históricos agregados
        dcc.Store(id="historical-data-store", storage_type="memory"),
        
        # Frames para animaciones temporales
        dcc.Store(id="anim-frames-store", storage_type="memory"),
        
        # Datos para comparación temporal entre períodos
        dcc.Store(id="comparison-data-store", storage_type="memory"),
        
        # Estados de carga
        dcc.Store(id="satellite-busy", data=False),
    ])

    # ===================================================================
    #                    CONTROLES PRINCIPALES BALANCEADOS
    # ===================================================================
    controls_top = html.Div([
        # Primera fila: Controles principales
        dbc.Row([
            # Selección de área
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-map-marked-alt me-2"), "Seleccionar área de análisis"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    dcc.Dropdown(
                        id="analysis-mode-selector",
                        options=fincas_options,
                        value="temporal",
                        clearable=False,
                        className="mb-2"
                    ),
                    html.Small("Elige una finca registrada o dibuja un polígono en el mapa", 
                              className="text-muted", 
                              style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ]), style={
                    "borderRadius": "12px",
                    "backgroundColor": AGRI_THEME["colors"]["bg_card"],
                    "border": f"1px solid {AGRI_THEME['colors']['border_light']}",
                    "boxShadow": f"0 2px 8px {AGRI_THEME['colors']['shadow']}",
                    "fontFamily": AGRI_THEME["fonts"]["primary"]
                }), md=4, className="mb-3"
            ),
            
            # Período de análisis
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-calendar-alt me-2"), "Período de análisis"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    dcc.DatePickerRange(
                        id="ndvi-date-range",
                        start_date=hist_start,
                        end_date=today,
                        display_format="DD/MM/YYYY",
                        className="mb-2", 
                        style={"width": "100%"}
                    ),
                    html.Small("Rango de fechas para el análisis satelital", 
                              className="text-muted",
                              style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ]), className="satellite-control-card"), md=4, className="mb-3"
            ),
            
            # Botones de acción
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-play me-2"), "Ejecutar análisis"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-satellite me-2"), "Análisis Actual"],
                            id="run-analysis-btn", 
                            color="primary", 
                            className="w-100 mb-2",
                            size="md"
                        )
                    ]),
                ]), className="satellite-control-card"), md=4, className="mb-3"
            ),
        ], className="mb-3"),
        
        # Segunda fila: Años de referencia + Índices + Color
        dbc.Row([
            # Años de referencia para anomalías
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-database me-2"), "Años de referencia para anomalías"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    dcc.Checklist(
                        id="reference-years-list", 
                        options=[], 
                        value=[2024, 2023, 2022], 
                        inline=True, 
                        className="mb-2"
                    ),
                    dbc.InputGroup([
                        dbc.Input(
                            id="reference-year-input", 
                            type="number", 
                            min=2015, 
                            max=today.year,
                            placeholder="Añadir año (ej. 2021)", 
                            debounce=True
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-plus me-1"), "Añadir"], 
                            id="add-reference-year-btn", 
                            color="secondary", 
                            n_clicks=0
                        ),
                    ], className="mb-2"),
                    html.Small("Selecciona años para comparar y detectar anomalías", 
                              className="text-muted",
                              style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ]), className="satellite-control-card"), md=5, className="mb-3"
            ),
            
            # Índices de vegetación
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-leaf me-2"), "Índices de vegetación"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    dcc.Dropdown(
                        id="analysis-index-selector",
                        options=[
                            {"label":"🌱 NDVI (Vigor vegetativo)","value":"NDVI"},
                            {"label":"🌿 OSAVI (Suelo optimizado)","value":"OSAVI"},
                            {"label":"🍃 NDRE (Estrés hídrico)","value":"NDRE"}
                        ],
                        value="NDVI", 
                        clearable=False,
                        className="mb-2"
                    ),
                    dcc.Checklist(
                        id="index-checklist",
                        options=[
                            {"label":"🌱 NDVI","value":"NDVI"},
                            {"label":"🌿 OSAVI","value":"OSAVI"},
                            {"label":"🍃 NDRE","value":"NDRE"}
                        ],
                        value=["NDVI"], 
                        className="mb-2"
                    ),
                    html.Small("Selecciona los índices a calcular", 
                              className="text-muted",
                              style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ]), className="satellite-control-card"), md=4, className="mb-3"
            ),
            
            # Escala de color
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Label([html.I(className="fas fa-palette me-2"), "Escala de color"], 
                             className="fw-bold mb-2",
                             style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    dcc.Dropdown(
                        id="ndvi-colormap-selector",
                        options=colormap_options,
                        value=default_cmap, 
                        clearable=False, 
                        className="mb-2"
                    ),
                    html.Small("Paleta de colores para visualizar los índices", 
                              className="text-muted",
                              style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ]), className="satellite-control-card"), md=3, className="mb-3"
            ),
        ])
    ], className="controls-section mb-4")

    # ===================================================================
    #                    INFORMACIÓN CONTEXTUAL
    # ===================================================================
    controls_refs = dbc.Row([
        dbc.Col(
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Strong("Consejo: "),
                "Los años de referencia te ayudan a detectar anomalías comparando con temporadas anteriores."
            ], color="info", className="mb-0", style={"fontSize": "0.9rem"}), 
            md=12
        )
    ], className="mb-3")

    # ===================================================================
    #                    CONTROLES AVANZADOS COLAPSABLES
    # ===================================================================
    advanced_controls = dbc.Row([
        dbc.Col([
            dbc.Button([
                html.I(className="fas fa-cog me-2"),
                "Configuración Avanzada"
            ], id="toggle-advanced-btn", color="outline-secondary", size="sm"),
            dbc.Collapse([
                dbc.Card(dbc.CardBody([
                    html.P("Configuraciones avanzadas aparecerán aquí", className="text-muted small")
                ]))
            ], id="advanced-controls-collapse", is_open=False)
        ], md=12)
    ], className="mb-3")

    # ===================================================================
    #                    MAPA SATELITAL INTERACTIVO
    # ===================================================================
    # Control de dibujo para definir áreas de análisis
    draw_control = dl.EditControl(
        id="bbox-draw-control",
        position="topleft",
        draw={
            "polyline": False,     # Deshabilitar líneas
            "rectangle": False,    # Deshabilitar rectángulos
            "circle": False,       # Deshabilitar círculos
            "circlemarker": False, # Deshabilitar marcadores circulares
            "marker": False,       # Deshabilitar marcadores puntuales
            "polygon": {
                "shapeOptions": {
                    "color": AGRI_THEME["colors"]["success"], 
                    "weight": 2, 
                    "fillOpacity": 0.05
                }
            },
        },
        edit={"remove": True, "edit": True},  # Permitir edición y eliminación
    )

    map_card = dbc.Card(dbc.CardBody([
        dl.Map(
            id="sat-map",
            center=[37.25, -3.6], zoom=12, preferCanvas=True,
            style={"width": "100%", "height": "560px", "zIndex": 0, "borderRadius": "8px"},
            children=[
                dl.LayersControl(position="topright", children=[
                    dl.BaseLayer(
                        dl.TileLayer(
                            id="base-tile-layer",
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                            attribution="&copy; Esri"
                        ),
                        name="🛰️ Satélite", checked=True
                    ),
                    dl.BaseLayer(
                        dl.TileLayer(
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                            attribution="&copy; OpenStreetMap"
                        ),
                        name="🗺️ Calles", checked=False
                    ),
                    dl.Overlay(_saved_fincas_layer(), name="Fincas guardadas", checked=True),
                    dl.Overlay(
                        dl.GeoJSON(id="selected-finca-overlay",
                                   data={"type":"FeatureCollection","features":[]},
                                   options={"style":{"color": AGRI_THEME["colors"]["warning"], "weight":2, "fillOpacity":0.05}},
                                   zoomToBounds=True),
                        name="🎯 Finca seleccionada", checked=True
                    ),
                    # Overlays raster (los callbacks actualizan url/bounds/opacity)
                    dl.Overlay(dl.ImageOverlay(id="dynamic-ndvi-overlay", url="", bounds=[[0,0],[0,0]], opacity=0), name="🌱 NDVI", checked=True),
                    dl.Overlay(dl.ImageOverlay(id="dynamic-osavi-overlay", url="", bounds=[[0,0],[0,0]], opacity=0), name="🌿 OSAVI", checked=False),
                    dl.Overlay(dl.ImageOverlay(id="dynamic-ndre-overlay", url="", bounds=[[0,0],[0,0]], opacity=0), name="🍃 NDRE", checked=False),
                    dl.Overlay(dl.ImageOverlay(id="anomaly-ndvi-overlay", url="", bounds=[[0,0],[0,0]], opacity=0), name="⚠️ Anomalías NDVI", checked=False),
                ]),
                dl.FeatureGroup([draw_control], id="feature-group"),
            ]
        ),
        # Overlay de carga para el mapa satelital
        html.Div(
            id="satellite-map-loading-overlay",
            children=html.Div([
                dbc.Spinner(size="lg", color="primary"),
                html.Div("Procesando datos satelitales…", className="mt-2 text-muted fw-bold")
            ], className="text-center p-4"),
            style={
                'display': 'none', 
                'position': 'absolute', 
                'inset': 0,
                'background': 'rgba(255,255,255,0.85)', 
                'borderRadius': '8px',
                'zIndex': 1000,
                'alignItems': 'center',
                'justifyContent': 'center'
            }
        ),
        html.Div(id="loading-indicator", className="satellite-loading mt-2"),
    ], style={'position': 'relative'}), className="satellite-map-card")


    # ===================================================================
    #                    SECCIÓN COMPARACIÓN TEMPORAL
    # ===================================================================
    comparison_section = dbc.Card(dbc.CardBody([
        html.H5([html.I(className="fas fa-exchange-alt me-2"), "Comparación Temporal de Índices"], 
                className="fw-bold mb-3",
                style={"color": AGRI_THEME["colors"]["info"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
        
        dbc.Row([
            dbc.Col([
                dbc.Label([html.I(className="fas fa-calendar me-2"), "Período 1 (Referencia)"], 
                         className="fw-bold mb-2",
                         style={"color": AGRI_THEME["colors"]["text_primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                dcc.DatePickerRange(
                    id="comparison-range1",
                    start_date=today - datetime.timedelta(days=37),
                    end_date=today - datetime.timedelta(days=30),
                    display_format="DD/MM/YYYY",
                    style={"width": "100%"}
                ),
                html.Small("Rango de fechas para el primer período", 
                          className="text-muted", 
                          style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
            ], md=3),
            
            dbc.Col([
                dbc.Label([html.I(className="fas fa-calendar-plus me-2"), "Período 2 (Comparación)"], 
                         className="fw-bold mb-2",
                         style={"color": AGRI_THEME["colors"]["text_primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                dcc.DatePickerRange(
                    id="comparison-range2",
                    start_date=today - datetime.timedelta(days=7),
                    end_date=today,
                    display_format="DD/MM/YYYY", 
                    style={"width": "100%"}
                ),
                html.Small("Rango de fechas para el segundo período", 
                          className="text-muted",
                          style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
            ], md=3),
            
            dbc.Col([
                dbc.Label([html.I(className="fas fa-seedling me-2"), "Índices a Comparar"], 
                         className="fw-bold mb-2",
                         style={"color": AGRI_THEME["colors"]["text_primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                dcc.Checklist(
                    id="comparison-indices",
                    options=[
                        {"label": "🌱 NDVI", "value": "NDVI"},
                        {"label": "🌿 OSAVI", "value": "OSAVI"},
                        {"label": "🍃 NDRE", "value": "NDRE"}
                    ],
                    value=["NDVI", "OSAVI"],
                    inline=True,
                    style={"fontFamily": AGRI_THEME["fonts"]["primary"]}
                ),
                html.Small("Elige los índices para el análisis comparativo", 
                          className="text-muted",
                          style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
            ], md=4),
            
            dbc.Col([
                dbc.Label("Acción", className="fw-bold mb-2",
                         style={"color": AGRI_THEME["colors"]["text_primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                html.Div([
                    dbc.Button([html.I(className="fas fa-analytics me-2"), "Comparar"],
                               id="run-comparison-btn", 
                               color="info",
                               style={
                                   "width": "100%",
                                   "borderRadius": "8px",
                                   "fontWeight": "600",
                                   "fontFamily": AGRI_THEME["fonts"]["primary"]
                               }),
                ], className="d-grid")
            ], md=2),
        ], className="g-3 mb-4"),

        # Contenedor para resultados de comparación simplificado
        html.Div(id="comparison-results-section", style={"display": "none"}, children=[
            html.Hr(),
            html.H6([html.I(className="fas fa-chart-line me-2"), "Resultados del Análisis"],
                    className="fw-bold mb-3",
                    style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            
            # KPIs de comparación simplificados
            html.Div(id="comparison-kpis", className="mb-4"),
            
            # Análisis simplificado para agricultores
            html.Div([
                html.H6([html.I(className="fas fa-chart-column me-2"), "¿Cómo ha Cambiado tu Cultivo?"], 
                       className="fw-bold mb-2", 
                       style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                html.P("Análisis comparativo entre dos períodos: qué porcentaje ha mejorado, empeorado o se mantiene igual", 
                      className="small text-muted mb-3",
                      style={"fontFamily": AGRI_THEME["fonts"]["primary"]}),
                html.Div(id="comparison-scatter-chart"),
                html.Div(id="comparison-difference-chart", className="mt-3")
            ], className="mb-3")
        ])
        
    ]), style={
        "borderRadius": "12px", 
        "backgroundColor": AGRI_THEME["colors"]["bg_card"],
        "border": f"1px solid {AGRI_THEME['colors']['border_light']}",
        "boxShadow": f"0 2px 8px {AGRI_THEME['colors']['shadow']}",
        "fontFamily": AGRI_THEME["fonts"]["primary"],
        "marginBottom": "1.5rem"
    })

    # ===================================================================
    #                    PANEL DE ANÁLISIS HISTÓRICO
    # ===================================================================
    historical_panel = dbc.Card(dbc.CardBody([
        html.Div(id="historical-section", style={"display":"block"}, children=[
            # Controles simplificados
            dbc.Row([
                dbc.Col([
                    dbc.Label([html.I(className="fas fa-calendar me-2"), "Período de Análisis"], className="fw-bold mb-2"),
                    dcc.DatePickerRange(
                        id="historical-date-range",
                        start_date=today - datetime.timedelta(days=180),  # 6 meses por defecto
                        end_date=today, 
                        display_format="DD/MM/YYYY",
                        first_day_of_week=1, 
                        className="mb-2"
                    ),
                    html.Small("Selecciona el período para ver cómo ha evolucionado tu cultivo", 
                              className="text-muted")
                ], md=6),
                dbc.Col([
                    dbc.Label([html.I(className="fas fa-chart-line me-2"), "Frecuencia de Análisis"], className="fw-bold mb-2"),
                    dcc.RadioItems(
                        id="historical-frequency",
                        options=[
                            {"label":"📅 Mensual (recomendado)","value":"monthly"},
                            {"label":"📊 Quincenal (más detalle)","value":"fortnight"}
                        ],
                        value="monthly", 
                        className="mb-2"
                    ),
                ], md=6),
            ], className="g-3 mb-4"),
            
            # Botón de acción destacado
            html.Div([
                dbc.Button([
                    html.I(className="fas fa-chart-area me-2"), 
                    "Ver Evolución del Cultivo"
                ], id="compute-historical-btn", 
                   color="primary", 
                   size="lg",
                   className="w-100 mb-3",
                   style={"borderRadius": "12px", "fontWeight": "600"}),
                html.Div(id="historical-controls-help", className="text-center text-muted small")
            ]),

            html.Hr(),

            # Resultados simplificados
            dcc.Loading([
                html.Div(id="historical-kpi-cards", className="mb-4"),
                html.Div(id="historical-charts-container")
            ], type="default", className="mt-3"),

            html.Hr(),

            # ---- Sección de Animación Temporal ----
            html.Div(id="animation-section", style={"display": "none"}, children=[
                html.H6([
                    html.I(className="fas fa-film me-2"), 
                    "Animación Temporal"
                ], className="fw-bold mb-3", 
                   style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-play me-2"), 
                            "Generar Animación"
                        ], id="generate-ndvi-animation-btn", 
                           color="secondary", 
                           className="w-100 mb-3",
                           style={"borderRadius": "8px"}),
                        html.Div(id="anim-helper-text", className="small text-muted text-center")
                    ], md=4),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-play me-2"), 
                            "Reproducir"
                        ], id="anim-play-btn", 
                           color="success", 
                           outline=True,
                           className="w-100 mb-2"),
                    ], md=4),
                ], className="mb-4"),

                # Controles de animación manual
                html.Div(id="manual-anim-container", style={"display": "block"}, children=[
                    dbc.Label("Fotograma", className="small fw-bold"),
                    dcc.Slider(
                        id="anim-slider", 
                        min=0, 
                        max=0, 
                        value=0, 
                        step=1, 
                        tooltip={"placement": "bottom"},
                        className="mb-3"
                    ),
                    html.Div(id="manual-animation-view", className="text-center mb-3"),
                    html.P(id="anim-current-label", className="text-muted small text-center"),
                ]),

                # Interval para animación automática
                dcc.Interval(id="anim-interval", interval=400, n_intervals=0, disabled=True),

                # Resultado de animación
                dcc.Loading(
                    html.Div(id="historical-ndvi-animation", className="mt-3"),
                    type="default"
                ),
            ])
        ])
    ]), className="shadow-sm", style={'border': 'none', 'borderRadius': '12px'})

    # ===================================================================
    #                    HEADER INFORMATIVO PRINCIPAL
    # ===================================================================
    info_header = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4([
                        html.I(className="fas fa-satellite me-3", style={"color": AGRI_THEME["colors"]["primary"]}),
                        "Análisis Satelital de Cultivos"
                    ], className="mb-2", style={"color": AGRI_THEME["colors"]["text_primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
                    html.P([
                        "Monitorea la salud y evolución de tus cultivos usando imágenes satelitales. ",
                        "Los índices de vegetación te ayudan a tomar decisiones informadas sobre riego, fertilización y tratamientos."
                    ], className="mb-0 text-muted", style={"fontFamily": AGRI_THEME["fonts"]["primary"]})
                ], md=8),
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-seedling fa-2x mb-2", style={"color": AGRI_THEME["colors"]["success"]}),
                                html.P("NDVI", className="fw-bold mb-1"),
                                html.Small("Vigor vegetativo", className="text-muted")
                            ], className="text-center")
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-leaf fa-2x mb-2", style={"color": AGRI_THEME["colors"]["info"]}),
                                html.P("OSAVI", className="fw-bold mb-1"),
                                html.Small("Suelo optimizado", className="text-muted")
                            ], className="text-center")
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-spa fa-2x mb-2", style={"color": AGRI_THEME["colors"]["warning"]}),
                                html.P("NDRE", className="fw-bold mb-1"),
                                html.Small("Estrés hídrico", className="text-muted")
                            ], className="text-center")
                        ], md=4)
                    ])
                ], md=4)
            ])
        ])
    ], style={
        "borderRadius": "12px",
        "backgroundColor": AGRI_THEME["colors"]["bg_light"],
        "border": f"1px solid {AGRI_THEME['colors']['border_light']}",
        "boxShadow": f"0 2px 8px {AGRI_THEME['colors']['shadow']}",
        "marginBottom": "1.5rem"
    })

    # ===================================================================
    #                    GUÍA RÁPIDA DE USO
    # ===================================================================
    steps_section = dbc.Card([
        dbc.CardBody([
            html.H5([
                html.I(className="fas fa-rocket me-2"),
                "Guía Rápida"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6([
                            html.Span("1⃣", className="me-2"),
                            "Elige tu parcela"
                        ], className="fw-bold text-primary mb-1"),
                        html.Small("Selecciona una finca o dibuja en el mapa", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H6([
                            html.Span("2⃣", className="me-2"),
                            "Configura fechas"
                        ], className="fw-bold text-info mb-1"),
                        html.Small("Define el período de análisis", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H6([
                            html.Span("3⃣", className="me-2"),
                            "Ejecuta análisis"
                        ], className="fw-bold text-success mb-1"),
                        html.Small("Pulsa 'Análisis Actual'", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H6([
                            html.Span("4⃣", className="me-2"),
                            "Revisa resultados"
                        ], className="fw-bold text-warning mb-1"),
                        html.Small("Mira el estado de tu cultivo", className="text-muted")
                    ])
                ], md=3)
            ])
        ])
    ], style={
        "borderRadius": "12px",
        "backgroundColor": AGRI_THEME["colors"]["bg_light"],
        "border": f"1px solid {AGRI_THEME['colors']['border_light']}",
        "marginBottom": "1.5rem"
    })

    # ===================================================================
    #                    COMPOSICIÓN FINAL DEL LAYOUT
    # ===================================================================
    return html.Div([
        stores,
        info_header,
        steps_section,
        
        # Sección 1: Configuración básica
        html.Div([
            html.H5([
                html.I(className="fas fa-cog me-2"),
                "Configuración del Análisis"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            controls_top,
            advanced_controls,
        ], className="mb-4"),
        
        # Sección 1.5: Monitor de API mejorado
        dbc.Row([
            dbc.Col([
                _create_api_quota_monitor()
            ], lg=6, md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6([
                            html.I(className="fas fa-rocket me-2"),
                            "Sistema Inteligente"
                        ], className="mb-2", style={"color": AGRI_THEME["colors"]["info"]}),
                        html.P([
                            html.I(className="fas fa-check me-1", style={"color": AGRI_THEME["colors"]["success"]}),
                            "Caché automático activado"
                        ], className="mb-1 small"),
                        html.P([
                            html.I(className="fas fa-check me-1", style={"color": AGRI_THEME["colors"]["success"]}),
                            "Resolución optimizada"
                        ], className="mb-1 small"),
                        html.P([
                            html.I(className="fas fa-check me-1", style={"color": AGRI_THEME["colors"]["success"]}),
                            "Minimización de requests"
                        ], className="mb-0 small")
                    ])
                ], color="light", outline=True, style={"borderRadius": "10px"})
            ], lg=6, md=6),
        ], className="mb-4"),
        
        # Sección 2: Mapa y KPIs principales con mejor organización
        html.Div([
            html.H5([
                html.I(className="fas fa-map me-2"),
                "Vista Satelital y Estado del Cultivo"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["primary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            
            # Mapa a ancho completo para mejor visualización
            dbc.Row([
                dbc.Col(map_card, md=12, className="mb-3")
            ]),
            
            # KPIs en fila separada para mejor legibilidad
            html.Div(id="kpi-section", children=[
                html.Div([
                    html.H6([
                        html.I(className="fas fa-chart-bar me-2"), 
                        "Métricas de Salud del Cultivo"
                    ], className="fw-bold mb-3", style={
                        "color": AGRI_THEME["colors"]["secondary"], 
                        "fontFamily": AGRI_THEME["fonts"]["primary"]
                    }),
                    html.Div(id="kpi-cards-container", className="mb-3")
                ])
            ], style={"display":"none"}, className="mb-4")
        ]),
        
        # Sección 3: Gráficos de análisis mejorados
        html.Div([
            html.H5([
                html.I(className="fas fa-chart-area me-2"),
                "Análisis Detallado de los Índices"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["secondary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            html.P([
                "📊 Visualizaciones avanzadas que te ayudan a interpretar el estado de tu cultivo. ",
                "Los histogramas muestran la distribución de valores y las tendencias de cambio."
            ], className="text-muted mb-3", style={"fontFamily": AGRI_THEME["fonts"]["primary"]}),
            html.Div(id="charts-section", children=[
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id="kpi-charts-container")
                    ])
                ], style={
                    "borderRadius": "12px",
                    "backgroundColor": AGRI_THEME["colors"]["bg_card"],
                    "border": f"1px solid {AGRI_THEME['colors']['border_light']}",
                    "boxShadow": f"0 2px 8px {AGRI_THEME['colors']['shadow']}"
                })
            ], style={"display":"none"})
        ], className="mb-4"),
        
        # Sección 4: Comparación temporal simplificada
        html.Div([
            html.H5([
                html.I(className="fas fa-exchange-alt me-2"),
                "Comparar Dos Fechas"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["info"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            html.P([
                "¿Has aplicado algún tratamiento? ¿Quieres ver si las lluvias han ayudado? ",
                "Compara dos fechas para ver si tu cultivo ha mejorado o empeorado."
            ], className="text-muted mb-3", style={"fontFamily": AGRI_THEME["fonts"]["primary"]}),
            comparison_section
        ], className="mb-4"),
        
        # Sección informativa (opcional)
        html.Div([
            controls_refs
        ], className="mb-2"),
        
        # Sección 6: Análisis histórico simplificado
        html.Div([
            html.H5([
                html.I(className="fas fa-chart-line me-2"),
                "Evolución de tu Cultivo"
            ], className="mb-3", style={"color": AGRI_THEME["colors"]["secondary"], "fontFamily": AGRI_THEME["fonts"]["primary"]}),
            html.P([
                "📈 Ve cómo ha cambiado tu cultivo en los últimos meses. ",
                "Identifica las mejores épocas de crecimiento y detecta problemas tempranos."
            ], className="text-muted mb-3", style={"fontFamily": AGRI_THEME["fonts"]["primary"]}),
            dbc.Alert([
                html.I(className="fas fa-lightbulb me-2"),
                html.Strong("Consejo: "),
                "Usa este análisis para planificar tratamientos y evaluar la eficacia de tus prácticas agrícolas."
            ], color="info", className="mb-3"),
            historical_panel
        ]),
        
        # Modal de carga global
        dbc.Modal([
            dbc.ModalBody([
                html.Div([
                    dbc.Spinner(size="lg", color="primary"),
                    html.H5("Procesando análisis satelital…", className="mt-3 text-center"),
                    html.P([
                        "Descargando y procesando imágenes satelitales. ",
                        "Este proceso puede tardar varios segundos."
                    ], className="text-center text-muted")
                ], className="text-center p-3")
            ])
        ], id="satellite-loading-modal", backdrop="static", keyboard=False, centered=True, is_open=False)
        
    ], style={
        'fontFamily': AGRI_THEME['fonts']['primary'], 
        'padding': '1.5rem',
        'backgroundColor': AGRI_THEME['colors']['bg_light'],
        'minHeight': '100vh'
    })
    
# ===============================================================================
#                           FUNCIONES DE COMPATIBILIDAD
# ===============================================================================

def build_layout_datos_satelitales_mejorado():
    """
    Función alias para mantener compatibilidad con código legacy.
    
    Proporciona acceso a la función principal bajo el nombre original
    utilizado en versiones anteriores del sistema. Mantiene la 
    retrocompatibilidad sin duplicar código.
    
    Returns:
        html.Div: Layout satelital completo (idéntico a función principal)
    """
    return build_scientific_satellite_layout()
