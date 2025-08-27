"""
Layout Histórico Mejorado - Diseño Profesional
- Estado meteorológico actual con métricas destacadas
- Selectores avanzados de período y agrupación
- Gráficos principales con zonas de riesgo científicas
- Alertas automáticas de repilo
- Centro de alertas expandido para mejor visibilidad
- Estilos consistentes con el tema agrícola
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from datetime import datetime, timedelta

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

def create_current_weather_section():
    """
    Sección mejorada de estado meteorológico actual
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.I(className="fas fa-cloud-sun me-2",
                          style={'color': AGRI_THEME['colors']['warning'], 'fontSize': '1.3rem'}),
                    html.H4("Estado Meteorológico Actual", className="mb-0 d-inline fw-bold")
                ], className="d-flex align-items-center"),
                html.Div([
                    html.Small(
                        "Última actualización: hace 15 minutos",
                        className="text-muted",
                        style={'fontSize': '0.8rem'}
                    ),
                    create_help_button("modal-weather", button_color="outline-primary"),
                    create_info_modal(
                        modal_id="modal-weather",
                        title=MODAL_CONTENTS['weather']['title'],
                        content_sections=MODAL_CONTENTS['weather']['sections'],
                    ),
                ], className="d-flex align-items-center"),
            ], className="d-flex justify-content-between align-items-center"),
        ], style={
            'backgroundColor': AGRI_THEME['colors']['bg_light'],
            'border': 'none',
            'borderBottom': f"3px solid {AGRI_THEME['colors']['primary']}"
        }),
        dbc.CardBody([
            html.Div(id="current-weather-metrics", children=[
                # El contenido se genera dinámicamente via callback
                create_alert_card(
                    message="Cargando datos meteorológicos...",
                    alert_type="info",
                    title="Actualizando"
                )
            ])
        ], className="p-4")
    ], style={
        **get_card_style('highlight'),
        'border': f"1px solid {AGRI_THEME['colors']['border_light']}",
        'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)'
    })

