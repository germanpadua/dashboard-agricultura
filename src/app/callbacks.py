from dash.dependencies import Input, Output
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from .plots import make_soil_figure, make_temp_figure


def render_weather(tab: str, df: pd.DataFrame) -> html.Div:
    """
    Genera el contenido del panel de clima según la pestaña seleccionada ('hoy' o 'semana').

    Args:
        tab: 'hoy' para datos del último registro, 'semana' para 7 días.
        df: DataFrame con columnas ['Dates','Air_Temp','Rain','Wind_Speed','Wind_Dir','Air_Relat_Hum'].
    Returns:
        Un Div de Dash con tarjetas de clima.
    """
    dias = {'Mon':'lun', 'Tue':'mar', 'Wed':'mié', 'Thu':'jue', 'Fri':'vie', 'Sat':'sáb', 'Sun':'dom'}

    if tab == 'hoy':
        latest = df.iloc[-1]
        fecha = latest['Dates'].strftime("%d/%m/%Y %H:%M")
        info = [
            ("📅 Fecha", fecha),
            ("🌡️ Temperatura", f"{latest['Air_Temp']:.1f} °C"),
            ("🌧️ Precipitación", f"{latest['Rain']:.1f} mm"),
            ("💨 Viento", f"{latest['Wind_Speed']:.1f} m/s, {int(latest['Wind_Dir'])}°"),
            ("🌬️ Humedad", f"{latest['Air_Relat_Hum']:.0f} %"),
        ]
        cards = []
        for title, value in info:
            cards.append(
                dbc.Card([
                    dbc.CardHeader(title, className="fw-bold text-center"),
                    dbc.CardBody(html.H4(value, className="card-title text-center mb-0"))
                ], className="shadow-sm", style={"minWidth": "10rem", "border": "none"})
            )
        return html.Div([dbc.Row([dbc.Col(c, width="auto") for c in cards], className="g-4 justify-content-center")])

    # pestaña 'semana'
    now = pd.Timestamp.now().normalize()
    monday = now - pd.Timedelta(days=now.weekday())
    dfw = df[(df['Dates'] >= monday) & (df['Dates'] < monday + pd.Timedelta(days=7))]
    if dfw.empty:
        last = df['Dates'].max()
        dfw = df[(df['Dates'] >= last - pd.Timedelta(days=6)) & (df['Dates'] <= last)]

    agg = {'Air_Temp': ['min', 'max'], 'Rain': 'sum'}
    dfg = dfw.set_index('Dates').resample('D').agg(agg)
    dfg.columns = ['_'.join(col) for col in dfg.columns]

    cards = []
    for ts, row in dfg.iterrows():
        dia_abbr = dias.get(ts.strftime('%a'), ts.strftime('%a'))
        numero = ts.day
        t_max = f"{row['Air_Temp_max']:.0f}°"
        t_min = f"{row['Air_Temp_min']:.0f}°"
        rain = f"{row['Rain_sum']:.1f} mm"
        icon = '🌧️' if row['Rain_sum'] >= 5 else ('⛅' if row['Rain_sum'] > 0 else '☀️')
        cards.append(html.Div([
            html.Div(f"{dia_abbr} {numero}", className="fw-bold mb-1"),
            html.Div(icon, style={"fontSize": "1.6rem", "lineHeight": "1"}),
            html.Div(t_max, className="small fw-semibold"),
            html.Div(t_min, className="small text-muted"),
            html.Div(rain, className="small")
        ], className="text-center p-2", style={
            "minWidth": "70px",
            "borderRadius": "0.75rem",
            "backgroundColor": "#f8f9fa",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
        }))

    return html.Div(cards, style={"display": "flex", "gap": "8px", "overflowX": "auto", "padding": "4px"})


def register_callbacks(app, df: pd.DataFrame):
    @app.callback(
        Output("fig-soil", "figure"),
        Output("fig-temp", "figure"),
        Input("shared-date-range", "start_date"),
        Input("shared-date-range", "end_date"),
        Input("shared-freq-dropdown", "value"),
    )
    def update_graphs(start_date, end_date, freq):
        dff = df[(df["Dates"] >= start_date) & (df["Dates"] <= end_date)]
        soil = dff.set_index("Dates").resample(freq).agg({"Rain": "sum", "Air_Relat_Hum": "mean"})
        soil.columns = ["Rain_sum", "Air_Relat_Hum_mean"]
        temp = dff.set_index("Dates").resample(freq).agg({"Air_Temp": ["min", "mean", "max"]})
        temp.columns = ["Air_Temp_min", "Air_Temp_mean", "Air_Temp_max"]
        return make_soil_figure(soil), make_temp_figure(temp)

    @app.callback(
        Output("weather-content", "children"),
        Input("tabs-clima", "value")
    )
    def weather_callback(tab):
        return render_weather(tab, df)
