import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import requests
from io import BytesIO
from PIL import Image
import os
import csv
from datetime import datetime

from config import TELEGRAM_TOKEN
from exif_utils import get_exif_data, get_gps_info, convert_to_degrees
from kml_utils import add_placemark, write_kml_file, placemarks
from drive_utils import upload_to_drive

bot = telebot.TeleBot(TELEGRAM_TOKEN)

drive_service = None  # Inicializado desde main.py
DRIVE_FOLDER_ID = None
user_state = {} 
CSV_FILENAME = "infecciones.csv"
KML_FILENAME = "placemarks.kml"

GRADOS = {
    "1": "Muy baja",
    "2": "Baja",
    "3": "Moderada",
    "4": "Alta",
    "5": "Muy alta"
}

def crear_botones_grado():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"{k} - {v}", callback_data=f"grado_{k}") for k, v in GRADOS.items()]
    keyboard.add(*buttons)
    return keyboard

# Inicializar CSV si no existe
def init_csv():
    if not os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['nombre_imagen', 'nombre_kml', 'lat', 'lon', 'timestamp', 'grado_infeccion'])

init_csv()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, (
        "👋 ¡Hola! Este bot registra infecciones vegetales por Repilo.\n\n"
        "📷 Envía una imagen como documento o foto.\n"
        "📍 Si tiene GPS, se guardará. Si no, se te pedirá la ubicación.\n"
        "🩺 Luego, indica el grado de infección (1-5).\n"
        "ℹ️ Usa /tutorial si tienes dudas."
    ))

@bot.message_handler(commands=['tutorial'])
def send_tutorial(message):
    bot.reply_to(message, (
        "📷 **¿Cómo enviar correctamente?**\n\n"
        "1️⃣ Toca el clip 📎 en la parte inferior derecha en este chat de Telegram\n"
        "2️⃣ Selecciona Archivo y luego Galería\n"
        "3️⃣ Elige la imagen y envíala\n"
        "4️⃣ Si la imagen no tiene GPS, envía tu ubicación actual tocando primero 📎 y luego el icono de ubicación\n"
        "5️⃣ Finalmente, indica el grado de infección (1 a 5)\n:"
        "    1: Muy baja\n"
        "    2: Baja\n"
        "    3: Moderada\n"
        "    4: Alta\n"
        "    5: Muy alta\n"
    ))

@bot.message_handler(content_types=['photo', 'document'])
def handle_image(message):
    chat_id = message.chat.id
    bot.reply_to(message, "✅ Imagen recibida.")

    # Obtener imagen y nombre temporal
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        filename = f"photo_{file_id}.jpg"
    else:
        if not message.document.mime_type.startswith('image/'):
            return
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        filename = message.document.file_name

    url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
    response = requests.get(url)
    image_path = f"temp_{filename}"
    with open(image_path, 'wb') as f:
        f.write(response.content)

    img = Image.open(BytesIO(response.content))
    exif = get_exif_data(img)
    gps = get_gps_info(exif)
    timestamp = exif.get("DateTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if gps.get('GPSLatitude'):
        lat = convert_to_degrees(gps['GPSLatitude'])
        if gps.get('GPSLatitudeRef') != 'N': lat = -lat
        lon = convert_to_degrees(gps['GPSLongitude'])
        if gps.get('GPSLongitudeRef') != 'E': lon = -lon
        step = 'waiting_label'
    else:
        lat = lon = None
        step = 'waiting_location'
        bot.reply_to(message, "📍 No se encontró GPS en la imagen. Por favor, envía tu ubicación actual.")

    user_state[chat_id] = {
        "nombre_imagen": image_path,
        "timestamp": timestamp,
        "lat": lat,
        "lon": lon,
        "step": step
    }

    

    if step == 'waiting_label':
        bot.send_message(chat_id, "🩺 Indica el grado de infección:", reply_markup=crear_botones_grado())

@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)

    if not state or state['step'] != 'waiting_location':
        bot.reply_to(message, "⚠️ Envía primero una imagen antes de compartir tu ubicación.")
        return

    state['lat'] = message.location.latitude
    state['lon'] = message.location.longitude
    state['step'] = 'waiting_label'

    bot.reply_to(message, "✅ Ubicación recibida.")
    bot.send_message(chat_id, "🩺 Ahora indica el grado de infección:", reply_markup=crear_botones_grado())

@bot.callback_query_handler(func=lambda call: call.data.startswith("grado_"))
def handle_severity_callback(call):
    chat_id = call.message.chat.id
    state = user_state.get(chat_id)

    if not state or state['step'] != 'waiting_label':
        bot.answer_callback_query(call.id, "⚠️ No estamos esperando un grado de infección.")
        return

    severity = call.data.split("_")[1]
    grado_txt = GRADOS.get(severity, 'Desconocido')

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="📤 Mensaje recibido. Subiendo datos..."
    )


    ts = datetime.strptime(state['timestamp'], "%Y-%m-%d %H:%M:%S")
    name_base = f"{ts.strftime('%Y-%m-%d_%H-%M-%S')}_g{severity}"
    if state['lat'] and state['lon']:
        name_base += f"_{round(state['lat'], 5)}_{round(state['lon'], 5)}"

    new_image_name = name_base + ".png"
    os.rename(state['nombre_imagen'], new_image_name)

    # Añadir al KML
    if state['lat'] and state['lon']:
        add_placemark(name_base, state['lon'], state['lat'])
        write_kml_file()
        upload_to_drive(KML_FILENAME, drive_service, DRIVE_FOLDER_ID)

    # Añadir al CSV
    file_exists = os.path.isfile(CSV_FILENAME)
    with open(CSV_FILENAME, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['imagen', 'nombre_kml', 'latitud', 'longitud', 'fecha', 'grado'])
        writer.writerow([new_image_name, name_base, state['lat'], state['lon'], state['timestamp'], severity])

    upload_to_drive(CSV_FILENAME, drive_service, DRIVE_FOLDER_ID)
    upload_to_drive(new_image_name, drive_service, DRIVE_FOLDER_ID)

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"✅ Registro completado.\n📸 Imagen subida\n📍 Coordenadas: {state['lat']}, {state['lon']}\n🩺 Infección: {severity} ({grado_txt})"
    )
    user_state.pop(chat_id)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def fallback_message(message):
    bot.reply_to(message, (
        "⚠️ No entendí tu mensaje. Por favor, envía una imagen o usa /tutorial para ayuda.\n\n"
    ))

def run_bot(ds, folder_id):
    global drive_service, DRIVE_FOLDER_ID
    drive_service = ds
    DRIVE_FOLDER_ID = folder_id
    bot.polling()
