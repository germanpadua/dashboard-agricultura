"""
Componentes modales de ayuda para el dashboard de agricultura
Proporciona información detallada sobre datos y funcionalidades específicas del Repilo
"""

import dash_bootstrap_components as dbc
from dash import html, Input, Output, State


def create_help_button(modal_id: str, button_text: str = "?", button_color: str = "outline-info", button_size: str = "sm") -> dbc.Button:
    """
    Crea un botón de ayuda que abrirá un modal
    
    Args:
        modal_id: ID único para el modal (debe coincidir con el modal)
        button_text: Texto del botón (por defecto "?")
        button_color: Color del botón Bootstrap
        button_size: Tamaño del botón
    
    Returns:
        Componente Button de Dash Bootstrap
    """
    return dbc.Button([
        html.I(className="fas fa-question-circle me-1"),
        button_text
    ], 
        id=f"open-{modal_id}",
        color=button_color, 
        size=button_size,
        className="ms-2",
        style={'borderRadius': '20px'}
    )


def create_info_modal(modal_id: str, title: str, content_sections: list, size: str = "lg") -> dbc.Modal:
    """
    Crea un modal informativo con múltiples secciones
    
    Args:
        modal_id: ID único para el modal
        title: Título del modal
        content_sections: Lista de secciones con {'title': str, 'content': str, 'icon': str}
        size: Tamaño del modal ('sm', 'lg', 'xl')
    
    Returns:
        Componente Modal de Dash Bootstrap
    """
    
    modal_body_content = []
    
    for section in content_sections:
        modal_body_content.extend([
            html.H6([
                html.I(className=f"fas {section.get('icon', 'fa-info-circle')} me-2 text-primary"),
                section['title']
            ], className="mb-3 mt-4 border-bottom pb-2"),
            html.Div(section['content'], className="mb-3")
        ])
    
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className="fas fa-seedling me-2 text-success"),
            title
        ])),
        dbc.ModalBody(modal_body_content),
        dbc.ModalFooter(
            dbc.Button("Cerrar", id=f"close-{modal_id}", className="ms-auto")
        )
    ], 
        id=modal_id, 
        size=size,
        is_open=False
    )


