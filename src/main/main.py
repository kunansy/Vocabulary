import os
import random as rand
from datetime import (
    date as DATE
)
from functools import reduce
from itertools import groupby

from xlrd import open_workbook
from src.backup.backup_setup import *
from src.main.common_funcs import (
    today, word_id, up_word, file_name,
    is_russian, file_exist, str_to_date,
    diff_words_id, first_rus_index, add_to_file_name
)
from src.main.constants import *
from src.docs.create_doc import *
from src.repeat.repeat_setup import repeat
from src.trouble.trouble import Trouble

from src.examples.examples import *

def init_vocabulary_from_file(f_name=VOC_PATH):
    # TODO: Удалить после перехода к db
    assert file_exist(f_name), \
        f"Wrong file: '{f_name}', func – init_vocabulary_from_file"

    with open(f_name, 'r', encoding='utf-8') as file:
        _content = file.readlines()
        _dates = map(lambda x: str_to_date(x).strftime(DATEFORMAT),
                     filter(lambda x: x.startswith('[') and '/' not in x, _content))

        _begin = lambda elem: _content.index(f"[{elem}]\n")
        _end = lambda elem: _content.index(f"[/{elem}]\n")

        words_per_day = [WordsPerDay(map(Word, _content[_begin(i) + 1: _end(i)]), i)
                         for i in _dates]
    return words_per_day


def parse_str(string: str):
    """ Разбирает строку на: термин, транксрицпию,
        свойства, английское определение, русское
    """
    # TODO: Удалить после перехода к db
    word_properties, other = string.split(' – ')

    if '[' in word_properties:
        prop_begin = word_properties.index('[')
        word, properties = word_properties[:prop_begin], Properties(word_properties[prop_begin:])
    else:
        word = word_properties
        properties = Properties('')

    if word.count("|") == 2:
        trans_begin = word.index("|")
        word, transcription = word[:trans_begin], word[trans_begin:]

    else:
        transcription = ''

    if other:
        if is_russian(other):
            fri = first_rus_index(other)
            original = other[:fri].split(';')
            native = other[fri:].split(';')
        else:
            original = other.split(';')
            native = []
    else:
        original = []
        native = []

    if any(word.lower() in i.split() for i in original):
        print(f"'{word.capitalize()}' is situated in the definition too. It is recommended to replace it on ***")

    if any('.' in i for i in original):
        print(f"There is wrong symbol '.' in the definition of the word '{word}'")

    return word, transcription, properties, original, native


def init_from_xlsx(f_name, out='tmp',
                   date=None):
    """ Преобразовать xlsx файл в список объектов класса Word,
        вывести их в файл с дополнением старого содержимого
    """
    # TODO: Редактировать после перехода к db
    assert file_exist(f_name), \
        f"File: '{f_name}' does not exist, func – init_from_xlsx"

    if not file_exist(out):
        with open(out, 'w'): pass

    if date is None:
        date = today()
    else:
        date = str_to_date(date).strftime(DATEFORMAT)

    assert f"[{date}]\n" not in open(out, 'r', encoding='utf-8').readlines(), \
        f"Date '{date}' currently exists in the '{out}' file, func – init_from_xlsx"

    rb = open_workbook(f_name)
    sheet = rb.sheet_by_index(0)

    # удаляется заглавие, введение и прочие некорректные данные
    content = list(filter(lambda x: len(x[0]) and (len(x[2]) or len(x[3])),
                          [sheet.row_values(i) for i in range(sheet.nrows)]))
    content.sort(key=lambda x: x[0])

    # группировка одинаковых слов вместе
    content = groupby(map(lambda x: Word(word=x[0], original_def=x[2], native_def=x[3]), content),
                      key=lambda x: (x.word, x.properties))

    # суммирование одинаковых слов в один объект класса Word
    result = [reduce(lambda res, elem: res + elem, list(group[1]), Word('')) for group in content]

    with open(out, 'a', encoding='utf-8') as f:
        f.write(f"\n\n[{date}]\n")
        f.write('\n'.join(map(str, result)))
        f.write(f"\n[/{date}]\n")


