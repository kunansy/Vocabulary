__all__ = [
    'SelfExamples',
    'RussianCorpusExamples',
    'ParallelCorpusExamples'
]


import asyncio
import random as rand
from typing import List, Dict

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from src.backup.backup_setup import backup
from src.main.common_funcs import (
    file_name, add_to_file_name, file_exist
)
from src.main.constants import (
    PCORPUS_URL, RCORPUS_URL, SELF_EX_PATH
)
from src.trouble.trouble import Trouble


SPH = 100_000


async def html_code(_url: str,
                    _ses: ClientSession,
                    **params) -> str:
    """ Получить html код страницы;

        Если ответ != от 200, то подождать
        секунду, вывести ошибку и повторить попытку
    """
    # TODO: как работать с потоками, чтобы загружать файлы в GDrive?
    async with _ses.get(_url, params=params) as resp:
        if resp.status != 200:
            await asyncio.sleep(1)
            print(f"{resp.status}: '{resp.reason}' "
                  f"error requesting to {_url}")
            return await html_code(
                _url, _ses, **params)

        html = await resp.read()
        return html.decode(encoding='utf-8')


async def bound_fetch(_sem: asyncio.Semaphore,
                      _url: str,
                      _session: ClientSession,
                      **params) -> str:
    """ Работа с учётом семафоры """
    async with _sem:
        return await html_code(
            _url, _session, **params)


async def parse_urls(_urls: List[str],
                     **params) -> List[str]:
    """ Корутина, получающая html коды страниц из списка url """
    _tasks = []
    _sem = asyncio.Semaphore(SPH)

    async with ClientSession() as session:
        _tasks = [
            asyncio.create_task(
                bound_fetch(
                    _sem, url, session, **params
                )
            )
            for url in _urls
        ]
        return await asyncio.gather(*_tasks)


def main_async(_urls: List[str],
               **params) -> List[str]:
    """ Вызов корутин, вернуть список
        полученных html кодов страниц
    """
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

    _future = asyncio.ensure_future(
        parse_urls(_urls, **params))
    return loop.run_until_complete(_future)


class SelfExamples:
    """ Класс собвтенных примеров """
    def __init__(self):
        """ Примеры храняться списком """
        # Порождает assert, если файл не найден;
        self.path = SELF_EX_PATH
        self._examples = self._load()

    def _load(self) -> list:
        """ Загрузить примеры из базы, регистр сохранён, кодировка – utf-8 """
        if not file_exist(self.path):
            print(Trouble(self._load, self.path, _p='w_file'))
            return []

        _examples = open(self.path, 'r', encoding='utf-8').readlines()
        return list(map(str.strip, _examples))

    def find(self,
             _item: str) -> list:
        """ Вернуть примеры слова списком, регистр выравнен """
        assert isinstance(_item, str) and _item, \
            Trouble(self.find, _item, _p='w_str')

        _item = _item.lower().strip()
        return list(filter(lambda x: _item in x.lower(),
                           self._examples))

    def count(self,
              _item: str) -> int:
        """ Количество примеров слова """
        return len(self.find(_item))

    def backup(self):
        """ Backup примеров """
        f_name = add_to_file_name(file_name(self.path),
                                  f"_{len(self)}")
        print(f"{self.__class__.__name__} backupping...")
        backup(f_name, self.path)

    def __call__(self,
                 _word: str) -> List[str]:
        return self.find(_word)

    def __getitem__(self,
                    _item):
        """
        Вернуть n-ый пример (индекс) или объект соответствующего
        класса (наследника), если передан срез
        """
        assert isinstance(_item, (int, slice)), \
            Trouble(self.__getitem__, _item, 'int or slice', _p='w_item')

        if isinstance(_item, slice):
            _res = self.__class__(self.base_path)
            _res._examples = self._examples[_item][:]
            return _res
        return self._examples[_item]

    def __contains__(self,
                     _item: str) -> bool:
        """ Есть ли пример такого слова """
        return bool(self.find(_item))

    def __str__(self) -> str:
        """ Пронумерованные (с 1) примеры """
        _res = [f"{i[0]}. {i[1]}" for i in
                enumerate(self._examples, 1)]
        return '\n'.join(_res)

    def __len__(self) -> int:
        """ Общий объём базы """
        return len(self._examples)

    def __bool__(self) -> bool:
        return bool(self._examples)

    def __iter__(self) -> iter:
        return iter(self._examples)


