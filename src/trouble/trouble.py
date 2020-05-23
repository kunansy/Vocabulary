__all__ = ['Trouble']


class Trouble(Exception):
    patterns = {
        'w_str': "Wrong str: '{}'",
        'w_int': "Wrong int: '{}'",
        'w_dict': "Wrong dict: '{}'",
        'w_list': "Wrong list: '{}'",
        'w_file': "File: '{}' does not exist",
        'w_item': "Wrong item: '{}', right {} expected"
    }

    def __init__(self, _f, _err='', _exp='',
                 _p=None):
        # функция
        self._f = _f
        # что случилось, необязательно
        self._err = str(_err)
        # что ожидалось, необязательно
        self._exp = str(_exp)
        # паттерн ошибки, необязательно
        self._pattern = self.patterns.get(_p, None)

    def get_class_name(self) -> str:
        """
        Получить имя класса, где произошла ошибка

        :return: если ф-ция – метод, то имя класса,
        иначе – пустая строка
        """
        class_name = ''
        if 'method' in self._f.__class__.__name__:
            class_name = f"{self._f.__self__.__class__.__name__}."
        return class_name

    def what(self) -> str:
        """ Что произошло """
        # что ожидалось (необязательно)
        _exp = f", {self._exp} expected" * bool(self._exp)
        # укоротить сообщение
        shorted = '...' * (len(self._err) > 50)
        _err = f"{self._err[:50]}{shorted}"
        return f"Trouble: {_err}{_exp}"

    def where(self) -> str:
        """ Где произошло """
        class_name = self.get_class_name()
        # имя функции, где ошибка
        _f = "func – " * (not class_name) + self._f.__name__

        return f"Where: {class_name}{_f}"

    def construct(self) -> str:
        """
        Превратить имеющиеся данные в строку формата:
            что: проблема, ожидалось (необязательно)
            где: имя класса (если он есть) и функции
        """
        if self._pattern is None:
            _what = self.what()
        else:
            _what = self._pattern.format(self._err, self._exp)
        return f"\n{_what}\n{self.where()}"

    def __call__(self, *args, **kwargs):
        """
        Объект класса может передаваться в нескольких местах
        внутри одной функции как исключение:
            raise obj('wrong life', 'correct')

        Эта функция нужна для изменения переданных в начале атрибутов
        как дефолтных под нужные в данной ситуации:
        :param kwargs: может изменяться всё, приоритет выше
        :param args: могут изменяться только ошибка и ожидание по порядку,
        то есть первым передаётся ошибка, ожидание – вторым

        :return: изменённый объект класса
        """
        self._f = kwargs.pop('_f', self._f)
        self._err = str(kwargs.pop('_err', self._err))
        self._exp = str(kwargs.pop('_exp', self._exp))

        _p = kwargs.pop('_p', self._pattern)
        self._pattern = self.patterns.get(_p, self._pattern)

        if len(args) in [1, 2]:
            self._err = args[0]
        if len(args) == 2:
            self._exp = args[1]

        return self

    def __str__(self) -> str:
        """ Строковое представление через construct """
        return self.construct()