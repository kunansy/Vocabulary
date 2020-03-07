from __future__ import print_function

import io
import pickle

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

from common_funcs import file_exist
from constants import SCOPES, TOKEN_PATH, CREDS_PATH, mimeTypes


class Auth:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time
        if file_exist(TOKEN_PATH):
            creds = self.creds()
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save the credentials for the next run
                self.dump(creds)
            else:
                self.login()

        self.drive_service = build('drive', 'v3', credentials=creds)

    def creds(self):
        """ Считать права доступа """
        assert file_exist(TOKEN_PATH), \
            f"Wrong token: '{TOKEN_PATH}'"

        with open(TOKEN_PATH, 'rb') as file:
            return pickle.load(file)

    def dump(self, creds):
        """ Вывести права доступа в файл """
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    def login(self):
        """ Получить права доступа и вывести их в файл """
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        self.dump(creds)

    def list_items(self, size):
        """ Вернуть список имён и ID айтемов на диске """
        results = self.drive_service.files().list(
            pageSize=size, fields="nextPageToken, files(id, name)").execute()
        return results.get('files', [])

    def upload_file(self, file_name, file_path,
                    mimetype, folder_id):
        """ Залить файл на Google Drive в указанную папку  """
        assert file_exist(file_path), \
            f"Wrong file: '{file_name}', func – Auth.upload_file"

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path,
                                mimetype=mimetype)

        file = self.drive_service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 fields='id').execute()

        return file.get('id')

    def download_file(self, file_id, file_path):
        """ Скачать файл по ID """
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

    def search(self, item_name, key="name = '{item}'"):
        """ Найти айтем по имени, принимает ключ
            поиска формата "атрибут оператор '{item}'"
        """
        results = self.drive_service.files().list(
            fields="nextPageToken, files(id, name, mimeType)",
            q=key.format(item=item_name)).execute()
        # fields(kind, mimetype)
        return results.get('files', [])

    def del_item(self, item_id):
        """ Удалить айтем по ID """
        self.drive_service.files().delete(
            fileId=item_id).execute()

    def create_folder(self, name):
        """ Создать папку с переданным именем,
            вернув её ID
        """
        folder_metadata = {
            'name': name,
            'mimeType': mimeTypes['folder']
        }
        folder = self.drive_service.files().create(
            body=folder_metadata, fields='id').execute()
        return folder.get('id')


def print_items(items):
    """ Распечатать айтемы, имя и ID """
    if items:
        name_id = map(lambda x: f"{x['name']} {x['id']}", items )
        print('\n'.join(name_id))
    else:
        print('No files found')