def search_by_attribute(_sample: list, _item: str) -> str:
    """ Ищет в выборке объект класса Word, один из
        атрибутов которого соответствует искомому айтему
    """
    _trbl = Trouble(search_by_attribute, 'sth')
    assert isinstance(_sample, list) and _sample, \
        _trbl(_trbl=f"Wrong words_list: '{_sample}'")
    assert all(isinstance(i, Word) for i in _sample), \
        _trbl(_trbl="Wrong type samples items")
    assert isinstance(_item, str) and _item, \
        _trbl(_trbl=f"Wrong item: '{_item}'", _exp='str')

    _item = _item.lower().strip()
    # Если в переданном айтеме есть русский символ – соответствие
    # может быть только с русским определением
    if is_russian(_item):
        try:
            r_defs = map(lambda x: x.get_native(True).lower(), _sample)
            return list(filter(lambda x: x == _item, r_defs))[0]
        except:
            print(f"Word, attributes fit with: '{_item}' in the sample: '{_sample}', not found")
            return ''

    # Поиск соответствия в самих словах
    in_word = list(filter(lambda x: x.word == _item, _sample))
    try:
        if len(in_word):
            return in_word[0]
        orig_defs = map(lambda x: x.get_original(True).lower(), _sample)
        return list(filter(lambda x: x == _item, orig_defs))[0]
    except:
        print(f"Word, attributes fit with: '{_item}' in the sample: '{_sample}', not found")
        return ''


class Properties:
    __slots__ = ['properties']

    def __init__(self, properties):
        assert isinstance(properties, (str, list)), \
            f"Wrong properties: '{properties}', func – Properties.__init__"

        if isinstance(properties, str):
            properties = properties.replace('[', '').replace(']', '').split(',')
        properties = list(filter(len, map(lambda x: x.strip().lower(), properties)))

        self.properties = properties[:]

    def __eq__(self, other):
        if isinstance(other, Properties):
            return sorted(self.properties) == sorted(other.properties)
        return other.lower() in self.properties

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, item):
        return self == item

    def __getattr__(self, item):
        return self == item

    def __len__(self):
        return len(self.properties)

    def __add__(self, other):
        if isinstance(other, Properties):
            return Properties(self.properties + other.properties)

    def __hash__(self):
        return hash(tuple(self.properties))

    def __str__(self):
        return f"[{', '.join(map(str.capitalize, self.properties))}]"


