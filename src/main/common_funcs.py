__all__ = (
    'today', 'word_id', 'clean_up',
    'language', 'just_word', 'load_json',
    'dump_json', 'fmt_str', 'is_russian', 'is_english',
    'str_to_date', 'extend_filename', 'american_spelling',
    'mime_type', 'get_synonyms', 'change_words', 'diff_words_id'
)

import asyncio
import datetime
import hashlib
import json
import re
import sqlite3
from mimetypes import MimeTypes
from pathlib import Path
from typing import List, Dict, Callable

import aiohttp

import src.main.constants as const

# URL and model of synonyms searching
SYNONYMS_SEARCH_URL = 'https://rusvectores.org/{model}/{word}/api/json/'
SYNONYMS_SEARCH_MODEL = 'tayga_upos_skipgram_300_2_2019'


def fmt_str(item: str) -> str:
    """ Low and strip the string.

    :param item: strable, item to low and strip.
    :return: str, lowed and stripped item.
    :exception TypeError: if the item is not strable.
    """
    if not hasattr(item, "__str__"):
        raise TypeError(f"Str expected, but '{type(item)}' given")
    return str(item).lower().strip()


def mime_type(file: Path or str) -> str:
    """ Get mime type of the file.

    :param file: str or Path, item to get its mime type.
    :return: str, mime type if there's.
    :exception TypeError: if wrong type given.
    """
    if not isinstance(file, (str, Path)):
        raise TypeError(f"Str or Path expected, but '{type(file)}' given")

    if isinstance(file, Path):
        file = file.name
    types = MimeTypes()
    types.add_type('application/octet-stream', '.db')
    return types.guess_type(file)[0]


def extend_filename(path: Path,
                    add: str) -> Path:
    """ Add sth to the end of the filename (before extension).

    :param path: Path to the file.
    :param add: str to add.
    :return: Path to the file with added str.
    :exception TypeError: if wrong type given.
    """
    if not isinstance(path, Path):
        raise TypeError(f"Path expected, {type(path)} given")

    if not path.suffix:
        return Path(f"{path}{add}")

    return path.parent / f"{path.stem}{add}{path.suffix}"


def language(item: str) -> str or None:
    """ Define language of the string: rus or eng.

    :param item: str to define its language.
    :return: str, 'rus', 'eng' or None if it isn't Rus or Eng.
    """
    if re.findall(r'[а-яё]', item, re.IGNORECASE):
        return 'rus'
    elif re.findall('r[a-z]', item, re.IGNORECASE):
        return 'eng'


def is_russian(item: str) -> bool:
    """ Whether the item contains Russian text """
    return language(item) == 'rus'


def is_english(item: str) -> bool:
    """ Whether the item contains English text """
    return language(item) == 'eng'


def str_to_date(item: str or datetime.date,
                swap: bool = False) -> datetime.date:
    """ Convert an item to date obj.

    :param item: str or date to convert.
    :param swap: bool, if it's True, swap day and month.
    :return: date, converted item.
    :exception AssertionError: if there're >= split
    symbols in the date.
    """
    if isinstance(item, datetime.date):
        if swap:
            return datetime.date(item.year, item.day, item.month)
        return item

    item = fmt_str(item)
    s_sym = [
        i for i in item
        if not i.isdigit()
    ]
    s_sym = max(set(s_sym), key=s_sym.count)

    assert len(s_sym) is 1, "Split symbol must be single"

    filtered_str = [
        i for i in item
        if i.isdigit() or i in s_sym
    ]
    filtered_str = ''.join(filtered_str)

    day, month, year = filtered_str.split(s_sym)
    day, month, year = int(day[:2]), int(month[:2]), int(year[:4])

    if swap:
        return datetime.date(year, day, month)
    return datetime.date(year, month, day)


