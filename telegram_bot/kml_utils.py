placemarks = []

def add_placemark(name, lon, lat):
    pm = (
        f"  <Placemark>\n"
        f"    <name>{name}</name>\n"
        f"    <Point><coordinates>{lon},{lat},0</coordinates></Point>\n"
        f"  </Placemark>\n"
    )
    placemarks.append(pm)

def write_kml_file(filename="placemarks.kml"):
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n  <Document>\n'
    footer = '  </Document>\n</kml>'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(header)
        for pm in placemarks:
            f.write(pm)
        f.write(footer)