class Word:
    __slots__ = (
        '_word', '_id', '_properties',
        '_english_defs', '_russian_defs')

    def __init__(self,
                 word: str = '',
                 properties: set = None,
                 english_defs: List[str] = None,
                 russian_defs: List[str] = None) -> None:
        """
        :param word: str, word to learn.
        :param properties: str, language level, formal, ancient etc.
        :param english_defs: list of str, original definitions of the word.
        :param russian_defs: list of str, native definitions of the word.
        """
        self._word = comm_func.fmt_str(word)
        self._id = comm_func.word_id(self._word)

        self._english_defs = english_defs or []
        self._russian_defs = russian_defs or []
        properties = properties or set()

        properties = set(
            comm_func.fmt_str(prop)
            for prop in properties
        )
        self._properties = properties

    @property
    def word(self) -> str:
        """ Get the word.

        :return: str, word.
        """
        return self._word

    @property
    def id(self) -> str:
        """ Get word's id.

        :return: str, word's id.
        """
        return self._id

    @property
    def english(self) -> List[str]:
        """ Get English defs of the word.

        :return: list of str, English defs.
        """
        return self._english_defs

    @property
    def russian(self) -> List[str]:
        """ Get Russian defs of the word.

        :return: list of str, Russian defs.
        """
        return self._russian_defs

    @property
    def properties(self) -> set:
        """ Get word's properties.

        :return: set, word's properties.
        """
        return self._properties

    def with_english(self) -> str:
        """ Get the word with its English defs.

        :return: str, word with its English defs.
        """
        defs = '; '.join(self.english)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def with_russian(self) -> str:
        """ Get the word with its Russian defs.

        :return: str, word with its Russian defs.
        """
        defs = '; '.join(self.russian)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def is_fit(self,
               *properties) -> bool:
        """
        :param properties: list of str, properties to check.
        :return: bool, whether the word fit with the properties.
        """
        return all(
            prop.lower() in self.properties
            for prop in properties
        )

    def __getitem__(self,
                    index: int or slice) -> str:
        """ Get symbol by the index or create str with slice.

        :param index: int or slice.
        :return: result str.
        """
        return self.word[index]

    def __iter__(self) -> iter:
        """
        :return: iter to the word.
        """
        return iter(self.word)

    def __add__(self,
                other: Any) -> Any:
        """ Join defs, properties of two objects.

        :param other: Word to join with self.
        :return: Word obj, joined items.
        :exception TypeError: if wrong type given.
        :exception ValueError: if the word aren't equal.
        """
        if not isinstance(other, Word):
            raise TypeError(f"Operator + between Word and str isn't supported")

        if self.word != other.word and self.word != other.word != '':
            raise ValueError("Operator + demands for the equal words")

        return Word(
            max(self.word, other.word),
            self.properties.union(other.properties),
            other.english + self.english,
            other.russian + self.russian
        )

    def __eq__(self,
               other: Any) -> bool:
        """ ==
        If other is int, comparing len of the word with it.
        If other is Word, comparing the words.

        :param other: int or Word to compare.
        :return: bool, whether word equals to the item.
        :exception TypeError: if wrong type given.
        """
        if isinstance(other, str):
            return self.word == other.strip()
        if isinstance(other, Word):
            return (self.word == other.word and
                    self.properties == other.properties)

        raise TypeError(f"Demanded str or Word, but '{type(other)}' given")

    def __ne__(self,
               other: Any) -> bool:
        """ != """
        return not (self == other)

    def __gt__(self,
               other: Any) -> bool:
        """ > """
        if isinstance(other, str):
            return self.word > other.strip()
        if isinstance(other, Word):
            return self.word > other.word

        raise TypeError(f"Demanded str or Word, but '{type(other)}' given")

    def __lt__(self,
               other: Any) -> bool:
        """ < """
        return self != other and not (self > other)

    def __ge__(self,
               other: Any) -> bool:
        """ >= """
        return self > other or self == other

    def __le__(self,
               other: Any) -> bool:
        """ <= """
        return self < other or self == other

    def __len__(self) -> int:
        """
        :return: int, length of the word.
        """
        return len(self.word)

    def __bool__(self) -> bool:
        """
        :return: bool, whether the word exists (not empty).
        """
        return bool(self.word)

    def __contains__(self,
                     item: str) -> bool:
        """
        :return: bool, whether the defs or the word contains given item.
        """
        item = comm_func.fmt_str(item)
        return any(
            item in definition
            for definition in [self.word] + self.english + self.russian
        )

    def __str__(self) -> str:
        """ Str format:
        `word [properties] – English defs; Russian defs.`

        Or without properties.

        :return: str this format.
        """
        word = self.word.capitalize()
        properties = f" [{self.properties}]" * bool(self.properties)
        eng = f"{'; '.join(self.english)}\t" * bool(self.english)
        rus = f"{'; '.join(self.russian)}" * bool(self.russian)

        return f"{word}{properties} – {eng}{rus}"

    def __hash__(self) -> int:
        """
        :return: int, hash the word and the properties.
        """
        return sum(self.word) + hash(self.properties)

    def __repr__(self) -> str:
        """ Str format:
            Word: ...
            Properties: ...
            English: ...
            Russian: ...

        :return: str this format.
        """
        res = f"Word: {self.word}\n" \
              f"Properties: {self.properties}\n" \
              f"English: {self.english}\n" \
              f"Russian: {self.russian}"
        return res


