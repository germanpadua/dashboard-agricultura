"""
===============================================================================
                      CALLBACKS DE GESTIÓN DE FINCAS
===============================================================================

Este módulo gestiona toda la funcionalidad de administración de fincas olivareras,
integrando capacidades de dibujo, edición, visualización y eliminación.

Características principales:
• Dibujo interactivo de polígonos en mapa
• Cambio dinámico de capas base (calles/satélite)
• Gestión CRUD completa (crear, leer, actualizar, eliminar)
• Cálculo automático de áreas en hectáreas
• Centrado automático en fincas seleccionadas
• Validación de datos y feedback visual
• Modales de confirmación para operaciones críticas

Autor: Sistema de Monitoreo Agrícola
Versión: 2.1
Última actualización: 2025

===============================================================================
"""

# ===============================================================================
#                                 IMPORTS
# ===============================================================================

# Librerías estándar
import logging
import datetime
import json

# Framework Dash
import dash
from dash import Input, Output, State, ctx, no_update, html, dcc
import dash_bootstrap_components as dbc

# Utilidades específicas del proyecto
from src.utils.finca_store import (
    add_finca, list_fincas, get_finca, update_finca, delete_finca,
    calculate_polygon_area_hectares
)

# Configuración de logging
logger = logging.getLogger(__name__)

# ===============================================================================
#                            CONFIGURACIÓN DE MAPAS
# ===============================================================================

# URLs de servicios de mapas base
OSM_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"  # OpenStreetMap - Vista de calles
ESRI_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"  # ESRI - Vista satelital



# ===============================================================================
#                           FUNCIONES AUXILIARES
# ===============================================================================

def _center_zoom_from_polygon(geometry):
    """
    Calcula el centro óptimo y nivel de zoom para mostrar un polígono completo.
    
    Utiliza heurísticas basadas en la extensión espacial del polígono para
    determinar el nivel de zoom más apropiado que permita visualizar toda
    la geometría sin desperdiciar espacio en pantalla.
    
    Args:
        geometry (dict): Geometría GeoJSON de tipo Polygon
        
    Returns:
        tuple: ([lat, lon], zoom) - Centro y nivel de zoom calculados
    """
    try:
        # Validar geometría de entrada
        if not geometry or geometry.get("type") != "Polygon":
            return [37.2387, -3.6712], 12  # Coordenadas de Benalúa (aprox)

        # Extraer coordenadas del polígono
        coords = geometry["coordinates"][0]
        lats = [c[1] for c in coords]
        lons = [c[0] for c in coords]
        
        # Calcular centro geométrico
        center_lat = (min(lats) + max(lats)) / 2
        center_lon = (min(lons) + max(lons)) / 2

        # Determinar zoom basado en la extensión espacial
        span = max(max(lats) - min(lats), max(lons) - min(lons))
        
        if span < 0.001:
            zoom = 18      # Muy detallado - parcelas pequeñas
        elif span < 0.005:
            zoom = 16      # Detallado - fincas medianas
        elif span < 0.01:
            zoom = 15      # Normal - fincas grandes
        elif span < 0.05:
            zoom = 13      # Amplio - múltiples fincas
        else:
            zoom = 11      # Vista regional
            
        return [center_lat, center_lon], zoom
        
    except Exception:
        # Fallback a coordenadas por defecto en caso de error
        return [37.2387, -3.6712], 12


# ===============================================================================
#                        FUNCIÓN PRINCIPAL DE REGISTRO
# ===============================================================================

