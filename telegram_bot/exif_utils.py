from PIL import Image, ExifTags

def get_exif_data(image):
    exif_data = {}
    try:
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                exif_data[decoded] = value
    except Exception as e:
        print("Error al obtener EXIF:", e)
    return exif_data

def get_gps_info(exif_data):
    gps_info = {}
    if "GPSInfo" in exif_data:
        for key in exif_data["GPSInfo"]:
            decode = ExifTags.GPSTAGS.get(key, key)
            gps_info[decode] = exif_data["GPSInfo"][key]
    return gps_info

def convert_to_degrees(value):
    d, m, s = float(value[0]), float(value[1]), float(value[2])
    return d + (m / 60.0) + (s / 3600.0)