def load_json(f_path: Path) -> Dict[str, str]:
    """ Load json dict from the file.

    :param f_path: Path to the file.
    :return: json dict of str.
    :exception FileExistsError: if the file doesn't exist.
    :exception TypeError: if the file extension isn't json.
    """
    if not f_path.exists():
        raise FileExistsError("File doesn't exist")
    if f_path.suffix != '.json':
        raise TypeError(f"Wrong file ext: {f_path.suffix}, json expected")

    with f_path.open('r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except Exception:
            return dict()
        return data


def dump_json(data: dict,
              f_path: Path) -> None:
    """ Dump dict to json file with indent = 2.

    :param data: dict to dump.
    :param f_path: Path to the file.
    :return: None.
    """
    with f_path.open('w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)


def diff_words_id() -> List[str]:
    """ Get list of ID of the unique words, most difficult to remember
    from the repeating log. They are sorted by worth decreasing.

    Worth = wrong variants count + count of erroneous choices.

    :return: List of str, words' IDs, sorted by worth decreasing.
    """
    log_dict = load_json(const.REPEAT_LOG_PATH)

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
    """ Coro, requesting to the URL and getting json from there.
    If an exception while json obtaining catch, return empty dict.

    :param url: str, URL to get json from there.
    :return: dict, {'search_model': {'word_1': its exact; int, ...}}
    """
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            try:
                json = await resp.json()
            except:
                return dict()
            return json


def get_synonyms(word: str) -> List[str]:
    """ Get linked words/synonyms to the given one.

    :param word: str, word to find its linked words/synonyms.
    :return: list of str, linked words/synonyms sorted by exact decreasing.
    :exception ValueError: if the word is empty or contains space symbol.
    """
    word = fmt_str(word)
    if ' ' in word or not word:
        raise ValueError(
            f"Str without spaces expected, but '{word}' given")

    url = SYNONYMS_SEARCH_URL.format(
        word=word, model=SYNONYMS_SEARCH_MODEL)
    resp = asyncio.run(json_from_url_coro(url))
    try:
        synonyms = list(resp[SYNONYMS_SEARCH_MODEL].values())
        # these items are sorted
        synonyms = [
            i.replace('_X', ' sth/sb').replace('_', ' ')
            for i in synonyms[0].keys()
        ]
    except Exception:
        return []
    else:
        return synonyms


def just_word(item: str) -> str:
    """ Get the wort without prepositions etc

    :param item: string, item to remove preps etc from there.
    :return: string, items without preps etc.
    :exception Trouble: if wrong type given.
    """
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
        if i not in const.ENG_PREPS
    ]

    if not del_preps:
        # if there's nothing except for preps, return first prep.
        return clean_up(del_trash[0])
    else:
        item = del_preps

    # it might be three verb forms via /.
    if len(item) is 1 and '/' in item[0]:
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

    :param item: str, item to clean.
    :return: filtered str.
    """
    filtered = [
        i for i in item
        if i.isalnum() or i in '-'
    ]
    return ''.join(filtered)


def change_words(full_str: str,
                 item: str,
                 f: Callable) -> str:
    """ Change all words similar to the item by using the function.
    Register is ignored.

    :param full_str: str, change items here.
    :param item: str to change.
    :param f: callable obj, changing the item.
    """
    return re.sub(item, f(item), full_str, flags=re.IGNORECASE)


def american_spelling(word: str) -> bool:
    """ Whether the word fit with american spelling.

    :param word: str, word to check.
    :return: bool, fit or not.
    """
    # wrong ends
    pattern = re.compile(r'\B*(uo|tre|nce|mm|ue|se|ll|re)\b+', re.IGNORECASE)
    # the word doesn't fit if there's a wrong end found
    return bool(pattern.search(word))


def word_id(item: str) -> str:
    """ Get words ID.

    ID – first and last 8 symbol from sha3_512 hash.

    :param item: str to get its ID.
    :return: str, ID.
    """
    # empty item – empty ID
    if not item:
        return ''

    _id = hashlib.sha3_512(bytes(item, encoding='utf-8')).hexdigest()
    return _id[:const.ID_LENGTH // 2] + _id[-const.ID_LENGTH // 2:]


def today(fmt: str = const.DATEFORMAT) -> str or datetime.date:
    """ Get today: date obj or str with the date format.

    :param fmt: string, date format.
    :return: str or date, format is None – date, else – str.
    """
    date = datetime.datetime.now().date()

    if fmt:
        return date.strftime(fmt)
    return date


def create_connection(db_path: Path) -> sqlite3.Connection:
    """ Create a connection to the database.

    Here it's assumed that the file exists.

    :param db_path: Path to the database file.
    :return: sqlite3.Connection to the database.
    :exception sqlite3.Error: if something went wrong.
    """
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error:
        raise
    return conn


def get_table_names(cursor: sqlite3.Cursor) -> List[str]:
    """ Get the names of tables in the database.

    :param cursor: sqlite3.Cursor to request to the database.
    :return: list of str, name of the tables in the database.
    """
    tables = cursor.execute(
        """ SELECT name FROM sqlite_master WHERE type="table" """
    )
    return [
        item[0]
        for item in tables.fetchall()
    ]


def get_columns_names(cursor: sqlite3.Cursor,
                      table_name: str) -> List[str]:
    """ Get the names of columns in the table.

    Here it's assumed that the table exists.

    :param cursor: sqlite3.Cursor to request to the database.
    :param table_name: str, name of the table to get names of its columns.
    :return: list of str, names of the columns
    """
    columns = cursor.execute(
        f""" SELECT * FROM {table_name} """
    )
    return [
        i[0]
        for i in columns.description
    ]
