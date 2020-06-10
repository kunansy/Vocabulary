__all__ = (
    'backup', 'list_items', 'restore'
)

from pathlib import Path
from pprint import pprint
from sys import stderr

from googleapiclient.errors import HttpError
from requests import get

from src.backup.backup import Auth, print_items
from src.main.common_funcs import mime_type
from src.main.constants import (
    BACKUP_FOLDER_NAME, FOLDER_MTYPE
)
from src.trouble.trouble import Trouble

Drive = Auth()


def pprint_http_err(err: HttpError) -> None:
    """ Pretty print json of HttpError. Request to its uri,
    get json from there and pprint it.

    :param err: HttpError to pprint its json.
    :return: None.
    :exception Trouble: if wrong type given.
    """
    if not isinstance(err, HttpError):
        raise Trouble(pprint_http_err, err, "HttpError", _p='w_item')
    reason = get(err.uri).json()
    pprint(reason)


def backup(f_name: str,
           f_path: Path) -> None:
    """ Delete previous base and upload new one to the folder 'backup'
     in the Drive. If there's no folder found, create it.

    Print a message if sth went wrong while uploading.
    Print a message finally about success.

    :param f_name: string, name of base will have in the Drive.
    :param f_path: Path, path to the file.
    :return: None.
    :exception Trouble: if wrong type given or the file does not exist.
    """
    trbl = Trouble(backup, _t=True)
    if not isinstance(f_path, Path):
        raise trbl(f"Wrong path type: '{f_path}'", "Path")
    if not (isinstance(f_name, str) and f_name):
        raise trbl(f_name, _p='w_str')
    if not f_path.exists():
        raise trbl(f_path, _p='w_file')

    folder_id = search_folder_id(BACKUP_FOLDER_NAME)
    # if there's no backup folder found, don't try to find
    # and delete last backup
    if folder_id:
        s_key = "name contains '{name}' and " \
                "parents = '{parents}' and " \
                "trashed = false"
        vals = {
            'name': f_name,
            'parents': folder_id,
        }
        m_type = mime_type(f_path)
        # mimeType can be None
        if m_type:
            s_key += " and mimeType = '{m_type}'"
            vals['m_type'] = m_type

        # search last base to delete
        try:
            last_backup = Drive.search(vals, s_key)
        except HttpError as http_err:
            print(trbl("HTTP error"), file=stderr)
            # show error details
            pprint_http_err(http_err)
            return

        if len(last_backup) == 1:
            # delete the last base
            last_id = last_backup[0]['id']
            del_item(last_id, "Previous base deleted")
        elif len(last_backup) > 1:
            # TODO: delete oldest one
            assert 1 == 0, \
                trbl("More than one previous base found")

    try:
        # folder's ID, to which the file will be uploaded
        # create it if there's not folder found
        folder_id = folder(BACKUP_FOLDER_NAME)
        Drive.upload_file(f_name, f_path, folder_id)
    except HttpError as http_err:
        print(trbl("HTTP error"), file=stderr)
        # show error details
        pprint_http_err(http_err)
    except Exception as err:
        print(trbl(f"{err}\n{f_path}"), file=stderr)
    else:
        print(f"File: '{f_name}' uploaded")


