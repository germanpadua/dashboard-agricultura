import pandas as pd
import geopandas as gpd
import json

def load_kml(path_kml: str) -> dict:
    gdf = gpd.read_file(path_kml, driver="KML")
    return json.loads(gdf.to_json())

def load_data(path_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, sep=";", parse_dates=["Dates"])
    return df.sort_values("Dates")
