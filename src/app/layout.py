import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_leaflet as dl

def build_layout(df, kml_geojson):
    return html.Div(
        [
            dbc.Row(
                [
                    # Columna del mapa
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                dl.Map(
                                    children=[
                                        # Capa satélite ESRI
                                        dl.TileLayer(
                                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                            attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics"
                                        ),
                                        # GeoJSON del KML
                                        dl.GeoJSON(
                                            data=kml_geojson,
                                            options=dict(style=dict(weight=2, color="#FF5722", fillOpacity=0.3)),
                                            zoomToBoundsOnClick=True
                                        ),
                                    ],
                                    style={"width": "100%", "height": "60vh"},
                                    center=[37.2387, -3.6712],
                                    zoom=12,
                                )
                            ),
                            className="rounded-3 shadow-sm mb-4 card-graph",
                        ),
                        md=4,
                    ),

                    # Columna central: selectores + gráficas
                    dbc.Col(
                        dbc.Card(
                            [
                                # Cabecera con DatePickerRange y Dropdown
                                dbc.CardHeader(
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.DatePickerRange(
                                                    id="shared-date-range",
                                                    start_date=df["Dates"].dt.date.min(),
                                                    end_date=df["Dates"].dt.date.max(),
                                                    display_format="DD/MM/YYYY",
                                                    className="rounded-pill px-3 py-1",
                                                    style={"minWidth": "180px"},
                                                ),
                                                xs="auto",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="shared-freq-dropdown",
                                                    options=[
                                                        {"label": "Días",          "value": "D"},
                                                        {"label": "Semanas",       "value": "W"},
                                                        {"label": "Meses",         "value": "ME"},
                                                        {"label": "Cuatrimestres", "value": "4ME"},
                                                    ],
                                                    value="D",
                                                    clearable=False,
                                                    className="rounded-pill px-3 py-1",
                                                    style={"minWidth": "120px"},
                                                ),
                                                xs="auto",
                                                className="ms-auto",
                                            ),
                                        ],
                                        align="center",
                                        justify="between",
                                        className="g-3",
                                    )
                                ),
                                # Body con las dos gráficas
                                dbc.CardBody(
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="fig-soil",
                                                    config={"displayModeBar": False},
                                                    style={"height": "40vh"},
                                                ),
                                                width=12,
                                            ),
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="fig-temp",
                                                    config={"displayModeBar": False},
                                                    style={"height": "40vh"},
                                                ),
                                                width=12,
                                            ),
                                        ],
                                        className="g-4",
                                    )
                                ),
                            ],
                            className="rounded-3 shadow-sm mb-4 card-graph",
                        ),
                        md=5,
                    ),

                    # Columna derecha: notificaciones y clima
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H5("Notificaciones y Alertas", className="mb-0")),
                                    dbc.CardBody(html.Div("Aquí irán tus notificaciones...", style={"minHeight": "150px"})),
                                ],
                                className="rounded-3 shadow-sm mb-4 card-graph",
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        dcc.Tabs(
                                            id="tabs-clima",
                                            value="hoy",
                                            className="nav nav-tabs",
                                            children=[
                                                dcc.Tab(label="Hoy", value="hoy"),
                                                dcc.Tab(label="Semana", value="semana"),
                                            ],
                                        )
                                    ),
                                    dbc.CardBody(html.Div(id="weather-content", style={"minHeight": "150px"})),
                                ],
                                className="rounded-3 shadow-sm card-graph",
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="g-4",
            ),
        ],
        style={"margin": "2rem"},
    )
