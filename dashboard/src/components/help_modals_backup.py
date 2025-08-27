"""
===============================================================================
                    SISTEMA DE AYUDA AVANZADO PARA DASHBOARD AGRÍCOLA
===============================================================================

Sistema comprehensivo de ayuda contextual diseñado específicamente para
agricultor profesional. Proporciona guías detalladas, explicaciones técnicas
y consejos prácticos para maximizar el uso del dashboard de monitoreo agrícola.

Características principales:
• Modales informativos con diseño profesional y user-friendly
• Contenido técnico adaptado para conocimiento agrícola específico
• Guías paso a paso para cada funcionalidad del dashboard
• Explicaciones científicas de índices y métricas agrícolas
• Consejos de interpretación de datos meteorológicos y satelitales
• Alertas y recomendaciones para toma de decisiones
• Integración completa con todos los módulos del dashboard

Módulos cubiertos:
• Análisis Meteorológico Histórico (temperatura, humedad, precipitación)
• Pronóstico Meteorológico y Planificación Agrícola
• Análisis Satelital NDVI y Salud de Cultivos
• Gestión y Registro de Fincas Agrícolas
• Sistema de Detección de Enfermedades (Repilo)
• Alertas Tempranas y Sistema de Notificaciones

Tecnologías integradas:
• Datos Sentinel-2 para análisis satelital
• API AEMET para datos meteorológicos
• Telegram Bot para reportes de campo
• Machine Learning para predicciones
• Sistemas GIS para georreferenciación

Autor: German Jose Padua Pleguezuelo
Universidad: Universidad de Granada
Máster: Ciencia de Datos
Curso: 2024-2025

===============================================================================
"""

import dash_bootstrap_components as dbc
from dash import html, Input, Output, State


def create_help_button(modal_id: str, button_text: str = "Ayuda", button_color: str = "outline-primary", button_size: str = "sm") -> dbc.Button:
    """
    Crea un botón de ayuda profesional y elegante que abrirá un modal informativo.
    
    Este botón está diseñado para integrarse seamlessly con el diseño del dashboard,
    proporcionando acceso rápido a información contextual sin interrumpir el flujo
    de trabajo del agricultor.
    
    Args:
        modal_id: ID único para el modal (debe coincidir exactamente con el modal target)
        button_text: Texto del botón (por defecto "Ayuda" - más claro que "?")
        button_color: Color del botón Bootstrap (outline-primary por defecto)
        button_size: Tamaño del botón (sm por defecto para no ser intrusivo)
    
    Returns:
        dbc.Button: Componente Button de Dash Bootstrap estilizado
        
    Features:
        • Icono intuitivo de ayuda
        • Hover effects suaves
        • Integración con tema del dashboard
        • Accesibilidad mejorada
        • Responsive design
    """
    return dbc.Button([
        html.I(className="fas fa-question-circle me-2", style={'fontSize': '0.9rem'}),
        button_text
    ], 
        id=f"open-{modal_id}",
        color=button_color, 
        size=button_size,
        className="help-btn ms-2",
        style={
            'borderRadius': '25px',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        },
        title="Obtener ayuda sobre esta sección"
    )


