from backup import Auth
from backup import print_items
from apiclient import errors

drive_client = Auth()


def backup(f_name, f_path):
    """ Залить файл на диск """
    last_backup = drive_client.search_item(f_name)

    if len(last_backup):
        del_item(last_backup[0]['id'])
    try:
        id = drive_client.upload_file(f_name, f_path)
    except Exception as trouble:
        print(trouble, f_path, 'Terminating', sep='\n')
    else:
        print(f"File: '{f_path}' successfully uploaded, ID: '{id}'")


def restore(f_name, f_path):
    """ Восстановить файл по имени """
    item = drive_client.search_item(f_name)

    if not item:
        print(f"File to restore: '{f_name}' not found\nTerminating")
        return
    if len(item) > 1:
        print(f"There are more than one file named: '{f_name}', "
              f"restore cannot be done\nTerminating")
        return

    id = item[0]['id']
    try:
        drive_client.download_file(id, f_path)
    except Exception as trouble:
        print(trouble, (f_name, id), 'Terminating', sep='\n')
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
        print(trouble, f_id, 'Terminating', sep='\n')
    except Exception as trouble:
        print(trouble, f_id, 'Terminating', sep='\n')
    else:
        print(f"Item: '{f_id}' deleted permanently")