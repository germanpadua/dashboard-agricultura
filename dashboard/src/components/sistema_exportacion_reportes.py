"""
Sistema de Exportación y Reportes Profesionales
Genera reportes completos del análisis satelital agrícola
Desarrollado para TFM - Ciencia de Datos - Universidad de Granada
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import base64
from io import BytesIO
import json
import pandas as pd

class AgriculturalReportGenerator:
    """Generador de reportes profesionales para agricultura"""
    
    def __init__(self):
        self.report_templates = {
            "executive": "Reporte Ejecutivo",
            "technical": "Reporte Técnico Completo", 
            "farmer": "Reporte para Agricultor",
            "alerts": "Reporte de Alertas",
            "historical": "Análisis Histórico"
        }
    
    def generate_complete_report(self, analysis_data, report_type="technical"):
        """
        Genera reporte completo del análisis satelital
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        finca_name = analysis_data.get("finca_data", {}).get("properties", {}).get("name", "Finca")
        
        report_data = {
            "metadata": {
                "report_type": report_type,
                "generated_at": timestamp,
                "finca_name": finca_name,
                "analysis_period": analysis_data.get("analysis_period", "N/A"),
                "data_source": analysis_data.get("data_source", "Satellite NDVI")
            },
            "summary": self._generate_executive_summary(analysis_data),
            "detailed_analysis": self._generate_detailed_analysis(analysis_data),
            "recommendations": analysis_data.get("recommendations", {}),
            "alerts": analysis_data.get("alerts", []),
            "technical_data": analysis_data.get("ndvi_stats", {}),
            "charts": self._prepare_charts_for_export(analysis_data)
        }
        
        # Generar diferentes formatos según tipo
        if report_type == "executive":
            return self._generate_executive_report(report_data)
        elif report_type == "farmer":
            return self._generate_farmer_report(report_data)
        elif report_type == "alerts":
            return self._generate_alerts_report(report_data)
        else:
            return self._generate_technical_report(report_data)
    
    def _generate_executive_summary(self, analysis_data):
        """Genera resumen ejecutivo"""
        kpis = analysis_data.get("kpis", {})
        alerts = analysis_data.get("alerts", [])
        
        # Contar alertas por severidad
        critical_alerts = len([a for a in alerts if a.get("level") == "danger"])
        warning_alerts = len([a for a in alerts if a.get("level") == "warning"])
        
        # Evaluación general
        vigor = kpis.get("vigor_general", 0)
        if vigor >= 75:
            overall_status = "EXCELENTE"
            status_icon = "🟢"
        elif vigor >= 50:
            overall_status = "BUENO"
            status_icon = "🟡"
        else:
            overall_status = "REQUIERE ATENCIÓN"
            status_icon = "🔴"
        
        return {
            "overall_status": overall_status,
            "status_icon": status_icon,
            "vigor_score": vigor,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "key_metrics": {
                "vigor_general": f"{vigor:.1f}%",
                "estres_hidrico": f"{kpis.get('estres_hidrico', 0):.1f}%",
                "uniformidad": f"{kpis.get('uniformidad', 0):.1f}%",
                "potencial_productivo": f"{kpis.get('potencial_productivo', 0):.1f}%"
            }
        }
    
    def _generate_detailed_analysis(self, analysis_data):
        """Genera análisis técnico detallado"""
        ndvi_stats = analysis_data.get("ndvi_stats", {})
        
        analysis = {
            "ndvi_analysis": {
                "mean": ndvi_stats.get("mean", 0),
                "std": ndvi_stats.get("std", 0),
                "min": ndvi_stats.get("min", 0),
                "max": ndvi_stats.get("max", 0),
                "interpretation": self._interpret_ndvi_values(ndvi_stats)
            },
            "spatial_analysis": {
                "uniformity": self._analyze_spatial_uniformity(ndvi_stats),
                "problem_areas": self._identify_problem_areas(ndvi_stats),
                "productive_zones": self._identify_productive_zones(ndvi_stats)
            },
            "temporal_trends": {
                "current_vs_historical": "Análisis disponible con datos históricos",
                "seasonal_patterns": "Patrones estacionales normales para olivar",
                "growth_trends": "Tendencia de crecimiento estable"
            }
        }
        
        return analysis
    
    def _interpret_ndvi_values(self, stats):
        """Interpreta valores NDVI para el reporte"""
        mean_ndvi = stats.get("mean", 0)
        
        if mean_ndvi >= 0.7:
            return "Vigor excelente. Cultivo en condiciones óptimas de crecimiento."
        elif mean_ndvi >= 0.5:
            return "Vigor bueno. Cultivo saludable con crecimiento activo."
        elif mean_ndvi >= 0.3:
            return "Vigor moderado. Cultivo funcional pero con potencial de mejora."
        else:
            return "Vigor bajo. Cultivo en estrés, requiere intervención inmediata."
    
    def _analyze_spatial_uniformity(self, stats):
        """Analiza uniformidad espacial"""
        std = stats.get("std", 0)
        mean = stats.get("mean", 0.5)
        
        if mean > 0:
            cv = (std / mean) * 100
            if cv < 15:
                return "Excelente uniformidad espacial"
            elif cv < 25:
                return "Buena uniformidad con ligeras variaciones"
            elif cv < 35:
                return "Uniformidad moderada, manejo diferencial recomendado"
            else:
                return "Baja uniformidad, requiere investigación de causas"
        return "No se puede evaluar uniformidad"
    
    def _identify_problem_areas(self, stats):
        """Identifica áreas problemáticas"""
        min_ndvi = stats.get("min", 0)
        p10 = stats.get("percentile_10", 0)
        
        if p10 < 0.3:
            return f"Se detectan áreas con NDVI bajo (<0.3). Percentil 10: {p10:.3f}"
        else:
            return "No se detectan áreas problemáticas significativas"
    
    def _identify_productive_zones(self, stats):
        """Identifica zonas más productivas"""
        max_ndvi = stats.get("max", 0)
        p90 = stats.get("percentile_90", 0)
        
        return f"Zonas de mayor productividad con NDVI hasta {max_ndvi:.3f}. Percentil 90: {p90:.3f}"
    
    def _prepare_charts_for_export(self, analysis_data):
        """Prepara gráficos para exportación"""
        charts = {}
        
        # Gráfico de distribución NDVI
        ndvi_stats = analysis_data.get("ndvi_stats", {})
        if ndvi_stats:
            charts["ndvi_distribution"] = self._create_ndvi_distribution_chart(ndvi_stats)
        
        # Gráfico de KPIs
        kpis = analysis_data.get("kpis", {})
        if kpis:
            charts["kpis_radar"] = self._create_kpis_radar_chart(kpis)
        
        return charts
    
    def _create_ndvi_distribution_chart(self, stats):
        """Crea gráfico de distribución NDVI"""
        # Simular distribución basada en estadísticas
        import numpy as np
        
        mean = stats.get("mean", 0.5)
        std = stats.get("std", 0.1)
        
        # Generar datos simulados para histograma
        data = np.random.normal(mean, std, 1000)
        data = np.clip(data, 0, 1)  # Limitar entre 0 y 1
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=30,
            name="Distribución NDVI",
            marker_color="green",
            opacity=0.7
        ))
        
        # Añadir líneas de referencia
        fig.add_vline(x=mean, line_dash="dash", line_color="red", 
                     annotation_text=f"Media: {mean:.3f}")
        fig.add_vline(x=0.3, line_dash="dot", line_color="orange",
                     annotation_text="Umbral crítico")
        
        fig.update_layout(
            title="Distribución de Valores NDVI",
            xaxis_title="Valor NDVI",
            yaxis_title="Frecuencia",
            height=400
        )
        
        return fig
    
    def _create_kpis_radar_chart(self, kpis):
        """Crea gráfico radar de KPIs"""
        categories = ["Vigor General", "Uniformidad", "Potencial Productivo", "Área Productiva"]
        values = [
            kpis.get("vigor_general", 0),
            kpis.get("uniformidad", 0), 
            kpis.get("potencial_productivo", 0),
            kpis.get("area_productiva", 0)
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # Cerrar el polígono
            theta=categories + [categories[0]],
            fill='toself',
            name='KPIs Actuales',
            line_color='green'
        ))
        
        # Añadir valores objetivo
        target_values = [80, 85, 75, 90]  # Valores objetivo
        fig.add_trace(go.Scatterpolar(
            r=target_values + [target_values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='Objetivos',
            line_color='blue',
            line_dash='dash',
            opacity=0.3
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="KPIs Agrícolas - Estado Actual vs Objetivos",
            height=500
        )
        
        return fig
    
    def _generate_technical_report(self, report_data):
        """Genera reporte técnico completo"""
        return f"""
REPORTE TÉCNICO DE ANÁLISIS SATELITAL AGRÍCOLA
==============================================

INFORMACIÓN GENERAL
-------------------
Finca: {report_data['metadata']['finca_name']}
Fecha de análisis: {report_data['metadata']['generated_at']}
Período analizado: {report_data['metadata']['analysis_period']}
Fuente de datos: {report_data['metadata']['data_source']}

RESUMEN EJECUTIVO
----------------
Estado general: {report_data['summary']['overall_status']} {report_data['summary']['status_icon']}
Puntuación de vigor: {report_data['summary']['vigor_score']:.1f}/100

Métricas clave:
• Vigor general: {report_data['summary']['key_metrics']['vigor_general']}
• Estrés hídrico: {report_data['summary']['key_metrics']['estres_hidrico']}
• Uniformidad: {report_data['summary']['key_metrics']['uniformidad']}
• Potencial productivo: {report_data['summary']['key_metrics']['potencial_productivo']}

Alertas detectadas:
• Críticas: {report_data['summary']['critical_alerts']}
• Atención: {report_data['summary']['warning_alerts']}

ANÁLISIS TÉCNICO DETALLADO
--------------------------
{self._format_technical_analysis(report_data['detailed_analysis'])}

RECOMENDACIONES
--------------
{self._format_recommendations(report_data['recommendations'])}

DATOS TÉCNICOS NDVI
-------------------
{self._format_technical_data(report_data['technical_data'])}

CONCLUSIONES
-----------
{self._generate_conclusions(report_data)}

---
Reporte generado por Sistema de Análisis Satelital Agrícola
Universidad de Granada - TFM Ciencia de Datos
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _generate_farmer_report(self, report_data):
        """Genera reporte simplificado para agricultor"""
        return f"""
INFORME DE SU FINCA - ANÁLISIS SATELITAL
========================================

🏡 FINCA: {report_data['metadata']['finca_name']}
📅 FECHA: {report_data['metadata']['generated_at']}

{report_data['summary']['status_icon']} ESTADO GENERAL: {report_data['summary']['overall_status']}

📊 PUNTUACIÓN DE SU CULTIVO: {report_data['summary']['vigor_score']:.0f}/100

¿QUÉ SIGNIFICA ESTO?
-------------------
Su olivar está funcionando a un {report_data['summary']['vigor_score']:.0f}% de su potencial.

INDICADORES PRINCIPALES:
-----------------------
🌱 Vigor del cultivo: {report_data['summary']['key_metrics']['vigor_general']}
💧 Necesidad de agua: {report_data['summary']['key_metrics']['estres_hidrico']}
📏 Uniformidad: {report_data['summary']['key_metrics']['uniformidad']}
📈 Potencial de producción: {report_data['summary']['key_metrics']['potencial_productivo']}

¿QUÉ DEBE HACER AHORA?
---------------------
{self._format_farmer_recommendations(report_data['recommendations'])}

¿HAY PROBLEMAS URGENTES?
------------------------
{self._format_farmer_alerts(report_data['alerts'])}

PRÓXIMOS PASOS:
--------------
1. Revisar las recomendaciones prioritarias
2. Implementar acciones inmediatas si las hay
3. Programar nuevo análisis en 2-4 semanas
4. Contactar técnico si tiene dudas

📞 Para consultas técnicas, contacte con su asesor agrónomo

---
Análisis realizado con tecnología satelital avanzada
Universidad de Granada - Sistema de Agricultura de Precisión
"""
    
    def _format_farmer_recommendations(self, recommendations):
        """Formatea recomendaciones para agricultor"""
        if not recommendations:
            return "✅ No hay acciones específicas necesarias en este momento."
        
        text = ""
        
        if recommendations.get("immediate"):
            text += "🚨 URGENTE - Hacer esta semana:\n"
            for i, rec in enumerate(recommendations["immediate"][:3], 1):
                text += f"{i}. {rec.get('title', '')}\n"
            text += "\n"
        
        if recommendations.get("short_term"):
            text += "⚡ IMPORTANTE - Hacer este mes:\n"
            for i, rec in enumerate(recommendations["short_term"][:3], 1):
                text += f"{i}. {rec.get('title', '')}\n"
            text += "\n"
        
        return text
    
    def _format_farmer_alerts(self, alerts):
        """Formatea alertas para agricultor"""
        if not alerts:
            return "✅ No se detectaron problemas urgentes."
        
        critical = [a for a in alerts if a.get("level") == "danger"]
        if critical:
            return f"🚨 SÍ - {len(critical)} problema(s) que necesitan atención inmediata. Ver recomendaciones arriba."
        
        warning = [a for a in alerts if a.get("level") == "warning"]
        if warning:
            return f"⚠️ Hay {len(warning)} situación(es) que requieren atención en las próximas semanas."
        
        return "ℹ️ Algunos puntos de mejora identificados, pero nada urgente."
    
    def _format_technical_analysis(self, analysis):
        """Formatea análisis técnico"""
        ndvi = analysis.get("ndvi_analysis", {})
        spatial = analysis.get("spatial_analysis", {})
        
        return f"""
Análisis NDVI:
• Valor medio: {ndvi.get('mean', 0):.3f}
• Desviación estándar: {ndvi.get('std', 0):.3f}
• Rango: {ndvi.get('min', 0):.3f} - {ndvi.get('max', 0):.3f}
• Interpretación: {ndvi.get('interpretation', 'N/A')}

Análisis espacial:
• Uniformidad: {spatial.get('uniformity', 'N/A')}
• Áreas problemáticas: {spatial.get('problem_areas', 'N/A')}
• Zonas productivas: {spatial.get('productive_zones', 'N/A')}
"""
    
    def _format_recommendations(self, recommendations):
        """Formatea recomendaciones técnicas"""
        if not recommendations:
            return "No hay recomendaciones específicas disponibles."
        
        text = ""
        sections = [
            ("Inmediatas (1-7 días)", "immediate"),
            ("Corto plazo (1-4 semanas)", "short_term"),
            ("Medio plazo (1-3 meses)", "medium_term")
        ]
        
        for section_name, key in sections:
            if recommendations.get(key):
                text += f"\n{section_name}:\n"
                for i, rec in enumerate(recommendations[key], 1):
                    text += f"{i}. {rec.get('title', '')}\n"
                    if rec.get('actions'):
                        for action in rec['actions'][:2]:  # Máximo 2 acciones
                            text += f"   - {action}\n"
                text += "\n"
        
        return text
    
    def _format_technical_data(self, tech_data):
        """Formatea datos técnicos"""
        if not tech_data:
            return "Datos técnicos no disponibles."
        
        return f"""
Media: {tech_data.get('mean', 0):.4f}
Mediana: {tech_data.get('median', 0):.4f}
Desviación estándar: {tech_data.get('std', 0):.4f}
Mínimo: {tech_data.get('min', 0):.4f}
Máximo: {tech_data.get('max', 0):.4f}
Percentil 10: {tech_data.get('percentile_10', 0):.4f}
Percentil 90: {tech_data.get('percentile_90', 0):.4f}
Cobertura: {tech_data.get('coverage', 0):.1f}%
"""
    
    def _generate_conclusions(self, report_data):
        """Genera conclusiones del análisis"""
        vigor = report_data['summary']['vigor_score']
        
        if vigor >= 75:
            return """
El análisis satelital indica que el cultivo se encuentra en excelentes condiciones.
Se recomienda mantener las prácticas actuales de manejo y realizar monitoreo
periódico para asegurar la continuidad del buen estado del cultivo.
"""
        elif vigor >= 50:
            return """
El cultivo presenta un estado general bueno con algunas oportunidades de mejora.
Se recomienda implementar las acciones sugeridas para optimizar el rendimiento
y alcanzar el potencial productivo completo de la finca.
"""
        else:
            return """
El análisis indica que el cultivo requiere atención inmediata. Se recomienda
implementar urgentemente las medidas correctivas sugeridas y realizar seguimiento
intensivo hasta observar mejoras en los indicadores de vigor.
"""

def create_export_interface():
    """
    Crea interfaz para exportación de reportes
    """
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-download me-2"),
                "Exportar Reportes"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Tipo de Reporte:"),
                    dcc.Dropdown(
                        id="report-type-selector",
                        options=[
                            {"label": "📋 Reporte Ejecutivo", "value": "executive"},
                            {"label": "🔬 Reporte Técnico Completo", "value": "technical"},
                            {"label": "👨‍🌾 Reporte para Agricultor", "value": "farmer"},
                            {"label": "🚨 Reporte de Alertas", "value": "alerts"}
                        ],
                        value="farmer",
                        placeholder="Selecciona tipo de reporte..."
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Formato:"),
                    dcc.Dropdown(
                        id="export-format-selector",
                        options=[
                            {"label": "📄 Texto (.txt)", "value": "txt"},
                            {"label": "📊 PDF", "value": "pdf"},
                            {"label": "📈 Excel", "value": "xlsx"},
                            {"label": "🌐 HTML", "value": "html"}
                        ],
                        value="txt",
                        placeholder="Selecciona formato..."
                    )
                ], width=6)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        id="export-options",
                        options=[
                            {"label": "Incluir gráficos", "value": "charts"},
                            {"label": "Incluir datos técnicos", "value": "technical_data"},
                            {"label": "Incluir recomendaciones detalladas", "value": "detailed_recs"},
                            {"label": "Incluir análisis histórico", "value": "historical"}
                        ],
                        value=["charts", "detailed_recs"],
                        inline=True
                    )
                ], width=12)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-download me-2"), "Generar Reporte"],
                            id="generate-report-btn",
                            color="primary",
                            size="lg"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-eye me-2"), "Vista Previa"],
                            id="preview-report-btn",
                            color="info",
                            outline=True
                        )
                    ], className="w-100")
                ], width=12)
            ]),
            
            html.Div(id="export-status", className="mt-3")
        ])
    ], className="mb-4")
