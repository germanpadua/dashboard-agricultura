"""
Configuración de tema visual para Dashboard Agrícola
Diseño optimizado para agricultores - TFM Master en Ciencia de Datos
"""

# 🎨 PALETA DE COLORES AGRÍCOLA
COLORS = {
    # Colores principales
    'primary': '#2E7D32',      # Verde olivo profesional
    'secondary': '#5D4037',    # Marrón tierra
    'success': '#388E3C',      # Verde éxito
    'info': '#0277BD',         # Azul cielo
    'warning': '#F57C00',      # Naranja cosecha
    'danger': '#D32F2F',       # Rojo alerta
    
    # Colores de fondo
    'bg_primary': '#F1F8E9',   # Verde muy suave
    'bg_secondary': '#EFEBE9', # Beige tierra
    'bg_light': '#FAFAFA',     # Blanco casi puro
    'bg_dark': '#2E2E2E',      # Gris carbón
    
    # Colores para datos específicos
    'temperature': '#FF6B35',   # Naranja cálido
    'humidity': '#4FC3F7',      # Azul agua
    'precipitation': '#42A5F5', # Azul lluvia
    'ndvi_healthy': '#4CAF50',  # Verde sano
    'ndvi_stressed': '#FFC107', # Amarillo estrés
    'ndvi_critical': '#F44336', # Rojo crítico
    
    # Colores para severidad de repilo
    'severity_1': '#4CAF50',    # Verde - Muy baja
    'severity_2': '#8BC34A',    # Verde claro - Baja
    'severity_3': '#FF9800',    # Naranja - Moderada
    'severity_4': '#F44336',    # Rojo - Alta
    'severity_5': '#9C27B0',    # Morado - Muy alta
}

# 📐 ESTILOS PARA TARJETAS
CARD_STYLES = {
    'main': {
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': '1px solid #E0E0E0',
        'marginBottom': '1rem'
    },
    'metric': {
        'borderRadius': '8px',
        'boxShadow': '0 1px 4px rgba(0,0,0,0.1)',
        'border': 'none',
        'background': 'linear-gradient(135deg, #F1F8E9 0%, #E8F5E8 100%)'
    },
    'alert': {
        'borderRadius': '8px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.15)',
        'border': '2px solid',
        'fontWeight': 'bold'
    }
}

# 🔤 TIPOGRAFÍA
TYPOGRAPHY = {
    'title_main': {
        'fontSize': '2.2rem',
        'fontWeight': '700',
        'color': COLORS['primary'],
        'marginBottom': '1rem',
        'textAlign': 'center'
    },
    'title_section': {
        'fontSize': '1.5rem',
        'fontWeight': '600',
        'color': COLORS['secondary'],
        'marginBottom': '0.5rem'
    },
    'metric_value': {
        'fontSize': '2rem',
        'fontWeight': 'bold',
        'color': COLORS['primary']
    },
    'metric_label': {
        'fontSize': '0.9rem',
        'color': '#666',
        'textTransform': 'uppercase',
        'letterSpacing': '0.5px'
    }
}

# 🎯 ESTILOS PARA BOTONES
BUTTON_STYLES = {
    'primary': {
        'backgroundColor': COLORS['primary'],
        'borderColor': COLORS['primary'],
        'borderRadius': '8px',
        'fontWeight': '600',
        'padding': '0.5rem 1.5rem',
        'boxShadow': '0 2px 4px rgba(46, 125, 50, 0.2)'
    },
    'filter': {
        'borderRadius': '20px',
        'fontWeight': '500',
        'padding': '0.4rem 1.2rem',
        'marginRight': '0.5rem',
        'border': f'2px solid {COLORS["primary"]}',
        'backgroundColor': 'transparent',
        'color': COLORS['primary']
    },
    'filter_active': {
        'borderRadius': '20px',
        'fontWeight': '600',
        'padding': '0.4rem 1.2rem',
        'marginRight': '0.5rem',
        'border': f'2px solid {COLORS["primary"]}',
        'backgroundColor': COLORS['primary'],
        'color': 'white'
    }
}

