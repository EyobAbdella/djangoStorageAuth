
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




def add_data_to_sheet(user_id, sheet_id, range_name, values):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    sheets_service = build("sheets", "v4", credentials=credentials)

    try:
        body = {
            'values': values
        }
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return {
            "status": "success",
            "sheet_id": sheet_id,
            "updated_range": result.get("updates", {}).get("updatedRange")
        }
    except:
        return None


def delete_data_from_sheet(user_id, sheet_id, operation, range_name=None, row_indices=None, sheet_name="Sheet1"):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    sheets_service = build("sheets", "v4", credentials=credentials)

    try:
        if operation == "bulk":
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!A1:Z1000"
            ).execute()
            return {"status": "success", "sheet_id": sheet_id, "operation": "bulk_clear"}

        elif operation == "cell" and range_name:
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            return {"status": "success", "sheet_id": sheet_id, "operation": "cell_clear", "range": range_name}

        elif operation in ["row", "rows"] and row_indices:
            row_indices = sorted(row_indices, reverse=True)
            requests = [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": 0,
                            "dimension": "ROWS",
                            "startIndex": index - 1,
                            "endIndex": index
                        }
                    }
                } for index in row_indices
            ]
            body = {"requests": requests}
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=body
            ).execute()
            return {
                "status": "success",
                "sheet_id": sheet_id,
                "operation": "row_delete",
                "deleted_rows": row_indices
            }

        return None
    except:
        return None


def update_data_in_sheet(user_id, sheet_id, range_name, values):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    sheets_service = build("sheets", "v4", credentials=credentials)

    try:
        body = {
            'values': values
        }
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return {
            "status": "success",
            "sheet_id": sheet_id,
            "updated_range": result.get("updatedRange"),
            "updated_rows": result.get("updatedRows"),
            "updated_columns": result.get("updatedColumns")
        }
    except:
        return None


def list_data_from_sheet(user_id, sheet_id, range_name="Sheet1!A1:Z1000", search_column=None, search_keyword=None):
    credentials = load_google_credentials(user_id)
    if not credentials:
        return None

    sheets_service = build("sheets", "v4", credentials=credentials)

    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        values = result.get("values", [])

        if not values:
            return {"status": "success", "sheet_id": sheet_id, "data": []}

        if search_column is not None and search_keyword is not None:
            try:
                search_column_index = ord(search_column.upper()) - ord('A')
            except:
                return None

            filtered_values = [
                row for row in values
                if len(row) > search_column_index and str(row[search_column_index]).lower() == search_keyword.lower()
            ]
            return {
                "status": "success",
                "sheet_id": sheet_id,
                "data": filtered_values,
                "search_column": search_column,
                "search_keyword": search_keyword
            }

        return {"status": "success", "sheet_id": sheet_id, "data": values}
    except:
        return None
