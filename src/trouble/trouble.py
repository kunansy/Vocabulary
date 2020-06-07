__all__ = 'Trouble'


class Trouble(Exception):
    PATTERNS = {
        'w_str': "Wrong str: '{}'",
        'w_int': "Wrong int: '{}'",
        'w_dict': "Wrong dict: '{}'",
        'w_list': "Wrong list: '{}'",
        'w_file': "File: '{}' does not exist",
        'w_item': "Wrong item: '{}'"
    }

    def __init__(self,
                 _f,
                 _err: str = '',
                 _exp: str = '',
                 _p: str = None,
                 _t: bool = False) -> None:
        """
        :param _f: function, callable obj.
        :param _err: string, what happened.
        :param _exp: string, what expected.
        :param _p: string, error pattern in PATTERNS.
        :return: None.
        """
        # function, required
        self._f = _f
        # what happened, optional
        self._err = str(_err)
        # what expected, optional
        self._exp = str(_exp)
        # error pattern, optional
        self._pattern = self.PATTERNS.get(_p, None)
        # add 'Terminating...' to str if is True
        self._terminating = _t

    def __class_name(self) -> str:
        """ Get class name from the function.

        :return: if the func is class method, class name, else – ''.
        """
        if 'method' in self._f.__class__.__name__:
            return f"{self._f.__self__.__class__.__name__}."
        return ''

    def what(self) -> str:
        """ What happened.

        :return: string, "Trouble: ..." + what happened
        """
        return f"Trouble: {self._err}"

    def expected(self) -> str:
        """ What expected. If nothing expected, return ''.

        :return: string, "Expected: ..." + what expected or
         empty str if nothing expected.
        """
        return f"Expected: {self._exp}" * bool(self._exp)

    def where(self) -> str:
        """ Where happened, class (if there's) and func name.

        :return: string, class (if there's) and func name.
        """
        class_name = self.__class_name()
        # set class name after func name (if it exists)
        _f = "func – " * (not class_name) + self._f.__name__

        return f"Where: {class_name}{_f}"

    def __call__(self, *args, **kwargs):
        """ Trouble obj can be called at different places in func
            raise obj(_err='wrong life', _exp='correct').

        The func used to changing given to init params for needed now.
        :param kwargs: can change all, highest priority.
        :param args: can change only err and exp by the given order,
        so first if error, second – expectation. Lowest priority.

        :return: changed obj
        """
        self._f = kwargs.pop('_f', self._f)
        self._err = str(kwargs.pop('_err', self._err))
        self._exp = str(kwargs.pop('_exp', self._exp))

        _p = kwargs.pop('_p', self._pattern)
        self._pattern = self.PATTERNS.get(_p, self._pattern)

        if len(args) in [1, 2]:
            self._err = args[0]
        if len(args) == 2:
            self._exp = args[1]

        return self

    def __str__(self) -> str:
        """ Convert data to string format:
        Trouble: problem (maybe just 'Trouble' without problem text)
        Expected: expectation (optional)
        Where: class_name(if there's).func_name, else func – func_name

        :return: string with it
        """
        if self._pattern is None:
            _what = self.what()
        else:
            _what = f"Trouble!\n{self._pattern.format(self._err)}"

        _terminating = "\nTerminating..." * self._terminating
        _expected = f"\n{self.expected()}" * bool(self._exp)
        return f"{_what}{_expected}\n{self.where()}{_terminating}"

    def __repr__(self) -> str:
        """
        Where: class and function name.
        Error: given _err.
        Expected: given _exp.
        Pattern: self._p
        Terminating: given key

        :return: string with it
        """
        return f'Where = {self.where()}\n ' \
               f'Error = {self._err}\n ' \
               f'Expected = {self._exp}\n' \
               f'Pattern: {self._pattern}\n' \
               f'Terminating: {self._terminating}'
