from backup_auth import Auth
from backup_auth import print_items


def backup(f_name, f_path):
    content_backup = Auth()
    last_backup = content_backup.search_item(f_name)

    if len(last_backup):
        del_file(last_backup[0]['id'])
    content_backup.upload_file(f_name, f_path)


def restore(f_name, f_path):
    restore = Auth()
    id = restore.search_item(f_name)[0]['id']
    restore.download_file(id, f_path)

    print(f"File: '{f_path}' successfully restored")


def list_files(count=10):
    content = Auth()
    print_items(content.list_items(count))


def search_items(name):
    content = Auth()
    print_items(content.search_item(name))


def del_file(f_id):
    delete = Auth()
    delete.del_file(f_id)

    print(f"Item: '{f_id}' deleted permanently")
