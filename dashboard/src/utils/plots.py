"""Utilidades de visualización para datos agrícolas.

Este módulo proporciona funciones para crear gráficos de datos meteorológicos
con énfasis en el análisis de condiciones de riesgo para cultivos.
"""

# Librerías de terceros
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def make_soil_figure(dfg: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico de humedad y precipitación con zonas de riesgo.
    
    Args:
        dfg: DataFrame con datos meteorológicos indexado por fecha
        
    Returns:
        Figura de Plotly con gráfico de doble eje
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Zona de riesgo repilo: Humedad > 95%
    if not dfg.empty:
        x_range = [dfg.index.min(), dfg.index.max()]
        fig.add_trace(
            go.Scatter(
                x=[x_range[0], x_range[1], x_range[1], x_range[0], x_range[0]],
                y=[95, 95, 105, 105, 95],
                fill="toself",
                fillcolor="rgba(255, 193, 7, 0.3)",
                line=dict(color="rgba(255, 193, 7, 0)", width=0),
                name="⚠️ Zona Riesgo Repilo",
                hovertemplate="<b>ZONA DE RIESGO REPILO</b><br>Humedad > 95%<br><extra></extra>",
                showlegend=True
            ),
            secondary_y=True
        )

    fig.add_trace(
        go.Scatter(
            x=dfg.index,
            y=dfg['Air_Relat_Hum_mean'],
            name="Humedad (%)",
            mode="lines+markers",
            line=dict(color="#4169E1", width=3, shape="spline"),
            marker=dict(size=6),
            hovertemplate="%{x|%d %b %Y}<br><b>%{y:.0f} %</b><extra></extra>"
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Bar(
            x=dfg.index,
            y=dfg['Rain_sum'],
            name="Lluvia (mm)",
            width=0.8 * 24*60*60*1000,
            marker=dict(
                color="rgba(30,144,255,0.6)",
                line=dict(color="rgba(30,144,255,1)", width=1.5)
            ),
            hovertemplate="%{x|%d %b %Y}<br><b>%{y:.1f} mm</b><extra></extra>"
        ),
        secondary_y=False
    )

    # Línea de referencia en 95% (umbral crítico)
    if not dfg.empty:
        fig.add_hline(
            y=95,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text="Umbral Riesgo (95%)",
            annotation_position="top right",
            secondary_y=True
        )

    fig.update_layout(
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=80, b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.2)", tickangle=-45)
    fig.update_yaxes(
        title_text="Precipitación (mm)",
        secondary_y=False,
        rangemode="tozero",  # Asegurar que el eje Y empiece en 0
        showgrid=True,
        gridcolor="rgba(200,200,200,0.2)"
    )
    fig.update_yaxes(
        title_text="Humedad (%)",
        secondary_y=True,
        range=[0, 105],
        rangemode="tozero",  # Asegurar que el eje Y empiece en 0
        showgrid=False  # Evitar sobrecarga visual con múltiples grillas
    )
    return fig

def make_temp_figure(dfg: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico de temperatura con zonas de riesgo para repilo.
    
    Args:
        dfg: DataFrame con datos meteorológicos indexado por fecha
        
    Returns:
        Figura de Plotly con gráfico de temperaturas
    """
    fig = go.Figure()
    
    # Zona de riesgo repilo: Temperatura óptima (13-17°C)
    if not dfg.empty:
        x_range = [dfg.index.min(), dfg.index.max()]
        
        # Zona de riesgo óptimo para desarrollo del hongo
        fig.add_trace(go.Scatter(
            x=[x_range[0], x_range[1], x_range[1], x_range[0], x_range[0]],
            y=[13, 13, 17, 17, 13],
            fill="toself",
            fillcolor="rgba(255, 152, 0, 0.3)",
            line=dict(color="rgba(255, 152, 0, 0)", width=0),
            name="⚠️ Zona Riesgo Repilo",
            hovertemplate="<b>ZONA RIESGO REPILO</b><br>Temperatura óptima: 13-17°C<extra></extra>",
            showlegend=True
        ))

    # Línea de temperatura media (principal)
    fig.add_trace(go.Scatter(
        x=dfg.index,
        y=dfg["Air_Temp_mean"],
        mode="lines+markers",
        line=dict(color="crimson", width=3, shape="spline"),
        marker=dict(size=5, symbol="circle", color="crimson"),
        name="Media",
        hovertemplate="%{x|%d %b %Y}<br>Media: %{y:.1f}°C<extra></extra>"
    ))

    # Línea de temperatura mínima
    fig.add_trace(go.Scatter(
        x=dfg.index,
        y=dfg["Air_Temp_min"],
        mode="lines",
        line=dict(color="blue", width=2, dash="dash"),
        name="Mínima",
        hovertemplate="%{x|%d %b %Y}<br>Mín: %{y:.1f}°C<extra></extra>"
    ))

    # Línea de temperatura máxima
    fig.add_trace(go.Scatter(
        x=dfg.index,
        y=dfg["Air_Temp_max"],
        mode="lines",
        line=dict(color="red", width=2, dash="dash"),
        name="Máxima",
        hovertemplate="%{x|%d %b %Y}<br>Máx: %{y:.1f}°C<extra></extra>"
    ))

    # Línea de referencia: temperatura óptima para repilo
    if not dfg.empty:
        fig.add_hline(
            y=15,
            line_dash="solid",
            line_color="darkorange",
            line_width=2,
            annotation_text="Temp. Óptima Repilo (15°C)",
            annotation_position="top right"
        )

    # Configuración del layout
    fig.update_layout(
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=80, b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.2)", tickangle=-45)
    fig.update_yaxes(
        title_text="Temperatura (°C)",
        rangemode="tozero",  # Asegurar que el eje Y empiece en 0
        showgrid=True,
        gridcolor="rgba(200,200,200,0.2)"
    )

    return fig