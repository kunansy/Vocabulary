import datetime
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Tuple

import src.main.common_funcs as comm_funcs
import src.main.constants as const


# def init_from_xlsx(f_name: Path,
#                    out: Path = 'tmp',
#                    date=None):
#     """ Преобразовать xlsx файл в список объектов класса Word,
#         вывести их в файл с дополнением старого содержимого
#     """
#     # TODO: Редактировать после перехода к db
#     assert f_name.exists(), \
#         f"File: '{f_name}' does not exist, func – init_from_xlsx"
#
#     if not out.exists():
#         with out.open('w'):
#             pass
#
#     if date is None:
#         date = datetime.date.today()
#     else:
#         date = comm_funcs.str_to_date(date).strftime(const.DATEFORMAT)
#
#     assert f"[{date}]\n" not in out.open('r', encoding='utf-8').readlines(), \
#         f"Date '{date}' currently exists in the '{out}' file, func – init_from_xlsx"
#
#     rb = open_workbook(str(f_name))
#     sheet = rb.sheet_by_index(0)
#
#     # удаляется заглавие, введение и прочие некорректные данные
#     content = list(filter(lambda x: len(x[0]) and (len(x[2]) or len(x[3])),
#                           [sheet.row_values(i) for i in range(sheet.nrows)]))
#     content.sort(key=lambda x: x[0])
#
#     # группировка одинаковых слов вместе
#     content = itertools.groupby(
#         map(lambda x: Word(x[0], x[2], x[3]), content),
#         key=lambda x: (x._word, x.properties)
#     )
#
#     # суммирование одинаковых слов в один объект класса Word
#     result = [
#         functools.reduce(lambda res, elem: res + elem, list(group[1]), Word(''))
#         for group in content
#     ]
#
#     with out.open('a', encoding='utf-8') as f:
#         f.write(f"\n\n[{date}]\n")
#         f.write('\n'.join(map(str, result)))
#         f.write(f"\n[/{date}]\n")