# Contenidos específicos para agricultura/Repilo
MODAL_CONTENTS = {
    'temperatura': {
        'title': '🌡️ Temperatura y su Impacto en el Olivar',
        'sections': [
            {
                'title': 'Explicación del Gráfico',
                'icon': 'fa-chart-area',
                'content': html.Div([
                    html.P([
                        "En este gráfico se representan tres curvas de temperatura: ",
                        html.Span("mínima (azul)", style={'color':'#1f77b4','fontWeight':'bold'}),
                        ", ",
                        html.Span("media (rojo)", style={'color':'#d62728','fontWeight':'bold'}),
                        " y ",
                        html.Span("máxima (rojo punteado)", style={'color':'#d62728','fontStyle':'italic'}),
                        ". El área sombreada muestra el rango diario [mínima – máxima]."
                    ], className="mb-2"),
                ], className="text-justify")
            },
            {
                'title': 'Rangos Críticos de Temperatura',
                'icon': 'fa-thermometer-half',
                'content': html.Div([
                    dbc.Alert([
                        html.H6("❗ Máximo Riesgo: 8 – 24 °C", className="alert-heading"),
                        html.P("Óptimo cerca de 15 °C, condiciones ideales para el desarrollo del repilo"),
                    ], color="danger"),
                    dbc.Alert([
                        html.H6("⚠️ Riesgo Moderado: 5 – 8 °C y 24 – 30 °C", className="alert-heading"),
                        html.P("Desarrollo más lento, pero aún activo")
                    ], color="warning"),
                    dbc.Alert([
                        html.H6("✅ Bajo Riesgo: < 5 °C o > 30 °C", className="alert-heading"),
                        html.P("Condiciones adversas que detienen el hongo")
                    ], color="success")
                ], className="mb-0")
            }
        ]
    },
    
    'precipitacion': {
        'title': '🌧️ Precipitación y Humedad',
        'sections': [
            {
                'title': 'Explicación del Gráfico',
                'icon': 'fa-chart-bar',
                'content': html.Div([
                    html.P(
                        [
                            "Este gráfico muestra dos variables clave para el repilo: ",
                            html.B("precipitación (mm)"),
                            " en el eje izquierdo y ",
                            html.B("humedad relativa (%)"),
                            " promedio en el eje derecho. ",
                            "Los picos simultáneos de lluvia y humedad prolongada ",
                            "se asocian con un riesgo elevado de infección."
                        ],
                        className="mb-3"
                    ),
                    html.P(
                        [
                            "El rango óptimo de temperatura para el desarrollo de la enfermedad es ",
                            html.Span("15 °C", className="fw-bold"),
                            " (puede variar entre ",
                            html.Span("8 – 24 °C", className="fst-italic"),
                            "). Bajo estas condiciones, la humedad foliar y la lluvia crean el microclima ideal."
                        ]
                    )
                ], className="text-justify")
            },
            {
                'title': 'La Lluvia y el Repilo',
                'icon': 'fa-cloud-rain',
                'content': html.Div([
                    html.P(
                        "Para que las esporas germinen y penetren la hoja se necesita:",
                        className="mb-3"
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("💧 Humedad Crítica", className="card-title text-primary"),
                                    html.Ul([
                                        html.Li("Humedad foliar ≥ 98 % continua durante ≥ 12 h"),
                                        html.Li("Temperatura del aire entre 15 °C y 20 °C")
                                    ], className="mb-0")
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("🌧️ Dispersión por Lluvia", className="card-title text-info"),
                                    html.Ul([
                                        html.Li("Lluvias ligeras ≥ 1 mm generan salpicaduras"),
                                        html.Li("Escorrentías mueven las conidias entre hojas")
                                    ], className="mb-0")
                                ])
                            ])
                        ], width=6)
                    ])
                ], className="text-justify")
            }
        ]
    },
    
    'ndvi': {
        'title': '🛰️ Análisis Geoespacial',
        'sections': [
            {
                'title': 'Tecnología Satelital',
                'icon': 'fa-satellite',
                'content': html.Ul([
                    html.Li("Satélites: Sentinel-2 (Programa Copernicus ESA)"),
                    html.Li("Resolución espacial: 10 m por píxel"),
                    html.Li("Frecuencia: Cada 5 días (condiciones atmosféricas)"),
                    html.Li("Bandas utilizadas: Rojo (B04) e Infrarrojo cercano (B08)"),
                ], className="mb-3")
            },
            {
                'title': '¿Qué es el NDVI?',
                'icon': 'fa-leaf',
                'content': html.Div([
                    html.P([
                        "El NDVI (Índice de Vegetación de Diferencia Normalizada) es un indicador de la salud de los cultivos. ",
                        "Se calcula comparando la reflexión del infrarrojo cercano (que generan las hojas verdes sanas) con la ",
                        "absorción de la luz roja por la clorofila. Valores altos indican vegetación densa y en buen estado, ",
                        "mientras que los valores bajos indican estrés, suelo desnudo o vegetación enferma."
                        
                    ], className="mb-3")
                ])
            },
            {
                'title': 'Cómo Interpretar los Colores',
                'icon': 'fa-palette',
                'content': html.Div([
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Color en el Mapa", style={'width': '100px'}),
                            html.Th("Valores NDVI"),
                            html.Th("¿Qué Significa para tu Olivar?")
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#004400', 'height': '30px'}),
                                html.Td("0.6 - 1.0"),
                                html.Td("🌿 Vegetación muy sana")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#0f540a', 'height': '30px'}),
                                html.Td("0.5 - 0.6"),
                                html.Td("✅ Buena salud")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#306d1c', 'height': '30px'}),
                                html.Td("0.4 - 0.5"),
                                html.Td("⚠️ Salud moderada")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#70a33f', 'height': '30px'}),
                                html.Td("0.2 - 0.4"),
                                html.Td("🚨 Vegetación en riesgo")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#ccc682', 'height': '30px'}),
                                html.Td("0 - 0.2"),
                                html.Td("⚡ Vegetación muy débil o suelo desnudo")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#eaeaea', 'height': '30px'}),
                                html.Td("-0.5 - 0"),
                                html.Td("❌ Sin vegetación o agua")
                            ]),
                            html.Tr([
                                html.Td("", style={'backgroundColor':'#0c0c0c', 'height': '30px'}),
                                html.Td("Menos de -0.5"),
                                html.Td("❌ Agua o nieve")
                            ])
                            
                        ])
                    ], className="table table-sm")
                ])
            }
        ]
    },
    
    'alertas': {
        'title': '🚨 Sistema de Alertas para el Agricultor',
        'sections': [
            {
                'title': 'Niveles de Alerta Explicados',
                'icon': 'fa-traffic-light',
                'content': html.Div([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("CRÍTICA", color="danger", className="me-2"),
                                    "¡Actúa Ya!"
                                ]),
                                dbc.CardBody([
                                    html.P("Condiciones perfectas para repilo detectadas"),
                                    html.Strong("Qué hacer: "),
                                    html.Ul([
                                        html.Li("Aplicar tratamiento en 24-48h"),
                                        html.Li("Inspeccionar campo diariamente"),
                                        html.Li("Preparar segunda aplicación si persiste")
                                    ])
                                ])
                            ], className="border-danger")
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("ALTA", color="warning", className="me-2"),
                                    "Precaución"
                                ]),
                                dbc.CardBody([
                                    html.P("Riesgo elevado en desarrollo"),
                                    html.Strong("Qué hacer: "),
                                    html.Ul([
                                        html.Li("Monitorear evolución del tiempo"),
                                        html.Li("Preparar equipo de aplicación"),
                                        html.Li("Revisar zonas más sensibles")
                                    ])
                                ])
                            ], className="border-warning")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("MEDIA", color="info", className="me-2"),
                                    "Atención"
                                ]),
                                dbc.CardBody([
                                    html.P("Condiciones parcialmente favorables"),
                                    html.Strong("Qué hacer: "),
                                    html.Ul([
                                        html.Li("Mantener vigilancia rutinaria"),
                                        html.Li("Revisar pronóstico extendido"),
                                        html.Li("Documentar observaciones")
                                    ])
                                ])
                            ], className="border-info")
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("BAJA", color="success", className="me-2"),
                                    "Tranquilo"
                                ]),
                                dbc.CardBody([
                                    html.P("Condiciones normales"),
                                    html.Strong("Qué hacer: "),
                                    html.Ul([
                                        html.Li("Mantenimiento rutinario"),
                                        html.Li("Planificar próximas labores"),
                                        html.Li("Revisar estado general")
                                    ])
                                ])
                            ], className="border-success")
                        ], width=6)
                    ])
                ])
            },
            {
                'title': 'Cómo Recibir las Alertas',
                'icon': 'fa-bell',
                'content': html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-desktop fa-2x text-primary mb-2"),
                                html.H6("Dashboard Web"),
                                html.P("Alertas en tiempo real mientras navegas", className="small text-muted")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-envelope fa-2x text-info mb-2"),
                                html.H6("Email"),
                                html.P("Resumen diario cada mañana a las 7:00", className="small text-muted")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-sms fa-2x text-warning mb-2"),
                                html.H6("SMS"),
                                html.P("Solo alertas críticas urgentes", className="small text-muted")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fab fa-whatsapp fa-2x text-success mb-2"),
                                html.H6("WhatsApp/Telegram"),
                                html.P("Notificaciones personalizadas", className="small text-muted")
                            ], className="text-center")
                        ], width=3)
                    ])
                ])
            },
            {
                'title': 'Personaliza tus Alertas',
                'icon': 'fa-cogs',
                'content': html.Div([
                    html.P("Ajusta el sistema según tu experiencia y necesidades:", className="mb-3"),
                    dbc.Accordion([
                        dbc.AccordionItem([
                            html.Ul([
                                html.Li("Temperatura: Ajusta los rangos según tu zona climática"),
                                html.Li("Humedad: Modifica según microclima de tu finca"),
                                html.Li("Precipitación: Considera tu sistema de riego")
                            ])
                        ], title="⚙️ Umbrales Personalizados"),
                        dbc.AccordionItem([
                            html.Ul([
                                html.Li("Horarios: Elige cuándo recibir notificaciones"),
                                html.Li("Frecuencia: Diaria, cada 6h, o solo cambios importantes"),
                                html.Li("Filtros: Solo alertas altas/críticas o todas")
                            ])
                        ], title="📱 Preferencias de Notificación"),
                        dbc.AccordionItem([
                            html.Ul([
                                html.Li("Historial: Revisa alertas pasadas y su precisión"),
                                html.Li("Calendario: Integra con tu plan de tratamientos"),
                                html.Li("Reportes: Recibe análisis mensuales de riesgo")
                            ])
                        ], title="📊 Herramientas Adicionales")
                    ])
                ])
            }
        ]
    }
}


