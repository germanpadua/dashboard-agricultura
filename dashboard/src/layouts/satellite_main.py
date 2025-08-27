"""
Archivo principal mejorado para el layout de datos satelitales
Integra layout mejorado con callbacks optimizados
"""

from src.layouts.layout_datos_satelitales_mejorado import build_scientific_satellite_layout
from src.callbacks_refactored.datos_satelitales_integrated import register_integrated_callbacks

# Exportar funciones principales
def create_satellite_layout(*args, **kwargs):
    """Crea el layout mejorado de datos satelitales"""
    return build_scientific_satellite_layout(*args, **kwargs)

def register_callbacks(app):
    """Registra todos los callbacks integrados"""
    return register_integrated_callbacks(app)

# Alias para compatibilidad
build_layout = create_satellite_layout
create_layout = create_satellite_layout
