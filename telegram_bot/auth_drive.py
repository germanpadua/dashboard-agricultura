import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

# Scope de Drive (permite acceso completo a archivos del usuario autenticado)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None

    # Usa token guardado si existe
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, iniciar login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # Si el refresh token falla, eliminar el token y reautenticar
                print("Token expirado, reautenticando...")
                if os.path.exists('token.pickle'):
                    os.remove('token.pickle')
                creds = None
        
        # Si no hay credenciales o falló la renovación, obtener nuevas
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Guarda el token para futuras ejecuciones
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Devuelve el servicio de Google Drive
    return build('drive', 'v3', credentials=creds)
