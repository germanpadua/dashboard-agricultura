# config_colormaps.py
"""
🎨 CONFIGURACIÓN DE ESCALAS DE COLORES PARA AGRICULTORES
- NDVI/OSAVI/NDRE: el gradiente (rojo→verde o marrón→verde) aplica SOLO a [0,1].
- Todo lo que no es vegetación (agua, nieve, nubes, sombras, NDVI<0, etc.) va en GRIS.
- Anomalías: divergente centrada en 0 (igual), negativo = peor, positivo = mejor.
"""

# ===============================
# Parámetros principales (editar)
# ===============================

# Nombre de escala NDVI por defecto
# Opciones: "vegetacion_clasica", "vegetacion_mejorada", "agricultura", "alto_contraste",
#           "contraste_rojo_verde_2", "contraste_rojo_verde_3", "modal_help_table", "verde_puro"
NDVI_COLORMAP = "agricultura"

# Nombre de escala de ANOMALÍAS por defecto
# Opciones: "rojo_azul_clasico", "sequia_humedad", "tierra_agua", "temperatura",
#           "alto_contraste_anomalia", "rojo_verde_agricola"
ANOMALY_COLORMAP = "rojo_verde_agricola"

# Transparencia global de overlays
NDVI_ALPHA = 0.85
ANOMALY_ALPHA = 0.80

# Color genérico para NO VEGETACIÓN (agua/nieve/nubes/valores < 0)
NON_VEG_COLOR = "#BEBEBE"
NON_VEG_ALPHA = 1.0  # opacidad de las zonas no vegetación

# Rango operativo recomendado para visualización NDVI (0–1 siempre)
# Si quieres forzar contraste, recorta en 0.20–0.85, por ejemplo:
NDVI_CUSTOM_RANGE = (0.20, 0.85)  # None = usar 0..1 completo

# Tolerancia de “igual” para anomalías (± alrededor de 0)
ANOMALY_ZERO_TOLERANCE = 0.03

# Umbrales descriptivos NDVI (para leyendas y etiquetas)
NDVI_CLASS_THRESHOLDS = [
    (0.30, "Crítica"),     # < 0.30
    (0.50, "Moderada"),    # 0.30–0.50
    (0.70, "Buena"),       # 0.50–0.70
    (1.01, "Excelente"),   # > 0.70
]

# ==================================================
# Definición de paletas (todas en 0→1)
# ==================================================

NDVI_COLORMAPS_DEF = {
    "vegetacion_clasica": [
        (0.00, "#5D4037"), (0.20, "#A1887F"), (0.35, "#F6E27F"),
        (0.55, "#A5D16D"), (0.70, "#4CAF50"), (0.85, "#2E7D32"), (1.00, "#1B5E20"),
    ],
    "vegetacion_mejorada": [
        (0.00, "#8E0000"), (0.20, "#D73027"), (0.40, "#FDAE61"),
        (0.60, "#A6D96A"), (0.80, "#1A9850"), (1.00, "#006837"),
    ],
    "agricultura": [
        (0.00, "#7F2704"), (0.20, "#D95F0E"), (0.30, "#FEC44F"),
        (0.45, "#C7E9C0"), (0.60, "#74C476"), (0.70, "#31A354"),
        (0.80, "#006D2C"), (1.00, "#00441B"),
    ],
    "alto_contraste": [
        (0.00, "#D7191C"), (0.25, "#FDAE61"), (0.50, "#FFFFBF"),
        (0.75, "#A6D96A"), (1.00, "#1A9641"),
    ],
    "contraste_rojo_verde_2": [
        (0.00, "#A50026"), (0.07, "#D73027"), (0.15, "#F46D43"),
        (0.23, "#FDAE61"), (0.30, "#FEE08B"), (0.37, "#FFFFBF"),
        (0.45, "#D9EF8B"), (0.51, "#D9EF8B"), (0.58, "#A6D96A"),
        (0.65, "#A6D96A"), (0.70, "#66BD63"), (0.75, "#66BD63"),
        (0.80, "#1A9850"), (0.85, "#1A9850"), (0.90, "#006837"),
        (0.95, "#006837"), (1.00, "#006837"),
    ],
    # Ejemplo con plateau gris inicial (opcional)
    "contraste_rojo_verde_3": [
        (0.00, "#BEBEBE"), (0.50, "#BEBEBE"),  # gris hasta 0.5
        (0.5001, "#A50026"), (0.75, "#FFFFBF"), (0.80, "#A6D96A"),
        (0.85, "#66BD63"), (0.90, "#1A9850"), (0.95, "#006837"), (1.00, "#006837"),
    ],
    "modal_help_table": [
        (0.00, "#0c0c0c"), (0.33, "#eaeaea"), (0.47, "#ccc682"),
        (0.60, "#70a33f"), (0.67, "#306d1c"), (0.73, "#0f540a"), (1.00, "#004400"),
    ],
    "verde_puro": [
        (0.00, "#FFFFFF"), (0.20, "#FFFFE0"), (0.40, "#ADFF2F"),
        (0.60, "#32CD32"), (0.80, "#228B22"), (1.00, "#006400"),
    ],
}

