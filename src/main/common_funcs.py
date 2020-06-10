__all__ = (
    'today', 'word_id', 'up_word',
    'clean_up', 'language', 'just_word',
    'load_json', 'dump_json', 'fmt_str',
    'is_russian', 'is_english', 'str_to_date',
    'extend_filename', 'american_spelling', 'mime_type',
    'get_synonyms', 'change_words', 'diff_words_id', 'first_rus_index'
)


import asyncio
import re
from datetime import (
    date, datetime
)
from hashlib import sha3_512
from json import loads, dump
from mimetypes import MimeTypes
from typing import List, Dict

from aiohttp import ClientSession

from src.main.constants import *
from src.trouble.trouble import Trouble


def fmt_str(item: str) -> str:
    """ Low and strip the string.

    :param item: strable, item to lowe and strip.
    :return: string, lowed and stripped item.
    :exception Trouble: if wrong type given.
    """
    if not hasattr(item, "__str__"):
        raise Trouble(fmt_str, item, _p='w_str')
    return str(item).lower().strip()


def mime_type(file: Path or str) -> str:
    """ Get mime type of a file.

    :param file: string or Path, item to get its mime type.
    :return: string, mime type if there's.
    :exception Trouble: if wrong type given.
    """
    if not isinstance(file, (str, Path)):
        raise Trouble(mime_type, file, "str or Path", _p='w_item')

    if isinstance(file, Path):
        file = file.name
    return MimeTypes().guess_type(file)[0]


def extend_filename(f_path: Path,
                    _add: str) -> Path:
    """ Add sth to the end of a filename (before extension).

    :param f_path: Path, path to the file.
    :param _add: string, item to add.
    :return: Path, path to the file with added str.
    :exception Trouble: if wrong type given.
    """
    trbl = Trouble(extend_filename, _t=True)
    if not isinstance(f_path, Path):
        raise trbl(f_path, f_path, "Path", _p='w_item')
    if not (isinstance(_add, str) and _add):
        raise trbl(_add, _p='w_str')

    if not f_path.suffix:
        return Path(f"{f_path}{_add}")

    return f_path.parent / f"{f_path.stem}{_add}{f_path.suffix}"


def language(_item: str) -> str:
    """ Define language of a string.

    :param _item: string, item to define.
    :return: string, if there's a Russian symbol – 'rus', else – 'eng'.
    """
    if re.findall(r'[а-яё]', _item, re.IGNORECASE):
        return 'rus'
    return 'eng'


def is_russian(_item: str) -> bool:
    return language(_item) == 'rus'


def is_english(_item: str) -> bool:
    return language(_item) == 'eng'


def str_to_date(item: str or date,
                swap: bool = False) -> date:
    """ Convert an item to date obj.

    :param item: string or date, item to convert.
    :param swap: bool, if it's True, swap day and month.
    :return: date, converted item.
    :exception Trouble: if wrong type given.
    """
    if isinstance(item, date):
        if swap:
            return date(item.year, item.day, item.month)
        return item
    trbl = Trouble(str_to_date, _t=True)
    if not (isinstance(item, str) and item):
        raise trbl(item, _p='w_str')

    item = fmt_str(item)
    s_sym = [
        i for i in item
        if not i.isdigit()
    ]
    s_sym = max(set(s_sym), key=s_sym.count)
    assert len(s_sym) is 1,\
        trbl("Length of split symbols list must equal 1")

    filtered_str = [
        i for i in item
        if i.isdigit() or i in s_sym
    ]
    filtered_str = ''.join(filtered_str)

    day, month, year = filtered_str.split(s_sym)
    day, month, year = int(day[:2]), int(month[:2]), int(year[:4])

    return date(year, day, month) if swap else date(year, month, day)