def create_info_modal(modal_id: str, title: str, content_sections: list, size: str = "xl") -> dbc.Modal:
    """
    Crea un modal informativo profesional con múltiples secciones organizadas.
    
    Diseñado para proporcionar información técnica y práctica de manera estructurada
    y visualmente atractiva. Incluye iconografía profesional, navegación clara y
    contenido adaptado para usuarios agrícolas con diferentes niveles técnicos.
    
    Args:
        modal_id: ID único para el modal (usado para callbacks)
        title: Título descriptivo del modal
        content_sections: Lista de secciones con estructura:
                         [{'title': str, 'content': html.Div, 'icon': str}]
        size: Tamaño del modal ('xl' por defecto para mejor legibilidad)
    
    Returns:
        dbc.Modal: Componente Modal de Dash Bootstrap completamente estilizado
        
    Features:
        • Design responsivo y profesional
        • Iconografía consistente
        • Navegación intuitiva
        • Contenido estructurado
        • Z-index optimizado
        • Animaciones suaves
    """
    
    modal_body_content = []
    
    # Crear contenido organizado por secciones
    for i, section in enumerate(content_sections):
        # Separador visual entre secciones (excepto la primera)
        if i > 0:
            modal_body_content.append(html.Hr(style={'margin': '2rem 0', 'opacity': '0.3'}))
            
        # Header de la sección con icono y estilo mejorado
        section_header = html.H5([
            html.I(className=f"fas {section.get('icon', 'fa-info-circle')} me-2", 
                   style={'color': '#2E7D32', 'fontSize': '1.2rem'}),
            section['title']
        ], className="mb-3 section-header", 
           style={
               'color': '#2E7D32',
               'fontWeight': '600',
               'borderBottom': '2px solid #E8F5E9',
               'paddingBottom': '0.5rem',
               'marginTop': '1.5rem' if i > 0 else '0'
           })
        
        # Contenido de la sección con padding mejorado
        section_content = html.Div(
            section['content'], 
            className="section-content",
            style={
                'padding': '1rem 0',
                'lineHeight': '1.6',
                'fontSize': '0.95rem'
            }
        )
        
        modal_body_content.extend([section_header, section_content])
    
    return dbc.Modal([
        # Header mejorado con diseño profesional
        dbc.ModalHeader([
            dbc.ModalTitle([
                html.I(className="fas fa-seedling me-2", 
                       style={'color': '#4CAF50', 'fontSize': '1.4rem'}),
                title
            ], style={
                'color': '#2E7D32',
                'fontWeight': '700',
                'fontSize': '1.3rem'
            }),
            # Botón de cerrar personalizado
            dbc.Button([
                html.I(className="fas fa-times")
            ], 
                id=f"close-{modal_id}",
                color="light",
                size="sm",
                className="btn-close-custom",
                style={
                    'borderRadius': '50%',
                    'width': '35px',
                    'height': '35px',
                    'padding': '0'
                },
                title="Cerrar ayuda"
            )
        ], style={
            'backgroundColor': '#F8FFF8',
            'borderBottom': '2px solid #E8F5E9'
        }),
        
        # Body con scroll optimizado
        dbc.ModalBody(
            modal_body_content,
            style={
                'maxHeight': '70vh',
                'overflowY': 'auto',
                'padding': '1.5rem',
                'backgroundColor': '#FFFFFF'
            }
        ),
        
        # Footer con acciones adicionales
        dbc.ModalFooter([
            html.Small(
                "💡 Tip: Use estas guías como referencia mientras trabaja con el dashboard",
                className="text-muted me-auto",
                style={'fontStyle': 'italic'}
            ),
            dbc.Button([
                html.I(className="fas fa-check me-2"),
                "Entendido"
            ], 
                id=f"close-{modal_id}-alt",
                color="success",
                size="sm",
                style={
                    'borderRadius': '20px',
                    'fontWeight': '500'
                }
            )
        ], style={
            'backgroundColor': '#F8FFF8',
            'borderTop': '1px solid #E8F5E9'
        })
    ],
        id=modal_id,
        size=size,
        is_open=False,
        zindex=3000,
        backdrop_style={"zIndex": 2999},
        className="help-modal",
        style={
            'fontFamily': "'Inter', sans-serif"
        }
    )


# ===============================================================================
#                         CONTENIDOS ESPECIALIZADOS POR MÓDULO
# ===============================================================================

