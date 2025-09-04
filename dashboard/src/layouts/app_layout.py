"""
Layout principal del dashboard agrícola
Separado del main.py para mejor organización
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from src.app.app_config import AGRI_THEME, DASHBOARD_TABS, get_tab_style, get_card_style

def create_dashboard_header():
    """
    Crea el header principal del dashboard con branding agrícola profesional
    
    Returns:
        html.Div: Componente header
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(
                        className="fas fa-seedling", 
                        style={
                            'fontSize': '3rem',
                            'color': AGRI_THEME['colors']['primary'],
                            'marginBottom': '1rem'
                        }
                    ),
                    html.H1(
                        "Dashboard Agrícola Inteligente",
                        style={
                            'color': AGRI_THEME['colors']['primary'],
                            'fontWeight': '700',
                            'fontSize': AGRI_THEME['fonts']['sizes']['display'],
                            'fontFamily': AGRI_THEME['fonts']['primary'],
                            'marginBottom': '0.5rem',
                            'lineHeight': '1.2'
                        }
                    ),
                    html.P(
                        "Sistema de Monitoreo y Análisis para Olivicultura",
                        style={
                            'fontSize': AGRI_THEME['fonts']['sizes']['lg'],
                            'color': AGRI_THEME['colors']['text_secondary'],
                            'fontWeight': '500',
                            'marginBottom': '0.25rem'
                        }
                    ),
                    html.P(
                        "Benalúa, Granada • TFM Master en Ciencia de Datos • UGR",
                        style={
                            'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
                            'color': AGRI_THEME['colors']['text_secondary'],
                            'opacity': '0.8',
                            'marginBottom': '0'
                        }
                    )
                ], style={'textAlign': 'center'})
            ], width=12)
        ]),
        
    ], style={
        **get_card_style(),
        'background': f'linear-gradient(135deg, {AGRI_THEME["colors"]["bg_card"]} 0%, {AGRI_THEME["colors"]["bg_light"]} 100%)',
        'padding': '2rem',
        'marginBottom': '2rem',
        'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}'
    }, className="shadow-agri")

def create_navigation_tabs():
    """
    Crea la navegación con tabs profesionales y user-friendly
    
    Returns:
        html.Div: Componente de navegación con tabs mejoradas
    """
    tab_styles = get_tab_style()
    
    # Definir tabs con información más clara para agricultores
    tabs_info = [
        {
            'label': 'Histórico Meteorológico',
            'icon': 'fas fa-chart-line',
            'value': 'historico',
            'description': 'Análisis de temperatura, humedad y clima'
        },
        {
            'label': 'Pronóstico del Tiempo',
            'icon': 'fas fa-cloud-sun',
            'value': 'prediccion',
            'description': 'Previsión meteorológica para planificar'
        },
        {
            'label': 'Imágenes Satelitales',
            'icon': 'fas fa-satellite',
            'value': 'datos-satelitales',
            'description': 'Salud y vigor de los cultivos'
        },
        {
            'label': 'Gestión de Fincas',
            'icon': 'fas fa-map-marked-alt',
            'value': 'fincas',
            'description': 'Administrar y analizar parcelas'
        },
        {
            'label': 'Detección de Enfermedades',
            'icon': 'fas fa-bug',
            'value': 'detecciones',
            'description': 'Monitoreo de repilo y otras patologías'
        }
    ]
    
    tabs = dcc.Tabs(
        id="main-tabs",
        children=[
            dcc.Tab(
                label=tab['label'],
                value=tab['value'],
                style=tab_styles['normal'],
                selected_style={**tab_styles['normal'], **tab_styles['selected']}
            ) for tab in tabs_info
        ],
        value="historico",  # Tab por defecto
        style={'marginBottom': '1.5rem'}
    )

    return html.Div([
        # Navegación principal
        html.Div(
            tabs,
            style={
                "position": "sticky", 
                "top": 0, 
                "zIndex": 2000, 
                "backgroundColor": AGRI_THEME['colors']['bg_light'],
                "padding": "1rem 0",
                "borderRadius": "12px",
                "boxShadow": f"0 2px 8px {AGRI_THEME['colors']['shadow']}"
            }
        ),
    ])

def create_main_layout(df=None, kml_geojson=None):
    """
    Crea el layout principal completo del dashboard
    
    Args:
        df: DataFrame con datos meteorológicos (opcional)
        kml_geojson: Datos geoespaciales (opcional)
        
    Returns:
        dbc.Container: Layout principal
    """
    # Crear contenido inicial del layout histórico para que aparezca algo inmediatamente
    try:
        from src.layouts.layout_historico import build_layout_historico_improved
        df_simple = pd.DataFrame(df) if df is not None else pd.DataFrame()
        print("Contenido inicial del layout histórico creado.")
        initial_content = build_layout_historico_improved(df_simple, kml_geojson or {})
    except Exception as e:
        # Fallback si no puede cargar el layout
        initial_content = html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔄 Dashboard Agrícola", className="text-center text-primary mb-3"),
                    html.P("Cargando datos...", className="text-center text-muted"),
                ])
            ])
        ], className="text-center mt-5")

    return dbc.Container([
        # Componente Location para trigger inicial
        dcc.Location(id="url", refresh=False),
        
        # Header principal con diseño profesional
        create_dashboard_header(),
        
        # Navegación con tabs mejoradas
        create_navigation_tabs(),
        
        # Contenido dinámico con contenedor profesional
        html.Div([
            html.Div(
                children=initial_content,
                id="main-content",  # ID usado por callbacks refactorizados
                style={
                    'minHeight': '500px',
                    'backgroundColor': AGRI_THEME['colors']['bg_card'],
                    'borderRadius': '12px',
                    'padding': '1.5rem',
                    'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}',
                    'boxShadow': f'0 2px 8px {AGRI_THEME["colors"]["shadow"]}'
                }
            )
        ], style={'marginBottom': '2rem'}),
        
        # Stores para datos (compatible con callbacks refactorizados)
        dcc.Store(
            id='weather-data', 
            data=df.to_dict('records') if (df is not None and not df.empty) else []
        ),
        dcc.Store(
            id='kml-data', 
            data=kml_geojson if kml_geojson is not None else {}
        ),
        
        # Footer mejorado
        create_dashboard_footer()
        
    ], fluid=True, className="main-container", style={
        'backgroundColor': AGRI_THEME['colors']['bg_light'],
        'minHeight': '100vh',
        'fontFamily': AGRI_THEME['fonts']['primary']
    })

