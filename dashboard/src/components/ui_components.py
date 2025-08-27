"""
Componentes UI reutilizables con diseño agrícola optimizado
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from .theme_config import COLORS, CARD_STYLES, TYPOGRAPHY, BUTTON_STYLES, get_card_style, get_severity_color, get_alert_style

def create_header(title, subtitle=None, help_button=None):
    """Crea un header principal con estilo agrícola"""
    header_content = [
        html.H1(
            title,
            style=TYPOGRAPHY['title_main']
        )
    ]
    
    if subtitle:
        header_content.append(
            html.P(
                subtitle,
                className="lead text-muted text-center mb-3",
                style={'fontSize': '1.1rem'}
            )
        )
    
    # Contenedor principal del header
    header_div = html.Div(
        header_content,
        className="text-center mb-4 p-3",
        style={
            'background': f'linear-gradient(135deg, {COLORS["bg_primary"]} 0%, white 100%)',
            'borderRadius': '12px',
            'border': f'2px solid {COLORS["primary"]}20',
            'position': 'relative'
        }
    )
    
    # Si hay botón de ayuda, añadirlo en la esquina
    if help_button:
        header_div = html.Div([
            header_div,
            html.Div(
                help_button,
                style={
                    'position': 'absolute',
                    'top': '10px',
                    'right': '10px'
                }
            )
        ], style={'position': 'relative'})
    
    return header_div

def create_metric_card(title, value, subtitle=None, icon=None, color='primary', size='normal'):
    """Crea una tarjeta de métrica con estilo mejorado"""
    
    # Configurar colores
    bg_color = COLORS.get(f'bg_{color}', COLORS['bg_light'])
    text_color = COLORS.get(color, COLORS['primary'])
    
    # Icono si se proporciona
    icon_element = None
    if icon:
        icon_element = html.I(
            className=f"fas {icon}",
            style={
                'fontSize': '1.5rem' if size == 'normal' else '2rem',
                'color': text_color,
                'marginBottom': '0.5rem'
            }
        )
    
    # Valor principal
    value_size = '2.5rem' if size == 'large' else '2rem' if size == 'normal' else '1.5rem'
    value_element = html.H3(
        str(value),
        className="mb-1",
        style={
            'fontSize': value_size,
            'fontWeight': 'bold',
            'color': text_color
        }
    )
    
    # Título
    title_element = html.P(
        title,
        className="mb-0",
        style={
            'fontSize': '0.9rem',
            'fontWeight': '600',
            'color': '#666',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px'
        }
    )
    
    # Subtítulo opcional
    subtitle_element = None
    if subtitle:
        subtitle_element = html.P(
            subtitle,
            className="mb-0 text-muted",
            style={'fontSize': '0.8rem'}
        )
    
    card_content = [icon_element, value_element, title_element, subtitle_element]
    card_content = [elem for elem in card_content if elem is not None]
    
    return dbc.Card([
        dbc.CardBody(
            card_content,
            className="text-center"
        )
    ], style={
        **get_card_style('metric'),
        'background': f'linear-gradient(135deg, {bg_color} 0%, white 100%)',
        'borderLeft': f'4px solid {text_color}'
    })

def create_alert_banner(message, level='info', dismissible=True, icon=None):
    """Crea banner de alerta con estilo agrícola"""
    
    # Configurar icono según nivel
    level_icons = {
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle', 
        'danger': 'fa-times-circle',
        'info': 'fa-info-circle'
    }
    
    alert_icon = icon or level_icons.get(level, 'fa-info-circle')
    
    alert_content = [
        html.I(className=f"fas {alert_icon} me-2"),
        message
    ]
    
    return dbc.Alert(
        alert_content,
        color=level,
        dismissible=dismissible,
        className="mb-3",
        style={
            'borderRadius': '8px',
            'border': f'1px solid {COLORS.get(level, COLORS["info"])}',
            'fontWeight': '500'
        }
    )

def create_filter_buttons(buttons_config, active_id=None):
    """Crea grupo de botones de filtro con estilo mejorado"""
    
    buttons = []
    for button in buttons_config:
        is_active = button.get('id') == active_id
        
        btn = dbc.Button(
            [
                html.I(className=f"fas {button.get('icon', 'fa-filter')} me-2"),
                button['label']
            ],
            id=button['id'],
            size="sm",
            className="me-2 mb-2",
            style=BUTTON_STYLES['filter_active'] if is_active else BUTTON_STYLES['filter'],
            outline=not is_active
        )
        buttons.append(btn)
    
    return html.Div(
        buttons,
        className="d-flex flex-wrap justify-content-center mb-3"
    )

def create_status_indicator(status, size='normal'):
    """Crea indicador de estado con colores agrícolas"""
    
    status_config = {
        'healthy': {'color': COLORS['success'], 'icon': 'fa-leaf', 'text': 'Saludable'},
        'warning': {'color': COLORS['warning'], 'icon': 'fa-exclamation-triangle', 'text': 'Atención'},
        'critical': {'color': COLORS['danger'], 'icon': 'fa-times-circle', 'text': 'Crítico'},
        'monitoring': {'color': COLORS['info'], 'icon': 'fa-eye', 'text': 'Monitoreo'},
        'offline': {'color': '#666', 'icon': 'fa-plug', 'text': 'Sin datos'}
    }
    
    config = status_config.get(status, status_config['monitoring'])
    icon_size = '1.2rem' if size == 'large' else '1rem' if size == 'normal' else '0.8rem'
    
    return html.Span([
        html.I(
            className=f"fas {config['icon']} me-2",
            style={'color': config['color'], 'fontSize': icon_size}
        ),
        config['text']
    ], style={'color': config['color'], 'fontWeight': '500'})

def create_progress_bar(value, max_value=100, label=None, color='primary', show_percentage=True):
    """Crea barra de progreso con estilo agrícola"""
    
    percentage = (value / max_value) * 100 if max_value > 0 else 0
    bar_color = COLORS.get(color, COLORS['primary'])
    
    progress_content = []
    
    if label:
        progress_content.append(
            html.Div([
                html.Span(label),
                html.Span(
                    f"{percentage:.1f}%" if show_percentage else str(value),
                    className="float-end fw-bold"
                )
            ], className="d-flex justify-content-between mb-1")
        )
    
    progress_content.append(
        dbc.Progress(
            value=percentage,
            color=color,
            style={
                'height': '8px',
                'borderRadius': '4px',
                'backgroundColor': f'{bar_color}20'
            },
            bar_style={
                'borderRadius': '4px',
                'background': f'linear-gradient(90deg, {bar_color} 0%, {bar_color}CC 100%)'
            }
        )
    )
    
    return html.Div(progress_content, className="mb-3")

def create_data_table_styled(data, columns, page_size=10, sort_action="native"):
    """Crea tabla de datos con estilo agrícola mejorado"""
    
    return dbc.Table.from_dataframe(
        data,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mt-3",
        style={
            'borderRadius': '8px',
            'overflow': 'hidden',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
        }
    ) if len(data) <= page_size else html.Div([
        dbc.Table.from_dataframe(
            data.head(page_size),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-3"
        ),
        html.P(
            f"Mostrando {page_size} de {len(data)} registros",
            className="text-muted text-center mt-2"
        )
    ])

def create_loading_spinner(text="Cargando datos...", color='primary'):
    """Crea spinner de carga con tema agrícola"""
    
    return html.Div([
        dbc.Spinner(
            color=color,
            size="lg"
        ),
        html.P(
            text,
            className="mt-2 text-muted text-center",
            style={'fontSize': '0.9rem'}
        )
    ], className="text-center p-4")

def create_info_tooltip(text, tooltip_text, placement="top"):
    """Crea tooltip informativo con estilo mejorado"""
    
    return dbc.Tooltip(
        tooltip_text,
        target=f"tooltip-{hash(text)}",
        placement=placement,
        style={
            'fontSize': '0.85rem',
            'maxWidth': '300px'
        }
    ), html.Span([
        text,
        html.I(
            className="fas fa-info-circle ms-1",
            id=f"tooltip-{hash(text)}",
            style={
                'color': COLORS['info'],
                'fontSize': '0.8rem',
                'cursor': 'help'
            }
        )
    ])

def create_navigation_tabs(tabs_config, active_tab=None):
    """Crea navegación por tabs con estilo agrícola mejorado"""
    
    tabs = []
    for tab in tabs_config:
        is_active = tab['value'] == active_tab
        
        tab_content = [
            html.I(className=f"{tab.get('icon', 'fas fa-circle')} me-2"),
            tab['label']
        ]
        
        tab_item = dbc.Tab(
            label=tab_content,
            tab_id=tab['value'],
            tab_style={
                'borderRadius': '8px 8px 0 0',
                'border': f'2px solid {COLORS["primary"]}',
                'marginRight': '2px'
            },
            active_tab_style={
                'backgroundColor': COLORS['primary'],
                'color': 'white',
                'fontWeight': 'bold'
            }
        )
        tabs.append(tab_item)
    
    return dbc.Tabs(
        tabs,
        id="main-tabs",
        active_tab=active_tab or tabs_config[0]['value'],
        className="mb-3"
    )

def create_section_divider(title=None, color='primary'):
    """Crea divisor de sección con estilo"""
    
    if title:
        return html.Div([
            html.Hr(style={
                'border': f'2px solid {COLORS[color]}',
                'borderRadius': '2px',
                'margin': '2rem 0 1rem 0'
            }),
            html.H4(
                title,
                className="text-center",
                style={
                    'color': COLORS[color],
                    'fontWeight': '600',
                    'marginTop': '-0.75rem',
                    'backgroundColor': 'white',
                    'padding': '0 1rem',
                    'display': 'inline-block',
                    'position': 'relative',
                    'left': '50%',
                    'transform': 'translateX(-50%)'
                }
            )
        ], className="text-center")
    
    return html.Hr(style={
        'border': f'2px solid {COLORS[color]}',
        'borderRadius': '2px',
        'margin': '2rem 0'
    })
