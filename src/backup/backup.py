from __future__ import print_function

__all__ = 'Auth', 'print_items'

import io
import pickle
from pathlib import Path
import sys
from typing import List, Dict

from apiclient import http
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.main import constants as const
import src.main.common_funcs as comm_func


# folder name in Drive to backup
BACKUP_FOLDER_NAME = 'backup'
# demanded to Drive types
FOLDER_MTYPE = 'application/vnd.google-apps.folder'
# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive']
# path to token for the Drive
TOKEN_PATH = const.PROGRAM_DATA_BASE_PATH / 'token.pickle'
# path to credentials to log in to Drive
CREDS_PATH = const.PROGRAM_DATA_BASE_PATH / 'client_secret.json'


class Auth:
    def __init__(self) -> None:
        """ Get credentials from a local file or log in to
        Google if there're no (valid) ones.
        
        Init drive with them.
        
        :return: None.
        """
        # it's a secret, nobody is to know it...
        api_key_path = const.DATA_BASE_PATH / 'program_data' / 'drive_API_key'
        api_key = api_key_path.open().read()

        creds = self.__obtain_creds()
        self.__drive = build('drive', 'v3',
                             credentials=creds,
                             developerKey=api_key)

    def __load(self) -> Credentials:
        """ Load credentials from the local file.
        
        :return: credentials.
        """
        if not TOKEN_PATH.exists():
            raise FileExistsError("Token not found")

        with TOKEN_PATH.open('rb') as file:
            return pickle.load(file)

    def __dump(self,
               __creds: Credentials) -> None:
        """ Dump credentials to the standard local (token) file.

        :param __creds: credentials to dump.
        :return: None.
        """
        with TOKEN_PATH.open('wb') as token:
            pickle.dump(__creds, token)

    def __obtain_creds(self) -> Credentials:
        """ Get credentials from the local file if they exist.
        Log in to Google if there're no (valid) ones and dump them to file.

        :return: credentials.
        """
        _creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time
        if TOKEN_PATH.exists():
            _creds = self.__load()
        # If there're no (valid) credentials available, let the user log in
        if not _creds or not _creds.valid:
            if _creds and _creds.expired and _creds.refresh_token:
                _creds.refresh(Request())
            else:
                _flow = InstalledAppFlow.from_client_secrets_file(
                    CREDS_PATH, SCOPES)
                _creds = _flow.run_local_server(port=0)
            # Save the credentials for the next run
            self.__dump(_creds)
        return _creds

    def list_items(self,
                   __size: int) -> List[Dict]:
        """ List n first item from the drive.

        :param __size: int, count of the items.
        :return: list of dicts, theirs ID and names.
        """
        _results = self.__drive.files().list(
            pageSize=__size, fields="nextPageToken, files(id, name)").execute()
        return _results.get('files', [])

    def upload_file(self,
                    __name: str,
                    __path: Path,
                    __folder_id: str) -> str:
        """ Upload a file to the Drive. MimeType gets automatically.

        :param __name: string, name, the file will have in Drive.
        :param __path: Path, file path.
        :param __folder_id: string, folder's ID, to which the file will be uploaded.
        :return: string, uploaded file's ID.
        :exception Trouble: if the file does not exist.
        """
        if not __path.exists():
            raise FileNotFoundError("File to upload not found")

        file_metadata = {
            'name': __name,
            'parents': [__folder_id]
        }
        # mime type getting
        m_type = comm_func.mime_type(__path)
        media = http.MediaFileUpload(__path, mimetype=m_type)

        _file = self.__drive.files().create(
            body=file_metadata, media_body=media, fields='id').execute()

        return _file.get('id')

    # TODO: some first bytes (symbols) losing.
    # TODO: it's unavailable to download media files (like PDF or mp4).
    # TODO: it's unavailable to download files encoding UTF-8.
    def download_file(self,
                      __id: str,
                      __path: Path) -> None:
        """ Download the file by ID.

        :param __id: string, file ID.
        :param __path: Path, path to download the file.
        :return: None.
        """
        # m_type = mime_type(__path)
        _request = self.__drive.files().get_media(fileId=__id)
        _fh = io.BytesIO()
        _downloader = http.MediaIoBaseDownload(_fh, _request)

        _done = False
        while _done is False:
            try:
                status, _done = _downloader.next_chunk()
            except Exception as e:
                print(f"{e}\nwhile downloading file: {__path}", file=sys.stderr)
                return

            print(f"Download {int(status.progress() * 100)}%")

        with io.open(str(__path), 'wb') as f:
            _fh.seek(10)
            f.write(_fh.read())

    def search(self,
               __s_key: str,
               __values: Dict[str, str],
               __fields: List[str] = ("id", "name", "mimeType")) -> List[Dict[str, str]]:
        """ Search items by the key.

        All key's and dict's keys must coincide and be in the fields.

        :param __s_key: string, search key format: "query_term operator '{value}'".
        :param __values: dict of str, values for search key.

        Example:
            key= "name = '{name}' and trashed = false and id = '{id}'",
            _values = {'name': 'sth', 'id': 'sth'}

        Key's params available:
         1. <=> – query_term <=> value.
         2. != – reversed equal.
         3. contains – value contains in the query_term.
         4. not query_term contains – reversed contain.
         5. in – query_term is in a list.
         6. trashed = true/false – whether the file is in the trash.
         7. modifiedTime <=> 'yy-mm-dd' – modification time.
         8. visibility = 'limited' – whether visibility is limited.

        :param __fields: tuple or list of strings, some fields to search in
         them and return their values, by default – (id, name, mimeType).
         Available fields (and query_term): kind, id, name, mimeType,
         capabilities, permissions, parents etc.
        :return: list of dicts; values of fields keys.
        :exception KeyError: if any __s_key key not in __values.
        """
        __s_key = __s_key.format(**__values)
        __fields = ", ".join(__fields)

        _results = self.__drive.files().list(
            fields=f"nextPageToken, files({__fields})", q=__s_key).execute()

        return _results.get('files', [])

    def del_item(self,
                 __id: str) -> None:
        """ Remove an item by ID.

        :param __id: removing item's ID.
        :return: None.
        """
        self.__drive.files().delete(fileId=__id).execute()

    def create_folder(self,
                      __name: str) -> str:
        """ Create folder in the Drive root, return its ID.

        :param __name: string, name of the folder.
        :return: string, created folder's ID.
        """
        fld_metadt = {
            'name': __name,
            'mimeType': FOLDER_MTYPE
        }
        _folder = self.__drive.files().create(
            body=fld_metadt, fields='id').execute()
        return _folder.get('id')


def print_items(__items: List[Dict],
                *ignoring_keys) -> None:
    """ Print enumerated (with 1) items in the dicts, all keys and
    values, except for given ones.

    If __items if empty, print "No files found".
    If all dicts' keys were ignored, print "All keys were ignored".

    :param __items: list of dicts.
    :param ignoring_keys: keys to ignore.
    :return: None.
    """
    if not __items:
        print('No files found')
        return

    # if all keys are ignored
    if all(i in ignoring_keys for i in __items[0].keys()):
        print("All keys were ignored")
        return
    res = []

    for num, i in enumerate(__items, 1):
        _filtered = [
            f"{key}='{val}'"
            for key, val in i.items()
            if key not in ignoring_keys
        ]
        res += [f"{num}. {'    '.join(_filtered)}"]
    print('\n'.join(res))
