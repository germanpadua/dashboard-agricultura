"""
Layout Mejorado para Detecciones de Repilo - Enhanced (consistente con AGRI_THEME)
- Filtros reales (periodo + severidad)
- Métricas sin duplicidad
- Mapa satélite con capas por severidad
- Timeline + Tabla
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_leaflet as dl

from src.app.app_config import AGRI_THEME, get_card_style, get_button_style


# ---------- Pequeños helpers UI ----------

def _card_metric(title, value_id, icon_class, color_key):
    color = AGRI_THEME['colors'][color_key]
    enhanced_style = get_card_style('metric').copy()
    enhanced_style.update({
        'border': 'none',
        'boxShadow': '0 4px 20px rgba(46, 125, 50, 0.08)',
        'transition': 'all 0.3s ease',
        'borderRadius': '12px'
    })
    
    return dbc.Card(
        dbc.CardBody([
            html.Div([html.I(className=icon_class)], className="text-center mb-2",
                     style={'fontSize': '2rem', 'color': color}),
            html.H2(id=value_id, children="—", className="text-center",
                    style={'color': color, 'fontWeight': 800, 'margin': 0}),
            html.Div(title, className="text-center text-muted", style={'marginTop': '0.35rem'})
        ]),
        style=enhanced_style,
        className="severity-metric-card"
    )


def _filters_bar():
    """Barra de filtros con los IDs que usa detecciones.py"""
    btn_style = get_button_style('filter', 'sm')
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                # Botones de período
                dbc.Col([
                    html.Div("Período", className="text-muted", style={'fontWeight': 600, 'marginBottom': '0.35rem'}),
                    dbc.ButtonGroup([
                        dbc.Button("Últ. semana", id="btn-week", style=btn_style),
                        dbc.Button("Últ. mes", id="btn-month", style=btn_style),
                        dbc.Button("Todo", id="btn-all", style=btn_style),
                        dbc.Button([html.I(className="fas fa-sync-alt me-1"), "Actualizar"], id="btn-refresh",
                                   style=get_button_style('outline', 'sm'))
                    ])
                ], md=8),

                # Checklist Severidad
                dbc.Col([
                    html.Div("Filtrar por severidad", className="text-muted", style={'fontWeight': 600, 'marginBottom': '0.35rem'}),
                    dcc.Checklist(
                        id="severity-filter",
                        options=[
                            {'label': html.Span("1", style={'padding': '0 8px', 'borderRadius': '999px', 'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}', 'background': '#E8F5E9'}), 'value': 1},
                            {'label': html.Span("2", style={'padding': '0 8px', 'borderRadius': '999px', 'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}', 'background': '#FFFDE7'}), 'value': 2},
                            {'label': html.Span("3", style={'padding': '0 8px', 'borderRadius': '999px', 'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}', 'background': '#FFF3E0'}), 'value': 3},
                            {'label': html.Span("4", style={'padding': '0 8px', 'borderRadius': '999px', 'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}', 'background': '#FFEBEE'}), 'value': 4},
                            {'label': html.Span("5", style={'padding': '0 8px', 'borderRadius': '999px', 'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}', 'background': '#F3E5F5'}), 'value': 5},
                        ],
                        value=[1, 2, 3, 4, 5],
                        inputStyle={'marginRight': '6px'},
                        labelStyle={'marginRight': '8px'}
                    )
                ], md=4)
            ], className="g-2")
        ]),
        style=get_card_style()
    )




# ---------- Partes del layout ----------

def _header():
    return html.Div([
        html.Div([
            html.I(className="fas fa-microscope me-2",
                   style={'fontSize': '2rem', 'color': AGRI_THEME['colors']['primary']}),
            html.H2("Detecciones de Repilo", className="d-inline",
                    style={'fontWeight': 800, 'color': AGRI_THEME['colors']['primary']})
        ], className="mb-2"),
        html.P("Monitoreo de imágenes de campo recibidas por Telegram: ubicación, fecha y severidad.",
               className="text-muted mb-3")
    ], style=get_card_style())


def _metrics_row():
    return dbc.Row([
        dbc.Col(_card_metric("Total histórico", "total-detections", "fas fa-database", "info"), lg=2, md=6, className="mb-3"),
        dbc.Col(_card_metric("Período actual", "current-detections", "fas fa-calendar-check", "primary"), lg=2, md=6, className="mb-3"),
        dbc.Col(_card_metric("Últimas 24h", "recent-detections", "fas fa-clock", "success"), lg=2, md=6, className="mb-3"),
        dbc.Col(_card_metric("Severidad media", "avg-severity", "fas fa-chart-line", "warning"), lg=2, md=6, className="mb-3"),
        dbc.Col(_card_metric("Nivel máximo", "max-severity", "fas fa-exclamation-triangle", "danger"), lg=2, md=6, className="mb-3"),
        dbc.Col(_card_metric("Tendencia", "trend-indicator", "fas fa-chart-area", "purple"), lg=2, md=6, className="mb-3")
    ])


def _severity_distribution_card():
    """Tarjeta de distribución de severidad con gráfico circular"""
    return dbc.Card(
        dbc.CardBody([
            html.H6([html.I(className="fas fa-chart-pie me-2"), "Distribución por Severidad"],
                    className="mb-2", style={'color': AGRI_THEME['colors']['primary']}),
            dcc.Loading(
                dcc.Graph(id="severity-distribution", style={'height': '200px'},
                          config={'displayModeBar': False}),
                type="circle", color=AGRI_THEME['colors']['primary']
            )
        ]),
        style=get_card_style()
    )

def _alert_status_card():
    """Tarjeta de estado de alertas"""
    return dbc.Card(
        dbc.CardBody([
            html.H6([html.I(className="fas fa-shield-alt me-2"), "Estado de Alertas"],
                    className="mb-3", style={'color': AGRI_THEME['colors']['danger']}),
            html.Div(id="alert-status-content", children=[
                html.Div([
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    "Calculando..."
                ], className="text-muted text-center")
            ])
        ]),
        style=get_card_style()
    )

def _map_block():
    """Mapa satélite + capas por severidad + overlay de carga"""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H6([html.I(className="fas fa-map-marked-alt me-2"), "Mapa de detecciones"],
                        className="mb-0", style={'color': AGRI_THEME['colors']['primary']}),
                dbc.Button([html.I(className="fas fa-expand-arrows-alt me-2"), "Ajustar vista"],
                           id="btn-fit-bounds", size="sm", color="secondary", className="ms-auto")
            ], className="d-flex align-items-center mb-2"),

            html.Div([
                dl.Map(
                    id="detections-map",
                    center=[37.2387, -3.6712], zoom=12,
                    style={"width": "100%", "height": "560px", "borderRadius": "12px",
                           "border": f'1px solid {AGRI_THEME["colors"]["border_light"]}'},
                    children=[
                        dl.TileLayer(
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                            attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics"
                        ),
                        dl.LayersControl(position="topright", children=[
                            dl.Overlay(dl.LayerGroup(id="severity-1-group"), name="🟢 Severidad 1", checked=True),
                            dl.Overlay(dl.LayerGroup(id="severity-2-group"), name="🟡 Severidad 2", checked=True),
                            dl.Overlay(dl.LayerGroup(id="severity-3-group"), name="🟠 Severidad 3", checked=True),
                            dl.Overlay(dl.LayerGroup(id="severity-4-group"), name="🔴 Severidad 4", checked=True),
                            dl.Overlay(dl.LayerGroup(id="severity-5-group"), name="🟣 Severidad 5", checked=True),
                            dl.Overlay(
                                dl.GeoJSON(id="detections-kml", data=None,
                                           options=dict(style=dict(weight=2, color="#FF5722", fillOpacity=0.3)),
                                           zoomToBoundsOnClick=True),
                                name="📊 Datos KML", checked=False
                            )
                        ]),
                    ]
                ),
                # Overlay de carga (lo alterna detecciones.py)
                html.Div(
                    id="map-loading-overlay",
                    children=html.Div([dbc.Spinner(size="lg", color="success"),
                                       html.Div("Actualizando mapa…", className="mt-2 text-muted")],
                                      className="text-center p-3"),
                    style={'display': 'none', 'position': 'absolute', 'inset': 0,
                           'background': 'rgba(255,255,255,0.7)', 'borderRadius': '12px'}
                ),
            ], style={'position': 'relative'})
        ]),
        style=get_card_style()
    )


def _timeline_block():
    return dbc.Card(
        dbc.CardBody([
            html.H6([html.I(className="fas fa-chart-area me-2"), "Evolución temporal"], className="mb-3",
                    style={'color': AGRI_THEME['colors']['secondary']}),
            dcc.Loading(
                dcc.Graph(id="detections-timeline", style={'height': '450px'},
                          config={'displayModeBar': True, 'displaylogo': False}),
                type="circle", color=AGRI_THEME['colors']['secondary']
            )
        ]),
        style=get_card_style('highlight')
    )



# ---------- Layout principal ----------

def build_layout_detecciones_enhanced():
    custom_styles = {
        'detections-dashboard': {
            'background': 'linear-gradient(135deg, #f8fffe 0%, #e8f5e9 100%)',
            'minHeight': '100vh',
            'padding': '1rem 0'
        },
        'metrics-card': {
            'border': 'none',
            'boxShadow': '0 4px 20px rgba(46, 125, 50, 0.08)',
            'transition': 'all 0.3s ease',
            'borderRadius': '12px'
        },
        'severity-card': {
            'background': 'linear-gradient(145deg, #ffffff 0%, rgba(46, 125, 50, 0.02) 100%)',
            'border': '2px solid rgba(46, 125, 50, 0.1)',
            'borderRadius': '16px',
            'transition': 'all 0.3s ease'
        },
        'filters-enhanced': {
            'background': 'linear-gradient(135deg, #ffffff 0%, rgba(46, 125, 50, 0.02) 100%)',
            'border': '1px solid rgba(46, 125, 50, 0.1)',
            'borderRadius': '12px'
        }
    }
    
    return html.Div([
        
        html.Div([
            _header(),
            
            # Filtros mejorados
            html.Div(_filters_bar(), className="mb-4", style=custom_styles['filters-enhanced']),

            # Métricas ampliadas con mejor diseño
            html.Div(_metrics_row(), className="mb-4"),

            # Mapa principal
            html.Div(_map_block(), className="mb-4"),

            # Sección de análisis
            dbc.Row([
                dbc.Col(_timeline_block(), lg=8, className="mb-3"),
                dbc.Col([
                    html.Div(_severity_distribution_card(), className="mb-3", style=custom_styles['severity-card']),
                    html.Div(_alert_status_card())
                ], lg=4, className="mb-3")
            ], className="g-3"),
            
            # Footer informativo
            html.Div([
                html.Hr(className="my-4", style={'border': 'none', 'height': '1px', 'background': 'linear-gradient(90deg, transparent, rgba(46, 125, 50, 0.3), transparent)'}),
                html.Div([
                    html.I(className="fas fa-info-circle me-2", style={'color': AGRI_THEME['colors']['primary']}),
                    html.Span([
                        "Sistema de Detección de Repilo - ",
                        html.Strong("Monitoreo en Tiempo Real"),
                        " | Datos sincronizados con Bot de Telegram"
                    ], className="text-muted small")
                ], className="text-center")
            ])
            
        ], style=custom_styles['detections-dashboard']),

        # Stores y modales
        dcc.Store(id="detections-period", data="all"),
        dcc.Store(id="detections-busy", data=False),
        dcc.Store(id="detections-data", data=None),
        
        # Modal de carga mejorado
        dbc.Modal([
            dbc.ModalBody([
                html.Div([
                    dbc.Spinner(size="lg", color="success"),
                    html.H4("Procesando Detecciones", className="mt-3 mb-2", style={'color': AGRI_THEME['colors']['primary']}),
                    html.P("Actualizando datos desde el sistema de monitoreo...", className="text-muted mb-0"),
                    html.Div([
                        html.I(className="fas fa-microscope me-2"),
                        "Analizando patrones de severidad"
                    ], className="text-success small mt-2")
                ], className="text-center p-3")
            ])
        ], id="global-loading-modal", backdrop="static", keyboard=False, centered=True, size="sm")
    ], style={'fontFamily': AGRI_THEME['fonts']['primary']})
