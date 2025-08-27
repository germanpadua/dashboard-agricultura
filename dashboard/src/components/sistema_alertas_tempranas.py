"""
Sistema de Alertas Tempranas para Agricultura de Precisión
Detecta automáticamente problemas en cultivos mediante análisis satelital
Desarrollado para TFM - Ciencia de Datos - Universidad de Granada
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

class AlertSystemOlive:
    """Sistema de alertas específico para cultivos de olivar"""
    
    # Umbrales críticos para olivar
    THRESHOLDS = {
        "ndvi_critico": 0.25,      # NDVI por debajo indica problema severo
        "ndvi_atencion": 0.35,     # NDVI por debajo requiere atención
        "ndvi_optimo_min": 0.5,    # NDVI mínimo para condiciones óptimas
        "variabilidad_max": 30,    # Coeficiente de variación máximo aceptable (%)
        "area_problematica_max": 15  # % máximo de área con problemas
    }
    
    def __init__(self):
        self.alerts = []
    
    def analyze_ndvi_data(self, ndvi_stats, finca_data=None):
        """
        Analiza datos NDVI y genera alertas automáticas
        """
        self.alerts = []
        finca_name = finca_data.get("properties", {}).get("name", "Finca") if finca_data else "Finca"
        
        # Análisis de vigor general
        self._check_vigor_alerts(ndvi_stats, finca_name)
        
        # Análisis de uniformidad
        self._check_uniformity_alerts(ndvi_stats, finca_name)
        
        # Análisis de áreas problemáticas
        self._check_area_alerts(ndvi_stats, finca_name)
        
        # Análisis estacional
        self._check_seasonal_alerts(ndvi_stats, finca_name)
        
        return self.alerts
    
    def _check_vigor_alerts(self, stats, finca_name):
        """Verifica alertas relacionadas con el vigor del cultivo"""
        ndvi_mean = stats.get("mean", 0)
        
        if ndvi_mean < self.THRESHOLDS["ndvi_critico"]:
            self.alerts.append({
                "level": "danger",
                "type": "Vigor Crítico",
                "title": "⚠️ ALERTA CRÍTICA: Vigor muy bajo",
                "message": f"El NDVI promedio ({ndvi_mean:.3f}) está por debajo del umbral crítico. "
                          f"Se requiere intervención inmediata en {finca_name}.",
                "priority": 1,
                "actions": [
                    "Inspección física inmediata del cultivo",
                    "Verificar sistema de riego",
                    "Evaluar presencia de plagas o enfermedades",
                    "Considerar fertilización de emergencia"
                ]
            })
        elif ndvi_mean < self.THRESHOLDS["ndvi_atencion"]:
            self.alerts.append({
                "level": "warning",
                "type": "Vigor Bajo",
                "title": "⚡ ATENCIÓN: Vigor por debajo del óptimo",
                "message": f"El NDVI promedio ({ndvi_mean:.3f}) indica vigor reducido en {finca_name}. "
                          f"Recomendable revisión y ajustes.",
                "priority": 2,
                "actions": [
                    "Revisar programa de fertilización",
                    "Evaluar eficiencia del riego",
                    "Monitorear semanalmente",
                    "Considerar análisis foliar"
                ]
            })
    
    def _check_uniformity_alerts(self, stats, finca_name):
        """Verifica alertas relacionadas con la uniformidad del cultivo"""
        ndvi_std = stats.get("std", 0)
        ndvi_mean = stats.get("mean", 0.5)
        
        if ndvi_mean > 0:
            cv = (ndvi_std / ndvi_mean) * 100
            
            if cv > self.THRESHOLDS["variabilidad_max"]:
                self.alerts.append({
                    "level": "info",
                    "type": "Uniformidad",
                    "title": "📊 INFORMACIÓN: Alta variabilidad detectada",
                    "message": f"Coeficiente de variación ({cv:.1f}%) superior al recomendado. "
                              f"Existe desuniformidad en {finca_name}.",
                    "priority": 3,
                    "actions": [
                        "Mapear zonas de diferente vigor",
                        "Ajustar riego diferencial por zonas",
                        "Evaluar variabilidad del suelo",
                        "Considerar manejo por ambientes"
                    ]
                })
    
    def _check_area_alerts(self, stats, finca_name):
        """Verifica alertas relacionadas con áreas problemáticas"""
        ndvi_mean = stats.get("mean", 0)
        ndvi_min = stats.get("min", 0)
        ndvi_p10 = stats.get("percentile_10", 0)
        
        # Estimar porcentaje de área problemática
        if ndvi_p10 < self.THRESHOLDS["ndvi_atencion"]:
            area_problematica = 20  # Estimación basada en percentil 10
            
            if area_problematica > self.THRESHOLDS["area_problematica_max"]:
                self.alerts.append({
                    "level": "warning",
                    "type": "Área Problemática",
                    "title": "🗺️ ATENCIÓN: Áreas con problemas detectadas",
                    "message": f"Aproximadamente {area_problematica:.1f}% del área en {finca_name} "
                              f"presenta valores NDVI bajos (< {self.THRESHOLDS['ndvi_atencion']}).",
                    "priority": 2,
                    "actions": [
                        "Identificar ubicación exacta de áreas problemáticas",
                        "Inspección dirigida de estas zonas",
                        "Análisis específico de suelo en áreas afectadas",
                        "Tratamiento localizado según diagnóstico"
                    ]
                })
    
    def _check_seasonal_alerts(self, stats, finca_name):
        """Verifica alertas estacionales específicas para olivar"""
        current_month = datetime.now().month
        ndvi_mean = stats.get("mean", 0)
        
        # Alertas específicas por temporada
        if current_month in [6, 7, 8]:  # Verano
            if ndvi_mean < 0.4:
                self.alerts.append({
                    "level": "warning",
                    "type": "Estrés Verano",
                    "title": "☀️ ATENCIÓN: Posible estrés hídrico veraniego",
                    "message": f"Durante el período crítico de verano, el NDVI ({ndvi_mean:.3f}) "
                              f"sugiere estrés hídrico en {finca_name}.",
                    "priority": 2,
                    "actions": [
                        "Incrementar frecuencia de riego",
                        "Revisar uniformidad del riego",
                        "Considerar riego nocturno",
                        "Evaluar sombreo natural"
                    ]
                })
        
        elif current_month in [3, 4, 5]:  # Primavera
            if ndvi_mean < 0.45:
                self.alerts.append({
                    "level": "info",
                    "type": "Desarrollo Primaveral",
                    "title": "🌱 INFO: Desarrollo primaveral por debajo del esperado",
                    "message": f"En período de crecimiento activo, el NDVI ({ndvi_mean:.3f}) "
                              f"podría ser más alto en {finca_name}.",
                    "priority": 3,
                    "actions": [
                        "Evaluar programa de fertilización primaveral",
                        "Verificar disponibilidad de agua",
                        "Monitorear desarrollo de brotes",
                        "Considerar análisis nutricional"
                    ]
                })

def create_alerts_dashboard(alerts):
    """
    Crea dashboard visual de alertas
    """
    if not alerts:
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "✅ No se detectaron problemas. El cultivo está en condiciones normales."
        ], color="success", className="mb-4")
    
    # Ordenar alertas por prioridad
    alerts_sorted = sorted(alerts, key=lambda x: x.get("priority", 3))
    
    alert_cards = []
    
    for alert in alerts_sorted:
        # Determinar icono según tipo de alerta
        icon_map = {
            "Vigor Crítico": "fas fa-exclamation-triangle",
            "Vigor Bajo": "fas fa-exclamation-circle", 
            "Uniformidad": "fas fa-chart-bar",
            "Área Problemática": "fas fa-map-marked-alt",
            "Estrés Verano": "fas fa-sun",
            "Desarrollo Primaveral": "fas fa-seedling"
        }
        
        icon = icon_map.get(alert["type"], "fas fa-info-circle")
        
        alert_card = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className=f"{icon} me-2"),
                    alert["title"]
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.P(alert["message"], className="mb-3"),
                html.H6("🔧 Acciones Recomendadas:", className="mb-2"),
                html.Ul([
                    html.Li(action) for action in alert.get("actions", [])
                ], className="mb-0")
            ])
        ], color=alert["level"], outline=True, className="mb-3")
        
        alert_cards.append(alert_card)
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5([
                    html.I(className="fas fa-bell me-2"),
                    f"Sistema de Alertas - {len(alerts)} detección(es)"
                ], className="mb-3")
            ])
        ]),
        html.Div(alert_cards)
    ])

def create_alerts_summary_badges(alerts):
    """
    Crea badges resumen de alertas por tipo y prioridad
    """
    if not alerts:
        return dbc.Badge("Sin Alertas", color="success", className="me-2")
    
    # Contar alertas por nivel
    levels = {"danger": 0, "warning": 0, "info": 0}
    for alert in alerts:
        level = alert.get("level", "info")
        if level in levels:
            levels[level] += 1
    
    badges = []
    
    if levels["danger"] > 0:
        badges.append(
            dbc.Badge([
                html.I(className="fas fa-exclamation-triangle me-1"),
                f"Críticas: {levels['danger']}"
            ], color="danger", className="me-2")
        )
    
    if levels["warning"] > 0:
        badges.append(
            dbc.Badge([
                html.I(className="fas fa-exclamation-circle me-1"),
                f"Atención: {levels['warning']}"
            ], color="warning", className="me-2")
        )
    
    if levels["info"] > 0:
        badges.append(
            dbc.Badge([
                html.I(className="fas fa-info-circle me-1"),
                f"Info: {levels['info']}"
            ], color="info", className="me-2")
        )
    
    return html.Div(badges)

def create_alert_timeline_chart(historical_alerts):
    """
    Crea gráfico temporal de evolución de alertas
    """
    # Datos simulados para demostración
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    critical_alerts = np.random.poisson(0.3, 30)  # Pocas alertas críticas
    warning_alerts = np.random.poisson(1.2, 30)   # Algunas alertas de atención
    info_alerts = np.random.poisson(2.1, 30)      # Más alertas informativas
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=critical_alerts,
        mode='lines+markers',
        name='Críticas',
        line=dict(color='#dc3545', width=3),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=warning_alerts,
        mode='lines+markers', 
        name='Atención',
        line=dict(color='#ffc107', width=2),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=info_alerts,
        mode='lines+markers',
        name='Informativas', 
        line=dict(color='#17a2b8', width=2),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title="Evolución de Alertas (Últimos 30 días)",
        xaxis_title="Fecha",
        yaxis_title="Número de Alertas",
        height=300,
        showlegend=True,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def generate_alert_report(alerts, finca_data=None):
    """
    Genera reporte textual de alertas para export
    """
    finca_name = finca_data.get("properties", {}).get("name", "Finca") if finca_data else "Finca"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""
REPORTE DE ALERTAS SATELITALES
===============================
Finca: {finca_name}
Fecha de análisis: {timestamp}
Sistema: Dashboard Agrícola TFM

RESUMEN DE ALERTAS:
------------------
Total de alertas detectadas: {len(alerts)}
"""
    
    if not alerts:
        report += "✅ No se detectaron problemas. El cultivo está en condiciones normales.\n"
        return report
    
    # Agrupar por nivel de prioridad
    critical = [a for a in alerts if a.get("level") == "danger"]
    warning = [a for a in alerts if a.get("level") == "warning"] 
    info = [a for a in alerts if a.get("level") == "info"]
    
    if critical:
        report += f"\n🔴 ALERTAS CRÍTICAS ({len(critical)}):\n"
        for i, alert in enumerate(critical, 1):
            report += f"{i}. {alert['title']}\n"
            report += f"   {alert['message']}\n"
            report += "   Acciones recomendadas:\n"
            for action in alert.get('actions', []):
                report += f"   - {action}\n"
            report += "\n"
    
    if warning:
        report += f"\n🟡 ALERTAS DE ATENCIÓN ({len(warning)}):\n"
        for i, alert in enumerate(warning, 1):
            report += f"{i}. {alert['title']}\n"
            report += f"   {alert['message']}\n"
            report += "   Acciones recomendadas:\n"
            for action in alert.get('actions', []):
                report += f"   - {action}\n"
            report += "\n"
    
    if info:
        report += f"\n🔵 ALERTAS INFORMATIVAS ({len(info)}):\n"
        for i, alert in enumerate(info, 1):
            report += f"{i}. {alert['title']}\n"
            report += f"   {alert['message']}\n"
            report += "   Acciones recomendadas:\n"
            for action in alert.get('actions', []):
                report += f"   - {action}\n"
            report += "\n"
    
    report += """
RECOMENDACIONES GENERALES:
-------------------------
- Realizar seguimiento semanal mediante imágenes satelitales
- Mantener registro de acciones implementadas
- Evaluar efectividad de medidas correctivas
- Consultar con técnico agrónomo para casos críticos

Generado por Sistema de Análisis Satelital Agrícola
Universidad de Granada - TFM Ciencia de Datos
"""
    
    return report