def create_chart_help_section(chart_type: str, title: str = None) -> html.Div:
    """
    Crea una sección completa con título, botón de ayuda y modal para un gráfico
    
    Args:
        chart_type: Tipo de gráfico ('temperatura', 'precipitacion', 'ndvi', 'alertas')
        title: Título personalizado (opcional)
    
    Returns:
        Div con título, botón y modal
    """
    modal_id = f"modal-{chart_type}"
    display_title = title or chart_type.replace('_', ' ').title()
    
    modal_config = MODAL_CONTENTS.get(chart_type, {
        'title': f'Información sobre {display_title}',
        'sections': [{'title': 'Sin información', 'content': 'Datos no disponibles'}]
    })
    
    return html.Div([
        html.Div([
            html.H6(display_title, className="mb-0"),
            create_help_button(modal_id, "Ayuda", "outline-primary")
        ], className="d-flex align-items-center justify-content-between mb-2"),
        
        create_info_modal(
            modal_id=modal_id,
            title=modal_config['title'],
            content_sections=modal_config['sections']
        )
    ])


def register_modal_callbacks(app):
    """
    Registra todos los callbacks para abrir/cerrar modales
    """
    
    # Callback para modal NDVI
    @app.callback(
        Output("modal-ndvi", "is_open"),
        [Input("open-modal-ndvi", "n_clicks"), Input("close-modal-ndvi", "n_clicks")],
        [State("modal-ndvi", "is_open")]
    )
    def toggle_modal_ndvi(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal general
    @app.callback(
        Output("modal-general", "is_open"),
        [Input("open-modal-general", "n_clicks"), Input("close-modal-general", "n_clicks")],
        [State("modal-general", "is_open")]
    )
    def toggle_modal_general(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal temperatura
    @app.callback(
        Output("modal-temperatura", "is_open"),
        [Input("open-modal-temperatura", "n_clicks"), Input("close-modal-temperatura", "n_clicks")],
        [State("modal-temperatura", "is_open")]
    )
    def toggle_modal_temperatura(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal precipitacion
    @app.callback(
        Output("modal-precipitacion", "is_open"),
        [Input("open-modal-precipitacion", "n_clicks"), Input("close-modal-precipitacion", "n_clicks")],
        [State("modal-precipitacion", "is_open")]
    )
    def toggle_modal_precipitacion(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal alertas
    @app.callback(
        Output("modal-alertas", "is_open"),
        [Input("open-modal-alertas", "n_clicks"), Input("close-modal-alertas", "n_clicks")],
        [State("modal-alertas", "is_open")]
    )
    def toggle_modal_alertas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal weather
    @app.callback(
        Output("modal-weather", "is_open"),
        [Input("open-modal-weather", "n_clicks"), Input("close-modal-weather", "n_clicks")],
        [State("modal-weather", "is_open")]
    )
    def toggle_modal_weather(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal prediccion
    @app.callback(
        Output("modal-prediccion", "is_open"),
        [Input("open-modal-prediccion", "n_clicks"), Input("close-modal-prediccion", "n_clicks")],
        [State("modal-prediccion", "is_open")]
    )
    def toggle_modal_prediccion(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal pred-semanal
    @app.callback(
        Output("modal-pred-semanal", "is_open"),
        [Input("open-modal-pred-semanal", "n_clicks"), Input("close-modal-pred-semanal", "n_clicks")],
        [State("modal-pred-semanal", "is_open")]
    )
    def toggle_modal_pred_semanal(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal pred-horaria
    @app.callback(
        Output("modal-pred-horaria", "is_open"),
        [Input("open-modal-pred-horaria", "n_clicks"), Input("close-modal-pred-horaria", "n_clicks")],
        [State("modal-pred-horaria", "is_open")]
    )
    def toggle_modal_pred_horaria(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal satelital
    @app.callback(
        Output("modal-satelital", "is_open"),
        [Input("open-modal-satelital", "n_clicks"), Input("close-modal-satelital", "n_clicks")],
        [State("modal-satelital", "is_open")]
    )
    def toggle_modal_satelital(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal temporal
    @app.callback(
        Output("modal-temporal", "is_open"),
        [Input("open-modal-temporal", "n_clicks"), Input("close-modal-temporal", "n_clicks")],
        [State("modal-temporal", "is_open")]
    )
    def toggle_modal_temporal(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal mapa-inter
    @app.callback(
        Output("modal-mapa-inter", "is_open"),
        [Input("open-modal-mapa-inter", "n_clicks"), Input("close-modal-mapa-inter", "n_clicks")],
        [State("modal-mapa-inter", "is_open")]
    )
    def toggle_modal_mapa_inter(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal estadisticas
    @app.callback(
        Output("modal-estadisticas", "is_open"),
        [Input("open-modal-estadisticas", "n_clicks"), Input("close-modal-estadisticas", "n_clicks")],
        [State("modal-estadisticas", "is_open")]
    )
    def toggle_modal_estadisticas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal nueva-finca
    @app.callback(
        Output("modal-nueva-finca", "is_open"),
        [Input("open-modal-nueva-finca", "n_clicks"), Input("close-modal-nueva-finca", "n_clicks")],
        [State("modal-nueva-finca", "is_open")]
    )
    def toggle_modal_nueva_finca(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal mapa-fincas
    @app.callback(
        Output("modal-mapa-fincas", "is_open"),
        [Input("open-modal-mapa-fincas", "n_clicks"), Input("close-modal-mapa-fincas", "n_clicks")],
        [State("modal-mapa-fincas", "is_open")]
    )
    def toggle_modal_mapa_fincas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal gestion-fincas
    @app.callback(
        Output("modal-gestion-fincas", "is_open"),
        [Input("open-modal-gestion-fincas", "n_clicks"), Input("close-modal-gestion-fincas", "n_clicks")],
        [State("modal-gestion-fincas", "is_open")]
    )
    def toggle_modal_gestion_fincas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
