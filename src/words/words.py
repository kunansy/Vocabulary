import datetime
import functools
import itertools
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Tuple

import xlrd

import src.docs.create_doc as create_doc
import src.main.common_funcs as comm_funcs
import src.main.constants as consts


def parse_cambridge_xlsx(f_name: Path,
                         date: datetime.date = None) -> List[Any]:
    """ Parse xlsx file from Cambridge Dictionary to list of words.

    There are words with one definition. Group the similar words
    with the different definitions to Word.

    :param f_name: Path, name of xlsx file.
    :param date: datetime.date, words have been learned on this date.
    :return: list of Words.
    """
    if not f_name.exists():
        raise FileExistsError("File doesn't exist")

    date = date or comm_funcs.today()

    rb = xlrd.open_workbook(str(f_name))
    sheet = rb.sheet_by_index(0)
    row_values = [
        sheet.row_values(row)
        for row in range(sheet.nrows)
    ]
    # remove empty row ([0]), header, description etc ([1])
    row_values = row_values[2:]
    row_values.sort(key=lambda x: x[0])
    content = [
        Word(word=field[0], date=date, properties=field[1],
             english=field[2], russian=field[3])
        for field in row_values
    ]
    # group the same words
    content = itertools.groupby(
        content, key=lambda word: (word.word, word.properties))

    words = []
    for group in content:
        # sum the same words to one
        words += [
            functools.reduce(
                lambda res, word_with_one_def: res + word_with_one_def,
                list(group[1]),
                Word(''))
        ]
    return words


