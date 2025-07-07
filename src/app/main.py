import dash
import dash_bootstrap_components as dbc
from .data_loader import load_data, load_kml
from .layout import build_layout
from .callbacks import register_callbacks

# Paths relativos
CSV_PATH = "data/raw/merged_output.csv"
KML_PATH = "assets/Prueba Bot.kml"

# Cargamos datos
df = load_data(CSV_PATH)
kml_geojson = load_kml(KML_PATH)

# Creamos la app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = build_layout(df, kml_geojson)

# Registramos callbacks
register_callbacks(app, df)

if __name__ == "__main__":
    app.run(debug=True)
