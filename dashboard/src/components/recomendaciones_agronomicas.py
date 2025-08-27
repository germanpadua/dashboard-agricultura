"""
Sistema de Recomendaciones Agronómicas Inteligentes
Genera recomendaciones específicas basadas en análisis satelital NDVI
Desarrollado para TFM - Ciencia de Datos - Universidad de Granada
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime
import numpy as np

class AgronomicRecommendationEngine:
    """Motor de recomendaciones agronómicas para olivar"""
    
    def __init__(self):
        # Base de conocimiento agronómico para olivar
        self.knowledge_base = {
            "fertilization": {
                "nitrogen_deficiency": {
                    "indicators": ["ndvi_low", "vigor_poor", "chlorosis"],
                    "recommendations": [
                        "Aplicar fertilizante nitrogenado (100-150 kg N/ha)",
                        "Realizar análisis foliar para confirmar deficiencia",
                        "Considerar fertirrigación para mejor absorción",
                        "Monitorear respuesta en 3-4 semanas"
                    ]
                },
                "balanced_nutrition": {
                    "indicators": ["ndvi_optimal", "vigor_good"],
                    "recommendations": [
                        "Mantener programa de fertilización actual", 
                        "Aplicar fertilización de mantenimiento NPK",
                        "Realizar análisis de suelo anual",
                        "Ajustar según fenología del cultivo"
                    ]
                }
            },
            "irrigation": {
                "water_stress": {
                    "indicators": ["ndvi_declining", "uniformity_poor", "summer_stress"],
                    "recommendations": [
                        "Incrementar frecuencia de riego en 20-30%",
                        "Revisar uniformidad del sistema de riego",
                        "Considerar riego deficitario controlado",
                        "Instalar sensores de humedad del suelo"
                    ]
                },
                "optimal_water": {
                    "indicators": ["ndvi_stable", "vigor_good"],
                    "recommendations": [
                        "Mantener programa de riego actual",
                        "Ajustar según evapotranspiración del cultivo",
                        "Monitorear eficiencia del sistema",
                        "Considerar riego diferencial por zonas"
                    ]
                }
            },
            "pest_disease": {
                "potential_issues": {
                    "indicators": ["ndvi_patchy", "vigor_declining", "high_variability"],
                    "recommendations": [
                        "Inspección visual para detectar plagas",
                        "Monitorear presencia de repilo en hojas",
                        "Evaluar necesidad de tratamiento fitosanitario",
                        "Realizar muestreo de insectos plaga"
                    ]
                }
            },
            "soil_management": {
                "compaction": {
                    "indicators": ["poor_uniformity", "patchy_growth"],
                    "recommendations": [
                        "Evaluar compactación del suelo",
                        "Considerar laboreo superficial",
                        "Implementar cubierta vegetal",
                        "Reducir tráfico de maquinaria"
                    ]
                }
            }
        }
    
    def generate_recommendations(self, ndvi_stats, kpis, alerts, finca_data=None):
        """
        Genera recomendaciones personalizadas basadas en análisis integral
        """
        recommendations = {
            "immediate": [],  # Acciones inmediatas (1-7 días)
            "short_term": [], # Acciones corto plazo (1-4 semanas)
            "medium_term": [],# Acciones medio plazo (1-3 meses)
            "long_term": []   # Acciones largo plazo (>3 meses)
        }
        
        # Análisis de estado del cultivo
        crop_status = self._analyze_crop_status(ndvi_stats, kpis)
        
        # Generar recomendaciones por categoría
        self._add_nutrition_recommendations(crop_status, recommendations)
        self._add_irrigation_recommendations(crop_status, recommendations)
        self._add_health_recommendations(crop_status, recommendations)
        self._add_management_recommendations(crop_status, recommendations)
        
        # Añadir recomendaciones basadas en alertas
        self._add_alert_based_recommendations(alerts, recommendations)
        
        # Añadir recomendaciones estacionales
        self._add_seasonal_recommendations(recommendations)
        
        return recommendations
    
    def _analyze_crop_status(self, ndvi_stats, kpis):
        """Analiza el estado general del cultivo"""
        ndvi_mean = ndvi_stats.get("mean", 0.5)
        vigor = kpis.get("vigor_general", 50)
        uniformity = kpis.get("uniformidad", 50)
        stress = kpis.get("estres_hidrico", 50)
        
        status = {
            "vigor_level": "low" if vigor < 50 else "medium" if vigor < 75 else "high",
            "water_status": "stressed" if stress > 60 else "moderate" if stress > 30 else "optimal",
            "uniformity_level": "poor" if uniformity < 50 else "good" if uniformity < 80 else "excellent",
            "ndvi_category": "low" if ndvi_mean < 0.35 else "medium" if ndvi_mean < 0.6 else "high",
            "overall_health": self._calculate_overall_health(vigor, stress, uniformity)
        }
        
        return status
    
    def _calculate_overall_health(self, vigor, stress, uniformity):
        """Calcula salud general del cultivo"""
        # Peso ponderado de factores
        health_score = (vigor * 0.4) + ((100 - stress) * 0.3) + (uniformity * 0.3)
        
        if health_score >= 80:
            return "excellent"
        elif health_score >= 65:
            return "good"
        elif health_score >= 50:
            return "fair"
        else:
            return "poor"
    
    def _add_nutrition_recommendations(self, status, recommendations):
        """Añade recomendaciones nutricionales"""
        if status["vigor_level"] == "low":
            recommendations["immediate"].append({
                "category": "Nutrición",
                "title": "🌱 Evaluación Nutricional Urgente",
                "description": "El bajo vigor sugiere posibles deficiencias nutricionales",
                "actions": [
                    "Realizar análisis foliar inmediato",
                    "Inspeccionar síntomas visuales de deficiencias",
                    "Preparar programa de fertilización correctiva"
                ],
                "priority": "high"
            })
            
            recommendations["short_term"].append({
                "category": "Nutrición", 
                "title": "🧪 Fertilización Correctiva",
                "description": "Implementar fertilización específica según resultados",
                "actions": [
                    "Aplicar fertilizante nitrogenado foliar (si confirmado)",
                    "Considerar quelatos de micronutrientes",
                    "Implementar fertirrigación balanceada",
                    "Monitorear respuesta del cultivo"
                ],
                "priority": "high"
            })
        
        elif status["vigor_level"] == "medium":
            recommendations["short_term"].append({
                "category": "Nutrición",
                "title": "⚖️ Optimización Nutricional",
                "description": "Ajustar programa nutricional para maximizar vigor",
                "actions": [
                    "Revisar programa de fertilización actual",
                    "Considerar fertilizantes de liberación lenta",
                    "Evaluar disponibilidad de micronutrientes",
                    "Ajustar según análisis de suelo"
                ],
                "priority": "medium"
            })
    
    def _add_irrigation_recommendations(self, status, recommendations):
        """Añade recomendaciones de riego"""
        if status["water_status"] == "stressed":
            recommendations["immediate"].append({
                "category": "Riego",
                "title": "💧 Ajuste Inmediato de Riego",
                "description": "Estrés hídrico detectado requiere acción inmediata",
                "actions": [
                    "Incrementar frecuencia de riego en 25%",
                    "Verificar funcionamiento de todos los emisores",
                    "Revisar presión del sistema",
                    "Evaluar uniformidad del riego"
                ],
                "priority": "high"
            })
            
            recommendations["medium_term"].append({
                "category": "Riego",
                "title": "🔧 Optimización del Sistema",
                "description": "Mejorar eficiencia del sistema de riego",
                "actions": [
                    "Instalar sensores de humedad del suelo",
                    "Implementar programación automática",
                    "Considerar riego diferencial por zonas",
                    "Evaluar renovación de equipos antiguos"
                ],
                "priority": "medium"
            })
        
        elif status["water_status"] == "optimal":
            recommendations["long_term"].append({
                "category": "Riego",
                "title": "📊 Monitoreo Continuo",
                "description": "Mantener condiciones óptimas de riego",
                "actions": [
                    "Implementar monitoreo meteorológico",
                    "Ajustar según evapotranspiración",
                    "Mantener calibración de equipos",
                    "Registro detallado de consumos"
                ],
                "priority": "low"
            })
    
    def _add_health_recommendations(self, status, recommendations):
        """Añade recomendaciones de sanidad del cultivo"""
        if status["uniformity_level"] == "poor":
            recommendations["immediate"].append({
                "category": "Sanidad",
                "title": "🔍 Inspección Sanitaria",
                "description": "Baja uniformidad puede indicar problemas sanitarios",
                "actions": [
                    "Inspección visual detallada del cultivo",
                    "Buscar síntomas de repilo y otras enfermedades",
                    "Evaluar presencia de plagas",
                    "Tomar muestras para análisis si es necesario"
                ],
                "priority": "high"
            })
        
        # Recomendaciones preventivas estacionales
        month = datetime.now().month
        if month in [3, 4, 5]:  # Primavera
            recommendations["short_term"].append({
                "category": "Sanidad",
                "title": "🌸 Programa Sanitario Primaveral",
                "description": "Prevención de enfermedades en período crítico",
                "actions": [
                    "Monitorear condiciones para repilo",
                    "Evaluar necesidad de tratamiento preventivo",
                    "Inspeccionar brotes nuevos",
                    "Mantener ventilación del cultivo"
                ],
                "priority": "medium"
            })
    
    def _add_management_recommendations(self, status, recommendations):
        """Añade recomendaciones de manejo general"""
        if status["overall_health"] == "poor":
            recommendations["medium_term"].append({
                "category": "Manejo",
                "title": "🔄 Plan de Recuperación Integral",
                "description": "Estado general deficiente requiere plan integral",
                "actions": [
                    "Desarrollar plan de mejora específico",
                    "Considerar asesoramiento técnico especializado",
                    "Evaluar prácticas culturales actuales",
                    "Implementar monitoreo intensivo"
                ],
                "priority": "high"
            })
        
        # Recomendaciones de mejora continua
        recommendations["long_term"].append({
            "category": "Manejo",
            "title": "📈 Mejora Continua",
            "description": "Estrategias para optimización a largo plazo",
            "actions": [
                "Implementar agricultura de precisión",
                "Desarrollar mapas de variabilidad",
                "Considerar tecnologías emergentes",
                "Mantener registro histórico detallado"
            ],
            "priority": "low"
        })
    
    def _add_alert_based_recommendations(self, alerts, recommendations):
        """Añade recomendaciones específicas basadas en alertas"""
        for alert in alerts:
            if alert.get("level") == "danger":
                recommendations["immediate"].append({
                    "category": "Alerta Crítica",
                    "title": f"🚨 {alert.get('type', 'Problema Crítico')}",
                    "description": alert.get("message", ""),
                    "actions": alert.get("actions", []),
                    "priority": "critical"
                })
    
    def _add_seasonal_recommendations(self, recommendations):
        """Añade recomendaciones estacionales específicas"""
        month = datetime.now().month
        season_recs = {
            1: {"season": "Invierno", "tasks": ["Poda de formación", "Mantenimiento equipos"]},
            2: {"season": "Invierno", "tasks": ["Fertilización base", "Preparación primavera"]},
            3: {"season": "Primavera", "tasks": ["Brotación", "Control preventivo"]},
            4: {"season": "Primavera", "tasks": ["Floración", "Polinización"]},
            5: {"season": "Primavera", "tasks": ["Cuajado", "Fertilización N"]},
            6: {"season": "Verano", "tasks": ["Crecimiento fruto", "Riego intensivo"]},
            7: {"season": "Verano", "tasks": ["Desarrollo aceite", "Control estrés"]},
            8: {"season": "Verano", "tasks": ["Maduración", "Preparación cosecha"]},
            9: {"season": "Otoño", "tasks": ["Cosecha temprana", "Evaluación"]},
            10: {"season": "Otoño", "tasks": ["Cosecha principal", "Post-cosecha"]},
            11: {"season": "Otoño", "tasks": ["Cosecha tardía", "Preparación invierno"]},
            12: {"season": "Invierno", "tasks": ["Descanso vegetativo", "Planificación"]}
        }
        
        current_season = season_recs.get(month, {"season": "Todo el año", "tasks": []})
        
        recommendations["medium_term"].append({
            "category": "Estacional",
            "title": f"📅 Tareas de {current_season['season']}",
            "description": f"Actividades recomendadas para {current_season['season'].lower()}",
            "actions": current_season["tasks"],
            "priority": "medium"
        })

def create_recommendations_dashboard(recommendations):
    """
    Crea dashboard visual de recomendaciones
    """
    if not recommendations or not any(recommendations.values()):
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No hay recomendaciones específicas en este momento."
        ], color="info")
    
    tabs = []
    
    # Tab para acciones inmediatas
    if recommendations.get("immediate"):
        tabs.append(dbc.Tab([
            html.Div([
                _create_recommendation_cards(recommendations["immediate"])
            ], className="mt-3")
        ], label="Inmediatas", tab_id="immediate", tab_style={"backgroundColor": "#dc3545", "color": "white"}))
    
    # Tab para acciones corto plazo
    if recommendations.get("short_term"):
        tabs.append(dbc.Tab([
            html.Div([
                _create_recommendation_cards(recommendations["short_term"])
            ], className="mt-3")
        ], label="Corto Plazo", tab_id="short_term"))
    
    # Tab para acciones medio plazo
    if recommendations.get("medium_term"):
        tabs.append(dbc.Tab([
            html.Div([
                _create_recommendation_cards(recommendations["medium_term"])
            ], className="mt-3")
        ], label="Medio Plazo", tab_id="medium_term"))
    
    # Tab para acciones largo plazo
    if recommendations.get("long_term"):
        tabs.append(dbc.Tab([
            html.Div([
                _create_recommendation_cards(recommendations["long_term"])
            ], className="mt-3")
        ], label="Largo Plazo", tab_id="long_term"))
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-lightbulb me-2"),
                "Recomendaciones Agronómicas Inteligentes"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Tabs(tabs, active_tab="immediate" if recommendations.get("immediate") else "short_term")
        ])
    ], className="mb-4")

def _create_recommendation_cards(rec_list):
    """Crea cards para lista de recomendaciones"""
    cards = []
    
    # Agrupar por categoría
    categories = {}
    for rec in rec_list:
        cat = rec.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rec)
    
    # Crear card por categoría
    for category, recs in categories.items():
        category_cards = []
        
        for rec in recs:
            priority_color = {
                "critical": "danger",
                "high": "warning", 
                "medium": "info",
                "low": "light"
            }.get(rec.get("priority", "medium"), "info")
            
            card = dbc.Card([
                dbc.CardHeader([
                    html.H6(rec.get("title", "Recomendación"), className="mb-0")
                ]),
                dbc.CardBody([
                    html.P(rec.get("description", ""), className="mb-3"),
                    html.H6("🔧 Acciones:", className="mb-2"),
                    html.Ul([
                        html.Li(action) for action in rec.get("actions", [])
                    ], className="mb-0")
                ])
            ], color=priority_color, outline=True, className="mb-3")
            
            category_cards.append(card)
        
        # Crear sección por categoría
        category_section = html.Div([
            html.H5([
                _get_category_icon(category),
                category
            ], className="mb-3 mt-4"),
            html.Div(category_cards)
        ])
        
        cards.append(category_section)
    
    return cards

def _get_category_icon(category):
    """Obtiene icono para cada categoría"""
    icons = {
        "Nutrición": html.I(className="fas fa-seedling me-2 text-success"),
        "Riego": html.I(className="fas fa-tint me-2 text-primary"),
        "Sanidad": html.I(className="fas fa-shield-alt me-2 text-info"),
        "Manejo": html.I(className="fas fa-cogs me-2 text-secondary"),
        "Estacional": html.I(className="fas fa-calendar me-2 text-warning"),
        "Alerta Crítica": html.I(className="fas fa-exclamation-triangle me-2 text-danger")
    }
    return icons.get(category, html.I(className="fas fa-info-circle me-2"))

def generate_recommendations_report(recommendations, finca_data=None):
    """
    Genera reporte de recomendaciones para exportar
    """
    finca_name = finca_data.get("properties", {}).get("name", "Finca") if finca_data else "Finca"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""
REPORTE DE RECOMENDACIONES AGRONÓMICAS
======================================
Finca: {finca_name}
Fecha de análisis: {timestamp}
Sistema: Dashboard Agrícola TFM - Universidad de Granada

"""
    
    sections = [
        ("ACCIONES INMEDIATAS (1-7 días)", "immediate"),
        ("ACCIONES CORTO PLAZO (1-4 semanas)", "short_term"),
        ("ACCIONES MEDIO PLAZO (1-3 meses)", "medium_term"),
        ("ACCIONES LARGO PLAZO (>3 meses)", "long_term")
    ]
    
    for section_title, section_key in sections:
        if recommendations.get(section_key):
            report += f"\n{section_title}\n"
            report += "=" * len(section_title) + "\n\n"
            
            for i, rec in enumerate(recommendations[section_key], 1):
                report += f"{i}. {rec.get('title', 'Recomendación')}\n"
                report += f"   Categoría: {rec.get('category', 'General')}\n"
                report += f"   Prioridad: {rec.get('priority', 'Medium').upper()}\n"
                report += f"   Descripción: {rec.get('description', '')}\n"
                report += "   Acciones:\n"
                for action in rec.get('actions', []):
                    report += f"   - {action}\n"
                report += "\n"
    
    report += """
INSTRUCCIONES DE USO:
====================
1. Priorizar acciones según urgencia y criticidad
2. Documentar implementación de cada recomendación
3. Monitorear resultados y ajustar según sea necesario
4. Repetir análisis satelital en 2-4 semanas
5. Consultar con técnico especialista para casos complejos

AVISO IMPORTANTE:
================
Estas recomendaciones se basan en análisis satelital NDVI y deben
complementarse con inspección de campo y criterio técnico profesional.

Generado por Sistema de Análisis Satelital Agrícola
Universidad de Granada - TFM Ciencia de Datos
"""
    
    return report
