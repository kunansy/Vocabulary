import re
from requests import get
from datetime import date
from os import access, F_OK
from json import loads, dump
from collections import Counter

from constants import REPEAT_LOG_PATH, PREPOSTIONS
from constants import SYNONYMS_SEARCH_URL, SYNONYMS_SEARCH_MODEL


def file_exist(f_path, ext=''):
    """ Есть ли доступ к файлу с переданным именем и расширением """
    f_path = add_ext(f_path, ext)
    return access(f_path, F_OK)


def add_ext(f_name, ext=''):
    """ Добавить к имени файла расширение, если его нет """
    if f_name.endswith(f".{ext}"):
        return f_name
    return f"{f_name}.{ext}"


def file_name(f_path: str):
    """ Вернуть имя файла из его пути """
    if '\\' in f_path:
        return f_path.split('\\')[-1]
    elif '/' in f_path:
        return f_path.split('/')[-1]


def file_ext(f_path: str):
    """ Вернуть расширение файла """
    if '.' not in f_path:
        return ''
    return f_path.split('.')[-1]


def add_to_file_name(f_path: str, add: str):
    """ Добавить что-то в конец имени файла до расширения """
    if '.' not in f_path:
        return f"{f_path}{add}"

    dot_rindex = f_path.rindex('.')
    return f"{f_path[:dot_rindex]}{add}{f_path[dot_rindex:]}"


def language(item: str):
    """ Есть русский символ в строке – rus, иначе – eng """
    if re.findall(r'[а-яё]', item, re.IGNORECASE):
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

    # разделителный символ как самый частый не
    # числовой и не буквенный символ в строке
    split_symbol = max(list(filter(lambda x: not x.isalnum(), string)),
                       key=lambda x: string.count(x))

    filtered_string = ''.join(filter(lambda x: x.isdigit() or x in split_symbol,
                                     string))

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

    # подсчёт значимости
    worth = lambda x: len(x) + sum(x.values())
    # сортировка по убыванию значимости
    most_error_count = dict(sorted(log_dict.items(),
                                   key=lambda t: worth(t[1]),
                                   reverse=True))

    # преобразование в пары: ID слова – его значимость
    id_to_worth = {key: worth(val)
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
                              key=lambda x: x[1],
                              reverse=True))

    return list(id_to_worth.keys())[:]


def get_synonyms(item):
    """ Получить список связнных слов/синонимов к заданному """
    # TODO: сортировка по близости слов
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', str expected, func – get_synonyms"

    url = SYNONYMS_SEARCH_URL.format(word=item.lower().strip(),
                                     model=SYNONYMS_SEARCH_MODEL)
    response = get(url)

    assert response.ok, \
        f"{response}, func – get_synonyms"

    try:
        res_json = response.json()
        items = list(res_json[SYNONYMS_SEARCH_MODEL].values())
        items = list(items[0].keys())
    except:
        return []
    # TODO: style
    linked_words = list(map(lambda x: ''.join(filter(str.isalpha, x.split('_')[0])), items))
    return list(set(linked_words))


def just_word(item: str):
    """ Вернуть слово без предлогов и прочего """
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', str expected, func – just_word"

    trash = ['sb','sth', 'not', 'no', 'do', 'doing', 'be', 'to',
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
    del_preps = list(filter(lambda x: x not in PREPOSTIONS, del_trash))

    if not del_preps:
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


def clean_up(item: str):
    """ Remove unalpha symbols except for '-' """
    assert isinstance(item, str) and item, \
        f"Wrong item: '{item}', str expected, func – clean_up"
    return ''.join(filter(lambda x: x.isalpha() or x in '-', item))


def change_words(string: str, word: str, changing):
    """ Изменить в строке все похожие слова (те, в которых есть
        item как составная часть), применив к ним changing (callable obj)
    """
    assert isinstance(string, str) and string, \
        f"Wrong string: '{string}', str expected, func – change_words"
    assert isinstance(word, str) and word, \
        f"Wrong word: '{word}', str expected, func – change_words"
    assert callable(changing), \
        f"Wrong changing model, callable object expected, func – change_words"

    pattern = re.compile(f'\w{word}\w', re.IGNORECASE)
    words = pattern.finditer(string)

    if not words or len(string) < len(word):
        return string

    # TODO: обойтись как-то без медленного for/ускорить его
    for i in words:
        begin, end = i.start(), i.end()
        # TODO: replace нельзя: string='thin... thing', item='in',
        #  в words есть thin – replace меняет все thin → thing = THINg;
        #  можно ли как-то иначе?
        string = string[:begin] + changing(string[begin:end]) + string[end:]
    return string


def trouble(item, problem, expected=''):
    """ Принимает функцию, из которой вызывается,
        возникшую проблему и что ожидалось (тип файла);

        Возращает проблему, что ожидалось (если передано), имя файла,
        класса (если передан метод класса) и функции, где произошла ошибка
    """
    class_name = ''
    if 'method' in item.__class__.__name__:
        # если передан объект класса, то показать имя класса
        class_name = f"{item.__self__.__class__.__name__}."
    func_name = item.__name__
    expected = f"{expected} expected," * bool(expected)
    return f"{problem}, {expected} {file_name(__file__)}.{class_name}{func_name}"