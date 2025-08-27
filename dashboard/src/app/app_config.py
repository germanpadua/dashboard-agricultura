"""
Configuración centralizada de la aplicación Dash
Separación de responsabilidades para mejor mantenimiento
"""

import dash
import dash_bootstrap_components as dbc
from pathlib import Path

# Configuración de rutas
ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_PATH = ROOT_DIR / "assets"

# Rutas de datos
DATA_PATHS = {
    'csv': "data/raw/merged_output.csv",
    'kml': "assets/Prueba Bot.kml"
}

# Configuración del tema agrícola profesional
AGRI_THEME = {
    'colors': {
        'primary': '#2E7D32',      # Verde olivo profesional
        'secondary': '#5D4037',    # Marrón tierra
        'success': '#4CAF50',      # Verde éxito brillante
        'warning': '#FF9800',      # Naranja cosecha
        'danger': '#F44336',       # Rojo alerta
        'info': '#2196F3',         # Azul cielo moderno
        'bg_light': '#F8FFF8',     # Fondo muy suave
        'bg_card': '#FFFFFF',      # Fondo de tarjetas
        'text_primary': '#2E2E2E', # Texto principal
        'text_secondary': '#666666', # Texto secundario
        'border_light': '#E8E8E8', # Bordes suaves
        'shadow': 'rgba(46, 125, 50, 0.1)', # Sombra verde suave
        'purple': '#9C27B0', # Morado para variantes
    },
    'external_stylesheets': [
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ],
    'fonts': {
        'primary': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        'sizes': {
            'xs': '0.75rem',
            'sm': '0.875rem', 
            'md': '1rem',
            'lg': '1.125rem',
            'xl': '1.25rem',
            'xxl': '1.5rem',
            'display': '2.25rem'
        }
    }
}

# Configuración de las tabs del dashboard
DASHBOARD_TABS = [
    {
        'label': '📈 Histórico',
        'value': 'tab-historico',
        'description': 'Análisis de datos meteorológicos históricos'
    },
    {
        'label': '🔮 Predicción',
        'value': 'tab-prediccion', 
        'description': 'Pronóstico meteorológico detallado'
    },
    {
        'label': '🛰️ Satelital',
        'value': 'tab-satelital',
        'description': 'Índices de vegetación y salud del cultivo'
    },
    {
        'label': '🦠 Detecciones',
        'value': 'tab-detecciones',
        'description': 'Monitoreo de repilo en tiempo real'
    },
    {
        'label': '🏞️ Fincas',
        'value': 'tab-fincas',
        'description': 'Gestión y análisis de parcelas'
    }
]

def create_dash_app():
    """
    Crea y configura la instancia de la aplicación Dash
    
    Returns:
        dash.Dash: Aplicación configurada
    """
    app = dash.Dash(
        __name__,
        external_stylesheets=AGRI_THEME['external_stylesheets'],
        suppress_callback_exceptions=True,
        assets_folder=str(ASSETS_PATH),
        title="Dashboard Agrícola - Benalua",
        update_title="Actualizando...",
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "description", "content": "Sistema de monitoreo agrícola inteligente para olivicultura"},
            {"name": "author", "content": "TFM Master Ciencia de Datos"}
        ]
    )
    
    return app

def get_tab_style():
    """
    Obtiene estilos consistentes para las tabs con diseño moderno
    
    Returns:
        dict: Estilos para tabs normales y seleccionadas
    """
    return {
        'normal': {
            'borderRadius': '12px 12px 0 0',
            'border': f'2px solid {AGRI_THEME["colors"]["border_light"]}',
            'borderBottom': 'none',
            'marginRight': '4px',
            'padding': '0.75rem 1.5rem',
            'fontWeight': '500',
            'fontSize': AGRI_THEME['fonts']['sizes']['md'],
            'fontFamily': AGRI_THEME['fonts']['primary'],
            'color': AGRI_THEME['colors']['text_secondary'],
            'backgroundColor': AGRI_THEME['colors']['bg_card'],
            'boxShadow': f'0 2px 4px {AGRI_THEME["colors"]["shadow"]}',
            'transition': 'all 0.2s ease',
            'cursor': 'pointer'
        },
        'selected': {
            'backgroundColor': AGRI_THEME['colors']['primary'],
            'color': 'white',
            'fontWeight': '600',
            'borderColor': AGRI_THEME['colors']['primary'],
            'boxShadow': f'0 4px 8px {AGRI_THEME["colors"]["shadow"]}',
            'transform': 'translateY(-2px)'
        }
    }