def register_callbacks(app):
    """
    Registra todos los callbacks para la gestión completa de fincas olivareras.
    
    Este sistema incluye:
    • Toggle de mapas base (calles/satélite)
    • Captura de dibujos y validación
    • Guardado de nuevas fincas
    • Actualización de capas y métricas
    • Gestión de listas y tablas
    • Navegación y centrado en mapa
    • Edición de propiedades
    • Eliminación con confirmación
    • Sistema de ayuda
    
    Args:
        app (Dash): Instancia de la aplicación Dash
        
    Returns:
        None: Registra los callbacks en la aplicación
    """
    logger.info("🏞️ Registrando callbacks de gestión de fincas...")

    # ===============================================================================
    #                          TOGGLE DE VISTA DE MAPA
    # ===============================================================================
    
    @app.callback(
        [
            Output("capa-base", "url"),
            Output("btn-vista-calles", "color"),
            Output("btn-vista-satelite", "color"),
        ],
        [
            Input("btn-vista-calles", "n_clicks"),
            Input("btn-vista-satelite", "n_clicks")
        ],
        prevent_initial_call=True
    )
    def toggle_map_view(n_calles, n_satelite):
        """
        Alterna entre vista de calles y vista satelital del mapa base.
        
        Args:
            n_calles (int): Número de clics en botón de vista de calles
            n_satelite (int): Número de clics en botón de vista satelital
            
        Returns:
            tuple: (url_mapa, color_btn_calles, color_btn_satelite)
        """
        triggered_button = ctx.triggered_id
        
        if triggered_button == "btn-vista-satelite":
            # Activar vista satelital
            return ESRI_URL, "outline-primary", "primary"
        else:
            # Activar vista de calles (por defecto)
            return OSM_URL, "primary", "outline-primary"

    # ===============================================================================
    #                       CAPTURA DE DIBUJO Y VALIDACIÓN
    # ===============================================================================
    
    @app.callback(
        [
            Output("store-geometria-actual", "data"),
            Output("btn-guardar-finca", "disabled"),
        ],
        [
            Input("finca-draw-control", "geojson"),
            Input("input-nombre-finca", "value"),
        ],
        prevent_initial_call=False
    )
    def on_draw_or_name_change(geojson, nombre):
        """
        Procesa cambios en el dibujo o nombre de finca y valida completitud.
        
        Monitorea:
        • Geometrías dibujadas en el mapa
        • Cambios en el campo de nombre
        • Validación de polígonos válidos
        • Habilitación/deshabilitación del botón guardar
        
        Args:
            geojson (dict): Datos GeoJSON del control de dibujo
            nombre (str): Nombre ingresado para la finca
            
        Returns:
            tuple: (geometria_almacenada, boton_deshabilitado)
        """
        geom_store = None
        
        # Procesar geometría si existe
        if geojson and geojson.get("features"):
            feature = geojson["features"][0]
            geometry = feature.get("geometry")
            
            if geometry and geometry.get("type") == "Polygon":
                # Validación opcional de área (para logging/debug)
                try:
                    coords = geometry.get("coordinates", [[]])[0]
                    area = calculate_polygon_area_hectares(coords) if coords else 0.0
                    logger.debug(f"Área calculada del polígono: {area:.2f} ha")
                except Exception as e:
                    logger.warning(f"Error calculando área: {e}")
                
                # Almacenar geometría válida
                geom_store = {
                    "type": "Feature", 
                    "geometry": geometry, 
                    "properties": {}
                }
        
        # Validar completitud: geometría Y nombre requeridos
        disabled = not (geom_store and nombre and str(nombre).strip())
        
        return geom_store, disabled

    # ===============================================================================
    #                            GUARDADO DE FINCA
    # ===============================================================================
    
    @app.callback(
        [
            Output("store-fincas-data", "data", allow_duplicate=True),
            Output("input-nombre-finca", "value", allow_duplicate=True),
            Output("store-geometria-actual", "data", allow_duplicate=True),
            Output("finca-draw-control", "geojson", allow_duplicate=True),
            Output("finca-feedback", "children", allow_duplicate=True),
        ],
        Input("btn-guardar-finca", "n_clicks"),
        [
            State("store-geometria-actual", "data"),
            State("input-nombre-finca", "value"),
        ],
        prevent_initial_call=True
    )
    def guardar_finca(n, geom, nombre):
        """
        Procesa el guardado de una nueva finca con validaciones completas.
        
        Realiza:
        • Validación de completitud de datos
        • Persistencia en almacenamiento
        • Limpieza de formulario tras éxito
        • Feedback visual al usuario
        • Actualización de timestamp para refrescar vistas
        
        Args:
            n (int): Número de clics en botón guardar
            geom (dict): Geometría almacenada temporalmente
            nombre (str): Nombre de la finca a guardar
            
        Returns:
            tuple: Estados actualizados para todos los componentes
        """
        # Ignorar si no hay clic real
        if not n:
            return no_update, no_update, no_update, no_update, no_update
        
        # Validar geometría
        if not geom or not geom.get("geometry"):
            warn = dbc.Alert(
                "❌ Dibuja la finca antes de guardar.", 
                color="warning", duration=3500
            )
            return no_update, no_update, no_update, no_update, warn
        
        # Validar nombre
        if not nombre or not str(nombre).strip():
            warn = dbc.Alert(
                "❌ Indica un nombre para la finca.", 
                color="warning", duration=3500
            )
            return no_update, no_update, no_update, no_update, warn

        try:
            # Guardar finca en almacenamiento persistente
            nueva_finca = add_finca(name=nombre.strip(), geometry=geom["geometry"])
            
            # Preparar estado post-guardado
            timestamp_update = {"ts": datetime.datetime.now().isoformat()}
            empty_geojson = {"type": "FeatureCollection", "features": []}
            success_alert = dbc.Alert(
                f"✅ Finca '{nombre.strip()}' guardada correctamente.", 
                color="success", duration=3500
            )
            
            # Limpiar formulario y actualizar vistas
            return timestamp_update, "", None, empty_geojson, success_alert

        except Exception as e:
            logger.exception("Error crítico guardando finca")
            error_alert = dbc.Alert(
                f"❌ Error al guardar: {e}", 
                color="danger", duration=6000
            )
            return no_update, no_update, no_update, no_update, error_alert

    # ===============================================================================
    #                     ACTUALIZACIÓN DE CAPA Y MÉTRICAS
    # ===============================================================================
    
    @app.callback(
        [
            Output("fincas-existentes-layer", "data"),
            Output("fincas-metrics", "children"),
        ],
        [
            Input("store-fincas-data", "data"),
            Input("interval-fincas-update", "n_intervals"),
        ],
        prevent_initial_call=False
    )
    def actualizar_capa_y_metricas(_stamp, _n):
        """
        Actualiza la capa GeoJSON del mapa y las métricas de resumen.
        
        Calcula:
        • Número total de fincas registradas
        • Superficie total en hectáreas
        • Superficie de la finca más grande
        • Preparación de features para visualización
        
        Args:
            _stamp (dict): Timestamp de actualización (no utilizado directamente)
            _n (int): Intervalos transcurridos (no utilizado directamente)
            
        Returns:
            tuple: (geojson_collection, metricas_html)
        """
        try:
            # Cargar todas las fincas desde almacenamiento
            fincas = list_fincas()
            
            # Preparar features para capa GeoJSON
            features = list(fincas)
            
            # Calcular métricas agregadas
            total_area = 0.0
            max_area = 0.0

            for finca in fincas:
                props = finca.get("properties", {}) or {}
                try:
                    area = float(props.get("area", 0) or 0)
                except (ValueError, TypeError):
                    area = 0.0
                    
                total_area += area
                max_area = max(max_area, area)

            # Generar tarjetas de métricas con diseño profesional
            metrics = html.Div([
                dbc.Row([
                    # Métrica: Número total de fincas
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("Fincas registradas", className="mb-2"),
                        html.H3(len(fincas), style={
                            'color': '#2E7D32',
                            'fontWeight': '700',
                            'margin': '0'
                        })
                    ])), md=4),
                    
                    # Métrica: Superficie total
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("Superficie total (ha)", className="mb-2"),
                        html.H3(f"{total_area:.1f}", style={
                            'color': '#FF9800',
                            'fontWeight': '700',
                            'margin': '0'
                        })
                    ])), md=4),
                    
                    # Métrica: Finca de mayor extensión
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("Finca mayor (ha)", className="mb-2"),
                        html.H3(f"{max_area:.1f}", style={
                            'color': '#9C27B0',
                            'fontWeight': '700',
                            'margin': '0'
                        })
                    ])), md=4),
                ], className="g-3")
            ], className="mb-3")

            # Retornar colección GeoJSON y métricas
            geojson_collection = {
                "type": "FeatureCollection", 
                "features": features
            }
            
            return geojson_collection, metrics

        except Exception as e:
            logger.exception("Error crítico generando capa/métricas")
            error_alert = dbc.Alert(
                f"Error cargando métricas: {e}", 
                color="danger"
            )
            empty_geojson = {
                "type": "FeatureCollection", 
                "features": []
            }
            return empty_geojson, error_alert

    # ===============================================================================
    #                        LISTA DE GESTIÓN DE FINCAS
    # ===============================================================================
    
    @app.callback(
        Output("lista-fincas-gestion", "children"),
        [
            Input("store-fincas-data", "data"),
            Input("interval-fincas-update", "n_intervals"),
        ],
        prevent_initial_call=False
    )
    def refrescar_lista(_stamp, _n):
        """
        Genera lista interactiva de fincas con opciones de gestión.
        
        Cada finca se presenta como una tarjeta con:
        • Nombre y superficie
        • Botones de acción (editar, ver en mapa, eliminar)
        • Diseño responsivo y profesional
        • Identificadores únicos para callbacks
        
        Args:
            _stamp (dict): Timestamp de actualización (no utilizado directamente)
            _n (int): Intervalos transcurridos (no utilizado directamente)
            
        Returns:
            list|Alert: Lista de tarjetas o alerta si no hay datos
        """
        try:
            # Cargar fincas desde almacenamiento
            fincas = list_fincas()
            
            # Estado vacío - mostrar mensaje informativo
            if not fincas:
                return dbc.Alert(
                    "No hay fincas registradas. Dibuja y guarda tu primera finca.", 
                    color="info"
                )

            # Construir tarjetas para cada finca
            items = []
            for finca in fincas:
                finca_id = finca.get("id")
                props = finca.get("properties", {}) or {}
                name = props.get("name", "Sin nombre")
                
                # Extraer área con validación
                try:
                    area = float(props.get("area", 0) or 0)
                except (ValueError, TypeError):
                    area = 0.0

                # Construir tarjeta individual
                card = dbc.Card(
                    dbc.CardBody([
                        dbc.Row([
                            # Información de la finca
                            dbc.Col([
                                html.B(name, className="mb-1"),
                                html.Div([
                                    html.Small(f"{area:.2f} ha", className="text-muted")
                                ])
                            ], md=8),
                            
                            # Botones de acción
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button(
                                        [html.I(className="fas fa-edit me-1"), "Editar"],
                                        id={"type": "btn-editar-finca", "index": finca_id},
                                        color="primary", size="sm"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-map-marker-alt me-1"), "Mapa"],
                                        id={"type": "btn-ir-finca", "index": finca_id},
                                        color="info", size="sm"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-trash me-1"), "Eliminar"],
                                        id={"type": "btn-eliminar-finca", "index": finca_id},
                                        color="danger", size="sm", outline=True
                                    ),
                                ], size="sm")
                            ], md=4, className="text-end"),
                        ], align="center")
                    ]),
                    className="mb-2 shadow-sm"
                )
                items.append(card)

            return items

        except Exception as e:
            logger.exception("Error construyendo lista de fincas")
            return dbc.Alert(
                f"Error cargando listado: {e}", 
                color="danger"
            )

    # ===============================================================================
    #                         TABLA SIMPLE (COMPATIBILIDAD)
    # ===============================================================================
    
    @app.callback(
        Output("tabla-fincas-registradas", "children"),
        [
            Input("store-fincas-data", "data"),
            Input("interval-fincas-update", "n_intervals"),
        ],
        prevent_initial_call=False
    )
    def refrescar_tabla(_stamp, _n):
        """
        Genera tabla simple de fincas para compatibilidad con layouts antiguos.
        
        Presenta información básica:
        • Nombre de la finca
        • Superficie en hectáreas
        • Formato de lista simple
        
        Args:
            _stamp (dict): Timestamp de actualización (no utilizado directamente)
            _n (int): Intervalos transcurridos (no utilizado directamente)
            
        Returns:
            ListGroup|Alert: Lista de elementos o alerta si no hay datos
        """
        try:
            # Cargar fincas desde almacenamiento
            fincas = list_fincas()
            
            # Estado vacío
            if not fincas:
                return dbc.Alert(
                    "No hay fincas registradas todavía.", 
                    color="info"
                )

            # Construir filas de tabla simple
            rows = []
            for finca in fincas:
                props = finca.get("properties", {}) or {}
                name = props.get("name", "Sin nombre")
                
                # Extraer área con validación
                try:
                    area = float(props.get("area", 0) or 0)
                except (ValueError, TypeError):
                    area = 0.0
                
                # Crear elemento de lista
                row = dbc.ListGroupItem([
                    html.B(name),
                    html.Span(f" • {area:.2f} ha", className="text-muted ms-2")
                ])
                rows.append(row)
            
            return dbc.ListGroup(rows)

        except Exception as e:
            logger.exception("Error construyendo tabla de fincas")
            return dbc.Alert(
                f"Error cargando listado: {e}", 
                color="danger"
            )

    # ===============================================================================
    #                         NAVEGACIÓN EN MAPA
    # ===============================================================================
    
    @app.callback(
        [
            Output("mapa-fincas", "center"),
            Output("mapa-fincas", "zoom"),
        ],
        Input({"type": "btn-ir-finca", "index": dash.ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def ver_en_mapa(n_clicks_list):
        """
        Centra y ajusta el mapa para mostrar una finca específica.
        
        Utiliza algoritmo inteligente para:
        • Calcular centro geométrico de la finca
        • Determinar nivel de zoom óptimo
        • Ajustar vista para mostrar toda la geometría
        
        Args:
            n_clicks_list (list): Lista de clics en botones "Ver en mapa"
            
        Returns:
            tuple: (centro, zoom) o no_update si no hay acción
        """
        # Verificar si hay clics válidos
        if not n_clicks_list or not any(n_clicks_list):
            return no_update, no_update
            
        # Identificar botón activado
        triggered_button = ctx.triggered_id
        
        if isinstance(triggered_button, dict) and triggered_button.get("type") == "btn-ir-finca":
            finca_id = triggered_button.get("index")
            
            # Cargar datos de la finca
            finca = get_finca(finca_id)
            
            if finca and finca.get("geometry"):
                # Calcular centro y zoom óptimos
                center, zoom = _center_zoom_from_polygon(finca["geometry"])
                logger.debug(f"Centrando mapa en finca {finca_id}: {center}, zoom {zoom}")
                return center, zoom
        
        return no_update, no_update

    # ===============================================================================
    #                          MODAL DE EDICIÓN
    # ===============================================================================
    
    @app.callback(
        [
            Output("modal-editar-finca", "is_open"),
            Output("input-nuevo-nombre-finca", "value"),
            Output("store-edit-target", "data"),
        ],
        [
            Input({"type": "btn-editar-finca", "index": dash.ALL}, "n_clicks"),
            Input("modal-editar-cancelar", "n_clicks"),
        ],
        State("store-edit-target", "data"),
        prevent_initial_call=True
    )
    def abrir_modal_editar(n_clicks_list, cancelar, current_target):
        """
        Controla la apertura y cierre del modal de edición de fincas.
        
        Gestiona:
        • Apertura del modal al hacer clic en "Editar"
        • Carga de datos actuales de la finca
        • Cierre del modal al cancelar
        • Validación de existencia de finca
        
        Args:
            n_clicks_list (list): Lista de clics en botones "Editar"
            cancelar (int): Clics en botón cancelar
            current_target (dict): Datos de finca actualmente en edición
            
        Returns:
            tuple: (modal_abierto, nombre_actual, datos_objetivo)
        """
        triggered_button = ctx.triggered_id
        
        # Sin trigger válido, mantener estado
        if not triggered_button:
            return no_update, no_update, no_update
            
        # Cancelar edición - cerrar modal y limpiar
        if triggered_button == "modal-editar-cancelar":
            return False, "", None

        # Procesar clic en botón editar
        if (isinstance(triggered_button, dict) and 
            triggered_button.get("type") == "btn-editar-finca"):
            
            # Verificar que hay clics válidos
            if not n_clicks_list or not any(n_clicks_list):
                return no_update, no_update, no_update
                
            finca_id = triggered_button.get("index")
            
            try:
                # Cargar datos de la finca a editar
                finca = get_finca(finca_id)
                if not finca:
                    logger.warning(f"Finca {finca_id} no encontrada para edición")
                    return no_update, no_update, no_update
                
                # Extraer nombre actual
                props = finca.get("properties", {}) or {}
                nombre_actual = props.get("name", "Sin nombre")
                
                # Preparar datos para edición
                target_data = {
                    "id": finca_id, 
                    "nombre_original": nombre_actual
                }
                
                return True, nombre_actual, target_data
                
            except Exception as e:
                logger.exception(f"Error abriendo modal de edición para finca {finca_id}")
                return no_update, no_update, no_update

        return no_update, no_update, no_update

    @app.callback(
        [
            Output("finca-feedback", "children", allow_duplicate=True),
            Output("modal-editar-finca", "is_open", allow_duplicate=True),
            Output("store-fincas-data", "data", allow_duplicate=True),
            Output("store-edit-target", "data", allow_duplicate=True),
        ],
        Input("modal-editar-confirmar", "n_clicks"),
        [
            State("input-nuevo-nombre-finca", "value"),
            State("store-edit-target", "data"),
        ],
        prevent_initial_call=True
    )
    def confirmar_edicion(n, nuevo_nombre, target):
        """
        Procesa la confirmación de edición de una finca.
        
        Realiza:
        • Validación del nuevo nombre
        • Comparación con nombre original
        • Actualización en almacenamiento
        • Actualización de timestamp
        • Feedback visual al usuario
        
        Args:
            n (int): Número de clics en confirmar
            nuevo_nombre (str): Nuevo nombre para la finca
            target (dict): Datos de la finca objetivo
            
        Returns:
            tuple: Estados actualizados para feedback, modal, store y target
        """
        # Validar precondiciones
        if not n or not target or not target.get("id"):
            return no_update, no_update, no_update, no_update

        finca_id = target["id"]
        nombre_original = target.get("nombre_original", "")
        
        # Validar nuevo nombre no vacío
        if not nuevo_nombre or not nuevo_nombre.strip():
            error_alert = dbc.Alert(
                "❌ El nombre no puede estar vacío.", 
                color="danger", duration=3500
            )
            return error_alert, no_update, no_update, no_update

        nuevo_nombre = nuevo_nombre.strip()
        
        # Verificar si realmente hay cambios
        if nuevo_nombre == nombre_original:
            info_alert = dbc.Alert(
                "ℹ️ No se realizaron cambios.", 
                color="info", duration=2500
            )
            return info_alert, False, no_update, None

        try:
            # Cargar finca actual desde almacenamiento
            finca = get_finca(finca_id)
            if not finca:
                error_alert = dbc.Alert(
                    "❌ No se encontró la finca.", 
                    color="danger", duration=3500
                )
                return error_alert, False, no_update, None
                
            # Aplicar actualización de nombre y timestamp
            finca["properties"]["name"] = nuevo_nombre
            finca["properties"]["updated_at"] = (
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            
            # Persistir cambios
            update_finca(finca_id, finca)
            
            # Preparar confirmación de éxito
            success_alert = dbc.Alert(
                f"✅ Finca renombrada de '{nombre_original}' a '{nuevo_nombre}'.", 
                color="success", duration=4000
            )
            timestamp_update = {"ts": datetime.datetime.now().isoformat()}
            
            return success_alert, False, timestamp_update, None
            
        except Exception as e:
            logger.exception(f"Error crítico actualizando finca {finca_id}")
            error_alert = dbc.Alert(
                f"❌ Error actualizando finca: {e}", 
                color="danger", duration=5000
            )
            return error_alert, no_update, no_update, no_update

    # ===============================================================================
    #                    MODAL DE CONFIRMACIÓN DE ELIMINACIÓN
    # ===============================================================================
    
    @app.callback(
        [
            Output("modal-confirmacion-eliminar", "is_open"),
            Output("modal-confirmacion-contenido", "children"),
            Output("store-delete-target", "data"),
        ],
        [
            Input({"type": "btn-eliminar-finca", "index": dash.ALL}, "n_clicks"),
            Input("modal-cancelar", "n_clicks"),
        ],
        State("store-delete-target", "data"),
        prevent_initial_call=True
    )
    def abrir_modal_eliminar(n_clicks_list, cancelar, current_target):
        """
        Controla el modal de confirmación para eliminación de fincas.
        
        Proporciona:
        • Confirmación explícita antes de eliminar
        • Visualización del nombre de finca a eliminar
        • Advertencia sobre acción irreversible
        • Opción de cancelar operación
        
        Args:
            n_clicks_list (list): Lista de clics en botones "Eliminar"
            cancelar (int): Clics en botón cancelar
            current_target (dict): Datos de finca actualmente seleccionada
            
        Returns:
            tuple: (modal_abierto, contenido_modal, datos_objetivo)
        """
        triggered_button = ctx.triggered_id
        
        # Sin trigger válido, mantener estado
        if not triggered_button:
            return no_update, no_update, no_update
            
        # Cancelar eliminación - cerrar modal y limpiar
        if triggered_button == "modal-cancelar":
            return False, no_update, None

        # Procesar clic en botón eliminar
        if (isinstance(triggered_button, dict) and 
            triggered_button.get("type") == "btn-eliminar-finca"):
            
            # Verificar que hay clics válidos
            if not n_clicks_list or not any(n_clicks_list):
                return no_update, no_update, no_update
                
            finca_id = triggered_button.get("index")
            
            try:
                # Cargar datos de la finca a eliminar
                finca = get_finca(finca_id)
                nombre = "Sin nombre"  # Valor por defecto
                
                if finca:
                    props = finca.get("properties", {}) or {}
                    nombre = props.get("name", "Sin nombre")
                
                # Crear contenido del modal de confirmación
                contenido = html.Div([
                    html.P(
                        "¿Seguro que quieres eliminar esta finca? Esta acción no se puede deshacer.",
                        className="mb-3"
                    ),
                    html.Div([
                        html.Strong("Finca a eliminar:"),
                        html.P(nombre, className="fw-bold text-danger mb-0 mt-2")
                    ], className="border rounded p-3 bg-light")
                ])
                
                target_data = {"id": finca_id}
                
                return True, contenido, target_data
                
            except Exception as e:
                logger.exception(f"Error abriendo modal de eliminación para finca {finca_id}")
                return no_update, no_update, no_update

        return no_update, no_update, no_update

    @app.callback(
        [
            Output("finca-feedback", "children", allow_duplicate=True),
            Output("modal-confirmacion-eliminar", "is_open", allow_duplicate=True),
            Output("store-fincas-data", "data", allow_duplicate=True),
            Output("store-delete-target", "data", allow_duplicate=True),
        ],
        Input("modal-confirmar-eliminar", "n_clicks"),
        State("store-delete-target", "data"),
        prevent_initial_call=True
    )
    def confirmar_eliminacion(n, target):
        """
        Ejecuta la eliminación confirmada de una finca.
        
        Procesos:
        • Validación de datos objetivo
        • Obtención de nombre para feedback
        • Eliminación del almacenamiento
        • Actualización de timestamp
        • Feedback de confirmación
        
        Args:
            n (int): Número de clics en confirmar eliminación
            target (dict): Datos de la finca a eliminar
            
        Returns:
            tuple: Estados actualizados para feedback, modal, store y target
        """
        # Validar precondiciones
        if not n or not target or not target.get("id"):
            return no_update, no_update, no_update, no_update

        try:
            finca_id = target["id"]
            
            # Obtener nombre para feedback antes de eliminar
            finca = get_finca(finca_id)
            nombre = "Sin nombre"  # Valor por defecto
            
            if finca:
                props = finca.get("properties", {}) or {}
                nombre = props.get("name", "Sin nombre")
            
            # Ejecutar eliminación
            delete_finca(finca_id)
            logger.info(f"Finca '{nombre}' (ID: {finca_id}) eliminada exitosamente")
            
            # Preparar confirmación de éxito
            success_alert = dbc.Alert(
                f"🗑️ Finca '{nombre}' eliminada correctamente.", 
                color="success", duration=3500
            )
            timestamp_update = {"ts": datetime.datetime.now().isoformat()}
            
            return success_alert, False, timestamp_update, None
            
        except Exception as e:
            logger.exception(f"Error crítico eliminando finca {target.get('id')}")
            error_alert = dbc.Alert(
                f"❌ Error eliminando finca: {e}", 
                color="danger", duration=6000
            )
            return error_alert, no_update, no_update, no_update

    # ===============================================================================
    #                             MODAL DE AYUDA
    # ===============================================================================
    
    @app.callback(
        Output("modal-ayuda-fincas", "is_open"),
        [
            Input("btn-ayuda-fincas", "n_clicks"), 
            Input("modal-ayuda-cerrar", "n_clicks")
        ],
        prevent_initial_call=True
    )
    def toggle_help_modal(open_clicks, close_clicks):
        """
        Controla la apertura y cierre del modal de ayuda.
        
        Args:
            open_clicks (int): Clics en botón de ayuda
            close_clicks (int): Clics en botón cerrar
            
        Returns:
            bool: Estado del modal (abierto/cerrado)
        """
        triggered_button = ctx.triggered_id
        
        if triggered_button == "btn-ayuda-fincas":
            return True
        else:
            return False

    logger.info("✅ Todos los callbacks de gestión de fincas registrados exitosamente")
