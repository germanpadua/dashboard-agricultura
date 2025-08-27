"""
Temporal Comparator Component with before/after slider
Advanced temporal comparison tool for satellite data
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import os
from typing import Dict, List, Optional, Tuple
import base64
import pickle
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def create_temporal_comparator() -> html.Div:
    """
    Creates temporal comparator interface with slider
    
    Returns:
        html.Div: Temporal comparator component
    """
    
    return html.Div([
        # Header with controls
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-history me-2"),
                    "Comparador Temporal"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Período Base:", className="fw-bold small"),
                        dcc.DatePickerRange(
                            id="temporal-base-period",
                            start_date=(datetime.now() - timedelta(days=60)).date(),
                            end_date=(datetime.now() - timedelta(days=30)).date(),
                            display_format="DD/MM/YYYY",
                            className="mb-2"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Período Comparación:", className="fw-bold small"),
                        dcc.DatePickerRange(
                            id="temporal-comparison-period", 
                            start_date=(datetime.now() - timedelta(days=30)).date(),
                            end_date=datetime.now().date(),
                            display_format="DD/MM/YYYY",
                            className="mb-2"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Acciones:", className="fw-bold small"),
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Comparar"
                        ], id="run-temporal-comparison", color="primary", className="w-100")
                    ], md=4)
                ])
            ])
        ], className="mb-3"),
        
        # Comparison viewer with slider
        html.Div([
            html.Div(id="temporal-comparison-viewer", className="mb-3"),
            html.Div(id="temporal-metrics-comparison", className="mb-3")
        ], id="temporal-comparison-container", style={"display": "none"})
    ], id="temporal-comparator-section")

def create_before_after_viewer(
    base_data: Dict, 
    comparison_data: Dict,
    index_name: str = "NDVI"
) -> html.Div:
    """
    Creates before/after viewer with slider divider
    
    Args:
        base_data: Base period data
        comparison_data: Comparison period data
        index_name: Vegetation index name
        
    Returns:
        html.Div: Before/after viewer component
    """
    try:
        # Deserialize arrays
        base_array = pickle.loads(base64.b64decode(base_data['array']))
        comp_array = pickle.loads(base64.b64decode(comparison_data['array']))
        
        # Calculate difference
        diff_array = comp_array - base_array
        
        # Create side-by-side comparison plots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[
                f'{index_name} - Período Base',
                f'{index_name} - Período Comparación', 
                'Diferencia (Comparación - Base)',
                'Histograma Base',
                'Histograma Comparación',
                'Histograma Diferencias'
            ],
            specs=[[{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
                   [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}]]
        )
        
        # Base period heatmap
        fig.add_trace(
            go.Heatmap(
                z=base_array,
                colorscale='RdYlGn',
                zmin=0, zmax=1,
                showscale=False,
                name="Base"
            ),
            row=1, col=1
        )
        
        # Comparison period heatmap
        fig.add_trace(
            go.Heatmap(
                z=comp_array,
                colorscale='RdYlGn', 
                zmin=0, zmax=1,
                showscale=False,
                name="Comparación"
            ),
            row=1, col=2
        )
        
        # Difference heatmap
        fig.add_trace(
            go.Heatmap(
                z=diff_array,
                colorscale='RdBu',
                zmid=0,
                showscale=True,
                name="Diferencia"
            ),
            row=1, col=3
        )
        
        # Histograms
        base_valid = base_array[np.isfinite(base_array)]
        comp_valid = comp_array[np.isfinite(comp_array)]
        diff_valid = diff_array[np.isfinite(diff_array)]
        
        # Base histogram
        fig.add_trace(
            go.Histogram(x=base_valid, nbinsx=30, name="Base", 
                        marker=dict(color='#1f77b4', opacity=0.7)),
            row=2, col=1
        )
        
        # Comparison histogram
        fig.add_trace(
            go.Histogram(x=comp_valid, nbinsx=30, name="Comparación",
                        marker=dict(color='#ff7f0e', opacity=0.7)), 
            row=2, col=2
        )
        
        # Difference histogram
        fig.add_trace(
            go.Histogram(x=diff_valid, nbinsx=30, name="Diferencia",
                        marker=dict(color='#2ca02c', opacity=0.7)),
            row=2, col=3
        )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            title=dict(
                text=f"📊 Comparación Temporal - {index_name}",
                x=0.5,
                font=dict(size=16)
            )
        )
        
        return html.Div([
            dcc.Graph(figure=fig, className="temporal-comparison-chart"),
            _create_comparison_slider()
        ])
        
    except Exception as e:
        logger.error(f"Error creating before/after viewer: {e}")
        return html.Div(f"Error en comparación: {str(e)}", className="text-danger")

def _create_comparison_slider() -> html.Div:
    """Creates interactive comparison slider"""
    
    return html.Div([
        html.H6("🔄 Control de Comparación", className="mb-3"),
        html.Div([
            dbc.Label("Mezcla de períodos:", className="small"),
            dcc.Slider(
                id="temporal-blend-slider",
                min=0,
                max=100,
                value=50,
                marks={
                    0: {'label': 'Solo Base', 'style': {'color': '#1f77b4'}},
                    50: {'label': 'Mezcla 50/50', 'style': {'color': '#666'}},
                    100: {'label': 'Solo Comparación', 'style': {'color': '#ff7f0e'}}
                },
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            )
        ]),
        html.Div([
            dbc.Button([
                html.I(className="fas fa-play me-2"),
                "Reproducir Animación"
            ], id="temporal-animation-btn", color="secondary", outline=True),
            dcc.Interval(
                id="temporal-animation-interval", 
                interval=800, 
                n_intervals=0, 
                disabled=True
            )
        ])
    ], className="temporal-controls p-3", 
       style={'backgroundColor': '#F8FFF8', 'borderRadius': '8px'})

def create_temporal_metrics_comparison(base_data: Dict, comparison_data: Dict, index_name: str) -> html.Div:
    """
    Creates metrics comparison between two time periods
    
    Args:
        base_data: Base period data
        comparison_data: Comparison period data 
        index_name: Vegetation index name
        
    Returns:
        html.Div: Metrics comparison component
    """
    try:
        # Deserialize and calculate stats
        base_array = pickle.loads(base64.b64decode(base_data['array']))
        comp_array = pickle.loads(base64.b64decode(comparison_data['array']))
        
        base_valid = base_array[np.isfinite(base_array)]
        comp_valid = comp_array[np.isfinite(comp_array)]
        
        if len(base_valid) == 0 or len(comp_valid) == 0:
            return html.Div("Sin datos válidos para comparar", className="text-warning")
        
        # Calculate metrics
        base_stats = {
            'mean': float(np.mean(base_valid)),
            'std': float(np.std(base_valid)),
            'min': float(np.min(base_valid)),
            'max': float(np.max(base_valid))
        }
        
        comp_stats = {
            'mean': float(np.mean(comp_valid)),
            'std': float(np.std(comp_valid)), 
            'min': float(np.min(comp_valid)),
            'max': float(np.max(comp_valid))
        }
        
        # Calculate changes
        changes = {
            'mean': comp_stats['mean'] - base_stats['mean'],
            'std': comp_stats['std'] - base_stats['std'],
            'min': comp_stats['min'] - base_stats['min'],
            'max': comp_stats['max'] - base_stats['max']
        }
        
        # Create comparison cards
        return dbc.Row([
            dbc.Col([
                _create_metric_comparison_card(
                    "Valor Promedio",
                    base_stats['mean'], 
                    comp_stats['mean'],
                    changes['mean'],
                    "fas fa-chart-line"
                )
            ], md=3),
            dbc.Col([
                _create_metric_comparison_card(
                    "Variabilidad",
                    base_stats['std'],
                    comp_stats['std'], 
                    changes['std'],
                    "fas fa-wave-square"
                )
            ], md=3),
            dbc.Col([
                _create_metric_comparison_card(
                    "Valor Mínimo", 
                    base_stats['min'],
                    comp_stats['min'],
                    changes['min'],
                    "fas fa-arrow-down"
                )
            ], md=3),
            dbc.Col([
                _create_metric_comparison_card(
                    "Valor Máximo",
                    base_stats['max'],
                    comp_stats['max'],
                    changes['max'], 
                    "fas fa-arrow-up"
                )
            ], md=3)
        ])
        
    except Exception as e:
        logger.error(f"Error creating temporal metrics: {e}")
        return html.Div(f"Error en métricas: {str(e)}", className="text-danger")

def _create_metric_comparison_card(title: str, base_val: float, comp_val: float, change: float, icon: str) -> dbc.Card:
    """Creates a metric comparison card"""
    
    # Determine change color and direction
    if abs(change) < 0.001:
        change_color = "#666"
        change_icon = "fas fa-minus"
        change_text = "Sin cambio"
    elif change > 0:
        change_color = "#4CAF50"
        change_icon = "fas fa-arrow-up"
        change_text = f"+{change:.3f}"
    else:
        change_color = "#F44336"
        change_icon = "fas fa-arrow-down"
        change_text = f"{change:.3f}"
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon} me-2"),
            html.Small(title, className="fw-bold")
        ]),
        dbc.CardBody([
            html.Div([
                html.Small("Base:", className="text-muted"),
                html.Div(f"{base_val:.3f}", className="h6 mb-1")
            ]),
            html.Div([
                html.Small("Actual:", className="text-muted"),
                html.Div(f"{comp_val:.3f}", className="h6 mb-1")
            ]),
            html.Hr(className="my-2"),
            html.Div([
                html.I(className=f"{change_icon} me-1", style={"color": change_color}),
                html.Span(change_text, style={"color": change_color, "fontWeight": "600"})
            ])
        ])
    ], className="h-100")

def create_temporal_comparator_callbacks(app):
    """
    Creates callbacks for temporal comparator functionality
    """
    
    @app.callback(
        [Output("temporal-comparison-container", "style"),
         Output("temporal-comparison-viewer", "children"),
         Output("temporal-metrics-comparison", "children")],
        Input("run-temporal-comparison", "n_clicks"),
        [State("temporal-base-period", "start_date"),
         State("temporal-base-period", "end_date"), 
         State("temporal-comparison-period", "start_date"),
         State("temporal-comparison-period", "end_date"),
         State("raw-ndvi-data-store", "data"),
         State("analysis-index-selector", "value")],
        prevent_initial_call=True
    )
    def run_temporal_comparison(n_clicks, base_start, base_end, comp_start, comp_end, stored_data, index_name):
        if not n_clicks:
            return {"display": "none"}, "", ""
        
        try:
            # Import required modules
            import os
            from src.utils.satellite_utils import get_access_token, compute_index_composite, build_evalscript
            from src.utils.finca_store import list_fincas
            import base64
            import pickle
            import numpy as np
            
            # Validate dates
            if not all([base_start, base_end, comp_start, comp_end]):
                return {"display": "block"}, dbc.Alert("Faltan fechas para la comparación", color="warning"), ""
            
            # Get authentication token
            cid = os.getenv("COPERNICUS_CLIENT_ID")
            csec = os.getenv("COPERNICUS_CLIENT_SECRET")
            if not cid or not csec:
                return {"display": "block"}, dbc.Alert("Credenciales de Copernicus no configuradas", color="danger"), ""
            
            token = get_access_token(cid, csec)
            selected_index = index_name or "NDVI"
            
            # Get current geometry from stored data
            if stored_data:
                try:
                    raw_data = pickle.loads(base64.b64decode(stored_data))
                    geometry = raw_data.get("geometry")
                except:
                    geometry = None
            else:
                geometry = None
            
            if not geometry:
                return {"display": "block"}, dbc.Alert("Selecciona una finca primero", color="warning"), ""
            
            # Fetch base period data
            base_array, _ = compute_index_composite(
                token=token,
                geometry_or_bbox=geometry,
                start_date=base_start,
                end_date=base_end,
                index=selected_index,
                masked=True,
                width=512,  # Smaller for comparison
                height=512
            )
            
            # Fetch comparison period data
            comp_array, _ = compute_index_composite(
                token=token,
                geometry_or_bbox=geometry,
                start_date=comp_start,
                end_date=comp_end,
                index=selected_index,
                masked=True,
                width=512,  # Smaller for comparison
                height=512
            )
            
            if base_array is None or comp_array is None:
                return {"display": "block"}, dbc.Alert("No se pudieron obtener datos para la comparación", color="danger"), ""
            
            # Ensure same dimensions
            min_h = min(base_array.shape[0], comp_array.shape[0])
            min_w = min(base_array.shape[1], comp_array.shape[1])
            base_array = base_array[:min_h, :min_w]
            comp_array = comp_array[:min_h, :min_w]
            
            # Create data dictionaries for comparison
            base_data = {
                'array': base64.b64encode(pickle.dumps(base_array)).decode('ascii'),
                'period': f"{base_start} a {base_end}"
            }
            
            comp_data = {
                'array': base64.b64encode(pickle.dumps(comp_array)).decode('ascii'),
                'period': f"{comp_start} a {comp_end}"
            }
            
            # Create viewer and metrics
            viewer = create_before_after_viewer(base_data, comp_data, selected_index)
            metrics = create_temporal_metrics_comparison(base_data, comp_data, selected_index)
            
            return {"display": "block"}, viewer, metrics
            
        except Exception as e:
            logger.error(f"Error in temporal comparison: {e}")
            return {"display": "block"}, dbc.Alert(f"Error en comparación: {str(e)}", color="danger"), ""
    
    @app.callback(
        Output("temporal-animation-interval", "disabled"),
        Input("temporal-animation-btn", "n_clicks"),
        State("temporal-animation-interval", "disabled"),
        prevent_initial_call=True
    )
    def toggle_animation(n_clicks, is_disabled):
        return not is_disabled