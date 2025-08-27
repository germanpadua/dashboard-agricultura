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
    #                              MÓDULO HISTÓRICO
    # ============================================================================
    'general': {
        'title': '📊 Análisis Meteorológico Histórico',
        'sections': [
            {
                'title': 'Controles de Visualización Inteligentes',
                'icon': 'fa-sliders-h',
                'content': html.Div([
                    html.P([
                        "El panel de controles le permite personalizar el análisis temporal ",
                        "para obtener insights específicos de las condiciones meteorológicas ",
                        "que afectan a su olivar:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H6("⏰ Selector de Período"),
                            html.Ul([
                                html.Li([html.Strong("1 Semana:"), " Para análisis de condiciones recientes y tendencias inmediatas"]),
                                html.Li([html.Strong("1 Mes:"), " Ideal para evaluar ciclos mensuales y patrones de riego"]),
                                html.Li([html.Strong("3 Meses:"), " Perfecto para análisis estacional y planificación agrícola"]),
                                html.Li([html.Strong("Todo:"), " Vista completa del histórico para análisis de tendencias anuales"])
                            ])
                        ], md=6),
                        dbc.Col([
                            html.H6("📈 Opciones de Agrupación"),
                            html.Ul([
                                html.Li([html.Strong("Diario:"), " Datos detallados día por día, ideal para seguimiento preciso"]),
                                html.Li([html.Strong("Semanal:"), " Promedios semanales para identificar patrones climáticos"]),
                                html.Li([html.Strong("Mensual:"), " Visión global de tendencias estacionales y anuales"])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-lightbulb me-2"),
                        html.Strong("💡 Consejo Profesional: "),
                        "Para detectar condiciones favorables al repilo, use períodos de 1 mes con agrupación diaria en otoño/invierno."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    'weather': {
        'title': '🌤️ Estado Meteorológico Actual',
        'sections': [
            {
                'title': 'Interpretación de Métricas en Tiempo Real',
                'icon': 'fa-cloud-sun',
                'content': html.Div([
                    html.P([
                        "El panel meteorológico muestra las condiciones más recientes registradas ",
                        "en su estación. Estos datos son fundamentales para tomar decisiones ",
                        "inmediatas sobre tratamientos y labores agrícolas."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-thermometer-half me-2"),
                                    html.Strong("Temperatura Actual")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    html.P("Valor instantáneo crítico para:", className="mb-2"),
                                    html.Ul([
                                        html.Li("Desarrollo de enfermedades fúngicas"),
                                        html.Li("Actividad de plagas"),
                                        html.Li("Eficacia de tratamientos"),
                                        html.Li("Estrés hídrico del cultivo")
                                    ], className="small")
                                ])
                            ], className="h-100")
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-tint me-2"),
                                    html.Strong("Humedad Relativa")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    html.P("Factor determinante en:", className="mb-2"),
                                    html.Ul([
                                        html.Li("Germinación de esporas fúngicas"),
                                        html.Li("Condiciones de infección"),
                                        html.Li("Evapotranspiración del cultivo"),
                                        html.Li("Eficiencia del riego")
                                    ], className="small")
                                ])
                            ], className="h-100")
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-cloud-rain me-2"),
                                    html.Strong("Precipitación")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    html.P("Influye directamente en:", className="mb-2"),
                                    html.Ul([
                                        html.Li("Dispersión de esporas del repilo"),
                                        html.Li("Humedad foliar prolongada"),
                                        html.Li("Programación del riego"),
                                        html.Li("Acceso al campo para labores")
                                    ], className="small")
                                ])
                            ], className="h-100")
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-wind me-2"),
                                    html.Strong("Viento")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    html.P("Afecta a:", className="mb-2"),
                                    html.Ul([
                                        html.Li("Dispersión aérea de patógenos"),
                                        html.Li("Secado de la humedad foliar"),
                                        html.Li("Deriva de tratamientos"),
                                        html.Li("Stress mecánico en plantas")
                                    ], className="small")
                                ])
                            ], className="h-100")
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    'temperatura': {
        'title': '🌡️ Análisis de Temperatura y Repilo',
        'sections': [
            {
                'title': 'Interpretación del Gráfico de Temperaturas',
                'icon': 'fa-chart-area',
                'content': html.Div([
                    html.P([
                        "El gráfico de temperatura muestra tres curvas fundamentales para ",
                        "el monitoreo del riesgo de repilo en olivar:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H6([
                                    html.Span("━", style={'color': '#1f77b4', 'fontSize': '2rem'}),
                                    " Temperatura Mínima"
                                ], className="mb-2"),
                                html.P("Representa las temperaturas nocturnas, críticas para la formación de rocío y humedad foliar.", className="small text-muted")
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H6([
                                    html.Span("━", style={'color': '#d62728', 'fontSize': '2rem'}),
                                    " Temperatura Media"
                                ], className="mb-2"),
                                html.P("Promedio diario, mejor indicador para modelos epidemiológicos de enfermedades.", className="small text-muted")
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H6([
                                    html.Span("┅┅", style={'color': '#d62728', 'fontSize': '1.5rem'}),
                                    " Temperatura Máxima"
                                ], className="mb-2"),
                                html.P("Picos diurnos que pueden inhibir el desarrollo fúngico si son excesivos.", className="small text-muted")
                            ])
                        ], md=4)
                    ]),
                    html.P([
                        html.Strong("Área sombreada: "),
                        "Muestra el rango térmico diario [mín-máx], indicador de la amplitud térmica."
                    ], className="mt-3 small")
                ])
            },
            {
                'title': 'Zonas de Riesgo para Repilo (Spilocaea oleagina)',
                'icon': 'fa-thermometer-half',
                'content': html.Div([
                    html.P([
                        "El repilo es extremadamente sensible a la temperatura. La siguiente guía ",
                        "le ayudará a interpretar el riesgo según los rangos térmicos:"
                    ]),
                    dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "🔴 RIESGO MÁXIMO: 8-24°C"
                        ], className="alert-heading text-danger"),
                        html.P([
                            html.Strong("Temperatura óptima: 15°C"),
                            " - Condiciones ideales para germinación de esporas, penetración foliar y desarrollo de lesiones.",
                        ]),
                        html.P([
                            html.Strong("Acción requerida: "),
                            "Monitoreo diario, aplicación preventiva de fungicidas si se combina con humedad >90% y lluvia."
                        ], className="mb-0")
                    ], color="danger"),
                    
                    dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-exclamation-circle me-2"),
                            "🟡 RIESGO MODERADO: 5-8°C y 24-30°C"
                        ], className="alert-heading text-warning"),
                        html.P("Desarrollo más lento pero aún activo. La infección puede producirse con humedad prolongada."),
                        html.P([
                            html.Strong("Acción requerida: "),
                            "Vigilancia reforzada, considerar tratamiento si las condiciones persisten."
                        ], className="mb-0")
                    ], color="warning"),
                    
                    dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-check-circle me-2"),
                            "🟢 RIESGO BAJO: <5°C o >30°C"
                        ], className="alert-heading text-success"),
                        html.P("Temperaturas adversas que inhiben significativamente el desarrollo del patógeno."),
                        html.P([
                            html.Strong("Situación: "),
                            "Condiciones naturalmente protectivas, mantenimiento rutinario del cultivo."
                        ], className="mb-0")
                    ], color="success")
                ])
            }
        ]
    },
    
    'precipitacion': {
        'title': '🌧️ Precipitación, Humedad y Riesgo Fúngico',
        'sections': [
            {
                'title': 'Interpretación del Gráfico Dual',
                'icon': 'fa-chart-bar',
                'content': html.Div([
                    html.P([
                        "Este gráfico combina dos variables críticas para la epidemiología del repilo:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([
                                        html.I(className="fas fa-cloud-rain me-2 text-primary"),
                                        "Precipitación (mm)"
                                    ]),
                                    html.P("Barras azules en eje izquierdo", className="small text-muted"),
                                    html.P([
                                        html.Strong("Función: "),
                                        "Dispersión de conidias, creación de microclima húmedo, lavado de tratamientos."
                                    ], className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([
                                        html.I(className="fas fa-tint me-2 text-info"),
                                        "Humedad Relativa (%)"
                                    ]),
                                    html.P("Línea naranja en eje derecho", className="small text-muted"),
                                    html.P([
                                        html.Strong("Función: "),
                                        "Ambiente necesario para germinación y desarrollo de estructuras fúngicas."
                                    ], className="small")
                                ])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Combinación crítica: "),
                        "Picos simultáneos de lluvia (>1mm) + humedad sostenida (>90%) + temperatura 15°C = MÁXIMO RIESGO"
                    ], color="warning", className="mt-3")
                ])
            },
            {
                'title': 'Condiciones de Infección del Repilo',
                'icon': 'fa-cloud-rain',
                'content': html.Div([
                    html.P([
                        "Para que se produzca infección por repilo se requiere la combinación ",
                        "precisa de múltiples factores ambientales:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-droplet me-2 text-primary"),
                                    html.Strong("Humedad Foliar Crítica")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li([html.Strong("Duración: "), "≥12 horas continuas de humedad foliar ≥98%"]),
                                        html.Li([html.Strong("Temperatura: "), "Entre 15-20°C durante el período húmedo"]),
                                        html.Li([html.Strong("Fuente: "), "Rocío, niebla, lluvia ligera o riego por aspersión"]),
                                        html.Li([html.Strong("Momento: "), "Especialmente crítico durante la noche y madrugada"])
                                    ], className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-wind me-2 text-success"),
                                    html.Strong("Dispersión por Lluvia")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li([html.Strong("Intensidad mínima: "), "≥1mm para generar salpicaduras efectivas"]),
                                        html.Li([html.Strong("Mecanismo: "), "Las gotas arrastran conidias desde lesiones"]),
                                        html.Li([html.Strong("Distancia: "), "Dispersión local entre hojas y ramas cercanas"]),
                                        html.Li([html.Strong("Timing: "), "Mayor riesgo si llueve sobre follaje ya infectado"])
                                    ], className="small")
                                ])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.H6([
                            html.I(className="fas fa-calendar-alt me-2"),
                            "Período de Mayor Riesgo"
                        ], className="alert-heading"),
                        html.P([
                            html.Strong("Otoño-Invierno (Octubre-Febrero): "),
                            "Temperaturas moderadas + humedad alta + lluvias frecuentes = Condiciones ideales para epidemias de repilo."
                        ], className="mb-0")
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    # ============================================================================
    #                            MÓDULO PREDICCIÓN
    # ============================================================================
    'prediccion': {
        'title': '🔮 Pronóstico Meteorológico Agrícola',
        'sections': [
            {
                'title': 'Funcionalidad del Módulo de Predicción',
                'icon': 'fa-cloud-sun',
                'content': html.Div([
                    html.P([
                        "El módulo de predicción utiliza datos de AEMET para proporcionar ",
                        "pronósticos meteorológicos específicos que permiten planificar ",
                        "las labores agrícolas con anticipación."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([
                                        html.I(className="fas fa-calendar-week me-2"),
                                        "Predicción a 7 Días"
                                    ], className="text-primary"),
                                    html.P("Pronóstico detallado día por día con temperaturas máximas, mínimas y precipitación esperada.", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6([
                                        html.I(className="fas fa-clock me-2"),
                                        "Predicción a 48 Horas"
                                    ], className="text-info"),
                                    html.P("Evolución hora por hora de temperatura, humedad y precipitación para planificación inmediata.", className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    'municipio': {
        'title': '🏘️ Selección de Municipio para Pronósticos',
        'sections': [
            {
                'title': 'Uso del Selector de Ubicación',
                'icon': 'fa-map-marker-alt',
                'content': html.Div([
                    html.P([
                        "Seleccione su municipio para obtener pronósticos meteorológicos ",
                        "específicos de su zona. El sistema utiliza la red de estaciones ",
                        "de AEMET para proporcionar datos precisos."
                    ]),
                    html.H6("🔍 Funciones del Selector:"),
                    html.Ul([
                        html.Li([html.Strong("Búsqueda inteligente: "), "Escriba las primeras letras para filtrar la lista"]),
                        html.Li([html.Strong("Autocompletado: "), "El sistema sugiere municipios mientras escribe"]),
                        html.Li([html.Strong("Validación: "), "Solo municipios con estación meteorológica disponible"]),
                        html.Li([html.Strong("Por defecto: "), "Benalua se establece como ubicación inicial"])
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong("Nota: "),
                        "Los pronósticos son más precisos para municipios con estaciones meteorológicas cercanas. ",
                        "Para ubicaciones sin estación propia, se interpolan datos de estaciones vecinas."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    'pred_semanal': {
        'title': '📅 Pronóstico Semanal Detallado',
        'sections': [
            {
                'title': 'Interpretación de las Tarjetas Diarias',
                'icon': 'fa-calendar-alt',
                'content': html.Div([
                    html.P([
                        "Cada tarjeta diaria presenta un resumen completo de las condiciones ",
                        "meteorológicas previstas, optimizado para toma de decisiones agrícolas."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H6("📊 Información por Tarjeta:"),
                            html.Ul([
                                html.Li([html.Strong("Día y fecha: "), "Identificación clara del día de la semana y fecha"]),
                                html.Li([html.Strong("Temperaturas: "), "Máxima y mínima esperadas en °C"]),
                                html.Li([html.Strong("Precipitación: "), "Cantidad esperada en mm y probabilidad"]),
                                html.Li([html.Strong("Icono meteorológico: "), "Representación visual del estado del tiempo"])
                            ])
                        ], md=6),
                        dbc.Col([
                            html.H6("🎯 Aplicaciones Prácticas:"),
                            html.Ul([
                                html.Li([html.Strong("Tratamientos: "), "Planificar aplicaciones cuando no se prevea lluvia"]),
                                html.Li([html.Strong("Riego: "), "Ajustar programación según lluvia esperada"]),
                                html.Li([html.Strong("Laboreo: "), "Programar tareas de campo en días secos"]),
                                html.Li([html.Strong("Cosecha: "), "Optimizar momentos de recolección"])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-lightbulb me-2"),
                        html.Strong("Recomendación: "),
                        "Revise el pronóstico cada mañana para ajustar las labores del día. ",
                        "Planifique tratamientos con al menos 24h sin lluvia posterior."
                    ], color="success", className="mt-3")
                ])
            }
        ]
    },
    
    'pred_horaria': {
        'title': '⏰ Evolución Meteorológica 48 Horas',
        'sections': [
            {
                'title': 'Interpretación del Gráfico Horario',
                'icon': 'fa-chart-line',
                'content': html.Div([
                    html.P([
                        "El gráfico horario muestra la evolución detallada de las variables ",
                        "meteorológicas para las próximas 48 horas, permitiendo timing preciso ",
                        "de las intervenciones agrícolas."
                    ]),
                    html.H6("📈 Variables Monitorizadas:"),
                    dbc.Row([
                        dbc.Col([
                            html.Ul([
                                html.Li([html.Strong("Temperatura (°C): "), "Evolución horaria para detectar heladas o picos de calor"]),
                                html.Li([html.Strong("Humedad Relativa (%): "), "Fundamental para riesgo de enfermedades"]),
                                html.Li([html.Strong("Precipitación (mm): "), "Momento exacto e intensidad de lluvias"])
                            ])
                        ], md=12)
                    ]),
                    html.H6("🕐 Aplicaciones por Horario:"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("🌅 Madrugada (00:00-06:00)"),
                                    html.P("Detección de rocío, heladas y condiciones de máxima humedad.", className="small")
                                ])
                            ])
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("🌞 Mañana (06:00-12:00)"),
                                    html.P("Momento óptimo para tratamientos, condiciones estables.", className="small")
                                ])
                            ])
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("☀️ Tarde (12:00-18:00)"),
                                    html.P("Picos de temperatura, evitación de aplicaciones.", className="small")
                                ])
                            ])
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("🌙 Noche (18:00-00:00)"),
                                    html.P("Subida de humedad, formación de rocío nocturno.", className="small")
                                ])
                            ])
                        ], md=3)
                    ])
                ])
            }
        ]
    },
    
    # ============================================================================
    #                          MÓDULO DATOS SATELITALES
    # ============================================================================
    'satelital': {
        'title': '🛰️ Análisis Satelital de Cultivos',
        'sections': [
            {
                'title': 'Tecnología y Fuentes de Datos',
                'icon': 'fa-satellite',
                'content': html.Div([
                    html.P([
                        "El módulo satelital utiliza imágenes de alta resolución para monitorizar ",
                        "la salud y vigor de los cultivos mediante índices de vegetación científicamente validados."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-satellite me-2"),
                                    html.Strong("Sentinel-2 ESA")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li("Resolución espacial: 10m por píxel"),
                                        html.Li("Frecuencia: Cada 5 días (condiciones óptimas)"),
                                        html.Li("Bandas espectrales: 13 bandas multiespectrales"),
                                        html.Li("Cobertura: Global y gratuita")
                                    ], className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-leaf me-2"),
                                    html.Strong("Índices Calculados")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li("NDVI: Índice de Vegetación Normalizado"),
                                        html.Li("OSAVI: Índice Optimizado Ajustado al Suelo"),
                                        html.Li("NDRE: Índice Red-Edge Normalizado"),
                                        html.Li("Anomalías: Detección de cambios temporales")
                                    ], className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    'ndvi': {
        'title': '🌱 Interpretación del NDVI en Olivicultura',
        'sections': [
            {
                'title': '¿Qué es el NDVI?',
                'icon': 'fa-leaf',
                'content': html.Div([
                    html.P([
                        "El NDVI (Normalized Difference Vegetation Index) es el índice más utilizado ",
                        "para evaluar la salud y vigor de la vegetación. Se calcula mediante la fórmula:"
                    ]),
                    dbc.Alert([
                        html.Div([
                            html.H5("NDVI = (NIR - RED) / (NIR + RED)", className="text-center"),
                            html.P([
                                html.Strong("NIR: "), "Infrarrojo Cercano (Banda 8, 842nm) | ",
                                html.Strong("RED: "), "Rojo Visible (Banda 4, 665nm)"
                            ], className="text-center small mb-0")
                        ])
                    ], color="light", className="text-center"),
                    html.P([
                        "Este índice explota el hecho de que la vegetación sana refleja fuertemente ",
                        "en el infrarrojo cercano y absorbe en el rojo visible debido a la clorofila."
                    ])
                ])
            },
            {
                'title': 'Escala de Interpretación para Olivar',
                'icon': 'fa-palette',
                'content': html.Div([
                    html.P([
                        "La siguiente tabla muestra cómo interpretar los valores NDVI específicamente ",
                        "para cultivos de olivo y su representación en el mapa:"
                    ]),
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Color"),
                                html.Th("Rango NDVI"),
                                html.Th("Interpretación Agrícola"),
                                html.Th("Acción Recomendada")
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#004400', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.6 - 1.0"),
                                html.Td("🌿 Vegetación muy vigorosa"),
                                html.Td("Monitoreo rutinario, óptimo estado")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#0f540a', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.5 - 0.6"),
                                html.Td("✅ Buena salud vegetativa"),
                                html.Td("Estado normal, mantenimiento estándar")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#306d1c', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.4 - 0.5"),
                                html.Td("⚠️ Salud moderada"),
                                html.Td("Investigar causas, evaluar riego/nutrición")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#70a33f', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.2 - 0.4"),
                                html.Td("🚨 Vegetación en estrés"),
                                html.Td("Intervención necesaria: riego, fertilización")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#ccc682', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.1 - 0.2"),
                                html.Td("⚡ Vegetación severamente estresada"),
                                html.Td("Diagnóstico urgente y tratamiento intensivo")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#eaeaea', 'border': '1px solid #ccc'
                                })),
                                html.Td("0.0 - 0.1"),
                                html.Td("❌ Suelo desnudo o vegetación muerta"),
                                html.Td("Replantación o recuperación de suelo")
                            ]),
                            html.Tr([
                                html.Td(html.Div(style={
                                    'width': '30px', 'height': '20px',
                                    'backgroundColor': '#0000ff', 'border': '1px solid #ccc'
                                })),
                                html.Td("< 0"),
                                html.Td("💧 Agua o superficies no vegetales"),
                                html.Td("Normal para zonas de agua o infraestructuras")
                            ])
                        ])
                    ], striped=True, hover=True, className="mt-3")
                ])
            }
        ]
    },
    
    # ============================================================================
    #                         MÓDULO DETECCIONES
    # ============================================================================
    'detecciones': {
        'title': '🔬 Sistema de Detección de Enfermedades',
        'sections': [
            {
                'title': 'Funcionalidad del Módulo',
                'icon': 'fa-microscope',
                'content': html.Div([
                    html.P([
                        "El módulo de detecciones integra reportes de campo enviados por agricultores ",
                        "a través del bot de Telegram, creando un sistema de monitoreo colaborativo ",
                        "de enfermedades del olivar en tiempo real."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fab fa-telegram me-2"),
                                    html.Strong("Bot de Telegram")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li("Reportes georreferenciados desde campo"),
                                        html.Li("Fotos de síntomas y severidad"),
                                        html.Li("Clasificación automática por IA"),
                                        html.Li("Base de datos centralizada")
                                    ], className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-chart-bar me-2"),
                                    html.Strong("Análisis Integrado")
                                ]),
                                dbc.CardBody([
                                    html.Ul([
                                        html.Li("Mapas de incidencia por severidad"),
                                        html.Li("Evolución temporal de brotes"),
                                        html.Li("Correlación con datos meteorológicos"),
                                        html.Li("Alertas automáticas de riesgo")
                                    ], className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    'filtros-detecciones': {
        'title': '🔍 Controles de Filtrado de Detecciones',
        'sections': [
            {
                'title': 'Uso de los Filtros Temporales y de Severidad',
                'icon': 'fa-filter',
                'content': html.Div([
                    html.P([
                        "Los controles le permiten personalizar la visualización de detecciones ",
                        "para análisis específicos según período temporal y nivel de severidad."
                    ]),
                    html.H6("📅 Filtros Temporales:"),
                    dbc.Row([
                        dbc.Col([
                            html.Ul([
                                html.Li([html.Strong("Última Semana: "), "Brotes más recientes, situación actual"]),
                                html.Li([html.Strong("Último Mes: "), "Tendencias mensuales y desarrollo de epidemias"]),
                                html.Li([html.Strong("Todo: "), "Vista histórica completa para análisis estacional"])
                            ])
                        ], md=6),
                        dbc.Col([
                            html.H6("🎯 Filtro por Severidad:"),
                            html.Ul([
                                html.Li([html.Strong("Nivel 1-2: "), "Infecciones iniciales y leves"]),
                                html.Li([html.Strong("Nivel 3: "), "Infecciones moderadas"]),
                                html.Li([html.Strong("Nivel 4-5: "), "Infecciones severas y críticas"])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-sync-alt me-2"),
                        html.Strong("Actualización: "),
                        "Use el botón 'Actualizar' para sincronizar con los últimos reportes del bot."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    # ============================================================================
    #                           MÓDULO FINCAS
    # ============================================================================
    'nueva-finca': {
        'title': '📝 Registro de Nuevas Fincas',
        'sections': [
            {
                'title': 'Proceso de Registro Paso a Paso',
                'icon': 'fa-edit',
                'content': html.Div([
                    html.P([
                        "El sistema de registro de fincas permite crear, editar y gestionar ",
                        "las propiedades agrícolas para su posterior análisis satelital."
                    ]),
                    html.H6("📋 Pasos para Registrar una Finca:"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.Strong("1. Asignar Nombre: "),
                            "Introduzca un nombre descriptivo y único para identificar la parcela."
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("2. Dibujar Polígono: "),
                            "Use las herramientas del mapa para delimitar exactamente los límites de la finca."
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("3. Verificar Área: "),
                            "El sistema calculará automáticamente la superficie en hectáreas."
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("4. Guardar Registro: "),
                            "Confirme los datos y guarde la finca en el sistema."
                        ])
                    ], flush=True),
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong("Nota: "),
                        "Las fincas registradas estarán disponibles inmediatamente para análisis satelital en el módulo correspondiente."
                    ], color="success", className="mt-3")
                ])
            }
        ]
    },
    
    'mapa-fincas': {
        'title': '🗺️ Herramientas de Mapeo Interactivo',
        'sections': [
            {
                'title': 'Uso de las Herramientas de Dibujo',
                'icon': 'fa-draw-polygon',
                'content': html.Div([
                    html.P([
                        "El mapa interactivo incluye herramientas profesionales de dibujo ",
                        "para delimitar con precisión los límites de sus parcelas agrícolas."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H6("🖊️ Herramientas Disponibles:"),
                            html.Ul([
                                html.Li([html.Strong("Polígono: "), "Trace límites irregulares siguiendo exactamente los bordes de la parcela"]),
                                html.Li([html.Strong("Rectángulo: "), "Para parcelas de forma regular y geométrica"]),
                                html.Li([html.Strong("Edición: "), "Modifique puntos de los polígonos ya creados"]),
                                html.Li([html.Strong("Eliminación: "), "Borre formas incorrectas o no deseadas"])
                            ])
                        ], md=6),
                        dbc.Col([
                            html.H6("🛰️ Capas Base:"),
                            html.Ul([
                                html.Li([html.Strong("Vista Satelital: "), "Imágenes de alta resolución para identificar cultivos"]),
                                html.Li([html.Strong("Vista de Calles: "), "Mapas tradicionales con toponimia"]),
                                html.Li([html.Strong("Híbrida: "), "Combinación de ambas vistas"]),
                                html.Li([html.Strong("Zoom Adaptativo: "), "Ajuste automático al área de trabajo"])
                            ])
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-mouse-pointer me-2"),
                        html.Strong("Consejo: "),
                        "Para mayor precisión, use la vista satelital y haga zoom hasta ver claramente los límites de la parcela antes de dibujar."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    'gestion-fincas': {
        'title': '📋 Gestión de Fincas Registradas',
        'sections': [
            {
                'title': 'Operaciones Disponibles',
                'icon': 'fa-tasks',
                'content': html.Div([
                    html.P([
                        "Una vez registradas, las fincas pueden ser gestionadas completamente ",
                        "a través del panel de administración con las siguientes funciones:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-search-location me-2"),
                                    html.Strong("Localización")
                                ]),
                                dbc.CardBody([
                                    html.P("Centrar mapa automáticamente en la finca seleccionada para revisión visual.", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-edit me-2"),
                                    html.Strong("Edición")
                                ]),
                                dbc.CardBody([
                                    html.P("Modificar nombre, ajustar límites geográficos o actualizar información.", className="small")
                                ])
                            ])
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-satellite me-2"),
                                    html.Strong("Análisis Satelital")
                                ]),
                                dbc.CardBody([
                                    html.P("Las fincas registradas aparecen automáticamente en el módulo de datos satelitales.", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-trash me-2"),
                                    html.Strong("Eliminación")
                                ]),
                                dbc.CardBody([
                                    html.P("Borrar fincas obsoletas con confirmación de seguridad.", className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    # ============================================================================
    #                       SISTEMA DE ALERTAS
    # ============================================================================
    'alertas': {
        'title': '🚨 Sistema Inteligente de Alertas Agrícolas',
        'sections': [
            {
                'title': 'Niveles de Alerta y Acciones Recomendadas',
                'icon': 'fa-exclamation-triangle',
                'content': html.Div([
                    html.P([
                        "El sistema de alertas integra datos meteorológicos, modelos epidemiológicos ",
                        "y reportes de campo para proporcionar notificaciones inteligentes sobre ",
                        "riesgo de enfermedades y condiciones adversas."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("CRÍTICA", color="danger", className="me-2"),
                                    html.Strong("Intervención Inmediata", style={'color': '#dc3545'})
                                ]),
                                dbc.CardBody([
                                    html.P([
                                        html.Strong("Condiciones: "), 
                                        "Temperatura 15°C + Humedad >95% + Lluvia reciente"
                                    ], className="small"),
                                    html.P([html.Strong("Acciones:")], className="small mb-2 text-danger"),
                                    html.Ul([
                                        html.Li("Aplicar tratamiento fungicida en 24-48h"),
                                        html.Li("Inspeccionar parcelas diariamente"),
                                        html.Li("Preparar segunda aplicación si persiste humedad"),
                                        html.Li("Suspender riego por aspersión")
                                    ], className="small")
                                ])
                            ], className="border-danger")
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("ALTA", color="warning", className="me-2"),
                                    html.Strong("Precaución Elevada", style={'color': '#fd7e14'})
                                ]),
                                dbc.CardBody([
                                    html.P([
                                        html.Strong("Condiciones: "), 
                                        "Factores de riesgo presentes, desarrollo epidémico probable"
                                    ], className="small"),
                                    html.P([html.Strong("Acciones:")], className="small mb-2 text-warning"),
                                    html.Ul([
                                        html.Li("Monitorizar evolución meteorológica"),
                                        html.Li("Preparar equipo de aplicación"),
                                        html.Li("Revisar zonas más sensibles del cultivo"),
                                        html.Li("Evaluar estado nutricional del olivo")
                                    ], className="small")
                                ])
                            ], className="border-warning")
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("MEDIA", color="info", className="me-2"),
                                    html.Strong("Atención Rutinaria", style={'color': '#0dcaf0'})
                                ]),
                                dbc.CardBody([
                                    html.P([
                                        html.Strong("Condiciones: "), 
                                        "Algunos factores de riesgo, vigilancia recomendada"
                                    ], className="small"),
                                    html.P([html.Strong("Acciones:")], className="small mb-2 text-info"),
                                    html.Ul([
                                        html.Li("Mantener vigilancia rutinaria"),
                                        html.Li("Revisar pronóstico meteorológico extendido"),
                                        html.Li("Documentar observaciones de campo"),
                                        html.Li("Optimizar ventilación del cultivo")
                                    ], className="small")
                                ])
                            ], className="border-info")
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("BAJA", color="success", className="me-2"),
                                    html.Strong("Condiciones Favorables", style={'color': '#198754'})
                                ]),
                                dbc.CardBody([
                                    html.P([
                                        html.Strong("Condiciones: "), 
                                        "Ambiente no favorable para desarrollo de enfermedades"
                                    ], className="small"),
                                    html.P([html.Strong("Acciones:")], className="small mb-2 text-success"),
                                    html.Ul([
                                        html.Li("Mantenimiento rutinario del olivar"),
                                        html.Li("Planificar próximas labores agrícolas"),
                                        html.Li("Revisar estado general de la plantación"),
                                        html.Li("Momento óptimo para podas y fertilización")
                                    ], className="small")
                                ])
                            ], className="border-success")
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    # ============================================================================
    #                         MODALES ADICIONALES PARA DETECCIONES
    # ============================================================================
    'metricas-detecciones': {
        'title': '📊 Métricas de Detección de Enfermedades',
        'sections': [
            {
                'title': 'Interpretación de las Tarjetas Métricas',
                'icon': 'fa-chart-bar',
                'content': html.Div([
                    html.P([
                        "Las tarjetas de métricas proporcionan un resumen estadístico completo ",
                        "de las detecciones de repilo registradas en el sistema:"
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-calculator me-2"),
                                    html.Strong("Total de Detecciones")
                                ]),
                                dbc.CardBody([
                                    html.P("Número total de reportes registrados en el período seleccionado", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-chart-line me-2"),
                                    html.Strong("Severidad Promedio")
                                ]),
                                dbc.CardBody([
                                    html.P("Nivel medio de severidad de todas las detecciones (1-5)", className="small")
                                ])
                            ])
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-calendar-alt me-2"),
                                    html.Strong("Detecciones Recientes")
                                ]),
                                dbc.CardBody([
                                    html.P("Número de reportes en los últimos 7 días", className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.I(className="fas fa-trending-up me-2"),
                                    html.Strong("Tendencia")
                                ]),
                                dbc.CardBody([
                                    html.P("Indicador de aumento o disminución de casos", className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    'detecciones-metricas': {
        'title': '📊 Métricas de Detección de Enfermedades',
        'sections': [
            {
                'title': 'Interpretación de las Tarjetas Métricas',
                'icon': 'fa-chart-bar',
                'content': html.Div([
                    html.P([
                        "Las tarjetas de métricas proporcionan un resumen estadístico completo ",
                        "de las detecciones de repilo registradas en el sistema."
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Strong("Actualización: "),
                        "Las métricas se actualizan automáticamente cada vez que se sincronizan nuevos reportes del bot de Telegram."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    'detecciones-mapa': {
        'title': '🗺️ Mapa de Detecciones Georreferenciadas',
        'sections': [
            {
                'title': 'Navegación e Interpretación del Mapa',
                'icon': 'fa-map-marked-alt',
                'content': html.Div([
                    html.P([
                        "El mapa muestra la ubicación exacta de cada reporte de enfermedad ",
                        "enviado por los agricultores a través del bot de Telegram."
                    ]),
                    html.H6("🎯 Capas por Severidad:"),
                    html.Ul([
                        html.Li([html.Strong("Severidad 1-2: "), "Marcadores verdes - Infecciones leves"]),
                        html.Li([html.Strong("Severidad 3: "), "Marcadores amarillos - Infecciones moderadas"]),
                        html.Li([html.Strong("Severidad 4-5: "), "Marcadores rojos - Infecciones severas"])
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-mouse-pointer me-2"),
                        html.Strong("Interacción: "),
                        "Haga clic en cualquier marcador para ver detalles del reporte, incluyendo fecha, severidad y observaciones."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    'detecciones-timeline': {
        'title': '⏳ Evolución Temporal de Detecciones',
        'sections': [
            {
                'title': 'Interpretación del Gráfico de Línea Temporal',
                'icon': 'fa-chart-line',
                'content': html.Div([
                    html.P([
                        "Este gráfico muestra la evolución de las detecciones de repilo ",
                        "a lo largo del tiempo, permitiendo identificar picos epidémicos ",
                        "y patrones estacionales."
                    ]),
                    html.H6("📈 Qué Buscar:"),
                    html.Ul([
                        html.Li([html.Strong("Picos de detección: "), "Incrementos súbitos que indican brotes"]),
                        html.Li([html.Strong("Tendencias estacionales: "), "Patrones que se repiten anualmente"]),
                        html.Li([html.Strong("Períodos de baja actividad: "), "Momentos de menor incidencia"]),
                        html.Li([html.Strong("Correlación meteorológica: "), "Aumentos tras períodos húmedos"])
                    ])
                ])
            }
        ]
    },
    
    'detecciones-distribucion': {
        'title': '🧮 Distribución de Severidad',
        'sections': [
            {
                'title': 'Interpretación del Gráfico Circular',
                'icon': 'fa-chart-pie',
                'content': html.Div([
                    html.P([
                        "El gráfico circular muestra la proporción de reportes en cada ",
                        "nivel de severidad, proporcionando una visión general del ",
                        "estado sanitario del olivar en la región."
                    ]),
                    html.H6("🎯 Interpretación por Colores:"),
                    html.Ul([
                        html.Li([html.Strong("Verde: "), "Severidad 1-2 (Leve) - Situación controlable"]),
                        html.Li([html.Strong("Amarillo: "), "Severidad 3 (Moderado) - Requiere atención"]),
                        html.Li([html.Strong("Rojo: "), "Severidad 4-5 (Severo) - Acción inmediata necesaria"])
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Alerta: "),
                        "Si más del 30% de las detecciones son de severidad 4-5, considere implementar medidas preventivas intensivas."
                    ], color="warning", className="mt-3")
                ])
            }
        ]
    },
    
    'detecciones-alertas': {
        'title': '🚨 Estado de Alertas por Detecciones',
        'sections': [
            {
                'title': 'Sistema de Alertas Basado en Reportes',
                'icon': 'fa-exclamation-triangle',
                'content': html.Div([
                    html.P([
                        "El sistema de alertas analiza los reportes recientes y genera ",
                        "recomendaciones automáticas basadas en la frecuencia, severidad ",
                        "y distribución geográfica de las detecciones."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("ALERTA ROJA", color="danger", className="me-2"),
                                    html.Strong("Epidemia Activa")
                                ]),
                                dbc.CardBody([
                                    html.P("Múltiples reportes de alta severidad en área concentrada", className="small"),
                                    html.P([html.Strong("Acción: "), "Tratamiento inmediato y monitoreo intensivo"], className="small")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Badge("VIGILANCIA", color="warning", className="me-2"),
                                    html.Strong("Actividad Moderada")
                                ]),
                                dbc.CardBody([
                                    html.P("Incremento gradual en reportes", className="small"),
                                    html.P([html.Strong("Acción: "), "Reforzar vigilancia y preparar tratamientos"], className="small")
                                ])
                            ])
                        ], md=6)
                    ])
                ])
            }
        ]
    },
    
    # ============================================================================
    #                         MODALES ADICIONALES PARA FINCAS
    # ============================================================================
    'estadisticas': {
        'title': '📊 Estadísticas de Fincas Registradas',
        'sections': [
            {
                'title': 'Interpretación de las Métricas',
                'icon': 'fa-chart-bar',
                'content': html.Div([
                    html.P([
                        "Las estadísticas muestran un resumen cuantitativo de todas las ",
                        "fincas registradas en el sistema, incluyendo superficie total ",
                        "y distribución por tamaños."
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H6("📏 Superficie Total"),
                            html.P("Suma de todas las áreas registradas en hectáreas", className="small")
                        ], md=6),
                        dbc.Col([
                            html.H6("🔢 Número de Parcelas"),
                            html.P("Cantidad total de fincas registradas en el sistema", className="small")
                        ], md=6)
                    ]),
                    dbc.Alert([
                        html.I(className="fas fa-calculator me-2"),
                        html.Strong("Cálculo Automático: "),
                        "Las estadísticas se actualizan automáticamente cada vez que se registra, modifica o elimina una finca."
                    ], color="info", className="mt-3")
                ])
            }
        ]
    },
    
    # ============================================================================
    #                         MODALES ADICIONALES PARA DATOS SATELITALES
    # ============================================================================
    'config-satelital': {
        'title': '⚙️ Configuración del Análisis Satelital',
        'sections': [
            {
                'title': 'Parámetros de Configuración',
                'icon': 'fa-sliders-h',
                'content': html.Div([
                    html.P([
                        "Configure los parámetros del análisis satelital para obtener ",
                        "resultados específicos según sus necesidades agrícolas."
                    ]),
                    html.H6("🗓️ Selección Temporal:"),
                    html.Ul([
                        html.Li([html.Strong("Fecha Inicio: "), "Seleccione el inicio del período de análisis"]),
                        html.Li([html.Strong("Fecha Fin: "), "Defina el final del período de estudio"]),
                        html.Li([html.Strong("Frecuencia: "), "Imágenes disponibles cada 5 días aprox."])
                    ]),
                    html.H6("🌱 Índices de Vegetación:"),
                    html.Ul([
                        html.Li([html.Strong("NDVI: "), "Salud general de la vegetación"]),
                        html.Li([html.Strong("OSAVI: "), "Optimizado para suelos con poca cobertura"]),
                        html.Li([html.Strong("NDRE: "), "Detección temprana de estrés"])
                    ])
                ])
            }
        ]
    },
    
    'config_satelital': {
        'title': '⚙️ Configuración del Análisis Satelital',
        'sections': [
            {
                'title': 'Parámetros de Configuración',
                'icon': 'fa-sliders-h',
                'content': html.Div([
                    html.P([
                        "Configure los parámetros del análisis satelital para obtener ",
                        "resultados específicos según sus necesidades agrícolas."
                    ])
                ])
            }
        ]
    },
    
    'mapa-satelital': {
        'title': '🗺️ Mapa Satelital Interactivo',
        'sections': [
            {
                'title': 'Navegación y Controles del Mapa',
                'icon': 'fa-map',
                'content': html.Div([
                    html.P([
                        "El mapa satelital muestra las imágenes Sentinel-2 procesadas ",
                        "con los índices de vegetación calculados para su finca."
                    ]),
                    html.H6("🎮 Controles Disponibles:"),
                    html.Ul([
                        html.Li([html.Strong("Zoom: "), "Use la rueda del ratón o botones +/- para acercar"]),
                        html.Li([html.Strong("Pan: "), "Arrastre con el ratón para desplazar el mapa"]),
                        html.Li([html.Strong("Capas: "), "Active/desactive diferentes índices"]),
                        html.Li([html.Strong("Opacidad: "), "Ajuste la transparencia de los overlays"])
                    ])
                ])
            }
        ]
    },
    
    'analisis-indices': {
        'title': '📊 Análisis de Índices de Vegetación',
        'sections': [
            {
                'title': 'Interpretación de Gráficos y Estadísticas',
                'icon': 'fa-chart-area',
                'content': html.Div([
                    html.P([
                        "Los gráficos muestran la distribución estadística y evolución ",
                        "temporal de los índices de vegetación en su finca."
                    ]),
                    html.H6("📈 Tipos de Visualización:"),
                    html.Ul([
                        html.Li([html.Strong("Histograma: "), "Distribución de valores en la finca"]),
                        html.Li([html.Strong("Series Temporales: "), "Evolución a lo largo del tiempo"]),
                        html.Li([html.Strong("Estadísticas: "), "Media, mediana, desviación estándar"])
                    ])
                ])
            }
        ]
    },
    
    'comparacion-satelital': {
        'title': '🔄 Comparación Temporal Satelital',
        'sections': [
            {
                'title': 'Análisis Comparativo entre Fechas',
                'icon': 'fa-exchange-alt',
                'content': html.Div([
                    html.P([
                        "Compare imágenes satelitales de diferentes fechas para ",
                        "identificar cambios en la salud y vigor de sus cultivos."
                    ]),
                    html.H6("🔍 Qué Buscar:"),
                    html.Ul([
                        html.Li([html.Strong("Mejoras: "), "Aumentos en valores NDVI (verde más intenso)"]),
                        html.Li([html.Strong("Deterioros: "), "Disminuciones en índices (amarillo/rojo)"]),
                        html.Li([html.Strong("Patrones: "), "Áreas consistentemente problemáticas"]),
                        html.Li([html.Strong("Efectos estacionales: "), "Cambios naturales por época"])
                    ])
                ])
            }
        ]
    },
    
    'historico-satelital': {
        'title': '📈 Histórico de Evolución Satelital',
        'sections': [
            {
                'title': 'Análisis de Tendencias a Largo Plazo',
                'icon': 'fa-chart-line',
                'content': html.Div([
                    html.P([
                        "El análisis histórico muestra la evolución de los índices ",
                        "de vegetación a lo largo de múltiples temporadas, permitiendo ",
                        "identificar tendencias y ciclos estacionales."
                    ]),
                    html.H6("📊 Aplicaciones Prácticas:"),
                    html.Ul([
                        html.Li([html.Strong("Planificación: "), "Identificar mejores épocas para labores"]),
                        html.Li([html.Strong("Problemas recurrentes: "), "Áreas que requieren atención especial"]),
                        html.Li([html.Strong("Eficacia de tratamientos: "), "Evaluar resultados de intervenciones"]),
                        html.Li([html.Strong("Variabilidad climática: "), "Impacto de condiciones meteorológicas"])
                    ])
                ])
            }
        ]
    }
}


def create_chart_help_section(chart_type: str, title: str = None) -> html.Div:
    """
    Crea una sección completa con título, botón de ayuda y modal para un gráfico.
    
    Esta función facilita la creación rápida de secciones con ayuda integrada,
    manteniendo consistencia en el diseño y funcionalidad a lo largo del dashboard.
    
    Args:
        chart_type: Tipo de gráfico/sección ('temperatura', 'precipitacion', 'ndvi', etc.)
        title: Título personalizado (opcional, se genera automáticamente si no se proporciona)
    
    Returns:
        html.Div: Componente completo con título, botón de ayuda y modal integrado
        
    Features:
        • Generación automática de IDs únicos
        • Integración automática con MODAL_CONTENTS
        • Fallback para contenido no definido
        • Diseño consistente y profesional
    """
    modal_id = f"modal-{chart_type}"
    display_title = title or chart_type.replace('_', ' ').title()
    
    # Obtener configuración del modal o crear una por defecto
    modal_config = MODAL_CONTENTS.get(chart_type, {
        'title': f'ℹ️ Información sobre {display_title}',
        'sections': [{
            'title': 'Información No Disponible', 
            'icon': 'fa-info-circle',
            'content': html.P([
                "La documentación para esta sección está en desarrollo. ",
                "Para más información, consulte la documentación técnica del sistema."
            ])
        }]
    })
    
    return html.Div([
        # Header de la sección con título y botón de ayuda
        html.Div([
            html.H5(display_title, className="mb-0", style={
                'color': '#2E7D32',
                'fontWeight': '600'
            }),
            create_help_button(modal_id, "Ayuda", "outline-primary", "sm")
        ], className="d-flex align-items-center justify-content-between mb-3"),
        
        # Modal de información integrado
        create_info_modal(
            modal_id=modal_id,
            title=modal_config['title'],
            content_sections=modal_config['sections']
        )
    ])


# ===============================================================================
#                           SISTEMA DE CALLBACKS AVANZADO
# ===============================================================================

def register_modal_callbacks(app):
    """
    Registra todos los callbacks necesarios para el funcionamiento de los modales de ayuda.
    
    Este sistema de callbacks está optimizado para manejar múltiples modales de forma
    eficiente, evitando conflictos de ID y proporcionando funcionalidad consistente
    a través de todo el dashboard.
    
    Args:
        app: Instancia de la aplicación Dash
        
    Features:
        • Callbacks automáticos para todos los modales definidos
        • Manejo de múltiples botones de cierre por modal
        • Prevención de conflictos de ID
        • Sistema robusto con manejo de errores
        • Compatibilidad con modales dinámicos
    
    Note:
        Esta función debe ejecutarse una sola vez durante la inicialización
        de la aplicación para registrar correctamente todos los callbacks.
    """
    
    # Lista de todos los tipos de modales definidos en MODAL_CONTENTS
    modal_types = list(MODAL_CONTENTS.keys())
    
    # Modales adicionales no incluidos en MODAL_CONTENTS pero usados en layouts
    additional_modals = [
        'config-satelital', 'mapa-satelital', 'analisis-indices', 'comparacion-satelital',
        'historico-satelital', 'detecciones-filtros', 'detecciones-metricas', 
        'detecciones-mapa', 'detecciones-timeline', 'detecciones-distribucion',
        'detecciones-alertas', 'estadisticas', 'pred-semanal', 'pred-horaria'
    ]
    
    # Combinar todas las listas de modales
    all_modals = modal_types + additional_modals
    
    # Registrar callback para cada modal
    for modal_type in all_modals:
        modal_id = f"modal-{modal_type}"
        open_button_id = f"open-{modal_id}"
        close_button_id = f"close-{modal_id}"
        close_alt_button_id = f"close-{modal_id}-alt"
        
        try:
            @app.callback(
                Output(modal_id, "is_open"),
                [
                    Input(open_button_id, "n_clicks"),
                    Input(close_button_id, "n_clicks"),
                    Input(close_alt_button_id, "n_clicks")
                ],
                [State(modal_id, "is_open")],
                prevent_initial_call=True
            )
            def toggle_modal(n_open, n_close, n_close_alt, is_open):
                """
                Callback dinámico para manejar la apertura y cierre de modales.
                
                Args:
                    n_open: Clics en botón de abrir
                    n_close: Clics en botón de cerrar principal
                    n_close_alt: Clics en botón de cerrar alternativo
                    is_open: Estado actual del modal
                    
                Returns:
                    bool: Nuevo estado del modal (abierto/cerrado)
                """
                # Determinar qué botón fue presionado
                if n_open or n_close or n_close_alt:
                    return not is_open
                return is_open
                
        except Exception as e:
            # Log del error sin interrumpir la carga de otros callbacks
            print(f"[WARNING] No se pudo registrar callback para modal '{modal_id}': {e}")
            continue
    
    print(f"[INFO] Sistema de callbacks de ayuda registrado para {len(all_modals)} modales")


def register_callbacks(app):
    """
    Función alias para compatibilidad con el sistema de registro global del dashboard.
    
    Args:
        app: Instancia de la aplicación Dash
        
    Note:
        Esta función mantiene compatibilidad con el patrón de registro usado
        en otros módulos del dashboard.
    """
    register_modal_callbacks(app)
    print("[INFO] ✅ Callbacks del sistema de ayuda registrados correctamente")