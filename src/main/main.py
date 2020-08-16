import asyncio
import os
import random as rand
import sqlite3
import datetime
import functools
import itertools
from pathlib import Path
from typing import List, Dict, Any

# import asyncpg as asyncpg
# from xlrd import open_workbook

# import src.backup.setup as backup
import src.docs.create_doc as create_doc
import src.main.common_funcs as comm_func

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
#         date = comm_func.str_to_date(date).strftime(const.DATEFORMAT)
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
    __slots__ = '_data', 'graphic_name', '_cursor'

    def __init__(self,
                 db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError
        self._data = []
        data = sqlite3.connect(db_path)
        self._cursor = data.cursor()

        # имя файла с графиком динамики изучения
        self.graphic_name = const.TABLE_FOLDER / f"info_{self.get_date_range()}.xlsx"

    @property
    def data(self) -> List[Word]:
        return self._data

    def dynamic(self,
                df: str = None) -> Dict[datetime.date, int]:
        """ Вернуть пары из непустых дней:
            дата – количество изученных слов
        """
        # df = df or const.DATEFORMAT
        # TODO

    def max_day_info(self):
        """ Информация о дне с max количеством
            слов: дата и само количество
        """
        # TODO

    def min_day_info(self):
        """ Информация о дне с min количеством
            слов: дата и само количество
        """
        # TODO

    def avg_count_of_words(self):
        """ Среднее количество изученных за день слов """
        # TODO

    def empty_days_count(self):
        """ Количество пустых дней """
        # TODO

    def statistics(self):
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

    def get_date_list(self):
        """ Список дат DATE-объектами """
        return list(map(lambda x: x.get_date(), self.data))

    def get_date_range(self):
        """ Дата первого дня-дата последнего дня """
        begin = self.begin().strftime(const.DATEFORMAT)
        end = self.end().strftime(const.DATEFORMAT)
        return f"{begin}-{end}"

    def get_item_before_now(self,
                            days_count: int):
        """ Вернуть непустой день, чей индекс = len - days_count """
        index = len(self.data) - days_count - 1

        if index < 0:
            raise ValueError(f"Wrong index: '{index}'")

        return self.data[index]

    def common_words_list(self):
        """ Вернуть отсортированный список всех слов """
        all_words = functools.reduce(
            lambda result, element: result + element.get_content(),
            self.data,
            [])
        all_words.sort()
        return all_words

    def duration(self):
        """ Продолжительность ведения словаря """
        return (self.end() - self.begin()).days + 1

    def visual_info(self):
        kwargs = {
            'x_axis_name': 'Days',
            'y_axis_name': 'Amount of words',
            'chart_title': 'Words learning dynamic'
        }
        date_count = self.dynamic()
        create_doc.visual_info(self.graphic_name, date_count, **kwargs)

    def create_docx(self):
        """ Создать docx-файл со всемии словами словаря,
            отсортированными по алфавиту; Имя файла –
            date_range текущего словаря;
        """
        filename = header = self.get_date_range()
        create_doc.create_docx(
            filename,
            self.common_words_list(),
            header
        )

    def create_pdf(self):
        """ Создать pdf-файл со всемии словами словаря,
            отсортированными по алфавиту; Имя файла –
            date_range текущего словаря;
        """
        create_doc.create_pdf(
            self.get_date_range(),
            self.common_words_list()
        )

    def search(self,
               item: Any):
        #  -> Dict[datetime.date, List[Word]]
        """ Вернуть словарь из даты изучения в ключе и
            найденными словами из этого дня в значениях
        """
        if not isinstance(item, (str, Word)):
            raise TypeError(f"Wrong item: '{item}'")

        if item not in self:
            raise ValueError(f"'{item}' not found")

    def show_graph(self):
        """ Показать график, создав его в случае отсутствия """
        if not self.graphic_name.exists():
            raise FileExistsError(f"{self.graphic_name} doesn't exist")

        os.system(self.graphic_name)

    def info(self):
        """ Создать xlsx файл с графиком изучения слов, вернуть информацию о словаре:
            пары: день – количество изученных слов; статистика """
        # TODO

    def repeat(self, *items_to_repeat, **params):
        """ Запуск повторения уникальных слов при указанном mode;
            Выбор слов для повторения:
                1. Если это int: день, чей индекс равен текущему - int_value;
                2. Если это str или DATE: день с такой датой;
                3. random=n: один либо n случайных дней;
                4. most_difficult=n: n либо все слова из лога повторений
        """
        pass

    def begin(self):
        """ Вернуть дату первого дня DATE-объектом """
        pass

    def end(self):
        """ Вернуть дату последнего дня DATE-объектом """
        pass

    def search_by_properties(self, *properties):
        """ Найти слова, удовлетворяющие переданным свойствам """
        pass

    # def search_by_id(self, *ids):
    #     """ Вернуть список слов, чьи ID равны ID переданным """
    #     if isinstance(ids[0], list):
    #         ids = sum(ids, [])
    #
    #     assert all(isinstance(i, str) and len(i) == ID_LENGTH for i in ids), \
    #         f"Wrong ids: '{ids}', func – Vocabulary.search_by_id"
    #
    #     # TODO: сортировать в соответствии с порядком id
    #     # id_to_word = list(map(lambda x: (x.get_id(), x), self.common_words_list()))
    #     # print(len(id_to_word))
    #     # print(list(filter(lambda x: )))
    #
    #     # return list(filter(lambda x: x[0] in ids, id_to_word))

    def how_to_say_in_native(self):
        """ Вернуть только слова на изучаемом языке """
        pass

    def how_to_say_in_original(self):
        """ Вернуть только нативные определения слов """
        pass

    def backup(self):
        """ Backup главного словаря """
        # добавить в имя файла текущий объём
        pass

    def __contains__(self, item):
        """ Есть ли слово (str или Word) в словаре """
        if isinstance(item, str):
            return any(item.lower().strip() in i for i in self.data)
        if isinstance(item, Word):
            return any(item in i for i in self.data)

    def __len__(self):
        """ Вернуть общее количество слов в словаре """
        pass

    def __getitem__(self,
                    date: datetime.date) -> List[Word]:
        """ Get list of the words learned at the date.


        :param date: date or slice.
        """
        pass

    def __call__(self,
                 item: str or Word) -> List[Word]:
        """ Get all found words.

        :param item: word yto find.
        :return: list of words.
        """
        pass

    def __str__(self):
        """ Вернуть все дни и информацию о словаре """
        pass

    def __bool__(self):
        """ Стандартный списочный """
        return bool(self.data)

    def __iter__(self):
        """ Стандартный списочный """
        return iter(self.data)

    def __hash__(self):
        return hash(self.data)


if __name__ == "__main__":
    # bd_path = Path(f"D:\\Python\\Projects\\Vocabulary\\data\\user_data\\Vocabulary.db")
    # print(RESTORE_FOLDER_PATH)
    # backup("eng_vocabulary.db", bd_path)
    pass
    # list_items(10)
    # print(path)

    # with sqlite3.connect(bd_path) as bd:
    #     pass


# TODO: как сказать по-английски?
#  как сказать по-русски?
#  ряд синонимов,
#  ряд антонимов,
#  полные предложения без перевода,
#  предложения без запоминаемой лексемы с переводом,
#  ассоциации с русскими лексемами, картинкми, образами,
#  переписывать предложения, заменив русские слова английскими (русские ↔ английскимми)
