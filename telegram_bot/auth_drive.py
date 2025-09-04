import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    token_path = "token.pickle"
    creds_path = "credentials.json"

    # Cargar token ya existente
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Si el token está caducado pero se puede refrescar → refrescar
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # re-guardar el token actualizado
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        except RefreshError:
            print("⚠️ Refresh token inválido. Borra token.pickle y vuelve a generarlo en el host.")
            raise

    # Si no hay credenciales válidas → error controlado
    if not creds or not creds.valid:
        raise RuntimeError(
            "No se encontró un token válido. "
            "Genera token.pickle fuera de Docker y móntalo en el contenedor."
        )

    return build('drive', 'v3', credentials=creds)
