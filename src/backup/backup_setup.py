__all__ = [
    'backup', 'restore', 'list_items'
]

from apiclient import errors

from src.backup.backup import (
    Auth, print_items
)
from src.main.common_funcs import (
    file_name, add_to_file_name
)
from src.main.constants import (
    VOC_PATH, mimeTypes, SELF_EX_PATH,
    REPEAT_LOG_PATH, BACKUP_FOLDER_NAME, RESTORE_FOLDER_PATH
)

drive_client = Auth()


def backup(f_name, f_path):
    """ Залить файл на диск в папку backup """
    from src.main.common_funcs import file_ext
    last_backup = drive_client.search(f_name)

    if last_backup:
        del_item(last_backup[0]['id'])
    try:
        # ID папки, куда заливать файл
        fold_id = folder(BACKUP_FOLDER_NAME)
        f_mime_type = mimeTypes[file_ext(f_name)]
        drive_client.upload_file(f_name, f_path, f_mime_type, fold_id)
    except Exception as trouble:
        print(trouble, f_path, 'Terminating...', sep='\n')
    else:
        print(f"File: '{f_name}' successfully uploaded")


def restore():
    """ Восстановить некоторый файл из диска (игнорируя корзину):
        предлагаются до восстановления 3 пользовательских файла,
        выбор одного из них, далее поиск файлов на диске с похожим именем,
        если их нет – завершение, если файл один – его и скачать, если больше,
        то выводить имена и давать выбор, какой из них скачать;
    """
    # номер, имя базы, путь к ней, расширение файла
    from src.main.common_funcs import file_ext

    choices = {1: ("Main data", VOC_PATH, file_ext(VOC_PATH)),
               2: ("Self examples", SELF_EX_PATH, file_ext(SELF_EX_PATH)),
               3: ("Repeat log", REPEAT_LOG_PATH, file_ext(REPEAT_LOG_PATH))}

    print("What do you want to restore?")
    print('\n'.join([f"{key}. {val[0]}" for key, val in choices.items()]))

    # TODO: добавить проверку правильности
    choice = int(input())
    # тип выбранной для восстановления базы
    base_to_restore_type = choices[choice][2]

    # имя файла выбранной базы
    base_to_restore_name = file_name(choices[choice][1]).split('.')[0]

    # ключ для поиска айтемов для восстановления
    search_key = "name contains '{name}' and " \
                 "mimeType contains '{mimeType}' and " \
                 "trashed = false"
    _vals = {
        'name': base_to_restore_name,
        'mimeType': mimeTypes[base_to_restore_type]
    }

    # поиск файлов на диске
    found_items = drive_client.search(
        _vals, s_key=search_key)
    if not found_items:
        print(f"'{choices[choice][0]}' not found\nTerminating...")
        return
    elif len(found_items) == 1:
        f_id = found_items[0]['id']
        f_name = found_items[0]['name']
    else:
        print("Enter the number: ")
        print('\n'.join(f"{num}. {i['name']}"
                        for num, i in enumerate(found_items, 1)))
        # TODO: добавить проверку правильности
        choice = int(choice) - 1

        f_id = found_items[choice]['id']
        f_name = found_items[choice]['name']

    print(f"'{f_name}' restoring...")
    f_path = RESTORE_FOLDER_PATH + f"\\{add_to_file_name(f_name, '_restored')}"

    try:
        drive_client.download_file(f_id, f_path)
    except Exception as trouble:
        print(trouble, f_id, 'Terminating', sep='\n')
    else:
        print(f"File: '{f_path}' successfully restored")


def list_items(count=10):
    """ Показать первые n айтемов """
    print_items(drive_client.list_items(count))


def del_item(f_id):
    """ Удалить айтем по ID """
    try:
        drive_client.del_item(f_id)
    except errors.HttpError as trouble:
        print(trouble, f_id, 'Terminating...', sep='\n')
    except Exception as trouble:
        print(trouble, f_id, 'Terminating...', sep='\n')
    else:
        print(f"Item: '{f_id}' deleted permanently")


def search_folder_id(_name) -> str:
    """
    Вернуть ID папки вне корзины по имени или пустую
    строку, если найдено больше одной папки с таким
    именем или не найдено вовсе
    """
    s_key = "name = 'name' " \
            "and mimeType = 'mtype' " \
            "and trashed = false"
    _vals = {
        'name': _name,
        'mtype': mimeTypes['folder']
    }
    _folders = drive_client.search(_vals, s_key)

    if len(_folders) == 1:
        return _folders[0]['id']
    if len(_folders) > 1:
        print(f"More than onw folder named: '{_name}' found")
    # если фолдер не найден или найдено
    # больше одного фолдера с таким именем
    return ''


def folder(_name) -> str:
    """ Если папка на диске существует – вернуть её ID,
        иначе – создать новую и вернуть ID
    """
    fold_id = search_folder_id(_name)
    if not fold_id:
        print(f"Backup folder does not exist, creating...")
        fold_id = drive_client.create_folder(_name)
        print(f"Folder '{_name}' successfully created")
    return fold_id