def load_json(f_path: Path) -> dict:
    """ Load json dict from the file.

    :param f_path: Path, path to the file.
    :return: dict, json dict from the file.
    :exception Trouble: if the file does not exist or its ext is not 'json'.
    """
    trbl = Trouble(load_json, _t=True)
    if not f_path.exists():
        raise trbl(f_path, _p='w_file')
    if f_path.suffix != '.json':
        raise trbl(f"Wrong file ext: {f_path.suffix}", ".json")

    with f_path.open('r', encoding='utf-8') as file:
        _res = ''.join(file.readlines())

    if _res:
        return loads(_res)
    return {}


def dump_json(data: dict,
              f_path: Path):
    """ Dump dict to json file with indent = 2

    :param data: dict, data to dump.
    :param f_path: Path, path to the file.
    :return: None.
    :exception Trouble: of wrong type given of file ext is not 'json'.
    """
    trbl = Trouble(dump_json, _t=True)
    if not (isinstance(data, dict) and data):
        raise trbl(data, _p='w_dict')
    if not isinstance(f_path, Path):
        raise trbl(f"Wrong file path type: '{f_path}'", "Path")
    if f_path.suffix != '.json':
        raise trbl(f"Wrong file ext: {f_path.suffix}", ".json")

    with f_path.open('w') as file:
        dump(data, file, indent=2)


def diff_words_id() -> List[str]:
    """ Get list of ID of the unique words, most difficult to remember,
    from the repeating log. They are sorted by worth decreasing.

    Worth = wrong variants count + count of erroneous choices.

    :return: List of str, words' IDs, sorted by worth decreasing.
    """
    log_dict = load_json(REPEAT_LOG_PATH)

    # repeat log can be empty
    if not log_dict:
        return []
    # worth calculating
    worth = lambda x: len(x) + sum(x.values())
    # sort by worth decrease
    most_error_count = sorted(
        log_dict.items(), key=lambda x: worth(x[1]), reverse=True)
    return [i[0] for i in most_error_count]


async def json_from_url_coro(url: str) -> Dict[str, str]:
    """ Coro, requesting to the url and getting json from there.
    If an exception while json obtaining catch, return empty dict.

    :param url: string, url to get json from there.
    :return: dict, {'search_model': {'word_1': its exact; int, ...}}
    """
    async with ClientSession() as sess:
        async with sess.get(url) as resp:
            try:
                json = await resp.json()
            except:
                return {}
            else:
                return json


def get_synonyms(item: str) -> List[str]:
    """ Get list of linked words/synonyms to the given word.

    :param item: string, word to find its linked words/synonyms.
    :return: list of str, linked words/synonyms sorted by excact decreasing.
    """
    trbl = Trouble(get_synonyms, _t=True)
    if not isinstance(item, str):
        raise trbl(item, _p='w_str')
    item = fmt_str(item)
    if ' ' in item or not item:
        raise trbl(item, "item without space symbol")

    url = SYNONYMS_SEARCH_URL.format(
        word=item, model=SYNONYMS_SEARCH_MODEL)
    resp = asyncio.run(json_from_url_coro(url))
    try:
        items = list(resp[SYNONYMS_SEARCH_MODEL].values())
        # these items are sorted
        items = [
            i.replace('_X', ' sth/sb').replace('_', ' ')
            for i in items[0].keys()
        ]
    except:
        return []
    else:
        return items


def just_word(item: str) -> str:
    """ Get the wort without prepositions etc

    :param item: string, item to remove preps etc from there.
    :return: string, items without preps etc.
    :exception Trouble: if wrong type given.
    """
    if not (isinstance(item, str) and item):
        raise Trouble(just_word, item, _p='w_str')

    item = fmt_str(item).replace("'", ' ')
    if not (' ' in item or '/' in item):
        return item
    elif '/' in item:
        return item.split('/')[0]

    trash = [
        'sb', 'sth', 'not', 'no', 'do', 'doing', 'be', 'to', 'the',
        'a', 'an', 'one', 'etc', 'that', 'those', 'these', 'this',
        'or', 'and', 'can', 'may', 'might', 'could', 'should',
        'must', 'would', 'your', 'my'
    ]
    item = item.split()
    item = filter(lambda x: len(x) > 1, item)
    del_trash = [
        i for i in item
        if i not in trash
    ]
    del_preps = [
        i for i in item
        if i not in ENG_PREPS
    ]

    if not del_preps:
        # if there's nothing except for preps, return first prep.
        return clean_up(del_trash[0])
    else:
        item = del_preps

    # it might be three verb forms via /.
    if len(item) == 1 and '/' in item[0]:
        return clean_up(item[0].split('/')[0])
    if all('/' in i for i in item):
        return clean_up(item[0].split('/')[0])

    res = [
        i for i in item
        if '/' not in i
    ]
    return clean_up(res[0])


