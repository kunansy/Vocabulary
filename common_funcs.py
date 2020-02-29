from os import access, F_OK


def file_exist(filename, extension=''):
    """ Существует ли файл с переданным именем и расширением """
    return access(add_ext(filename, extension), F_OK)


def add_ext(name, extension=''):
    """ Добавить к имени файла переданное расширение, если его в нём нет """
    return name if name.endswith(f".{extension}") else f"{name}.{extension}"


def file_name(f_path):
    """ Вернуть имя файла из его пути """
    assert isinstance(f_path, str) and f_path, \
        f"Wrong f_path: '{f_path}', str expected, func – get_file_name"

    return f_path.split('\\')[-1]


def add_to_file_name(f_path, add):
    """ Добавить что-то в конец имени файла до расширения """
    assert isinstance(f_path, str) and f_path, \
        f"Wrong f_path: '{f_path}', str expected, func – add_to_file_name"

    if '.' not in f_path:
        return f"{f_path}{add}"

    d_rindex = f_path.rindex('.')
    return f"{f_path[:d_rindex]}{add}{f_path[d_rindex:]}"