def restore(f_name: str,
            f_path: Path) -> None:
    """ Restore a file from Drive (trash ignored), 'backup' folder.
    Print a message and return if an exception while file searching
    and downloading catch.
    Print a message finally about success.

    If file not found print about it.
    If >1 files found let the user to choose which one he wants to
    restore (there's input checking).

    :param f_name: string, name of the file to restore.
    :param f_path: Path, path to where the file will be saved.
    :return: None.
    :exception Trouble: if wrong type given or backup folder not found.
    """
    trbl = Trouble(restore)
    if not (isinstance(f_name, str) and f_name):
        raise trbl(f_name, _p='w_str')
    if not isinstance(f_path, Path):
        raise trbl(f"Wrong path type: '{f_path}'", "Path")
    if not search_folder_id(BACKUP_FOLDER_NAME):
        raise trbl("Backup folder not found, nothing to restore")
    # creation demanded to search values
    s_key = "name contains '{name}' and " \
            "parents = '{parent}' and " \
            "trashed = false"
    vals = {
        'name': f_name,
        'parent': search_folder_id(BACKUP_FOLDER_NAME)
    }
    fields = ['id', 'name', 'mimeType', 'modifiedTime', 'parents']

    m_type = mime_type(f_path)
    # mimeType can be None
    if m_type:
        s_key += " and mimeType = '{m_type}'"
        vals['m_type'] = m_type

    try:
        found_files = Drive.search(vals, s_key, fields)
    except KeyError:
        print(trbl("'search_key' and 'values' must have "
                   "the same names of fields"), file=stderr)
        return
    except HttpError as http_err:
        print(trbl("HTTP error"), file=stderr)
        pprint_http_err(http_err)
        return
    except Exception as err:
        print(trbl(err), file=stderr)
        return

    if not found_files:
        print(f"File with name: '{f_name}', "
              f"mimeType: '{m_type}' not found\n",
              "func – restore",
              file=stderr)
        return
    if len(found_files) > 1:
        print("There're > 1 files with the given name found.")
        print("Which of them do you want to restore?")
        print_items(found_files, 'id', 'parents')
        num = int(input())

        while num < 1 or num > len(found_files):
            print("Wrong choice, try again!", file=stderr)
            print(f"Nums in [1;{len(found_files)}]", file=stderr)
            num = int(input())

        f_id = found_files[num - 1]['id']
    else:
        f_id = found_files[0]['id']

    try:
        Drive.download_file(f_id, f_path)
    except HttpError as http_err:
        print(trbl("HTTP error"), file=stderr)
        pprint_http_err(http_err)
    except Exception as trouble:
        print(trbl(f"{trouble}\n{f_id}"), file=stderr)
    else:
        print(f"File: '{f_path}' restored")


def list_items(count: int = 10,
               *ignoring_keys) -> None:
    """ Show first count items.

    :param count: int, count of items.
    :param ignoring_keys: keys to ignore.
    :return: None.
    """
    print_items(Drive.list_items(count), *ignoring_keys)


def del_item(__id: str,
             __msg: str = '') -> None:
    """ Delete item by ID. Catch all exceptions from del_item method.

    :param __id: string, item to delete.
    :param __msg: string, message to print if everything is OK.
    :return: None.
    """
    try:
        Drive.del_item(__id)
    except HttpError as http_err:
        print("HTTP error\nfunc – del_item", file=stderr)
        pprint_http_err(http_err)
    except Exception as trouble:
        print(trouble, __id, 'func – del_item',
              'Terminating...', sep='\n', file=stderr)
    else:
        print(__msg) if __msg else ...


def search_folder_id(_name: str) -> str:
    """ Get folder's ID by name (ignore trash).

    If there's not folder found or found > 1 folders,
    return empty string.

    :param _name: string, name of the folder to found.
    :return: folder's ID or empty string.
    :exception Trouble: if wrong type given
    """
    trbl = Trouble(search_folder_id)
    if not (isinstance(_name, str) and _name):
        raise trbl(_name, _p='w_str')

    s_key = "name = '{name}' " \
            "and mimeType = '{m_type}' " \
            "and trashed = false"
    vals = {
        'name': _name,
        'm_type': FOLDER_MTYPE
    }
    try:
        _folders = Drive.search(vals, s_key)
    except HttpError as http_err:
        print(trbl("HTTP error"), file=stderr)
        pprint_http_err(http_err)
    except Exception as err:
        print(trbl, err, sep='\n', file=stderr)
    else:
        if len(_folders) == 1:
            return _folders[0]['id']
        if len(_folders) > 1:
            print(trbl(f"More than one folder named: '{_name}' found"),
                  file=stderr)
    # If there's no folder found or found > 1 folders
    return ''


def folder(_name: str) -> str:
    """ If there's folder in the Drive, return its ID,
    else – create it and return its ID.

    :param _name: string, folder name.
    :return: string, folder's ID.
    """
    fold_id = search_folder_id(_name)
    if not fold_id:
        print(f"Backup folder does not exist, creating...")
        fold_id = Drive.create_folder(_name)
        print(f"Folder '{_name}' created")
    return fold_id


# TODO: what is 'requests_async'?
