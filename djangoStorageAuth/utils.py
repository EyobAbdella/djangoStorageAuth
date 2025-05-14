
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .models import OAuthTokens


def load_google_credentials(user_id):
    oauth_tokens = OAuthTokens.objects.filter(user_id=user_id).only("google_access", "google_refresh").first()
    if not oauth_tokens:
        return None
    credentials = Credentials(
        token=oauth_tokens.google_access,
        refresh_token=oauth_tokens.google_refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ],
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        OAuthTokens.objects.filter(user=user_id).update(google_access=credentials.token)

    return credentials


def list_drive_files(user_id, mime_type=None):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return []

    drive_service = build("drive", "v3", credentials=credentials)

    query = "trashed=false"
    if mime_type:
        query += f" and mimeType='{mime_type}'"

    response = drive_service.files().list(
        q=query,
        spaces='drive',
        fields="files(id, name, mimeType)",
        pageSize=100,
    ).execute()

    return response.get("files", [])


def list_google_drive_folders(user_id):
    return list_drive_files(user_id, mime_type="application/vnd.google-apps.folder")


def create_drive_file(user_id, title="Untitled File", mime_type="application/vnd.google-apps.document", parent_folder_id=None):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    drive_service = build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": title,
        "mimeType": mime_type
    }

    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]

    file = drive_service.files().create(
        body=file_metadata,
        fields="id, name, mimeType, webViewLink"
    ).execute()

    return {
        "id": file["id"],
        "name": file["name"],
        "mime_type": file["mimeType"],
        "url": file["webViewLink"]
    }


def update_drive_file_metadata(user_id, file_id, new_title=None, new_parent_folder_id=None):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    drive_service = build("drive", "v3", credentials=credentials)

    updates = {}
    if new_title:
        updates["name"] = new_title

    if updates:
        drive_service.files().update(
            fileId=file_id,
            body=updates,
            fields="id, name, mimeType"
        ).execute()

    if new_parent_folder_id:
        file = drive_service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        drive_service.files().update(
            fileId=file_id,
            addParents=new_parent_folder_id,
            removeParents=previous_parents,
            fields="id, parents"
        ).execute()

    return {"status": "success", "file_id": file_id}


def delete_drive_file(user_id, file_id):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    drive_service = build("drive", "v3", credentials=credentials)

    try:
        drive_service.files().delete(fileId=file_id).execute()
        return {"status": "success", "file_id": file_id}
    except:
        return None

