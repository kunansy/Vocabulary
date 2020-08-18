__all__ = 'SelfExamples'

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import (
    List, Callable, Any
)

import src.main.common_funcs as comm_funcs


class SelfExamples:
    """ Working with self examples """
    __slots__ = '_sentences', '_marker', '_db', '_cursor'
    _TABLE_NAME = 'self_examples'

    def __init__(self,
                 db_path: Path,
                 marker: Callable = None) -> None:
        """ Create a connection to the database,
        load all sentences from there.

        :param db_path: Path to the database.
        :param marker: function to highlight searched words in sentences.
        :return: None.
        :exception FileExistsError: if the file doesn't exist.
        :exception sqlite3.Error: if something went wrong while
        creating connection to the database.
        :exception ValueError: if the database doesn't contain the table.
        """
        if not db_path.exists():
            raise FileExistsError(f"File '{db_path}' not found")

        try:
            self._db = comm_funcs.create_connection(db_path)
        except sqlite3.Error:
            print("Error while connecting to the database, working stopped")
            raise

        self._cursor = self._db.cursor()
        if self._TABLE_NAME not in comm_funcs.get_table_names(self._cursor):
            raise ValueError("Database doesn't contain the table")

        self._sentences = self._load()

        # function to highlight searched words in examples
        self._marker = marker

    def _load(self) -> List[str]:
        """ Get all sentences from the table in the database.

        :return: list of str, all sentences.
        """
        data = self._cursor.execute(
            f""" SELECT sentence FROM {self._TABLE_NAME} """
        )
        return [
            result[0]
            for result in data.fetchall()
        ]

    @property
    def sentences(self) -> List[str]:
        """
        :return: list of str, list of all sentences.
        """
        return self._sentences

    @property
    def marker(self) -> Callable:
        """
        :return: callable obj, marker function.
        """
        return self._marker

    def find_examples(self,
                      word: str) -> List[str]:
        """ Find all sentences with the word insight.
        All found words'll be marked.

        :param word: str, word to find its examples.
        :return: list of str, sentences with the word.
        """
        data = self._cursor.execute(
            f""" SELECT sentence FROM {self._TABLE_NAME} WHERE sentence LIKE '%{word}%' """
        )

        return [
            self.mark_words(result[0], word)
            for result in data.fetchall()
        ]

    def find_date(self,
                  date: datetime.date) -> List[str]:
        """ Get all sentences created on the date.

        :param date: datetime.date object.
        :return: list of str, sentences.
        """
        data = self._cursor.execute(
            f""" SELECT sentence FROM {self._TABLE_NAME} WHERE date = {date} """
        )
        return [
            result[0]
            for result in data.fetchall()
        ]

    def sort(self,
             key: Callable = len,
             reverse: bool = False) -> None:
        """ Sort the sentences list by the key.
        By default – sorting by len of sentences.

        :param key: callable obj, key to sort sentences.
        By default – len.
        :param reverse: bool, whether the list'll be sorted in
        reversed order.
        :return: None.
        :exception TypeError: if the key is uncallable.
        """
        if not callable(key):
            raise TypeError("Sort key must be callable")

        self._sentences.sort(key=key, reverse=reverse)

    def mark_words(self,
                   string: str,
                   word: str) -> str:
        """ Mark words in the string by using marker function.

        if the word is empty or marker is None –
        return string without changes.

        :param string: str to mark words here.
        :param word: str, word to mark.
        :return: str with marked words or original one.
        """
        if self.marker is None or not word:
            return string

        for match in re.finditer(fr'\b\w*{word}\w*\b', string, flags=re.IGNORECASE):
            start, end = match.start(), match.end()
            string = f"{string[:start]}{self.marker(string[start:end])}{string[end:]}"
        return string

    def __call__(self,
                 word: str) -> List[str]:
        """ Find all sentences with the word insight.

        All the same to find_examples().

        :param word: str, word to find its examples.
        :return: list of str, sentences with the word.
        """
        return self.find_examples(word)

    def __contains__(self,
                     word: str) -> bool:
        """
        :param word: str, word to check.
        :return: whether there's a sentence with the word.
        """
        data = self._cursor.execute(
            f""" SELECT sentence FROM {self._TABLE_NAME} WHERE sentence LIKE '%{word}%' """
        )
        return bool(data.fetchone())

    def __str__(self) -> str:
        """
        :return: all sentences from the base, joined with \n.
        """
        return '\n'.join(self.sentences)

    def __iter__(self) -> iter:
        """
        :return: iter to sentences list.
        """
        return iter(self.sentences)

    def __bool__(self) -> bool:
        """
        :return: whether the sentences list exists.
        """
        return bool(self.sentences)

    def __getitem__(self,
                    item: int or slice) -> List[str]:
        """ Get the item at the index or the list with sliced data.

        :param item: int or slice.
        :return: one sentence or list of them.
        :exception TypeError: if wrong type given.
        """
        if isinstance(item, (int, slice)):
            return self.sentences[item]
        raise TypeError(f"Wrong value: {item}, int or slice expected")

    def __len__(self) -> int:
        """
        :return: int, sentences list size.
        """
        return len(self.sentences)

    def __eq__(self,
               other: Any) -> bool:
        """
        :param other: another SelfExamples obj or list.
        :return: bool, whether the sentences lists equal.
        :exception TypeError: if the wrong type given.
        """
        if isinstance(other, self.__class__):
            return self.sentences == other.sentences
        elif isinstance(other, list):
            return self.sentences == other
        raise TypeError(f"'Operator ==' not implemented to {type(self)} and {type(other)}")