def get_card_style(variant='default'):
    """
    Obtiene estilos para tarjetas con variantes
    
    Args:
        variant: Tipo de tarjeta ('default', 'metric', 'alert', 'highlight')
    
    Returns:
        dict: Estilos de tarjeta
    """
    base_style = {
        'borderRadius': '12px',
        'backgroundColor': AGRI_THEME['colors']['bg_card'],
        'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}',
        'boxShadow': f'0 2px 8px {AGRI_THEME["colors"]["shadow"]}',
        'transition': 'all 0.2s ease',
        'fontFamily': AGRI_THEME['fonts']['primary']
    }
    
    variants = {
        'metric': {
            **base_style,
            'background': f'linear-gradient(135deg, {AGRI_THEME["colors"]["bg_light"]} 0%, {AGRI_THEME["colors"]["bg_card"]} 100%)',
            'borderLeft': f'4px solid {AGRI_THEME["colors"]["primary"]}'
        },
        'alert': {
            **base_style,
            'borderLeft': f'4px solid {AGRI_THEME["colors"]["warning"]}',
            'backgroundColor': '#FFF8E1'
        },
        'highlight': {
            **base_style,
            'borderLeft': f'4px solid {AGRI_THEME["colors"]["info"]}',
            'backgroundColor': '#F3F8FF'
        }
    }
    
    return variants.get(variant, base_style)

def get_button_style(variant='primary', size='md'):
    """
    Obtiene estilos para botones con variantes y tamaños
    
    Args:
        variant: Tipo de botón ('primary', 'secondary', 'outline', 'filter')
        size: Tamaño ('sm', 'md', 'lg')
    
    Returns:
        dict: Estilos de botón
    """
    sizes = {
        'sm': {'padding': '0.5rem 1rem', 'fontSize': AGRI_THEME['fonts']['sizes']['sm']},
        'md': {'padding': '0.625rem 1.5rem', 'fontSize': AGRI_THEME['fonts']['sizes']['md']},
        'lg': {'padding': '0.75rem 2rem', 'fontSize': AGRI_THEME['fonts']['sizes']['lg']}
    }
    
    base_style = {
        'borderRadius': '8px',
        'fontWeight': '600',
        'fontFamily': AGRI_THEME['fonts']['primary'],
        'border': 'none',
        'cursor': 'pointer',
        'transition': 'all 0.2s ease',
        'textDecoration': 'none',
        **sizes.get(size, sizes['md'])
    }
    
    variants = {
        'primary': {
            **base_style,
            'backgroundColor': AGRI_THEME['colors']['primary'],
            'color': 'white',
            'boxShadow': f'0 2px 4px rgba(46, 125, 50, 0.2)'
        },
        'secondary': {
            **base_style,
            'backgroundColor': AGRI_THEME['colors']['secondary'],
            'color': 'white',
            'boxShadow': f'0 2px 4px rgba(93, 64, 55, 0.2)'
        },
        'outline': {
            **base_style,
            'backgroundColor': 'transparent',
            'color': AGRI_THEME['colors']['primary'],
            'border': f'2px solid {AGRI_THEME["colors"]["primary"]}'
        },
        'filter': {
            **base_style,
            'borderRadius': '20px',
            'backgroundColor': AGRI_THEME['colors']['bg_light'],
            'color': AGRI_THEME['colors']['text_primary'],
            'border': f'1px solid {AGRI_THEME["colors"]["border_light"]}',
            'padding': '0.5rem 1.2rem'
        }
    }
    
    return variants.get(variant, variants['primary'])
