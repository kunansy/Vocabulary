from backup import Auth
from backup import print_items


def backup(f_name, f_path):
    """ Залить файл на диск """
    content_backup = Auth()
    last_backup = content_backup.search_item(f_name)

    if len(last_backup):
        del_file(last_backup[0]['id'])
    id = content_backup.upload_file(f_name, f_path)
    print(f"File: '{f_path}' successfully uploaded, ID: '{id}'")


def restore(f_name, f_path):
    """ Восстановить файл по имени """
    restore = Auth()
    try:
        id = restore.search_item(f_name)[0]['id']
    except:
        print(f"Item to restore: '{f_name}' does not exist\nTerminating ")
    else:
        restore.download_file(id, f_path)
        print(f"File: '{f_path}' successfully restored")


def list_files(count=10):
    """ Показать первые n айтемов """
    content = Auth()
    print_items(content.list_items(count))


def search_items(name):
    """ Найти айтем по имени """
    content = Auth()
    print_items(content.search_item(name))


def del_file(f_id):
    """ Удалить айтем по ID """
    delete = Auth()
    try:
        delete.del_file(f_id)
    except:
        print(f"Something went wrong deleting item: '{f_id}'\nTerminating")
    else:
        print(f"Item: '{f_id}' deleted permanently")


def download_file(f_id, f_path):
    """ Скачать файл по ID """
    download = Auth()
    try:
        download.download_file(f_id, f_path)
    except:
        print(f"Something went wrong downloading item: '{f_id}'\nTerminating")
    else:
        print(f"File: '{f_path}' successfully downloaded")