class Word:
    __slots__ = (
        '_word', '_id', '_properties',
        '_english_defs', '_russian_defs', '_date')

    def __init__(self,
                 word: str = '',
                 date: datetime.date or str = None,
                 properties: List[str] or str = None,
                 english: str or List[str] = None,
                 russian: str or List[str] = None) -> None:
        """
        :param word: str, word. It will be lowered and stripped.
        :param properties: str or list of str, language level, formal, ancient etc.
        :param date: datetime.date, in this date the word has been learned.
        :param english: str or list of str, English definitions of the word.
        :param russian: str or list of str, Russian definitions of the word.
        """
        self._word = comm_funcs.fmt_str(word)
        self._id = comm_funcs.word_id(self._word)

        english = english or []
        russian = russian or []
        self._english_defs = (
            english.split('; ') if isinstance(english, str) else english)
        self._russian_defs = (
            russian.split('; ') if isinstance(russian, str) else russian)

        date = date or comm_funcs.today()
        self._date = comm_funcs.str_to_date(date)

        properties = properties or list()
        if isinstance(properties, str):
            if properties.startswith('[') and properties.endswith(']'):
                properties = properties[1:-1]
            properties = properties.split(', ')

        properties = [
            comm_funcs.fmt_str(prop)
            for prop in properties
            if prop
        ]
        properties = list(Counter(properties).keys())
        properties.sort()
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
    def properties(self) -> List[str]:
        """
        :return: list of str, word's properties.
        """
        return self._properties

    @property
    def fields(self) -> Dict:
        """
        :return: dict of str and datetime.date, all word fields.
        """
        props = f"[{', '.join(self.properties)}]" * bool(self.properties)

        english = '; '.join(self.english)
        russian = '; '.join(self.russian)

        return {
            'id': self.id,
            'date': self.date,
            'word': self.word,
            'properties': props,
            'English': english,
            'Russian': russian
        }

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
            comm_funcs.fmt_str(prop) in self.properties
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

        if self.word != other.word and all([self.word, other.word]):
            raise ValueError("Operator + demands for the equal words")

        return Word(
            max(self.word, other.word),
            min(self.date, other.date),
            other.properties + self.properties,
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
            item in field
            for field in [self.word] + self.english + self.russian
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
    _TEMPLATE_TO_WORD = "SELECT word, date, properties, " \
                        "English, Russian from {table} "

    def __init__(self,
                 db_path: Path) -> None:
        """" Create a connection to database, cursor,
        load Words from there.

        :param db_path: Path to the database.
        :return: None.
        :exception FileNotFoundError: if the database file doesn't exist.
        :exception sqlite3.Error: if something went wrong while connecting to db.
        """
        if not db_path.exists():
            raise FileNotFoundError("DB file doesn't exist")
        
        try:
            self._db = sqlite3.connect(db_path)
        except sqlite3.Error:
            print("Something went wrong while connecting to the database")
            raise
        
        self._cursor = self._db.cursor()
        self._data = self._load()

        # filename with dynamics of learning
        self.graphic_name = (consts.TABLE_FOLDER /
                             f"info_{self.get_date_span()}.xlsx")

    @classmethod
    def set_restrict_show(cls,
                          new_value: int or bool) -> None:
        """ Change the amount of shown in print words.
        If this value is False, all words will be shown.

        :param new_value: int or bool, amount of words shown in print.
        :return: None.
        """
        cls._RESTRICT_SHOW = new_value

    def _load(self) -> List[Word]:
        """
        :return: list of Words loaded from the database.
        """
        data = self._cursor.execute(
            self._TEMPLATE_TO_WORD.format(table=self._TABLE_NAME)
        )
        words = map(
            lambda fields: Word(*fields),
            data.fetchall()
        )
        return list(words)

    @property
    def data(self) -> List[Word]:
        """
        :return: list of Words, data.
        """
        return self._data

    @property
    def begin(self) -> datetime.date:
        """ Get the date of the first day.

        :return: datetime.date, first date.
        """
        first_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date """
        ).fetchone()
        return comm_funcs.str_to_date(first_date[0])

    @property
    def end(self) -> datetime.date:
        """ Get the date of the last day.

        :return: datetime.date, last date.
        """
        last_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date DESC """
        ).fetchone()
        return comm_funcs.str_to_date(last_date[0])

    @property
    def duration(self) -> int:
        """
        :return: int, duration of the Vocabulary using.
        """
        return (self.end - self.begin).days + 1

    def dynamic(self) -> Dict[datetime.date, int]:
        """
        :return: dict of datetime.date and int, pairs:
        date – amount of learned words in this date.
        """
        dates = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} """
        )
        dates = map(
            lambda date: comm_funcs.str_to_date(date[0]),
            dates.fetchall()
        )
        dates = list(dates)
        return dict(Counter(dates))

    def max_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        date_to_amount = max(self.dynamic().items(), key=lambda x: x[1])
        return date_to_amount

    def min_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        date_to_amount = min(self.dynamic().items(), key=lambda x: x[1])
        return date_to_amount

    def avg_count_of_words(self) -> int:
        """
        :return: int, average amount of words learned per one day.
        """
        count_of_words = self.dynamic().values()
        return sum(count_of_words) // len(count_of_words)

    def empty_days_count(self) -> int:
        """
        :return: int, amount of days, the user did nothing.
        """
        return (self.end - self.begin).days + 1 - len(self.get_date_list())

    def statistics(self) -> str:
        """ Statistics about Vocabulary, str format:
            Duration: ...
            Average amount of learned words: ...
            Empty days: ...
            Total: ...
            Would be total: ...
            Max day: ...
            Min day: ...

        Would be total = amount of empty days *
            average amount of words learned per one day

        :return: this str.
        """
        avg_per_day = self.avg_count_of_words()
        empty_days = self.empty_days_count()
        total = len(self)
        would_be_total = total + avg_per_day * empty_days

        max_date, max_amount = self.max_day_info()
        min_date, min_amount = self.min_day_info()
        min_date = min_date.strftime(consts.DATEFORMAT)
        max_date = max_date.strftime(consts.DATEFORMAT)

        return f"Duration: {self.duration} days\n" \
               f"Average amount of learned words: {avg_per_day}\n" \
               f"Empty days: {empty_days}\n" \
               f"Total: {total}\n" \
               f"Would be total: {would_be_total}\n" \
               f"Max day: {max_date} = {max_amount}\n" \
               f"Min day: {min_date} = {min_amount}"

    def get_date_list(self) -> List[datetime.date]:
        """ Get all dates when the user learned something.

        :return: list of datetime.date, all dates.
        """
        dates = self._cursor.execute(
            f""" SELECT DISTINCT date FROM {self._TABLE_NAME} """
        )
        dates = map(
            lambda date: comm_funcs.str_to_date(date[0]),
            dates.fetchall()
        )
        return list(dates)

    def get_date_span(self,
                      datefmt: str = consts.DATEFORMAT) -> str:
        """
        :param datefmt: str, date format.
        :return: str, date of the first day - date of the last day.
        """
        begin = self.begin.strftime(datefmt)
        end = self.end.strftime(datefmt)
        return f"{begin}-{end}"

    def get_item_before_now(self,
                            days_count: int) -> List[Word]:
        """ Get words which have been learned
        before the last date for days_count days.

        :param days_count: int, index of day before the last.
        :return: list of Words.
        :exception ValueError: if the index < 0.
        """
        dates = self.get_date_list()
        date_index = len(dates) - days_count - 1
        if date_index < 0:
            raise ValueError("Expected day doesn't exist")

        expected_date = dates[date_index]
        return self[expected_date]

    def all_words(self,
                  reverse: bool = False) -> List[Word]:
        """
        :param reverse: bool, whether the sort will be in reversed order.
        :return: sorted by alphabet list of all words.
        """
        all_words = self.data[:]
        all_words.sort(reverse=reverse)

        return all_words

    def visual_info(self) -> None:
        """ Create a xlsx file with dynamic of learning words.

        :return: None.
        """
        kwargs = {
            'x_axis_name': 'Days',
            'y_axis_name': 'Amount of words',
            'chart_title': 'Words learning dynamic'
        }
        date_to_count = self.dynamic()
        create_doc.visual_info(self.graphic_name, date_to_count, **kwargs)

    def create_docx(self) -> None:
        """ Create docx-file with all words, sorted by alphabet.

        Filename – date_span().

        :return: None.
        """
        filename = header = self.get_date_span()
        create_doc.create_docx(filename, self.all_words(), header)

    def create_pdf(self) -> None:
        """ Create pdf-file with all words, sorted by alphabet.

        Filename – date_span().

        :return: None.
        """
        create_doc.create_pdf(self.get_date_span(), self.all_words())

    def search(self,
               item: str or Word) -> List[Word]:
        """ Get all similar words, means the item is
        in the word or the word is in the item.

        :param item: str or Word, word to find.
        :return: list of words similar to the item.
        :exception TypeError: if wrong type given.
        """
        # TODO: check id's similarity
        if not isinstance(item, (str, Word)):
            raise TypeError(f"Wrong item: '{item}'")

        if isinstance(item, Word):
            item = item.word
        item = comm_funcs.fmt_str(item)

        similar_words = filter(
            lambda word: item in word.word or word.word in item,
            self.data
        )
        return list(similar_words)

    def show_graphic(self) -> None:
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

        :param ids: list of str.
        :return: list of words, words which ids are in the list.
        """
        words_by_id = filter(
            lambda word: word.id in ids,
            self.data
        )
        return list(words_by_id)

    def how_to_say_in_russian(self) -> List[str]:
        """
        :return: list of str, only words.
        """
        words = map(Word.word, self.data)
        return list(words)

    def how_to_say_in_english(self) -> List[str]:
        """
        :return: list of str, only English definitions of the words.
        """
        english_definitions = map(
            lambda word: '; '.join(word.english),
            self.data
        )
        return list(english_definitions)

    def backup(self) -> None:
        """ Backup the database to Google Drive.

        :return: None.
        """
        pass

    def _add_word_to_db(self,
                        item: Word) -> None:
        """ Add a word to the database.

        :param item: Word to add.
        :return: None.
        :exception TypeError: of wrong type given.
        """
        if not isinstance(item, Word):
            raise TypeError(f"Word expected, but '{type(item)}' given")

        self._cursor.execute(
            """ INSERT INTO Vocabulary (id, date, word, properties, 
            transcription, English, Russian) VALUES (:id, :date, 
            :word, :properties, '', :English, :Russian) """,
            item.fields
        )
        self._db.commit()

    def append(self,
               item: Word) -> None:
        """ Add a Word to the database.

        Update the data list.

        :param item: Word to add.
        :return: None.
        :exception TypeError: if wrong type given.
        """
        try:
            self._add_word_to_db(item)
        except Exception:
            raise
        self._data = self._load()

    def extend(self,
               items: List[Word]) -> None:
        """ Extend the database.

        Update the data list.

        :param items: list of Words to add.
        :return: None.
        :exception TypeError: if wrong type give.
        """
        for word in items:
            try:
                self._add_word_to_db(word)
            except Exception:
                raise
        self._data = self._load()

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
            f""" SELECT word FROM {self._TABLE_NAME} 
                  WHERE word LIKE '%{item}%' """
        )
        return bool(words.fetchone())

    def __len__(self) -> int:
        """
        :return: int, amount of learned words.
        """
        return len(self.data)

    def __getitem__(self,
                    item: datetime.date) -> List[Word]:
        """ Get the list of the words learned
        on the date or between the dates: [start; stop].

        :param item: date or slice of dates.
        :return: list of Words.
        :exception TypeError: if the wrong type given.
        :exception ValueError: if the start index > stop.
        """
        if not isinstance(item, (datetime.date, slice)):
            raise TypeError(f"Wrong type: '{type(item)}', "
                            f"datetime.date or slice expected")

        if isinstance(item, datetime.date):
            items_at_date = filter(
                lambda word: word.date == item,
                self.data
            )
        elif isinstance(item, slice):
            start = item.start or self.begin
            stop = item.stop or self.end

            if not isinstance((start, stop), datetime.date):
                raise TypeError(
                    f"Slice for '{type(start)}', '{type(stop)}'"
                    f" not defined, datetime.date expected")
            if start > stop:
                raise ValueError("Start must be <= than stop")

            items_at_date = filter(
                lambda word: start <= word.date <= stop,
                self.data
            )
        return list(items_at_date)

    def __call__(self,
                 item: str or Word) -> List[Word]:
        """ Find all found that are similar to the given one.

        All the same to search().

        :param item: str ot Word, word to find.
        :return: list of found words.
        """
        return self.search(item)

    def __str__(self) -> str:
        """
        :return: str, info about the Vocabulary and some words.
        """
        info = self.statistics()

        some_words = self.data
        is_shorted = False
        if self._RESTRICT_SHOW is not False:
            some_words = some_words[:self._RESTRICT_SHOW]
            is_shorted = True

        if is_shorted is True:
            some_words += ['...']
        some_words = '\n'.join(
            f"{num}. {word}"
            for num, word in enumerate(some_words)
        )

        return f"{info}\n\n{some_words}"

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
#  переписывать предложения, заменив русские
#  слова английскими (русские ↔ английскимми)
