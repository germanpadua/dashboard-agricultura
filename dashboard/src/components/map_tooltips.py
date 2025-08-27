"""
Map Tooltips Component for interactive NDVI value display
Click anywhere on map to get detailed vegetation health information
"""

import numpy as np
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from typing import Dict, List, Optional, Tuple, Any
import base64
import pickle
import logging
import json
import pandas as pd

logger = logging.getLogger(__name__)

def create_map_tooltip() -> html.Div:
    """
    Creates map tooltip container
    
    Returns:
        html.Div: Tooltip container
    """
    return html.Div([
        html.Div(id="map-tooltip-content"),
        dcc.Store(id="tooltip-data", data={}),
        dcc.Store(id="current-overlay-data", data={})
    ], id="map-tooltip", style={
        "position": "absolute",
        "top": "0px",
        "left": "0px", 
        "zIndex": 1001,
        "display": "none",
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "border": "1px solid #E8E8E8",
        "borderRadius": "8px",
        "padding": "12px",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
        "backdropFilter": "blur(10px)",
        "minWidth": "200px",
        "maxWidth": "300px",
        "pointerEvents": "none"
    })

def create_tooltip_content(
    lat: float, 
    lon: float, 
    ndvi_value: Optional[float] = None,
    index_name: str = "NDVI",
    additional_data: Dict = None
) -> html.Div:
    """
    Creates tooltip content for map click
    
    Args:
        lat: Latitude of clicked point
        lon: Longitude of clicked point  
        ndvi_value: NDVI value at clicked point
        index_name: Name of vegetation index
        additional_data: Additional contextual data
        
    Returns:
        html.Div: Tooltip content
    """
    additional_data = additional_data or {}
    
    # Header with coordinates
    header = html.Div([
        html.H6([
            html.I(className="fas fa-map-pin me-2", style={"color": "#2E7D32"}),
            "Información del Punto"
        ], className="mb-2", style={"fontSize": "0.9rem"})
    ])
    
    # Coordinates
    coords_section = html.Div([
        html.Small("📍 Coordenadas:", className="fw-bold text-muted"),
        html.Div(f"Lat: {lat:.6f}°", style={"fontSize": "0.8rem"}),
        html.Div(f"Lon: {lon:.6f}°", style={"fontSize": "0.8rem"}),
    ], className="mb-2")
    
    # Vegetation index value
    index_section = html.Div()
    if ndvi_value is not None:
        # Determine health status
        if index_name.upper() == "NDVI":
            if ndvi_value > 0.7:
                health_status = "Excelente"
                health_color = "#4CAF50"
                health_icon = "fas fa-leaf"
            elif ndvi_value > 0.5:
                health_status = "Buena"
                health_color = "#FF9800"
                health_icon = "fas fa-seedling"
            elif ndvi_value > 0.3:
                health_status = "Moderada"
                health_color = "#F44336"
                health_icon = "fas fa-exclamation-triangle"
            else:
                health_status = "Crítica"
                health_color = "#D32F2F"
                health_icon = "fas fa-exclamation-circle"
        else:
            health_status = "Normal"
            health_color = "#2196F3"
            health_icon = "fas fa-chart-line"
        
        index_section = html.Div([
            html.Small(f"🌱 {index_name}:", className="fw-bold text-muted"),
            html.Div([
                html.Span(f"{ndvi_value:.3f}", 
                         style={"fontSize": "1.1rem", "fontWeight": "bold", "color": health_color}),
                html.Div([
                    html.I(className=f"{health_icon} me-1", style={"color": health_color}),
                    html.Span(health_status, style={"color": health_color, "fontSize": "0.85rem"})
                ], className="mt-1")
            ])
        ], className="mb-2")
    else:
        index_section = html.Div([
            html.Small("ℹ️ ", className="text-muted"),
            html.Small("Haz clic en un área analizada para ver valores", className="text-muted")
        ], className="mb-2")
    
    # Recommendations based on value
    recommendations = html.Div()
    if ndvi_value is not None and index_name.upper() == "NDVI":
        if ndvi_value > 0.7:
            rec_text = "Vegetación saludable. Mantener manejo actual."
            rec_color = "#4CAF50"
            rec_icon = "fas fa-check-circle"
        elif ndvi_value > 0.5:
            rec_text = "Considerar optimización de nutrientes."
            rec_color = "#FF9800"
            rec_icon = "fas fa-info-circle"
        elif ndvi_value > 0.3:
            rec_text = "Revisar riego y estado sanitario."
            rec_color = "#F44336"
            rec_icon = "fas fa-exclamation-triangle"
        else:
            rec_text = "Intervención urgente requerida."
            rec_color = "#D32F2F"
            rec_icon = "fas fa-exclamation-circle"
        
        recommendations = html.Div([
            html.Hr(style={"margin": "8px 0"}),
            html.Div([
                html.I(className=f"{rec_icon} me-2", style={"color": rec_color}),
                html.Small(rec_text, style={"color": rec_color})
            ])
        ])
    
    # Additional contextual data
    context_section = html.Div()
    if additional_data:
        context_items = []
        for key, value in additional_data.items():
            if key == "elevation":
                context_items.append(
                    html.Div(f"🏔️ Elevación: {value}m", style={"fontSize": "0.8rem"})
                )
            elif key == "slope":
                context_items.append(
                    html.Div(f"📐 Pendiente: {value}°", style={"fontSize": "0.8rem"})
                )
            elif key == "soil_type":
                context_items.append(
                    html.Div(f"🌍 Suelo: {value}", style={"fontSize": "0.8rem"})
                )
        
        if context_items:
            context_section = html.Div([
                html.Hr(style={"margin": "8px 0"}),
                html.Div(context_items)
            ])
    
    return html.Div([
        header,
        coords_section,
        index_section,
        recommendations,
        context_section
    ])