class CorpusExamples:
    """ Базовый класс корпусных примеров """
    def __init__(self,
                 _url: str,
                 _word: str) -> None:
        """
        Полученные примеры хранятся в списке

        :param _url: адрес с {lex} и {p_num}, откуда будут получаться примеры
        :param _word: искомое слово
        """
        _trbl = Trouble(self.__init__)
        assert isinstance(_url, str) and _url, \
            _trbl(_url, _p='w_str')
        assert isinstance(_word, str) and _word, \
            _trbl(_word, _p='w_str')

        self._url = _url
        self._word = _word.lower().strip()
        self._examples = []

        try:
            _url.format(lex='1', p_num='1')
        except KeyError:
            raise _trbl("Invalid URL", "keys 'lex' and 'p_num'")

    def _new_examples(self,
                      _count: int) -> None:
        """ Получить новые примеры, обновить список, перемешав его """
        _trbl = Trouble(self._new_examples)

        assert isinstance(_count, int) and 0 < _count <= 45, \
            _trbl(f"Wrong examples count, it must be less than 46")

        try:
            new_exps = self._request_examples(
                self._word, _count)
        except Exception as err:
            print(err, f"Requesting examples to '{self._word}'",
                  "Terminating...", sep='\n')
        else:
            rand.shuffle(new_exps)
            self._examples = new_exps[:]

    def _request_examples(self,
                          _item: str,
                          _count: int) -> List[Dict]:
        """ Получить count примеров слова,

            Документов на страницу 5 → запрашиваем count // 5
            страниц, но меньше 10, т.к. иначе 429 ошибка
        """
        _trbl = Trouble(self._request_examples)

        assert isinstance(_item, str) and _item, \
            _trbl(_item, _p='w_str')
        assert isinstance(_count, int) and _count, \
            _trbl(_count, 'w_int')

        p_count = _count // 5 if _count >= 5 else 1
        # TODO: если примеров всего пара штук, то дальшейшие запросы
        #  занимают много времени; что делать?
        # нумерация с 0, тк первая страница имеет такой индекс
        urls = [
            self._url.format(lex=_item, p_num=num)
            for num in range(p_count)
        ]

        # html коды страниц
        htmls = main_async(urls)

        # TODO: асинхронный парсинг html страниц, возможно ли?
        res = self._parse_all(htmls)
        return res[:_count]

    def _parse_str(self,
                   _text: str) -> List[Dict]:
        """ парсинг зависит от подкорпуса,
            переопределено в наследниках
        """
        pass

    def _parse_page(self,
                    _html: str) -> List[Dict]:
        """ распарсить html код одной страницы, вычленив
            все ul тэги и разбив текст из них на словари
            с помощью _parse_str, вернуть их
        """
        soup = BeautifulSoup(_html, 'lxml')
        ul = soup.findAll('ul')
        res = []
        for tag in ul:
            try:
                parsed_text = self._parse_str(tag.text)
            except ValueError:
                pass
            except Exception as err:
                print(err, f"{self._parse_page}")
            else:
                res += parsed_text
        return res

    def _parse_all(self,
                   htmls: List[str]) -> List[Dict]:
        """ Распарсить все html коды страниц """
        return sum([self._parse_page(page) for page in htmls], [])

    def get(self,
            _count: int) -> List[Dict]:
        """ Получить первые count примеров из имеющегося списка """
        return self[:_count]

    def __len__(self):
        """ Общая длина списка """
        return len(self._examples)

    def __getitem__(self,
                    _item: int or slice) -> List[Dict]:
        if isinstance(_item, int):
            return self._examples[_item]
        elif isinstance(_item, slice):
            return self._examples[_item.start:_item.stop:_item.step]

    def __str__(self) -> str:
        """ Пронумерованнаые с 1 примеры """
        _res = []
        for num, i in enumerate(self._examples, 1):
            j = f'{num}.\n'
            for key, val in i.items():
                j += f"{key.upper()}: {val}\n"
            _res += [j]
        return '\n'.join(_res) if _res else \
            f"Examples to '{self._word}' not found"

    def __iter__(self) -> iter:
        return iter(self._examples)

    def __bool__(self):
        return bool(self._examples)


