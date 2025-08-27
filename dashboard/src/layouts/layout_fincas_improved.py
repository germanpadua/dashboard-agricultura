"""
===============================================================================
                    LAYOUT MEJORADO PARA GESTIÓN DE FINCAS
===============================================================================

Layout profesional optimizado para la administración completa de propiedades
agrícolas. Diseñado con enfoque user-friendly para facilitar el registro,
edición y gestión de fincas por parte de agricultores profesionales.

Características principales:
• Sistema CRUD completo para gestión de propiedades agrícolas
• Mapa interactivo con herramientas de dibujo profesionales
• Formulario inteligente con validación en tiempo real
• Cálculo automático de superficies y perímetros
• Visualización satelital y de calles intercambiable
• Sistema de alertas y notificaciones informativas
• Métricas automáticas de propiedades registradas
• Modales de confirmación para operaciones críticas
• Integración completa con sistema de análisis satelital

Componentes técnicos:
• Herramientas de dibujo avanzadas (polígonos, rectángulos)
• Geolocalización automática y centrado inteligente
• Almacenamiento persistente de geometrías
• Validación de integridad de datos geoespaciales
• Sistema de notificaciones contextual
• Botón de ayuda flotante con guías detalladas

Interfaz de usuario:
• Diseño responsive y adaptativo
• Iconografía profesional y consistente
• Formularios optimizados para entrada rápida
• Feedback visual inmediato para todas las acciones
• Sistema de confirmación para operaciones destructivas

Autor: Sistema de Monitoreo Agrícola
Versión: 2.1 Improved
Última actualización: 2025

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Framework Dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_leaflet as dl

# Configuración de la aplicación
from src.app.app_config import AGRI_THEME, get_card_style, get_button_style

# Componentes UI especializados
from src.components.ui_components_improved import (
    create_section_header,      # Headers de sección estandarizados
    create_metric_card,         # Tarjetas de métricas
    create_alert_card,          # Alertas informativas
    create_data_table_wrapper   # Envoltorio para tablas de datos
)

# ===============================================================================
#                        FUNCIÓN PRINCIPAL DE CONSTRUCCIÓN
# ===============================================================================

def build_layout_fincas_improved():
    """
    Construye el layout completo para gestión avanzada de fincas agrícolas.
    
    Genera una interfaz profesional y comprehensiva que permite a los
    agricultores registrar, editar, visualizar y gestionar sus propiedades
    agrícolas de manera eficiente e intuitiva.
    
    Architecture:
        • Header informativo con contexto del módulo
        • Panel de registro de nuevas fincas con formulario
        • Mapa interactivo con herramientas de dibujo avanzadas
        • Sistema de métricas dinámicas
        • Lista completa de fincas registradas con acciones
        • Modales de confirmación y edición
        • Stores para manejo de estado
        • Sistema de ayuda integrado
        
    Features:
        • Validación en tiempo real de formularios
        • Cálculo automático de superficies
        • Visualización dual (satelital/calles)
        • Operaciones CRUD completas
        • Sistema de notificaciones
        • Ayuda contextual
        
    Returns:
        html.Div: Layout completo del módulo de gestión de fincas
        
    Note:
        Diseñado para trabajar con callbacks en fincas.py para
        funcionalidad completa de gestión.
    """
    return html.Div([
        # ===============================================================
        #                    HEADER Y CONTEXTO
        # ===============================================================
        
        create_section_header(
            title="Gestión de Fincas y Parcelas",
            subtitle="Administre sus propiedades agrícolas, registre nuevas parcelas y analice la información cadastral",
            icon="fas fa-map-marked-alt"
        ),

        # ===============================================================
        #                    SISTEMA DE FEEDBACK
        # ===============================================================
        
        # Contenedor dinámico para mensajes de éxito/error/información
        html.Div(id="finca-feedback", className="mb-3"),

        # ===============================================================
        #                    INFORMACIÓN DEL SISTEMA
        # ===============================================================
        
        html.Div([
            create_alert_card(
                message="Registre sus fincas para poder realizar análisis satelitales específicos. Cada finca guardada aparecerá disponible en la sección de análisis de imágenes satelitales.",
                alert_type="info",
                title="Información del Sistema",
                dismissable=True
            )
        ], className="mb-4"),

        # ===============================================================
        #                    PANEL DE CONTROL PRINCIPAL
        # ===============================================================
        
        dbc.Row([
            # ===== FORMULARIO DE REGISTRO DE NUEVA FINCA =====
            dbc.Col([
                html.Div([
                    create_section_header(
                        title="Registrar Nueva Finca",
                        icon="fas fa-plus-circle"
                    ),
                    html.Div([
                        # ===== CAMPO NOMBRE DE FINCA =====
                        html.Div([
                            html.Label(
                                "Nombre de la Finca",
                                style={
                                    'fontSize': AGRI_THEME['fonts']['sizes']['md'],
                                    'fontWeight': '600',
                                    'color': AGRI_THEME['colors']['primary'],
                                    'marginBottom': '0.5rem',
                                    'fontFamily': AGRI_THEME['fonts']['primary']
                                }
                            ),
                            dcc.Input(
                                id="input-nombre-finca",
                                type="text",
                                placeholder="Ej: Olivar Norte - Picual 2020",
                                style={
                                    'width': '100%',
                                    'fontFamily': AGRI_THEME['fonts']['primary']
                                },
                                className="form-control-agri mb-3"
                            ),
                            html.Small(
                                "Incluya ubicación y características distintivas",
                                style={
                                    'color': AGRI_THEME['colors']['text_secondary'],
                                    'fontSize': AGRI_THEME['fonts']['sizes']['xs']
                                }
                            )
                        ], className="mb-3"),


                        # ===== INFORMACIÓN SOBRE CÁLCULO AUTOMÁTICO =====
                        html.Small(
                            "La superficie se calculará automáticamente al dibujar en el mapa "
                            "(no es necesario introducirla).",
                            style={
                                'color': AGRI_THEME['colors']['text_secondary'],
                                'fontSize': AGRI_THEME['fonts']['sizes']['xs'],
                                'fontStyle': 'italic'
                            }
                        ),

                        # ===== BOTONES DE ACCIÓN =====
                        html.Div([
                            html.Button(
                                [html.I(className="fas fa-save me-2"), "Guardar Finca"],
                                id="btn-guardar-finca",
                                style=get_button_style('primary'),
                                className="me-3 mt-3",
                                disabled=True  # Habilitado por callback cuando hay geometría
                            ),
                            html.Button(
                                [html.I(className="fas fa-redo me-2"), "Limpiar Formulario"],
                                id="btn-limpiar-finca",
                                style=get_button_style('outline'),
                                className="mt-3"
                            )
                        ], style={'textAlign': 'center'})
                    ])
                ], style=get_card_style())
            ], md=4),

            # ===== MAPA INTERACTIVO CON HERRAMIENTAS =====
            dbc.Col([
                html.Div([
                    create_section_header(
                        title="Delimitar Finca en el Mapa",
                        icon="fas fa-map"
                    ),
                    html.Div([
                        # ===== INSTRUCCIONES DE USO =====
                        create_alert_card(
                            message="Use la barra de herramientas del mapa (esquina superior izquierda) para dibujar su finca. Cierre el polígono con doble clic.",
                            alert_type="info",
                            title="Cómo usar el mapa"
                        ),

                        # ===== CONTROLES DE VISUALIZACIÓN =====
                        html.Div([
                            dbc.ButtonGroup([
                                dbc.Button(
                                    [html.I(className="fas fa-map me-2"), "Calles"],
                                    id="btn-vista-calles",
                                    color="primary",
                                    size="sm",
                                    style={'fontSize': '12px'}
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-satellite me-2"), "Satélite"],
                                    id="btn-vista-satelite",
                                    color="outline-primary",
                                    size="sm",
                                    style={'fontSize': '12px'}
                                )
                            ], className="mb-3")
                        ], style={'textAlign': 'center'}),

                        # ===== MAPA INTERACTIVO CON HERRAMIENTAS DE DIBUJO =====
                        html.Div([
                            dl.Map(
                                id="mapa-fincas",
                                children=[
                                    # Capa base cartográfica (OpenStreetMap)
                                    dl.TileLayer(
                                        id="capa-base",
                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                                        attribution="© OpenStreetMap contributors"
                                    ),
                                    
                                    # Capa de fincas existentes (GeoJSON)
                                    dl.GeoJSON(
                                        id="fincas-existentes-layer",
                                        data={"type": "FeatureCollection", "features": []},
                                        options={
                                            "style": {
                                                "color": AGRI_THEME['colors']['success'],
                                                "weight": 3,
                                                "fillOpacity": 0.2,
                                                "fillColor": AGRI_THEME['colors']['success']
                                            }
                                        },
                                        hoverStyle={
                                            "weight": 4,
                                            "color": AGRI_THEME['colors']['primary'],
                                            "fillOpacity": 0.4
                                        }
                                    ),
                                    
                                    # Grupo de herramientas de dibujo y edición
                                    dl.FeatureGroup([
                                        dl.EditControl(
                                            id="finca-draw-control",
                                            position="topleft",
                                            draw={
                                                "polyline": False,      # Deshabilitar líneas
                                                "rectangle": True,      # Habilitar rectángulos
                                                "circle": False,        # Deshabilitar círculos
                                                "circlemarker": False,  # Deshabilitar marcadores circulares
                                                "marker": False,        # Deshabilitar marcadores puntuales
                                                "polygon": {            # Configurar polígonos
                                                    "shapeOptions": {
                                                        "color": AGRI_THEME['colors']['warning'],
                                                        "weight": 3,
                                                        "fillOpacity": 0.3
                                                    }
                                                },
                                            },
                                            edit={"remove": True, "edit": True},  # Permitir edición y eliminación
                                        )
                                    ], id="draw-feature-group"),
                                ],
                                style={
                                    "width": "100%",
                                    "height": "500px",
                                    "borderRadius": "8px",
                                    "border": f"2px solid {AGRI_THEME['colors']['primary']}"
                                },
                                center=[37.2387, -3.6712],  # Coordenadas Benalúa, Almería
                                zoom=14
                            )
                        ], className="map-container")
                    ])
                ], style=get_card_style())
            ], md=8)
        ], className="mb-4"),

        # ===============================================================
        #                    PANEL DE MÉTRICAS DINÁMICAS
        # ===============================================================
        
        # Contenedor de métricas (poblado por callbacks)
        html.Div([
            dbc.Row(id="fincas-metrics", className="mb-4")
        ]),

        # ===============================================================
        #                    LISTA DE FINCAS REGISTRADAS
        # ===============================================================
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-list-alt me-2",
                                   style={'color': AGRI_THEME['colors']['primary']}),
                            html.H4("Fincas Registradas", className="mb-0 d-inline")
                        ])
                    ], style={'backgroundColor': AGRI_THEME['colors']['bg_light']}),
                    dbc.CardBody([
                        html.Div(id="lista-fincas-gestion", children=[
                            dbc.Alert([
                                html.I(className="fas fa-info-circle me-2"),
                                "No hay fincas registradas. Cree su primera finca usando el mapa."
                            ], color="info", className="text-center mb-0")
                        ])
                    ], className="p-3")
                ], style=get_card_style('default'))
            ], md=12)
        ], className="mb-4"),

        # ===============================================================
        #                    STORES DE ESTADO
        # ===============================================================
        
        html.Div([
            # Almacén de datos de fincas
            dcc.Store(id="store-fincas-data"),
            
            # Geometría actualmente dibujada
            dcc.Store(id="store-geometria-actual"),
            
            # Finca seleccionada para operaciones
            dcc.Store(id="store-finca-seleccionada"),
            
            # Modo actual del mapa (calles/satélite)
            dcc.Store(id="store-modo-mapa"),
            
            # Target para operaciones de eliminación
            dcc.Store(id="store-delete-target"),
            
            # Target para operaciones de edición
            dcc.Store(id="store-edit-target"),
            
            # Intervalo de actualización automática
            dcc.Interval(
                id="interval-fincas-update",
                interval=30*1000,  # 30 segundos
                n_intervals=0,
                disabled=True
            )
        ], style={'display': 'none'}),

        # ===============================================================
        #                    MODALES DE INTERACCIÓN
        # ========================================================
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirmar Eliminación")),
            dbc.ModalBody([
                html.Div(id="modal-confirmacion-contenido")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancelar", className="ms-auto", n_clicks=0, color="secondary"),
                dbc.Button("Eliminar", id="modal-confirmar-eliminar", className="ms-2", n_clicks=0, color="danger")
            ])
        ], id="modal-confirmacion-eliminar", is_open=False),

        # Modal de edición de nombre
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-edit me-2"),
                "Editar Nombre de Finca"
            ])),
            dbc.ModalBody([
                html.Div([
                    html.Label("Nuevo nombre:", className="fw-bold mb-2"),
                    dcc.Input(
                        id="input-nuevo-nombre-finca",
                        type="text",
                        placeholder="Introduce el nuevo nombre...",
                        style={'width': '100%'},
                        className="form-control mb-3"
                    ),
                    html.Small("El nombre debe ser descriptivo para facilitar la identificación de la finca.",
                              className="text-muted")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-editar-cancelar", className="ms-auto", n_clicks=0, color="secondary"),
                dbc.Button("Guardar Cambios", id="modal-editar-confirmar", className="ms-2", n_clicks=0, color="primary")
            ])
        ], id="modal-editar-finca", is_open=False),

        # Modal de ayuda
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-question-circle me-2"),
                "Guía de Gestión de Fincas"
            ])),
            dbc.ModalBody([
                html.H6("🗺️ Uso del Mapa", className="text-primary"),
                html.P("• Use los botones 'Calles' y 'Satélite' para cambiar la vista del mapa"),
                html.P("• Haga clic en el icono de polígono para dibujar y delimitar su finca"),
                html.P("• Use 'Eliminar' en la barra de herramientas para borrar el polígono"),
                html.Hr(),
                html.H6("📝 Gestión de Fincas", className="text-success"),
                html.P("• Complete el formulario con los datos de su finca"),
                html.P("• Las fincas aparecerán en la lista después de guardarlas"),
                html.P("• Seleccione fincas existentes para editarlas o eliminarlas"),
                html.Hr(),
                html.H6("📊 Datos Satelitales", className="text-warning"),
                html.P("• Las fincas registradas estarán disponibles en 'Datos Satelitales'"),
                html.P("• Podrá realizar análisis NDVI y detección de anomalías")
            ]),
            dbc.ModalFooter([dbc.Button("Entendido", id="modal-ayuda-cerrar", color="primary")])
        ], id="modal-ayuda-fincas", is_open=False, size="lg"),

        # ===============================================================
        #                    SISTEMA DE AYUDA FLOTANTE
        # ===============================================================
        
        html.Div([
            dbc.Button(
                [html.I(className="fas fa-question-circle")],
                id="btn-ayuda-fincas",
                color="info",
                size="lg",
                className="rounded-circle shadow",
                style={
                    'position': 'fixed', 
                    'bottom': '20px', 
                    'right': '20px',
                    'zIndex': '1000', 
                    'width': '60px', 
                    'height': '60px'
                }
            )
        ])
    ], style={'fontFamily': AGRI_THEME['fonts']['primary'], 'padding': '1rem 0'})

# ===============================================================================
#                           FUNCIÓN DE COMPATIBILIDAD
# ===============================================================================

def build_layout_fincas():
    """
    Función alias para mantener compatibilidad con código legacy.
    
    Proporciona acceso a la función principal bajo el nombre original
    utilizado en versiones anteriores del sistema. Mantiene la
    retrocompatibilidad sin duplicar código.
    
    Returns:
        html.Div: Layout de gestión de fincas (idéntico a función principal)
    """
    return build_layout_fincas_improved()
