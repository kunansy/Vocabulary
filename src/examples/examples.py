__all__ = (
    'SelfExamples',
    'RussianCorpusExamples',
    'EnglishCorpusExamples'
)

import asyncio
import random as rand
from typing import (
    List, Dict, Callable, Tuple, Any
)

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from src.backup.backup_setup import backup
from src.main.common_funcs import (
    fmt_str, file_name, file_exist,
    add_to_file_name
)
from src.main.constants import (
    SELF_EX_PATH, CORPUS_URL
)
from src.trouble.trouble import Trouble


SPH = 100_000


async def fetch(_url: str,
                _ses: ClientSession,
                **kwargs) -> str:
    """ Coro, obtained html code of the page;

        If response.status != 200, (async) sleep 1
        second, print a message and try again

    :param _url: URL to get its html code;
    URL must start with http(s)://
    :param _ses: asyncio.ClientSession
    :param kwargs: kwargs to aiohttp.ClientSession.get()
    :return: html code, decoding to str(UTF-8)
    """
    async with _ses.get(_url, params=kwargs) as resp:
        if resp.status != 200:
            await asyncio.sleep(1)
            print(f"{resp.status}: '{resp.reason}'",
                  f"error requesting to {_url}", sep='\n')
            return await fetch(_url, _ses, **kwargs)

        html = await resp.read()
        return html.decode(encoding='utf-8')


async def bound_fetch(_sem: asyncio.Semaphore,
                      _url: str,
                      _session: ClientSession,
                      **kwargs) -> str:
    """ Coro, working with Semaphore

    :param _sem: asyncio.Semaphore
    :param _url: URL to get its html code;
    URL must start with http(s)://
    :param _session: asyncio.ClientSession
    :param kwargs: kwargs to aiohttp.ClientSession.get()
    :return: str, html code of the page
    """
    async with _sem:
        return await fetch(_url, _session, **kwargs)


async def get_htmls_coro(_url: str,
                         p_count: int,
                         **kwargs) -> List[str]:
    """ Coro with ClientSession, creating tasks and gathering;
        Creating and transmitting Semaphore to the next coro

    :param _url: str, URL to get its html codes;
    URL must start with http(s)://
    :param p_count: int, count of pages and 'p' key
    for corpus requesting
    :param kwargs: kwargs to aiohttp.ClientSession.get()
    :return: list of str, html codes of the pages
    """
    _sem = asyncio.Semaphore(SPH)

    async with ClientSession() as session:
        _tasks = [
            asyncio.create_task(
                bound_fetch(
                    _sem, _url, session, p=p_num, **kwargs
                )
            )
            for p_num in range(p_count)
        ]

        return await asyncio.gather(*_tasks)


def get_htmls(_url: str,
              p_count: int,
              **kwargs) -> List[str]:
    """ Coro running, get html code of the pages

    :param _url: str, URL to get its html code;
    URLs must start with http(s)://
    :param p_count: int, count of pages and key 'p'
    for corpus requesting
    :param kwargs: kwargs to aiohttp.ClientSession.get()
    :return: list of str, html codes of the pages
    :exception Trouble: if wrong type given or
    p_count <= 0
    """
    trbl = Trouble(get_htmls)
    if not (isinstance(_url, str) and _url):
        raise trbl(f"Wrong ULR {_url}", "right str")
    if not (isinstance(p_count, int) and p_count > 0):
        raise trbl(p_count, _p='w_int')

    try:
        res = asyncio.run(get_htmls_coro(_url, p_count, **kwargs))
    except aiohttp.client.InvalidURL as err:
        print(f"Invalid url: {err}",
              "Wrong urls or params given",
              "Func – get_htmls", sep='\n')
    else:
        return res


