import re
from requests import get
from datetime import date
from os import access, F_OK
from json import loads, dump
from collections import Counter

from constants import REPEAT_LOG_PATH
from constants import SYNONYMS_SEARCH_URL, SYNONYMS_SEARCH_MODEL


def file_exist(f_path, ext=''):
    """ Существует ли файл с переданным именем и расширением """
    assert isinstance(f_path, str) and f_path, \
        f"Wrong f_path: '{f_path}', str expected, func – file_exist"
    assert isinstance(ext, str), \
        f"Wrong extention: '{ext}', str expected, func – file_exist"

    return access(add_ext(f_path, ext), F_OK)


def add_ext(f_name, ext=''):
    """ Добавить к имени файла расширение, если его нет """
    assert isinstance(f_name, str) and f_name, \
        f"Wrong f_name: '{f_name}', str expected, func – add_ext"
    assert isinstance(ext, str), \
        f"Wrong extention: '{ext}', str expected, func – add_ext"

    if f_name.endswith(f".{ext}"):
        return f_name
    return f"{f_name}.{ext}"


def file_name(f_path: str):
    """ Вернуть имя файла из его пути """
    assert isinstance(f_path, str) and f_path, \
        f"Wrong f_path: '{f_path}', str expected, func – get_file_name"

    return f_path.split('\\')[-1]


def file_ext(f_path: str):
    """ Вернуть расширение файла """
    assert isinstance(f_path, str), \
        f"Wrong f_path: '{f_path}', str expected, func – file_ext"

    if '.' not in f_path:
        return ''
    return f_path.split('.')[-1]


def add_to_file_name(f_path: str, add: str):
    """ Добавить что-то в конец имени файла до расширения """
    assert isinstance(f_path, str) and f_path, \
        f"Wrong f_path: '{f_path}', str expected, func – add_to_file_name"

    if '.' not in f_path:
        return f"{f_path}{add}"

    dot_rindex = f_path.rindex('.')
    return f"{f_path[:dot_rindex]}{add}{f_path[dot_rindex:]}"


def language(item: str):
    """ Есть русский символ в строке – rus, иначе – eng """
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', func – language"

    pattern = re.compile(r'[а-яА-ЯёЁ]')

    if pattern.findall(item):
        return 'rus'
    return 'eng'


def is_russian(item: str):
    return language(item) == 'rus'


def is_english(item: str):
    return language(item) == 'eng'


def str_to_date(string, swap=False):
    """ Преобразовать переданный айтем к date,
        поменять местами dd и mm если swap is True
    """
    if isinstance(string, date):
        return string

    assert isinstance(string, str), \
        f"Wrong date: '{string}', str expected, func – str_to_date"

    # разделителный символ находится автоматически
    # как самый частый не числовой и не буквенный
    # символ в строке
    split_symbol = max(list(filter(lambda x: not x.isalnum(), string)),
                       key=lambda x: string.count(x))

    filtered_string = ''.join(filter(lambda x: x.isdigit() or x in split_symbol, string))

    # убрать возможный мусор из строки
    day, month, year, *trash = filtered_string.split(split_symbol)
    day, month, year = int(day[:2]), int(month[:2]), int(year[:4])

    return date(year, day, month) if swap else date(year, month, day)


def load_json_dict(f_name):
    """ Вернуть словарь из json-файла """
    assert file_exist(f_name, 'json'), \
        f"Wrong file: {f_name}, func – load_json_dict"

    with open(add_ext(f_name, 'json'), 'r', encoding='utf-8') as file:
        res = ''.join(file.readlines())

    if res:
        return loads(res)
    return {}


def dump_json_dict(data, filename):
    """ Вывести словарь в json-файл с отступом = 2 """
    assert isinstance(data, dict), f"Wrong data: '{data}', func – dump_json_dict"

    with open(add_ext(filename, 'json'), 'w') as file:
        dump(data, file, indent=2)


def diff_words_id():
    """ Получить список уникальных ID самых в труднозапоминаемых
        (порядке убывания) слов из лога запоминаний;
        'значимость' – сумма количества ошибочных вариантов
        и количества выбора этих вариантов
    """
    log_dict = load_json_dict(REPEAT_LOG_PATH)

    # лог запоминаний бывает пустым
    if not log_dict:
        return []

    # сортировка по убыванию значимости
    most_error_count = dict(sorted(log_dict.items(),
                                   key=lambda t: len(t[1]) + sum(t[1].values()),
                                   reverse=True))

    # преобразование в пары: ID слова – его значимость
    id_to_worth = {key: len(val) + sum(val.values())
                   for key, val in most_error_count.items()}

    # пары: ID – количество слов, для которых данное является
    # ошибочным вариантом (при кол-ве выборов > 1)
    # TODO: переработать
    mistaken_variants = sum([[j for j in filter(lambda x: log_dict[i][x] != 1, log_dict[i])]
                             for i in most_error_count],
                            [])

    for key, val in Counter(mistaken_variants).items():
        if key in id_to_worth:
            id_to_worth[key] += val
        else:
            id_to_worth[key] = val

    # сортировка слов по значимости после её изменения
    id_to_worth = dict(sorted(id_to_worth.items(),
                              key=lambda x: x[1], reverse=True))

    return list(id_to_worth.keys())[:]


def get_synonyms(item):
    """ Получить список связнных слов/синонимов к заданному """
    # TODO: сортировка по близости слов
    assert isinstance(item, str), \
        f"Wrong item: '{item}', str expected, func – get_synonyms"

    word = item.lower().strip()
    response = get(SYNONYMS_SEARCH_URL.format(word=word, model=SYNONYMS_SEARCH_MODEL))

    assert response.ok, \
        f"Something went wrong, word: '{word}', func – get_synonyms {response}"

    try:
        items = list(list(response.json()[SYNONYMS_SEARCH_MODEL].values())[0].keys())
    except:
        return []

    linked_words = list(map(lambda x: ''.join(filter(str.isalpha, x.split('_')[0])), items))
    return list(set(linked_words))