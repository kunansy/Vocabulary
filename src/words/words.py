#!/usr/bin/env python3
import abc
import datetime
import hashlib
import sqlite3
from pathlib import Path
from typing import List, NamedTuple, Set, Tuple, Any

# TODO: get it from ENV
DB_PATH = Path('eng_vocabulary.db')
DATE_FORMAT = "%Y-%m-%d"


def get_table_names(cursor: sqlite3.Cursor) -> List[str]:
    """ Get the names of tables in the database.

    :param cursor: sqlite3.Cursor to request to the database.
    :return: yield str, name of the table in the database.
    """
    tables = cursor.execute(
        """ SELECT name FROM sqlite_master WHERE type="table" """
    )
    for item in tables.fetchall():
        yield item[0]


def get_columns_names(cursor: sqlite3.Cursor,
                      table_name: str) -> List[str]:
    """ Get the names of columns in the table.
    Here it's assumed that the table exists.

    :param cursor: sqlite3.Cursor to request to the database.
    :param table_name: str, name of the table to get names
     of its columns.
    :return: yield str, name of the column.
    """
    columns = cursor.execute(
        f""" SELECT * FROM {table_name} """
    )
    for item in columns.description:
        yield item[0]


def print_scheme(cur: sqlite3.Cursor) -> None:
    for table in get_table_names(cur):
        print(f"{table}:".capitalize())
        for column in get_columns_names(cur, table):
            print(f"\t{column}")


def word_id(item):
    if not item:
        return ''

    _id = hashlib.sha3_512(bytes(item, encoding='utf-8')).hexdigest()
    return _id[:8] + _id[-8:]


class Word(NamedTuple):
    id: str
    date: datetime.date
    word: str
    properties: Set[str]
    transcription: str
    english: List[str]
    russian: List[str]

    @property
    def _values(self) -> Tuple:
        date = self.date.strftime(DATE_FORMAT)
        props = f"[{', '.join(self.properties)}]"
        eng = '; '.join(self.english)
        rus = '; '.join(self.russian)

        return self.id, date, self.word, props, self.transcription, eng, rus

    def __repr__(self) -> str:
        res = f"{self.__class__.__name__}(\n"
        res += '\n'.join(
            f"\t{key}={val}"
            for key, val in self._asdict().items()
        )
        return res + '\n)'

    def __str__(self) -> str:
        word = self.word.capitalize()
        tr = f"/{self.transcription}/" * bool(self.transcription)
        props = f" ({', '.join(self.properties)})" * (len(self.properties) > 0)
        eng = '; '.join(self.english)
        rus = '; '.join(self.russian)

        return f"{word}{props}{tr} – {eng}; {rus}"

    def __contains__(self,
                     item: str) -> bool:
        """
        :return: bool, whether the defs or the word contains given item.
        """
        pass

    def __len__(self) -> int:
        """
        :return: int, length of the word.
        """
        return len(self.word)

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
        pass

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

        if self.id != other.id and all([self.id, other.id]):
            raise ValueError("Operator + demands for the equal words")

        return Word(
            self.id,
            min(self.date, other.date),
            max(self.word, other.word),
            other.properties | self.properties,
            self.transcription or other.transcription,
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


class WordToLearn(NamedTuple):
    id: str
    word: str

    @property
    def _values(self) -> Tuple:
        return self.id, self.word


class SelfExample(NamedTuple):
    date: datetime.date
    sentence: str

    def __repr__(self) -> str:
        fields = '\n'.join(
            f"\t{key}={value}"
            for key, value in self._asdict().items()
        )
        return f"{self.__class__.__name__}(\n{fields}\n)"

    def __str__(self) -> str:
        return self.sentence


class DBTable(abc.ABC):
    FILE_PATH = DB_PATH
    TABLE_NAME = ''
    ITEM_TYPE = type

    templates = {
        "select":
            """ SELECT * FROM {table_name} """,
        "insert":
            """ INSERT INTO {table_name} ({fields}) VALUES ({items}) """,
        "delete":
            """ DELETE FROM {table_name} WHERE {field}={value} """
    }

    def __init__(self) -> None:
        self.__conn = sqlite3.connect(self.FILE_PATH)
        self.__cur = self.__conn.cursor()

        self.__content = self.from_db()

    def from_db(self) -> List:
        res = self.cursor.execute(
            self.templates['select'].format(table_name=self.TABLE_NAME)
        ).fetchall()

        return [
            self.parse_row(row)
            for row in res
        ]

    @abc.abstractmethod
    def parse_row(self,
                  row: Tuple) -> ITEM_TYPE:
        ...

    @property
    def connect(self) -> sqlite3.Connection:
        return self.__conn

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self.__cur

    @property
    def content(self) -> List[ITEM_TYPE]:
        return self.__content

    def add(self,
            item: ITEM_TYPE) -> None:
        if not isinstance(item, self.ITEM_TYPE):
            raise TypeError(
                f"{self.ITEM_TYPE} expected, but {type(item)} found")

        fields = ', '.join(f"'{i}'" for i in item._fields)
        values = ', '.join(f"'{i}'" for i in item._values)

        query = self.templates['insert'].format(
            table_name=self.TABLE_NAME, fields=fields, items=values
        )
        self.cursor.execute(query)
        self.connect.commit()

        self.__content += [item]

    def delete(self,
               item: ITEM_TYPE) -> None:
        self.cursor.execute(
            self.templates['delete'].format(
                table_name=self.TABLE_NAME, field='id', value=f"'{item.id}'")
        )
        self.connect.commit()

    def pop(self) -> ITEM_TYPE:
        item = self.__content.pop()
        self.delete(item)

        return item

    def table_scheme(self) -> str:
        return ', '.join(get_columns_names(self.cursor, self.TABLE_NAME))

    def db_scheme(self) -> str:
        res = ''
        for table in get_table_names(self.cursor):
            res += f"{table}:\n".capitalize()
            for column in get_columns_names(self.cursor, table):
                res += f"\t{column}\n"
        return res.rstrip()

    def __str__(self) -> str:
        return '\n'.join(
            f"{num}. {item}"
            for num, item in enumerate(self.content, 1)
        )

    def __iter__(self) -> iter:
        return iter(self.content)

    def __len__(self) -> int:
        return len(self.content)

    def __getitem__(self,
                    index: int) -> ITEM_TYPE:
        return self.content[index]


class Vocabulary(DBTable):
    TABLE_NAME = 'Vocabulary'
    ITEM_TYPE = Word

    def parse_row(self,
                  row: Tuple) -> Tuple:
        id_, date, word, props, tr, eng, rus = row

        date = datetime.datetime.strptime(date, DATE_FORMAT).date()
        props = set(props[1:-1].split(', '))
        eng = eng.split('; ')
        rus = rus.split('; ')

        return Word(id_, date, word, props, tr, eng, rus)


class WordsToLearn(DBTable):
    TABLE_NAME = 'words_to_learn'
    ITEM_TYPE = WordToLearn

    def parse_row(self,
                  row: Tuple) -> Tuple:
        return WordToLearn(*row)


class SelfExamples(DBTable):
    TABLE_NAME = 'self_examples'
    ITEM_TYPE = SelfExample

    def parse_row(self,
                  row: Tuple) -> Tuple:
        return SelfExample(*row)


def main() -> None:
    words_to_learn = WordsToLearn()
    vocabulary = Vocabulary()
    self_examples = SelfExamples()

    while True:
        word = input()
        id = word_id(word.lower().strip())

        words_to_learn.add(WordToLearn(id, word))
        print(f"'{word}' successfully added")


if __name__ == "__main__":
    main()