class Examples:
    """ Base examples class """
    __slots__ = '_item', '_examples'

    def __init__(self,
                 _word: str) -> None:
        """ Init the word and examples base

        :param _word: str, word to find its examples
        :return: None
        :exception Trouble: if the wrong type given
        """
        if not (isinstance(_word, str) and _word):
            raise Trouble(self.__init__, _word, _p='w_str')

        self._item = fmt_str(_word)
        self._examples = []

    def pop(self,
            _index: int) -> Any:
        """ Pop the element from the list by its index,
            using standard list method

        :param _index: int, index of the pop element
        :return: its value
        :exception Trouble: If wrong type given
        """
        if not isinstance(_index, int):
            raise Trouble(self.pop, _index, _p='w_int')

        return self._examples.pop(_index)

    def reverse(self) -> None:
        """ Reverse the examples list,
            using standard list method

        :return: None
        """
        self._examples.reverse()

    def clear(self) -> None:
        """ Clear the examples list,
            using standard list method

        :return: None
        """
        self._examples.clear()

    def get(self,
            _count: int) -> List[Any]:
        """ Get first n examples, using slice

        :param _count: int, count of examples
        :return: list of examples
        :exception Trouble: if wrong type given
        """
        if not isinstance(_count, int):
            raise Trouble(self.get, _count, _p='w_int')
        return self[:_count]

    def shuffle(self) -> None:
        """ Shuffle the examples list

        :return: None
        """
        rand.shuffle(self._examples)

    def __iter__(self) -> iter:
        """ Get the iter, using standard list method

        :return: iter to self._examples
        """
        return iter(self._examples)

    def __bool__(self) -> bool:
        """ bool to examples list, standard list method

        :return: bool value to examples list
        """
        return bool(self._examples)

    def __getitem__(self,
                    _item: int or slice) -> List[Any]:
        """ Standard list method, returning list of dicts

        :param _item: int or slice
        :return: list of examples
        :exception Trouble: if wrong type given
        """
        if isinstance(_item, int):
            return [self._examples[_item]]
        elif isinstance(_item, slice):
            return self._examples[_item.start:_item.stop:_item.step]
        else:
            raise Trouble(self.__getitem__,
                          f"Wrong value: {_item}",
                          "int or slice")

    def sort(self,
             key: Callable = len,
             **kwargs) -> None:
        """ Sort the examples list by the given key (callable object),
            using standard list method;
            Supports standard list.sort params;
            By default – sorting by len of sentences

        :param key: callable obj
        :param kwargs: kwargs arguments to list.sort method
        :return: None
        :exception Trouble: if key is uncallable
        """
        if not callable(key):
            raise Trouble(self.sort, key, 'callable obj')

        self._examples.sort(key=lambda x: key(x), **kwargs)

    def __len__(self) -> int:
        """ Len of the examples list,
            using standard list method

        :return: int, size of examples list
        """
        return len(self._examples)


