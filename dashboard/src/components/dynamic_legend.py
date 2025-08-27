"""
Dynamic Legend Component with histogram and real-time stats
Advanced interactive legend for satellite data visualization
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Dict, Optional, Tuple
import base64
import pickle
import logging

logger = logging.getLogger(__name__)

def create_dynamic_legend(
    index_data: Dict, 
    index_name: str = "NDVI", 
    colormap_name: str = "agricultura",
    show_histogram: bool = True
) -> html.Div:
    """
    Creates an advanced dynamic legend with histogram and statistics
    
    Args:
        index_data: Dictionary with array data
        index_name: Name of the vegetation index
        colormap_name: Colormap being used
        show_histogram: Whether to show histogram
    
    Returns:
        html.Div: Dynamic legend component
    """
    if not index_data or 'array' not in index_data:
        return html.Div("No hay datos para mostrar la leyenda", className="text-muted small")
    
    try:
        # Deserialize array data
        array = pickle.loads(base64.b64decode(index_data['array']))
        valid_data = array[np.isfinite(array)]
        
        if len(valid_data) == 0:
            return html.Div("Sin datos válidos", className="text-muted small")
        
        # Calculate statistics
        stats = {
            'min': float(np.min(valid_data)),
            'max': float(np.max(valid_data)),
            'mean': float(np.mean(valid_data)),
            'std': float(np.std(valid_data)),
            'p25': float(np.percentile(valid_data, 25)),
            'p75': float(np.percentile(valid_data, 75)),
            'count': len(valid_data),
            'total_pixels': array.size
        }
        
        # Create color scale visualization
        color_scale = _create_color_scale_bar(index_name, colormap_name, stats['min'], stats['max'])
        
        # Create mini histogram if requested
        histogram = None
        if show_histogram and len(valid_data) > 10:
            histogram = _create_mini_histogram(valid_data, index_name)
        
        # Health assessment for NDVI
        health_assessment = None
        if index_name.upper() == "NDVI":
            health_assessment = _create_health_assessment(valid_data)
        
        # Build legend components
        legend_components = [
            # Header
            html.Div([
                html.H6([
                    html.I(className=f"fas fa-{'leaf' if index_name.upper() == 'NDVI' else 'chart-line'} me-2"),
                    f"Leyenda {index_name}"
                ], className="mb-2", style={"color": "#2E7D32"}),
            ]),
            
            # Color scale
            color_scale,
            
            # Statistics table
            _create_stats_table(stats, index_name),
        ]
        
        # Add histogram if available
        if histogram:
            legend_components.insert(-1, histogram)
        
        # Add health assessment for NDVI
        if health_assessment:
            legend_components.append(health_assessment)
        
        return html.Div(
            legend_components,
            className="dynamic-legend-container",
            style={
                'backgroundColor': 'rgba(255, 255, 255, 0.95)',
                'border': '1px solid #E8E8E8',
                'borderRadius': '12px',
                'padding': '1rem',
                'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.15)',
                'backdropFilter': 'blur(10px)',
                'minWidth': '280px',
                'maxWidth': '320px'
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating dynamic legend: {e}")
        return html.Div(f"Error en leyenda: {str(e)}", className="text-danger small")

def _create_color_scale_bar(index_name: str, colormap_name: str, vmin: float, vmax: float) -> html.Div:
    """Creates a color scale bar visualization"""
    
    # Create a gradient div for color scale
    # Using CSS gradient based on common NDVI colors
    if index_name.upper() == "NDVI":
        gradient = "linear-gradient(to right, #8B0000, #FF4500, #FFD700, #ADFF2F, #32CD32, #006400)"
    elif index_name.upper() == "OSAVI":
        gradient = "linear-gradient(to right, #4B0082, #0000FF, #00BFFF, #00FF7F, #32CD32)"
    else:
        gradient = "linear-gradient(to right, #800080, #FF1493, #FF6347, #FFD700, #32CD32)"
    
    return html.Div([
        # Color bar
        html.Div(
            style={
                'height': '20px',
                'background': gradient,
                'borderRadius': '4px',
                'border': '1px solid #E8E8E8',
                'marginBottom': '8px'
            }
        ),
        # Scale labels
        html.Div([
            html.Span(f"{vmin:.3f}", style={'fontSize': '0.75rem', 'color': '#666'}),
            html.Span(f"{vmax:.3f}", 
                     style={'fontSize': '0.75rem', 'color': '#666', 'float': 'right'})
        ], style={'position': 'relative'})
    ], className="mb-3")

def _create_mini_histogram(data: np.ndarray, index_name: str) -> dcc.Graph:
    """Creates a mini histogram for the legend"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=20,
        marker=dict(
            color='#2E7D32',
            opacity=0.7,
            line=dict(width=0.5, color='white')
        ),
        showlegend=False
    ))
    
    fig.update_layout(
        height=120,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10),
        xaxis=dict(
            title=dict(text=index_name, font=dict(size=10)),
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            tickfont=dict(size=8)
        ),
        yaxis=dict(
            title=dict(text="Frecuencia", font=dict(size=10)),
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            tickfont=dict(size=8)
        )
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        className="mini-histogram mb-2"
    )

