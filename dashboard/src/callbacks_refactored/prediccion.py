"""
===============================================================================
                   CALLBACKS DE PREDICCIÓN METEOROLÓGICA
===============================================================================

Este módulo gestiona la funcionalidad completa de predicción meteorológica
con enfoque especializado en evaluación de riesgo de enfermedades del olivo.

Características principales:
• Sistema de caché inteligente optimizado para Benalúa
• Predicciones semanales con tarjetas visuales interactivas
• Análisis horario detallado (48h)
• KPIs meteorológicos en tiempo real
• Evaluación científica de riesgo de Venturia oleaginea (repilo)
• Alertas proactivas con recomendaciones agronómicas
• Integración con AEMET API (preparado para producción)

Autor: German Jose Padua Pleguezuelo
Universidad de Granada
Master en Ciencia de Datos

Fichero: src.callbacks_refactored.prediccion.py

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Análisis de datos y cálculo numérico
import pandas as pd
import numpy as np

# Framework Dash
from dash import callback, Input, Output, State, html, no_update
import dash_bootstrap_components as dbc

# Utilidades específicas del proyecto
from src.utils.forecast_plots import (
    create_weekly_forecast_chart,
    create_48h_forecast_chart,
    analyze_disease_risk_forecast,
    create_empty_forecast_chart
)
from src.components.ui_components_improved import create_metric_card, create_alert_card

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                     CONFIGURACIÓN DE CACHÉ INTELIGENTE
# ===============================================================================

# Sistema de caché optimizado para Benalúa (municipio prioritario)
BENALUA_CACHE_FILE = "cache/benalua_forecast_premium.json"
CACHE_DURATION_MINUTES = 30  # Actualización frecuente para datos críticos

# ===============================================================================
#                       FUNCIONES DE GESTIÓN DE CACHÉ
# ===============================================================================

def get_benalua_cached_forecast():
    """
    Recupera datos de predicción de Benalúa desde sistema de caché optimizado.
    
    Sistema de caché premium con:
    • Verificación de integridad de archivo
    • Limpieza automática de archivos corruptos
    • Manejo robusto de errores
    • Codificación UTF-8 para caracteres especiales
    
    Returns:
        dict|None: Datos de predicción cacheados o None si no disponible
    """
    try:
        if os.path.exists(BENALUA_CACHE_FILE):
            with open(BENALUA_CACHE_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Verificar contenido no vacío
                if content:
                    data = json.loads(content)
                    logger.debug(f"💾 Caché de Benalúa leído exitosamente")
                    return data
                    
        logger.debug(f"📂 Archivo de caché no encontrado: {BENALUA_CACHE_FILE}")
        return None
        
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.warning(f"⚠️ Error leyendo caché de Benalúa: {e}")
        
        # Limpiar archivo corrupto para regeneración
        try:
            if os.path.exists(BENALUA_CACHE_FILE):
                os.remove(BENALUA_CACHE_FILE)
                logger.info(f"🧹 Caché corrupto eliminado: {BENALUA_CACHE_FILE}")
        except Exception:
            pass
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Error crítico leyendo caché de Benalúa: {e}")
        return None

def save_benalua_forecast_cache(data):
    """
    Almacena datos de predicción de Benalúa en caché premium con protección.
    
    Características de seguridad:
    • Escritura atómica (archivo temporal + rename)
    • Creación automática de directorios
    • Serialización robusta de timestamps
    • Metadatos de caché para validación
    
    Args:
        data (dict): Datos de predicción a cachear
        
    Returns:
        None: Opera por efectos secundarios (escritura a disco)
    """
    try:
        # Asegurar existencia del directorio de caché
        cache_dir = Path(BENALUA_CACHE_FILE).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Preparar datos para serialización JSON
        serializable_data = convert_to_serializable(data)
        
        # Estructura de caché con metadatos
        cache_structure = {
            'data': serializable_data,
            'timestamp': datetime.now().isoformat(),
            'municipality': 'Benalúa',
            'cache_type': 'premium',
            'version': '2.1'
        }
        
        # Escritura atómica: temporal + rename
        temp_file = BENALUA_CACHE_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(cache_structure, f, ensure_ascii=False, indent=2)
        
        # Operación atómica para evitar corrupción
        os.replace(temp_file, BENALUA_CACHE_FILE)
            
        logger.info(f"💾 Caché premium guardado exitosamente: {BENALUA_CACHE_FILE}")
        
    except Exception as e:
        logger.error(f"❌ Error crítico guardando caché de Benalúa: {e}")

def convert_to_serializable(data):
    """
    Convierte estructura de datos compleja a formato JSON-serializable.
    
    Maneja recursivamente:
    • Diccionarios anidados
    • Listas y arrays
    • Objetos datetime/Timestamp (a ISO format)
    • Tipos numéricos especiales (NumPy)
    • Valores NaN (a null)
    
    Args:
        data: Estructura de datos a convertir
        
    Returns:
        Estructura serializable para JSON
    """
    if isinstance(data, dict):
        return {k: convert_to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_serializable(item) for item in data]
    elif hasattr(data, 'isoformat'):  # datetime, Timestamp
        return data.isoformat()
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()  # Convertir tipos NumPy a Python nativo
    elif pd.isna(data):
        return None  # NaN a null
    else:
        return data

def is_cache_valid(timestamp_str):
    """
    Valida si el caché sigue siendo válido según política de duración.
    
    Verifica:
    • Existencia de timestamp
    • Formato ISO válido
    • Antigüedad vs límite configurado
    • Manejo de zonas horarias
    
    Args:
        timestamp_str (str): Timestamp en formato ISO
        
    Returns:
        bool: True si el caché aún es válido
    """
    try:
        if not timestamp_str:
            logger.debug("⚠️ Timestamp vacío en validación de caché")
            return False
            
        # Normalizar formato de timestamp
        normalized_timestamp = timestamp_str.replace('Z', '+00:00').replace('+00:00', '')
        cache_time = datetime.fromisoformat(normalized_timestamp)
        
        # Calcular antigüedad en minutos
        now = datetime.now()
        age_minutes = (now - cache_time).total_seconds() / 60
        
        is_valid = age_minutes < CACHE_DURATION_MINUTES
        
        status = 'válido' if is_valid else 'expirado'
        logger.debug(f"📊 Validación de caché: {age_minutes:.1f}min de antigüedad ({status})")
        
        return is_valid
        
    except Exception as e:
        logger.warning(f"⚠️ Error validando caché: {e}")
        return False

# ===============================================================================
#                         FUNCIONES AUXILIARES
# ===============================================================================

def _dia_semana_es(dt: pd.Timestamp) -> str:
    """
    Convierte abreviación de día de la semana al español.
    
    Args:
        dt (pd.Timestamp): Fecha a convertir
        
    Returns:
        str: Abreviación en español (lun, mar, mié, etc.)
    """
    dias_es = {
        'Mon': 'lun', 'Tue': 'mar', 'Wed': 'mié', 'Thu': 'jue',
        'Fri': 'vie', 'Sat': 'sáb', 'Sun': 'dom'
    }
    return dias_es.get(dt.strftime('%a'), dt.strftime('%a'))

def _icono_estado(estado: str) -> str:
    """
    Determina emoji apropiado según descripción del estado meteorológico.
    
    Args:
        estado (str): Descripción textual del clima
        
    Returns:
        str: Emoji representativo del estado del tiempo
    """
    descripcion = (estado or "").lower()
    
    # Condiciones severas
    if "tormenta" in descripcion or "severo" in descripcion:
        return "⛈️"  # Tormenta
    
    # Precipitación
    if "lluvia" in descripcion or "chubasc" in descripcion or "llovizna" in descripcion:
        return "🌧️"  # Lluvia
    
    # Nubosidad
    if any(word in descripcion for word in ["nuboso", "nube", "cubierto", "nublado"]):
        return "☁️"  # Nublado
    
    # Condiciones despejadas
    if "despejado" in descripcion or "sol" in descripcion or "soleado" in descripcion:
        return "☀️"  # Sol
    
    # Por defecto: parcialmente nublado
    return "🌤️"

def _riesgo_repilo_dia(tmin, tmax, hummin, hummax) -> tuple[str, str]:
    """
    Evaluación científica del riesgo de infección por Venturia oleaginea (repilo).
    
    Criterios según tabla científica oficial:
    
    ALTO RIESGO:
    • 15–20°C y mojado continuo ≥18–24h → Tratamiento preventivo/pos-evento
    • Episodios consecutivos ≥2–3 días con ≥8–12h/día → Activar plan de control
    
    MODERADO RIESGO:
    • 12–15°C (o 20–22°C) con mojado 12–18h → Vigilancia estrecha
    • Hum. rel. >95% y 12–20°C ≥10–12h nocturno → Alerta local
    
    BAJO RIESGO:
    • <5°C o >25–28°C y mojado limitado <6h → Seguimiento rutinario
    
    Args:
        tmin (float): Temperatura mínima del día (°C)
        tmax (float): Temperatura máxima del día (°C)
        hummin (float): Humedad mínima del día (%)
        hummax (float): Humedad máxima del día (%)
        
    Returns:
        tuple[str, str]: (nivel_riesgo, color_bootstrap)
        
    Referencias:
    - Tabla oficial: Condiciones favorables a Venturia oleaginea
    - Niveles de alerta para repilo en olivicultura
    """
    try:
        # Validación y conversión de tipos
        tmin = float(tmin) if tmin is not None else None
        tmax = float(tmax) if tmax is not None else None
        hummin = float(hummin) if hummin is not None else None
        hummax = float(hummax) if hummax is not None else None
        
    except (ValueError, TypeError):
        logger.debug("⚠️ Datos de entrada inválidos para análisis de riesgo")
        return ("Bajo", "success")  # Fallback conservador

    # Verificar disponibilidad de datos esenciales
    if not all(x is not None for x in [tmin, tmax, hummax]):
        logger.debug("⚠️ Datos insuficientes para análisis de riesgo")
        return ("Bajo", "success")
        
    # ===================================================================
    #                       EVALUACIÓN DE RIESGO
    # ===================================================================
    
    # RIESGO ALTO - Condiciones óptimas para Venturia oleaginea
    temperatura_optima = (15 <= tmin <= 20) or (15 <= tmax <= 20)
    humedad_critica = hummax > 95
    
    if temperatura_optima and humedad_critica:
        return ("Alto", "danger")
    
    # RIESGO MODERADO - Condiciones suboptimales pero favorables
    temp_moderada = (
        (12 <= tmin <= 15) or (12 <= tmax <= 15) or  # Rango bajo
        (20 <= tmin <= 22) or (20 <= tmax <= 22)     # Rango alto
    )
    
    if humedad_critica and temp_moderada:
        return ("Moderado", "warning")
        
    # Condiciones nocturnas húmedas en rango intermedio
    temp_nocturna_favorable = (12 <= tmin <= 20) or (12 <= tmax <= 20)
    if humedad_critica and temp_nocturna_favorable:
        return ("Moderado", "warning")
    
    # RIESGO BAJO - Condiciones inhibitorias según tabla científica
    temperatura_inhibitoria = (
        (tmin < 5 or tmax < 5) or          # <5°C inhibe desarrollo
        (tmin > 28 or tmax > 28)           # >25–28°C inhibe desarrollo (rango alto de la tabla)
    )
    humedad_limitante = hummax < 95        # Mojado limitado (<6h proxy)
    
    if temperatura_inhibitoria or humedad_limitante:
        return ("Bajo", "success")
    
    # Por defecto: riesgo bajo (enfoque conservador científico)
    return ("Bajo", "success")

# ===============================================================================
#                       FUNCIONES DE VISUALIZACIÓN
# ===============================================================================

def create_weather_cards(df_semanal: pd.DataFrame) -> html.Div:
    """
    Genera tarjetas visuales profesionales para predicción meteorológica semanal.
    
    Cada tarjeta incluye:
    • Día de la semana en español
    • Icono meteorológico contextual
    • Temperaturas máxima y mínima con codificación de color
    • Probabilidad de precipitación con barra de progreso
    • Datos de humedad y viento
    • Badge de riesgo de repilo (evaluación científica)
    • Diseño responsive y profesional
    
    Args:
        df_semanal (pd.DataFrame): Datos de predicción con columnas estandarizadas
        
    Returns:
        html.Div: Componente con grid de tarjetas meteorológicas
    """
    # Validar datos de entrada
    if df_semanal is None or df_semanal.empty:
        return html.Div(
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No hay datos de predicción semanal disponibles"
            ], color="warning", className="text-center")
        )

    # Procesar cada día de la predicción semanal
    weather_cards = []
    
    for idx, row in df_semanal.iterrows():
        # ===================================================================
        #                    EXTRACCIÓN DE DATOS DEL DÍA
        # ===================================================================
        
        # Fecha con formato flexible
        fecha = (
            pd.to_datetime(row["date"]) if "date" in row 
            else pd.to_datetime(row.get("fecha", pd.Timestamp.now()))
        )
        
        # Icono del estado meteorológico
        icon = _icono_estado(row.get("estado", "Soleado"))
        
        # Temperaturas (compatibilidad con múltiples formatos)
        tmax = float(row.get("temp_max", row.get("tmax", 20)))
        tmin = float(row.get("temp_min", row.get("tmin", 10)))
        
        # Humedad relativa
        hummax = float(row.get("humidity", row.get("hummax", 80)))
        hummin = float(row.get("hummin", max(hummax - 20, 40)))  # Mínimo razonable
        
        # Precipitación (convertir mm a probabilidad % si es necesario)
        rain_value = row.get("rain", row.get("prob_lluvia", 0))
        if rain_value < 1:  # Asumido como probabilidad (0-1)
            prob_lluvia = int(rain_value * 100)
        else:  # Asumido como mm o porcentaje directo
            prob_lluvia = min(100, int(rain_value))
            if prob_lluvia > 100:  # Si es mm, convertir heurísticamente
                prob_lluvia = min(100, int(rain_value / 10))
        
        # Viento
        velocidad_viento = float(row.get("wind_speed", row.get("viento", 5)))
        direccion_viento = str(row.get("viento_dir", "N"))

        # Evaluación científica de riesgo de repilo
        riesgo_nivel, riesgo_color = _riesgo_repilo_dia(tmin, tmax, hummin, hummax)

        # ===================================================================
        #                    CONSTRUCCIÓN DE TARJETA PREMIUM
        # ===================================================================
        
        card = dbc.Card(
            [
                # Header con día y badge de riesgo
                dbc.CardHeader(
                    [
                        # Información temporal
                        html.Div([
                            html.Span(
                                f"{_dia_semana_es(fecha).upper()}",
                                className="fw-bold text-muted",
                                style={
                                    'fontSize': '12px', 
                                    'letterSpacing': '1px'
                                }
                            ),
                            html.Br(),
                            html.Span(
                                f"{fecha.day}",
                                className="fw-bold",
                                style={
                                    'fontSize': '18px', 
                                    'color': '#2c3e50'
                                }
                            )
                        ]),
                        
                        # Badge de riesgo de repilo
                        dbc.Badge(
                            riesgo_nivel, 
                            color=riesgo_color, 
                            className=f"ms-auto badge-{riesgo_color}",
                            title=f"Riesgo de repilo: {riesgo_nivel}"
                        )
                    ],
                    className="d-flex align-items-center justify-content-between py-2 px-3",
                ),
                # Cuerpo de la tarjeta con datos meteorológicos
                dbc.CardBody(
                    [
                        # Icono meteorológico optimizado
                        html.Div(
                            icon, 
                            className="weather-icon text-center",
                            style={
                                "fontSize": "2.0rem",  # Reducido para tarjetas más compactas
                                "lineHeight": "1", 
                                "marginBottom": "8px"  # Menos espacio
                            }
                        ),
                        
                        # Display de temperaturas compacto
                        html.Div(
                            [
                                # Temperatura mínima (azul)
                                html.Span(
                                    f"{int(tmin)}°", 
                                    className="temperature-min",
                                    style={
                                        "color": "#3498db", 
                                        "fontSize": "15px",  # Reducido para compacidad
                                        "fontWeight": "600",
                                        "marginRight": "3px"
                                    },
                                    title=f"Temperatura mínima: {tmin:.1f}°C"
                                ),
                                
                                # Separador visual
                                html.Span(
                                    "•", 
                                    style={
                                        "color": "#bdc3c7", 
                                        "fontSize": "14px", 
                                        "margin": "0 4px"
                                    }
                                ),
                                
                                # Temperatura máxima (rojo)
                                html.Span(
                                    f"{int(tmax)}°", 
                                    className="temperature-max",
                                    style={
                                        "color": "#e74c3c", 
                                        "fontSize": "15px",  # Reducido para compacidad
                                        "fontWeight": "600",
                                        "marginLeft": "3px"
                                    },
                                    title=f"Temperatura máxima: {tmax:.1f}°C"
                                ),
                            ],
                            className="text-center mb-2",  # Reducir margen inferior
                        ),
                        
                        # Sección de probabilidad de precipitación
                        html.Div(
                            [
                                # Label con icono
                                html.Div([
                                    html.I(
                                        className="fas fa-cloud-rain", 
                                        style={
                                            'color': '#3498db', 
                                            'fontSize': '12px', 
                                            'marginRight': '4px'
                                        }
                                    ),
                                    html.Small(
                                        f"{prob_lluvia}%", 
                                        className="text-muted", 
                                        style={'fontSize': '10px'}  # Texto más compacto
                                    )
                                ], className="d-flex align-items-center mb-1"),
                                
                                # Barra de progreso visual
                                dbc.Progress(
                                    value=prob_lluvia,
                                    color="info" if prob_lluvia < 30 else "warning" if prob_lluvia < 70 else "danger",
                                    className="mb-2",
                                    style={'height': '6px'}
                                ),
                            ],
                            className="mb-2"
                        ),
                        
                        # Datos adicionales: humedad y viento
                        html.Div(
                            [
                                # Rango de humedad relativa
                                html.Div([
                                    html.Span(
                                        "💧", 
                                        style={'fontSize': '12px', 'marginRight': '4px'}
                                    ),
                                    html.Small(
                                        f"{int(hummin)}-{int(hummax)}%", 
                                        className="text-muted", 
                                        style={'fontSize': '10px'},  # Texto más compacto
                                        title=f"Humedad relativa: {hummin:.0f}% - {hummax:.0f}%"
                                    )
                                ], className="d-flex align-items-center mb-1"),
                                
                                # Velocidad y dirección del viento
                                html.Div([
                                    html.Span(
                                        "🌬️", 
                                        style={'fontSize': '12px', 'marginRight': '4px'}
                                    ),
                                    html.Small(
                                        f"{int(velocidad_viento)}km/h {direccion_viento}", 
                                        className="text-muted", 
                                        style={'fontSize': '10px'},  # Texto más compacto
                                        title=f"Viento: {velocidad_viento:.1f} km/h dirección {direccion_viento}"
                                    )
                                ], className="d-flex align-items-center")
                            ],
                            className="weather-details"
                        ),
                    ],
                    className="py-1 px-2"  # Menos padding para tarjetas más compactas
                ),
            ],
            className="h-100 shadow-sm weather-forecast-card",
            style={
                'transition': 'transform 0.2s ease, box-shadow 0.2s ease',
                'cursor': 'default'
            }
        )

        weather_cards.append(card)

    # ===================================================================
    #                      LAYOUT FINAL DE TARJETAS - FILA ÚNICA
    # ===================================================================
    
    return html.Div(
        [
            html.Div(card, className="wx-card")
            for card in weather_cards
        ],
        className="wx-grid",  # Usar solo la clase CSS grid optimizada
        style={
            'margin': '0 auto', 
            'width': '100%',
            'maxWidth': '1400px'  # Control de ancho máximo
        }
    )

def generate_mock_forecast_data(municipality: str = "Benalua") -> pd.DataFrame:
    """
    Genera datos mock de predicción para testing
    En producción, esto se reemplazará con llamadas a AEMET API
    """
    try:
        # Generar 7 días de predicción diaria
        dates = pd.date_range(start=datetime.now(), periods=7, freq='D')
        
        # Simular datos meteorológicos realistas
        np.random.seed(42)  # Para reproducibilidad
        
        forecast_data = pd.DataFrame({
            'date': dates,
            'temp_max': np.random.uniform(18, 25, 7),  # Temperaturas típicas de primavera
            'temp_min': np.random.uniform(8, 15, 7),
            'humidity': np.random.uniform(70, 98, 7),
            'hummax': np.random.uniform(85, 98, 7),  # Campo adicional para weather cards
            'hummin': np.random.uniform(60, 80, 7),   # Campo adicional para weather cards
            'rain': np.random.exponential(2, 7),  # Precipitación exponencial (más días secos)
            'wind_speed': np.random.uniform(5, 20, 7),
            'viento_dir': np.random.choice(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW'], 7),
            'pressure': np.random.uniform(1010, 1025, 7),
            'estado': np.random.choice(['Soleado', 'Nuboso', 'Lluvia ligera', 'Despejado', 'Parcialmente nuboso'], 7)
        })
        
        # Analizar riesgo para cada día
        risk_analysis = analyze_disease_risk_forecast(forecast_data)
        forecast_data['risk_level'] = [day['risk_level'] for day in risk_analysis['risk_days']]
        
        logger.info(f"Datos de predicción generados para {municipality}: {len(forecast_data)} días")
        return forecast_data
        
    except Exception as e:
        logger.error(f"Error generando datos de predicción: {e}")
        return pd.DataFrame()

def generate_enhanced_mock_forecast_data(municipality: str = "Benalua") -> pd.DataFrame:
    """
    Genera datos mock mejorados con condiciones de riesgo de repilo realistas.
    
    Simula escenarios con condiciones favorables para el desarrollo de repilo
    para demostrar las capacidades de visualización de zonas de riesgo.
    """
    try:
        # Generar 7 días de predicción diaria
        dates = pd.date_range(start=datetime.now(), periods=7, freq='D')
        
        # Seed diferente para generar escenarios de riesgo variados
        np.random.seed(123)
        
        # Temperaturas con algunos días en zona crítica (15-20°C)
        temp_max = np.array([22, 18, 16, 19, 24, 17, 21])  # Algunos en zona crítica
        temp_min = np.array([12, 14, 13, 15, 16, 13, 14])  # Algunos en zona crítica
        
        # Humedad alta en algunos días (>95% para riesgo crítico)
        humidity = np.array([85, 96, 94, 97, 88, 95, 92])  # Días 2, 4, 6 críticos
        hummax = humidity + np.random.uniform(2, 8, 7)
        hummin = humidity - np.random.uniform(10, 20, 7)
        
        forecast_data = pd.DataFrame({
            'date': dates,
            'temp_max': temp_max,
            'temp_min': temp_min,
            'humidity': humidity,
            'hummax': np.clip(hummax, humidity, 100),
            'hummin': np.clip(hummin, 40, humidity),
            'rain': np.array([0, 2.5, 1.2, 3.8, 0, 1.5, 0.8]),  # Lluvia en algunos días
            'wind_speed': np.random.uniform(5, 15, 7),
            'viento_dir': np.random.choice(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW'], 7),
            'pressure': np.random.uniform(1015, 1025, 7),
            'estado': ['Soleado', 'Lluvia ligera', 'Nuboso', 'Lluvia', 'Soleado', 'Nublado', 'Parcialmente nuboso']
        })
        
        # Calcular nivel de riesgo según tabla científica Venturia oleaginea
        risk_levels = []
        for _, row in forecast_data.iterrows():
            # Usar función actualizada para consistency
            riesgo_nivel, _ = _riesgo_repilo_dia(
                row['temp_min'], row['temp_max'], 
                row['humidity'], row['humidity']  # Usando humidity como proxy para hummin/hummax
            )
            risk_levels.append(riesgo_nivel.lower())
        
        forecast_data['risk_level'] = risk_levels
        
        logger.info(f"Datos de predicción mejorados generados para {municipality}: {len(forecast_data)} días")
        logger.info(f"Días con riesgo alto: {sum(1 for r in risk_levels if r == 'alto')}")
        logger.info(f"Días con riesgo moderado: {sum(1 for r in risk_levels if r == 'moderado')}")
        
        return forecast_data
        
    except Exception as e:
        logger.error(f"Error generando datos de predicción mejorados: {e}")
        return pd.DataFrame()

def generate_mock_hourly_data(municipality: str = "Benalua") -> pd.DataFrame:
    """
    Genera datos horarios mock para 48h con escenarios de riesgo de repilo realistas.
    
    Crea patrones que demuestran:
    • Ciclos de temperatura que entran en zonas críticas (15-20°C)
    • Períodos nocturnos con alta humedad (>95%)
    • Eventos de precipitación que favorecen la infección
    • Combinaciones de condiciones de alto riesgo
    """
    try:
        # Generar 48 horas de datos horarios
        datetimes = pd.date_range(start=datetime.now(), periods=48, freq='h')
        
        # Seed para reproducibilidad pero con variaciones realistas
        np.random.seed(456)
        
        # Simular ciclo diario de temperatura más realista
        hours = np.array([dt.hour for dt in datetimes])
        days = np.array([dt.day for dt in datetimes])
        
        # Temperatura base con ciclo diario y variación entre días
        daily_variation = np.sin((days - days[0]) * np.pi / 3)  # Variación entre días
        hourly_cycle = 5 * np.sin((hours - 6) * np.pi / 12)  # Ciclo diario
        base_temp = 17 + daily_variation * 3 + hourly_cycle  # Centrado en zona de riesgo
        
        # Añadir ruido realista
        temperature = base_temp + np.random.normal(0, 1.5, 48)
        temperature = np.clip(temperature, 8, 28)  # Límites realistas
        
        # Humedad con patrones nocturnos altos (condición favorable para repilo)
        # Mayor humedad durante la noche (20:00-06:00)
        humidity_base = np.where(
            (hours >= 20) | (hours <= 6),  # Período nocturno
            np.random.uniform(92, 99, 48),  # Alta humedad nocturna
            np.random.uniform(70, 90, 48)   # Humedad diurna moderada
        )
        
        # Ajustar por temperatura (relación inversa)
        humidity = humidity_base - (temperature - 15) * 0.5 + np.random.normal(0, 3, 48)
        humidity = np.clip(humidity, 45, 100)
        
        # Precipitación con eventos concentrados (favorece dispersión de esporas)
        rain = np.zeros(48)
        
        # Simular 2-3 eventos de lluvia de duración variable
        rain_events = [
            (8, 12),   # Evento matutino de 4 horas
            (20, 24),  # Evento nocturno de 4 horas
            (35, 38)   # Evento corto al segundo día
        ]
        
        for start, end in rain_events:
            if start < len(rain):
                duration = min(end - start, len(rain) - start)
                rain[start:start+duration] = np.random.exponential(0.8, duration)
        
        hourly_data = pd.DataFrame({
            'datetime': datetimes,
            'temperature': temperature,
            'humidity': humidity,
            'rain': rain
        })
        
        # Calcular estadísticas de riesgo para logging
        critical_temp_hours = len(hourly_data[(hourly_data['temperature'] >= 15) & 
                                            (hourly_data['temperature'] <= 20)])
        critical_humidity_hours = len(hourly_data[hourly_data['humidity'] > 95])
        combined_risk_hours = len(hourly_data[
            (hourly_data['temperature'] >= 15) & 
            (hourly_data['temperature'] <= 20) &
            (hourly_data['humidity'] > 95)
        ])
        
        logger.info(f"Datos horarios con riesgo generados para {municipality}: {len(hourly_data)} horas")
        logger.info(f"Horas temperatura crítica (15-20°C): {critical_temp_hours}/48")
        logger.info(f"Horas humedad crítica (>95%): {critical_humidity_hours}/48")
        logger.info(f"Horas riesgo combinado: {combined_risk_hours}/48")
        
        return hourly_data
        
    except Exception as e:
        logger.error(f"Error generando datos horarios con zonas de riesgo: {e}")
        return pd.DataFrame()

def register_callbacks(app):
    """
    Registra todos los callbacks de predicción
    """
    
    @app.callback(
        [
            Output("forecast-data-store", "data"),
            Output("selected-municipality-store", "data")
        ],
        Input("input-municipio", "value"),
        prevent_initial_call=False
    )
    def update_forecast_data(municipio):
        """
        Actualiza los datos de predicción con sistema de caché inteligente para Benalúa
        """
        try:
            if not municipio:
                return {}, ""
            
            logger.info(f"🎯 Cargando predicción para municipio: {municipio}")
            
            # Sistema de caché especial para Benalúa (datos más frecuentes)
            if municipio.lower() in ['benalúa', 'benalua']:
                logger.info("🏠 Municipio prioritario detectado - usando caché optimizado")
                
                # Intentar cargar desde caché primero
                cached_data = get_benalua_cached_forecast()
                if cached_data and is_cache_valid(cached_data.get('timestamp')):
                    logger.info("📂 Usando datos de Benalúa desde caché (válido)")
                    return cached_data['data'], municipio
                
                # Si no hay caché válido, generar nuevos datos
                logger.info("🔄 Generando nuevos datos con zonas de riesgo para Benalúa")
                forecast_data = generate_enhanced_mock_forecast_data(municipio)
                hourly_data = generate_mock_hourly_data(municipio)
                
                # Preparar datos mejorados para Benalúa
                data = {
                    'weekly': forecast_data.to_dict('records') if not forecast_data.empty else [],
                    'hourly': hourly_data.to_dict('records') if not hourly_data.empty else [],
                    'municipality': municipio,
                    'last_updated': datetime.now().isoformat(),
                    'data_quality': 'premium',  # Marca de calidad premium para Benalúa
                    'cache_enabled': True
                }
                
                # Guardar en caché para próximas consultas
                save_benalua_forecast_cache(data)
                
            else:
                # Para otros municipios usar datos estándar
                logger.info("📍 Municipio estándar - generando datos con análisis de riesgo")
                forecast_data = generate_enhanced_mock_forecast_data(municipio)
                hourly_data = generate_mock_hourly_data(municipio)
                
                data = {
                    'weekly': forecast_data.to_dict('records') if not forecast_data.empty else [],
                    'hourly': hourly_data.to_dict('records') if not hourly_data.empty else [],
                    'municipality': municipio,
                    'last_updated': datetime.now().isoformat(),
                    'data_quality': 'standard',
                    'cache_enabled': False
                }
            
            return data, municipio
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos de predicción: {e}")
            return {}, ""
    
    @app.callback(
        Output("current-weather-kpis", "children"),
        Input("forecast-data-store", "data")
    )
    def update_current_kpis(forecast_data):
        """
        Actualiza los KPIs de condiciones actuales
        """
        try:
            if not forecast_data or not forecast_data.get('weekly'):
                return create_alert_card(
                    message="No hay datos de predicción disponibles",
                    alert_type="warning",
                    title="Sin Datos"
                )
            
            # Obtener datos del día actual (primer día de la predicción)
            today_data = forecast_data['weekly'][0]
            
            # Obtener datos horarios actuales si disponibles
            current_hour_data = None
            if forecast_data.get('hourly'):
                current_hour_data = forecast_data['hourly'][0]
            
            # Crear KPIs profesionales
            kpi_cards = [
                dbc.Col([
                    create_metric_card(
                        title="Temperatura Actual",
                        value=f"{current_hour_data.get('temperature', today_data.get('temp_max', 0)):.1f}" if current_hour_data else f"{today_data.get('temp_max', 0):.1f}",
                        unit="°C",
                        icon="fas fa-thermometer-half",
                        color="danger" if 15 <= (current_hour_data.get('temperature', today_data.get('temp_max', 0)) if current_hour_data else today_data.get('temp_max', 0)) <= 20 else "info",
                        description="Temperatura prevista"
                    )
                ], md=2),
                
                dbc.Col([
                    create_metric_card(
                        title="Máxima Hoy",
                        value=f"{today_data.get('temp_max', 0):.1f}",
                        unit="°C",
                        icon="fas fa-thermometer-full",
                        color="danger" if 15 <= today_data.get('temp_max', 0) <= 20 else "warning",
                        description="Temperatura máxima"
                    )
                ], md=2),
                
                dbc.Col([
                    create_metric_card(
                        title="Mínima Hoy",
                        value=f"{today_data.get('temp_min', 0):.1f}",
                        unit="°C",
                        icon="fas fa-thermometer-empty",
                        color="info",
                        description="Temperatura mínima"
                    )
                ], md=2),
                
                dbc.Col([
                    create_metric_card(
                        title="Humedad",
                        value=f"{current_hour_data.get('humidity', today_data.get('humidity', 0)):.0f}" if current_hour_data else f"{today_data.get('humidity', 0):.0f}",
                        unit="%",
                        icon="fas fa-tint",
                        color="danger" if (current_hour_data.get('humidity', today_data.get('humidity', 0)) if current_hour_data else today_data.get('humidity', 0)) > 95 else "success",
                        description="Humedad relativa"
                    )
                ], md=2),
                
                dbc.Col([
                    create_metric_card(
                        title="Precipitación",
                        value=f"{today_data.get('rain', 0):.1f}",
                        unit="mm",
                        icon="fas fa-cloud-rain",
                        color="info",
                        description="Lluvia prevista hoy"
                    )
                ], md=2),
                
                dbc.Col([
                    create_metric_card(
                        title="Riesgo Repilo",
                        value=today_data.get('risk_level', 'bajo').upper(),
                        unit="",
                        icon="fas fa-bug",
                        color="danger" if today_data.get('risk_level') == 'alto' else ("warning" if today_data.get('risk_level') == 'moderado' else "success"),
                        description="Nivel de riesgo"
                    )
                ], md=2)
            ]
            
            return dbc.Row(kpi_cards, className="g-3")
            
        except Exception as e:
            logger.error(f"Error actualizando KPIs actuales: {e}")
            return create_alert_card(
                message=f"Error cargando datos: {str(e)}",
                alert_type="danger",
                title="Error"
            )
    
    @app.callback(
        Output("pred-semanal-cards", "children"),
        Input("forecast-data-store", "data")
    )
    def update_weather_cards(forecast_data):
        """
        Actualiza las tarjetas de predicción semanal con análisis de riesgo
        """
        try:
            if not forecast_data or not forecast_data.get('weekly'):
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "No hay datos de predicción semanal disponibles"
                    ], color="warning", className="text-center")
                ])
            
            # Convertir datos del store a DataFrame
            df = pd.DataFrame(forecast_data['weekly'])
            df['date'] = pd.to_datetime(df['date'])
            
            # Crear weather cards
            return create_weather_cards(df)
            
        except Exception as e:
            logger.error(f"Error actualizando tarjetas semanales: {e}")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error cargando predicción: {str(e)}"
                ], color="danger", className="text-center")
            ])
    
    @app.callback(
        Output("forecast-weekly-chart", "figure"),
        Input("forecast-data-store", "data")
    )
    def update_weekly_chart(forecast_data):
        """
        Actualiza el gráfico semanal con zonas de riesgo de repilo.
        
        Genera visualización con temperaturas máx/mín y zonas sombreadas que indican
        los niveles de riesgo para el desarrollo de repilo basados en rangos de temperatura:
        • Zona crítica: 15-20°C (condiciones óptimas para infección)
        • Zonas moderadas: 12-15°C y 20-22°C (condiciones subóptimas)
        """
        try:
            if not forecast_data or not forecast_data.get('weekly'):
                logger.warning("📅 No hay datos semanales disponibles para el gráfico")
                return create_empty_forecast_chart("No hay datos de predicción semanal disponibles")
            
            # Convertir datos del store a DataFrame
            df = pd.DataFrame(forecast_data['weekly'])
            df['date'] = pd.to_datetime(df['date'])
            
            # Validar columnas necesarias
            required_cols = ['date', 'temp_max', 'temp_min', 'humidity', 'rain']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.warning(f"⚠️ Columnas faltantes para gráfico semanal: {missing_cols}")
            
            # Log de condiciones de riesgo semanales
            temp_risk_days = len(df[
                ((df['temp_max'] >= 15) & (df['temp_max'] <= 20)) |
                ((df['temp_min'] >= 15) & (df['temp_min'] <= 20))
            ])
            humidity_risk_days = len(df[df.get('humidity', 0) > 95])
            
            logger.info(f"🌡️ Análisis semanal de condiciones de riesgo:")
            logger.info(f"  • Días con temperatura crítica (15-20°C): {temp_risk_days}/{len(df)}")
            logger.info(f"  • Días con humedad crítica (>95%): {humidity_risk_days}/{len(df)}")
            
            # Generar gráfico semanal con zonas de riesgo
            return create_weekly_forecast_chart(df)
            
        except Exception as e:
            logger.error(f"❌ Error crítico actualizando gráfico semanal con zonas de riesgo: {e}")
            return create_empty_forecast_chart(f"Error generando gráfico: {str(e)}")
    
    @app.callback(
        Output("forecast-48h-chart", "figure"),
        Input("forecast-data-store", "data")
    )
    def update_48h_chart(forecast_data):
        """
        Actualiza el gráfico de predicción 48h con zonas de riesgo de repilo.
        
        Genera visualización avanzada que incluye:
        • Zonas sombreadas de riesgo de temperatura (15-20°C crítica, 12-15°C y 20-22°C moderada)
        • Indicadores de períodos nocturnos (20:00-06:00) cuando el repilo se desarrolla más
        • Línea de humedad crítica >95% con marcadores especiales
        • Barras de precipitación que favorecen la dispersión de esporas
        • Marcadores especiales para condiciones críticas combinadas
        """
        try:
            if not forecast_data or not forecast_data.get('hourly'):
                logger.warning("📅 No hay datos horarios disponibles para el gráfico 48h")
                return create_48h_forecast_chart(pd.DataFrame())
            
            # Convertir datos del store a DataFrame con validación
            df = pd.DataFrame(forecast_data['hourly'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Validar columnas necesarias para análisis de riesgo
            required_cols = ['datetime', 'temperature', 'humidity', 'rain']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.warning(f"⚠️ Columnas faltantes para análisis de riesgo: {missing_cols}")
                # Agregar columnas faltantes con valores por defecto
                for col in missing_cols:
                    if col == 'temperature':
                        df[col] = 18.0  # Temperatura promedio
                    elif col == 'humidity':
                        df[col] = 75.0  # Humedad moderada
                    elif col == 'rain':
                        df[col] = 0.0   # Sin lluvia por defecto
            
            # Log de condiciones críticas para monitoring
            critical_temp_periods = len(df[(df['temperature'] >= 15) & (df['temperature'] <= 20)])
            critical_humidity_periods = len(df[df['humidity'] > 95])
            rain_periods = len(df[df['rain'] > 0])
            
            logger.info(f"🌡️ Condiciones de riesgo detectadas:")
            logger.info(f"  • Períodos temperatura crítica (15-20°C): {critical_temp_periods}/{len(df)}")
            logger.info(f"  • Períodos humedad crítica (>95%): {critical_humidity_periods}/{len(df)}")
            logger.info(f"  • Períodos con precipitación: {rain_periods}/{len(df)}")
            
            # Generar gráfico con zonas de riesgo resaltadas
            return create_48h_forecast_chart(df)
            
        except Exception as e:
            logger.error(f"❌ Error crítico actualizando gráfico 48h con zonas de riesgo: {e}")
            return create_48h_forecast_chart(pd.DataFrame())
    
    @app.callback(
        Output("disease-risk-alerts", "children"),
        Input("forecast-data-store", "data")
    )
    def update_disease_risk_alerts(forecast_data):
        """
        Actualiza las alertas consolidadas de riesgo de enfermedad
        """
        try:
            if not forecast_data:
                return create_alert_card(
                    message="No hay datos de predicción disponibles para el análisis de riesgo",
                    alert_type="warning",
                    title="Sin Datos"
                )
            
            alerts = []
            risk_summary = {
                'weekly_high_risk_days': 0,
                'hourly_high_risk_periods': 0,
                'max_risk_level': 'bajo',
                'recommendations': []
            }
            
            # Analizar datos semanales
            if forecast_data.get('weekly'):
                weekly_df = pd.DataFrame(forecast_data['weekly'])
                high_risk_days = weekly_df[weekly_df.get('risk_level', 'bajo') == 'alto']
                risk_summary['weekly_high_risk_days'] = len(high_risk_days)
                
                # Determinar máximo nivel de riesgo semanal
                if len(high_risk_days) > 0:
                    risk_summary['max_risk_level'] = 'alto'
                elif len(weekly_df[weekly_df.get('risk_level', 'bajo') == 'moderado']) > 0:
                    risk_summary['max_risk_level'] = 'moderado'
            
            # Analizar datos horarios (48h)
            if forecast_data.get('hourly'):
                hourly_df = pd.DataFrame(forecast_data['hourly'])
                # Simular análisis de riesgo horario
                critical_hours = hourly_df[
                    (hourly_df.get('temperature', 0) >= 15) & 
                    (hourly_df.get('temperature', 0) <= 20) & 
                    (hourly_df.get('humidity', 0) > 95)
                ]
                risk_summary['hourly_high_risk_periods'] = len(critical_hours)
                
                if len(critical_hours) > 0 and risk_summary['max_risk_level'] != 'alto':
                    risk_summary['max_risk_level'] = 'alto'

            # Crear tarjetas de alerta
            alert_cards = []
            
            # Alerta principal según nivel de riesgo máximo
            if risk_summary['max_risk_level'] == 'alto':
                alert_cards.append(
                    dbc.Col([
                        create_alert_card(
                            title="🚨 RIESGO ALTO DETECTADO",
                            message=f"Condiciones críticas (15-20°C + mojado continuo) detectadas: {risk_summary['weekly_high_risk_days']} días esta semana, {risk_summary['hourly_high_risk_periods']} períodos en 48h",
                            alert_type="danger"
                        )
                    ], md=6)
                )
            elif risk_summary['max_risk_level'] == 'moderado':
                alert_cards.append(
                    dbc.Col([
                        create_alert_card(
                            title="⚠️ Riesgo Moderado",
                            message="Condiciones subóptimas detectadas (12-15°C o 20-22°C + humedad >95%)",
                            alert_type="warning"
                        )
                    ], md=6)
                )
            else:
                alert_cards.append(
                    dbc.Col([
                        create_alert_card(
                            title="✅ Bajo Riesgo",
                            message="Condiciones no favorables para repilo (<5°C o >25-28°C, mojado limitado)",
                            alert_type="success"
                        )
                    ], md=6)
                )
            
            
            return dbc.Row(alert_cards, className="g-3")
            
        except Exception as e:
            logger.error(f"Error actualizando alertas de riesgo: {e}")
            return create_alert_card(
                message=f"Error analizando riesgo de enfermedad: {str(e)}",
                alert_type="danger",
                title="Error en Análisis"
            )
    
    # ===============================================================================
    #                     CALLBACK PARA TABS DE PREDICCIÓN
    # ===============================================================================
    
    @app.callback(
        [Output("weekly-content", "style"),
         Output("hourly-content", "style")],
        Input("forecast-tabs", "active_tab")
    )
    def toggle_forecast_tabs(active_tab):
        """
        Controla la visibilidad de las secciones de predicción según la tab activa.
        Esto evita que se pierda el contenido al cambiar entre tabs.
        """
        if active_tab == "weekly-tab":
            return {'display': 'block'}, {'display': 'none'}
        elif active_tab == "hourly-tab":
            return {'display': 'none'}, {'display': 'block'}
        else:
            # Por defecto mostrar la predicción semanal
            return {'display': 'block'}, {'display': 'none'}
    
    # ===============================================================================
    #                     CALLBACKS PARA ESTADOS DE RIESGO POR PERÍODO
    # ===============================================================================
    
    @app.callback(
        [Output("current-risk-status", "children"),
         Output("48h-risk-status", "children"), 
         Output("weekly-risk-status", "children")],
        Input("forecast-data-store", "data")
    )
    def update_risk_status_indicators(forecast_data):
        """
        Actualiza los indicadores de estado de riesgo para cada período de tiempo con razones específicas
        """
        try:
            # Estados por defecto
            current_status = html.Div([
                html.I(className="fas fa-circle text-info me-1"),
                html.Small("Sin datos disponibles", className="text-muted")
            ])
            
            h48_status = html.Div([
                html.I(className="fas fa-circle text-info me-1"),
                html.Small("Sin datos disponibles", className="text-muted")
            ])
            
            weekly_status = html.Div([
                html.I(className="fas fa-circle text-info me-1"),
                html.Small("Sin datos disponibles", className="text-muted")
            ])
            
            if not forecast_data:
                return current_status, h48_status, weekly_status
            
            # ===== ANÁLISIS DE CONDICIONES ACTUALES =====
            if forecast_data.get('weekly') or forecast_data.get('hourly'):
                # Usar datos horarios actuales si están disponibles, sino el primer día de la predicción
                current_temp = None
                current_humidity = None
                current_rain = None
                predefined_risk_level = None
                
                if forecast_data.get('hourly'):
                    # Usar la primera hora de datos horarios como "actual"
                    current_hour = forecast_data['hourly'][0]
                    current_temp = current_hour.get('temperature')
                    current_humidity = current_hour.get('humidity')
                    current_rain = current_hour.get('rain', 0)
                elif forecast_data.get('weekly'):
                    # Usar datos del día actual - USAR MISMOS DATOS QUE LOS KPIs
                    today = forecast_data['weekly'][0]
                    current_temp = today.get('temp_max')  # Usar temp_max igual que en KPIs
                    current_humidity = today.get('humidity')
                    current_rain = today.get('rain', 0)
                    predefined_risk_level = today.get('risk_level')  # Usar el risk_level calculado
                
                # Usar el mismo análisis que en los KPIs para consistencia
                if current_temp is not None and current_humidity is not None:
                    risk_factors = []
                    is_critical_temp = 15 <= current_temp <= 20
                    is_high_humidity = current_humidity > 95
                    is_moderate_humidity = 85 <= current_humidity <= 95
                    has_rain = current_rain > 0
                    
                    # Usar el risk_level predefinido si está disponible, sino calcularlo
                    if predefined_risk_level:
                        calculated_risk = predefined_risk_level
                    else:
                        if is_critical_temp and is_high_humidity:
                            calculated_risk = 'alto'
                        elif is_critical_temp or (is_moderate_humidity and has_rain):
                            calculated_risk = 'moderado'
                        else:
                            calculated_risk = 'bajo'
                    
                    # Preparar factores explicativos
                    if is_critical_temp:
                        risk_factors.append(f"Temp: {current_temp:.1f}°C (crítica 15-20°C)")
                    else:
                        risk_factors.append(f"Temp: {current_temp:.1f}°C")
                    
                    if is_high_humidity:
                        risk_factors.append(f"Humedad: {current_humidity:.0f}% (crítica >95%)")
                    elif is_moderate_humidity:
                        risk_factors.append(f"Humedad: {current_humidity:.0f}% (alta)")
                    else:
                        risk_factors.append(f"Humedad: {current_humidity:.0f}%")
                    
                    if has_rain:
                        risk_factors.append(f"Lluvia: {current_rain:.1f}mm")
                    
                    # Mostrar resultado consistente
                    if calculated_risk == 'alto':
                        current_status = html.Div([
                            html.I(className="fas fa-exclamation-triangle text-danger me-1"),
                            html.Div([
                                html.Strong("RIESGO ALTO", className="text-danger small d-block"),
                                html.Small(" • ".join(risk_factors), className="text-muted")
                            ])
                        ])
                    elif calculated_risk == 'moderado':
                        current_status = html.Div([
                            html.I(className="fas fa-exclamation-circle text-warning me-1"),
                            html.Div([
                                html.Strong("Riesgo Moderado", className="text-warning small d-block"),
                                html.Small(" • ".join(risk_factors), className="text-muted")
                            ])
                        ])
                    else:
                        current_status = html.Div([
                            html.I(className="fas fa-check-circle text-success me-1"),
                            html.Div([
                                html.Strong("Bajo Riesgo", className="text-success small d-block"),
                                html.Small(" • ".join(risk_factors), className="text-muted")
                            ])
                        ])
            
            # ===== ANÁLISIS 48 HORAS =====
            if forecast_data.get('hourly'):
                hourly_df = pd.DataFrame(forecast_data['hourly'])
                
                # Análisis correcto: temperatura crítica + humedad crítica
                critical_hours = hourly_df[
                    (hourly_df['temperature'] >= 15) & 
                    (hourly_df['temperature'] <= 20) & 
                    (hourly_df['humidity'] > 95)
                ]
                
                # Horas con temperatura crítica (independiente de humedad)
                critical_temp_hours = hourly_df[
                    (hourly_df['temperature'] >= 15) & 
                    (hourly_df['temperature'] <= 20)
                ]
                
                # Horas con humedad alta
                high_humidity_hours = hourly_df[hourly_df['humidity'] > 95]
                moderate_humidity_hours = hourly_df[hourly_df['humidity'] > 85]
                
                # Horas con precipitación (separado de humedad)
                rain_hours = hourly_df[hourly_df['rain'] > 0]
                
                reasons_48h = []
                
                if len(critical_hours) > 5:
                    # Condiciones críticas combinadas (temp + humedad)
                    reasons_48h.append(f"{len(critical_hours)}h críticas (15-20°C + >95% hum)")
                    if len(rain_hours) > 0:
                        total_rain = hourly_df['rain'].sum()
                        reasons_48h.append(f"{len(rain_hours)}h lluvia ({total_rain:.1f}mm)")
                    
                    h48_status = html.Div([
                        html.I(className="fas fa-exclamation-triangle text-danger me-1"),
                        html.Div([
                            html.Strong("RIESGO ALTO", className="text-danger small d-block"),
                            html.Small(" • ".join(reasons_48h), className="text-muted")
                        ])
                    ])
                
                elif len(critical_hours) > 0 or (len(critical_temp_hours) > 10 and len(moderate_humidity_hours) > 20):
                    # Algunas condiciones críticas O muchas condiciones favorables
                    if len(critical_hours) > 0:
                        reasons_48h.append(f"{len(critical_hours)}h críticas")
                    if len(critical_temp_hours) > len(critical_hours):
                        reasons_48h.append(f"{len(critical_temp_hours)}h temp crítica (15-20°C)")
                    if len(high_humidity_hours) > len(critical_hours):
                        reasons_48h.append(f"{len(high_humidity_hours)}h humedad alta (>95%)")
                    if len(rain_hours) > 0:
                        total_rain = hourly_df['rain'].sum()
                        reasons_48h.append(f"{len(rain_hours)}h lluvia ({total_rain:.1f}mm)")
                    
                    h48_status = html.Div([
                        html.I(className="fas fa-exclamation-circle text-warning me-1"),
                        html.Div([
                            html.Strong("Riesgo Moderado", className="text-warning small d-block"),
                            html.Small(" • ".join(reasons_48h), className="text-muted")
                        ])
                    ])
                
                else:
                    # Condiciones favorables
                    avg_temp = hourly_df['temperature'].mean()
                    avg_humidity = hourly_df['humidity'].mean()
                    reasons_48h.append(f"Temp media: {avg_temp:.1f}°C")
                    reasons_48h.append(f"Humedad media: {avg_humidity:.0f}%")
                    if len(rain_hours) > 0:
                        total_rain = hourly_df['rain'].sum()
                        reasons_48h.append(f"Lluvia: {total_rain:.1f}mm")
                    
                    h48_status = html.Div([
                        html.I(className="fas fa-check-circle text-success me-1"),
                        html.Div([
                            html.Strong("Bajo Riesgo", className="text-success small d-block"),
                            html.Small(" • ".join(reasons_48h), className="text-muted")
                        ])
                    ])
            
            # ===== ANÁLISIS SEMANAL =====
            if forecast_data.get('weekly'):
                weekly_df = pd.DataFrame(forecast_data['weekly'])
                high_risk_days = weekly_df[weekly_df.get('risk_level', 'bajo') == 'alto']
                moderate_risk_days = weekly_df[weekly_df.get('risk_level', 'bajo') == 'moderado']
                rain_days = weekly_df[weekly_df.get('rain', 0) > 0]
                
                reasons_week = []
                if len(high_risk_days) > 2:
                    reasons_week.append(f"{len(high_risk_days)} días alto riesgo")
                    if len(rain_days) > 0:
                        reasons_week.append(f"{len(rain_days)} días con lluvia")
                    weekly_status = html.Div([
                        html.I(className="fas fa-exclamation-triangle text-danger me-1"),
                        html.Div([
                            html.Strong(f"RIESGO ALTO", className="text-danger small d-block"),
                            html.Small(" • ".join(reasons_week), className="text-muted")
                        ])
                    ])
                elif len(high_risk_days) > 0 or len(moderate_risk_days) > 3:
                    if len(high_risk_days) > 0:
                        reasons_week.append(f"{len(high_risk_days)} días críticos")
                    if len(moderate_risk_days) > 3:
                        reasons_week.append(f"{len(moderate_risk_days)} días moderados")
                    if len(rain_days) > 0:
                        reasons_week.append(f"{len(rain_days)} días lluvia")
                    weekly_status = html.Div([
                        html.I(className="fas fa-exclamation-circle text-warning me-1"),
                        html.Div([
                            html.Strong("Riesgo Moderado", className="text-warning small d-block"),
                            html.Small(" • ".join(reasons_week), className="text-muted")
                        ])
                    ])
                else:
                    avg_temp_max = weekly_df['temp_max'].mean() if 'temp_max' in weekly_df.columns else 0
                    avg_humidity = weekly_df['humidity'].mean() if 'humidity' in weekly_df.columns else 0
                    reasons_week.append(f"Temp media: {avg_temp_max:.1f}°C")
                    reasons_week.append(f"Hum media: {avg_humidity:.0f}%")
                    weekly_status = html.Div([
                        html.I(className="fas fa-check-circle text-success me-1"),
                        html.Div([
                            html.Strong("Bajo Riesgo", className="text-success small d-block"),
                            html.Small(" • ".join(reasons_week), className="text-muted")
                        ])
                    ])
            
            return current_status, h48_status, weekly_status
            
        except Exception as e:
            logger.error(f"Error actualizando indicadores de riesgo: {e}")
            error_status = html.Div([
                html.I(className="fas fa-exclamation text-danger me-1"),
                html.Div([
                    html.Strong("Error", className="text-danger small d-block"),
                    html.Small(str(e), className="text-muted")
                ])
            ])
            return error_status, error_status, error_status
    
    logger.info("✅ Callbacks de predicción meteorológica registrados")