# 🗂️ CONFIGURACIÓN DE NAVEGACIÓN
NAV_CONFIG = {
    'tabs': [
        {
            'label': '📈 Histórico',
            'value': 'historico',
            'icon': 'fas fa-chart-line',
            'description': 'Análisis de datos meteorológicos históricos'
        },
        {
            'label': '🔮 Predicción', 
            'value': 'prediccion',
            'icon': 'fas fa-cloud-sun',
            'description': 'Pronóstico meteorológico detallado'
        },
        {
            'label': '🛰️ Satelital',
            'value': 'datos-satelitales', 
            'icon': 'fas fa-satellite',
            'description': 'Índices de vegetación y salud del cultivo'
        },
        {
            'label': '🏞️ Fincas',
            'value': 'fincas',
            'icon': 'fas fa-map-marked-alt', 
            'description': 'Gestión y análisis de parcelas'
        },
        {
            'label': '🦠 Detecciones',
            'value': 'detecciones-repilo',
            'icon': 'fas fa-bug',
            'description': 'Monitoreo de repilo en tiempo real'
        }
    ]
}

# 📊 CONFIGURACIÓN DE GRÁFICOS
CHART_CONFIG = {
    'default_layout': {
        'font': {'family': 'Arial, sans-serif', 'size': 12},
        'showlegend': True,
        'legend': {'orientation': 'h', 'y': -0.1},
        'margin': {'l': 50, 'r': 50, 't': 80, 'b': 60},
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white'
    },
    'colors': {
        'temperature': COLORS['temperature'],
        'humidity': COLORS['humidity'], 
        'precipitation': COLORS['precipitation'],
        'primary': COLORS['primary'],
        'secondary': COLORS['secondary']
    }
}

# 🏷️ ETIQUETAS Y TEXTOS
LABELS = {
    'temperature': '🌡️ Temperatura',
    'humidity': '💧 Humedad', 
    'precipitation': '🌧️ Precipitación',
    'wind': '💨 Viento',
    'pressure': '📊 Presión',
    'ndvi': '🌱 ÍNDICE NDVI',
    'evi': '🌿 ÍNDICE EVI',
    'severity': '⚠️ Severidad',
    'location': '📍 Ubicación',
    'date': '📅 Fecha',
    'time': '⏰ Hora'
}

# 🎨 FUNCIÓN PARA CREAR ESTILOS PERSONALIZADOS
def get_card_style(card_type='main', **kwargs):
    """Obtiene estilo de tarjeta con personalización"""
    style = CARD_STYLES.get(card_type, CARD_STYLES['main']).copy()
    style.update(kwargs)
    return style

def get_severity_color(severity_level):
    """Obtiene color según nivel de severidad"""
    severity_colors = {
        1: COLORS['severity_1'],
        2: COLORS['severity_2'], 
        3: COLORS['severity_3'],
        4: COLORS['severity_4'],
        5: COLORS['severity_5']
    }
    return severity_colors.get(severity_level, COLORS['secondary'])

def get_alert_style(alert_level):
    """Obtiene estilo según nivel de alerta"""
    alert_styles = {
        'success': {'backgroundColor': COLORS['bg_primary'], 'borderColor': COLORS['success'], 'color': COLORS['success']},
        'warning': {'backgroundColor': '#FFF8E1', 'borderColor': COLORS['warning'], 'color': COLORS['warning']},
        'danger': {'backgroundColor': '#FFEBEE', 'borderColor': COLORS['danger'], 'color': COLORS['danger']},
        'info': {'backgroundColor': '#E3F2FD', 'borderColor': COLORS['info'], 'color': COLORS['info']}
    }
    return {**CARD_STYLES['alert'], **alert_styles.get(alert_level, alert_styles['info'])}

# 📱 ESTILOS RESPONSIVE
RESPONSIVE = {
    'mobile_breakpoint': 768,
    'container_padding': {
        'mobile': '0.5rem',
        'desktop': '1rem 2rem'
    },
    'card_margins': {
        'mobile': '0.5rem 0',
        'desktop': '1rem 0'
    }
}

def get_responsive_style(is_mobile=False):
    """Obtiene estilos responsive"""
    if is_mobile:
        return {
            'padding': RESPONSIVE['container_padding']['mobile'],
            'margin': RESPONSIVE['card_margins']['mobile']
        }
    return {
        'padding': RESPONSIVE['container_padding']['desktop'],
        'margin': RESPONSIVE['card_margins']['desktop']
    }