def _create_stats_table(stats: Dict, index_name: str) -> html.Div:
    """Creates a compact statistics table"""
    
    return html.Div([
        html.H6("📊 Estadísticas", className="mb-2", style={"color": "#666", "fontSize": "0.9rem"}),
        html.Table([
            html.Tbody([
                html.Tr([
                    html.Td("Promedio:", style={"fontSize": "0.8rem", "paddingRight": "8px"}),
                    html.Td(f"{stats['mean']:.3f}", style={"fontSize": "0.8rem", "fontWeight": "600"})
                ]),
                html.Tr([
                    html.Td("Rango:", style={"fontSize": "0.8rem", "paddingRight": "8px"}), 
                    html.Td(f"{stats['min']:.3f} - {stats['max']:.3f}", style={"fontSize": "0.8rem"})
                ]),
                html.Tr([
                    html.Td("Desv. Est:", style={"fontSize": "0.8rem", "paddingRight": "8px"}),
                    html.Td(f"{stats['std']:.3f}", style={"fontSize": "0.8rem"})
                ]),
                html.Tr([
                    html.Td("Píxeles:", style={"fontSize": "0.8rem", "paddingRight": "8px"}),
                    html.Td(f"{stats['count']:,}", style={"fontSize": "0.8rem"})
                ]),
                html.Tr([
                    html.Td("Cobertura:", style={"fontSize": "0.8rem", "paddingRight": "8px"}),
                    html.Td(f"{stats['count']/stats['total_pixels']*100:.1f}%", style={"fontSize": "0.8rem"})
                ])
            ])
        ], style={"width": "100%"})
    ], className="mb-3")

def _create_health_assessment(ndvi_data: np.ndarray) -> html.Div:
    """Creates health assessment for NDVI data"""
    
    # Classification thresholds
    excellent = np.sum(ndvi_data > 0.7)
    good = np.sum((ndvi_data > 0.5) & (ndvi_data <= 0.7))
    moderate = np.sum((ndvi_data > 0.3) & (ndvi_data <= 0.5))
    poor = np.sum(ndvi_data <= 0.3)
    total = len(ndvi_data)
    
    # Overall health score
    health_score = (excellent * 4 + good * 3 + moderate * 2 + poor * 1) / (total * 4) * 100
    
    # Status color
    if health_score >= 75:
        status_color = "#4CAF50"
        status_text = "Excelente"
        status_icon = "fas fa-leaf"
    elif health_score >= 50:
        status_color = "#FF9800" 
        status_text = "Buena"
        status_icon = "fas fa-seedling"
    elif health_score >= 25:
        status_color = "#F44336"
        status_text = "Moderada"
        status_icon = "fas fa-exclamation-triangle"
    else:
        status_color = "#D32F2F"
        status_text = "Crítica"
        status_icon = "fas fa-exclamation-circle"
    
    return html.Div([
        html.H6("🌱 Salud Vegetal", className="mb-2", style={"color": "#666", "fontSize": "0.9rem"}),
        html.Div([
            html.I(className=f"{status_icon} me-2", style={"color": status_color}),
            html.Span(f"{status_text} ({health_score:.0f}%)", 
                     style={"color": status_color, "fontWeight": "600", "fontSize": "0.9rem"})
        ], className="mb-2"),
        html.Div([
            _create_health_bar("Excelente", excellent/total*100, "#4CAF50"),
            _create_health_bar("Buena", good/total*100, "#FF9800"),
            _create_health_bar("Moderada", moderate/total*100, "#F44336"),
            _create_health_bar("Crítica", poor/total*100, "#D32F2F")
        ])
    ])

def _create_health_bar(label: str, percentage: float, color: str) -> html.Div:
    """Creates a small health bar"""
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize": "0.75rem", "color": "#666"}),
            html.Span(f"{percentage:.1f}%", 
                     style={"fontSize": "0.75rem", "color": "#666", "float": "right"})
        ]),
        html.Div([
            html.Div(
                style={
                    'width': f'{percentage}%',
                    'height': '4px',
                    'backgroundColor': color,
                    'borderRadius': '2px',
                    'transition': 'width 0.3s ease'
                }
            )
        ], style={
            'width': '100%',
            'height': '4px', 
            'backgroundColor': '#E8E8E8',
            'borderRadius': '2px',
            'marginBottom': '4px'
        })
    ], style={'marginBottom': '6px'})

def create_floating_legend_callback(app):
    """
    Creates callback to update the floating legend position and content
    """
    from dash import Input, Output, State, callback_context
    
    @app.callback(
        Output("floating-legend", "children"),
        Output("floating-legend", "style"),
        [
            Input("raw-ndvi-data-store", "data"),
            Input("analysis-index-selector", "value"),
            Input("ndvi-colormap-selector", "value"),
        ],
        prevent_initial_call=True
    )
    def update_floating_legend(stored_data, selected_index, colormap_name):
        if not stored_data or not selected_index:
            return "", {"display": "none"}
        
        indices = stored_data.get("indices", {})
        if selected_index not in indices:
            return "", {"display": "none"}
        
        legend_content = create_dynamic_legend(
            indices[selected_index], 
            selected_index, 
            colormap_name or "agricultura",
            show_histogram=True
        )
        
        legend_style = {
            "position": "absolute",
            "top": "20px",
            "right": "20px",
            "zIndex": 1000,
            "display": "block"
        }
        
        return legend_content, legend_style