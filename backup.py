from __future__ import print_function

import io
import pickle
import os.path

from apiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

from constants import SCOPES, TOKEN_PATH, CREDENTIALS_PATH, FOLDER_ID


class Auth:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if file_exist(TOKEN_PATH):
            creds = self.credentials()
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

        self.drive_service = build('drive', 'v3', credentials=creds)

    def credentials(self):
        """ Получить права доступа """
        assert file_exist(TOKEN_PATH), f"Wrong token: '{TOKEN_PATH}'"

        with open(TOKEN_PATH, 'rb') as file:
            return pickle.load(file)

    def list_items(self, size=10):
        """ Вернуть список имени и id первых n айтемов """
        results = self.drive_service.files().list(
            pageSize=size, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        return items

    def upload_file(self, file_name, file_path, mimetype='text/', folder_id=FOLDER_ID):
        """ Залить файл на Google Drive в папку backup """
        assert file_exist(file_path), f"Wrong file: '{file_name}', func – Auth.upload_file"

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path,
                                mimetype=mimetype)

        file = self.drive_service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 fields='id').execute()

        print(f"File: '{file_path}' successfully uploaded, ID: '{file.get('id')}'")

    def download_file(self, file_id, file_path):
        """ Скачать файл по ID """
        # TODO: не может качать медифайлы
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

    def search_item(self, item_name):
        """ Найти айтем по имени """
        results = self.drive_service.files().list(
             fields="nextPageToken, files(id, name)", q=f"name = '{item_name}'").execute()
        # fields(kind, mimetype)
        items = results.get('files', [])

        return items

    def del_file(self, item_id):
        """ Удалить айтем по ID """
        try:
            self.drive_service.files().delete(fileId=item_id).execute()
        except errors.HttpError as error:
            print(error)


def print_items(items):
    """ Распечатать айтемы, имя и ID """
    if items:
        print('\n'.join(u'{0} ({1})'.format(item['name'], item['id']) for item in items))
    else:
        print('No files found')


def file_exist(filename):
    """ Существует ли файл """
    return os.path.exists(filename)