MODAL_CONTENTS = {
    # ============================================================================
    #                              MÓDULO GENERAL
    # ============================================================================
    'general': {
        'title': '⚙️ Configuración de Análisis Meteorológico',
        'sections': [
            {
                'title': 'Controles de Visualización',
                'icon': 'fa-sliders-h',
                'content': html.Div([
                    html.P([
                        "Los controles de período le permiten personalizar el rango temporal ",
                        "de análisis para obtener insights específicos de su cultivo:"
                    ]),
                    html.Ul([
                        html.Li([html.Strong("Período:"), " Seleccione entre 1 semana, 1 mes, 3 meses o todo el histórico disponible"]),
                        html.Li([html.Strong("Agrupación:"), " Visualice datos por día, semana o mes según sus necesidades"]),
                        html.Li([html.Strong("Variables:"), " Active/desactive temperatura, humedad, precipitación y viento"])
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-lightbulb me-2"),
                        html.Strong("Consejo profesional: "),
                        "Para detectar patrones estacionales, use períodos de 3 meses o más con agrupación semanal."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    # ============================================================================
    #                         MÓDULO METEOROLÓGICO
    # ============================================================================
    'weather': {
        'title': '🌤️ Panel Meteorológico en Tiempo Real',
        'sections': [
            {
                'title': 'Interpretación de Datos Actuales',
                'icon': 'fa-cloud-sun',
                'content': html.Div([
                    html.P([
                        "El panel meteorológico muestra las condiciones más recientes de su estación:",
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([html.I(className="fas fa-thermometer-half me-2"), "Temperatura"], className="text-primary"),
                                    html.P("Valor instantáneo en °C, crítico para el desarrollo de enfermedades fúngicas", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([html.I(className="fas fa-tint me-2"), "Humedad Relativa"], className="text-info"),
                                    html.P("Porcentaje de humedad del aire, factor clave en infecciones", className="small")
                                ])
                            ])
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([html.I(className="fas fa-cloud-rain me-2"), "Precipitación"], className="text-success"),
                                    html.P("Cantidad de lluvia reciente, favorece dispersión de esporas", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([html.I(className="fas fa-wind me-2"), "Viento"], className="text-warning"),
                                    html.P("Velocidad y dirección, ayuda en dispersión aérea de patógenos", className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
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
    'prediccion': {
        'title': '🔮 Pronóstico Meteorológico',
        'sections': [
            {
                'title': '¿Qué ofrece este módulo?',
                'icon': 'fa-info-circle',
                'content': html.P(
                    'Permite explorar las predicciones meteorológicas y el riesgo de repilo para planificar las labores agrícolas.'
                ),
            }
        ],
    },

    'municipio': {
        'title': '🏙️ Selección de Municipio',
        'sections': [
            {
                'title': 'Cómo utilizarlo',
                'icon': 'fa-map-marker-alt',
                'content': html.P(
                    'Elija el municipio para obtener pronósticos específicos de esa ubicación. Puede escribir para filtrar la lista.'
                ),
            }
        ],
    },

    'pred_semanal': {
        'title': '📅 Predicción Semanal',
        'sections': [
            {
                'title': 'Interpretación de las tarjetas',
                'icon': 'fa-chart-bar',
                'content': html.P(
                    'Cada tarjeta resume la previsión diaria con temperaturas, probabilidad de lluvia y nivel de riesgo de repilo.'
                ),
            }
        ],
    },

    'pred_horaria': {
        'title': '⏰ Evolución 48 Horas',
        'sections': [
            {
                'title': 'Lectura del gráfico',
                'icon': 'fa-chart-line',
                'content': html.P(
                    'Muestra la evolución prevista de temperatura, humedad y precipitación para las próximas 48 horas.'
                ),
            }
        ],
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
    'satelital': {
        'title': '🛰️ Módulo de Datos Satelitales',
        'sections': [
            {
                'title': '¿Para qué sirve?',
                'icon': 'fa-info-circle',
                'content': html.P(
                    'Permite monitorear la salud de los cultivos mediante índices de vegetación obtenidos de imágenes Sentinel-2.'
                ),
            },
            {
                'title': 'Fuentes de datos',
                'icon': 'fa-satellite',
                'content': html.Ul([
                    html.Li('Satélites Sentinel-2 (programa Copernicus)'),
                    html.Li('Resolución espacial de 10 m por píxel'),
                    html.Li('Actualizaciones aproximadas cada 5 días')
                ])
            }
        ],
    },
    'config_satelital': {
        'title': '⚙️ Configuración del Análisis',
        'sections': [
            {
                'title': 'Selección de área',
                'icon': 'fa-draw-polygon',
                'content': html.P(
                    'Escoge una finca registrada o dibuja un polígono en el mapa para delimitar la zona de estudio.'
                ),
            },
            {
                'title': 'Parámetros de cálculo',
                'icon': 'fa-sliders-h',
                'content': html.P(
                    'Define fechas, índice de vegetación y paleta de colores antes de ejecutar el análisis.'
                ),
            }
        ],
    },
    'mapa_satelital': {
        'title': '🗺️ Vista Satelital',
        'sections': [
            {
                'title': 'Interacción con el mapa',
                'icon': 'fa-map',
                'content': html.P(
                    'Navega con el ratón, activa capas y ajusta la opacidad de los índices para explorar tu cultivo.'
                ),
            },
            {
                'title': 'Dibujo y selección',
                'icon': 'fa-pencil-alt',
                'content': html.P(
                    'Utiliza las herramientas de dibujo para crear o modificar áreas de análisis directamente sobre el mapa.'
                ),
            }
        ],
    },
    'analisis_indices': {
        'title': '📊 Análisis de Índices',
        'sections': [
            {
                'title': 'Lectura de gráficos',
                'icon': 'fa-chart-area',
                'content': html.P(
                    'Los histogramas y curvas muestran la distribución y evolución de los valores de cada índice seleccionado.'
                ),
            }
        ],
    },
    'comparacion_satelital': {
        'title': '🔄 Comparación de Fechas',
        'sections': [
            {
                'title': 'Cómo funciona',
                'icon': 'fa-exchange-alt',
                'content': html.P(
                    'Selecciona dos rangos temporales e índices para evaluar mejoras o deterioros en la vegetación.'
                ),
            }
        ],
    },
    'historico_satelital': {
        'title': '📈 Evolución Histórica',
        'sections': [
            {
                'title': 'Objetivo',
                'icon': 'fa-chart-line',
                'content': html.P(
                    'Revisa cómo ha cambiado tu cultivo a lo largo del tiempo para detectar tendencias o anomalías.'
                ),
            }
        ],
    },
    'detecciones': {
        'title': '🧪 Detecciones de Repilo',
        'sections': [
            {
                'title': '¿Qué muestra esta sección?',
                'icon': 'fa-microscope',
                'content': html.P(
                    'Visualiza las incidencias reportadas por los agricultores a través del bot de Telegram, '
                    'permitiendo un monitoreo georreferenciado de la enfermedad.'
                ),
            }
        ],
    },
    'filtros-detecciones': {
        'title': '🔍 Controles de Visualización',
        'sections': [
            {
                'title': 'Filtrado y actualización',
                'icon': 'fa-filter',
                'content': html.P(
                    'Ajusta el periodo temporal y las severidades para refinar las detecciones mostradas '
                    'en los gráficos y el mapa.'
                ),
            }
        ],
    },
    'metricas-detecciones': {
        'title': '📊 Métricas de Detección',
        'sections': [
            {
                'title': 'Interpretación de tarjetas',
                'icon': 'fa-chart-bar',
                'content': html.P(
                    'Cada tarjeta resume estadísticas claves como totales históricos, severidad media y tendencias recientes.'
                ),
            }
        ],
    },
    'mapa-detecciones': {
        'title': '🗺️ Mapa de Detecciones',
        'sections': [
            {
                'title': 'Capas por severidad',
                'icon': 'fa-map-marked-alt',
                'content': html.P(
                    'Explora la ubicación exacta de cada reporte y activa capas para visualizar las diferentes severidades.'
                ),
            }
        ],
    },
    'timeline-detecciones': {
        'title': '⏳ Evolución Temporal',
        'sections': [
            {
                'title': 'Comprender el gráfico',
                'icon': 'fa-chart-line',
                'content': html.P(
                    'Muestra cómo han variado las detecciones en el tiempo para identificar picos y tendencias.'
                ),
            }
        ],
    },
    'distribucion-detecciones': {
        'title': '🧮 Distribución de Severidad',
        'sections': [
            {
                'title': 'Lectura del gráfico',
                'icon': 'fa-chart-pie',
                'content': html.P(
                    'El gráfico circular indica la proporción de reportes en cada nivel de severidad.'
                ),
            }
        ],
    },
    'alertas-detecciones': {
        'title': '🚨 Estado de Alertas',
        'sections': [
            {
                'title': 'Indicadores de riesgo',
                'icon': 'fa-exclamation-triangle',
                'content': html.P(
                    'Resume el nivel de atención requerido según las detecciones recientes y su gravedad.'
                ),
            }
        ],
    },

    'nueva-finca': {
        'title': '📝 Registro de Nuevas Fincas',
        'sections': [
            {
                'title': 'Cómo completar el formulario',
                'icon': 'fa-edit',
                'content': html.P(
                    'Asigne un nombre descriptivo a la finca. La superficie se calcula automáticamente tras dibujar el polígono.'
                ),
            },
            {
                'title': 'Guardar o limpiar',
                'icon': 'fa-save',
                'content': html.P(
                    'Use "Guardar Finca" para almacenarla o "Limpiar Formulario" para reiniciar el proceso.'
                ),
            },
        ],
    },

    'mapa-fincas': {
        'title': '🗺️ Delimitación en el Mapa',
        'sections': [
            {
                'title': 'Herramientas de dibujo',
                'icon': 'fa-draw-polygon',
                'content': html.P(
                    'Utilice la barra del mapa para dibujar polígonos o rectángulos y cierre la forma con doble clic.'
                ),
            },
            {
                'title': 'Opciones de visualización',
                'icon': 'fa-layer-group',
                'content': html.P(
                    'Cambie entre vista de calles y satélite con los botones superiores.'
                ),
            },
        ],
    },

    'estadisticas': {
        'title': '📊 Métricas de Fincas',
        'sections': [
            {
                'title': 'Interpretación',
                'icon': 'fa-chart-bar',
                'content': html.P(
                    'Las tarjetas muestran el número total de parcelas y su superficie acumulada. Se actualizan automáticamente.'
                ),
            }
        ],
    },

    'gestion-fincas': {
        'title': '📋 Gestión de Fincas Registradas',
        'sections': [
            {
                'title': 'Acciones disponibles',
                'icon': 'fa-tasks',
                'content': html.P(
                    'Selecciona una finca para centrarla en el mapa, editar su nombre o eliminarla definitivamente.'
                ),
            },
            {
                'title': 'Uso posterior',
                'icon': 'fa-satellite',
                'content': html.P(
                    'Las fincas guardadas podrán utilizarse en el módulo de Datos Satelitales.'
                ),
            },
        ],
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
    

    # Callback para modal configuración satelital
    @app.callback(
        Output("modal-config-satelital", "is_open"),
        [Input("open-modal-config-satelital", "n_clicks"), Input("close-modal-config-satelital", "n_clicks")],
        [State("modal-config-satelital", "is_open")]
    )
    def toggle_modal_config_satelital(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal mapa satelital
    @app.callback(
        Output("modal-mapa-satelital", "is_open"),
        [Input("open-modal-mapa-satelital", "n_clicks"), Input("close-modal-mapa-satelital", "n_clicks")],
        [State("modal-mapa-satelital", "is_open")]
    )
    def toggle_modal_mapa_satelital(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal análisis de índices
    @app.callback(
        Output("modal-analisis-indices", "is_open"),
        [Input("open-modal-analisis-indices", "n_clicks"), Input("close-modal-analisis-indices", "n_clicks")],
        [State("modal-analisis-indices", "is_open")]
    )
    def toggle_modal_analisis_indices(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal comparación satelital
    @app.callback(
        Output("modal-comparacion-satelital", "is_open"),
        [Input("open-modal-comparacion-satelital", "n_clicks"), Input("close-modal-comparacion-satelital", "n_clicks")],
        [State("modal-comparacion-satelital", "is_open")]
    )
    def toggle_modal_comparacion_satelital(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal histórico satelital
    @app.callback(
        Output("modal-historico-satelital", "is_open"),
        [Input("open-modal-historico-satelital", "n_clicks"), Input("close-modal-historico-satelital", "n_clicks")],
        [State("modal-historico-satelital", "is_open")]
    )
    def toggle_modal_historico_satelital(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open
    
    # Callback para modal detecciones (general)
    @app.callback(
        Output("modal-detecciones", "is_open"),
        [Input("open-modal-detecciones", "n_clicks"), Input("close-modal-detecciones", "n_clicks")],
        [State("modal-detecciones", "is_open")]
    )
    def toggle_modal_detecciones(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal filtros de detecciones
    @app.callback(
        Output("modal-detecciones-filtros", "is_open"),
        [Input("open-modal-detecciones-filtros", "n_clicks"), Input("close-modal-detecciones-filtros", "n_clicks")],
        [State("modal-detecciones-filtros", "is_open")]
    )
    def toggle_modal_detecciones_filtros(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal métricas de detecciones
    @app.callback(
        Output("modal-detecciones-metricas", "is_open"),
        [Input("open-modal-detecciones-metricas", "n_clicks"), Input("close-modal-detecciones-metricas", "n_clicks")],
        [State("modal-detecciones-metricas", "is_open")]
    )
    def toggle_modal_detecciones_metricas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal mapa de detecciones
    @app.callback(
        Output("modal-detecciones-mapa", "is_open"),
        [Input("open-modal-detecciones-mapa", "n_clicks"), Input("close-modal-detecciones-mapa", "n_clicks")],
        [State("modal-detecciones-mapa", "is_open")]
    )
    def toggle_modal_detecciones_mapa(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal timeline de detecciones
    @app.callback(
        Output("modal-detecciones-timeline", "is_open"),
        [Input("open-modal-detecciones-timeline", "n_clicks"), Input("close-modal-detecciones-timeline", "n_clicks")],
        [State("modal-detecciones-timeline", "is_open")]
    )
    def toggle_modal_detecciones_timeline(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal distribución de severidad
    @app.callback(
        Output("modal-detecciones-distribucion", "is_open"),
        [Input("open-modal-detecciones-distribucion", "n_clicks"), Input("close-modal-detecciones-distribucion", "n_clicks")],
        [State("modal-detecciones-distribucion", "is_open")]
    )
    def toggle_modal_detecciones_distribucion(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open

    # Callback para modal alertas de detecciones
    @app.callback(
        Output("modal-detecciones-alertas", "is_open"),
        [Input("open-modal-detecciones-alertas", "n_clicks"), Input("close-modal-detecciones-alertas", "n_clicks")],
        [State("modal-detecciones-alertas", "is_open")]
    )
    def toggle_modal_detecciones_alertas(n_open, n_close, is_open):
        if n_open or n_close:
            return not is_open
        return is_open


def register_callbacks(app):
    """Alias para compatibilidad con el sistema de registro global"""
    register_modal_callbacks(app)