def create_dashboard_footer():
    """
    Crea footer informativo y profesional del dashboard
    
    Returns:
        html.Div: Componente footer
    """
    return html.Div([
        # Información principal del proyecto
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-graduation-cap", style={
                        'fontSize': '1.5rem', 
                        'color': AGRI_THEME['colors']['primary'],
                        'marginBottom': '0.5rem'
                    }),
                    html.H6(
                        "Trabajo Final de Máster",
                        style={
                            'color': AGRI_THEME['colors']['primary'],
                            'fontWeight': '600',
                            'marginBottom': '0.25rem',
                            'fontFamily': AGRI_THEME['fonts']['primary']
                        }
                    ),
                    html.P([
                        "Master en Ciencia de Datos",
                        html.Br(),
                        "Universidad de Granada",
                        html.Br(),
                        "Curso 2024-2025"
                    ], style={
                        'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
                        'color': AGRI_THEME['colors']['text_secondary'],
                        'marginBottom': '0',
                        'fontFamily': AGRI_THEME['fonts']['primary']
                    })
                ], style={'textAlign': 'center'})
            ], md=3),
            
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-map-marker-alt", style={
                        'fontSize': '1.5rem', 
                        'color': AGRI_THEME['colors']['success'],
                        'marginBottom': '0.5rem'
                    }),
                    html.H6(
                        "Área de Estudio",
                        style={
                            'color': AGRI_THEME['colors']['primary'],
                            'fontWeight': '600',
                            'marginBottom': '0.25rem',
                            'fontFamily': AGRI_THEME['fonts']['primary']
                        }
                    ),
                    html.P([
                        "Benalúa, Granada",
                    ], style={
                        'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
                        'color': AGRI_THEME['colors']['text_secondary'],
                        'marginBottom': '0',
                        'fontFamily': AGRI_THEME['fonts']['primary']
                    })
                ], style={'textAlign': 'center'})
            ], md=3),
            
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-cogs", style={
                        'fontSize': '1.5rem', 
                        'color': AGRI_THEME['colors']['info'],
                        'marginBottom': '0.5rem'
                    }),
                    html.H6(
                        "Tecnologías Utilizadas",
                        style={
                            'color': AGRI_THEME['colors']['primary'],
                            'fontWeight': '600',
                            'marginBottom': '0.25rem',
                            'fontFamily': AGRI_THEME['fonts']['primary']
                        }
                    ),
                    html.P([
                        "Python • Dash • Plotly",
                        html.Br(),
                        "Sentinel-2 • AEMET API",
                        html.Br(),
                        "Telegram Bot • ML"
                    ], style={
                        'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
                        'color': AGRI_THEME['colors']['text_secondary'],
                        'marginBottom': '0',
                        'fontFamily': AGRI_THEME['fonts']['primary']
                    })
                ], style={'textAlign': 'center'})
            ], md=3),
            
        ], className="mb-3"),
        
        # Separador
        html.Hr(style={
            'borderColor': AGRI_THEME['colors']['border_light'],
            'margin': '1.5rem 0 1rem 0',
            'opacity': '0.5'
        }),
        
        # Características destacadas del sistema
        html.Div([
            html.Div([
                html.I(className="fas fa-satellite me-2", style={'color': AGRI_THEME['colors']['success']}),
                html.Span("Datos Satelitales")
            ], className="d-inline-block me-4"),
            html.Div([
                html.I(className="fas fa-cloud-sun me-2", style={'color': AGRI_THEME['colors']['info']}),
                html.Span("Meteorología")
            ], className="d-inline-block me-4"),
            html.Div([
                html.I(className="fas fa-bug me-2", style={'color': AGRI_THEME['colors']['danger']}),
                html.Span("Detección de Enfermedades")
            ], className="d-inline-block me-4"),
            html.Div([
                html.I(className="fas fa-chart-area me-2", style={'color': AGRI_THEME['colors']['primary']}),
                html.Span("Análisis Predictivo")
            ], className="d-inline-block")
        ], style={
            'textAlign': 'center',
            'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
            'color': AGRI_THEME['colors']['text_secondary'],
            'fontFamily': AGRI_THEME['fonts']['primary'],
            'fontWeight': '500'
        }),
        
    ], style={
        **get_card_style(),
        'background': f'linear-gradient(135deg, {AGRI_THEME["colors"]["bg_card"]} 0%, {AGRI_THEME["colors"]["bg_light"]} 100%)',
        'padding': '2rem',
        'marginTop': '3rem',
        'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}'
    })
