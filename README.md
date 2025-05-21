# djangoStorageAuth

`djangoStorageAuth` is a Django module for authentication with Google and Microsoft accounts and performing operations on Google Drive, Google Sheets, and OneDrive, including file and spreadsheet management. It supports OAuth2 authentication with encrypted token storage and provides reusable utilities in `djangoStorageAuth.utils` (e.g., `from djangoStorageAuth.utils import list_onedrive_files`) for tasks like listing, creating, updating, deleting, and manipulating spreadsheet data.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Cloud Storage Utilities](#cloud-storage-utilities)
    - [Google Drive Utilities](#google-drive-utilities)
    - [Google Sheets Utilities](#google-sheets-utilities)
    - [OneDrive Utilities](#onedrive-utilities)
    - [Excel Utilities](#excel-utilities)

## Features

- OAuth2 authentication for Google and Microsoft accounts with encrypted token storage
- Reusable utilities in `djangoStorageAuth.utils` for operations like file and spreadsheet management.
- Google Drive operations: list, create, update, and delete files/folders.
- Google Sheets operations: add, update, delete, and list spreadsheet data (bulk, cell, row-based).
- OneDrive operations: list, create, update, and delete files/folders.
- Excel operations: add, update, delete, and list data in OneDrive Excel files (bulk, cell, row-based).
- JWT authentication with access/refresh tokens for secure API access.
- Search functionality to filter spreadsheet data by column and keyword.
- Security: encrypts OAuth tokens using `FIELD_ENCRYPTION_KEY`.

## Installation

1. Install the module using pip:
    
    ```bash
    pip install git+https://github.com/EyobAbdella/djangoStorageAuth.git
    ```
    
2. Update `settings.py`:
    
    ```python
    import os
    
    INSTALLED_APPS = [
        ...,
        'rest_framework',
        'djangoStorageAuth',
    ]
    
    FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET")
    ```
    
3. Add to the project’s root `urls.py`:
    
    ```python
    from django.urls import path, include
    
    urlpatterns = [
        ...,
        path("oauth/", include("djangoStorageAuth.urls")),
    ]
    ```
    
4. Create migrations:
    
    ```bash
    python manage.py makemigrations
    ```
    
5. Apply migrations:
    
    ```bash
    python manage.py migrate
    ```
    
6. Start the development server:
    
    ```bash
    python manage.py runserver
    ```
    

## Configuration

1. Configure OAuth credentials:
    
    - **Google**: Create a project in [Google Cloud Console](https://console.cloud.google.com/), enable Drive and Sheets APIs, set up OAuth credentials, and add `http://127.0.0.1:8000/oauth/google/callback` to Authorized redirect URIs (update for production).
    - **Microsoft**: Register an app in [Azure Portal](https://portal.azure.com/), configure `User.Read` and `Files.ReadWrite.All` permissions, obtain client ID/secret, and add `http://127.0.0.1:8000/oauth/microsoft/callback` to redirect URIs (update for production).
2. Set environment variables in a `.env` file in the project root:
    
    ```env
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    MICROSOFT_CLIENT_ID=your-microsoft-client-id
    MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
    FIELD_ENCRYPTION_KEY=4DgkYtV5IQeH-RERo8fHMZ-Zu3TqCLrixFsmbSUDajg=
    ```
    
    - Generate a unique `FIELD_ENCRYPTION_KEY`:
        
        ```bash
        python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        ```
        

## Authentication

`djangoStorageAuth` provides endpoints for OAuth authentication with Google and Microsoft accounts.

### Google OAuth

- **Redirect**: `GET http://localhost:8000/oauth/google/redirect`
    - Initiates Google OAuth flow in the browser.
    - Redirects to Google’s consent screen.
- **Callback**: `GET http://localhost:8000/oauth/google/callback`
    - Returns JWT tokens:
        
        ```json
        {
          "access_token": "jwt-access-token",
          "refresh_token": "jwt-refresh-token"
        }
        ```
        

### Microsoft OAuth

- **Redirect**: `GET http://localhost:8000/oauth/microsoft/redirect`
    - Initiates Microsoft OAuth flow in the browser.
    - Redirects to Microsoft’s consent screen.
- **Callback**: `GET http://localhost:8000/oauth/microsoft/callback/`
    - Returns JWT tokens:
        
        ```json
        {
          "access_token": "jwt-access-token",
          "refresh_token": "jwt-refresh-token"
        }
        ```
        

## Cloud Storage Utilities

Utilities for managing cloud storage and spreadsheets, integrable into Django applications. These utilities support authenticated operations on Google Drive, Google Sheets, OneDrive, and Excel files, enabling tasks like file management and spreadsheet data manipulation.

### Google Drive Utilities

- **List Files**: `list_drive_files(user_id, mime_type=None)`
    
    - Arguments:
        
        - `user_id`: User ID (e.g., `request.user.id`).
        - `mime_type`: Filter by MIME type (e.g., `application/vnd.google-apps.spreadsheet`).
    - Returns: List of files `[{ "id": "file_id", "name": "file_name", "mimeType": "type" }, ...]` or `[]`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_drive_files
        
        @api_view(['GET'])
        def google_drive_list(request):
            mime_type = request.GET.get('mime_type')
            files = list_drive_files(
                user_id=request.user.id,
                mime_type=mime_type
            )
            return Response(files)
        ```
        
- **List Folders**: `list_google_drive_folders(user_id)`
    
    - Arguments: `user_id`.
        
    - Returns: List of folders `[{ "id": "folder_id", "name": "folder_name", "mimeType": "application/vnd.google-apps.folder" }, ...]` or `[]`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_google_drive_folders
        
        @api_view(['GET'])
        def google_drive_folders(request):
            folders = list_google_drive_folders(
                user_id=request.user.id
            )
            return Response(folders)
        ```
        
- **Create File**: `create_drive_file(user_id, title="Untitled File", mime_type="application/vnd.google-apps.document", parent_folder_id=None)`
    
    - Arguments: `user_id`, `title`, `mime_type`, `parent_folder_id`.
        
    - Returns: `{ "id": "file_id", "name": "file_name", "mime_type": "type", "url": "file_url" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import create_drive_file
        
        @api_view(['POST'])
        def google_drive_create(request):
            title = request.data.get('title', 'Untitled File')
            mime_type = request.data.get('mime_type', 'application/vnd.google-apps.spreadsheet')
            parent_folder_id = request.data.get('parent_folder_id')
            
            file = create_drive_file(
                user_id=request.user.id,
                title=title,
                mime_type=mime_type,
                parent_folder_id=parent_folder_id
            )
            return Response(file)
        ```
        
- **Update File Metadata**: `update_drive_file_metadata(user_id, file_id, new_title=None, new_parent_folder_id=None)`
    
    - Arguments: `user_id`, `file_id`, `new_title`, `new_parent_folder_id`.
        
    - Returns: `{ "status": "success", "file_id": "file_id" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import update_drive_file_metadata
        
        @api_view(['POST'])
        def google_drive_update(request):
            file_id = request.data.get('file_id')
            new_title = request.data.get('new_title')
            new_parent_folder_id = request.data.get('new_parent_folder_id')
            
            result = update_drive_file_metadata(
                user_id=request.user.id,
                file_id=file_id,
                new_title=new_title,
                new_parent_folder_id=new_parent_folder_id
            )
            return Response(result)
        ```
        
- **Delete File**: `delete_drive_file(user_id, file_id)`
    
    - Arguments: `user_id`, `file_id`.
        
    - Returns: `{ "status": "success", "file_id": "file_id" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import delete_drive_file
        
        @api_view(['POST'])
        def google_drive_delete(request):
            file_id = request.data.get('file_id')
            
            result = delete_drive_file(
                user_id=request.user.id,
                file_id=file_id
            )
            return Response(result)
        ```
        

### Google Sheets Utilities

- **Add Data**: `add_data_to_sheet(user_id, sheet_id, range_name, values)`
    
    - Arguments: `user_id`, `sheet_id`, `range_name` (e.g., `Sheet1!A1`), `values` (list of lists).
        
    - Returns: `{ "status": "success", "sheet_id": "sheet_id", "updated_range": "range" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import add_data_to_sheet
        
        @api_view(['POST'])
        def google_sheets_add(request):
            sheet_id = request.data.get('sheet_id')
            range_name = request.data.get('range_name', 'Sheet1!A1')
            values = request.data.get('values', [['Column1', 'Column2'], ['Value1', 'Value2']])
            
            result = add_data_to_sheet(
                user_id=request.user.id,
                sheet_id=sheet_id,
                range_name=range_name,
                values=values
            )
            return Response(result)
        ```
        
- **Update Data**: `update_data_in_sheet(user_id, sheet_id, range_name, values)`
    
    - Arguments: Same as above.
        
    - Returns: `{ "status": "success", "sheet_id": "sheet_id", "updated_range": "range", "updated_rows": int, "updated_columns": int }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import update_data_in_sheet
        
        @api_view(['POST'])
        def google_sheets_update(request):
            sheet_id = request.data.get('sheet_id')
            range_name = request.data.get('range_name', 'Sheet1!A1')
            values = request.data.get('values', [['Column1', 'Column2'], ['Value1', 'Value2']])
            
            result = update_data_in_sheet(
                user_id=request.user.id,
                sheet_id=sheet_id,
                range_name=range_name,
                values=values
            )
            return Response(result)
        ```
        
- **Delete Data**: `delete_data_from_sheet(user_id, sheet_id, operation, range_name=None, row_indices=None, sheet_name="Sheet1")`
    
    - Arguments: `user_id`, `sheet_id`, `operation` (`bulk`, `cell`, `row`, `rows`), `range_name` (for `cell`), `row_indices` (for `row`/`rows`), `sheet_name`.
        
    - Returns: `{ "status": "success", "sheet_id": "sheet_id", "operation": "type", ... }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import delete_data_from_sheet
        
        @api_view(['POST'])
        def google_sheets_delete(request):
            sheet_id = request.data.get('sheet_id')
            operation = request.data.get('operation')
            range_name = request.data.get('range_name')
            row_indices = request.data.get('row_indices')
            sheet_name = request.data.get('sheet_name', 'Sheet1')
            
            result = delete_data_from_sheet(
                user_id=request.user.id,
                sheet_id=sheet_id,
                operation=operation,
                range_name=range_name,
                row_indices=row_indices,
                sheet_name=sheet_name
            )
            return Response(result)
        ```
        
- **List Data**: `list_data_from_sheet(user_id, sheet_id, range_name="Sheet1!A1:Z1000", search_column=None, search_keyword=None)`
    
    - Arguments: `user_id`, `sheet_id`, `range_name`, `search_column` (e.g., `A`), `search_keyword`.
        
    - Returns: `{ "status": "success", "sheet_id": "sheet_id", "data": [[]], ... }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_data_from_sheet
        
        @api_view(['GET'])
        def google_sheets_list(request):
            sheet_id = request.GET.get('sheet_id')
            range_name = request.GET.get('range_name', 'Sheet1!A1:Z1000')
            search_column = request.GET.get('search_column')
            search_keyword = request.GET.get('search_keyword')
            
            result = list_data_from_sheet(
                user_id=request.user.id,
                sheet_id=sheet_id,
                range_name=range_name,
                search_column=search_column,
                search_keyword=search_keyword
            )
            return Response(result)
        ```
        

### OneDrive Utilities

- **List Files**: `list_onedrive_files(user_id, mime_type=None)`
    
    - Arguments:
        
        - `user_id`: User ID (e.g., `request.user.id`).
        - `mime_type`: Filter by MIME type (e.g., `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`).
    - Returns: List of files `[{ "id": "file_id", "name": "file_name", "mime_type": "type" }, ...]` or `[]`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_onedrive_files
        
        @api_view(['GET'])
        def onedrive_list(request):
            mime_type = request.GET.get('mime_type')
            
            files = list_onedrive_files(
                user_id=request.user.id,
                mime_type=mime_type
            )
            return Response(files)
        ```
        
- **List Folders**: `list_onedrive_folders(user_id)`
    
    - Arguments: `user_id`.
        
    - Returns: List of folders `[{ "id": "folder_id", "name": "folder_name", "mime_type": "application/vnd.google-apps.folder" }, ...]` or `[]`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_onedrive_folders
        
        @api_view(['GET'])
        def onedrive_folders(request):
            folders = list_onedrive_folders(
                user_id=request.user.id
            )
            return Response(folders)
        ```
        
- **Create File**: `create_onedrive_file(user_id, title="Untitled File", mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", parent_folder_id=None)`
    
    - Arguments: `user_id`, `title`, `mime_type`, `parent_folder_id`.
        
    - Returns: `{ "id": "file_id", "name": "file_name", "mime_type": "type", "url": "file_url" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import create_onedrive_file
        
        @api_view(['POST'])
        def onedrive_create(request):
            title = request.data.get('title', 'Untitled File')
            mime_type = request.data.get('mime_type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            parent_folder_id = request.data.get('parent_folder_id')
            
            file = create_onedrive_file(
                user_id=request.user.id,
                title=title,
                mime_type=mime_type,
                parent_folder_id=parent_folder_id
            )
            return Response(file)
        ```
        
- **Update File Metadata**: `update_onedrive_file_metadata(user_id, file_id, new_title=None, new_parent_folder_id=None)`
    
    - Arguments: `user_id`, `file_id`, `new_title`, `new_parent_folder_id`.
        
    - Returns: `{ "status": "success", "file_id": "file_id" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import update_onedrive_file_metadata
        
        @api_view(['POST'])
        def onedrive_update(request):
            file_id = request.data.get('file_id')
            new_title = request.data.get('new_title')
            new_parent_folder_id = request.data.get('new_parent_folder_id')
            
            result = update_onedrive_file_metadata(
                user_id=request.user.id,
                file_id=file_id,
                new_title=new_title,
                new_parent_folder_id=new_parent_folder_id
            )
            return Response(result)
        ```
        
- **Delete File**: `delete_onedrive_file(user_id, file_id)`
    
    - Arguments: `user_id`, `file_id`.
        
    - Returns: `{ "status": "success", "file_id": "file_id" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import delete_onedrive_file
        
        @api_view(['POST'])
        def onedrive_delete(request):
            file_id = request.data.get('file_id')
            
            result = delete_onedrive_file(
                user_id=request.user.id,
                file_id=file_id
            )
            return Response(result)
        ```
        

### Excel Utilities

- **Add Data**: `add_data_to_excel(user_id, workbook_id, range_name, values, sheet_name="Sheet1")`
    
    - Arguments: `user_id`, `workbook_id`, `range_name` (e.g., `Sheet1!A1`), `values` (list of lists), `sheet_name`.
        
    - Returns: `{ "status": "success", "workbook_id": "workbook_id", "updated_range": "range" }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import add_data_to_excel
        
        @api_view(['POST'])
        def excel_add(request):
            workbook_id = request.data.get('workbook_id')
            range_name = request.data.get('range_name', 'Sheet1!A1')
            values = request.data.get('values', [['Column1', 'Column2'], ['Value1', 'Value2']])
            sheet_name = request.data.get('sheet_name', 'Sheet1')
            
            result = add_data_to_excel(
                user_id=request.user.id,
                workbook_id=workbook_id,
                range_name=range_name,
                values=values,
                sheet_name=sheet_name
            )
            return Response(result)
        ```
        
- **Update Data**: `update_data_in_excel(user_id, workbook_id, range_name, values)`
    
    - Arguments: `user_id`, `workbook_id`, `range_name`, `values`.
        
    - Returns: `{ "status": "success", "workbook_id": "workbook_id", "updated_range": "range", "updated_rows": int, "updated_columns": int }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import update_data_in_excel
        
        @api_view(['POST'])
        def excel_update(request):
            workbook_id = request.data.get('workbook_id')
            range_name = request.data.get('range_name', 'Sheet1!A1')
            values = request.data.get('values', [['Column1', 'Column2'], ['Value1', 'Value2']])
            
            result = update_data_in_excel(
                user_id=request.user.id,
                workbook_id=workbook_id,
                range_name=range_name,
                values=values
            )
            return Response(result)
        ```
        
- **Delete Data**: `delete_data_from_excel(user_id, workbook_id, operation, range_name=None, row_indices=None, sheet_name="Sheet1")`
    
    - Arguments: `user_id`, `workbook_id`, `operation` (`bulk`, `cell`, `row`, `rows`), `range_name` (for `cell`), `row_indices` (for `row`/`rows`), `sheet_name`.
        
    - Returns: `{ "status": "success", "workbook_id": "workbook_id", "operation": "type", ... }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import delete_data_from_excel
        
        @api_view(['POST'])
        def excel_delete(request):
            workbook_id = request.data.get('workbook_id')
            operation = request.data.get('operation')
            range_name = request.data.get('range_name')
            row_indices = request.data.get('row_indices')
            sheet_name = request.data.get('sheet_name', 'Sheet1')
            
            result = delete_data_from_excel(
                user_id=request.user.id,
                workbook_id=workbook_id,
                operation=operation,
                range_name=range_name,
                row_indices=row_indices,
                sheet_name=sheet_name
            )
            return Response(result)
        ```
        
- **List Data**: `list_data_from_excel(user_id, workbook_id, range_name="Sheet1!A1:Z100", search_column=None, search_keyword=None)`
    
    - Arguments: `user_id`, `workbook_id`, `range_name`, `search_column` (e.g., `A`), `search_keyword`.
        
    - Returns: `{ "status": "success", "workbook_id": "workbook_id", "data": [[]], ... }` or `None`.
        
    - Example:
        
        ```python
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        from djangoStorageAuth.utils import list_data_from_excel
        
        @api_view(['GET'])
        def excel_list(request):
            workbook_id = request.GET.get('workbook_id')
            range_name = request.GET.get('range_name', 'Sheet1!A1:Z100')
            search_column = request.GET.get('search_column')
            search_keyword = request.GET.get('search_keyword')
            
            result = list_data_from_excel(
                user_id=request.user.id,
                workbook_id=workbook_id,
                range_name=range_name,
                search_column=search_column,
                search_keyword=search_keyword
            )
            return Response(result)
        ```
