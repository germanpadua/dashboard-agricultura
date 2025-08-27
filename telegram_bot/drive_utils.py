from googleapiclient.http import MediaFileUpload

# Esta variable será definida en main.py
DRIVE_FOLDER_ID = None

def get_or_create_shared_folder(folder_name, user_email, drive_service):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    res = drive_service.files().list(q=query, fields="files(id)").execute()
    files = res.get("files", [])

    if files:
        folder_id = files[0]["id"]
    else:
        metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        file = drive_service.files().create(body=metadata, fields='id').execute()
        folder_id = file.get('id')

    # Compartir con tu cuenta
    drive_service.permissions().create(
        fileId=folder_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': user_email},
        sendNotificationEmail=False
    ).execute()

    return folder_id

def upload_to_drive(filename, drive_service, folder_id=None):
    media = MediaFileUpload(filename, mimetype='application/octet-stream', resumable=False)
    metadata = {'name': filename}
    if folder_id:
        metadata['parents'] = [folder_id]

    res = drive_service.files().list(q=f"name='{filename}' and trashed=false", spaces='drive', fields='files(id)').execute()
    files = res.get('files', [])

    if files:
        file_id = files[0]['id']
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file = drive_service.files().create(body=metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')

    drive_service.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    info = drive_service.files().get(fileId=file_id, fields='webViewLink').execute()
    return info.get('webViewLink')
