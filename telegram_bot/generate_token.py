import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']  # igual que en tu auth_drive.py

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)  # se abrirá tu navegador local para autorizar
with open('token.pickle', 'wb') as f:
    pickle.dump(creds, f)
print("✅ token.pickle creado junto a credentials.json")