def interpolate_array_value(array: np.ndarray, bounds: List[List[float]], lat: float, lon: float) -> Optional[float]:
    """
    Interpolates array value at given coordinates
    
    Args:
        array: 2D numpy array
        bounds: [[south, west], [north, east]]
        lat: Latitude
        lon: Longitude
        
    Returns:
        Interpolated value or None if out of bounds
    """
    try:
        if not bounds or len(bounds) != 2:
            return None
        
        south, west = bounds[0]
        north, east = bounds[1]
        
        # Check if point is within bounds
        if not (south <= lat <= north and west <= lon <= east):
            return None
        
        # Convert lat/lon to array indices
        height, width = array.shape
        
        # Normalize coordinates to [0, 1]
        lat_norm = (lat - south) / (north - south)
        lon_norm = (lon - west) / (east - west)
        
        # Convert to array indices
        row = int((1 - lat_norm) * (height - 1))  # Flip because array is top-to-bottom
        col = int(lon_norm * (width - 1))
        
        # Ensure indices are within bounds
        row = max(0, min(height - 1, row))
        col = max(0, min(width - 1, col))
        
        value = array[row, col]
        
        # Return None if value is NaN or invalid
        if np.isfinite(value):
            return float(value)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error interpolating array value: {e}")
        return None

def create_map_click_callbacks(app):
    """
    Creates callbacks for map click interactions and tooltips
    """
    
    @app.callback(
        [Output("map-tooltip", "style"),
         Output("map-tooltip-content", "children"),
         Output("tooltip-data", "data")],
        [Input("sat-map", "clickData")],
        [State("raw-ndvi-data-store", "data"),
         State("overlay-bounds", "data"),
         State("analysis-index-selector", "value")],
        prevent_initial_call=True
    )
    def handle_map_click(clickData, stored_data, bounds_data, selected_index):
        if not clickData:
            return {"display": "none"}, "", {}
        
        try:
            # Extract coordinates from click data
            lat = clickData['points'][0]['lat']
            lon = clickData['points'][0]['lon']
            
            # Get vegetation index value if data is available
            ndvi_value = None
            index_name = selected_index or "NDVI"
            
            if stored_data and bounds_data:
                indices = stored_data.get("indices", {})
                if index_name in indices:
                    try:
                        # Deserialize array
                        array_data = pickle.loads(base64.b64decode(indices[index_name]['array']))
                        # Interpolate value at clicked coordinates
                        ndvi_value = interpolate_array_value(array_data, bounds_data, lat, lon)
                    except Exception as e:
                        logger.error(f"Error extracting value from array: {e}")
            
            # Create tooltip content
            tooltip_content = create_tooltip_content(
                lat=lat,
                lon=lon, 
                ndvi_value=ndvi_value,
                index_name=index_name,
                additional_data={}  # Could add elevation, soil type, etc.
            )
            
            # Position tooltip near click point
            # Note: In a real implementation, you'd convert lat/lon to pixel coordinates
            tooltip_style = {
                "position": "absolute",
                "top": "100px",  # Would calculate based on click position
                "left": "100px", # Would calculate based on click position
                "zIndex": 1001,
                "display": "block",
                "backgroundColor": "rgba(255, 255, 255, 0.95)",
                "border": "1px solid #E8E8E8",
                "borderRadius": "8px",
                "padding": "12px",
                "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
                "backdropFilter": "blur(10px)",
                "minWidth": "200px",
                "maxWidth": "300px",
                "pointerEvents": "auto"  # Allow interaction with tooltip
            }
            
            # Store data for potential future use
            tooltip_data = {
                "lat": lat,
                "lon": lon,
                "ndvi_value": ndvi_value,
                "index_name": index_name,
                "timestamp": str(pd.Timestamp.now())
            }
            
            logger.info(f"🗺️ Map clicked at ({lat:.6f}, {lon:.6f}) - {index_name}: {ndvi_value}")
            
            return tooltip_style, tooltip_content, tooltip_data
            
        except Exception as e:
            logger.error(f"Error handling map click: {e}")
            return {"display": "none"}, "", {}
    
    
    @app.callback(
        Output("map-tooltip", "style", allow_duplicate=True),
        Input("sat-map", "relayoutData"),
        prevent_initial_call=True
    )
    def hide_tooltip_on_map_interaction(relayoutData):
        """Hide tooltip when user interacts with map (zoom, pan)"""
        if relayoutData:
            return {"display": "none"}
        return no_update

def create_enhanced_map_interactions() -> html.Div:
    """
    Creates enhanced map interaction panel
    
    Returns:
        html.Div: Enhanced interactions panel
    """
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-mouse-pointer me-2"),
                    "Interacciones del Mapa"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-hand-pointer me-2", style={"color": "#2E7D32"}),
                        html.Strong("Clic en el mapa: "),
                        html.Span("Ver valores NDVI y recomendaciones")
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-search-plus me-2", style={"color": "#2196F3"}),
                        html.Strong("Zoom: "),
                        html.Span("Rueda del ratón o controles del mapa")
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-arrows-alt me-2", style={"color": "#FF9800"}),
                        html.Strong("Arrastrar: "),
                        html.Span("Mover la vista del mapa")
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-layer-group me-2", style={"color": "#9C27B0"}),
                        html.Strong("Capas: "),
                        html.Span("Control en esquina superior derecha")
                    ])
                ], style={"fontSize": "0.9rem"})
            ])
        ], className="mb-3")
    ], className="map-interactions-help")