class SelfExamples(Examples):
    """ Class to work with self examples """
    __slots__ = '_path', '_examples'

    def __init__(self,
                 path: str = SELF_EX_PATH) -> None:
        """ Init path, load examples from it

        :param path: str, path to the self examples base
        :return: None
        :exception Trouble: if file does not exist
        """
        super().__init__("init")
        if not file_exist(path):
            raise Trouble(self.__init__, path, _p='w_file')

        self._path = path
        self._examples = self._load()

    def _load(self) -> List[str]:
        """ Load examples from the base,
            register does not change,
            encoding – UTF-8

        :return: list of str, examples from the base
        """
        examples = open(self._path, 'r', encoding='utf-8').readlines()
        examples = filter(lambda x: not ('[' in x or ']' in x), examples)
        examples = filter(lambda x: x.strip(), examples)
        return [
            i.strip()
            for i in examples
        ]

    def find(self,
             _word: str) -> List[str]:
        """ Find all examples of the word

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
            i for i in self._examples
            if _word in i.lower()
        ]

    def count(self,
              _word: str) -> int:
        """ Count of examples of the word in the base,
            len of the list from find()

        :param _word: str, word to find the count
        of its examples, lowered and stripped
        :return: int, count of the examples
        :exception Trouble: if wrong type given,
        _word is empty or ' ' in _word
        """
        return len(self.find(_word))

    def backup(self) -> None:
        """ Backup examples base to the Google Drive,
            using backup module;
            Name of the file on the disk is equal
            base name + base length

        :return: None
        """
        f_name = add_to_file_name(file_name(self._path),
                                  f"_{len(self)}")
        print(f"{self.__class__.__name__} backupping...")
        backup(f_name, self._path)

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
            bool() to results of the find(_word)

        :param _word: word to find its example,
        lowered and stripped
        :return: bool, Is there an example in the base?
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
            f"{i[0]}. {i[1]}"
            for i in enumerate(self._examples, 1)
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


# Some of corpus examples http keys:
# I. Sorting, key &sort
#  1. i_grtagging – by default (what it means?)
#  2. random – randomly
#  3. i_grauthor – by author
#  4. i_grcreated_inv – by creation date
#  5. i_grcreated – by creation date in reversed order
#  6. i_grbirthday_inv – by author's birth date
#  7. i_grbirthday – by author's birth date in reversed order
# II. Subcorpus type, key &mode
#  1. main – main (russian) subcorpus
#  2. para – parallel subcorpus (all of them)
#  3. paper – paper subcorpus etc...
# III. Searching method, key &text:
#  1. lexgramm – lexical and grammatical search
#  2. lexform – search for exact forms, words via &req, spaces = %20
# IV. Showing format, key &out:
#  1. normal – usual
#  2. kwic – Key Word In Context,
#     2.1 &kwsz – amount of words in context
# V. Amount of examples in the document, key &spd
#  1. &spd – int value
# VI. Docs per page, key &dpp
#  1. &dpp – int value
# VII. Page number, key &p
#  1. &p – int value
# VIII. Distance between n and (n + 1) word, keys &min(n + 1), &max(n + 1)
#  1. &min(n + 1) – int value
#  2. &max(n + 1) – int value
# IX. &mycorp
#  1. %28lang%3A%22eng%22%7Clang_trans%3A%22eng%22%29 – for English parallel subcorpus
# X. Unknown keys:
#  1. &seed=any int, optionally
#  2. &env=alpha, optionally
#  3. &level_n=0, optionally
#  4. &parent_n=0, optionally
#  5. &mysentsize=1608212, optionally
#  6. &mysize=28363771, optionally


class CorpusExamples(Examples):
    """ Base class of corpus examples """
    __slots__ = '_url', '_item', '_count', '_examples', '_params'
    # max distance between neighboring words
    MAX_DIST = 2
    # documents per page
    DOC_PER_PAGE = 5
    # examples per document
    SENTENCES_PER_DOC = 1

    def __init__(self,
                 _word: str,
                 _count: int) -> None:
        """ Contains url of the corpus, word,
            count and examples, obtained from the corpus;

            Count be in range (0; 45);
            If there is space in _word, then request
            happens with all words, max distance between
            them is MAX_DIST constant

        :param _word: word to find, str
        :param _count: int, in range (0; 45]
        :return: None
        :exception Trouble: if wrong type given,
        count beyond the range
        """
        super().__init__(_word)
        _trbl = Trouble(self.__init__)
        if not (isinstance(_count, int)):
            raise _trbl(_count, _p='w_int')
        if not (0 < _count <= 45):
            raise _trbl(f"Wrong examples count: '{_count}'",
                        "in (0; 45)")

        self._item = fmt_str(_word).split()
        self._examples = []
        self._count = _count
        self._url = CORPUS_URL
        self._params = {
            'text': 'lexgramm',
            'out': 'normal',
            'sort': 'i_grcreated',
            'env': 'alpha',
            'dpp': self.DOC_PER_PAGE,
            'spd': self.SENTENCES_PER_DOC
        }

    def _new_examples(self) -> None:
        """ Get examples, put them to the list, write a
            message if sth went wrong (catch an exception);

            Usually it obtained more examples than expected,
            to list gets only fist _count by using slice
        :return: None
        """
        try:
            _examples = self._request_parse_examples()
        except Exception as err:
            print(err,
                  f"Requesting examples to '{' '.join(self._item)}'",
                  "Terminating...",
                  sep='\n')
        else:
            self._examples = _examples[:][:self._count]

    def _request_parse_examples(self) -> List[Dict]:
        """ Request count examples of the word
            and parse html code of the pages

            There are 5 docs at the page → requesting count // 5 pages,
            but <= 9, otherwise the corpus returns 429 error
        :return: list of dicts, parsed pages
        """
        # TODO: if there are a little count of examples in the corpus,
        #  or if count examples obtained from < count // 5 pages,
        #  further requests get a lot of time; How to fix?

        p_count = self._count // 5 if self._count >= 5 else 1
        self._extend_params()

        # html code of the pages
        htmls = get_htmls(self._url, p_count, **self._params)
        # TODO: async html code parsing, how to?
        #  1. unsync, https://youtu.be/F19R_M4Nay4 – slower than sync
        #  2. loop.run_in_executor() – parsers must be segregated from classes and
        #  executing time is not better a lot (gt. asyncreq.py)
        return self._parse_all(htmls)

    def _parse_doc(self,
                   _text: str) -> List[Dict]:
        """ Parse the doc to list of dicts {
                lang or another key: text,
                source: text source
            }

            Parsing depends on subcorpus, the
            method redefined at descendants
        """
        pass

    def _parse_page(self,
                    _html: str) -> List[Dict]:
        """ Parse html code of one page by ul tags to
            dicts, parsing depends on _parse_doc func;
            Catch all exception from _parse_doc

        :param _html: html code of the page
        :return: list of dicts, all docs in the page
        :exception Trouble: if wrong type given
        """
        if not (isinstance(_html, str) and _html):
            raise Trouble(self._parse_page, _html, _p='w_str')

        soup = BeautifulSoup(_html, 'lxml')
        ul = soup.findAll('ul')
        res = []
        for tag in ul:
            try:
                parsed_text = self._parse_doc(tag.text)
            except ValueError:
                # substring not found
                pass
            except Exception as err:
                print("Error:", err, f"{self._parse_page.__name__}")
            else:
                res += parsed_text
        return res

    def _parse_all(self,
                   htmls: List[str]) -> List[Dict]:
        """ Parse html code of the all pages,
            parsing depends on _parse_doc func

        :param htmls: list of str, html codes
        :return: list of dicts, parsed html codes
        :exception Trouble: if wrong type given
        """
        if not(isinstance(htmls, list) and htmls and
               all(isinstance(i, str) for i in htmls)):
            raise Trouble(self._parse_all, htmls, _p='w_tuples')

        return sum([(self._parse_page(page)) for page in htmls], [])

    def _txt_src(self,
                 text: str) -> Tuple[str, str]:
        """ Parse the string to txt and source,
            removing '[омин...' part

        :param text: str
        :return: tuple of text and its source
        :exception Trouble: if wrong type given
        """
        if not (isinstance(text, str) and text):
            raise Trouble(self._txt_src, text, _p='w_str')

        brace = text.index('[')
        txt, src = text[:brace], text[brace:text.index('[омон')].strip()
        # remove braces symbols
        if src.startswith('['):
            src = src[1:]
        if src.endswith(']'):
            src = src[:-1]
        return txt, src

    def _clean_str(self,
                   text: str) -> str:
        """ Remove double spaces, and everything but
            '-–.,:;―!? from the string

        :param text: str
        :return: cleaned str
        :exception Trouble: if wrong type given
        """
        if not (isinstance(text, str) and text):
            raise Trouble(self._clean_str, text, _p='w_str')

        text = filter(lambda x: x.isalpha() or x in " '-–.,:;―!?", text)
        text = ''.join(text)
        text = text.replace('\\', '').split()
        return ' '.join(text)

    def _extend_params(self) -> None:
        """ Add words and distance between them to
            params dict

        :return: None
        """
        # if there are more than 1 word,
        # add distance parameter
        flag = len(self._item) > 1

        for num, word in enumerate(self._item, 1):
            self._params[f'lex{num}'] = word
            if flag:
                self._params[f'max{num + 1}'] = self.MAX_DIST
                self._params[f'min{num + 1}'] = 1

    def extend(self,
               other) -> None:
        """ Extend the examples list by another item,
            using '+=' method;

        :param other: list of dicts, one dict or CorpusExamples object
        :return: None
        :exception Trouble: if wrong type given
        """
        # TODO: fix
        self += other

    def __str__(self) -> str:
        """ Enumerated with '1' examples,
            using dict keys;

            Example:
            self._examples like:
            [{'en': some text, 'ru': some text, 'source': some text} * n,
            {'text': some text, 'source': some text} * m]
            converting to str like:
            1.
            EN: some text
            RU: some text
            SOURCE: some text
            ...
            n + 1.
            TEXT: some text
            SOURCE: some text
            ...
            n + m.
            TEXT: some text
            SOURCE: some text

        :return: str with enumerated examples or
        "Examples to: 'word' not found" if resulting list is empty
        """
        if not self._examples:
            return f"Examples to '{' '.join(self._item)}' not found"

        _res = []
        for num, exmpl in enumerate(self._examples, 1):
            j = f'{num}.\n'
            for key, val in exmpl.items():
                j += f"{key.upper()}: {val}\n"
            _res += [j]

        return '\n'.join(_res)

    def __iadd__(self,
                 other):
        """ Extend examples list with another list of dicts,
        one dict or CorpusExamples object

        :param other: list of dicts, one dict or CorpusExamples object
        :return: self
        :exception Trouble: if wrong type given
        """
        if isinstance(other, list) and all(isinstance(i, dict) for i in other):
            self._examples.extend(other)
            return self
        elif isinstance(other, dict):
            self._examples.append(other)
            return self
        elif isinstance(other, CorpusExamples):
            self._examples.extend(other._examples)
            return self
        else:
            raise Trouble(self.__iadd__,
                          f"Wrong item: '{other}'",
                          "list, CorpusExamples or dict")


class RussianCorpusExamples(CorpusExamples):
    """ Class to work with general (russian) subcorpus of NCRL """
    __slots__ = '_url', '_item', '_count', '_examples'

    def __init__(self,
                 _word: str,
                 _count: int) -> None:
        """ Parent init and getting examples;

        :param _word: str, word to find its examples
        :param _count: int, count of examples
        :return: None:
        :exception Trouble: if wrong type given,
        count beyond the range
        """
        super().__init__(_word, _count)

        self._params['mode'] = 'main'
        self._new_examples()

    def _parse_doc(self,
                   _text: str) -> List[Dict[str, str]]:
        """ Dicts: {
                text: russian text,
                source: text source
            }
        :param _text: doc to parse
        :return: list of dicts
        :exception Trouble: if wrong type given
        """
        if not(isinstance(_text, str) and _text):
            raise Trouble(self._parse_doc, _text, _p='w_str')

        # divide to groups, the last symbol is '' ever
        text = _text.split('←…→')[:-1]
        res = []
        for i in text:
            add = {}
            txt, src = self._txt_src(i)

            if not (txt and src):
                continue

            add['text'] = self._clean_str(txt)
            add['source'] = src
            # keys checking
            try:
                add['source'], add['text']
            except ValueError as trbl:
                print(f"{trbl}, RussianCorpusExamples._parse_tag",
                      txt, src, sep='\n')
            except Exception as trbl:
                print(trbl)
            else:
                res += [add]
        return res

    def sort(self,
             key: Callable = len,
             **params) -> None:
        """ Applying the key to the examples;
            Default – sorting by len

        :param key: callable obj
        :param params: standard kwargs to list.sort
        :return: None
        :exception Trouble: if key is uncallable
        """
        super().sort(key=lambda x: key(x['text']), **params)


class EnglishCorpusExamples(CorpusExamples):
    """ Class to work with parallel (english) subcorpus of NCRL """
    __slots__ = '_url', '_item', '_count', '_examples'

    def __init__(self,
                 _word: str,
                 _count: int) -> None:
        """ Parent init and getting examples;

        :param _word: str, word to find its examples
        :param _count: int, count of examples
        :return: None:
        :exception Trouble: if wrong type given,
        count beyond the range
        """
        super().__init__(_word, _count)
        self._params['mode'] = 'para'
        self._params['mycorp'] = '%28lang%3A%22eng%22%7Clang_trans%3A%22eng%22%29'

        self._new_examples()

    def _lang(self,
              _text: str) -> str:
        """ Language of the str, two alpha symbols in the beginning

        :param _text: str to define its language
        :return: 'en', 'ru' or empty str
        :exception Trouble: if the wrong type given or
        'ru' and 'en' not in _text
        :exception AssertionError: if the length of lang != 2
        """
        _trbl = Trouble(self._lang)
        if not isinstance(_text, str):
            raise _trbl(_text, _p='w_str')

        if not _text:
            return ''

        if not ('ru' in _text or 'en' in _text):
            raise _trbl(f"Wrong text: '{_text}'", "'ru' or 'en' insight")

        _text = _text[:3].strip()
        res = ''.join(filter(str.isalpha, _text))
        assert len(res) == 2, \
            _trbl(f"Wrong length of: '{_text}'", "2")
        return res

    def __join_duplicates(self,
                          trbl: List[str]) -> List[str]:
        """ If there are examples with the same language,
            going in a row, join them to the one str

        :param trbl: list of str with wrong examples
        :return: list of str, fixed examples
        :exception Trouble: if wrong type given
        """
        if not (isinstance(trbl, list) and trbl):
            raise Trouble(self.__join_duplicates, trbl, _p='w_list')
        res, prev_lang = [], None

        for i in range(len(trbl)):
            i_lang = self._lang(trbl[i])
            if prev_lang == i_lang:
                # TODO: if there are > 2 duplicates?
                #  What happened with the source?
                prev, curr = trbl[i - 1], trbl[i]
                # brace index in previous sentence
                pbi = prev.index('[')
                prev_txt, prev_src = prev[:pbi], prev[pbi:]
                curr_text = curr[:curr.index('[')].replace(i_lang, '', 1)

                res[-1] = prev_txt + curr_text + prev_src
            else:
                prev_lang = i_lang
                res += [trbl[i]]
        return res

    def __lang_txt_src(self,
                       _text: str) -> Tuple[str, str, str]:
        """ Parse the string to lang, text and source

        :param _text: text to parse
        :return: tuple of str: language, text and source
        :exception trouble: if wrong type given
        """
        if not (isinstance(_text, str) and _text):
            raise Trouble(self.__lang_txt_src, _text, _p='w_str')

        txt, src = self._txt_src(_text)
        lang = self._lang(txt)
        txt = txt.replace(lang, '', 1)
        return lang, txt, src

    def _parse_doc(self,
                   _text: str) -> List[Dict[str, str]]:
        """ Dicts: {
                'ru': russian text,
                'en': english text,
                'source': text source
            }
        :param _text: doc to parse
        :return: list of dicts
        :exception Trouble: if wrong type given
        """
        if not (isinstance(_text, str) and text):
            raise Trouble(self._parse_doc, _text, _p='w_str')

        # divide to groups, the last symbol is '' ever
        _text = _text.split('←…→')[:-1]

        # if there are sentences with the same language,
        # going in a row, unite them to the one str
        if any(self._lang(_text[i]) == self._lang(_text[i - 1])
               for i in range(1, len(_text))):
            _text = self.__join_duplicates(_text)[:]

        res = []
        # original-translate going by pairs
        for fst, sec in zip(_text[::2], _text[1::2]):
            if not (fst and sec):
                continue
            add = {}
            # language, text, source
            fl, ft, fs = self.__lang_txt_src(fst)
            sl, st, ss = self.__lang_txt_src(sec)
            # source takes from the english text
            # TODO: sometimes a source is better in the 'ru' text
            src = fs if fl == 'en' else ss

            add[fl], add[sl] = self._clean_str(ft), self._clean_str(st)
            add['source'] = src

            # keys checking
            try:
                add['ru'], add['en'], add['source']
            except KeyError:
                print('One of the keys is wrong',
                      "'en', 'ru' and 'source' expected",
                      'func – parse_tag', sep='\n')
            except Exception as err:
                print(err, "parse_tag", sep='\n')
            else:
                res += [add]
        return res

    def sort(self,
             key: Callable = len,
             **params):
        """ Applying the key to the english text
            Default – sorting by len

        :param key: callable obj
        :param params: standard kwargs to list.sort
        :return: None
        :exception Trouble: if key is uncallable
        """
        super().sort(key=lambda x: key(x['en']), **params)


# TODO: write tests and docs to all features
# TODO: define comparison operators to CorpusExamples class
