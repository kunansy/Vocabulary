__all__ = [
    'today', 'word_id', 'up_word', 'add_ext',
    'file_ext', 'clean_up', 'language', 'just_word',
    'load_json', 'dump_json', 'file_name', 'file_exist',
    'diff_words', 'is_russian', 'is_english', 'str_to_date',
    'get_synonyms', 'change_words', 'diff_words_id', 'first_rus_index',
    'add_to_file_name', 'backup_repeat_log', 'american_spelling',
]


import asyncio
import collections
import os
import re
from datetime import (
    date, datetime
)
from hashlib import sha3_512
from json import loads, dump

from aiohttp import ClientSession
from typing import List

from src.main.constants import *
from src.trouble.trouble import Trouble


def file_exist(f_path: str, ext='') -> bool:
    """
    Есть ли доступ к файлу

    :param f_path: путь к файлу, str
    :param ext: расширение файла, str
    """
    f_path = add_ext(f_path, ext)
    return os.access(f_path, os.F_OK)


def add_ext(f_name: str, ext='') -> str:
    """
    Добавить к имени файла расширение, если его нет

    :param f_name: путь/имя файла, str
    :param ext: необходимое расширение, str
    """
    if f_name.endswith(f".{ext}"):
        return f_name
    return f"{f_name}.{ext}"


def file_name(f_path: str) -> str:
    """ Вернуть имя файла из его пути """
    if '\\' in f_path:
        return f_path.split('\\')[-1]
    elif '/' in f_path:
        return f_path.split('/')[-1]
    else:
        return f_path


def file_ext(f_path: str) -> str:
    """
    Получить расширение файла

    :param f_path: путь к файлу
    :return: расширение файла как всё после последней
    точки, если оно есть, иначе – пустая строка
    """
    if '.' not in f_path:
        return ''
    return f_path.split('.')[-1]


def add_to_file_name(f_path: str, _add: str) -> str:
    """ Добавить что-то в конец имени файла до расширения """
    if '.' not in f_path:
        return f"{f_path}{_add}"

    # точка может быть и в имени файла,
    # нужен индекс последней
    dot_rindex = f_path.rindex('.')
    return f"{f_path[:dot_rindex]}{_add}{f_path[dot_rindex:]}"


def language(_item: str) -> str:
    """ Есть русский символ в строке – rus, иначе – eng """
    if re.findall(r'[а-яё]', _item, re.IGNORECASE):
        return 'rus'
    return 'eng'


def is_russian(_item: str) -> bool:
    return language(_item) == 'rus'


def is_english(_item: str) -> bool:
    return language(_item) == 'eng'


def str_to_date(_str, swap=False) -> date:
    """ 
    Преобразовать переданный айтем к date, 
    поменять местами dd и mm если swap is True
    """
    if isinstance(_str, date):
        if swap:
            return date(_str.year, _str.day, _str.month)
        return _str
    
    assert isinstance(_str, str), \
        Trouble(str_to_date, _str, _p='w_str')
        # f"Wrong date: '{_str}', str expected, func – str_to_date"

    # разделителный символ как самый частый не
    # числовой и не буквенный символ в строке
    split_symbol = max(list(filter(lambda x: not x.isalnum(), _str)),
                       key=lambda x: _str.count(x))

    filtered_string = ''.join(filter(lambda x: x.isdigit() or x in split_symbol,
                                     _str))

    # убрать возможный мусор из строки
    day, month, year, *trash = filtered_string.split(split_symbol)
    day, month, year = int(day[:2]), int(month[:2]), int(year[:4])

    return date(year, day, month) if swap else date(year, month, day)


def load_json(f_name: str) -> dict:
    """ Вернуть словарь из json-файла """
    assert file_exist(f_name, 'json'), \
        Trouble(load_json, f_name, _p='w_file')

    with open(add_ext(f_name, 'json'), 'r', encoding='utf-8') as file:
        _res = ''.join(file.readlines())

    if _res:
        return loads(_res)
    return {}


def dump_json(data: dict, f_name: str):
    """ Вывести словарь в json-файл с отступом = 2 """
    Trouble(dump_json, data, _p='w_dict')
    assert isinstance(data, dict), \
        f"Wrong data: '{data}', func – dump_json_dict"

    with open(add_ext(f_name, 'json'), 'w') as file:
        dump(data, file, indent=2)


def diff_words_id() -> list:
    """ 
    Получить список уникальных ID самых труднозапоминаемых 
    (в порядке убывания) слов из лога запоминаний;
    
    'значимость' – сумма количества ошибочных вариантов и 
    количества выбора этих вариантов
    """
    log_dict = load_json(REPEAT_LOG_PATH)

    # лог запоминаний бывает пустым
    if not log_dict:
        return []

    # подсчёт значимости
    worth = lambda x: len(x) + sum(x.values())
    # сортировка по убыванию значимости
    #most_error_count = dict(sorted(log_dict.items(),
    #                               key=lambda t: worth(t[1]),
    #                               reverse=True))

    # преобразование в пары: ID слова – его значимость
    id_to_worth = {key: worth(val)
                   for key, val in log_dict.items()}

    # пары: ID – количество слов, для которых данное является
    # ошибочным вариантом (при кол-ве выборов > 1)
    # TODO: переработать
    mistaken_variants = [[j for j in filter(lambda x: log_dict[i][x] != 1, log_dict[i])]
                         for i in log_dict],
    mistaken_variants = sum(mistaken_variants, [])

    for key, val in collections.Counter(mistaken_variants).items():
        if key in id_to_worth:
            id_to_worth[key] += val
        else:
            id_to_worth[key] = val

    # сортировка слов по значимости после её изменения
    id_to_worth = dict(sorted(id_to_worth.items(),
                              key=lambda x: x[1],
                              reverse=True))

    return list(id_to_worth.keys())[:]


