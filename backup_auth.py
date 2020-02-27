from __future__ import print_function
import pickle
import os.path
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN = 'program_data\\token.pickle'
CREDENTIALS = 'program_data\\credentials.json'
FOLDER_ID = '1C990uxIFIZJOIS7ZhuXQWj4izeivTPB-'
FILE_WITH_ID = "id.txt"


class Auth:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN):
            with open(TOKEN, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN, 'wb') as token:
                pickle.dump(creds, token)

        self.drive_service = build('drive', 'v3', credentials=self.credentials())

    def credentials(self):
        with open(TOKEN, 'rb') as file:
            return pickle.load(file)

    def list_files(self, size=10):
        service = build('drive', 'v3', credentials=self.credentials())

        # Call the Drive v3 API
        results = service.files().list(
            pageSize=size, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found')
        else:
            print('\n'.join(u'{0} ({1})'.format(item['name'], item['id']) for item in items))

    def upload_file(self, file_name, file_path, mimetype='text/'):
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(file_path,
                                mimetype=mimetype)

        file = self.drive_service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 fields='id').execute()
        file_id = file.get('id')
        print(f"File ID: {file_id}")

        with open(FILE_WITH_ID, 'w') as f:
            f.write(file_id)

    def download_file(self, file_id=None, file_path=''):
        if file_id is None and os.path.exists(FILE_WITH_ID):
            file_id = open(FILE_WITH_ID, 'r').read()

        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            try:
                status, done = downloader.next_chunk()
            except Exception as trouble:
                print(trouble)
                return

            print(f"Download {int(status.progress() * 100)}%.")

        with io.open(file_path, 'wb') as file:
            fh.seek(10)
            file.write(fh.read())