class RussianCorpusExamples(CorpusExamples):
    def __init__(self,
                 _word: str,
                 _count: int) -> None:
        """ init родителя и получение count примеров """
        assert 0 < _count <= 45, \
            Trouble(self.__init__, f"Wrong examples count, it must be less than 46")

        super().__init__(RCORPUS_URL, _word)

        self._new_examples(_count)

    def _parse_str(self,
                   _text: str) -> List[Dict]:
        """ Распарсить ul тэг на список словарей {
                'text: russian text,
                'source': text source
            }
        """
        # убрать двойные пробелы, разбить на группы результатов
        parsed = ' '.join(_text.split()).split('←…→')
        res = []
        for i in filter(len, parsed):
            add = {}
            try:
                txt = i[:i.index('[')].strip()
                source = i[i.index('[') + 1:i.index('[омонимия') - 2].strip()
                assert txt, source

                add['text'] = txt
                add['source'] = source
            except ValueError as trbl:
                print(f"{trbl}, RussianCorpusExamples._parse_str")
                continue
            except AssertionError:
                pass
            except Exception as trbl:
                print(trbl)
            else:
                res += [add]
        return res


class ParallelCorpusExamples(CorpusExamples):
    def __init__(self,
                 _word: str,
                 _count: int) -> None:
        assert 0 < _count <= 45, \
            Trouble(self.__init__, f"Wrong examples count, it must be less than 46")
        super().__init__(PCORPUS_URL, _word)

        self._new_examples(_count)

    def _parse_str(self,
                   _text: str) -> List[Dict]:
        """ Распарcить один ul тег на список словарей {
                    'ru': russian text,
                    'en': english text,
                    'source': text source
                }
            """
        # TODO: trouble, ru-ru and en-en
        res = []
        # убрать двойные пробелы, слэш, разбить на группы результатов
        parsed = ' '.join(_text.split()).replace('\\', '').split('←…→')
        # print(*parsed, sep='\n', end='\n\n')

        # оригинал - перевод идут в этом порядке
        for i in zip(parsed[::2], parsed[1::2]):
            fst, sec = i[0].strip(), i[1].strip()
            if not (fst and sec):
                continue
            add = {}
            # язык и текст первого
            fl = fs = ''
            # язык и текст второго
            sl = ss = ''
            # источник текста
            source = ''
            # TODO: вытягивать источник из строки, используя re
            # every str begins with 'en' or 'ru'
            if 'en' in fst[:4]:
                # источник вытягиваем из английского варианта
                source = fst[fst.index('[') + 1:fst.index('[омонимия') - 2].strip()
                fl, fs = 'en', fst[fst.index('en') + 2:fst.index('[')].strip()
                sl, ss = 'ru', sec[sec.index('ru') + 2:sec.index('[')].strip()
            elif 'ru' in fst[:4]:
                # источник вытягиваем из английского варианта
                source = sec[sec.index('[') + 1:sec.index('омонимия') - 2]
                fl, fs = 'ru', fst[fst.index('ru') + 2:fst.index('[')].strip()
                sl, ss = 'en', sec[sec.index('en') + 2:sec.index('[')].strip()

            # проверка ключей
            try:
                add[fl] = fs
                add[sl] = ss
                add['source'] = source
                add['ru'], add['en'], add['source']
            except KeyError:
                print("key error, parse_str")
                continue
            except Exception:
                print("exception, parse_str")
                pass
            else:
                res += [add]
        return res