def create_controls_section():
    """
    Panel de control mejorado con selectores avanzados
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                    html.I(className="fas fa-cogs me-2",
                          style={'color': AGRI_THEME['colors']['primary'], 'fontSize': '1.2rem'}),
                    html.H5("Configuración de Análisis", className="mb-0 d-inline fw-bold"),
                ], className="d-flex align-items-center"),
                create_help_button("modal-general", button_color="outline-primary"),
                create_info_modal(
                    modal_id="modal-general",
                    title=MODAL_CONTENTS['general']['title'],
                    content_sections=MODAL_CONTENTS['general']['sections'],
                ),
            ], className="d-flex justify-content-between align-items-center",
            style={
            'backgroundColor': AGRI_THEME['colors']['bg_light'],
            'border': 'none',
            'borderBottom': f"3px solid {AGRI_THEME['colors']['primary']}"
        }),
        dbc.CardBody([
            dbc.Row([
                # Selector de período
                dbc.Col([
                    html.Label("Período de Análisis", 
                              className="form-label fw-bold mb-2",
                              style={'color': AGRI_THEME['colors']['text_primary']}),
                    dcc.Dropdown(
                        id="period-selector",
                        options=[
                            {"label": "🕐 Últimas 24 horas", "value": "24h"},
                            {"label": "📅 Última semana", "value": "7d"},
                            {"label": "📊 Último mes", "value": "30d"},
                            {"label": "🎯 Período personalizado", "value": "custom"}
                        ],
                        value="7d",
                        clearable=False,
                        style={
                            'fontSize': '0.9rem',
                            'borderRadius': '8px'
                        },
                        className="mb-3"
                    )
                ], md=3),
                
                # Selector de rango personalizado - mejorado
                dbc.Col([
                    html.Div([
                        html.Label("Rango Personalizado", 
                                  id="custom-date-label",
                                  className="form-label fw-bold mb-2",
                                  style={
                                      'color': AGRI_THEME['colors']['text_primary'],
                                      'display': 'none'  # Inicialmente oculto
                                  }),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Fecha Inicio:", 
                                              className="form-label small mb-1",
                                              style={'color': AGRI_THEME['colors']['text_secondary']}),
                                    dcc.DatePickerSingle(
                                        id="start-date-picker",
                                        date=datetime.now() - timedelta(days=7),
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'},
                                        className="form-control-sm"
                                    )
                                ], md=6),
                                dbc.Col([
                                    html.Label("Fecha Fin:", 
                                              className="form-label small mb-1",
                                              style={'color': AGRI_THEME['colors']['text_secondary']}),
                                    dcc.DatePickerSingle(
                                        id="end-date-picker",
                                        date=datetime.now(),
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'},
                                        className="form-control-sm"
                                    )
                                ], md=6)
                            ])
                        ], id="custom-date-container", style={'display': 'none'})
                    ])
                ], md=4),
                
                # Selector de agrupación
                dbc.Col([
                    html.Label("Agrupación de Datos", 
                              className="form-label fw-bold mb-2",
                              style={'color': AGRI_THEME['colors']['text_primary']}),
                    dcc.Dropdown(
                        id="grouping-selector",
                        options=[
                            {"label": "📍 Todos los registros", "value": "none"},
                            {"label": "📊 Agrupación diaria", "value": "D"},
                            {"label": "📈 Agrupación semanal", "value": "W"},
                            {"label": "📉 Agrupación mensual", "value": "M"},
                            {"label": "🗂️ Agrupación trimestral", "value": "Q"}
                        ],
                        value="none",
                        clearable=False,
                        style={
                            'fontSize': '0.9rem',
                            'borderRadius': '8px'
                        },
                        className="mb-3"
                    )
                ], md=3),
                
                # Botón de actualización
                dbc.Col([
                    html.Label("Acciones", 
                              className="form-label fw-bold mb-2",
                              style={'color': AGRI_THEME['colors']['text_primary']}),
                    dbc.Button(
                        [
                            html.I(className="fas fa-sync-alt me-2"),
                            "Actualizar Datos"
                        ],
                        id="update-charts-btn",
                        color="primary",
                        size="md",
                        className="w-100",
                        style={
                            **get_button_style('primary'),
                            'borderRadius': '10px',
                            'fontWeight': '600',
                            'padding': '12px 20px',
                            'boxShadow': '0 3px 6px rgba(0, 0, 0, 0.15)',
                            'transition': 'all 0.2s ease'
                        }
                    )
                ], md=2)
            ], className="align-items-start")
        ], className="p-4")
    ], style={
        **get_card_style('default'),
        'border': f"1px solid {AGRI_THEME['colors']['border_light']}",
        'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.08)'
    })

def create_main_charts():
    """
    Gráficos principales con diseño profesional mejorado
    """
    return dbc.Row([
        # Gráfico de Precipitación y Humedad
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Div([
                            html.I(
                                className="fas fa-cloud-rain me-2",
                                style={'color': AGRI_THEME['colors']['info'], 'fontSize': '1.1rem'}
                            ),
                            html.H6("Precipitación y Humedad Relativa", className="mb-0 fw-bold"),
                        ], className="d-flex align-items-center"),
                        create_help_button("modal-precipitacion", button_color="outline-info"),
                        create_info_modal(
                            modal_id="modal-precipitacion",
                            title=MODAL_CONTENTS['precipitacion']['title'],
                            content_sections=MODAL_CONTENTS['precipitacion']['sections'],
                        ),
                    ], className="d-flex justify-content-between align-items-center"),
                ], style={
                    'backgroundColor': AGRI_THEME['colors']['bg_light'],
                    'border': 'none',
                    'borderBottom': f"2px solid {AGRI_THEME['colors']['info']}"
                }),
                dbc.CardBody([
                    dcc.Loading([
                        dcc.Graph(
                            id="precipitation-humidity-chart",
                            style={'height': '420px'},
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'autoScale2d']
                            }
                        )
                    ], type="circle", color=AGRI_THEME['colors']['info'])
                ], className="p-3")
            ], style={
                'border': f"1px solid {AGRI_THEME['colors']['border_light']}",
                'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.08)',
                'borderRadius': '10px'
            })
        ], md=6, className="mb-4"),
        
        # Gráfico de Temperatura
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Div([
                            html.I(
                                className="fas fa-thermometer-half me-2",
                                style={'color': AGRI_THEME['colors']['warning'], 'fontSize': '1.1rem'}
                            ),
                            html.H6("Análisis de Temperatura", className="mb-0 fw-bold"),
                        ], className="d-flex align-items-center"),
                        create_help_button("modal-temperatura", button_color="outline-warning"),
                        create_info_modal(
                            modal_id="modal-temperatura",
                            title=MODAL_CONTENTS['temperatura']['title'],
                            content_sections=MODAL_CONTENTS['temperatura']['sections'],
                        ),
                    ], className="d-flex justify-content-between align-items-center"),
                ], style={
                    'backgroundColor': AGRI_THEME['colors']['bg_light'],
                    'border': 'none',
                    'borderBottom': f"2px solid {AGRI_THEME['colors']['warning']}"
                }),
                dbc.CardBody([
                    dcc.Loading([
                        dcc.Graph(
                            id="temperature-chart",
                            style={'height': '420px'},
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'autoScale2d']
                            }
                        )
                    ], type="circle", color=AGRI_THEME['colors']['warning'])
                ], className="p-3")
            ], style={
                'border': f"1px solid {AGRI_THEME['colors']['border_light']}",
                'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.08)',
                'borderRadius': '10px'
            })
        ], md=6, className="mb-4")
    ])

def create_alerts_section():
    """
    Sección mejorada de alertas de enfermedad
    """
    return dbc.Row([
        # Alertas de enfermedad con diseño mejorado
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([

                    html.Div([
                            html.I(
                                className="fas fa-bell me-2",
                                style={'color': AGRI_THEME['colors']['warning'], 'fontSize': '1.2rem'}
                            ),
                            html.H5("Centro de Alertas Agrícolas", className="mb-0 d-inline fw-bold"),
                        ], className="d-flex align-items-center"),
                        create_help_button("modal-alertas", button_color="outline-warning"),
                        create_info_modal(
                            modal_id="modal-alertas",
                            title=MODAL_CONTENTS['alertas']['title'],
                            content_sections=MODAL_CONTENTS['alertas']['sections'],
                        ),
                    ], className="d-flex justify-content-between align-items-center", 
                       style={
                        'backgroundColor': AGRI_THEME['colors']['bg_light'],
                        'border': 'none',
                        'borderBottom': f"3px solid {AGRI_THEME['colors']['warning']}"
                }),
                dbc.CardBody([
                    html.Div(id="disease-alerts", children=[
                        # Panel de alertas principal
                        dbc.Row([
                            # Alerta principal
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
                                                html.P("Analizando condiciones meteorológicas en tiempo real para prevenir riesgos en el cultivo.", 
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
                        
                        # Tarjetas de monitoreo específico
                        dbc.Row([
                            # Temperatura
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-thermometer-half mb-2", 
                                                  style={'fontSize': '1.8rem', 'color': '#dc3545'}),
                                            html.H6("Control Térmico", className="fw-bold mb-2"),
                                            html.P("Monitoreo continuo de temperaturas extremas", 
                                                  className="small text-muted mb-2"),
                                            html.Div([
                                                html.Span("Estado: ", className="fw-bold"),
                                                html.Span("🟢 Normal", className="badge bg-success")
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
                                            html.P("Detección de riesgo de enfermedades fúngicas", 
                                                  className="small text-muted mb-2"),
                                            html.Div([
                                                html.Span("Estado: ", className="fw-bold"),
                                                html.Span("🟡 Vigilancia", className="badge bg-warning")
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
                                            html.P("Optimización del programa de irrigación", 
                                                  className="small text-muted mb-2"),
                                            html.Div([
                                                html.Span("Estado: ", className="fw-bold"),
                                                html.Span("🟢 Óptimo", className="badge bg-success")
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
                ], className="p-4")
            ], style={
                **get_card_style('default'),
                'border': f"1px solid {AGRI_THEME['colors']['border_light']}",
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
            })
        ], md=12, className="mb-4")
    ])

def build_layout_historico_improved(df=None, kml_geojson=None):
    """
    Layout histórico con diseño profesional mejorado
    """
    return html.Div([
        # Header principal de sección
        create_section_header(
            title="Análisis Meteorológico Histórico",
            subtitle="Monitoreo de condiciones ambientales, análisis de riesgo de enfermedades y visualización geoespacial",
            icon="fas fa-chart-line"
        ),
        
        # Estado meteorológico actual
        html.Div([
            create_current_weather_section()
        ], className="mb-4"),
        
        # Panel de controles
        html.Div([
            create_controls_section()
        ], className="mb-4"),
        
        # Gráficos principales
        create_main_charts(),
        
        # Alertas de enfermedad
        create_alerts_section(),
        
        # Stores para datos
        dcc.Store(id="weather-data-store"),
        dcc.Store(id="current-filters-store", data={
            "period": "7d",
            "grouping": "none",
            "start_date": None,
            "end_date": None
        }),
        
        # Nota: Se necesitará un callback para mostrar/ocultar el selector personalizado:
        # @app.callback(
        #     [Output('custom-date-container', 'style'),
        #      Output('custom-date-label', 'style')],
        #     Input('period-selector', 'value')
        # )
        # def toggle_custom_date_picker(period_value):
        #     if period_value == 'custom':
        #         return {'display': 'block'}, {'color': AGRI_THEME['colors']['text_primary'], 'display': 'block'}
        #     return {'display': 'none'}, {'display': 'none'}
        
    ], 
    style={
        'fontFamily': AGRI_THEME['fonts']['primary'],
        'backgroundColor': AGRI_THEME['colors']['bg_light'],
        'minHeight': '100vh',
        'padding': '1.5rem'
    })

# Función de compatibilidad
def build_layout_historico(df=None, kml_geojson=None):
    """Mantiene compatibilidad con el código existente"""
    return build_layout_historico_improved(df, kml_geojson)