async def fetch(url: str,
                sess: ClientSession) -> List[str]:
    async with sess.get(url) as resp:
        if resp.status == 200:
            try:
                json = await resp.json()
            except:
                return ['']
            else:
                return json


async def gsyns(url: str) -> List[str]:
    async with ClientSession() as sess:
        _task = asyncio.create_task(fetch(url, sess))
        return await asyncio.gather(_task)


def get_synonyms(item: str) -> List[str]:
    """ Получить список связнных слов/синонимов к заданному """
    # TODO: сортировка по близости слов
    assert isinstance(item, str) and item, \
        Trouble(get_synonyms, _p='w_str')

    url = SYNONYMS_SEARCH_URL.format(word=item.lower().strip(),
                                     model=SYNONYMS_SEARCH_MODEL)
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

    _future = asyncio.ensure_future(gsyns(url))
    resp = loop.run_until_complete(_future)

    try:
        items = list(resp[0][SYNONYMS_SEARCH_MODEL].values())
        items = list(
            i.replace('_X', ' sth/sb').replace('_', ' ')
            for i in items[0].keys()
        )
    except:
        return []
    else:
        return list(set(items))


def just_word(item: str) -> str:
    """ Вернуть слово без предлогов и прочего """
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', str expected, func – just_word"

    trash = ['sb', 'sth', 'not', 'no', 'do', 'doing', 'be', 'to',
             'the', 'a', 'an', 'one', 'etc', 'that', 'those',
             'these', 'this', 'or', 'and', 'can', 'may', 'might',
             'could', 'should', 'must', 'would', 'your', 'my']

    item = item.lower().replace("'", ' ').strip()
    if ' ' not in item and '/' not in item:
        return item
    if ' ' not in item and '/' in item:
        return item.split('/')[0]

    item = item.split()
    item = filter(lambda x: len(x) > 1, item)
    del_trash = list(filter(lambda x: x not in trash, item))
    del_preps = list(filter(lambda x: x not in ENG_PREPS, del_trash))

    if not del_preps:
        # если кроме предлогов ничего нет,
        # то вернуть первый предлог
        return clean_up(del_trash[0])
    else:
        item = del_preps

    item = list(filter(lambda x: len(x) > 1, item))
    # могут быть записаны три формы глагола через /
    if len(item) == 1 and '/' in item[0]:
        return clean_up(item[0].split('/')[0])
    if all('/' in i for i in item):
        return clean_up(item[0].split('/')[0])

    return clean_up(list(filter(lambda x: '/' not in x, item))[0])


def clean_up(item: str) -> str:
    """ Remove unalpha symbols except for '-' """
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', str expected, func – clean_up"
    return ''.join(filter(lambda x: x.isalpha() or x in '-', item))


def change_words(_str: str,
                 _item: str,
                 _f) -> str:
    """
    Изменить в строке все похожие слова (те, в которых есть
    item как составная часть), применив к ним функцию;
    регистр игнорируется
    """
    _trbl = Trouble(change_words, _p='w_str')
    assert isinstance(_str, str) and _str, _trbl(_str)
    assert isinstance(_item, str) and _item, _trbl(_item)
    assert callable(_f), _trbl(_f, 'callable object', _p='w_item')

    pattern = re.compile(f'\w*{_item}\w*', re.IGNORECASE)
    words = pattern.finditer(_str)

    if not words or len(_str) < len(_item):
        return _str
    for i in words:
        begin, end = i.start(), i.end()
        _str = _str[:begin] + _f(_str[begin:end]) + _str[end:]
    return _str


def first_rus_index(item: str) -> int:
    # TODO: Удалить после перехода к db
    rus_aplphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    return list(map(lambda x: x in rus_aplphabet, item.lower())).index(True)


def up_word(_str: str,
            _item: str) -> str:
    """ Поднять в строке регистр слов,
        которые содержат item
    """
    _trbl = Trouble(up_word, _p='w_str')
    assert isinstance(_item, str) and _item, _trbl(_item)
    assert isinstance(_str, str) and _str, _trbl(_str)
    assert len(_str) >= len(_item), \
        _trbl(f"Wrong len", _p=None)

    _item = _item.lower().strip()
    if _item not in _str.lower():
        return _str

    return change_words(_str, _item, str.upper)


def american_spelling(word: str) -> bool:
    """ Соответствует ли слово американской манере письма """
    assert isinstance(word, str) and word, \
        Trouble(american_spelling, word, _p='w_str')
    # wrong ends
    pattern = re.compile(r'\w*(uo|tre|nce|mm|ue|se|ll|re)\W', re.IGNORECASE)
    return bool(pattern.findall(word))


def word_id(_item: str) -> str:
    """
    Получить ID переданного строкой слова; ID – первые
    и последние восемь символов sha3_512 хеша этого слова
    """
    assert isinstance(_item, str), \
        Trouble(word_id, _item, _p='w_str')
    # пустой item – пустой ID
    if not _item:
        return ''

    _id = sha3_512(bytes(_item, encoding='utf-8')).hexdigest()
    return _id[:ID_LENGTH // 2] + _id[-ID_LENGTH // 2:]


def today(d_frmt=DATEFORMAT):
    """ Today: format is None – DATE, else – d_frmt """
    _res = datetime.now().date()
    return _res if d_frmt is None else _res.strftime(d_frmt)


def diff_words(_base):
    """ Most difficult words from json base """
    _ids = diff_words_id()
    return _base.search_by_id(_ids)


def backup_repeat_log():
    """ Backup лога повторений """
    from src.backup.backup_setup import backup

    print("Repeat log backupping...")
    f_name = file_name(REPEAT_LOG_PATH)
    backup(f_name, REPEAT_LOG_PATH)