class Word:
    __slots__ = (
        '_word', '_id', '_properties',
        '_english_defs', '_russian_defs', '_date')

    def __init__(self,
                 word: str = '',
                 date: datetime.date or str = None,
                 properties: set or str = None,
                 english_defs: List[str] = None,
                 russian_defs: List[str] = None) -> None:
        """
        :param word: str, word to learn.
        :param properties: set or str, language level, formal, ancient etc.
        :param date: datetime.date, in the date word has been learned.
        :param english_defs: list of str, English definitions of the word.
        :param russian_defs: list of str, Russian definitions of the word.
        """
        self._word = comm_funcs.fmt_str(word)
        self._id = comm_funcs.word_id(self._word)

        english_defs = english_defs or []
        russian_defs = russian_defs or []
        english_defs = (english_defs.split('; ') if
                        isinstance(english_defs, str) else english_defs)
        russian_defs = (russian_defs.split('; ') if
                        isinstance(russian_defs, str) else russian_defs)

        self._english_defs = english_defs
        self._russian_defs = russian_defs
        self._date = (comm_funcs.str_to_date(date) or
                      datetime.datetime.now().date())

        properties = properties or set()
        if isinstance(properties, str):
            # properties here like '[p1, ...]'
            properties = properties[1:-1].split(', ')

        properties = set(
            comm_funcs.fmt_str(prop)
            for prop in properties
            if prop
        )
        self._properties = properties

    @property
    def word(self) -> str:
        """
        :return: str, word.
        """
        return self._word

    @property
    def date(self) -> datetime.date:
        """
        :return: datetime.date, in this date word has been learned.
        """
        return self._date

    @property
    def id(self) -> str:
        """
        :return: str, word's id.
        """
        return self._id

    @property
    def english(self) -> List[str]:
        """
        :return: list of str, English defs.
        """
        return self._english_defs

    @property
    def russian(self) -> List[str]:
        """
        :return: list of str, Russian defs.
        """
        return self._russian_defs

    @property
    def properties(self) -> set:
        """
        :return: set, word's properties.
        """
        return self._properties

    def with_english(self) -> str:
        """
        :return: str, word with its English defs joined with '; '.
        """
        defs = '; '.join(self.english)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def with_russian(self) -> str:
        """
        :return: str, word with its Russian defs joined with '; '.
        """
        defs = '; '.join(self.russian)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def is_fit(self,
               *properties: str) -> bool:
        """
        :param properties: list of str, properties to check.
        :return: bool, whether the word fit with the all properties.
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
            min(self.date, other.date),
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
        item = comm_funcs.fmt_str(item)
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
        properties = f" [{', '.join(self.properties)}]" * bool(self.properties)
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
    __slots__ = '_data', 'graphic_name', '_cursor', '_db'
    _TABLE_NAME = 'Vocabulary'
    _RESTRICT_SHOW = 50

    def __init__(self,
                 db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError
        
        try:
            self._db = sqlite3.connect(db_path)
        except sqlite3.Error:
            print("Something went while connecting to the database")
            raise
        
        self._cursor = self._db.cursor()
        self._data = self._load()

        # filename with dynamics of learning
        self.graphic_name = const.TABLE_FOLDER / f"info_{self.get_date_range()}.xlsx"

    @classmethod
    def set_restrict_show(cls,
                          new_value: int or bool) -> None:
        """ Change the amount of shown in print words.
        If this value is False, all words'll be shown.

        :param new_value: int or bool, amount of shown in print words.
        :return: None.
        """
        cls._RESTRICT_SHOW = new_value

    def _load(self) -> List[Word]:
        data = self._cursor.execute(
            f""" SELECT word, date, properties, English, Russian from {self._TABLE_NAME} """
        )
        return [
            Word(*fields)
            for fields in data.fetchall()
        ]

    @property
    def data(self) -> List[Word]:
        return self._data

    @property
    def begin(self) -> datetime.date:
        """ Get the first day.

        :return: datetime.date, first date.
        """
        first_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date """
        ).fetchone()
        return comm_funcs.str_to_date(first_date[0])

    @property
    def end(self) -> datetime.date:
        """ Get the last day.

        :return: datetime.date, last date.
        """
        last_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date DESC """
        ).fetchone()
        return comm_funcs.str_to_date(last_date[0])

    def dynamic(self) -> Dict[datetime.date, int]:
        """
        :return: dict of datetime.date and str, pairs:
        date – amount of learned words in this date.
        """
        dates = self.get_date_list()
        return dict(Counter(dates))

    def max_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        max_day = max(self.dynamic().items(), key=lambda x: x[1])
        return tuple(max_day)

    def min_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        min_day = min(self.dynamic().items(), key=lambda x: x[1])
        return tuple(min_day)

    def avg_count_of_words(self) -> float:
        """ Average count of learned per day words.

        :return: float, this value.
        """
        count_of_words = self.dynamic().values()
        return sum(count_of_words) / len(count_of_words)

    def empty_days_count(self) -> int:
        """
        :return: int, amount of empty days.
        """
        pass

    def statistics(self) -> str:
        """ Статистика о словаре:
            продолжительность; среднее количество слов; всего слов изучено;
            могло бы быть изучно, но эти дни пустые (считается умножением
            количества пустых дней на среднее количество изученных в день слов);
            min/max количества изученных слов
        """
        # TODO
        # avg_value = self.avg_count_of_words()
        # empty_count = self.empty_days_count()
        #
        # avg_words_count = f"Average value = {avg_value}"
        # duration = f"Duration = {self.duration()}"
        # total_amount = f"Total = {len(self)}"
        # would_be_total = f"Would be total = {len(self) + avg_value * empty_count}\n" \
        #                  f"Lost = {self.avg_count_of_words() * empty_count} items per " \
        #                  f"{empty_count} empty days"
        # min_max = f"{self.max_day_info()}\n{self.min_day_info()}"
        #
        # return f"{duration}\n{avg_words_count}\n{total_amount}\n{would_be_total}\n\n{min_max}"

    def get_date_list(self) -> List[datetime.date]:
        """ Get all dates from the database.

        :return: list of datetime.date, all dates.
        """
        return list(map(Word.date, self.data))

    def get_date_range(self) -> str:
        """ Dateformat is default.

        :return: str, date of the first day - date of the last day.
        """
        begin = self.begin.strftime(const.DATEFORMAT)
        end = self.end.strftime(const.DATEFORMAT)
        return f"{begin}-{end}"

    def get_item_before_now(self,
                            days_count: int) -> List[Word]:
        """ Get words which have been learned on the date equals to
        the last date - given days count - 1 """
        pass

    def common_words_list(self,
                          reverse: bool = False) -> List[Word]:
        """
        :param reverse: bool, whether the sort'll be in reversed order.
        :return: sorted by alphabet list of all words in the Vocabulary.
        """
        all_words = self.data[:]
        all_words.sort(reverse=reverse)

        return all_words

    def duration(self) -> int:
        """
        :return: int, duration of the Vocabulary using.
        """
        return (self.end - self.begin).days + 1

    # def visual_info(self):
    #     kwargs = {
    #         'x_axis_name': 'Days',
    #         'y_axis_name': 'Amount of words',
    #         'chart_title': 'Words learning dynamic'
    #     }
    #     date_count = self.dynamic()
    #     create_doc.visual_info(self.graphic_name, date_count, **kwargs)
    #
    # def create_docx(self):
    #     """ Создать docx-файл со всемии словами словаря,
    #         отсортированными по алфавиту; Имя файла –
    #         date_range текущего словаря;
    #     """
    #     filename = header = self.get_date_range()
    #     create_doc.create_docx(
    #         filename,
    #         self.common_words_list(),
    #         header
    #     )
    #
    # def create_pdf(self):
    #     """ Создать pdf-файл со всемии словами словаря,
    #         отсортированными по алфавиту; Имя файла –
    #         date_range текущего словаря;
    #     """
    #     create_doc.create_pdf(
    #         self.get_date_range(),
    #         self.common_words_list()
    #     )

    def search(self,
               item: str or Word) -> List[Word]:
        """ Get all similar words, means the item is in the word or
        the word is in the item.

        :param item: str or Word, word to find.
        :return: list of similar to the item words.
        """
        # TODO: check id's similarity
        if not isinstance(item, (str, Word)):
            raise TypeError(f"Wrong item: '{item}'")

        if item not in self:
            raise ValueError(f"'{item}' not found")

        if isinstance(item, Word):
            item = item.word
        item = comm_funcs.fmt_str(item)

        similar_words = filter(
            lambda word: item in word.word or word.word in item,
            self.data
        )
        return list(similar_words)

    def show_graph(self) -> None:
        """ Show the graphic.

        :return: None.
        :exception FileExistsError: if the graphic doesn't exist.
        """
        if not self.graphic_name.exists():
            raise FileExistsError(f"{self.graphic_name} doesn't exist")

        os.system(self.graphic_name)

    def search_by_properties(self,
                             *properties: str) -> List[Word]:
        """ Find all words which fit with the given properties.

        :param properties: list of str, properties.
        :return: list of word, words which are fit with the given properties.
        """
        fit_words = filter(
            lambda word: word.is_fit(*properties),
            self.data
        )
        return list(fit_words)

    def search_by_id(self,
                     *ids: str) -> List[Word]:
        """ Find words by their ids.

        :param ids: list of str, ids to find words.
        :return: list of word, words which id is in the list.
        """
        words_by_id = filter(
            lambda word: word.id in ids,
            self.data
        )
        return list(words_by_id)

    def how_to_say_in_native(self) -> List[str]:
        """
        :return: list of str, only words.
        """
        words = map(
            lambda word: word.word,
            self.data
        )
        return list(words)

    def how_to_say_in_english(self):
        """
        :return: list of str, only English definitions of the words.
        """
        english_definitions = map(
            lambda word: '; '.join(word.english),
            self.data
        )
        return list(english_definitions)

    def backup(self):
        """ Backup главного словаря """
        # добавить в имя файла текущий объём
        pass

    def append(self,
               item: Word) -> None:
        pass

    def extend(self,
               items: List[Word]) -> None:
        pass

    def __add__(self,
                other: Word or List[Word]) -> Any:
        pass

    def __iadd__(self,
                 other: Word or List[Word]) -> Any:
        pass

    def __contains__(self,
                     item: str or Word) -> bool:
        """
        :param item: str or Word, word to check.
        :return: bool, whether the word is in the Vocabulary.
        """
        if isinstance(item, Word):
            item = item.word

        item = comm_funcs.fmt_str(item)
        words = self._cursor.execute(
            f""" SELECT word FROM {self._TABLE_NAME} WHERE word LIKE '%{item}%' """
        )
        return bool(words.fetchone())

    def __len__(self) -> int:
        """
        :return: int, amount of word in the data list.
        """
        return len(self.data)

    def __getitem__(self,
                    item: datetime.date) -> List[Word]:
        """ Get list of the words learned
        on the date or between the dates.

        :param item: date or slice, item to get words.
        :return: list of words.
        """
        if not isinstance(item, (datetime.date, slice)):
            raise TypeError(
                f"Wrong item type: '{type(item)}', "
                f"datetime.date or slice expected ")

        if isinstance(item, datetime.date):
            date_range = self._cursor.execute(
                f""" SELECT word, date, properties, English, Russian 
                     FROM {self._TABLE_NAME} WHERE date = {item}
                """
            )
        elif isinstance(item, slice):
            start = item.start or self.begin
            stop = item.stop or self.end

            if not isinstance((start, stop), datetime.date):
                raise TypeError(
                    f"Slice for '{type(start)}', '{type(stop)}'"
                    f" not defined, datetime.date expected")

            date_range = self._cursor.execute(
                f""" SELECT word, date, properties, English, Russian 
                     FROM {self._TABLE_NAME} WHERE date BETWEEN 
                     DATE('{start}') AND DATE('{stop}')
                """
            )

        return [
            Word(*fields)
            for fields in date_range.fetchall()
        ]

    def __call__(self,
                 item: str or Word) -> List[Word]:
        """ Get all found words.

        All the same to search().

        :param item: str ot Word, word to find.
        :return: list of words.
        """
        return self.search(item)

    def __str__(self) -> str:
        """
        :return: str, info about the Vocabulary and some words.
        """
        # TODO: restrict shown amount of examples
        pass

    def __bool__(self) -> bool:
        """
        :return: bool, whether the data list isn't empty.
        """
        return bool(self.data)

    def __iter__(self) -> iter:
        """
        :return: iter to data list.
        """
        return iter(self.data)

    def __hash__(self) -> int:
        """
        :return: int, hash from data list.
        """
        return hash(self.data)


# TODO: как сказать по-английски?
#  как сказать по-русски?
#  ряд синонимов,
#  ряд антонимов,
#  полные предложения без перевода,
#  предложения без запоминаемой лексемы с переводом,
#  ассоциации с русскими лексемами, картинкми, образами,
#  переписывать предложения, заменив русские слова английскими (русские ↔ английскимми)
