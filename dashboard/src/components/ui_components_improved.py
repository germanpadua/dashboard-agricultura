"""
Componentes de UI mejorados para Dashboard Agrícola
Diseño profesional orientado a agricultores
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from src.app.app_config import AGRI_THEME, get_card_style, get_button_style

def create_metric_card(title, value, unit="", icon=None, color="primary", change=None, description=None):
    """
    Crea una tarjeta de métrica profesional y clara
    
    Args:
        title: Título de la métrica
        value: Valor numérico
        unit: Unidad de medida
        icon: Icono FontAwesome (opcional)
        color: Color theme ('primary', 'success', 'warning', 'danger', 'info')
        change: Cambio porcentual o descripción del cambio
        description: Descripción adicional
    
    Returns:
        dbc.Card: Tarjeta de métrica
    """
    color_map = {
        'primary': AGRI_THEME['colors']['primary'],
        'success': AGRI_THEME['colors']['success'],
        'warning': AGRI_THEME['colors']['warning'],
        'danger': AGRI_THEME['colors']['danger'],
        'info': AGRI_THEME['colors']['info']
    }
    
    theme_color = color_map.get(color, AGRI_THEME['colors']['primary'])
    
    # Contenido del icono
    icon_content = []
    if icon:
        icon_content = [
            html.I(
                className=icon,
                style={
                    'fontSize': '2rem',
                    'color': theme_color,
                    'opacity': '0.8',
                    'marginBottom': '0.5rem'
                }
            )
        ]
    
    # Contenido del cambio
    change_content = []
    if change:
        change_color = AGRI_THEME['colors']['success'] if isinstance(change, str) and '+' in change else AGRI_THEME['colors']['danger']
        if not isinstance(change, str) or ('+' not in change and '-' not in change):
            change_color = AGRI_THEME['colors']['info']
            
        change_content = [
            html.Div(
                change,
                style={
                    'fontSize': AGRI_THEME['fonts']['sizes']['xs'],
                    'color': change_color,
                    'fontWeight': '600',
                    'marginTop': '0.25rem'
                }
            )
        ]
    
    # Descripción adicional
    desc_content = []
    if description:
        desc_content = [
            html.P(
                description,
                style={
                    'fontSize': AGRI_THEME['fonts']['sizes']['xs'],
                    'color': AGRI_THEME['colors']['text_secondary'],
                    'marginTop': '0.5rem',
                    'marginBottom': '0',
                    'fontStyle': 'italic'
                }
            )
        ]
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                *icon_content,
                html.H4(
                    [str(value), html.Small(f" {unit}", className="text-muted ms-1")],
                    style={
                        'color': theme_color,
                        'fontWeight': '700',
                        'fontSize': AGRI_THEME['fonts']['sizes']['xl'],
                        'marginBottom': '0.25rem',
                        'fontFamily': AGRI_THEME['fonts']['primary']
                    }
                ),
                html.P(
                    title,
                    style={
                        'fontSize': AGRI_THEME['fonts']['sizes']['sm'],
                        'color': AGRI_THEME['colors']['text_secondary'],
                        'fontWeight': '500',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.5px',
                        'marginBottom': '0.25rem',
                        'fontFamily': AGRI_THEME['fonts']['primary']
                    }
                ),
                *change_content,
                *desc_content
            ], style={'textAlign': 'center'})
        ], style={'padding': '1.5rem'})
    ], style=get_card_style('metric'))

def create_alert_card(message, alert_type="info", title=None, dismissable=False):
    """
    Crea una tarjeta de alerta profesional
    
    Args:
        message: Mensaje de la alerta
        alert_type: Tipo ('success', 'warning', 'danger', 'info')
        title: Título opcional
        dismissable: Si se puede cerrar
    
    Returns:
        dbc.Alert: Componente de alerta
    """
    icon_map = {
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    }
    
    alert_content = []
    if title:
        alert_content.append(
            html.H6([
                html.I(className=f"{icon_map.get(alert_type, 'fas fa-info-circle')} me-2"),
                title
            ], style={
                'fontWeight': '600',
                'marginBottom': '0.5rem',
                'fontFamily': AGRI_THEME['fonts']['primary']
            })
        )
    
    alert_content.append(
        html.P(
            message,
            style={
                'marginBottom': '0',
                'fontFamily': AGRI_THEME['fonts']['primary']
            }
        )
    )
    
    return dbc.Alert(
        alert_content,
        color=alert_type,
        dismissable=dismissable,
        style={
            'border': 'none',
            'borderRadius': '12px',
            'fontFamily': AGRI_THEME['fonts']['primary']
        },
        className="alert-agri"
    )

def create_section_header(title, subtitle=None, icon=None, actions=None):
    """
    Crea un header de sección consistente
    
    Args:
        title: Título de la sección
        subtitle: Subtítulo opcional
        icon: Icono FontAwesome
        actions: Lista de botones/acciones
    
    Returns:
        html.Div: Header de sección
    """
    header_content = []
    
    # Icono y título
    title_content = []
    if icon:
        title_content.append(
            html.I(className=f"{icon} me-3", style={
                'color': AGRI_THEME['colors']['primary'],
                'fontSize': '1.75rem'
            })
        )
    
    title_content.append(
        html.Span(title, style={
            'fontFamily': AGRI_THEME['fonts']['primary'],
            'fontWeight': '600',
            'fontSize': AGRI_THEME['fonts']['sizes']['xxl']
        })
    )
    
    header_content.append(
        html.H2(
            title_content,
            style={
                'color': AGRI_THEME['colors']['primary'],
                'marginBottom': '0.5rem' if subtitle else '1rem',
                'display': 'flex',
                'alignItems': 'center'
            }
        )
    )
    
    # Subtítulo
    if subtitle:
        header_content.append(
            html.P(
                subtitle,
                style={
                    'color': AGRI_THEME['colors']['text_secondary'],
                    'fontSize': AGRI_THEME['fonts']['sizes']['lg'],
                    'fontFamily': AGRI_THEME['fonts']['primary'],
                    'marginBottom': '1rem'
                }
            )
        )
    
    # Crear layout con acciones si las hay
    if actions:
        return dbc.Row([
            dbc.Col(header_content, width='auto'),
            dbc.Col([
                html.Div(actions, className="d-flex gap-2 justify-content-end")
            ], width=True)
        ], className="align-items-center mb-4")
    
    return html.Div(header_content, className="mb-4")

def create_loading_component(message="Cargando datos..."):
    """
    Componente de carga consistente
    
    Args:
        message: Mensaje de carga
    
    Returns:
        html.Div: Componente de loading
    """
    return html.Div([
        html.Div([
            html.Div(className="loading-spinner"),
            html.Span(
                message,
                style={
                    'fontSize': AGRI_THEME['fonts']['sizes']['md'],
                    'color': AGRI_THEME['colors']['text_secondary'],
                    'fontFamily': AGRI_THEME['fonts']['primary']
                }
            )
        ], className="loading-container")
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'minHeight': '200px',
        'backgroundColor': AGRI_THEME['colors']['bg_light'],
        'borderRadius': '12px',
        'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}'
    })

def create_filter_button_group(buttons, active_button=None):
    """
    Crea un grupo de botones de filtro
    
    Args:
        buttons: Lista de diccionarios con 'label', 'value', e 'icon' (opcional)
        active_button: Valor del botón activo
    
    Returns:
        html.Div: Grupo de botones de filtro
    """
    button_components = []
    
    for button in buttons:
        is_active = button['value'] == active_button
        button_style = get_button_style('filter', 'sm')
        
        if is_active:
            button_style.update({
                'backgroundColor': AGRI_THEME['colors']['primary'],
                'color': 'white',
                'borderColor': AGRI_THEME['colors']['primary']
            })
        
        button_content = []
        if button.get('icon'):
            button_content.append(
                html.I(className=f"{button['icon']} me-2")
            )
        button_content.append(button['label'])
        
        button_components.append(
            html.Button(
                button_content,
                id=f"filter-{button['value']}",
                n_clicks=0,
                style=button_style,
                className="btn-filter me-2"
            )
        )
    
    return html.Div(
        button_components,
        className="d-flex flex-wrap gap-2 mb-3"
    )

def create_info_tooltip(text, icon="fas fa-question-circle"):
    """
    Crea un tooltip informativo
    
    Args:
        text: Texto del tooltip
        icon: Icono a mostrar
    
    Returns:
        html.Span: Componente con tooltip
    """
    return html.Span([
        html.I(
            className=icon,
            id="info-tooltip",
            style={
                'color': AGRI_THEME['colors']['info'],
                'cursor': 'pointer',
                'marginLeft': '0.5rem'
            }
        ),
        dbc.Tooltip(
            text,
            target="info-tooltip",
            placement="top"
        )
    ])

def create_chart_container(title, chart_component, subtitle=None, actions=None, loading=False):
    """
    Contenedor estandardizado para gráficos
    
    Args:
        title: Título del gráfico
        chart_component: Componente del gráfico (dcc.Graph, etc.)
        subtitle: Subtítulo opcional
        actions: Botones de acción opcionales
        loading: Si mostrar estado de carga
    
    Returns:
        html.Div: Contenedor del gráfico
    """
    header = create_section_header(title, subtitle, actions=actions)
    
    content = chart_component
    if loading:
        content = create_loading_component("Generando gráfico...")
    
    return html.Div([
        header,
        html.Div(
            content,
            style={
                'backgroundColor': AGRI_THEME['colors']['bg_card'],
                'borderRadius': '12px',
                'padding': '1rem',
                'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}',
                'boxShadow': f'0 2px 4px {AGRI_THEME["colors"]["shadow"]}'
            }
        )
    ], className="chart-container mb-4")

def create_data_table_wrapper(table_component, title=None, subtitle=None):
    """
    Wrapper para tablas de datos con estilos consistentes
    
    Args:
        table_component: Componente de tabla
        title: Título opcional
        subtitle: Subtítulo opcional
    
    Returns:
        html.Div: Tabla con wrapper
    """
    content = []
    
    if title:
        header = create_section_header(title, subtitle)
        content.append(header)
    
    content.append(
        html.Div(
            table_component,
            className="table-agri",
            style={
                'backgroundColor': AGRI_THEME['colors']['bg_card'],
                'borderRadius': '12px',
                'overflow': 'hidden',
                'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}',
                'boxShadow': f'0 2px 4px {AGRI_THEME["colors"]["shadow"]}'
            }
        )
    )
    
    return html.Div(content, className="mb-4")

def create_status_badge(status, text):
    """
    Crea un badge de estado
    
    Args:
        status: Estado ('active', 'inactive', 'warning', 'error')
        text: Texto del badge
    
    Returns:
        dbc.Badge: Badge de estado
    """
    status_colors = {
        'active': 'success',
        'inactive': 'secondary',
        'warning': 'warning',
        'error': 'danger',
        'info': 'info'
    }
    
    return dbc.Badge(
        text,
        color=status_colors.get(status, 'secondary'),
        pill=True,
        style={
            'fontFamily': AGRI_THEME['fonts']['primary'],
            'fontSize': AGRI_THEME['fonts']['sizes']['xs']
        }
    )

def create_breadcrumb(items):
    """
    Crea un breadcrumb para navegación
    
    Args:
        items: Lista de diccionarios con 'label' y 'href' (opcional)
    
    Returns:
        dbc.Breadcrumb: Componente breadcrumb
    """
    breadcrumb_items = []
    for i, item in enumerate(items):
        is_active = i == len(items) - 1
        breadcrumb_items.append(
            dbc.BreadcrumbItem(
                item['label'],
                href=item.get('href') if not is_active else None,
                active=is_active,
                style={'fontFamily': AGRI_THEME['fonts']['primary']}
            )
        )
    
    return dbc.Breadcrumb(
        breadcrumb_items,
        style={
            'backgroundColor': AGRI_THEME['colors']['bg_light'],
            'borderRadius': '8px',
            'padding': '0.75rem 1rem',
            'marginBottom': '1rem'
        }
    )

# Funciones de utilidad para estilos rápidos
def get_professional_card_style():
    """Retorna estilo de tarjeta profesional"""
    return get_card_style()

def get_metric_card_style():
    """Retorna estilo de tarjeta métrica"""
    return get_card_style('metric')

def get_primary_button_style():
    """Retorna estilo de botón primario"""
    return get_button_style('primary')

def get_filter_button_style(active=False):
    """Retorna estilo de botón filtro"""
    style = get_button_style('filter')
    if active:
        style.update({
            'backgroundColor': AGRI_THEME['colors']['primary'],
            'color': 'white',
            'borderColor': AGRI_THEME['colors']['primary']
        })
    return style