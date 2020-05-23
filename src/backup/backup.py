from __future__ import print_function

__all__ = [
    'Auth', 'print_items'
]

import io
import pickle

from apiclient import http
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.trouble.trouble import Trouble
from src.main.common_funcs import file_exist
from src.main.constants import (
    SCOPES, mimeTypes, TOKEN_PATH,
    CREDS_PATH
)


class Auth:
    def __init__(self) -> None:
        _creds = self.obtain_creds()
        self.drive_service = build('drive', 'v3', credentials=_creds)

    def load(self) -> Credentials:
        """ Считать права доступа по стандартному пути """
        assert file_exist(TOKEN_PATH), \
            Trouble(self.load, TOKEN_PATH, _p='w_file')

        with open(TOKEN_PATH, 'rb') as file:
            return pickle.load(file)

    def dump(self, _creds: Credentials) -> None:
        """ Вывести права доступа по стандартному пути """
        with open(TOKEN_PATH, 'wb') as _token:
            pickle.dump(_creds, _token)

    def obtain_creds(self) -> Credentials:
        """
        Получить права доступа, вывести их в файл
        по стандартному пути и вернуть
        """
        _creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time
        if file_exist(TOKEN_PATH):
            _creds = self.load()
        # If there are no (valid) credentials available, let the user log in
        if not _creds or not _creds.valid:
            if _creds and _creds.expired and _creds.refresh_token:
                _creds.refresh(Request())
                # Save the credentials for the next run
            else:
                _flow = InstalledAppFlow.from_client_secrets_file(
                    CREDS_PATH, SCOPES)
                _creds = _flow.run_local_server(port=0)
            self.dump(_creds)
        return _creds

    def list_items(self, _size: int) -> list:
        """ Вернуть список имён и ID первых n айтемов на диске """
        _results = self.drive_service.files().list(
            pageSize=_size, fields="nextPageToken, files(id, name)").execute()
        return _results.get('files', [])

    def upload_file(self, file_name, file_path,
                    mimetype, folder_id) -> str:
        """ Залить файл на Google Drive в указанную папку  """
        assert file_exist(file_path), \
            Trouble(self.upload_file, file_name, _p='w_file')

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        _media = http.MediaFileUpload(file_path, mimetype=mimetype)
        _file = self.drive_service.files().create(
            body=file_metadata,
            media_body=_media,
            fields='id').execute()

        return _file.get('id')

    def download_file(self, f_id: str, f_path: str) -> None:
        """ Скачать файл по ID """
        _request = self.drive_service.files().get_media(fileId=f_id)
        _fh = io.BytesIO()
        _downloader = http.MediaIoBaseDownload(_fh, _request)

        _done = False
        while _done is False:
            try:
                status, _done = _downloader.next_chunk()
            except Exception as trouble:
                print(trouble)
                return

            print(f"Download {int(status.progress() * 100)}%")

        with io.open(f_path, 'wb') as file:
            _fh.seek(10)
            file.write(_fh.read())

    def search(self, _values: dict, s_key="name = '{name}'",
               _fields="id, name, mimeType") -> list:
        """
        Найти айтемы по переданному ключу

        :param _values: словарь с именами f полей ключа и их значениями:
            key= "name = '{m}' and id ='{k}'",
            _values = {name: 'sth', id: 'sth'}
        :param s_key: ключ поиска формата "query_term operator '{values}'",
        по умолчанию – name = '{values}'
        :param _fields: поля, в которых будет происходить поиск:
        по умолчанию – id, name, mimeType
        :return: список словарей найденных айтемов с ключами,
        переденными в _fields

        Все ключи словаря должны содержаться в ключе поиска,
        иначе – ошибка

        Возможности ключа:
        1. <=> – query_term <=> значение;
        2. != – обратный равенству;
        3. contains – содержание значения в query_term;
        4. not query_term contains – обратный содержанию;
        5. in – query_term находится в списке;
        6. trashed = true/false – файл в корзине или нет;
        7. modifiedTime <=> 'yy-mm-dd' – время модификации;
        8. visibility = 'limited' – ограниченная видимость;

        Возможные поля (_fields и query_term): kind, id, name,
        mimeType, capabilities, permissions, parents etc;
        """
        try:
            s_key = s_key.format(**_values)
        except Exception as _err:
            print(f"Wrong values or search key: {_values}, {s_key}", "\nTerminating...")
            return []

        _results = self.drive_service.files().list(
            fields=f"nextPageToken, files({_fields})",
            q=s_key).execute()
        return _results.get('files', [])

    def del_item(self, _id: str) -> None:
        """
        Удалить айтем по ID. Проверка наличия айтема
        с переданным ID не проводится

        :param _id: ID удаляемогоо айтема, str
        """
        self.drive_service.files().delete(
            fileId=_id).execute()

    def create_folder(self, _name: str) -> str:
        """
        Создать папку с переданным именем
        в корне диска, вернув её ID
        """
        folder_metadata = {
            'name': _name,
            'mimeType': mimeTypes['folder']
        }
        _folder = self.drive_service.files().create(
            body=folder_metadata, fields='id').execute()
        return _folder.get('id')


def print_items(_items: list, *ignoring_keys) -> None:
    """
    Распечатать айтемы, все ключи и значения,
    игнорируя переданные в ignoring_keys

    :param _items: список словарей
    :param ignoring_keys: ключи, значения которых
    не будут выведены
    """
    if _items:
        # если все ключи проигнорированы
        if all(i in ignoring_keys for i in _items[0].keys()):
            print("All keys were ignored")
            return
        res = []

        for i in _items:
            _filtered = [f"{k}='{v}'" for k, v in i.items()
                         if k not in ignoring_keys]
            res += [' '.join(_filtered)]
        print('\n'.join(res))
    else:
        print('No files found')