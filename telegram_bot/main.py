from bot import run_bot
from auth_drive import get_drive_service

DRIVE_FOLDER_ID = "1N7DHpYhhoqVgLD-rgsuUP9Q_5vyHC07W"  # ID de tu carpeta en Drive

if __name__ == "__main__":
    drive_service = get_drive_service()
    run_bot(drive_service, DRIVE_FOLDER_ID)