def clean_up(item: str) -> str:
    """ Remove unalpha symbols from string except for '-'.

    :param item: string, item to remove wrong symbols from there.
    :return: string, filtered item.
    :exception Trouble: if wrong type given.
    """
    if not (isinstance(item, str) and item):
        raise Trouble(clean_up, item, _p='w_str')

    filtered = [
        i for i in item
        if i.isalnum() or i in '-'
    ]
    return ''.join(filtered)


def change_words(_str: str,
                 _item: str,
                 _f) -> str:
    """ Change all similar to the _item in the string
    (which has the _item like component) using the func to them.
    Register is ignored.

    :param _str: string, change items there.
    :param _item: string, item to change.
    :param _f: callable obj, func to call, changing the item.
    :exception Trouble: if wrong type given.
    """
    _trbl = Trouble(change_words, _p='w_str', _t=True)
    if not (isinstance(_str, str) and _str):
        raise _trbl(_str)
    if not (isinstance(_item, str) and _item):
        raise _trbl(_item)
    if not callable(_f):
        raise _trbl(_f, 'callable object', _p='w_item')

    words = re.finditer(fr'\w*{_item}\w*', _str, re.IGNORECASE)

    if not words or len(_str) < len(_item):
        return _str
    for i in words:
        begin, end = i.start(), i.end()
        _str = f"{_str[:begin]}{_f(_str[begin:end])}{_str[end:]}"
    return _str


def first_rus_index(item: str) -> int:
    # TODO: Удалить после перехода к db
    rus_aplphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    return list(map(lambda x: x in rus_aplphabet, item.lower())).index(True)


def up_word(_str: str,
            _item: str) -> str:
    """ Up all words in the str, which contain the item.

    :param _str: string, str to up word there.
    :param _item: string, word to up.
    :return: string, str with upped words.
    :exception Trouble: if wrong type given.
    """
    return change_words(_str, _item, str.upper)


def american_spelling(word: str) -> bool:
    """ Does the word fit with american spelling.

    :param word: string, word to check.
    :return: bool, fit – True, doesn't – False.
    :exception Trouble: if wrong item given.
    """
    if not (isinstance(word, str) and word):
        raise Trouble(american_spelling, word, _p='w_str', _t=True)
    # wrong ends
    pattern = re.compile(r'\w*(uo|tre|nce|mm|ue|se|ll|re)\W', re.IGNORECASE)
    # if there're wrong ends found, the word doesn't fit
    return bool(pattern.findall(word))


def word_id(item: str) -> str:
    """ Get words ID. ID – first and last 8 symbol from
    sha3_512 hash.

    :param item: string, item to get its ID.
    :return: string, ID.
    :exception Trouble: if wrong type given.
    """
    if not isinstance(item, str):
        raise Trouble(word_id, item, _p='w_str', _t=True)
    # empty item – empty ID
    if not item:
        return ''

    _id = sha3_512(bytes(item, encoding='utf-8')).hexdigest()
    return _id[:ID_LENGTH // 2] + _id[-ID_LENGTH // 2:]


def today(fmt=DATEFORMAT) -> str or date:
    """ Get today: date obj or str with the date format.

    :param fmt: string, date format.
    :return: string or date obj, format is None – date, else – str.
     with the date format.
    """
    _res = datetime.now().date()
    return _res if fmt is None else _res.strftime(fmt)