class Vocabulary:
    __slots__ = ['list_of_days', 'graphic_name']

    def __init__(self, f_name=VOC_PATH):
        assert file_exist(f_name), \
            f"Wrong file: {f_name}, func – Vocabulary.__init__"
        self.list_of_days = init_vocabulary_from_file(f_name)[:]

        # имя файла с графиком динамики изучения
        self.graphic_name = f"{TABLE_FOLDER}\\Information_{self.get_date_range()}.xlsx"

    def dynamic(self, df=None):
        """ Вернуть пары из непустых дней:
            дата – количество изученных слов
        """
        return {i.get_date(df): len(i) for i in self.list_of_days}

    def max_day_info(self):
        """ Информация о дне с max количеством
            слов: дата и само количество
        """
        max_day = max(self.list_of_days)
        return f"Maximum day {max_day.get_date(DATEFORMAT)}: {len(max_day)}"

    def min_day_info(self):
        """ Информация о дне с min количеством
            слов: дата и само количество
        """
        min_day = min(self.list_of_days)
        return f"Minimum day {min_day.get_date(DATEFORMAT)}: {len(min_day)}"

    def avg_count_of_words(self):
        """ Среднее количество изученных за день слов """
        return sum(len(i) for i in self.list_of_days) // self.duration()

    def empty_days_count(self):
        """ Количество пустых дней """
        return self.duration() - len(self.list_of_days)

    def statistics(self):
        """ Статистика о словаре:
            продолжительность; среднее количество слов; всего слов изучено;
            могло бы быть изучно, но эти дни пустые (считается умножением
            количества пустых дней на среднее количество изученных в день слов);
            min/max количества изученных слов
        """
        avg_value = self.avg_count_of_words()
        empty_count = self.empty_days_count()

        avg_words_count = f"Average value = {avg_value}"
        duration = f"Duration = {self.duration()}"
        total_amount = f"Total = {len(self)}"
        would_be_total = f"Would be total = {len(self) + avg_value * empty_count}\n" \
                         f"Lost = {self.avg_count_of_words() * empty_count} items per " \
                         f"{empty_count} empty days"
        min_max = f"{self.max_day_info()}\n{self.min_day_info()}"

        return f"{duration}\n{avg_words_count}\n{total_amount}\n{would_be_total}\n\n{min_max}"

    def get_date_list(self):
        """ Список дат DATE-объектами """
        return list(map(lambda x: x.get_date(), self.list_of_days))

    def get_date_range(self):
        """ Дата первого дня-дата последнего дня """
        return f"{self.begin().strftime(DATEFORMAT)}-" \
               f"{self.end().strftime(DATEFORMAT)}"

    def get_item_before_now(self, days_count: int):
        """ Вернуть непустой день, чей индекс = len - days_count """
        assert isinstance(days_count, int) and days_count >= 0, \
            f"Wrong days_count: '{days_count}', func – Vocabulary.get_item_before_now"

        index = len(self.list_of_days) - days_count - 1

        assert index >= 0, \
            f"Wrong index: '{index}', func – Vocabulary.get_item_before_now"

        return self.list_of_days[index]

    def common_words_list(self):
        """ Вернуть отсортированный список всех слов """
        return list(sorted(reduce(
            lambda result, element: result + element.get_content(),
            self.list_of_days,
            [])))

    def duration(self):
        """ Продолжительность ведения словаря """
        return (self.end() - self.begin()).days + 1

    def visual_info(self):
        kwargs = {
            'x_axis_name': 'Days',
            'y_axis_name': 'Count',
            'chart_title': 'Words learning dynamic'
        }
        date_count = self.dynamic(DATEFORMAT)
        visual_info(self.graphic_name, date_count, **kwargs)

    def create_docx(self):
        """ Создать docx-файл со всемии словами словаря,
            отсортированными по алфавиту; Имя файла –
            date_range текущего словаря;
        """
        create_docx(_content=self.common_words_list(),
                    f_name=self.get_date_range(),
                    _header=self.get_date_range())

    def create_pdf(self):
        """ Создать pdf-файл со всемии словами словаря,
            отсортированными по алфавиту; Имя файла –
            date_range текущего словаря;
        """
        create_pdf(_content=self.common_words_list(),
                   f_name=self.get_date_range())

    def search(self, item):
        """ Вернуть словарь из даты изучения в ключе и
            найденными словами из этого дня в значениях
        """
        # TODO: написать комментарий к принципу поиска, иправить его
        assert isinstance(item, (str, Word)), \
            f"Wrong item: '{item}', func – Vocabulary.search"
        assert len(item) > 1, \
            f"Wrong item: '{item}', func – Vocabulary.search"
        assert item in self, \
            f"Word is not in the Vocabulary '{item}', func – Vocabulary.search"

        item = item.lower().strip()

        return {i.get_date(DATEFORMAT): i[item] for i in filter(lambda x: item in x, self.list_of_days)}

    def show_graph(self):
        """ Показать график, создав его в случае отсутствия """
        if not file_exist(self.graphic_name):
            self.visual_info()

        os.system(self.graphic_name)

    def info(self):
        """ Создать xlsx файл с графиком изучения слов, вернуть информацию о словаре:
            пары: день – количество изученных слов; статистика """
        self.visual_info()
        dynamic = [f"{date}: {count}" for date, count in
                   self.dynamic(DATEFORMAT).items()]
        dynamic = '\n'.join(dynamic)

        return dynamic + f"\n{DIVIDER}\n" + self.statistics()

    def repeat(self, *items_to_repeat, **params):
        """ Запуск повторения уникальных слов при указанном mode;
            Выбор слов для повторения:
                1. Если это int: день, чей индекс равен текущему - int_value;
                2. Если это str или DATE: день с такой датой;
                3. random=n: один либо n случайных дней;
                4. most_difficult=n: n либо все слова из лога повторений
        """
        _rand = params.pop('rand', 0)
        most_difficult = params.pop('most_difficult', 0)
        repeating_days = []
        if _rand:
            repeating_days += rand.sample(self.list_of_days, _rand)
        if most_difficult:
            repeating_days += [WordsPerDay(self.search_by_id(*diff_words_id()[:most_difficult]), today())]
        if items_to_repeat:
            days_before_now = filter(lambda x: isinstance(x, int), items_to_repeat)
            dates = filter(lambda x: isinstance(x, (str, DATE)), items_to_repeat)

            days_before_now = list(map(self.get_item_before_now, days_before_now))
            dates = list(map(self.__getitem__, dates))

            repeating_days += dates + days_before_now

        assert len(repeating_days) != 0, \
            f"Wrong item to repeat, func – Vocabulary.repeat"

        repeating_days.sort(key=lambda x: x.get_date())

        if len(repeating_days) > 1 and repeating_days[0].get_date() != repeating_days[-1].get_date():
            window_title = f"{repeating_days[0].get_date()}-{repeating_days[-1].get_date()}, {len(repeating_days)} days"
        else:
            window_title = repeating_days[0].get_date(DATEFORMAT)

        # Переданные айтемы могут содержать одинаковые слова
        repeating_days = sum(list(map(WordsPerDay.get_content, repeating_days)), [])
        repeating_days = list(set(tuple(repeating_days)))

        repeat(repeating_days, window_title, **params)

    def begin(self):
        """ Вернуть дату первого дня DATE-объектом """
        return self.list_of_days[0].get_date()

    def end(self):
        """ Вернуть дату последнего дня DATE-объектом """
        return self.list_of_days[-1].get_date()

    def search_by_properties(self, *properties):
        """ Найти слова, удовлетворяющие переданным свойствам """
        # TODO: будет ли работать при sth.search_by_properties([prop1, prop2...])?
        return list(filter(lambda x: x.is_fit(*properties), self.common_words_list()))

    def search_by_id(self, *ids):
        """ Вернуть список слов, чьи ID равны ID переданным """
        if isinstance(ids[0], list):
            ids = sum(ids, [])

        assert all(isinstance(i, str) and len(i) == ID_LENGTH for i in ids), \
            f"Wrong ids: '{ids}', func – Vocabulary.search_by_id"

        # TODO: сортировать в соответствии с порядком id
        # id_to_word = list(map(lambda x: (x.get_id(), x), self.common_words_list()))
        # print(len(id_to_word))
        # print(list(filter(lambda x: )))

        # return list(filter(lambda x: x[0] in ids, id_to_word))

    def how_to_say_in_native(self):
        """ Вернуть только слова на изучаемом языке """
        return list(map(lambda x: x.word, self.common_words_list()))

    def how_to_say_in_original(self):
        """ Вернуть только нативные определения слов """
        return reduce(lambda res, elem: res + elem.native_only(def_only=True),
                      self.list_of_days, [])

    def backup(self):
        """ Backup главного словаря """
        f_name = file_name(VOC_PATH)
        # добавить в имя файла текущий объём
        f_name = add_to_file_name(f_name, f"_{len(self)}")
        print("Main data backupping...")
        backup(f_name, VOC_PATH)

    def __contains__(self, item):
        """ Есть ли слово (str или Word) или WordsPerDay
            с такой датой (только DATE) в словаре
        """
        if isinstance(item, str):
            return any(item.lower().strip() in i for i in self.list_of_days)
        if isinstance(item, Word):
            return any(item in i for i in self.list_of_days)
        if isinstance(item, DATE):
            if not any(i.date == item for i in self.list_of_days):
                # если нет равенства даты – проверка на вхождение даты в промежуток
                # [начало словаря; конец], и если дата попала в промежуток, то это
                # означает, что день с такой датой есть в словаре, но он пуст
                if self.begin() <= item <= self.end():
                    return True
                return False
            return True

    def __len__(self):
        """ Вернуть общее количество слов в словаре """
        return sum(len(i) for i in self.list_of_days)

    def __getitem__(self, _item):
        """ Вернуть WordsPerDay элемент с датой, равной item
            Если день с датой пуст – вернуть пустой WordsPerDay-объект

            :param _item: дата строкой, DATE-объектом или срезом
        """
        _trbl = Trouble(Vocabulary.__getitem__)
        assert isinstance(_item, (DATE, str, slice)), \
            _trbl(_item, "str or slice", _p='w_item')

        # TODO: it could be some troubles after empty days removing
        if isinstance(_item, slice):
            start = str_to_date(_item.start) if _item.start is not None else _item.start
            stop = str_to_date(_item.stop) if _item.stop is not None else _item.stop

            if start is not None and stop is not None and start > stop:
                raise ValueError(f"Start '{start}' cannot be more than stop '{stop}'")
            if start is not None and (start < self.begin() or start > self.end()):
                raise ValueError(f"Wrong start: '{start}'")
            if stop is not None and (stop > self.end() or stop < self.begin()):
                raise ValueError(f"Wrong stop: '{stop}'")

            begin = start if start is None else list(map(lambda x: x.get_date() == start, self.list_of_days)).index(True)
            end = stop if stop is None else list(map(lambda x: x.get_date() == stop, self.list_of_days)).index(True)
            # TODO: нет инита по списку
            # res = self.__class__()
            # res.list_of_days = self.list_of_days[begin:end]
            # return res

        item = str_to_date(_item)

        assert item in self, \
            f"Wrong date: '{item}' func – Vocabulary.__getitem__"
        # дата в словаре, но её нет в списке дат – день пуст
        if item not in self.get_date_list():
            return WordsPerDay([], item)

        return list(filter(lambda x: item == x.get_date(), self.list_of_days))[0]

    def __call__(self, _item, **kwargs):
        """ Вернуть все найденные слова строкой;
            Параметры поиска:
                1. by_def – искать в определениях; если в искомом элементе есть хоть
                    один русский символ – также искать в определениях;
        """
        assert isinstance(_item, (str, Word)) and len(_item) > 1, \
            Trouble(Vocabulary.__call__, _item, 'str or Word',_p='w_item')

        word = _item.lower().strip()
        by_def = kwargs.pop('by_def', False)
        word = f" – " * by_def + word

        try:
            res = [f"{date}: {S_TAB.join(map(lambda x: up_word(str(x), word), words))}"
                   for date, words in self.search(word).items()]
            return '\n'.join(res)
        except Exception as _err:
            return f"Word '{word}' not found, {_err}"

    def __str__(self):
        """ Вернуть все дни и информацию о словаре """
        return f"{self.info()}\n{DIVIDER}\n" + \
               f"\n{DIVIDER}\n\n".join(map(str, self.list_of_days))

    def __bool__(self):
        """ Стандартный списочный """
        return bool(self.list_of_days)

    def __iter__(self):
        """ Стандартный списочный """
        return iter(self.list_of_days)

    def __hash__(self):
        return hash(sum(hash(i) for i in self.list_of_days))


def backup_everything(*backupping_bases):
    """ Backup everything, supporting
        backup() method
    """
    assert all(hasattr(i, 'backup') for i in backupping_bases)

    for i in backupping_bases:
        i.backup()
        print()
    print("Backup completed")


if __name__ == "__main__":
    try:
        # init_from_xlsx('1_16_2020.xlsx')
        # dictionary = Vocabulary()
        # print(dictionary)
        # s_exams = SelfExamples()
        c_exams = ParallelCorpusExamples('Worth', 10)
        print(c_exams)
        # backup_everything(dictionary, s_exams, c_exams)
        pass
    except Exception as trouble:
        print(trouble)

# TODO: в поля классов добавить _ в начало имени

# TODO: как сказать по-английски?
#  как сказать по-русски?
#  ряд синонимов,
#  ряд антонимов,
#  полные предложения без перевода,
#  предложения без запоминаемой лексемы с переводом,
#  ассоциации с русскими лексемами, картинкми, образами,
#  переписывать предложения, заменив русские слова английскими (русские ↔ английскимми)