ANOMALY_COLORMAPS_DEF = {
    "rojo_azul_clasico": [
        (-1.00, "#2C7BB6"), (-0.50, "#ABD9E9"), (-0.10, "#E0F3F8"),
        (0.00, "#F7F7F7"),
        (0.10, "#FEE090"), (0.50, "#F46D43"), (1.00, "#D73027"),
    ],
    "sequia_humedad": [
        (-1.00, "#7F3B08"), (-0.30, "#B35806"), (-0.10, "#E08214"),
        (-0.03, "#F0F0F0"),
        (0.00, "#F7F7F7"),
        (0.03, "#E0F3DB"), (0.10, "#A8DDB5"), (0.30, "#43A2CA"), (1.00, "#0868AC"),
    ],
    "tierra_agua": [
        (-1.00, "#8C510A"), (-0.30, "#BF812D"), (-0.10, "#DFC27D"),
        (0.00, "#F5F5F5"),
        (0.10, "#80CDC1"), (0.30, "#35978F"), (1.00, "#01665E"),
    ],
    "temperatura": [
        (-1.00, "#313695"), (-0.50, "#74ADD1"), (-0.10, "#D1E5F0"),
        (0.00, "#F6F6F6"),
        (0.10, "#FEE090"), (0.50, "#F46D43"), (1.00, "#A50026"),
    ],
    "alto_contraste_anomalia": [
        (-1.00, "#084081"), (-0.50, "#7BCCC4"), (-0.10, "#DEEBF7"),
        (0.00, "#FFFFFF"),
        (0.10, "#FEE0D2"), (0.50, "#FC9272"), (1.00, "#CB181D"),
    ],
    "rojo_verde_agricola": [
        (-1.00, "#B71C1C"), (-0.50, "#E53935"), (-0.20, "#EF5350"), (-0.05, "#FFCDD2"),
        (0.00, "#FFFFFF"),
        (0.05, "#C8E6C9"), (0.20, "#66BB6A"), (0.50, "#4CAF50"), (1.00, "#2E7D32"),
    ],
}

def get_all_ndvi_colormap_names():
    return list(NDVI_COLORMAPS_DEF.keys())

def get_colormap_description(name: str) -> str:
    descriptions = {
        "vegetacion_clasica": "Marrón → Amarillo → Verde tradicional para vegetación",
        "vegetacion_mejorada": "Rojo → Amarillo → Verde intenso, muy expresiva",
        "agricultura": "Optimizada para agricultura, enfoque en 0.2-0.8",
        "alto_contraste": "Máximo contraste para diferenciación clara",
        "modal_help_table": "Escala científica con categorías específicas de salud vegetal",
        "verde_puro": "Gradiente verde puro para comparación limpia"
    }
    return descriptions.get(name, f"Escala de colores {name}")

def create_colormap_preview(name: str) -> str:
    color_stops = get_ndvi_colormap(name)
    gradient_parts = []
    min_val = color_stops[0][0]
    max_val = color_stops[-1][0]
    for value, color in color_stops:
        percentage = ((value - min_val) / (max_val - min_val)) * 100
        gradient_parts.append(f"{color} {percentage:.0f}%")
    return f"linear-gradient(to right, {', '.join(gradient_parts)})"

def validate_colormap_definition(name: str) -> bool:
    try:
        color_stops = NDVI_COLORMAPS_DEF.get(name)
        if not color_stops:
            return False
        values = [stop[0] for stop in color_stops]
        if values != sorted(values):
            logger.warning(f"⚠️ Colormap '{name}': valores no están en orden ascendente")
            return False
        for _, color in color_stops:
            if not isinstance(color, str) or not color.startswith('#') or len(color) != 7:
                logger.warning(f"⚠️ Colormap '{name}': color inválido '{color}'")
                return False
        return True
    except Exception as e:
        logger.error(f"❌ Error validando colormap '{name}': {e}")
        return False

COLORMAP_RECOMMENDATIONS = {
    "general_agriculture": "agricultura",
    "research": "modal_help_table",
    "presentation": "vegetacion_mejorada",
    "quick_analysis": "alto_contraste",
    "olive_groves": "agricultura",
    "stress_detection": "vegetacion_mejorada"
}

def get_recommended_colormap(use_case: str = "general_agriculture") -> str:
    return COLORMAP_RECOMMENDATIONS.get(use_case, "agricultura")
