__all__ = (
    'backup', 'list_items', 'restore'
)

from pathlib import Path
from pprint import pprint
from sys import stderr

import requests
from googleapiclient.errors import HttpError

import src.backup.backup as bp
import src.main.common_funcs as comm_func

Drive = bp.Auth()


def pprint_http_err(err: HttpError) -> None:
    """ Pretty print json of HttpError. Request to its uri,
    get json from there and pprint it.

    :param err: HttpError to pprint its json.
    :return: None.
    :exception Trouble: if wrong type given.
    """
    reason = requests.get(err.uri).json()
    pprint(reason)


def backup(f_name: str,
           f_path: Path) -> None:
    """ Delete previous base and upload new one
    If there's no backup folder found, create it.

    Print a message if sth went wrong while uploading.
    Print a message finally about success.

    :param f_name: str, name of file'll have in the Drive.
    :param f_path: Path, path to the file.
    :return: None.
    """
    if not f_path.exists():
        raise FileExistsError("File to backup doesn't exist")

    folder_id = search_folder_id(bp.BACKUP_FOLDER_NAME)
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
        m_type = comm_func.mime_type(f_path)
        # mimeType can be None
        if m_type:
            s_key += " and mimeType = '{m_type}'"
            vals['m_type'] = m_type

        # search last base to delete
        try:
            last_backup = Drive.search(s_key, vals)
        except HttpError as http_err:
            # show error details
            pprint_http_err(http_err)
            raise

        if len(last_backup) is 1:
            # delete the last base
            last_id = last_backup[0]['id']
            del_item(last_id, "Previous base deleted")
        elif len(last_backup) > 1:
            # TODO: delete oldest one
            raise RuntimeError("More than one previous base found")

    try:
        # folder's ID, to which the file will be uploaded
        # create it if there's not folder found
        folder_id = folder(bp.BACKUP_FOLDER_NAME)
        Drive.upload_file(f_name, f_path, folder_id)
    except HttpError as http_err:
        # show error details
        pprint_http_err(http_err)
        raise
    except Exception:
        raise
    else:
        print(f"File: '{f_name}' uploaded")


def restore(f_name: str,
            f_path: Path) -> None:
    """ Restore a file from Drive (trash ignored), 'backup' folder.
    Print a message finally about success.

    If file not found print about it.
    If > 1 files found let the user to choose which one he wants to
    restore (there's input checking).

    :param f_name: str, name of the file to restore.
    :param f_path: Path, path to where the file'll be saved.
    :return: None.
    """
    if not search_folder_id(bp.BACKUP_FOLDER_NAME):
        raise ValueError("Backup folder not found, nothing to restore")
    # creation demanded to search values
    s_key = "name contains '{name}' and " \
            "parents = '{parent}' and " \
            "trashed = false"
    vals = {
        'name': f_name,
        'parent': search_folder_id(bp.BACKUP_FOLDER_NAME)
    }
    fields = ['id', 'name', 'mimeType', 'modifiedTime', 'parents']

    m_type = comm_func.mime_type(f_path)
    # mimeType can be None
    if m_type:
        s_key += " and mimeType = '{m_type}'"
        vals['m_type'] = m_type

    try:
        found_files = Drive.search(s_key, vals, fields)
    except KeyError:
        raise KeyError(
            "'search_key' and 'values' must have the same names of fields")
    except HttpError as http_err:
        pprint_http_err(http_err)
        raise
    except Exception:
        raise

    if not found_files:
        raise RuntimeError("File not found")
    if len(found_files) > 1:
        print("There're > 1 files with the given name found.")
        print("Which of them do you want to restore?")
        bp.print_items(found_files, 'id', 'parents')

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
        pprint_http_err(http_err)
        raise
    except Exception:
        raise
    else:
        print(f"File: '{f_path}' restored successfully")


def list_items(items_count: int = 10,
               *ignoring_keys) -> None:
    """ Show first count items.

    :param items_count: int, count of items.
    :param ignoring_keys: keys to ignore.
    :return: None.
    """
    bp.print_items(Drive.list_items(items_count), *ignoring_keys)


def del_item(id: str,
             msg: str = '') -> None:
    """ Delete item by ID. Catch all exceptions from del_item method.

    :param id: str, item to delete.
    :param msg: str, message to print if everything is OK.
    :return: None.
    """
    try:
        Drive.del_item(id)
    except HttpError as http_err:
        pprint_http_err(http_err)
        raise
    except Exception as e:
        raise RuntimeError(f"{e}\n while deleting item")
    else:
        print(msg) if msg else ...


def search_folder_id(folder_name: str) -> str:
    """ Get folder's ID by name (ignore trash).

    :param folder_name: str, folder name.
    :return: folder's ID.
    """
    s_key = "name = '{name}' " \
            "and mimeType = '{m_type}' " \
            "and trashed = false"
    vals = {
        'name': folder_name,
        'm_type': bp.FOLDER_MTYPE
    }
    try:
        folders = Drive.search(s_key, vals)
    except HttpError as e:
        pprint_http_err(e)
        raise e
    except Exception:
        raise

    if len(folders) is 1:
        return folders[0]['id']
    if len(folders) > 1:
        raise ValueError(f"> 1 folders named: '{folder_name}' found")


def folder(folder_name: str) -> str:
    """ Get folder's ID or create new one and get it's ID.

    :param folder_name: str, folder name.
    :return: str, folder's ID.
    """
    fold_id = search_folder_id(folder_name)
    if not fold_id:
        print(f"'{folder_name}' folder doesn't exist, creating...")
        fold_id = Drive.create_folder(folder_name)
        print(f"Folder '{folder_name}' created")
    return fold_id
