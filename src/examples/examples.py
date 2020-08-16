__all__ = 'SelfExamples'

import asyncio
import os
import random as rand
from builtins import enumerate
from pathlib import Path
from pprint import pprint
from socket import timeout
from sys import stderr
from time import time
from typing import (
    List, Dict, Callable, Tuple, Any
)

import aiohttp
import bs4

# from src.backup.setup import backup
from requests import get

import src.main.constants as const
import src.main.common_funcs as comm_func


class Examples:
    """ Base examples class """
    __slots__ = '_word', '_examples', '_marker'

    def __init__(self,
                 word: str,
                 **kwargs) -> None:
        """ Init the word and examples base

        :param word: str, word to find its examples.
        :keyword marker: function to highlight searched words in examples.
        :return: None.
        """
        self._word = comm_func.fmt_str(word)
        self._examples = []

        # function to highlight searched words in examples
        marker = kwargs.get('marker', None)
        self._marker = marker

    @property
    def examples(self) -> List[str]:
        """ Get examples list """
        return self._examples

    @property
    def word(self) -> str:
        """ Get word to search """
        return self._word

    def shuffle(self) -> None:
        """ Shuffle the examples list

        :return: None
        """
        rand.shuffle(self._examples)

    def sort(self,
             key: Callable = len,
             reverse: bool = False) -> None:
        """ Sort the examples list by the given key (callable object).
        By default – sorting by len of sentences.

        Supports standard list.sort params.

        :param key: callable obj, default – len.
        :param reverse: bool, whether sort'll be in reversed order.
        :return: None
        :exception TypeError: if the key is uncallable.
        """
        if not callable(key):
            raise TypeError("Sort key must be callable")

        self._examples.sort(key=lambda x: key(x), reverse=reverse)

    def mark_searched_words(self,
                            _str: str,
                            words: List[str]) -> str:
        """ Mark words in str by using self._marker function.

        if _words is empty or marker is None – return _str.

        :param _str: string, str to mark words.
        :param words: list of strings, words to mark.
        :return: string, str with marked words or original str
         if marker is None or _words is empty.
        :exception Trouble: if wrong type given.
        """
        if self._marker is None or not words:
            return _str

        words = _str.split()
        marked_words = [
            self._marker(i)
            if any(sw.lower() == comm_func.clean_up(i).lower() for sw in words) else i
            for i in words
        ]
        return ' '.join(marked_words)

    def __iter__(self) -> iter:
        """
        :return: iter to examples list.
        """
        return iter(self.examples)

    def __bool__(self) -> bool:
        """
        :return: whether the examples list exists.
        """
        return bool(self.examples)

    def __getitem__(self,
                    item: int or slice) -> List[str]:
        """ Standard list method, get item at the index.

        :param item: int or slice.
        :return: ane example or list of them.
        :exception TypeError: if wrong type given.
        """
        if isinstance(item, (int, slice)):
            return self.examples[item]
        raise TypeError(f"Wrong value: {item}, int or slice expected")

    def __len__(self) -> int:
        """
        :return: int, examples list size.
        """
        return len(self.examples)


class SelfExamples(Examples):
    """ Class to work with self examples """
    __slots__ = '_path', '_examples', '_marker'

    def __init__(self,
                 f_path: Path = SELF_EX_PATH,
                 **kwargs) -> None:
        """ Init path, load examples from it

        :param f_path: string or Path, path to the self examples base
        :keyword marker: function to highlight searched words in examples,
         it must be callable, otherwise it is None
        :return: None
        :exception Trouble: if file does not exist
        """
        super().__init__("init", **kwargs)
        if isinstance(f_path, str):
            f_path = Path(f_path)

        if not f_path.exists():
            raise Trouble(self.__init__, f_path, _p='w_file')

        self._path = f_path
        self._examples = self._load()

    def _load(self) -> List[str]:
        """ Load examples from the base,
            register does not change,
            encoding – UTF-8

        :return: list of str, examples from the base
        """
        examples = self._path.open('r', encoding='utf-8').readlines()
        examples = filter(lambda x: not ('[' in x or ']' in x), examples)
        examples = filter(lambda x: x.strip(), examples)
        return [
            i.strip()
            for i in examples
        ]

    def find(self,
             _word: str) -> List[str]:
        """ Find all examples of the word,
        mark searched words by using _marker function

        :param _word: str, word to find its examples,
         lowered and stripped
        :return: list of str, all examples (_word in this sentence)
        :exception Trouble: if wrong type given,
         _word is empty or ' ' in _word
        """
        if not (isinstance(_word, str) and _word and ' ' not in _word):
            raise Trouble(self.find, _word, _p='w_str')

        _word = fmt_str(_word)
        return [
            self.mark_searched_words(sent, [_word])
            for sent in self._examples
            if _word in sent.lower()
        ]

    def count(self,
              _word: str) -> int:
        """ Count of examples of the word in the base,
            len of the find() list

        :param _word: str, word to find the count
         of its examples, lowered and stripped
        :return: int, count of the examples
        :exception Trouble: if wrong type given,
         _word is empty or ' ' in _word
        """
        return len(self.find(_word))

    def __call__(self,
                 _word: str) -> List[str]:
        """ Find all examples of the word;
            The same as find(_word)

        :param _word: str, word to find its examples,
         lowered and stripped
        :return: list of str, all examples (_word in this sentence)
        :exception Trouble: if wrong type given,
         _word is empty or ' ' in _word
        """
        return self.find(_word)

    def __contains__(self,
                     _word: str) -> bool:
        """ Is there an example in the base?
            bool to find(_word) list

        :param _word: word to find its example,
         lowered and stripped
        :return: bool, Is there an example in the base?
        :exception Trouble: if wrong type given,
         _word is empty or ' ' in _word
        """
        return bool(self.find(_word))

    def __str__(self) -> str:
        """ Examples, enumerated with 1 if they exist,
            'Examples do not exist' – otherwise

        :return: str with enumerated examples or
        'Examples do not exist'
        """
        if not self._examples:
            return "Examples do not exist"

        _res = [
            f"{num}. {sent}"
            for num, sent in enumerate(self._examples, 1)
        ]
        return '\n'.join(_res)

    def __eq__(self,
               other) -> bool:
        """ Compare examples lists

        :param other: another list or SelfExamples obj
        :return: does the lists equal?
        :exception Trouble: if wrong type given
        """
        if isinstance(other, SelfExamples):
            return self._examples == other._examples
        elif isinstance(other, list):
            return self._examples == other
        else:
            raise Trouble(self.__eq__,
                          f"Wrong type: '{other}'",
                          f"list or SelfExamples object")


if __name__ == '__main__':
    pass
